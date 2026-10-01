"""Keep product links and indexed source material on this site."""

import re
import unittest
from pathlib import Path
from ui_common import plain_text_html


ROOT = Path(__file__).resolve().parents[1]
APP_FILES = [ROOT / "app.py", ROOT / "ui_common.py", ROOT / "project_identity.py", *sorted((ROOT / "pages").glob("*.py"))]
SOURCE_FILES = sorted((ROOT / "Product Docs" / "dataset" / "knowledge_base").glob("*.md"))


class InternalNavigationTests(unittest.TestCase):
    def test_model_text_is_not_rendered_as_an_external_link(self):
        text = '[private portal](https://example.invalid) <a href="https://example.invalid">open</a>'
        html = plain_text_html(text)
        self.assertIn("[private portal](https://example.invalid)", html)
        self.assertNotIn("<a href=", html)
        self.assertIn("&lt;a href=", html)

    def test_product_has_no_external_navigation_targets(self):
        for path in [*APP_FILES, *SOURCE_FILES]:
            content = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertNotRegex(content, r"https?://|st\.link_button\s*\(|href\s*=", "Keep product navigation and source text on this site")

    def test_page_links_resolve_to_local_pages(self):
        pattern = r"st\.(?:Page|page_link|switch_page)\(\s*['\"](pages/[^'\"]+)"
        for path in APP_FILES:
            content = path.read_text(encoding="utf-8")
            for match in re.finditer(pattern, content):
                with self.subTest(source=path.name, target=match.group(1)):
                    self.assertTrue((ROOT / match.group(1)).is_file())


if __name__ == "__main__":
    unittest.main()
