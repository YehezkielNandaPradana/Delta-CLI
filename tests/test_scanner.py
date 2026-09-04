import unittest
from delta.modules.scanner import ScanResult

class TestScannerModule(unittest.TestCase):
    def test_scan_result_defaults(self):
        sr = ScanResult(target="example.com", ip="93.184.216.34")
        self.assertEqual(sr.target, "example.com")
        self.assertEqual(sr.ip, "93.184.216.34")
        self.assertEqual(sr.open_ports, [])
        self.assertEqual(sr.services, {})
        self.assertEqual(sr.headers, {})
        self.assertEqual(sr.ssl_info, {})
        self.assertEqual(sr.dns_info, {})
        self.assertEqual(sr.vulnerabilities, [])
        self.assertEqual(sr.risk_level, "info")

if __name__ == "__main__":
    unittest.main()
