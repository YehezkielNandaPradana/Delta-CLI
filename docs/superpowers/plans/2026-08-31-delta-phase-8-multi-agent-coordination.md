# Delta Autonomous Engineering Agent (Phase 8: Multi-Agent Coordination) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Multi-Agent Coordination Subsystem for Delta (`delta/agent/runtime/` and `delta/agent/workers/`) featuring scoped worker roles (Architect, Researcher, Coder, Tester, Debugger, Reviewer, SecurityReviewer), `ResourceLockManager` for conflict-free resource access, dynamic `TaskDAG` scheduling, `RoleContext` isolation, and an `AgentCoordinator` that replaces flat execution with an in-process async execution graph.

**Architecture:**
- **Worker Infrastructure**:
  - `delta/agent/runtime/worker.py`: `ScopedWorker` interface, `WorkerResult`, `RoleContext`, `Artifact` models.
  - `delta/agent/runtime/locks.py`: `ResourceLockManager` (async acquisition with deterministic path sorting to prevent deadlocks).
  - `delta/agent/runtime/dag.py`: `TaskDAG` (dependency graph, topological scheduling, dynamic node insertion).
  - `delta/agent/runtime/registry.py`: `WorkerRegistry` & `WorkerSelector` (matches plan steps to worker capabilities).
- **Concrete Worker Fleet** (`delta/agent/workers/`):
  - `architect.py`, `researcher.py`, `coder.py`, `tester.py`, `debugger.py`, `reviewer.py`, `security_reviewer.py`.
- **Coordinator & Integration**:
  - `delta/agent/runtime/coordinator.py`: `AgentCoordinator` orchestrating worker execution graph, budget enforcement, parallel execution via `asyncio`, failure handling, and event streaming.

**Tech Stack:** Python 3.10+, stdlib (`asyncio`, `dataclasses`, `enum`, `typing`, `time`, `pathlib`), pytest.

## Global Constraints

- Workers are NOT chatbots; communication is structured via `WorkerResult`, `RoleContext`, and `Artifact` references.
- No raw text chatter between workers. The `AgentCoordinator` controls execution flow deterministically.
- `ResourceLockManager` must sort lock keys before acquisition to prevent deadlocks.
- All workers must pass actions through `ToolRegistry` and `ExecutionPolicy` interceptors.
- Zero regression across all 364+ baseline tests.

---

### Task 1: ScopedWorker Interface, WorkerResult & RoleContext Models

**Files:**
- Create: `delta/agent/runtime/worker.py`
- Create: `delta/agent/runtime/__init__.py`
- Test: `tests/test_multi_agent_models.py`

**Interfaces:**
- Produces: `WorkerStatus` (PENDING, RUNNING, COMPLETED, FAILED, BLOCKED, CANCELLED), `WorkerResult`, `RoleContext`, `Artifact`, `ScopedWorker` ABC.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_multi_agent_models.py
from delta.agent.runtime.worker import WorkerStatus, WorkerResult, RoleContext, Artifact, ScopedWorker

class DummyWorker(ScopedWorker):
    def role(self) -> str:
        return "dummy"
    async def execute(self, context: RoleContext) -> WorkerResult:
        return WorkerResult(
            worker_id=self.role(),
            role=self.role(),
            task_id=context.task_id,
            status=WorkerStatus.COMPLETED,
            findings=["Found 1 item"]
        )

def test_worker_result_serialization():
    ctx = RoleContext(task_id="t123", objective="Test worker")
    worker = DummyWorker()
    assert worker.role() == "dummy"
```

- [ ] **Step 2: Implement minimal code**

```python
# delta/agent/runtime/worker.py
import abc
import time
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

class WorkerStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

@dataclass
class Artifact:
    id: str
    kind: str  # "research", "diff", "test_report", "security_finding", "review_report"
    data: Dict[str, Any]
    created_at: float = field(default_factory=time.time)

