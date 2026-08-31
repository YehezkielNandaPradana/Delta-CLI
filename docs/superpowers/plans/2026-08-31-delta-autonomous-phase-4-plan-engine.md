# Delta Autonomous Engineering Agent (Phase 4: Structured Plan Engine & Tool Runtime Integration) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Structured Plan Engine (Plan, PlanStep, StepStatus, dynamic re-planning, rollbacks) and integrate all tool categories into a Unified Tool Runtime for Delta.

**Architecture:** Implement `delta/agent/planner/` containing `PlanStep`, `Plan`, `PlanEngine` (synthesizes structured plans, updates step status, handles dynamic step insertion/re-planning after failures), and `delta/tools/` exposing unified tool adapters (Filesystem, Code, Execution, Git, Security).

**Tech Stack:** Python 3.10+, stdlib (`dataclasses`, `enum`, `typing`, `json`, `uuid`, `time`), pytest.

## Global Constraints

- Plans are structured objects, not plain strings.
- Dynamic re-planning can add new steps after diagnostic failures or mark steps as rolled back.
- Zero regression across all 364 existing tests.

---

### Task 1: Plan Dataclasses and Step Lifecycle Models

**Files:**
- Create: `delta/agent/planner/model.py`
- Create: `delta/agent/planner/__init__.py`
- Test: `tests/test_plan_model.py`

**Interfaces:**
- Produces: `StepStatus` (PENDING, RUNNING, COMPLETED, FAILED, SKIPPED, ROLLED_BACK), `PlanStep`, `Plan`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_plan_model.py
from delta.agent.planner.model import Plan, PlanStep, StepStatus

def test_plan_step_lifecycle():
    step = PlanStep(
        id="step_1",
        description="Inspect auth/token.py",
        assigned_role="researcher",
        dependencies=[],
        target_files=["auth/token.py"]
    )
    assert step.status == StepStatus.PENDING
    step.status = StepStatus.COMPLETED
    assert step.status.value == "completed"

