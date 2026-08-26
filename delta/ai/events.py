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

    def subscribe(self, callback: Callable[[AgentEvent], None]) -> Callable[[], None]:
        self._subscribers.append(callback)
        def unsubscribe():
            if callback in self._subscribers:
                self._subscribers.remove(callback)
        return unsubscribe

    def emit(self, event: AgentEvent) -> None:
        for subscriber in list(self._subscribers):
            try:
                subscriber(event)
            except Exception:
                pass

# Global Event Bus instance
event_bus = EventBus()
