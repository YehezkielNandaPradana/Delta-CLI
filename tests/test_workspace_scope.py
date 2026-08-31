# tests/test_workspace_scope.py
import os
import tempfile
from pathlib import Path
from delta.agent.policy.workspace import WorkspaceScope, RolePermissionMatrix
from delta.agent.policy.risk import ToolRisk

def test_workspace_boundary_containment():
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = WorkspaceScope(tmpdir)
        inside_file = os.path.join(tmpdir, "src", "main.py")
        outside_file = os.path.abspath(os.path.join(tmpdir, "..", "secret.txt"))

        assert ws.contains_path(inside_file) is True
        assert ws.contains_path(outside_file) is False

def test_role_permission_matrix():
    matrix = RolePermissionMatrix()

    # Architect & Researcher: READ only
    assert matrix.is_allowed(role="architect", risk=ToolRisk.READ, category="filesystem") is True
    assert matrix.is_allowed(role="architect", risk=ToolRisk.WRITE, category="filesystem") is False
    assert matrix.is_allowed(role="researcher", risk=ToolRisk.WRITE, category="filesystem") is False

    # Coder: READ, LOW_WRITE, WRITE
    assert matrix.is_allowed(role="coder", risk=ToolRisk.WRITE, category="filesystem") is True
    assert matrix.is_allowed(role="coder", risk=ToolRisk.HIGH_IMPACT, category="filesystem") is False

    # Tester: READ, LOW_WRITE, WRITE for test/execution
    assert matrix.is_allowed(role="tester", risk=ToolRisk.WRITE, category="execution") is True
