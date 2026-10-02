"""Evidence lineage and conservative transfer-tracing regressions."""

import sqlite3
import unittest
from contextlib import closing

from data.case_evidence import case_evidence_coverage, chunk_source_text, search_case_chunks
from data.fund_flow import case_transactions, case_window_links, trace_transaction
from data.knowledge_search import DB_PATH


class CaseEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row

    def tearDown(self):
        self.conn.close()

    def test_every_case_has_case_records_and_customer_kyc_samples(self):
        case_ids = [row[0] for row in self.conn.execute("SELECT case_id FROM alerts")]
        self.assertGreaterEqual(len(case_ids), 40)
        for case_id in case_ids:
            coverage = case_evidence_coverage(self.conn, case_id)
            self.assertEqual(coverage["sample_identity_records"], 2)
            self.assertEqual(coverage["original_uploaded_files"], 0)
            self.assertIn("cannot be determined", coverage["conclusion"])
            self.assertTrue(case_transactions(self.conn, case_id))

    def test_case_source_chunks_reconstruct_exact_body(self):
        for doc_id in ("KYC-PROFILE-CUST-1005", "SAMPLE-PAN-CUST-1005", "CASE-LEDGER-CASE-041"):
            source = self.conn.execute(
                "SELECT body FROM case_evidence_sources WHERE doc_id=?", (doc_id,)
            ).fetchone()
            self.assertIsNotNone(source)
            chunks = [row[0] for row in self.conn.execute(
                "SELECT chunk_text FROM case_evidence_chunks WHERE doc_id=? ORDER BY chunk_index", (doc_id,)
            )]
            self.assertEqual(chunks, chunk_source_text(source["body"]))
            self.assertEqual("\n\n".join(chunks), source["body"])
        sample = self.conn.execute(
            "SELECT body FROM case_evidence_sources WHERE doc_id='SAMPLE-PAN-CUST-1005'"
        ).fetchone()[0]
        self.assertIn("not an authentic government document", sample)

    def test_case_retrieval_returns_scoped_chunk_ids_and_provenance(self):
        hits = search_case_chunks(self.conn, "CASE-043", "KYC profile source funds", 4)
        self.assertTrue(hits)
        self.assertTrue(all(hit["chunk_id"] and hit["doc_id"] and hit["verification_status"] for hit in hits))
        self.assertTrue(any(hit["category"] == "kyc_profile" for hit in hits))
        self.assertFalse(any("CUST-TEST-02" in hit["doc_id"] for hit in hits))

    def test_case_041_cash_deposit_does_not_invent_sender(self):
        trace = trace_transaction(self.conn, "TXN-19927")
        self.assertEqual(trace["link_status"], "cash_deposit_not_account_transfer")
        self.assertIsNone(trace["source"]["account_id"])
        self.assertEqual(trace["destination"]["account_id"], "ACC-1652")
        self.assertFalse(trace["onward_candidates"])

    def test_ledger_link_is_not_claimed_as_settled_without_pair(self):
        trace = trace_transaction(self.conn, "TXN-10023")
        self.assertEqual(trace["link_status"], "single_ledger_link_only")
        self.assertIsNone(trace["mirror_transaction_id"])
        self.assertEqual(trace["source"]["account_id"], "ACC-1001")
        self.assertEqual(trace["destination"]["account_id"], "ACC-1424")
        self.assertEqual(trace["destination"]["original_identity_files"], 0)

    def test_matched_cases_are_calculated_alerts_with_same_recorded_pattern(self):
        for case_id in ("CASE-043", "CASE-044"):
            alert = self.conn.execute("SELECT * FROM alerts WHERE case_id=?", (case_id,)).fetchone()
            self.assertIsNotNone(alert)
            self.assertTrue(alert["trigger_transaction_id"].startswith("TXN-TEST-"))
            rows = self.conn.execute(
                "SELECT direction, amount, counterparty_account_id FROM transactions "
                "WHERE account_id=? AND date(txn_datetime)='2026-10-01'", (alert["account_id"],)
            ).fetchall()
            self.assertEqual(len(rows), 10)
            self.assertEqual(sum(r["amount"] for r in rows if r["direction"] == "CR"), 1200000)
            self.assertEqual(sum(r["amount"] for r in rows if r["direction"] == "DR"), 1080000)
            self.assertEqual(len({r["counterparty_account_id"] for r in rows if r["direction"] == "DR"}), 6)
            coverage = case_evidence_coverage(self.conn, case_id)
            self.assertEqual(coverage["original_uploaded_files"], 0)
            self.assertEqual(coverage["unknown_counterparty_count"], 10)
            self.assertTrue(any("no mapped customer profile" in gap for gap in coverage["gaps"]))

    def test_review_window_lists_all_ten_endpoints_without_inventing_external_kyc(self):
        rows = case_window_links(self.conn, "CASE-043")
        self.assertEqual(len(rows), 10)
        self.assertEqual(len({row["transaction_id"] for row in rows}), 10)
        for row in rows:
            external_side = "source" if row["direction"] == "CR" else "destination"
            self.assertIsNone(row[f"{external_side}_customer"])
            self.assertEqual(row[f"{external_side}_kyc_field"], "Unknown")
            self.assertEqual(row[f"{external_side}_original_files"], 0)
            self.assertEqual(row["link_status"], "counterparty_not_in_bank_dataset")

    def test_duplicate_source_account_is_explicitly_ambiguous(self):
        owners = [row[0] for row in self.conn.execute(
            "SELECT customer_id FROM accounts WHERE account_id='ACC-1004'"
        )]
        self.assertEqual(set(owners), {"CUST-1004", "CUST-0004"})
        coverage = case_evidence_coverage(self.conn, "CASE-001")
        self.assertTrue(any("multiple customers" in gap for gap in coverage["gaps"]))
        trace = trace_transaction(self.conn, "TXN-10202")
        self.assertIsNone(trace["destination"]["customer_id"])
        self.assertIn("Ambiguous owner", trace["destination"]["name"])

    def test_mirror_requires_completed_and_unique_opposite_side_row(self):
        with closing(sqlite3.connect(":memory:")) as conn:
            conn.row_factory = sqlite3.Row
            conn.executescript("""
                CREATE TABLE customers (customer_id TEXT, name TEXT, kyc_status TEXT);
                CREATE TABLE accounts (account_id TEXT, customer_id TEXT);
                CREATE TABLE case_evidence_sources (customer_id TEXT, is_original_upload INTEGER);
                CREATE TABLE transactions (
                    txn_id TEXT, account_id TEXT, counterparty_account_id TEXT,
                    direction TEXT, amount INTEGER, status TEXT, channel TEXT,
                    txn_datetime TEXT
                );
                INSERT INTO customers VALUES ('C1','One','Dataset only'),('C2','Two','Dataset only');
                INSERT INTO accounts VALUES ('A1','C1'),('A2','C2');
                INSERT INTO transactions VALUES
                    ('T1','A1','A2','DR',100,'Pending','NEFT','2026-10-01T10:00:00'),
                    ('T2','A2','A1','CR',100,'Completed','NEFT','2026-10-01T10:01:00');
            """)
            pending = trace_transaction(conn, "T1")
            self.assertIsNone(pending["mirror_transaction_id"])
            self.assertEqual(pending["link_status"], "single_ledger_link_only")
            conn.execute("UPDATE transactions SET status='Completed' WHERE txn_id='T1'")
            unique = trace_transaction(conn, "T1")
            self.assertEqual(unique["mirror_transaction_id"], "T2")
            self.assertIn("possible", unique["caveat"])
            conn.execute("INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?)", (
                "T3", "A2", "A1", "CR", 100, "Completed", "NEFT", "2026-10-01T10:02:00",
            ))
            ambiguous = trace_transaction(conn, "T1")
            self.assertIsNone(ambiguous["mirror_transaction_id"])
            self.assertEqual(ambiguous["link_status"], "ambiguous_ledger_pair")


if __name__ == "__main__":
    unittest.main()
