"""General helper utilities."""

import os

import json

import math

import random

import string

from datetime import datetime, timedelta

from typing import Any, Dict, List, Optional

__all__ = ["Helpers"]

class Helpers:

    """General helper functions."""

    @staticmethod

    def timestamp() -> str:

        """Get current timestamp string (ISO format)."""

        return datetime.now().isoformat()

    @staticmethod

    def generate_id(prefix: str = "delta") -> str:

        """Generate unique ID with prefix and random suffix."""

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        rand = ''.join(random.choices(string.hexdigits.lower(), k=8))

        return f"{prefix}_{ts}_{rand}"

    @staticmethod

    def ensure_dir(path: str) -> str:

        """Ensure directory exists, create recursively if needed. Returns path."""

        os.makedirs(path, exist_ok=True)

        return path

    @staticmethod

    def read_file(path: str) -> Optional[str]:

        """Read file content as string. Returns None on failure."""

        try:

            with open(path, "r", encoding="utf-8") as f:

                return f.read()

        except (OSError, IOError):

            return None

    @staticmethod

    def write_file(path: str, content: str) -> bool:

        """Write content to file, creating directories as needed. Returns success."""

        try:

            os.makedirs(os.path.dirname(path), exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:

                f.write(content)

            return True

        except (OSError, IOError):

            return False

    @staticmethod

    def read_json(path: str) -> Optional[Any]:

        """Read and parse JSON file. Returns None on failure."""

        try:

            with open(path, "r") as f:

                return json.load(f)

        except (OSError, json.JSONDecodeError):

            return None

    @staticmethod

    def write_json(path: str, data: Any) -> bool:

        """Write data as JSON to file. Returns success."""

        try:

            os.makedirs(os.path.dirname(path), exist_ok=True)

            with open(path, "w") as f:

                json.dump(data, f, indent=2)

            return True

        except (OSError, IOError):

            return False

    @staticmethod

    def truncate(text: str, max_len: int = 100) -> str:

        """Truncate text to max length with ellipsis."""

        if not text or len(text) <= max_len:

            return text or ""

        return text[:max_len - 3] + "..."

    @staticmethod

    def format_bytes(bytes_val: int) -> str:

        """Format bytes to human-readable string (B, KB, MB, GB, TB, PB)."""

        val = float(bytes_val)

        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:

            if val < 1024:

                return f"{val:.1f} {unit}"

            val /= 1024

        return f"{val:.1f} PB"

    @staticmethod

    def merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:

        """Deep merge two dictionaries."""

        merged = base.copy()

        for key, value in override.items():

            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):

                merged[key] = Helpers.merge_dicts(merged[key], value)

            else:

                merged[key] = value

        return merged

    @staticmethod

    def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:

        """Split a list into chunks of specified size."""

        return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]

    @staticmethod

    def unique(items: List[Any]) -> List[Any]:

        """Return unique items preserving order."""

        seen = set()

        result = []

        for item in items:

            if item not in seen:

                seen.add(item)

                result.append(item)

        return result

    @staticmethod

    def time_ago(dt: datetime) -> str:

        """Human-readable relative time string."""

        now = datetime.now()

        diff = now - dt

        seconds = int(diff.total_seconds())

        if seconds < 0:

            return "just now"

        if seconds < 60:

            return f"{seconds}s ago"

        minutes = seconds // 60

        if minutes < 60:

            return f"{minutes}m ago"

        hours = minutes // 60

        if hours < 24:

            return f"{hours}h ago"

        days = hours // 24

        if days < 30:

            return f"{days}d ago"

        months = days // 30

        if months < 12:

            return f"{months}mo ago"

        years = months // 12

        return f"{years}y ago"

    @staticmethod

    def slugify(text: str) -> str:

        """Convert text to URL-friendly slug."""

        slug = text.lower().strip()

        slug = re.sub(r'[^\w\s-]', '', slug)

        slug = re.sub(r'[-\s]+', '-', slug)

        return slug.strip('-')