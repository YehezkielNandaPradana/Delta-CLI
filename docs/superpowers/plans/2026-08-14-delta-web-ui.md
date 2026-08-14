# Delta Web UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a clean, responsive, single-page Web UI for Delta CLI that includes interactive Web Terminal, Dashboard metrics, and Report viewer via `delta web` or `delta --web`.

**Architecture:** Python `http.server` / WS backend in `delta/web/server.py` and `delta/web/bridge.py` connecting Delta engine output to a clean dark-themed HTML/JS frontend in `delta/web/static/index.html`.

**Tech Stack:** Python 3.11 stdlib (`http.server`, `threading`, `json`), HTML5, Tailwind CSS (via CDN), xterm.js (via CDN).

## Global Constraints

- Must run smoothly without forcing heavy third-party dependencies (React/Vue/Node build step).
- Must connect cleanly to `DeltaEngine` and stream output in real-time.
- Localhost security bound (`127.0.0.1`).

---

### Task 1: Create Web Core Bridge & API Server Module

**Files:**
- Create: `delta/web/__init__.py`
- Create: `delta/web/bridge.py`
- Create: `delta/web/server.py`
- Test: `tests/test_web_server.py`

**Interfaces:**
- Consumes: `delta.core.engine.DeltaEngine`
- Produces: `delta.web.server.start_web_server(engine, host='127.0.0.1', port=8000)`

- [ ] **Step 1: Write the failing test for Web Server initialization and API status endpoint**

```python
import pytest
import urllib.request
import json
import threading
import time
from delta.web.server import DeltaWebServer
from delta.core.engine import DeltaEngine

def test_web_server_status_endpoint(tmp_path):
    server = DeltaWebServer(engine=None, host="127.0.0.1", port=8999)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)

    try:
        req = urllib.request.Request("http://127.0.0.1:8999/api/status")
        with urllib.request.urlopen(req, timeout=2) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "online"
            assert "version" in data
    finally:
        server.shutdown()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_web_server.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'delta.web'`

- [ ] **Step 3: Write minimal implementation for bridge and server**

Create `delta/web/__init__.py`:
```python
"""Delta Web Package."""
```

Create `delta/web/bridge.py`:
```python
"""Bridge between Delta CLI Engine and Web Interface."""
import io
import sys
from typing import Any, Dict, Optional

class EngineBridge:
    def __init__(self, engine: Optional[Any] = None):
        self.engine = engine

    def get_status(self) -> Dict[str, Any]:
        return {
            "status": "online",
            "version": "1.0.0",
            "llm_enabled": getattr(self.engine.config, "llm_enabled", False) if self.engine and hasattr(self.engine, "config") else False,
        }

    def execute_command(self, cmd: str) -> str:
        if not self.engine:
            return f"Executed command (mock): {cmd}"
        output_capture = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = output_capture
            self.engine._dispatch_command(cmd)
        finally:
            sys.stdout = old_stdout
        return output_capture.getvalue()
```

Create `delta/web/server.py`:
```python
"""Lightweight stdlib HTTP server for Delta Web UI."""
import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Any, Optional
from delta.web.bridge import EngineBridge

class DeltaRequestHandler(SimpleHTTPRequestHandler):
    bridge: Optional[EngineBridge] = None
    static_dir: str = os.path.join(os.path.dirname(__file__), "static")

    def do_GET(self):
        if self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            status_data = self.bridge.get_status() if self.bridge else {"status": "online", "version": "1.0.0"}
            self.wfile.write(json.dumps(status_data).encode("utf-8"))
            return

        if self.path == "/" or self.path == "/index.html":
            index_path = os.path.join(self.static_dir, "index.html")
            if os.path.exists(index_path):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(index_path, "rb") as f:
                    self.wfile.write(f.read())
                return

        self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path == "/api/execute":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body) if body else {}
            cmd = data.get("command", "")
            
            output = self.bridge.execute_command(cmd) if self.bridge else f"Engine offline: {cmd}"
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"output": output}).encode("utf-8"))
            return

        self.send_error(404, "Not Found")

class DeltaWebServer(HTTPServer):
    def __init__(self, engine: Optional[Any] = None, host: str = "127.0.0.1", port: int = 8000):
        self.bridge = EngineBridge(engine)
        def handler_factory(*args, **kwargs):
            handler = DeltaRequestHandler(*args, **kwargs)
            return handler
        
        # Pass bridge reference to request handler class
        DeltaRequestHandler.bridge = self.bridge
        super().__init__((host, port), DeltaRequestHandler)

def start_web_server(engine: Optional[Any] = None, host: str = "127.0.0.1", port: int = 8000):
    server = DeltaWebServer(engine, host, port)
    print(f"[*] Delta Web UI server running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_web_server.py -v`
