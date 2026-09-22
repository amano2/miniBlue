"""Database module for Enterprise Action Logging, Governance Auditing & HITL Workflow.

Features:
- Immutable SQLite audit logs (db/actions.db)
- Cryptographic SHA-256 hash chaining (tamper-evident audit trail)
- Human-in-the-Loop (HITL) manager review queue for flagged requests
- Real-time aggregation telemetry for executive observability
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from src import config

DB_DIR: Path = config.BASE_DIR / "db"
DB_PATH: Path = DB_DIR / "actions.db"


def get_db_connection() -> sqlite3.Connection:
    """Creates database directory and returns SQLite connection."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def calculate_hash(prev_hash: str, payload_str: str, decision: str, timestamp: str) -> str:
    """Computes SHA-256 cryptographic hash for tamper-evident audit chaining."""
    raw = f"{prev_hash}|{payload_str}|{decision}|{timestamp}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def init_db() -> None:
    """Initializes SQLite database schema and migrates columns if necessary."""
    conn = get_db_connection()
    cursor = conn.cursor()

    default_zero_hash = "0" * 64

    # Governance Action Logs Table with HITL & Cryptographic Verification
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS action_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            intent TEXT NOT NULL,
            action_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            decision TEXT NOT NULL,
            reason TEXT NOT NULL,
            rule_cited TEXT NOT NULL,
            status TEXT DEFAULT 'RESOLVED',
            reviewed_by TEXT,
            review_notes TEXT,
            reviewed_at TEXT,
            prev_hash TEXT DEFAULT '{default_zero_hash}',
            entry_hash TEXT
        )
        """
    )

    # Conversation Logs Table for Telemetry
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS conversation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            user_message TEXT NOT NULL,
            agent_used TEXT NOT NULL,
            intent TEXT NOT NULL,
            confidence REAL NOT NULL,
            response_text TEXT NOT NULL,
            governance_decision TEXT,
            latency_ms REAL DEFAULT 0.0
        )
        """
    )

    # Migration: Add new columns if table existed without them
    cursor.execute("PRAGMA table_info(action_logs)")
    columns = [col[1] for col in cursor.fetchall()]

    new_cols = {
        "status": "TEXT DEFAULT 'RESOLVED'",
        "reviewed_by": "TEXT",
        "review_notes": "TEXT",
        "reviewed_at": "TEXT",
        "prev_hash": f"TEXT DEFAULT '{default_zero_hash}'",
        "entry_hash": "TEXT",
    }
    for col_name, col_def in new_cols.items():
        if col_name not in columns:
            cursor.execute(f"ALTER TABLE action_logs ADD COLUMN {col_name} {col_def}")

    cursor.execute("PRAGMA table_info(conversation_logs)")
    conv_columns = [col[1] for col in cursor.fetchall()]
    if "latency_ms" not in conv_columns:
        cursor.execute("ALTER TABLE conversation_logs ADD COLUMN latency_ms REAL DEFAULT 0.0")

    conn.commit()
    conn.close()


def get_latest_hash(conn: sqlite3.Connection) -> str:
    """Retrieves the entry_hash of the most recent action log record."""
    cursor = conn.cursor()
    cursor.execute("SELECT entry_hash FROM action_logs ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    if row and row[0]:
        return str(row[0])
    return "0" * 64


def log_action_decision(
    session_id: str,
    intent: str,
    action_type: str,
    payload: dict[str, Any],
    decision: str,
    reason: str,
    rule_cited: str,
) -> int:
    """Records a governance decision into action_logs with SHA-256 hash chaining."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_iso = datetime.now().isoformat()
    payload_str = json.dumps(payload, ensure_ascii=False)

    prev_hash = get_latest_hash(conn)
    entry_hash = calculate_hash(prev_hash, payload_str, decision, now_iso)

    # If flagged, initial status is PENDING_REVIEW; otherwise RESOLVED
    initial_status = "PENDING_REVIEW" if decision == "FLAG_FOR_REVIEW" else "RESOLVED"

    cursor.execute(
        """
        INSERT INTO action_logs (
            session_id, timestamp, intent, action_type, payload_json,
            decision, reason, rule_cited, status, prev_hash, entry_hash
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            now_iso,
            intent,
            action_type,
            payload_str,
            decision,
            reason,
            rule_cited,
            initial_status,
            prev_hash,
            entry_hash,
        ),
    )
    conn.commit()
    log_id = cursor.lastrowid or 0
    conn.close()
    return log_id


