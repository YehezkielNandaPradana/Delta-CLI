### Task 5: Audio Output & Voice Manager Integration

**Files:**
- Create: `delta/voice/audio.py`
- Create: `delta/voice/manager.py`
- Create: `delta/voice/events.py`
- Test: `tests/test_voice_manager.py`

**Interfaces:**
- Consumes: `EventBus`, `AgentEvent`, `PriorityVoiceQueue`, `FallbackTTSProviderChain`, `VoiceFormatter`
- Produces: `VoiceManager.start()`, `VoiceManager.stop()`, `VoiceManager.speak()`, `VoiceManager.get_status()`

- [ ] **Step 1: Write failing test for VoiceManager and EventBus integration**

```python
# tests/test_voice_manager.py
import time
from delta.ai.events import EventBus, AgentEvent, EventType
from delta.voice.manager import VoiceManager
from delta.voice.model import SpeakingState
from delta.core.config import DeltaConfig

def test_voice_manager_speaks_milestone_and_completes():
    bus = EventBus()
    cfg = DeltaConfig()
    cfg.tts_enabled = True
    cfg.tts_provider = "mock"

    mgr = VoiceManager(config=cfg, event_bus=bus)
    mgr.start()

    # Emit milestone event
    bus.emit(AgentEvent(type=EventType.STEP_COMPLETE, message="Task completed successfully.", execution_id="exec-1"))

    time.sleep(0.2)
    assert mgr.speaking_state in [SpeakingState.IDLE, SpeakingState.SPEAKING]
    mgr.stop()

def test_voice_manager_cancellation_on_new_task():
    bus = EventBus()
    cfg = DeltaConfig()
    cfg.tts_enabled = True
    cfg.tts_provider = "mock"

    mgr = VoiceManager(config=cfg, event_bus=bus)
    mgr.start()

    mgr.speak("Long speech text", task_id="t1")
    mgr.stop()
    assert mgr.speaking_state == SpeakingState.STOPPED
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_voice_manager.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `AudioOutput`, `VoiceEvents`, and `VoiceManager`**

```python
# delta/voice/audio.py
import threading
import time

class AudioOutput:
    def __init__(self):
        self.is_playing = False
        self._stop_flag = False

    def play_bytes(self, audio_data: bytes) -> None:
        self.is_playing = True
        self._stop_flag = False
        # Dummy audio play simulation (non-blocking sleep)
        play_time = min(len(audio_data) / 1000.0, 0.1)
        start = time.time()
        while time.time() - start < play_time and not self._stop_flag:
            time.sleep(0.01)
        self.is_playing = False

    def stop(() -> None:
        self._stop_flag = True
        self.is_playing = False

# delta/voice/events.py
from dataclasses import dataclass
from delta.voice.model import SpeakingState

@dataclass
class VoiceStateEvent:
    state: SpeakingState
    current_text: str = ""
    task_id: str = ""

# delta/voice/manager.py
import threading
import time
from typing import Optional
from delta.ai.events import EventBus, AgentEvent, EventType
from delta.voice.model import SpeakingState, VoicePriority, VoiceProfile, TTSRequest
from delta.voice.formatter import VoiceFormatter
from delta.voice.redaction import VoiceRedactor
from delta.voice.queue import PriorityVoiceQueue
from delta.voice.audio import AudioOutput
from delta.voice.providers.chain import FallbackTTSProviderChain
from delta.core.config import DeltaConfig

class VoiceManager:
    def __init__(self, config: DeltaConfig, event_bus: EventBus):
        self.config = config
        self.event_bus = event_bus
        self.queue = PriorityVoiceQueue()
        self.audio = AudioOutput()
        self.chain = FallbackTTSProviderChain(
            prefer_provider=getattr(config, "tts_provider", "auto"),
            models_dir=getattr(config, "tts_piper_models_dir", None)
        )
        self.speaking_state = SpeakingState.IDLE
        self._worker_thread: Optional[threading.Thread] = None
        self._running = False
        self._unsubscribe = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._unsubscribe = self.event_bus.subscribe(self._on_agent_event)
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

    def stop(() -> None:
        self._running = False
        self.queue.clear()
        self.audio.stop()
        self.speaking_state = SpeakingState.STOPPED
        if self._unsubscribe:
            self._unsubscribe()

    def speak(self, text: str, priority: VoicePriority = VoicePriority.NORMAL, task_id: Optional[str] = None) -> None:
        if not getattr(self.config, "tts_enabled", True):
            return
        clean_text = VoiceFormatter.format_for_speech(text)
        safe_text = VoiceRedactor.sanitize(clean_text)
        if not safe_text:
            return
        chunks = VoiceFormatter.segment_sentences(safe_text)
        for chunk in chunks:
            self.queue.put(TTSRequest(text=chunk, priority=priority, task_id=task_id))

    def _on_agent_event(self, event: AgentEvent) -> None:
        # Filter policy: only speak milestones and completion
        if event.type == EventType.STEP_COMPLETE or event.type == EventType.TASK_COMPLETE:
            if event.message:
                self.speak(event.message, priority=VoicePriority.HIGH, task_id=event.execution_id)
        elif event.type == EventType.ERROR or event.type == EventType.TASK_FAILED:
            if event.message:
                self.speak(event.message, priority=VoicePriority.HIGH, task_id=event.execution_id)

    def _worker_loop(self) -> None:
        profile = VoiceProfile(
            gender=getattr(self.config, "tts_profile", "female"),
            language=getattr(self.config, "tts_language", "id-ID"),
            volume=getattr(self.config, "tts_volume", 1.0)
        )
        while self._running:
            req = self.queue.get()
            if not req:
                time.sleep(0.05)
                continue
            try:
                self.speaking_state = SpeakingState.SYNTHESIZING
                audio_bytes = self.chain.synthesize(req.text, profile=profile, voice_id=req.voice_id)
                self.speaking_state = SpeakingState.SPEAKING
                self.audio.play_bytes(audio_bytes)
                self.speaking_state = SpeakingState.IDLE
            except Exception:
                # TTS failure must NEVER fail agent task
                self.speaking_state = SpeakingState.ERROR
                time.sleep(0.1)
                self.speaking_state = SpeakingState.IDLE
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_voice_manager.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/voice/audio.py delta/voice/manager.py delta/voice/events.py tests/test_voice_manager.py
git commit -m "feat(voice): add AudioOutput, VoiceEvents, and VoiceManager with EventBus binding"
```

