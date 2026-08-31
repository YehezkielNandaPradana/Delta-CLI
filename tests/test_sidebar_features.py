"""Integration tests for Delta Web UI Sidebar & API Endpoints."""

import os
import json
import time
import socket
import threading
import urllib.request
from delta.core.config import DeltaConfig
from delta.core.database import Database
from delta.core.session import SessionManager
from delta.core.display import DisplayManager
from delta.core.plugin import PluginManager
from delta.ai.intent import IntentEngine
from delta.ai.llm import LLMEngine
from delta.core.engine import DeltaEngine
from delta.web.server import ThreadingDeltaWebServer

def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

def _create_test_engine(tmp_path: str) -> DeltaEngine:
    config = DeltaConfig()
    config.data_dir = tmp_path
    config.config_dir = tmp_path
    config.plugin_dir = tmp_path
    config.llm_enabled = True

    db_path = os.path.join(tmp_path, "delta_test.db")
    database = Database(db_path=db_path)
    database.initialize()
    session = SessionManager(database=database)
    intent_engine = IntentEngine(config=config, database=database)
    display = DisplayManager()
    plugin_manager = PluginManager(plugin_dir=tmp_path)
    llm_engine = LLMEngine(api_key="test_key", provider="9router", model="AntigravityCombo")

    engine = DeltaEngine(
        config=config,
        database=database,
        session=session,
        intent_engine=intent_engine,
        plugin_manager=plugin_manager,
        display=display,
        llm_engine=llm_engine,
        cwd=tmp_path
    )
    engine.web_mode = True
    return engine

def test_sidebar_api_endpoints_full_lifecycle(tmp_path):
    engine = _create_test_engine(str(tmp_path))
    port = _find_free_port()
    server = ThreadingDeltaWebServer(engine=engine, host="127.0.0.1", port=port)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.3)

    base_url = f"http://127.0.0.1:{port}"

    try:
        # 1. Test Static Index.html
        with urllib.request.urlopen(f"{base_url}/") as resp:
            assert resp.status == 200
            content = resp.read().decode("utf-8")
            assert "DELTA WORKSTATION" in content
            assert "Recon" in content
            assert "Targets" in content

        # 2. Test Initial Status
        with urllib.request.urlopen(f"{base_url}/api/status") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "online"
            assert data["targets_count"] == 0
            assert "active_agents" in data

        # 3. Test Targets: Add, List, Active, Delete
        add_req = urllib.request.Request(
            f"{base_url}/api/targets/add",
            data=json.dumps({"host": "scanme.nmap.org", "ip": "45.33.32.156", "notes": "Authorized test host"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(add_req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "ok"

        # List targets
        with urllib.request.urlopen(f"{base_url}/api/targets") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "ok"
            assert len(data["targets"]) == 1
            assert data["targets"][0]["host"] == "scanme.nmap.org"
            assert data["active_target"] == "scanme.nmap.org"

        # Add second target
        add_req2 = urllib.request.Request(
            f"{base_url}/api/targets/add",
            data=json.dumps({"host": "127.0.0.1", "ip": "127.0.0.1", "notes": "Localhost"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(add_req2) as resp:
            assert resp.status == 200

        # Set active target
        active_req = urllib.request.Request(
            f"{base_url}/api/targets/active",
            data=json.dumps({"host": "127.0.0.1"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(active_req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["active_target"] == "127.0.0.1"

        # Verify status counts updated
        with urllib.request.urlopen(f"{base_url}/api/status") as resp:
            assert resp.status == 200
            st_data = json.loads(resp.read().decode("utf-8"))
            assert st_data["targets_count"] == 2
            assert st_data["active_target"] == "127.0.0.1"

        # Delete target
        del_req = urllib.request.Request(
            f"{base_url}/api/targets/delete",
            data=json.dumps({"host": "scanme.nmap.org"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(del_req) as resp:
            assert resp.status == 200
            del_data = json.loads(resp.read().decode("utf-8"))
            assert del_data["status"] == "ok"

        # 4. Test Models List and Selection
        with urllib.request.urlopen(f"{base_url}/api/models") as resp:
            assert resp.status == 200
            mod_data = json.loads(resp.read().decode("utf-8"))
            assert mod_data["status"] == "ok"
            assert len(mod_data["models"]) > 0

        select_req = urllib.request.Request(
            f"{base_url}/api/models/select",
            data=json.dumps({"model": "DeepseekCombo"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(select_req) as resp:
            assert resp.status == 200
            sel_data = json.loads(resp.read().decode("utf-8"))
            assert sel_data["status"] == "ok"

        # 5. Test Router Status
        with urllib.request.urlopen(f"{base_url}/api/router") as resp:
            assert resp.status == 200
            r_data = json.loads(resp.read().decode("utf-8"))
            assert r_data["status"] == "ok"
            assert "port" in r_data

        # 6. Test Reports Generate, List, and View
        gen_req = urllib.request.Request(
            f"{base_url}/api/reports/generate",
            data=json.dumps({"target": "127.0.0.1"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(gen_req) as resp:
            assert resp.status == 200
            rep_gen = json.loads(resp.read().decode("utf-8"))
            assert rep_gen["status"] == "ok"
            report_id = rep_gen["report_id"]
            assert report_id is not None

        # List reports
        with urllib.request.urlopen(f"{base_url}/api/reports") as resp:
            assert resp.status == 200
            reps = json.loads(resp.read().decode("utf-8"))
            assert reps["status"] == "ok"
            assert len(reps["reports"]) >= 1

        # View report content
        with urllib.request.urlopen(f"{base_url}/api/reports/view?id={report_id}") as resp:
            assert resp.status == 200
            view_rep = json.loads(resp.read().decode("utf-8"))
            assert view_rep["status"] == "ok"
            assert "Security Assessment Report" in view_rep["report"]["content"]

        # 7. Test Evidence API
        with urllib.request.urlopen(f"{base_url}/api/evidence") as resp:
            assert resp.status == 200
            ev_data = json.loads(resp.read().decode("utf-8"))
            assert ev_data["status"] == "ok"
            assert isinstance(ev_data["evidence"], list)

        # 8. Test History Persistence & Clear
        engine.session.add_to_history(command="scan 127.0.0.1", status="completed", result_summary="Port 80 open")
        with urllib.request.urlopen(f"{base_url}/api/history") as resp:
            assert resp.status == 200
            hist_data = json.loads(resp.read().decode("utf-8"))
            assert hist_data["status"] == "ok"
            assert len(hist_data["history"]) >= 1
            assert hist_data["history"][0]["command"] == "scan 127.0.0.1"

        clear_req = urllib.request.Request(
            f"{base_url}/api/history/clear",
            data=b"{}",
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(clear_req) as resp:
            assert resp.status == 200
            clear_res = json.loads(resp.read().decode("utf-8"))
            assert clear_res["status"] == "ok"

        with urllib.request.urlopen(f"{base_url}/api/history") as resp:
            assert resp.status == 200
            hist_after = json.loads(resp.read().decode("utf-8"))
            assert len(hist_after["history"]) == 0

    finally:
        server.shutdown()
        server.server_close()
