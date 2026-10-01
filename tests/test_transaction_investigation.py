"""Tests that deviation claims are anchored to an identified alert transaction."""

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import agents.transaction_investigation_agent as transaction_module


class TransactionInvestigationTests(unittest.TestCase):
    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        db_path = Path(temp_dir.name) / "demo.db"
        with closing(sqlite3.connect(db_path)) as conn:
            with conn:
                conn.execute("""
                    CREATE TABLE transactions (
                        txn_id TEXT, account_id TEXT, txn_datetime TEXT,
                        direction TEXT, amount REAL, counterparty_name TEXT,
                        counterparty_account_id TEXT, reference_text TEXT
                    )
                """)
                conn.executemany("INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?)", [
                    ("TXN-OLD", "ACC-1", "2026-09-17T09:00:00", "CR", 100, "Old", "EXT-1", "Prior"),
                    ("TXN-FIRST", "ACC-1", "2026-09-18T10:00:00", "CR", 200, "First", "EXT-2", "First"),
                    ("TXN-TRIGGER", "ACC-1", "2026-09-18T11:00:00", "CR", 600, "Trigger", "EXT-3", "Trigger"),
                ])
        path_patch = patch.object(transaction_module, "DB_PATH", str(db_path))
        path_patch.start()
        self.addCleanup(path_patch.stop)

    def test_missing_trigger_id_does_not_invent_a_ratio(self):
        evidence = transaction_module.TransactionInvestigationAgent().run("ACC-1", "2026-09-18")
        self.assertEqual(len(evidence["window_transactions"]), 2)
        self.assertIsNone(evidence["deviation_ratio"])
        self.assertIsNone(evidence["trigger_transaction_id"])

    def test_uses_recorded_trigger_not_first_window_transaction(self):
        evidence = transaction_module.TransactionInvestigationAgent().run(
            "ACC-1", "2026-09-18", trigger_txn_id="TXN-TRIGGER"
        )
        self.assertEqual(evidence["deviation_ratio"], 6.0)
        self.assertEqual(evidence["trigger_transaction_id"], "TXN-TRIGGER")

    def test_cached_ratio_without_source_trigger_is_removed(self):
        stored = {"window_transactions": [{"txn_id": "TXN-FIRST", "amount": 200}],
                  "baseline_avg_amount": 100, "deviation_ratio": 2.0,
                  "evidence_window_empty": False}
        checked = transaction_module.anchor_cached_evidence(stored, {"trigger_transaction_id": None})
        self.assertIsNone(checked["deviation_ratio"])
        self.assertIsNone(checked["trigger_transaction_id"])
        self.assertEqual(stored["deviation_ratio"], 2.0)

    def test_cached_ratio_is_recomputed_from_recorded_trigger(self):
        stored = {"window_transactions": [{"txn_id": "TXN-TRIGGER", "amount": 600}],
                  "baseline_avg_amount": 100, "deviation_ratio": 99.0,
                  "evidence_window_empty": False}
        checked = transaction_module.anchor_cached_evidence(
            stored, {"trigger_transaction_id": "TXN-TRIGGER"}
        )
        self.assertEqual(checked["deviation_ratio"], 6.0)


if __name__ == "__main__":
    unittest.main()
