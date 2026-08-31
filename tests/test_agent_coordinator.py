# tests/test_agent_coordinator.py
import pytest
from delta.agent.runtime.coordinator import AgentCoordinator
from delta.agent.runtime.dag import TaskDAG

@pytest.mark.asyncio
async def test_coordinator_runs_dag_pipeline():
    coord = AgentCoordinator()
    dag = TaskDAG()
    dag.add_node("architect", deps=[])
    dag.add_node("researcher", deps=["architect"])
    dag.add_node("coder", deps=["researcher"])
    dag.add_node("tester", deps=["coder"])
    dag.add_node("reviewer", deps=["tester"])

    results = await coord.run_task_graph(
        objective="Fix token expiry handling",
        target_files=["delta/core/auth.py"],
        dag=dag
    )

    assert "architect" in results
    assert "coder" in results
    assert "reviewer" in results
    assert results["reviewer"].status.value == "completed"
