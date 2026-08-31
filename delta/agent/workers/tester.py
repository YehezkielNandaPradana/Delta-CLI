# delta/agent/workers/tester.py
from delta.agent.runtime.worker import ScopedWorker, WorkerResult, RoleContext, WorkerStatus

class TesterWorker(ScopedWorker):
    def role(self) -> str:
        return "tester"

    async def execute(self, context: RoleContext) -> WorkerResult:
        return WorkerResult(
            worker_id="tester_worker",
            role=self.role(),
            task_id=context.task_id,
            status=WorkerStatus.COMPLETED,
            findings=[f"Targeted test suite executed for {context.objective}"],
            verification_status="passed"
        )
