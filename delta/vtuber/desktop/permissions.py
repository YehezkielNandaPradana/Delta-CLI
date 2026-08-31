"""
Desktop Capability & Privacy Permission Manager for Delta VTuber.
Enforces opt-in consent for sensitive operations (screenshots, clipboard, active window metadata).
"""

import logging
from typing import Dict, Set
from delta.vtuber.desktop.schemas import DesktopCapability

logger = logging.getLogger(__name__)


class DesktopPermissionManager:
    """
    Guards desktop capabilities with configurable opt-in security policies.
    """

    def __init__(
        self,
        active_window_allowed: bool = True,
        workspace_allowed: bool = True,
        screenshot_allowed: bool = False,
        clipboard_allowed: bool = False,
        hotkey_allowed: bool = True,
        notifications_allowed: bool = True,
        overlay_allowed: bool = True,
    ):
        self._permissions: Dict[DesktopCapability, bool] = {
            DesktopCapability.ACTIVE_WINDOW: active_window_allowed,
            DesktopCapability.WORKSPACE: workspace_allowed,
            DesktopCapability.SCREENSHOT: screenshot_allowed,
            DesktopCapability.CLIPBOARD: clipboard_allowed,
            DesktopCapability.GLOBAL_HOTKEY: hotkey_allowed,
            DesktopCapability.DESKTOP_NOTIFICATION: notifications_allowed,
            DesktopCapability.DESKTOP_OVERLAY: overlay_allowed,
        }

    def is_permitted(self, capability: DesktopCapability) -> bool:
        """Check if capability is enabled under current privacy settings."""
        return self._permissions.get(capability, False)

    def set_permission(self, capability: DesktopCapability, allowed: bool) -> None:
        """Update permission state for specific desktop capability."""
        self._permissions[capability] = allowed
        logger.info("[Desktop Privacy] Permission updated: %s = %s", capability.value, allowed)

    def get_all_permissions(self) -> Dict[str, bool]:
        """Return dict of all current permission states."""
        return {cap.value: val for cap, val in self._permissions.items()}
