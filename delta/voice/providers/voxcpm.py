"""VoxCPM TTS Provider with LoRA Indonesian Female v2 support.

Base model: openbmb/VoxCPM1.5
LoRA fine-tune: aisyahsyihab/voxcpm-lora-indonesian-female-v2
Native Sample Rate: 44100 Hz (44.1 kHz)
"""
import io
import os
import wave
import logging
from typing import List, Optional, Any, Dict
from delta.voice.providers.base import TTSProvider
from delta.voice.model import TTSVoice, VoiceProfile

logger = logging.getLogger(__name__)

class VoxCPMProvider(TTSProvider):
    def __init__(
        self,
        model_name: str = "openbmb/VoxCPM1.5",
        lora_name: str = "aisyahsyihab/voxcpm-lora-indonesian-female-v2",
        cfg_value: float = 2.5,
        inference_timesteps: int = 10,
        sample_rate: int = 44100,
        device: Optional[str] = None,
    ):
        self.model_name = model_name
        self.lora_name = lora_name
        self.cfg_value = cfg_value
        self.inference_timesteps = inference_timesteps
        self.sample_rate = sample_rate
        self.device = device or self._detect_device()
        self._model: Optional[Any] = None
        self._is_loading = False

    def _detect_device(self) -> str:
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
        except Exception:
            pass
        return "cpu"

    def _lazy_load_model(self) -> Any:
        if self._model is not None:
            return self._model
        
        try:
            self._is_loading = True
            # Attempt loading VoxCPM via transformers / official voxcpm package
            try:
                import voxcpm
                model = voxcpm.load_model(
                    self.model_name,
                    lora=self.lora_name,
                    device=self.device,
                )
                self._model = model
                return self._model
            except ImportError:
                pass

            # Fallback to general HF transformers pipeline if voxcpm direct module is not installed
            from transformers import AutoModelForCausalLM, AutoTokenizer
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                device_map=self.device,
                trust_remote_code=True,
            )
            if hasattr(model, "load_adapter"):
                model.load_adapter(self.lora_name)
            self._model = model
            return self._model
        except Exception as exc:
            logger.warning(f"Failed to load VoxCPM model: {exc}")
            raise RuntimeError(f"VoxCPM model unavailable: {exc}") from exc
        finally:
            self._is_loading = False

    def health_check(self) -> bool:
        # Provider is considered available if torch is present or voxcpm module exists
        try:
            import torch
            return True
        except ImportError:
            return False

    def list_voices(self) -> List[TTSVoice]:
        return [
            TTSVoice(
                id="voxcpm-id-female-v2",
                name="Female Indonesian Natural",
                language="id-ID",
                gender="female",
                provider="voxcpm",
                metadata={
                    "model": self.model_name,
                    "lora": self.lora_name,
                    "sample_rate": self.sample_rate,
                    "device": self.device,
                    "license": "Apache-2.0",
                }
            )
        ]

    def resolve_voice(self, profile: VoiceProfile) -> Optional[TTSVoice]:
        voices = self.list_voices()
        return voices[0] if voices else None

    def synthesize(self, text: str, profile: VoiceProfile, voice_id: Optional[str] = None) -> bytes:
        if not text or not text.strip():
            return b""

        model = self._lazy_load_model()
        
        # Synthesize audio with model
        try:
            if hasattr(model, "generate_speech"):
                audio_array = model.generate_speech(
                    text=text,
                    cfg_value=self.cfg_value,
                    inference_timesteps=self.inference_timesteps,
                )
            elif hasattr(model, "generate_audio"):
                audio_array = model.generate_audio(text)
            else:
                # Custom callable mock or pipeline
                audio_array = model(text)

            # Convert numpy/tensor to 44.1kHz WAV bytes
            return self._to_wav_bytes(audio_array, sample_rate=self.sample_rate)
        except Exception as exc:
            logger.error(f"VoxCPM synthesis error: {exc}")
            raise RuntimeError(f"Synthesis failed: {exc}") from exc

    def _to_wav_bytes(self, audio_data: Any, sample_rate: int = 44100) -> bytes:
        import numpy as np
        if hasattr(audio_data, "cpu"):
            audio_data = audio_data.cpu().numpy()
        if not isinstance(audio_data, np.ndarray):
            audio_data = np.array(audio_data, dtype=np.float32)

        # Normalize to 16-bit PCM
        if audio_data.dtype in (np.float32, np.float64):
            audio_data = np.clip(audio_data, -1.0, 1.0)
            audio_data = (audio_data * 32767).astype(np.int16)

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        return buffer.getvalue()

    def unload(self) -> None:
        self._model = None
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
