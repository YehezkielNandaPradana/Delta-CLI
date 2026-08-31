# delta/agent/reviewer/scope.py
from dataclasses import dataclass, field
from typing import List
from pathlib import Path

@dataclass
class ScopeAnalysisResult:
    has_unrelated_changes: bool
    expected_files: List[str] = field(default_factory=list)
    actual_modified_files: List[str] = field(default_factory=list)
    unexpected_files: List[str] = field(default_factory=list)
    missing_expected_files: List[str] = field(default_factory=list)
    deleted_test_files: List[str] = field(default_factory=list)

class IntentScopeAnalyzer:
    def analyze(self, objective: str, target_files: List[str], modified_files: List[str]) -> ScopeAnalysisResult:
        expected = set(target_files)
        actual = set(modified_files)

        unexpected = []
        for mf in actual:
            if expected and mf not in expected:
                mf_stem = Path(mf).stem.lower()
                is_related = any(Path(ef).stem.lower() in mf_stem or mf_stem in Path(ef).stem.lower() for ef in expected)
                if not is_related and not mf.startswith("tests/"):
                    unexpected.append(mf)

        missing = list(expected - actual)
        deleted_tests = [mf for mf in actual if mf.startswith("tests/") and not Path(mf).exists()]

        has_unrelated = len(unexpected) > 0 or len(deleted_tests) > 0

        return ScopeAnalysisResult(
            has_unrelated_changes=has_unrelated,
            expected_files=list(expected),
            actual_modified_files=list(actual),
            unexpected_files=unexpected,
            missing_expected_files=missing,
            deleted_test_files=deleted_tests
        )
