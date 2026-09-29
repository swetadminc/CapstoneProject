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
from agents.investigation_summary_agent import InvestigationSummaryAgent
from agents.grounding_validator import GroundingValidator
from agents.llm_client import GEMINI_MODEL
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

    def investigate(self, case_id: str) -> dict:
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

        txn = self.transaction_investigation.run(alert["account_id"], alert["alert_date"])
        log_audit_event(case_id, actor="ai", action="transaction_investigation_complete",
                         actor_name=self.transaction_investigation.name,
                         details={"transactions_in_window": len(txn["window_transactions"]),
                                   "evidence_window_empty": txn["evidence_window_empty"],
                                   "deviation_ratio": txn["deviation_ratio"]})

        rel = self.relationship.run(alert["account_id"], txn["window_transactions"])
        log_audit_event(case_id, actor="ai", action="relationship_check_complete", actor_name=self.relationship.name,
                         details={"counterparties_checked": len(rel["relationships"])})

        evi = self.evidence.run(alert, case_id)
        log_audit_event(case_id, actor="ai", action="evidence_assembled", actor_name=self.evidence.name,
                         details={"knowledge_chunks_retrieved": [g["chunk_id"] for g in evi["guidance"]],
                                   "documents_on_file": len(evi["documents"])})

        context = {"case_id": case_id, "alert": alert, "customer": kyc["customer"], "account": kyc["account"]}
        evidence = {
            **txn,
            "relationships": rel["relationships"],
            "prior_cases": kyc["prior_cases"],
            "documents": evi["documents"],
        }
        guidance = evi["guidance"]

        raw_report = self.investigation_summary.run(context, evidence, guidance)
        log_audit_event(case_id, actor="ai", action="investigation_summary_complete",
                         actor_name=self.investigation_summary.name,
                         details={"model": GEMINI_MODEL, "findings_drafted": len(raw_report.get("findings", []))})

        validated_report = self.grounding_validator.validate(raw_report, evidence, guidance)
        log_audit_event(case_id, actor="ai", action="report_generated", actor_name=self.grounding_validator.name,
                         details={"model": GEMINI_MODEL,
                                   "validator_result": validated_report["_validator_result"],
                                   "validator_notes": validated_report["_validator_notes"],
                                   "findings_count": len(validated_report.get("findings", []))})

        return {"context": context, "evidence": evidence, "guidance": guidance, "report": validated_report}
