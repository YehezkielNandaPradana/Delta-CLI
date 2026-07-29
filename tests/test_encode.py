"""Tests for encoding/decoding module."""
import unittest
from delta.modules.encode import EncodeModule


class TestEncodeModule(unittest.TestCase):
    """Test encoding and decoding operations."""

    def setUp(self):
        self.encode = EncodeModule()

    def test_decode_base64(self):
        """Test Base64 decoding."""
        result = self.encode.decode_base64("SGVsbG8gV29ybGQ=")
        self.assertTrue(result.success)
        self.assertEqual(result.result, "Hello World")

    def test_decode_base64_no_padding(self):
        """Test Base64 decoding without padding."""
        result = self.encode.decode_base64("SGVsbG8gV29ybGQ")
        self.assertTrue(result.success)
        self.assertEqual(result.result, "Hello World")

    def test_encode_base64(self):
        """Test Base64 encoding."""
        result = self.encode.encode_base64("Hello World")
        self.assertTrue(result.success)
        self.assertEqual(result.result, "SGVsbG8gV29ybGQ=")

    def test_decode_hex(self):
        """Test hex decoding."""
        result = self.encode.decode_hex("48656c6c6f")
        self.assertTrue(result.success)
        self.assertEqual(result.result, "Hello")

    def test_decode_hex_with_prefix(self):
        """Test hex decoding with 0x prefix."""
        result = self.encode.decode_hex("0x48656c6c6f")
        self.assertTrue(result.success)
        self.assertEqual(result.result, "Hello")

    def test_encode_hex(self):
        """Test hex encoding."""
        result = self.encode.encode_hex("Hello")
        self.assertTrue(result.success)
        self.assertEqual(result.result, "48656c6c6f")

    def test_decode_url(self):
        """Test URL decoding."""
        result = self.encode.decode_url("Hello%20World%21")
        self.assertTrue(result.success)
        self.assertEqual(result.result, "Hello World!")

    def test_encode_url(self):
        """Test URL encoding."""
        result = self.encode.encode_url("Hello World!")
        self.assertTrue(result.success)
        self.assertEqual(result.result, "Hello%20World%21")

    def test_decode_jwt(self):
        """Test JWT decoding."""
        result = self.encode.decode_jwt(
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dummy"
        )
        self.assertTrue(result.success)
        self.assertIn("HEADER", result.result)
        self.assertIn("PAYLOAD", result.result)

    def test_decode_jwt_invalid(self):
        """Test JWT decoding with invalid token."""
        result = self.encode.decode_jwt("invalid.token")
        self.assertFalse(result.success)
        self.assertIn("Invalid JWT", result.error)

    def test_format_json(self):
        """Test JSON formatting."""
        result = self.encode.format_json('{"name":"test","value":42}')
        self.assertTrue(result.success)
        self.assertIn('"name"', result.result)
        self.assertIn('"value"', result.result)

    def test_format_json_invalid(self):
        """Test JSON formatting with invalid input."""
        result = self.encode.format_json("not json")
        self.assertFalse(result.success)
        self.assertIn("JSON parse error", result.error)

    def test_roundtrip_base64(self):
        """Test Base64 encode/decode roundtrip."""
        original = "Test data with special chars: !@#$%^&*()"
        encoded = self.encode.encode_base64(original)
        self.assertTrue(encoded.success)
        decoded = self.encode.decode_base64(encoded.result)
        self.assertTrue(decoded.success)
        self.assertEqual(decoded.result, original)

    def test_empty_input_base64(self):
        """Test Base64 decode with empty input."""
        result = self.encode.decode_base64("")
        self.assertTrue(result.success)
        self.assertEqual(result.result, "")


if __name__ == "__main__":
    unittest.main()
