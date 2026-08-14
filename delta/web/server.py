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
            index_path = os.path.join(os.path.dirname(__file__), "index.html")
            if not os.path.exists(index_path):
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
        DeltaRequestHandler.bridge = self.bridge
        super().__init__((host, port), DeltaRequestHandler)

def start_web_server(engine: Optional[Any] = None, host: str = "127.0.0.1", port: int = 8000):
    server = DeltaWebServer(engine, host, port)
    print(f"[*] Delta Web UI server running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
