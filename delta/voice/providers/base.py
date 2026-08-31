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
