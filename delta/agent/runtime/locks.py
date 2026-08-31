# delta/agent/runtime/locks.py
import asyncio
from typing import List, Dict
from contextlib import asynccontextmanager

class ResourceLockManager:
    def __init__(self):
        self._locks: Dict[str, asyncio.Lock] = {}

    def _get_lock(self, key: str) -> asyncio.Lock:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    def is_locked(self, key: str) -> bool:
        if key not in self._locks:
            return False
        return self._locks[key].locked()

    @asynccontextmanager
    async def lock_resources(self, resource_keys: List[str]):
        sorted_keys = sorted(list(set(resource_keys)))
        acquired = []
        try:
            for key in sorted_keys:
                lock = self._get_lock(key)
                await lock.acquire()
                acquired.append(lock)
            yield
        finally:
            for lock in reversed(acquired):
                lock.release()
