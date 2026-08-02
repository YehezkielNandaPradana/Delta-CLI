"""Input validation utilities."""

import re

import html

import socket

from typing import Any, Dict, List, Optional, Tuple

__all__ = ["Validators"]

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

        host = re.sub(r'^https?://', '', host)

        host = host.split("/")[0]

        host = host.split(":")[0]

        if host and (re.match(r'^[\w.-]+$', host) or Validators._is_valid_ip(host)):

            return host

        return None

    @staticmethod

    def validate_email(email: str) -> Optional[str]:

        """Validate email address format."""

        if not email or not email.strip():

            return None

        email = email.strip().lower()

        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if re.match(pattern, email):

            return email

        return None

    @staticmethod

    def validate_domain(domain: str) -> Optional[str]:

        """Validate domain name format."""

        if not domain or not domain.strip():

            return None

        domain = domain.strip().lower()

        pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'

        if re.match(pattern, domain):

            return domain

        return None

    @staticmethod

    def sanitize_html(text: str) -> str:

        """Sanitize HTML content to prevent XSS."""

        return html.escape(text, quote=True)

    @staticmethod

    def is_strong_password(password: str, min_length: int = 8) -> Dict[str, Any]:

        """Check password strength and return detailed analysis."""

        result = {

            "valid": False,

            "score": 0,

            "missing": [],

            "suggestions": [],

        }

        if not password:

            result["suggestions"].append("Password cannot be empty")

            return result

        if len(password) < min_length:

            result["missing"].append(f"At least {min_length} characters")

            result["suggestions"].append(f"Add {min_length - len(password)} more characters")

        checks = {

            "uppercase": (r'[A-Z]', "Add uppercase letters"),

            "lowercase": (r'[a-z]', "Add lowercase letters"),

            "digit": (r'\d', "Add digits"),

            "special": (r'[!@#$%^&*(),.?":{}|<>]', "Add special characters"),

        }

        score = 0

        for name, (pattern, suggestion) in checks.items():

            if re.search(pattern, password):

                score += 1

            else:

                result["missing"].append(name)

                result["suggestions"].append(suggestion)

        if len(password) >= min_length:

            score += 1

        if len(password) >= 12:

            score += 1

        if len(password) >= 16:

            score += 1

        result["score"] = min(score, 5)

        result["valid"] = score >= 3

        return result

    @staticmethod

    def validate_ip_range(ip_range: str) -> Optional[tuple]:

        """Validate IP range (CIDR or dash notation)."""

        if not ip_range or not ip_range.strip():

            return None

        ip_range = ip_range.strip()

        cidr = re.match(r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/(\d{1,2})$', ip_range)

        if cidr:

            ip, prefix = cidr.groups()

            prefix_int = int(prefix)

            if Validators._is_valid_ip(ip) and 0 <= prefix_int <= 32:

                return ("cidr", ip, prefix_int)

        dash = re.match(r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})-(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$', ip_range)

        if dash:

            start, end = dash.groups()

            if Validators._is_valid_ip(start) and Validators._is_valid_ip(end):

                return ("range", start, end)

        single = re.match(r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$', ip_range)

        if single:

            ip = single.group(1)

            if Validators._is_valid_ip(ip):

                return ("single", ip, ip)

        return None

    @staticmethod

    def validate_url(url: str) -> Optional[str]:

        """Validate and normalize URL."""

        if not url or not url.strip():

            return None

        url = url.strip()

        if not url.startswith(('http://', 'https://')):

            url = 'https://' + url

        pattern = r'^https?://[\w.-]+(?::\d+)?(?:/[\w./%-]*)?$'

        if re.match(pattern, url):

            return url

        return None

    @staticmethod

    def validate_mac(mac: str) -> Optional[str]:

        """Validate MAC address format (aa:bb:cc:dd:ee:ff)."""

        if not mac or not mac.strip():

            return None

        mac = mac.strip().lower()

        pattern = r'^([0-9a-f]{2}[:-]){5}[0-9a-f]{2}$'

        if re.match(pattern, mac):

            return mac

        return None

    @staticmethod

    def _is_valid_ip(ip: str) -> bool:

        """Check valid IP address."""

        try:

            socket.inet_aton(ip)

            return True

        except (socket.error, OSError):

            return False