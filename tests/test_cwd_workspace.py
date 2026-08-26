import os
import tempfile
import pytest
from delta.core.config import DeltaConfig
from delta.core.database import Database
from delta.core.session import SessionManager
from delta.core.display import DisplayManager
from delta.ai.intent import IntentEngine
from delta.core.plugin import PluginManager
from delta.core.engine import DeltaEngine
from delta.web.bridge import EngineBridge
from delta.main import create_engine

def test_initial_cwd_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = create_engine(cwd=tmpdir)
        assert engine.cwd == os.path.abspath(tmpdir)
        assert engine.session.context.working_directory == os.path.abspath(tmpdir)

def test_cwd_flag_override():
    with tempfile.TemporaryDirectory() as tmpdir1:
        with tempfile.TemporaryDirectory() as tmpdir2:
            engine = create_engine(cwd=tmpdir2)
            assert engine.cwd == os.path.abspath(tmpdir2)
            assert engine.cwd != os.path.abspath(tmpdir1)

def test_change_directory_tool_and_persistence():
    with tempfile.TemporaryDirectory() as parent_dir:
        sub_dir = os.path.join(parent_dir, "backend")
        os.makedirs(sub_dir, exist_ok=True)

        engine = create_engine(cwd=parent_dir)
        assert engine.cwd == os.path.abspath(parent_dir)

        # Execute change_directory tool
        ok, msg = engine.set_cwd("backend")
        assert ok is True
        assert engine.cwd == os.path.abspath(sub_dir)
        assert engine.fs.cwd == os.path.abspath(sub_dir)
        assert engine.codebase.root_dir == os.path.abspath(sub_dir)
        assert engine.session.context.working_directory == os.path.abspath(sub_dir)

        # Perform filesystem read / list to ensure cwd persists
        ok, entries = engine.fs.list_dir(".")
        assert ok is True
        assert engine.cwd == os.path.abspath(sub_dir)

def test_engine_bridge_workspace_status():
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = create_engine(cwd=tmpdir)
        bridge = EngineBridge(engine)
        status = bridge.get_status()
        assert status["working_directory"] == os.path.abspath(tmpdir)