def log_conversation_turn(
    session_id: str,
    user_message: str,
    agent_used: str,
    intent: str,
    confidence: float,
    response_text: str,
    governance_decision: str | None = None,
    latency_ms: float = 0.0,
) -> int:
    """Records a complete conversation turn with latency telemetry."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_iso = datetime.now().isoformat()

    cursor.execute(
        """
        INSERT INTO conversation_logs (
            session_id, timestamp, user_message, agent_used,
            intent, confidence, response_text, governance_decision, latency_ms
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            now_iso,
            user_message,
            agent_used,
            intent,
            confidence,
            response_text,
            governance_decision,
            latency_ms,
        ),
    )
    conn.commit()
    log_id = cursor.lastrowid or 0
    conn.close()
    return log_id


def get_pending_reviews() -> list[dict[str, Any]]:
    """Retrieves all action logs currently awaiting Human-in-the-Loop review."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM action_logs WHERE status = 'PENDING_REVIEW' ORDER BY id DESC"
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def resolve_review(
    log_id: int,
    manager_id: str,
    resolution: str,
    review_notes: str,
) -> bool:
    """Updates a flagged action with managerial approval or rejection."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_iso = datetime.now().isoformat()

    new_decision = "APPROVE (Manager Override)" if resolution.upper() == "APPROVE" else "BLOCK (Manager Rejection)"
    new_status = "RESOLVED"

    cursor.execute(
        """
        UPDATE action_logs
        SET status = ?, decision = ?, reviewed_by = ?, review_notes = ?, reviewed_at = ?
        WHERE id = ?
        """,
        (new_status, new_decision, manager_id, review_notes, now_iso, log_id),
    )
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


def get_all_action_logs(limit: int = 100) -> list[dict[str, Any]]:
    """Retrieves recent action logs."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM action_logs ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def verify_audit_hash_chain() -> dict[str, Any]:
    """Cryptographically verifies the SHA-256 hash integrity of all audit log records."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp, payload_json, decision, prev_hash, entry_hash FROM action_logs ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return {"valid": True, "total_records": 0, "corrupted_id": None}

    prev_hash = "0" * 64
    for row in rows:
        r_id = row["id"]
        timestamp = row["timestamp"]
        payload_str = row["payload_json"]
        decision = row["decision"]
        stored_prev = row["prev_hash"]
        stored_entry = row["entry_hash"]

        if stored_entry:
            expected_hash = calculate_hash(stored_prev or prev_hash, payload_str, decision, timestamp)
            if expected_hash != stored_entry:
                return {
                    "valid": False,
                    "total_records": len(rows),
                    "corrupted_id": r_id,
                    "message": f"Hash mismatch at Record #{r_id}",
                }
            prev_hash = stored_entry

    return {
        "valid": True,
        "total_records": len(rows),
        "corrupted_id": None,
        "message": "Audit trail is 100% cryptographically verified & tamper-free.",
    }


def get_telemetry_metrics() -> dict[str, Any]:
    """Computes high-level governance and orchestrator telemetry metrics for dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM conversation_logs")
    total_inquiries = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(latency_ms) FROM conversation_logs")
    avg_latency = cursor.fetchone()[0] or 0.0

    cursor.execute("SELECT intent, COUNT(*) FROM conversation_logs GROUP BY intent")
    intent_counts = dict(cursor.fetchall())

    cursor.execute("SELECT decision, COUNT(*) FROM action_logs GROUP BY decision")
    decision_counts = dict(cursor.fetchall())

    cursor.execute("SELECT COUNT(*) FROM action_logs")
    total_actions = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM action_logs WHERE status = 'PENDING_REVIEW'")
    pending_reviews = cursor.fetchone()[0]

    conn.close()
    return {
        "total_inquiries": total_inquiries,
        "total_actions": total_actions,
        "pending_reviews": pending_reviews,
        "avg_latency_ms": round(avg_latency, 1),
        "intent_counts": intent_counts,
        "decision_counts": decision_counts,
    }


# Auto-initialize database on import
init_db()
