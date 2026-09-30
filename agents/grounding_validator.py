# -*- coding: utf-8 -*-
"""
Grounding Validator — the hallucination backstop.

Deliberately NOT one of the six specialist agents (Alert Triage, Customer/
KYC, Transaction Investigation, Relationship, Evidence, Investigation
Summary). Technical Architecture §2 lists it as its own "Validation layer",
separate from the "AI layer" the six agents belong to — it runs after the
Investigation Summary Agent drafts a report and checks every claim in that
draft against the real evidence, before anything reaches a human.

Citation checks (transaction/doc IDs) catch an invented source. They don't
catch the LLM correctly citing a real source but misquoting a number about
it in its own prose (e.g. writing "9x" when the computed deviation_ratio is
6.6x) — _check_deviation_claims below closes that specific gap.
"""
import re

FORBIDDEN_WORDS = ["illegal", "criminal", "guilty", "launderer", "confirmed money laundering", "money laundering confirmed"]
_RATIO_RE = re.compile(r"(\d+(?:\.\d+)?)\s*x\b", re.IGNORECASE)


class GroundingValidator:
    name = "Grounding Validator"

    def _check_ratio_claims(self, text: str, real_ratio: float, notes: list, where: str):
        """Flags a "9x"-style claim in free prose that doesn't match the
        real computed deviation_ratio — citation checks alone wouldn't
        catch a real source misquoted in the model's own sentence."""
        for match in _RATIO_RE.finditer(text):
            claimed = float(match.group(1))
            if abs(claimed - real_ratio) > 0.05:
                notes.append(
                    f"Flagged a number mismatch in {where}: text says {claimed}x but the computed "
                    f"deviation_ratio is {real_ratio}x"
                )

    def validate(self, report: dict, evidence: dict, guidance: list) -> dict:
        known_txn_ids = {t["txn_id"] for t in evidence["window_transactions"]}
        known_doc_ids = {g["doc_id"] for g in guidance}
        real_ratio = evidence.get("deviation_ratio")
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

            raw_text = f"{finding.get('description', '')} {finding.get('why_it_matters', '')}"
            text = raw_text.lower()
            for word in FORBIDDEN_WORDS:
                if word in text:
                    notes.append(f"Flagged forbidden wording in a finding: '{word}'")
            if real_ratio is not None:
                self._check_ratio_claims(raw_text, real_ratio, notes, "a finding")

        valid_steps = []
        for step in report.get("recommended_next_steps", []):
            if step.get("playbook_doc_id") in known_doc_ids:
                valid_steps.append(step)
            else:
                notes.append(f"Dropped a next step: cited unknown playbook doc_id '{step.get('playbook_doc_id')}'")
        report["recommended_next_steps"] = valid_steps

        narrative = report.get("narrative_summary", "")
        summary_lower = narrative.lower()
        for word in FORBIDDEN_WORDS:
            if word in summary_lower:
                notes.append(f"Flagged forbidden wording in narrative_summary: '{word}'")
        if real_ratio is not None:
            self._check_ratio_claims(narrative, real_ratio, notes, "narrative_summary")

        report["_validator_notes"] = notes
        report["_validator_result"] = "PASS" if not notes else "PASS_WITH_CORRECTIONS"
        return report
