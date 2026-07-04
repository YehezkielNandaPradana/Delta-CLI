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


if __name__ == "__main__":
    unittest.main()