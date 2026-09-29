# -*- coding: utf-8 -*-
"""
Investigation Summary Agent — sixth and last of the specialist agents (see
alert_triage_agent.py for the roadmap reference).

The only agent that calls the LLM. Takes the outputs of every other agent
(triage, KYC, transactions, relationships, evidence) and drafts the
structured report: findings, investigation questions, recommended next
steps, narrative summary. Its output is a *draft* — the Grounding Validator
(a separate validation layer, not one of the six specialist agents, per
Technical Architecture §2) checks every citation before anything reaches a
human.
"""
import json

from agents.llm_client import call_gemini

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


class InvestigationSummaryAgent:
    name = "Investigation Summary Agent"

    def build_prompt(self, context: dict, evidence: dict, guidance: list) -> str:
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
deviation_ratio: {f"{evidence['deviation_ratio']}x baseline" if evidence['deviation_ratio'] is not None else "not computable — see note below"}
{"NOTE: no transactions fell within this alert's review window (the account had no recorded activity in that period). The transactions below are the nearest ones in time, shown ONLY as background context — do NOT treat any of them as the transaction that triggered this alert, and say plainly in your findings that the review window itself was empty." if evidence['evidence_window_empty'] else "window_transactions (within the alert's review window):"}
{json.dumps(evidence['window_transactions'], default=str)}

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

    def run(self, context: dict, evidence: dict, guidance: list) -> dict:
        prompt = self.build_prompt(context, evidence, guidance)
        return call_gemini(prompt, REPORT_SCHEMA)
