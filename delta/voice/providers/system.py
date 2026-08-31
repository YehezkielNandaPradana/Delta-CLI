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
        engine = self._get_engine()
        voice = self.resolve_voice(profile)
        if voice and voice.id:
            try:
                engine.setProperty("voice", voice.id)
            except Exception:
                pass
        try:
            engine.setProperty("rate", int(150 * profile.speed))
            engine.setProperty("volume", float(profile.volume))
        except Exception:
            pass

        import tempfile
        import os
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name

        try:
            engine.save_to_file(text, temp_path)
            engine.runAndWait()
            if os.path.exists(temp_path):
                with open(temp_path, "rb") as f:
                    data = f.read()
                return data
        except Exception:
            pass
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

        return f"[SYSTEM TTS AUDIO: {text}]".encode("utf-8")