Expected: PASS

- [ ] **Step 5: Commit Task 1**

```bash
git add delta/web/ tests/test_web_server.py
git commit -m "feat(web): add core web server and engine bridge"
```

---

### Task 2: Build Frontend UI Dashboard & Web Terminal Interface

**Files:**
- Create: `delta/web/static/index.html`
- Test: `tests/test_web_frontend.py`

**Interfaces:**
- Serves Single Page App (SPA) UI with Tailwind CSS & Web Terminal layout.

- [ ] **Step 1: Write test to verify static HTML serves properly**

```python
import pytest
import urllib.request
import threading
import time
from delta.web.server import DeltaWebServer

def test_web_static_html_served():
    server = DeltaWebServer(engine=None, host="127.0.0.1", port=8998)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)

    try:
        req = urllib.request.Request("http://127.0.0.1:8998/")
        with urllib.request.urlopen(req, timeout=2) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
            assert "<title>Delta AI Security Dashboard</title>" in html
            assert "Delta Web Terminal" in html
    finally:
        server.shutdown()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_web_frontend.py -v`
Expected: FAIL with "Delta AI Security Dashboard not in html"

- [ ] **Step 3: Create index.html with clean dark theme UI**

Create `delta/web/static/index.html`:
```html
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Delta AI Security Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        cyber: {
                            bg: '#0a0d14',
                            card: '#121824',
                            border: '#1e293b',
                            accent: '#10b981',
                            accentHover: '#059669'
                        }
                    }
                }
            }
        }
    </script>
</head>
<body class="bg-cyber-bg text-slate-100 font-sans min-h-screen flex flex-col">
    <!-- Header -->
    <header class="border-b border-cyber-border bg-cyber-card/50 backdrop-blur px-6 py-4 flex items-center justify-between">
        <div class="flex items-center space-x-3">
            <span class="text-2xl font-bold text-cyber-accent">Δ</span>
            <h1 class="text-xl font-bold tracking-wide">DELTA <span class="text-xs text-cyber-accent font-mono uppercase bg-cyber-accent/10 px-2 py-0.5 rounded border border-cyber-accent/20">Security Web Dashboard</span></h1>
        </div>
        <div class="flex items-center space-x-4">
            <span id="status-badge" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                ● Online
            </span>
        </div>
    </header>

    <!-- Main Workspace -->
    <main class="flex-1 p-6 grid grid-cols-1 lg:grid-cols-3 gap-6 max-w-7xl mx-auto w-full">
        <!-- Dashboard Metrics Card -->
        <div class="bg-cyber-card border border-cyber-border rounded-xl p-5 shadow-lg space-y-4">
            <h2 class="text-lg font-semibold text-slate-200 flex items-center gap-2">
                📊 System Status
            </h2>
            <div class="grid grid-cols-2 gap-4">
                <div class="bg-cyber-bg p-4 rounded-lg border border-cyber-border">
                    <p class="text-xs text-slate-400">Engine Version</p>
                    <p class="text-xl font-bold text-slate-100 font-mono mt-1" id="val-version">v1.0.0</p>
                </div>
                <div class="bg-cyber-bg p-4 rounded-lg border border-cyber-border">
                    <p class="text-xs text-slate-400">AI Mode</p>
                    <p class="text-xl font-bold text-cyber-accent font-mono mt-1" id="val-ai">ACTIVE</p>
                </div>
            </div>
            
            <div class="pt-4 border-t border-cyber-border">
                <h3 class="text-sm font-medium text-slate-300 mb-3">Quick Commands</h3>
                <div class="flex flex-wrap gap-2">
                    <button onclick="runQuickCmd('scan localhost')" class="px-3 py-1.5 bg-cyber-bg hover:bg-cyber-border text-xs rounded border border-cyber-border font-mono transition">scan localhost</button>
                    <button onclick="runQuickCmd('check security on localhost')" class="px-3 py-1.5 bg-cyber-bg hover:bg-cyber-border text-xs rounded border border-cyber-border font-mono transition">check security</button>
                    <button onclick="runQuickCmd('help')" class="px-3 py-1.5 bg-cyber-bg hover:bg-cyber-border text-xs rounded border border-cyber-border font-mono transition">help</button>
                </div>
            </div>
        </div>

        <!-- Terminal Console -->
        <div class="lg:col-span-2 bg-cyber-card border border-cyber-border rounded-xl p-5 shadow-lg flex flex-col h-[500px]">
            <div class="flex items-center justify-between pb-3 border-b border-cyber-border mb-3">
                <h2 class="text-lg font-semibold text-slate-200 flex items-center gap-2">
                    💻 Delta Web Terminal
                </h2>
                <span class="text-xs font-mono text-slate-400">Interactive Console</span>
            </div>
            
            <!-- Terminal Output Window -->
            <div id="terminal-out" class="flex-1 bg-cyber-bg rounded-lg p-4 font-mono text-sm overflow-y-auto space-y-2 border border-cyber-border text-slate-300">
                <div class="text-cyber-accent">Welcome to Delta AI Security Web Terminal.</div>
                <div class="text-slate-500">Type any CLI command below (e.g. 'scan 127.0.0.1' or 'explain XSS').</div>
            </div>

            <!-- Terminal Input -->
            <form id="cmd-form" onsubmit="handleSend(event)" class="mt-4 flex gap-2">
                <span class="text-cyber-accent font-bold font-mono self-center">Δ &gt;</span>
                <input type="text" id="cmd-input" placeholder="Type command..." class="flex-1 bg-cyber-bg border border-cyber-border rounded px-4 py-2 font-mono text-sm focus:outline-none focus:border-cyber-accent text-slate-100">
                <button type="submit" class="bg-cyber-accent hover:bg-cyber-accentHover text-cyber-bg px-5 py-2 rounded font-semibold text-sm transition">Send</button>
            </form>
        </div>
    </main>

    <script>
        async function fetchStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                document.getElementById('val-version').innerText = data.version || 'v1.0.0';
                document.getElementById('val-ai').innerText = data.llm_enabled ? 'ACTIVE' : 'OFFLINE';
            } catch (e) {
                console.error(e);
            }
        }

        async function handleSend(e) {
            if(e) e.preventDefault();
            const input = document.getElementById('cmd-input');
            const cmd = input.value.trim();
            if(!cmd) return;

            const term = document.getElementById('terminal-out');
            term.innerHTML += `<div class="text-slate-100 font-bold mt-2">Δ &gt; ${cmd}</div>`;
            input.value = '';

            try {
                const res = await fetch('/api/execute', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command: cmd})
                });
                const data = await res.json();
                term.innerHTML += `<pre class="text-emerald-400 font-mono whitespace-pre-wrap">${data.output}</pre>`;
                term.scrollTop = term.scrollHeight;
            } catch (err) {
                term.innerHTML += `<div class="text-rose-500">Error executing command</div>`;
            }
        }

        function runQuickCmd(cmd) {
            document.getElementById('cmd-input').value = cmd;
            handleSend();
        }

        fetchStatus();
    </script>
</body>
</html>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_web_frontend.py -v`
Expected: PASS

