"""
Renderer-agnostic data schemas and state models for Delta VTuber Avatar Runtime.
"""

import time
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator
from delta.vtuber.emotion.schemas import VTuberEmotion, VTuberExpression


class AvatarState(BaseModel):
    """
    Core renderer-agnostic representation of an avatar's visual and physical posture.
    """
    expression: VTuberExpression = VTuberExpression.NEUTRAL
    expression_intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    mouth_open: float = Field(default=0.0, ge=0.0, le=1.0)
    mouth_form: float = Field(default=0.0, ge=-1.0, le=1.0)
    head_x: float = Field(default=0.0, ge=-1.0, le=1.0)
    head_y: float = Field(default=0.0, ge=-1.0, le=1.0)
    body_angle: float = Field(default=0.0, ge=-1.0, le=1.0)
    speaking: bool = False
    timestamp: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("expression_intensity", "mouth_open", mode="before")
    @classmethod
    def clamp_0_1(cls, v: Any) -> float:
        try:
            val = float(v)
            return max(0.0, min(1.0, val))
        except (ValueError, TypeError):
            return 0.0

    @field_validator("mouth_form", "head_x", "head_y", "body_angle", mode="before")
    @classmethod
    def clamp_neg1_1(cls, v: Any) -> float:
        try:
            val = float(v)
            return max(-1.0, min(1.0, val))
        except (ValueError, TypeError):
            return 0.0

    def is_significantly_different_from(self, other: "AvatarState", threshold: float = 0.02) -> bool:
        """
        Check if state change is significant enough to warrant a re-render.
        """
        if self.expression != other.expression or self.speaking != other.speaking:
            return True

        if abs(self.expression_intensity - other.expression_intensity) > threshold:
            return True

        if abs(self.mouth_open - other.mouth_open) > threshold:
            return True

        if abs(self.mouth_form - other.mouth_form) > threshold:
            return True

        if abs(self.head_x - other.head_x) > threshold or abs(self.head_y - other.head_y) > threshold:
            return True

        if abs(self.body_angle - other.body_angle) > threshold:
            return True

        return False
