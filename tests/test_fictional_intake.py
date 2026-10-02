"""Synthetic intake persists real calculated rows without claiming real KYC."""

import hashlib
import os
import sqlite3
import unittest
from unittest.mock import patch

from data.case_evidence import chunk_source_text
from data.fictional_intake import (
    assess_fictional_case, fictional_intake_enabled, intake_fictional_batch, make_generated_fictional_batch,
    list_fictional_cases, read_fictional_case, search_fictional_chunks,
)
from data.incoming_monitor import make_fictional_lab_batch


def fictional_rows(incoming: int = 300000, outgoing: int = 180000) -> list[dict]:
    rows = make_fictional_lab_batch(incoming, outgoing)
    for row in rows:
        row["txn_id"] = row["txn_id"].replace("TXN-LAB", "FIC-TXN")
        row["account_id"] = "FIC-ACC-001"
        row["counterparty_account_id"] = row["counterparty_account_id"].replace("EXT-LAB", "FIC-EXT")
    return rows


class FictionalIntakeTests(unittest.TestCase):
    def test_public_railway_default_and_explicit_intake_override(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(fictional_intake_enabled())
        with patch.dict(os.environ, {"RAILWAY_PUBLIC_DOMAIN": "investigateiq.example"}, clear=True):
            self.assertTrue(fictional_intake_enabled())
            os.environ["ENABLE_FICTIONAL_INTAKE"] = "0"
            self.assertFalse(fictional_intake_enabled())
        with patch.dict(os.environ, {"ENABLE_FICTIONAL_INTAKE": "1"}, clear=True):
            self.assertTrue(fictional_intake_enabled())

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row

    def tearDown(self):
        self.conn.close()

    def test_calculated_case_stores_rows_and_exact_searchable_chunks(self):
        result = intake_fictional_batch(self.conn, fictional_rows(), 80000)
        self.assertTrue(result["created"])
        self.assertEqual(result["signal"]["incoming_multiplier"], 15)
        self.assertEqual(result["signal"]["outbound_percent"], 90)
        case_id = result["case_id"]
        self.assertEqual(self.conn.execute(
            "SELECT COUNT(*) FROM fictional_intake_transactions WHERE case_id=?", (case_id,)
        ).fetchone()[0], 10)
        docs = self.conn.execute(
            "SELECT doc_id, body, content_sha256, is_original_upload FROM fictional_intake_documents WHERE case_id=?",
            (case_id,),
        ).fetchall()
        self.assertEqual(len(docs), 5)
        for doc in docs:
            self.assertEqual(doc["is_original_upload"], 0)
            self.assertEqual(doc["content_sha256"], hashlib.sha256(doc["body"].encode()).hexdigest())
            chunks = [row[0] for row in self.conn.execute(
                "SELECT chunk_text FROM fictional_intake_chunks WHERE doc_id=? ORDER BY chunk_index",
                (doc["doc_id"],),
            )]
            self.assertEqual(chunks, chunk_source_text(doc["body"]))
            self.assertEqual("\n\n".join(chunks), doc["body"])
        self.assertGreater(self.conn.execute(
            "SELECT COUNT(*) FROM fictional_intake_chunks_fts WHERE fictional_intake_chunks_fts MATCH 'baseline' "
            "AND case_id=?", (case_id,),
        ).fetchone()[0], 0)
        packet = read_fictional_case(self.conn, case_id)
        self.assertEqual(len(packet["transactions"]), 10)
        self.assertEqual(len(packet["documents"]), 5)
        self.assertEqual(packet["original_identity_files"], 0)
        self.assertEqual(packet["external_customer_profiles"], 0)
        self.assertEqual(packet["source_kind"], "generated_fictional_batch")
        queue = list_fictional_cases(self.conn)
        self.assertEqual(queue[0]["case_id"], case_id)
        self.assertEqual(queue[0]["trigger_transaction_id"], "FIC-TXN-01")

    def test_packet_search_is_scoped_to_one_case(self):
        first = intake_fictional_batch(
            self.conn, make_generated_fictional_batch(300000, 180000, 80000), 80000
        )["case_id"]
        second = intake_fictional_batch(
            self.conn, make_generated_fictional_batch(320000, 180000, 80000), 80000
        )["case_id"]
        matches = search_fictional_chunks(self.conn, first, "baseline")
        self.assertTrue(matches)
        self.assertTrue(all(first in row["doc_id"] for row in matches))
        self.assertFalse(any(second in row["doc_id"] for row in matches))

    def test_identical_batch_is_idempotent(self):
        first = intake_fictional_batch(self.conn, fictional_rows(), 80000)
        second = intake_fictional_batch(self.conn, fictional_rows(), 80000)
        self.assertFalse(second["created"])
        self.assertEqual(first["case_id"], second["case_id"])
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM fictional_intake_cases").fetchone()[0], 1)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM fictional_intake_transactions").fetchone()[0], 10)

    def test_changed_numeric_scenario_gets_distinct_synthetic_ids(self):
        first = make_generated_fictional_batch(300000, 180000, 80000)
        changed = make_generated_fictional_batch(320000, 180000, 80000)
        self.assertNotEqual(first[0]["txn_id"], changed[0]["txn_id"])
        self.assertNotEqual(first[0]["account_id"], changed[0]["account_id"])
        saved_first = intake_fictional_batch(self.conn, first, 80000)
        saved_changed = intake_fictional_batch(self.conn, changed, 80000)
        self.assertTrue(saved_first["created"] and saved_changed["created"])
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM fictional_intake_cases").fetchone()[0], 2)

    def test_below_threshold_creates_no_case(self):
        result = intake_fictional_batch(self.conn, fictional_rows(outgoing=100000), 80000)
        self.assertIsNone(result["case_id"])
        self.assertFalse(result["created"])
        self.assertIsNone(self.conn.execute(
            "SELECT name FROM sqlite_master WHERE name='fictional_intake_cases'"
        ).fetchone())

    def test_nonfictional_ids_are_rejected(self):
        rows = fictional_rows()
        rows[0]["counterparty_account_id"] = "12345678901234"
        with self.assertRaisesRegex(ValueError, "fictional FIC-EXT"):
            intake_fictional_batch(self.conn, rows, 80000)

    def test_out_of_range_values_are_rejected_before_storage(self):
        with self.assertRaisesRegex(ValueError, "baseline"):
            intake_fictional_batch(self.conn, fictional_rows(), 10**1000)
        with self.assertRaisesRegex(ValueError, "amount"):
            intake_fictional_batch(self.conn, fictional_rows(incoming=100_000_001), 80000)

    def test_transaction_id_collision_rolls_back_new_case(self):
        intake_fictional_batch(self.conn, fictional_rows(), 80000)
        with self.assertRaises(sqlite3.IntegrityError):
            intake_fictional_batch(self.conn, fictional_rows(incoming=320000), 80000)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM fictional_intake_cases").fetchone()[0], 1)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM fictional_intake_documents").fetchone()[0], 5)

    def test_assessment_rechecks_rows_and_stops_short_of_a_verdict(self):
        case_id = intake_fictional_batch(self.conn, fictional_rows(), 80000)["case_id"]
        assessment = assess_fictional_case(self.conn, case_id)
        self.assertTrue(assessment["review_signal_recomputed"])
        self.assertTrue(assessment["source_integrity_confirmed"])
        self.assertEqual(assessment["observed"]["completed_transaction_rows"], 10)
        self.assertEqual(assessment["observed"]["incoming_inr"], 1200000)
        self.assertIsNone(assessment["lawfulness_verdict"])
        self.assertTrue(any("source-of-funds" in gap for gap in assessment["missing_evidence"]))

    def test_assessment_flags_tampered_ledger_or_document(self):
        case_id = intake_fictional_batch(self.conn, fictional_rows(), 80000)["case_id"]
        self.conn.execute(
            "UPDATE fictional_intake_transactions SET amount='1' WHERE txn_id='FIC-TXN-01'"
        )
        self.conn.execute(
            "UPDATE fictional_intake_documents SET body='changed' WHERE doc_id=?",
            (f"FIC-PAN-{case_id}",),
        )
        assessment = assess_fictional_case(self.conn, case_id)
        self.assertFalse(assessment["review_signal_recomputed"])
        self.assertFalse(assessment["source_integrity_confirmed"])
        self.assertIsNone(assessment["lawfulness_verdict"])

    def test_assessment_detects_missing_source_even_when_alert_math_still_matches(self):
        case_id = intake_fictional_batch(self.conn, fictional_rows(), 80000)["case_id"]
        doc_id = f"FIC-PAN-{case_id}"
        self.conn.execute("DELETE FROM fictional_intake_chunks WHERE doc_id=?", (doc_id,))
        self.conn.execute("DELETE FROM fictional_intake_documents WHERE doc_id=?", (doc_id,))
        assessment = assess_fictional_case(self.conn, case_id)
        self.assertTrue(assessment["review_signal_recomputed"])
        self.assertFalse(assessment["source_integrity_confirmed"])

    def test_assessment_detects_search_index_drift(self):
        case_id = intake_fictional_batch(self.conn, fictional_rows(), 80000)["case_id"]
        chunk_id = self.conn.execute(
            "SELECT chunk_id FROM fictional_intake_chunks WHERE case_id=? LIMIT 1", (case_id,)
        ).fetchone()[0]
        self.conn.execute("DELETE FROM fictional_intake_chunks_fts WHERE chunk_id=?", (chunk_id,))
        assessment = assess_fictional_case(self.conn, case_id)
        self.assertTrue(assessment["review_signal_recomputed"])
        self.assertFalse(assessment["source_integrity_confirmed"])

    def test_assessment_detects_row_change_outside_alert_amounts(self):
        case_id = intake_fictional_batch(self.conn, fictional_rows(), 80000)["case_id"]
        self.conn.execute(
            "UPDATE fictional_intake_transactions SET counterparty_account_id='FIC-EXT-CHANGED' "
            "WHERE txn_id='FIC-TXN-01'"
        )
        assessment = assess_fictional_case(self.conn, case_id)
        self.assertTrue(assessment["review_signal_recomputed"])
        self.assertFalse(assessment["source_integrity_confirmed"])

    def test_assessment_fails_closed_on_malformed_stored_amount(self):
        case_id = intake_fictional_batch(self.conn, fictional_rows(), 80000)["case_id"]
        self.conn.execute(
            "UPDATE fictional_intake_transactions SET amount='not-a-number' "
            "WHERE txn_id='FIC-TXN-01'"
        )
        assessment = assess_fictional_case(self.conn, case_id)
        self.assertFalse(assessment["review_signal_recomputed"])
        self.assertFalse(assessment["source_integrity_confirmed"])
        self.assertTrue(any("malformed" in gap for gap in assessment["missing_evidence"]))
        self.assertIsNone(assessment["lawfulness_verdict"])


if __name__ == "__main__":
    unittest.main()
