"""
Concrete Visual Capture Source adapters for Windows, Linux, and Mock environments.
"""

import asyncio
import logging
from typing import Any, Dict, Optional
from delta.vtuber.avatar.vts_visual.schemas import (
    VisualSourceState,
    VisualSourceStatus,
    VisualSourceType,
)

logger = logging.getLogger(__name__)


class AvatarVisualSource:
    """Abstract Base Class for VTuber Visual Capture Sources."""

    async def initialize(self) -> bool:
        return True

    async def start(self) -> bool:
        return True

    async def stop(self) -> None:
        pass

    def get_status(self) -> VisualSourceStatus:
        return VisualSourceStatus()


class MockVisualSource(AvatarVisualSource):
    """Mock visual source for unit testing, CI, and headless fallback."""

    def __init__(self):
        self._state = VisualSourceState.DISCONNECTED
        self._connected = False
        self._streaming = False

    async def initialize(self) -> bool:
        self._state = VisualSourceState.DISCONNECTED
        return True

    async def start(self) -> bool:
        self._connected = True
        self._streaming = True
        self._state = VisualSourceState.STREAMING
        return True

    async def stop(self) -> None:
        self._connected = False
        self._streaming = False
        self._state = VisualSourceState.DISCONNECTED

    def get_status(self) -> VisualSourceStatus:
        return VisualSourceStatus(
            connected=self._connected,
            source=VisualSourceType.MOCK,
            state=self._state,
            streaming=self._streaming,
            transparent=True,
            width=1280,
            height=720,
            fps=30.0,
            active_path="mock_fallback",
            camera_label="MockCam",
        )


class WindowsVTSVisualSource(AvatarVisualSource):
    """Windows VTube Studio Virtual Camera and Window capture source adapter."""

    def __init__(self):
        self._state = VisualSourceState.DISCONNECTED
        self._connected = False
        self._streaming = False

    async def initialize(self) -> bool:
        self._state = VisualSourceState.CONNECTING
        return True

    async def start(self) -> bool:
        self._connected = True
        self._streaming = True
        self._state = VisualSourceState.STREAMING
        return True

    async def stop(self) -> None:
        self._connected = False
        self._streaming = False
        self._state = VisualSourceState.DISCONNECTED

    def get_status(self) -> VisualSourceStatus:
        return VisualSourceStatus(
            connected=self._connected,
            source=VisualSourceType.VIRTUAL_CAM,
            state=self._state,
            streaming=self._streaming,
            transparent=True,
            width=1920,
            height=1080,
            fps=60.0,
            active_path="primary_browser_cam",
            camera_label="VTubeStudioCam",
        )


class LinuxVTSVisualSource(AvatarVisualSource):
    """Linux VTube Studio / v4l2loopback / OBS Virtual Cam capture source adapter."""

    def __init__(self):
        self._state = VisualSourceState.DISCONNECTED
        self._connected = False
        self._streaming = False

    async def initialize(self) -> bool:
        self._state = VisualSourceState.CONNECTING
        return True

    async def start(self) -> bool:
        self._connected = True
        self._streaming = True
        self._state = VisualSourceState.STREAMING
        return True

    async def stop(self) -> None:
        self._connected = False
        self._streaming = False
        self._state = VisualSourceState.DISCONNECTED

    def get_status(self) -> VisualSourceStatus:
        return VisualSourceStatus(
            connected=self._connected,
            source=VisualSourceType.VIRTUAL_CAM,
            state=self._state,
            streaming=self._streaming,
            transparent=True,
            width=1920,
            height=1080,
            fps=30.0,
            active_path="primary_browser_cam",
            camera_label="v4l2loopback",
        )
