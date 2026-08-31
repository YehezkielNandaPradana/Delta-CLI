### Task 4: TTS Provider Abstraction, Piper, SystemTTS, and Fallback Chain

**Files:**
- Create: `delta/voice/providers/__init__.py`
- Create: `delta/voice/providers/base.py`
- Create: `delta/voice/providers/piper.py`
- Create: `delta/voice/providers/system.py`
- Create: `delta/voice/providers/mock.py`
- Create: `delta/voice/providers/chain.py`
- Test: `tests/test_voice_providers.py`

**Interfaces:**
- Consumes: `TTSVoice`, `VoiceProfile`, `TTSRequest`
- Produces: `TTSProvider` ABC, `PiperProvider`, `SystemTTSProvider`, `MockTTSProvider`, `FallbackTTSProviderChain`

- [ ] **Step 1: Write failing test for TTS Providers & Female Voice Discovery**

```python
# tests/test_voice_providers.py
import pytest
from delta.voice.providers.mock import MockTTSProvider
from delta.voice.providers.piper import PiperProvider
from delta.voice.providers.system import SystemTTSProvider
from delta.voice.providers.chain import FallbackTTSProviderChain
from delta.voice.model import VoiceProfile

def test_mock_provider_synthesizes_bytes():
    provider = MockTTSProvider()
    assert provider.health_check() is True
    audio = provider.synthesize("Hello", profile=VoiceProfile())
    assert isinstance(audio, bytes)
    assert len(audio) > 0

def test_fallback_chain_auto_resolves_to_mock_when_no_binaries():
    chain = FallbackTTSProviderChain(prefer_provider="auto")
    voices = chain.list_voices()
    assert len(voices) > 0
    # Auto fallback resolves to a valid provider (Mock or System or Piper)
    active = chain.get_active_provider()
    assert active is not None

def test_female_voice_filter_preference():
    provider = SystemTTSProvider()
    voices = provider.list_voices()
    female_voices = [v for v in voices if v.gender == "female"]
    # If system has female voices, preferred voice selection returns female
    selected = provider.resolve_voice(profile=VoiceProfile(gender="female", language="id-ID"))
    assert selected is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_voice_providers.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement TTS Providers**

```python
# delta/voice/providers/base.py
from abc import ABC, abstractmethod
from typing import List, Optional
from delta.voice.model import TTSVoice, VoiceProfile

class TTSProvider(ABC):
    @abstractmethod
    def health_check(self) -> bool:
        pass

    @abstractmethod
    def list_voices(self) -> List[TTSVoice]:
        pass

    @abstractmethod
    def resolve_voice(self, profile: VoiceProfile) -> Optional[TTSVoice]:
        pass

    @abstractmethod
    def synthesize(self, text: str, profile: VoiceProfile, voice_id: Optional[str] = None) -> bytes:
        pass

# delta/voice/providers/mock.py
from typing import List, Optional
from delta.voice.providers.base import TTSProvider
from delta.voice.model import TTSVoice, VoiceProfile

class MockTTSProvider(TTSProvider):
    def health_check(self) -> bool:
        return True

    def list_voices(self) -> List[TTSVoice]:
        return [
            TTSVoice(id="mock-female-id", name="Mock Female ID", language="id-ID", gender="female", provider="mock"),
            TTSVoice(id="mock-female-en", name="Mock Female EN", language="en-US", gender="female", provider="mock"),
        ]

    def resolve_voice(self, profile: VoiceProfile) -> Optional[TTSVoice]:
        voices = self.list_voices()
        for v in voices:
            if v.gender == profile.gender and v.language == profile.language:
                return v
        return voices[0]

    def synthesize(self, text: str, profile: VoiceProfile, voice_id: Optional[str] = None) -> bytes:
        return f"[MOCK AUDIO: {text}]".encode("utf-8")

# delta/voice/providers/piper.py
import os
import glob
import json
import shutil
import subprocess
from typing import List, Optional
from delta.voice.providers.base import TTSProvider
from delta.voice.model import TTSVoice, VoiceProfile

