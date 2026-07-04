# delta/utils/helpers.py
"""General helper utilities."""

import os
import json
import time
import random
import string
from datetime import datetime
from typing import Any, Dict, List, Optional


class Helpers:
    """General helper functions."""

    @staticmethod
    def timestamp() -> str:
        """Get current timestamp string."""
        return datetime.now().isoformat()

    @staticmethod
    def generate_id(prefix: str = "delta") -> str:
        """Generate unique ID."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        rand = ''.join(random.choices(string.hexdigits.lower(), k=8))
        return f"{prefix}_{ts}_{rand}"

    @staticmethod
    def ensure_dir(path: str) -> str:
        """Ensure directory exists, create if needed."""
        os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def read_file(path: str) -> Optional[str]:
        """Read file content."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None

    @staticmethod
    def write_file(path: str, content: str) -> bool:
        """Write content to file."""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception:
            return False

    @staticmethod
    def read_json(path: str) -> Optional[Any]:
        """Read JSON file."""
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return None

    @staticmethod
    def write_json(path: str, data: Any) -> bool:
        """Write data to JSON file."""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception:
            return False

    @staticmethod
    def truncate(text: str, max_len: int = 100) -> str:
        """Truncate text to max length."""
        if len(text) <= max_len:
            return text
        return text[:max_len-3] + "..."

    @staticmethod
    def format_bytes(bytes_val: int) -> str:
        """Format bytes to human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f} PB"