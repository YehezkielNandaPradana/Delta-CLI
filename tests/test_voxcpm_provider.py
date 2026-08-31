import io
import wave
import pytest
from unittest.mock import MagicMock, patch
from delta.voice.providers.voxcpm import VoxCPMProvider
from delta.voice.providers.chain import FallbackTTSProviderChain
from delta.voice.model import VoiceProfile

def test_voxcpm_provider_metadata_and_voice_listing():
    provider = VoxCPMProvider(
        model_name="openbmb/VoxCPM1.5",
        lora_name="aisyahsyihab/voxcpm-lora-indonesian-female-v2",
        sample_rate=44100
    )
    voices = provider.list_voices()
    assert len(voices) == 1
    v = voices[0]
    assert v.name == "Female Indonesian Natural"
    assert v.language == "id-ID"
    assert v.gender == "female"
    assert v.provider == "voxcpm"
    assert v.metadata["lora"] == "aisyahsyihab/voxcpm-lora-indonesian-female-v2"
    assert v.metadata["sample_rate"] == 44100
    assert v.metadata["license"] == "Apache-2.0"

def test_voxcpm_provider_synthesize_mock_pipeline():
    provider = VoxCPMProvider()
    profile = VoiceProfile(language="id-ID", gender="female")
    
    mock_model = MagicMock()
    # Generate 1000 samples of mock sine/audio array
    import numpy as np
    mock_model.generate_speech.return_value = np.zeros(1000, dtype=np.float32)
    
    with patch.object(provider, "_lazy_load_model", return_value=mock_model):
        audio_bytes = provider.synthesize("Halo Delta", profile)
        assert isinstance(audio_bytes, bytes)
        assert len(audio_bytes) > 0
        
        # Verify valid WAV container and sample rate
        with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
            assert wf.getframerate() == 44100
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2

def test_voice_provider_chain_cascading_fallback():
    chain = FallbackTTSProviderChain(prefer_provider="auto")
    profile = VoiceProfile(language="id-ID", gender="female")
    
    # If VoxCPM synthesis fails, it should seamlessly fallback without crashing
    with patch.object(chain.voxcpm, "synthesize", side_effect=RuntimeError("GPU OOM")):
        with patch.object(chain.piper, "synthesize", return_value=b"piper_audio"):
            with patch.object(chain.piper, "health_check", return_value=True):
                audio = chain.synthesize("Test fallback", profile)
                assert audio == b"piper_audio"
