"""
Voice and Speech Synthesis Subpackage for Delta VTuber.
"""

from delta.vtuber.voice.schemas import (
    SpeechState,
    SpeechLifecycleEventType,
    SpeechLifecycleEvent,
    SpeechChunk,
    AudioData,
)
from delta.vtuber.voice.sentence_chunker import (
    SentenceChunker,
)
from delta.vtuber.voice.tts import (
    TTSProvider,
    MockTTSProvider,
)
from delta.vtuber.voice.edge_tts_provider import (
    EdgeTTSProvider,
)
from delta.vtuber.voice.audio import (
    AudioPlayer,
    MockAudioPlayer,
)
from delta.vtuber.voice.browser_player import (
    BrowserAudioPlayer,
    browser_audio_player,
)
from delta.vtuber.voice.speech_manager import (
    SpeechManager,
)

from delta.vtuber.voice.stt import (
    STTState,
    VADState,
    STTResult,
    STTPartialResult,
    STTFinalResult,
    STTProvider,
    MockSTTProvider,
    VoiceActivityDetector,
    STTManager,
    stt_manager,
)

from delta.vtuber.voice.prosody import (
    ProsodyProfile,
    EMOTION_PROSODY_DEFAULTS,
    ProsodyModulator,
    ProsodyController,
    prosody_controller,
)

__all__ = [
    "SpeechState",
    "SpeechLifecycleEventType",
    "SpeechLifecycleEvent",
    "SpeechChunk",
    "AudioData",
    "SentenceChunker",
    "TTSProvider",
    "MockTTSProvider",
    "EdgeTTSProvider",
    "AudioPlayer",
    "MockAudioPlayer",
    "BrowserAudioPlayer",
    "browser_audio_player",
    "SpeechManager",
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
    "ProsodyProfile",
    "EMOTION_PROSODY_DEFAULTS",
    "ProsodyModulator",
    "ProsodyController",
    "prosody_controller",
]
