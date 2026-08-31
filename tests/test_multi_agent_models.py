# tests/test_multi_agent_models.py
import pytest
from delta.agent.runtime.worker import WorkerStatus, WorkerResult, RoleContext, Artifact, ScopedWorker

class DummyWorker(ScopedWorker):
    def role(self) -> str:
        return "dummy"
    async def execute(self, context: RoleContext) -> WorkerResult:
        return WorkerResult(
            worker_id=self.role(),
            role=self.role(),
            task_id=context.task_id,
            status=WorkerStatus.COMPLETED,
            findings=["Found 1 item"]
        )

@pytest.mark.asyncio
async def test_worker_result_serialization():
    ctx = RoleContext(task_id="t123", objective="Test worker")
    worker = DummyWorker()
    res = await worker.execute(ctx)
    assert res.worker_id == "dummy"
    assert res.status == WorkerStatus.COMPLETED
    assert len(res.findings) == 1
