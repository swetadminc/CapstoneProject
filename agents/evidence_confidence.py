"""Transparent evidence-support confidence for investigation drafts.

This is deliberately not a fraud, crime, or outcome prediction.  It is a
deterministic rubric that describes how completely the *current draft* is
supported by the records supplied to the investigation pipeline.
"""
from __future__ import annotations

from typing import Any


DISCLAIMER = (
    "This is not a probability of crime, money laundering, or a recommended "
    "case outcome. It measures only how well this draft is supported by the "
    "records and playbook passages supplied to this run. Human review remains required."
)


def _citation_coverage(findings: list[dict[str, Any]]) -> tuple[int, str, list[str]]:
    """Return points, explanation, and limitations for draft-claim citations."""
    reviewable = [
        finding for finding in findings
        if str(finding.get("evidence_status", "")).lower() not in {"missing", "conflicting"}
    ]
    if not reviewable:
        return 0, "No supported or inferred finding was available to cite.", [
            "There are no supported findings with citations in this draft."
        ]

    cited = sum(
        bool(finding.get("supporting_txn_ids") or finding.get("supporting_case_chunk_ids"))
        for finding in reviewable
    )
    points = round(20 * cited / len(reviewable))
    if cited == len(reviewable):
        return points, f"All {cited} supported finding(s) include a record or chunk citation.", []
    return points, f"{cited} of {len(reviewable)} supported finding(s) include a record or chunk citation.", [
        "Some supported findings do not include a direct transaction or source-chunk citation."
    ]


def calculate_evidence_confidence(
    report: dict[str, Any], evidence: dict[str, Any], guidance: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Calculate a repeatable 0-100 evidence-support score.

    The components are intentionally exposed to the user so the score can be
    challenged, not treated as an opaque AI assertion.
    """
    guidance = guidance or []
    findings = report.get("findings") or []
    notes = report.get("_validator_notes") or []
    limitations: list[str] = []
    supported_by: list[str] = []
    components: list[dict[str, Any]] = []

    validator_passed = str(report.get("_validator_result", "")).upper() == "PASS" and not notes
    validator_points = 25 if validator_passed else 10 if str(report.get("_validator_result", "")).upper() == "PASS" else 0
    validator_reason = (
        "Selected grounding checks passed without recorded notes."
        if validator_passed
        else "The grounding validator has notes or did not pass; review them before relying on this draft."
    )
    components.append({"label": "Grounding checks", "points": validator_points, "max_points": 25, "reason": validator_reason})
    (supported_by if validator_points == 25 else limitations).append(validator_reason)

    has_review_window = bool(evidence.get("window_transactions")) and not evidence.get("evidence_window_empty")
    window_points = 20 if has_review_window else 0
    window_reason = (
        f"{len(evidence.get('window_transactions') or [])} transaction record(s) fall in the alert review window."
        if has_review_window
        else "No transaction record is available inside the alert review window; nearby activity is context only."
    )
    components.append({"label": "Review-window records", "points": window_points, "max_points": 20, "reason": window_reason})
    (supported_by if window_points else limitations).append(window_reason)

    citation_points, citation_reason, citation_limits = _citation_coverage(findings)
    components.append({"label": "Finding citations", "points": citation_points, "max_points": 20, "reason": citation_reason})
    (supported_by if citation_points else limitations).append(citation_reason)
    limitations.extend(citation_limits)

    next_steps = report.get("recommended_next_steps") or []
    all_steps_grounded = bool(next_steps) and all(step.get("playbook_doc_id") for step in next_steps)
    guidance_points = 15 if guidance and all_steps_grounded else 0
    guidance_reason = (
        f"{len(guidance)} retrieved playbook passage(s) support the proposed next step(s)."
        if guidance_points
        else "The proposed next steps are not fully linked to retrieved playbook guidance."
    )
    components.append({"label": "Retrieved guidance", "points": guidance_points, "max_points": 15, "reason": guidance_reason})
    (supported_by if guidance_points else limitations).append(guidance_reason)

    ownership_clear = not evidence.get("account_ownership_ambiguous")
    ownership_points = 10 if ownership_clear else 0
    ownership_reason = (
        "No account-ownership collision was reported in the supplied records."
        if ownership_clear
        else "An account ID maps to multiple customer records, so transaction attribution is ambiguous."
    )
    components.append({"label": "Record attribution", "points": ownership_points, "max_points": 10, "reason": ownership_reason})
    (supported_by if ownership_points else limitations).append(ownership_reason)

    has_source_summary = bool(evidence.get("documents") or evidence.get("case_chunks"))
    source_points = 10 if has_source_summary else 0
    source_reason = (
        "A source-document summary or case-index passage was supplied to this run."
        if has_source_summary
        else "No source-document summary or case-index passage was supplied to this run."
    )
    components.append({"label": "Source-document coverage", "points": source_points, "max_points": 10, "reason": source_reason})
    (supported_by if source_points else limitations).append(source_reason)

    explicit_gaps = [finding for finding in findings if str(finding.get("evidence_status", "")).lower() in {"missing", "conflicting"}]
    gap_deduction = min(20, 10 * len(explicit_gaps))
    if gap_deduction:
        gap_reason = f"{len(explicit_gaps)} finding(s) explicitly identifies missing or conflicting evidence."
        components.append({"label": "Explicit evidence gaps", "points": -gap_deduction, "max_points": 0, "reason": gap_reason})
        limitations.append(gap_reason)

    score = max(0, min(100, sum(component["points"] for component in components)))
    rating = "High" if score >= 85 else "Moderate" if score >= 60 else "Low"
    if explicit_gaps and rating == "High":
        rating = "Moderate"

    return {
        "score": score,
        "rating": rating,
        "supported_by": supported_by,
        "limitations": limitations,
        "components": components,
        "disclaimer": DISCLAIMER,
    }
