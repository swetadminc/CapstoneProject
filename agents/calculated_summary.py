"""Transparent, non-generative investigation draft from computed evidence."""

from __future__ import annotations


def build_calculated_report(context: dict, evidence: dict, guidance: list) -> dict:
    """Summarize recorded activity without an AI call or a case disposition."""
    activity = evidence.get("activity_24h")
    findings = []
    if evidence.get("account_ownership_ambiguous"):
        findings.append({
            "type": "conflicting",
            "description": "The same account ID is assigned to more than one customer in the source workbook; transaction ownership is unresolved.",
            "evidence_status": "Conflicting", "supporting_txn_ids": [],
            "why_it_matters": "The ledger cannot be attributed to one customer until the source account identifier is corrected.",
        })
    elif activity and activity.get("credit_txn_ids"):
        multiplier = activity.get("incoming_monthly_multiplier")
        comparison = f" ({multiplier}x the six-month monthly credit baseline)" if multiplier is not None else ""
        outbound_pct = activity.get("outgoing_to_incoming_pct")
        outbound = f"{outbound_pct}% of that incoming value" if outbound_pct is not None else "an unquantified amount"
        findings.append({
            "type": "red_flag",
            "description": (f"Recorded 24-hour credits total INR {activity['incoming_total']:,.0f}{comparison}; "
                            f"recorded debits total INR {activity['outgoing_total']:,.0f}, or {outbound}, "
                            f"to {activity['distinct_beneficiaries']} distinct recorded beneficiary IDs."),
            "evidence_status": "Verified",
            "supporting_txn_ids": activity["credit_txn_ids"] + activity["debit_txn_ids"],
            "why_it_matters": "These ledger amounts meet a review signal; they do not prove that the same funds moved onward or establish the purpose of the payments.",
        })
    elif evidence.get("evidence_window_empty"):
        findings.append({
            "type": "missing", "description": "No ledger rows are available inside the alert's review window.",
            "evidence_status": "Missing", "supporting_txn_ids": [],
            "why_it_matters": "Nearby historical rows cannot stand in for the transaction that triggered this alert.",
        })
    else:
        findings.append({
            "type": "red_flag", "description": "Transaction rows exist in the review window and require comparison with the alert rule.",
            "evidence_status": "Verified", "supporting_txn_ids": [t["txn_id"] for t in evidence["window_transactions"]],
            "why_it_matters": "The alert is a starting point for review, not a disposition.",
        })
    findings.append({
        "type": "missing",
        "description": "Original identity documents, independent source-of-funds corroboration, and external counterparty KYC are not supplied in this fictional case package.",
        "evidence_status": "Missing", "supporting_txn_ids": [],
        "why_it_matters": "A customer profile field or generated sample cannot replace an original checked document or an external-bank confirmation.",
    })
    steps = ([{"step": "Review source transactions and request missing identity, purpose and source-of-funds records before deciding the case.",
               "playbook_doc_id": guidance[0]["doc_id"]}] if guidance else [])
    return {
        "findings": findings,
        "investigation_questions": [
            "Who are the senders and beneficiaries, and which identities can be independently confirmed?",
            "What records support the stated purpose of both incoming and outgoing payments?",
            "Are there matching opposite-side postings or only a single account's ledger references?",
        ],
        "recommended_next_steps": steps,
        "narrative_summary": (
            f"{context['case_id']} has a calculated, fictional evidence summary. "
            "The recorded pattern merits review, but the available records cannot determine the purpose or lawfulness of funds. "
            "This is a non-generative draft for a human investigator."
        ),
    }
