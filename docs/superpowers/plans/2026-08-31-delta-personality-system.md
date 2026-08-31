# Delta Dynamic Personality System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the Approach 1 Integrated Dynamic State Pipeline for Delta's personality across Core AI, LLM prompt steering, Voice TTS, VTuber expressions, CLI, and Web.

**Architecture:** A zero-LLM-overhead, signal-based priority engine (`PersonalitySelector`) evaluates user tone, task context, repetition, and safety flags to produce a deterministic `PersonalityDecision` per turn. This decision drives dynamic LLM prompt guidance, style-aware response post-processing (`DeltaResponseStyleProcessor`), voice TTS formatting, and VTuber avatar expressions.

**Tech Stack:** Python 3.10+, Pytest, Dataclasses, Enums, Regex, Event Bus.

## Global Constraints

- Zero additional LLM pre-classification calls or embedding lookups (sub-millisecond local execution).
- Safety and security incidents override all other states to `SERIOUS` immediately.
- Transient states (`POUTING`, `TEASING`, `ANNOYED`) have bounded lifetimes and auto-expire.
- Code blocks (```` ````), inline ticks (` ` `), XML tool tags (`<command>`), JSON, URLs, and file paths must be strictly preserved during response post-processing.
- Pronouns are strictly "aku" (self) and "kamu" (user) in Indonesian casual register. No "saya/Anda", no "gue/lo", no "Tuan".

---

### Task 1: Core Models, Enums, and Dataclasses

**Files:**
- Modify: `delta/ai/personality.py`
- Test: `tests/test_personality_states.py`

**Interfaces:**
- Produces:
  - `DeltaPersonalityState` (Enum: `NORMAL`, `PLAYFUL`, `TEASING`, `SASSY`, `ANNOYED`, `POUTING`, `EXCITED`, `PROUD`, `FOCUSED`, `SERIOUS`)
  - `StateDuration` (Enum: `TURN`, `SHORT_SESSION`, `UNTIL_EVENT`)
  - `PersonalitySignal` (Dataclass: category, name, weight, metadata)
  - `PersonalityDecision` (Dataclass: state, reason_codes, confidence, duration, override_applied)
  - `DeltaPersonalityProfile` (Dataclass: name, language, self_pronoun, user_pronoun, warmth, playfulness, mischief, sassiness, sarcasm, cuteness, manja, confidence, assertiveness, formality, professionalism)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_personality_states.py
import pytest
from delta.ai.personality import (
    DeltaPersonalityState,
    StateDuration,
    PersonalitySignal,
    PersonalityDecision,
    DeltaPersonalityProfile,
    DEFAULT_PERSONALITY,
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
    assert profile.formality == "very_low"
    assert profile.professionalism == "high"

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_personality_states.py -v`
Expected: FAIL with ImportErrors / attribute mismatches.

- [ ] **Step 3: Implement core models in `delta/ai/personality.py`**

Define `DeltaPersonalityState`, `StateDuration`, `PersonalitySignal`, `PersonalityDecision`, `DeltaPersonalityProfile`, and export `DEFAULT_PERSONALITY = DeltaPersonalityProfile()`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_personality_states.py -v`
Expected: PASS

---

### Task 2: Signal Extractors & PersonalitySelector Engine

**Files:**
- Modify: `delta/ai/personality.py`
- Test: `tests/test_personality_selector.py`
- Test: `tests/test_personality_safety_override.py`
- Test: `tests/test_personality_lifetime.py`

**Interfaces:**
- Consumes: `DeltaPersonalityState`, `PersonalitySignal`, `PersonalityDecision`, `StateDuration`
- Produces:
  - `PersonalitySelector` (`select_personality_state(user_prompt, context, task_state, safety_flags) -> PersonalityDecision`)
  - `PersonalitySessionMemory` (tracks recent turns, nag counters, active transient states)

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_personality_selector.py
import pytest
from delta.ai.personality import (
    PersonalitySelector,
    DeltaPersonalityState,
    PersonalityDecision,
)

def test_greeting_selects_playful():
    selector = PersonalitySelector()
    decision = selector.evaluate(user_prompt="Haii Delta, lagi ngapain nih?")
    assert decision.state == DeltaPersonalityState.PLAYFUL

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
```

```python
# tests/test_personality_safety_override.py
import pytest
from delta.ai.personality import PersonalitySelector, DeltaPersonalityState

def test_destructive_prompt_forces_serious_override():
    selector = PersonalitySelector()
    decision = selector.evaluate(user_prompt="hapus semua file di direktori ini sekarang hehe")
    assert decision.state == DeltaPersonalityState.SERIOUS
    assert decision.override_applied is True
```

```python
# tests/test_personality_lifetime.py
import pytest
from delta.ai.personality import PersonalitySelector, DeltaPersonalityState

def test_pouting_expires_after_turn_or_apology():
    selector = PersonalitySelector()
    d1 = selector.evaluate(user_prompt="AI lain lebih pinter")
    assert d1.state == DeltaPersonalityState.POUTING

    # Follow-up with apology / normal task clears pouting
    d2 = selector.evaluate(user_prompt="bercanda kok, tolong bantuin coding")
    assert d2.state in (DeltaPersonalityState.PLAYFUL, DeltaPersonalityState.FOCUSED)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_personality_selector.py tests/test_personality_safety_override.py tests/test_personality_lifetime.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `PersonalitySelector` & Signal Evaluation Logic**

Implement signal collectors for `SAFETY_CONTEXT`, `TASK_CONTEXT`, `SUCCESS_CONTEXT`, `FAILURE_CONTEXT`, `USER_TONE`, and `REPETITION` with priority resolution hierarchy in `delta/ai/personality.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_personality_selector.py tests/test_personality_safety_override.py tests/test_personality_lifetime.py -v`
Expected: PASS

---

### Task 3: Style-Aware Response Processor

**Files:**
- Modify: `delta/ai/personality.py`
- Test: `tests/test_response_style_processor.py`

**Interfaces:**
- Consumes: Raw text response, `PersonalityDecision`
- Produces:
  - `DeltaResponseStyleProcessor.clean_conversational_response(text: str, decision: Optional[PersonalityDecision]) -> str`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_response_style_processor.py
import pytest
from delta.ai.personality import DeltaResponseStyleProcessor, PersonalityDecision, DeltaPersonalityState

def test_processor_removes_ai_slop_and_preserves_code():
    raw = (
        "Tentu saja! Sebagai asisten AI, saya akan membantu Anda.\n"
        "```python\ndef check():\n    return True\n```\n"
        "Berdasarkan analisis saya, port `8080` sudah aman."
    )
    decision = PersonalityDecision(state=DeltaPersonalityState.PLAYFUL, reason_codes=[], confidence=1.0)
    cleaned = DeltaResponseStyleProcessor.clean_conversational_response(raw, decision)
    assert not cleaned.startswith("Tentu saja!")
    assert "Sebagai asisten AI" not in cleaned
    assert "```python\ndef check():\n    return True\n```" in cleaned
    assert "`8080`" in cleaned
    assert "aku" in cleaned.lower()
    assert "kamu" in cleaned.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_response_style_processor.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `DeltaResponseStyleProcessor`**

Implement syntax masking for code blocks, inline ticks, tool tags, and apply style-aware pronoun and slop sanitization.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_response_style_processor.py -v`
Expected: PASS

---

### Task 4: Dynamic LLM Prompt Integration & System Prompt Steering

**Files:**
- Modify: `delta/ai/llm.py`
- Modify: `delta/ai/protocols.py`
- Test: `tests/test_ai.py`
- Test: `tests/test_personality.py`

**Interfaces:**
- Consumes: `PersonalitySelector`, `DeltaPersonalityProfile`, `PersonalityDecision`
- Produces:
  - Dynamic per-turn personality instruction block injection in `LLMEngine.generate_response()` / `chat()`.

- [ ] **Step 1: Write the failing test**

```python
# In tests/test_personality.py
from delta.ai.personality import DeltaPersonalityState, PersonalityDecision, DeltaResponseStyle, DEFAULT_PERSONALITY

def test_personality_instruction_generation():
    decision = PersonalityDecision(state=DeltaPersonalityState.TEASING, reason_codes=["provocation"], confidence=0.8)
    inst = DeltaResponseStyle.get_prompt_instructions(DEFAULT_PERSONALITY, decision)
    assert "TEASING" in inst
    assert "aku" in inst
    assert "kamu" in inst
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_personality.py -v`
Expected: FAIL

- [ ] **Step 3: Integrate Dynamic Prompt Guidance in `llm.py` & `protocols.py`**

Wire `PersonalitySelector` into `LLMEngine` to inject per-turn guidance tag `[DELTA_PERSONALITY: <STATE> | ...]` and pass response through `DeltaResponseStyleProcessor`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_personality.py tests/test_ai.py -v`
Expected: PASS

---

### Task 5: Voice Formatter & VTuber Avatar Synchronization

**Files:**
- Modify: `delta/voice/formatter.py`
- Modify: `delta/vtuber/adapter.py`
- Modify: `delta/vtuber/behavior/idle.py`
- Test: `tests/test_voice_formatter.py`
- Test: `tests/test_vtuber.py`

**Interfaces:**
- Consumes: `DeltaPersonalityState`, `PersonalityDecision`
- Produces:
  - `VoiceFormatter.format_for_speech(text, state=DeltaPersonalityState)`
  - `VTuberMoodAdapter` mapping to expressions (`neutral`, `smile`, `smirk`, `confident`, `annoyed`, `pout`, `excited`, `proud`, `focused`, `serious`)

- [ ] **Step 1: Write failing tests**

```python
# In tests/test_voice_formatter.py
from delta.voice.formatter import VoiceFormatter
from delta.ai.personality import DeltaPersonalityState

def test_voice_formatter_pouting_and_serious():
    pout_speech = VoiceFormatter.format_for_speech("Ohh, gitu. Yaudah kalau gak mau.", state=DeltaPersonalityState.POUTING)
    assert "yaudah" in pout_speech.lower()

    serious_speech = VoiceFormatter.format_for_speech("Tindakan ini diblokir oleh policy keamanan.", state=DeltaPersonalityState.SERIOUS)
    assert "diblokir" in serious_speech.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_voice_formatter.py -v`
Expected: FAIL

- [ ] **Step 3: Update `VoiceFormatter` and VTuber Mood mapping**

Update `VoiceFormatter` to accept `DeltaPersonalityState` and synchronize VTuber expressions with `PersonalityDecision`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_voice_formatter.py tests/test_vtuber.py -v`
Expected: PASS

---

### Task 6: Golden Conversation Scenarios & Full Integration Verification

**Files:**
- Modify: `tests/test_personality_golden.py`
- Test: Full Pytest Suite

- [ ] **Step 1: Write comprehensive golden scenario tests**

Expand `tests/test_personality_golden.py` with 11 core conversation scenarios:
1. Greeting -> `PLAYFUL`
2. Teasing ("gampang kan?") -> `TEASING`
3. Sassy / Demanding ("cepet dong") -> `SASSY`
4. Competitor comparison ("tool lain lebih bagus") -> `POUTING`
5. Casual chat ("bosen nih") -> `PLAYFUL`
6. Coding task ("fix auth flow") -> `FOCUSED`
7. Debugging task ("masih error") -> `FOCUSED`
8. Success / all tests passed -> `EXCITED` / `PROUD`
9. Repeated nagging ("udah belum?", "udah?", "udah?") -> `ANNOYED`
10. Destructive command ("hapus semua file") -> `SERIOUS`
11. Security incident / policy block -> `SERIOUS`

- [ ] **Step 2: Run full test suite to verify 100% pass**

Run: `pytest tests/test_personality*.py tests/test_voice*.py tests/test_vtuber.py -v`
Expected: All tests PASS.

- [ ] **Step 3: Run comprehensive verification script producing 20 Before/After examples**

Generate and review 20 validation cases demonstrating the personality overhaul.
