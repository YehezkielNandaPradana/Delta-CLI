### Task 2: Voice Formatter & Secret Redactor Integration

**Files:**
- Create: `delta/voice/formatter.py`
- Create: `delta/voice/redaction.py`
- Test: `tests/test_voice_formatter.py`
- Test: `tests/test_voice_redaction.py`

**Interfaces:**
- Consumes: `delta/voice/model.py` (`TTSRequest`, `TTSChunk`)
- Produces: `VoiceFormatter.format_for_speech()`, `VoiceFormatter.segment_sentences()`, `VoiceRedactor.sanitize()`

- [ ] **Step 1: Write failing test for VoiceFormatter and VoiceRedactor**

```python
# tests/test_voice_formatter.py
from delta.voice.formatter import VoiceFormatter

def test_format_for_speech_strips_markdown_and_code():
    raw = "## Header\n`AuthService.validate()` was fixed.\n```python\ntoken.expired()\n```\nTests: 42 passed."
    clean = VoiceFormatter.format_for_speech(raw)
    assert "Header" not in clean or "Result" not in clean
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

# tests/test_voice_redaction.py
from delta.voice.redaction import VoiceRedactor

def test_voice_redaction_masks_api_keys():
    text = "Found key sk-proj-1234567890abcdef1234567890 inside config."
    clean = VoiceRedactor.sanitize(text)
    assert "sk-proj" not in clean
    assert "[REDACTED]" in clean or "REDACTED" in clean
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_voice_formatter.py tests/test_voice_redaction.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `VoiceFormatter` and `VoiceRedactor`**

```python
# delta/voice/formatter.py
import re
from typing import List

class VoiceFormatter:
    @staticmethod
    def format_for_speech(text: str) -> str:
        # Strip markdown code blocks
        text = re.sub(r"```[\s\S]*?```", "", text)
        # Strip inline code ticks
        text = re.sub(r"`([^`]+)`", r"\1", text)
        # Remove headers #
        text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
        # Remove bold/italic * _
        text = re.sub(r"[\*_]{1,3}", "", text)
        # Normalize code identifiers like AuthService.validate() -> AuthService validate
        text = re.sub(r"(\w+)\.(\w+)\(\)", r"\1 \2", text)
        # Technical acronym normalization
        tech_map = {
            r"\bC#\b": "C sharp",
            r"\bAPI\b": "A P I",
            r"\bHTTP\b": "H T T P",
            r"\bHTTPS\b": "H T T P S",
            r"\bNPM\b": "N P M",
            r"\bCLI\b": "C L I",
            r"\bURL\b": "U R L",
        }
        for pattern, replacement in tech_map.items():
            text = re.sub(pattern, replacement, text)
        # Clean extra whitespace
        text = re.sub(r"\n+", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def segment_sentences(text: str) -> List[str]:
        if not text:
            return []
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

# delta/voice/redaction.py
import re

class VoiceRedactor:
    SECRET_PATTERNS = [
        r"sk-[a-zA-Z0-9]{20,}",
        r"ghp_[a-zA-Z0-9]{36}",
        r"(?:api_key|password|secret|token)\s*=\s*['\"]?([a-zA-Z0-9_\-\.\=\+]{8,})['\"]?",
    ]

    @classmethod
    def sanitize(cls, text: str) -> str:
        clean = text
        for pattern in cls.SECRET_PATTERNS:
            clean = re.sub(pattern, "[REDACTED SECRET]", clean, flags=re.IGNORECASE)
        return clean
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_voice_formatter.py tests/test_voice_redaction.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/voice/formatter.py delta/voice/redaction.py tests/test_voice_formatter.py tests/test_voice_redaction.py
git commit -m "feat(voice): add VoiceFormatter and VoiceRedactor"
```

