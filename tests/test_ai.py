# tests/test_ai.py
"""Tests for AI engine components."""
import unittest
from delta.ai.intent import IntentEngine, IntentType, IntentResult
from delta.core.config import DeltaConfig


class TestIntentEngine(unittest.TestCase):
    """Test intent recognition."""
    
    def setUp(self):
        self.config = DeltaConfig()
        self.engine = IntentEngine(self.config, None)
    
    def test_scan_intent(self):
        """Test scan intent recognition."""
        result = self.engine.process("scan localhost")
        self.assertIsNotNone(result)
        self.assertEqual(result.intent, IntentType.SCAN)
        self.assertIn("localhost", result.target)
    
    def test_audit_intent(self):
        """Test audit intent recognition."""
        result = self.engine.process("audit 192.168.1.1")
        self.assertIsNotNone(result)
        self.assertEqual(result.intent, IntentType.AUDIT)
    
    def test_dns_intent(self):
        """Test DNS intent recognition."""
        result = self.engine.process("dns lookup example.com")
        self.assertIsNotNone(result)
        self.assertEqual(result.intent, IntentType.DNS)
    
    def test_help_intent(self):
        """Test help intent."""
        result = self.engine.process("help")
        self.assertIsNotNone(result)
        self.assertEqual(result.intent, IntentType.HELP)

    def test_mkdir_intent(self):
        """Test folder creation intent (Indonesian)."""
        result = self.engine.process("buat folder src")
        self.assertIsNotNone(result)
        self.assertEqual(result.intent, IntentType.MKDIR)
        self.assertEqual(result.args, ["src"])

    def test_write_intent(self):
        """Test file creation intent."""
        result = self.engine.process("bikin file test.txt dengan isi halo")
        self.assertIsNotNone(result)
        self.assertEqual(result.intent, IntentType.WRITE)
        self.assertEqual(result.args[0], "test.txt")

    def test_edit_intent(self):
        """Test edit file intent."""
        result = self.engine.process("edit file config.txt ganti admin dengan root")
        self.assertIsNotNone(result)
        self.assertEqual(result.intent, IntentType.EDIT)
        self.assertEqual(result.args[0], "config.txt")

    def test_cat_intent(self):
        """Test view document intent."""
        result = self.engine.process("buka dokumen laporan.txt")
        self.assertIsNotNone(result)
        self.assertEqual(result.intent, IntentType.CAT)
        self.assertEqual(result.args[0], "laporan.txt")

    def test_cd_intent(self):
        """Test change directory intent."""
        result = self.engine.process("masuk folder proyek")
        self.assertIsNotNone(result)
        self.assertEqual(result.intent, IntentType.CD)
        self.assertEqual(result.args, ["proyek"])

    def test_ls_intent(self):
        """Test list folder intent."""
        result = self.engine.process("lihat isi folder")
        self.assertIsNotNone(result)
        self.assertEqual(result.intent, IntentType.LS)

    def test_dirinfo_intent(self):
        """Test directory analysis intent beats generic analyze."""
        result = self.engine.process("analisis folder src")
        self.assertIsNotNone(result)
        self.assertEqual(result.intent, IntentType.DIRINFO)
        self.assertEqual(result.args, ["src"])

    def test_analyze_folder_english(self):
        """Test English directory analysis intent."""
        result = self.engine.process("analyze the folder src")
        self.assertIsNotNone(result)
        self.assertEqual(result.intent, IntentType.DIRINFO)
        self.assertEqual(result.args, ["src"])


if __name__ == "__main__":
    unittest.main()