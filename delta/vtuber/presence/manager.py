"""
Presence and Personal Companion Manager for Delta VTuber.
Coordinates personal presence state, friendly greetings, graceful farewell with timeout,
and contextual micro-reactions.
"""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, Optional, Set

from delta.vtuber.emotion.engine import EmotionEngine, emotion_engine
from delta.vtuber.event_bus import VTuberEventBus, vtuber_event_bus
from delta.vtuber.personality.manager import PersonalityManager, personality_manager
from delta.vtuber.presence.notifications import NotificationManager
from delta.vtuber.presence.reactions import MicroReactionEngine
from delta.vtuber.presence.schemas import PresenceActivity, PresenceState
from delta.vtuber.presence.scheduler import PresenceScheduler
from delta.vtuber.voice.speech_manager import SpeechManager

logger = logging.getLogger(__name__)


class PresenceManager:
    """
    Orchestrates Delta's personal companion presence, awareness, greeting, and farewell lifecycle.
    """

    def __init__(
        self,
        personality_mgr: Optional[PersonalityManager] = None,
        emotion_eng: Optional[EmotionEngine] = None,
        speech_mgr: Optional[SpeechManager] = None,
        event_bus: Optional[VTuberEventBus] = None,
        scheduler: Optional[PresenceScheduler] = None,
        notifications: Optional[NotificationManager] = None,
        companion_mode: bool = True,
    ):
        self.personality = personality_mgr or personality_manager
        self.emotion = emotion_eng or emotion_engine
        self.speech_manager = speech_mgr
        self.event_bus = event_bus or vtuber_event_bus
        self.scheduler = scheduler or PresenceScheduler()
        self.notifications = notifications or NotificationManager(self.event_bus)
        self.companion_mode = companion_mode

        self._activity: PresenceActivity = PresenceActivity.IDLE
        self._listeners: Set[Callable[[PresenceState], Any]] = set()

    @property
    def current_state(self) -> PresenceState:
        return PresenceState(
            online=True,
            activity=self._activity,
            last_interaction=self.scheduler._last_interaction_time,
            idle_duration=self.scheduler.idle_duration,
            attention_level=self.scheduler.attention_level,
        )

    def set_activity(self, activity: PresenceActivity) -> None:
        self._activity = activity
        self.scheduler.record_interaction()
        self._emit_presence_change()

    def add_listener(self, listener: Callable[[PresenceState], Any]) -> Callable[[], None]:
        self._listeners.add(listener)

        def _unsub():
            if listener in self._listeners:
                self._listeners.remove(listener)

        return _unsub

    def _emit_presence_change(self) -> None:
        state = self.current_state
        for listener in list(self._listeners):
            try:
                res = listener(state)
                if asyncio.iscoroutine(res):
                    asyncio.create_task(res)
            except Exception as exc:
                logger.error("Error in presence listener: %s", exc)

    async def generate_greeting(self, user_name: str = "kamu") -> str:
        """
        Generate natural spoken greeting based on persona, mood, and time of day.
        """
        import datetime
        hour = datetime.datetime.now().hour
        time_greeting = "Hai, selamat pagi" if 5 <= hour < 12 else ("Hai, selamat siang" if 12 <= hour < 16 else ("Hai, selamat sore" if 16 <= hour < 19 else "Hai, selamat malam"))

        persona = self.personality.profile
        if persona.formality < 0.5:
            greeting = f"{time_greeting}! Delta siap bantuin kamu ngoding dan riset hari ini."
        else:
            greeting = f"{time_greeting}. Sistem Delta AI siap bantu kamu."

        return greeting

    async def trigger_greeting(self, user_name: str = "kamu") -> Optional[str]:
        """
        Speak greeting if companion mode and speech manager are enabled.
        """
        if not self.companion_mode:
            return None

        greeting_text = await self.generate_greeting(user_name)
        if self.speech_manager:
            await self.speech_manager.enqueue_text(
                greeting_text,
                emotion=self.emotion.current_emotion,
                intensity=self.emotion.current_intensity,
            )
        return greeting_text

    async def trigger_farewell(self, timeout_sec: float = 3.0) -> None:
        """
        Speak graceful farewell before shutdown with strict timeout protection.
        """
        if not self.companion_mode or not self.speech_manager:
            return

        farewell_text = "Sampai jumpa lagi! Aku standby saat kamu butuh."
        try:
            await asyncio.wait_for(
                self.speech_manager.enqueue_text(
                    farewell_text,
                    emotion=self.emotion.current_emotion,
                    intensity=0.6,
                ),
                timeout=timeout_sec,
            )
        except Exception as exc:
            logger.debug("Farewell timed out or was skipped: %s", exc)

    async def start(self) -> None:
        await self.scheduler.start()

    async def stop(self) -> None:
        await self.scheduler.stop()


# Global singleton instance
presence_manager = PresenceManager()
