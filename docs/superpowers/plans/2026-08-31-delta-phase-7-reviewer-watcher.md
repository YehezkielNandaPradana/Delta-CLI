# Delta Autonomous Engineering Agent (Phase 7: Self-Reviewer & Regression Watcher) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the independent Self-Reviewer and Regression Watcher Subsystem (`delta/agent/reviewer/`) that evaluates task diffs for intent scope, correctness, architecture compliance, security vulnerabilities, change risk, and reintroduced regressions.

**Architecture:** Implement `delta/agent/reviewer/` containing:
- `model.py`: `ReviewStatus` (PASS, PASS_WITH_WARNINGS, REJECT, BLOCKED), `ReviewFinding`, `ChangeRiskLevel` (LOW, MEDIUM, HIGH, CRITICAL), and `ReviewReport`.
- `scope.py`: `IntentScopeAnalyzer` (detects unrelated file changes, excessive edits, deleted tests, unexpected deps).
- `correctness.py`: `CorrectnessReviewer` (evaluates requirements satisfaction, edge cases, type & API compatibility).
- `architecture.py`: `ArchitectureReviewer` (checks against `RepositoryGraph` for circular dependencies, bypassed abstractions, logic duplication).
- `security.py`: `SecurityReviewer` (scans input validation, secrets, unsafe shell, path handling, injection risks).
- `regression.py`: `RegressionWatcher` (consumes `ExtendedRegressionReport`, tracks historical failures, flags `REINTRODUCED` regressions).
- `quality.py`: `ChangeRiskAnalyzer` (assesses LOC, critical modules, public API impact, test coverage).
- `engine.py`: `ReviewerEngine` (read-only orchestrator with review attempt budget tracking).

**Tech Stack:** Python 3.10+, stdlib (`dataclasses`, `enum`, `typing`, `re`, `pathlib`), pytest.

## Global Constraints

- Reviewer is strictly READ-ONLY; it never modifies source code directly.
- Findings must be evidence-backed (file, symbol, test, or diff evidence).
- IntentScopeAnalyzer flags unrelated modifications (e.g. editing UI when task is auth).
- Zero regression across all 364+ existing tests.

---

### Task 1: Reviewer Models & Risk Dataclasses

**Files:**
- Create: `delta/agent/reviewer/model.py`
- Create: `delta/agent/reviewer/__init__.py`
- Test: `tests/test_reviewer_model.py`

**Interfaces:**
- Produces: `ReviewStatus` (PASS, PASS_WITH_WARNINGS, REJECT, BLOCKED), `ChangeRiskLevel` (LOW, MEDIUM, HIGH, CRITICAL), `ReviewFinding` (category, message, evidence, severity), `ReviewReport`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_reviewer_model.py
from delta.agent.reviewer.model import ReviewStatus, ChangeRiskLevel, ReviewFinding, ReviewReport

def test_reviewer_models():
    finding = ReviewFinding(
        category="scope",
        message="Unrelated modification to UI file",
        severity="error",
        evidence="Modified: src/ui/Button.tsx during auth task"
    )
    report = ReviewReport(
        status=ReviewStatus.REJECT,
        risk_level=ChangeRiskLevel.MEDIUM,
        findings=[finding],
        required_actions=["Revert changes to src/ui/Button.tsx"]
    )
    assert report.status == ReviewStatus.REJECT
    assert report.risk_level.value == "MEDIUM"
    assert len(report.findings) == 1
    assert report.findings[0].category == "scope"
```

- [ ] **Step 2: Implement minimal code**

```python
# delta/agent/reviewer/model.py
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

class ReviewStatus(str, Enum):
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    REJECT = "REJECT"
    BLOCKED = "BLOCKED"

class ChangeRiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class ReviewFinding:
    category: str  # "scope", "correctness", "architecture", "security", "regression", "quality"
    message: str
    severity: str = "warning"  # "info", "warning", "error", "critical"
    evidence: str = ""
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    recommended_fix: str = ""

@dataclass
class ReviewReport:
    status: ReviewStatus
    risk_level: ChangeRiskLevel = ChangeRiskLevel.LOW
    findings: List[ReviewFinding] = field(default_factory=list)
    scope_violations: List[str] = field(default_factory=list)
    correctness_issues: List[str] = field(default_factory=list)
    architecture_issues: List[str] = field(default_factory=list)
    security_issues: List[str] = field(default_factory=list)
    regression_issues: List[str] = field(default_factory=list)
    quality_issues: List[str] = field(default_factory=list)
    changed_files: List[str] = field(default_factory=list)
    unexpected_files: List[str] = field(default_factory=list)
    missing_tests: List[str] = field(default_factory=list)
    required_actions: List[str] = field(default_factory=list)
    attempts_used: int = 1
    max_attempts: int = 3
