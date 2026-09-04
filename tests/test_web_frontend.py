import pytest
import urllib.request
import threading
import time
from pathlib import Path
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
            assert "<title>DELTA" in html or "<title>Delta" in html
            assert "Delta" in html or "DELTA" in html
    finally:
        server.shutdown()

def test_exploit_studio_ui_elements_in_static_html():
    static_html = Path("delta/web/static/index.html").read_text(encoding="utf-8")
    
    # Delta Web Core layout & controls
    assert "DELTA" in static_html
    assert 'id="view-execution"' in static_html
    assert 'id="view-camera"' in static_html or 'id="view-recon"' in static_html
    assert 'id="user-input"' in static_html or 'id="chat-form"' in static_html

def test_exploit_studio_ui_elements_in_root_html():
    root_html = Path("delta/web/index.html").read_text(encoding="utf-8")
    
    # Delta Web Core layout & controls
    assert "DELTA" in root_html
    assert 'id="view-execution"' in root_html
    assert 'id="view-recon"' in root_html
    assert 'id="user-input"' in root_html or 'id="chat-form"' in root_html

def test_exploit_studio_js_functions():
    static_html = Path("delta/web/static/index.html").read_text(encoding="utf-8")
    root_html = Path("delta/web/index.html").read_text(encoding="utf-8")
    
    for html in (static_html, root_html):
        assert "navigate" in html
        assert "handleSubmit" in html or "handleKeyDown" in html
        assert "switchModel" in html or "loadModelsData" in html or "loadHistoryData" in html
