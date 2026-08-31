"""
Clipboard Reader with Secret Filtering for Delta VTuber Desktop Intelligence.
"""

import logging
from typing import Optional, Protocol, runtime_checkable
from delta.vtuber.desktop.schemas import ClipboardData
from delta.vtuber.memory.security import SecretFilter

logger = logging.getLogger(__name__)


@runtime_checkable
class ClipboardProvider(Protocol):
    """Protocol for reading clipboard content on-demand."""
    async def read_text(self) -> Optional[str]:
        ...


class SystemClipboardProvider:
    """Reads system clipboard with Tkinter/ctypes fallback and sanitizes secrets."""

    async def read_text(self) -> Optional[str]:
        raw_text = None
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            raw_text = root.clipboard_get()
            root.destroy()
        except Exception:
            try:
                # Windows ctypes fallback
                import ctypes
                user32 = ctypes.windll.user32
                kernel32 = ctypes.windll.kernel32
                if user32.OpenClipboard(None):
                    h_clip = user32.GetClipboardData(13)  # CF_UNICODETEXT
                    if h_clip:
                        p_clip = kernel32.GlobalLock(h_clip)
                        if p_clip:
                            raw_text = ctypes.c_wchar_p(p_clip).value
                            kernel32.GlobalUnlock(h_clip)
                    user32.CloseClipboard()
            except Exception as exc:
                logger.debug("System clipboard read failed: %s", exc)
                return None

        if not raw_text:
            return None

        # Sanitize credentials before returning
        return SecretFilter.sanitize(raw_text)


class NoopClipboardProvider:
    """Mock clipboard provider for testing."""

    def __init__(self, canned_text: Optional[str] = "def hello():\n    return 'world'"):
        self.canned_text = canned_text

    async def read_text(self) -> Optional[str]:
        if not self.canned_text:
            return None
        return SecretFilter.sanitize(self.canned_text)
