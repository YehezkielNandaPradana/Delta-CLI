# Refactor: event payload
# delta/ai/events.py
"""
Structured Agent Event System & Event Bus for Delta AI Coding Agent.
Provides strongly-typed AgentEvent model, EventType enum, Task model, and EventBus publisher/subscriber engine.
"""

import time
import uuid
import difflib
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Union

class EventType(str, Enum):
    # Agent Lifecycle
    AGENT_START = "agent_start"
    AGENT_THINKING = "agent_thinking"
    AGENT_STATUS = "agent_status"
    AGENT_COMPLETE = "agent_complete"

    # Step Lifecycle
    AGENT_STEP_CREATED = "agent_step_created"
    AGENT_STEP_STARTED = "agent_step_started"
    AGENT_STEP_PROGRESS = "agent_step_progress"
    AGENT_STEP_COMPLETED = "agent_step_completed"
    AGENT_STEP_FAILED = "agent_step_failed"
    AGENT_STEP_CANCELLED = "agent_step_cancelled"

    # Task Lifecycle
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"

    # Tool Lifecycle
    TOOL_START = "tool_start"
    TOOL_PROGRESS = "tool_progress"
    TOOL_RESULT = "tool_result"

    # File Modifications
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_UPDATE = "file_update"
    FILE_CREATED = "file_created"
    FILE_DELETED = "file_deleted"
    DIFF_GENERATED = "diff_generated"

    # Command & Execution
    COMMAND_START = "command_start"
    COMMAND_OUTPUT = "command_output"
    COMMAND_COMPLETED = "command_completed"
    TEST_START = "test_start"
    TEST_RESULT = "test_result"

    # Diagnostics & Messages
    DIAGNOSTIC = "diagnostic"
    ERROR = "error"
    MESSAGE_DELTA = "message_delta"
    MESSAGE_COMPLETE = "message_complete"

class StepKind(str, Enum):
    ROOT = "root"
    UNDERSTAND = "understand"
    CONTEXT = "context"
    SEARCH = "search"
    READ = "read"
    ANALYZE = "analyze"
    PLAN = "plan"
    TOOL = "tool"
    COMMAND = "command"
    EDIT = "edit"
    CREATE = "create"
    DELETE = "delete"
    TEST = "test"
    VERIFY = "verify"
    RESULT = "result"

class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AgentStep:
    id: str
    task_id: str
    execution_id: str
    parent_id: Optional[str]
    kind: StepKind
    label: str
    status: StepStatus
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    duration_ms: Optional[float] = None
    tool_name: Optional[str] = None
    file_path: Optional[str] = None
    command: Optional[str] = None
    diff_stats: Optional[Dict[str, int]] = None
    error: Optional[str] = None
    output_preview: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self, existing_steps: Optional[Dict[str, "AgentStep"]] = None) -> None:
        """Validate step properties, ROOT constraints, and circular parent chain dependencies."""
        if self.parent_id and self.parent_id == self.id:
            raise ValueError(f"Self-parent circular dependency detected: step {self.id} cannot be its own parent")
        if self.parent_id and existing_steps:
            visited = {self.id}
            curr_parent_id: Optional[str] = self.parent_id
            while curr_parent_id:
                if curr_parent_id in visited:
                    raise ValueError(f"Circular parent chain detected involving step {curr_parent_id}")
                visited.add(curr_parent_id)
                parent_step = existing_steps.get(curr_parent_id)
                curr_parent_id = parent_step.parent_id if parent_step else None
        if self.kind == StepKind.ROOT or self.kind == "root":
            if self.parent_id is not None:
                raise ValueError(f"Root step {self.id} must have parent_id=None")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "execution_id": self.execution_id,
            "parent_id": self.parent_id,
            "kind": self.kind.value if isinstance(self.kind, Enum) else self.kind,
            "label": self.label,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "tool_name": self.tool_name,
            "file_path": self.file_path,
            "command": self.command,
            "diff_stats": self.diff_stats,
            "error": self.error,
            "output_preview": self.output_preview,
            "metadata": self.metadata,
        }

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

