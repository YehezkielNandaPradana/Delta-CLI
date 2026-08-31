# delta/agent/reviewer/model.py
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional

class ReviewStatus(str, Enum):
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    REJECT = "REJECT"
    BLOCKED = "BLOCKED"

class ChangeRiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class ReviewFinding:
    category: str
    message: str
    severity: str = "warning"
    evidence: str = ""
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    recommended_fix: str = ""

@dataclass
class ReviewReport:
    status: ReviewStatus
    risk_level: ChangeRiskLevel = ChangeRiskLevel.LOW
    findings: List[ReviewFinding] = field(default_factory=list)
    scope_violations: List[str] = field(default_factory=list)
    correctness_issues: List[str] = field(default_factory=list)
    architecture_issues: List[str] = field(default_factory=list)
    security_issues: List[str] = field(default_factory=list)
    regression_issues: List[str] = field(default_factory=list)
    quality_issues: List[str] = field(default_factory=list)
    changed_files: List[str] = field(default_factory=list)
    unexpected_files: List[str] = field(default_factory=list)
    missing_tests: List[str] = field(default_factory=list)
    required_actions: List[str] = field(default_factory=list)
    attempts_used: int = 1
    max_attempts: int = 3
