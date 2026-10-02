"""The two Rahul document scenarios must start with the same alert math."""

import unittest

from data.incoming_monitor import detect_pass_through


def ten_transaction_example(account_id: str) -> list[dict]:
    times = ["09:00", "09:20", "09:40", "10:00", "10:15", "10:30",
             "10:45", "11:00", "11:15", "11:30"]
    return [{
        "txn_id": f"{account_id}-T{index:03d}", "account_id": account_id,
        "txn_datetime": f"2026-10-01T{time}:00", "direction": "CR" if index <= 4 else "DR",
        "amount": 300000 if index <= 4 else 180000,
        "status": "Completed", "counterparty_account_id": f"S{index:02d}" if index <= 4 else f"B{index-4:02d}",
    } for index, time in enumerate(times, start=1)]


class IncomingMonitorTests(unittest.TestCase):
    def test_same_pattern_fires_for_both_fictional_cases_without_outcome_leakage(self):
        for account in ("ACC-F001", "ACC-L001"):
            alerts = detect_pass_through(ten_transaction_example(account), 80000)
            self.assertEqual(len(alerts), 1)
            alert = alerts[0]
            self.assertEqual(alert["incoming"], 1200000)
            self.assertEqual(alert["outgoing"], 1080000)
            self.assertEqual(alert["incoming_multiplier"], 15)
            self.assertEqual(alert["outbound_percent"], 90)
            self.assertEqual(alert["beneficiary_count"], 6)
            self.assertNotIn("fraud", alert["assessment"].lower())

    def test_pending_or_incomplete_pattern_does_not_fire(self):
        rows = ten_transaction_example("ACC-F001")
        for row in rows[4:]:
            row["status"] = "Pending"
        self.assertEqual(detect_pass_through(rows, 80000), [])

    def test_bad_input_is_rejected(self):
        rows = ten_transaction_example("ACC-F001")
        rows[1]["txn_id"] = rows[0]["txn_id"]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            detect_pass_through(rows, 80000)


if __name__ == "__main__":
    unittest.main()
