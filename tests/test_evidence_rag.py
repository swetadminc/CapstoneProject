"""Read-only source and chunk provenance checks for the public RAG screen."""

import unittest
import os
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from data import runtime_db

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


class EvidenceRagTests(unittest.TestCase):
    def test_railway_public_default_shows_synthetic_intake(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {
                "RAILWAY_PUBLIC_DOMAIN": "investigateiq.example",
                "FICTIONAL_INTAKE_DB_PATH": str(Path(directory) / "public-intake.db"),
            }):
                os.environ.pop("ENABLE_FICTIONAL_INTAKE", None)
                app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
                app.switch_page("pages/8_Evidence_RAG.py").run(timeout=30)
                app.session_state["rag_view"] = "Fictional Intake"
                app.run(timeout=30)
                self.assertFalse(app.exception)
                self.assertEqual(app.session_state["rag_view"], "Fictional Intake")
                self.assertTrue(any(item.label == "Intake monthly baseline (INR)"
                                    for item in app.number_input))

    def test_fictional_intake_stays_inaccessible_when_feature_flag_is_off(self):
        with patch.dict(os.environ, {"ENABLE_FICTIONAL_INTAKE": "0"}):
            app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
            app.switch_page("pages/8_Evidence_RAG.py").run(timeout=30)
            app.session_state["rag_view"] = "Fictional Intake"
            app.run(timeout=30)
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["rag_view"], "Case records")
            self.assertFalse(any(item.label == "Intake monthly baseline (INR)"
                                 for item in app.number_input))

    def test_case_records_show_fictional_kyc_and_transaction_path(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
        app.session_state["rag_case_id"] = "CASE-041"
        app.switch_page("pages/8_Evidence_RAG.py").run(timeout=30)
        self.assertFalse(app.exception)
        self.assertEqual(app.selectbox(key="rag_case_choice").value, "CASE-041")
        page = "\n".join(item.value for item in app.get("markdown"))
        headings = "\n".join(item.value for item in app.get("subheader"))
        self.assertIn("Transaction path", headings)
        self.assertIn("FICTIONAL COURSE SAMPLE", page)
        self.assertNotIn("github.com", page)
        self.assertTrue(any("Current case index:" in item.value and
                            "not the source-document date" in item.value
                            for item in app.get("caption")))

    def test_matched_case_shows_recomputed_timeline(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
        app.session_state["rag_case_id"] = "CASE-043"
        app.switch_page("pages/8_Evidence_RAG.py").run(timeout=30)
        self.assertFalse(app.exception)
        headings = "\n".join(item.value for item in app.get("subheader"))
        self.assertIn("Recomputed ten-transaction alert", headings)
        self.assertTrue(any("complete ten-row timeline" in item.label for item in app.get("expander")))
        self.assertTrue(any("Review-window link register · 10 row(s)" == item.label for item in app.get("expander")))
        open_source = next(item for item in app.button if item.label == "Open this transaction's source chunk")
        open_source.click().run(timeout=30)
        self.assertFalse(app.exception)
        case_source = next(item for item in app.selectbox if item.label == "Case source")
        self.assertEqual(case_source.value, "CASE-LEDGER-CASE-043")

    def test_rule_lab_recalculates_fictional_batch_without_a_queue_write(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
        app.switch_page("pages/8_Evidence_RAG.py").run(timeout=30)
        app.session_state["rag_view"] = "Rule Lab"
        app.run(timeout=30)
        self.assertFalse(app.exception)
        self.assertTrue(any("Review signal" in item.value for item in app.get("warning")))
        debit = next(item for item in app.number_input if item.label == "Each of six outgoing transfers (INR)")
        debit.set_value(100000).run(timeout=30)
        self.assertFalse(app.exception)
        self.assertTrue(any("No review signal" in item.value for item in app.get("success")))

    def test_gated_fictional_intake_saves_searchable_case_packet(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = str(Path(directory) / "fictional.db")
            action_path = str(Path(directory) / "actions.db")
            with patch.dict(os.environ, {"ENABLE_FICTIONAL_INTAKE": "1", "FICTIONAL_INTAKE_DB_PATH": db_path}), \
                    patch.object(runtime_db, "RUNTIME_DB_PATH", action_path), \
                    patch.object(runtime_db, "_initialized", False):
                app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
                app.session_state["user_name"] = "Case Reviewer"
                app.session_state["user_role"] = "Investigator"
                app.switch_page("pages/8_Evidence_RAG.py").run(timeout=30)
                app.session_state["rag_view"] = "Fictional Intake"
                app.run(timeout=30)
                self.assertFalse(app.exception)
                next(button for button in app.button if button.label == "Calculate and save fictional case").click().run(timeout=30)
                self.assertFalse(app.exception)
                self.assertTrue(any("Saved: FIC-CASE-" in item.value for item in app.get("success")))
                with closing(sqlite3.connect(db_path)) as conn:
                    self.assertEqual(conn.execute("SELECT COUNT(*) FROM fictional_intake_cases").fetchone()[0], 1)
                    self.assertEqual(conn.execute("SELECT COUNT(*) FROM fictional_intake_documents").fetchone()[0], 5)
                    case_id = conn.execute("SELECT case_id FROM fictional_intake_cases").fetchone()[0]
                app.text_input(key=f"fic_chunk_search_{case_id}").set_value("baseline").run(timeout=30)
                self.assertFalse(app.exception)
                self.assertTrue(any("matching passage(s)" in item.value for item in app.get("caption")))
                self.assertTrue(any("baseline" in item.value.lower() for item in app.get("markdown")))
                self.assertTrue(any("passage" in item.label.lower() for item in app.get("expander")))
                app.switch_page("pages/0_Case_Queue.py").run(timeout=30)
                self.assertFalse(app.exception)
                self.assertTrue(any(case_id in item.value for item in app.get("markdown")))
                app.button(key=f"inv_{case_id}").click().run(timeout=30)
                self.assertFalse(app.exception)
                app.session_state["selected_case_id"] = case_id
                app.switch_page("pages/2_Investigation_Demo.py").run(timeout=30)
                self.assertTrue(any("feature-gated fictional intake store" in item.value
                                    for item in app.get("info")))
                app.selectbox(key=f"fic_suggestion_{case_id}_0").set_value(
                    "Request more information.").run(timeout=30)
                self.assertFalse(app.exception)
                self.assertIn("request the original identity/KYC",
                              app.session_state[f"fictional_chat_{case_id}"][-1]["content"])
                app.selectbox(key=f"fic_suggestion_{case_id}_2").set_value(
                    "Explain for compliance review.").run(timeout=30)
                self.assertFalse(app.exception)
                self.assertIn("Compliance review brief",
                              app.session_state[f"fictional_chat_{case_id}"][-1]["content"])
                app.session_state[f"fic_action_{case_id}"] = "Escalate for Compliance review"
                app.session_state[f"fic_rationale_{case_id}"] = (
                    "Independent identity and source-of-funds evidence is missing."
                )
                app.run(timeout=30)
                app.button(key=f"fic_submit_{case_id}").click().run(timeout=30)
                self.assertFalse(app.exception)
                self.assertEqual(runtime_db.get_latest_decision_per_case()[case_id]["action"], "escalate")
                self.assertEqual(len(runtime_db.get_audit_log(case_id)), 1)
                app.switch_page("pages/3_Compliance_Queue.py").run(timeout=30)
                self.assertFalse(app.exception)
                self.assertTrue(any(case_id in item.value for item in app.get("markdown")))
                self.assertTrue(any("Independent identity and source-of-funds evidence is missing."
                                    in item.value for item in app.get("markdown")))

    def test_guest_can_inspect_source_chunks_and_method(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
        app.switch_page("pages/8_Evidence_RAG.py").run(timeout=30)
        app.session_state["rag_view"] = "Source & chunks"
        app.run(timeout=30)
        self.assertFalse(app.exception)
        page = "\n".join(item.value for item in app.get("markdown"))
        headings = "\n".join(item.value for item in app.get("subheader"))
        self.assertIn("Evidence & RAG", page)
        self.assertIn("Original source document", headings)
        self.assertIn("How this document was split", headings)
        self.assertIn("No vector embeddings are used", page)
        self.assertNotIn("github.com", page)
        labels = [item.label for item in app.get("expander")]
        self.assertIn("Read the complete source text", labels)
        self.assertGreaterEqual(len(labels), 2)
        app.session_state["rag_view"] = "Method & code"
        app.run(timeout=30)
        self.assertFalse(app.exception)
        page = "\n".join(item.value for item in app.get("markdown"))
        self.assertIn("knowledge_search.py", page)
        self.assertNotIn("github.com", page)
        labels = [item.label for item in app.get("expander")]
        self.assertEqual(sum(label[:1].isdigit() for label in labels), 8)
        self.assertIn("3 · Split case records", labels)
        self.assertIn("6 · Inspect a transaction link", labels)

    def test_admin_defines_rag_okf_and_explains_bm25_score(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
        app.session_state["user_name"] = "Knowledge Reviewer"
        app.session_state["user_role"] = "Admin"
        app.session_state["kb_admin_unlocked"] = True
        app.switch_page("pages/1_Admin_Knowledge_Base.py").run(timeout=30)
        self.assertFalse(app.exception)
        text = "\n".join(item.value for item in app.get("markdown"))
        self.assertIn("Retrieval-Augmented Generation", text)
        self.assertIn("Open Knowledge Format", text)
        self.assertIn("Case KYC and transaction records", text)
        app.text_input(key="kb_query").set_value("source of funds").run(timeout=30)
        self.assertFalse(app.exception)
        self.assertTrue(any(item.label == "BM25 score" for item in app.get("metric")))
        self.assertTrue(any("not a percentage" in item.value for item in app.get("info")))

    def test_document_selection_shows_its_chunks(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
        app.switch_page("pages/8_Evidence_RAG.py").run(timeout=30)
        app.session_state["rag_view"] = "Source & chunks"
        app.run(timeout=30)
        app.selectbox(key="rag_doc_choice").set_value("PB-AML-STR-01").run(timeout=30)
        self.assertFalse(app.exception)
        self.assertEqual(app.selectbox(key="rag_doc_choice").value, "PB-AML-STR-01")
        labels = [item.label for item in app.get("expander")]
        self.assertTrue(any("PB-AML-STR-01" in label and "metadata" in label for label in labels))
        self.assertTrue(any("PB-AML-STR-01" in label and "body" in label for label in labels))

    def test_deep_link_does_not_lock_document_picker(self):
        app = AppTest.from_file(str(APP_PATH))
        app.query_params["doc"] = "PB-AML-STR-01"
        app.run(timeout=30)
        app.switch_page("pages/8_Evidence_RAG.py").run(timeout=30)
        self.assertEqual(app.selectbox(key="rag_doc_choice").value, "PB-AML-STR-01")
        app.selectbox(key="rag_doc_choice").set_value("PB-AML-STR-02").run(timeout=30)
        self.assertFalse(app.exception)
        self.assertEqual(app.selectbox(key="rag_doc_choice").value, "PB-AML-STR-02")

    def test_search_result_opens_exact_chunk_on_this_page(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
        app.switch_page("pages/8_Evidence_RAG.py").run(timeout=30)
        app.session_state["rag_view"] = "Search the index"
        app.run(timeout=30)
        app.text_input[0].set_value("structuring cash deposits").run(timeout=30)
        open_buttons = [item for item in app.button if item.label == "Open this chunk in its source"]
        self.assertTrue(open_buttons)
        open_buttons[0].click().run(timeout=30)
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["rag_view"], "Source & chunks")
        self.assertTrue(any("This is the chunk opened" in item.value for item in app.get("success")))


if __name__ == "__main__":
    unittest.main()
