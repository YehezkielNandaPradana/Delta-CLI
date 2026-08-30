# tests/test_voice_models.py
from delta.voice.model import VoicePriority, SpeakingState, VoiceProfile, TTSVoice, TTSRequest, TTSChunk
from delta.core.config import DeltaConfig

def test_voice_enums_and_dataclasses():
    assert VoicePriority.CRITICAL.value == 0
    assert VoicePriority.HIGH.value == 1
    assert VoicePriority.NORMAL.value == 2
    assert VoicePriority.LOW.value == 3

    assert SpeakingState.IDLE.value == "idle"
    assert SpeakingState.SPEAKING.value == "speaking"

    p = VoiceProfile(gender="female", language="id-ID")
    assert p.gender == "female"

    v = TTSVoice(id="piper-id-female", name="Indonesian Female", language="id-ID", gender="female", provider="piper")
    assert v.gender == "female"

    req = TTSRequest(text="Hello world", priority=VoicePriority.HIGH, task_id="task-1")
    assert req.task_id == "task-1"

    c = TTSChunk(chunk_id="c1", text="text", sequence=1, total_chunks=1, priority=VoicePriority.HIGH, task_id="task-1")
    assert c.chunk_id == "c1"

def test_config_voice_fields():
    cfg = DeltaConfig()
    assert hasattr(cfg, "tts_enabled")
    assert hasattr(cfg, "tts_provider")
    assert hasattr(cfg, "tts_profile")
    assert hasattr(cfg, "tts_language")
    assert hasattr(cfg, "tts_speed")
    assert hasattr(cfg, "tts_volume")
    assert hasattr(cfg, "tts_piper_models_dir")
    assert cfg.tts_profile == "female"
    assert cfg.tts_language == "id-ID"
    assert cfg.tts_volume == 1.0
    assert cfg.tts_piper_models_dir == "~/.delta/voice/models"
