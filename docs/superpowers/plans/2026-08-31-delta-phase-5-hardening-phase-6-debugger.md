# Delta Autonomous Engineering Agent (Phase 5 Hardening & Phase 6 Auto-Debugger Subsystem) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden Phase 5 Verifier Subsystem (robust subprocess handling, timeout/signal recovery, missing runner handling, malformed output resilience) and build Phase 6 Auto-Debugger & Root Cause Analyzer (Structured Failure Model, Failure Classification, Evidence Collector, Hypothesis Engine, Debug Budget, and Verifier Integration).

**Architecture:**
- **Phase 5 Hardening**: Upgrade `AutoTestRunner`, `TestRunResult`, `TargetedTestMapper`, and `RegressionDetector` in `delta/agent/verifier/`.
- **Phase 6 Debugger Subsystem**: Implement `delta/agent/debugger/` containing `model.py` (Structured Failure & Root Cause models), `classifier.py` (`FailureClassifier`), `evidence.py` (`DebugEvidenceCollector`), `hypotheses.py` (`HypothesisEngine`), `root_cause.py` (`RootCauseAnalyzer`), and `engine.py` (`DebuggerEngine` with budget tracking).

**Tech Stack:** Python 3.10+, stdlib (`subprocess`, `dataclasses`, `enum`, `re`, `json`, `pathlib`, `typing`, `time`), pytest.

## Global Constraints

- Debugger must produce evidence-backed root causes without fabricating confidence scores or exposing hidden reasoning chains.
- Debugger does NOT edit code directly; it works through Plan/Coder/ToolRegistry/Policy pipeline.
- RegressionDetector distinguishes `NEW_FAILURE`, `PRE_EXISTING_FAILURE`, `RESOLVED_FAILURE`, `FLAKY_CANDIDATE`, and `ENVIRONMENT_FAILURE`.
- All 364+ baseline tests must pass with zero regression.

---

### Task 1: Harden Phase 5 Verifier Subsystem

**Files:**
- Modify: `delta/agent/verifier/runner.py`
- Modify: `delta/agent/verifier/engine.py`
- Create: `tests/test_verifier_hardening.py`

**Interfaces:**
- Updates `AutoTestRunner.run_tests(test_command, target_file)` to handle missing executables (`FileNotFoundError`), process kill signals (`SIGTERM`), malformed outputs, and empty results gracefully.
- Extends `RegressionDetector.analyze()` to categorize `new_failures`, `pre_existing_failures`, `resolved_failures`, `flaky_candidates`, and `environment_failures`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_verifier_hardening.py
import tempfile
from delta.agent.verifier.runner import AutoTestRunner, TestRunResult
from delta.agent.verifier.engine import RegressionDetector, RegressionReport

def test_auto_test_runner_handles_missing_executable():
    runner = AutoTestRunner()
    res = runner.run_tests(test_command="non_existent_test_runner_command_12345")
    assert res.exit_code != 0
    assert "not found" in res.raw_output.lower() or "environment_error" in res.failed_tests

def test_regression_detector_distinguishes_pre_existing_and_resolved():
    baseline = TestRunResult(
        passed_count=5, failed_count=2,
        passed_tests=["test_a", "test_b"],
        failed_tests=["test_old_fail_1", "test_old_fail_2"]
    )
    current = TestRunResult(
        passed_count=6, failed_count=2,
        passed_tests=["test_a", "test_b", "test_old_fail_1"], # test_old_fail_1 resolved!
        failed_tests=["test_old_fail_2", "test_new_bug"]     # test_new_bug is new failure
    )
    detector = RegressionDetector()
    report = detector.analyze_extended(baseline=baseline, current=current)
    assert "test_new_bug" in report.new_failures
    assert "test_old_fail_2" in report.pre_existing_failures
    assert "test_old_fail_1" in report.resolved_failures
    assert report.has_regression is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_verifier_hardening.py -v`
Expected: FAIL with missing `analyze_extended` or missing executable error handling.

- [ ] **Step 3: Implement minimal hardening**

Update `delta/agent/verifier/runner.py` to handle `FileNotFoundError` as an environment error result and `delta/agent/verifier/engine.py` to add `analyze_extended` returning detailed failure categories (`new_failures`, `pre_existing_failures`, `resolved_failures`, `flaky_candidates`, `environment_failures`).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_verifier_hardening.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/agent/verifier/runner.py delta/agent/verifier/engine.py tests/test_verifier_hardening.py
git commit -m "fix(verifier): harden AutoTestRunner subprocess handling and extend RegressionDetector failure categories"
```

---

### Task 2: Failure Models & Classification Engine (Phase 6)

