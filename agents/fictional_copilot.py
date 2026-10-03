"""Case-scoped, source-cited Q&A for the synthetic intake ledger.

This is deterministic retrieval and calculation, not a model or an identity
verification service. The intake packet is loaded from SQLite by the caller;
the exact chunk IDs returned here identify the stored text used in an answer.
"""

from __future__ import annotations

import calendar
import re
from datetime import datetime
from decimal import Decimal


def _mentions(question: str, *phrases: str) -> bool:
    return any(re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", question)
               for phrase in phrases)


def _month_requested(question: str, rows: list[dict]) -> tuple[int, int, str] | None:
    """Resolve a requested month against the case, never the server clock."""
    match = re.search(r"\b(20\d{2})-(0[1-9]|1[0-2])\b", question)
    if match:
        year, month = int(match[1]), int(match[2])
        return year, month, "requested calendar month"
    for month in range(1, 13):
        names = (calendar.month_name[month].lower(), calendar.month_abbr[month].lower())
        for name in names:
            match = re.search(rf"\b{re.escape(name)}\s+(20\d{{2}})\b", question)
            if match:
                return int(match[1]), month, "requested calendar month"
    if not rows:
        return None
    latest = max(datetime.fromisoformat(row["txn_datetime"]) for row in rows)
    if _mentions(question, "last month", "previous month"):
        year, month = latest.year, latest.month - 1
        if month == 0:
            year, month = year - 1, 12
        return year, month, "previous calendar month relative to the latest stored transaction"
    if _mentions(question, "month", "monthly", "one month", "1 month"):
        return latest.year, latest.month, "calendar month containing the latest stored transaction"
    return None


