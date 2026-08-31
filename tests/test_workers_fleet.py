# tests/test_workers_fleet.py
import pytest
from delta.agent.runtime.registry import WorkerRegistry, WorkerSelector
from delta.agent.workers.architect import ArchitectWorker
from delta.agent.workers.coder import CoderWorker
from delta.agent.workers.reviewer import ReviewerWorker

def test_worker_registry_and_selector():
    registry = WorkerRegistry()
    registry.register(ArchitectWorker())
    registry.register(CoderWorker())
    registry.register(ReviewerWorker())

    selector = WorkerSelector(registry)
    worker = selector.select_worker_for_role("coder")
    assert worker is not None
    assert worker.role() == "coder"

    roles = registry.list_roles()
    assert "architect" in roles
    assert "coder" in roles
    assert "reviewer" in roles
