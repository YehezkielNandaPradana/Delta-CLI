"""
Desktop Intelligence and Personal Companion OS Integration Package for Delta VTuber.
"""

from delta.vtuber.desktop.schemas import (
    DesktopCapability,
    ActiveWindow,
    ProjectContext,
    DesktopContext,
    ScreenshotData,
    ClipboardData,
    OverlayMode,
)
from delta.vtuber.desktop.permissions import (
    DesktopPermissionManager,
)
from delta.vtuber.desktop.active_window import (
    ActiveWindowProvider,
    WindowsActiveWindowProvider,
    LinuxActiveWindowProvider,
    NoopActiveWindowProvider,
)
from delta.vtuber.desktop.clipboard import (
    ClipboardProvider,
    SystemClipboardProvider,
    NoopClipboardProvider,
)
from delta.vtuber.desktop.screenshot import (
    ScreenshotProvider,
    SystemScreenshotProvider,
    NoopScreenshotProvider,
)
from delta.vtuber.desktop.hotkey import (
    GlobalHotkeyProvider,
    SystemHotkeyProvider,
    NoopHotkeyProvider,
)
from delta.vtuber.desktop.overlay import (
    DesktopOverlayController,
)
from delta.vtuber.desktop.context import (
    ProjectContextProvider,
)
from delta.vtuber.desktop.manager import (
    DesktopManager,
    desktop_manager,
)

# Re-export legacy Phase 7 desktop integration classes for backward compatibility
from delta.vtuber.desktop_legacy import (
    DesktopIntegration,
    WindowsDesktopIntegration,
    LinuxDesktopIntegration,
    NoopDesktopIntegration,
)

__all__ = [
    "DesktopCapability",
    "ActiveWindow",
    "ProjectContext",
    "DesktopContext",
    "ScreenshotData",
    "ClipboardData",
    "OverlayMode",
    "DesktopPermissionManager",
    "ActiveWindowProvider",
    "WindowsActiveWindowProvider",
    "LinuxActiveWindowProvider",
    "NoopActiveWindowProvider",
    "ClipboardProvider",
    "SystemClipboardProvider",
    "NoopClipboardProvider",
    "ScreenshotProvider",
    "SystemScreenshotProvider",
    "NoopScreenshotProvider",
    "GlobalHotkeyProvider",
    "SystemHotkeyProvider",
    "NoopHotkeyProvider",
    "DesktopOverlayController",
    "ProjectContextProvider",
    "DesktopManager",
    "desktop_manager",
    "DesktopIntegration",
    "WindowsDesktopIntegration",
    "LinuxDesktopIntegration",
    "NoopDesktopIntegration",
]
