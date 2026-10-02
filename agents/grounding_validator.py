# -*- coding: utf-8 -*-
"""
Grounding Validator — the hallucination backstop.

Deliberately NOT one of the six specialist agents (Alert Triage, Customer/
KYC, Transaction Investigation, Relationship, Evidence, Investigation
Summary). Technical Architecture §2 lists it as its own "Validation layer",
separate from the six specialist workflow components. It runs after the
Investigation Summary Agent drafts a report and checks selected citations,
verified-finding requirements, ratio claims, and wording patterns against
the supplied evidence before a human reviews the draft. It cannot verify
every sentence or guarantee that the report is correct.

Citation checks (transaction/doc IDs) catch an invented source. They don't
catch the LLM correctly citing a real source but misquoting a number about
it in its own prose (e.g. writing "9x" when the computed deviation_ratio is
6.6x) — ratio checks below flag that specific gap for human review.
"""
import re

FORBIDDEN_WORDS = ["illegal", "criminal", "guilty", "launderer", "confirmed money laundering", "money laundering confirmed"]
_FORBIDDEN_RE = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(word) for word in sorted(FORBIDDEN_WORDS, key=len, reverse=True)) + r")(?!\w)",
    re.IGNORECASE,
)
_RATIO_RE = re.compile(r"(\d+(?:\.\d+)?)\s*x\b", re.IGNORECASE)


def sanitize_forbidden_wording(value: str, notes: list, where: str) -> str:
    """Remove unsupported verdict language before it can be displayed."""
    text = str(value or "")
    if _FORBIDDEN_RE.search(text):
        notes.append(f"Removed unsupported conclusion wording from {where}")
        return _FORBIDDEN_RE.sub("[conclusion removed for human review]", text)
    return text


class GroundingValidator:
    name = "Grounding Validator"

    def _check_ratio_claims(self, value: str, real_ratio: float, notes: list, where: str,
                            aggregate_ratio: float | None = None):
        """Withhold unsupported "9x"-style prose before it is displayed.

        A cited ID alone cannot establish the numerical wording. With no
        identified trigger, even a previously cached ratio is unsupported.
        """
        mismatch = False
        def replace(match):
            nonlocal mismatch
            claimed = float(match.group(1))
            supported = [ratio for ratio in (real_ratio, aggregate_ratio) if ratio is not None]
            if not any(abs(claimed - ratio) <= 0.05 for ratio in supported):
                mismatch = True
                reason = "no supported ratio" if not supported else f"supported ratio(s): {', '.join(f'{r}x' for r in supported)}"
                notes.append(f"Withheld an unsupported ratio in {where}: text said {claimed}x; {reason}")
                return "[ratio withheld for source review]"
            return match.group(0)
        cleaned = _RATIO_RE.sub(replace, str(value or ""))
        return cleaned, mismatch

    def validate(self, report: dict, evidence: dict, guidance: list) -> dict:
        known_txn_ids = {t["txn_id"] for t in evidence["window_transactions"]}
        known_case_chunk_ids = {p["chunk_id"] for p in evidence.get("case_chunks", [])}
        known_doc_ids = {g["doc_id"] for g in guidance}
        trigger_id = evidence.get("trigger_transaction_id")
        real_ratio = (evidence.get("deviation_ratio") if trigger_id in known_txn_ids
                      and not evidence.get("evidence_window_empty") else None)
        activity = evidence.get("activity_24h") or {}
        scoped_ids = set(activity.get("credit_txn_ids") or [])
        aggregate_ratio = (
            activity.get("incoming_monthly_multiplier")
            if trigger_id in known_txn_ids and scoped_ids and scoped_ids <= known_txn_ids
            and activity.get("historical_monthly_credit", 0) > 0
            and not evidence.get("evidence_window_empty") else None
        )
        notes = []

        for finding in report.get("findings", []):
            cited = set(finding.get("supporting_txn_ids") or [])
            unknown = cited - known_txn_ids
            if unknown:
                notes.append(f"Downgraded a finding: cited unknown txn_id(s) {unknown}")
                finding["evidence_status"] = "Inferred"
                finding["supporting_txn_ids"] = list(cited & known_txn_ids)
            case_cited = set(finding.get("supporting_case_chunk_ids") or [])
            unknown_case = case_cited - known_case_chunk_ids
            if unknown_case:
                notes.append(f"Removed unknown case chunk ID(s) {unknown_case} from a finding")
                finding["supporting_case_chunk_ids"] = sorted(case_cited & known_case_chunk_ids)
            if finding["evidence_status"] == "Verified" and not finding.get("supporting_txn_ids"):
                notes.append("Downgraded a finding: 'Verified' with no citation")
                finding["evidence_status"] = "Inferred"
            if finding["evidence_status"] == "Verified" and evidence.get("evidence_window_empty"):
                notes.append("Downgraded a finding: cited transactions are background context outside the alert review window")
                finding["evidence_status"] = "Inferred"
            if finding["evidence_status"] == "Verified" and evidence.get("account_ownership_ambiguous"):
                notes.append("Downgraded a finding: account ID maps to multiple customers")
                finding["evidence_status"] = "Inferred"

            for field in ("description", "why_it_matters"):
                cleaned = sanitize_forbidden_wording(finding.get(field, ""), notes, "a finding")
                finding[field], ratio_issue = self._check_ratio_claims(cleaned, real_ratio, notes, "a finding", aggregate_ratio)
                if ratio_issue:
                    finding["evidence_status"] = "Inferred"

        valid_steps = []
        for step in report.get("recommended_next_steps", []):
            if step.get("playbook_doc_id") in known_doc_ids:
                cleaned = sanitize_forbidden_wording(step.get("step", ""), notes, "a next step")
                step["step"], _ = self._check_ratio_claims(cleaned, real_ratio, notes, "a next step", aggregate_ratio)
                valid_steps.append(step)
            else:
                notes.append(f"Dropped a next step: cited unknown playbook doc_id '{step.get('playbook_doc_id')}'")
        report["recommended_next_steps"] = valid_steps

        questions = []
        for question in report.get("investigation_questions", []):
            cleaned = sanitize_forbidden_wording(question, notes, "an investigation question")
            checked, _ = self._check_ratio_claims(cleaned, real_ratio, notes, "an investigation question", aggregate_ratio)
            questions.append(checked)
        report["investigation_questions"] = questions
        narrative = sanitize_forbidden_wording(report.get("narrative_summary", ""), notes, "narrative_summary")
        report["narrative_summary"], _ = self._check_ratio_claims(narrative, real_ratio, notes, "narrative_summary", aggregate_ratio)

        report["_validator_notes"] = notes
        report["_validator_result"] = "PASS" if not notes else "REVIEW_REQUIRED"
        return report