@dataclass
class RoleContext:
    task_id: str
    objective: str
    role: str = "main"
    step_id: Optional[str] = None
    target_files: List[str] = field(default_factory=list)
    modified_files: List[str] = field(default_factory=list)
    artifacts: Dict[str, Artifact] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkerResult:
    worker_id: str
    role: str
    task_id: str
    status: WorkerStatus
    findings: List[str] = field(default_factory=list)
    artifacts: List[Artifact] = field(default_factory=list)
    affected_files: List[str] = field(default_factory=list)
    affected_symbols: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    requested_actions: List[str] = field(default_factory=list)
    verification_status: Optional[str] = None
    error: Optional[str] = None
    duration_ms: float = 0.0

class ScopedWorker(abc.ABC):
    @abc.abstractmethod
    def role(self) -> str:
        pass

    @abc.abstractmethod
    async def execute(self, context: RoleContext) -> WorkerResult:
        pass

    def can_handle(self, context: RoleContext) -> bool:
        return True
```

```python
# delta/agent/runtime/__init__.py
from delta.agent.runtime.worker import WorkerStatus, WorkerResult, RoleContext, Artifact, ScopedWorker

__all__ = ["WorkerStatus", "WorkerResult", "RoleContext", "Artifact", "ScopedWorker"]
```

---

### Task 2: ResourceLockManager & TaskDAG Scheduler

**Files:**
- Create: `delta/agent/runtime/locks.py`
- Create: `delta/agent/runtime/dag.py`
- Test: `tests/test_locks_and_dag.py`

**Interfaces:**
- Produces: `ResourceLockManager.acquire(resource_keys)`, `ResourceLockManager.release(resource_keys)` (async deadlock-free acquisition via sorted keys).
- Produces: `TaskDAG.add_node(worker_role, deps)`, `TaskDAG.get_executable_nodes()`, `TaskDAG.mark_completed(node_id)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_locks_and_dag.py
import pytest
import asyncio
from delta.agent.runtime.locks import ResourceLockManager
from delta.agent.runtime.dag import TaskDAG

@pytest.mark.asyncio
async def test_resource_lock_manager_deadlock_free():
    mgr = ResourceLockManager()
    # Acquire sorted lock keys
    async with mgr.lock_resources(["file_b.py", "file_a.py"]):
        assert mgr.is_locked("file_a.py")
        assert mgr.is_locked("file_b.py")
    assert not mgr.is_locked("file_a.py")

def test_task_dag_scheduling():
    dag = TaskDAG()
    dag.add_node("architect", deps=[])
    dag.add_node("researcher", deps=["architect"])
    dag.add_node("coder", deps=["researcher"])

    ready = dag.get_executable_nodes()
    assert ready == ["architect"]

    dag.mark_completed("architect")
    ready_2 = dag.get_executable_nodes()
    assert ready_2 == ["researcher"]
```

- [ ] **Step 2: Implement minimal code**

```python
# delta/agent/runtime/locks.py
import asyncio
from typing import List, Dict, Set
from contextlib import asynccontextmanager

class ResourceLockManager:
    def __init__(self):
        self._locks: Dict[str, asyncio.Lock] = {}
        self._global_guard = asyncio.Lock()

    def _get_lock(self, key: str) -> asyncio.Lock:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    def is_locked(self, key: str) -> bool:
        if key not in self._locks:
            return False
        return self._locks[key].locked()

    @asynccontextmanager
    async def lock_resources(self, resource_keys: List[str]):
        # Sort resource keys deterministically to avoid deadlocks
        sorted_keys = sorted(list(set(resource_keys)))
        acquired = []
        try:
            for key in sorted_keys:
                lock = self._get_lock(key)
                await lock.acquire()
                acquired.append(lock)
            yield
        finally:
            for lock in reversed(acquired):
                lock.release()
```

```python
# delta/agent/runtime/dag.py
from typing import List, Dict, Set

