"""
Emotion Engine for Delta VTuber.
Maintains emotion lifecycle state, applies deterministic rules, suppresses duplicate transitions,
and emits EmotionChangedEvent instances to VTuberEventBus.
"""

import logging
from typing import Any, Callable, Dict, Optional, Set
from delta.ai.events import AgentEvent
from delta.vtuber.emotion.schemas import (
    EmotionChangedEvent,
    EmotionResult,
    VTuberEmotion,
    VTuberExpression,
)
from delta.vtuber.emotion.rules import (
    map_emotion_to_expression,
    resolve_emotion_from_event,
)
from delta.vtuber.event_bus import VTuberEventBus, vtuber_event_bus

logger = logging.getLogger(__name__)


class EmotionEngine:
    """
    Stateful Emotion Engine maintaining current VTuber emotion, calculating context-aware
    transitions, suppressing redundant duplicate transitions, and broadcasting to EventBus.
    """

    def __init__(
        self,
        initial_emotion: VTuberEmotion = VTuberEmotion.NEUTRAL,
        initial_intensity: float = 0.3,
        event_bus: Optional[VTuberEventBus] = None,
        auto_emit: bool = True,
    ):
        self._current_emotion: VTuberEmotion = initial_emotion
        self._current_intensity: float = max(0.0, min(1.0, initial_intensity))
        self._current_expression: VTuberExpression = map_emotion_to_expression(initial_emotion)
        self.event_bus = event_bus if event_bus is not None else vtuber_event_bus
        self.auto_emit = auto_emit
        self._listeners: Set[Callable[[EmotionChangedEvent], Any]] = set()

    @property
    def current_emotion(self) -> VTuberEmotion:
        return self._current_emotion

    @property
    def current_intensity(self) -> float:
        return self._current_intensity

    @property
    def current_expression(self) -> VTuberExpression:
        return self._current_expression

    @property
    def current(self) -> EmotionResult:
        return EmotionResult(
            emotion=self._current_emotion,
            intensity=self._current_intensity,
            expression=self._current_expression,
        )

    def add_listener(self, listener: Callable[[EmotionChangedEvent], Any]) -> Callable[[], None]:
        """Subscribe a listener directly to emotion change events."""
        self._listeners.add(listener)

        def _unsub():
            if listener in self._listeners:
                self._listeners.remove(listener)

        return _unsub

    def resolve(self, event: AgentEvent) -> EmotionResult:
        """
        Pure rule-based resolution of an AgentEvent to an EmotionResult without mutating engine state.
        """
        emo, intensity, expr = resolve_emotion_from_event(event)
        source = getattr(event.type, "value", str(event.type))
        return EmotionResult(
            emotion=emo,
            intensity=intensity,
            expression=expr,
            source_event=source,
            metadata={"tool": event.tool, "success": event.success},
        )

    async def process_agent_event(self, event: AgentEvent) -> Optional[EmotionChangedEvent]:
        """
        Resolve emotion for incoming AgentEvent, update current state, and emit if changed.
        Suppresses redundant emissions when emotion and expression remain identical.
        """
        res = self.resolve(event)
        return await self.set_emotion(
            emotion=res.emotion,
            intensity=res.intensity,
            expression=res.expression,
            metadata={"source_event": res.source_event, **res.metadata},
        )

    async def set_emotion(
        self,
        emotion: VTuberEmotion,
        intensity: float = 0.5,
        expression: Optional[VTuberExpression] = None,
        metadata: Optional[Dict[str, Any]] = None,
        force: bool = False,
    ) -> Optional[EmotionChangedEvent]:
        """
        Set new emotion state. Only emits if state or intensity changed significantly, or force=True.
        """
        clamped_intensity = max(0.0, min(1.0, float(intensity)))
        target_expr = expression or map_emotion_to_expression(emotion)

        # Duplicate suppression: same emotion, same expression, and delta intensity < 0.15
        is_same_emotion = (self._current_emotion == emotion)
        is_same_expr = (self._current_expression == target_expr)
        intensity_delta = abs(self._current_intensity - clamped_intensity)

        if not force and is_same_emotion and is_same_expr and intensity_delta < 0.15:
            # Suppress duplicate transition
            return None

        prev_emotion = self._current_emotion
        self._current_emotion = emotion
        self._current_intensity = clamped_intensity
        self._current_expression = target_expr

        event = EmotionChangedEvent(
            emotion=self._current_emotion,
            intensity=self._current_intensity,
            expression=self._current_expression,
            previous_emotion=prev_emotion,
            metadata=metadata or {},
        )

        # 1. Notify direct listeners
        for listener in list(self._listeners):
            try:
                listener(event)
            except Exception as exc:
                logger.error("Error in EmotionEngine listener: %s", exc)

        return event

    def reset(self) -> None:
        """Reset emotion to default neutral."""
        self._current_emotion = VTuberEmotion.NEUTRAL
        self._current_intensity = 0.3
        self._current_expression = VTuberExpression.NEUTRAL


# Global singleton instance
emotion_engine = EmotionEngine()