@dataclass
class Task:
    id: str
    title: str
    status: TaskStatus = TaskStatus.PENDING
    parent_id: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status.value,
            "parent_id": self.parent_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata,
        }

@dataclass
class AgentEvent:
    type: Union[EventType, str]
    timestamp: float = field(default_factory=time.time)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sequence: int = 0
    step_id: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)

    # Metadata & Payload fields
    agent_id: Optional[str] = None
    parent_agent_id: Optional[str] = None
    execution_id: Optional[str] = None
    session_id: Optional[str] = None

    # Tool execution
    tool: Optional[str] = None
    input: Optional[Dict[str, Any]] = None
    output: Optional[Any] = None
    success: Optional[bool] = None
    duration_ms: Optional[float] = None

    # File & Diff
    path: Optional[str] = None
    added_lines: Optional[int] = None
    removed_lines: Optional[int] = None
    diff: Optional[str] = None
    start_line: Optional[int] = 1

    # Tasks
    task: Optional[Dict[str, Any]] = None
    task_id: Optional[str] = None
    tasks: Optional[List[Dict[str, Any]]] = None

    # Command & Tests
    command: Optional[str] = None
    exit_code: Optional[int] = None
    passed: Optional[int] = None
    failed_count: Optional[int] = None

    # Telemetry & Status
    status_text: Optional[str] = None
    elapsed_time: Optional[float] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    tokens_available: bool = True

    # Diagnostics & Errors
    severity: Optional[str] = None
    count: Optional[int] = None
    files: Optional[List[str]] = None
    error: Optional[Dict[str, Any]] = None

    # Streaming text content
    content: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        res = {}
        for k, v in asdict(self).items():
            if v is not None:
                if isinstance(v, Enum):
                    res[k] = v.value
                else:
                    res[k] = v
        if isinstance(self.type, Enum):
            res["type"] = self.type.value
        return res

def generate_real_diff(path: str, old_content: str, new_content: str) -> Optional[AgentEvent]:
    """Calculate line additions, removals, unified diff, and return a file_update AgentEvent."""
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    diff_lines = list(difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
        lineterm=""
    ))

    if not diff_lines:
        return None

    added = sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff_lines if line.startswith("-") and not line.startswith("---"))

    start_line = 1
    for line in diff_lines:
        if line.startswith("@@"):
            try:
                # Format: @@ -old_start,len +new_start,len @@
                parts = line.split("+")[1].split(",")[0].split(" ")[0]
                start_line = int(parts)
                break
            except Exception:
                pass

    diff_str = "\n".join(diff_lines)

    return AgentEvent(
        type=EventType.FILE_UPDATE,
        path=path,
        added_lines=added,
        removed_lines=removed,
        diff=diff_str,
        start_line=start_line
    )

class EventBus:
    """Thread-safe multi-subscriber event bus for streaming AgentEvent instances to CLI & Web."""

    def __init__(self):
        self._subscribers: List[Callable[[AgentEvent], None]] = []
        self._sequences: Dict[str, int] = {}
        self._global_seq: int = 0

    def subscribe(self, callback: Callable[[AgentEvent], None]) -> Callable[[], None]:
        self._subscribers.append(callback)
        def unsubscribe():
            if callback in self._subscribers:
                self._subscribers.remove(callback)
        return unsubscribe

    def emit(self, event: AgentEvent) -> None:
        exec_id = event.execution_id or "default"
        self._sequences[exec_id] = self._sequences.get(exec_id, 0) + 1
        if not event.sequence:
            event.sequence = self._sequences[exec_id]
        for subscriber in list(self._subscribers):
            try:
                subscriber(event)
            except Exception:
                pass

# Global Event Bus instance
event_bus = EventBus()
