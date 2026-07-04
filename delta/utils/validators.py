# delta/utils/validators.py
"""Input validation utilities."""

import re
from typing import Any, Dict, List, Optional, Type


class Validators:
    """Input validation and sanitization utilities."""

    @staticmethod
    def validate_port(port: Any) -> Optional[int]:
        """Validate and sanitize port number."""
        try:
            port = int(port)
            if 1 <= port <= 65535:
                return port
        except (ValueError, TypeError):
            pass
        return None

    @staticmethod
    def validate_timeout(timeout: Any) -> float:
        """Validate timeout value."""
        try:
            timeout = float(timeout)
            return max(0.1, min(timeout, 300.0))
        except (ValueError, TypeError):
            return 30.0

    @staticmethod
    def sanitize_command(cmd: str) -> str:
        """Sanitize command input."""
        # Remove dangerous characters
        dangerous = [";", "|", "&", "`", "$", "(", ")", "{", "}", "<", ">", "!"]
        for char in dangerous:
            cmd = cmd.replace(char, "")
        return cmd.strip()

    @staticmethod
    def validate_host(host: str) -> Optional[str]:
        """Validate and normalize host address."""
        if not host or not host.strip():
            return None
        
        host = host.strip().lower()
        # Remove protocol
        host = re.sub(r'^https?://', '', host)
        # Remove path
        host = host.split("/")[0]
        # Remove port
        host = host.split(":")[0]
        
        if host and (re.match(r'^[\w.-]+$', host) or Validators._is_valid_ip(host)):
            return host
        return None

    @staticmethod
    def _is_valid_ip(ip: str) -> bool:
        """Check valid IP address."""
        import socket
        try:
            socket.inet_aton(ip)
            return True
        except:
            return False