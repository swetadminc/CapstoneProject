"""Checks the illustrative rule preview's time-window arithmetic."""

import sqlite3
import unittest

from data.trigger_rules import would_trigger_r1, would_trigger_r2


class TriggerRulePreviewTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.addCleanup(self.conn.close)
        self.conn.execute("""
            CREATE TABLE transactions (
                account_id TEXT, direction TEXT, amount REAL, txn_datetime TEXT
            )
        """)
        self.conn.executemany(
            "INSERT INTO transactions VALUES (?,?,?,?)",
            [
                ("ACC-1", "CR", 100.0, "2026-09-17T09:00:00"),
                ("ACC-1", "CR", 600.0, "2026-09-18T09:00:00"),
                ("ACC-1", "DR", 250.0, "2026-09-18T10:00:00"),
                ("ACC-1", "DR", 250.0, "2026-09-18T11:00:00"),
                ("ACC-1", "DR", 999.0, "2026-09-19T10:00:00"),
            ],
        )

    def test_r1_uses_prior_credit_baseline(self):
        fired, baseline, ratio = would_trigger_r1(
            self.conn, "ACC-1", "2026-09-18T09:00:00", 5.0
        )
        self.assertTrue(fired)
        self.assertEqual(baseline, 100.0)
        self.assertEqual(ratio, 6.0)

    def test_same_day_iso_timestamp_debits_count_within_twelve_hours(self):
        fired, pct = would_trigger_r2(
            self.conn, "ACC-1", "2026-09-18T09:00:00", 600.0, 80.0, 12.0
        )
        self.assertTrue(fired)
        self.assertAlmostEqual(pct, 500.0 / 600.0 * 100.0)

    def test_one_debit_is_not_enough_even_when_large(self):
        fired, pct = would_trigger_r2(
            self.conn, "ACC-1", "2026-09-18T09:00:00", 600.0, 80.0, 1.5
        )
        self.assertFalse(fired)
        self.assertEqual(pct, 0.0)


if __name__ == "__main__":
    unittest.main()
