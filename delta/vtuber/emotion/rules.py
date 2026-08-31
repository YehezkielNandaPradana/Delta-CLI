"""
Deterministic rule-based mapping engine for AgentEvent context to VTuberEmotion and VTuberExpression.
"""

from typing import Any, Dict, Optional, Tuple
from delta.ai.events import AgentEvent, EventType
from delta.vtuber.emotion.schemas import VTuberEmotion, VTuberExpression


# Direct mapping from Emotion to logical Expression (Avatar-agnostic)
EMOTION_TO_EXPRESSION_MAP: Dict[VTuberEmotion, VTuberExpression] = {
    VTuberEmotion.NEUTRAL: VTuberExpression.NEUTRAL,
    VTuberEmotion.HAPPY: VTuberExpression.SMILE,
    VTuberEmotion.EXCITED: VTuberExpression.EXCITED,
    VTuberEmotion.CONFUSED: VTuberExpression.CONFUSED,
    VTuberEmotion.THINKING: VTuberExpression.THINKING,
    VTuberEmotion.SURPRISED: VTuberExpression.SURPRISED,
    VTuberEmotion.ANGRY: VTuberExpression.ANGRY,
    VTuberEmotion.SAD: VTuberExpression.SAD,
}


def map_emotion_to_expression(emotion: VTuberEmotion) -> VTuberExpression:
    """Map an emotion enum to its logical avatar expression."""
    return EMOTION_TO_EXPRESSION_MAP.get(emotion, VTuberExpression.NEUTRAL)


def resolve_emotion_from_event(event: AgentEvent) -> Tuple[VTuberEmotion, float, VTuberExpression]:
    """
    Context-aware deterministic resolution of emotion, intensity, and expression from an AgentEvent.
    Fast (O(1)), zero-LLM, deterministic rules.
    """
    ev_type = event.type if isinstance(event.type, EventType) else EventType(str(event.type))

    # 1. Agent Start / Thinking
    if ev_type == EventType.AGENT_START:
        return VTuberEmotion.THINKING, 0.60, VTuberExpression.THINKING

    if ev_type == EventType.AGENT_THINKING:
        return VTuberEmotion.THINKING, 0.65, VTuberExpression.THINKING

    # 2. Tool Execution Start
    if ev_type == EventType.TOOL_START:
        tool_name = (event.tool or "").lower()
        if any(kw in tool_name for kw in ["scan", "exploit", "pentest", "audit"]):
            return VTuberEmotion.THINKING, 0.70, VTuberExpression.THINKING
        return VTuberEmotion.THINKING, 0.60, VTuberExpression.THINKING

    # 3. Tool Result
    if ev_type == EventType.TOOL_RESULT:
        is_success = event.success if event.success is not None else True
        if is_success:
            # Successful tool execution
            return VTuberEmotion.HAPPY, 0.65, VTuberExpression.SMILE
        else:
            # Tool failure (agent will recover)
            return VTuberEmotion.CONFUSED, 0.55, VTuberExpression.CONFUSED

    # 4. Message Complete / Speaking
    if ev_type == EventType.MESSAGE_COMPLETE:
        content = (event.content or "").lower()
        if any(kw in content for kw in ["berhasil", "sukses", "selesai", "found", "discovered", "congratulations"]):
            return VTuberEmotion.HAPPY, 0.75, VTuberExpression.SMILE
        return VTuberEmotion.NEUTRAL, 0.40, VTuberExpression.NEUTRAL

    # 5. Agent Completion
    if ev_type == EventType.AGENT_COMPLETE:
        return VTuberEmotion.HAPPY, 0.80, VTuberExpression.SMILE

    # 6. Errors
    if ev_type == EventType.ERROR:
        err_str = str(event.error or "").lower()
        if any(kw in err_str for kw in ["fatal", "crash", "refused", "timeout", "abort"]):
            return VTuberEmotion.SAD, 0.85, VTuberExpression.SAD
        return VTuberEmotion.CONFUSED, 0.70, VTuberExpression.CONFUSED

    # Default fallback
    return VTuberEmotion.NEUTRAL, 0.30, VTuberExpression.NEUTRAL
