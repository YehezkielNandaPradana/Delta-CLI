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
            assert "Delta AI" in html
    finally:
        server.shutdown()
