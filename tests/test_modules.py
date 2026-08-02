# tests/test_modules.py
"""Tests for scanner and security modules."""
import unittest
from delta.modules.crypto import CryptoModule

class TestCryptoModule(unittest.TestCase):
    """Test cryptography module."""
    
    def setUp(self):
        self.crypto = CryptoModule()
    
    def test_hash_identification(self):
        """Test hash type identification."""
        result = self.crypto.identify_hash(
            "5d41402abc4b2a76b9719d911017c592"
        )
        self.assertTrue(result.matches)
        self.assertIn("MD5/MD4/NTLM/LM", result.possible_types)
    
    def test_password_strength(self):
        """Test password strength analysis."""
        result = self.crypto.analyze_password("Tr0ub4dor&3")
        self.assertGreaterEqual(result.score, 3)
        self.assertGreater(result.entropy, 40)
    
    def test_weak_password(self):
        """Test weak password detection."""
        result = self.crypto.analyze_password("password")
        self.assertEqual(result.score, 0)
        self.assertIn("common", result.feedback[0].lower() if result.feedback else "")

if __name__ == "__main__":
    unittest.main()