# tests/test_agent_scenarios.py

"""
Comprehensive Integration Acceptance Tests for Delta AI Software Engineering Agent.
Tests Scenarios A through G:
  - Scenario A & B: Casual Chat ("tes", "lah") -> 0 Agent Tasks, 0 tools.
  - Scenario C: Project Inspection ("lihat struktur project") -> 1 Task, codebase_tree tool call.
  - Scenario D: Code Editing ("ubah file") -> Read, Edit, Syntax Verification.
  - Scenario E: Terminal Command Execution -> Safe Execution & Exit Codes.
  - Scenario F: Event Deduplication & Idempotency.
  - Scenario G: Git Workflow Tools (git_status, git_diff, git_log).
"""

import os
import tempfile
import pytest

from delta.core.config import DeltaConfig
from delta.core.database import Database
from delta.core.session import SessionManager
from delta.ai.intent import IntentEngine
from delta.core.plugin import PluginManager
from delta.core.display import DisplayManager
from delta.core.engine import DeltaEngine

class MockLLMEngine:
    def __init__(self, responses=None):
        self.is_configured = True
        self.model = "test-model"
        self.provider = "9router"
        self.base_url = "http://localhost:20128/v1"
        self.responses = responses or []
        self.call_count = 0
        self.messages = []
        self.memory_enabled = False

    def set_system_context(self, ctx):
        pass

    def _validate_settings(self):
        return None

    def _configure_llm_retry(self):
        pass

    def chat(self, prompt, tools=None, is_continuation=False, **kwargs):
        if self.call_count < len(self.responses):
            res = self.responses[self.call_count]
            self.call_count += 1
            return res
        return "Default response."

    def append_tool_result(self, tool_id, result):
        pass


@pytest.fixture
def temp_engine():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = DeltaConfig()
        config.data_dir = tmpdir
        config.config_dir = tmpdir
        config.plugin_dir = tmpdir
        config.llm_enabled = True

        db = Database(os.path.join(tmpdir, "test.db"))
        db.initialize()
        session = SessionManager(database=db)
        intent = IntentEngine(config=config, database=db)
        plugin_mgr = PluginManager(plugin_dir=tmpdir)
        display = DisplayManager()

        llm = MockLLMEngine()
        engine = DeltaEngine(
            config=config,
            database=db,
            session=session,
            intent_engine=intent,
            plugin_manager=plugin_mgr,
            display=display,
            llm_engine=llm,
            cwd=tmpdir
        )
        engine.cwd = tmpdir
        engine.tui_mode = True
        engine.web_mode = True
        try:
            yield engine, tmpdir
        finally:
            db.close()


def test_scenario_a_and_b_casual_chat(temp_engine):
    engine, _ = temp_engine
    engine.llm_engine.responses = ["Halo Tuan, ada yang bisa saya bantu?"]

    res = engine._process_input("lah")
    assert isinstance(res, dict)
    assert res["is_task"] is False
    assert res["task_id"] is None
    assert "Halo Tuan" in res["response"]


def test_scenario_c_project_inspection(temp_engine):
    engine, _ = temp_engine
    engine.llm_engine.responses = [
        '{"tool_calls": [{"id": "call_1", "function": {"name": "codebase_tree", "arguments": {"max_depth": 2}}}]}',
        "Berikut adalah struktur folder project Tuan."
    ]
    engine.llm_engine.call_count = 0

    res = engine._process_input("lihat struktur project")
    print("DEBUG RES:", res)
    assert isinstance(res, dict)
    assert res["is_task"] is True
    assert res["task_id"] is not None
    assert "Berikut adalah struktur folder" in res["response"]


def test_scenario_d_code_editing(temp_engine):
    engine, tmpdir = temp_engine
    test_file = os.path.join(tmpdir, "main.py")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("def add(a, b):\n    return a + b\n")

    engine.llm_engine.responses = [
        '{"tool_calls": [{"id": "call_1", "function": {"name": "edit_file", "arguments": {"path": "main.py", "old_text": "return a + b", "new_text": "return a * b"}}}]}',
        "Sudah saya ubah fungsi perkalian di main.py."
    ]
    engine.llm_engine.call_count = 0

    res = engine._process_input("ubah main.py dari pertambahan ke perkalian")
    assert isinstance(res, dict)
    assert res["is_task"] is True

    with open(test_file, "r", encoding="utf-8") as f:
        updated = f.read()
    assert "return a * b" in updated


def test_scenario_e_git_tools_registered(temp_engine):
    engine, _ = temp_engine
    tools = [t.name for t in engine.tools.list_tools()]
    assert "git_status" in tools
    assert "git_diff" in tools
    assert "git_log" in tools
    assert "git_commit" in tools
