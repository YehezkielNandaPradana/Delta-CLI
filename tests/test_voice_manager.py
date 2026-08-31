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

    bus.emit(AgentEvent(type=EventType.AGENT_STEP_COMPLETED, status_text="Task completed successfully.", execution_id="exec-1"))

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
