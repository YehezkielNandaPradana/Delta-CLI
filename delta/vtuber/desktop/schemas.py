"""
Data schemas and models for Delta VTuber Desktop Intelligence & Context System.
"""

import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DesktopCapability(str, Enum):
    ACTIVE_WINDOW = "active_window"
    WORKSPACE = "workspace"
    SCREENSHOT = "screenshot"
    CLIPBOARD = "clipboard"
    GLOBAL_HOTKEY = "global_hotkey"
    DESKTOP_NOTIFICATION = "desktop_notification"
    DESKTOP_OVERLAY = "desktop_overlay"


class ActiveWindow(BaseModel):
    application: Optional[str] = None
    window_title: Optional[str] = None
    process_name: Optional[str] = None
    pid: Optional[int] = None
    timestamp: float = Field(default_factory=time.time)


class ProjectContext(BaseModel):
    project_name: Optional[str] = None
    project_path: Optional[str] = None
    language: Optional[str] = None
    framework: Optional[str] = None
    git_branch: Optional[str] = None
    active_file: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DesktopContext(BaseModel):
    """
    On-demand snapshot of user's active desktop environment.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    active_application: Optional[str] = None
    active_window_title: Optional[str] = None
    workspace_path: Optional[str] = None
    workspace_name: Optional[str] = None
    active_file: Optional[str] = None
    git_branch: Optional[str] = None
    clipboard_available: bool = False
    timestamp: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScreenshotData(BaseModel):
    """
    Ephemeral in-memory screenshot payload.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    image_base64: str = ""
    format: str = "png"
    width: int = 0
    height: int = 0
    timestamp: float = Field(default_factory=time.time)
    retention: str = "ephemeral"


class ClipboardData(BaseModel):
    """
    Sanitized text from user clipboard.
    """
    text: Optional[str] = None
    has_content: bool = False
    timestamp: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OverlayMode(str, Enum):
    NORMAL = "normal"
    COMPACT = "compact"
    AVATAR_ONLY = "avatar_only"
    VOICE_ONLY = "voice_only"
