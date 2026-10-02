"""The case copilot must answer from every selected case, not just hero cases."""

import sqlite3
import unittest
import os
import tempfile
import json
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from agents.chat_agent import answer_fictional_case_question
from agents.imported_copilot import answer_imported_case_question
from data.fictional_intake import (
    assess_fictional_case, intake_fictional_batch, make_generated_fictional_batch,
    read_fictional_case,
)
from data.knowledge_search import DB_PATH
from data import runtime_db


QUESTION = "How many transactions were stored in one month, which need review, and is KYC verified?"


class CaseCopilotTests(unittest.TestCase):
    def test_imported_case_chat_uses_database_chunk_links(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(runtime_db, "RUNTIME_DB_PATH", str(Path(directory) / "audit.db")), \
                 patch.object(runtime_db, "_initialized", False):
                runtime_db.init_runtime_db()
                app_path = Path(__file__).resolve().parents[1] / "app.py"
                app = AppTest.from_file(str(app_path)).run(timeout=30)
                app.session_state["user_name"] = "Case Reviewer"
                app.session_state["user_role"] = "Investigator"
                app.session_state["selected_case_id"] = "CASE-041"
                app.switch_page("pages/2_Investigation_Demo.py").run(timeout=30)
                self.assertFalse(app.exception)
                run = next(item for item in app.button if item.label.startswith("▶ Run investigation"))
                run.click().run(timeout=30)
                self.assertFalse(app.exception)
                app.button(key="sugg_CASE-041_1").click().run(timeout=30)
                self.assertFalse(app.exception)
                self.assertTrue(any("Transaction count in" in item.value for item in app.get("markdown")))
                self.assertTrue(any("CASE-LEDGER-ALL-CASE-041-C" in item.value
                                    for item in app.get("caption")))

    def test_fictional_case_chat_interaction_renders_a_multi_part_answer(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "case-chat.db")
            with closing(sqlite3.connect(path)) as conn:
                case_id = intake_fictional_batch(
                    conn, make_generated_fictional_batch(300000, 180000, 80000), 80000
                )["case_id"]
            with patch.dict(os.environ, {"ENABLE_FICTIONAL_INTAKE": "1", "FICTIONAL_INTAKE_DB_PATH": path}):
                app_path = Path(__file__).resolve().parents[1] / "app.py"
                app = AppTest.from_file(str(app_path)).run(timeout=30)
                app.session_state["user_name"] = "Case Reviewer"
                app.session_state["user_role"] = "Investigator"
                app.session_state["selected_case_id"] = case_id
                app.switch_page("pages/2_Investigation_Demo.py").run(timeout=30)
                self.assertFalse(app.exception)
                app.button(key=f"fic_question_{case_id}_1").click().run(timeout=30)
                self.assertFalse(app.exception)
                self.assertTrue(any("Transaction count in October 2026: 10" in item.value
                                    for item in app.get("markdown")))
                self.assertTrue(any("FIC-LEDGER" in item.value for item in app.get("caption")))

    def test_multpart_answer_cites_exact_chunks_for_fictional_intake(self):
        with closing(sqlite3.connect(":memory:")) as conn:
            result = intake_fictional_batch(conn, make_generated_fictional_batch(300000, 180000, 80000), 80000)
            case_id = result["case_id"]
            packet = read_fictional_case(conn, case_id)
            assessment = assess_fictional_case(conn, case_id)
            answer = answer_fictional_case_question(QUESTION, packet, assessment)
            self.assertIn("Transaction count in October 2026: 10", answer["answer"])
            self.assertIn("Review signal: 10", answer["answer"])
            self.assertIn("0 original uploaded identity", answer["answer"])
            self.assertIn("not a complete bank-month total", answer["answer"])
            known_chunks = {chunk["chunk_id"] for chunk in packet["chunks"]}
            self.assertTrue(answer["chunk_ids"])
            self.assertTrue(set(answer["chunk_ids"]).issubset(known_chunks))
            self.assertEqual(len(answer["txn_ids"]), 10)

    def test_all_imported_cases_answer_and_cite_scoped_chunks(self):
        with closing(sqlite3.connect(DB_PATH)) as conn:
            cases = [row[0] for row in conn.execute("SELECT case_id FROM alerts ORDER BY case_id")]
            self.assertGreaterEqual(len(cases), 40)
            for case_id in cases:
                with self.subTest(case_id=case_id):
                    answer = answer_imported_case_question(QUESTION, case_id)
                    self.assertIn("Transaction count", answer["answer"])
                    self.assertIn("KYC:", answer["answer"])
                    self.assertTrue(answer["chunk_ids"])
                    invalid = [chunk_id for chunk_id in answer["chunk_ids"] if conn.execute(
                        "SELECT 1 FROM case_evidence_chunks WHERE chunk_id=? "
                        "AND (case_id=? OR case_id IS NULL)", (chunk_id, case_id),
                    ).fetchone() is None]
                    self.assertEqual(invalid, [])

    def test_every_imported_case_account_row_is_in_its_full_ledger_index(self):
        with closing(sqlite3.connect(DB_PATH)) as conn:
            for case_id, account_id in conn.execute("SELECT case_id, account_id FROM alerts"):
                with self.subTest(case_id=case_id):
                    transaction_ids = {row[0] for row in conn.execute(
                        "SELECT txn_id FROM transactions WHERE account_id=?", (account_id,))}
                    passages = [row[0] for row in conn.execute(
                        "SELECT chunk_text FROM case_evidence_chunks WHERE doc_id=?",
                        (f"CASE-LEDGER-ALL-{case_id}",))]
                    self.assertTrue(passages)
                    self.assertEqual([txn_id for txn_id in transaction_ids
                                      if not any(txn_id in passage for passage in passages)], [])

    def test_account_collision_is_not_silently_attributed(self):
        answer = answer_imported_case_question(QUESTION, "CASE-001")
        self.assertIn("Account-ownership warning", answer["answer"])

    def test_explicit_empty_month_is_not_treated_as_no_bank_activity(self):
        answer = answer_imported_case_question("How many transactions in January 2025?", "CASE-041")
        self.assertIn("January 2025", answer["answer"])
        self.assertIn("supplied dataset may not cover", answer["answer"])

    def test_relevant_questions_use_selected_case_and_exact_row_passages(self):
        questions = (
            "Show the transaction trail and counterparties in September 2026.",
            "How much came in and went out in September 2026?",
            "Which transactions need review and why?",
            "Is KYC verified and can you establish the source of funds?",
            "What evidence is missing and what should I request next?",
        )
        with closing(sqlite3.connect(DB_PATH)) as conn:
            for question in questions:
                with self.subTest(question=question):
                    answer = answer_imported_case_question(question, "CASE-041")
                    self.assertTrue(answer["answer"])
                    self.assertTrue(answer["chunk_ids"])
                    for chunk_id in answer["chunk_ids"]:
                        self.assertIsNotNone(conn.execute(
                            "SELECT 1 FROM case_evidence_chunks WHERE chunk_id=? AND "
                            "(case_id='CASE-041' OR case_id IS NULL)", (chunk_id,),
                        ).fetchone())
            trail = answer_imported_case_question(questions[0], "CASE-041")
            for txn_id in trail["txn_ids"]:
                self.assertTrue(any(conn.execute(
                    "SELECT 1 FROM case_evidence_chunks WHERE chunk_id=? AND instr(chunk_text,?)>0",
                    (chunk_id, txn_id),
                ).fetchone() for chunk_id in trail["chunk_ids"]))

    def test_saved_draft_candidates_are_distinct_from_source_trigger(self):
        cached = json.loads((Path(__file__).resolve().parents[1] / "data" / "cached_reports" /
                             "CASE-041.json").read_text(encoding="utf-8"))
        answer = answer_imported_case_question(
            "Which transactions need review?", "CASE-041", cached["evidence"], cached["report"]
        )
        for txn_id in ("TXN-19927", "TXN-19928", "TXN-19930", "TXN-19932"):
            self.assertIn(txn_id, answer["answer"])
        self.assertIn("draft red-flag candidates", answer["answer"])
        self.assertIn("Separately, the source alert", answer["answer"])


if __name__ == "__main__":
    unittest.main()
