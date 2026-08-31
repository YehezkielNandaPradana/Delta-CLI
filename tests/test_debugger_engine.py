# tests/test_debugger_engine.py
from delta.agent.debugger.model import TestFailure
from delta.agent.debugger.engine import DebuggerEngine, DebuggerStatus

def test_debugger_engine_attempts_and_budget():
    fail = TestFailure(
        test_id="test_login",
        message="AssertionError: login failed",
        raw_output="AssertionError: login failed"
    )
    debugger = DebuggerEngine(max_debug_attempts=2)
    report = debugger.diagnose(fail, modified_files=["src/login.py"])

    assert report.status == DebuggerStatus.DIAGNOSED
    assert report.root_cause is not None
    assert report.attempts_used == 1

def test_debugger_engine_exhaustion():
    fail = TestFailure(test_id="test_impossible", message="Hard error")
    debugger = DebuggerEngine(max_debug_attempts=1)
    debugger.attempts = 1
    report = debugger.diagnose(fail, modified_files=["src/impossible.py"])
    assert report.status == DebuggerStatus.DEBUG_EXHAUSTED
