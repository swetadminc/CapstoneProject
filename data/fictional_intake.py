"""Store calculated fictional alerts with inspectable, explicitly unverified evidence.

This is a local data component, not an authenticated bank feed or public upload
endpoint. Only synthetic-prefixed IDs and numeric ledger fields are accepted;
no names, document images, free-text references, or real account numbers enter
this store. The caller must provide its own SQLite connection.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from decimal import Decimal, InvalidOperation

from data.case_evidence import chunk_source_text
from data.incoming_monitor import detect_pass_through, make_fictional_lab_batch, validate_batch
from data.runtime_db import RUNTIME_DB_PATH


_ID = re.compile(r"^FIC-[A-Z0-9-]{3,40}$")
MAX_SAVED_CASES = 50


def fictional_intake_enabled() -> bool:
    """Expose synthetic-only intake on the public Railway service by default.

    An explicit flag always wins, including ``0`` to disable public writes.
    Local development and CI remain off unless deliberately enabled.
    """
    setting = os.environ.get("ENABLE_FICTIONAL_INTAKE")
    if setting is not None:
        return setting == "1"
    return bool(os.environ.get("RAILWAY_PUBLIC_DOMAIN"))


def fictional_intake_path() -> str:
    """Use the separate persistent runtime store unless tests isolate it."""
    return os.environ.get("FICTIONAL_INTAKE_DB_PATH") or RUNTIME_DB_PATH


def make_generated_fictional_batch(incoming_amount: int, outgoing_amount: int,
                                   monthly_baseline: int) -> list[dict]:
    """Produce synthetic-only IDs for a numeric course example; no PII entry."""
    token = hashlib.sha256(
        f"{incoming_amount}:{outgoing_amount}:{monthly_baseline}".encode("ascii")
    ).hexdigest()[:8].upper()
    rows = make_fictional_lab_batch(incoming_amount, outgoing_amount)
    for index, row in enumerate(rows, start=1):
        row["txn_id"] = f"FIC-TXN-{token}-{index:02d}"
        row["account_id"] = f"FIC-ACC-{token}"
        row["counterparty_account_id"] = f"FIC-EXT-{token}-{index:02d}"
    return rows


def init_fictional_intake(conn: sqlite3.Connection) -> None:
    """Create an isolated namespace; never alter the rebuilt source tables."""
    conn.execute("PRAGMA foreign_keys=ON")
    with conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS fictional_intake_cases (
            case_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL UNIQUE,
            customer_id TEXT NOT NULL, account_id TEXT NOT NULL,
            monthly_baseline TEXT NOT NULL, signal_json TEXT NOT NULL,
            source_kind TEXT NOT NULL CHECK(source_kind='generated_fictional_batch')
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS fictional_intake_transactions (
            txn_id TEXT PRIMARY KEY, case_id TEXT NOT NULL,
            txn_datetime TEXT NOT NULL, direction TEXT NOT NULL,
            amount TEXT NOT NULL, status TEXT NOT NULL,
            counterparty_account_id TEXT NOT NULL,
            FOREIGN KEY(case_id) REFERENCES fictional_intake_cases(case_id)
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS fictional_intake_documents (
            doc_id TEXT PRIMARY KEY, case_id TEXT NOT NULL,
            category TEXT NOT NULL, title TEXT NOT NULL, body TEXT NOT NULL,
            verification_status TEXT NOT NULL, is_original_upload INTEGER NOT NULL CHECK(is_original_upload=0),
            content_sha256 TEXT NOT NULL,
            FOREIGN KEY(case_id) REFERENCES fictional_intake_cases(case_id)
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS fictional_intake_chunks (
            chunk_id TEXT PRIMARY KEY, doc_id TEXT NOT NULL, case_id TEXT NOT NULL,
            chunk_index INTEGER NOT NULL, chunk_text TEXT NOT NULL,
            FOREIGN KEY(doc_id) REFERENCES fictional_intake_documents(doc_id)
        )""")
        conn.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS fictional_intake_chunks_fts USING fts5(
            chunk_id UNINDEXED, doc_id UNINDEXED, case_id UNINDEXED, chunk_text
        )""")


def _checked_rows(rows: list[dict]) -> list[dict]:
    normalized = validate_batch(rows)
    if len(normalized) > 50:
        raise ValueError("The course intake accepts at most 50 fictional rows")
    for row in normalized:
        if not _ID.fullmatch(row["txn_id"]) or not row["txn_id"].startswith("FIC-TXN-"):
            raise ValueError("Transaction IDs must use the fictional FIC-TXN- prefix")
        if not _ID.fullmatch(row["account_id"]) or not row["account_id"].startswith("FIC-ACC-"):
            raise ValueError("Account IDs must use the fictional FIC-ACC- prefix")
        if not _ID.fullmatch(row["counterparty_account_id"]) or not row["counterparty_account_id"].startswith("FIC-EXT-"):
            raise ValueError("Counterparty IDs must use the fictional FIC-EXT- prefix")
        if row["amount"] > Decimal(100_000_000):
            raise ValueError("Fictional transaction amounts must not exceed INR 100,000,000")
    return normalized


def _documents(case_id: str, customer_id: str, account_id: str,
               rows: list[dict], signal: dict) -> list[tuple[str, str, str, str]]:
    """Create authored course artifacts, never replicas of issued identity files."""
    warning = "FICTIONAL GENERATED RECORD. Not an original file or independent verification."
    ledger_sections = [
        f"{warning} Case {case_id}; monitored account {account_id}. These are supplied fictional ledger rows, not a bank statement.",
        "A recorded counterparty ID is an unverified endpoint. No opposite-side posting, external customer profile, or onward settlement is supplied.",
    ]
    for offset in range(0, len(rows), 4):
        ledger_sections.append("\n".join(
            f"{row['txn_id']} | {row['txn_datetime'].isoformat()} | {row['direction']} | "
            f"INR {row['amount']} | {row['status']} | counterparty {row['counterparty_account_id']}"
            for row in rows[offset:offset + 4]
        ))
    return [
        (f"FIC-KYC-{case_id}", "kyc_profile", "Fictional customer profile", "\n\n".join([
            f"{warning} Customer {customer_id} is a generated course identity linked to account {account_id}.",
            f"The supplied historical monthly credit baseline is INR {signal['baseline']:,.0f}. This is a fictional input assertion, not an independently checked income or source-of-funds document.",
            "KYC verification status: not independently verified. No original identification, address proof, customer consent, or officer check was supplied.",
        ])),
        (f"FIC-PAN-{case_id}", "identity_sample", "Illustrative PAN reference", "\n\n".join([
            f"{warning} Customer {customer_id}; sample reference DEMO-PAN-{customer_id} deliberately does not use an issued PAN format.",
            "This text demonstrates the document slot and chunking only. No scan, e-PAN, issuer response, or verification trail exists.",
        ])),
        (f"FIC-OVD-{case_id}", "identity_sample", "Illustrative passport reference", "\n\n".join([
            f"{warning} Customer {customer_id}; sample reference DEMO-PASSPORT-{customer_id} is not an issued passport number.",
            "No original passport image, address, expiry check, issuing authority response, or consent record exists.",
        ])),
        (f"FIC-LEDGER-{case_id}", "transaction_record", "Submitted fictional transaction rows", "\n\n".join(ledger_sections)),
        (f"FIC-ALERT-{case_id}", "alert_record", "Calculated review signal", "\n\n".join([
            f"{warning} The signal was calculated from {len(rows)} supplied transaction rows, not delivered by a bank or third party.",
            f"Incoming INR {signal['incoming']:,.0f}; outgoing INR {signal['outgoing']:,.0f}; incoming versus monthly baseline {signal['incoming_multiplier']}x; outgoing versus incoming {signal['outbound_percent']}%; distinct outgoing beneficiaries {signal['beneficiary_count']}.",
            "This is a reason to review evidence, not a finding that money is lawful or unlawful. External counterparty KYC and independent source-of-funds proof are unavailable.",
        ])),
    ]


def intake_fictional_batch(conn: sqlite3.Connection, rows: list[dict], monthly_baseline: object) -> dict:
    """Calculate and atomically save a novel fictional case; repeat input is idempotent.

    A batch below threshold creates no case. This function does not expose an
    upload endpoint or make the saved case available to the main investigation
    agents; those are separate integration steps.
    """
    normalized = _checked_rows(rows)
    try:
        baseline = Decimal(str(monthly_baseline))
    except InvalidOperation as exc:
        raise ValueError("Fictional monthly baseline must be numeric") from exc
    if not baseline.is_finite() or not 0 < baseline <= Decimal(100_000_000):
        raise ValueError("Fictional monthly baseline must be between 0 and INR 100,000,000")
    signal_list = detect_pass_through(rows, monthly_baseline)
    if not signal_list:
        return {"case_id": None, "created": False, "signal": None}
    signal = signal_list[0]
    canonical = {
        "baseline": str(Decimal(str(monthly_baseline))),
        "rows": [{**row, "txn_datetime": row["txn_datetime"].isoformat(), "amount": str(row["amount"])}
                 for row in normalized],
    }
    fingerprint = hashlib.sha256(json.dumps(canonical, sort_keys=True).encode("utf-8")).hexdigest()
    case_id = f"FIC-CASE-{fingerprint[:12].upper()}"
    customer_id = f"FIC-CUST-{fingerprint[:12].upper()}"
    account_id = normalized[0]["account_id"]
    init_fictional_intake(conn)
    with conn:
        existing = conn.execute(
            "SELECT case_id FROM fictional_intake_cases WHERE fingerprint=?", (fingerprint,)
        ).fetchone()
        if existing:
            return {"case_id": existing[0], "created": False, "signal": signal}
        if conn.execute("SELECT COUNT(*) FROM fictional_intake_cases").fetchone()[0] >= MAX_SAVED_CASES:
            raise ValueError("Fictional intake is full; no new cases can be saved")
        inserted = conn.execute(
            "INSERT OR IGNORE INTO fictional_intake_cases VALUES (?,?,?,?,?,?,?)",
            (case_id, fingerprint, customer_id, account_id, canonical["baseline"],
             json.dumps(signal, sort_keys=True), "generated_fictional_batch"),
        ).rowcount
        if not inserted:
            return {"case_id": case_id, "created": False, "signal": signal}
        conn.executemany(
            "INSERT INTO fictional_intake_transactions VALUES (?,?,?,?,?,?,?)",
            [(row["txn_id"], case_id, row["txn_datetime"].isoformat(), row["direction"],
              str(row["amount"]), row["status"], row["counterparty_account_id"])
             for row in normalized],
        )
        for doc_id, category, title, body in _documents(case_id, customer_id, account_id, normalized, signal):
            verification = "source_rows_only" if category in {"transaction_record", "alert_record"} else "illustrative_only"
            conn.execute(
                "INSERT INTO fictional_intake_documents VALUES (?,?,?,?,?,?,?,?)",
                (doc_id, case_id, category, title, body, verification, 0,
                 hashlib.sha256(body.encode("utf-8")).hexdigest()),
            )
            for index, chunk in enumerate(chunk_source_text(body)):
                chunk_id = f"{doc_id}-C{index}"
                conn.execute("INSERT INTO fictional_intake_chunks VALUES (?,?,?,?,?)",
                             (chunk_id, doc_id, case_id, index, chunk))
                conn.execute("INSERT INTO fictional_intake_chunks_fts VALUES (?,?,?,?)",
                             (chunk_id, doc_id, case_id, chunk))
    return {"case_id": case_id, "created": True, "signal": signal}


def read_fictional_case(conn: sqlite3.Connection, case_id: str) -> dict:
    """Return the exact stored packet for inspection, without inferred verdicts."""
    conn.row_factory = sqlite3.Row
    case = conn.execute("SELECT * FROM fictional_intake_cases WHERE case_id=?", (case_id,)).fetchone()
    if case is None:
        raise ValueError(f"Unknown fictional case: {case_id}")
    rows = [dict(row) for row in conn.execute(
        "SELECT * FROM fictional_intake_transactions WHERE case_id=? ORDER BY rowid",
        (case_id,),
    )]
    documents = [dict(row) for row in conn.execute(
        "SELECT * FROM fictional_intake_documents WHERE case_id=? ORDER BY doc_id",
        (case_id,),
    )]
    chunks = [dict(row) for row in conn.execute(
        "SELECT * FROM fictional_intake_chunks WHERE case_id=? ORDER BY doc_id, chunk_index",
        (case_id,),
    )]
    return {
        "case_id": case_id, "fingerprint": case["fingerprint"], "customer_id": case["customer_id"],
        "account_id": case["account_id"], "source_kind": case["source_kind"],
        "monthly_baseline": case["monthly_baseline"],
        "signal": json.loads(case["signal_json"]),
        "transactions": rows, "documents": documents, "chunks": chunks,
        "original_identity_files": sum(doc["is_original_upload"] for doc in documents),
        "external_customer_profiles": 0,
    }


def list_fictional_cases(conn: sqlite3.Connection) -> list[dict]:
    """Return only calculated fictional cases for an explicitly gated queue."""
    conn.row_factory = sqlite3.Row
    result = []
    for row in conn.execute(
        "SELECT case_id, customer_id, account_id, signal_json FROM fictional_intake_cases ORDER BY rowid DESC"
    ):
        signal = json.loads(row["signal_json"])
        result.append({
            "case_id": row["case_id"], "customer_id": row["customer_id"],
            "account_id": row["account_id"],
            "alert_date": signal["window_start"][:10],
            "trigger_transaction_id": signal["credit_txn_ids"][0],
            "source_kind": "generated_fictional_batch",
        })
    return result


def search_fictional_chunks(conn: sqlite3.Connection, case_id: str, query: str) -> list[dict]:
    """Search only one saved packet; return stored chunk text, never a generated answer."""
    phrase = query.strip()[:120]
    if not phrase:
        return []
    conn.row_factory = sqlite3.Row
    quoted = '"' + phrase.replace('"', '""') + '"'
    return [dict(row) for row in conn.execute(
        "SELECT chunk_id, doc_id, chunk_text FROM fictional_intake_chunks_fts "
        "WHERE fictional_intake_chunks_fts MATCH ? AND case_id=? "
        "ORDER BY bm25(fictional_intake_chunks_fts) LIMIT 8",
        (quoted, case_id),
    )]


def assess_fictional_case(conn: sqlite3.Connection, case_id: str) -> dict:
    """Recheck saved rows and evidence integrity before suggesting human review.

    Generated KYC prose and matching chunks prove only that the stored course
    packet is internally reproducible. They cannot establish identity, fund
    source, settlement, or the lawful purpose of a payment.
    """
    packet = read_fictional_case(conn, case_id)
    rows = [{
        "txn_id": row["txn_id"], "account_id": packet["account_id"],
        "txn_datetime": row["txn_datetime"], "direction": row["direction"],
        "amount": row["amount"], "status": row["status"],
        "counterparty_account_id": row["counterparty_account_id"],
    } for row in packet["transactions"]]
    malformed_rows = False
    try:
        recalculated = detect_pass_through(rows, packet["monthly_baseline"])
        completed = [row for row in rows if row["status"] == "Completed"]
        incoming = sum((Decimal(row["amount"]) for row in completed if row["direction"] == "CR"), Decimal(0))
        outgoing = sum((Decimal(row["amount"]) for row in completed if row["direction"] == "DR"), Decimal(0))
        beneficiaries = {row["counterparty_account_id"] for row in completed if row["direction"] == "DR"}
    except (ValueError, InvalidOperation, TypeError, KeyError):
        malformed_rows = True
        recalculated, completed, incoming, outgoing, beneficiaries = [], [], Decimal(0), Decimal(0), set()
    saved = packet["signal"]
    signal_confirmed = bool(recalculated) and all(
        recalculated[0][key] == saved[key]
        for key in ("incoming", "outgoing", "incoming_multiplier", "outbound_percent", "beneficiary_count")
    )
    chunks_by_doc: dict[str, list[str]] = {}
    for chunk in packet["chunks"]:
        chunks_by_doc.setdefault(chunk["doc_id"], []).append(chunk["chunk_text"])
    expected_doc_ids = {f"FIC-{kind}-{case_id}" for kind in ("KYC", "PAN", "OVD", "LEDGER", "ALERT")}
    canonical = {
        "baseline": packet["monthly_baseline"],
        "rows": [
            {"txn_id": row["txn_id"], "account_id": packet["account_id"],
             "txn_datetime": row["txn_datetime"], "direction": row["direction"],
             "amount": row["amount"], "status": row["status"],
             "counterparty_account_id": row["counterparty_account_id"]}
            for row in packet["transactions"]
        ],
    }
    row_fingerprint_confirmed = hashlib.sha256(
        json.dumps(canonical, sort_keys=True).encode("utf-8")
    ).hexdigest() == packet["fingerprint"]
    indexed = conn.execute(
        "SELECT chunk_id, doc_id, case_id, chunk_text FROM fictional_intake_chunks_fts WHERE case_id=?",
        (case_id,),
    ).fetchall()
    indexed_tuples = sorted(tuple(row) for row in indexed)
    source_tuples = sorted(
        (chunk["chunk_id"], chunk["doc_id"], chunk["case_id"], chunk["chunk_text"])
        for chunk in packet["chunks"]
    )
    content_integrity = (
        row_fingerprint_confirmed
        and {doc["doc_id"] for doc in packet["documents"]} == expected_doc_ids
        and set(chunks_by_doc) == expected_doc_ids
        and indexed_tuples == source_tuples
        and all(
        hashlib.sha256(doc["body"].encode("utf-8")).hexdigest() == doc["content_sha256"]
        and chunks_by_doc.get(doc["doc_id"]) == chunk_source_text(doc["body"])
        for doc in packet["documents"]
        )
    )
    gaps = [
        "No original identity document or independent KYC verification is stored.",
        "The monthly baseline and customer profile are fictional input assertions, not verified income.",
        "No independent source-of-funds document is stored.",
        "External counterparties have no mapped customer profiles or KYC in this packet.",
        "No opposite-side posting or onward-settlement record is stored.",
    ]
    if malformed_rows:
        gaps.insert(0, "Stored transaction rows are malformed; stop review and investigate data integrity.")
    if not signal_confirmed:
        gaps.insert(0, "The saved alert no longer matches the stored transaction rows; investigate data integrity.")
    if not content_integrity:
        gaps.insert(0, "A source fingerprint or exact chunk reconstruction failed; investigate data integrity.")
    return {
        "case_id": case_id,
        "review_signal_recomputed": signal_confirmed,
        "source_integrity_confirmed": content_integrity,
        "observed": {
            "completed_transaction_rows": len(completed),
            "incoming_inr": float(incoming),
            "outgoing_inr": float(outgoing),
            "distinct_beneficiaries": len(beneficiaries),
        },
        "asserted": ["Historical monthly credit baseline", "Generated customer identity/profile"],
        "missing_evidence": gaps,
        "recommended_action": "Request original identity and source-of-funds records, counterparty information, and posting confirmations; a human reviewer must decide the case.",
        "lawfulness_verdict": None,
    }
