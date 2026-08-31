# tests/test_locks_and_dag.py
import pytest
import asyncio
from delta.agent.runtime.locks import ResourceLockManager
from delta.agent.runtime.dag import TaskDAG

@pytest.mark.asyncio
async def test_resource_lock_manager_deadlock_free():
    mgr = ResourceLockManager()
    async with mgr.lock_resources(["file_b.py", "file_a.py"]):
        assert mgr.is_locked("file_a.py")
        assert mgr.is_locked("file_b.py")
    assert not mgr.is_locked("file_a.py")

def test_task_dag_scheduling():
    dag = TaskDAG()
    dag.add_node("architect", deps=[])
    dag.add_node("researcher", deps=["architect"])
    dag.add_node("coder", deps=["researcher"])

    ready = dag.get_executable_nodes()
    assert ready == ["architect"]

    dag.mark_completed("architect")
    ready_2 = dag.get_executable_nodes()
    assert ready_2 == ["researcher"]
