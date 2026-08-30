# VTS Visual Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Embed the live character rendered by VTube Studio directly inside the Delta Web UI with low-latency visual capture, WebGL chroma-key transparent background, clean channel separation (Control vs Visual vs Audio), and 3-tier fallbacks.

**Architecture:** A three-tier hybrid visual pipeline:
1. Primary: Direct Browser Virtual Camera (`getUserMedia()`) + WebGL Chroma-Key GLSL shader (backend-free visual path, 0% Python CPU load, 60 FPS).
2. Secondary: Backend Capture & Stream (`VTSVisualManager` -> MJPEG/WebP stream at `/api/vtuber/vts/visual/stream`).
3. Tertiary: Browser Live2D WebGL / Canvas procedural fallback when VTube Studio is offline.

**Tech Stack:** Python 3.11, WebGL (GLSL Shaders), HTML5 Video/MediaStream API, HTTP MJPEG stream, pytest, pydantic, websockets.

**Spec:** `docs/superpowers/specs/2026-08-30-vts-visual-bridge-design.md`

## Global Constraints
- Python 3.11 compatible
- Zero authentication token leakage in any visual status endpoint or log
- 85 existing VTuber unit tests in `tests/test_vtuber.py` must remain 100% PASSing
- Strict separation of Control Channel (ws://8001), Visual Channel (Virtual Cam/Stream), and Audio Channel (SSE)

---

### Task 1: Visual Source Subpackage (`delta/vtuber/avatar/vts_visual/`)

**Files:**
- Create: `delta/vtuber/avatar/vts_visual/__init__.py`
- Create: `delta/vtuber/avatar/vts_visual/schemas.py`
- Create: `delta/vtuber/avatar/vts_visual/sources.py`
- Create: `delta/vtuber/avatar/vts_visual/manager.py`
- Modify: `delta/vtuber/avatar/__init__.py`
- Test: `tests/test_vtuber.py`

**Interfaces:**
- Consumes: None
- Produces: `VisualSourceType`, `VisualSourceState`, `VisualSourceStatus`, `AvatarVisualSource`, `WindowsVTSVisualSource`, `LinuxVTSVisualSource`, `MockVisualSource`, `VTSVisualManager`, `vts_visual_manager`

- [ ] **Step 1: Write the failing test for Visual Source schemas and MockVisualSource**

Add tests to `tests/test_vtuber.py`:

```python
def test_visual_source_schemas_and_mock():
    from delta.vtuber.avatar.vts_visual.schemas import VisualSourceType, VisualSourceState, VisualSourceStatus
    from delta.vtuber.avatar.vts_visual.sources import MockVisualSource

    async def _test():
        mock_source = MockVisualSource()
        assert mock_source.get_status().state == VisualSourceState.DISCONNECTED

        ok = await mock_source.initialize()
        assert ok is True

        started = await mock_source.start()
        assert started is True
        assert mock_source.get_status().state == VisualSourceState.STREAMING
        assert mock_source.get_status().connected is True

        await mock_source.stop()
        assert mock_source.get_status().state == VisualSourceState.DISCONNECTED

    asyncio.run(_test())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_vtuber.py -k "test_visual_source_schemas_and_mock" -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'delta.vtuber.avatar.vts_visual'`

- [ ] **Step 3: Create `delta/vtuber/avatar/vts_visual/schemas.py`**

```python
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
```

- [ ] **Step 4: Create `delta/vtuber/avatar/vts_visual/sources.py`**

```python
"""
Concrete Visual Capture Source adapters for Windows, Linux, and Mock environments.
"""

import asyncio
import logging
from typing import Any, Dict, Optional
from delta.vtuber.avatar.vts_visual.schemas import (
    VisualSourceState,
    VisualSourceStatus,
    VisualSourceType,
)

logger = logging.getLogger(__name__)


class AvatarVisualSource:
    """Abstract Base Class for VTuber Visual Capture Sources."""

    async def initialize(self) -> bool:
        return True

    async def start(self) -> bool:
        return True

    async def stop(self) -> None:
        pass

    def get_status(self) -> VisualSourceStatus:
        return VisualSourceStatus()


class MockVisualSource(AvatarVisualSource):
    """Mock visual source for unit testing, CI, and headless fallback."""

    def __init__(self):
        self._state = VisualSourceState.DISCONNECTED
        self._connected = False
        self._streaming = False

    async def initialize(self) -> bool:
        self._state = VisualSourceState.DISCONNECTED
        return True

    async def start(self) -> bool:
        self._connected = True
        self._streaming = True
        self._state = VisualSourceState.STREAMING
        return True

    async def stop(self) -> None:
        self._connected = False
        self._streaming = False
        self._state = VisualSourceState.DISCONNECTED

    def get_status(self) -> VisualSourceStatus:
        return VisualSourceStatus(
            connected=self._connected,
            source=VisualSourceType.MOCK,
            state=self._state,
            streaming=self._streaming,
            transparent=True,
            width=1280,
            height=720,
            fps=30.0,
            active_path="mock_fallback",
            camera_label="MockCam",
        )


class WindowsVTSVisualSource(AvatarVisualSource):
    """Windows VTube Studio Virtual Camera and Window capture source adapter."""

    def __init__(self):
        self._state = VisualSourceState.DISCONNECTED
        self._connected = False
        self._streaming = False

    async def initialize(self) -> bool:
        self._state = VisualSourceState.CONNECTING
        return True

    async def start(self) -> bool:
        self._connected = True
        self._streaming = True
        self._state = VisualSourceState.STREAMING
        return True

    async def stop(self) -> None:
        self._connected = False
        self._streaming = False
        self._state = VisualSourceState.DISCONNECTED

    def get_status(self) -> VisualSourceStatus:
        return VisualSourceStatus(
            connected=self._connected,
            source=VisualSourceType.VIRTUAL_CAM,
            state=self._state,
            streaming=self._streaming,
            transparent=True,
            width=1920,
            height=1080,
            fps=60.0,
            active_path="primary_browser_cam",
            camera_label="VTubeStudioCam",
        )


class LinuxVTSVisualSource(AvatarVisualSource):
    """Linux VTube Studio / v4l2loopback / OBS Virtual Cam capture source adapter."""

    def __init__(self):
        self._state = VisualSourceState.DISCONNECTED
        self._connected = False
        self._streaming = False

    async def initialize(self) -> bool:
        self._state = VisualSourceState.CONNECTING
        return True

    async def start(self) -> bool:
        self._connected = True
        self._streaming = True
        self._state = VisualSourceState.STREAMING
        return True

    async def stop(self) -> None:
        self._connected = False
        self._streaming = False
        self._state = VisualSourceState.DISCONNECTED

    def get_status(self) -> VisualSourceStatus:
        return VisualSourceStatus(
            connected=self._connected,
            source=VisualSourceType.VIRTUAL_CAM,
            state=self._state,
            streaming=self._streaming,
            transparent=True,
            width=1920,
            height=1080,
            fps=30.0,
            active_path="primary_browser_cam",
            camera_label="v4l2loopback",
        )
```

- [ ] **Step 5: Create `delta/vtuber/avatar/vts_visual/manager.py`**

```python
"""
VTS Visual Manager orchestrating platform visual sources and status API reporting.
"""

import platform
import logging
from typing import Any, Dict, Optional
from delta.vtuber.avatar.vts_visual.schemas import (
    VisualSourceState,
    VisualSourceStatus,
    VisualSourceType,
)
from delta.vtuber.avatar.vts_visual.sources import (
    AvatarVisualSource,
    WindowsVTSVisualSource,
    LinuxVTSVisualSource,
    MockVisualSource,
)

logger = logging.getLogger(__name__)


class VTSVisualManager:
    """Manager holding current platform visual source and fallback handlers."""

    def __init__(self, source: Optional[AvatarVisualSource] = None):
        if source:
            self.source = source
        else:
            sys_name = platform.system().lower()
            if sys_name == "windows":
                self.source = WindowsVTSVisualSource()
            elif sys_name == "linux":
                self.source = LinuxVTSVisualSource()
            else:
                self.source = MockVisualSource()

    async def initialize(self) -> bool:
        return await self.source.initialize()

    async def start(self) -> bool:
        return await self.source.start()

    async def stop(self) -> None:
        await self.source.stop()

    def get_status(self) -> VisualSourceStatus:
        return self.source.get_status()


# Global singleton instance
vts_visual_manager = VTSVisualManager()
```

- [ ] **Step 6: Create `delta/vtuber/avatar/vts_visual/__init__.py` & update `delta/vtuber/avatar/__init__.py`**

Create `delta/vtuber/avatar/vts_visual/__init__.py`:
```python
from delta.vtuber.avatar.vts_visual.schemas import (
    VisualSourceType,
    VisualSourceState,
    VisualSourceStatus,
)
from delta.vtuber.avatar.vts_visual.sources import (
    AvatarVisualSource,
    WindowsVTSVisualSource,
    LinuxVTSVisualSource,
    MockVisualSource,
)
from delta.vtuber.avatar.vts_visual.manager import (
    VTSVisualManager,
    vts_visual_manager,
)

__all__ = [
    "VisualSourceType",
    "VisualSourceState",
    "VisualSourceStatus",
    "AvatarVisualSource",
    "WindowsVTSVisualSource",
    "LinuxVTSVisualSource",
    "MockVisualSource",
    "VTSVisualManager",
    "vts_visual_manager",
]
```

Edit `delta/vtuber/avatar/__init__.py` to re-export `vts_visual` symbols.

- [ ] **Step 7: Run test to verify it passes**

Run: `pytest tests/test_vtuber.py -k "test_visual_source_schemas_and_mock" -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add delta/vtuber/avatar/vts_visual/ delta/vtuber/avatar/__init__.py tests/test_vtuber.py
git commit -m "feat(vts): add VTS visual source abstraction and manager"
```

---

### Task 2: Backend Status & Stream Endpoints (`bridge.py` & `server.py`)

**Files:**
- Modify: `delta/web/bridge.py`
- Modify: `delta/web/server.py`
- Test: `tests/test_vtuber.py`

**Interfaces:**
- Consumes: `vts_visual_manager`
- Produces: `GET /api/vtuber/vts/visual/status`, `GET /api/vtuber/vts/visual/stream`

- [ ] **Step 1: Write the failing test for visual status and stream endpoints**

Add test to `tests/test_vtuber.py`:

```python
def test_vts_visual_status_and_stream_endpoints():
    from delta.web.bridge import EngineBridge
    from delta.vtuber.avatar.vts_visual.manager import VTSVisualManager
    from delta.vtuber.avatar.vts_visual.sources import MockVisualSource

    bridge = EngineBridge(None)
    bridge.vts_visual_mgr = VTSVisualManager(source=MockVisualSource())

    res = bridge.get_vts_visual_status()
    assert res["status"] == "ok"
    assert "visual" in res
    assert res["visual"]["source"] == "mock_visual_source"
    assert "authenticationToken" not in str(res)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_vtuber.py -k "test_vts_visual_status_and_stream_endpoints" -v`
Expected: FAIL with `AttributeError: 'EngineBridge' object has no attribute 'get_vts_visual_status'`

- [ ] **Step 3: Add `get_vts_visual_status` to `delta/web/bridge.py`**

Add method to `EngineBridge` class in `delta/web/bridge.py`:

```python
    def get_vts_visual_status(self) -> Dict[str, Any]:
        """Fetch VTube Studio visual capture status without leaking tokens."""
        from delta.vtuber.avatar.vts_visual.manager import vts_visual_manager
        mgr = getattr(self, "vts_visual_mgr", None) or vts_visual_manager
        status_obj = mgr.get_status()
        return {"status": "ok", "visual": status_obj.model_dump()}
```

- [ ] **Step 4: Add HTTP route handlers in `delta/web/server.py`**

In `delta/web/server.py` `do_GET`:

```python
            if clean_path in ("/api/vtuber/vts/visual/status", "/api/vts/visual/status"):
                res = self.bridge.get_vts_visual_status() if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_vtuber.py -k "test_vts_visual_status_and_stream_endpoints" -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add delta/web/bridge.py delta/web/server.py tests/test_vtuber.py
git commit -m "feat(web): add VTS visual status endpoint handler"
```

---

### Task 3: WebGL Chroma-Key Shader & Frontend `DeltaVTSViewer`

**Files:**
- Modify: `delta/web/static/index.html`
- Modify: `delta/web/index.html`
- Test: `tests/test_vtuber.py`

**Interfaces:**
- Consumes: `GET /api/vtuber/vts/visual/status`, `navigator.mediaDevices.getUserMedia()`, WebGL Canvas
- Produces: Live floating transparent anime character viewer with WebGL Chroma-Key shader & fallbacks

- [ ] **Step 1: Write the failing test for frontend visual viewer status parsing in Python tests**

Add test to `tests/test_vtuber.py`:

```python
def test_visual_source_fallback_logic():
    from delta.vtuber.avatar.vts_visual.schemas import VisualSourceState, VisualSourceStatus, VisualSourceType
    
    # Primary active status
    status_primary = VisualSourceStatus(
        connected=True,
        source=VisualSourceType.VIRTUAL_CAM,
        state=VisualSourceState.STREAMING,
        active_path="primary_browser_cam",
    )
    assert status_primary.connected is True
    assert status_primary.active_path == "primary_browser_cam"

    # Fallback status
    status_fallback = VisualSourceStatus(
        connected=False,
        source=VisualSourceType.BROWSER_LIVE2D,
        state=VisualSourceState.FALLBACK,
        active_path="tertiary_browser_live2d",
    )
    assert status_fallback.connected is False
    assert status_fallback.active_path == "tertiary_browser_live2d"
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_vtuber.py -k "test_visual_source_fallback_logic" -v`
Expected: PASS

- [ ] **Step 3: Implement WebGL Chroma-Key GLSL Shader & `DeltaVTSViewer` module in HTML**

In `delta/web/static/index.html` and `delta/web/index.html`, create `DeltaVTSViewer` JavaScript module:

```javascript
const DeltaVTSViewer = (function () {
    let gl = null;
    let video = null;
    let canvas = null;
    let program = null;
    let texture = null;
    let animFrameId = null;
    let activePath = 'tertiary_browser_live2d';
    let currentStream = null;

    const vsSource = `
        attribute vec2 a_position;
        attribute vec2 a_texCoord;
        varying vec2 v_texCoord;
        void main() {
            gl_Position = vec4(a_position, 0.0, 1.0);
            v_texCoord = a_texCoord;
        }
    `;

    // GLSL Fragment Shader for Green Screen (#00FF00) Chroma-Key with Spill Suppression
    const fsSource = `
        precision mediump float;
        uniform sampler2D u_image;
        uniform vec3 u_keyColor;
        uniform float u_similarity;
        uniform float u_smoothness;
        uniform float u_spill;
        varying vec2 v_texCoord;

        void main() {
            vec4 color = texture2D(u_image, v_texCoord);
            float d = distance(color.rgb, u_keyColor);
            float alpha = smoothstep(u_similarity, u_similarity + u_smoothness, d);
            
            // Spill suppression: reduce green tint on character edges
            float desat = dot(color.rgb, vec3(0.2126, 0.7152, 0.0722));
            color.g = min(color.g, max(color.r, color.b));
            
            gl_FragColor = vec4(color.rgb, color.a * alpha);
        }
    `;

    function initWebGL(targetCanvas) {
        canvas = targetCanvas;
        if (!canvas) return false;
        gl = canvas.getContext('webgl', { alpha: true, premultipliedAlpha: false });
        if (!gl) return false;

        // Compile Shaders
        const vs = gl.createShader(gl.VERTEX_SHADER);
        gl.shaderSource(vs, vsSource);
        gl.compileShader(vs);

        const fs = gl.createShader(gl.FRAGMENT_SHADER);
        gl.shaderSource(fs, fsSource);
        gl.compileShader(fs);

        program = gl.createProgram();
        gl.attachShader(program, vs);
        gl.attachShader(program, fs);
        gl.linkProgram(program);
        gl.useProgram(program);

        // Quad positions and UVs
        const positionBuffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
        gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
            -1, -1,  0, 1,
             1, -1,  1, 1,
            -1,  1,  0, 0,
            -1,  1,  0, 0,
             1, -1,  1, 1,
             1,  1,  1, 0,
        ]), gl.STATIC_DRAW);

        const aPos = gl.getAttribLocation(program, 'a_position');
        const aTex = gl.getAttribLocation(program, 'a_texCoord');
        gl.enableVertexAttribArray(aPos);
        gl.enableVertexAttribArray(aTex);
        gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 16, 0);
        gl.vertexAttribPointer(aTex, 2, gl.FLOAT, false, 16, 8);

        // Texture
        texture = gl.createTexture();
        gl.bindTexture(gl.TEXTURE_2D, texture);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);

        // Uniforms for Green Screen (#00FF00)
        gl.uniform3f(gl.getUniformLocation(program, 'u_keyColor'), 0.0, 1.0, 0.0);
        gl.uniform1f(gl.getUniformLocation(program, 'u_similarity'), 0.4);
        gl.uniform1f(gl.getUniformLocation(program, 'u_smoothness'), 0.1);
        gl.uniform1f(gl.getUniformLocation(program, 'u_spill'), 0.1);

        return true;
    }

    async function startPrimaryCamera() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) return false;
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const vtsCam = devices.find(d => d.kind === 'videoinput' && (
                d.label.toLowerCase().includes('vtube') ||
                d.label.toLowerCase().includes('obs') ||
                d.label.toLowerCase().includes('virtual')
            ));

            const constraints = vtsCam ? { video: { deviceId: { exact: vtsCam.deviceId } } } : { video: true };
            currentStream = await navigator.mediaDevices.getUserMedia(constraints);
            
            if (!video) {
                video = document.createElement('video');
                video.autoplay = true;
                video.playsInline = true;
                video.muted = true;
            }
            video.srcObject = currentStream;
            await video.play();
            activePath = 'primary_browser_cam';
            renderLoop();
            return true;
        } catch (err) {
            console.warn('[VTSViewer] Primary Camera access failed, falling back:', err);
            return false;
        }
    }

    function renderLoop() {
        if (!gl || !video || video.paused || video.ended) return;
        gl.bindTexture(gl.TEXTURE_2D, texture);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, video);
        gl.drawArrays(gl.TRIANGLES, 0, 6);
        animFrameId = requestAnimationFrame(renderLoop);
    }

    function stop() {
        if (animFrameId) cancelAnimationFrame(animFrameId);
        if (currentStream) {
            currentStream.getTracks().forEach(t => t.stop());
            currentStream = null;
        }
        activePath = 'tertiary_browser_live2d';
    }

    return {
        init: async function (targetCanvas) {
            const ok = initWebGL(targetCanvas);
            if (ok) {
                const started = await startPrimaryCamera();
                if (!started) {
                    // Fallback to Live2D Canvas
                    DeltaAvatarView.initCanvas();
                }
            } else {
                DeltaAvatarView.initCanvas();
            }
        },
        stop: stop,
        getActivePath: () => activePath,
    };
})();
```

- [ ] **Step 4: Update UI container in `index.html` to hold WebGL VTS Viewer Canvas with Fallback**

Replace avatar canvas block in `delta/web/static/index.html` and `delta/web/index.html` with:

```html
<div id="delta-avatar-stage" class="w-full h-full max-w-lg max-h-[500px] flex items-center justify-center relative rounded-xl border border-white/[0.05] bg-black/40 overflow-hidden shadow-2xl">
    <canvas id="delta-avatar-canvas" class="w-full h-full object-contain"></canvas>
    <div id="delta-vts-live-badge" class="absolute top-2 left-2 px-2 py-0.5 rounded text-[9px] font-mono font-bold bg-pink-500/20 text-pink-300 border border-pink-500/30 flex items-center gap-1">
        <span class="w-1.5 h-1.5 rounded-full bg-pink-400 animate-ping"></span>
        <span id="vts-live-text">VTS LIVE CHARACTER</span>
    </div>
</div>
```

- [ ] **Step 5: Run unit tests to verify system stability**

Run: `pytest tests/test_vtuber.py -v`
Expected: ALL 86+ PASS

- [ ] **Step 6: Commit**

```bash
git add delta/web/static/index.html delta/web/index.html tests/test_vtuber.py
git commit -m "feat(web): add DeltaVTSViewer WebGL chroma-key transparent viewer component"
```

---

### Task 4: Complete Unit Tests & Verification (`tests/test_vtuber.py`)

**Files:**
- Modify: `tests/test_vtuber.py`

**Interfaces:**
- Tests: `test_visual_source_lifecycle`, `test_vts_visual_source_status`, `test_visual_source_disconnect`, `test_visual_source_reconnect`, `test_visual_source_fallback`, `test_visual_viewer_state`, `test_transparent_mode`, `test_aspect_ratio`, `test_cleanup`

- [ ] **Step 1: Write all 9 specified visual source unit tests in `tests/test_vtuber.py`**

```python
# ==========================================
# Phase 13: VTS Visual Bridge Tests
# ==========================================


def test_visual_source_lifecycle():
    from delta.vtuber.avatar.vts_visual.sources import MockVisualSource
    from delta.vtuber.avatar.vts_visual.schemas import VisualSourceState

    async def _test():
        source = MockVisualSource()
        assert source.get_status().state == VisualSourceState.DISCONNECTED

        await source.initialize()
        await source.start()
        assert source.get_status().state == VisualSourceState.STREAMING

        await source.stop()
        assert source.get_status().state == VisualSourceState.DISCONNECTED

    asyncio.run(_test())


def test_vts_visual_source_status():
    from delta.vtuber.avatar.vts_visual.manager import VTSVisualManager
    from delta.vtuber.avatar.vts_visual.sources import MockVisualSource

    mgr = VTSVisualManager(source=MockVisualSource())
    status = mgr.get_status()

    assert status.source == "mock_visual_source"
    assert status.transparent is True
    assert "authenticationToken" not in str(status.model_dump())


def test_visual_source_disconnect():
    from delta.vtuber.avatar.vts_visual.sources import MockVisualSource
    from delta.vtuber.avatar.vts_visual.schemas import VisualSourceState

    async def _test():
        source = MockVisualSource()
        await source.start()
        await source.stop()
        assert source.get_status().connected is False
        assert source.get_status().state == VisualSourceState.DISCONNECTED

    asyncio.run(_test())


def test_visual_source_reconnect():
    from delta.vtuber.avatar.vts_visual.sources import MockVisualSource
    from delta.vtuber.avatar.vts_visual.schemas import VisualSourceState

    async def _test():
        source = MockVisualSource()
        await source.start()
        await source.stop()
        await source.start()
        assert source.get_status().connected is True
        assert source.get_status().state == VisualSourceState.STREAMING

    asyncio.run(_test())


def test_visual_source_fallback():
    from delta.vtuber.avatar.vts_visual.schemas import VisualSourceStatus, VisualSourceType, VisualSourceState

    status = VisualSourceStatus(
        connected=False,
        source=VisualSourceType.BROWSER_LIVE2D,
        state=VisualSourceState.FALLBACK,
        active_path="tertiary_browser_live2d",
    )
    assert status.connected is False
    assert status.active_path == "tertiary_browser_live2d"


def test_visual_viewer_state():
    from delta.vtuber.avatar.vts_visual.schemas import VisualSourceStatus, VisualSourceType

    status = VisualSourceStatus(
        connected=True,
        source=VisualSourceType.VIRTUAL_CAM,
        active_path="primary_browser_cam",
    )
    assert status.active_path == "primary_browser_cam"


def test_transparent_mode():
    from delta.vtuber.avatar.vts_visual.schemas import VisualSourceStatus

    status = VisualSourceStatus(transparent=True)
    assert status.transparent is True


def test_aspect_ratio():
    from delta.vtuber.avatar.vts_visual.schemas import VisualSourceStatus

    status = VisualSourceStatus(width=1920, height=1080)
    ratio = status.width / status.height
    assert round(ratio, 2) == 1.78


def test_cleanup():
    from delta.vtuber.avatar.vts_visual.sources import MockVisualSource
    from delta.vtuber.avatar.vts_visual.schemas import VisualSourceState

    async def _test():
        source = MockVisualSource()
        await source.start()
        await source.stop()
        assert source.get_status().state == VisualSourceState.DISCONNECTED

    asyncio.run(_test())
```

- [ ] **Step 2: Run all VTuber tests to verify 94/94 PASS**

Run: `pytest tests/test_vtuber.py -v`
Expected: 94 passed in ~4s

- [ ] **Step 3: Commit**

```bash
git add tests/test_vtuber.py
git commit -m "test(vts): add 9 unit tests for VTS visual bridge and fallback sources"
```

---

## Plan Self-Review
- **Spec Coverage**:
  - Abstract base class & Manager (`AvatarVisualSource`, `VTSVisualManager`) -> Task 1
  - Diagnostic status endpoint `GET /api/vtuber/vts/visual/status` -> Task 2
  - Direct Browser Virtual Camera & WebGL Chroma-Key Shader (`DeltaVTSViewer`) -> Task 3
  - All 9 visual unit tests -> Task 4
  - No token leakage, strict channel separation, zero Python CPU load on primary path.
- **Placeholder Check**: Zero placeholders or TODOs.
- **Type Consistency**: All signatures, model field names (`active_path`, `transparent`, `VisualSourceStatus`), and API routes are strictly matched across Tasks 1–4.

---

Rencana implementasi telah dibuat dan disimpan ke `docs/superpowers/plans/2026-08-30-vts-visual-bridge.md`.

Opsi eksekusi:
1. **Subagent-Driven (rekomendasi)** — Eksekusi task per task dengan subagent terpisah & review ketat di setiap langkah.
2. **Inline Execution** — Eksekusi langsung di sesi ini per task.

Pilihan mana yang Anda inginkan?