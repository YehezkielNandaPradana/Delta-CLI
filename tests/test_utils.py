"""Tests for utility modules."""
import unittest
import tempfile
import os
from delta.utils.validators import Validators
from delta.utils.network import NetworkUtils
from delta.utils.helpers import Helpers


class TestValidators(unittest.TestCase):
    """Test input validation utilities."""

    def test_validate_port_valid(self):
        """Test valid port numbers."""
        self.assertEqual(Validators.validate_port(80), 80)
        self.assertEqual(Validators.validate_port("443"), 443)
        self.assertEqual(Validators.validate_port(1), 1)
        self.assertEqual(Validators.validate_port(65535), 65535)

    def test_validate_port_invalid(self):
        """Test invalid port numbers."""
        self.assertIsNone(Validators.validate_port(0))
        self.assertIsNone(Validators.validate_port(65536))
        self.assertIsNone(Validators.validate_port("abc"))
        self.assertIsNone(Validators.validate_port(-1))

    def test_validate_timeout(self):
        """Test timeout validation."""
        self.assertEqual(Validators.validate_timeout(30), 30.0)
        self.assertEqual(Validators.validate_timeout("10"), 10.0)
        self.assertEqual(Validators.validate_timeout(-5), 0.1)
        self.assertEqual(Validators.validate_timeout(500), 300.0)
        self.assertEqual(Validators.validate_timeout("invalid"), 30.0)

    def test_sanitize_command(self):
        """Test command sanitization."""
        self.assertEqual(Validators.sanitize_command("ls"), "ls")
        self.assertEqual(Validators.sanitize_command("scan; rm -rf /"), "scan rm -rf /")
        self.assertEqual(Validators.sanitize_command("  ls -la  "), "ls -la")

    def test_validate_host(self):
        """Test host validation."""
        self.assertEqual(Validators.validate_host("example.com"), "example.com")
        self.assertEqual(Validators.validate_host("https://example.com"), "example.com")
        self.assertEqual(Validators.validate_host("192.168.1.1"), "192.168.1.1")
        self.assertIsNone(Validators.validate_host(""))
        self.assertIsNone(Validators.validate_host(None))

    def test_is_valid_ip(self):
        """Test IP validation."""
        self.assertTrue(Validators._is_valid_ip("192.168.1.1"))
        self.assertTrue(Validators._is_valid_ip("8.8.8.8"))
        self.assertFalse(Validators._is_valid_ip("999.999.999.999"))
        self.assertFalse(Validators._is_valid_ip("not.an.ip"))


class TestNetworkUtils(unittest.TestCase):
    """Test network utility functions."""

    def test_is_valid_ip(self):
        """Test IP address validation."""
        self.assertTrue(NetworkUtils.is_valid_ip("192.168.1.1"))
        self.assertTrue(NetworkUtils.is_valid_ip("0.0.0.0"))
        self.assertFalse(NetworkUtils.is_valid_ip("999.999.999.999"))
        self.assertFalse(NetworkUtils.is_valid_ip("abc"))

    def test_is_valid_hostname(self):
        """Test hostname validation."""
        self.assertTrue(NetworkUtils.is_valid_hostname("example.com"))
        self.assertTrue(NetworkUtils.is_valid_hostname("sub.domain.org"))
        self.assertFalse(NetworkUtils.is_valid_hostname(""))
        self.assertFalse(NetworkUtils.is_valid_hostname("-invalid.com"))

    def test_is_valid_url(self):
        """Test URL validation."""
        self.assertTrue(NetworkUtils.is_valid_url("https://example.com"))
        self.assertTrue(NetworkUtils.is_valid_url("http://example.com/path"))
        self.assertFalse(NetworkUtils.is_valid_url("not-a-url"))
        self.assertFalse(NetworkUtils.is_valid_url(""))

    def test_extract_ips(self):
        """Test IP extraction from text."""
        text = "Server at 192.168.1.1 and gateway at 10.0.0.1"
        ips = NetworkUtils.extract_ips(text)
        self.assertEqual(len(ips), 2)
        self.assertIn("192.168.1.1", ips)
        self.assertIn("10.0.0.1", ips)

    def test_extract_domains(self):
        """Test domain extraction from text."""
        text = "Visit example.com and test.org for info"
        domains = NetworkUtils.extract_domains(text)
        self.assertIn("example.com", domains)
        self.assertIn("test.org", domains)

    def test_port_to_service_known(self):
        """Test known port to service mapping."""
        self.assertEqual(NetworkUtils.port_to_service(80), "http")
        self.assertEqual(NetworkUtils.port_to_service(22), "ssh")
        self.assertEqual(NetworkUtils.port_to_service(443), "https")

    def test_port_to_service_unknown(self):
        """Test unknown port to service mapping."""
        result = NetworkUtils.port_to_service(9999)
        self.assertEqual(result, "port-9999")


