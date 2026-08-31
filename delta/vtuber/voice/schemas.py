"""
Data schemas and models for Delta VTuber Voice and Speech system.
"""

import time
import uuid
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from delta.vtuber.events import VTuberEmotion


class SpeechState(str, Enum):
    IDLE = "IDLE"
    QUEUED = "QUEUED"
    SYNTHESIZING = "SYNTHESIZING"
    PLAYING = "PLAYING"
    FINISHED = "FINISHED"
    INTERRUPTED = "INTERRUPTED"
    ERROR = "ERROR"


class SpeechLifecycleEventType(str, Enum):
    SPEECH_QUEUED = "SPEECH_QUEUED"
    SPEECH_STARTED = "SPEECH_STARTED"
    SPEECH_SYNTHESIZED = "SPEECH_SYNTHESIZED"
    SPEECH_PLAYING = "SPEECH_PLAYING"
    SPEECH_FINISHED = "SPEECH_FINISHED"
    SPEECH_INTERRUPTED = "SPEECH_INTERRUPTED"
    SPEECH_ERROR = "SPEECH_ERROR"


class SpeechChunk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    speech_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sequence: int = 0
    text: str
    emotion: VTuberEmotion = VTuberEmotion.NEUTRAL
    intensity: float = 1.0
    created_at: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AudioData(BaseModel):
    chunk_id: str
    speech_id: str = ""
    sequence: int = 0
    audio_bytes: bytes = b""
    sample_rate: int = 24000
    format: str = "mp3"
    duration_sec: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SpeechLifecycleEvent(BaseModel):
    event_type: SpeechLifecycleEventType
    speech_id: Optional[str] = None
    chunk_id: Optional[str] = None
    sequence: int = 0
    text: Optional[str] = None
    state: SpeechState = SpeechState.IDLE
    timestamp: float = Field(default_factory=time.time)
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