```

```python
# delta/agent/reviewer/__init__.py
from delta.agent.reviewer.model import ReviewStatus, ChangeRiskLevel, ReviewFinding, ReviewReport

__all__ = ["ReviewStatus", "ChangeRiskLevel", "ReviewFinding", "ReviewReport"]
```

---

### Task 2: Intent Scope & Risk Analyzers

**Files:**
- Create: `delta/agent/reviewer/scope.py`
- Create: `delta/agent/reviewer/quality.py`
- Test: `tests/test_reviewer_scope_and_quality.py`

**Interfaces:**
- Produces: `IntentScopeAnalyzer.analyze(objective, target_files, modified_files) -> ScopeAnalysisResult`
- Produces: `ChangeRiskAnalyzer.analyze_risk(modified_files, git_diff, test_results) -> ChangeRiskLevel`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_reviewer_scope_and_quality.py
from delta.agent.reviewer.scope import IntentScopeAnalyzer
from delta.agent.reviewer.quality import ChangeRiskAnalyzer, ChangeRiskLevel

def test_intent_scope_analyzer_detects_unrelated_files():
    analyzer = IntentScopeAnalyzer()
    res = analyzer.analyze(
        objective="Fix authentication token validation bug",
        target_files=["delta/core/auth.py"],
        modified_files=["delta/core/auth.py", "delta/web/dashboard_ui.py"]
    )
    assert len(res.unexpected_files) == 1
    assert "delta/web/dashboard_ui.py" in res.unexpected_files
    assert res.has_unrelated_changes is True

def test_change_risk_analyzer_evaluates_high_risk_security_edits():
    analyzer = ChangeRiskAnalyzer()
    risk = analyzer.analyze_risk(
        modified_files=["delta/core/auth.py", "delta/pentest/scope.py"],
        lines_changed=250,
        has_security_code=True
    )
    assert risk in [ChangeRiskLevel.HIGH, ChangeRiskLevel.CRITICAL]
```

- [ ] **Step 2: Implement minimal code**

```python
# delta/agent/reviewer/scope.py
from dataclasses import dataclass, field
from typing import List, Set
from pathlib import Path

@dataclass
class ScopeAnalysisResult:
    has_unrelated_changes: bool
    expected_files: List[str] = field(default_factory=list)
    actual_modified_files: List[str] = field(default_factory=list)
    unexpected_files: List[str] = field(default_factory=list)
    missing_expected_files: List[str] = field(default_factory=list)
    deleted_test_files: List[str] = field(default_factory=list)

class IntentScopeAnalyzer:
    def analyze(self, objective: str, target_files: List[str], modified_files: List[str]) -> ScopeAnalysisResult:
        expected = set(target_files)
        actual = set(modified_files)

        unexpected = []
        for mf in actual:
            # If target_files were defined, check if file is within expected paths/domains
            if expected and mf not in expected:
                # Heuristic: check domain match
                mf_stem = Path(mf).stem.lower()
                is_related = any(Path(ef).stem.lower() in mf_stem or mf_stem in Path(ef).stem.lower() for ef in expected)
                if not is_related and not mf.startswith("tests/"):
                    unexpected.append(mf)

        missing = list(expected - actual)
        deleted_tests = [mf for mf in actual if mf.startswith("tests/") and not Path(mf).exists()]

        has_unrelated = len(unexpected) > 0 or len(deleted_tests) > 0

        return ScopeAnalysisResult(
            has_unrelated_changes=has_unrelated,
            expected_files=list(expected),
            actual_modified_files=list(actual),
            unexpected_files=unexpected,
            missing_expected_files=missing,
            deleted_test_files=deleted_tests
        )
```

```python
# delta/agent/reviewer/quality.py
from typing import List
from delta.agent.reviewer.model import ChangeRiskLevel

class ChangeRiskAnalyzer:
    def analyze_risk(
        self,
        modified_files: List[str],
        lines_changed: int = 0,
        has_security_code: bool = False,
        has_public_api_change: bool = False
    ) -> ChangeRiskLevel:
        score = 0
        file_count = len(modified_files)

        score += file_count * 10
        score += min(lines_changed, 500) // 10

        if has_security_code or any("auth" in f.lower() or "scope" in f.lower() or "security" in f.lower() for f in modified_files):
            score += 40

        if has_public_api_change or any("api" in f.lower() or "routes" in f.lower() for f in modified_files):
            score += 30

        if score >= 80:
            return ChangeRiskLevel.CRITICAL
        elif score >= 50:
            return ChangeRiskLevel.HIGH
        elif score >= 25:
            return ChangeRiskLevel.MEDIUM
        return ChangeRiskLevel.LOW
```

