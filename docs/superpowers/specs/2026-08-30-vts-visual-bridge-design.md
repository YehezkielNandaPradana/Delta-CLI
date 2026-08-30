# Delta VTS Visual Bridge — Design Document

**Date**: 2026-08-30  
**Status**: Approved  
**Scope**: Embedding VTube Studio rendered visual output into Delta Web UI with low latency, transparent background, separation of control/visual/audio channels, and multi-tier fallbacks.

---

## 1. System Overview & Principles

The VTS Visual Bridge provides a seamless integration where VTube Studio acts as a background renderer for the Delta VTuber character, while Delta Web displays the live visual character directly inside its UI interface (`#/vtuber`).

### Core Design Principles
1. **Strict Channel Separation**:
   - **Control Channel**: Delta → VTS WebSocket API (`ws://127.0.0.1:8001`) for model parameter injection (`ParamAngleX`, `ParamMouthOpenY`, expressions, physics).
   - **Visual Channel**: VTube Studio → Visual Capture → Delta Web (`DeltaVTSViewer`). Uses a **backend-free visual path** for the primary web camera stream to achieve zero additional backend hop delay.
   - **Audio Channel**: Delta TTS → Browser Audio SSE (`/api/vtuber/audio`).
2. **Three-Tier Hybrid Fallback Architecture**:
   - **Primary Path**: Direct Browser Virtual Camera (`navigator.mediaDevices.getUserMedia()`) + Realtime WebGL Chroma-Key GLSL Shader (transparent background, 60 FPS, 0% Python CPU load).
   - **Secondary Path**: Backend Capture & Frame Stream (`GET /api/vtuber/vts/visual/stream`) via Python `VTSVisualManager`.
   - **Tertiary Path**: Browser WebGL Live2D / Canvas procedural fallback when VTube Studio is offline or unauthenticated.
3. **Fault Tolerance & Safety**:
   - Zero authentication token leakage in any visual API endpoint or log.
   - Fail-safe fallback when VTS is closed or disconnected without interrupting Delta Core agent execution, STT, TTS, memory, or personality.

---

## 2. Python Backend Subsystem (`delta/vtuber/avatar/vts_visual/`)

### 2.1 Visual Source Abstraction Contract

```python
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
    active_path: str = "primary_browser_cam"  # "primary_browser_cam" | "secondary_backend_stream" | "tertiary_browser_live2d" | "procedural_fallback"
    camera_label: Optional[str] = "VTubeStudioCam"
    last_error: Optional[Dict[str, Any]] = None


class AvatarVisualSource:
    """Abstract Base Class for VTuber Visual Capture Sources."""

    async def initialize(self) -> bool:
        ...

    async def start(self) -> bool:
        ...

    async def stop(self) -> None:
        ...

    def get_status(self) -> VisualSourceStatus:
        ...
```

### 2.2 Concrete Implementations

1. `WindowsVTSVisualSource`:
   - Checks Windows system video devices and VTube Studio window presence.
   - Detects virtual camera drivers (e.g. OBS Virtual Camera / VTS Virtual Cam).
2. `LinuxVTSVisualSource`:
   - Checks `/dev/video*` devices (v4l2loopback) and OBS Virtual Cam on Linux.
3. `MockVisualSource`:
   - Provides mock frame metadata and status simulation for unit testing and headless CI.
4. `VTSVisualManager`:
   - Unified manager holding the active `AvatarVisualSource` instance.
   - Serves API status data and frame streaming feeds for secondary fallback.

---

## 3. Web API Endpoints (`delta/web/server.py` & `delta/web/bridge.py`)

### 3.1 Status & Telemetry Endpoint
`GET /api/vtuber/vts/visual/status`

**Response Payload:**
```json
{
  "status": "ok",
  "visual": {
    "connected": true,
    "source": "vtube_studio_virtual_cam",
    "state": "STREAMING",
    "streaming": true,
    "transparent": true,
    "width": 1920,
    "height": 1080,
    "fps": 60.0,
    "active_path": "primary_browser_cam",
    "camera_label": "VTubeStudioCam",
    "last_error": null
  }
}
```

### 3.2 Secondary Frame Stream Endpoint
`GET /api/vtuber/vts/visual/stream`
- Serves MJPEG (`multipart/x-mixed-replace`) or WebP frame stream if browser camera access is unavailable or denied.

---

## 4. Frontend Component (`DeltaVTSViewer` in `delta/web/static/index.html` & `delta/web/index.html`)

### 4.1 Component Responsibilities
- Replaces static avatar canvas area on `#/vtuber` and `#/vtuber/avatar`.
- Manages video stream element, WebGL Chroma-Key GLSL Shader context, aspect-ratio scaling (`contain`/`cover`), resize handlers, and auto-reconnection.
- Maintains floating transparent character presentation.

### 4.2 WebGL Chroma-Key GLSL Shader
Converts solid background (Green `#00FF00` or Blue `#0000FF`) into real-time transparent alpha pixels directly on the WebGL canvas:
- **RGB Distance Threshold**: Calculates color distance from background key color.
- **Alpha Smoothing**: Applies smooth step transparency curve around boundaries.
- **Spill Suppression**: Neutralizes green/blue fringe bounce on hair/clothing edges.

### 4.3 Fallback & Reconnection Decision Tree

```
               [ User Navigates to #/vtuber ]
                             │
                             ▼
         [ Fetch /api/vtuber/vts/visual/status ]
                             │
                             ▼
              Browser checks Virtual Cam device
             via navigator.mediaDevices.enumerateDevices()
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
   [ VTS Cam Device Found ]        [ VTS Cam Device Missing ]
            │                                 │
   Request getUserMedia()                     │
            │                                 │
      ┌─────┴─────┐                           │
      ▼           ▼                           │
  [Success]   [Denied/Err]                    │
      │           │                           │
      │           └───────────┬───────────────┘
      │                       │
      ▼                       ▼
  PRIMARY PATH      Check Backend Stream Status
 (Browser Cam +    (/api/vtuber/vts/visual/status)
 WebGL Chroma)                │
                              ├────────────────────────┐
                              ▼                        ▼
                       [Backend Active]       [Backend Offline]
                              │                        │
                        SECONDARY PATH           TERTIARY PATH
                        (MJPEG Stream)         (Browser WebGL Live2D
                                                 / Canvas Fallback)
```

---

## 5. Testing Strategy

1. **Unit Testing (`tests/test_vtuber.py`)**:
   - `test_visual_source_lifecycle`: Test initialize/start/stop on `MockVisualSource`.
   - `test_vts_visual_source_status`: Verify response structure of `/api/vtuber/vts/visual/status`.
   - `test_visual_source_disconnect`: State transition on disconnect.
   - `test_visual_source_reconnect`: Reconnection state transitions.
   - `test_visual_source_fallback`: Path switching verification (primary -> secondary -> tertiary).
   - `test_visual_viewer_state`: State machine output assertions.
   - `test_transparent_mode`: Transparency flag verification.
   - `test_aspect_ratio`: Dimension ratio validations.
   - `test_cleanup`: Resource release verification.
2. **Regression Check**:
   - All 85 existing VTuber test cases in `tests/test_vtuber.py` must remain 100% PASSing.
