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
        if target_file and (self.workspace / target_file).exists():
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
        except FileNotFoundError as e:
            return TestRunResult(
                passed_count=0,
                failed_count=1,
                failed_tests=["environment_error"],
                raw_output=f"Test runner executable not found: {cmd_parts[0]}",
                exit_code=127,
                duration_ms=0.0
            )
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

        m_pytest = re.search(r"(\d+)\s+passed", raw)
        if m_pytest:
            passed_cnt = int(m_pytest.group(1))

        m_failed = re.search(r"(\d+)\s+failed", raw)
        if m_failed:
            failed_cnt = int(m_failed.group(1))

        for line in raw.splitlines():
            if line.startswith("FAILED ") or ("::" in line and "FAIL" in line):
                parts = line.split()
                if len(parts) >= 2:
                    failed_names.append(parts[1])

        return passed_cnt, failed_cnt, passed_names, failed_names
