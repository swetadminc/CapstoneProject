# -*- coding: utf-8 -*-
"""
Investigation Orchestrator — pending item #5, the multi-agent split.

Technical Architecture §5 documented this as the roadmap step after the
single-agent prototype: "split into six specialist agents — Alert Triage,
Transaction Investigation, Relationship, Customer/KYC, Evidence,
Investigation Summary — as originally proposed by the team... each future
agent takes over one existing tool-call sequence." This orchestrator is
that split: each agent below is a real, independently-testable class in its
own file, and every agent's completion is its own audit-log entry — not
just a start/end pair around one monolithic function.

The Grounding Validator runs after the Investigation Summary Agent, as its
own validation layer (not one of the six), exactly as Technical
Architecture §2 describes it.

This produces byte-for-byte the same report shape as the original
single-file agent — same schema, same one LLM call, same validator logic —
so every downstream consumer (chat agent, Investigation Demo page, cached
report fixtures) needed no changes.
"""
from agents.alert_triage_agent import AlertTriageAgent
from agents.customer_kyc_agent import CustomerKYCAgent
from agents.transaction_investigation_agent import TransactionInvestigationAgent
from agents.relationship_agent import RelationshipAgent
from agents.evidence_agent import EvidenceAgent
from agents.investigation_summary_agent import InvestigationSummaryAgent, safe_transactions_for_prompt, safe_case_passages_for_prompt
from agents.grounding_validator import GroundingValidator
from agents.llm_client import GEMINI_MODEL
from agents.calculated_summary import build_calculated_report
from data.runtime_db import log_audit_event


class InvestigationOrchestrator:
    def __init__(self):
        self.alert_triage = AlertTriageAgent()
        self.customer_kyc = CustomerKYCAgent()
        self.transaction_investigation = TransactionInvestigationAgent()
        self.relationship = RelationshipAgent()
        self.evidence = EvidenceAgent()
        self.investigation_summary = InvestigationSummaryAgent()
        self.grounding_validator = GroundingValidator()

    def investigate(self, case_id: str, draft_mode: str = "model") -> dict:
        if draft_mode not in {"model", "calculated"}:
            raise ValueError("draft_mode must be model or calculated")
        log_audit_event(case_id, actor="system", action="investigation_started", details={"model": GEMINI_MODEL})

        triage = self.alert_triage.run(case_id)
        alert = triage["alert"]
        log_audit_event(case_id, actor="ai", action="alert_triage_complete", actor_name=self.alert_triage.name,
                         details={"alert_type": alert["alert_type"], "scenario_id": alert.get("scenario_id"),
                                   "severity": alert["severity"]})

        kyc = self.customer_kyc.run(alert, case_id)
        log_audit_event(case_id, actor="ai", action="customer_kyc_complete", actor_name=self.customer_kyc.name,
                         details={"risk_rating": kyc["customer"]["risk_rating"],
                                   "kyc_status": kyc["customer"]["kyc_status"],
                                   "prior_cases_found": len(kyc["prior_cases"])})

        txn = self.transaction_investigation.run(
            alert["account_id"], alert["alert_date"],
            trigger_txn_id=alert.get("trigger_transaction_id"),
        )
        log_audit_event(case_id, actor="ai", action="transaction_investigation_complete",
                         actor_name=self.transaction_investigation.name,
                         details={"transactions_in_window": len(txn["window_transactions"]),
                                   "evidence_window_empty": txn["evidence_window_empty"],
                                   "deviation_ratio": txn["deviation_ratio"]})

        rel = ({"relationships": []} if txn.get("account_ownership_ambiguous") else
               self.relationship.run(alert["account_id"], txn["window_transactions"]))
        log_audit_event(case_id, actor="ai", action="relationship_check_complete", actor_name=self.relationship.name,
                         details={"counterparties_checked": len(rel["relationships"])})

        evi = self.evidence.run(alert, case_id)
        log_audit_event(case_id, actor="ai", action="evidence_assembled", actor_name=self.evidence.name,
                         details={"knowledge_chunks_retrieved": [g["chunk_id"] for g in evi["guidance"]],
                                   "case_chunks_retrieved": [g["chunk_id"] for g in evi.get("case_chunks", [])],
                                   "documents_on_file": len(evi["documents"])})

        context = {"case_id": case_id, "alert": alert, "customer": kyc["customer"], "account": kyc["account"]}
        evidence = {
            **txn,
            "relationships": rel["relationships"],
            "prior_cases": kyc["prior_cases"],
            "documents": evi["documents"],
            "case_chunks": evi.get("case_chunks", []),
        }
        guidance = evi["guidance"]

        _, flagged_reference_ids = safe_transactions_for_prompt(evidence["window_transactions"])
        if flagged_reference_ids:
            log_audit_event(case_id, actor="system", action="untrusted_transaction_reference_withheld",
                            details={"txn_ids": flagged_reference_ids,
                                     "reason": "instruction-like reference text excluded from model prompt"})
        _, flagged_case_chunks = safe_case_passages_for_prompt(evidence.get("case_chunks", []))
        if flagged_case_chunks:
            log_audit_event(case_id, actor="system", action="untrusted_case_passage_withheld",
                            details={"chunk_ids": flagged_case_chunks,
                                     "reason": "instruction-like source text excluded from model prompt"})

        raw_report = (self.investigation_summary.run(context, evidence, guidance)
                      if draft_mode == "model" else build_calculated_report(context, evidence, guidance))
        log_audit_event(case_id, actor="ai", action="investigation_summary_complete",
                         actor_name=self.investigation_summary.name,
                         details={"model": GEMINI_MODEL if draft_mode == "model" else "none — calculated draft",
                                  "findings_drafted": len(raw_report.get("findings", []))})

        validated_report = self.grounding_validator.validate(raw_report, evidence, guidance)
        validated_report["_draft_mode"] = draft_mode
        log_audit_event(case_id, actor="ai", action="report_generated", actor_name=self.grounding_validator.name,
                         details={"model": GEMINI_MODEL if draft_mode == "model" else "none — calculated draft",
                                   "validator_result": validated_report["_validator_result"],
                                   "validator_notes": validated_report["_validator_notes"],
                                   "findings_count": len(validated_report.get("findings", []))})

        return {"context": context, "evidence": evidence, "guidance": guidance, "report": validated_report}
