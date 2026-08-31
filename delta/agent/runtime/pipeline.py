# delta/agent/runtime/pipeline.py
import os
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path

from delta.agent.policy.autonomy import AutonomyMode
from delta.agent.policy.engine import ExecutionPolicy
from delta.agent.state.task_state import TaskState
from delta.agent.state.checkpoint import CheckpointManager
from delta.intelligence.repository.detector import RepositoryDetector
from delta.intelligence.repository.indexer import IncrementalIndexer
from delta.intelligence.context.engine import ContextEngine
from delta.intelligence.context.layers import ContextItem, ContextLayerType, LayerPriority
from delta.agent.planner.engine import PlanEngine
from delta.agent.planner.model import Plan
from delta.agent.runtime.dag import TaskDAG
from delta.agent.runtime.coordinator import AgentCoordinator
from delta.agent.verifier.runner import AutoTestRunner, TestRunResult
from delta.agent.verifier.engine import VerifierEngine, ExtendedRegressionReport
from delta.agent.debugger.model import TestFailure
from delta.agent.debugger.engine import DebuggerEngine
from delta.agent.reviewer.engine import ReviewerEngine
from delta.agent.reviewer.model import ReviewReport
from delta.agent.runtime.completion import TaskCompletionEvaluator, CompletionDecision
from delta.agent.runtime.lifecycle import AgentLifecycleEngine, LifecycleState

@dataclass
class PipelineResult:
    task_id: str
    objective: str
    task_status: str
    lifecycle_history: List[str]
    completion_decision: CompletionDecision
    modified_files: List[str] = field(default_factory=list)
    verifier_report: Optional[ExtendedRegressionReport] = None
    review_report: Optional[ReviewReport] = None
    duration_ms: float = 0.0

class AutonomousPipeline:
    def __init__(
        self,
        workspace_root: str = ".",
        autonomy: AutonomyMode = AutonomyMode.SUPERVISED
    ):
        self.workspace = Path(workspace_root).resolve()
        self.autonomy = autonomy
        self.policy = ExecutionPolicy(autonomy=autonomy, workspace_root=str(self.workspace))
        self.checkpoint_mgr = CheckpointManager(workspace_root=str(self.workspace))
        self.detector = RepositoryDetector(workspace_root=str(self.workspace))
        self.indexer = IncrementalIndexer(workspace_root=str(self.workspace))
        self.context_engine = ContextEngine(max_tokens=8000)
        self.coordinator = AgentCoordinator(workspace_root=str(self.workspace))
        self.verifier = VerifierEngine(workspace_root=str(self.workspace))
        self.debugger = DebuggerEngine(workspace_root=str(self.workspace))
        self.reviewer = ReviewerEngine(workspace_root=str(self.workspace))
        self.evaluator = TaskCompletionEvaluator()

    async def run(
        self,
        objective: str,
        target_files: List[str],
        task_id: str = "task_auto_001"
    ) -> PipelineResult:
        start_t = time.time()
        lifecycle = AgentLifecycleEngine()
        state = TaskState(task_id=task_id, goal=objective)
        self.checkpoint_mgr.save_task_state(state)

        # 1. OBSERVE & UNDERSTAND
        lifecycle.transition(LifecycleState.UNDERSTAND)
        detector_res = self.detector.detect()
        repo_graph = self.indexer.index()

        # 2. CONTEXT & PLAN
        lifecycle.transition(LifecycleState.PLAN)
        self.context_engine.clear()
        self.context_engine.add_item(ContextItem(
            layer_type=ContextLayerType.L0_TASK,
            priority=LayerPriority.P1_CRITICAL,
            content=f"Objective: {objective}\nTarget files: {', '.join(target_files)}",
            name="task_invariant"
        ))

        plan_engine = PlanEngine(task_id=task_id, objective=objective)
        plan = plan_engine.create_plan([
            {"id": "1", "description": f"Architect check for {objective}", "role": "architect"},
            {"id": "2", "description": f"Research target files: {', '.join(target_files)}", "role": "researcher", "deps": ["1"]},
            {"id": "3", "description": f"Code implementation patch for {objective}", "role": "coder", "deps": ["2"]},
            {"id": "4", "description": f"Run tests for {objective}", "role": "tester", "deps": ["3"]},
            {"id": "5", "description": f"Self-review changes for {objective}", "role": "reviewer", "deps": ["4"]}
        ])
        state.plan = plan.to_dict()

        # 3. EXECUTE VIA MULTI-AGENT COORDINATOR
        lifecycle.transition(LifecycleState.EXECUTE)
        dag = TaskDAG()
        for step in plan.steps:
            dag.add_node(step.assigned_role, deps=step.dependencies)

        worker_results = await self.coordinator.run_task_graph(
            objective=objective,
            target_files=target_files,
            dag=dag,
            task_id=task_id
        )

        for step in plan.steps:
            if step.assigned_role in worker_results and worker_results[step.assigned_role].status.value == "completed":
                plan_engine.complete_step(step.id)

        # 4. VERIFY
        lifecycle.transition(LifecycleState.VERIFY)
        baseline = TestRunResult(passed_count=1, failed_count=0)
        ver_report = self.verifier.verify_changes(
            baseline=baseline,
            modified_files=target_files,
            test_command=detector_res.test_command or "pytest"
        )

        # 5. DEBUG IF VERIFICATION FAILED
        if ver_report.has_regression:
            lifecycle.transition(LifecycleState.DEBUG)
            dummy_fail = TestFailure(test_id=ver_report.new_failures[0] if ver_report.new_failures else "test_fail")
            self.debugger.diagnose(dummy_fail, modified_files=target_files)
            lifecycle.transition(LifecycleState.EXECUTE)
            lifecycle.transition(LifecycleState.VERIFY)

        # 6. REVIEW
        lifecycle.transition(LifecycleState.REVIEW)
        rev_report = self.reviewer.review_task(
            objective=objective,
            target_files=target_files,
            modified_files=target_files,
            diff_text="+ modified",
            baseline_run=baseline,
            current_run=baseline,
            repo_graph=repo_graph
        )

        # 7. REFLECT & FINISH
        lifecycle.transition(LifecycleState.REFLECT)
        completion_dec = self.evaluator.evaluate(
            task_state=state,
            plan=plan,
            verifier_report=ver_report,
            review_report=rev_report
        )

        final_status = "FINISHED" if completion_dec.eligible else "FAILED"
        if completion_dec.eligible:
            lifecycle.transition(LifecycleState.FINISH)
            state.status = "completed"
        else:
            lifecycle.transition(LifecycleState.FAILED)
            state.status = "failed"

        self.checkpoint_mgr.save_task_state(state)
        self.checkpoint_mgr.create_checkpoint(state, description="End of autonomous pipeline execution")

        return PipelineResult(
            task_id=task_id,
            objective=objective,
            task_status=final_status,
            lifecycle_history=[s.value for s in lifecycle.history],
            completion_decision=completion_dec,
            modified_files=target_files,
            verifier_report=ver_report,
            review_report=rev_report,
            duration_ms=(time.time() - start_t) * 1000.0
        )
