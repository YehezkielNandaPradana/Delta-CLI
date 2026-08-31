"""
Local Expression Intelligence & Dynamics Engine for Delta VTuber.
Fuses EmotionEngine, MoodState, PresenceState, and SpeechState into smooth, lifelike facial expressions.
"""

from typing import Dict, Tuple
from delta.vtuber.avatar.schemas import AvatarState
from delta.vtuber.emotion.schemas import VTuberEmotion, VTuberExpression
from delta.vtuber.personality.schemas import MoodState
from delta.vtuber.presence.schemas import PresenceActivity, PresenceState


class ExpressionIntensityModulator:
    """
    Computes bounded, smooth expression intensity modulated by persistent character mood & presence.
    """

    @classmethod
    def modulate_intensity(
        cls,
        base_intensity: float,
        mood: MoodState,
        presence: PresenceState,
        expression: VTuberExpression,
    ) -> float:
        clamped_base = max(0.0, min(1.0, float(base_intensity)))

        # Mood modifiers
        mood_multiplier = 1.0
        if expression == VTuberExpression.SMILE or expression == VTuberExpression.EXCITED:
            mood_multiplier += (mood.happiness - 0.5) * 0.4 + (mood.confidence - 0.5) * 0.2
        elif expression == VTuberExpression.CONFUSED or expression == VTuberExpression.SAD:
            mood_multiplier += (mood.stress - 0.3) * 0.5
        elif expression == VTuberExpression.THINKING:
            mood_multiplier += (mood.curiosity - 0.5) * 0.3

        # Presence attention modifier
        presence_multiplier = 0.8 + 0.4 * presence.attention_level

        final_intensity = clamped_base * mood_multiplier * presence_multiplier
        return round(max(0.0, min(1.0, final_intensity)), 3)


class ExpressionTransitionController:
    """
    Smoothes expression state transitions to avoid sudden jumps.
    """

    def __init__(self, smoothing_factor: float = 0.15):
        self.smoothing_factor = smoothing_factor
        self._current_smoothed_intensity: float = 0.5

    def step(self, target_intensity: float) -> float:
        self._current_smoothed_intensity += (target_intensity - self._current_smoothed_intensity) * self.smoothing_factor
        return round(self._current_smoothed_intensity, 3)


class ExpressionDynamics:
    """
    Master expression dynamics coordinator.
    """

    def __init__(self):
        self.modulator = ExpressionIntensityModulator()
        self.transition = ExpressionTransitionController()

    def resolve_dynamic_expression(
        self,
        base_expression: VTuberExpression,
        base_intensity: float,
        mood: MoodState,
        presence: PresenceState,
    ) -> Tuple[VTuberExpression, float]:
        target_intensity = self.modulator.modulate_intensity(
            base_intensity=base_intensity,
            mood=mood,
            presence=presence,
            expression=base_expression,
        )
        smoothed = self.transition.step(target_intensity)
        return base_expression, smoothed
