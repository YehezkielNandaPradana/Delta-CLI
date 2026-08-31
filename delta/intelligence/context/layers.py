import math
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

class LayerPriority(str, Enum):
    P1_CRITICAL = "P1_CRITICAL"  # Invariants, active step, active code (Never prune)
    P2_HIGH = "P2_HIGH"          # Related symbols, direct dependencies
    P3_MEDIUM = "P3_MEDIUM"      # Architecture summary, decision history
    P4_LOW = "P4_LOW"            # Repo-wide file tree, verbose stats

    @property
    def weight(self) -> int:
        weights = {
            "P1_CRITICAL": 10,
            "P2_HIGH": 20,
            "P3_MEDIUM": 30,
            "P4_LOW": 40
        }
        return weights[self.value]

class ContextLayerType(str, Enum):
    L0_TASK = "L0_TASK"
    L1_FILES = "L1_FILES"
    L2_SYMBOLS = "L2_SYMBOLS"
    L3_DEPENDENCY = "L3_DEPENDENCY"
    L4_DIAGNOSTIC = "L4_DIAGNOSTIC"
    L5_ARCHITECTURE = "L5_ARCHITECTURE"
    L6_HISTORY = "L6_HISTORY"
    L7_REPO_WIDE = "L7_REPO_WIDE"

@dataclass
class ContextItem:
    layer_type: ContextLayerType
    priority: LayerPriority
    content: str
    name: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    token_estimate: int = 0

    def __post_init__(self):
        if not self.token_estimate:
            # Heuristic estimate: ~4 characters per token
            self.token_estimate = max(1, math.ceil(len(self.content) / 4))

    @property
    def is_prunable(self) -> bool:
        return self.priority != LayerPriority.P1_CRITICAL
