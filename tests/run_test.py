# tests/run_test.py
import sys
import os

# Adjust python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.test_agent_scenarios import *

if __name__ == '__main__':
    # Simple manual run
    import tempfile

    print("[*] Running Scenario A & B (Casual Chat)...")
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

        llm = MockLLMEngine(["Halo Tuan, ada yang bisa saya bantu?"])
        engine = DeltaEngine(
            config=config,
            database=db,
            session=session,
            intent_engine=intent,
            plugin_manager=plugin_mgr,
            display=display,
            llm_engine=llm  # type: ignore
        )
        engine.cwd = tmpdir
        engine.tui_mode = True
        engine.web_mode = True

        res = engine._process_input("lah")
        assert isinstance(res, dict)
        assert res["is_task"] is False
        assert res["task_id"] is None
        assert "Halo Kamu" in res["response"] or "Halo Tuan" in res["response"]
        db.close()
        print("    [✓] Scenario A & B Passed!")

    print("[*] Running Scenario C (Project Inspection)...")
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

        llm = MockLLMEngine([
            '{"tool_calls": [{"id": "call_1", "function": {"name": "codebase_tree", "arguments": {"max_depth": 2}}}]}',
            "Berikut adalah struktur folder project Tuan."
        ])
        engine = DeltaEngine(
            config=config,
            database=db,
            session=session,
            intent_engine=intent,
            plugin_manager=plugin_mgr,
            display=display,
            llm_engine=llm  # type: ignore
        )
        engine.cwd = tmpdir
        engine.tui_mode = True
        engine.web_mode = True

        res = engine._process_input("lihat struktur project")
        assert isinstance(res, dict)
        assert res["is_task"] is True
        assert res["task_id"] is not None
        assert "Berikut adalah struktur folder" in res["response"]
        db.close()
        print("    [✓] Scenario C Passed!")

    print("[*] Running Scenario D (Code Editing)...")
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

        llm = MockLLMEngine([
            '{"tool_calls": [{"id": "call_1", "function": {"name": "edit_file", "arguments": {"path": "main.py", "old_text": "return a + b", "new_text": "return a * b"}}}]}',
            "Sudah saya ubah fungsi perkalian di main.py."
        ])
        engine = DeltaEngine(
            config=config,
            database=db,
            session=session,
            intent_engine=intent,
            plugin_manager=plugin_mgr,
            display=display,
            llm_engine=llm,  # type: ignore
            cwd=tmpdir
        )
        engine.cwd = tmpdir
        engine.tui_mode = True
        engine.web_mode = True

        test_file = os.path.join(tmpdir, "main.py")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("def add(a, b):\n    return a + b\n")

        res = engine._process_input("ubah main.py dari pertambahan ke perkalian")
        assert isinstance(res, dict)
        assert res["is_task"] is True

        with open(test_file, "r", encoding="utf-8") as f:
            updated = f.read()
        assert "return a * b" in updated
        db.close()
        print("    [✓] Scenario D Passed!")

    print("[*] All Acceptance Scenarios Passed Successfully!")
