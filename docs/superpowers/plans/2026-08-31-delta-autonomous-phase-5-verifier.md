# Delta Autonomous Engineering Agent (Phase 5: Verification & Automated Test Loop) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Automated Verification Subsystem: `AutoTestRunner` (executes project-specific test runners safely), `BaselineCapture` (records passed/failed test states before edits), `TargetedTestMapper` (uses RepositoryGraph to map modified code files to corresponding test files), and `RegressionDetector` (detects newly introduced failures).

**Architecture:** Implement `delta/agent/verifier/` with `AutoTestRunner`, `BaselineCapture`, `TargetedTestMapper`, and `VerifierEngine` coordinating post-edit regression checks.

**Tech Stack:** Python 3.10+, stdlib (`subprocess`, `dataclasses`, `enum`, `re`, `json`, `pathlib`), pytest.

## Global Constraints

- Never pass untested code to completion.
- Baseline test state must be captured before code modification.
- Regression = New Failures ∉ Baseline Failures.
- Zero regression across all existing tests.

---

### Task 1: AutoTestRunner and Baseline Capture Engine

**Files:**
- Create: `delta/agent/verifier/runner.py`
- Create: `delta/agent/verifier/__init__.py`
- Test: `tests/test_verifier_runner.py`

**Interfaces:**
- Produces: `TestRunResult` (passed_count, failed_count, passed_tests, failed_tests, raw_output, exit_code, duration_ms), `AutoTestRunner(workspace_root).run_tests(test_command, target_test_file) -> TestRunResult`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_verifier_runner.py
import tempfile
import os
from delta.agent.verifier.runner import AutoTestRunner, TestRunResult

def test_auto_test_runner_python_execution():
    with tempfile.TemporaryDirectory() as tmp:
        # Create dummy passing test
        test_file = os.path.join(tmp, "test_sample.py")
        with open(test_file, "w") as f:
            f.write("def test_ok(): assert True\n")

        runner = AutoTestRunner(workspace_root=tmp)
        res = runner.run_tests(test_command="pytest", target_file="test_sample.py")
        assert isinstance(res, TestRunResult)
        assert res.exit_code == 0
        assert res.passed_count >= 1
        assert res.failed_count == 0
```

- [ ] **Step 2: Write minimal implementation**

```python
# delta/agent/verifier/runner.py
import time
import subprocess
import re
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path

@dataclass
class TestRunResult:
    passed_count: int
    failed_count: int
    passed_tests: List[str] = field(default_factory=list)
    failed_tests: List[str] = field(default_factory=list)
    raw_output: str = ""
    exit_code: int = 0
    duration_ms: float = 0.0

class AutoTestRunner:
    def __init__(self, workspace_root: str = "."):
        self.workspace = Path(workspace_root).resolve()

    def run_tests(self, test_command: str = "pytest", target_file: Optional[str] = None) -> TestRunResult:
        cmd_parts = test_command.split()
        if target_file:
            cmd_parts.append(target_file)

        start_t = time.time()
        try:
            res = subprocess.run(
                cmd_parts,
                cwd=str(self.workspace),
                capture_output=True,
                text=True,
                timeout=120
            )
            raw = res.stdout + "\n" + res.stderr
            exit_code = res.returncode
        except subprocess.TimeoutExpired:
            return TestRunResult(
                passed_count=0,
                failed_count=1,
                failed_tests=["timeout_exceeded"],
                raw_output="Test execution timed out after 120s",
                exit_code=124,
                duration_ms=120000.0
            )
        except Exception as e:
            return TestRunResult(
                passed_count=0,
                failed_count=1,
                failed_tests=[str(e)],
                raw_output=str(e),
                exit_code=1,
                duration_ms=0.0
            )

        duration = (time.time() - start_t) * 1000.0
        passed_cnt, failed_cnt, passed_names, failed_names = self._parse_output(raw)

        # Fallback if regex parsing returned zero counts but process succeeded/failed
        if passed_cnt == 0 and failed_cnt == 0:
            if exit_code == 0:
                passed_cnt = 1
            else:
                failed_cnt = 1

        return TestRunResult(
            passed_count=passed_cnt,
            failed_count=failed_cnt,
            passed_tests=passed_names,
            failed_tests=failed_names,
            raw_output=raw,
            exit_code=exit_code,
            duration_ms=duration
        )

    def _parse_output(self, raw: str):
        passed_cnt = 0
        failed_cnt = 0
        passed_names = []
        failed_names = []

        # Pytest summary match: e.g. "3 passed, 1 failed in 0.5s"
        m_pytest = re.search(r"(\d+)\s+passed", raw)
        if m_pytest:
            passed_cnt = int(m_pytest.group(1))

        m_failed = re.search(r"(\d+)\s+failed", raw)
        if m_failed:
            failed_cnt = int(m_failed.group(1))

        # Extract specific failing test names
        for line in raw.splitlines():
            if line.startswith("FAILED ") or "::" in line and "FAIL" in line:
                parts = line.split()
                if len(parts) >= 2:
                    failed_names.append(parts[1])

        return passed_cnt, failed_cnt, passed_names, failed_names
