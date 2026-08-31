"""
Presence Scheduler for Delta VTuber.
Periodically computes idle duration, adjusts attention levels, and decays presence metrics.
"""

import asyncio
import time
from typing import Optional


class PresenceScheduler:
    """
    Background timer loop tracking user interaction gaps and decaying attention level.
    """

    def __init__(self, tick_interval_sec: float = 1.0):
        self.tick_interval_sec = tick_interval_sec
        self._task: Optional[asyncio.Task] = None
        self._is_running = False
        self._last_interaction_time: float = time.time()
        self._attention_level: float = 0.8

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def idle_duration(self) -> float:
        return max(0.0, time.time() - self._last_interaction_time)

    @property
    def attention_level(self) -> float:
        return self._attention_level

    def record_interaction(self) -> None:
        """Mark that an active user interaction occurred."""
        self._last_interaction_time = time.time()
        self._attention_level = 0.95

    async def start(self) -> None:
        if self._task is None or self._task.done():
            self._is_running = True
            self._task = asyncio.create_task(self._scheduler_loop())

    async def stop(self) -> None:
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _scheduler_loop(self) -> None:
        try:
            while self._is_running:
                idle = self.idle_duration
                # Attention decays gently if user has been idle for > 60s
                if idle > 60.0:
                    self._attention_level = max(0.3, self._attention_level - 0.02)
                await asyncio.sleep(self.tick_interval_sec)
        except asyncio.CancelledError:
            self._is_running = False