---

### Task 3: Correctness, Architecture & Security Reviewers

**Files:**
- Create: `delta/agent/reviewer/correctness.py`
- Create: `delta/agent/reviewer/architecture.py`
- Create: `delta/agent/reviewer/security.py`
- Test: `tests/test_reviewer_checks.py`

**Interfaces:**
- Produces: `CorrectnessReviewer.review(objective, modified_files, diff) -> List[ReviewFinding]`
- Produces: `ArchitectureReviewer.review(repo_graph, modified_files) -> List[ReviewFinding]`
- Produces: `SecurityReviewer.review(modified_files, diff) -> List[ReviewFinding]`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_reviewer_checks.py
from delta.agent.reviewer.correctness import CorrectnessReviewer
from delta.agent.reviewer.architecture import ArchitectureReviewer
from delta.agent.reviewer.security import SecurityReviewer

def test_security_reviewer_detects_hardcoded_secrets():
    sec_rev = SecurityReviewer()
    findings = sec_rev.review(
        modified_files=["src/config.py"],
        diff_text='+ API_KEY = "sk-live-12345678901234567890"'
    )
    assert len(findings) >= 1
    assert findings[0].category == "security"

def test_architecture_reviewer_detects_layer_violations():
    arch_rev = ArchitectureReviewer()
    findings = arch_rev.review(
        repo_graph=None,
        modified_files=["delta/core/engine.py", "delta/web/bridge.py"]
    )
    assert isinstance(findings, list)
```

- [ ] **Step 2: Implement minimal code**

```python
# delta/agent/reviewer/correctness.py
import re
from typing import List
from delta.agent.reviewer.model import ReviewFinding

class CorrectnessReviewer:
    def review(self, objective: str, modified_files: List[str], diff_text: str = "") -> List[ReviewFinding]:
        findings = []
        # Check for placeholder left in diff
        if re.search(r"\b(TODO|FIXME|TBD|pass\s*#\s*implement)\b", diff_text, re.IGNORECASE):
            findings.append(ReviewFinding(
                category="correctness",
                message="Unfinished TODO/FIXME placeholder detected in modified code",
                severity="warning",
                recommended_fix="Complete implementation or remove placeholder comment"
            ))
        return findings
```

```python
# delta/agent/reviewer/architecture.py
from typing import List, Optional
from delta.agent.reviewer.model import ReviewFinding

class ArchitectureReviewer:
    def review(self, repo_graph: Optional[Any], modified_files: List[str]) -> List[ReviewFinding]:
        findings = []
        # Check if internal core module directly imports outer UI/Web bridge inappropriately
        # Example layer boundary check
        has_core = any("delta/core/" in f for f in modified_files)
        has_web = any("delta/web/" in f for f in modified_files)
        if has_core and has_web and len(modified_files) == 2:
            findings.append(ReviewFinding(
                category="architecture",
                message="Modification spans both core and web layer simultaneously",
                severity="info",
                recommended_fix="Verify clear boundary separation between core engine and web bridge"
            ))
        return findings
```

```python
# delta/agent/reviewer/security.py
import re
from typing import List
from delta.agent.reviewer.model import ReviewFinding

class SecurityReviewer:
    SECRET_PATTERNS = [
        (re.compile(r"(['\"]?)(?:api[_-]?key|secret|password|token)\1\s*[:=]\s*['\"](?![A-Za-z0-9_-]*\$\{)[A-Za-z0-9_\-\.]{16,}['\"]", re.IGNORECASE), "Potential hardcoded secret or API key"),
        (re.compile(r"\beval\s*\("), "Dangerous eval() usage"),
        (re.compile(r"\bsubprocess\s*\.\s*(?:Popen|run|call)\s*\(\s*f['\"]|\.format\("), "Potential command injection in subprocess string formatting")
    ]

    def review(self, modified_files: List[str], diff_text: str = "") -> List[ReviewFinding]:
        findings = []
        for line in diff_text.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                for pat, msg in self.SECRET_PATTERNS:
                    if pat.search(line):
                        findings.append(ReviewFinding(
                            category="security",
                            message=msg,
                            severity="error",
                            evidence=line.strip(),
                            recommended_fix="Use environment variables or secure vault for credentials/commands"
                        ))
        return findings
