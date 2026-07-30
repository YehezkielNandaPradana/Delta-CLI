# delta/utils/network.py
"""Network utility functions."""

import socket
import re
from typing import List, Optional, Tuple

__all__ = ["NetworkUtils"]


class NetworkUtils:
    """Network-related utility functions."""

    @staticmethod
    def is_valid_ip(ip: str) -> bool:
        """Check if string is a valid IP address."""
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False

    @staticmethod
    def is_valid_hostname(hostname: str) -> bool:
        """Check if string is a valid hostname."""
        if len(hostname) > 253:
            return False
        pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        return bool(re.match(pattern, hostname))

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if string is a valid URL."""
        pattern = r'^https?://[\w.-]+(?::\d+)?(?:/[\w./%-]*)?$'
        return bool(re.match(pattern, url))

    @staticmethod
    def extract_ips(text: str) -> List[str]:
        """Extract valid IP addresses from text."""
        pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        candidates = re.findall(pattern, text)
        return [ip for ip in candidates if NetworkUtils.is_valid_ip(ip)]

    @staticmethod
    def extract_domains(text: str) -> List[str]:
        """Extract domain names from text."""
        pattern = r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b'
        return re.findall(pattern, text)

    @staticmethod
    def get_local_ip() -> str:
        """Get local machine IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    @staticmethod
    def port_to_service(port: int) -> str:
        """Convert port number to common service name."""
        try:
            return socket.getservbyport(port)
        except:
            services = {
                21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp", 53: "domain",
                80: "http", 110: "pop3", 143: "imap", 443: "https", 445: "microsoft-ds",
                993: "imaps", 995: "pop3s", 1433: "ms-sql-s", 3306: "mysql",
                3389: "ms-wbt-server", 5432: "postgresql", 5900: "vnc", 6379: "redis",
                8080: "http-proxy", 8443: "https-alt", 27017: "mongod",
            }
            return services.get(port, f"port-{port}")