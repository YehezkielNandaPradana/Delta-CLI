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
