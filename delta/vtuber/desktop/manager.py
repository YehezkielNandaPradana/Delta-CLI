"""
Desktop Intelligence Manager for Delta VTuber.
Central coordinator managing active window detection, workspace context,
on-demand ephemeral screenshots, sanitized clipboard reading, and global hotkeys.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, Optional, Set

from delta.vtuber.desktop.active_window import ActiveWindowProvider, WindowsActiveWindowProvider, NoopActiveWindowProvider
from delta.vtuber.desktop.clipboard import ClipboardProvider, SystemClipboardProvider, NoopClipboardProvider
from delta.vtuber.desktop.context import ProjectContextProvider
from delta.vtuber.desktop.hotkey import GlobalHotkeyProvider, SystemHotkeyProvider, NoopHotkeyProvider
from delta.vtuber.desktop.overlay import DesktopOverlayController
from delta.vtuber.desktop.permissions import DesktopPermissionManager
from delta.vtuber.desktop.schemas import (
    ActiveWindow,
    ClipboardData,
    DesktopCapability,
    DesktopContext,
    ProjectContext,
    ScreenshotData,
)
from delta.vtuber.desktop.screenshot import ScreenshotProvider, SystemScreenshotProvider, NoopScreenshotProvider

logger = logging.getLogger(__name__)


class DesktopManager:
    """
    Coordinates desktop awareness, context snapshots, ephemeral media captures, and permissions.
    """

    def __init__(
        self,
        active_window_provider: Optional[ActiveWindowProvider] = None,
        screenshot_provider: Optional[ScreenshotProvider] = None,
        clipboard_provider: Optional[ClipboardProvider] = None,
        hotkey_provider: Optional[GlobalHotkeyProvider] = None,
        permissions: Optional[DesktopPermissionManager] = None,
        overlay: Optional[DesktopOverlayController] = None,
        cwd: Optional[str] = None,
    ):
        self.active_window = active_window_provider or (WindowsActiveWindowProvider() if WindowsActiveWindowProvider() else NoopActiveWindowProvider())
        self.screenshot = screenshot_provider or NoopScreenshotProvider()
        self.clipboard = clipboard_provider or NoopClipboardProvider()
        self.hotkey = hotkey_provider or NoopHotkeyProvider()
        self.permissions = permissions or DesktopPermissionManager()
        self.overlay = overlay or DesktopOverlayController()
        self.cwd = cwd

        self._summon_listeners: Set[Callable[[], Any]] = set()

    def add_summon_listener(self, listener: Callable[[], Any]) -> Callable[[], None]:
        self._summon_listeners.add(listener)

        def _unsub():
            if listener in self._summon_listeners:
                self._summon_listeners.remove(listener)

        return _unsub

    def register_quick_summon(self, hotkey_combo: str = "ctrl+shift+space") -> bool:
        """Register global hotkey to trigger Quick Summon."""
        if not self.permissions.is_permitted(DesktopCapability.GLOBAL_HOTKEY):
            return False

        return self.hotkey.register_hotkey(hotkey_combo, self._on_quick_summon)

    def _on_quick_summon(self) -> None:
        """Triggered when user hits the global summon hotkey."""
        logger.info("[Quick Summon] Hotkey pressed: summoning Delta companion")
        self.overlay.visible = True
        for listener in list(self._summon_listeners):
            try:
                res = listener()
                if asyncio.iscoroutine(res):
                    asyncio.create_task(res)
            except Exception as exc:
                logger.error("Error in summon listener: %s", exc)

    async def capture_context(self, current_cwd: Optional[str] = None) -> DesktopContext:
        """
        Capture on-demand context snapshot of active desktop and workspace.
        """
        target_cwd = current_cwd or self.cwd

        # 1. Active Window Metadata (if permitted)
        win: ActiveWindow
        if self.permissions.is_permitted(DesktopCapability.ACTIVE_WINDOW):
            try:
                win = await self.active_window.get_active_window()
            except Exception:
                win = ActiveWindow(application="Unknown", window_title="")
        else:
            win = ActiveWindow(application="Protected", window_title="")

        # 2. Workspace Context
        proj: ProjectContext = ProjectContextProvider.resolve_context(target_cwd)

        # 3. Clipboard availability check
        clip_avail = self.permissions.is_permitted(DesktopCapability.CLIPBOARD)

        return DesktopContext(
            active_application=win.application,
            active_window_title=win.window_title,
            workspace_path=proj.project_path,
            workspace_name=proj.project_name,
            active_file=proj.active_file,
            git_branch=proj.git_branch,
            clipboard_available=clip_avail,
            metadata={"language": proj.language, "framework": proj.framework},
        )

    async def capture_ephemeral_screenshot(self) -> Optional[ScreenshotData]:
        """
        Capture on-demand ephemeral screenshot with explicit permission check.
        """
        if not self.permissions.is_permitted(DesktopCapability.SCREENSHOT):
            logger.warning("[Privacy] Screenshot request rejected: SCREENSHOT capability is disabled.")
            return None

        return await self.screenshot.capture_screen()

    async def read_sanitized_clipboard(self) -> Optional[ClipboardData]:
        """
        Read sanitized clipboard text with explicit permission check.
        """
        if not self.permissions.is_permitted(DesktopCapability.CLIPBOARD):
            logger.warning("[Privacy] Clipboard read rejected: CLIPBOARD capability is disabled.")
            return None

        text = await self.clipboard.read_text()
        return ClipboardData(
            text=text,
            has_content=bool(text and text.strip()),
        )


# Global singleton instance
desktop_manager = DesktopManager()
