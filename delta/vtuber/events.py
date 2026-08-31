"""
Structured Event Definitions & Models for Delta VTuber.
"""

import time
import uuid
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class VTuberEventType(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    TOOL_USE = "TOOL_USE"
    SPEAKING = "SPEAKING"
    RESPONSE = "RESPONSE"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


class VTuberEmotion(str, Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    EXCITED = "excited"
    CONFUSED = "confused"
    THINKING = "thinking"
    SURPRISED = "surprised"
    ANGRY = "angry"
    SAD = "sad"


class VTuberPayload(BaseModel):
    text: Optional[str] = None
    emotion: Optional[VTuberEmotion] = VTuberEmotion.NEUTRAL
    intensity: float = Field(default=1.0, ge=0.0, le=1.0)
    tool: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VTuberEvent(BaseModel):
    type: VTuberEventType
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    payload: VTuberPayload = Field(default_factory=VTuberPayload)

    @classmethod
    def create(
        cls,
        event_type: VTuberEventType,
        text: Optional[str] = None,
        emotion: Optional[VTuberEmotion] = VTuberEmotion.NEUTRAL,
        intensity: float = 1.0,
        tool: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "VTuberEvent":
        return cls(
            type=event_type,
            payload=VTuberPayload(
                text=text,
                emotion=emotion,
                intensity=intensity,
                tool=tool,
                metadata=metadata or {},
            ),
        )
