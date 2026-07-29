"""Tests for DNS lookup module."""
import unittest
from unittest.mock import patch, MagicMock
from delta.modules.dns import DNSModule


class TestDNSModule(unittest.TestCase):
    """Test DNS lookup operations."""

    def setUp(self):
        self.dns = DNSModule()

    @patch("delta.modules.dns.socket.gethostbyname")
    def test_lookup_success(self, mock_gethostbyname):
        """Test successful DNS lookup."""
        mock_gethostbyname.return_value = "93.184.216.34"
        result = self.dns.lookup("example.com")
        self.assertEqual(result.domain, "example.com")
        self.assertEqual(result.ip, "93.184.216.34")

    @patch("delta.modules.dns.socket.gethostbyname")
    def test_lookup_failure(self, mock_gethostbyname):
        """Test DNS lookup failure."""
        import socket
        mock_gethostbyname.side_effect = socket.gaierror()
        result = self.dns.lookup("nonexistent.invalid")
        self.assertEqual(result.domain, "nonexistent.invalid")
        self.assertEqual(result.ip, "")

    def test_query_mx(self):
        """Test MX record query returns list."""
        records = self.dns.query_mx("example.com")
        self.assertIsInstance(records, list)

    def test_query_ns(self):
        """Test NS record query returns list."""
        records = self.dns.query_ns("example.com")
        self.assertIsInstance(records, list)

    @patch("delta.modules.dns.socket.gethostbyaddr")
    def test_reverse_lookup_success(self, mock_gethostbyaddr):
        """Test successful reverse DNS lookup."""
        mock_gethostbyaddr.return_value = ("host.example.com", [], ["93.184.216.34"])
        result = self.dns.reverse_lookup("93.184.216.34")
        self.assertEqual(result, "host.example.com")

    @patch("delta.modules.dns.socket.gethostbyaddr")
    def test_reverse_lookup_failure(self, mock_gethostbyaddr):
        """Test reverse DNS lookup failure."""
        import socket
        mock_gethostbyaddr.side_effect = socket.herror()
        result = self.dns.reverse_lookup("192.0.2.1")
        self.assertEqual(result, "")

    @patch.object(DNSModule, "lookup")
    @patch.object(DNSModule, "query_mx")
    @patch.object(DNSModule, "query_ns")
    def test_get_all_dns(self, mock_query_ns, mock_query_mx, mock_lookup):
        """Test comprehensive DNS info."""
        delta_result = MagicMock()
        delta_result.ip = "93.184.216.34"
        delta_result.a_records = ["93.184.216.34"]
        mock_lookup.return_value = delta_result
        mock_query_mx.return_value = ["mail.example.com -> 93.184.216.34"]
        mock_query_ns.return_value = ["ns1.example.com -> 93.184.216.34"]

        result = self.dns.get_all_dns("example.com")
        self.assertEqual(result.ip, "93.184.216.34")
        self.assertEqual(len(result.mx_records), 1)
        self.assertEqual(len(result.ns_records), 1)


if __name__ == "__main__":
    unittest.main()
