# tests/test_response_style_processor.py
from delta.ai.personality import DeltaResponseStyleProcessor, PersonalityDecision, DeltaPersonalityState

def test_processor_removes_ai_slop_and_preserves_code():
    raw = (
        "Tentu saja! Sebagai asisten AI, saya akan membantu Anda.\n"
        "```python\ndef check():\n    return True\n```\n"
        "Berdasarkan analisis saya, port `8080` sudah aman.\n"
        "<command>scan localhost</command>"
    )
    decision = PersonalityDecision(state=DeltaPersonalityState.PLAYFUL, reason_codes=[], confidence=1.0)
    cleaned = DeltaResponseStyleProcessor.clean_conversational_response(raw, decision)
    assert not cleaned.startswith("Tentu saja!")
    assert "Sebagai asisten AI" not in cleaned
    assert "```python\ndef check():\n    return True\n```" in cleaned
    assert "`8080`" in cleaned
    assert "<command>scan localhost</command>" in cleaned
    assert "aku" in cleaned.lower()
    assert "kamu" in cleaned.lower()
