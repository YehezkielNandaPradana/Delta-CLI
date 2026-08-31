"""
Ephemeral Screenshot Capture Providers for Delta VTuber.
Ensures zero-persistence memory buffers for privacy compliance.
"""

import base64
import io
import logging
from typing import Optional, Protocol, runtime_checkable
from delta.vtuber.desktop.schemas import ScreenshotData

logger = logging.getLogger(__name__)


@runtime_checkable
class ScreenshotProvider(Protocol):
    """Protocol for capturing on-demand desktop screenshots."""
    async def capture_screen(self) -> Optional[ScreenshotData]:
        ...


class SystemScreenshotProvider:
    """Captures screen in memory using Pillow ImageGrab or mss."""

    async def capture_screen(self) -> Optional[ScreenshotData]:
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            img_bytes = buf.getvalue()
            b64_str = base64.b64encode(img_bytes).decode("ascii")

            return ScreenshotData(
                image_base64=b64_str,
                format="png",
                width=img.width,
                height=img.height,
                retention="ephemeral",
            )
        except Exception as exc:
            logger.debug("Screenshot capture failed: %s", exc)
            return None


class NoopScreenshotProvider:
    """Mock screenshot provider for testing."""

    def __init__(self, mock_bytes: bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"):
        self.mock_bytes = mock_bytes

    async def capture_screen(self) -> Optional[ScreenshotData]:
        b64_str = base64.b64encode(self.mock_bytes).decode("ascii")
        return ScreenshotData(
            image_base64=b64_str,
            format="png",
            width=1920,
            height=1080,
            retention="ephemeral",
        )
