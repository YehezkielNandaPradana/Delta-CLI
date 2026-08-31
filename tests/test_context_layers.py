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
