# tests/test_execution_policy.py
import tempfile
from pathlib import Path
from delta.agent.policy.autonomy import AutonomyMode
from delta.agent.policy.risk import ToolRisk
from delta.agent.policy.engine import ExecutionPolicy


def test_strict_mode_prompts_writes():
    with tempfile.TemporaryDirectory() as tmp:
        policy = ExecutionPolicy(autonomy=AutonomyMode.STRICT, workspace_root=tmp)
        dec = policy.evaluate_tool_call(
            tool_name="write_file",
            tool_args={"file_path": f"{tmp}/test.py", "content": "print(1)"},
            worker_role="coder",
            tool_category="filesystem",
        )
        assert dec.allowed is True
        assert dec.requires_confirmation is True
        assert dec.requires_checkpoint is True


def test_supervised_mode_allows_workspace_writes():
    with tempfile.TemporaryDirectory() as tmp:
        policy = ExecutionPolicy(autonomy=AutonomyMode.SUPERVISED, workspace_root=tmp)
        dec = policy.evaluate_tool_call(
            tool_name="write_file",
            tool_args={"file_path": f"{tmp}/test.py", "content": "print(1)"},
            worker_role="coder",
            tool_category="filesystem",
        )
        assert dec.allowed is True
        assert dec.requires_confirmation is False
        assert dec.requires_checkpoint is True


def test_autonomous_ci_mode_blocks_high_impact_deterministically():
    with tempfile.TemporaryDirectory() as tmp:
        policy = ExecutionPolicy(
            autonomy=AutonomyMode.FULL_AUTONOMOUS, workspace_root=tmp
        )
        dec = policy.evaluate_tool_call(
            tool_name="shell",
            tool_args={"command": "rm -rf /"},
            worker_role="main",
            tool_category="execution",
        )
        assert dec.allowed is False
        assert dec.requires_confirmation is False
        assert "blocked in autonomous/CI mode" in dec.reason


def test_role_matrix_rejection():
    with tempfile.TemporaryDirectory() as tmp:
        policy = ExecutionPolicy(autonomy=AutonomyMode.SUPERVISED, workspace_root=tmp)
        # Architect role has max risk READ and cannot perform WRITE
        dec = policy.evaluate_tool_call(
            tool_name="write_file",
            tool_args={"file_path": f"{tmp}/test.py", "content": "print(1)"},
            worker_role="architect",
            tool_category="filesystem",
        )
        assert dec.allowed is False
        assert "not authorized" in dec.reason


def test_workspace_boundary_escape_requires_confirmation_in_supervised():
    with tempfile.TemporaryDirectory() as tmp:
        policy = ExecutionPolicy(autonomy=AutonomyMode.SUPERVISED, workspace_root=tmp)
        # Path outside workspace
        outside_path = str(Path(tmp).parent / "outside_secret.txt")
        dec = policy.evaluate_tool_call(
            tool_name="write_file",
            tool_args={"file_path": outside_path, "content": "data"},
            worker_role="coder",
            tool_category="filesystem",
        )
        assert dec.allowed is True
        assert dec.requires_confirmation is True
        assert "outside workspace root" in dec.reason
