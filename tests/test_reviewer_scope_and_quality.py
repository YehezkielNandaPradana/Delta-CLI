# tests/test_reviewer_scope_and_quality.py
from delta.agent.reviewer.scope import IntentScopeAnalyzer
from delta.agent.reviewer.quality import ChangeRiskAnalyzer, ChangeRiskLevel

def test_intent_scope_analyzer_detects_unrelated_files():
    analyzer = IntentScopeAnalyzer()
    res = analyzer.analyze(
        objective="Fix authentication token validation bug",
        target_files=["delta/core/auth.py"],
        modified_files=["delta/core/auth.py", "delta/web/dashboard_ui.py"]
    )
    assert len(res.unexpected_files) == 1
    assert "delta/web/dashboard_ui.py" in res.unexpected_files
    assert res.has_unrelated_changes is True

def test_change_risk_analyzer_evaluates_high_risk_security_edits():
    analyzer = ChangeRiskAnalyzer()
    risk = analyzer.analyze_risk(
        modified_files=["delta/core/auth.py", "delta/pentest/scope.py"],
        lines_changed=250,
        has_security_code=True
    )
    assert risk in [ChangeRiskLevel.HIGH, ChangeRiskLevel.CRITICAL]
