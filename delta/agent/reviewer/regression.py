# delta/agent/reviewer/regression.py
from typing import List, Optional, Set
from delta.agent.verifier.engine import ExtendedRegressionReport
from delta.agent.reviewer.model import ReviewFinding

class RegressionWatcher:
    def inspect_regression(self, ext_report: ExtendedRegressionReport, historical_failures: Optional[Set[str]] = None) -> List[ReviewFinding]:
        findings = []
        if ext_report.has_regression:
            for nf in ext_report.new_failures:
                is_reintroduced = historical_failures is not None and nf in historical_failures
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
