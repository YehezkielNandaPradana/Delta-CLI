# tests/test_verifier_hardening.py
import tempfile
from delta.agent.verifier.runner import AutoTestRunner, TestRunResult
from delta.agent.verifier.engine import RegressionDetector, ExtendedRegressionReport

def test_auto_test_runner_handles_missing_executable():
    runner = AutoTestRunner()
    res = runner.run_tests(test_command="non_existent_test_runner_command_12345")
    assert res.exit_code != 0
    assert "environment_error" in res.failed_tests or "not found" in res.raw_output.lower()

def test_regression_detector_distinguishes_pre_existing_and_resolved():
    baseline = TestRunResult(
        passed_count=5, failed_count=2,
        passed_tests=["test_a", "test_b"],
        failed_tests=["test_old_fail_1", "test_old_fail_2"]
    )
    current = TestRunResult(
        passed_count=6, failed_count=2,
        passed_tests=["test_a", "test_b", "test_old_fail_1"],
        failed_tests=["test_old_fail_2", "test_new_bug"]
    )
    detector = RegressionDetector()
    report = detector.analyze_extended(baseline=baseline, current=current)
    assert "test_new_bug" in report.new_failures
    assert "test_old_fail_2" in report.pre_existing_failures
    assert "test_old_fail_1" in report.resolved_failures
    assert report.has_regression is True
