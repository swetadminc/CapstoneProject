"""Regression checks for human-decision and audit-log consistency."""

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from data import runtime_db


class RuntimeDBTransactionTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        db_path = Path(self.temp_dir.name) / "runtime.db"
        path_patch = patch.object(runtime_db, "RUNTIME_DB_PATH", str(db_path))
        initialized_patch = patch.object(runtime_db, "_initialized", False)
        path_patch.start()
        initialized_patch.start()
        self.addCleanup(path_patch.stop)
        self.addCleanup(initialized_patch.stop)
        runtime_db.init_runtime_db()

    def test_decision_and_audit_are_saved_together(self):
        action_id = runtime_db.record_human_decision(
            "CASE-TEST", "Tester", "close", "Evidence reviewed", ["F1"], []
        )
        actions = runtime_db.get_human_actions("CASE-TEST")
        events = runtime_db.get_audit_log("CASE-TEST")
        self.assertEqual(len(actions), 1)
        self.assertEqual(len(events), 1)
        self.assertEqual(actions[0]["action_id"], action_id)
        self.assertEqual(events[0]["action"], "decision: close")
        self.assertEqual(actions[0]["timestamp"], events[0]["timestamp"])

    def test_failed_audit_insert_rolls_back_decision(self):
        with closing(sqlite3.connect(runtime_db.RUNTIME_DB_PATH)) as conn:
            with conn:
                conn.execute("""
                    CREATE TRIGGER reject_human_audit BEFORE INSERT ON audit_log
                    WHEN NEW.actor = 'human'
                    BEGIN SELECT RAISE(ABORT, 'simulated audit failure'); END
                """)

        with self.assertRaises(sqlite3.IntegrityError):
            runtime_db.record_human_decision(
                "CASE-TEST", "Tester", "escalate", "Needs review", [], []
            )
        self.assertEqual(runtime_db.get_human_actions("CASE-TEST"), [])
        self.assertEqual(runtime_db.get_audit_log("CASE-TEST"), [])

    def test_empty_rationale_is_rejected(self):
        with self.assertRaises(ValueError):
            runtime_db.record_human_decision(
                "CASE-TEST", "Tester", "close", "  ", [], []
            )
        self.assertEqual(runtime_db.get_human_actions("CASE-TEST"), [])

    def test_demo_reset_removes_human_decisions_but_keeps_system_history(self):
        runtime_db.record_human_decision("CASE-TEST", "Investigator", "close",
                                         "Evidence reviewed", [], [])
        runtime_db.log_audit_event("CASE-TEST", "system", "report_generated")

        result = runtime_db.reset_demo_human_decisions("Demo Admin")

        self.assertEqual(result, {"human_decisions_removed": 1, "human_audit_entries_removed": 1})
        self.assertEqual(runtime_db.get_human_actions("CASE-TEST"), [])
        events = runtime_db.get_audit_log("CASE-TEST")
        self.assertEqual([event["action"] for event in events], ["report_generated"])
        reset_events = runtime_db.get_audit_log("SYSTEM-DEMO")
        self.assertEqual(len(reset_events), 1)
        self.assertEqual(reset_events[0]["actor_name"], "Demo Admin")

    def test_decision_is_immutable_until_compliance_returns_case(self):
        runtime_db.record_human_decision("CASE-TEST", "Investigator", "escalate",
                                         "Needs a second review", [], [])
        with self.assertRaisesRegex(ValueError, "already recorded"):
            runtime_db.record_human_decision("CASE-TEST", "Other investigator", "close",
                                             "Stale browser tab", [], [])
        runtime_db.record_human_decision("CASE-TEST", "Compliance", "compliance_return",
                                         "Request original identity evidence", [], [])
        runtime_db.record_human_decision("CASE-TEST", "Investigator", "request_info",
                                         "Follow-up action after return", [], [])
        self.assertEqual([row["action"] for row in runtime_db.get_human_actions("CASE-TEST")],
                         ["escalate", "compliance_return", "request_info"])
        self.assertEqual(len(runtime_db.get_audit_log("CASE-TEST")), 3)
        with self.assertRaisesRegex(ValueError, "already recorded"):
            runtime_db.record_human_decision("CASE-TEST", "Investigator", "escalate",
                                             "Duplicate follow-up", [], [])
        self.assertEqual(len(runtime_db.get_audit_log("CASE-TEST")), 3)

    def test_compliance_cannot_act_without_current_escalation(self):
        with self.assertRaisesRegex(ValueError, "requires a current"):
            runtime_db.record_human_decision("CASE-TEST", "Compliance", "compliance_ack",
                                             "No escalation exists", [], [])
        runtime_db.record_human_decision("CASE-TEST", "Investigator", "escalate",
                                         "Requires review", [], [])
        runtime_db.record_human_decision("CASE-TEST", "Compliance", "compliance_ack",
                                         "Reviewed", [], [])
        with self.assertRaisesRegex(ValueError, "requires a current"):
            runtime_db.record_human_decision("CASE-TEST", "Compliance", "compliance_ack",
                                             "Duplicate action", [], [])

    def test_rule_change_and_audit_are_saved_together(self):
        runtime_db.set_rule_param("R1", "deviation_multiplier", 6.0, "Tester")
        self.assertEqual(runtime_db.get_rule_config()[("R1", "deviation_multiplier")], 6.0)
        events = runtime_db.get_audit_log("SYSTEM-RULES")
        self.assertEqual(len(events), 1)
        self.assertIn("R1.deviation_multiplier = 6.0", events[0]["action"])

    def test_failed_rule_audit_rolls_back_rule_change(self):
        with closing(sqlite3.connect(runtime_db.RUNTIME_DB_PATH)) as conn:
            with conn:
                conn.execute("""
                    CREATE TRIGGER reject_rule_audit BEFORE INSERT ON audit_log
                    WHEN NEW.case_id = 'SYSTEM-RULES'
                    BEGIN SELECT RAISE(ABORT, 'simulated rule audit failure'); END
                """)

        with self.assertRaises(sqlite3.IntegrityError):
            runtime_db.set_rule_param("R1", "deviation_multiplier", 6.0, "Tester")
        self.assertEqual(
            runtime_db.get_rule_config()[("R1", "deviation_multiplier")],
            runtime_db.DEFAULT_RULE_CONFIG[("R1", "deviation_multiplier")],
        )
        self.assertEqual(runtime_db.get_audit_log("SYSTEM-RULES"), [])

    def test_multiple_rule_changes_commit_as_one_batch(self):
        runtime_db.set_rule_params({
            ("R1", "deviation_multiplier"): 6.0,
            ("R2", "pass_through_pct"): 85.0,
        }, "Tester")
        config = runtime_db.get_rule_config()
        self.assertEqual(config[("R1", "deviation_multiplier")], 6.0)
        self.assertEqual(config[("R2", "pass_through_pct")], 85.0)
        events = runtime_db.get_audit_log("SYSTEM-RULES")
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["timestamp"], events[1]["timestamp"])

    def test_failed_second_rule_audit_rolls_back_entire_batch(self):
        with closing(sqlite3.connect(runtime_db.RUNTIME_DB_PATH)) as conn:
            with conn:
                conn.execute("""
                    CREATE TRIGGER reject_second_rule_audit BEFORE INSERT ON audit_log
                    WHEN NEW.case_id = 'SYSTEM-RULES' AND NEW.action LIKE '%R2.pass_through_pct%'
                    BEGIN SELECT RAISE(ABORT, 'simulated second audit failure'); END
                """)
        with self.assertRaises(sqlite3.IntegrityError):
            runtime_db.set_rule_params({
                ("R1", "deviation_multiplier"): 6.0,
                ("R2", "pass_through_pct"): 85.0,
            }, "Tester")
        self.assertEqual(runtime_db.get_rule_config(), runtime_db.DEFAULT_RULE_CONFIG)
        self.assertEqual(runtime_db.get_audit_log("SYSTEM-RULES"), [])


if __name__ == "__main__":
    unittest.main()
