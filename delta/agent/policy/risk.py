from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any

class ToolRisk(str, Enum):
    READ = "READ"
    LOW_WRITE = "LOW_WRITE"
    WRITE = "WRITE"
    HIGH_IMPACT = "HIGH_IMPACT"

    @property
    def level(self) -> int:
        levels = {
            "READ": 10,
            "LOW_WRITE": 20,
            "WRITE": 30,
            "HIGH_IMPACT": 40
        }
        return levels[self.value]

@dataclass
class PolicyDecision:
    allowed: bool
    requires_confirmation: bool
    requires_checkpoint: bool
    risk_level: ToolRisk
    reason: str
    rollback_strategy: Optional[str] = None
    scope: str = "workspace"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "requires_confirmation": self.requires_confirmation,
            "requires_checkpoint": self.requires_checkpoint,
            "risk_level": self.risk_level.value,
            "reason": self.reason,
            "rollback_strategy": self.rollback_strategy,
            "scope": self.scope
        }