**Files:**
- Create: `delta/agent/debugger/model.py`
- Create: `delta/agent/debugger/classifier.py`
- Create: `delta/agent/debugger/__init__.py`
- Test: `tests/test_debugger_classifier.py`

**Interfaces:**
- Produces: `FailureClassification` enum (CODE_ERROR, TYPE_ERROR, SYNTAX_ERROR, IMPORT_ERROR, ASSERTION_FAILURE, RUNTIME_ERROR, DEPENDENCY_ERROR, CONFIGURATION_ERROR, ENVIRONMENT_ERROR, TIMEOUT, FLAKY_CANDIDATE, UNKNOWN).
- Produces: `TestFailure` dataclass.
- Produces: `FailureClassifier.classify(failure: TestFailure) -> FailureClassification`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_debugger_classifier.py
from delta.agent.debugger.model import TestFailure, FailureClassification
from delta.agent.debugger.classifier import FailureClassifier

def test_classify_syntax_error():
    fail = TestFailure(
        test_id="test_parse",
        raw_output="SyntaxError: invalid syntax in src/auth.py line 42",
        message="SyntaxError"
    )
    classifier = FailureClassifier()
    cls = classifier.classify(fail)
    assert cls == FailureClassification.SYNTAX_ERROR

def test_classify_import_error():
    fail = TestFailure(
        test_id="test_import",
        raw_output="ModuleNotFoundError: No module named 'jwt'",
        message="ModuleNotFoundError"
    )
    classifier = FailureClassifier()
    cls = classifier.classify(fail)
    assert cls == FailureClassification.IMPORT_ERROR

def test_classify_unknown_when_ambiguous():
    fail = TestFailure(
        test_id="test_weird",
        raw_output="Something custom happened without standard trace",
        message="Custom string"
    )
    classifier = FailureClassifier()
    cls = classifier.classify(fail)
    assert cls == FailureClassification.UNKNOWN
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_debugger_classifier.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'delta.agent.debugger'`

- [ ] **Step 3: Implement minimal code**

```python
# delta/agent/debugger/model.py
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

class FailureClassification(str, Enum):
    CODE_ERROR = "CODE_ERROR"
    TYPE_ERROR = "TYPE_ERROR"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    IMPORT_ERROR = "IMPORT_ERROR"
    ASSERTION_FAILURE = "ASSERTION_FAILURE"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    ENVIRONMENT_ERROR = "ENVIRONMENT_ERROR"
    TIMEOUT = "TIMEOUT"
    FLAKY_CANDIDATE = "FLAKY_CANDIDATE"
    UNKNOWN = "UNKNOWN"

@dataclass
class TestFailure:
    test_id: str
    framework: str = "pytest"
    file: Optional[str] = None
    line: Optional[int] = None
    error_type: Optional[str] = None
    message: str = ""
    stack_trace: str = ""
    raw_output: str = ""
    exit_code: int = 1
    classification: FailureClassification = FailureClassification.UNKNOWN
```

```python
# delta/agent/debugger/classifier.py
import re
from delta.agent.debugger.model import TestFailure, FailureClassification

class FailureClassifier:
    def classify(self, failure: TestFailure) -> FailureClassification:
        text = (failure.message + "\n" + failure.raw_output + "\n" + failure.stack_trace).lower()

        if "syntaxerror" in text or "parseerror" in text or "unexpected token" in text:
            return FailureClassification.SYNTAX_ERROR
        if "modulenotfounderror" in text or "importerror" in text or "cannot find module" in text:
            return FailureClassification.IMPORT_ERROR
        if "typeerror" in text or "attributeerror" in text or "argumentcounterror" in text:
            return FailureClassification.TYPE_ERROR
        if "assertionerror" in text or "expected" in text and "got" in text:
            return FailureClassification.ASSERTION_FAILURE
        if "connectionrefused" in text or "econnrefused" in text or "command not found" in text or "environment_error" in text:
            return FailureClassification.ENVIRONMENT_ERROR
        if "timeout" in text or "timed out" in text:
            return FailureClassification.TIMEOUT
        if "keyerror" in text or "indexerror" in text or "zero-division" in text or "runtimeerror" in text:
            return FailureClassification.RUNTIME_ERROR

        return FailureClassification.UNKNOWN
```

```python
# delta/agent/debugger/__init__.py
from delta.agent.debugger.model import FailureClassification, TestFailure
from delta.agent.debugger.classifier import FailureClassifier

