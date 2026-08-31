# Delta Architecture & System-Wide Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clean up codebase technical debt, unify the event bus across CLI/TUI and Web UI, reorganize directory boundaries into 5 clean modules, and stabilize autonomous pentesting capabilities.

**Architecture:** A 5-package architecture (`delta/core`, `delta/ai`, `delta/pentest`, `delta/web`, `delta/modules`). All subsystem status changes, findings, and tool logs emit through a central `AsyncEventBus` defined in `delta/core/events.py`. The Web UI bridge (`delta/web/bridge.py`) relays these events to WebSockets without separate business logic.

**Tech Stack:** Python 3.11+, Asyncio, Pydantic, FastAPI, Uvicorn, Rich/Console, Pytest.

## Global Constraints

- Preserve module compatibility: CLI commands and Web UI parameters must not break.
- No dangling backup files (`.bak`) in the tree.
- Graceful fallbacks for external security tooling (MSFRPC, Burp Suite API) when unready or offline.
- Every task includes an explicit pytest test run step.

---

### Task 1: Clean Up Technical Debt & Remove Backup Files

**Files:**
- Remove: `delta/ai/llm.py.bak`
- Remove: `delta/ai/events.py` (migrated to `delta/core/events.py`)

**Interfaces:**
- Produces: Clean tree without dead files or duplicated event definitions.

- [ ] **Step 1: Write failing test verifying absence of dead files**

```python
# tests/test_codebase_cleanliness.py
from pathlib import Path

def test_no_bak_files():
    bak_files = list(Path("delta").rglob("*.bak"))
    assert len(bak_files) == 0, f"Found backup files: {bak_files}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_codebase_cleanliness.py -v`  
Expected: FAIL (finds `delta/ai/llm.py.bak`)

- [ ] **Step 3: Remove backup file and redundant event module**

Remove `delta/ai/llm.py.bak` and remove `delta/ai/events.py` after consolidating into `delta/core/events.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_codebase_cleanliness.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_codebase_cleanliness.py
git rm delta/ai/llm.py.bak delta/ai/events.py || true
git commit -m "refactor(core): remove dead files and duplicate event modules"
```

---

### Task 2: Core Event Bus & Model Consolidation

**Files:**
- Modify: `delta/core/events.py`
- Create: `tests/test_core_events.py`

**Interfaces:**
- Produces: `AsyncEventBus` and Pydantic event models (`SystemStateEvent`, `AgentStepEvent`, `ToolExecutionEvent`, `FindingDiscoveredEvent`, `LogEvent`).

- [ ] **Step 1: Write failing test for AsyncEventBus**

```python
# tests/test_core_events.py
import pytest
import asyncio
from delta.core.events import AsyncEventBus, SystemStateEvent

@pytest.mark.asyncio
async def test_async_event_bus_pub_sub():
    bus = AsyncEventBus()
    received = []

    async def handler(event: SystemStateEvent):
        received.append(event)

    bus.subscribe(SystemStateEvent, handler)
    event = SystemStateEvent(state="RUNNING", message="Engine active")
    await bus.publish(event)

    assert len(received) == 1
    assert received[0].state == "RUNNING"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_core_events.py -v`  
Expected: FAIL (missing or incompatible `AsyncEventBus` implementation)

- [ ] **Step 3: Update `delta/core/events.py`**

Implement Pydantic event classes and the async pub-sub handler:

```python
import asyncio
from typing import Type, Callable, Dict, List, Any
from pydantic import BaseModel

class SystemStateEvent(BaseModel):
    state: str
    message: str

class AgentStepEvent(BaseModel):
    step: int
    thought: str
    action: str

class ToolExecutionEvent(BaseModel):
    tool_name: str
    args: dict
    output: str

class FindingDiscoveredEvent(BaseModel):
    title: str
    severity: str
    target: str

class LogEvent(BaseModel):
    level: str
    message: str

class AsyncEventBus:
    def __init__(self):
        self._subscribers: Dict[Type[BaseModel], List[Callable[[Any], Any]]] = {}

    def subscribe(self, event_type: Type[BaseModel], handler: Callable[[Any], Any]):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    async def publish(self, event: BaseModel):
        event_type = type(event)
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_core_events.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/core/events.py tests/test_core_events.py
git commit -m "feat(core): consolidate event models and implement AsyncEventBus"
```

---

### Task 3: Metasploit & Security Tool Fallback Stabilization

**Files:**
- Modify: `delta/pentest/metasploit.py`
- Modify: `delta/pentest/burp.py`
- Create: `tests/test_pentest_tool_fallbacks.py`

**Interfaces:**
- Consumes: `delta/core/events.py`
- Produces: `MetasploitClient` & `BurpClient` with safe `connect()` and `.is_available` methods.

- [ ] **Step 1: Write failing test for Metasploit fallback**

```python
# tests/test_pentest_tool_fallbacks.py
import pytest
from delta.pentest.metasploit import MetasploitClient
from delta.pentest.burp import BurpClient

def test_metasploit_client_offline_fallback():
    client = MetasploitClient(host="127.0.0.1", port=55553)
    connected = client.connect(password="wrong_pass")
    assert connected is False
    assert client.is_available is False

def test_burp_client_offline_fallback():
    client = BurpClient(api_url="http://127.0.0.1:9999")
    connected = client.connect()
    assert connected is False
    assert client.is_available is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_pentest_tool_fallbacks.py -v`  
Expected: FAIL (unhandled exceptions or connection errors)

- [ ] **Step 3: Update `delta/pentest/metasploit.py` and `delta/pentest/burp.py`**

Wrap RPC/HTTP connections in exception blocks and track `.is_available`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_pentest_tool_fallbacks.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/pentest/metasploit.py delta/pentest/burp.py tests/test_pentest_tool_fallbacks.py
git commit -m "fix(pentest): add graceful connection fallbacks for Metasploit and Burp Suite"
```

---

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

---

### Task 5: End-to-End System Smoke Test

**Files:**
- Create: `tests/test_e2e_refactor.py`

- [ ] **Step 1: Write failing E2E test**

```python
# tests/test_e2e_refactor.py
import pytest
from delta.core.engine import DeltaEngine

@pytest.mark.asyncio
async def test_full_engine_lifecycle():
    engine = DeltaEngine()
    await engine.initialize()
    status = await engine.get_status()
    assert status["initialized"] is True
    await engine.shutdown()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_e2e_refactor.py -v`  
Expected: FAIL

- [ ] **Step 3: Ensure `DeltaEngine` lifecycle works end-to-end**

Update `delta/core/engine.py` to coordinate session, event bus, and subsystem initialization cleanly.

- [ ] **Step 4: Run full pytest suite**

Run: `pytest -v`  
Expected: All unit & E2E tests PASS.

- [ ] **Step 5: Commit**

```bash
git add delta/core/engine.py tests/test_e2e_refactor.py
git commit -m "feat(core): implement unified DeltaEngine lifecycle and pass E2E smoke tests"
```
