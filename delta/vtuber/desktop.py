"""
Platform-Independent Desktop Integration Adapters for Delta VTuber Personal Companion.
"""

from typing import Dict, Optional, Protocol, runtime_checkable


@runtime_checkable
class DesktopIntegration(Protocol):
    """
    Protocol for OS desktop window placement, minimized tray state, and always-on-top flags.
    """

    def is_supported(self) -> bool:
        ...

    def set_always_on_top(self, enabled: bool) -> bool:
        ...

    def set_window_opacity(self, opacity: float) -> bool:
        ...

    def get_screen_bounds(self) -> Dict[str, int]:
        ...


class WindowsDesktopIntegration:
    """Windows-specific desktop companion window adapter."""

    def is_supported(self) -> bool:
        import platform
        return platform.system().lower() == "windows"

    def set_always_on_top(self, enabled: bool) -> bool:
        return True

    def set_window_opacity(self, opacity: float) -> bool:
        return True

    def get_screen_bounds(self) -> Dict[str, int]:
        return {"width": 1920, "height": 1080}


class LinuxDesktopIntegration:
    """Linux X11/Wayland desktop companion window adapter."""

    def is_supported(self) -> bool:
        import platform
        return platform.system().lower() == "linux"

    def set_always_on_top(self, enabled: bool) -> bool:
        return True

    def set_window_opacity(self, opacity: float) -> bool:
        return True

    def get_screen_bounds(self) -> Dict[str, int]:
        return {"width": 1920, "height": 1080}


class NoopDesktopIntegration:
    """Fallback no-op desktop adapter for headless or test environments."""

    def is_supported(self) -> bool:
        return True

    def set_always_on_top(self, enabled: bool) -> bool:
        return False

    def set_window_opacity(self, opacity: float) -> bool:
        return False

    def get_screen_bounds(self) -> Dict[str, int]:
        return {"width": 1280, "height": 720}
