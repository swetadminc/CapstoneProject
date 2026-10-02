"""Two neutral, fictional matched cases derived from Rahul's test-data PDF.

Both cases have the same six-month baseline and ten-transaction pattern. The
source PDF's hidden fraud/legitimate labels are deliberately NOT written to
the investigation tables. Initial customer explanations are assertions, not
verified supporting files. Their alert rows are calculated by code rather
than copied from an expected-output table.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3

if __package__:
    from .incoming_monitor import detect_pass_through
else:
    from incoming_monitor import detect_pass_through


def _insert(conn: sqlite3.Connection, table: str, row: dict) -> None:
    cols = ",".join(row)
    slots = ",".join("?" for _ in row)
    conn.execute(f"INSERT INTO {table} ({cols}) VALUES ({slots})", tuple(row.values()))


def seed_matched_cases(conn: sqlite3.Connection) -> tuple[int, int]:
    """Seed source rows, then compute the two alerts from the rows themselves."""
    conn.execute("""CREATE TABLE IF NOT EXISTS matched_case_metadata (
        case_id TEXT PRIMARY KEY, source_description TEXT NOT NULL,
        opening_balance INTEGER NOT NULL, historical_monthly_credit INTEGER NOT NULL,
        balance_after_batch INTEGER NOT NULL, input_sha256 TEXT NOT NULL
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS matched_case_beneficiaries (
        case_id TEXT NOT NULL, account_id TEXT NOT NULL, added_date TEXT NOT NULL,
        relationship_assertion TEXT NOT NULL,
        PRIMARY KEY(case_id, account_id)
    )""")
    subjects = [
        ("CASE-043", "CUST-TEST-01", "ACC-TEST-01", "Arjun Mehta",
         "Customer says receipts were from friends and debits repaid personal loans; this explanation is uncorroborated."),
        ("CASE-044", "CUST-TEST-02", "ACC-TEST-02", "Neeraj Shah",
         "Customer says receipts and payments relate to a family settlement; no agreement or participant verification file is attached."),
    ]
    for case_id, customer_id, account_id, name, explanation in subjects:
        _insert(conn, "customers", {
            "customer_id": customer_id, "name": name, "type": "Individual",
            "segment": "Retail - fictional matched-case test", "occupation_or_industry": "Salaried employee",
            "declared_annual_income": 960000, "expected_monthly_credit": 80000,
            "expected_monthly_debit": 60000, "declared_source_of_funds": "Salary — fictional customer assertion",
            "risk_rating": "Medium", "kyc_status": "Current — dataset assertion only",
            "kyc_last_updated": "2026-09-01", "country": "India", "onboarding_date": "2022-10-01",
        })
        _insert(conn, "accounts", {
            "account_id": account_id, "customer_id": customer_id, "type": "Savings",
            "open_date": "2022-10-01", "currency": "INR", "status": "Active",
            "risk_rating": "Medium", "is_internal": 1, "counterparty_name": None,
        })
        prefix = "01" if case_id == "CASE-043" else "02"
        for month in range(4, 10):
            _insert(conn, "transactions", {
                "txn_id": f"TXN-TEST-{prefix}-BASE-{month:02d}", "account_id": account_id,
                "txn_datetime": f"2026-{month:02d}-01T09:00:00", "direction": "CR",
                "amount": 80000, "currency": "INR", "channel": "NEFT",
                "counterparty_account_id": None, "counterparty_name": "Fictional employer",
                "reference_text": "Monthly salary — test baseline only", "status": "Completed",
            })

        times = ["09:00", "09:20", "09:40", "10:00", "10:15", "10:30",
                 "10:45", "11:00", "11:15", "11:30"]
        imported_rows = []
        for index, time in enumerate(times, start=1):
            credit = index <= 4
            suffix = f"S{index:02d}" if credit else f"B{index-4:02d}"
            counterparty_id = f"EXT-{prefix}-{suffix}"
            if not conn.execute("SELECT 1 FROM accounts WHERE account_id=?", (counterparty_id,)).fetchone():
                _insert(conn, "accounts", {
                    "account_id": counterparty_id, "customer_id": None,
                    "type": "External account placeholder", "open_date": None,
                    "currency": "INR", "status": "Unknown", "risk_rating": "Unrated",
                    "is_internal": 0, "counterparty_name": f"Fictional {suffix}",
                })
            row = {
                "txn_id": f"TXN-TEST-{prefix}-{index:02d}", "account_id": account_id,
                "txn_datetime": f"2026-10-01T{time}:00", "direction": "CR" if credit else "DR",
                "amount": 300000 if credit else 180000, "currency": "INR", "channel": "NEFT",
                "counterparty_account_id": counterparty_id,
                "counterparty_name": f"Fictional {suffix}",
                "reference_text": ("Investment allocation" if case_id == "CASE-043" else "Family settlement contribution")
                                  if credit else ("Personal loan repayment" if case_id == "CASE-043" else "Family settlement distribution"),
                "status": "Completed",
            }
            _insert(conn, "transactions", row)
            imported_rows.append(row)
            if not credit:
                _insert(conn, "matched_case_beneficiaries", {
                    "case_id": case_id, "account_id": counterparty_id,
                    "added_date": "2026-09-30" if index < 10 else "2026-04-01",
                    "relationship_assertion": "Customer explanation only; no independent relationship or identity file",
                })

        findings = detect_pass_through(imported_rows, 80000)
        if len(findings) != 1:
            raise AssertionError(f"Matched-case data failed its own alert calculation: {case_id}")
        calculated = findings[0]
        _insert(conn, "alerts", {
            "alert_id": f"ALERT-TEST-{prefix}", "case_id": case_id,
            "customer_id": customer_id, "account_id": account_id,
            "alert_type": "Rapid incoming funds and multi-beneficiary dispersal",
            "scenario_id": "rapid-movement-of-funds",
            "trigger_rule": "Calculated: 24h incoming >=5x six-month monthly credit baseline; outgoing >=80%; >=3 beneficiaries",
            "alert_date": "2026-10-01", "severity": "High",
            "trigger_transaction_id": calculated["credit_txn_ids"][0], "status": "Open",
        })
        _insert(conn, "documents", {
            "doc_id": f"DOC-TEST-{prefix}-EXPLANATION", "customer_id": customer_id,
            "case_id": case_id, "doc_type": "Customer explanation summary (fictional)",
            "doc_date": "2026-10-01", "extracted_summary": explanation, "verified": 0,
        })
        payload = json.dumps(imported_rows, sort_keys=True).encode("utf-8")
        _insert(conn, "matched_case_metadata", {
            "case_id": case_id,
            "source_description": "Fictional matched-case test adapted from Rahul's process/test-data PDF; no bank feed",
            "opening_balance": 20000, "historical_monthly_credit": 80000,
            "balance_after_batch": 140000,
            "input_sha256": hashlib.sha256(payload).hexdigest(),
        })
    conn.commit()
    return 2, 20