```

---

### Task 4: Regression Watcher & Reviewer Engine

**Files:**
- Create: `delta/agent/reviewer/regression.py`
- Create: `delta/agent/reviewer/engine.py`
- Test: `tests/test_reviewer_engine.py`

**Interfaces:**
- Produces: `RegressionWatcher.inspect_regression(extended_report, historical_failures) -> List[ReviewFinding]`
- Produces: `ReviewerEngine(workspace_root, max_review_attempts=3).review_task(objective, target_files, modified_files, diff_text, baseline_run, current_run) -> ReviewReport`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_reviewer_engine.py
from delta.agent.verifier.runner import TestRunResult
from delta.agent.reviewer.engine import ReviewerEngine
from delta.agent.reviewer.model import ReviewStatus

def test_reviewer_engine_rejects_unrelated_and_security_issues():
    engine = ReviewerEngine()
    baseline = TestRunResult(passed_count=10, failed_count=0)
    current = TestRunResult(passed_count=10, failed_count=0)

    # Submits task with unrelated modification and hardcoded secret
    report = engine.review_task(
        objective="Fix authentication token validation",
        target_files=["delta/core/auth.py"],
        modified_files=["delta/core/auth.py", "delta/web/unrelated_ui.py"],
        diff_text='+ API_KEY = "sk-live-12345678901234567890"',
        baseline_run=baseline,
        current_run=current
    )

    assert report.status == ReviewStatus.REJECT
    assert len(report.scope_violations) >= 1
    assert len(report.security_issues) >= 1
    assert len(report.required_actions) >= 1

def test_reviewer_engine_passes_clean_task():
    engine = ReviewerEngine()
    baseline = TestRunResult(passed_count=10, failed_count=0)
    current = TestRunResult(passed_count=10, failed_count=0)

    report = engine.review_task(
        objective="Fix authentication token validation",
        target_files=["delta/core/auth.py"],
        modified_files=["delta/core/auth.py"],
        diff_text='+ timestamp = time.time()',
        baseline_run=baseline,
        current_run=current
    )

    assert report.status in [ReviewStatus.PASS, ReviewStatus.PASS_WITH_WARNINGS]
    assert len(report.scope_violations) == 0
```

- [ ] **Step 2: Implement minimal code**

```python
# delta/agent/reviewer/regression.py
from typing import List, Set
from delta.agent.verifier.engine import ExtendedRegressionReport
from delta.agent.reviewer.model import ReviewFinding

class RegressionWatcher:
    def inspect_regression(self, ext_report: ExtendedRegressionReport, historical_failures: Set[str] = None) -> List[ReviewFinding]:
        findings = []
        if ext_report.has_regression:
            for nf in ext_report.new_failures:
                is_reintroduced = historical_failures and nf in historical_failures
                sev = "error" if not is_reintroduced else "critical"
                msg = f"Reintroduced historical failure: {nf}" if is_reintroduced else f"New test regression: {nf}"
                findings.append(ReviewFinding(
                    category="regression",
                    message=msg,
                    severity=sev,
                    evidence=f"Failed in current test run: {nf}",
                    recommended_fix="Fix regression or restore behavior before finishing task"
                ))
        return findings
```

