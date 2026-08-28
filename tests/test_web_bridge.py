from delta.core.events import AsyncEventBus, LogEvent
from delta.web.bridge import WebBridge
from delta.ai.events import AgentEvent, EventType, StepKind, StepStatus, AgentStep
import time

def test_web_bridge_handle_event():
    bus = AsyncEventBus()
    bridge = WebBridge(bus)

    event = LogEvent(level="INFO", message="Web bridge event test")
    bridge.handle_event(event)

    assert len(bridge.event_queue) == 1
    assert bridge.event_queue[0]["type"] == "LogEvent"
    assert bridge.event_queue[0]["data"]["message"] == "Web bridge event test"

def test_web_bridge_handles_agent_step_events():
    bus = AsyncEventBus()
    bridge = WebBridge(bus)

    step = AgentStep(
        id="step_test_1",
        task_id="task_1",
        execution_id="exec_1",
        parent_id=None,
        kind=StepKind.ROOT,
        label="Root Step",
        status=StepStatus.RUNNING,
        created_at=time.time(),
        started_at=time.time()
    )

    ev = AgentEvent(
        type=EventType.AGENT_STEP_STARTED,
        execution_id="exec_1",
        task_id="task_1",
        step_id="step_test_1",
        payload={"step": step.to_dict()}
    )

    bridge.event_queue.append(ev.to_dict())
    assert len(bridge.event_queue) == 1
    assert bridge.event_queue[0]["type"] == "agent_step_started"
    assert bridge.event_queue[0]["payload"]["step"]["kind"] == "root"
    assert bridge.event_queue[0]["payload"]["step"]["status"] == "running"


def test_engine_bridge_get_exploit_modules_fallback():
    from delta.web.bridge import EngineBridge
    bridge = EngineBridge()
    res = bridge.get_exploit_modules()
    assert res["status"] == "ok"
    assert "modules" in res
    assert len(res["modules"]) > 0
    mod = res["modules"][0]
    assert "name" in mod
    assert "title" in mod
    assert "category" in mod
    assert "cvss_score" in mod
    assert "cve_list" in mod
    assert "safety_category" in mod


def test_engine_bridge_get_exploit_modules_filtered():
    from delta.web.bridge import EngineBridge
    bridge = EngineBridge()
    res = bridge.get_exploit_modules(category="web", search="tomcat")
    assert res["status"] == "ok"
    assert len(res["modules"]) >= 1
    assert any("tomcat" in m["name"].lower() for m in res["modules"])


def test_engine_bridge_execute_exploit_roe_enforcement():
    from delta.web.bridge import EngineBridge
    bridge = EngineBridge()
    # Without roe_confirmed
    res = bridge.execute_exploit("127.0.0.1", 8080, "exploit/multi/http/tomcat_mgr_upload", roe_confirmed=False)
    assert res["status"] == "error"
    assert "Rules of Engagement and legal authorization must be explicitly confirmed" in res["message"]


def test_engine_bridge_execute_exploit_with_engine():
    from unittest.mock import MagicMock
    from delta.web.bridge import EngineBridge
    from delta.pentest.metasploit import MetasploitExecutionResult, MetasploitExecutionConfig

    mock_engine = MagicMock()
    mock_msf = MagicMock()
    mock_res = MetasploitExecutionResult(
        execution_id="EXEC-123",
        config=MetasploitExecutionConfig(
            module_name="exploit/multi/http/tomcat_mgr_upload",
            module_type="exploit",
            target_host="127.0.0.1",
            target_port=8080
        ),
        status="success",
        output="Target validated successfully",
        session_id="MSF-SESS-001",
        vulnerability_confirmed=True,
        evidence_data={"finding": "vuln"},
        execution_time_ms=45.2
    )
    mock_msf.execute_controlled_validation.return_value = mock_res
    mock_engine.pentest.metasploit = mock_msf

    bridge = EngineBridge(engine=mock_engine)
    res = bridge.execute_exploit("127.0.0.1", 8080, "exploit/multi/http/tomcat_mgr_upload", check_only=True, roe_confirmed=True)
    assert res["status"] == "success"
    assert res["execution_id"] == "EXEC-123"
    assert res["vulnerability_confirmed"] is True
    assert res["session_id"] == "MSF-SESS-001"
    assert res["execution_time_ms"] == 45.2
    assert res["evidence"] == {"finding": "vuln"}


def test_engine_bridge_sessions_management():
    from unittest.mock import MagicMock
    from delta.web.bridge import EngineBridge
    from delta.pentest.metasploit import MetasploitSessionRecord, SessionStatus

    mock_engine = MagicMock()
    mock_msf = MagicMock()
    mock_record = MetasploitSessionRecord(
        session_id="SESS-1",
        target_host="192.168.1.10",
        target_port=8080,
        module_used="exploit/multi/http/tomcat_mgr_upload",
        created_at=1000.0,
        expires_at=2000.0,
        status=SessionStatus.ACTIVE,
        session_type="shell"
    )
    mock_msf.session_manager.sessions = {"SESS-1": mock_record}
    mock_engine.pentest.metasploit = mock_msf

    bridge = EngineBridge(engine=mock_engine)
    res = bridge.get_exploit_sessions()
    assert res["status"] == "ok"
    assert len(res["sessions"]) == 1
    s = res["sessions"][0]
    assert s["session_id"] == "SESS-1"
    assert s["target_host"] == "192.168.1.10"
    assert s["target_port"] == 8080
    assert s["module_used"] == "exploit/multi/http/tomcat_mgr_upload"
    assert s["status"] == "ACTIVE"

    # Kill session
    kill_res = bridge.kill_exploit_session("SESS-1")
    assert kill_res["status"] == "ok"
    assert "SESS-1 terminated" in kill_res["message"]
    mock_msf.session_manager.cleanup_session.assert_called_once_with("SESS-1", mock_msf.backend)


def test_engine_bridge_generate_exploit_poc():
    from unittest.mock import MagicMock
    from delta.web.bridge import EngineBridge

    mock_engine = MagicMock()
    mock_msf = MagicMock()
    mock_msf.generate_poc_script.return_value = {
        "curl": "curl http://127.0.0.1:8080",
        "python": "import requests",
        "raw_http": "GET / HTTP/1.1"
    }
    mock_engine.pentest.metasploit = mock_msf

    bridge = EngineBridge(engine=mock_engine)
    res = bridge.generate_exploit_poc("127.0.0.1", 8080, "exploit/multi/http/tomcat_mgr_upload", options={"HttpUsername": "root"})
    assert res["status"] == "ok"
    assert "poc" in res
    assert res["poc"]["curl"] == "curl http://127.0.0.1:8080"


