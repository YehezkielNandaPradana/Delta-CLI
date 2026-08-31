"""
Personality and Mood Manager for Delta VTuber.
Maintains PersonaProfile, updates MoodState over agent events, and calculates contextual mood influence on emotion.
"""

import time
from typing import Optional, Tuple
from delta.ai.events import AgentEvent, EventType
from delta.vtuber.emotion.schemas import VTuberEmotion
from delta.vtuber.personality.behavior import PersonalityBehavior
from delta.vtuber.personality.schemas import MoodState, PersonaProfile


class PersonalityManager:
    """
    Coordinates persona profile traits, mood updates, contextual emotion modulation,
    and speech formatting.
    """

    def __init__(
        self,
        profile: Optional[PersonaProfile] = None,
        mood: Optional[MoodState] = None,
    ):
        self.profile = profile or PersonaProfile()
        self.mood = mood or MoodState()
        self.behavior = PersonalityBehavior(self.profile)
        self._last_decay_check: float = time.time()

    def update_mood_from_event(self, event: AgentEvent) -> MoodState:
        """
        Gently update character mood based on ReAct agent events.
        """
        now = time.time()
        elapsed = now - self._last_decay_check
        if elapsed > 10.0:
            self.mood.decay_towards_baseline(elapsed)
            self._last_decay_check = now

        ev_type = event.type if isinstance(event.type, EventType) else EventType(str(event.type))

        if ev_type == EventType.TOOL_RESULT:
            if event.success:
                self.mood.happiness = min(1.0, self.mood.happiness + 0.08)
                self.mood.confidence = min(1.0, self.mood.confidence + 0.05)
                self.mood.stress = max(0.0, self.mood.stress - 0.05)
            else:
                self.mood.stress = min(1.0, self.mood.stress + 0.12)
                self.mood.confidence = max(0.2, self.mood.confidence - 0.05)

        elif ev_type == EventType.AGENT_COMPLETE:
            self.mood.happiness = min(1.0, self.mood.happiness + 0.15)
            self.mood.confidence = min(1.0, self.mood.confidence + 0.10)
            self.mood.stress = max(0.0, self.mood.stress - 0.10)

        elif ev_type == EventType.ERROR:
            self.mood.stress = min(1.0, self.mood.stress + 0.20)
            self.mood.happiness = max(0.1, self.mood.happiness - 0.15)

        elif ev_type == EventType.AGENT_THINKING:
            self.mood.curiosity = min(1.0, self.mood.curiosity + 0.04)

        return self.mood

    def modulate_emotion(
        self,
        base_emotion: VTuberEmotion,
        base_intensity: float,
    ) -> Tuple[VTuberEmotion, float]:
        """
        Apply persistent mood bias to instantaneous emotion calculations.
        """
        # If high stress and confused -> amplify confusion intensity
        if self.mood.stress > 0.6 and base_emotion == VTuberEmotion.CONFUSED:
            return VTuberEmotion.CONFUSED, min(1.0, base_intensity + 0.2)

        # If high happiness and happy -> elevate to EXCITED
        if self.mood.happiness > 0.8 and base_emotion == VTuberEmotion.HAPPY:
            return VTuberEmotion.EXCITED, min(1.0, base_intensity + 0.15)

        # If high curiosity and thinking -> elevate thinking intensity
        if self.mood.curiosity > 0.8 and base_emotion == VTuberEmotion.THINKING:
            return VTuberEmotion.THINKING, min(1.0, base_intensity + 0.1)

        return base_emotion, base_intensity

    def format_agent_speech(self, response_text: str) -> Tuple[str, str]:
        """
        Format response into (display_text, speech_text).
        """
        return self.behavior.format_responses(response_text)


# Global singleton instance
personality_manager = PersonalityManager()
