# delta/modules/dns.py
"""
DNS Lookup Module - Performs DNS resolution, reverse DNS, and record enumeration.
"""

import socket
import struct
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class DNSResult:
    """DNS lookup result."""
    domain: str
    ip: str = ""
    a_records: List[str] = field(default_factory=list)
    aaaa_records: List[str] = field(default_factory=list)
    mx_records: List[str] = field(default_factory=list)
    ns_records: List[str] = field(default_factory=list)
    txt_records: List[str] = field(default_factory=list)
    cname_records: List[str] = field(default_factory=list)
    soa_record: str = ""
    reverse_dns: str = ""


class DNSModule:
    """
    DNS enumeration module using standard library socket operations.
    Performs various DNS lookups without external dependencies.
    """

    def __init__(self):
        self._dns_servers = ["8.8.8.8", "1.1.1.1", "208.67.222.222"]

    def lookup(self, domain: str) -> DNSResult:
        """Perform comprehensive DNS lookup."""
        result = DNSResult(domain=domain)
        
        # A record
        try:
            result.ip = socket.gethostbyname(domain)
            result.a_records = [result.ip]
            
            # Get all A records
            try:
                _, _, ip_list = socket.gethostbyname_ex(domain)
                result.a_records = ip_list
            except:
                pass
        except socket.gaierror:
            pass

        # Reverse DNS
        try:
            if result.ip:
                result.reverse_dns = socket.gethostbyaddr(result.ip)[0]
        except (socket.herror, socket.gaierror):
            pass

        # CNAME
        try:
            cname = socket.getfqdn(domain)
            if cname != domain:
                result.cname_records = [cname]
        except:
            pass

        return result

    def query_mx(self, domain: str) -> List[str]:
        """Simple MX record lookup via DNS resolution patterns."""
        records = []
        # Common MX patterns
        mx_patterns = [
            f"mail.{domain}",
            f"smtp.{domain}",
            f"mx1.{domain}",
            f"mx.{domain}",
        ]
        for pattern in mx_patterns:
            try:
                ip = socket.gethostbyname(pattern)
                records.append(f"{pattern} -> {ip}")
            except:
                pass
        return records

    def query_ns(self, domain: str) -> List[str]:
        """Simple NS record lookup."""
        records = []
        ns_patterns = [
            f"ns1.{domain}",
            f"ns2.{domain}",
            f"dns.{domain}",
        ]
        for pattern in ns_patterns:
            try:
                ip = socket.gethostbyname(pattern)
                records.append(f"{pattern} -> {ip}")
            except:
                pass
        return records

    def reverse_lookup(self, ip: str) -> str:
        """Reverse DNS lookup."""
        try:
            return socket.gethostbyaddr(ip)[0]
        except:
            return ""

    def get_all_dns(self, domain: str) -> DNSResult:
        """Get all available DNS information."""
        result = self.lookup(domain)
        result.mx_records = self.query_mx(domain)
        result.ns_records = self.query_ns(domain)
        return result