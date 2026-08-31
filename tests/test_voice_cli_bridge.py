from delta.web.bridge import EngineBridge
from delta.core.config import DeltaConfig

def test_engine_bridge_voice_status():
    cfg = DeltaConfig()
    bridge = EngineBridge()
    bridge.engine = type("DummyEngine", (), {"config": cfg})()
    status = bridge.get_voice_status()
    assert "enabled" in status
    assert "provider" in status
    assert "profile" in status

def test_engine_bridge_set_voice_config():
    cfg = DeltaConfig()
    bridge = EngineBridge()
    bridge.engine = type("DummyEngine", (), {"config": cfg})()
    bridge.update_voice_config(enabled=False, profile="female")
    assert cfg.tts_enabled is False
