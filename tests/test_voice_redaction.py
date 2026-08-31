from delta.voice.redaction import VoiceRedactor

def test_voice_redaction_masks_api_keys():
    text = "Found key sk-proj-1234567890abcdef1234567890 inside config."
    clean = VoiceRedactor.sanitize(text)
    assert "sk-proj" not in clean
    assert "[REDACTED SECRET]" in clean or "REDACTED" in clean
