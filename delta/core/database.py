# delta/core/database.py

"""

Database management for Delta.

Uses SQLite for persistent storage of history, hosts, reports, sessions, and knowledge.

"""

import sqlite3

import json

import os

from datetime import datetime

from dataclasses import dataclass, field, asdict

from typing import Any, Dict, List, Optional, Tuple

from pathlib import Path

@dataclass

class HistoryEntry:

    """Represents a command history entry."""

    id: Optional[int] = None

    command: str = ""

    timestamp: str = ""

    host: str = ""

    status: str = ""

    result_summary: str = ""

@dataclass

class HostEntry:

    """Represents a scanned host entry."""

    id: Optional[int] = None

    host: str = ""

    ip: str = ""

    hostname: str = ""

    open_ports: str = ""

    services: str = ""

    os: str = ""

    first_seen: str = ""

    last_scanned: str = ""

    notes: str = ""

    risk_level: str = "unknown"

@dataclass

class ReportEntry:

    """Represents a generated report entry."""

    id: Optional[int] = None

    title: str = ""

    host: str = ""

    report_type: str = ""

    severity: str = ""

    content: str = ""

    format: str = "markdown"

    created_at: str = ""

    file_path: str = ""

@dataclass

class SessionEntry:

    """Represents a session state entry."""

    id: Optional[int] = None

    session_id: str = ""

    current_host: str = ""

    context: str = ""

    created_at: str = ""

    updated_at: str = ""