class TaskDAG:
    def __init__(self):
        self.nodes: Set[str] = set()
        self.deps: Dict[str, Set[str]] = {}
        self.completed: Set[str] = set()
        self.running: Set[str] = set()
        self.failed: Set[str] = set()

    def add_node(self, node_id: str, deps: List[str] = None):
        self.nodes.add(node_id)
        self.deps[node_id] = set(deps or [])

    def get_executable_nodes(self) -> List[str]:
        executable = []
        for node in self.nodes:
            if node in self.completed or node in self.running or node in self.failed:
                continue
            node_deps = self.deps.get(node, set())
            if node_deps.issubset(self.completed):
                executable.append(node)
        return sorted(executable)

    def mark_running(self, node_id: str):
        self.running.add(node_id)

    def mark_completed(self, node_id: str):
        if node_id in self.running:
            self.running.remove(node_id)
        self.completed.add(node_id)

    def mark_failed(self, node_id: str):
        if node_id in self.running:
            self.running.remove(node_id)
        self.failed.add(node_id)

    def is_finished(self) -> bool:
        return (len(self.completed) + len(self.failed)) == len(self.nodes)
```

---

### Task 3: Worker Registry & Concrete Scoped Workers

**Files:**
- Create: `delta/agent/runtime/registry.py`
- Create: `delta/agent/workers/__init__.py`
- Create: `delta/agent/workers/architect.py`
- Create: `delta/agent/workers/researcher.py`
- Create: `delta/agent/workers/coder.py`
- Create: `delta/agent/workers/tester.py`
- Create: `delta/agent/workers/debugger.py`
- Create: `delta/agent/workers/reviewer.py`
- Create: `delta/agent/workers/security_reviewer.py`
- Test: `tests/test_workers_fleet.py`

**Interfaces:**
- Produces: `WorkerRegistry`, `WorkerSelector`, concrete worker implementations wrapping Phase 1-7 engines.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_workers_fleet.py
import pytest
from delta.agent.runtime.registry import WorkerRegistry, WorkerSelector
from delta.agent.workers.architect import ArchitectWorker
from delta.agent.workers.coder import CoderWorker

def test_worker_registry_and_selector():
    registry = WorkerRegistry()
    registry.register(ArchitectWorker())
    registry.register(CoderWorker())

    selector = WorkerSelector(registry)
    worker = selector.select_worker_for_role("coder")
    assert worker is not None
    assert worker.role() == "coder"
```

- [ ] **Step 2: Implement minimal worker fleet**

Implement `WorkerRegistry`, `WorkerSelector`, and wrapping worker classes: `ArchitectWorker`, `ResearcherWorker`, `CoderWorker`, `TesterWorker`, `DebuggerWorker`, `ReviewerWorker`, and `SecurityReviewerWorker`.

---

### Task 4: AgentCoordinator & Multi-Agent Integration

**Files:**
- Create: `delta/agent/runtime/coordinator.py`
- Test: `tests/test_agent_coordinator.py`

**Interfaces:**
- Produces: `AgentCoordinator(workspace_root)`.
- Method: `async run_task_graph(objective, target_files, dag) -> Dict[str, WorkerResult]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_agent_coordinator.py
import pytest
from delta.agent.runtime.coordinator import AgentCoordinator
from delta.agent.runtime.dag import TaskDAG

@pytest.mark.asyncio
async def test_coordinator_runs_dag_pipeline():
    coord = AgentCoordinator()
    dag = TaskDAG()
    dag.add_node("architect", deps=[])
    dag.add_node("researcher", deps=["architect"])
    dag.add_node("coder", deps=["researcher"])
    dag.add_node("tester", deps=["coder"])
    dag.add_node("reviewer", deps=["tester"])

    results = await coord.run_task_graph(
        objective="Fix token expiry handling",
        target_files=["delta/core/auth.py"],
        dag=dag
    )

    assert "architect" in results
    assert "coder" in results
    assert "reviewer" in results
    assert results["reviewer"].status.value == "completed"
```

- [ ] **Step 2: Implement minimal coordinator**

Implement `AgentCoordinator` with async concurrent execution of unblocked nodes using `asyncio.gather()`, context passing via `RoleContext`, resource locking, budget management, and result aggregation.
