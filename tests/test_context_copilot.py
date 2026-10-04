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
        self.assertIn("Case Queue", answer_context_question("What can I do on this page?", "Case Queue")["answer"])
        self.assertIn("Case Queue", answer_context_question("How do I choose a case?", "Home")["answer"])
        self.assertIn("cannot independently verify", answer_context_question(
            "What information can the Copilot actually verify?", "Home")["answer"])

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

    def test_floating_question_panel_is_available_on_queue_and_evidence(self):
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(app_path)).run(timeout=30)
        app.session_state["user_name"] = "Case Reviewer"
        app.session_state["user_role"] = "Investigator"
        app.switch_page("pages/0_Case_Queue.py").run(timeout=30)
        self.assertFalse(app.exception)
        self.assertEqual(app.button(key="floating_copilot_open").label, "✦ Ask InvestigateIQ")
        app.button(key="floating_copilot_open").click().run(timeout=30)
        self.assertTrue(app.session_state["iq_floating_copilot_open"])
        suggestion = next(item for item in app.selectbox if item.label == "Suggested questions")
        suggestion.set_value("What am I looking at?").run(timeout=30)
        self.assertTrue(any("Selected question: What am I looking at?" in item.value
                            for item in app.get("markdown")))
        ask_buttons = [item for item in app.button if item.label == "Send"]
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
        next(item for item in app.button if item.label == "Send").click().run(timeout=30)
        self.assertFalse(app.exception)
        self.assertTrue(any("Selected passage CASE-ALERT-CASE-041-C1" in item.value
                            for item in app.get("markdown")))
        next(item for item in app.button if item.label == "Inspect the first cited source").click().run(timeout=30)
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["rag_case_choice"], "CASE-041")

    def test_floating_chat_answers_three_consecutive_questions(self):
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(app_path)).run(timeout=30)
        app.session_state["user_name"] = "Case Reviewer"
        app.session_state["user_role"] = "Investigator"
        app.session_state["selected_case_id"] = "CASE-041"
        app.switch_page("pages/2_Investigation_Demo.py").run(timeout=30)
        app.button(key="floating_copilot_open").click().run(timeout=30)
        questions = (
            "Why was this alert triggered?",
            "How many transactions were stored in one month, and which need review?",
            "What KYC and counterparty evidence is missing?",
        )
        for number, question in enumerate(questions, 1):
            with self.subTest(number=number):
                app.text_input(key="context_copilot_question").set_value(question)
                next(item for item in app.button if item.label == "Send").click().run(timeout=30)
                self.assertFalse(app.exception)
                history = app.session_state["chat_CASE-041"]
                self.assertEqual(len(history), number * 2)
                self.assertEqual(history[-2]["content"], question)
                self.assertTrue(history[-1]["content"].strip())
        transcript = "\n".join(item.value for item in app.get("markdown"))
        self.assertIn("InvestigateIQ Copilot", transcript)
        self.assertTrue(any("Conversation" in item.value and "scroll up" in item.value
                            for item in app.get("caption")))
        self.assertNotIn("Earlier messages", transcript)

    def test_admin_page_suggestions_send_repeatedly_without_message_field(self):
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(app_path)).run(timeout=30)
        app.session_state["user_name"] = "Case Reviewer"
        app.session_state["user_role"] = "Investigator"
        app.session_state["active_case_id"] = "CASE-043"
        app.switch_page("pages/4_Admin_Rule_Config.py").run(timeout=30)
        self.assertFalse(app.exception)
        app.button(key="floating_copilot_open").click().run(timeout=30)
        questions = (
            "Why was this alert triggered?",
            "Show the transaction sequence and recorded counterparties.",
            "Can we conclude that these funds are lawful or unlawful?",
        )
        for index, question in enumerate(questions):
            app.selectbox(key=f"context_copilot_suggestion_CASE-043_{2 * index}").set_value(
                question).run(timeout=30)
            self.assertEqual(app.text_input(key="context_copilot_question").value, "")
            next(item for item in app.button if item.label == "Send").click().run(timeout=30)
            self.assertFalse(app.exception)
            history = app.session_state["chat_CASE-043"]
            self.assertEqual(len(history), 2 * (index + 1))
            self.assertEqual(history[-2]["content"], question)
            self.assertTrue(history[-1]["content"].strip())

    def test_case_conversation_follows_navigation_but_not_a_new_case(self):
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(app_path)).run(timeout=30)
        app.session_state["user_name"] = "Case Reviewer"
        app.session_state["user_role"] = "Investigator"
        app.session_state["selected_case_id"] = "CASE-010"
        app.switch_page("pages/2_Investigation_Demo.py").run(timeout=30)
        self.assertFalse(app.exception)
        app.button(key="floating_copilot_open").click().run(timeout=30)
        app.text_input(key="context_copilot_question").set_value("Summarize this case")
        next(item for item in app.button if item.label == "Send").click().run(timeout=30)
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

    def test_floating_panel_renders_on_every_named_screen(self):
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
                self.assertEqual(app.button(key="floating_copilot_open").label, "✦ Ask InvestigateIQ")
                self.assertFalse(any(item.label == "✦ Ask InvestigateIQ" for item in app.get("expander")))

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
