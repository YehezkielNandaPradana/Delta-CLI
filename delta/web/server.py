# Refactor: server routes
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

from urllib.parse import urlparse, parse_qs

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

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With, Accept")

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def _send_json_response(self, data: Any, status_code: int = 200) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._send_cors_headers()
        self.end_headers()
        self._safe_write(body)

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

            if clean_path == "/api/voice/status":
                res = self.bridge.get_voice_status() if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path == "/api/vtuber/audio":
                # Realtime Audio stream endpoint for browser audio client
                from delta.vtuber.voice.browser_player import browser_audio_player
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("X-Accel-Buffering", "no")
                self.end_headers()

                audio_queue: queue.Queue = queue.Queue(maxsize=150)
                browser_audio_player.register_client(audio_queue)

                # Send initial audio config frame
                init_frame = {
                    "type": "audio_config",
                    "format": "mp3",
                    "sample_rate": 24000,
                    "channels": 1,
                    "timestamp": time.time(),
                }
                if not self._safe_write(f"data: {json.dumps(init_frame)}\r\n\r\n".encode("utf-8")):
                    browser_audio_player.unregister_client(audio_queue)
                    return

                try:
                    while True:
                        try:
                            msg = audio_queue.get(timeout=1.0)
                            payload = f"data: {json.dumps(msg)}\r\n\r\n".encode("utf-8")
                            if not self._safe_write(payload):
                                break
                        except Empty:
                            ping_bytes = f": ping {int(time.time())}\r\n\r\n".encode("utf-8")
                            if not self._safe_write(ping_bytes):
                                break
                finally:
                    browser_audio_player.unregister_client(audio_queue)
                return

            if clean_path == "/api/camera/status":
                res = self.bridge.get_camera_status() if self.bridge else {"is_live": False, "device": None}
                self._send_json_response(res)
                return

            if clean_path == "/api/camera/frame":
                # Return current frame (SVG or JPEG)
                import base64
                frame_raw = self.bridge.get_latest_camera_frame() if self.bridge else None
                if not frame_raw:
                    self.send_response(204)
                    self._send_cors_headers()
                    self.end_headers()
                    return

                mime_type = "image/jpeg"
                if "image/svg+xml" in frame_raw or "<svg" in frame_raw:
                    mime_type = "image/svg+xml"

                if "," in frame_raw:
                    frame_raw = frame_raw.split(",", 1)[1]

                try:
                    img_bytes = base64.b64decode(frame_raw)
                    self.send_response(200)
                    self.send_header("Content-Type", mime_type)
                    self.send_header("Content-Length", str(len(img_bytes)))
                    self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                    self._send_cors_headers()
                    self.end_headers()
                    self._safe_write(img_bytes)
                except Exception as e:
                    self._send_json_response({"error": str(e)}, 500)
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

            if clean_path == "/api/targets":
                res = self.bridge.get_targets() if self.bridge else {"status": "error", "message": "Bridge offline", "targets": []}
                body = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return

            if clean_path == "/api/history":
                query = parse_qs(parsed_url.query)
                limit = int(query.get("limit", [50])[0])
                res = self.bridge.get_history(limit=limit) if self.bridge else {"status": "error", "message": "Bridge offline", "history": []}
                body = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return

            if clean_path == "/api/models":
                res = self.bridge.get_models() if self.bridge else {"status": "error", "message": "Bridge offline", "models": []}
                body = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return

            if clean_path == "/api/tunnel":
                res = self.bridge.get_tunnel_status() if self.bridge else {"status": "error", "message": "Bridge offline"}
                body = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return

            if clean_path == "/api/tunnel/logs":
                query = parse_qs(parsed_url.query)
                limit = int(query.get("limit", [100])[0]) if query.get("limit", [""])[0].isdigit() else 100
                res = self.bridge.get_tunnel_logs(limit=limit) if self.bridge else {"status": "error", "message": "Bridge offline", "logs": []}
                body = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return

            if clean_path == "/api/router":
                res = self.bridge.get_router_status() if self.bridge else {"status": "error", "message": "Bridge offline"}
                body = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return

            if clean_path == "/api/evidence":
                res = self.bridge.get_evidence() if self.bridge else {"status": "error", "message": "Bridge offline", "evidence": []}
                body = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return

            if clean_path == "/api/reports":
                query = parse_qs(parsed_url.query)
                limit = int(query.get("limit", [20])[0])
                res = self.bridge.get_reports(limit=limit) if self.bridge else {"status": "error", "message": "Bridge offline", "reports": []}
                body = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return

            if clean_path == "/api/reports/view":
                query = parse_qs(parsed_url.query)
                report_id_str = query.get("id", [""])[0]
                if not report_id_str.isdigit():
                    res = {"status": "error", "message": "Invalid report id parameter"}
                    status_code = 400
                else:
                    res = self.bridge.get_report_content(int(report_id_str)) if self.bridge else {"status": "error", "message": "Bridge offline"}
                    status_code = 200 if res.get("status") == "ok" else 404
                body = json.dumps(res).encode("utf-8")
                self.send_response(status_code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return

            if clean_path == "/api/fs/tree":
                query = parse_qs(parsed_url.query)
                sub_path = query.get("path", [""])[0]
                res = self.bridge.get_directory_tree(sub_path) if self.bridge else {"status": "error", "message": "Bridge offline"}
                body = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return

            if clean_path == "/api/fs/read":
                query = parse_qs(parsed_url.query)
                file_path = query.get("path", [""])[0]
                res = self.bridge.read_file_content(file_path) if self.bridge else {"status": "error", "message": "Bridge offline"}
                status_code = 200 if res.get("status") == "ok" else (403 if "Access denied" in res.get("message", "") else 404)
                body = json.dumps(res).encode("utf-8")
                self.send_response(status_code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return

            if clean_path == "/api/exploit/modules":
                query = parse_qs(parsed_url.query)
                category = query.get("category", [""])[0]
                search = query.get("search", [""])[0]
                res = self.bridge.get_exploit_modules(category=category, search=search) if self.bridge else {"status": "error", "message": "Bridge offline", "modules": []}
                body = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return

            if clean_path == "/api/exploit/sessions":
                res = self.bridge.get_exploit_sessions() if self.bridge else {"status": "error", "message": "Bridge offline", "sessions": []}
                body = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return

            if clean_path == "/api/web/inspect":
                query = parse_qs(parsed_url.query)
                target = query.get("target", [""])[0]
                port = int(query.get("port", [80])[0]) if query.get("port", [""])[0].isdigit() else 80
                fast_mode = query.get("fast", ["0"])[0] in ("1", "true")
                res = self.bridge.inspect_web_target(target, port=port, fast_mode=fast_mode) if self.bridge else {"status": "error", "message": "Bridge offline"}
                body = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return

            if clean_path == "/api/web/search":
                query = parse_qs(parsed_url.query)
                q = query.get("q", [""])[0]
                search_type = query.get("type", ["search"])[0]
                res = self.bridge.search_web_intelligence(q, search_type=search_type) if self.bridge else {"status": "error", "message": "Bridge offline", "results": []}
                body = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return

            if clean_path == "/api/web/fetch":
                query = parse_qs(parsed_url.query)
                url_param = query.get("url", [""])[0]
                res = self.bridge.fetch_web_page_content(url_param) if self.bridge else {"status": "error", "message": "Bridge offline"}
                body = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return

            if clean_path == "/api/network/ping":
                query = parse_qs(parsed_url.query)
                host = query.get("host", [""])[0]
                count = int(query.get("count", [4])[0]) if query.get("count", [""])[0].isdigit() else 4
                res = self.bridge.run_network_ping(host, count=count) if self.bridge else {"status": "error", "message": "Bridge offline"}
                body = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return

            if clean_path == "/api/network/dns":
                query = parse_qs(parsed_url.query)
                domain = query.get("domain", [""])[0]
                res = self.bridge.run_network_dns(domain) if self.bridge else {"status": "error", "message": "Bridge offline"}
                body = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return

            if clean_path == "/api/network/traceroute":
                query = parse_qs(parsed_url.query)
                host = query.get("host", [""])[0]
                max_hops = int(query.get("max_hops", [15])[0]) if query.get("max_hops", [""])[0].isdigit() else 15
                res = self.bridge.run_network_traceroute(host, max_hops=max_hops) if self.bridge else {"status": "error", "message": "Bridge offline"}
                body = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return

            if clean_path == "/api/network/geoip":
                query = parse_qs(parsed_url.query)
                host = query.get("host", [""])[0]
                res = self.bridge.run_network_geoip(host) if self.bridge else {"status": "error", "message": "Bridge offline"}
                body = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return

            if clean_path == "/api/network/ssl":
                query = parse_qs(parsed_url.query)
                host = query.get("host", [""])[0]
                port = int(query.get("port", [443])[0]) if query.get("port", [""])[0].isdigit() else 443
                res = self.bridge.run_network_ssl(host, port=port) if self.bridge else {"status": "error", "message": "Bridge offline"}
                body = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return

            if clean_path == "/api/network/sweep":
                query = parse_qs(parsed_url.query)
                network = query.get("network", [""])[0]
                res = self.bridge.run_network_sweep(network) if self.bridge else {"status": "error", "message": "Bridge offline"}
                body = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return

            if clean_path == "/api/geotrace/audit":
                query = parse_qs(parsed_url.query)
                limit = int(query.get("limit", [50])[0]) if query.get("limit", [""])[0].isdigit() else 50
                res = self.bridge.geotrace_get_audit(limit=limit) if self.bridge else {"status": "error", "message": "Bridge offline", "logs": []}
                body = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return

            if clean_path == "/api/geotrace/verify-audit":
                res = self.bridge.geotrace_verify_audit() if self.bridge else {"status": "error", "message": "Bridge offline", "valid": False}
                body = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._safe_write(body)
                return

            if clean_path in ("/voice", "/voice.html"):
                search_paths = [
                    os.path.join(self.static_dir, "voice.html"),
                    os.path.join(os.path.dirname(__file__), "static", "voice.html"),
                    os.path.join(os.path.dirname(__file__), "voice.html"),
                ]
                for vp in search_paths:
                    if os.path.exists(vp):
                        with open(vp, "rb") as f:
                            content = f.read()
                        self.send_response(200)
                        self.send_header("Content-Type", "text/html; charset=utf-8")
                        self.send_header("Content-Length", str(len(content)))
                        self.end_headers()
                        self._safe_write(content)
                        return

            if clean_path in ("/", "/index.html"):
                index_path = os.path.join(self.static_dir, "index.html")
                if not os.path.exists(index_path):
                    index_path = os.path.join(os.path.dirname(__file__), "index.html")
                if os.path.exists(index_path):
                    with open(index_path, "rb") as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(content)))
                    self.end_headers()
                    self._safe_write(content)
                    return

            if clean_path in ("/LogoDelta.png", "/static/LogoDelta.png"):
                logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "LogoDelta.png")
                if not os.path.exists(logo_path):
                    logo_path = os.path.join(self.static_dir, "LogoDelta.png")
                if os.path.exists(logo_path):
                    with open(logo_path, "rb") as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "image/png")
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

            if clean_path == "/api/camera/stream":
                content_length = int(self.headers.get("Content-Length", 0))
                body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                frame_b64 = data.get("frame", "")
                device = data.get("device", "iPhone")
                res = self.bridge.update_camera_frame(frame_b64, device=device) if self.bridge else {"status": "error"}
                self._send_json_response(res)
                return

            if clean_path == "/api/tunnel/start":
                content_length = int(self.headers.get("Content-Length", 0))
                body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                port = int(data.get("port", 8080))
                res = self.bridge.start_tunnel(port=port) if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path == "/api/tunnel/stop":
                res = self.bridge.stop_tunnel() if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path == "/api/cancel":
                res = self.bridge.cancel_execution() if self.bridge else {"status": "error", "message": "Bridge unavailable"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path == "/api/plan/generate":
                content_length = int(self.headers.get("Content-Length", 0))
                body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                res = self.bridge.generate_project_plan(data) if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path in ("/api/execute", "/api/chat"):
                content_length = int(self.headers.get("Content-Length", 0))
                body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
                body = body_bytes.decode("utf-8") if body_bytes else "{}"
                data = json.loads(body) if body else {}
                cmd = data.get("command", "") or data.get("prompt", "") or data.get("message", "")
                execution_id = data.get("execution_id")

                res = self.bridge.execute_command(cmd, execution_id=execution_id) if self.bridge else {"output": f"Engine offline: {cmd}", "is_task": False, "task_id": None}
                self._send_json_response(res)
                return

            if clean_path == "/api/voice/process":
                content_length = int(self.headers.get("Content-Length", 0))
                body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                text = data.get("text", "")
                res = self.bridge.process_voice_transcript(text) if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path == "/api/vtuber/personality":
                res = self.bridge.get_vtuber_personality_data() if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path == "/api/vtuber/personality/clear-memory":
                res = self.bridge.clear_vtuber_memories() if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path == "/api/vtuber/runtime":
                res = self.bridge.get_vtuber_runtime_data() if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path in ("/api/vtuber/vts/status", "/api/vts/status"):
                res = self.bridge.get_vts_status() if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path in ("/api/vtuber/vts/visual/status", "/api/vts/visual/status"):
                res = self.bridge.get_vts_visual_status() if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path in ("/api/vtuber/vts/test-parameter", "/api/vts/test-parameter"):
                import asyncio
                content_length = int(self.headers.get("Content-Length", 0))
                body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                param = str(data.get("parameter", ""))
                val = float(data.get("value", 0.0))
                res = asyncio.run(self.bridge.vts_test_parameter(param, val)) if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path in ("/api/vtuber/vts/test-expression", "/api/vts/test-expression"):
                import asyncio
                content_length = int(self.headers.get("Content-Length", 0))
                body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                expr = str(data.get("expression", ""))
                intensity = float(data.get("intensity", 0.8))
                res = asyncio.run(self.bridge.vts_test_expression(expr, intensity=intensity)) if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path in ("/api/vtuber/vts/reset", "/api/vts/reset"):
                import asyncio
                res = asyncio.run(self.bridge.vts_reset_parameters()) if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path in ("/api/vtuber/vts/test-lipsync", "/api/vts/test-lipsync"):
                import asyncio
                res = asyncio.run(self.bridge.vts_test_lipsync()) if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path in ("/api/vtuber/vts/test-physics", "/api/vts/test-physics"):
                import asyncio
                res = asyncio.run(self.bridge.vts_test_physics()) if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path in ("/api/vtuber/vts/auto-test", "/api/vts/auto-test"):
                import asyncio
                res = asyncio.run(self.bridge.vts_run_auto_test()) if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path == "/api/vtuber/settings":
                content_length = int(self.headers.get("Content-Length", 0))
                body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                res = self.bridge.update_vtuber_settings(data) if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path == "/api/desktop/context":
                import asyncio
                res = asyncio.run(self.bridge.get_desktop_context()) if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path == "/api/desktop/screenshot":
                import asyncio
                res = asyncio.run(self.bridge.capture_screen()) if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path == "/api/desktop/clipboard":
                import asyncio
                res = asyncio.run(self.bridge.read_clipboard()) if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path == "/api/targets/add":
                content_length = int(self.headers.get("Content-Length", 0))
                body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                host = data.get("host", "")
                ip = data.get("ip", "")
                notes = data.get("notes", "")
                risk = data.get("risk_level", "unknown")
                res = self.bridge.add_target(host, ip=ip, notes=notes, risk_level=risk) if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path == "/api/targets/delete":
                content_length = int(self.headers.get("Content-Length", 0))
                body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                host = data.get("host", "")
                res = self.bridge.delete_target(host) if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path == "/api/targets/active":
                content_length = int(self.headers.get("Content-Length", 0))
                body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                host = data.get("host", "")
                res = self.bridge.set_active_target(host) if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path == "/api/history/delete":
                content_length = int(self.headers.get("Content-Length", 0))
                body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                item_id = data.get("id")
                if item_id is None:
                    res = {"status": "error", "message": "Missing history id"}
                else:
                    res = self.bridge.delete_history_item(int(item_id)) if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self._send_cors_headers()
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path == "/api/history/clear":
                res = self.bridge.clear_history() if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path == "/api/router/start":
                res = self.bridge.start_router() if self.bridge else {"status": "error", "message": "Bridge offline"}
                status_code = 200 if res.get("status") == "ok" else 500
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(status_code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self._send_cors_headers()
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path == "/api/models/select":
                content_length = int(self.headers.get("Content-Length", 0))
                body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                model_name = data.get("model", "")
                res = self.bridge.select_model(model_name) if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path == "/api/reports/generate":
                content_length = int(self.headers.get("Content-Length", 0))
                body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                target = data.get("target", "")
                res = self.bridge.generate_report(target=target) if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path == "/api/exploit/execute":
                content_length = int(self.headers.get("Content-Length", 0))
                body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                target_host = data.get("target_host", "")
                target_port = int(data.get("target_port", 0))
                module_name = data.get("module_name", "")
                options = data.get("options")
                payload = data.get("payload")
                payload_options = data.get("payload_options")
                check_only = bool(data.get("check_only", True))
                roe_confirmed = bool(data.get("roe_confirmed", False))
                res = self.bridge.execute_exploit(
                    target_host=target_host,
                    target_port=target_port,
                    module_name=module_name,
                    options=options,
                    payload=payload,
                    payload_options=payload_options,
                    check_only=check_only,
                    roe_confirmed=roe_confirmed
                ) if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path == "/api/exploit/sessions/kill":
                content_length = int(self.headers.get("Content-Length", 0))
                body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                session_id = data.get("session_id", "")
                res = self.bridge.kill_exploit_session(session_id) if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path == "/api/exploit/generate-poc":
                content_length = int(self.headers.get("Content-Length", 0))
                body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                target_host = data.get("target_host", "")
                target_port = int(data.get("target_port", 0))
                module_name = data.get("module_name", "")
                options = data.get("options")
                res = self.bridge.generate_exploit_poc(
                    target_host=target_host,
                    target_port=target_port,
                    module_name=module_name,
                    options=options
                ) if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path == "/api/geotrace/analyze":
                content_length = int(self.headers.get("Content-Length", 0))
                body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                target = data.get("target", "")
                operator = data.get("operator", "delta-analyst")
                purpose = data.get("purpose", "OSINT Geolocation Investigation")
                consent_mode = bool(data.get("consent_mode", False))

                res = self.bridge.geotrace_analyze(
                    target=target,
                    operator=operator,
                    purpose=purpose,
                    consent_mode=consent_mode
                ) if self.bridge else {"status": "error", "message": "Bridge offline"}
                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self._safe_write(resp_bytes)
                return

            if clean_path == "/api/web/raw-request":
                content_length = int(self.headers.get("Content-Length", 0))
                body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                url = data.get("url", "")
                method = data.get("method", "GET").upper()
                custom_headers = data.get("headers", {})
                req_body = data.get("body", "")

                try:
                    import urllib.request
                    import urllib.error
                    import time
                    req = urllib.request.Request(url, method=method)
                    req.add_header("User-Agent", "Delta-Security-Scanner/1.0")
                    for k, v in custom_headers.items():
                        req.add_header(k, v)
                    
                    data_bytes = req_body.encode("utf-8") if req_body and method in ("POST", "PUT", "PATCH") else None
                    
                    start_t = time.time()
                    try:
                        with urllib.request.urlopen(req, data=data_bytes, timeout=12) as resp:
                            duration = round((time.time() - start_t) * 1000, 1)
                            resp_content = resp.read().decode("utf-8", errors="replace")
                            res = {
                                "status": "ok",
                                "status_code": resp.status,
                                "duration_ms": duration,
                                "headers": dict(resp.headers),
                                "body": resp_content[:15000],
                                "content_length": len(resp_content)
                            }
                    except urllib.error.HTTPError as e:
                        duration = round((time.time() - start_t) * 1000, 1)
                        resp_content = e.read().decode("utf-8", errors="replace")
                        res = {
                            "status": "ok",
                            "status_code": e.code,
                            "duration_ms": duration,
                            "headers": dict(e.headers),
                            "body": resp_content[:15000],
                            "content_length": len(resp_content)
                        }
                except Exception as exc:
                    res = {"status": "error", "message": str(exc)}

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

    def __init__(self, engine: Optional[Any] = None, host: str = "0.0.0.0", port: int = 8080):
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

def start_web_server(engine: Optional[Any] = None, host: str = "0.0.0.0", port: int = 8080, open_browser: bool = False):
    if engine is None:
        try:
            from delta.main import create_engine
            engine = create_engine()
        except Exception as e:
            print(f"[!] Warning: Could not initialize full Delta Engine: {e}")
            engine = None
    server = ThreadingDeltaWebServer(engine, host, port)
    url = f"http://localhost:{port}"
    print(f"[*] Delta Web & Mobile API server running at {url} (listening on {host}:{port})")
    if open_browser:
        from delta.web.launcher import launch_delta_browser
        launch_delta_browser(url=url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

if __name__ == "__main__":
    start_web_server()
