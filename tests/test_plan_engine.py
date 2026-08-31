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
    assert plan.steps[2].dependencies == ["1b"]
