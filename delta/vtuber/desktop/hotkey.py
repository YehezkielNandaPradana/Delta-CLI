"""
Global Hotkey & Quick Summon Provider for Delta VTuber Companion.
"""

import logging
from typing import Callable, Optional, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class GlobalHotkeyProvider(Protocol):
    """Protocol for registering and listening to global system hotkeys."""

    def register_hotkey(self, hotkey: str, callback: Callable[[], None]) -> bool:
        ...

    def unregister_all(self) -> None:
        ...


class SystemHotkeyProvider:
    """Registers system hotkeys using keyboard library if available."""

    def __init__(self):
        self._is_registered = False

    def register_hotkey(self, hotkey: str, callback: Callable[[], None]) -> bool:
        try:
            import keyboard  # type: ignore
            keyboard.add_hotkey(hotkey, callback)
            self._is_registered = True
            logger.info("[Global Hotkey] Registered: %s", hotkey)
            return True
        except Exception as exc:
            logger.debug("[Global Hotkey] Could not bind '%s': %s", hotkey, exc)
            return False

    def unregister_all(self) -> None:
        try:
            import keyboard
            keyboard.unhook_all()
        except Exception:
            pass


class NoopHotkeyProvider:
    """Mock hotkey provider for tests and non-GUI runs."""

    def __init__(self):
        self.registered_hotkeys: dict[str, Callable[[], None]] = {}

    def register_hotkey(self, hotkey: str, callback: Callable[[], None]) -> bool:
        self.registered_hotkeys[hotkey] = callback
        return True

    def unregister_all(self) -> None:
        self.registered_hotkeys.clear()

    def trigger(self, hotkey: str) -> None:
        """Simulate hotkey press in test environment."""
        if hotkey in self.registered_hotkeys:
            self.registered_hotkeys[hotkey]()
