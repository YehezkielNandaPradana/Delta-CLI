# Delta Autonomous Engineering Agent (Phase 8.5: End-to-End Integration & Autonomy Validation) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate all Phase 1-8 subsystems into ONE unified, persistent autonomous engineering runtime. Implement `TaskCompletionEvaluator`, state machine transition validation in `AgentLifecycle`, dynamic DAG scheduling, end-to-end event emission, crash recovery, and realistic integration test fixtures.

**Architecture:**
- `delta/agent/runtime/completion.py`: `TaskCompletionEvaluator` & `CompletionDecision` (verifies objective, plan criteria, test verification, review status, and persistent state before allowing `FINISHED`).
- `delta/agent/runtime/lifecycle.py`: `AgentLifecycleEngine` (enforces strict state machine: `OBSERVE -> UNDERSTAND -> PLAN -> EXECUTE -> VERIFY -> REVIEW -> REFLECT -> FINISH` with recovery paths).
- `delta/agent/runtime/pipeline.py`: `AutonomousPipeline` (wraps end-to-end task execution: Task creation, Repo intelligence, ContextEngine L0-L7, PlanEngine, AgentCoordinator, VerifierEngine, DebuggerEngine, ReviewerEngine, TaskCompletionEvaluator).
- `tests/fixtures/`: Synthetic deterministic test repositories (`fixture_bug`, `fixture_review_reject`, `fixture_security`).

**Tech Stack:** Python 3.10+, stdlib (`asyncio`, `dataclasses`, `enum`, `typing`, `time`, `pathlib`, `shutil`), pytest.

## Global Constraints

- A task CANNOT be marked `FINISHED` without passing `TaskCompletionEvaluator` (objective, verification, zero regression, review approved, state saved).
- Policy and budget boundaries are strictly enforced across all steps.
- All existing 364+ baseline tests must pass with zero regression.

---

### Task 1: TaskCompletionEvaluator & State Machine Integration

**Files:**
- Create: `delta/agent/runtime/completion.py`
- Create: `delta/agent/runtime/lifecycle.py`
- Test: `tests/test_task_completion_evaluator.py`

**Interfaces:**
- Produces: `CompletionDecision` (eligible, reasons, failed_criteria, unresolved_findings, verification_state, review_state).
- Produces: `TaskCompletionEvaluator.evaluate(task_state, plan, verifier_report, review_report) -> CompletionDecision`.
- Produces: `AgentLifecycleEngine` enforcing valid transitions: `OBSERVE -> UNDERSTAND -> PLAN -> EXECUTE -> VERIFY -> REVIEW -> REFLECT -> FINISH`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_task_completion_evaluator.py
from delta.agent.state.task_state import TaskState
from delta.agent.planner.model import Plan, PlanStep, StepStatus
from delta.agent.verifier.engine import ExtendedRegressionReport
from delta.agent.reviewer.model import ReviewReport, ReviewStatus
from delta.agent.runtime.completion import TaskCompletionEvaluator, CompletionDecision
from delta.agent.runtime.lifecycle import AgentLifecycleEngine, LifecycleState

def test_task_completion_evaluator_rejects_unverified_task():
    state = TaskState(task_id="t1", goal="Fix bug")
    plan = Plan(task_id="t1", objective="Fix bug")
    ver_report = ExtendedRegressionReport(has_regression=True, new_failures=["test_auth"])
    rev_report = ReviewReport(status=ReviewStatus.REJECT)

    evaluator = TaskCompletionEvaluator()
    dec = evaluator.evaluate(state, plan, ver_report, rev_report)
    assert dec.eligible is False
    assert len(dec.unresolved_findings) >= 1

def test_lifecycle_state_machine_validates_transitions():
    lifecycle = AgentLifecycleEngine()
    assert lifecycle.current_state == LifecycleState.OBSERVE
    
    # Valid transition: OBSERVE -> UNDERSTAND
    lifecycle.transition(LifecycleState.UNDERSTAND)
    assert lifecycle.current_state == LifecycleState.UNDERSTAND

    # Invalid transition: UNDERSTAND -> FINISH directly (Blocked)
    assert lifecycle.can_transition(LifecycleState.FINISH) is False
```

- [ ] **Step 2: Implement minimal code**

```python
# delta/agent/runtime/completion.py
from dataclasses import dataclass, field
from typing import List, Optional
from delta.agent.state.task_state import TaskState
from delta.agent.planner.model import Plan, StepStatus
from delta.agent.verifier.engine import ExtendedRegressionReport
from delta.agent.reviewer.model import ReviewReport, ReviewStatus

@dataclass
class CompletionDecision:
    eligible: bool
    reasons: List[str] = field(default_factory=list)
    failed_criteria: List[str] = field(default_factory=list)
    unresolved_findings: List[str] = field(default_factory=list)
    verification_state: str = "unverified"
    review_state: str = "unreviewed"

