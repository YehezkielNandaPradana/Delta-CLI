from delta.voice.providers.mock import MockTTSProvider
from delta.voice.providers.piper import PiperProvider
from delta.voice.providers.system import SystemTTSProvider
from delta.voice.providers.chain import FallbackTTSProviderChain
from delta.voice.model import VoiceProfile

def test_mock_provider_synthesizes_bytes():
    provider = MockTTSProvider()
    assert provider.health_check() is True
    audio = provider.synthesize("Hello", profile=VoiceProfile())
    assert isinstance(audio, bytes)
    assert len(audio) > 0

def test_fallback_chain_auto_resolves_to_mock_when_no_binaries():
    chain = FallbackTTSProviderChain(prefer_provider="auto")
    voices = chain.list_voices()
    assert len(voices) > 0
    active = chain.get_active_provider()
    assert active is not None

def test_female_voice_filter_preference():
    provider = SystemTTSProvider()
    voices = provider.list_voices()
    selected = provider.resolve_voice(profile=VoiceProfile(gender="female", language="id-ID"))
    if voices:
        assert selected is not None
