# delta/agent/runtime/registry.py
from typing import Dict, Optional, List
from delta.agent.runtime.worker import ScopedWorker

class WorkerRegistry:
    def __init__(self):
        self._workers: Dict[str, ScopedWorker] = {}

    def register(self, worker: ScopedWorker):
        self._workers[worker.role().lower()] = worker

    def get_worker(self, role: str) -> Optional[ScopedWorker]:
        return self._workers.get(role.lower())

    def list_roles(self) -> List[str]:
        return sorted(list(self._workers.keys()))

class WorkerSelector:
    def __init__(self, registry: WorkerRegistry):
        self.registry = registry

    def select_worker_for_role(self, role: str) -> Optional[ScopedWorker]:
        return self.registry.get_worker(role)