class TaskCompletionEvaluator:
    def evaluate(
        self,
        task_state: TaskState,
        plan: Optional[Plan],
        verifier_report: Optional[ExtendedRegressionReport],
        review_report: Optional[ReviewReport]
    ) -> CompletionDecision:
        reasons = []
        failed_criteria = []
        unresolved = []
        eligible = True

        # 1. Check Plan criteria
        if not plan:
            eligible = False
            failed_criteria.append("No active execution plan found")
        else:
            incomplete_steps = [s.id for s in plan.steps if s.status != StepStatus.COMPLETED]
            if incomplete_steps:
                eligible = False
                failed_criteria.append(f"Incomplete plan steps: {', '.join(incomplete_steps)}")

        # 2. Check Verifier
        ver_state = "unverified"
        if not verifier_report:
            eligible = False
            unresolved.append("No verification run performed")
        elif verifier_report.has_regression:
            eligible = False
            ver_state = "regression_detected"
            unresolved.append(f"Regressed tests: {', '.join(verifier_report.new_failures)}")
        else:
            ver_state = "passed"

        # 3. Check Reviewer
        rev_state = "unreviewed"
        if not review_report:
            eligible = False
            unresolved.append("No self-review performed")
        elif review_report.status not in [ReviewStatus.PASS, ReviewStatus.PASS_WITH_WARNINGS]:
            eligible = False
            rev_state = review_report.status.value
            for act in review_report.required_actions:
                unresolved.append(f"Review action required: {act}")
        else:
            rev_state = review_report.status.value

        if eligible:
            reasons.append("All plan steps completed, verification passed, and self-review approved.")

        return CompletionDecision(
            eligible=eligible,
            reasons=reasons,
            failed_criteria=failed_criteria,
            unresolved_findings=unresolved,
            verification_state=ver_state,
            review_state=rev_state
        )
```

```python
# delta/agent/runtime/lifecycle.py
from enum import Enum
from typing import Set, Dict, List

class LifecycleState(str, Enum):
    OBSERVE = "OBSERVE"
    UNDERSTAND = "UNDERSTAND"
    PLAN = "PLAN"
    EXECUTE = "EXECUTE"
    VERIFY = "VERIFY"
    DEBUG = "DEBUG"
    REVIEW = "REVIEW"
    REFLECT = "REFLECT"
    FINISH = "FINISH"
    FAILED = "FAILED"

class AgentLifecycleEngine:
    VALID_TRANSITIONS: Dict[LifecycleState, Set[LifecycleState]] = {
        LifecycleState.OBSERVE: {LifecycleState.UNDERSTAND, LifecycleState.FAILED},
        LifecycleState.UNDERSTAND: {LifecycleState.PLAN, LifecycleState.FAILED},
        LifecycleState.PLAN: {LifecycleState.EXECUTE, LifecycleState.FAILED},
        LifecycleState.EXECUTE: {LifecycleState.VERIFY, LifecycleState.FAILED},
        LifecycleState.VERIFY: {LifecycleState.REVIEW, LifecycleState.DEBUG, LifecycleState.FAILED},
        LifecycleState.DEBUG: {LifecycleState.PLAN, LifecycleState.EXECUTE, LifecycleState.FAILED},
        LifecycleState.REVIEW: {LifecycleState.REFLECT, LifecycleState.PLAN, LifecycleState.FAILED},
        LifecycleState.REFLECT: {LifecycleState.FINISH, LifecycleState.FAILED},
        LifecycleState.FINISH: set(),
        LifecycleState.FAILED: set()
    }

    def __init__(self, initial_state: LifecycleState = LifecycleState.OBSERVE):
        self.current_state = initial_state
        self.history: List[LifecycleState] = [initial_state]

    def can_transition(self, target: LifecycleState) -> bool:
        allowed = self.VALID_TRANSITIONS.get(self.current_state, set())
        return target in allowed

    def transition(self, target: LifecycleState):
        if not self.can_transition(target):
            raise ValueError(f"Illegal lifecycle transition from {self.current_state.value} to {target.value}")
        self.current_state = target
        self.history.append(target)
```

---

### Task 2: AutonomousPipeline (Full Integration Orchestrator)

**Files:**
- Create: `delta/agent/runtime/pipeline.py`
- Test: `tests/test_autonomous_pipeline.py`

**Interfaces:**
- Produces: `AutonomousPipeline(workspace_root, autonomy_mode).run(objective, target_files) -> PipelineResult` (orchestrates end-to-end loop asynchronously).

- [ ] **Step 1: Write failing integration test**

```python
# tests/test_autonomous_pipeline.py
import pytest
import tempfile
import os
from delta.agent.runtime.pipeline import AutonomousPipeline
from delta.agent.policy.autonomy import AutonomyMode

@pytest.mark.asyncio
async def test_autonomous_pipeline_end_to_end_clean_run():
    with tempfile.TemporaryDirectory() as tmp:
        # Create minimal Python repo fixture
        with open(os.path.join(tmp, "pyproject.toml"), "w") as f:
            f.write("[tool.pytest.ini_options]\n")
        with open(os.path.join(tmp, "calc.py"), "w") as f:
            f.write("def add(a, b):\n    return a + b\n")
        with open(os.path.join(tmp, "test_calc.py"), "w") as f:
            f.write("from calc import add\ndef test_add(): assert add(1, 2) == 3\n")

        pipeline = AutonomousPipeline(workspace_root=tmp, autonomy=AutonomyMode.FULL_AUTONOMOUS)
        res = await pipeline.run(objective="Verify calc.py implementation", target_files=["calc.py"])
        assert res.task_status == "FINISHED"
        assert res.completion_decision.eligible is True
```

- [ ] **Step 2: Implement AutonomousPipeline**

Implement `AutonomousPipeline` connecting:
- `RepositoryDetector` & `IncrementalIndexer` (`UNDERSTAND`)
- `ContextEngine` L0-L7 (`CONTEXT`)
- `PlanEngine` (`PLAN`)
- `AgentCoordinator` with `TaskDAG` (`EXECUTE`)
- `VerifierEngine` (`VERIFY`)
- `DebuggerEngine` (`DEBUG` if test failed)
- `ReviewerEngine` (`REVIEW`)
- `TaskCompletionEvaluator` & `CheckpointManager` (`FINISH`)
