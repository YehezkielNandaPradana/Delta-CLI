"""
Speech Prosody Data Schemas and Modulation Models for Delta VTuber Voice.
"""

from enum import Enum
from typing import Any, Dict
from pydantic import BaseModel, Field, field_validator
from delta.vtuber.emotion.schemas import VTuberEmotion


class ProsodyProfile(BaseModel):
    """
    Audio pitch, speech rate, volume, and pause adjustments for emotional voice synthesis.
    """
    emotion: VTuberEmotion = VTuberEmotion.NEUTRAL
    rate_multiplier: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch_offset_hz: float = Field(default=0.0, ge=-50.0, le=50.0)
    volume_multiplier: float = Field(default=1.0, ge=0.0, le=2.0)
    pause_factor: float = Field(default=1.0, ge=0.5, le=2.0)
    rate_ssml: str = "+0%"
    pitch_ssml: str = "+0Hz"
    volume_ssml: str = "+0%"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("rate_multiplier", "volume_multiplier", "pause_factor", mode="before")
    @classmethod
    def clamp_multiplier(cls, v: Any) -> float:
        try:
            return max(0.5, min(2.0, float(v)))
        except (ValueError, TypeError):
            return 1.0


# Emotion -> Default Prosody Mapping Table
EMOTION_PROSODY_DEFAULTS: Dict[VTuberEmotion, Dict[str, Any]] = {
    VTuberEmotion.NEUTRAL: {
        "rate": 1.0, "pitch_hz": 0.0, "rate_ssml": "+0%", "pitch_ssml": "+0Hz"
    },
    VTuberEmotion.HAPPY: {
        "rate": 1.05, "pitch_hz": 4.0, "rate_ssml": "+5%", "pitch_ssml": "+4Hz"
    },
    VTuberEmotion.EXCITED: {
        "rate": 1.12, "pitch_hz": 8.0, "rate_ssml": "+12%", "pitch_ssml": "+8Hz"
    },
    VTuberEmotion.THINKING: {
        "rate": 0.94, "pitch_hz": -2.0, "rate_ssml": "-6%", "pitch_ssml": "-2Hz"
    },
    VTuberEmotion.CONFUSED: {
        "rate": 0.98, "pitch_hz": 3.0, "rate_ssml": "-2%", "pitch_ssml": "+3Hz"
    },
    VTuberEmotion.SURPRISED: {
        "rate": 1.08, "pitch_hz": 7.0, "rate_ssml": "+8%", "pitch_ssml": "+7Hz"
    },
    VTuberEmotion.SAD: {
        "rate": 0.88, "pitch_hz": -6.0, "rate_ssml": "-12%", "pitch_ssml": "-6Hz"
    },
    VTuberEmotion.ANGRY: {
        "rate": 1.08, "pitch_hz": -3.0, "rate_ssml": "+8%", "pitch_ssml": "-3Hz"
    },
}