class Database:

    """

    SQLite database manager with context manager support.

    Provides CRUD operations for all Delta data types.

    """

    def __init__(self, db_path: str = ":memory:"):

        """

        Initialize database connection.

        Args:

            db_path: Path to SQLite database file. Use ":memory:" for in-memory.

        """

        self.db_path = db_path

        self.connection: Optional[sqlite3.Connection] = None

        self.cursor: Optional[sqlite3.Cursor] = None

    def initialize(self) -> None:

        """Initialize database and create tables if they don't exist."""

        os.makedirs(os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else ".", exist_ok=True)

        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)

        self.connection.row_factory = sqlite3.Row

        self.connection.execute("PRAGMA journal_mode=WAL")

        self.connection.execute("PRAGMA synchronous=NORMAL")

        self.connection.execute("PRAGMA foreign_keys=ON")

        self.cursor = self.connection.cursor()

        self._create_tables()

    def _create_tables(self) -> None:

        """Create all database tables."""

        create_history = """

        CREATE TABLE IF NOT EXISTS history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            command TEXT NOT NULL,

            timestamp TEXT NOT NULL DEFAULT (datetime('now')),

            host TEXT DEFAULT '',

            status TEXT DEFAULT 'completed',

            result_summary TEXT DEFAULT ''

        )

        """

        create_hosts = """

        CREATE TABLE IF NOT EXISTS hosts (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            host TEXT NOT NULL,

            ip TEXT DEFAULT '',

            hostname TEXT DEFAULT '',

            open_ports TEXT DEFAULT '',

            services TEXT DEFAULT '',

            os TEXT DEFAULT '',

            first_seen TEXT NOT NULL DEFAULT (datetime('now')),

            last_scanned TEXT NOT NULL DEFAULT (datetime('now')),

            notes TEXT DEFAULT '',

            risk_level TEXT DEFAULT 'unknown',

            UNIQUE(host)

        )

        """

        create_reports = """

        CREATE TABLE IF NOT EXISTS reports (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT NOT NULL,

            host TEXT DEFAULT '',

            report_type TEXT DEFAULT 'scan',

            severity TEXT DEFAULT 'info',

            content TEXT DEFAULT '',

            format TEXT DEFAULT 'markdown',

            created_at TEXT NOT NULL DEFAULT (datetime('now')),

            file_path TEXT DEFAULT ''

        )

        """

        create_sessions = """

        CREATE TABLE IF NOT EXISTS sessions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            session_id TEXT UNIQUE NOT NULL,

            current_host TEXT DEFAULT '',

            context TEXT DEFAULT '{}',

            created_at TEXT NOT NULL DEFAULT (datetime('now')),

            updated_at TEXT NOT NULL DEFAULT (datetime('now'))

        )

        """

        create_knowledge = """

        CREATE TABLE IF NOT EXISTS knowledge (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            key TEXT UNIQUE NOT NULL,

            value TEXT NOT NULL,

            category TEXT DEFAULT 'general',

            updated_at TEXT NOT NULL DEFAULT (datetime('now'))

        )

        """

        for sql in [create_history, create_hosts, create_reports, create_sessions, create_knowledge]:

            self.cursor.execute(sql)

        self.connection.commit()

    # --- History operations ---

    def add_history(self, command: str, host: str = "",

                    status: str = "completed", result_summary: str = "") -> int:

        """Add a command to history."""

        self.cursor.execute(

            "INSERT INTO history (command, host, status, result_summary) VALUES (?, ?, ?, ?)",

            (command, host, status, result_summary)

        )

        self.connection.commit()

        return self.cursor.lastrowid

    def get_history(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:

        """Get command history."""

        self.cursor.execute(

            "SELECT * FROM history ORDER BY id DESC LIMIT ? OFFSET ?",

            (limit, offset)

        )

        return [dict(row) for row in self.cursor.fetchall()]

    def search_history(self, query: str) -> List[Dict[str, Any]]:

        """Search command history."""

        self.cursor.execute(

            "SELECT * FROM history WHERE command LIKE ? ORDER BY id DESC LIMIT 50",

            (f"%{query}%",)

        )

        return [dict(row) for row in self.cursor.fetchall()]

    def clear_history(self) -> None:

        """Clear all history."""

        self.cursor.execute("DELETE FROM history")

        self.connection.commit()

    # --- Host operations ---

    def upsert_host(self, host: str, **kwargs) -> int:

        """Insert or update a host record."""

        existing = self.get_host(host)

        if existing:

            fields = []

            values = []

            for key, value in kwargs.items():

                if key != "id" and hasattr(HostEntry, key):

                    fields.append(f"{key} = ?")

                    values.append(value)

            fields.append("last_scanned = datetime('now')")

            values.append(host)

            self.cursor.execute(

                f"UPDATE hosts SET {', '.join(fields)} WHERE host = ?",

                values

            )

        else:

            fields = ["host"] + [k for k in kwargs if hasattr(HostEntry, k)]

            placeholders = ["?"] * len(fields)

            values = [host] + [kwargs.get(k, "") for k in fields[1:]]

            self.cursor.execute(

                f"INSERT INTO hosts ({', '.join(fields)}) VALUES ({', '.join(placeholders)})",

                values

            )

        self.connection.commit()

        return self.cursor.lastrowid

    def get_host(self, host: str) -> Optional[Dict[str, Any]]:

        """Get a host by name/IP."""

        self.cursor.execute("SELECT * FROM hosts WHERE host = ?", (host,))

        row = self.cursor.fetchone()

        return dict(row) if row else None

    def get_all_hosts(self) -> List[Dict[str, Any]]:

        """Get all hosts."""

        self.cursor.execute("SELECT * FROM hosts ORDER BY last_scanned DESC")

        return [dict(row) for row in self.cursor.fetchall()]

    def delete_host(self, host: str) -> bool:

        """Delete a host record."""

        self.cursor.execute("DELETE FROM hosts WHERE host = ?", (host,))

        self.connection.commit()

        return self.cursor.rowcount > 0

    # --- Report operations ---

    def save_report(self, title: str, host: str = "", report_type: str = "scan",

                    severity: str = "info", content: str = "",

                    format: str = "markdown", file_path: str = "") -> int:

        """Save a report."""

        self.cursor.execute(

            "INSERT INTO reports (title, host, report_type, severity, content, format, file_path) "

            "VALUES (?, ?, ?, ?, ?, ?, ?)",

            (title, host, report_type, severity, content, format, file_path)

        )

        self.connection.commit()

        return self.cursor.lastrowid

    def get_reports(self, limit: int = 20) -> List[Dict[str, Any]]:

        """Get all reports."""

        self.cursor.execute(

            "SELECT * FROM reports ORDER BY created_at DESC LIMIT ?", (limit,)

        )

        return [dict(row) for row in self.cursor.fetchall()]

    def get_report(self, report_id: int) -> Optional[Dict[str, Any]]:

        """Get a specific report."""

        self.cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))

        row = self.cursor.fetchone()

        return dict(row) if row else None

    # --- Session operations ---

    def save_session(self, session_id: str, current_host: str = "",

                     context: Optional[Dict[str, Any]] = None) -> None:

        """Save or update a session."""

        context_json = json.dumps(context or {})

        self.cursor.execute(

            "INSERT OR REPLACE INTO sessions (session_id, current_host, context, updated_at) "

            "VALUES (?, ?, ?, datetime('now'))",

            (session_id, current_host, context_json)

        )

        self.connection.commit()

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:

        """Get a session by ID."""

        self.cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))

        row = self.cursor.fetchone()

        if row:

            result = dict(row)

            try:

                result["context"] = json.loads(result["context"])

            except (json.JSONDecodeError, TypeError):

                result["context"] = {}

            return result

        return None

    # --- Knowledge operations ---

    def save_knowledge(self, key: str, value: str, category: str = "general") -> None:

        """Save a knowledge entry."""

        self.cursor.execute(

            "INSERT OR REPLACE INTO knowledge (key, value, category, updated_at) "

            "VALUES (?, ?, ?, datetime('now'))",

            (key, value, category)

        )

        self.connection.commit()

    def get_knowledge(self, key: str) -> Optional[str]:

        """Get a knowledge entry by key."""

        self.cursor.execute("SELECT value FROM knowledge WHERE key = ?", (key,))

        row = self.cursor.fetchone()

        return row["value"] if row else None

    def search_knowledge(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:

        """Search knowledge base."""

        if category:

            self.cursor.execute(

                "SELECT * FROM knowledge WHERE (key LIKE ? OR value LIKE ?) AND category = ? LIMIT 50",

                (f"%{query}%", f"%{query}%", category)

            )

        else:

            self.cursor.execute(

                "SELECT * FROM knowledge WHERE key LIKE ? OR value LIKE ? LIMIT 50",

                (f"%{query}%", f"%{query}%")

            )

        return [dict(row) for row in self.cursor.fetchall()]

    def close(self) -> None:

        """Close database connection."""

        if self.connection:

            self.connection.close()

    def __enter__(self) -> "Database":

        """Context manager entry."""

        if not self.connection:

            self.initialize()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:

        """Context manager exit."""

        self.close()