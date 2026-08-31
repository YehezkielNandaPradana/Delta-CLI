# tests/test_debugger_classifier.py
from delta.agent.debugger.model import TestFailure, FailureClassification
from delta.agent.debugger.classifier import FailureClassifier

def test_classify_syntax_error():
    fail = TestFailure(
        test_id="test_parse",
        raw_output="SyntaxError: invalid syntax in src/auth.py line 42",
        message="SyntaxError"
    )
    classifier = FailureClassifier()
    cls = classifier.classify(fail)
    assert cls == FailureClassification.SYNTAX_ERROR

def test_classify_import_error():
    fail = TestFailure(
        test_id="test_import",
        raw_output="ModuleNotFoundError: No module named 'jwt'",
        message="ModuleNotFoundError"
    )
    classifier = FailureClassifier()
    cls = classifier.classify(fail)
    assert cls == FailureClassification.IMPORT_ERROR

def test_classify_unknown_when_ambiguous():
    fail = TestFailure(
        test_id="test_weird",
        raw_output="Something custom happened without standard trace",
        message="Custom string"
    )
    classifier = FailureClassifier()
    cls = classifier.classify(fail)
    assert cls == FailureClassification.UNKNOWN
