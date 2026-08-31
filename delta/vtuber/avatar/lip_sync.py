"""
Lip Sync Controller Abstraction and Implementation for Delta VTuber.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class LipSyncController(Protocol):
    """
    Protocol defining the interface for avatar mouth opening and lip sync controllers.
    """

    async def update_amplitude(self, amplitude: float) -> None:
        """
        Update mouth opening level (0.0 = closed, 1.0 = fully open).
        """
        ...

    async def reset(self) -> None:
        """
        Reset mouth to closed rest position.
        """
        ...

    @property
    def current_mouth_open(self) -> float:
        ...


class DefaultLipSyncController:
    """
    Default in-memory lip-sync controller.
    Clamps mouth amplitude values between 0.0 and 1.0 with smoothing.
    """

    def __init__(self, smoothing_factor: float = 0.7):
        self.smoothing_factor = smoothing_factor
        self._mouth_open: float = 0.0
        self._mouth_form: float = 0.0

    @property
    def current_mouth_open(self) -> float:
        return self._mouth_open

    @property
    def current_mouth_form(self) -> float:
        return self._mouth_form

    async def update_amplitude(self, amplitude: float) -> None:
        clamped = max(0.0, min(1.0, float(amplitude)))
        # Exponential smoothing: S_t = alpha * Y_t + (1 - alpha) * S_{t-1}
        self._mouth_open = round(self.smoothing_factor * clamped + (1.0 - self.smoothing_factor) * self._mouth_open, 3)

    async def reset(self) -> None:
        self._mouth_open = 0.0
        self._mouth_form = 0.0
