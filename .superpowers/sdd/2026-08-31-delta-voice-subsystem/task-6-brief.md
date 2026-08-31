### Task 6: CLI & Web Bridge Commands

**Files:**
- Modify: `delta/core/engine.py`
- Modify: `delta/web/bridge.py`
- Test: `tests/test_voice_cli_bridge.py`

**Interfaces:**
- Consumes: `VoiceManager`, `EngineBridge`
- Produces: CLI commands (`delta voice on/off/status/list/set/test`), Web endpoint/bridge handlers

- [ ] **Step 1: Write failing test for CLI & EngineBridge integration**

```python
# tests/test_voice_cli_bridge.py
from delta.web.bridge import EngineBridge
from delta.core.config import DeltaConfig

def test_engine_bridge_voice_status():
    cfg = DeltaConfig()
    bridge = EngineBridge(config=cfg)
    status = bridge.get_voice_status()
    assert "enabled" in status
    assert "provider" in status
    assert "profile" in status

def test_engine_bridge_set_voice_config():
    cfg = DeltaConfig()
    bridge = EngineBridge(config=cfg)
    bridge.update_voice_config(enabled=False, profile="female")
    assert cfg.tts_enabled is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_voice_cli_bridge.py -v`
Expected: FAIL with `AttributeError: 'EngineBridge' object has no attribute 'get_voice_status'`

- [ ] **Step 3: Extend `EngineBridge` and `DeltaEngine` CLI dispatcher**

In `delta/web/bridge.py`:
Add methods:
```python
def get_voice_status(self) -> Dict[str, Any]:
    return {
        "enabled": getattr(self.config, "tts_enabled", True),
        "provider": getattr(self.config, "tts_provider", "auto"),
        "profile": getattr(self.config, "tts_profile", "female"),
        "language": getattr(self.config, "tts_language", "id-ID"),
    }

def update_voice_config(self, enabled: Optional[bool] = None, profile: Optional[str] = None) -> None:
    if enabled is not None:
        self.config.tts_enabled = enabled
    if profile is not None:
        self.config.tts_profile = profile
    self.config.save()
```

In `delta/core/engine.py`:
Add `_cmd_voice(args)` handler to process `delta voice on | off | status | list | set | test`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_voice_cli_bridge.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/web/bridge.py delta/core/engine.py tests/test_voice_cli_bridge.py
git commit -m "feat(voice): integrate voice subsystem into EngineBridge and CLI commands"
```

