"""
Desktop Overlay Controller for Delta VTuber.
"""

from typing import Any, Dict
from delta.vtuber.desktop.schemas import OverlayMode


class DesktopOverlayController:
    """
    Manages desktop companion overlay state, mode, visibility, and click-through options.
    """

    def __init__(
        self,
        mode: OverlayMode = OverlayMode.NORMAL,
        always_on_top: bool = False,
        click_through: bool = False,
        visible: bool = True,
    ):
        self.mode = mode
        self.always_on_top = always_on_top
        self.click_through = click_through
        self.visible = visible

    def set_mode(self, mode: OverlayMode) -> None:
        self.mode = mode

    def toggle_visibility(self) -> bool:
        self.visible = not self.visible
        return self.visible

    def get_state(self) -> Dict[str, Any]:
        return {
            "mode": self.mode.value,
            "always_on_top": self.always_on_top,
            "click_through": self.click_through,
            "visible": self.visible,
        }
