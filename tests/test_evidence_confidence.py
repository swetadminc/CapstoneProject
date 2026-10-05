import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

from agents.evidence_confidence import DISCLAIMER, calculate_evidence_confidence


class EvidenceConfidenceTests(unittest.TestCase):
    def test_complete_grounded_draft_scores_high(self):
        report = {
            "_validator_result": "PASS",
            "_validator_notes": [],
            "findings": [{"evidence_status": "Verified", "supporting_txn_ids": ["TXN-1"]}],
            "recommended_next_steps": [{"step": "Review the source", "playbook_doc_id": "PB-1"}],
        }
        evidence = {"window_transactions": [{"transaction_id": "TXN-1"}], "case_chunks": [{"chunk_id": "C-1"}]}
        confidence = calculate_evidence_confidence(report, evidence, [{"doc_id": "PB-1"}])

        self.assertEqual(confidence["score"], 100)
        self.assertEqual(confidence["rating"], "High")
        self.assertFalse(confidence["limitations"])

    def test_known_evidence_gap_prevents_high_rating(self):
        report = {
            "_validator_result": "PASS",
            "_validator_notes": [],
            "findings": [
                {"evidence_status": "Verified", "supporting_txn_ids": ["TXN-1"]},
                {"evidence_status": "Missing", "supporting_txn_ids": []},
            ],
            "recommended_next_steps": [{"step": "Review the source", "playbook_doc_id": "PB-1"}],
        }
        evidence = {"window_transactions": [{"transaction_id": "TXN-1"}], "documents": []}
        confidence = calculate_evidence_confidence(report, evidence, [{"doc_id": "PB-1"}])

        self.assertEqual(confidence["score"], 80)
        self.assertEqual(confidence["rating"], "Moderate")
        self.assertTrue(any("missing or conflicting" in item for item in confidence["limitations"]))

    def test_unsupported_draft_explains_low_support(self):
        report = {
            "_validator_result": "REVIEW",
            "_validator_notes": ["A citation needs review."],
            "findings": [{"evidence_status": "Inferred", "supporting_txn_ids": []}],
            "recommended_next_steps": [{"step": "Follow up"}],
        }
        evidence = {"window_transactions": [], "evidence_window_empty": True, "account_ownership_ambiguous": True}
        confidence = calculate_evidence_confidence(report, evidence, [])

        self.assertEqual(confidence["rating"], "Low")
        self.assertLess(confidence["score"], 60)
        self.assertEqual(confidence["disclaimer"], DISCLAIMER)
        self.assertIn("not a probability of crime", confidence["disclaimer"])

    def test_workspace_exposes_the_score_and_its_rubric(self):
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(app_path)).run(timeout=30)
        app.session_state["user_name"] = "Case Reviewer"
        app.session_state["user_role"] = "Investigator"
        app.session_state["selected_case_id"] = "CASE-041"
        app.switch_page("pages/2_Investigation_Demo.py").run(timeout=30)
        next(item for item in app.button if item.label.startswith("▶ Run investigation")).click().run(timeout=30)

        self.assertFalse(app.exception)
        rendered = "\n".join(item.value for item in app.get("markdown"))
        self.assertIn("Evidence confidence", rendered)
        self.assertTrue(any("not a probability of crime" in item.value for item in app.get("info")))

