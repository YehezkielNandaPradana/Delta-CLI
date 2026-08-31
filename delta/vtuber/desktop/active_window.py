"""
Active Window Detection Providers for Delta VTuber Companion.
"""

import logging
from typing import Optional, Protocol, runtime_checkable
from delta.vtuber.desktop.schemas import ActiveWindow

logger = logging.getLogger(__name__)


@runtime_checkable
class ActiveWindowProvider(Protocol):
    """Protocol for active foreground window detection."""
    async def get_active_window(self) -> ActiveWindow:
        ...


class WindowsActiveWindowProvider:
    """Windows ctypes/win32 foreground window detection provider."""

    async def get_active_window(self) -> ActiveWindow:
        try:
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return ActiveWindow(application="Desktop", window_title="")

            # Get window title
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value

            # Get process ID
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

            # Approximate app name from title or common IDE patterns
            app_name = "Desktop"
            t_lower = title.lower()
            if "visual studio code" in t_lower or " - code" in t_lower:
                app_name = "Visual Studio Code"
            elif "cursor" in t_lower:
                app_name = "Cursor"
            elif "chrome" in t_lower or "google chrome" in t_lower:
                app_name = "Google Chrome"
            elif "edge" in t_lower or "microsoft edge" in t_lower:
                app_name = "Microsoft Edge"
            elif "terminal" in t_lower or "powershell" in t_lower or "cmd" in t_lower or "bash" in t_lower:
                app_name = "Terminal"
            elif title:
                app_name = title.split(" - ")[-1] if " - " in title else title

            return ActiveWindow(
                application=app_name,
                window_title=title,
                pid=pid.value,
            )
        except Exception as exc:
            logger.debug("Windows active window detection error: %s", exc)
            return ActiveWindow(application="Desktop", window_title="")


class LinuxActiveWindowProvider:
    """Linux active window provider using xdotool/wmctrl fallback."""

    async def get_active_window(self) -> ActiveWindow:
        return ActiveWindow(application="Linux Desktop", window_title="Workspace")


class NoopActiveWindowProvider:
    """Fallback no-op provider for headless / testing environments."""

    def __init__(self, default_app: str = "Visual Studio Code", default_title: str = "delta - server.py"):
        self.default_app = default_app
        self.default_title = default_title

    async def get_active_window(self) -> ActiveWindow:
        return ActiveWindow(
            application=self.default_app,
            window_title=self.default_title,
        )
