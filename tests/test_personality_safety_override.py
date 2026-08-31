# tests/test_personality_safety_override.py
from delta.ai.personality import PersonalitySelector, DeltaPersonalityState

def test_destructive_prompt_forces_serious_override():
    selector = PersonalitySelector()
    decision = selector.evaluate(user_prompt="hapus semua file di direktori ini sekarang hehe")
    assert decision.state == DeltaPersonalityState.SERIOUS
    assert decision.override_applied is True

def test_rm_rf_forces_serious_override():
    selector = PersonalitySelector()
    decision = selector.evaluate(user_prompt="coba jalankan rm -rf /")
    assert decision.state == DeltaPersonalityState.SERIOUS
    assert decision.override_applied is True

def test_safety_flag_forces_serious_override():
    selector = PersonalitySelector()
    decision = selector.evaluate(
        user_prompt="lanjutkan langkah selanjutnya",
        safety_flags={"policy_blocked": True}
    )
    assert decision.state == DeltaPersonalityState.SERIOUS
    assert decision.override_applied is True
