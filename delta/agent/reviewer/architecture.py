# delta/agent/reviewer/architecture.py
from typing import List, Optional, Any
from delta.agent.reviewer.model import ReviewFinding

class ArchitectureReviewer:
    def review(self, repo_graph: Optional[Any], modified_files: List[str]) -> List[ReviewFinding]:
        findings = []
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
