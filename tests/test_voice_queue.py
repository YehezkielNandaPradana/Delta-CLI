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