__all__ = ["FailureClassification", "TestFailure", "FailureClassifier"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_debugger_classifier.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/agent/debugger/model.py delta/agent/debugger/classifier.py delta/agent/debugger/__init__.py tests/test_debugger_classifier.py
git commit -m "feat(debugger): implement FailureClassification enum and FailureClassifier engine"
```

---

### Task 3: Debug Evidence Collector & Hypothesis Engine

**Files:**
- Create: `delta/agent/debugger/evidence.py`
- Create: `delta/agent/debugger/hypotheses.py`
- Create: `delta/agent/debugger/root_cause.py`
- Test: `tests/test_debugger_evidence_and_hypotheses.py`

**Interfaces:**
- Produces: `DebugEvidenceCollector(workspace_root, repo_graph, context_engine).collect_evidence(failure, modified_files) -> DebugEvidence`
- Produces: `HypothesisEngine.generate_and_rank(failure, evidence) -> List[Hypothesis]`
- Produces: `RootCauseAnalyzer.analyze(hypotheses) -> RootCause`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_debugger_evidence_and_hypotheses.py
from delta.agent.debugger.model import TestFailure, FailureClassification
from delta.agent.debugger.evidence import DebugEvidenceCollector
from delta.agent.debugger.hypotheses import HypothesisEngine, Hypothesis
from delta.agent.debugger.root_cause import RootCauseAnalyzer

def test_hypothesis_generation_and_ranking():
    fail = TestFailure(
        test_id="tests/test_auth.py::test_validate_token",
        message="AssertionError: Expected True but got False",
        raw_output="AssertionError: Expected True but got False"
    )
    collector = DebugEvidenceCollector()
    evidence = collector.collect_evidence(fail, modified_files=["delta/auth/token.py"])
    assert "delta/auth/token.py" in evidence.modified_files

    engine = HypothesisEngine()
    hypotheses = engine.generate_and_rank(fail, evidence)
    assert len(hypotheses) >= 1
    assert hypotheses[0].confidence_score > 0.0

    analyzer = RootCauseAnalyzer()
    root_cause = analyzer.analyze(hypotheses)
    assert root_cause.summary != ""
    assert root_cause.recommended_action != ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_debugger_evidence_and_hypotheses.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'delta.agent.debugger.evidence'`

- [ ] **Step 3: Implement minimal code**

```python
# delta/agent/debugger/evidence.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class DebugEvidence:
    failing_test_id: str
    error_message: str
    stack_trace: str
    modified_files: List[str] = field(default_factory=list)
    relevant_symbols: List[str] = field(default_factory=list)
    git_diff_summary: str = ""

class DebugEvidenceCollector:
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = workspace_root

    def collect_evidence(self, failure: Any, modified_files: List[str]) -> DebugEvidence:
        return DebugEvidence(
            failing_test_id=getattr(failure, "test_id", "unknown_test"),
            error_message=getattr(failure, "message", ""),
            stack_trace=getattr(failure, "stack_trace", ""),
            modified_files=modified_files,
            relevant_symbols=[f for f in modified_files],
            git_diff_summary="Modified: " + ", ".join(modified_files)
        )
```

```python
# delta/agent/debugger/hypotheses.py
from dataclasses import dataclass, field
from typing import List, Optional
from delta.agent.debugger.model import TestFailure, FailureClassification
from delta.agent.debugger.evidence import DebugEvidence

@dataclass
class Hypothesis:
    id: str
    description: str
    evidence_sources: List[str] = field(default_factory=list)
    confidence_score: float = 0.5
    proposed_remediation: str = ""

class HypothesisEngine:
    def generate_and_rank(self, failure: TestFailure, evidence: DebugEvidence) -> List[Hypothesis]:
        hypotheses = []
        if failure.classification == FailureClassification.SYNTAX_ERROR:
            hypotheses.append(Hypothesis(
                id="H1",
                description="Syntax error in recently modified file",
                evidence_sources=["raw_output", "modified_files"],
                confidence_score=0.9,
                proposed_remediation="Revert invalid syntax edit"
            ))
        elif failure.classification == FailureClassification.IMPORT_ERROR:
            hypotheses.append(Hypothesis(
                id="H1",
                description="Missing module import or unresolved dependency",
                evidence_sources=["stack_trace"],
                confidence_score=0.85,
                proposed_remediation="Insert missing import or install package"
            ))
        else:
            hypotheses.append(Hypothesis(
                id="H1",
                description=f"Logic mismatch in modified file(s): {', '.join(evidence.modified_files)}",
                evidence_sources=["modified_files", "test_failure_message"],
                confidence_score=0.7,
                proposed_remediation="Adjust logic implementation in modified file to satisfy assertion"
            ))
        return hypotheses
```

```python
# delta/agent/debugger/root_cause.py
from dataclasses import dataclass, field
from typing import List, Optional
from delta.agent.debugger.hypotheses import Hypothesis

@dataclass
class RootCause:
    summary: str
    recommended_action: str
    top_hypothesis: Optional[Hypothesis] = None
    supporting_evidence: List[str] = field(default_factory=list)

class RootCauseAnalyzer:
    def analyze(self, hypotheses: List[Hypothesis]) -> RootCause:
        if not hypotheses:
            return RootCause(
                summary="Unknown root cause; insufficient evidence gathered",
                recommended_action="Gather broader logs or manual inspection"
            )
        top = hypotheses[0]
        return RootCause(
            summary=top.description,
            recommended_action=top.proposed_remediation,
            top_hypothesis=top,
            supporting_evidence=top.evidence_sources
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_debugger_evidence_and_hypotheses.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/agent/debugger/evidence.py delta/agent/debugger/hypotheses.py delta/agent/debugger/root_cause.py tests/test_debugger_evidence_and_hypotheses.py
git commit -m "feat(debugger): implement DebugEvidenceCollector, HypothesisEngine, and RootCauseAnalyzer"
```

---

### Task 4: DebuggerEngine & Budget Management

**Files:**
- Create: `delta/agent/debugger/engine.py`
- Test: `tests/test_debugger_engine.py`

**Interfaces:**
- Produces: `DebuggerEngine(workspace_root, max_debug_attempts=3)` with `debug_failure(failure, modified_files) -> DebuggerReport`.
- Manages: Budget tracking, `DEBUG_EXHAUSTED` state, event emission (`debug.started`, `debug.classified`, `debug.root_cause_found`, `debug.exhausted`).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_debugger_engine.py
from delta.agent.debugger.model import TestFailure, FailureClassification
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
    debugger.attempts = 1 # Simulate reached attempt limit
    report = debugger.diagnose(fail, modified_files=["src/impossible.py"])
    assert report.status == DebuggerStatus.DEBUG_EXHAUSTED
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_debugger_engine.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'delta.agent.debugger.engine'`

- [ ] **Step 3: Implement minimal code**

```python
# delta/agent/debugger/engine.py
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from delta.agent.debugger.model import TestFailure, FailureClassification
from delta.agent.debugger.classifier import FailureClassifier
from delta.agent.debugger.evidence import DebugEvidenceCollector, DebugEvidence
from delta.agent.debugger.hypotheses import HypothesisEngine, Hypothesis
from delta.agent.debugger.root_cause import RootCauseAnalyzer, RootCause

class DebuggerStatus(str, Enum):
    IDLE = "idle"
    DIAGNOSED = "diagnosed"
    PATCH_RECOMMENDED = "patch_recommended"
    DEBUG_EXHAUSTED = "debug_exhausted"

@dataclass
class DebuggerReport:
    status: DebuggerStatus
    classification: FailureClassification
    evidence: Optional[DebugEvidence] = None
    root_cause: Optional[RootCause] = None
    attempts_used: int = 0
    max_attempts: int = 3

class DebuggerEngine:
    def __init__(self, workspace_root: str = ".", max_debug_attempts: int = 3):
        self.workspace_root = workspace_root
        self.max_debug_attempts = max_debug_attempts
        self.attempts = 0
        self.classifier = FailureClassifier()
        self.evidence_collector = DebugEvidenceCollector(workspace_root)
        self.hypothesis_engine = HypothesisEngine()
        self.root_cause_analyzer = RootCauseAnalyzer()

    def diagnose(self, failure: TestFailure, modified_files: List[str]) -> DebuggerReport:
        if self.attempts >= self.max_debug_attempts:
            return DebuggerReport(
                status=DebuggerStatus.DEBUG_EXHAUSTED,
                classification=failure.classification,
                attempts_used=self.attempts,
                max_attempts=self.max_debug_attempts
            )

        self.attempts += 1
        classification = self.classifier.classify(failure)
        failure.classification = classification

        evidence = self.evidence_collector.collect_evidence(failure, modified_files)
        hypotheses = self.hypothesis_engine.generate_and_rank(failure, evidence)
        root_cause = self.root_cause_analyzer.analyze(hypotheses)

        return DebuggerReport(
            status=DebuggerStatus.DIAGNOSED,
            classification=classification,
            evidence=evidence,
            root_cause=root_cause,
            attempts_used=self.attempts,
            max_attempts=self.max_debug_attempts
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_debugger_engine.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/agent/debugger/engine.py tests/test_debugger_engine.py
git commit -m "feat(debugger): implement DebuggerEngine with attempt budget management and diagnostic reports"
```
