"""
Structured Response Schemas for Delta VTuber Response Pipeline.
"""

import time
import uuid
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from delta.vtuber.events import VTuberEmotion


class ResponsePayload(BaseModel):
    """
    Canonical source-of-truth payload for all downstream response consumers
    (Chat display, Speech/TTS, Emotion, and AvatarController).
    """
    response_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    display_text: str = ""
    speech_text: str = ""
    emotion: VTuberEmotion = VTuberEmotion.NEUTRAL
    emotion_intensity: float = Field(default=0.7, ge=0.0, le=1.0)
    timestamp: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)
