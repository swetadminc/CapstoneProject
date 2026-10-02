"""Conservative ledger-link inspection for fictional course transactions.

A counterparty field is a recorded claim of a link, not evidence that the
receiving ledger posted the same transfer. Candidate onward activity is not
proof that the same funds moved again.
"""

from __future__ import annotations

import sqlite3


NON_TRANSFER_CHANNELS = {"Cash Deposit"}


def account_identity(conn: sqlite3.Connection, account_id: str | None) -> dict:
    if not account_id:
        return {"account_id": None, "customer_id": None, "name": "Not recorded",
                "dataset_kyc_status": "Unknown", "original_identity_files": 0}
    rows = conn.execute(
        "SELECT a.account_id, c.customer_id, c.name, c.kyc_status FROM accounts a "
        "JOIN customers c ON c.customer_id=a.customer_id WHERE a.account_id=?",
        (account_id,),
    ).fetchall()
    if len(rows) > 1:
        return {"account_id": account_id, "customer_id": None,
                "name": "Ambiguous owner — multiple customer rows", "dataset_kyc_status": "Unknown — ID collision",
                "original_identity_files": 0,
                "candidate_customer_ids": [row["customer_id"] for row in rows]}
    if not rows:
        return {"account_id": account_id, "customer_id": None, "name": "External or unknown",
                "dataset_kyc_status": "Unknown", "original_identity_files": 0}
    row = rows[0]
    originals = conn.execute(
        "SELECT COUNT(*) FROM case_evidence_sources WHERE customer_id=? AND is_original_upload=1",
        (row["customer_id"],),
    ).fetchone()[0]
    return {"account_id": row["account_id"], "customer_id": row["customer_id"],
            "name": row["name"], "dataset_kyc_status": row["kyc_status"],
            "original_identity_files": originals}


def trace_transaction(conn: sqlite3.Connection, txn_id: str) -> dict:
    """Return a direction-aware one-hop link and bounded, unproven onward candidates."""
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM transactions WHERE txn_id=?", (txn_id,)).fetchone()
    if row is None:
        raise ValueError(f"Unknown transaction: {txn_id}")
    is_transfer = row["channel"] not in NON_TRANSFER_CHANNELS
    counterparty = row["counterparty_account_id"] if is_transfer else None
    source_id = row["account_id"] if row["direction"] == "DR" else counterparty
    destination_id = counterparty if row["direction"] == "DR" else row["account_id"]
    source = account_identity(conn, source_id)
    destination = account_identity(conn, destination_id)
    if not is_transfer:
        link_status = "cash_deposit_not_account_transfer"
        caveat = "Cash deposits do not establish a sender account or a subsequent transfer chain."
    elif not counterparty:
        link_status = "counterparty_account_missing"
        caveat = "No counterparty account was recorded; the other endpoint cannot be identified."
    elif source.get("candidate_customer_ids") or destination.get("candidate_customer_ids"):
        link_status = "account_ownership_ambiguous"
        caveat = "An account ID is assigned to multiple customer rows. This link cannot be attributed to a single owner."
    elif not source["customer_id"] or not destination["customer_id"]:
        link_status = "counterparty_not_in_bank_dataset"
        caveat = "The counterparty account is not mapped to a customer in this bank dataset; its KYC is unknown."
    else:
        link_status = "single_ledger_link_only"
        caveat = "This is one row's reported account link. No matching opposite-side posting proves settlement."
    mirror = None
    if (is_transfer and counterparty and row["status"] == "Completed"
            and source["customer_id"] and destination["customer_id"]):
        matches = conn.execute(
            "SELECT txn_id FROM transactions WHERE account_id=? AND counterparty_account_id=? "
            "AND direction<>? AND amount=? AND status='Completed' "
            "AND ABS(julianday(txn_datetime)-julianday(?))<=1 AND txn_id<>? LIMIT 2",
            (counterparty, row["account_id"], row["direction"], row["amount"],
             row["txn_datetime"], txn_id),
        ).fetchall()
        if len(matches) == 1:
            mirror = matches[0]
            link_status = "matching_ledger_pair"
            caveat = "One candidate opposite-side row supports a possible account-to-account posting. Without a shared transfer reference it does not prove settlement, source of funds, or lawfulness."
        elif len(matches) > 1:
            link_status = "ambiguous_ledger_pair"
            caveat = "Multiple opposite-side rows share the amount and time window; a unique transfer cannot be identified."

    candidates = []
    if is_transfer and destination["customer_id"] and row["status"] == "Completed":
        candidates = conn.execute(
            "SELECT txn_id, txn_datetime, amount, counterparty_account_id FROM transactions "
            "WHERE account_id=? AND direction='DR' AND status='Completed' "
            "AND julianday(txn_datetime)>julianday(?) AND julianday(txn_datetime)<=julianday(?, '+3 days') "
            "AND channel<>'Cash Deposit' AND amount BETWEEN ? AND ? "
            "ORDER BY txn_datetime LIMIT 5",
            (destination_id, row["txn_datetime"], row["txn_datetime"],
             max(1, round(row["amount"] * .5)), row["amount"]),
        ).fetchall()
    return {
        "transaction": dict(row), "source": source, "destination": destination,
        "link_status": link_status, "mirror_transaction_id": mirror["txn_id"] if mirror else None,
        "caveat": caveat,
        "onward_candidates": [dict(candidate) for candidate in candidates],
        "onward_caveat": "Later outgoing rows from the destination account are candidates only; amount and timing do not prove that the same funds were passed on.",
    }


def case_transactions(conn: sqlite3.Connection, case_id: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    alert = conn.execute("SELECT account_id FROM alerts WHERE case_id=?", (case_id,)).fetchone()
    if alert is None:
        raise ValueError(f"Unknown case: {case_id}")
    return [dict(row) for row in conn.execute(
        "SELECT txn_id, txn_datetime, direction, amount, channel, counterparty_account_id, status "
        "FROM transactions WHERE account_id=? ORDER BY txn_datetime DESC",
        (alert["account_id"],),
    ).fetchall()]
