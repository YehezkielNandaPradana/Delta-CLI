# delta/agent/runtime/worker.py
import abc
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

class WorkerStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

@dataclass
class Artifact:
    id: str
    kind: str
    data: Dict[str, Any]
    created_at: float = field(default_factory=time.time)

@dataclass
class RoleContext:
    task_id: str
    objective: str
    role: str = "main"
    step_id: Optional[str] = None
    target_files: List[str] = field(default_factory=list)
    modified_files: List[str] = field(default_factory=list)
    artifacts: Dict[str, Artifact] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkerResult:
    worker_id: str
    role: str
    task_id: str
    status: WorkerStatus
    findings: List[str] = field(default_factory=list)
    artifacts: List[Artifact] = field(default_factory=list)
    affected_files: List[str] = field(default_factory=list)
    affected_symbols: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    requested_actions: List[str] = field(default_factory=list)
    verification_status: Optional[str] = None
    error: Optional[str] = None
    duration_ms: float = 0.0

class ScopedWorker(abc.ABC):
    @abc.abstractmethod
    def role(self) -> str:
        pass

    @abc.abstractmethod
    async def execute(self, context: RoleContext) -> WorkerResult:
        pass

    def can_handle(self, context: RoleContext) -> bool:
        return True
