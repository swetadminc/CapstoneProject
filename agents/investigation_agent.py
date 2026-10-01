# -*- coding: utf-8 -*-
"""
Investigation Agent — compatibility facade over the six-agent pipeline.

Pending item #5 (the multi-agent split) replaced the single orchestrating
function that used to live in this file with six real, separately-testable
agent classes (agents/alert_triage_agent.py through
agents/investigation_summary_agent.py), a standalone Grounding Validator
(agents/grounding_validator.py), and an Orchestrator that wires them
together (agents/orchestrator.py) — matching the roadmap documented in
Technical Architecture §5 and the Delivery Plan's Phase 3.

This file now exists only so nothing that already imports from it (the
Investigation Demo page, the Chat Agent, generate_cached_reports.py, and
the prompt-injection safety test) has to change: every name below delegates
to the real agent that now owns that responsibility. `discover_evidence`
in particular is a thin wrapper composing three separate agents' outputs
into the exact same return shape it always had, because a safety-critical
test (scripts/test_prompt_injection.py) calls it directly with a synthetic,
not-in-the-database context.
"""
from agents.alert_triage_agent import AlertTriageAgent
from agents.customer_kyc_agent import CustomerKYCAgent
from agents.transaction_investigation_agent import TransactionInvestigationAgent
from agents.relationship_agent import RelationshipAgent
from agents.evidence_agent import EvidenceAgent
from agents.investigation_summary_agent import InvestigationSummaryAgent, REPORT_SCHEMA
from agents.grounding_validator import GroundingValidator, FORBIDDEN_WORDS
from agents.orchestrator import InvestigationOrchestrator
from agents.llm_client import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_URL, call_gemini as _call_gemini
from data.knowledge_search import DB_PATH

__all__ = [
    "GEMINI_API_KEY", "GEMINI_MODEL", "GEMINI_URL", "DB_PATH", "REPORT_SCHEMA", "FORBIDDEN_WORDS",
    "gather_context", "discover_evidence", "retrieve_guidance", "build_prompt", "call_gemini",
    "validate_report", "investigate",
]


def gather_context(case_id: str) -> dict:
    triage = AlertTriageAgent().run(case_id)
    kyc = CustomerKYCAgent().run(triage["alert"], case_id)
    return {"case_id": case_id, "alert": triage["alert"], "customer": kyc["customer"], "account": kyc["account"]}


def discover_evidence(context: dict, window_days: int = 10) -> dict:
    account_id = context["account"]["account_id"]
    alert_date = context["alert"]["alert_date"]

    txn = TransactionInvestigationAgent().run(
        account_id, alert_date, window_days=window_days,
        trigger_txn_id=context["alert"].get("trigger_transaction_id"),
    )
    rel = RelationshipAgent().run(account_id, txn["window_transactions"])
    kyc = CustomerKYCAgent().run(context["alert"], context["case_id"])
    documents = EvidenceAgent().documents_for(context["case_id"])

    return {
        **txn,
        "relationships": rel["relationships"],
        "prior_cases": kyc["prior_cases"],
        "documents": documents,
    }


def retrieve_guidance(context: dict, evidence: dict, k: int = 4) -> list:
    return EvidenceAgent().guidance_for(context["alert"], k=k)


def build_prompt(context: dict, evidence: dict, guidance: list) -> str:
    return InvestigationSummaryAgent().build_prompt(context, evidence, guidance)


def call_gemini(prompt: str, schema: dict = None, max_retries: int = 3) -> dict:
    return _call_gemini(prompt, schema or REPORT_SCHEMA, max_retries)


def validate_report(report: dict, evidence: dict, guidance: list) -> dict:
    return GroundingValidator().validate(report, evidence, guidance)


def investigate(case_id: str) -> dict:
    return InvestigationOrchestrator().investigate(case_id)


if __name__ == "__main__":
    import json
    import sys as _sys
    case = _sys.argv[1] if len(_sys.argv) > 1 else "CASE-001"
    result = investigate(case)
    print(json.dumps(result["report"], indent=2))
