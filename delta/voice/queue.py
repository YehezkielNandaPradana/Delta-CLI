import heapq
import threading
from typing import Optional, List
from delta.voice.model import TTSRequest, VoicePriority

class PriorityVoiceQueue:
    def __init__(self, maxsize: int = 100):
        self.maxsize = maxsize
        self._heap: List[tuple] = []
        self._lock = threading.Lock()
        self._counter = 0

    def put(self, item: TTSRequest) -> bool:
        with self._lock:
            # Drop LOW priority items if queue is full
            if len(self._heap) >= self.maxsize:
                if item.priority == VoicePriority.LOW:
                    return False
                # Remove lowest priority item if possible
                self._heap = [x for x in self._heap if x[0] != VoicePriority.LOW]

            self._counter += 1
            # (priority_value, sequence, item)
            heapq.heappush(self._heap, (int(item.priority), self._counter, item))
            return True

    def get(self) -> Optional[TTSRequest]:
        with self._lock:
            if not self._heap:
                return None
            return heapq.heappop(self._heap)[2]

    def flush_task(self, task_id: str) -> None:
        with self._lock:
            self._heap = [x for x in self._heap if x[2].task_id != task_id]
            heapq.heapify(self._heap)

    def clear(self) -> None:
        with self._lock:
            self._heap.clear()

    def size(self) -> int:
        with self._lock:
            return len(self._heap)
