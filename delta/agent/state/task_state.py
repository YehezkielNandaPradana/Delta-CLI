import time
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

@dataclass
class TaskState:
    task_id: str
    goal: str
    status: str = "pending"
    plan: Optional[Dict[str, Any]] = None
    current_step: Optional[str] = None
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    modified_files: List[str] = field(default_factory=list)
    tests_run: List[Dict[str, Any]] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    decisions: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def record_modified_file(self, file_path: str):
        if file_path not in self.modified_files:
            self.modified_files.append(file_path)
            self.updated_at = time.time()

    def record_decision(self, decision: str):
        self.decisions.append(decision)
        self.updated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskState":
        return cls(**data)
