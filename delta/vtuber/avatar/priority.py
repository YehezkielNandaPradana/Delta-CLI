"""
Avatar Animation Priority System for Delta VTuber.
Ensures critical expressive states (ERROR, INTERRUPT, SPEAKING, LISTENING, THINKING)
override background subtle motions (IDLE, EMOTION).
"""

from enum import IntEnum
from typing import Optional
from delta.vtuber.avatar.schemas import AvatarState
from delta.vtuber.emotion.schemas import VTuberExpression


class AnimationPriority(IntEnum):
    """
    Numeric priority hierarchy (higher number = higher priority override).
    """
    IDLE = 10
    EMOTION = 20
    LISTENING = 30
    THINKING = 40
    SPEAKING = 50
    INTERRUPT = 60
    ERROR = 70


class AnimationPrioritySystem:
    """
    Maintains current animation priority and arbitrates whether incoming
    animation/expression changes are allowed to override active state.
    """

    def __init__(self, default_priority: AnimationPriority = AnimationPriority.IDLE):
        self._current_priority: AnimationPriority = default_priority
        self._active_source: str = "default"

    @property
    def current_priority(self) -> AnimationPriority:
        return self._current_priority

    def can_override(self, new_priority: AnimationPriority) -> bool:
        """
        Check if new animation request has equal or higher priority than currently active state.
        """
        return int(new_priority) >= int(self._current_priority)

    def request_transition(
        self,
        new_priority: AnimationPriority,
        source: str = "system",
        force: bool = False,
    ) -> bool:
        """
        Request priority change. Succeeds and updates priority if new_priority >= current_priority or force=True.
        """
        if force or self.can_override(new_priority):
            self._current_priority = new_priority
            self._active_source = source
            return True
        return False

    def release_priority(self, priority_to_release: AnimationPriority) -> None:
        """
        Release elevated priority back to IDLE baseline when a higher-tier activity completes.
        """
        if self._current_priority == priority_to_release:
            self._current_priority = AnimationPriority.IDLE
            self._active_source = "idle"

    def reset(self) -> None:
        """Reset priority to baseline IDLE."""
        self._current_priority = AnimationPriority.IDLE
        self._active_source = "reset"
