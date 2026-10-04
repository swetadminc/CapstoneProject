"""Local acceptance check for the human decision and Compliance handoff."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from data import runtime_db


class WorkflowAcceptanceTests(unittest.TestCase):
    def test_investigator_escalation_compliance_followup_and_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(runtime_db, "RUNTIME_DB_PATH", str(Path(directory) / "audit.db")), \
                 patch.object(runtime_db, "_initialized", False):
                runtime_db.init_runtime_db()
                app_path = Path(__file__).resolve().parents[1] / "app.py"
                app = AppTest.from_file(str(app_path)).run(timeout=30)
                app.session_state["user_name"] = "Flow Investigator"
                app.session_state["user_role"] = "Investigator"
                app.session_state["selected_case_id"] = "CASE-041"
                app.switch_page("pages/2_Investigation_Demo.py").run(timeout=30)
                self.assertFalse(app.exception)
                run = next(item for item in app.button if item.label.startswith("▶ Run investigation"))
                run.click().run(timeout=30)
                self.assertFalse(app.exception)
                app.radio(key="action_CASE-041").set_value("Escalate to Compliance")
                app.text_area(key="rationale_CASE-041").set_value(
                    "Review the saved draft against current source records and request original KYC."
                )
                app.button(key="submit_CASE-041").click().run(timeout=30)
                self.assertFalse(app.exception)
                actions = runtime_db.get_human_actions("CASE-041")
                self.assertEqual(len(actions), 1)
                self.assertEqual(actions[0]["action"], "escalate")
                self.assertEqual(actions[0]["investigator"], "Flow Investigator")
                self.assertFalse(any(button.key == "submit_CASE-041" for button in app.button))
                self.assertFalse(any(item.key == "rationale_CASE-041" for item in app.text_area))
                self.assertTrue(any("Recorded human action:" in item.value and
                                    "Escalate to Compliance" in item.value
                                    for item in app.get("success")))
                self.assertTrue(any("Review the saved draft against current source records" in item.value
                                    for item in app.get("markdown")))
                self.assertEqual(runtime_db.resolve_status("Open", runtime_db.get_latest_decision_per_case()["CASE-041"]),
                                 "Escalated")

                app.session_state["user_name"] = "Flow Compliance"
                app.session_state["user_role"] = "Compliance Officer"
                app.switch_page("pages/3_Compliance_Queue.py").run(timeout=30)
                self.assertFalse(app.exception)
                self.assertTrue(any("CASE-041" in item.value for item in app.get("markdown")))
                app.radio(key="caction_CASE-041").set_value("Return to investigator for more information")
                app.text_area(key="crationale_CASE-041").set_value(
                    "Original identity records and source-of-funds proof are still needed."
                )
                app.button(key="csubmit_CASE-041").click().run(timeout=30)
                self.assertFalse(app.exception)
                actions = runtime_db.get_human_actions("CASE-041")
                audit = runtime_db.get_audit_log("CASE-041")
                self.assertEqual([item["action"] for item in actions], ["escalate", "compliance_return"])
                self.assertEqual([item["action"] for item in audit if item["actor"] == "human"],
                                 ["decision: escalate", "decision: compliance_return"])
                self.assertEqual(runtime_db.resolve_status("Open", runtime_db.get_latest_decision_per_case()["CASE-041"]),
                                 "Compliance returned — information needed")

    def test_compliance_outcomes_have_distinct_queue_statuses(self):
        self.assertEqual(
            runtime_db.resolve_status("Open", {"action": "compliance_ack"}),
            "Compliance reviewed — no further action",
        )
        self.assertEqual(
            runtime_db.resolve_status("Open", {"action": "compliance_return"}),
            "Compliance returned — information needed",
        )
        self.assertEqual(
            runtime_db.resolve_status("Open", {"action": "compliance_refer"}),
            "Compliance referred onward — recorded",
        )


if __name__ == "__main__":
    unittest.main()