def test_plan_serialization():
    step1 = PlanStep(id="1", description="Locate bug", assigned_role="researcher")
    step2 = PlanStep(id="2", description="Fix bug", assigned_role="coder", dependencies=["1"])
    plan = Plan(
        task_id="task_001",
        objective="Fix auth bug",
        constraints=["Do not break token API"],
        steps=[step1, step2]
    )
    d = plan.to_dict()
    assert d["task_id"] == "task_001"
    assert len(d["steps"]) == 2
    assert d["steps"][1]["dependencies"] == ["1"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_plan_model.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'delta.agent.planner'`

- [ ] **Step 3: Write minimal implementation**

```python
# delta/agent/planner/model.py
import time
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"

@dataclass
class PlanStep:
    id: str
    description: str
    assigned_role: str = "main"
    dependencies: List[str] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    target_files: List[str] = field(default_factory=list)
    verification_command: Optional[str] = None
    rollback_strategy: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d

@dataclass
class Plan:
    task_id: str
    objective: str
    constraints: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    steps: List[PlanStep] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["steps"] = [s.to_dict() for s in self.steps]
        return d
```

```python
# delta/agent/planner/__init__.py
from delta.agent.planner.model import StepStatus, PlanStep, Plan

__all__ = ["StepStatus", "PlanStep", "Plan"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_plan_model.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/agent/planner/model.py delta/agent/planner/__init__.py tests/test_plan_model.py
git commit -m "feat(planner): implement StepStatus, PlanStep, and Plan dataclasses"
```

---

### Task 2: PlanEngine and Dynamic Re-planning

**Files:**
- Create: `delta/agent/planner/engine.py`
- Test: `tests/test_plan_engine.py`

**Interfaces:**
- Produces: `PlanEngine(task_id, objective)`, `create_plan(steps_def) -> Plan`, `mark_step_completed(step_id)`, `insert_step_after(step_id, new_step)`, `mark_step_failed(step_id, error_reason)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_plan_engine.py
from delta.agent.planner.engine import PlanEngine
from delta.agent.planner.model import StepStatus

def test_plan_engine_lifecycle_and_replanning():
    engine = PlanEngine(task_id="task_abc", objective="Fix token validation")
    plan = engine.create_plan([
        {"id": "1", "description": "Locate auth file", "role": "researcher"},
        {"id": "2", "description": "Patch token validation", "role": "coder", "deps": ["1"]}
    ])
    assert len(plan.steps) == 2
    assert plan.steps[0].status == StepStatus.PENDING

    # Advance step 1
    engine.start_step("1")
    assert plan.steps[0].status == StepStatus.RUNNING

    engine.complete_step("1")
    assert plan.steps[0].status == StepStatus.COMPLETED

    # Dynamic re-planning after diagnostic discovery
    engine.insert_step_after(
        after_step_id="1",
        new_step_def={"id": "1b", "description": "Verify token structure with AST parser", "role": "debugger"}
    )
    assert len(plan.steps) == 3
    assert plan.steps[1].id == "1b"
    assert plan.steps[2].dependencies == ["1b"] # Dependency updated dynamically
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_plan_engine.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'delta.agent.planner.engine'`

- [ ] **Step 3: Write minimal implementation**

```python
# delta/agent/planner/engine.py
import time
from typing import List, Dict, Any, Optional
from delta.agent.planner.model import Plan, PlanStep, StepStatus

class PlanEngine:
    def __init__(self, task_id: str, objective: str):
        self.task_id = task_id
        self.objective = objective
        self.plan: Optional[Plan] = None

    def create_plan(self, steps_def: List[Dict[str, Any]], constraints: List[str] = None) -> Plan:
        steps = []
        for s in steps_def:
            steps.append(PlanStep(
                id=s["id"],
                description=s["description"],
                assigned_role=s.get("role", "main"),
                dependencies=s.get("deps", []),
                target_files=s.get("target_files", [])
            ))
        self.plan = Plan(
            task_id=self.task_id,
            objective=self.objective,
            constraints=constraints or [],
            steps=steps
        )
        return self.plan

    def get_step(self, step_id: str) -> Optional[PlanStep]:
        if not self.plan:
            return None
        return next((s for s in self.plan.steps if s.id == step_id), None)

    def start_step(self, step_id: str):
        step = self.get_step(step_id)
        if step:
            step.status = StepStatus.RUNNING
            self.plan.updated_at = time.time()

    def complete_step(self, step_id: str):
        step = self.get_step(step_id)
        if step:
            step.status = StepStatus.COMPLETED
            self.plan.updated_at = time.time()

    def fail_step(self, step_id: str, reason: str = ""):
        step = self.get_step(step_id)
        if step:
            step.status = StepStatus.FAILED
            step.metadata["error"] = reason
            self.plan.updated_at = time.time()

    def insert_step_after(self, after_step_id: str, new_step_def: Dict[str, Any]) -> PlanStep:
        if not self.plan:
            raise ValueError("No active plan to insert step into")

        idx = next((i for i, s in enumerate(self.plan.steps) if s.id == after_step_id), -1)
        if idx == -1:
            raise ValueError(f"Step {after_step_id} not found in plan")

        new_step = PlanStep(
            id=new_step_def["id"],
            description=new_step_def["description"],
            assigned_role=new_step_def.get("role", "main"),
            dependencies=[after_step_id],
            target_files=new_step_def.get("target_files", [])
        )

        # Update downstream dependencies
        for s in self.plan.steps[idx + 1:]:
            if after_step_id in s.dependencies:
                s.dependencies.remove(after_step_id)
                s.dependencies.append(new_step.id)

        self.plan.steps.insert(idx + 1, new_step)
        self.plan.updated_at = time.time()
        return new_step
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_plan_engine.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/agent/planner/engine.py tests/test_plan_engine.py
git commit -m "feat(planner): implement PlanEngine with dynamic re-planning and step lifecycle transitions"
```
