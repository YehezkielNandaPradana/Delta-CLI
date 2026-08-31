### Task 3: Priority Voice Queue with Task Isolation

**Files:**
- Create: `delta/voice/queue.py`
- Test: `tests/test_voice_queue.py`

**Interfaces:**
- Consumes: `VoicePriority`, `TTSRequest`, `TTSChunk`
- Produces: `PriorityVoiceQueue.put()`, `PriorityVoiceQueue.get()`, `PriorityVoiceQueue.flush_task()`, `PriorityVoiceQueue.clear()`

- [ ] **Step 1: Write failing test for PriorityVoiceQueue**

```python
# tests/test_voice_queue.py
import pytest
from delta.voice.queue import PriorityVoiceQueue
from delta.voice.model import TTSRequest, VoicePriority

def test_queue_priority_order():
    q = PriorityVoiceQueue()
    q.put(TTSRequest(text="Low priority", priority=VoicePriority.LOW, task_id="t1"))
    q.put(TTSRequest(text="Critical priority", priority=VoicePriority.CRITICAL, task_id="t1"))
    q.put(TTSRequest(text="High priority", priority=VoicePriority.HIGH, task_id="t1"))

    assert q.get().text == "Critical priority"
    assert q.get().text == "High priority"
    assert q.get().text == "Low priority"

def test_queue_flush_task():
    q = PriorityVoiceQueue()
    q.put(TTSRequest(text="Task 1 msg", priority=VoicePriority.NORMAL, task_id="t1"))
    q.put(TTSRequest(text="Task 2 msg", priority=VoicePriority.NORMAL, task_id="t2"))

    q.flush_task("t1")
    assert q.size() == 1
    assert q.get().text == "Task 2 msg"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_voice_queue.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `PriorityVoiceQueue`**

```python
# delta/voice/queue.py
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

    def get(() -> Optional[TTSRequest]:
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_voice_queue.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/voice/queue.py tests/test_voice_queue.py
git commit -m "feat(voice): add PriorityVoiceQueue with task isolation"
```

