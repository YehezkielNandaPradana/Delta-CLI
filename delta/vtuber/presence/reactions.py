"""
Deterministic Contextual Micro-Reaction Engine for Delta VTuber Companion.
Generates subtle non-blocking emotional/expression reactions without LLM calls.
"""

from typing import Optional, Tuple
from delta.ai.events import AgentEvent, EventType
from delta.vtuber.emotion.schemas import VTuberEmotion, VTuberExpression


class MicroReactionEngine:
    """
    Evaluates agent lifecycle events in O(1) time and yields subtle companion micro-reactions.
    """

    @classmethod
    def evaluate_reaction(cls, event: AgentEvent) -> Optional[Tuple[VTuberEmotion, float, str]]:
        """
        Returns (emotion, intensity, short_reaction_phrase) or None if no reaction triggered.
        """
        ev_type = event.type if isinstance(event.type, EventType) else EventType(str(event.type))

        if ev_type == EventType.TOOL_START:
            tool_name = (event.tool or "").lower()
            if any(k in tool_name for k in ["scan", "audit", "exploit"]):
                return VTuberEmotion.THINKING, 0.65, "Mengecek target..."
            return VTuberEmotion.THINKING, 0.55, "Sedang bekerja..."

        if ev_type == EventType.TOOL_RESULT:
            if event.success:
                return VTuberEmotion.HAPPY, 0.60, "Beres."
            else:
                return VTuberEmotion.CONFUSED, 0.55, "Hmm, ada kendala di tool."

        if ev_type == EventType.AGENT_COMPLETE:
            return VTuberEmotion.HAPPY, 0.75, "Semua tugas selesai."

        if ev_type == EventType.ERROR:
            return VTuberEmotion.CONFUSED, 0.70, "Terjadi kesalahan sistem."

        return None
