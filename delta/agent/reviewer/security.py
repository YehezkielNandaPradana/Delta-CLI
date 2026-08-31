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
