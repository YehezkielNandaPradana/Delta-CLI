# tests/test_core.py
"""Tests for core Delta components."""
import unittest
import tempfile
import os
from delta.core.config import DeltaConfig
from delta.core.database import Database

class TestProtocols(unittest.TestCase):
    """Test core protocol contracts."""

    def test_core_protocols_exist(self):
        """Protocols are importable."""
        from delta.core.protocols import EngineProtocol, ConfigProtocol
        self.assertIsNotNone(EngineProtocol)
        self.assertIsNotNone(ConfigProtocol)

    def test_engine_conforms(self):
        """DeltaEngine satisfies EngineProtocol."""
        from unittest.mock import MagicMock
        from delta.core.protocols import EngineProtocol
        from delta.core.engine import DeltaEngine
        engine = DeltaEngine(
            config=MagicMock(), database=MagicMock(), session=MagicMock(),
            intent_engine=MagicMock(), plugin_manager=MagicMock(), display=MagicMock(),
        )
        self.assertIsInstance(engine, EngineProtocol)
        self.assertEqual(engine.execute(""), "")
        engine.execute("echo halo")

    def test_config_conforms(self):
        """DeltaConfig satisfies ConfigProtocol."""
        from delta.core.protocols import ConfigProtocol
        from delta.core.config import DeltaConfig
        self.assertIsInstance(DeltaConfig(), ConfigProtocol)

class TestConfig(unittest.TestCase):
    """Test Delta configuration."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = DeltaConfig()
        self.assertEqual(config.debug, False)
        self.assertEqual(config.verbose, False)
        self.assertEqual(config.timeout, 30)
    
    def test_save_load(self):
        """Test config save and load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DeltaConfig(data_dir=tmpdir)
            config.timeout = 60
            config.debug = True
            config.save(os.path.join(tmpdir, "config.json"))
            
            config2 = DeltaConfig(data_dir=tmpdir)
            config2.load(os.path.join(tmpdir, "config.json"))
            self.assertEqual(config2.timeout, 60)
            self.assertEqual(config2.debug, True)

class TestDatabase(unittest.TestCase):
    """Test database operations."""
    
    def setUp(self):
        self.db = Database(":memory:")
        self.db.initialize()
    
    def tearDown(self):
        self.db.close()
    
    def test_history(self):
        """Test history CRUD."""
        self.db.add_history("scan localhost", host="127.0.0.1")
        history = self.db.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["command"], "scan localhost")
    
    def test_host_upsert(self):
        """Test host upsert."""
        self.db.upsert_host("127.0.0.1", os="Linux")
        host = self.db.get_host("127.0.0.1")
        self.assertIsNotNone(host)
        self.assertEqual(host["os"], "Linux")

if __name__ == "__main__":
    unittest.main()