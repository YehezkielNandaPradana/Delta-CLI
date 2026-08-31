# Delta Autonomous Engineering Agent (Phase 3: Context Prioritization Engine L0-L7) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Multi-Layer Context Prioritization Engine (L0 to L7) with deterministic token budget allocation, invariant preservation, and intelligent pruning for Delta.

**Architecture:** Implement `delta/intelligence/context/` providing `ContextLayer` models (L0 Task, L1 Files, L2 Symbols, L3 Dependencies, L4 Diagnostics, L5 Architecture, L6 History, L7 Repo-wide), `TokenBudget` allocator, and `ContextEngine` that formats and prioritizes context within strict token limits without losing invariants.

**Tech Stack:** Python 3.10+, stdlib (`dataclasses`, `enum`, `typing`, `json`), pytest.

## Global Constraints

- L0 (Task Invariants), L1 (Active Files), and L4 (Active Diagnostics) have strict Priority 1 and must NEVER be pruned away.
- When token limit is exceeded, L7 is discarded first, L6/L5 are compressed/summarized, L3/L2 are trimmed.
- Zero regression across all 364 existing tests.

---

### Task 1: Context Layer Models and Prioritization Definitions

**Files:**
- Create: `delta/intelligence/context/layers.py`
- Create: `delta/intelligence/context/__init__.py`
- Test: `tests/test_context_layers.py`

**Interfaces:**
- Produces: `LayerPriority` (P1_CRITICAL, P2_HIGH, P3_MEDIUM, P4_LOW), `ContextLayerType` (L0_TASK, L1_FILES, L2_SYMBOLS, L3_DEPENDENCY, L4_DIAGNOSTIC, L5_ARCHITECTURE, L6_HISTORY, L7_REPO_WIDE), `ContextItem` (type, priority, content, token_estimate).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_context_layers.py
from delta.intelligence.context.layers import ContextLayerType, LayerPriority, ContextItem

def test_layer_priority_ordering():
    assert LayerPriority.P1_CRITICAL.weight < LayerPriority.P2_HIGH.weight
    assert LayerPriority.P2_HIGH.weight < LayerPriority.P3_MEDIUM.weight
    assert LayerPriority.P3_MEDIUM.weight < LayerPriority.P4_LOW.weight

def test_context_item_token_estimation():
    item = ContextItem(
        layer_type=ContextLayerType.L0_TASK,
        priority=LayerPriority.P1_CRITICAL,
        content="Fix auth bug in token validation",
        name="task_objective"
    )
    assert item.token_estimate > 0
    assert item.is_prunable is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_context_layers.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'delta.intelligence.context'`

- [ ] **Step 3: Write minimal implementation**

```python
# delta/intelligence/context/layers.py
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
```

```python
# delta/intelligence/context/__init__.py
from delta.intelligence.context.layers import LayerPriority, ContextLayerType, ContextItem