```

```python
# delta/agent/verifier/__init__.py
from delta.agent.verifier.runner import AutoTestRunner, TestRunResult

__all__ = ["AutoTestRunner", "TestRunResult"]
```

---

### Task 2: Targeted Test Mapper and Regression Detector Engine

**Files:**
- Create: `delta/agent/verifier/engine.py`
- Test: `tests/test_verifier_engine.py`

**Interfaces:**
- Produces: `TargetedTestMapper(repo_graph).map_modified_to_tests(modified_files) -> List[str]`, `RegressionDetector(baseline, current) -> RegressionReport`, `VerifierEngine(workspace_root)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_verifier_engine.py
from delta.agent.verifier.runner import TestRunResult
from delta.agent.verifier.engine import RegressionDetector, TargetedTestMapper

def test_regression_detection():
    baseline = TestRunResult(passed_count=10, failed_count=0, passed_tests=["test_a", "test_b"])
    current_regressed = TestRunResult(passed_count=9, failed_count=1, failed_tests=["test_b"])

    detector = RegressionDetector()
    report = detector.analyze(baseline=baseline, current=current_regressed)
    assert report.has_regression is True
    assert "test_b" in report.new_failures

def test_targeted_test_mapper():
    mapper = TargetedTestMapper()
    test_files = mapper.suggest_test_files(modified_files=["delta/core/auth.py"])
    assert any("test_auth" in tf or "test_core" in tf for tf in test_files)
```

- [ ] **Step 2: Write minimal implementation**

```python
# delta/agent/verifier/engine.py
import os
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path
from delta.agent.verifier.runner import AutoTestRunner, TestRunResult

@dataclass
class RegressionReport:
    has_regression: bool
    new_failures: List[str] = field(default_factory=list)
    baseline_failed_count: int = 0
    current_failed_count: int = 0
    summary: str = ""

class RegressionDetector:
    def analyze(self, baseline: TestRunResult, current: TestRunResult) -> RegressionReport:
        baseline_failed_set = set(baseline.failed_tests)
        current_failed_set = set(current.failed_tests)

        new_fails = list(current_failed_set - baseline_failed_set)
        has_regressed = len(new_fails) > 0 or (current.exit_code != 0 and baseline.exit_code == 0)

        summary = "No regression detected."
        if has_regressed:
            summary = f"Regression detected! {len(new_fails)} new failing test(s): {', '.join(new_fails)}"

        return RegressionReport(
            has_regression=has_regressed,
            new_failures=new_fails,
            baseline_failed_count=baseline.failed_count,
            current_failed_count=current.failed_count,
            summary=summary
        )

class TargetedTestMapper:
    def suggest_test_files(self, modified_files: List[str]) -> List[str]:
        test_candidates = []
        for mf in modified_files:
            p = Path(mf)
            stem = p.stem
            # Heuristic convention matching
            candidates = [
                f"tests/test_{stem}.py",
                f"test_{stem}.py",
                f"tests/{stem}_test.py",
                f"tests/test_{stem}.ts",
                f"tests/test_{stem}.js"
            ]
            test_candidates.extend(candidates)
        return test_candidates

class VerifierEngine:
    def __init__(self, workspace_root: str = "."):
        self.runner = AutoTestRunner(workspace_root)
        self.detector = RegressionDetector()
        self.mapper = TargetedTestMapper()

    def verify_changes(
        self,
        baseline: TestRunResult,
        modified_files: List[str],
        test_command: str = "pytest"
    ) -> RegressionReport:
        suggested_tests = self.mapper.suggest_test_files(modified_files)
        target = suggested_tests[0] if suggested_tests else None

        current = self.runner.run_tests(test_command=test_command, target_file=target)
        return self.detector.analyze(baseline=baseline, current=current)
```
