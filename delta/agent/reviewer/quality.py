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
