import pytest
import urllib.request
import json
import threading
import time
from delta.web.server import DeltaWebServer

def test_web_server_status_endpoint():
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
