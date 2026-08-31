# tests/test_task_state_and_checkpoint.py
import tempfile
import os
from delta.agent.state.task_state import TaskState
from delta.agent.state.checkpoint import CheckpointManager

def test_task_state_serialization():
    state = TaskState(
        task_id="task_123",
        goal="Fix authentication bug in token validation",
        status="in_progress"
    )
    state.record_modified_file("src/auth.py")
    state.record_decision("Use UTC timestamp for token expiry")

    d = state.to_dict()
    assert d["task_id"] == "task_123"
    assert "src/auth.py" in d["modified_files"]
    assert len(d["decisions"]) == 1

def test_checkpoint_creation_and_restore():
    with tempfile.TemporaryDirectory() as tmp:
        mgr = CheckpointManager(workspace_root=tmp)
        state = TaskState(task_id="task_999", goal="Refactor router")

        # Save task and create checkpoint
        mgr.save_task_state(state)
        cp = mgr.create_checkpoint(state, description="Before router modification")
        assert cp.checkpoint_id is not None
        assert os.path.exists(os.path.join(tmp, ".delta", "tasks", "task_999", "checkpoints"))

        # Resume task
        loaded = mgr.load_task_state("task_999")
        assert loaded is not None
        assert loaded.goal == "Refactor router"
