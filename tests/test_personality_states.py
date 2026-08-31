# tests/test_personality_states.py
import pytest
from delta.ai.personality import (
    DeltaPersonalityState,
    StateDuration,
    PersonalitySignal,
    PersonalityDecision,
    DeltaPersonalityProfile,
    DEFAULT_PERSONALITY,
    FEMININE_PLAYFUL,
)

def test_personality_states_enum():
    expected_states = {
        "NORMAL", "PLAYFUL", "TEASING", "SASSY", "ANNOYED",
        "POUTING", "EXCITED", "PROUD", "FOCUSED", "SERIOUS"
    }
    actual_states = {s.value for s in DeltaPersonalityState}
    assert actual_states == expected_states

def test_state_duration_enum():
    assert StateDuration.TURN.value == "turn"
    assert StateDuration.SHORT_SESSION.value == "short_session"
    assert StateDuration.UNTIL_EVENT.value == "until_event"

def test_personality_profile_defaults():
    profile = DEFAULT_PERSONALITY
    assert profile.name == "feminine_playful"
    assert profile.self_pronoun == "aku"
    assert profile.user_pronoun == "kamu"
    assert profile.warmth == "high"
    assert profile.playfulness == "high"
    assert profile.mischief == "high"
    assert profile.sassiness == "medium_high"
    assert profile.sarcasm == "medium"
    assert profile.formality == "very_low"
    assert profile.professionalism == "high"
    assert DEFAULT_PERSONALITY == FEMININE_PLAYFUL

def test_personality_decision_structure():
    decision = PersonalityDecision(
        state=DeltaPersonalityState.PLAYFUL,
        reason_codes=["greeting"],
        confidence=0.9,
        duration=StateDuration.TURN,
        override_applied=False,
    )
    assert decision.state == DeltaPersonalityState.PLAYFUL
    assert decision.confidence == 0.9
    assert decision.to_dict()["state"] == "PLAYFUL"
