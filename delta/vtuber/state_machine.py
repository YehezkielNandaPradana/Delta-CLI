"""
Lifecycle State Machine for Delta VTuber.
"""

from enum import Enum
from typing import Any, Dict, Optional, Set, Union
from delta.vtuber.events import VTuberEventType, VTuberEvent, VTuberPayload, VTuberEmotion
from delta.vtuber.event_bus import VTuberEventBus, vtuber_event_bus


class VTuberState(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    TOOL_USE = "TOOL_USE"
    SPEAKING = "SPEAKING"
    ERROR = "ERROR"


class InvalidStateTransitionError(ValueError):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, from_state: VTuberState, to_state: VTuberState):
        super().__init__(
            f"Invalid VTuber state transition from {from_state.value} to {to_state.value}"
        )
        self.from_state = from_state
        self.to_state = to_state


class VTuberStateMachine:
    """
    State machine enforcing valid transitions for Delta VTuber lifecycle.
    Can automatically emit lifecycle events to an event bus on state transition.
    """

    # Allowed transitions graph
    _ALLOWED_TRANSITIONS: Dict[VTuberState, Set[VTuberState]] = {
        VTuberState.IDLE: {
            VTuberState.LISTENING,
            VTuberState.THINKING,  # direct prompt / trigger
            VTuberState.ERROR,
        },
        VTuberState.LISTENING: {
            VTuberState.THINKING,
            VTuberState.IDLE,  # timeout / cancelled
            VTuberState.ERROR,
        },
        VTuberState.THINKING: {
            VTuberState.TOOL_USE,
            VTuberState.SPEAKING,
            VTuberState.ERROR,
            VTuberState.IDLE,
        },
        VTuberState.TOOL_USE: {
            VTuberState.THINKING,
            VTuberState.SPEAKING,
            VTuberState.ERROR,
            VTuberState.IDLE,
        },
        VTuberState.SPEAKING: {
            VTuberState.IDLE,
            VTuberState.LISTENING,  # conversational turn-taking
            VTuberState.THINKING,  # user interrupted / next response
            VTuberState.ERROR,
        },
        VTuberState.ERROR: {
            VTuberState.IDLE,
            VTuberState.LISTENING,
            VTuberState.THINKING,
        },
    }

    # Mapping State -> default EventType
    _STATE_TO_EVENT: Dict[VTuberState, VTuberEventType] = {
        VTuberState.IDLE: VTuberEventType.IDLE,
        VTuberState.LISTENING: VTuberEventType.LISTENING,
        VTuberState.THINKING: VTuberEventType.THINKING,
        VTuberState.TOOL_USE: VTuberEventType.TOOL_USE,
        VTuberState.SPEAKING: VTuberEventType.SPEAKING,
        VTuberState.ERROR: VTuberEventType.ERROR,
    }

    def __init__(
        self,
        initial_state: VTuberState = VTuberState.IDLE,
        event_bus: Optional[VTuberEventBus] = None,
        auto_emit: bool = True,
    ):
        self._current_state = initial_state
        self.event_bus = event_bus if event_bus is not None else vtuber_event_bus
        self.auto_emit = auto_emit

    @property
    def current_state(self) -> VTuberState:
        return self._current_state

    def can_transition_to(self, to_state: Union[VTuberState, str]) -> bool:
        target = to_state if isinstance(to_state, VTuberState) else VTuberState(to_state)
        allowed = self._ALLOWED_TRANSITIONS.get(self._current_state, set())
        return target in allowed

    async def transition_to(
        self,
        to_state: Union[VTuberState, str],
        payload: Optional[VTuberPayload] = None,
        text: Optional[str] = None,
        emotion: Optional[VTuberEmotion] = None,
        intensity: float = 1.0,
        tool: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> VTuberState:
        """
        Transition to next state if allowed. Emits an event if auto_emit is enabled.
        """
        target = to_state if isinstance(to_state, VTuberState) else VTuberState(to_state)
        if not self.can_transition_to(target):
            raise InvalidStateTransitionError(self._current_state, target)

        from_state = self._current_state
        self._current_state = target

        if self.auto_emit and self.event_bus:
            event_type = self._STATE_TO_EVENT.get(target, VTuberEventType.IDLE)
            meta = {"from_state": from_state.value, "to_state": target.value}
            if metadata:
                meta.update(metadata)
            event_payload = payload or VTuberPayload(
                text=text,
                emotion=emotion or VTuberEmotion.NEUTRAL,
                intensity=intensity,
                tool=tool,
                metadata=meta,
            )
            event = VTuberEvent(type=event_type, payload=event_payload)
            await self.event_bus.emit(event)

        return self._current_state

    def reset(self) -> None:
        """Reset state directly to IDLE without transition checks."""
        self._current_state = VTuberState.IDLE
