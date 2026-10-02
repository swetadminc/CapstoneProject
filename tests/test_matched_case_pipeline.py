"""Two equal transaction patterns must not produce an unsupported disposition."""

import unittest
from unittest.mock import patch
from io import BytesIO

from pypdf import PdfReader

from agents.orchestrator import InvestigationOrchestrator
from report_pdf import build_report_pdf


class MatchedCasePipelineTests(unittest.TestCase):
    def test_both_cases_have_same_initial_calculated_assessment(self):
        with patch("agents.orchestrator.log_audit_event"):
            first = InvestigationOrchestrator().investigate("CASE-043", draft_mode="calculated")
            second = InvestigationOrchestrator().investigate("CASE-044", draft_mode="calculated")
        for result in (first, second):
            activity = result["evidence"]["activity_24h"]
            self.assertEqual(activity["incoming_total"], 1200000)
            self.assertEqual(activity["outgoing_total"], 1080000)
            self.assertEqual(activity["incoming_monthly_multiplier"], 15)
            self.assertEqual(activity["outgoing_to_incoming_pct"], 90)
            self.assertEqual(activity["distinct_beneficiaries"], 6)
            self.assertEqual(result["report"]["_validator_result"], "PASS")
            self.assertEqual(result["report"]["findings"][1]["evidence_status"], "Missing")
            self.assertIn("request missing", result["report"]["recommended_next_steps"][0]["step"])
            self.assertNotIn("close", result["report"]["narrative_summary"].lower())
            self.assertNotIn("fraud", result["report"]["narrative_summary"].lower())
        self.assertEqual(first["report"]["findings"][0]["description"],
                         second["report"]["findings"][0]["description"])
        pdf = build_report_pdf("CASE-043", first["context"], first["evidence"], first["report"])
        extracted = "\n".join(page.extract_text() for page in PdfReader(BytesIO(pdf)).pages)
        self.assertIn("24-hour incoming: Rs 1,200,000", extracted)
        self.assertIn("non-generative calculation", extracted)
        self.assertIn("No original identity", extracted)


if __name__ == "__main__":
    unittest.main()