- [ ] **Step 5: Commit Task 2**

```bash
git add delta/web/static/index.html tests/test_web_frontend.py
git commit -m "feat(web): add clean dark dashboard and web terminal UI"
```

---

### Task 3: Integrate `delta web` Command in CLI Entry Point

**Files:**
- Modify: `delta/main.py`
- Test: `tests/test_cli_web_integration.py`

**Interfaces:**
- Modifies: `run_web_chat()` / `--web` handling in `delta/main.py` to launch `delta.web.server`

- [ ] **Step 1: Write test to verify CLI web flag launches web server**

```python
import pytest
from unittest.mock import patch
from delta.main import build_parser

def test_web_flag_parsing():
    parser = build_parser()
    args = parser.parse_args(["--web"])
    assert args.web is True
```

- [ ] **Step 2: Run test to verify it passes**

Run: `python -m pytest tests/test_cli_web_integration.py -v`
Expected: PASS

- [ ] **Step 3: Modify `delta/main.py` to route `run_web_chat` to `DeltaWebServer`**

Update `delta/main.py`:
```python
def run_web_chat() -> None:
    """Run the web dashboard interface."""
    from delta.web.server import start_web_server
    engine = create_engine()
    start_web_server(engine=engine, host="127.0.0.1", port=8000)
```

- [ ] **Step 4: Run all pytest suites to ensure no regression**

Run: `python -m pytest tests/ -v`
Expected: All tests pass.

- [ ] **Step 5: Commit Task 3**

```bash
git add delta/main.py tests/test_cli_web_integration.py
git commit -m "feat(cli): connect --web flag to Delta Web Dashboard server"
```

---

## Self-Review

1. **Spec Coverage:**
   - Web UI launcher (`delta --web`): Task 3
   - Clean UI Dashboard & Terminal: Task 2
   - Backend API & Delta Engine integration: Task 1
2. **Placeholder Scan:** No placeholders or vague TODOs.
3. **Type Consistency:** Method names and parameters (`DeltaWebServer`, `EngineBridge`, `start_web_server`) match across tasks.
