from delta.ai.personality import (
    DeltaPersonalityProfile,
    DeltaPersonalityState,
    PersonalityDecision,
    FEMININE_PLAYFUL,
    DEFAULT_PERSONALITY,
    DeltaResponseStyle,
)
from delta.voice.formatter import VoiceFormatter

def test_personality_profile_defaults():
    assert FEMININE_PLAYFUL.name == "feminine_playful"
    assert FEMININE_PLAYFUL.language == "id-ID"
    assert FEMININE_PLAYFUL.formality in ("low", "very_low")
    assert FEMININE_PLAYFUL.warmth == "high"
    assert FEMININE_PLAYFUL.playfulness == "high"
    assert FEMININE_PLAYFUL.mischief == "high"
    assert FEMININE_PLAYFUL.sassiness == "medium_high"
    assert FEMININE_PLAYFUL.assertiveness == "high"
    assert DEFAULT_PERSONALITY == FEMININE_PLAYFUL

def test_delta_response_style_helper():
    profile = DeltaResponseStyle.get_profile()
    assert profile.name == "feminine_playful"
    decision = PersonalityDecision(state=DeltaPersonalityState.TEASING, reason_codes=["test"], confidence=0.8)
    instructions = DeltaResponseStyle.get_prompt_instructions(profile, decision)
    assert "TEASING" in instructions
    assert "aku" in instructions
    assert "kamu" in instructions

def test_voice_formatter_feminine_playful():
    speech = VoiceFormatter.format_for_speech("Saya akan mulai menganalisis tugas ini.", state=DeltaPersonalityState.PLAYFUL)
    assert "aku" in speech.lower()
    assert "tuan" not in speech.lower()

    done_speech = VoiceFormatter.format_for_speech("Task completed successfully. All tests passed.", state=DeltaPersonalityState.EXCITED)
    assert "udah beres" in done_speech.lower() or "semua test" in done_speech.lower()
