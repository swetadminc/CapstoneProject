"""Analytics charts must explain their axes and preserve full category names."""

import json
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


class AnalyticsUiTests(unittest.TestCase):
    def test_typology_and_action_charts_have_explanatory_tooltips(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run(timeout=30)
        app.session_state["user_name"] = "Chart Reviewer"
        app.session_state["user_role"] = "Investigator"
        app.switch_page("pages/5_Analytics.py").run(timeout=30)
        self.assertFalse(app.exception)
        charts = app.get("vega_lite_chart")
        self.assertGreaterEqual(len(charts), 5)
        typology = json.loads(charts[1].proto.spec)
        self.assertEqual(typology["encoding"]["x"]["title"], "Number of stored alerts")
        self.assertEqual(typology["encoding"]["y"]["title"], "Recorded alert typology")
        self.assertEqual(typology["encoding"]["y"]["axis"]["labelLimit"], 350)
        self.assertIn("What this means", [tip["title"] for tip in typology["encoding"]["tooltip"]])
        captions = [item.value for item in app.get("caption")]
        self.assertTrue(any("not final case outcomes" in caption for caption in captions) or
                        any("No decisions have been recorded" in item.value for item in app.get("info")))
        self.assertTrue(any("X-axis: week ending date" in caption for caption in captions))


if __name__ == "__main__":
    unittest.main()
