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
