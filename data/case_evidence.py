"""Build inspectable, explicitly fictional case and KYC evidence records.

The source workbook has structured fields and short document summaries, not
original PAN/Aadhaar/passport files. Generated sample documents demonstrate
lineage and chunking; they must never be described as independently verified
identity documents or sufficient proof of lawful funds.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import re


def _value(value: object) -> str:
    return "Not recorded" if value is None or str(value).strip() == "" else str(value)


def _money(value: object) -> str:
    try:
        return f"INR {float(value):,.0f}"
    except (TypeError, ValueError):
        return "Not recorded"


def _source(doc_id: str, customer_id: str, case_id: str | None, category: str,
            document_type: str, title: str, paragraphs: list[str], origin: str,
            verification_status: str, source_table: str,
            source_record_ids: list[str], doc_date: str | None = None) -> dict:
    body = "\n\n".join(paragraphs)
    return {
        "doc_id": doc_id,
        "customer_id": customer_id,
        "case_id": case_id,
        "category": category,
        "document_type": document_type,
        "title": title,
        "body": body,
        "origin": origin,
        "verification_status": verification_status,
        "source_table": source_table,
        "source_record_ids": json.dumps(source_record_ids),
        "doc_date": doc_date,
        "content_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "is_original_upload": 0,
    }


def chunk_source_text(body: str) -> list[str]:
    """Split authored evidence sections without changing their exact text.

    Paragraph boundaries preserve the semantic sections (identity, activity,
    provenance). For a transaction packet each four-record group is a
    paragraph. Joining the chunks with two newlines reconstructs the source.
    """
    return [part for part in body.split("\n\n") if part.strip()]


def _customer_sources(customer: sqlite3.Row, index: int) -> list[dict]:
    cid = customer["customer_id"]
    name = _value(customer["name"])
    customer_type = _value(customer["type"])
    kyc_status = _value(customer["kyc_status"])
    updated = _value(customer["kyc_last_updated"])
    prefix = "FICTIONAL COURSE SAMPLE — not an authentic government document or an independent verification."

    profile = _source(
        f"KYC-PROFILE-{cid}", cid, None, "kyc_profile", "Customer profile snapshot",
        f"KYC profile on record — {name}", [
            f"{prefix} This profile is generated from a fictional Customers table row "
            f"(workbook import or matched-case fixture). Customer ID: {cid}. "
            f"Recorded name: {name}. Customer type: {customer_type}. Segment: {_value(customer['segment'])}. "
            f"Country: {_value(customer['country'])}. Onboarding date: {_value(customer['onboarding_date'])}.",
            f"Recorded occupation or industry: {_value(customer['occupation_or_industry'])}. "
            f"Declared annual income: {_money(customer['declared_annual_income'])}. "
            f"Expected monthly credit: {_money(customer['expected_monthly_credit'])}. "
            f"Expected monthly debit: {_money(customer['expected_monthly_debit'])}. "
            f"Declared source of funds: {_value(customer['declared_source_of_funds'])}. "
            "These are customer-profile assertions, not independently proved source-of-funds facts.",
            f"Dataset KYC status: {kyc_status}; last-updated field: {updated}; risk rating: "
            f"{_value(customer['risk_rating'])}. The status is copied from fictional data. "
            "No issuing authority, original identity file, biometric check, or bank officer verification is attached. "
            "A reviewer must obtain and check appropriate independent records before relying on identity or source of funds.",
        ], "generated_from_customer_row", "recorded_not_independently_verified",
        "customers", [cid], updated,
    )

    pan = _source(
        f"SAMPLE-PAN-{cid}", cid, None, "identity_sample", "PAN sample record",
        f"Illustrative PAN evidence record — {name}", [
            f"{prefix} Subject customer ID: {cid}; recorded holder name: {name}. "
            f"Sample reference: DEMO-PAN-{cid}. This deliberately does not use a valid PAN format and "
            "is not a scan, e-PAN, or confirmation from an issuing authority.",
            "Cross-check demonstration: compare the recorded holder name and customer ID with the customer profile. "
            "A matching name in two records generated from the same customer row is not independent proof. "
            "The actual PAN, its issuing record, and any verification result are not present in this dataset.",
        ], "generated_fictional_sample", "illustrative_only", "customers", [cid], updated,
    )

    if customer_type.lower() == "individual":
        ovd_type = ("Aadhaar sample record", "Passport sample record", "Driving licence sample record")[index % 3]
        label = ovd_type.split()[0].upper().replace("AADHAAR", "AADHAAR")
        other = _source(
            f"SAMPLE-OVD-{cid}", cid, None, "identity_sample", ovd_type,
            f"Illustrative {ovd_type.lower()} — {name}", [
                f"{prefix} Subject customer ID: {cid}; recorded holder name: {name}. "
                f"Sample reference: DEMO-{label}-{cid}. This is text for a course walkthrough, not an "
                "issued Aadhaar card, passport, driving licence, or authenticated electronic document.",
                "Cross-check demonstration: compare name, customer ID and recorded country with the customer profile. "
                "No real document number, address image, photograph, expiry verification, issuer response, "
                "Aadhaar authentication, or customer consent record is stored here. Mark identity as needing "
                "independent review rather than treating this example as verified evidence.",
            ], "generated_fictional_sample", "illustrative_only", "customers", [cid], updated,
        )
    else:
        other = _source(
            f"SAMPLE-BUSINESS-{cid}", cid, None, "identity_sample", "Business registration sample record",
            f"Illustrative business-identity record — {name}", [
                f"{prefix} Business customer ID: {cid}; recorded business name: {name}. "
                f"Sample reference: DEMO-BUSINESS-{cid}. The workbook says only 'Business'; it does not "
                "establish whether this customer is a company, partnership, proprietorship, or another form.",
                "No original registration certificate, legal-form proof, authorised-signatory document, "
                "beneficial-owner record, or independent issuer check is available here. Those gaps must "
                "be resolved under the institution's applicable KYC procedure before treating the profile as verified.",
            ], "generated_fictional_sample", "illustrative_only", "customers", [cid], updated,
        )
    return [profile, pan, other]


def _case_sources(conn: sqlite3.Connection, alert: sqlite3.Row) -> list[dict]:
    case_id, cid, account_id = alert["case_id"], alert["customer_id"], alert["account_id"]
    alert_id = alert["alert_id"]
    owner_count = conn.execute(
        "SELECT COUNT(DISTINCT customer_id) FROM accounts WHERE account_id=? AND customer_id IS NOT NULL",
        (account_id,),
    ).fetchone()[0]
    ambiguous_account = owner_count > 1
    matched = conn.execute(
        "SELECT * FROM matched_case_metadata WHERE case_id=?", (case_id,)
    ).fetchone()
    alert_doc = _source(
        f"CASE-ALERT-{case_id}", cid, case_id, "alert_record", "Alert record",
        f"Recorded alert — {case_id}", [
            ("FICTIONAL COURSE DATA — this alert was calculated from the matched-case transaction fixture, "
             "not received from a third-party monitoring service. The app has no incoming alert API."
             if matched else "FICTIONAL COURSE DATA — this is a record imported from the Alerts worksheet, "
             "not a third-party monitoring message. The app has no incoming alert API."),
            f"Alert ID: {alert_id}; case ID: {case_id}; customer ID: {cid}; account ID: {account_id}. "
            f"Recorded alert type: {_value(alert['alert_type'])}. Scenario ID: {_value(alert['scenario_id'])}. "
            f"Recorded rule label: {_value(alert['trigger_rule'])}. Severity: {_value(alert['severity'])}. "
            f"Alert date: {_value(alert['alert_date'])}. Trigger transaction ID: "
            f"{_value(alert['trigger_transaction_id'])}.",
            ("The matched-case alert was recomputed from the ten source rows at build time. "
             "This remains a fictional test signal, not a bank alert or a legal/criminal verdict."
             if matched else "The rule label is source-dataset metadata, not proof that the current app "
             "independently recomputed the trigger. A monitoring signal is a reason to review records, "
             "not a legal or criminal verdict."),
        ], "calculated_from_fictional_test_rows" if matched else "copied_from_alert_row",
        "calculated_fictional_test_signal" if matched else "recorded_not_independently_recalculated",
        "alerts", [alert_id, case_id], _value(alert["alert_date"]),
    )

    rows = conn.execute(
        """SELECT txn_id, txn_datetime, direction, amount, counterparty_name,
                  counterparty_account_id, reference_text FROM transactions
           WHERE account_id=? AND julianday(txn_datetime)>=julianday(?)
             AND julianday(txn_datetime)<julianday(?, '+' || ? || ' days')
           ORDER BY txn_datetime""",
        (account_id, alert["alert_date"], alert["alert_date"], 10),
    ).fetchall()
    in_window = bool(rows)
    if not rows:
        rows = conn.execute(
            """SELECT txn_id, txn_datetime, direction, amount, counterparty_name,
                      counterparty_account_id, reference_text FROM transactions
               WHERE account_id=?
               ORDER BY ABS(julianday(txn_datetime)-julianday(?)) LIMIT 5""",
            (account_id, alert["alert_date"]),
        ).fetchall()
        rows = sorted(rows, key=lambda row: row["txn_datetime"])

    ids = [row["txn_id"] for row in rows]
    scope = "within the alert's 10-day review window" if in_window else "nearest in time only; outside the alert review window"
    sections = [
        "FICTIONAL COURSE DATA — this statement is assembled from transaction rows, not an "
        "uploaded bank statement or confirmation of a transfer's final destination.",
        f"Case ID: {case_id}; account ID: {account_id}. Transaction scope: {scope}. "
        f"Number of source rows displayed: {len(rows)}. Every line below carries the transaction ID "
        "needed to open or cross-check the original database record.",
    ]
    if ambiguous_account:
        sections.append(
            "SOURCE-DATA COLLISION: this account ID belongs to multiple customer rows. The ledger rows cannot "
            "be confidently attributed to this case customer. Do not use this packet to verify a customer-specific "
            "amount, baseline or chain until the source identifier is corrected."
        )
    if matched:
        sections.append(
            f"Matched-case test baseline: six monthly salary credit rows of INR 80,000 each. "
            f"Opening balance asserted by the fictional fixture: {_money(matched['opening_balance'])}. "
            f"Balance after the ten test rows: {_money(matched['balance_after_batch'])}. "
            "These balances are fictional fixture assumptions, not an uploaded bank statement."
        )
        beneficiary_rows = conn.execute(
            "SELECT account_id, added_date FROM matched_case_beneficiaries WHERE case_id=? ORDER BY account_id",
            (case_id,),
        ).fetchall()
        sections.append(
            "Beneficiary-added dates asserted by the fictional fixture: " +
            "; ".join(f"{r['account_id']} added {r['added_date']}" for r in beneficiary_rows) +
            ". External account placeholders have no customer KYC or independent relationship confirmation."
        )
    for offset in range(0, len(rows), 4):
        lines = []
        for row in rows[offset:offset + 4]:
            lines.append(
                f"{row['txn_id']} | {row['txn_datetime']} | {row['direction']} | "
                f"{_money(row['amount'])} | counterparty: {_value(row['counterparty_name'])} | "
                f"counterparty account: {_value(row['counterparty_account_id'])} | "
                f"reference: {_value(row['reference_text'])}"
            )
        sections.append("\n".join(lines))
    if not rows:
        sections.append("No transaction record exists for this account in the source dataset. Do not infer a flow of funds.")
    sections.append(
        "These rows show recorded activity, not the economic purpose or lawfulness of funds. "
        "A missing trigger ID, empty review window, unknown counterparty, or missing source-of-funds "
        "document remains an explicit investigation gap."
    )
    ledger_doc = _source(
        f"CASE-LEDGER-{case_id}", cid, case_id, "transaction_record", "Transaction evidence packet",
        f"Transaction rows for {case_id}", sections, "assembled_from_transaction_rows",
        "ambiguous_account_owner" if ambiguous_account else
        ("source_rows_only" if in_window else "background_context_only"),
        "transactions", ids, _value(alert["alert_date"]),
    )
    full_rows = conn.execute(
        "SELECT txn_id, txn_datetime, direction, amount, status, channel, "
        "counterparty_account_id FROM transactions WHERE account_id=? "
        "ORDER BY txn_datetime, txn_id", (account_id,),
    ).fetchall()
    full_sections = [
        "FICTIONAL COURSE DATA — all recorded rows for this account in the supplied dataset, "
        "not a complete bank statement or a guarantee of uninterrupted coverage.",
        f"Case ID: {case_id}; account ID: {account_id}; stored rows: {len(full_rows)}. "
        "A calendar-month count refers only to these stored rows, not all real account activity.",
    ]
    if ambiguous_account:
        full_sections.append(
            "SOURCE-DATA COLLISION: this account ID has multiple customer owners in the supplied tables. "
            "Do not attribute these account rows to one customer until the identifier is resolved."
        )
    for offset in range(0, len(full_rows), 4):
        full_sections.append("\n".join(
            f"{row['txn_id']} | {row['txn_datetime']} | {row['direction']} | "
            f"{_money(row['amount'])} | {row['status']} | {row['channel']} | "
            f"counterparty account: {_value(row['counterparty_account_id'])}"
            for row in full_rows[offset:offset + 4]
        ))
    if not full_rows:
        full_sections.append("No transaction row is stored for this account.")
    full_ledger_doc = _source(
        f"CASE-LEDGER-ALL-{case_id}", cid, case_id, "transaction_record",
        "All stored account rows", f"All stored ledger rows for {case_id}", full_sections,
        "assembled_from_all_stored_account_rows",
        "ambiguous_account_owner" if ambiguous_account else "source_rows_only",
        "transactions", [row["txn_id"] for row in full_rows],
        _value(alert["alert_date"]),
    )
    return [alert_doc, ledger_doc, full_ledger_doc]


def build_case_evidence(conn: sqlite3.Connection) -> tuple[int, int]:
    """Rebuild synthetic source documents and their exact, inspectable chunks."""
    conn.row_factory = sqlite3.Row
    sources = []
    customers = conn.execute("SELECT * FROM customers ORDER BY customer_id").fetchall()
    for index, customer in enumerate(customers):
        sources.extend(_customer_sources(customer, index))
    alerts = conn.execute("SELECT * FROM alerts ORDER BY case_id").fetchall()
    for alert in alerts:
        sources.extend(_case_sources(conn, alert))
    for row in conn.execute("SELECT * FROM documents ORDER BY doc_id").fetchall():
        did = row["doc_id"]
        sources.append(_source(
            f"SUMMARY-{did}", row["customer_id"], row["case_id"], "document_summary",
            _value(row["doc_type"]), f"Recorded summary of {did}", [
                "FICTIONAL COURSE DATA — only a summary row was supplied in the Documents table "
                "(workbook import or matched-case fixture). "
                "The underlying file or image is not in this repository or database.",
                f"Document ID: {did}; type: {_value(row['doc_type'])}; date: {_value(row['doc_date'])}. "
                f"Recorded extracted summary: {_value(row['extracted_summary'])}",
                f"Dataset verified flag: {_value(row['verified'])}. This flag cannot be independently "
                "confirmed without the original document and verification trail; do not call the summary "
                "a verified source document.",
            ], "copied_from_document_summary_row", "summary_without_original",
            "documents", [did], _value(row["doc_date"]),
        ))

    conn.execute("DROP TABLE IF EXISTS case_evidence_chunks_fts")
    conn.execute("DROP TABLE IF EXISTS case_evidence_chunks")
    conn.execute("DROP TABLE IF EXISTS case_evidence_sources")
    conn.execute("""CREATE TABLE case_evidence_sources (
        doc_id TEXT PRIMARY KEY, customer_id TEXT NOT NULL, case_id TEXT,
        category TEXT NOT NULL, document_type TEXT NOT NULL, title TEXT NOT NULL,
        body TEXT NOT NULL, origin TEXT NOT NULL, verification_status TEXT NOT NULL,
        source_table TEXT NOT NULL, source_record_ids TEXT NOT NULL,
        doc_date TEXT, content_sha256 TEXT NOT NULL, is_original_upload INTEGER NOT NULL
    )""")
    conn.execute("""CREATE TABLE case_evidence_chunks (
        chunk_id TEXT PRIMARY KEY, doc_id TEXT NOT NULL, customer_id TEXT NOT NULL,
        case_id TEXT, chunk_index INTEGER NOT NULL, chunk_text TEXT NOT NULL,
        word_count INTEGER NOT NULL,
        FOREIGN KEY(doc_id) REFERENCES case_evidence_sources(doc_id)
    )""")
    conn.execute("""CREATE VIRTUAL TABLE case_evidence_chunks_fts USING fts5(
        chunk_id UNINDEXED, doc_id UNINDEXED, customer_id UNINDEXED,
        case_id UNINDEXED, chunk_text
    )""")
    columns = ("doc_id", "customer_id", "case_id", "category", "document_type", "title",
               "body", "origin", "verification_status", "source_table", "source_record_ids",
               "doc_date", "content_sha256", "is_original_upload")
    source_sql = f"INSERT INTO case_evidence_sources ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})"
    chunk_count = 0
    for source in sources:
        conn.execute(source_sql, [source[column] for column in columns])
        for index, passage in enumerate(chunk_source_text(source["body"])):
            chunk_id = f"{source['doc_id']}-C{index}"
            conn.execute(
                "INSERT INTO case_evidence_chunks VALUES (?,?,?,?,?,?,?)",
                (chunk_id, source["doc_id"], source["customer_id"], source["case_id"],
                 index, passage, len(passage.split())),
            )
            conn.execute(
                "INSERT INTO case_evidence_chunks_fts VALUES (?,?,?,?,?)",
                (chunk_id, source["doc_id"], source["customer_id"], source["case_id"], passage),
            )
            chunk_count += 1
    conn.execute("CREATE INDEX IF NOT EXISTS idx_case_evidence_customer ON case_evidence_sources(customer_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_case_evidence_case ON case_evidence_sources(case_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_case_chunks_doc ON case_evidence_chunks(doc_id)")
    conn.commit()
    return len(sources), chunk_count


def case_evidence_coverage(conn: sqlite3.Connection, case_id: str) -> dict:
    """Report document coverage and gaps, never a legal/illegal classification."""
    conn.row_factory = sqlite3.Row
    alert = conn.execute(
        "SELECT case_id, customer_id, account_id, trigger_transaction_id FROM alerts WHERE case_id=?",
        (case_id,),
    ).fetchone()
    if alert is None:
        raise ValueError(f"Unknown case: {case_id}")
    cid = alert["customer_id"]
    docs = conn.execute(
        "SELECT category, verification_status, is_original_upload FROM case_evidence_sources "
        "WHERE customer_id=? AND (case_id IS NULL OR case_id=?)",
        (cid, case_id),
    ).fetchall()
    sample_ids = sum(row["category"] == "identity_sample" for row in docs)
    summary_only = sum(row["category"] == "document_summary" for row in docs)
    originals = sum(row["is_original_upload"] == 1 for row in docs)
    ledger = next((row for row in docs if row["category"] == "transaction_record"), None)
    gaps = []
    if originals == 0:
        gaps.append("No original identity or supporting document has been uploaded or independently verified.")
    owner_count = conn.execute(
        "SELECT COUNT(DISTINCT customer_id) FROM accounts WHERE account_id=? AND customer_id IS NOT NULL",
        (alert["account_id"],),
    ).fetchone()[0]
    if owner_count > 1:
        gaps.append("Source-data collision: the account ID is assigned to multiple customers; transaction attribution is unresolved.")
    counterparties = [row[0] for row in conn.execute(
        "SELECT DISTINCT counterparty_account_id FROM transactions WHERE account_id=? "
        "AND julianday(txn_datetime)>=julianday((SELECT alert_date FROM alerts WHERE case_id=?)) "
        "AND julianday(txn_datetime)<julianday((SELECT alert_date FROM alerts WHERE case_id=?), '+10 days') "
        "AND counterparty_account_id IS NOT NULL AND channel<>'Cash Deposit' AND status='Completed'",
        (alert["account_id"], case_id, case_id),
    ).fetchall()]
    unknown_counterparties = [account_id for account_id in counterparties if not conn.execute(
        "SELECT 1 FROM accounts a JOIN customers c ON c.customer_id=a.customer_id "
        "WHERE a.account_id=? LIMIT 1",
        (account_id,),
    ).fetchone()]
    if unknown_counterparties:
        gaps.append(
            f"{len(unknown_counterparties)} distinct counterparty account(s) in the review window "
            "have no mapped customer profile in this bank dataset. Their KYC status and onward activity are unknown."
        )
    if summary_only:
        gaps.append("Document entries on file are summaries; underlying files are unavailable for cross-checking.")
    if ledger is None or ledger["verification_status"] == "background_context_only":
        gaps.append("No transaction rows fall inside this alert's review window; nearby rows are context only.")
    if not alert["trigger_transaction_id"]:
        gaps.append("The source alert has no identified trigger transaction ID.")
    gaps.append("Declared source of funds is not corroborated by an independent source document in this dataset.")
    return {
        "case_id": case_id, "customer_id": cid, "sample_identity_records": sample_ids,
        "summary_only_records": summary_only, "original_uploaded_files": originals,
        "unknown_counterparty_count": len(unknown_counterparties),
        "transaction_window_status": ledger["verification_status"] if ledger else "missing",
        "gaps": gaps, "conclusion": "Evidence review required; lawfulness cannot be determined from these records.",
    }


def search_case_chunks(conn: sqlite3.Connection, case_id: str, query: str, limit: int = 4) -> list[dict]:
    """Retrieve case/customer source passages using the same FTS5/BM25 method.

    Results expose provenance and verification status. Retrieval relevance is
    not evidence authenticity or a finding of lawful funds.
    """
    conn.row_factory = sqlite3.Row
    alert = conn.execute("SELECT customer_id FROM alerts WHERE case_id=?", (case_id,)).fetchone()
    if alert is None:
        raise ValueError(f"Unknown case: {case_id}")
    terms = [term for term in re.findall(r"[A-Za-z0-9]+", query.lower()) if len(term) > 2]
    if not terms or not 1 <= limit <= 20:
        return []
    expression = " OR ".join(terms[:12])
    rows = conn.execute(
        "SELECT f.chunk_id, f.doc_id, f.chunk_text, s.title, s.category, s.origin, "
        "s.verification_status, s.source_record_ids, bm25(case_evidence_chunks_fts) AS rank "
        "FROM case_evidence_chunks_fts f JOIN case_evidence_sources s ON s.doc_id=f.doc_id "
        "WHERE case_evidence_chunks_fts MATCH ? AND f.customer_id=? "
        "AND (f.case_id IS NULL OR f.case_id=?) ORDER BY rank LIMIT ?",
        (expression, alert["customer_id"], case_id, limit),
    ).fetchall()
    return [dict(row) for row in rows]
