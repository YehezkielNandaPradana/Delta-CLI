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
