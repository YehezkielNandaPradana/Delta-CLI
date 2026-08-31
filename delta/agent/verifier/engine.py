# delta/agent/verifier/engine.py
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path
from delta.agent.verifier.runner import AutoTestRunner, TestRunResult

@dataclass
class ExtendedRegressionReport:
    has_regression: bool
    new_failures: List[str] = field(default_factory=list)
    pre_existing_failures: List[str] = field(default_factory=list)
    resolved_failures: List[str] = field(default_factory=list)
    flaky_candidates: List[str] = field(default_factory=list)
    environment_failures: List[str] = field(default_factory=list)
    baseline_failed_count: int = 0
    current_failed_count: int = 0
    summary: str = ""

@dataclass
class RegressionReport:
    has_regression: bool
    new_failures: List[str] = field(default_factory=list)
    baseline_failed_count: int = 0
    current_failed_count: int = 0
    summary: str = ""

class RegressionDetector:
    def analyze(self, baseline: TestRunResult, current: TestRunResult) -> RegressionReport:
        ext = self.analyze_extended(baseline, current)
        return RegressionReport(
            has_regression=ext.has_regression,
            new_failures=ext.new_failures,
            baseline_failed_count=ext.baseline_failed_count,
            current_failed_count=ext.current_failed_count,
            summary=ext.summary
        )

    def analyze_extended(self, baseline: TestRunResult, current: TestRunResult) -> ExtendedRegressionReport:
        baseline_failed_set = set(baseline.failed_tests)
        current_failed_set = set(current.failed_tests)
        current_passed_set = set(current.passed_tests)

        new_fails = list(current_failed_set - baseline_failed_set)
        pre_existing = list(current_failed_set & baseline_failed_set)
        resolved = list(baseline_failed_set & current_passed_set)
        env_fails = [f for f in current.failed_tests if "environment_error" in f or "timeout" in f]

        has_regressed = len(new_fails) > 0 or (current.exit_code != 0 and baseline.exit_code == 0 and not env_fails)

        summary = "No regression detected."
        if has_regressed:
            summary = f"Regression detected! {len(new_fails)} new failing test(s): {', '.join(new_fails)}"

        return ExtendedRegressionReport(
            has_regression=has_regressed,
            new_failures=new_fails,
            pre_existing_failures=pre_existing,
            resolved_failures=resolved,
            flaky_candidates=[],
            environment_failures=env_fails,
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
    ) -> ExtendedRegressionReport:
        suggested_tests = self.mapper.suggest_test_files(modified_files)
        target = suggested_tests[0] if suggested_tests else None

        current = self.runner.run_tests(test_command=test_command, target_file=target)
        return self.detector.analyze_extended(baseline=baseline, current=current)
