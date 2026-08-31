# delta/agent/debugger/engine.py
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional
from delta.agent.debugger.model import TestFailure, FailureClassification
from delta.agent.debugger.classifier import FailureClassifier
from delta.agent.debugger.evidence import DebugEvidenceCollector, DebugEvidence
from delta.agent.debugger.hypotheses import HypothesisEngine
from delta.agent.debugger.root_cause import RootCauseAnalyzer, RootCause

class DebuggerStatus(str, Enum):
    IDLE = "idle"
    DIAGNOSED = "diagnosed"
    PATCH_RECOMMENDED = "patch_recommended"
    DEBUG_EXHAUSTED = "debug_exhausted"

@dataclass
class DebuggerReport:
    status: DebuggerStatus
    classification: FailureClassification
    evidence: Optional[DebugEvidence] = None
    root_cause: Optional[RootCause] = None
    attempts_used: int = 0
    max_attempts: int = 3

class DebuggerEngine:
    def __init__(self, workspace_root: str = ".", max_debug_attempts: int = 3):
        self.workspace_root = workspace_root
        self.max_debug_attempts = max_debug_attempts
        self.attempts = 0
        self.classifier = FailureClassifier()
        self.evidence_collector = DebugEvidenceCollector(workspace_root)
        self.hypothesis_engine = HypothesisEngine()
        self.root_cause_analyzer = RootCauseAnalyzer()

    def diagnose(self, failure: TestFailure, modified_files: List[str]) -> DebuggerReport:
        if self.attempts >= self.max_debug_attempts:
            return DebuggerReport(
                status=DebuggerStatus.DEBUG_EXHAUSTED,
                classification=failure.classification,
                attempts_used=self.attempts,
                max_attempts=self.max_debug_attempts
            )

        self.attempts += 1
        classification = self.classifier.classify(failure)
        failure.classification = classification

        evidence = self.evidence_collector.collect_evidence(failure, modified_files)
        hypotheses = self.hypothesis_engine.generate_and_rank(failure, evidence)
        root_cause = self.root_cause_analyzer.analyze(hypotheses)

        return DebuggerReport(
            status=DebuggerStatus.DIAGNOSED,
            classification=classification,
            evidence=evidence,
            root_cause=root_cause,
            attempts_used=self.attempts,
            max_attempts=self.max_debug_attempts
        )
