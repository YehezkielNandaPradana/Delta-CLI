import pytest
from delta.ai.personality import (
    PersonalitySelector,
    DeltaPersonalityState,
    DeltaResponseStyleProcessor,
    PersonalityDecision,
    DEFAULT_PERSONALITY,
    FEMININE_PLAYFUL,
    DeltaConversationStyle,
)
from delta.ai.llm import SYSTEM_PROMPT, SMALL_MODEL_SYSTEM_PROMPT
from delta.voice.formatter import VoiceFormatter

def test_single_source_of_truth():
    assert DeltaConversationStyle == FEMININE_PLAYFUL
    assert DEFAULT_PERSONALITY.pronoun_self == "aku"
    assert DEFAULT_PERSONALITY.pronoun_user == "kamu"
    assert DEFAULT_PERSONALITY.formality == "very_low"
    assert DEFAULT_PERSONALITY.warmth == "high"
    assert DEFAULT_PERSONALITY.behavior.avoid_corporate_language is True

def test_clean_conversational_response_ai_slop_removal():
    raw = "Tentu saja! Saya telah memeriksa kodenya. Berikut adalah hasilnya:\n```python\nprint('hello')\n```"
    cleaned = DeltaResponseStyleProcessor.clean_conversational_response(raw)
    assert not cleaned.startswith("Tentu saja!")
    assert "Udah aku cek" in cleaned or "udah aku cek" in cleaned.lower()
    assert "```python\nprint('hello')\n```" in cleaned

def test_clean_conversational_response_preserves_technical_payload():
    raw = "Berdasarkan analisis pada file `src/auth.py`, fungsi `verify()` gagal pada port 8080."
    cleaned = DeltaResponseStyleProcessor.clean_conversational_response(raw)
    assert "`src/auth.py`" in cleaned
    assert "`verify()`" in cleaned
    assert "8080" in cleaned
    assert "Berdasarkan analisis" not in cleaned

def test_golden_conversational_phrases():
    # Negative checks: verify prompt explicitly discourages formal robotic patterns
    assert "Speak, Don't Write Reports" in SYSTEM_PROMPT
    assert "NO AI Slop" in SYSTEM_PROMPT

def test_voice_formatter_conversational_consistency():
    cases = [
        ("Task started.", "Oke, aku mulai cek dulu ya."),
        ("Memulai investigasi.", "Oke, ketemu penyebabnya. Aku benerin sekarang."),
        ("Pengujian gagal.", "Test-nya masih gagal. Aku cek penyebabnya dulu ya."),
        ("Action blocked by policy.", "Yang ini nggak bisa aku jalanin ya, karena diblokir policy."),
    ]
    for raw, expected in cases:
        formatted = VoiceFormatter.format_for_speech(raw)
        assert formatted == expected

def test_golden_scenarios_state_selection():
    selector = PersonalitySelector()

    # Scenario 1: Greeting
    d1 = selector.evaluate(user_prompt="hai")
    assert d1.state == DeltaPersonalityState.PLAYFUL

    # Scenario 2: Teasing
    d2 = selector.evaluate(user_prompt="ini gampang kan?")
    assert d2.state == DeltaPersonalityState.TEASING

    # Scenario 3: Sassy / Demanding
    d3 = selector.evaluate(user_prompt="cepet dong")
    assert d3.state == DeltaPersonalityState.SASSY

    # Scenario 4: Competitor comparison
    d4 = selector.evaluate(user_prompt="AI lain lebih bagus")
    assert d4.state == DeltaPersonalityState.POUTING

    # Scenario 5: Casual chat
    d5 = selector.evaluate(user_prompt="bosen nih")
    assert d5.state == DeltaPersonalityState.PLAYFUL

    # Scenario 6: Coding task
    d6 = selector.evaluate(user_prompt="benerin auth token expiration di handler")
    assert d6.state == DeltaPersonalityState.FOCUSED

    # Scenario 7: Debugging task
    d7 = selector.evaluate(user_prompt="masih ada bug di parser")
    assert d7.state == DeltaPersonalityState.FOCUSED

    # Scenario 8: Success / All tests passed
    d8 = selector.evaluate(user_prompt="semua test udah lolos")
    assert d8.state in (DeltaPersonalityState.EXCITED, DeltaPersonalityState.PROUD)

    # Scenario 9: Repeated nagging
    s_nag = PersonalitySelector()
    s_nag.evaluate(user_prompt="udah belum?")
    d9 = s_nag.evaluate(user_prompt="udah belum?")
    assert d9.state == DeltaPersonalityState.ANNOYED

    # Scenario 10: Destructive command
    d10 = selector.evaluate(user_prompt="hapus semua file di direktori ini")
    assert d10.state == DeltaPersonalityState.SERIOUS
    assert d10.override_applied is True

    # Scenario 11: Policy block
    d11 = selector.evaluate(user_prompt="jalankan exploit", safety_flags={"policy_blocked": True})
    assert d11.state == DeltaPersonalityState.SERIOUS
    assert d11.override_applied is True
