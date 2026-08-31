"""
Avatar Expression Controller for Delta VTuber.
Maintains and computes expression states from EmotionChangedEvent data.
"""

from typing import Dict, Tuple
from delta.vtuber.emotion.schemas import (
    EmotionChangedEvent,
    VTuberEmotion,
    VTuberExpression,
)


class ExpressionController:
    """
    Sub-controller managing expression states and intensities.
    """

    # Comprehensive Emotion -> Expression mapping table
    EMOTION_MAP: Dict[VTuberEmotion, VTuberExpression] = {
        VTuberEmotion.NEUTRAL: VTuberExpression.NEUTRAL,
        VTuberEmotion.HAPPY: VTuberExpression.SMILE,
        VTuberEmotion.EXCITED: VTuberExpression.EXCITED,
        VTuberEmotion.CONFUSED: VTuberExpression.CONFUSED,
        VTuberEmotion.THINKING: VTuberExpression.THINKING,
        VTuberEmotion.SURPRISED: VTuberExpression.SURPRISED,
        VTuberEmotion.ANGRY: VTuberExpression.ANGRY,
        VTuberEmotion.SAD: VTuberExpression.SAD,
    }

    def __init__(self, default_expression: VTuberExpression = VTuberExpression.NEUTRAL):
        self._current_expression = default_expression
        self._current_intensity = 0.5

    @property
    def current_expression(self) -> VTuberExpression:
        return self._current_expression

    @property
    def current_intensity(self) -> float:
        return self._current_intensity

    def handle_emotion_event(self, event: EmotionChangedEvent) -> Tuple[VTuberExpression, float]:
        """
        Process an EmotionChangedEvent and update internal expression state.
        """
        expr = event.expression or self.EMOTION_MAP.get(event.emotion, VTuberExpression.NEUTRAL)
        intensity = max(0.0, min(1.0, float(event.intensity)))

        self._current_expression = expr
        self._current_intensity = intensity
        return self._current_expression, self._current_intensity

    def set_expression(self, expression: VTuberExpression, intensity: float = 0.5) -> None:
        self._current_expression = expression
        self._current_intensity = max(0.0, min(1.0, float(intensity)))

    def reset(self) -> None:
        self._current_expression = VTuberExpression.NEUTRAL
        self._current_intensity = 0.5
