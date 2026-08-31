# delta/agent/debugger/classifier.py
from delta.agent.debugger.model import TestFailure, FailureClassification

class FailureClassifier:
    def classify(self, failure: TestFailure) -> FailureClassification:
        text = (failure.message + "\n" + failure.raw_output + "\n" + failure.stack_trace).lower()

        if "syntaxerror" in text or "parseerror" in text or "unexpected token" in text:
            return FailureClassification.SYNTAX_ERROR
        if "modulenotfounderror" in text or "importerror" in text or "cannot find module" in text:
            return FailureClassification.IMPORT_ERROR
        if "typeerror" in text or "attributeerror" in text or "argumentcounterror" in text:
            return FailureClassification.TYPE_ERROR
        if "assertionerror" in text or ("expected" in text and "got" in text):
            return FailureClassification.ASSERTION_FAILURE
        if "connectionrefused" in text or "econnrefused" in text or "command not found" in text or "environment_error" in text:
            return FailureClassification.ENVIRONMENT_ERROR
        if "timeout" in text or "timed out" in text:
            return FailureClassification.TIMEOUT
        if "keyerror" in text or "indexerror" in text or "zero-division" in text or "runtimeerror" in text:
            return FailureClassification.RUNTIME_ERROR

        return FailureClassification.UNKNOWN
