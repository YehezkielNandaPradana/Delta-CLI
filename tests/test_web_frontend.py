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
            assert "dark:bg-slate-950" in html
            assert "dark:bg-slate-900" in html
            assert "dark:border-slate-800" in html
            assert "dark:text-slate-100" in html
    finally:
        server.shutdown()

def test_workflow_cyber_glass_css_classes():
    from pathlib import Path
    static_html = Path("delta/web/static/index.html").read_text(encoding="utf-8")
    assert "animate-radar-pulse" in static_html
    assert "connector-line" in static_html
    assert "cyber-glass" in static_html

def test_workflow_turn_container_structure():
    from pathlib import Path
    static_html = Path("delta/web/static/index.html").read_text(encoding="utf-8")
    assert "DELTA AGENT PIPELINE" in static_html
    assert "timeline-progress-" in static_html
    assert "timeline-steps-" in static_html

def test_workflow_step_drawer_functions():
    from pathlib import Path
    static_html = Path("delta/web/static/index.html").read_text(encoding="utf-8")
    assert "toggleStepDrawer" in static_html
    assert "drawer-" in static_html

def test_workflow_finalize_success_logic():
    from pathlib import Path
    static_html = Path("delta/web/static/index.html").read_text(encoding="utf-8")
    assert "finalizeTimelineSuccess" in static_html
    assert "COMPLETED" in static_html
    assert "bg-emerald-500" in static_html

def test_files_explorer_frontend_script():
    from pathlib import Path
    static_html = Path("delta/web/static/index.html").read_text(encoding="utf-8")
    assert "renderFilesExplorer" in static_html
    assert "toggleFolderNode" in static_html
    assert "filterFileTree" in static_html

def test_file_code_viewer_modal_functions():
    from pathlib import Path
    static_html = Path("delta/web/static/index.html").read_text(encoding="utf-8")
    assert "openFileCodeViewer" in static_html
    assert "code-viewer-modal" in static_html
    assert "askAiAboutFile" in static_html





