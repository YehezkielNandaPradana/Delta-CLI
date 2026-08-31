"""
VTube Studio Avatar Renderer for Delta VTuber.
Implements AvatarRenderer protocol to relay avatar states directly to desktop VTube Studio.
"""

import logging
import time
from typing import Optional
from delta.vtuber.avatar.character_profile import CharacterProfile, default_character_profile
from delta.vtuber.avatar.schemas import AvatarState
from delta.vtuber.avatar.vts.client import VTSClient

logger = logging.getLogger(__name__)


class VTSRenderer:
    """
    Concrete AvatarRenderer routing AvatarState frames to a running VTube Studio instance
    with rate limiting, delta threshold filtering, and latest-state-wins queue management.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8001,
        plugin_name: str = "Delta AI VTuber",
        plugin_developer: str = "Delta Team",
        auth_token: Optional[str] = None,
        profile: Optional[CharacterProfile] = None,
        update_hz: float = 30.0,
        delta_threshold: float = 0.015,
        enabled: bool = False,
    ):
        self.client = VTSClient(
            host=host,
            port=port,
            plugin_name=plugin_name,
            plugin_developer=plugin_developer,
            auth_token=auth_token,
            enabled=enabled,
        )
        self.profile = profile or default_character_profile
        self.update_interval = 1.0 / max(1.0, update_hz)
        self.delta_threshold = delta_threshold

        self.is_initialized: bool = False
        self.is_shutdown: bool = False
        self._last_render_time: float = 0.0
        self._last_sent_state: Optional[AvatarState] = None
        self._dropped_updates: int = 0
        self._stale_updates_dropped: int = 0

    @property
    def dropped_updates(self) -> int:
        return self._dropped_updates

    @property
    def stale_updates_dropped(self) -> int:
        return self._stale_updates_dropped

    async def initialize(self) -> None:
        self.is_initialized = True
        self.is_shutdown = False
        if self.client.enabled:
            await self.client.connect()

    async def shutdown(self) -> None:
        self.is_shutdown = True
        self.is_initialized = False
        await self.client.disconnect()

    async def render(self, state: AvatarState, urgent: bool = False) -> None:
        if not self.client.enabled or not self.client.is_connected or not self.client.is_authenticated:
            return

        now = time.time()

        if not urgent:
            # 1. Rate Limiting Cadence Check (Latest-state-wins: drops stale intermediate frames)
            # Speaking frames bypass cadence to keep lip-sync realtime
            if not state.speaking and now - self._last_render_time < self.update_interval and self._last_sent_state is not None:
                self._stale_updates_dropped += 1
                return

            # 2. Delta Threshold Check (Suppress tiny imperceptible jitter updates)
            if self._last_sent_state is not None and not state.is_significantly_different_from(self._last_sent_state, threshold=self.delta_threshold):
                self._dropped_updates += 1
                return

        self._last_render_time = now
        self._last_sent_state = state.model_copy()

        # 3. Filter supported capabilities before dispatch
        supported_params = self.profile.supported_parameters if self.profile else None
        await self.client.send_avatar_state(state, supported_parameters=supported_params)
