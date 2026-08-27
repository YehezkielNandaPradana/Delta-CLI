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
            assert "<title>Delta IDE Workspace</title>" in html or "<title>Delta" in html
            assert "Delta" in html
    finally:
        server.shutdown()

def test_web_static_html_has_theme_script():
    server = DeltaWebServer(engine=None, host="127.0.0.1", port=8997)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)

    try:
        req = urllib.request.Request("http://127.0.0.1:8997/")
        with urllib.request.urlopen(req, timeout=2) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
            assert "darkMode: 'class'" in html
            assert "delta-theme" in html
            assert "applyTheme" in html
    finally:
        server.shutdown()

def test_web_static_html_has_theme_toggle_button():
    server = DeltaWebServer(engine=None, host="127.0.0.1", port=8996)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)

    try:
        req = urllib.request.Request("http://127.0.0.1:8996/")
        with urllib.request.urlopen(req, timeout=2) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
            assert 'id="theme-toggle-btn"' in html
            assert "setTheme(" in html
    finally:
        server.shutdown()

def test_web_static_html_has_dark_mode_classes():
    server = DeltaWebServer(engine=None, host="127.0.0.1", port=8995)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)

    try:
        req = urllib.request.Request("http://127.0.0.1:8995/")
        with urllib.request.urlopen(req, timeout=2) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
            assert "dark" in html or "darkMode" in html
    finally:
        server.shutdown()