class TestHelpers(unittest.TestCase):
    """Test general helper functions."""

    def test_timestamp(self):
        """Test timestamp generation."""
        ts = Helpers.timestamp()
        self.assertIsInstance(ts, str)
        self.assertGreater(len(ts), 10)

    def test_generate_id(self):
        """Test ID generation."""
        id1 = Helpers.generate_id("test")
        id2 = Helpers.generate_id("test")
        self.assertTrue(id1.startswith("test_"))
        self.assertNotEqual(id1, id2)

    def test_ensure_dir(self):
        """Test directory creation."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "new_dir", "nested")
            result = Helpers.ensure_dir(path)
            self.assertTrue(os.path.exists(result))
            self.assertEqual(result, path)

    def test_read_write_file(self):
        """Test file read/write operations."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test.txt")
            success = Helpers.write_file(path, "hello world")
            self.assertTrue(success)
            content = Helpers.read_file(path)
            self.assertEqual(content, "hello world")

    def test_read_file_not_found(self):
        """Test reading non-existent file."""
        result = Helpers.read_file("/nonexistent/file.txt")
        self.assertIsNone(result)

    def test_read_write_json(self):
        """Test JSON file read/write."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "data.json")
            data = {"key": "value", "num": 42}
            success = Helpers.write_json(path, data)
            self.assertTrue(success)
            loaded = Helpers.read_json(path)
            self.assertEqual(loaded, data)

    def test_truncate(self):
        """Test text truncation."""
        self.assertEqual(Helpers.truncate("short"), "short")
        self.assertEqual(Helpers.truncate("a" * 100), "a" * 100)
        result = Helpers.truncate("a" * 200, max_len=10)
        self.assertEqual(result, "aaaaaaa...")
        self.assertEqual(len(result), 10)

    def test_format_bytes(self):
        """Test byte formatting."""
        self.assertEqual(Helpers.format_bytes(0), "0.0 B")
        self.assertEqual(Helpers.format_bytes(1023), "1023.0 B")
        self.assertEqual(Helpers.format_bytes(1024), "1.0 KB")
        self.assertEqual(Helpers.format_bytes(1048576), "1.0 MB")
        self.assertEqual(Helpers.format_bytes(1073741824), "1.0 GB")



class TestTextUtils(unittest.TestCase):
    """Test text utility functions."""

    def setUp(self):
        from delta.utils.text_utils import TextUtils
        self.text_utils = TextUtils

    def test_slugify(self):
        """Test slug generation."""
        self.assertEqual(self.text_utils.slugify("Hello World"), "hello-world")
        self.assertEqual(self.text_utils.slugify("  Test  "), "test")
        self.assertEqual(self.text_utils.slugify("Hello! World?"), "hello-world")

    def test_word_count(self):
        """Test word counting."""
        self.assertEqual(self.text_utils.word_count(""), 0)
        self.assertEqual(self.text_utils.word_count("hello"), 1)
        self.assertEqual(self.text_utils.word_count("one two three"), 3)

    def test_char_count(self):
        """Test character counting."""
        self.assertEqual(self.text_utils.char_count("hello"), 5)
        self.assertEqual(self.text_utils.char_count("he llo"), 6)
        self.assertEqual(self.text_utils.char_count("he llo", include_spaces=False), 5)

    def test_extract_urls(self):
        """Test URL extraction."""
        text = "Visit https://example.com and http://test.org/path"
        urls = self.text_utils.extract_urls(text)
        self.assertEqual(len(urls), 2)
        self.assertIn("https://example.com", urls)

    def test_extract_emails(self):
        """Test email extraction."""
        text = "Contact admin@example.com or support@test.org"
        emails = self.text_utils.extract_emails(text)
        self.assertEqual(len(emails), 2)
        self.assertIn("admin@example.com", emails)

    def test_extract_hashes(self):
        """Test hash extraction."""
        text = "md5: d41d8cd98f00b204e9800998ecf8427e sha1: da39a3ee5e6b4b0d3255bfef95601890afd80709"
        hashes = self.text_utils.extract_hashes(text)
        self.assertIn("md5", hashes)
        self.assertIn("sha1", hashes)

    def test_obfuscate_email(self):
        """Test email obfuscation."""
        result = self.text_utils.obfuscate_email("john.doe@example.com")
        self.assertIn("@example.com", result)
        self.assertNotIn("john", result)

    def test_obfuscate_ip(self):
        """Test IP obfuscation."""
        result = self.text_utils.obfuscate_ip("192.168.1.100")
        self.assertEqual(result, "192.168.*.*")

    def test_detect_language(self):
        """Test language detection."""
        en = self.text_utils.detect_language("The quick brown fox")
        id_result = self.text_utils.detect_language("Halo apa kabar dan dimana")
        self.assertEqual(en, "en")
        self.assertEqual(id_result, "id")

    def test_is_palindrome(self):
        """Test palindrome detection."""
        self.assertTrue(self.text_utils.is_palindrome("racecar"))
        self.assertTrue(self.text_utils.is_palindrome("A man a plan a canal Panama"))
        self.assertFalse(self.text_utils.is_palindrome("hello"))

    def test_word_frequency(self):
        """Test word frequency analysis."""
        text = "apple banana apple cherry banana apple"
        freq = self.text_utils.word_frequency(text, top_n=2)
        self.assertEqual(freq[0][0], "apple")
        self.assertEqual(freq[0][1], 3)

    def test_count_sentences(self):
        """Test sentence counting."""
        self.assertEqual(self.text_utils.count_sentences("Hello. World!"), 2)
        self.assertEqual(self.text_utils.count_sentences(""), 0)

    def test_average_word_length(self):
        """Test average word length."""
        avg = self.text_utils.average_word_length("a bb ccc")
        self.assertAlmostEqual(avg, 2.0)
        self.assertEqual(self.text_utils.average_word_length(""), 0.0)

    def test_readability(self):
        """Test readability score."""
        score = self.text_utils.calculate_readability("The cat sat on the mat.")
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)


if __name__ == "__main__":
    unittest.main()
