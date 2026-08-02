# delta/ai/context.py

"""

Context Manager for Delta - maintains conversation context and session memory.

"""

from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field

from datetime import datetime

@dataclass

class ContextEntry:

    """A single context entry with metadata."""

    key: str

    value: Any

    source: str = "user"

    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    ttl: Optional[int] = None  # Time-to-live in seconds

class ContextManager:

    """

    Manages conversation context with automatic memory decay.

    Provides context-aware responses and maintains session state.

    """

    def __init__(self, max_entries: int = 100):

        self.max_entries = max_entries

        self._entries: Dict[str, ContextEntry] = {}

        self._history: List[ContextEntry] = []

    def set(self, key: str, value: Any, source: str = "system", ttl: Optional[int] = None) -> None:

        """Set a context value."""

        entry = ContextEntry(key=key, value=value, source=source, ttl=ttl)

        self._entries[key] = entry

        self._history.append(entry)

        self._trim()

    def get(self, key: str, default: Any = None) -> Any:

        """Get a context value."""

        entry = self._entries.get(key)

        if entry is None:

            return default

        if entry.ttl and self._is_expired(entry):

            del self._entries[key]

            return default

        return entry.value

    def get_all(self) -> Dict[str, Any]:

        """Get all non-expired context entries."""

        result = {}

        to_delete = []

        for key, entry in self._entries.items():

            if entry.ttl and self._is_expired(entry):

                to_delete.append(key)

            else:

                result[key] = entry.value

        for key in to_delete:

            del self._entries[key]

        return result

    def clear(self) -> None:

        """Clear all context and history."""

        self._entries.clear()

        self._history.clear()

    def _is_expired(self, entry: ContextEntry) -> bool:

        """Check if entry is expired."""

        if entry.ttl is None:

            return False

        created = datetime.fromisoformat(entry.timestamp)

        elapsed = (datetime.now() - created).total_seconds()

        return elapsed > entry.ttl

    def _trim(self) -> None:

        """Trim history to max entries."""

        if len(self._history) > self.max_entries:

            self._history = self._history[-self.max_entries:]

        if len(self._entries) > self.max_entries:

            # Remove oldest entries

            keys = list(self._entries.keys())

            for key in keys[:len(keys) - self.max_entries]:

                del self._entries[key]