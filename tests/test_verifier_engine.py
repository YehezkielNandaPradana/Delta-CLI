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
