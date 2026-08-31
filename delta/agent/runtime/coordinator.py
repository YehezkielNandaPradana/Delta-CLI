# delta/agent/runtime/coordinator.py
import asyncio
import time
from typing import List, Dict, Any, Optional
from delta.agent.runtime.worker import ScopedWorker, WorkerResult, RoleContext, WorkerStatus
from delta.agent.runtime.locks import ResourceLockManager
from delta.agent.runtime.dag import TaskDAG
from delta.agent.runtime.registry import WorkerRegistry
from delta.agent.workers.architect import ArchitectWorker
from delta.agent.workers.researcher import ResearcherWorker
from delta.agent.workers.coder import CoderWorker
from delta.agent.workers.tester import TesterWorker
from delta.agent.workers.debugger import DebuggerWorker
from delta.agent.workers.reviewer import ReviewerWorker
from delta.agent.workers.security_reviewer import SecurityReviewerWorker

class AgentCoordinator:
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = workspace_root
        self.lock_manager = ResourceLockManager()
        self.registry = WorkerRegistry()
        self._register_default_fleet()

    def _register_default_fleet(self):
        self.registry.register(ArchitectWorker())
        self.registry.register(ResearcherWorker())
        self.registry.register(CoderWorker())
        self.registry.register(TesterWorker())
        self.registry.register(DebuggerWorker())
        self.registry.register(ReviewerWorker())
        self.registry.register(SecurityReviewerWorker())

    async def run_task_graph(
        self,
        objective: str,
        target_files: List[str],
        dag: TaskDAG,
        task_id: str = "task_multiact_001"
    ) -> Dict[str, WorkerResult]:
        results: Dict[str, WorkerResult] = {}
        modified_files: List[str] = []

        while not dag.is_finished():
            executable = dag.get_executable_nodes()
            if not executable:
                # Deadlock safety or finished
                break

            tasks_to_run = []
            for node_id in executable:
                dag.mark_running(node_id)
                tasks_to_run.append(self._execute_worker_node(node_id, task_id, objective, target_files, modified_files))

            node_results = await asyncio.gather(*tasks_to_run, return_exceptions=True)

            for node_id, res in zip(executable, node_results):
                if isinstance(res, Exception):
                    dag.mark_failed(node_id)
                    results[node_id] = WorkerResult(
                        worker_id=node_id,
                        role=node_id,
                        task_id=task_id,
                        status=WorkerStatus.FAILED,
                        error=str(res)
                    )
                else:
                    results[node_id] = res
                    if res.status == WorkerStatus.COMPLETED:
                        dag.mark_completed(node_id)
                        if res.affected_files:
                            for f in res.affected_files:
                                if f not in modified_files:
                                    modified_files.append(f)
                    else:
                        dag.mark_failed(node_id)

        return results

    async def _execute_worker_node(
        self,
        role: str,
        task_id: str,
        objective: str,
        target_files: List[str],
        modified_files: List[str]
    ) -> WorkerResult:
        worker = self.registry.get_worker(role)
        if not worker:
            return WorkerResult(
                worker_id=role,
                role=role,
                task_id=task_id,
                status=WorkerStatus.FAILED,
                error=f"No registered worker found for role '{role}'"
            )

        context = RoleContext(
            task_id=task_id,
            objective=objective,
            role=role,
            target_files=target_files,
            modified_files=list(modified_files)
        )

        lock_keys = target_files if role in ["coder", "debugger"] else []
        start_t = time.time()

        async with self.lock_manager.lock_resources(lock_keys):
            res = await worker.execute(context)

        res.duration_ms = (time.time() - start_t) * 1000.0
        return res
