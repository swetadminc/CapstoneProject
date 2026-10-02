"""The two Rahul document scenarios must start with the same alert math."""

import unittest

from data.incoming_monitor import detect_pass_through, make_fictional_lab_batch


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

    def test_same_beneficiary_is_not_six_distinct_destinations(self):
        rows = ten_transaction_example("ACC-F001")
        for row in rows[4:]:
            row["counterparty_account_id"] = "EXT-ONE"
        self.assertEqual(detect_pass_through(rows, 80000), [])

    def test_later_non_overlapping_window_can_still_trigger(self):
        earlier = ten_transaction_example("ACC-F001")[:1]
        earlier[0]["amount"] = 1000
        later = ten_transaction_example("ACC-F001")
        for row in later:
            row["txn_id"] = "LATER-" + row["txn_id"]
            row["txn_datetime"] = row["txn_datetime"].replace("2026-10-01", "2026-10-03")
        alerts = detect_pass_through(earlier + later, 80000)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["window_start"], "2026-10-03T09:00:00")

    def test_bad_input_is_rejected(self):
        rows = ten_transaction_example("ACC-F001")
        rows[1]["txn_id"] = rows[0]["txn_id"]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            detect_pass_through(rows, 80000)

    def test_rule_lab_uses_changed_amounts_without_saving_a_case(self):
        rows = make_fictional_lab_batch(300000, 180000)
        self.assertEqual(len(rows), 10)
        self.assertEqual(len(detect_pass_through(rows, 80000)), 1)
        self.assertEqual(sum(row["amount"] for row in rows if row["direction"] == "DR"), 1080000)
        self.assertTrue(all(row["account_id"] == "ACC-LAB-001" for row in rows))
        self.assertEqual(detect_pass_through(make_fictional_lab_batch(300000, 100000), 80000), [])
        self.assertEqual(detect_pass_through(rows, 300000), [])
        with self.assertRaisesRegex(ValueError, "Incoming"):
            make_fictional_lab_batch(0, 180000)


if __name__ == "__main__":
    unittest.main()
