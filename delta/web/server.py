"""Robust Threading HTTP Server with Per-Client SSE Streaming for Delta Web UI."""

import json
import os
import queue
import time
import socket
from queue import Empty
from socketserver import ThreadingMixIn
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Any, Optional

from delta.web.bridge import EngineBridge
from delta.ai.events import event_bus, AgentEvent

from urllib.parse import urlparse

def _is_disconnect_error(exc: BaseException) -> bool:
    """Check if exception is caused by client disconnect (Windows & Unix)."""
    if isinstance(exc, (BrokenPipeError, ConnectionResetError, ConnectionAbortedError)):
        return True
    if isinstance(exc, (socket.error, OSError)):
        win_err = getattr(exc, "winerror", None) or getattr(exc, "errno", None)
        if win_err in (10053, 10054, 10058, 32, 104):
            return True
        msg = str(exc).lower()
        if "aborted" in msg or "reset" in msg or "broken" in msg or "closed" in msg:
            return True
    return False

class DeltaRequestHandler(SimpleHTTPRequestHandler):
    bridge: Optional[EngineBridge] = None
    static_dir: str = os.path.join(os.path.dirname(__file__), "static")

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress noisy HTTP request logs for SSE heartbeats."""
        if args and isinstance(args[0], str) and "/api/events" in args[0]:
            return
        super().log_message(format, *args)

    def handle_error(self, request: Any, client_address: Any) -> None:
        """Override error handler to suppress client disconnect tracebacks."""
        import sys
        _, exc_val, _ = sys.exc_info()
        if exc_val and _is_disconnect_error(exc_val):
            return
        super().handle_error(request, client_address)

    def _safe_write(self, data: bytes) -> bool:
        """Safely write bytes to wfile and flush, returning False on client disconnect."""
        try:
            self.wfile.write(data)
            self.wfile.flush()
            return True
        except Exception as exc:
            if _is_disconnect_error(exc):
                return False
            raise

    def do_GET(self):
        try:
            parsed_url = urlparse(self.path)
            clean_path = parsed_url.path

            if clean_path == "/api/events":
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("X-Accel-Buffering", "no")
                self.end_headers()

                client_queue: queue.Queue = queue.Queue(maxsize=100)

                def on_event(ev: AgentEvent):
                    try:
                        client_queue.put_nowait(ev)
                    except queue.Full:
                        pass  # Drop event if client queue fills up to prevent memory leaks

                unsubscribe = event_bus.subscribe(on_event)

                # Send initial ping event
                ping_payload = f"data: {json.dumps({'type': 'ping', 'timestamp': time.time()})}\r\n\r\n".encode("utf-8")
                if not self._safe_write(ping_payload):
                    unsubscribe()
                    return

                # Send initial workspace_info event
                cwd = getattr(self.bridge.engine, "cwd", None) or os.getcwd() if self.bridge else os.getcwd()
                ws_payload = f"data: {json.dumps({'type': 'workspace_info', 'working_directory': cwd, 'timestamp': time.time()})}\r\n\r\n".encode("utf-8")
                if not self._safe_write(ws_payload):
                    unsubscribe()
                    return

                last_heartbeat = time.time()
                heartbeat_interval = 15.0  # 15s heartbeat interval

                try:
                    while True:
                        try:
                            ev: AgentEvent = client_queue.get(timeout=1.0)
                            payload = f"data: {json.dumps(ev.to_dict())}\r\n\r\n".encode("utf-8")
                            if not self._safe_write(payload):
                                break
                            last_heartbeat = time.time()
                        except Empty:
                            # Queue timeout is a normal idle state
                            now = time.time()
                            if now - last_heartbeat >= heartbeat_interval:
                                ping_bytes = f": ping {int(now)}\r\n\r\n".encode("utf-8")
                                if not self._safe_write(ping_bytes):
                                    break
                                last_heartbeat = now
                finally:
                    unsubscribe()
                return

            if clean_path in ("/api/status", "/api/health"):
                status_data = self.bridge.get_status() if self.bridge else {"status": "online", "version": "1.0.0"}
                body = json.dumps(status_data).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return

            if clean_path in ("/", "/index.html"):
                index_path = os.path.join(os.path.dirname(__file__), "index.html")
                if not os.path.exists(index_path):
                    index_path = os.path.join(self.static_dir, "index.html")
                if os.path.exists(index_path):
                    with open(index_path, "rb") as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(content)))
                    self.end_headers()
                    self._safe_write(content)
                    return

            self.send_error(404, "Not Found")
        except Exception as exc:
            if _is_disconnect_error(exc):
                return
            raise

    def do_POST(self):
        try:
            parsed_url = urlparse(self.path)
            clean_path = parsed_url.path

            if clean_path == "/api/execute":
                content_length = int(self.headers.get("Content-Length", 0))
                body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
                body = body_bytes.decode("utf-8") if body_bytes else "{}"
                data = json.loads(body) if body else {}
                cmd = data.get("command", "")

                res = self.bridge.execute_command(cmd) if self.bridge else {"output": f"Engine offline: {cmd}", "is_task": False, "task_id": None}
                resp_bytes = json.dumps(res).encode("utf-8")

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            self.send_error(404, "Not Found")
        except Exception as exc:
            if _is_disconnect_error(exc):
                return
            raise

class ThreadingDeltaWebServer(ThreadingMixIn, HTTPServer):
    """Multi-threaded HTTP server allowing concurrent long-lived SSE streams & REST requests."""
    daemon_threads = True

    def __init__(self, engine: Optional[Any] = None, host: str = "127.0.0.1", port: int = 8000):
        self.bridge = EngineBridge(engine)
        DeltaRequestHandler.bridge = self.bridge
        super().__init__((host, port), DeltaRequestHandler)

    def handle_error(self, request: Any, client_address: Any) -> None:
        """Suppress socket disconnect stack traces in thread execution."""
        import sys
        _, exc_val, _ = sys.exc_info()
        if exc_val and _is_disconnect_error(exc_val):
            return
        super().handle_error(request, client_address)

DeltaWebServer = ThreadingDeltaWebServer

def start_web_server(engine: Optional[Any] = None, host: str = "127.0.0.1", port: int = 8000):
    server = ThreadingDeltaWebServer(engine, host, port)
    print(f"[*] Delta Web UI server running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
