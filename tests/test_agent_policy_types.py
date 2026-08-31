import pytest
from delta.agent.policy.autonomy import AutonomyMode
from delta.agent.policy.risk import ToolRisk, PolicyDecision

def test_autonomy_mode_values():
    assert AutonomyMode.STRICT.value == "strict"
    assert AutonomyMode.SUPERVISED.value == "supervised"
    assert AutonomyMode.FULL_AUTONOMOUS.value == "autonomous"

def test_tool_risk_ordering():
    assert ToolRisk.READ.level < ToolRisk.LOW_WRITE.level
    assert ToolRisk.LOW_WRITE.level < ToolRisk.WRITE.level
    assert ToolRisk.WRITE.level < ToolRisk.HIGH_IMPACT.level

def test_policy_decision_to_dict():
    decision = PolicyDecision(
        allowed=True,
        requires_confirmation=False,
        requires_checkpoint=True,
        risk_level=ToolRisk.WRITE,
        reason="Local project modification",
        rollback_strategy="git_diff_revert"
    )
    d = decision.to_dict()
    assert d["allowed"] is True
    assert d["requires_checkpoint"] is True
    assert d["risk_level"] == "WRITE"
    assert d["rollback_strategy"] == "git_diff_revert"
