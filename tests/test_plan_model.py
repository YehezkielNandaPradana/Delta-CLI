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
