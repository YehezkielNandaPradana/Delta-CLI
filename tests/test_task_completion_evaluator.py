# tests/test_task_completion_evaluator.py
from delta.agent.state.task_state import TaskState
from delta.agent.planner.model import Plan, PlanStep, StepStatus
from delta.agent.verifier.engine import ExtendedRegressionReport
from delta.agent.reviewer.model import ReviewReport, ReviewStatus
from delta.agent.runtime.completion import TaskCompletionEvaluator
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

    lifecycle.transition(LifecycleState.UNDERSTAND)
    assert lifecycle.current_state == LifecycleState.UNDERSTAND

    assert lifecycle.can_transition(LifecycleState.FINISH) is False
