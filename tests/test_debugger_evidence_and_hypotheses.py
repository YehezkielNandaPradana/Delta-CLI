# tests/test_debugger_evidence_and_hypotheses.py
from delta.agent.debugger.model import TestFailure
from delta.agent.debugger.evidence import DebugEvidenceCollector
from delta.agent.debugger.hypotheses import HypothesisEngine
from delta.agent.debugger.root_cause import RootCauseAnalyzer

def test_hypothesis_generation_and_ranking():
    fail = TestFailure(
        test_id="tests/test_auth.py::test_validate_token",
        message="AssertionError: Expected True but got False",
        raw_output="AssertionError: Expected True but got False"
    )
    collector = DebugEvidenceCollector()
    evidence = collector.collect_evidence(fail, modified_files=["delta/auth/token.py"])
    assert "delta/auth/token.py" in evidence.modified_files

    engine = HypothesisEngine()
    hypotheses = engine.generate_and_rank(fail, evidence)
    assert len(hypotheses) >= 1
    assert hypotheses[0].confidence_score > 0.0

    analyzer = RootCauseAnalyzer()
    root_cause = analyzer.analyze(hypotheses)
    assert root_cause.summary != ""
    assert root_cause.recommended_action != ""
