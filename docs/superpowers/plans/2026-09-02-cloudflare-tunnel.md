# Delta Cloudflare Quick Tunnel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Cloudflare Quick Tunnel auto-discovery and lifecycle management in Delta CLI and integrate remote tunnel connection options into Delta Mobile App.

**Architecture:** Python `cloudflared` wrapper manages ephemeral secure tunnels and surfaces the public HTTPS URL via REST endpoint `/api/tunnel` and CLI. The Mobile App stores and connects to this URL seamlessly over internet/4G.

**Tech Stack:** Python 3.10+, `cloudflared` subprocess, React Native / Expo, Zustand, TypeScript.

---

### Task 1: Cloudflare Tunnel Manager Backend

**Files:**
- Create: `delta/utils/tunnel_manager.py`
- Test: `tests/test_tunnel_manager.py`

**Interfaces:**
- Produces: `start_cloudflare_tunnel(port: int = 8080) -> Dict[str, Any]`, `stop_cloudflare_tunnel() -> bool`, `get_tunnel_status() -> Dict[str, Any]`

- [ ] **Step 1: Write failing test for tunnel manager**

```python
# tests/test_tunnel_manager.py
from delta.utils.tunnel_manager import is_cloudflared_available, get_tunnel_status

def test_tunnel_status_initial():
    status = get_tunnel_status()
    assert isinstance(status, dict)
    assert "running" in status
    assert "url" in status
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_tunnel_manager.py -v`

- [ ] **Step 3: Implement `delta/utils/tunnel_manager.py`**

```python
"""Cloudflare Quick Tunnel Process Manager for Delta."""
import re
import shutil
import subprocess
import threading
import time
from typing import Any, Dict, Optional

_tunnel_process: Optional[subprocess.Popen] = None
_tunnel_url: Optional[str] = None
_tunnel_lock = threading.Lock()

TRY_CLOUDFLARE_REGEX = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

def is_cloudflared_available() -> bool:
    return shutil.which("cloudflared") is not None

def get_tunnel_status() -> Dict[str, Any]:
    global _tunnel_process, _tunnel_url
    running = _tunnel_process is not None and _tunnel_process.poll() is None
    return {
        "running": running,
        "url": _tunnel_url if running else None,
        "available": is_cloudflared_available()
    }

def start_cloudflare_tunnel(port: int = 8080, timeout: float = 25.0) -> Dict[str, Any]:
    global _tunnel_process, _tunnel_url
    with _tunnel_lock:
        if _tunnel_process is not None and _tunnel_process.poll() is None:
            return {"status": "ok", "running": True, "url": _tunnel_url}

        if not is_cloudflared_available():
            return {
                "status": "error",
                "running": False,
                "url": None,
                "message": "cloudflared binary not found. Install from https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
            }

        _tunnel_url = None
        cmd = ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}"]
        _tunnel_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        deadline = time.time() + timeout
        while time.time() < deadline:
            if _tunnel_process.poll() is not None:
                break
            line = _tunnel_process.stdout.readline() if _tunnel_process.stdout else ""
            if line:
                match = TRY_CLOUDFLARE_REGEX.search(line)
                if match:
                    _tunnel_url = match.group(0)
                    break
            time.sleep(0.1)

        if _tunnel_url:
            return {"status": "ok", "running": True, "url": _tunnel_url}
        return {"status": "error", "running": False, "url": None, "message": "Failed to obtain Cloudflare tunnel URL"}

def stop_cloudflare_tunnel() -> bool:
    global _tunnel_process, _tunnel_url
    with _tunnel_lock:
        if _tunnel_process and _tunnel_process.poll() is None:
            _tunnel_process.terminate()
            try:
                _tunnel_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                _tunnel_process.kill()
            _tunnel_process = None
            _tunnel_url = None
            return True
        _tunnel_process = None
        _tunnel_url = None
        return False
```

- [ ] **Step 4: Run test to verify pass**

Run: `pytest tests/test_tunnel_manager.py -v`

- [ ] **Step 5: Commit**

```bash
git add delta/utils/tunnel_manager.py tests/test_tunnel_manager.py
git commit -m "feat(tunnel): add cloudflare quick tunnel manager backend"
```

---

### Task 2: Web Server & Bridge API Endpoints

**Files:**
- Modify: `delta/web/bridge.py`
- Modify: `delta/web/server.py`

**Interfaces:**
- Produces: `GET /api/tunnel`, `POST /api/tunnel/start`, `POST /api/tunnel/stop`

- [ ] **Step 1: Add bridge methods in `delta/web/bridge.py`**
- [ ] **Step 2: Wire endpoints in `delta/web/server.py` (`do_GET` and `do_POST`)**
- [ ] **Step 3: Test REST endpoints via `pytest tests/test_web_server.py`**
- [ ] **Step 4: Commit**

```bash
git add delta/web/bridge.py delta/web/server.py
git commit -m "feat(api): expose cloudflare tunnel management endpoints"
```

---

### Task 3: Mobile App Tunnel Connection Support

**Files:**
- Modify: `delta/mobile/src/store/useSettingsStore.ts`
- Modify: `delta/mobile/app/(tabs)/settings.tsx`
- Modify: `delta/mobile/src/services/api/apiClient.ts`

**Interfaces:**
- Produces: ConnectionMode `'tunnel'`, configurable `tunnelUrl`, automatic route switching.

- [ ] **Step 1: Update `ConnectionMode` type and store in `useSettingsStore.ts`**
- [ ] **Step 2: Add Cloudflare Tunnel selector and URL input in `settings.tsx`**
- [ ] **Step 3: Update `apiClient.ts` to route requests to `tunnelUrl` when in `'tunnel'` mode**
- [ ] **Step 4: Test TypeScript build `npm run typecheck`**
- [ ] **Step 5: Commit**

```bash
git add delta/mobile/src/store/useSettingsStore.ts delta/mobile/app/(tabs)/settings.tsx delta/mobile/src/services/api/apiClient.ts
git commit -m "feat(mobile): add cloudflare tunnel remote connection mode"
```
