# delta/agent/reviewer/engine.py
from typing import List, Optional, Set, Any
from delta.agent.verifier.runner import TestRunResult
from delta.agent.verifier.engine import RegressionDetector
from delta.agent.reviewer.model import ReviewStatus, ReviewFinding, ReviewReport
from delta.agent.reviewer.scope import IntentScopeAnalyzer
from delta.agent.reviewer.quality import ChangeRiskAnalyzer
from delta.agent.reviewer.correctness import CorrectnessReviewer
from delta.agent.reviewer.architecture import ArchitectureReviewer
from delta.agent.reviewer.security import SecurityReviewer
from delta.agent.reviewer.regression import RegressionWatcher

class ReviewerEngine:
    def __init__(self, workspace_root: str = ".", max_review_attempts: int = 3):
        self.workspace_root = workspace_root
        self.max_review_attempts = max_review_attempts
        self.attempts = 0
        self.scope_analyzer = IntentScopeAnalyzer()
        self.risk_analyzer = ChangeRiskAnalyzer()
        self.correctness_rev = CorrectnessReviewer()
        self.arch_rev = ArchitectureReviewer()
        self.security_rev = SecurityReviewer()
        self.regression_watcher = RegressionWatcher()
        self.regression_detector = RegressionDetector()

    def review_task(
        self,
        objective: str,
        target_files: List[str],
        modified_files: List[str],
        diff_text: str = "",
        baseline_run: Optional[TestRunResult] = None,
        current_run: Optional[TestRunResult] = None,
        repo_graph: Optional[Any] = None,
        historical_failures: Optional[Set[str]] = None
    ) -> ReviewReport:
        self.attempts += 1
        findings: List[ReviewFinding] = []
        scope_violations: List[str] = []
        correctness_issues: List[str] = []
        arch_issues: List[str] = []
        sec_issues: List[str] = []
        reg_issues: List[str] = []
        required_actions: List[str] = []

        # 1. Scope Check
        scope_res = self.scope_analyzer.analyze(objective, target_files, modified_files)
        if scope_res.has_unrelated_changes:
            for unexp in scope_res.unexpected_files:
                msg = f"Unrelated file modified: {unexp}"
                scope_violations.append(msg)
                findings.append(ReviewFinding(category="scope", message=msg, severity="error", file_path=unexp))
                required_actions.append(f"Revert changes to unexpected file '{unexp}'")

        # 2. Correctness Check
        c_findings = self.correctness_rev.review(objective, modified_files, diff_text)
        for f in c_findings:
            findings.append(f)
            correctness_issues.append(f.message)

        # 3. Architecture Check
        a_findings = self.arch_rev.review(repo_graph, modified_files)
        for f in a_findings:
            findings.append(f)
            arch_issues.append(f.message)

        # 4. Security Check
        s_findings = self.security_rev.review(modified_files, diff_text)
        for f in s_findings:
            findings.append(f)
            sec_issues.append(f.message)
            if f.severity in ["error", "critical"]:
                required_actions.append(f"Address security finding: {f.message}")

        # 5. Regression Check
        if baseline_run and current_run:
            ext_report = self.regression_detector.analyze_extended(baseline_run, current_run)
            r_findings = self.regression_watcher.inspect_regression(ext_report, historical_failures)
            for f in r_findings:
                findings.append(f)
                reg_issues.append(f.message)
                required_actions.append(f"Fix test regression: {f.message}")

        # 6. Calculate Risk
        risk_level = self.risk_analyzer.analyze_risk(
            modified_files=modified_files,
            lines_changed=len(diff_text.splitlines()),
            has_security_code=len(sec_issues) > 0
        )

        # Determine Final Status
        has_critical_error = any(f.severity in ["error", "critical"] for f in findings) or len(scope_violations) > 0 or len(reg_issues) > 0
        if has_critical_error:
            status = ReviewStatus.REJECT
        elif len(findings) > 0:
            status = ReviewStatus.PASS_WITH_WARNINGS
        else:
            status = ReviewStatus.PASS

        if self.attempts > self.max_review_attempts and status == ReviewStatus.REJECT:
            status = ReviewStatus.BLOCKED

        return ReviewReport(
            status=status,
            risk_level=risk_level,
            findings=findings,
            scope_violations=scope_violations,
            correctness_issues=correctness_issues,
            architecture_issues=arch_issues,
            security_issues=sec_issues,
            regression_issues=reg_issues,
            changed_files=modified_files,
            unexpected_files=scope_res.unexpected_files,
            required_actions=required_actions,
            attempts_used=self.attempts,
            max_attempts=self.max_review_attempts
        )
