# -*- coding: utf-8 -*-
"""
Runtime database — human decisions and the audit log.

Deliberately a SEPARATE SQLite file from data/investigateiq.db. The main
database is rebuilt from scratch on every deploy (see build_database.py /
railway.json's preDeployCommand) — that's correct for reference data, but
would silently destroy every investigator decision and every audit entry if
they lived in the same file. Keeping them apart means a bug or change in the
rebuild step can never wipe real decisions, by construction, not by care.

Storage location:
- In production (Railway), this file lives on a mounted persistent volume
  at /app/runtime_data — survives deploys and restarts, unlike the rest of
  the container's filesystem.
- Locally (no volume mounted), it falls back to data/investigateiq_runtime.db
  next to the main database.

Tables match the AIReport / HumanAction / AuditLog entities in the documented
data model (Product Docs/07-Data-Requirements.md).
"""
import json
import os
import sqlite3
import uuid
import datetime

_VOLUME_DIR = "/app/runtime_data"
if os.path.isdir(_VOLUME_DIR):
    RUNTIME_DB_PATH = os.path.join(_VOLUME_DIR, "investigateiq_runtime.db")
else:
    RUNTIME_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "investigateiq_runtime.db")


def _connect():
    conn = sqlite3.connect(RUNTIME_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_runtime_db():
    """Idempotent — creates tables only if they don't already exist. Never
    drops or recreates anything, so it's safe to call on every app startup."""
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            event_id TEXT PRIMARY KEY,
            case_id TEXT NOT NULL,
            actor TEXT NOT NULL,           -- 'ai' | 'human' | 'system'
            actor_name TEXT,
            action TEXT NOT NULL,
            details TEXT,                   -- JSON blob
            timestamp TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS human_actions (
            action_id TEXT PRIMARY KEY,
            case_id TEXT NOT NULL,
            investigator TEXT NOT NULL,
            action TEXT NOT NULL,           -- 'close' | 'request_info' | 'escalate'
            rationale TEXT NOT NULL,
            findings_accepted TEXT,          -- JSON list
            findings_rejected TEXT,          -- JSON list
            timestamp TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_case ON audit_log(case_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_actions_case ON human_actions(case_id)")
    conn.commit()
    conn.close()


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def log_audit_event(case_id: str, actor: str, action: str, actor_name: str | None = None, details: dict | None = None):
    """actor: 'ai' | 'human' | 'system'. Append-only — this function never
    updates or deletes an existing row."""
    init_runtime_db()
    conn = _connect()
    conn.execute(
        "INSERT INTO audit_log (event_id, case_id, actor, actor_name, action, details, timestamp) VALUES (?,?,?,?,?,?,?)",
        (f"AUD-{uuid.uuid4().hex[:10]}", case_id, actor, actor_name, action,
         json.dumps(details, default=str) if details else None, _now()),
    )
    conn.commit()
    conn.close()


def record_human_decision(case_id: str, investigator: str, action: str, rationale: str,
                           findings_accepted: list, findings_rejected: list):
    """Records the decision AND writes the corresponding audit entry in one
    call — a human decision without an audit trail entry should not be
    possible through this code path."""
    if not rationale or not rationale.strip():
        raise ValueError("A rationale is required to record a human decision (BR4).")

    init_runtime_db()
    conn = _connect()
    action_id = f"HACT-{uuid.uuid4().hex[:10]}"
    ts = _now()
    conn.execute(
        """INSERT INTO human_actions
           (action_id, case_id, investigator, action, rationale, findings_accepted, findings_rejected, timestamp)
           VALUES (?,?,?,?,?,?,?,?)""",
        (action_id, case_id, investigator, action, rationale,
         json.dumps(findings_accepted, default=str), json.dumps(findings_rejected, default=str), ts),
    )
    conn.commit()
    conn.close()

    log_audit_event(
        case_id, actor="human", actor_name=investigator, action=f"decision: {action}",
        details={"rationale": rationale, "findings_accepted": len(findings_accepted), "findings_rejected": len(findings_rejected)},
    )
    return action_id


def get_audit_log(case_id: str) -> list:
    init_runtime_db()
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM audit_log WHERE case_id = ? ORDER BY timestamp", (case_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_human_actions(case_id: str) -> list:
    init_runtime_db()
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM human_actions WHERE case_id = ? ORDER BY timestamp", (case_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
