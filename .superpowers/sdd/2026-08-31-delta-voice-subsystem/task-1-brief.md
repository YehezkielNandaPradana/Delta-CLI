### Task 1: Voice Data Models and Config Extensions

**Files:**
- Create: `delta/voice/__init__.py`
- Create: `delta/voice/model.py`
- Modify: `delta/core/config.py`
- Test: `tests/test_voice_models.py`

**Interfaces:**
- Consumes: `delta/core/config.py` (`DeltaConfig`)
- Produces: `VoicePriority`, `SpeakingState`, `VoiceProfile`, `TTSVoice`, `TTSRequest`, `TTSChunk`, `DeltaConfig.tts_*` settings

- [ ] **Step 1: Write failing test for models and config extension**

```python
# tests/test_voice_models.py
from delta.voice.model import VoicePriority, SpeakingState, VoiceProfile, TTSVoice, TTSRequest, TTSChunk
from delta.core.config import DeltaConfig

def test_voice_enums_and_dataclasses():
    assert VoicePriority.CRITICAL.value == 0
    assert VoicePriority.HIGH.value == 1
    assert VoicePriority.NORMAL.value == 2
    assert VoicePriority.LOW.value == 3

    assert SpeakingState.IDLE.value == "idle"
    assert SpeakingState.SPEAKING.value == "speaking"

    v = TTSVoice(id="piper-id-female", name="Indonesian Female", language="id-ID", gender="female", provider="piper")
    assert v.gender == "female"

    req = TTSRequest(text="Hello world", priority=VoicePriority.HIGH, task_id="task-1")
    assert req.task_id == "task-1"

def test_config_voice_fields():
    cfg = DeltaConfig()
    assert hasattr(cfg, "tts_enabled")
    assert hasattr(cfg, "tts_provider")
    assert hasattr(cfg, "tts_profile")
    assert hasattr(cfg, "tts_language")
    assert hasattr(cfg, "tts_speed")
    assert hasattr(cfg, "tts_volume")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_voice_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'delta.voice'`

- [ ] **Step 3: Implement `delta/voice/model.py` and extend `DeltaConfig`**

```python
# delta/voice/model.py
from enum import Enum, IntEnum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

class VoicePriority(IntEnum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3

class SpeakingState(str, Enum):
    IDLE = "idle"
    QUEUED = "queued"
    SYNTHESIZING = "synthesizing"
    SPEAKING = "speaking"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"

@dataclass
class VoiceProfile:
    gender: str = "female"
    language: str = "id-ID"
    speed: float = 1.0
    pitch: float = 0.0
    volume: float = 1.0

@dataclass
class TTSVoice:
    id: str
    name: str
    language: str
    gender: str
    provider: str
    path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TTSRequest:
    text: str
    priority: VoicePriority = VoicePriority.NORMAL
    task_id: Optional[str] = None
    voice_id: Optional[str] = None

@dataclass
class TTSChunk:
    chunk_id: str
    text: str
    sequence: int
    total_chunks: int
    priority: VoicePriority
    task_id: Optional[str] = None
```

In `delta/core/config.py`:
Add default fields:
`tts_profile: str = "female"`
`tts_language: str = "id-ID"`
`tts_volume: float = 1.0`
`tts_piper_models_dir: str = "~/.delta/voice/models"`

In `delta/voice/__init__.py`:
Export `VoicePriority`, `SpeakingState`, `VoiceProfile`, `TTSVoice`, `TTSRequest`, `TTSChunk`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_voice_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/voice/__init__.py delta/voice/model.py delta/core/config.py tests/test_voice_models.py
git commit -m "feat(voice): add voice models, enums and config extensions"
```

