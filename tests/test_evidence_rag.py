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
        self.assertIn("knowledge_search.py", page)
        self.assertIn("No vector embeddings are used", page)
        self.assertNotIn("github.com", page)
        self.assertEqual(len(app.get("expander")), 4)

    def test_document_selection_shows_its_chunks(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
        app.switch_page("pages/8_Evidence_RAG.py").run(timeout=30)
        app.selectbox(key="rag_doc_choice").set_value("PB-AML-STR-01").run(timeout=30)
        self.assertFalse(app.exception)
        page = "\n".join(item.value for item in app.get("markdown"))
        self.assertIn("PB-AML-STR-01", page)
        self.assertIn("metadata", page)
        self.assertIn("body", page)

    def test_deep_link_does_not_lock_document_picker(self):
        app = AppTest.from_file(str(APP_PATH))
        app.query_params["doc"] = "PB-AML-STR-01"
        app.run(timeout=30)
        app.switch_page("pages/8_Evidence_RAG.py").run(timeout=30)
        self.assertEqual(app.selectbox(key="rag_doc_choice").value, "PB-AML-STR-01")
        app.selectbox(key="rag_doc_choice").set_value("PB-AML-STR-02").run(timeout=30)
        self.assertFalse(app.exception)
        self.assertEqual(app.selectbox(key="rag_doc_choice").value, "PB-AML-STR-02")


if __name__ == "__main__":
    unittest.main()
