# delta/agent/debugger/model.py
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class FailureClassification(str, Enum):
    CODE_ERROR = "CODE_ERROR"
    TYPE_ERROR = "TYPE_ERROR"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    IMPORT_ERROR = "IMPORT_ERROR"
    ASSERTION_FAILURE = "ASSERTION_FAILURE"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    ENVIRONMENT_ERROR = "ENVIRONMENT_ERROR"
    TIMEOUT = "TIMEOUT"
    FLAKY_CANDIDATE = "FLAKY_CANDIDATE"
    UNKNOWN = "UNKNOWN"

@dataclass
class TestFailure:
    test_id: str
    framework: str = "pytest"
    file: Optional[str] = None
    line: Optional[int] = None
    error_type: Optional[str] = None
    message: str = ""
    stack_trace: str = ""
    raw_output: str = ""
    exit_code: int = 1
    classification: FailureClassification = FailureClassification.UNKNOWN
