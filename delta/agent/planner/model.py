# delta/agent/planner/model.py
import time
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"

@dataclass
class PlanStep:
    id: str
    description: str
    assigned_role: str = "main"
    dependencies: List[str] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    target_files: List[str] = field(default_factory=list)
    verification_command: Optional[str] = None
    rollback_strategy: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d

@dataclass
class Plan:
    task_id: str
    objective: str
    constraints: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    steps: List[PlanStep] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["steps"] = [s.to_dict() for s in self.steps]
        return d
