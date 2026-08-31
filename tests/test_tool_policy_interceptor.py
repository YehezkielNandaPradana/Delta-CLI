import pytest
from delta.ai.tools import ToolRegistry, Tool, ToolParameter
from delta.agent.policy.engine import ExecutionPolicy
from delta.agent.policy.autonomy import AutonomyMode
from delta.agent.policy.risk import ToolRisk

def test_tool_registry_intercepts_unauthorized_call():
    registry = ToolRegistry()
    registry.register(Tool(
        name="dangerous_rm",
        description="deletes file",
        func=lambda path: "deleted",
        parameters=[ToolParameter("path", "string", "Path")]
    ))

    # Attach CI execution policy
    policy = ExecutionPolicy(autonomy=AutonomyMode.FULL_AUTONOMOUS, max_autonomous_risk=ToolRisk.LOW_WRITE)
    registry.set_execution_policy(policy)

    # Call with high-impact mock tool
    res = registry.execute_call("dangerous_rm", {"path": "/etc/shadow"}, worker_role="researcher")
    assert "error" in res
    assert "not authorized" in res["error"] or "blocked" in res["error"]

def test_tool_registry_allows_authorized_call():
    registry = ToolRegistry()
    registry.register(Tool(
        name="read_file",
        description="reads file",
        func=lambda path: "content",
        parameters=[ToolParameter("path", "string", "Path")]
    ))

    policy = ExecutionPolicy(autonomy=AutonomyMode.FULL_AUTONOMOUS)
    registry.set_execution_policy(policy)

    res = registry.execute_call("read_file", {"path": "delta/core/config.py"}, worker_role="main")
    assert res.get("success") is True
    assert res.get("output") == "content"

def test_tool_registry_backward_compatibility_when_no_policy_set():
    registry = ToolRegistry()
    registry.register(Tool(
        name="echo_test",
        description="echoes back",
        func=lambda text: f"echo {text}",
        parameters=[ToolParameter("text", "string", "Text")]
    ))

    # No policy set -> executes directly
    res = registry.execute_call("echo_test", {"text": "hello"})
    assert res.get("success") is True
    assert res.get("output") == "echo hello"
