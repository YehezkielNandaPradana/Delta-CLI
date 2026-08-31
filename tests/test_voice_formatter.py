from delta.voice.formatter import VoiceFormatter

def test_format_for_speech_strips_markdown_and_code():
    raw = "## Header\n`AuthService.validate()` was fixed.\n```python\ntoken.expired()\n```\nTests: 42 passed."
    clean = VoiceFormatter.format_for_speech(raw)
    assert "Header" in clean or "AuthService" in clean
    assert "```" not in clean
    assert "AuthService validate was fixed" in clean
    assert "42 passed" in clean

def test_normalize_tech_terms():
    assert "C sharp" in VoiceFormatter.format_for_speech("C#")
    assert "A P I" in VoiceFormatter.format_for_speech("API")
    assert "H T T P" in VoiceFormatter.format_for_speech("HTTP")

def test_segment_sentences():
    text = "First sentence. Second sentence! Third sentence?"
    chunks = VoiceFormatter.segment_sentences(text)
    assert len(chunks) == 3
    assert chunks[0] == "First sentence."
