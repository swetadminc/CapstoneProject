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


_initialized = False


def init_runtime_db():
    """Idempotent — creates tables only if they don't already exist. Never
    drops or recreates anything, so it's safe to call on every app startup.

    Every write/read function below called this unconditionally, which meant
    a full connect + 4x CREATE TABLE IF NOT EXISTS + 2x CREATE INDEX IF NOT
    EXISTS + commit + close on every single audit-log write — and the
    multi-agent split (pending item #5) took audit events per investigation
    from 3 to 8, nearly tripling that overhead. The DDL is idempotent within
    a process either way, so a process-lifetime guard changes nothing about
    correctness — it just stops re-running the same six no-op statements on
    every call."""
    global _initialized
    if _initialized:
        return
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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rule_config (
            rule_id TEXT NOT NULL,
            param_name TEXT NOT NULL,
            param_value REAL NOT NULL,
            updated_by TEXT,
            updated_at TEXT,
            PRIMARY KEY (rule_id, param_name)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_case ON audit_log(case_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_actions_case ON human_actions(case_id)")
    conn.commit()
    conn.close()
    _initialized = True


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _insert_audit_event(conn, case_id: str, actor: str, action: str,
                        actor_name: str | None = None, details: dict | None = None,
                        timestamp: str | None = None):
    """Insert on the caller's connection so related writes can be atomic."""
    conn.execute(
        "INSERT INTO audit_log (event_id, case_id, actor, actor_name, action, details, timestamp) VALUES (?,?,?,?,?,?,?)",
        (f"AUD-{uuid.uuid4().hex[:10]}", case_id, actor, actor_name, action,
         json.dumps(details, default=str) if details else None, timestamp or _now()),
    )


def log_audit_event(case_id: str, actor: str, action: str, actor_name: str | None = None, details: dict | None = None):
    """actor: 'ai' | 'human' | 'system'. Append-only — this function never
    updates or deletes an existing row."""
    init_runtime_db()
    conn = _connect()
    try:
        with conn:
            _insert_audit_event(conn, case_id, actor, action, actor_name, details)
    finally:
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
    try:
        # Serialize the state check and write so a stale second browser tab
        # cannot silently append another decision to the same workflow step.
        conn.execute("BEGIN IMMEDIATE")
        latest = conn.execute(
            "SELECT action FROM human_actions WHERE case_id=? "
            "ORDER BY timestamp DESC, rowid DESC LIMIT 1", (case_id,)
        ).fetchone()
        previous = latest["action"] if latest else None
        investigator_actions = {"close", "request_info", "escalate"}
        compliance_actions = {"compliance_ack", "compliance_return", "compliance_refer"}
        if action in investigator_actions:
            if previous not in (None, "compliance_return"):
                raise ValueError("A human action is already recorded for this case. "
                                 "The existing decision is read-only; a new investigator action "
                                 "requires a recorded Compliance return.")
        elif action in compliance_actions:
            if previous != "escalate":
                raise ValueError("A Compliance action requires a current investigator escalation.")
        else:
            raise ValueError("Unknown human action.")
        with conn:
            conn.execute(
                """INSERT INTO human_actions
                   (action_id, case_id, investigator, action, rationale, findings_accepted, findings_rejected, timestamp)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (action_id, case_id, investigator, action, rationale,
                 json.dumps(findings_accepted, default=str), json.dumps(findings_rejected, default=str), ts),
            )
            _insert_audit_event(
                conn, case_id, actor="human", actor_name=investigator, action=f"decision: {action}",
                details={"rationale": rationale, "findings_accepted": len(findings_accepted),
                         "findings_rejected": len(findings_rejected)}, timestamp=ts,
            )
    finally:
        conn.close()
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
        "SELECT * FROM human_actions WHERE case_id = ? ORDER BY timestamp, rowid", (case_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_human_actions() -> list:
    """Every recorded decision, across every case — used by the Analytics
    page's investigator-throughput chart. `get_human_actions` above is
    scoped to one case; this is the whole table."""
    init_runtime_db()
    conn = _connect()
    rows = conn.execute("SELECT * FROM human_actions ORDER BY timestamp").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def reset_demo_human_decisions(admin_name: str) -> dict:
    """Remove all persistent human decisions for a deliberate demo reset.

    This is intentionally narrow: it deletes the decision rows and their
    human-authored audit rows, but keeps system/AI audit events and rule
    configuration.  A new system audit entry records who performed the reset
    and the exact counts removed.  It must only be exposed behind the Admin
    passcode and a deliberate UI confirmation.
    """
    if not admin_name or not admin_name.strip():
        raise ValueError("An admin name is required to reset demo decisions.")
    init_runtime_db()
    conn = _connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        decision_count = conn.execute("SELECT COUNT(*) FROM human_actions").fetchone()[0]
        human_audit_count = conn.execute("SELECT COUNT(*) FROM audit_log WHERE actor='human'").fetchone()[0]
        conn.execute("DELETE FROM human_actions")
        conn.execute("DELETE FROM audit_log WHERE actor='human'")
        _insert_audit_event(
            conn, "SYSTEM-DEMO", actor="system", action="demo_human_decisions_reset",
            actor_name=admin_name.strip(),
            details={"human_decisions_removed": decision_count,
                     "human_audit_entries_removed": human_audit_count},
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return {
        "human_decisions_removed": decision_count,
        "human_audit_entries_removed": human_audit_count,
    }


def get_latest_decision_per_case() -> dict:
    """One query for the whole queue dashboard, instead of one query per
    case: {case_id: {"action": ..., "investigator": ..., "timestamp": ...}}
    — only the most recent decision per case (a case can be decided more
    than once over time, e.g. reopened)."""
    init_runtime_db()
    conn = _connect()
    rows = conn.execute("""
        SELECT h.case_id, h.action, h.investigator, h.timestamp
        FROM human_actions h
        INNER JOIN (
            SELECT case_id, MAX(timestamp) AS max_ts FROM human_actions GROUP BY case_id
        ) latest ON h.case_id = latest.case_id AND h.timestamp = latest.max_ts
    """).fetchall()
    conn.close()
    return {r["case_id"]: dict(r) for r in rows}


_DECISION_STATUS_LABELS = {
    "close": "Closed", "escalate": "Escalated", "request_info": "Info Requested",
    # A Compliance action must be visible as its own outcome in Case Queue.
    # Do not collapse acknowledgement into a generic "closed" label: that
    # hides both who acted and what the next permitted step is.
    "compliance_ack": "Compliance reviewed — no further action",
    "compliance_return": "Compliance returned — information needed",
    "compliance_refer": "Compliance referred onward — recorded",
}


def resolve_status(raw_alert_status: str, decision: dict | None) -> str:
    """The one place that decides what "status" means for an alert: a
    recorded human decision overrides the dataset's original status,
    otherwise falls back to the raw value. Case Queue, Home, and Analytics
    all call this instead of each re-deriving it — they used to read
    `alerts.status` directly, so escalating or closing a case from the
    workspace showed up on Case Queue but not on Home/Analytics, which kept
    counting the dataset's original, pre-decision status."""
    if decision:
        return _DECISION_STATUS_LABELS.get(decision["action"], decision["action"])
    if raw_alert_status == "Closed - Simulated Example":
        return "Demo closed — simulated"
    if raw_alert_status.startswith("Closed"):
        # A workbook label is not a decision recorded in this application.
        # Keep it distinct from a reviewed, auditable human close action.
        return "Source closed — unverified"
    return raw_alert_status


# Defaults match the documented rule definitions (CEO Playbook / Functional
# Requirements: R1 amount deviation >= 5x baseline, R2 rapid pass-through
# >= 80% of the credit leaves within 72 hours across >= 2 hops).
DEFAULT_RULE_CONFIG = {
    ("R1", "deviation_multiplier"): 5.0,
    ("R2", "pass_through_pct"): 80.0,
    ("R2", "window_hours"): 72.0,
}


def get_rule_config() -> dict:
    """{(rule_id, param_name): value} — falls back to the documented default
    for any parameter that hasn't been explicitly saved yet."""
    init_runtime_db()
    conn = _connect()
    rows = conn.execute("SELECT rule_id, param_name, param_value FROM rule_config").fetchall()
    conn.close()
    config = dict(DEFAULT_RULE_CONFIG)
    for r in rows:
        config[(r["rule_id"], r["param_name"])] = r["param_value"]
    return config


def set_rule_params(changes: dict, updated_by: str):
    """Save one or more rule parameters and their audit entries atomically."""
    updated_by = str(updated_by or "").strip()
    if not updated_by:
        raise ValueError("An actor name is required for rule changes")
    unknown = set(changes) - set(DEFAULT_RULE_CONFIG)
    if unknown:
        raise ValueError(f"Unknown rule parameter(s): {sorted(unknown)}")
    if not changes:
        return
    init_runtime_db()
    conn = _connect()
    ts = _now()
    try:
        with conn:
            for (rule_id, param_name), value in changes.items():
                conn.execute(
                    """INSERT INTO rule_config (rule_id, param_name, param_value, updated_by, updated_at)
                       VALUES (?,?,?,?,?)
                       ON CONFLICT(rule_id, param_name) DO UPDATE SET param_value=excluded.param_value,
                           updated_by=excluded.updated_by, updated_at=excluded.updated_at""",
                    (rule_id, param_name, value, updated_by, ts),
                )
                _insert_audit_event(
                    conn, "SYSTEM-RULES", actor="human", actor_name=updated_by,
                    action=f"rule_config_updated: {rule_id}.{param_name} = {value}", timestamp=ts,
                )
    finally:
        conn.close()


def set_rule_param(rule_id: str, param_name: str, value: float, updated_by: str):
    """Single-parameter compatibility wrapper around the batch transaction."""
    set_rule_params({(rule_id, param_name): value}, updated_by)
