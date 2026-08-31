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
            models_dir=getattr(config, "tts_piper_models_dir", None),
            voxcpm_model=getattr(config, "tts_voxcpm_model", "openbmb/VoxCPM1.5"),
            voxcpm_lora=getattr(config, "tts_voxcpm_lora", "aisyahsyihab/voxcpm-lora-indonesian-female-v2"),
            voxcpm_cfg=getattr(config, "tts_voxcpm_cfg", 2.5),
            voxcpm_timesteps=getattr(config, "tts_voxcpm_timesteps", 10),
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

    def stop(self) -> None:
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
        msg = event.status_text or event.content or (event.payload.get("message") if isinstance(event.payload, dict) else None)
        if not msg and event.error:
            msg = str(event.error)

        if event.type in (EventType.AGENT_STEP_COMPLETED, EventType.TASK_COMPLETED, EventType.AGENT_COMPLETE):
            if msg:
                self.speak(msg, priority=VoicePriority.HIGH, task_id=event.execution_id or event.task_id)
        elif event.type in (EventType.ERROR, EventType.TASK_FAILED, EventType.AGENT_STEP_FAILED):
            if msg:
                self.speak(msg, priority=VoicePriority.HIGH, task_id=event.execution_id or event.task_id)

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