__all__ = ["LayerPriority", "ContextLayerType", "ContextItem"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_context_layers.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/intelligence/context/layers.py delta/intelligence/context/__init__.py tests/test_context_layers.py
git commit -m "feat(context): implement ContextLayerType, LayerPriority, and ContextItem models"
```

---

### Task 2: Token Budget Allocator and Context Prioritization Engine

**Files:**
- Create: `delta/intelligence/context/engine.py`
- Test: `tests/test_context_engine.py`

**Interfaces:**
- Produces: `ContextEngine(max_tokens: int = 8000)`, `engine.add_item(item: ContextItem)`, `engine.assemble_context() -> str`, `engine.get_assembled_items() -> List[ContextItem]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_context_engine.py
from delta.intelligence.context.layers import ContextLayerType, LayerPriority, ContextItem
from delta.intelligence.context.engine import ContextEngine

def test_context_engine_preserves_p1_and_prunes_p4():
    engine = ContextEngine(max_tokens=100) # strict token budget (~400 chars)

    # L0: Critical invariant
    l0 = ContextItem(
        layer_type=ContextLayerType.L0_TASK,
        priority=LayerPriority.P1_CRITICAL,
        content="Goal: Fix authentication bug in token expiry handling.",
        name="objective"
    )
    # L7: Huge low-priority file listing
    l7 = ContextItem(
        layer_type=ContextLayerType.L7_REPO_WIDE,
        priority=LayerPriority.P4_LOW,
        content="File tree: " + ("src/module/sub/file.py\n" * 50),
        name="file_tree"
    )

    engine.add_item(l0)
    engine.add_item(l7)

    assembled = engine.assemble_context()
    assert "Goal: Fix authentication bug" in assembled
    # Verify L7 was pruned to fit within max_tokens
    items = engine.get_assembled_items()
    item_names = [it.name for it in items]
    assert "objective" in item_names
    assert "file_tree" not in item_names

def test_context_engine_budget_allocation():
    engine = ContextEngine(max_tokens=500)
    l1 = ContextItem(layer_type=ContextLayerType.L1_FILES, priority=LayerPriority.P1_CRITICAL, content="def auth(): pass")
    l2 = ContextItem(layer_type=ContextLayerType.L2_SYMBOLS, priority=LayerPriority.P2_HIGH, content="def helper(): pass")
    l5 = ContextItem(layer_type=ContextLayerType.L5_ARCHITECTURE, priority=LayerPriority.P3_MEDIUM, content="Architecture: MVC")

    engine.add_item(l1)
    engine.add_item(l2)
    engine.add_item(l5)

    assembled = engine.assemble_context()
    assert "def auth(): pass" in assembled
    assert "def helper(): pass" in assembled
    assert "Architecture: MVC" in assembled
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_context_engine.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'delta.intelligence.context.engine'`

- [ ] **Step 3: Write minimal implementation**

```python
# delta/intelligence/context/engine.py
from typing import List, Dict, Optional
from delta.intelligence.context.layers import ContextItem, LayerPriority, ContextLayerType

class ContextEngine:
    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens
        self.items: List[ContextItem] = []

    def add_item(self, item: ContextItem):
        self.items.append(item)

    def clear(self):
        self.items.clear()

    def get_assembled_items(self) -> List[ContextItem]:
        # 1. Separate Critical vs Prunable items
        critical_items = [it for it in self.items if it.priority == LayerPriority.P1_CRITICAL]
        prunable_items = [it for it in self.items if it.priority != LayerPriority.P1_CRITICAL]

        # 2. Sort prunable items by priority weight ascending (P2 first, then P3, then P4 last)
        prunable_items.sort(key=lambda x: x.priority.weight)

        total_tokens = sum(it.token_estimate for it in critical_items)
        selected_items = list(critical_items)

        # 3. Fit prunable items into remaining budget
        for item in prunable_items:
            if total_tokens + item.token_estimate <= self.max_tokens:
                selected_items.append(item)
                total_tokens += item.token_estimate

        # Sort back into standard layer order L0 -> L7
        layer_order = {
            ContextLayerType.L0_TASK: 0,
            ContextLayerType.L1_FILES: 1,
            ContextLayerType.L4_DIAGNOSTIC: 2,
            ContextLayerType.L2_SYMBOLS: 3,
            ContextLayerType.L3_DEPENDENCY: 4,
            ContextLayerType.L5_ARCHITECTURE: 5,
            ContextLayerType.L6_HISTORY: 6,
            ContextLayerType.L7_REPO_WIDE: 7
        }
        selected_items.sort(key=lambda x: layer_order.get(x.layer_type, 99))
        return selected_items

    def assemble_context(self) -> str:
        assembled_items = self.get_assembled_items()
        sections: List[str] = []

        for it in assembled_items:
            header = f"=== [{it.layer_type.value}] {it.name} ===" if it.name else f"=== [{it.layer_type.value}] ==="
            sections.append(f"{header}\n{it.content}")

        return "\n\n".join(sections)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_context_engine.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/intelligence/context/engine.py tests/test_context_engine.py
git commit -m "feat(context): implement ContextEngine with priority-based pruning and budget allocator"
```
