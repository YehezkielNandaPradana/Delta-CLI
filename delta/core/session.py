# delta/core/session.py

"""

Session management for Delta.

Maintains conversation context, host state, and memory across commands.

"""

import json

import uuid

from datetime import datetime

from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field, asdict

from delta.core.database import Database

@dataclass

class ConversationMemory:

    """Represents a single conversation exchange."""

    role: str  # 'user' or 'assistant'

    message: str

    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass

class SessionContext:

    """

    Current session context with memory and state.

    Tracks the active host, recent commands, and conversation history.

    """

    working_directory: str = ""

    current_host: str = ""

    current_ports: str = ""

    last_command: str = ""

    last_result: str = ""

    scan_results: Dict[str, Any] = field(default_factory=dict)

    metadata: Dict[str, Any] = field(default_factory=dict)

    def update(self, **kwargs) -> None:

        """Update context fields."""

        for key, value in kwargs.items():

            if hasattr(self, key):

                setattr(self, key, value)

            else:

                self.metadata[key] = value

    def to_dict(self) -> Dict[str, Any]:

        """Convert to dictionary."""

        return {

            "working_directory": self.working_directory,

            "current_host": self.current_host,

            "current_ports": self.current_ports,

            "last_command": self.last_command,

            "last_result": self.last_result[:500] if self.last_result else "",

            "scan_results": self.scan_results,

            "metadata": self.metadata,

        }

class SessionManager:

    """

    Manages user sessions with persistent memory and context.

    Provides conversation history, host state tracking, and session persistence.

    """

    def __init__(self, database: Database):

        """

        Initialize session manager.

        Args:

            database: Database instance for persistence

        """

        self.database = database

        self.session_id: str = self._generate_session_id()

        self.context = SessionContext()

        self.conversation: List[ConversationMemory] = []

        self.max_history: int = 100

        # Load any existing session

        self._load_session()

    def _generate_session_id(self) -> str:

        """Generate unique session ID."""

        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    def _load_session(self) -> None:

        """Load session state from database."""

        current = self.database.get_session(self.session_id)

        if current:

            ctx = current.get("context", {})

            self.context = SessionContext(

                working_directory=ctx.get("working_directory", ""),

                current_host=ctx.get("current_host", ""),

                current_ports=ctx.get("current_ports", ""),

                last_command=ctx.get("last_command", ""),

                last_result=ctx.get("last_result", ""),

                scan_results=ctx.get("scan_results", {}),

                metadata=ctx.get("metadata", {}),

            )

    def save(self) -> None:

        """Save current session to database."""

        self.database.save_session(

            session_id=self.session_id,

            current_host=self.context.current_host,

            context=self.context.to_dict(),

        )

    def add_to_history(self, command: str, host: str = "",

                       status: str = "completed", result_summary: str = "") -> None:

        """Add command to history database."""

        self.database.add_history(

            command=command,

            host=host or self.context.current_host,

            status=status,

            result_summary=result_summary[:200],

        )

        # Update conversation memory

        self.context.last_command = command

        self.context.last_result = result_summary

        # Truncate conversation if too long

        if len(self.conversation) > self.max_history * 2:

            self.conversation = self.conversation[-self.max_history:]

    def add_conversation(self, role: str, message: str,

                         metadata: Optional[Dict[str, Any]] = None) -> None:

        """Add a conversation exchange."""

        mem = ConversationMemory(

            role=role,

            message=message,

            metadata=metadata or {},

        )

        self.conversation.append(mem)

    def get_recent_conversation(self, n: int = 10) -> List[ConversationMemory]:

        """Get last N conversation exchanges."""

        return self.conversation[-n:]

    def set_host(self, host: str) -> None:

        """Set current active host."""

        self.context.current_host = host

    def get_host(self) -> str:

        """Get current active host."""

        return self.context.current_host

    def set_scan_result(self, key: str, value: Dict[str, Any]) -> None:

        """Store a scan result."""

        self.context.scan_results[key] = value

    def get_scan_result(self, key: str) -> Optional[Dict[str, Any]]:

        """Get a stored scan result."""

        return self.context.scan_results.get(key)

    def clear_scan_results(self) -> None:

        """Clear all scan results."""

        self.context.scan_results.clear()

    def update_context(self, **kwargs) -> None:

        """Update session context."""

        self.context.update(**kwargs)

    def get_context_summary(self) -> str:

        """Get a human-readable summary of current context."""

        parts = []

        if self.context.current_host:

            parts.append(f"Current host: {self.context.current_host}")

        if self.context.current_ports:

            parts.append(f"Ports: {self.context.current_ports}")

        if self.context.last_command:

            parts.append(f"Last command: {self.context.last_command}")

        if self.context.scan_results:

            parts.append(f"Saved results: {len(self.context.scan_results)}")

        conv_count = len(self.conversation)

        if conv_count:

            parts.append(f"Conversation: {conv_count} exchanges")

        return " | ".join(parts) if parts else "No active context"

    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:

        """Get command history from database."""

        return self.database.get_history(limit=limit)

    def search_history(self, query: str) -> List[Dict[str, Any]]:

        """Search command history."""

        return self.database.search_history(query)

    def reset(self) -> None:

        """Reset session context."""

        self.context = SessionContext()

        self.conversation.clear()

        self.save()