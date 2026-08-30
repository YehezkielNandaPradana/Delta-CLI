"""
Data schemas and status models for Delta VTS Visual Bridge.
"""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class VisualSourceType(str, Enum):
    VIRTUAL_CAM = "vtube_studio_virtual_cam"
    WINDOW_CAPTURE = "vtube_studio_window"
    BROWSER_LIVE2D = "browser_live2d"
    MOCK = "mock_visual_source"


class VisualSourceState(str, Enum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    STREAMING = "STREAMING"
    FALLBACK = "FALLBACK"
    ERROR = "ERROR"


class VisualSourceStatus(BaseModel):
    connected: bool = False
    source: VisualSourceType = VisualSourceType.MOCK
    state: VisualSourceState = VisualSourceState.DISCONNECTED
    streaming: bool = False
    transparent: bool = True
    width: int = 1920
    height: int = 1080
    fps: float = 0.0
    active_path: str = "primary_browser_cam"
    camera_label: Optional[str] = "VTubeStudioCam"
    last_error: Optional[Dict[str, Any]] = None
