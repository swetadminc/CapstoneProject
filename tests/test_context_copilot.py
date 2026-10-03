"""The cross-page Copilot must not invent page, case, or evidence context."""

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from agents.context_copilot import answer_context_question
from data.fictional_intake import intake_fictional_batch, make_generated_fictional_batch, read_fictional_case
from data.knowledge_search import DB_PATH


class ContextCopilotTests(unittest.TestCase):
    def test_page_question_and_missing_case_are_explicit(self):
        page = answer_context_question("What am I looking at?", "Case Queue")
        self.assertIn("Case Queue", page["answer"])
        self.assertEqual(page["sources"], [])
        missing = answer_context_question("Summarize this case", "Case Queue")
        self.assertIn("No case is selected", missing["answer"])
        self.assertEqual(missing["sources"], [])

    def test_selected_evidence_requires_a_real_passage_in_this_case(self):
        with closing(sqlite3.connect(DB_PATH)) as conn:
            valid = conn.execute(
                "SELECT chunk_id FROM case_evidence_chunks WHERE case_id=? LIMIT 1", ("CASE-041",)
            ).fetchone()[0]
            wrong_case = conn.execute(
                "SELECT chunk_id FROM case_evidence_chunks WHERE case_id=? LIMIT 1", ("CASE-010",)
            ).fetchone()[0]
        absent = answer_context_question("Explain this evidence", "Evidence & RAG", "CASE-041")
        self.assertIn("No evidence passage is selected", absent["answer"])
        accepted = answer_context_question("Explain this evidence", "Evidence & RAG", "CASE-041", valid)
        self.assertEqual(accepted["chunk_ids"], [valid])
        self.assertIn("Exact indexed text", accepted["answer"])
        refused = answer_context_question("Explain this evidence", "Evidence & RAG", "CASE-041", wrong_case)
        self.assertEqual(refused["chunk_ids"], [])
        self.assertIn("not available in the selected case", refused["answer"])
        fabricated = answer_context_question("Explain this evidence", "Evidence & RAG", "CASE-041", "FAKE-C999")
        self.assertEqual(fabricated["sources"], [])

    def test_shared_entry_uses_saved_report_provenance_without_rewriting_it(self):
        answer = answer_context_question("Why does the old report say zero chunks?", "Case Queue", "CASE-041")
        self.assertIn("0 case passage(s)", answer["answer"])
        self.assertIn("do not establish when those additional passages became available", answer["answer"])

    def test_fictional_passage_is_scoped_to_its_own_case(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "intake.db")
            with closing(sqlite3.connect(path)) as conn:
                case_a = intake_fictional_batch(conn, make_generated_fictional_batch(300000, 180000, 80000), 80000)["case_id"]
                case_b = intake_fictional_batch(conn, make_generated_fictional_batch(350000, 200000, 90000), 90000)["case_id"]
                chunk_a = read_fictional_case(conn, case_a)["chunks"][0]["chunk_id"]
            with patch("agents.context_copilot.fictional_intake_path", return_value=path):
                valid = answer_context_question("Explain this evidence", "Evidence & RAG", case_a, chunk_a)
                wrong_case = answer_context_question("Explain this evidence", "Evidence & RAG", case_b, chunk_a)
            self.assertEqual(valid["chunk_ids"], [chunk_a])
            self.assertEqual(wrong_case["chunk_ids"], [])

    def test_sidebar_question_panel_is_available_on_queue_and_evidence(self):
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(app_path)).run(timeout=30)
        app.session_state["user_name"] = "Case Reviewer"
        app.session_state["user_role"] = "Investigator"
        app.switch_page("pages/0_Case_Queue.py").run(timeout=30)
        self.assertFalse(app.exception)
        self.assertTrue(any(item.label == "✦ Ask InvestigateIQ" for item in app.get("expander")))
        app.text_input(key="context_copilot_question").set_value("What am I looking at?")
        ask_buttons = [item for item in app.button if item.label == "Ask"]
        self.assertTrue(ask_buttons, [item.label for item in app.button])
        ask_buttons[0].click().run(timeout=30)
        self.assertFalse(app.exception)
        self.assertTrue(any("Case Queue lists stored fictional alerts" in item.value
                            for item in app.get("markdown")))
        app.session_state["rag_case_id"] = "CASE-041"
        app.session_state["rag_case_doc_id"] = "CASE-ALERT-CASE-041"
        app.session_state["rag_case_chunk_id"] = "CASE-ALERT-CASE-041-C1"
        app.switch_page("pages/8_Evidence_RAG.py").run(timeout=30)
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["active_case_id"], "CASE-041")
        self.assertEqual(app.session_state["context_evidence_chunk_id"], "CASE-ALERT-CASE-041-C1")
        app.text_input(key="context_copilot_question").set_value("Explain this evidence")
        next(item for item in app.button if item.label == "Ask").click().run(timeout=30)
        self.assertFalse(app.exception)
        self.assertTrue(any("Selected passage CASE-ALERT-CASE-041-C1" in item.value
                            for item in app.get("markdown")))
        next(item for item in app.button if item.label == "Open cited passage").click().run(timeout=30)
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["rag_case_choice"], "CASE-041")

    def test_case_conversation_follows_navigation_but_not_a_new_case(self):
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(app_path)).run(timeout=30)
        app.session_state["user_name"] = "Case Reviewer"
        app.session_state["user_role"] = "Investigator"
        app.session_state["selected_case_id"] = "CASE-010"
        app.switch_page("pages/2_Investigation_Demo.py").run(timeout=30)
        self.assertFalse(app.exception)
        app.text_input(key="context_copilot_question").set_value("Summarize this case")
        next(item for item in app.button if item.label == "Ask").click().run(timeout=30)
        self.assertFalse(app.exception)
        self.assertTrue(app.session_state["chat_CASE-010"])
        app.switch_page("pages/5_Analytics.py").run(timeout=30)
        self.assertFalse(app.exception)
        self.assertTrue(any("Selected case CASE-010" in item.value for item in app.get("markdown")))
        app.session_state["selected_case_id"] = "CASE-011"
        app.switch_page("pages/2_Investigation_Demo.py").run(timeout=30)
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["active_case_id"], "CASE-011")
        self.assertNotIn("chat_CASE-011", app.session_state)
        self.assertFalse(any("Selected case CASE-010" in item.value for item in app.get("markdown")))

    def test_shared_panel_renders_on_every_named_screen(self):
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(app_path)).run(timeout=30)
        app.session_state["user_name"] = "Case Reviewer"
        app.session_state["user_role"] = "Investigator"
        pages = (
            "pages/home.py", "pages/0_Case_Queue.py", "pages/1_Admin_Knowledge_Base.py",
            "pages/2_Investigation_Demo.py", "pages/3_Compliance_Queue.py",
            "pages/4_Admin_Rule_Config.py", "pages/5_Analytics.py",
            "pages/6_Global_Search.py", "pages/7_Project_Team.py", "pages/8_Evidence_RAG.py",
        )
        for page in pages:
            with self.subTest(page=page):
                app.switch_page(page).run(timeout=30)
                self.assertFalse(app.exception)
                self.assertTrue(any(item.label == "✦ Ask InvestigateIQ" for item in app.get("expander")))

    def test_evidence_page_keeps_an_explicitly_selected_case(self):
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(app_path)).run(timeout=30)
        app.session_state["user_name"] = "Case Reviewer"
        app.session_state["user_role"] = "Investigator"
        app.session_state["selected_case_id"] = "CASE-017"
        app.switch_page("pages/2_Investigation_Demo.py").run(timeout=30)
        self.assertEqual(app.session_state["active_case_id"], "CASE-017")
        app.switch_page("pages/8_Evidence_RAG.py").run(timeout=30)
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["rag_case_choice"], "CASE-017")
        self.assertEqual(app.session_state["active_case_id"], "CASE-017")


if __name__ == "__main__":
    unittest.main()
