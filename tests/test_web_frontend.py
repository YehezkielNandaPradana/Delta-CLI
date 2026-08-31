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
            assert "<title>Delta Workstation</title>" in html or "<title>Delta" in html
            assert "Delta" in html
    finally:
        server.shutdown()

def test_exploit_studio_ui_elements_in_static_html():
    static_html = Path("delta/web/static/index.html").read_text(encoding="utf-8")
    
    # Governance & Safety Bar elements
    assert "Exploit & Vulnerability Validation Studio" in static_html
    assert "STANDARDS: PTES / OWASP / NIST 800-115" in static_html
    assert 'id="exploit-roe-mode-check"' in static_html or 'id="exploit-roe-mode-exploit"' in static_html or 'id="exploit-roe-toggle"' in static_html or 'id="exploit-roe-mode"' in static_html
    assert 'id="exploit-scope-status"' in static_html
    assert 'id="exploit-auth-checkbox"' in static_html

    # 3-Pane Industrial Workspace Layout
    # Left pane: Catalog & Search
    assert 'id="exploit-search-input"' in static_html
    assert 'id="exploit-modules-list"' in static_html
    assert "filterExploitCategory" in static_html
    
    # Center pane: Config & Payload Builder
    assert 'id="exploit-target-input"' in static_html
    assert 'id="exploit-port-input"' in static_html
    assert 'id="exploit-ssl-toggle"' in static_html
    assert 'id="exploit-uri-input"' in static_html
    assert 'id="exploit-active-module-banner"' in static_html
    assert 'id="exploit-payload-select"' in static_html
    assert 'id="exploit-lhost-input"' in static_html
    assert 'id="exploit-lport-input"' in static_html
    assert 'id="btn-run-check"' in static_html
    assert 'id="btn-run-exploit"' in static_html
    assert 'id="btn-generate-poc"' in static_html

    # Right pane: Tabs & Telemetry / Sessions / PoC
    assert 'id="tab-btn-telemetry"' in static_html
    assert 'id="tab-btn-sessions"' in static_html
    assert 'id="tab-btn-poc"' in static_html
    assert 'id="exploit-telemetry-container"' in static_html
    assert 'id="exploit-sessions-container"' in static_html
    assert 'id="exploit-poc-container"' in static_html

def test_web_static_html_served_theme():
    server = DeltaWebServer(engine=None, host="127.0.0.1", port=8996)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)

    try:
        req = urllib.request.Request("http://127.0.0.1:8996/")
        with urllib.request.urlopen(req, timeout=2) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
            assert "dark" in html
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

def test_exploit_studio_ui_elements_in_root_html():
    root_html = Path("delta/web/index.html").read_text(encoding="utf-8")
    
    # Governance & Safety Bar elements
    assert "Exploit & Vulnerability Validation Studio" in root_html
    assert "STANDARDS: PTES / OWASP / NIST 800-115" in root_html
    assert 'id="exploit-scope-status"' in root_html
    assert 'id="exploit-auth-checkbox"' in root_html

    # 3-Pane Industrial Workspace Layout
    assert 'id="exploit-search-input"' in root_html
    assert 'id="exploit-modules-list"' in root_html
    assert 'id="exploit-target-input"' in root_html
    assert 'id="exploit-port-input"' in root_html
    assert 'id="exploit-ssl-toggle"' in root_html
    assert 'id="exploit-uri-input"' in root_html
    assert 'id="exploit-active-module-banner"' in root_html
    assert 'id="exploit-payload-select"' in root_html
    assert 'id="exploit-lhost-input"' in root_html
    assert 'id="exploit-lport-input"' in root_html
    assert 'id="btn-run-check"' in root_html
    assert 'id="btn-run-exploit"' in root_html
    assert 'id="btn-generate-poc"' in root_html

    assert 'id="tab-btn-telemetry"' in root_html
    assert 'id="tab-btn-sessions"' in root_html
    assert 'id="tab-btn-poc"' in root_html
    assert 'id="exploit-telemetry-container"' in root_html
    assert 'id="exploit-sessions-container"' in root_html
    assert 'id="exploit-poc-container"' in root_html

def test_exploit_studio_js_functions():
    static_html = Path("delta/web/static/index.html").read_text(encoding="utf-8")
    root_html = Path("delta/web/index.html").read_text(encoding="utf-8")
    
    for html in (static_html, root_html):
        assert "loadExploitModules" in html
        assert "selectExploitModule" in html
        assert "filterExploitCategory" in html
        assert "runExploitExecution" in html
        assert "loadExploitSessions" in html
        assert "killExploitSession" in html
        assert "generateExploitPoC" in html
        assert "switchExploitTab" in html
