"""Behavior checks for the report guardrail without calling a model."""

import unittest
import json
from pathlib import Path

from agents.grounding_validator import GroundingValidator, FORBIDDEN_WORDS
from agents.transaction_investigation_agent import anchor_cached_evidence
from report_pdf import build_report_pdf


class GroundingValidatorTests(unittest.TestCase):
    def setUp(self):
        self.evidence = {"window_transactions": [{"txn_id": "TXN-1"}],
                         "deviation_ratio": 2.0, "trigger_transaction_id": "TXN-1"}
        self.guidance = [{"doc_id": "PB-1"}]

    def report(self):
        return {
            "findings": [{
                "type": "red_flag",
                "description": "2x the baseline",
                "evidence_status": "Verified",
                "supporting_txn_ids": ["TXN-1"],
                "why_it_matters": "Review the pattern",
            }],
            "investigation_questions": ["What source documents exist?"],
            "recommended_next_steps": [{"step": "Review documents", "playbook_doc_id": "PB-1"}],
            "narrative_summary": "The alert needs human review.",
        }

    def test_clean_report_passes(self):
        result = GroundingValidator().validate(self.report(), self.evidence, self.guidance)
        self.assertEqual(result["_validator_result"], "PASS")
        self.assertEqual(result["_validator_notes"], [])

    def test_unsupported_verdict_wording_is_removed_everywhere(self):
        report = self.report()
        report["findings"][0]["description"] = "The customer is a criminal"
        report["findings"][0]["why_it_matters"] = "This is illegal"
        report["investigation_questions"] = ["Is the customer guilty?"]
        report["recommended_next_steps"][0]["step"] = "Label the counterparty a launderer"
        report["narrative_summary"] = "Confirmed money laundering"
        result = GroundingValidator().validate(report, self.evidence, self.guidance)
        displayed = " ".join([
            result["findings"][0]["description"], result["findings"][0]["why_it_matters"],
            *result["investigation_questions"], result["recommended_next_steps"][0]["step"],
            result["narrative_summary"],
        ]).lower()
        self.assertEqual(result["_validator_result"], "REVIEW_REQUIRED")
        for word in FORBIDDEN_WORDS:
            self.assertNotIn(word, displayed)
        self.assertIn("[conclusion removed for human review]", displayed)

    def test_bad_citations_are_downgraded_or_dropped(self):
        report = self.report()
        report["findings"][0]["supporting_txn_ids"] = ["UNKNOWN"]
        report["recommended_next_steps"][0]["playbook_doc_id"] = "UNKNOWN"
        result = GroundingValidator().validate(report, self.evidence, self.guidance)
        self.assertEqual(result["findings"][0]["evidence_status"], "Inferred")
        self.assertEqual(result["findings"][0]["supporting_txn_ids"], [])
        self.assertEqual(result["recommended_next_steps"], [])
        self.assertEqual(result["_validator_result"], "REVIEW_REQUIRED")

    def test_mismatched_ratio_requires_review(self):
        report = self.report()
        report["findings"][0]["description"] = "9x the baseline"
        result = GroundingValidator().validate(report, self.evidence, self.guidance)
        self.assertEqual(result["findings"][0]["evidence_status"], "Inferred")
        self.assertNotIn("9x", result["findings"][0]["description"])
        self.assertEqual(result["_validator_result"], "REVIEW_REQUIRED")

    def test_unanchored_ratio_is_withheld(self):
        report = self.report()
        evidence = {**self.evidence, "deviation_ratio": None, "trigger_transaction_id": None}
        report["findings"][0]["description"] = "0.9x baseline"
        report["narrative_summary"] = "The deviation was 0.9x."
        result = GroundingValidator().validate(report, evidence, self.guidance)
        self.assertEqual(result["_validator_result"], "REVIEW_REQUIRED")
        self.assertEqual(result["findings"][0]["evidence_status"], "Inferred")
        self.assertNotIn("0.9x", result["findings"][0]["description"])
        self.assertNotIn("0.9x", result["narrative_summary"])

    def test_ratio_is_withheld_when_trigger_id_is_not_in_evidence(self):
        report = self.report()
        evidence = {**self.evidence, "trigger_transaction_id": "TXN-NOT-IN-WINDOW"}
        result = GroundingValidator().validate(report, evidence, self.guidance)
        self.assertEqual(result["_validator_result"], "REVIEW_REQUIRED")
        self.assertNotIn("2x", result["findings"][0]["description"])

    def test_background_transactions_cannot_verify_alert_window_finding(self):
        report = self.report()
        evidence = {**self.evidence, "evidence_window_empty": True, "deviation_ratio": None}
        result = GroundingValidator().validate(report, evidence, self.guidance)
        self.assertEqual(result["findings"][0]["evidence_status"], "Inferred")
        self.assertEqual(result["_validator_result"], "REVIEW_REQUIRED")

    def test_every_cached_case_replays_and_exports_offline(self):
        cache_dir = Path(__file__).resolve().parents[1] / "data" / "cached_reports"
        paths = sorted(cache_dir.glob("CASE-*.json"))
        self.assertEqual(len(paths), 5, "Review this test when the demo cache set changes")
        for path in paths:
            with self.subTest(case=path.stem):
                cached = json.loads(path.read_text(encoding="utf-8"))
                evidence = anchor_cached_evidence(cached["evidence"], cached["context"]["alert"])
                report = GroundingValidator().validate(
                    cached["report"], evidence, cached["guidance"]
                )
                self.assertIn(report["_validator_result"], {"PASS", "REVIEW_REQUIRED"})
                self.assertTrue(report.get("findings"))
                pdf = build_report_pdf(
                    cached["case_id"], cached["context"], evidence, report
                )
                self.assertTrue(pdf.startswith(b"%PDF-"))
                self.assertGreater(len(pdf), 1000)
                if path.stem in {"CASE-003", "CASE-006"}:
                    self.assertEqual(report["_validator_result"], "REVIEW_REQUIRED")


if __name__ == "__main__":
    unittest.main()
