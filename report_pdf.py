# -*- coding: utf-8 -*-
"""
PDF export of an investigation report — for the case file / compliance
record, not just an on-screen view.

Uses fpdf2's built-in Helvetica core font (no font files to bundle or
host), which only supports Latin-1. `_safe()` below sanitizes text before
it's written so a rupee sign, em dash, or smart quote in generated LLM text
can't crash the export — it degrades to a plain-ASCII equivalent instead.
"""
import datetime

from fpdf import FPDF
from fpdf.enums import XPos, YPos

_REPLACEMENTS = {
    "₹": "Rs ", "—": "-", "–": "-", "‘": "'", "’": "'",
    "“": '"', "”": '"', "…": "...", "→": "->", "✓": "OK",
}


def _safe(text) -> str:
    text = str(text)
    for src, dst in _REPLACEMENTS.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", errors="replace").decode("latin-1")


class _ReportPDF(FPDF):
    """Every cell()/multi_cell() call below passes new_x=LMARGIN,
    new_y=NEXT explicitly. fpdf2's default end position for a full-width
    (w=0) cell leaves the cursor at the RIGHT margin, not back at the left
    — the deprecated ln=True shortcut used to paper over this, but without
    it (or without these explicit params) every subsequent multi_cell call
    starts with ~0 width left on the line and raises FPDFException("Not
    enough horizontal space to render a single character")."""

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(26, 42, 74)
        self.cell(0, 9, "InvestigateIQ - Investigation Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(46, 99, 191)
        self.set_line_width(0.6)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 10, _safe(f"Page {self.page_no()} - All data fictional - Prototype output, not a filed report"), align="C")

    def section_title(self, text):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(26, 42, 74)
        self.cell(0, 8, _safe(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0, 0, 0)

    def body(self, text, style="", size=10):
        self.set_font("Helvetica", style, size)
        self.multi_cell(0, 5.5, _safe(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def build_report_pdf(case_id: str, context: dict, evidence: dict, report: dict,
                      human_action: dict = None) -> bytes:
    """Renders the same findings/questions/next-steps/narrative shown on the
    Investigation Demo page into a downloadable PDF. Takes the already-
    validated report dict — this never re-runs the agent or the LLM."""
    pdf = _ReportPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    generated_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 6, _safe(f"Generated {generated_at}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, _safe(f"{case_id} - {context['customer']['name']}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.body(
        f"Alert type: {context['alert']['alert_type']}\n"
        f"Severity: {context['alert']['severity']}\n"
        f"Scenario: {context['alert'].get('scenario_id')}\n"
        f"Recorded rule label: {context['alert'].get('trigger_rule') or 'not supplied'} "
        f"({'calculated from fictional matched-case rows' if context['alert']['alert_id'].startswith('ALERT-TEST-') else 'source dataset; not recalculated in this report'})\n"
        f"Trigger transaction ID: {context['alert'].get('trigger_transaction_id') or 'not supplied'}\n"
        f"Customer risk rating: {context['customer'].get('risk_rating')} | "
        f"KYC status: {context['customer'].get('kyc_status')}"
    )
    if not context["alert"].get("trigger_transaction_id"):
        pdf.body("Source alert has no trigger-transaction ID; recorded rule label is not independently verified.")
    if evidence.get("account_ownership_ambiguous"):
        pdf.body("SOURCE-DATA COLLISION: account ID maps to multiple customer rows. Ledger activity cannot be attributed to this customer without correction.")
    pdf.body("KYC status is a fictional source-data field. No original identity or source-of-funds file is independently verified in this case package.")
    pdf.ln(3)

    pdf.section_title("Transaction Analysis")
    dev = f"{evidence['deviation_ratio']}x baseline" if evidence.get("deviation_ratio") is not None else "not computable"
    window_note = " (no transactions fell within the review window - nearest activity shown for context)" \
        if evidence.get("evidence_window_empty") else ""
    pdf.body(
        f"{'Mixed-ID baseline (unreliable)' if evidence.get('account_ownership_ambiguous') else 'Baseline avg. transaction amount'}: Rs {evidence['baseline_avg_amount']:,.2f}\n"
        f"Trigger/baseline ratio: {dev}\n"
        f"Transactions considered: {len(evidence['window_transactions'])}{window_note}\n"
        f"Prior cases on file for this customer: {len(evidence.get('prior_cases', []))}"
    )
    activity = evidence.get("activity_24h")
    if activity:
        monthly_ratio = (f"{activity['incoming_monthly_multiplier']}x" if activity['incoming_monthly_multiplier'] is not None
                         else "not computable")
        outbound_ratio = (f"{activity['outgoing_to_incoming_pct']}%" if activity['outgoing_to_incoming_pct'] is not None
                          else "not computable")
        pdf.body(
            f"24-hour incoming: Rs {activity['incoming_total']:,.0f} | outgoing: Rs {activity['outgoing_total']:,.0f}\n"
            f"Previous six-month average monthly credits: Rs {activity['historical_monthly_credit']:,.0f}\n"
            f"Aggregate incoming/monthly baseline: {monthly_ratio} | "
            f"outgoing/incoming: {outbound_ratio} | "
            f"beneficiary IDs: {activity['distinct_beneficiaries']}\n"
            "These are account-activity ratios, not proof that the incoming funds financed the outgoing payments."
        )
    pdf.ln(3)

    pdf.section_title(f"Findings ({len(report.get('findings', []))})")
    for f in report.get("findings", []):
        pdf.set_font("Helvetica", "B", 10)
        pdf.multi_cell(0, 5.5, _safe(f"[{f['type'].upper()}] {f['evidence_status']}"),
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.body(f["description"])
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(90, 90, 90)
        pdf.multi_cell(0, 5, _safe(f["why_it_matters"]), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)
        if f.get("supporting_txn_ids"):
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(0, 5, _safe("Citations: " + ", ".join(f["supporting_txn_ids"])),
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        if f.get("supporting_case_chunk_ids"):
            pdf.body("Case source chunks: " + ", ".join(f["supporting_case_chunk_ids"]), size=9)
        pdf.ln(2)

    pdf.section_title("Investigation Questions")
    for q in report.get("investigation_questions", []):
        pdf.body(f"- {q}")
    pdf.ln(2)

    pdf.section_title("Recommended Next Steps")
    if report.get("recommended_next_steps"):
        for step in report["recommended_next_steps"]:
            pdf.body(f"- {step['step']} [Retrieved: {step['playbook_doc_id']}]")
    else:
        pdf.body("No grounded next step available from the knowledge base for this scenario.")
    pdf.ln(2)

    pdf.section_title("Narrative Summary")
    pdf.body("Draft mode: " + ("non-generative calculation" if report.get("_draft_mode") == "calculated" else "model-assisted or saved replay"), size=9)
    pdf.body(report.get("narrative_summary", ""))
    pdf.ln(3)

    pdf.section_title("Grounding Validator")
    notes = report.get("_validator_notes") or []
    pdf.body(
        f"Result: {report.get('_validator_result', 'N/A')}\n"
        + ("No issues found by selected checks; human review is still required."
           if not notes else "Validator notes for human review:\n" + "\n".join(f"- {n}" for n in notes))
    )
    pdf.ln(3)

    confidence = report.get("_evidence_confidence")
    if confidence:
        pdf.section_title("Evidence Confidence")
        pdf.body(
            f"Evidence support score: {confidence.get('score', 'N/A')} / 100 ({confidence.get('rating', 'N/A')})\n"
            + confidence.get("disclaimer", "")
        )
        components = confidence.get("components") or []
        if components:
            pdf.body("Transparent score components:\n" + "\n".join(
                f"- {item.get('label')}: {item.get('points')} of {item.get('max_points')} - {item.get('reason')}"
                for item in components
            ), size=9)
        limitations = confidence.get("limitations") or []
        if limitations:
            pdf.body("Known limitations for human review:\n" + "\n".join(
                f"- {item}" for item in limitations
            ), size=9)
        pdf.ln(3)

    pdf.section_title("Human Decision")
    if human_action:
        pdf.body(
            f"Investigator: {human_action['investigator']}\n"
            f"Decision: {human_action['action']}\n"
            f"Rationale: {human_action['rationale']}\n"
            f"Recorded: {human_action['timestamp']}"
        )
    else:
        pdf.body("No decision has been recorded for this case yet — this report reflects the AI-assisted "
                  "draft only. AI findings are not a final disposition (BR1, BR4).")

    return bytes(pdf.output())
