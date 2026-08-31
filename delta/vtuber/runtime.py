"""
Personal VTuber Runtime Coordinator for Delta.
Central orchestration layer tying together DeltaEngine, VTuberAgentAdapter,
SpeechManager, STTManager, EmotionEngine, PersonalityManager, MemoryManager, AvatarController,
and IdleBehaviorManager.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from delta.vtuber.adapter import VTuberAgentAdapter
from delta.vtuber.avatar.controller import AvatarController, avatar_controller
from delta.vtuber.avatar.priority import AnimationPriority, AnimationPrioritySystem
from delta.vtuber.behavior.idle import IdleBehaviorManager, idle_behavior_manager
from delta.vtuber.desktop import DesktopIntegration, WindowsDesktopIntegration, LinuxDesktopIntegration, NoopDesktopIntegration
from delta.vtuber.emotion.engine import EmotionEngine, emotion_engine
from delta.vtuber.event_bus import VTuberEventBus, vtuber_event_bus
from delta.vtuber.memory.manager import MemoryManager, memory_manager
from delta.vtuber.personality.manager import PersonalityManager, personality_manager
from delta.vtuber.presence.manager import PresenceManager, presence_manager
from delta.vtuber.response import ResponseDispatcher, response_dispatcher
from delta.vtuber.state_machine import VTuberState, VTuberStateMachine
from delta.vtuber.voice.speech_manager import SpeechManager
from delta.vtuber.voice.stt.manager import STTManager, stt_manager

logger = logging.getLogger(__name__)


class PersonalVTuberRuntime:
    """
    Comprehensive unified runtime coordinator for Delta AI VTuber companion experience.
    """

    def __init__(
        self,
        event_bus: Optional[VTuberEventBus] = None,
        state_machine: Optional[VTuberStateMachine] = None,
        adapter: Optional[VTuberAgentAdapter] = None,
        speech_mgr: Optional[SpeechManager] = None,
        stt_mgr: Optional[STTManager] = None,
        emotion_eng: Optional[EmotionEngine] = None,
        personality_mgr: Optional[PersonalityManager] = None,
        memory_mgr: Optional[MemoryManager] = None,
        avatar_ctrl: Optional[AvatarController] = None,
        idle_mgr: Optional[IdleBehaviorManager] = None,
    ):
        self.event_bus = event_bus or vtuber_event_bus
        self.state_machine = state_machine or VTuberStateMachine(event_bus=self.event_bus)
        self.adapter = adapter or VTuberAgentAdapter(state_machine=self.state_machine, event_bus=self.event_bus)
        self.speech_manager = speech_mgr
        self.stt_manager = stt_mgr or stt_manager
        self.emotion_engine = emotion_eng or emotion_engine
        self.personality = personality_mgr or personality_manager
        self.memory = memory_mgr or memory_manager
        self.avatar = avatar_ctrl or avatar_controller
        self.idle_behavior = idle_mgr or idle_behavior_manager
        self.presence = presence_manager
        self.response_dispatcher = response_dispatcher
        self.priority_system = AnimationPrioritySystem()
        self.desktop = WindowsDesktopIntegration() if WindowsDesktopIntegration().is_supported() else (LinuxDesktopIntegration() if LinuxDesktopIntegration().is_supported() else NoopDesktopIntegration())

        self._is_initialized = False

    @property
    def is_initialized(self) -> bool:
        return self._is_initialized

    async def initialize(self) -> None:
        """Initialize all VTuber subsystem lifecycles cleanly."""
        if self._is_initialized:
            return

        logger.info("Initializing Personal VTuber Runtime...")

        # 1. Initialize Avatar Controller
        await self.avatar.initialize()

        # 2. Initialize STT Manager & wire SpeechManager for barge-in
        await self.stt_manager.initialize()
        if self.speech_manager:
            self.stt_manager.speech_manager = self.speech_manager

        # 3. Attach Response Dispatcher unified pipeline
        self.response_dispatcher.attach_core_events()
        if self.speech_manager:
            self.response_dispatcher.wire_speech_lifecycle(self.speech_manager)

        # 4. Start Presence Scheduler
        await self.presence.start()

        # 5. Start Idle Behavior Background Scheduler
        await self.idle_behavior.start()

        self._is_initialized = True
        logger.info("Personal VTuber Runtime initialized successfully.")

    async def shutdown(self) -> None:
        """Release all VTuber subsystem lifecycles cleanly."""
        logger.info("Shutting down Personal VTuber Runtime...")

        # 1. Stop presence & idle scheduler
        await self.presence.stop()
        await self.idle_behavior.stop()

        # 2. Detach response pipeline core listener
        self.response_dispatcher.detach_core_events()

        # 3. Stop speech & STT
        if self.speech_manager:
            await self.speech_manager.shutdown()
        await self.stt_manager.shutdown()

        # 4. Shutdown avatar
        await self.avatar.shutdown()

        self._is_initialized = False
        logger.info("Personal VTuber Runtime shutdown complete.")

    def get_runtime_status(self) -> Dict[str, Any]:
        """Collect real-time state metrics across all VTuber subsystems."""
        return {
            "status": "online" if self._is_initialized else "ready",
            "state": self.state_machine.current_state.value,
            "persona": self.personality.profile.model_dump(),
            "mood": self.personality.mood.model_dump(),
            "emotion": {
                "emotion": self.emotion_engine.current_emotion.value,
                "intensity": self.emotion_engine.current_intensity,
                "expression": self.emotion_engine.current_expression.value,
            },
            "avatar": {
                "expression": self.avatar.current_state.expression.value,
                "speaking": self.avatar.current_state.speaking,
                "mouth_open": self.avatar.current_state.mouth_open,
                "head_x": self.avatar.current_state.head_x,
                "head_y": self.avatar.current_state.head_y,
            },
            "voice": {
                "speech_queue_size": self.speech_manager.queue_size if self.speech_manager else 0,
                "is_speaking": self.speech_manager.is_speaking if self.speech_manager else False,
                "voice_mode_active": self.stt_manager.is_voice_mode_active,
                "stt_state": self.stt_manager.current_state.value,
            },
            "memory": {
                "short_term_count": len(self.memory.short_term.messages),
                "long_term_count": len(self.memory.store.retrieve(limit=100)),
            },
            "presence": {
                "activity": self.presence.current_state.activity.value,
                "idle_duration": round(self.presence.current_state.idle_duration, 1),
                "attention_level": round(self.presence.current_state.attention_level, 2),
            },
            "priority": {
                "current_priority": self.priority_system.current_priority.name,
            },
        }


# Global singleton instance
personal_vtuber_runtime = PersonalVTuberRuntime()
