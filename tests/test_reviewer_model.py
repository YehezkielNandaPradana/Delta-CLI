# tests/test_reviewer_model.py
from delta.agent.reviewer.model import ReviewStatus, ChangeRiskLevel, ReviewFinding, ReviewReport

def test_reviewer_models():
    finding = ReviewFinding(
        category="scope",
        message="Unrelated modification to UI file",
        severity="error",
        evidence="Modified: src/ui/Button.tsx during auth task"
    )
    report = ReviewReport(
        status=ReviewStatus.REJECT,
        risk_level=ChangeRiskLevel.MEDIUM,
        findings=[finding],
        required_actions=["Revert changes to src/ui/Button.tsx"]
    )
    assert report.status == ReviewStatus.REJECT
    assert report.risk_level.value == "MEDIUM"
    assert len(report.findings) == 1
    assert report.findings[0].category == "scope"
