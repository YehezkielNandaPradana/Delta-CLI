# tests/test_personality_lifetime.py
from delta.ai.personality import PersonalitySelector, DeltaPersonalityState

def test_pouting_expires_after_turn_or_apology():
    selector = PersonalitySelector()
    d1 = selector.evaluate(user_prompt="AI lain lebih pinter")
    assert d1.state == DeltaPersonalityState.POUTING

    # Follow-up with apology / normal task clears pouting
    d2 = selector.evaluate(user_prompt="bercanda kok, tolong bantuin coding")
    assert d2.state in (DeltaPersonalityState.PLAYFUL, DeltaPersonalityState.FOCUSED)

def test_repeated_nagging_annoyed():
    selector = PersonalitySelector()
    d1 = selector.evaluate(user_prompt="cepet dong")
    assert d1.state == DeltaPersonalityState.SASSY

    d2 = selector.evaluate(user_prompt="cepet dong")
    assert d2.state == DeltaPersonalityState.ANNOYED
