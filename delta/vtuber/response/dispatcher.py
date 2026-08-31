"""
Response Dispatcher for Delta VTuber Unified Pipeline.
Single source of truth for routing ResponsePayloads to VTuberEventBus, SpeechManager (TTS),
EmotionEngine, AvatarController, and VTube Studio.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, Optional, Set
from delta.ai.events import AgentEvent, EventType, event_bus as core_event_bus
from delta.vtuber.avatar.controller import AvatarController, avatar_controller
from delta.vtuber.emotion import EmotionEngine, emotion_engine
from delta.vtuber.event_bus import VTuberEventBus, vtuber_event_bus
from delta.vtuber.events import VTuberEvent, VTuberEventType, VTuberEmotion, VTuberPayload
from delta.vtuber.response.processor import ResponseProcessor, response_processor
from delta.vtuber.response.schemas import ResponsePayload
from delta.vtuber.voice.schemas import SpeechLifecycleEvent, SpeechLifecycleEventType
from delta.vtuber.voice.speech_manager import SpeechManager

logger = logging.getLogger(__name__)


class ResponseDispatcher:
    """
    Downstream orchestrator dispatching ResponsePayloads across all VTuber subsystems.
    """

    def __init__(
        self,
        processor: Optional[ResponseProcessor] = None,
        speech_mgr: Optional[SpeechManager] = None,
        avatar_ctrl: Optional[AvatarController] = None,
        emotion_eng: Optional[EmotionEngine] = None,
        event_bus: Optional[VTuberEventBus] = None,
        auto_attach_core: bool = False,
    ):
        self.processor = processor or response_processor
        self.speech_manager = speech_mgr
        self.avatar = avatar_ctrl or avatar_controller
        self.emotion_engine = emotion_eng or emotion_engine
        self.event_bus = event_bus or vtuber_event_bus

        self._dispatched_response_ids: Set[str] = set()
        self._current_response_id: Optional[str] = None
        self._unsubscribe_core: Optional[Callable[[], None]] = None
        self._unsubscribe_speech_lifecycle: Optional[Callable[[], None]] = None

        if auto_attach_core:
            self.attach_core_events()

    def attach_core_events(self, target_bus: Optional[Any] = None) -> None:
        """Subscribe to Delta Core AgentEvent stream for automatic MESSAGE_COMPLETE & ERROR dispatch."""
        bus = target_bus or core_event_bus
        if self._unsubscribe_core is None:
            self._unsubscribe_core = bus.subscribe(self.handle_core_agent_event)

    def detach_core_events(self) -> None:
        if self._unsubscribe_core is not None:
            self._unsubscribe_core()
            self._unsubscribe_core = None

    def wire_speech_lifecycle(self, speech_mgr: SpeechManager) -> None:
        """Wire SpeechManager lifecycle events to AvatarController and cancellation handlers."""
        self.speech_manager = speech_mgr
        if self._unsubscribe_speech_lifecycle is not None:
            self._unsubscribe_speech_lifecycle()

        def _on_speech_event(event: SpeechLifecycleEvent):
            # Safe async dispatch to avatar controller
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.avatar.handle_speech_lifecycle(event))
            except RuntimeError:
                pass

        self._unsubscribe_speech_lifecycle = speech_mgr.add_listener(_on_speech_event)

    def handle_core_agent_event(self, event: AgentEvent) -> None:
        """Synchronous callback from core EventBus."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.handle_core_agent_event_async(event))
        except RuntimeError:
            pass

    async def handle_core_agent_event_async(self, event: AgentEvent) -> None:
        """Process core MESSAGE_COMPLETE / ERROR events into ResponsePayloads."""
        ev_type = event.type if isinstance(event.type, EventType) else EventType(str(event.type))

        if ev_type == EventType.MESSAGE_COMPLETE:
            raw_text = event.content or ""
            res_id = getattr(event, "execution_id", None) or getattr(event, "session_id", None)
            payload = self.processor.process(
                raw_text,
                response_id=res_id,
                metadata={"execution_id": getattr(event, "execution_id", "")},
            )
            await self.dispatch(payload)

        elif ev_type == EventType.ERROR:
            err_msg = str(event.error) if event.error else (event.status_text or "Error processing request")
            payload = self.processor.process(
                err_msg,
                is_error=True,
                metadata={"error": True},
            )
            await self.dispatch(payload)

    async def dispatch(self, payload: ResponsePayload) -> bool:
        """
        Dispatch canonical ResponsePayload downstream.
        1. Deduplication check
        2. Empty check (suppresses empty speech & avatar triggers)
        3. Emit VTuberEvent.RESPONSE on bus
        4. Trigger EmotionEngine & Avatar Expression
        5. Enqueue TTS in SpeechManager
        """
        if not payload.response_id:
            return False

        # 1. Deduplication check
        if payload.response_id in self._dispatched_response_ids:
            logger.debug("[ResponseDispatcher] Ignored duplicate response_id: %s", payload.response_id)
            return False

        # Cap memory of dispatched IDs
        if len(self._dispatched_response_ids) > 300:
            self._dispatched_response_ids.clear()
        self._dispatched_response_ids.add(payload.response_id)
        self._current_response_id = payload.response_id

        # 2. Empty check
        if not payload.speech_text and not payload.display_text:
            logger.debug("[ResponseDispatcher] Suppressed empty response_id: %s", payload.response_id)
            return False

        logger.info("[ResponseDispatcher] Dispatching VTUBER_RESPONSE (%s) speech_len=%d", payload.response_id, len(payload.speech_text))

        # 3. Emit VTuberEvent RESPONSE on bus
        if self.event_bus:
            evt = VTuberEvent.create(
                event_type=VTuberEventType.RESPONSE,
                text=payload.speech_text or payload.display_text,
                emotion=payload.emotion,
                intensity=payload.emotion_intensity,
                metadata={"response_id": payload.response_id, "display_text": payload.display_text, **payload.metadata},
            )
            await self.event_bus.emit(evt)

        # 4. Trigger Emotion & Avatar Expression
        try:
            from delta.vtuber.emotion.schemas import VTuberEmotion as EmotionSchemaVal
            em_schema = EmotionSchemaVal(payload.emotion.value)
            await self.emotion_engine.set_emotion(
                emotion=em_schema,
                intensity=payload.emotion_intensity,
            )
            await self.avatar.set_expression(
                expression=self.emotion_engine.current_expression,
                intensity=payload.emotion_intensity,
            )
        except Exception as exc:
            logger.debug("Failed to set emotion in response dispatch: %s", exc)

        # 5. Enqueue TTS in SpeechManager if speech_text present
        if payload.speech_text and self.speech_manager:
            try:
                await self.speech_manager.enqueue_text(
                    text=payload.speech_text,
                    emotion=payload.emotion,
                    intensity=payload.emotion_intensity,
                    speech_id=payload.response_id,
                    metadata={"response_id": payload.response_id},
                )
                await self.avatar.set_speaking(True)
            except Exception as exc:
                logger.error("Failed to enqueue TTS in response dispatch: %s", exc)

        return True

    async def cancel_response(self, response_id: Optional[str] = None) -> None:
        """
        Barge-in / Cancellation: Immediate audio stop, zero mouth, reset avatar speaking.
        """
        target_id = response_id or self._current_response_id or "all"
        logger.info("[ResponseDispatcher] Cancelling response (%s)", target_id)

        if self.speech_manager:
            await self.speech_manager.stop()

        await self.avatar.set_speaking(False)
        await self.avatar.set_mouth_open(0.0)

    async def feed_stream_token(self, token: str, emotion: VTuberEmotion = VTuberEmotion.NEUTRAL) -> None:
        """Stream token to SpeechManager for incremental sentence synthesis."""
        if self.speech_manager:
            chunks = await self.speech_manager.enqueue_stream_token(token, emotion=emotion)
            if chunks:
                await self.avatar.set_speaking(True)

    async def flush_stream(self, emotion: VTuberEmotion = VTuberEmotion.NEUTRAL) -> None:
        """Flush remaining stream tokens."""
        if self.speech_manager:
            chunks = await self.speech_manager.flush_stream_tokens(emotion=emotion)
            if chunks:
                await self.avatar.set_speaking(True)


# Global singleton instance
response_dispatcher = ResponseDispatcher()