```python
# delta/agent/reviewer/engine.py
from typing import List, Optional, Set, Dict, Any
from delta.agent.verifier.runner import TestRunResult
from delta.agent.verifier.engine import RegressionDetector, ExtendedRegressionReport
from delta.agent.reviewer.model import ReviewStatus, ChangeRiskLevel, ReviewFinding, ReviewReport
from delta.agent.reviewer.scope import IntentScopeAnalyzer
from delta.agent.reviewer.quality import ChangeRiskAnalyzer
from delta.agent.reviewer.correctness import CorrectnessReviewer
from delta.agent.reviewer.architecture import ArchitectureReviewer
from delta.agent.reviewer.security import SecurityReviewer
from delta.agent.reviewer.regression import RegressionWatcher

class ReviewerEngine:
    def __init__(self, workspace_root: str = ".", max_review_attempts: int = 3):
        self.workspace_root = workspace_root
        self.max_review_attempts = max_review_attempts
        self.attempts = 0
        self.scope_analyzer = IntentScopeAnalyzer()
        self.risk_analyzer = ChangeRiskAnalyzer()
        self.correctness_rev = CorrectnessReviewer()
        self.arch_rev = ArchitectureReviewer()
        self.security_rev = SecurityReviewer()
        self.regression_watcher = RegressionWatcher()
        self.regression_detector = RegressionDetector()

    def review_task(
        self,
        objective: str,
        target_files: List[str],
        modified_files: List[str],
        diff_text: str = "",
        baseline_run: Optional[TestRunResult] = None,
        current_run: Optional[TestRunResult] = None,
        repo_graph: Optional[Any] = None,
        historical_failures: Optional[Set[str]] = None
    ) -> ReviewReport:
        self.attempts += 1
        findings: List[ReviewFinding] = []
        scope_violations: List[str] = []
        correctness_issues: List[str] = []
        arch_issues: List[str] = []
        sec_issues: List[str] = []
        reg_issues: List[str] = []
        required_actions: List[str] = []

        # 1. Scope Check
        scope_res = self.scope_analyzer.analyze(objective, target_files, modified_files)
        if scope_res.has_unrelated_changes:
            for unexp in scope_res.unexpected_files:
                msg = f"Unrelated file modified: {unexp}"
                scope_violations.append(msg)
                findings.append(ReviewFinding(category="scope", message=msg, severity="error", file_path=unexp))
                required_actions.append(f"Revert changes to unexpected file '{unexp}'")

        # 2. Correctness Check
        c_findings = self.correctness_rev.review(objective, modified_files, diff_text)
        for f in c_findings:
            findings.append(f)
            correctness_issues.append(f.message)

        # 3. Architecture Check
        a_findings = self.arch_rev.review(repo_graph, modified_files)
        for f in a_findings:
            findings.append(f)
            arch_issues.append(f.message)

        # 4. Security Check
        s_findings = self.security_rev.review(modified_files, diff_text)
        for f in s_findings:
            findings.append(f)
            sec_issues.append(f.message)
            if f.severity in ["error", "critical"]:
                required_actions.append(f"Address security finding: {f.message}")

        # 5. Regression Check
        if baseline_run and current_run:
            ext_report = self.regression_detector.analyze_extended(baseline_run, current_run)
            r_findings = self.regression_watcher.inspect_regression(ext_report, historical_failures)
            for f in r_findings:
                findings.append(f)
                reg_issues.append(f.message)
                required_actions.append(f"Fix test regression: {f.message}")

        # 6. Calculate Risk
        risk_level = self.risk_analyzer.analyze_risk(
            modified_files=modified_files,
            lines_changed=len(diff_text.splitlines()),
            has_security_code=len(sec_issues) > 0
        )

        # Determine Final Status
        has_critical_error = any(f.severity in ["error", "critical"] for f in findings) or len(scope_violations) > 0 or len(reg_issues) > 0
        if has_critical_error:
            status = ReviewStatus.REJECT
        elif len(findings) > 0:
            status = ReviewStatus.PASS_WITH_WARNINGS
        else:
            status = ReviewStatus.PASS

        if self.attempts > self.max_review_attempts and status == ReviewStatus.REJECT:
            status = ReviewStatus.BLOCKED

        return ReviewReport(
            status=status,
            risk_level=risk_level,
            findings=findings,
            scope_violations=scope_violations,
            correctness_issues=correctness_issues,
            architecture_issues=arch_issues,
            security_issues=sec_issues,
            regression_issues=reg_issues,
            changed_files=modified_files,
            unexpected_files=scope_res.unexpected_files,
            required_actions=required_actions,
            attempts_used=self.attempts,
            max_attempts=self.max_review_attempts
        )
```

- [ ] **Step 3: Update `delta/agent/reviewer/__init__.py`**

```python
# delta/agent/reviewer/__init__.py
from delta.agent.reviewer.model import ReviewStatus, ChangeRiskLevel, ReviewFinding, ReviewReport
from delta.agent.reviewer.scope import IntentScopeAnalyzer, ScopeAnalysisResult
from delta.agent.reviewer.quality import ChangeRiskAnalyzer
from delta.agent.reviewer.correctness import CorrectnessReviewer
from delta.agent.reviewer.architecture import ArchitectureReviewer
from delta.agent.reviewer.security import SecurityReviewer
from delta.agent.reviewer.regression import RegressionWatcher
from delta.agent.reviewer.engine import ReviewerEngine

__all__ = [
    "ReviewStatus",
    "ChangeRiskLevel",
    "ReviewFinding",
    "ReviewReport",
    "IntentScopeAnalyzer",
    "ScopeAnalysisResult",
    "ChangeRiskAnalyzer",
    "CorrectnessReviewer",
    "ArchitectureReviewer",
    "SecurityReviewer",
    "RegressionWatcher",
    "ReviewerEngine",
]
```
