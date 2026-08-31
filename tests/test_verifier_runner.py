# tests/test_verifier_runner.py
import tempfile
import os
from delta.agent.verifier.runner import AutoTestRunner, TestRunResult

def test_auto_test_runner_python_execution():
    with tempfile.TemporaryDirectory() as tmp:
        test_file = os.path.join(tmp, "test_sample.py")
        with open(test_file, "w") as f:
            f.write("def test_ok(): assert True\n")

        runner = AutoTestRunner(workspace_root=tmp)
        res = runner.run_tests(test_command="pytest", target_file="test_sample.py")
        assert isinstance(res, TestRunResult)
        assert res.exit_code == 0
        assert res.passed_count >= 1
        assert res.failed_count == 0
