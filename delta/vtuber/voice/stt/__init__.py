"""
Speech-to-Text (STT) Subpackage for Delta VTuber.
"""

from delta.vtuber.voice.stt.schemas import (
    STTState,
    VADState,
    STTResult,
    STTPartialResult,
    STTFinalResult,
)
from delta.vtuber.voice.stt.provider import (
    STTProvider,
)
from delta.vtuber.voice.stt.mock import (
    MockSTTProvider,
)
from delta.vtuber.voice.stt.vad import (
    VoiceActivityDetector,
)
from delta.vtuber.voice.stt.manager import (
    STTManager,
    stt_manager,
)

__all__ = [
    "STTState",
    "VADState",
    "STTResult",
    "STTPartialResult",
    "STTFinalResult",
    "STTProvider",
    "MockSTTProvider",
    "VoiceActivityDetector",
    "STTManager",
    "stt_manager",
]
