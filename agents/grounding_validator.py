# -*- coding: utf-8 -*-
"""
Grounding Validator — the hallucination backstop.

Deliberately NOT one of the six specialist agents (Alert Triage, Customer/
KYC, Transaction Investigation, Relationship, Evidence, Investigation
Summary). Technical Architecture §2 lists it as its own "Validation layer",
separate from the "AI layer" the six agents belong to — it runs after the
Investigation Summary Agent drafts a report and checks every claim in that
draft against the real evidence, before anything reaches a human.
"""

FORBIDDEN_WORDS = ["illegal", "criminal", "guilty", "launderer", "confirmed money laundering", "money laundering confirmed"]


class GroundingValidator:
    name = "Grounding Validator"

    def validate(self, report: dict, evidence: dict, guidance: list) -> dict:
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
