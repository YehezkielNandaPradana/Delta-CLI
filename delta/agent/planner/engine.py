# delta/agent/planner/engine.py
import time
from typing import List, Dict, Any, Optional
from delta.agent.planner.model import Plan, PlanStep, StepStatus

class PlanEngine:
    def __init__(self, task_id: str, objective: str):
        self.task_id = task_id
        self.objective = objective
        self.plan: Optional[Plan] = None

    def create_plan(self, steps_def: List[Dict[str, Any]], constraints: Optional[List[str]] = None) -> Plan:
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
        if step and self.plan:
            step.status = StepStatus.RUNNING
            self.plan.updated_at = time.time()

    def complete_step(self, step_id: str):
        step = self.get_step(step_id)
        if step and self.plan:
            step.status = StepStatus.COMPLETED
            self.plan.updated_at = time.time()

    def fail_step(self, step_id: str, reason: str = ""):
        step = self.get_step(step_id)
        if step and self.plan:
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
