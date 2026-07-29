"""Tests for GeoIP module."""
import unittest
from unittest.mock import patch, MagicMock
from delta.modules.geoip import GeoIPModule


class TestGeoIPModule(unittest.TestCase):
    """Test IP geolocation operations."""

    def setUp(self):
        self.geo = GeoIPModule()

    @patch("delta.modules.geoip.urlopen")
    def test_lookup_success(self, mock_urlopen):
        """Test successful geolocation lookup."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'''{
            "status": "success",
            "country": "United States",
            "countryCode": "US",
            "region": "CA",
            "city": "Los Angeles",
            "zip": "90001",
            "lat": 34.0522,
            "lon": -118.2437,
            "timezone": "America/Los_Angeles",
            "isp": "Test ISP",
            "org": "Test Org",
            "as": "AS12345 Test AS",
            "query": "8.8.8.8"
        }'''
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = self.geo.lookup("8.8.8.8")
        self.assertTrue(result.success)
        self.assertEqual(result.country, "United States")
        self.assertEqual(result.country_code, "US")
        self.assertEqual(result.city, "Los Angeles")
        self.assertEqual(result.isp, "Test ISP")
        self.assertEqual(result.ip, "8.8.8.8")

    @patch("delta.modules.geoip.urlopen")
    def test_lookup_failure(self, mock_urlopen):
        """Test failed geolocation lookup."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'''{
            "status": "fail",
            "message": "invalid query",
            "query": "invalid"
        }'''
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = self.geo.lookup("invalid")
        self.assertFalse(result.success)
        self.assertIn("invalid", result.error)

    def test_lookup_invalid_ip(self):
        """Test lookup with invalid IP address."""
        result = self.geo.lookup("not.an.ip")
        self.assertFalse(result.success)
        self.assertIn("Invalid IP", result.error)

    @patch("delta.modules.geoip.GeoIPModule.lookup")
    def test_lookup_local(self, mock_lookup):
        """Test local machine lookup."""
        mock_result = MagicMock()
        mock_lookup.return_value = mock_result
        result = self.geo.lookup_local()
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
