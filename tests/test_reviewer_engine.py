# tests/test_reviewer_engine.py
from delta.agent.verifier.runner import TestRunResult
from delta.agent.reviewer.engine import ReviewerEngine
from delta.agent.reviewer.model import ReviewStatus

def test_reviewer_engine_rejects_unrelated_and_security_issues():
    engine = ReviewerEngine()
    baseline = TestRunResult(passed_count=10, failed_count=0)
    current = TestRunResult(passed_count=10, failed_count=0)

    report = engine.review_task(
        objective="Fix authentication token validation",
        target_files=["delta/core/auth.py"],
        modified_files=["delta/core/auth.py", "delta/web/unrelated_ui.py"],
        diff_text='+ API_KEY = "sk-live-12345678901234567890"',
        baseline_run=baseline,
        current_run=current
    )

    assert report.status == ReviewStatus.REJECT
    assert len(report.scope_violations) >= 1
    assert len(report.security_issues) >= 1
    assert len(report.required_actions) >= 1

def test_reviewer_engine_passes_clean_task():
    engine = ReviewerEngine()
    baseline = TestRunResult(passed_count=10, failed_count=0)
    current = TestRunResult(passed_count=10, failed_count=0)

    report = engine.review_task(
        objective="Fix authentication token validation",
        target_files=["delta/core/auth.py"],
        modified_files=["delta/core/auth.py"],
        diff_text='+ timestamp = time.time()',
        baseline_run=baseline,
        current_run=current
    )

    assert report.status in [ReviewStatus.PASS, ReviewStatus.PASS_WITH_WARNINGS]
    assert len(report.scope_violations) == 0
