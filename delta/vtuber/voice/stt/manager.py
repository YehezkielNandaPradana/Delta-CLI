"""
Speech-to-Text Manager coordinating microphone inputs, VAD boundaries, STT provider transcription,
and automatic conversational loop routing to DeltaEngine.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Set

from delta.vtuber.events import VTuberEvent, VTuberEventType
from delta.vtuber.event_bus import VTuberEventBus, vtuber_event_bus
from delta.vtuber.state_machine import VTuberState, VTuberStateMachine
from delta.vtuber.voice.speech_manager import SpeechManager
from delta.vtuber.voice.stt.mock import MockSTTProvider
from delta.vtuber.voice.stt.provider import STTProvider
from delta.vtuber.voice.stt.schemas import STTFinalResult, STTPartialResult, STTResult, STTState
from delta.vtuber.voice.stt.vad import VoiceActivityDetector

logger = logging.getLogger(__name__)


class STTManager:
    """
    Orchestrates voice capture, VAD voice triggering, STT transcription,
    and automatic barge-in interrupts against SpeechManager.
    """

    def __init__(
        self,
        stt_provider: Optional[STTProvider] = None,
        vad: Optional[VoiceActivityDetector] = None,
        speech_manager: Optional[SpeechManager] = None,
        state_machine: Optional[VTuberStateMachine] = None,
        event_bus: Optional[VTuberEventBus] = None,
        input_handler: Optional[Callable[[str], Any]] = None,
    ):
        self.provider = stt_provider or MockSTTProvider()
        self.vad = vad or VoiceActivityDetector()
        self.speech_manager = speech_manager
        self.state_machine = state_machine
        self.event_bus = event_bus or vtuber_event_bus
        self.input_handler = input_handler

        self._state: STTState = STTState.IDLE
        self._listeners: Set[Callable[[STTResult], Any]] = set()
        self._is_voice_mode_active = False
        self._is_echo_protect_enabled = True

    @property
    def current_state(self) -> STTState:
        return self._state

    @property
    def is_voice_mode_active(self) -> bool:
        return self._is_voice_mode_active

    def set_voice_mode(self, active: bool) -> None:
        self._is_voice_mode_active = active
        if not active:
            self._state = STTState.IDLE
            self.vad.reset()

    def add_listener(self, listener: Callable[[STTResult], Any]) -> Callable[[], None]:
        self._listeners.add(listener)

        def _unsub():
            if listener in self._listeners:
                self._listeners.remove(listener)

        return _unsub

    async def initialize(self) -> None:
        if hasattr(self.provider, "initialize"):
            await self.provider.initialize()

    async def shutdown(self) -> None:
        self.set_voice_mode(False)
        if hasattr(self.provider, "shutdown"):
            await self.provider.shutdown()
        self._listeners.clear()

    async def handle_user_speech_start(self) -> None:
        """
        Triggered by VAD when user begins speaking: executes immediate barge-in interrupt.
        """
        # 1. Barge-in: immediately cancel ongoing agent speech & audio playback
        if self.speech_manager and self.speech_manager.is_speaking:
            logger.info("[Barge-in] User voice detected: interrupting ongoing speech")
            await self.speech_manager.stop()

        # 2. Transition State Machine to LISTENING
        if self.state_machine and self.state_machine.can_transition_to(VTuberState.LISTENING):
            await self.state_machine.transition_to(VTuberState.LISTENING)

        self._state = STTState.LISTENING

    async def process_audio_buffer(
        self,
        audio_bytes: bytes,
        language: str = "id-ID",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[STTResult]:
        """
        Process completed audio recording and trigger Delta conversational loop.
        """
        if not audio_bytes:
            return None

        self._state = STTState.PROCESSING
        try:
            result = await self.provider.transcribe(
                audio_data=audio_bytes,
                language=language,
                metadata=metadata,
            )

            # Notify listeners
            for listener in list(self._listeners):
                try:
                    res = listener(result)
                    if asyncio.iscoroutine(res):
                        asyncio.create_task(res)
                except Exception as exc:
                    logger.error("Error in STT listener: %s", exc)

            # Route to Delta conversational loop if text is non-empty
            if result.is_final and result.text.strip():
                await self._dispatch_to_conversational_loop(result.text.strip())

            self._state = STTState.IDLE
            return result

        except Exception as exc:
            self._state = STTState.ERROR
            logger.error("STT transcription error: %s", exc, exc_info=True)
            return None

    async def _dispatch_to_conversational_loop(self, transcribed_text: str) -> None:
        """
        Transition state to THINKING and dispatch user voice prompt to DeltaEngine.
        """
        logger.info("[Conversational Loop] Voice Input recognized: '%s'", transcribed_text)

        if self.state_machine and self.state_machine.can_transition_to(VTuberState.THINKING):
            await self.state_machine.transition_to(
                VTuberState.THINKING,
                text=f"User: {transcribed_text}",
            )

        if self.input_handler:
            import inspect
            if inspect.iscoroutinefunction(self.input_handler):
                await self.input_handler(transcribed_text)
            else:
                self.input_handler(transcribed_text)


# Global singleton instance
stt_manager = STTManager()
