import re

class VoiceRedactor:
    SECRET_PATTERNS = [
        r"sk-[a-zA-Z0-9]{20,}",
        r"ghp_[a-zA-Z0-9]{36}",
        r"(?:api_key|password|secret|token)\s*=\s*['\"]?([a-zA-Z0-9_\-\.\=\+]{8,})['\"]?",
    ]

    @classmethod
    def sanitize(cls, text: str) -> str:
        clean = text
        for pattern in cls.SECRET_PATTERNS:
            clean = re.sub(pattern, "[REDACTED SECRET]", clean, flags=re.IGNORECASE)
        return clean
