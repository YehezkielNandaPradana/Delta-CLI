# delta/agent/debugger/root_cause.py
from dataclasses import dataclass, field
from typing import List, Optional
from delta.agent.debugger.hypotheses import Hypothesis

@dataclass
class RootCause:
    summary: str
    recommended_action: str
    top_hypothesis: Optional[Hypothesis] = None
    supporting_evidence: List[str] = field(default_factory=list)

class RootCauseAnalyzer:
    def analyze(self, hypotheses: List[Hypothesis]) -> RootCause:
        if not hypotheses:
            return RootCause(
                summary="Unknown root cause; insufficient evidence gathered",
                recommended_action="Gather broader logs or manual inspection"
            )
        top = hypotheses[0]
        return RootCause(
            summary=top.description,
            recommended_action=top.proposed_remediation,
            top_hypothesis=top,
            supporting_evidence=top.evidence_sources
        )
