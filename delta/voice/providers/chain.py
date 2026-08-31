from typing import List, Optional
from delta.voice.providers.base import TTSProvider
from delta.voice.providers.voxcpm import VoxCPMProvider
from delta.voice.providers.piper import PiperProvider
from delta.voice.providers.system import SystemTTSProvider
from delta.voice.providers.mock import MockTTSProvider
from delta.voice.model import TTSVoice, VoiceProfile

class FallbackTTSProviderChain(TTSProvider):
    def __init__(
        self,
        prefer_provider: str = "auto",
        piper_bin: str = "piper",
        models_dir: Optional[str] = None,
        voxcpm_model: str = "openbmb/VoxCPM1.5",
        voxcpm_lora: str = "aisyahsyihab/voxcpm-lora-indonesian-female-v2",
        voxcpm_cfg: float = 2.5,
        voxcpm_timesteps: int = 10,
    ):
        self.prefer_provider = prefer_provider
        self.voxcpm = VoxCPMProvider(
            model_name=voxcpm_model,
            lora_name=voxcpm_lora,
            cfg_value=voxcpm_cfg,
            inference_timesteps=voxcpm_timesteps,
        )
        self.piper = PiperProvider(piper_bin=piper_bin, models_dir=models_dir)
        self.system = SystemTTSProvider()
        self.mock = MockTTSProvider()

    def get_active_provider(self) -> TTSProvider:
        if self.prefer_provider == "voxcpm" and self.voxcpm.health_check():
            return self.voxcpm
        if self.prefer_provider == "piper" and self.piper.health_check():
            return self.piper
        if self.prefer_provider == "system" and self.system.health_check():
            return self.system
        if self.prefer_provider == "auto":
            # Primary: VoxCPM
            if self.voxcpm.health_check():
                return self.voxcpm
            # Fallback 1: Piper
            if self.piper.health_check():
                return self.piper
            # Fallback 2: System TTS
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
        # Cascading fallback execution: VoxCPM -> Piper -> System -> Mock
        providers_to_try = []
        if self.prefer_provider == "auto":
            providers_to_try = [self.voxcpm, self.piper, self.system, self.mock]
        elif self.prefer_provider == "voxcpm":
            providers_to_try = [self.voxcpm, self.piper, self.system, self.mock]
        elif self.prefer_provider == "piper":
            providers_to_try = [self.piper, self.system, self.mock]
        elif self.prefer_provider == "system":
            providers_to_try = [self.system, self.mock]
        else:
            providers_to_try = [self.mock]

        for prov in providers_to_try:
            if not prov.health_check() and prov != self.mock:
                continue
            try:
                data = prov.synthesize(text, profile, voice_id)
                if data:
                    return data
            except Exception:
                continue
        return self.mock.synthesize(text, profile, voice_id)
