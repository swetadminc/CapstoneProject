# -*- coding: utf-8 -*-
"""
Investigation Agent — first working slice.

This is a real, working proof that the full pipeline runs end to end:
  DB (deterministic facts) -> RAG retrieval (FTS5) -> Gemini (reasoning) ->
  Grounding Validator (checks every citation) -> structured report.

It is deliberately ONE file and ONE orchestrating function, matching the
prototype-scope decision in the CEO Playbook (Section 5): the five agent
*roles* (Context, Discovery, Evidence/Validation, Conclusion, Grounding
Validator) exist here as clearly separated functions/stages, not five
separate LLM calls. Splitting them into real separate agents is the
documented roadmap step, not a rewrite — each future agent takes over one
function below.

This is a foundation slice for the AI/ML engineer to build on, not the
finished product — the actual prompt tuning, the second/third scenario, and
the full five-agent split are still open work.
"""
import json
import os
import re
import sqlite3
import sys
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
sys.path.insert(0, REPO_ROOT)

from data.knowledge_search import search as search_knowledge, DB_PATH  # noqa: E402

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
# gemini-flash-lite-latest, not gemini-flash-latest: during this build,
# flash-lite reliably returned 200s on real-sized prompts while flash was
# consistently 503 (high demand) — see scripts/test_llm_connection.py for
# how to re-check this if it changes. Overridable via GEMINI_MODEL env var.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "models/gemini-flash-lite-latest")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/{GEMINI_MODEL}:generateContent"

FORBIDDEN_WORDS = ["illegal", "criminal", "guilty", "launderer", "confirmed money laundering", "money laundering confirmed"]

REPORT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "findings": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "type": {"type": "STRING", "enum": ["red_flag", "counter_evidence", "missing", "conflicting"]},
                    "description": {"type": "STRING"},
                    "evidence_status": {"type": "STRING", "enum": ["Verified", "Inferred", "Missing", "Conflicting"]},
                    "supporting_txn_ids": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "why_it_matters": {"type": "STRING"},
                },
                "required": ["type", "description", "evidence_status", "why_it_matters"],
            },
        },
        "investigation_questions": {"type": "ARRAY", "items": {"type": "STRING"}},
        "recommended_next_steps": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "step": {"type": "STRING"},
                    "playbook_doc_id": {"type": "STRING"},
                },
                "required": ["step", "playbook_doc_id"],
            },
        },
        "narrative_summary": {"type": "STRING"},
    },
    "required": ["findings", "investigation_questions", "recommended_next_steps", "narrative_summary"],
}