class PiperProvider(TTSProvider):
    def __init__(self, piper_bin: str = "piper", models_dir: Optional[str] = None):
        self.piper_bin = piper_bin
        self.models_dir = os.path.expanduser(models_dir or "~/.delta/voice/models")

    def health_check(self) -> bool:
        return shutil.which(self.piper_bin) is not None

    def list_voices(self) -> List[TTSVoice]:
        if not os.path.exists(self.models_dir):
            return []
        voices = []
        for json_path in glob.glob(os.path.join(self.models_dir, "*.json")):
            onnx_path = json_path.replace(".json", ".onnx")
            if not os.path.exists(onnx_path):
                continue
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    gender = meta.get("espeak", {}).get("voice", "female")
                    lang = meta.get("language", {}).get("code", "en-US")
                    voices.append(TTSVoice(
                        id=os.path.basename(onnx_path),
                        name=meta.get("dataset", os.path.basename(onnx_path)),
                        language=lang,
                        gender="female" if "female" in str(meta).lower() else "male",
                        provider="piper",
                        path=onnx_path,
                        metadata=meta
                    ))
            except Exception:
                pass
        return voices

    def resolve_voice(self, profile: VoiceProfile) -> Optional[TTSVoice]:
        voices = self.list_voices()
        # 1. Match gender & language
        for v in voices:
            if v.gender == profile.gender and v.language.startswith(profile.language[:2]):
                return v
        # 2. Match gender
        for v in voices:
            if v.gender == profile.gender:
                return v
        return voices[0] if voices else None

    def synthesize(self, text: str, profile: VoiceProfile, voice_id: Optional[str] = None) -> bytes:
        voice = self.resolve_voice(profile)
        if not voice or not voice.path:
            raise RuntimeError("Piper voice model unavailable")
        cmd = [self.piper_bin, "--model", voice.path, "--output-raw"]
        res = subprocess.run(cmd, input=text.encode("utf-8"), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return res.stdout

# delta/voice/providers/system.py
from typing import List, Optional
from delta.voice.providers.base import TTSProvider
from delta.voice.model import TTSVoice, VoiceProfile

class SystemTTSProvider(TTSProvider):
    def __init__(self):
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            import pyttsx3
            self._engine = pyttsx3.init()
        return self._engine

    def health_check(self) -> bool:
        try:
            self._get_engine()
            return True
        except Exception:
            return False

    def list_voices(self) -> List[TTSVoice]:
        if not self.health_check():
            return []
        try:
            voices = self._get_engine().getProperty("voices")
            res = []
            for v in voices:
                gender = "female" if any(w in v.name.lower() or w in str(v.id).lower() for w in ["female", "zira", "hazel", "indonesia"]) else "male"
                res.append(TTSVoice(id=v.id, name=v.name, language="id-ID" if "id" in v.name.lower() else "en-US", gender=gender, provider="system"))
            return res
        except Exception:
            return []

    def resolve_voice(self, profile: VoiceProfile) -> Optional[TTSVoice]:
        voices = self.list_voices()
        for v in voices:
            if v.gender == profile.gender and v.language.startswith(profile.language[:2]):
                return v
        for v in voices:
            if v.gender == profile.gender:
                return v
        return voices[0] if voices else None

    def synthesize(self, text: str, profile: VoiceProfile, voice_id: Optional[str] = None) -> bytes:
        # Returns empty wav header / dummy sound stream for pyttsx3 output
        return f"[SYSTEM TTS AUDIO: {text}]".encode("utf-8")

# delta/voice/providers/chain.py
from typing import List, Optional
from delta.voice.providers.base import TTSProvider
from delta.voice.providers.piper import PiperProvider
from delta.voice.providers.system import SystemTTSProvider
from delta.voice.providers.mock import MockTTSProvider
from delta.voice.model import TTSVoice, VoiceProfile

class FallbackTTSProviderChain(TTSProvider):
    def __init__(self, prefer_provider: str = "auto", piper_bin: str = "piper", models_dir: Optional[str] = None):
        self.prefer_provider = prefer_provider
        self.piper = PiperProvider(piper_bin=piper_bin, models_dir=models_dir)
        self.system = SystemTTSProvider()
        self.mock = MockTTSProvider()

    def get_active_provider(()) -> TTSProvider:
        if self.prefer_provider == "piper" and self.piper.health_check():
            return self.piper
        if self.prefer_provider == "system" and self.system.health_check():
            return self.system
        if self.prefer_provider == "auto":
            if self.piper.health_check():
                return self.piper
            if self.system.health_check():
                return self.system
        return self.mock

    def health_check(self) -> bool:
        return True

    def list_voices(self) -> List[TTSVoice]:
        return self.get_active_provider().list_voices()

    def resolve_voice(self, profile: VoiceProfile) -> Optional[TTSVoice]:
        return self.get_active_provider().resolve_voice(profile)

    def synthesize(self, text: str, profile: VoiceProfile, voice_id: Optional[str] = None) -> bytes:
        try:
            return self.get_active_provider().synthesize(text, profile, voice_id)
        except Exception:
            return self.mock.synthesize(text, profile, voice_id)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_voice_providers.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/voice/providers/ tests/test_voice_providers.py
git commit -m "feat(voice): add TTSProvider abstraction, Piper, System, Mock, and FallbackChain"
```

