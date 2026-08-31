# delta/agent/debugger/hypotheses.py
from dataclasses import dataclass, field
from typing import List
from delta.agent.debugger.model import TestFailure, FailureClassification
from delta.agent.debugger.evidence import DebugEvidence

@dataclass
class Hypothesis:
    id: str
    description: str
    evidence_sources: List[str] = field(default_factory=list)
    confidence_score: float = 0.5
    proposed_remediation: str = ""

class HypothesisEngine:
    def generate_and_rank(self, failure: TestFailure, evidence: DebugEvidence) -> List[Hypothesis]:
        hypotheses = []
        if failure.classification == FailureClassification.SYNTAX_ERROR:
            hypotheses.append(Hypothesis(
                id="H1",
                description="Syntax error in recently modified file",
                evidence_sources=["raw_output", "modified_files"],
                confidence_score=0.9,
                proposed_remediation="Revert invalid syntax edit"
            ))
        elif failure.classification == FailureClassification.IMPORT_ERROR:
            hypotheses.append(Hypothesis(
                id="H1",
                description="Missing module import or unresolved dependency",
                evidence_sources=["stack_trace"],
                confidence_score=0.85,
                proposed_remediation="Insert missing import or install package"
            ))
        else:
            hypotheses.append(Hypothesis(
                id="H1",
                description=f"Logic mismatch in modified file(s): {', '.join(evidence.modified_files)}",
                evidence_sources=["modified_files", "test_failure_message"],
                confidence_score=0.7,
                proposed_remediation="Adjust logic implementation in modified file to satisfy assertion"
            ))
        return hypotheses
