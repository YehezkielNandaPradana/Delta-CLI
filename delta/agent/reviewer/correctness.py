# delta/agent/reviewer/correctness.py
import re
from typing import List
from delta.agent.reviewer.model import ReviewFinding

class CorrectnessReviewer:
    def review(self, objective: str, modified_files: List[str], diff_text: str = "") -> List[ReviewFinding]:
        findings = []
        if re.search(r"\b(TODO|FIXME|TBD|pass\s*#\s*implement)\b", diff_text, re.IGNORECASE):
            findings.append(ReviewFinding(
                category="correctness",
                message="Unfinished TODO/FIXME placeholder detected in modified code",
                severity="warning",
                recommended_fix="Complete implementation or remove placeholder comment"
            ))
        return findings
