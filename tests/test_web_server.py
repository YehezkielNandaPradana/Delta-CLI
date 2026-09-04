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
        def _process_input(self, cmd, execution_id=None):
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

def test_exploit_endpoints():
    server = DeltaWebServer(engine=None, host="127.0.0.1", port=8991)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)

    try:
        # GET /api/exploit/modules
        req = urllib.request.Request("http://127.0.0.1:8991/api/exploit/modules?category=exploit&search=tomcat")
        with urllib.request.urlopen(req, timeout=2) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "ok"
            assert "modules" in data
            assert isinstance(data["modules"], list)

        # GET /api/exploit/sessions
        req = urllib.request.Request("http://127.0.0.1:8991/api/exploit/sessions")
        with urllib.request.urlopen(req, timeout=2) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "ok"
            assert "sessions" in data
            assert isinstance(data["sessions"], list)

        # POST /api/exploit/execute
        payload = json.dumps({
            "target_host": "127.0.0.1",
            "target_port": 8080,
            "module_name": "exploit/multi/http/tomcat_mgr_upload",
            "options": {},
            "payload": "generic/shell_reverse_tcp",
            "payload_options": {},
            "check_only": True,
            "roe_confirmed": True
        }).encode("utf-8")
        req = urllib.request.Request("http://127.0.0.1:8991/api/exploit/execute", data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert "status" in data

        # POST /api/exploit/sessions/kill
        payload = json.dumps({"session_id": "sess_1"}).encode("utf-8")
        req = urllib.request.Request("http://127.0.0.1:8991/api/exploit/sessions/kill", data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert "status" in data

        # POST /api/exploit/generate-poc
        payload = json.dumps({
            "target_host": "127.0.0.1",
            "target_port": 8080,
            "module_name": "exploit/multi/http/tomcat_mgr_upload",
            "options": {}
        }).encode("utf-8")
        req = urllib.request.Request("http://127.0.0.1:8991/api/exploit/generate-poc", data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "ok"
            assert "poc" in data
    finally:
        server.shutdown()

def test_web_research_endpoints():
    server = DeltaWebServer(engine=None, host="127.0.0.1", port=8990)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)

    try:
        # GET /api/web/inspect
        req = urllib.request.Request("http://127.0.0.1:8990/api/web/inspect?target=127.0.0.1&port=8990&fast=1")
        with urllib.request.urlopen(req, timeout=3) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "ok"
            assert "security_grade" in data
            assert "security_headers" in data
            assert "technologies" in data

        # GET /api/web/search
        req = urllib.request.Request("http://127.0.0.1:8990/api/web/search?q=test&type=search")
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "ok"
            assert "results" in data

        # POST /api/web/raw-request
        payload = json.dumps({
            "method": "GET",
            "url": "http://127.0.0.1:8990/api/status",
            "headers": {"X-Custom-Test": "1"},
            "body": ""
        }).encode("utf-8")
        req = urllib.request.Request("http://127.0.0.1:8990/api/web/raw-request", data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "ok"
            assert data["status_code"] == 200
            assert "duration_ms" in data
    finally:
        server.shutdown()

def test_network_diagnostics_endpoints():
    server = DeltaWebServer(engine=None, host="127.0.0.1", port=8989)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)

    try:
        # GET /api/network/ping
        req = urllib.request.Request("http://127.0.0.1:8989/api/network/ping?host=127.0.0.1&count=1")
        with urllib.request.urlopen(req, timeout=3) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "ok"
            assert "alive" in data
            assert "rtt_ms" in data

        # GET /api/network/dns
        req = urllib.request.Request("http://127.0.0.1:8989/api/network/dns?domain=localhost")
        with urllib.request.urlopen(req, timeout=3) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "ok"
            assert "a_records" in data
            assert "mx_records" in data

        # GET /api/network/geoip
        req = urllib.request.Request("http://127.0.0.1:8989/api/network/geoip?host=1.1.1.1")
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert "status" in data

        # GET /api/network/ssl
        req = urllib.request.Request("http://127.0.0.1:8989/api/network/ssl?host=google.com&port=443")
        with urllib.request.urlopen(req, timeout=6) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "ok"
            assert "valid" in data
    finally:
        server.shutdown()


def test_camera_status_and_frame_endpoints():
    server = DeltaWebServer(engine=None, host="127.0.0.1", port=8988)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)

    try:
        # GET /api/camera/status
        req = urllib.request.Request("http://127.0.0.1:8988/api/camera/status")
        with urllib.request.urlopen(req, timeout=3) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["is_live"] is True
            assert data["has_frame"] is True
            assert "device" in data

        # GET /api/camera/frame
        req_frame = urllib.request.Request("http://127.0.0.1:8988/api/camera/frame")
        with urllib.request.urlopen(req_frame, timeout=3) as resp:
            assert resp.status == 200
            content = resp.read()
            assert len(content) > 0
            assert resp.headers.get("Content-Type") in ("image/svg+xml", "image/jpeg")
    finally:
        server.shutdown()






