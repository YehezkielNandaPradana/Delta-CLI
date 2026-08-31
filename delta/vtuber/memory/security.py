"""
Security & Credential Filtering Utilities for VTuber Memory System.
Prevents API keys, passwords, bearer tokens, and private secrets from ever entering long-term memory.
"""

import re
from typing import List

# Patterns matching API keys, JWT tokens, private keys, passwords, and sensitive credentials
SECRET_PATTERNS: List[re.Pattern] = [
    re.compile(r"(?:api[_-]?key|apikey|secret|token|password|passwd|auth[_-]?token)\s*[:=]\s*['\"]?([A-Za-z0-9_\-\.\$\/]{8,})['\"]?", re.IGNORECASE),
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9._-]{10,}\.[A-Za-z0-9_-]{10,}", re.IGNORECASE),  # JWT tokens
    re.compile(r"-----BEGIN (?:[A-Z0-9_\- ]+ )?PRIVATE KEY-----", re.IGNORECASE),  # Private keys
    re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{30,}", re.IGNORECASE),  # GitHub tokens
    re.compile(r"sk-[A-Za-z0-9]{32,}", re.IGNORECASE),  # OpenAI / provider API keys
    re.compile(r"AKIA[0-9A-Z]{16}", re.IGNORECASE),  # AWS Access Key ID
]


class SecretFilter:
    """
    Scans candidate memory text and rejects storage if secrets or credentials are found.
    """

    @classmethod
    def contains_secrets(cls, text: str) -> bool:
        """
        Return True if candidate text contains credential patterns.
        """
        if not text:
            return False

        for pat in SECRET_PATTERNS:
            if pat.search(text):
                return True

        return False

    @classmethod
    def sanitize(cls, text: str) -> str:
        """
        Redact any detected secret substring in text.
        """
        if not text:
            return ""

        sanitized = text
        for pat in SECRET_PATTERNS:
            sanitized = pat.sub("[REDACTED_SECRET]", sanitized)

        return sanitized
