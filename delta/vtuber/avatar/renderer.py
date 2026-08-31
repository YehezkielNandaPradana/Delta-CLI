"""
Avatar Renderer Protocol and Implementations for Delta VTuber.
"""

from typing import List, Protocol, runtime_checkable
from delta.vtuber.avatar.schemas import AvatarState


@runtime_checkable
class AvatarRenderer(Protocol):
    """
    Protocol defining the interface for avatar renderers (Mock, Live2D WebGL, VTS).
    """

    async def render(self, state: AvatarState, urgent: bool = False) -> None:
        """
        Render a new AvatarState frame.
        urgent=True bypasses rate limiting and delta suppression (e.g. barge-in reset).
        """
        ...

    async def initialize(self) -> None:
        """Initialize renderer resources."""
        ...

    async def shutdown(self) -> None:
        """Release renderer resources."""
        ...


class MockAvatarRenderer:
    """
    Mock Avatar Renderer for testing and headless verification.
    Records rendered states in memory without requiring graphic engines.
    """

    def __init__(self):
        self.rendered_states: List[AvatarState] = []
        self.is_initialized: bool = False
        self.is_shutdown: bool = False

    async def initialize(self) -> None:
        self.is_initialized = True
        self.is_shutdown = False

    async def shutdown(self) -> None:
        self.is_shutdown = True
        self.is_initialized = False

    async def render(self, state: AvatarState, urgent: bool = False) -> None:
        self.rendered_states.append(state)
