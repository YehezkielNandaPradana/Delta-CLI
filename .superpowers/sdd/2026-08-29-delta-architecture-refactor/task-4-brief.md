### Task 4: Web UI Server & WebSocket Bridge Integration

**Files:**
- Modify: `delta/web/server.py`
- Modify: `delta/web/bridge.py`
- Create: `tests/test_web_bridge.py`

**Interfaces:**
- Consumes: `delta/core/events.py` (`AsyncEventBus`)
- Produces: FastAPI WebSocket `/ws` endpoint broadcasting serialized event streams.

- [ ] **Step 1: Write failing test for WebSocket event bridge**

```python
# tests/test_web_bridge.py
import pytest
from fastapi.testclient import TestClient
from delta.web.server import app
from delta.core.events import AsyncEventBus, LogEvent
from delta.web.bridge import WebBridge

def test_websocket_bridge_relay():
    bus = AsyncEventBus()
    bridge = WebBridge(bus)
    client = TestClient(app)
    
    with client.websocket_connect("/ws") as websocket:
        bus.publish_nowait(LogEvent(level="INFO", message="Web socket test"))
        # Receive serialized event over websocket
        data = websocket.receive_json()
        assert data["type"] == "LogEvent"
        assert data["data"]["message"] == "Web socket test"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_web_bridge.py -v`  
Expected: FAIL (WebSocket endpoint not found or event formatting mismatch)

- [ ] **Step 3: Implement WebBridge and WebSocket relay in `delta/web/bridge.py` & `delta/web/server.py`**

Wire `WebBridge` to subscribe to `AsyncEventBus` and push JSON payloads to active WebSocket client connections.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_web_bridge.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/web/server.py delta/web/bridge.py tests/test_web_bridge.py
git commit -m "feat(web): wire AsyncEventBus to WebSocket server bridge"
```
