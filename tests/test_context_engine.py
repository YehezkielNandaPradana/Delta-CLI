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
