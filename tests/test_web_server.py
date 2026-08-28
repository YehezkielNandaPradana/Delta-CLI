import urllib.request
import urllib.error
import json
import threading
import time
from delta.web.server import ThreadingDeltaWebServer as DeltaWebServer
from delta.web.bridge import clean_terminal_output, EngineBridge

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

def test_clean_terminal_output_sanitization():
    raw_cli_output = "\x1b[95m  Δ AI\x1b[0m \x1b[90m→ \x1b[1mTuan\x1b[0m\n  \x1b[2m▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔\x1b[0m\nSistem aktif, Tuan. Kirim perintah."
    cleaned = clean_terminal_output(raw_cli_output)
    assert cleaned == "Sistem aktif, Tuan. Kirim perintah."
    assert "\x1b" not in cleaned
    assert "Δ AI" not in cleaned
    assert "▔" not in cleaned

def test_engine_bridge_web_mode():
    class DummyEngine:
        def __init__(self):
            self.web_mode = False
            self.tui_mode = False
        def _process_input(self, cmd):
            if self.web_mode:
                return {"response": f"Clean response: {cmd}", "command": "", "error": "", "is_task": False, "task_id": None}
            return "CLI response"

    engine = DummyEngine()
    bridge = EngineBridge(engine)
    assert engine.web_mode is True
    res = bridge.execute_command("test")
    assert res["output"] == "Clean response: test"

def test_agent_event_execution_id():
    from delta.ai.events import AgentEvent, EventType
    event = AgentEvent(type=EventType.TOOL_START, tool="read_file", execution_id="exec_123")
    data = event.to_dict()
    assert data["type"] == "tool_start"
    assert data["tool"] == "read_file"
    assert data["execution_id"] == "exec_123"

def test_fs_tree_endpoint():
    server = DeltaWebServer(engine=None, host="127.0.0.1", port=8994)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)

    try:
        req = urllib.request.Request("http://127.0.0.1:8994/api/fs/tree")
        with urllib.request.urlopen(req, timeout=2) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "ok"
            assert "tree" in data
            assert isinstance(data["tree"], list)
            assert data["total_files"] >= 0
    finally:
        server.shutdown()

def test_fs_read_endpoint():
    server = DeltaWebServer(engine=None, host="127.0.0.1", port=8993)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)

    try:
        req = urllib.request.Request("http://127.0.0.1:8993/api/fs/read?path=setup.py")
        with urllib.request.urlopen(req, timeout=2) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "ok"
            assert data["filename"] == "setup.py"
            assert "content" in data
            assert data["line_count"] > 0
    finally:
        server.shutdown()

def test_fs_read_security_traversal_prevention():
    server = DeltaWebServer(engine=None, host="127.0.0.1", port=8992)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)

    try:
        req = urllib.request.Request("http://127.0.0.1:8992/api/fs/read?path=../../windows/system32/cmd.exe")
        try:
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                assert data["status"] == "error"
        except urllib.error.HTTPError as err:
            assert err.code in (400, 403, 404)
    finally:
        server.shutdown()


