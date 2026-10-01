"""Read-only source and chunk provenance checks for the public RAG screen."""

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


class EvidenceRagTests(unittest.TestCase):
    def test_guest_can_inspect_source_chunks_and_method(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
        app.switch_page("pages/8_Evidence_RAG.py").run(timeout=30)
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
        self.assertEqual(len(app.get("expander")), 4)

    def test_document_selection_shows_its_chunks(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
        app.switch_page("pages/8_Evidence_RAG.py").run(timeout=30)
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
