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
