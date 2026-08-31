import os
import json
import time
import subprocess
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from pathlib import Path
from delta.agent.state.task_state import TaskState

@dataclass
class Checkpoint:
    checkpoint_id: str
    task_id: str
    timestamp: float
    description: str
    git_commit_sha: Optional[str]
    git_diff: str
    state_snapshot: Dict[str, Any]

class CheckpointManager:
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root).resolve()
        self.delta_dir = self.workspace_root / ".delta"
        self.tasks_dir = self.delta_dir / "tasks"
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    def _task_dir(self, task_id: str) -> Path:
        p = self.tasks_dir / task_id
        p.mkdir(parents=True, exist_ok=True)
        return p

    def save_task_state(self, state: TaskState):
        state_file = self._task_dir(state.task_id) / "state.json"
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, indent=2)

    def load_task_state(self, task_id: str) -> Optional[TaskState]:
        state_file = self._task_dir(task_id) / "state.json"
        if not state_file.exists():
            return None
        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return TaskState.from_dict(data)

    def create_checkpoint(self, state: TaskState, description: str = "") -> Checkpoint:
        cp_id = f"cp_{int(time.time()*1000)}"
        cp_dir = self._task_dir(state.task_id) / "checkpoints"
        cp_dir.mkdir(parents=True, exist_ok=True)

        git_diff = ""
        git_sha = None
        try:
            res_diff = subprocess.run(["git", "diff"], cwd=str(self.workspace_root), capture_output=True, text=True)
            if res_diff.returncode == 0:
                git_diff = res_diff.stdout
            res_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(self.workspace_root), capture_output=True, text=True)
            if res_sha.returncode == 0:
                git_sha = res_sha.stdout.strip()
        except Exception:
            pass

        cp = Checkpoint(
            checkpoint_id=cp_id,
            task_id=state.task_id,
            timestamp=time.time(),
            description=description,
            git_commit_sha=git_sha,
            git_diff=git_diff,
            state_snapshot=state.to_dict()
        )

        cp_file = cp_dir / f"{cp_id}.json"
        with open(cp_file, "w", encoding="utf-8") as f:
            json.dump(asdict(cp), f, indent=2)

        return cp
