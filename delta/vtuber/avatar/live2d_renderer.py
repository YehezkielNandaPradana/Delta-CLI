"""
Live2D Canvas Renderer Adapter for Delta VTuber.
Dispatches mapped Live2D parameter frames to connected browser clients via WebSocket/SSE.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from delta.vtuber.avatar.live2d_mapper import Live2DParameterMapper
from delta.vtuber.avatar.schemas import AvatarState
from delta.vtuber.voice.browser_player import browser_audio_player

logger = logging.getLogger(__name__)


class Live2DCanvasRenderer:
    """
    Concrete AvatarRenderer that translates AvatarState into Live2D parameters
    and broadcasts state frames to the browser canvas via the realtime transport channel.
    """

    def __init__(self, transport: Optional[Any] = None):
        self.transport = transport or browser_audio_player
        self.is_initialized: bool = False
        self.is_shutdown: bool = False
        self.last_dispatched_params: Optional[Dict[str, float]] = None

    async def initialize(self) -> None:
        self.is_initialized = True
        self.is_shutdown = False

    async def shutdown(self) -> None:
        self.is_shutdown = True
        self.is_initialized = False

    async def render(self, state: AvatarState) -> None:
        """
        Translate state to Live2D parameters and broadcast to browser canvas.
        """
        live2d_params = Live2DParameterMapper.to_live2d_parameters(state)
        self.last_dispatched_params = live2d_params

        payload = {
            "type": "avatar_state",
            "expression": state.expression.value if hasattr(state.expression, "value") else str(state.expression),
            "expression_intensity": state.expression_intensity,
            "mouth_open": state.mouth_open,
            "mouth_form": state.mouth_form,
            "head_x": state.head_x,
            "head_y": state.head_y,
            "body_angle": state.body_angle,
            "speaking": state.speaking,
            "live2d_params": live2d_params,
            "timestamp": state.timestamp,
        }

        if hasattr(self.transport, "broadcast_message"):
            self.transport.broadcast_message(payload)
        elif callable(self.transport):
            self.transport(payload)
