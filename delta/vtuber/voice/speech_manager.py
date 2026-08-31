"""
Speech Manager and Pipeline Orchestrator for Delta VTuber.
Manages sentence chunking, FIFO speech queue, TTS synthesis, playback, and barge-in interrupts.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Set

from delta.vtuber.events import VTuberEmotion, VTuberEvent, VTuberEventType
from delta.vtuber.event_bus import VTuberEventBus, vtuber_event_bus
from delta.vtuber.voice.schemas import (
    AudioData,
    SpeechChunk,
    SpeechLifecycleEvent,
    SpeechLifecycleEventType,
    SpeechState,
)
from delta.vtuber.voice.sentence_chunker import SentenceChunker
from delta.vtuber.voice.tts import MockTTSProvider, TTSProvider
from delta.vtuber.voice.audio import AudioPlayer, MockAudioPlayer

logger = logging.getLogger(__name__)


class SpeechManager:
    """
    Speech pipeline manager that coordinates text chunking, TTS synthesis,
    and sequential audio playback while supporting clean barge-in interruption.
    """

    def __init__(
        self,
        tts_provider: Optional[TTSProvider] = None,
        audio_player: Optional[AudioPlayer] = None,
        sentence_chunker: Optional[SentenceChunker] = None,
        event_bus: Optional[VTuberEventBus] = None,
        auto_subscribe: bool = True,
    ):
        self.tts = tts_provider or MockTTSProvider()
        self.player = audio_player or MockAudioPlayer(playback_speed_multiplier=10.0)
        self.chunker = sentence_chunker or SentenceChunker()
        self.event_bus = event_bus or vtuber_event_bus

        self._queue: asyncio.Queue[SpeechChunk] = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._current_chunk: Optional[SpeechChunk] = None
        self._state: SpeechState = SpeechState.IDLE
        self._listeners: Set[Callable[[SpeechLifecycleEvent], Any]] = set()
        self._unsubscribe_bus: Optional[Callable[[], None]] = None
        self._is_running = False

        if auto_subscribe and self.event_bus:
            self._unsubscribe_bus = self.event_bus.subscribe(
                self.handle_vtuber_event,
                VTuberEventType.SPEAKING,
            )

    @property
    def current_state(self) -> SpeechState:
        return self._state

    @property
    def queue_size(self) -> int:
        return self._queue.qsize()

    @property
    def is_speaking(self) -> bool:
        return self._state in (SpeechState.SYNTHESIZING, SpeechState.PLAYING) or not self._queue.empty()

    def add_listener(self, listener: Callable[[SpeechLifecycleEvent], Any]) -> Callable[[], None]:
        """Subscribe a listener to internal speech lifecycle events."""
        self._listeners.add(listener)

        def _unsub():
            if listener in self._listeners:
                self._listeners.remove(listener)

        return _unsub

    def _emit_lifecycle(
        self,
        event_type: SpeechLifecycleEventType,
        chunk: Optional[SpeechChunk] = None,
        state: Optional[SpeechState] = None,
        error: Optional[str] = None,
        speech_id: Optional[str] = None,
    ) -> None:
        target_state = state or self._state
        sid = speech_id or (chunk.speech_id if chunk else self._current_speech_id)
        evt = SpeechLifecycleEvent(
            event_type=event_type,
            speech_id=sid,
            chunk_id=chunk.id if chunk else None,
            sequence=chunk.sequence if chunk else 0,
            text=chunk.text if chunk else None,
            state=target_state,
            error=error,
        )
        for listener in list(self._listeners):
            try:
                res = listener(evt)
                if asyncio.iscoroutine(res):
                    asyncio.create_task(res)
            except Exception as exc:
                logger.error("Error in speech lifecycle listener: %s", exc)

    async def start(self) -> None:
        """Start the background speech processing worker."""
        if self._worker_task is None or self._worker_task.done():
            self._is_running = True
            self._worker_task = asyncio.create_task(self._process_queue_loop())

    async def enqueue_text(
        self,
        text: str,
        emotion: VTuberEmotion = VTuberEmotion.NEUTRAL,
        intensity: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        speech_id: Optional[str] = None,
    ) -> List[SpeechChunk]:
        """
        Chunk full text and enqueue sentence parts for TTS synthesis and playback.
        """
        if not text or not text.strip():
            return []

        import uuid
        s_id = speech_id or str(uuid.uuid4())
        self._current_speech_id = s_id

        chunks = self.chunker.chunk_text(
            text,
            emotion=emotion,
            intensity=intensity,
            speech_id=s_id,
        )

        for chunk in chunks:
            if metadata:
                chunk.metadata.update(metadata)
            await self._queue.put(chunk)
            self._emit_lifecycle(
                SpeechLifecycleEventType.SPEECH_QUEUED,
                chunk=chunk,
                state=SpeechState.QUEUED,
                speech_id=s_id,
            )

        # Ensure worker is active
        await self.start()
        return chunks

    async def enqueue_stream_token(
        self,
        token: str,
        emotion: VTuberEmotion = VTuberEmotion.NEUTRAL,
        intensity: float = 1.0,
    ) -> List[SpeechChunk]:
        """
        Feed partial stream tokens incrementally and enqueue completed sentences immediately.
        """
        ready_chunks = self.chunker.append_stream_token(
            token,
            emotion=emotion,
            intensity=intensity,
        )
        for chunk in ready_chunks:
            await self._queue.put(chunk)
            self._emit_lifecycle(
                SpeechLifecycleEventType.SPEECH_QUEUED,
                chunk=chunk,
                state=SpeechState.QUEUED,
            )

        if ready_chunks:
            await self.start()

        return ready_chunks

    async def flush_stream_tokens(
        self,
        emotion: VTuberEmotion = VTuberEmotion.NEUTRAL,
        intensity: float = 1.0,
    ) -> List[SpeechChunk]:
        """
        Flush remaining streaming buffer and enqueue remaining text.
        """
        flushed_chunks = self.chunker.flush_stream(
            emotion=emotion,
            intensity=intensity,
        )
        for chunk in flushed_chunks:
            await self._queue.put(chunk)
            self._emit_lifecycle(
                SpeechLifecycleEventType.SPEECH_QUEUED,
                chunk=chunk,
                state=SpeechState.QUEUED,
            )

        if flushed_chunks:
            await self.start()

        return flushed_chunks

    async def handle_vtuber_event(self, event: VTuberEvent) -> None:
        """
        VTuberEventBus listener for SPEAKING events.
        """
        if event.type == VTuberEventType.SPEAKING and event.payload.text:
            await self.enqueue_text(
                text=event.payload.text,
                emotion=event.payload.emotion or VTuberEmotion.NEUTRAL,
                intensity=event.payload.intensity,
                metadata=event.payload.metadata,
            )

    async def _process_queue_loop(self) -> None:
        """
        Sequential consumer loop guaranteeing in-order synthesis and playback.
        """
        try:
            while self._is_running:
                chunk = await self._queue.get()
                self._current_chunk = chunk
                self._state = SpeechState.SYNTHESIZING

                self._emit_lifecycle(
                    SpeechLifecycleEventType.SPEECH_STARTED,
                    chunk=chunk,
                    state=SpeechState.SYNTHESIZING,
                )

                try:
                    # 1. Synthesize audio
                    audio_data = await self.tts.synthesize(chunk)
                    self._emit_lifecycle(
                        SpeechLifecycleEventType.SPEECH_SYNTHESIZED,
                        chunk=chunk,
                        state=SpeechState.PLAYING,
                    )

                    # 2. Play audio sequentially
                    self._state = SpeechState.PLAYING
                    self._emit_lifecycle(
                        SpeechLifecycleEventType.SPEECH_PLAYING,
                        chunk=chunk,
                        state=SpeechState.PLAYING,
                    )

                    await self.player.play(audio_data)

                    self._state = SpeechState.FINISHED
                    self._emit_lifecycle(
                        SpeechLifecycleEventType.SPEECH_FINISHED,
                        chunk=chunk,
                        state=SpeechState.FINISHED,
                    )

                except asyncio.CancelledError:
                    self._state = SpeechState.INTERRUPTED
                    self._emit_lifecycle(
                        SpeechLifecycleEventType.SPEECH_INTERRUPTED,
                        chunk=chunk,
                        state=SpeechState.INTERRUPTED,
                    )
                    raise
                except Exception as exc:
                    self._state = SpeechState.ERROR
                    logger.error("TTS or Audio error processing chunk %s: %s", chunk.id, exc, exc_info=True)
                    self._emit_lifecycle(
                        SpeechLifecycleEventType.SPEECH_ERROR,
                        chunk=chunk,
                        state=SpeechState.ERROR,
                        error=str(exc),
                    )
                finally:
                    self._current_chunk = None
                    self._queue.task_done()
                    if self._queue.empty():
                        self._state = SpeechState.IDLE

        except asyncio.CancelledError:
            self._state = SpeechState.INTERRUPTED
        finally:
            self._current_chunk = None
            if self._queue.empty():
                self._state = SpeechState.IDLE

    async def clear(self) -> None:
        """
        Drain all pending queued chunks without stopping current playback.
        """
        while not self._queue.empty():
            try:
                chunk = self._queue.get_nowait()
                self._queue.task_done()
                self._emit_lifecycle(
                    SpeechLifecycleEventType.SPEECH_INTERRUPTED,
                    chunk=chunk,
                    state=SpeechState.INTERRUPTED,
                )
            except asyncio.QueueEmpty:
                break
        self.chunker.reset_stream()

    async def stop(self) -> None:
        """
        Barge-in / Interrupt: Instantly cancel current TTS/playback and purge all queued speech.
        Guarantees zero orphan tasks left behind.
        """
        # 1. Purge queue
        await self.clear()

        # 2. Stop audio player
        try:
            await self.player.stop()
        except Exception as exc:
            logger.warning("Error stopping audio player: %s", exc)

        # 3. Cancel worker task cleanly
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None

        self._state = SpeechState.IDLE
        self._current_chunk = None

    async def shutdown(self) -> None:
        """Release all resources and unsubscribe from event bus."""
        await self.stop()
        if self._unsubscribe_bus:
            self._unsubscribe_bus()
            self._unsubscribe_bus = None
        self._listeners.clear()
