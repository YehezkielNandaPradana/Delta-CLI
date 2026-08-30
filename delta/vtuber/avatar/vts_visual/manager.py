"""
VTS Visual Manager orchestrating platform visual sources and status API reporting.
"""

import platform
import logging
from typing import Any, Dict, Optional
from delta.vtuber.avatar.vts_visual.schemas import (
    VisualSourceState,
    VisualSourceStatus,
    VisualSourceType,
)
from delta.vtuber.avatar.vts_visual.sources import (
    AvatarVisualSource,
    WindowsVTSVisualSource,
    LinuxVTSVisualSource,
    MockVisualSource,
)

logger = logging.getLogger(__name__)


class VTSVisualManager:
    """Manager holding current platform visual source and fallback handlers."""

    def __init__(self, source: Optional[AvatarVisualSource] = None):
        if source:
            self.source = source
        else:
            sys_name = platform.system().lower()
            if sys_name == "windows":
                self.source = WindowsVTSVisualSource()
            elif sys_name == "linux":
                self.source = LinuxVTSVisualSource()
            else:
                self.source = MockVisualSource()

    async def initialize(self) -> bool:
        return await self.source.initialize()

    async def start(self) -> bool:
        return await self.source.start()

    async def stop(self) -> None:
        await self.source.stop()

    def get_status(self) -> VisualSourceStatus:
        return self.source.get_status()


# Global singleton instance
vts_visual_manager = VTSVisualManager()
