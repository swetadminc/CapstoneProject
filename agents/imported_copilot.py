"""Read-only, case-scoped answers across every imported fictional alert."""

from __future__ import annotations

import calendar
import sqlite3
from contextlib import closing
from datetime import datetime
from decimal import Decimal

from agents.fictional_copilot import _mentions, _month_requested
from data.case_evidence import case_evidence_index_status
from data.knowledge_search import DB_PATH


def answer_imported_case_question(question: str, case_id: str, evidence: dict | None = None,
                                  report: dict | None = None,
                                  saved_report_info: dict | None = None) -> dict:
    """Query the selected case's account and cite exact source chunks.

    All rows are account-scoped, never silently attributed to a customer when
    the workbook reuses an account ID. Imported rule labels are not recomputed
    or interpreted as an individual transaction verdict here.
    """
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        alert = conn.execute("SELECT * FROM alerts WHERE case_id=?", (case_id,)).fetchone()
        if alert is None:
            raise ValueError(f"Unknown case: {case_id}")
        customer = conn.execute("SELECT * FROM customers WHERE customer_id=?",
                                (alert["customer_id"],)).fetchone()
        rows = [dict(row) for row in conn.execute(
            "SELECT txn_id, txn_datetime, direction, amount, status, channel, "
            "counterparty_account_id FROM transactions WHERE account_id=? "
            "ORDER BY txn_datetime, txn_id", (alert["account_id"],))]
        owner_ids = {row[0] for row in conn.execute(
            "SELECT customer_id FROM accounts WHERE account_id=?", (alert["account_id"],))}
        identity_docs = [dict(row) for row in conn.execute(
            "SELECT doc_id, category, verification_status, is_original_upload "
            "FROM case_evidence_sources WHERE customer_id=? AND case_id IS NULL "
            "AND category IN ('kyc_profile','identity_sample')",
            (alert["customer_id"],))]
        source_chunks = [dict(row) for row in conn.execute(
            "SELECT chunk_id, doc_id, chunk_text FROM case_evidence_chunks "
            "WHERE customer_id=? AND (case_id IS NULL OR case_id=?)",
            (alert["customer_id"], case_id))]
        index_status = case_evidence_index_status(conn, case_id)

    query = " ".join(question.lower().split())
    provenance_question = _mentions(query, "saved report", "old report", "snapshot",
                                    "current evidence", "current index", "retrieved case passages",
                                    "zero chunks", "0 chunks", "evidence changed")
    if provenance_question:
        if saved_report_info is None:
            snapshot = "No saved-report evidence snapshot is selected, so I cannot state what an earlier report captured."
        else:
            captured = saved_report_info.get("case_chunk_count")
            captured_text = f"{captured} case passage(s)" if captured is not None else "an unknown number of case passages"
            generated = saved_report_info.get("generated_at") or "an unrecorded time"
            other_counts = [("transaction row(s)", saved_report_info.get("transaction_count")),
                            ("document summary record(s)", saved_report_info.get("document_count")),
                            ("playbook passage(s)", saved_report_info.get("guidance_count"))]
            additional = ", ".join(f"{count} {label}" for label, count in other_counts
                                   if count is not None)
            if additional:
                captured_text += f", plus {additional}"
            snapshot = (f"Saved Report Evidence: the selected report generated at {generated} captured "
                        f"{captured_text}. That count belongs to the saved report, not today's index. "
                        "The historical index snapshot/version was not recorded.")
        built = index_status["built_at_utc"] or "an unrecorded build time"
        current = (f"Current Available Evidence: this case has {index_status['source_count']} source record(s) "
                   f"and {index_status['chunk_count']} indexed passage(s) in the index built at {built}. "
                   "Currently indexed passages can support current Copilot answers, but they do not retroactively "
                   "change the saved report. Different counts do not by themselves mean the older report was wrong. "
                   "The available records do not establish when those additional passages became available.")
        caution = ("An indexed fictional passage is not an authenticated original document or proof that funds "
                   "are lawful or unlawful. Inspect the cited source and its verification status.")
        first_chunk = next((item["chunk_id"] for item in source_chunks
                            if item["doc_id"] == f"CASE-LEDGER-ALL-{case_id}"), None)
        if first_chunk is None:
            first_chunk = next((item["chunk_id"] for item in source_chunks), None)
        cited = [first_chunk] if first_chunk else []
        example = (f"Example currently indexed case passage: {first_chunk}. This passage lets you inspect "
                   "the current source text; it is not proof of the index-build time or historical snapshot."
                   if first_chunk else "No current case passage is available to open.")
        return {"answer": "\n\n".join((snapshot, current, caution, example)), "chunk_ids": cited,
                "txn_ids": [], "sources": cited, "source": "evidence_provenance"}
    chunk_ids: list[str] = []
    txn_ids: list[str] = []
    sections: list[str] = []

    def cite(doc_id: str, needle: str) -> None:
        hit = next((chunk for chunk in source_chunks if chunk["doc_id"] == doc_id
                    and needle in chunk["chunk_text"]), None)
        if hit and hit["chunk_id"] not in chunk_ids:
            chunk_ids.append(hit["chunk_id"])

    def cite_rows(selected: list[dict]) -> None:
        doc_id = f"CASE-LEDGER-ALL-{case_id}"
        for row in selected:
            if row["txn_id"] not in txn_ids:
                txn_ids.append(row["txn_id"])
            cite(doc_id, row["txn_id"])

    if _mentions(query, "related to", "relationship between", "related parties"):
        return {"answer": "The available case evidence does not establish that relationship. "
                "A recorded counterparty account or customer name is not proof of ownership or a personal link. "
                "Request verified ownership and relationship records before drawing a conclusion.",
                "chunk_ids": [], "txn_ids": [], "sources": [], "source": "evidence_limit"}
    if "shell company" in query:
        return {"answer": "The available case records do not establish that this entity is a shell company. "
                "Company registration, beneficial ownership, and business activity would need independent review.",
                "chunk_ids": [], "txn_ids": [], "sources": [], "source": "evidence_limit"}
    if _mentions(query, "why did", "why has", "guess why") and _mentions(
        query, "transfer", "transferred", "send", "sent", "move the money"
    ):
        return {"answer": "The available case evidence does not establish the customer's motive for "
                "the transfer. Transaction records show recorded activity, not intent.",
                "chunk_ids": [], "txn_ids": [], "sources": [], "source": "evidence_limit"}

    month = _month_requested(query, rows)
    selected = [row for row in rows if not month or
                (datetime.fromisoformat(row["txn_datetime"]).year == month[0]
                 and datetime.fromisoformat(row["txn_datetime"]).month == month[1])]
    completed = [row for row in selected if row["status"] == "Completed"]
    wants_count = _mentions(query, "how many", "count", "number of transactions", "total transactions")
    wants_trail = _mentions(query, "trail", "sequence", "timeline", "transaction", "transactions",
                            "when", "from", "where", "transfer", "transfers", "happened", "who",
                            "counterparty", "counterparties")
    wants_totals = _mentions(query, "how much", "amount", "total in", "total out", "credit", "debit")
    wants_signal = _mentions(query, "suspicious", "flag", "flagged", "alert", "risk", "detect",
                             "trigger", "why", "review", "concern", "unusual")
    wants_kyc = _mentions(query, "kyc", "identity", "pan", "passport", "verification", "verified")
    wants_origin = _mentions(query, "source of funds", "origin of funds", "money came from",
                            "where did this customer get", "where did the customer get")
    wants_gaps = _mentions(query, "missing", "gap", "next", "request", "action", "evidence")
    wants_verdict = _mentions(query, "legal", "illegal", "lawful", "unlawful", "fraud", "laundering", "guilty")
    wants_counterview = _mentions(query, "contradict", "against the alert", "against this alert",
                                  "exculpatory", "alternative explanation", "normal explanation",
                                  "innocent explanation")

    if _mentions(query, "summarize this case", "summarise this case", "summarize case",
                 "summarise case", "case summary"):
        sections.append(f"Selected case {case_id}: source alert {alert['alert_id']} records "
                        f"{alert['alert_type']} for customer {alert['customer_id']} and account "
                        f"{alert['account_id']}. The supplied account ledger contains {len(rows)} "
                        f"row(s), including {sum(row['status'] == 'Completed' for row in rows)} "
                        "completed row(s). This is an alert for review, not a finding of wrongdoing.")
        cite(f"CASE-ALERT-{case_id}", "Alert ID:")
        cite(f"CASE-LEDGER-ALL-{case_id}", "stored rows:")
        if len(owner_ids) != 1 or alert["customer_id"] not in owner_ids:
            sections.append("Account-ownership warning: this account ID is missing or assigned to "
                            "multiple customers in the supplied tables. The ledger rows cannot be "
                            "confidently attributed to the selected customer.")
            cite(f"CASE-LEDGER-ALL-{case_id}", "SOURCE-DATA COLLISION")
        return {"answer": "\n\n".join(sections), "chunk_ids": chunk_ids,
                "txn_ids": [], "sources": chunk_ids, "source": "imported_case_database"}

    if _mentions(query, "review window", "alert window") and _mentions(
        query, "how many", "count", "number of transactions"
    ):
        from agents.transaction_investigation_agent import TransactionInvestigationAgent

        window = TransactionInvestigationAgent().run(
            alert["account_id"], alert["alert_date"], trigger_txn_id=alert["trigger_transaction_id"]
        )
        in_window = [] if window["evidence_window_empty"] else window["window_transactions"]
        sections.append(f"Current 10-day alert review window beginning {alert['alert_date']}: "
                        f"{len(in_window)} stored transaction row(s). This is not the full account ledger.")
        cite(f"CASE-ALERT-{case_id}", "Alert date:")
        if in_window:
            cite_rows(in_window)
        else:
            sections.append("The Workspace may show the nearest recorded rows as background context, "
                            "but they are outside this alert's review window and are not trigger evidence.")
            cite(f"CASE-LEDGER-ALL-{case_id}", "stored rows:")
        if len(owner_ids) != 1 or alert["customer_id"] not in owner_ids:
            sections.insert(0, "Account-ownership warning: this account ID is shared or unowned "
                            "in the supplied tables; the rows cannot be confidently attributed "
                            "to this customer.")
        return {"answer": "\n\n".join(sections), "chunk_ids": chunk_ids,
                "txn_ids": txn_ids, "sources": chunk_ids + txn_ids,
                "source": "imported_case_database"}

    if wants_counterview:
        originals = sum(int(doc["is_original_upload"]) for doc in identity_docs)
        sections.append("I cannot identify verified evidence that disproves this alert from the supplied "
                        "records. The alert is a review signal, not proof of wrongdoing; lack of a verified "
                        "contradiction is not proof that the alert is correct.")
        cite(f"CASE-ALERT-{case_id}", "not a legal")
        if not alert["trigger_transaction_id"]:
            sections.append("The source alert has no trigger transaction ID, so its rule label cannot be "
                            "checked against a named transaction here.")
            cite(f"CASE-ALERT-{case_id}", "Trigger transaction ID")
        else:
            sections.append(f"The source alert names {alert['trigger_transaction_id']} as its trigger, "
                            "but this screen does not independently recalculate the source rule.")
        pending = [row for row in rows if row["status"] != "Completed"]
        if pending:
            sections.append(f"{len(pending)} stored row(s) are not marked completed; they should not "
                            "be treated as settled movement without confirmation.")
            cite_rows(pending[:3])
        sections.append(f"The customer KYC field is {customer['kyc_status'] or 'not recorded'}, "
                        f"but {originals} original uploaded identity file(s) are available here. "
                        "A workbook status or generated sample cannot verify identity or a legitimate "
                        "business purpose independently.")
        cite(f"KYC-PROFILE-{alert['customer_id']}", "Dataset KYC status")
        sections.append("To test an alternative explanation, request the original KYC, business-purpose "
                        "and source-of-funds records, and matching counterparty postings. A human reviewer "
                        "must weigh both supporting and contradictory evidence.")
        if len(owner_ids) != 1 or alert["customer_id"] not in owner_ids:
            sections.insert(0, "Account-ownership warning: this account ID maps to multiple customers; "
                            "these account rows cannot be confidently attributed to the selected customer.")
            cite(f"CASE-LEDGER-ALL-{case_id}", "SOURCE-DATA COLLISION")
        return {"answer": "\n\n".join(sections), "chunk_ids": chunk_ids,
                "txn_ids": txn_ids, "sources": chunk_ids + txn_ids,
                "source": "imported_case_database"}

    if wants_count or (month and wants_trail):
        label = f"{calendar.month_name[month[1]]} {month[0]}" if month else "this account's stored dataset"
        sections.append(f"Transaction count in {label}: {len(selected)} stored row(s) "
                        f"({len(completed)} completed, {len(selected) - len(completed)} pending).")
        cite(f"CASE-LEDGER-ALL-{case_id}", "stored rows:")
        cite_rows(selected)
        if month:
            sections.append(f"I used the {month[2]}. This supplied dataset may not cover the whole "
                            "month, so the count is not a complete bank-month total.")

    if wants_totals:
        incoming = sum((Decimal(str(row["amount"])) for row in completed if row["direction"] == "CR"), Decimal(0))
        outgoing = sum((Decimal(str(row["amount"])) for row in completed if row["direction"] == "DR"), Decimal(0))
        scope = f"{calendar.month_name[month[1]]} {month[0]}" if month else "this account's stored dataset"
        sections.append(f"Completed-row amounts in {scope}: INR {incoming:,.2f} incoming and "
                        f"INR {outgoing:,.2f} outgoing. These totals do not trace the same funds "
                        "through another account.")
        cite(f"CASE-LEDGER-ALL-{case_id}", "stored rows:")
        cite_rows(completed)

    if wants_trail and not wants_count:
        if completed:
            sections.append("Recorded completed-row sequence:\n" + "\n".join(
                f"{row['txn_datetime']}: {row['txn_id']} — "
                f"{'IN from' if row['direction'] == 'CR' else 'OUT to'} "
                f"{row['counterparty_account_id'] or 'unknown endpoint'}, "
                f"INR {Decimal(str(row['amount'])):,.2f}"
                for row in completed))
            cite_rows(completed)
        else:
            sections.append("No completed transaction row is stored for this requested period.")
            cite(f"CASE-LEDGER-ALL-{case_id}", "stored rows:")
        sections.append("A recorded counterparty is not verified ownership, a matching opposite-side "
                        "posting, or proof that the same funds continued onward.")

    if wants_signal:
        activity = (evidence or {}).get("activity_24h") or {}
        contributing_ids = set(activity.get("credit_txn_ids", []) + activity.get("debit_txn_ids", []))
        contributors = [row for row in completed if row["txn_id"] in contributing_ids]
        draft_ids = {
            str(txn_id)
            for finding in (report or {}).get("findings", [])
            if finding.get("type") == "red_flag"
            for txn_id in finding.get("supporting_txn_ids", [])
        }
        draft_rows = [row for row in completed if row["txn_id"] in draft_ids]
        trigger_id = alert["trigger_transaction_id"]
        cite(f"CASE-ALERT-{case_id}", "Trigger transaction ID")
        if contributors and alert["alert_id"].startswith("ALERT-TEST-"):
            cite_rows(contributors)
            sections.append(f"Calculated test-alert contributors in this view: "
                            f"{', '.join(row['txn_id'] for row in contributors)}. "
                            "This is a 24-hour account-level review signal, not a finding that each "
                            "transaction is individually suspicious or unlawful.")
        elif draft_rows:
            cite_rows(draft_rows)
            sections.append("The saved investigation draft highlights these recorded rows for follow-up: "
                            + ", ".join(row["txn_id"] for row in draft_rows) + ". "
                            "They are draft red-flag candidates, not independently proved suspicious "
                            "transactions. Verify the underlying ledger and any business explanation.")
            if trigger_id and any(row["txn_id"] == trigger_id for row in selected):
                sections.append(f"Separately, the source alert names {trigger_id} as its trigger transaction.")
        elif trigger_id and any(row["txn_id"] == trigger_id for row in selected):
            row = next(row for row in selected if row["txn_id"] == trigger_id)
            cite_rows([row])
            sections.append(f"The source alert identifies {trigger_id} as its trigger transaction. "
                            "The recorded rule label is not independently recalculated here; it does "
                            "not classify other rows as suspicious or establish unlawful funds.")
        elif trigger_id:
            sections.append(f"The source alert names {trigger_id}, but that row is not in the "
                            "requested period. I cannot identify a qualifying transaction in this view.")
        else:
            sections.append("This imported alert does not identify a trigger transaction. Its rule label "
                            "is source metadata; no individual stored row can be defensibly labelled "
                            "suspicious from that label alone.")

    if wants_kyc:
        originals = sum(int(doc["is_original_upload"]) for doc in identity_docs)
        sections.append(f"KYC: the customer's dataset status is {customer['kyc_status'] or 'not recorded'}, "
                        f"but the case has {originals} original uploaded identity files. "
                        "Generated sample records and a workbook status are not independent identity "
                        "verification. Counterparty KYC is not established by this account ledger.")
        cite(f"KYC-PROFILE-{alert['customer_id']}", "Dataset KYC status")
        for doc in identity_docs:
            if doc["category"] == "identity_sample":
                cite(doc["doc_id"], "not")

    if wants_origin:
        sections.append("The source of funds is not established by independently verified evidence here. "
                        "The source-of-funds field is a fictional customer assertion, not independent "
                        "proof. Cash deposits lack a sender-account trail; transfer endpoints may be "
                        "unmapped. An onward movement cannot be established from one ledger side alone.")
        cite(f"KYC-PROFILE-{alert['customer_id']}", "Declared source of funds")

    if wants_gaps:
        sections.append("Next evidence to request: original identity and KYC checks, independent "
                        "source-of-funds records, counterparty ownership, and matching postings for any "
                        "claimed transfer chain. A human reviewer must decide the case.")
        cite(f"KYC-PROFILE-{alert['customer_id']}", "No issuing authority")
        cite(f"CASE-LEDGER-{case_id}", "not the economic purpose")

    if wants_verdict:
        sections.append("This case does not prove lawful or unlawful money, fraud, or laundering. "
                        "A named human must review independent evidence and record the next action.")
        cite(f"CASE-ALERT-{case_id}", "not a legal")

    if len(owner_ids) != 1 or alert["customer_id"] not in owner_ids:
        sections.insert(0, "Account-ownership warning: this account ID is missing or assigned to "
                        "multiple customers in the supplied tables. The account-level rows below "
                        "cannot be confidently attributed to the selected customer.")
        cite(f"CASE-LEDGER-ALL-{case_id}", "SOURCE-DATA COLLISION")

    if not sections:
        sections.append("Ask about this selected case's stored month count, transaction sequence, "
                        "alert, KYC evidence, or source-of-funds gaps. I cannot check outside bank "
                        "records or determine whether money is lawful.")

    return {"answer": "\n\n".join(sections), "chunk_ids": chunk_ids,
            "txn_ids": txn_ids, "sources": chunk_ids + txn_ids,
            "source": "imported_case_database"}
