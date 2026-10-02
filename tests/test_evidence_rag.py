"""Read-only source and chunk provenance checks for the public RAG screen."""

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


class EvidenceRagTests(unittest.TestCase):
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

    def test_matched_case_shows_recomputed_timeline(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
        app.session_state["rag_case_id"] = "CASE-043"
        app.switch_page("pages/8_Evidence_RAG.py").run(timeout=30)
        self.assertFalse(app.exception)
        headings = "\n".join(item.value for item in app.get("subheader"))
        self.assertIn("Recomputed ten-transaction alert", headings)
        self.assertTrue(any("complete ten-row timeline" in item.label for item in app.get("expander")))
        open_source = next(item for item in app.button if item.label == "Open this transaction's source chunk")
        open_source.click().run(timeout=30)
        self.assertFalse(app.exception)
        case_source = next(item for item in app.selectbox if item.label == "Case source")
        self.assertEqual(case_source.value, "CASE-LEDGER-CASE-043")

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
        self.assertEqual(len(labels), 8)
        self.assertIn("3 · Split case records", labels)
        self.assertIn("6 · Inspect a transaction link", labels)

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
