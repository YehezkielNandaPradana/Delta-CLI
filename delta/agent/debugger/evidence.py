# delta/agent/debugger/evidence.py
from dataclasses import dataclass, field
from typing import List, Any

@dataclass
class DebugEvidence:
    failing_test_id: str
    error_message: str
    stack_trace: str
    modified_files: List[str] = field(default_factory=list)
    relevant_symbols: List[str] = field(default_factory=list)
    git_diff_summary: str = ""

class DebugEvidenceCollector:
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = workspace_root

    def collect_evidence(self, failure: Any, modified_files: List[str]) -> DebugEvidence:
        return DebugEvidence(
            failing_test_id=getattr(failure, "test_id", "unknown_test"),
            error_message=getattr(failure, "message", ""),
            stack_trace=getattr(failure, "stack_trace", ""),
            modified_files=modified_files,
            relevant_symbols=list(modified_files),
            git_diff_summary="Modified: " + ", ".join(modified_files)
        )