# ---------------------------------------------------------------------------
# Stage 1 — Context Agent: assemble the case
# ---------------------------------------------------------------------------
def gather_context(case_id: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    alert = cur.execute(
        "SELECT * FROM alerts WHERE case_id = ?", (case_id,)
    ).fetchone()
    if not alert:
        conn.close()
        raise ValueError(f"No alert found for case_id={case_id}")
    alert = dict(alert)

    customer = dict(cur.execute(
        "SELECT * FROM customers WHERE customer_id = ?", (alert["customer_id"],)
    ).fetchone())

    account = dict(cur.execute(
        "SELECT * FROM accounts WHERE account_id = ?", (alert["account_id"],)
    ).fetchone())

    conn.close()
    return {"case_id": case_id, "alert": alert, "customer": customer, "account": account}


# ---------------------------------------------------------------------------
# Stage 2 — Discovery Agent: deterministic transaction/relationship analysis
# (all numbers computed here, by code — never by the LLM)
# ---------------------------------------------------------------------------
def discover_evidence(context: dict, window_days: int = 10) -> dict:
    account_id = context["account"]["account_id"]
    alert_date = context["alert"]["alert_date"]

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Baseline: average transaction amount for this account, excluding the
    # alert window itself, so the "how unusual is this" comparison is fair.
    baseline_row = cur.execute(
        """SELECT AVG(amount) as avg_amt, COUNT(*) as n FROM transactions
           WHERE account_id = ? AND txn_datetime < ?""",
        (account_id, alert_date),
    ).fetchone()
    baseline_avg = baseline_row["avg_amt"] or 0
    baseline_n = baseline_row["n"]

    # Bounded on both ends: this account has multiple historical alerts
    # (e.g. the C1/C2 twin case both sit on ACC-1004), so an unbounded
    # ">= alert_date" filter would pull in a LATER, unrelated alert's
    # transactions too if this alert is the older of the two. window_days
    # matches the R2 rapid-pass-through rule's own review period.
    window_txns = cur.execute(
        """SELECT txn_id, txn_datetime, direction, amount, counterparty_name,
                  counterparty_account_id, reference_text
           FROM transactions
           WHERE account_id = ? AND txn_datetime >= ?
             AND txn_datetime <= datetime(?, '+' || ? || ' days')
           ORDER BY txn_datetime""",
        (account_id, alert_date, alert_date, window_days),
    ).fetchall()
    window_txns = [dict(r) for r in window_txns]

    # Relationships for every counterparty seen in the window.
    counterparty_ids = {t["counterparty_account_id"] for t in window_txns if t["counterparty_account_id"]}
    relationships = []
    for cp_id in counterparty_ids:
        rel = cur.execute(
            """SELECT relationship_type, source, verified, start_date, previously_flagged
               FROM relationships WHERE account_from = ? AND account_to = ?""",
            (account_id, cp_id),
        ).fetchone()
        relationships.append({"counterparty_account_id": cp_id, "relationship": dict(rel) if rel else None})

    # Prior cases for this customer (excluding the current one).
    prior_cases = cur.execute(
        """SELECT case_id, disposition, rationale FROM past_cases
           WHERE customer_id = ? AND case_id != ?""",
        (context["customer"]["customer_id"], context["case_id"]),
    ).fetchall()
    prior_cases = [dict(r) for r in prior_cases]

    # Documents on file for this case.
    documents = cur.execute(
        """SELECT doc_id, doc_type, doc_date, extracted_summary, verified
           FROM documents WHERE case_id = ?""",
        (context["case_id"],),
    ).fetchall()
    documents = [dict(r) for r in documents]

    conn.close()

    trigger_amt = window_txns[0]["amount"] if window_txns else 0
    deviation_ratio = round(trigger_amt / baseline_avg, 1) if baseline_avg else None

    return {
        "baseline_avg_amount": round(baseline_avg, 2),
        "baseline_txn_count": baseline_n,
        "deviation_ratio": deviation_ratio,
        "window_transactions": window_txns,
        "relationships": relationships,
        "prior_cases": prior_cases,
        "documents": documents,
    }


# ---------------------------------------------------------------------------
# Stage 3 — retrieve relevant playbook guidance (RAG, keyword/FTS5 today)
# ---------------------------------------------------------------------------
def retrieve_guidance(context: dict, evidence: dict, k: int = 4) -> list:
    query = f"{context['alert']['alert_type']} {context['alert']['scenario_id']}"
    return search_knowledge(query, k=k, scenario_id=context["alert"].get("scenario_id"))


# ---------------------------------------------------------------------------
# Stage 4 — Conclusion Agent: the one LLM call, tightly grounded
# ---------------------------------------------------------------------------
def build_prompt(context: dict, evidence: dict, guidance: list) -> str:
    return f"""You are an AML investigation assistant. You NEVER decide guilt or
innocence, and you NEVER use the words illegal, criminal, guilty, or state
that money laundering is confirmed. An identified pattern is a reason to
investigate further, not a conclusion. You may ONLY state a finding as
"Verified" if you cite a specific transaction ID (txn_id) from the evidence
below that directly supports it. If you cannot cite a specific record, use
"Inferred" or "Missing" instead. Every recommended next step MUST cite one of
the playbook document IDs given below — never invent a next step that isn't
grounded in one of them.

CASE
case_id: {context['case_id']}
alert_type: {context['alert']['alert_type']}
severity: {context['alert']['severity']}

CUSTOMER
name: {context['customer']['name']}
type: {context['customer']['type']}
occupation_or_industry: {context['customer'].get('occupation_or_industry')}
risk_rating: {context['customer']['risk_rating']}
kyc_status: {context['customer']['kyc_status']}

TRANSACTION ANALYSIS (computed, not estimated)
baseline_avg_amount: {evidence['baseline_avg_amount']}
deviation_ratio: {evidence['deviation_ratio']}x baseline
window_transactions: {json.dumps(evidence['window_transactions'], default=str)}

RELATIONSHIPS
{json.dumps(evidence['relationships'], default=str)}

PRIOR CASES FOR THIS CUSTOMER
{json.dumps(evidence['prior_cases'], default=str) if evidence['prior_cases'] else "None found."}

DOCUMENTS ON FILE
{json.dumps(evidence['documents'], default=str) if evidence['documents'] else "None found."}

RELEVANT PLAYBOOK GUIDANCE (cite these doc_ids in recommended_next_steps)
{json.dumps([{"doc_id": g["doc_id"], "text": g["chunk_text"]} for g in guidance], default=str)}

Produce the investigation report now, following the given JSON schema exactly.
"""


def call_gemini(prompt: str, max_retries: int = 3) -> dict:
    """Gemini's flash tier returns transient 503s under load reasonably
    often (observed during this build) — retry with backoff rather than
    failing the whole investigation on a temporary blip. This is exactly
    the kind of thing the cached-report fallback (CEO Playbook, Section 12)
    exists for at demo time; this retry is the first, cheaper line of
    defense before falling back to a cached report."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set in the environment.")

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(
                GEMINI_URL,
                params={"key": GEMINI_API_KEY},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "responseMimeType": "application/json",
                        "responseSchema": REPORT_SCHEMA,
                    },
                },
                timeout=60,
            )
            if resp.status_code == 503 and attempt < max_retries:
                time.sleep(2 * attempt)
                continue
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
        except requests.exceptions.RequestException as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(2 * attempt)
    raise last_error


# ---------------------------------------------------------------------------
# Stage 5 — Grounding Validator: the hallucination backstop
# ---------------------------------------------------------------------------
def validate_report(report: dict, evidence: dict, guidance: list) -> dict:
    known_txn_ids = {t["txn_id"] for t in evidence["window_transactions"]}
    known_doc_ids = {g["doc_id"] for g in guidance}
    notes = []

    for finding in report.get("findings", []):
        cited = set(finding.get("supporting_txn_ids") or [])
        unknown = cited - known_txn_ids
        if unknown:
            notes.append(f"Downgraded a finding: cited unknown txn_id(s) {unknown}")
            finding["evidence_status"] = "Inferred"
            finding["supporting_txn_ids"] = list(cited & known_txn_ids)
        if finding["evidence_status"] == "Verified" and not finding.get("supporting_txn_ids"):
            notes.append("Downgraded a finding: 'Verified' with no citation")
            finding["evidence_status"] = "Inferred"

        text = f"{finding.get('description', '')} {finding.get('why_it_matters', '')}".lower()
        for word in FORBIDDEN_WORDS:
            if word in text:
                notes.append(f"Flagged forbidden wording in a finding: '{word}'")

    valid_steps = []
    for step in report.get("recommended_next_steps", []):
        if step.get("playbook_doc_id") in known_doc_ids:
            valid_steps.append(step)
        else:
            notes.append(f"Dropped a next step: cited unknown playbook doc_id '{step.get('playbook_doc_id')}'")
    report["recommended_next_steps"] = valid_steps

    summary_lower = report.get("narrative_summary", "").lower()
    for word in FORBIDDEN_WORDS:
        if word in summary_lower:
            notes.append(f"Flagged forbidden wording in narrative_summary: '{word}'")

    report["_validator_notes"] = notes
    report["_validator_result"] = "PASS" if not notes else "PASS_WITH_CORRECTIONS"
    return report


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------
def investigate(case_id: str) -> dict:
    context = gather_context(case_id)
    evidence = discover_evidence(context)
    guidance = retrieve_guidance(context, evidence)
    prompt = build_prompt(context, evidence, guidance)
    raw_report = call_gemini(prompt)
    validated_report = validate_report(raw_report, evidence, guidance)
    return {
        "context": context,
        "evidence": evidence,
        "guidance": guidance,
        "report": validated_report,
    }


if __name__ == "__main__":
    import sys as _sys
    case = _sys.argv[1] if len(_sys.argv) > 1 else "CASE-001"
    result = investigate(case)
    print(json.dumps(result["report"], indent=2))
