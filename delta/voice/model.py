from enum import Enum, IntEnum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

class VoicePriority(IntEnum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3

class SpeakingState(str, Enum):
    IDLE = "idle"
    QUEUED = "queued"
    SYNTHESIZING = "synthesizing"
    SPEAKING = "speaking"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"

@dataclass
class VoiceProfile:
    gender: str = "female"
    language: str = "id-ID"
    style: str = "genz_cute"
    personality: str = "cute_manja"
    formality: str = "casual"
    energy: str = "medium"
    speed: float = 0.95
    pitch: float = 0.0
    volume: float = 1.0
    pause_scale: float = 1.05

@dataclass
class TTSVoice:
    id: str
    name: str
    language: str
    gender: str
    provider: str
    path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TTSRequest:
    text: str
    priority: VoicePriority = VoicePriority.NORMAL
    task_id: Optional[str] = None
    voice_id: Optional[str] = None

@dataclass
class TTSChunk:
    chunk_id: str
    text: str
    sequence: int
    total_chunks: int
    priority: VoicePriority
    task_id: Optional[str] = None