def answer_fictional_case_question(question: str, packet: dict, assessment: dict) -> dict:
    """Answer all recognizable parts of a question using one selected case.

    The signal is an account/window-level review condition. A contributing
    transaction is not independently classified as suspicious or unlawful.
    """
    query = " ".join(question.lower().split())
    case_id = packet["case_id"]
    rows = sorted(packet["transactions"], key=lambda row: (row["txn_datetime"], row["txn_id"]))
    chunks = packet.get("chunks", [])
    chunk_ids: list[str] = []
    txn_ids: list[str] = []

    def cite(doc_kind: str, needle: str) -> None:
        doc_id = f"FIC-{doc_kind}-{case_id}"
        hit = next((chunk for chunk in chunks if chunk["doc_id"] == doc_id
                    and needle in chunk["chunk_text"]), None)
        if hit and hit["chunk_id"] not in chunk_ids:
            chunk_ids.append(hit["chunk_id"])

    def cite_rows(selected: list[dict]) -> None:
        for row in selected:
            if row["txn_id"] not in txn_ids:
                txn_ids.append(row["txn_id"])
            cite("LEDGER", row["txn_id"])

    if not assessment["review_signal_recomputed"] or not assessment["source_integrity_confirmed"]:
        return {
            "answer": "The saved signal or source chunks failed an integrity check. Stop: I cannot safely "
                      "interpret this case until the stored rows and index are repaired.",
            "chunk_ids": [], "txn_ids": [], "sources": [], "source": "calculated_case",
        }

    if _mentions(query, "related to", "relationship between", "related parties"):
        return {"answer": "The available case evidence does not establish that relationship. "
                "Counterparty IDs in this packet do not verify ownership or a personal link.",
                "chunk_ids": [], "txn_ids": [], "sources": [], "source": "evidence_limit"}
    if "shell company" in query:
        return {"answer": "The available case records do not establish that this entity is a shell company. "
                "Independent registration, ownership, and business-activity records are not in this packet.",
                "chunk_ids": [], "txn_ids": [], "sources": [], "source": "evidence_limit"}
    if _mentions(query, "why did", "why has", "guess why") and _mentions(
        query, "transfer", "transferred", "send", "sent", "move the money"
    ):
        return {"answer": "The available case evidence does not establish the customer's motive for "
                "the transfer. Recorded activity alone does not establish intent.",
                "chunk_ids": [], "txn_ids": [], "sources": [], "source": "evidence_limit"}

    if _mentions(query, "summarize this case", "summarise this case", "case summary"):
        cite("ALERT", "Incoming INR")
        cite("LEDGER", "unverified endpoint")
        return {
            "answer": (f"Case {case_id} is a fictional account-level review alert. "
                       f"Its stored packet contains {len(rows)} transaction row(s). "
                       "The saved signal identifies activity for a human to check; it does not prove "
                       "money laundering. The key missing checks are original KYC, the source of "
                       "funds, and verified ownership of transfer endpoints."),
            "chunk_ids": chunk_ids, "txn_ids": [], "sources": chunk_ids,
            "source": "calculated_case",
        }

    if _mentions(query, "request more information"):
        cite("KYC", "KYC verification status")
        cite("ALERT", "External counterparty KYC")
        cite("LEDGER", "unverified endpoint")
        return {
            "answer": (f"For {case_id}, request the original identity/KYC files and their verification "
                       "results; independent source-of-funds records; ownership/KYC for the recorded "
                       "counterparty endpoints; and matching sender/recipient postings for any claimed "
                       "transfer chain. The stored packet has generated identity text and a one-sided "
                       "ledger, not those independent checks. State which record is missing in your "
                       "written rationale, then a named investigator can choose 'Request more "
                       "information' below. This does not mean the documents have been received."),
            "chunk_ids": chunk_ids, "txn_ids": [], "sources": chunk_ids,
            "source": "calculated_case",
        }

    if _mentions(query, "explain for compliance review"):
        signal = packet["signal"]
        cite("ALERT", "Incoming INR")
        cite("KYC", "KYC verification status")
        cite("LEDGER", "unverified endpoint")
        return {
            "answer": (f"Compliance review brief for {case_id}: the fictional packet contains "
                       f"{len(rows)} transaction row(s). Its saved 24-hour account-level signal "
                       f"records incoming at {signal['incoming_multiplier']}x the supplied monthly "
                       f"baseline, outgoing/incoming at {signal['outbound_percent']}%, and "
                       f"{signal['beneficiary_count']} distinct outgoing beneficiary IDs. These are "
                       "reasons to review the account, not a finding that any transaction is illegal. "
                       "Original identity verification, independent source-of-funds proof, and "
                       "counterparty ownership/matching postings are missing. A named investigator "
                       "should record a rationale and choose 'Escalate for Compliance review' below "
                       "only if escalation is warranted. No regulatory report is filed here."),
            "chunk_ids": chunk_ids, "txn_ids": [], "sources": chunk_ids,
            "source": "calculated_case",
        }

    wants_count = _mentions(query, "how many", "count", "number of transactions", "total transactions")
    wants_trail = (_mentions(query, "trail", "sequence", "timeline", "transaction", "transactions",
                             "transfer", "transfers") or
                   (_mentions(query, "counterparty", "counterparties") and
                    not _mentions(query, "kyc", "evidence", "missing", "gap", "verification")))
    wants_totals = _mentions(query, "how much", "amount", "total in", "total out", "credit", "debit")
    wants_signal = _mentions(query, "suspicious", "flag", "flagged", "alert", "risk", "detect",
                             "trigger", "why", "review", "concern", "unusual")
    wants_kyc = _mentions(query, "kyc", "identity", "pan", "passport", "verification", "verified")
    wants_origin = _mentions(query, "source of funds", "origin of funds", "money came from",
                            "where did this customer get", "where did the customer get")
    wants_gaps = _mentions(query, "missing", "gap", "next", "request", "action", "evidence")
    wants_verdict = _mentions(query, "legal", "illegal", "lawful", "unlawful", "fraud", "laundering", "guilty")
    if wants_signal and not _mentions(query, "trail", "sequence", "timeline"):
        wants_trail = False
    month = _month_requested(query, rows)
    selected = [row for row in rows if (not month or
                (datetime.fromisoformat(row["txn_datetime"]).year == month[0]
                 and datetime.fromisoformat(row["txn_datetime"]).month == month[1]))]
    completed = [row for row in selected if row["status"] == "Completed"]
    sections: list[str] = []

    if wants_count or (month and wants_trail):
        label = f"{calendar.month_name[month[1]]} {month[0]}" if month else "this stored case packet"
        pending = len(selected) - len(completed)
        sections.append(f"Transaction count in {label}: {len(selected)} stored row(s) "
                        f"({len(completed)} completed, {pending} pending).")
        cite_rows(selected)
        if month:
            sections.append(f"I used the {month[2]}. This packet may cover only part of that month; "
                            "the count is not a complete bank-month total.")

    if wants_totals:
        incoming = sum((Decimal(str(row["amount"])) for row in completed if row["direction"] == "CR"), Decimal(0))
        outgoing = sum((Decimal(str(row["amount"])) for row in completed if row["direction"] == "DR"), Decimal(0))
        scope = f"{calendar.month_name[month[1]]} {month[0]}" if month else "this stored packet"
        sections.append(f"Completed-row amounts in {scope}: INR {incoming:,.2f} incoming and "
                        f"INR {outgoing:,.2f} outgoing. These are recorded activity totals, not "
                        "a traced source-to-destination balance.")
        cite_rows(completed)

    if wants_trail and not wants_count:
        if completed:
            lines = [f"{row['txn_datetime']}: {row['txn_id']} — "
                     f"{'IN from' if row['direction'] == 'CR' else 'OUT to'} "
                     f"{row['counterparty_account_id']}, INR {Decimal(str(row['amount'])):,.2f}"
                     for row in completed]
            sections.append("Recorded completed-row sequence:\n" + "\n".join(lines))
            cite_rows(completed)
        else:
            sections.append("No completed transaction rows are stored for the requested period.")
        sections.append("Counterparty IDs are unverified endpoints. These rows do not prove the original "
                        "source of funds or that a later debit spent the same incoming money.")

    if wants_signal:
        signal = packet["signal"]
        contributors = set(signal["credit_txn_ids"] + signal["debit_txn_ids"])
        relevant = [row for row in completed if row["txn_id"] in contributors]
        cite("ALERT", "Incoming INR")
        cite_rows(relevant)
        if relevant:
            sections.append(
                f"Review signal: {len(relevant)} completed row(s) in the requested view contribute to "
                f"the saved 24-hour account-level alert: {', '.join(row['txn_id'] for row in relevant)}. "
                f"Across the full alert window, incoming was {signal['incoming_multiplier']}x the supplied "
                f"monthly baseline, outgoing/incoming was {signal['outbound_percent']}%, and there were "
                f"{signal['beneficiary_count']} distinct outgoing beneficiary IDs. The illustrative conditions "
                "are at least 5x, 80%, and three beneficiaries. These rows need review; none is individually "
                "proved suspicious or unlawful."
            )
        else:
            sections.append("No completed row in the requested view contributes to this saved 24-hour "
                            "review signal. That does not establish that other activity is lawful.")

    if wants_kyc:
        identity_docs = [doc for doc in packet["documents"] if doc["category"] in
                         ("kyc_profile", "identity_sample")]
        original_count = sum(int(doc["is_original_upload"]) for doc in identity_docs)
        verified_count = sum(doc["verification_status"] == "verified" for doc in identity_docs)
        sections.append(f"KYC status: {len(identity_docs)} generated profile/identity text record(s), "
                        f"{original_count} original uploaded identity file(s), and {verified_count} "
                        "independently verified identity record(s). The external counterparty IDs have no "
                        "mapped KYC profiles in this packet.")
        cite("KYC", "KYC verification status")
        cite("PAN", "No scan")
        cite("OVD", "No original")

    if wants_origin:
        sections.append("The source of funds is not established in the available evidence. "
                        "The ledger identifies recorded incoming endpoint IDs, but it contains no independent "
                        "source-of-funds proof, verified sender owner, earlier-hop record, or onward settlement.")
        cite("LEDGER", "unverified endpoint")
        cite("KYC", "source-of-funds")

    if wants_gaps:
        sections.append("Evidence still needed: " + " ".join(assessment["missing_evidence"]) + " "
                        + assessment["recommended_action"])
        cite("KYC", "KYC verification status")
        cite("ALERT", "External counterparty KYC")

    if wants_verdict:
        sections.append("No lawful/unlawful or fraud verdict is supported. This is a review signal from "
                        "fictional rows; an accountable investigator must examine independent evidence.")
        cite("ALERT", "not a finding")

    if not sections:
        sections.append("I can answer from this selected case's stored ledger, alert, and generated evidence. "
                        "Ask for a date-range count, transaction trail, review signal, KYC status, missing "
                        "records, or next step. I cannot verify outside records or decide legality.")

    return {
        "answer": "\n\n".join(sections), "chunk_ids": chunk_ids, "txn_ids": txn_ids,
        "sources": chunk_ids + txn_ids, "source": "calculated_case",
    }
