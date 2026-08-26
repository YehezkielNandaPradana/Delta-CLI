# Refactor: task queue
# delta/ai/task_manager.py
"""
Agent Task Manager for Delta AI Agentic Execution.
Manages tasks, statuses, parent/child execution structures, and emits real-time events to EventBus.
"""

import time
import uuid
from typing import Any, Dict, List, Optional
from delta.ai.events import Task, TaskStatus, AgentEvent, EventType, EventBus, event_bus

class AgentTaskManager:
    def __init__(self, bus: Optional[EventBus] = None):
        self.bus = bus or event_bus
        self.tasks: Dict[str, Task] = {}

    def create_task(self, title: str, parent_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Task:
        task_id = str(uuid.uuid4())[:8]
        task = Task(
            id=task_id,
            title=title,
            status=TaskStatus.PENDING,
            parent_id=parent_id,
            metadata=metadata or {}
        )
        self.tasks[task_id] = task
        self.bus.emit(AgentEvent(
            type=EventType.TASK_CREATED,
            task=task.to_dict(),
            task_id=task_id,
            tasks=self.get_all_tasks_dict()
        ))
        return task

    def start_task(self, task_id: str) -> Optional[Task]:
        if task_id not in self.tasks:
            return None
        task = self.tasks[task_id]
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        self.bus.emit(AgentEvent(
            type=EventType.TASK_STARTED,
            task=task.to_dict(),
            task_id=task_id,
            tasks=self.get_all_tasks_dict()
        ))
        return task

    def complete_task(self, task_id: str) -> Optional[Task]:
        if task_id not in self.tasks:
            return None
        task = self.tasks[task_id]
        task.status = TaskStatus.COMPLETED
        task.completed_at = time.time()
        self.bus.emit(AgentEvent(
            type=EventType.TASK_COMPLETED,
            task=task.to_dict(),
            task_id=task_id,
            tasks=self.get_all_tasks_dict()
        ))
        return task

    def fail_task(self, task_id: str, error: Optional[str] = None) -> Optional[Task]:
        if task_id not in self.tasks:
            return None
        task = self.tasks[task_id]
        task.status = TaskStatus.FAILED
        task.completed_at = time.time()
        if error:
            task.metadata["error"] = error
        self.bus.emit(AgentEvent(
            type=EventType.TASK_FAILED,
            task=task.to_dict(),
            task_id=task_id,
            error={"message": error} if error else None,
            tasks=self.get_all_tasks_dict()
        ))
        return task

    def set_plan(self, titles: List[str]) -> List[Task]:
        self.tasks.clear()
        created = []
        for title in titles:
            created.append(self.create_task(title))
        return created

    def get_all_tasks_dict(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self.tasks.values()]
