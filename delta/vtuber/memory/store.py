"""
SQLite-backed Persistent Storage for Delta VTuber Long-term Memory.
"""

import json
import logging
import os
import sqlite3
from typing import Any, Dict, List, Optional
from delta.vtuber.memory.schemas import MemoryEntry, MemoryType
from delta.vtuber.memory.security import SecretFilter

logger = logging.getLogger(__name__)


class SQLiteMemoryStore:
    """
    Thread-safe SQLite storage for durable user facts, preferences, and long-term notes.
    """

    def __init__(self, db_path: Optional[str] = None):
        if not db_path:
            base_dir = os.path.join(os.path.expanduser("~"), ".delta")
            os.makedirs(base_dir, exist_ok=True)
            self.db_path = os.path.join(base_dir, "vtuber_memory.db")
        else:
            self.db_path = db_path

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS vtuber_memories (
                    id TEXT PRIMARY KEY,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL,
                    importance REAL DEFAULT 0.5,
                    source TEXT DEFAULT 'user',
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    last_accessed REAL NOT NULL,
                    expires_at REAL,
                    metadata TEXT
                )
            """)
            # Migration check: ensure required columns exist if table was created in older schema
            cur.execute("PRAGMA table_info(vtuber_memories)")
            columns = [row[1] for row in cur.fetchall()]
            if "source" not in columns:
                cur.execute("ALTER TABLE vtuber_memories ADD COLUMN source TEXT DEFAULT 'user'")
            if "updated_at" not in columns:
                cur.execute("ALTER TABLE vtuber_memories ADD COLUMN updated_at REAL DEFAULT 0")
            if "last_accessed" not in columns:
                cur.execute("ALTER TABLE vtuber_memories ADD COLUMN last_accessed REAL DEFAULT 0")
            if "expires_at" not in columns:
                cur.execute("ALTER TABLE vtuber_memories ADD COLUMN expires_at REAL")
            if "metadata" not in columns:
                cur.execute("ALTER TABLE vtuber_memories ADD COLUMN metadata TEXT DEFAULT '{}'")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_mem_type ON vtuber_memories(memory_type)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_mem_cat ON vtuber_memories(category)")
            conn.commit()

    def store(self, entry: MemoryEntry) -> bool:
        """
        Store a new memory entry with strict credential filtering.
        """
        if SecretFilter.contains_secrets(entry.content):
            logger.warning("Rejected memory storage: content contains credential or API key pattern.")
            return False

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO vtuber_memories
                (id, memory_type, content, category, importance, source, created_at, updated_at, last_accessed, expires_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.id,
                entry.memory_type.value,
                entry.content,
                entry.category,
                entry.importance,
                entry.source,
                entry.created_at,
                entry.updated_at,
                entry.last_accessed,
                entry.expires_at,
                json.dumps(entry.metadata),
            ))
            conn.commit()
        return True

    def cleanup_expired(self) -> int:
        """Purge temporary memories that have exceeded their expires_at timestamp."""
        import time
        now = time.time()
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM vtuber_memories WHERE expires_at IS NOT NULL AND expires_at < ?", (now,))
            conn.commit()
            return cur.rowcount

    def retrieve(
        self,
        query: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        category: Optional[str] = None,
        limit: int = 10,
    ) -> List[MemoryEntry]:
        """
        Retrieve memories matching keyword query, memory_type, and/or category.
        """
        self.cleanup_expired()
        import time
        now = time.time()

        with self._get_connection() as conn:
            cur = conn.cursor()
            sql = "SELECT id, memory_type, content, category, importance, source, created_at, updated_at, last_accessed, expires_at, metadata FROM vtuber_memories"
            params = []
            clauses = []

            if memory_type:
                clauses.append("memory_type = ?")
                params.append(memory_type.value)

            if category:
                clauses.append("category = ?")
                params.append(category)

            if query and query.strip():
                clauses.append("content LIKE ?")
                params.append(f"%{query.strip()}%")

            if clauses:
                sql += " WHERE " + " AND ".join(clauses)

            sql += " ORDER BY importance DESC, created_at DESC LIMIT ?"
            params.append(limit)

            cur.execute(sql, tuple(params))
            rows = cur.fetchall()

            results: List[MemoryEntry] = []
            for r in rows:
                meta = json.loads(r[10]) if r[10] else {}
                results.append(
                    MemoryEntry(
                        id=r[0],
                        memory_type=MemoryType(r[1]),
                        content=r[2],
                        category=r[3],
                        importance=float(r[4]),
                        source=r[5] or "user",
                        created_at=float(r[6]),
                        updated_at=float(r[7]),
                        last_accessed=float(r[8]),
                        expires_at=float(r[9]) if r[9] is not None else None,
                        metadata=meta,
                    )
                )
            return results

    def delete(self, memory_id: str) -> bool:
        """Delete specific memory entry by id."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM vtuber_memories WHERE id = ?", (memory_id,))
            conn.commit()
            return cur.rowcount > 0

    def delete_by_query(self, query: str) -> int:
        """Delete memories containing query substring."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM vtuber_memories WHERE content LIKE ?", (f"%{query.strip()}%",))
            conn.commit()
            return cur.rowcount

    def clear_all(self) -> None:
        """Clear all stored long-term memories."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM vtuber_memories")
            conn.commit()
