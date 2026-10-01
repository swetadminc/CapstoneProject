"""Checks that the page guide stays accessible and does not trust markup."""

import unittest
from unittest.mock import patch

from ui_common import page_flow


class PageFlowTests(unittest.TestCase):
    @patch("ui_common.st.markdown")
    def test_renders_purpose_ordered_steps_and_note(self, markdown):
        page_flow("Choose a case", [("Find", "Search alerts"), ("Review", "Read evidence")], "Fictional data")
        html = markdown.call_args.args[0]
        self.assertIn('aria-label="How this page works"', html)
        self.assertIn('<ol class="iq-flow-steps">', html)
        self.assertIn('class="iq-flow-icon" aria-hidden="true"', html)
        self.assertIn("STEP 01", html)
        self.assertIn("Choose a case", html)
        self.assertIn("Search alerts", html)
        self.assertIn("Fictional data", html)

    @patch("ui_common.st.markdown")
    def test_escapes_untrusted_text(self, markdown):
        page_flow("<script>", [("<img>", "a & b")])
        html = markdown.call_args.args[0]
        self.assertNotIn("<script>", html)
        self.assertNotIn("<img>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("a &amp; b", html)

    def test_rejects_empty_flow(self):
        with self.assertRaises(ValueError):
            page_flow("No steps", [])


if __name__ == "__main__":
    unittest.main()
