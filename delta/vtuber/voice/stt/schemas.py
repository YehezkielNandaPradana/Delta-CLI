"""
Data schemas and type-safe models for Delta VTuber Speech-to-Text (STT) and Voice Input.
"""

import time
import uuid
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator


class STTState(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    ERROR = "ERROR"


class VADState(str, Enum):
    SILENCE = "SILENCE"
    SPEECH_START = "SPEECH_START"
    SPEAKING = "SPEAKING"
    SPEECH_END = "SPEECH_END"


class STTResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    is_final: bool = True
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    language: str = "id-ID"
    timestamp: float = Field(default_factory=time.time)
    duration_sec: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, v: Any) -> float:
        try:
            val = float(v)
            return max(0.0, min(1.0, val))
        except (ValueError, TypeError):
            return 1.0


class STTPartialResult(STTResult):
    is_final: bool = False


class STTFinalResult(STTResult):
    is_final: bool = True
