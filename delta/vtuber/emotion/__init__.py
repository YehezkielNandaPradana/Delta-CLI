"""
Emotion & Expression Subpackage for Delta VTuber.
"""

from delta.vtuber.emotion.schemas import (
    VTuberEmotion,
    VTuberExpression,
    EmotionResult,
    EmotionChangedEvent,
)
from delta.vtuber.emotion.rules import (
    EMOTION_TO_EXPRESSION_MAP,
    map_emotion_to_expression,
    resolve_emotion_from_event,
)
from delta.vtuber.emotion.engine import (
    EmotionEngine,
    emotion_engine,
)

__all__ = [
    "VTuberEmotion",
    "VTuberExpression",
    "EmotionResult",
    "EmotionChangedEvent",
    "EMOTION_TO_EXPRESSION_MAP",
    "map_emotion_to_expression",
    "resolve_emotion_from_event",
    "EmotionEngine",
    "emotion_engine",
]
