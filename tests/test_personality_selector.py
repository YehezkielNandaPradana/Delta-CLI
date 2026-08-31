# tests/test_personality_selector.py
from delta.ai.personality import (
    PersonalitySelector,
    DeltaPersonalityState,
    PersonalitySignal,
)

def test_greeting_selects_playful():
    selector = PersonalitySelector()
    decision = selector.evaluate(user_prompt="Haii Delta, lagi ngapain nih?")
    assert decision.state == DeltaPersonalityState.PLAYFUL
    assert "casual_greeting" in decision.reason_codes or "warm_playful" in decision.reason_codes

def test_casual_teasing_provocation():
    selector = PersonalitySelector()
    decision = selector.evaluate(user_prompt="ini gampang kan?")
    assert decision.state == DeltaPersonalityState.TEASING

def test_active_coding_selects_focused():
    selector = PersonalitySelector()
    decision = selector.evaluate(
        user_prompt="benerin auth token expiration di src/auth.py",
        task_context={"active_mode": "coding"}
    )
    assert decision.state == DeltaPersonalityState.FOCUSED

def test_competitor_comparison_selects_pouting():
    selector = PersonalitySelector()
    decision = selector.evaluate(user_prompt="ah Claude lebih bagus dari kamu")
    assert decision.state == DeltaPersonalityState.POUTING

def test_praise_selects_proud():
    selector = PersonalitySelector()
    decision = selector.evaluate(user_prompt="Wah kamu pinter banget ya!")
    assert decision.state == DeltaPersonalityState.PROUD

def test_insult_selects_sassy():
    selector = PersonalitySelector()
    decision = selector.evaluate(user_prompt="kamu bodoh banget")
    assert decision.state == DeltaPersonalityState.SASSY

def test_signals_generation():
    sig = PersonalitySignal(category="USER_TONE", name="test_signal", weight=0.8)
    assert sig.category == "USER_TONE"
    assert sig.weight == 0.8
