"""The fictional closure example must remain traceable and non-deceptive."""

import sqlite3
import unittest

from agents.imported_copilot import answer_imported_case_question
from data.case_evidence import chunk_source_text, case_evidence_coverage
from data.closed_case_fixture import CASE_ID, CREDIT_ID, DEBIT_ID
from data.knowledge_search import DB_PATH
from data.runtime_db import resolve_status


class ClosedCaseFixtureTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row

    def tearDown(self):
        self.conn.close()

    def test_status_is_not_a_human_close(self):
        alert = self.conn.execute("SELECT * FROM alerts WHERE case_id=?", (CASE_ID,)).fetchone()
        self.assertEqual(alert["status"], "Closed - Simulated Example")
        self.assertEqual(resolve_status(alert["status"], None), "Demo closed — simulated")
        self.assertEqual(resolve_status("Closed - No Concern", None), "Source closed — unverified")
        self.assertEqual(alert["trigger_transaction_id"], CREDIT_ID)

    def test_summaries_match_ledger_but_are_not_original_proof(self):
        alert = self.conn.execute("SELECT * FROM alerts WHERE case_id=?", (CASE_ID,)).fetchone()
        customer = self.conn.execute("SELECT * FROM customers WHERE customer_id=?", (alert["customer_id"],)).fetchone()
        self.assertEqual(customer["expected_monthly_credit"], 20000)
        rows = self.conn.execute("SELECT * FROM transactions WHERE account_id=? ORDER BY txn_datetime",
                                 (alert["account_id"],)).fetchall()
        self.assertEqual([(r["txn_id"], r["direction"], r["amount"]) for r in rows],
                         [(CREDIT_ID, "CR", 60000), (DEBIT_ID, "DR", 8000)])
        self.assertEqual(rows[0]["amount"] / customer["expected_monthly_credit"], 3)
        docs = self.conn.execute("SELECT * FROM documents WHERE case_id=? ORDER BY doc_id", (CASE_ID,)).fetchall()
        self.assertEqual(len(docs), 4)
        self.assertTrue(all(doc["verified"] == 0 for doc in docs))
        for doc in docs:
            source = self.conn.execute("SELECT * FROM case_evidence_sources WHERE doc_id=?",
                                       (f"SUMMARY-{doc['doc_id']}",)).fetchone()
            self.assertEqual(source["is_original_upload"], 0)
            self.assertEqual(source["verification_status"], "summary_without_original")
            chunks = [r[0] for r in self.conn.execute(
                "SELECT chunk_text FROM case_evidence_chunks WHERE doc_id=? ORDER BY chunk_index",
                (source["doc_id"],))]
            self.assertEqual(chunks, chunk_source_text(source["body"]))
        self.assertIn(CREDIT_ID, next(d["extracted_summary"] for d in docs if "INVOICE" in d["doc_id"]))
        self.assertIn(DEBIT_ID, next(d["extracted_summary"] for d in docs if "SUPPLIER" in d["doc_id"]))
        self.assertEqual(case_evidence_coverage(self.conn, CASE_ID)["original_uploaded_files"], 0)

    def test_copilot_cites_packet_and_disclaims_lawfulness(self):
        answer = answer_imported_case_question("What closure evidence is stored and why closed?", CASE_ID)
        self.assertIn("fictional closed-case", answer["answer"])
        self.assertIn("not independent confirmation", answer["answer"])
        self.assertIn("not proof of lawful funds", answer["answer"])
        self.assertIn("3.0x", answer["answer"])
        self.assertEqual(set(answer["txn_ids"]), {CREDIT_ID, DEBIT_ID})
        self.assertTrue(any(chunk.startswith("SUMMARY-DOC-DEMO-045-INVOICE") for chunk in answer["chunk_ids"]))
        self.assertTrue(any(chunk.startswith("SUMMARY-DOC-DEMO-045-REVIEW") for chunk in answer["chunk_ids"]))
        for chunk_id in answer["chunk_ids"]:
            self.assertIsNotNone(self.conn.execute(
                "SELECT 1 FROM case_evidence_chunks WHERE chunk_id=? AND case_id=?",
                (chunk_id, CASE_ID)).fetchone())


if __name__ == "__main__":
    unittest.main()
