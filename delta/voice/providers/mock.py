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
