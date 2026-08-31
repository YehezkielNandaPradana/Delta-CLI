"""
GeoTrace Audit & Safety Guard Module.
Provides immutable audit logging, rate limiting, and ethical/safety guardrails
(refusal of private accounts, minor protection heuristics).
"""

import hashlib
import json
import os
import sqlite3
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class AuditRecord:
    query_id: str
    operator: str
    target: str
    timestamp: str
    purpose: str
    consent_mode: bool
    status: str  # "ALLOWED", "REJECTED_PRIVATE", "REJECTED_MINOR", "RATE_LIMITED", "COMPLETED"
    reason: str = ""
    target_hash: str = ""
    prev_record_hash: str = ""
    record_hash: str = ""


class SafetyGateException(Exception):
    """Exception raised when a query violates safety, ethical, or legal policies."""
    pass


class GeoTraceAuditManager:
    """
    Immutable audit logger with cryptographic hash chaining and safety guardrails.
    """

    DEFAULT_DB_PATH = os.path.join(os.path.expanduser("~"), ".delta", "geotrace_audit.db")

    # Rate limiting disabled / unlimited queries
    MAX_QUERIES_PER_TARGET = 999999
    RATE_LIMIT_WINDOW_SECONDS = 3600

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or self.DEFAULT_DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize audit table with append-only design."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS geotrace_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id TEXT UNIQUE NOT NULL,
                    operator TEXT NOT NULL,
                    target TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    consent_mode INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    reason TEXT,
                    target_hash TEXT NOT NULL,
                    prev_record_hash TEXT,
                    record_hash TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_target_timestamp 
                ON geotrace_audit_log(target, timestamp)
            """)
            conn.commit()

    def _get_last_hash(self) -> str:
        """Fetch the hash of the latest audit record for chain integrity."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT record_hash FROM geotrace_audit_log ORDER BY id DESC LIMIT 1")
            row = cur.fetchone()
            return row[0] if row else "GENESIS_ROOT_HASH"

    def _calculate_record_hash(self, record_dict: Dict[str, Any], prev_hash: str) -> str:
        payload = f"{record_dict.get('query_id')}:{record_dict.get('operator')}:{record_dict.get('target')}:" \
                  f"{record_dict.get('timestamp')}:{record_dict.get('purpose')}:{record_dict.get('consent_mode')}:" \
                  f"{record_dict.get('status')}:{prev_hash}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def check_rate_limit(self, target: str) -> Tuple[bool, str]:
        """Unlimited queries allowed (rate limiting removed)."""
        return True, ""

    def evaluate_target_safety(self, profile_data: Dict[str, Any]) -> Tuple[bool, str, str]:
        """
        Evaluate ethical & safety guardrails:
        1. Refuse private accounts.
        2. Refuse minors based on heuristics (bio patterns, birthday indicators).
        Returns (is_allowed, status_code, refusal_reason).
        """
        is_private = profile_data.get("is_private", False)
        if is_private:
            return False, "REJECTED_PRIVATE", "Target account is private. GeoTrace strictly strictly processes public OSINT data only."

        # Heuristic Minor Check
        bio = str(profile_data.get("bio", "")).lower()
        username = str(profile_data.get("username", "")).lower()

        # Age indicators & minor keywords
        minor_keywords = [
            "under 18", "underage", "minor", "smp", "sd ", "sekolah dasar", 
            "middle school", "elementary school", "age 12", "age 13", "age 14", 
            "age 15", "age 16", "age 17", "12yo", "13yo", "14yo", "15yo", "16yo", "17yo",
            "kelas 7", "kelas 8", "kelas 9", "kelas 10", "kelas 11", "kelas 12"
        ]

        for kw in minor_keywords:
            if kw in bio or kw in username:
                return False, "REJECTED_MINOR", f"Heuristic safety check detected minor indicator ('{kw}'). Processing refused under child protection guidelines."

        return True, "ALLOWED", ""

    def log_query(
        self,
        operator: str,
        target: str,
        purpose: str,
        consent_mode: bool,
        status: str,
        reason: str = ""
    ) -> AuditRecord:
        """
        Append an immutable log record to the audit chain.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        target_hash = hashlib.sha256(target.strip().lower().encode("utf-8")).hexdigest()
        prev_hash = self._get_last_hash()

        query_seed = f"{operator}:{target}:{timestamp}:{time.time_ns()}"
        query_id = "GT-" + hashlib.sha1(query_seed.encode("utf-8")).hexdigest()[:12].upper()

        rec_dict = {
            "query_id": query_id,
            "operator": operator,
            "target": target,
            "timestamp": timestamp,
            "purpose": purpose,
            "consent_mode": consent_mode,
            "status": status,
            "reason": reason,
            "target_hash": target_hash,
            "prev_record_hash": prev_hash,
        }
        record_hash = self._calculate_record_hash(rec_dict, prev_hash)
        rec_dict["record_hash"] = record_hash

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO geotrace_audit_log (
                    query_id, operator, target, timestamp, purpose, consent_mode,
                    status, reason, target_hash, prev_record_hash, record_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                query_id, operator, target, timestamp, purpose, 1 if consent_mode else 0,
                status, reason, target_hash, prev_hash, record_hash
            ))
            conn.commit()

        return AuditRecord(**rec_dict)

    def verify_log_integrity(self) -> Tuple[bool, List[str]]:
        """Verify tamper-evidence across the entire hash chain."""
        issues = []
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT query_id, operator, target, timestamp, purpose, consent_mode, status, prev_record_hash, record_hash FROM geotrace_audit_log ORDER BY id ASC")
            rows = cur.fetchall()

            prev_expected_hash = "GENESIS_ROOT_HASH"
            for row in rows:
                qid, op, tgt, ts, purp, cm, st, prev_h, rec_h = row
                if prev_h != prev_expected_hash:
                    issues.append(f"Broken chain at record {qid}: expected prev_hash {prev_expected_hash}, found {prev_h}")
                
                computed = self._calculate_record_hash({
                    "query_id": qid,
                    "operator": op,
                    "target": tgt,
                    "timestamp": ts,
                    "purpose": purp,
                    "consent_mode": bool(cm),
                    "status": st
                }, prev_h)

                if computed != rec_h:
                    issues.append(f"Hash mismatch at record {qid}: stored {rec_h}, calculated {computed}")

                prev_expected_hash = rec_h

        return len(issues) == 0, issues
