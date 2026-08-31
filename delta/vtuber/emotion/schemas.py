"""
Data Schemas and Type-Safe Models for Delta VTuber Emotion & Expression System.
"""

import time
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator


class VTuberEmotion(str, Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    EXCITED = "excited"
    CONFUSED = "confused"
    THINKING = "thinking"
    SURPRISED = "surprised"
    ANGRY = "angry"
    SAD = "sad"


class VTuberExpression(str, Enum):
    NEUTRAL = "neutral"
    SMILE = "smile"
    EXCITED = "excited"
    THINKING = "thinking"
    CONFUSED = "confused"
    SURPRISED = "surprised"
    SAD = "sad"
    ANGRY = "angry"


class EmotionResult(BaseModel):
    emotion: VTuberEmotion = VTuberEmotion.NEUTRAL
    intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    expression: VTuberExpression = VTuberExpression.NEUTRAL
    timestamp: float = Field(default_factory=time.time)
    source_event: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("intensity", mode="before")
    @classmethod
    def clamp_intensity(cls, v: Any) -> float:
        try:
            val = float(v)
            return max(0.0, min(1.0, val))
        except (ValueError, TypeError):
            return 0.5


class EmotionChangedEvent(BaseModel):
    type: str = "emotion_changed"
    emotion: VTuberEmotion = VTuberEmotion.NEUTRAL
    intensity: float = 0.5
    expression: VTuberExpression = VTuberExpression.NEUTRAL
    previous_emotion: Optional[VTuberEmotion] = None
    timestamp: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)
