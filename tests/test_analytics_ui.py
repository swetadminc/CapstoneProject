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
        typology_bars = typology["layer"][0]
        self.assertEqual(typology_bars["encoding"]["x"]["title"], "Number of stored alerts")
        self.assertEqual(typology_bars["encoding"]["y"]["title"], "Recorded alert typology")
        self.assertEqual(typology_bars["encoding"]["y"]["axis"]["labelLimit"], 350)
        self.assertIn("What this means", [tip["title"] for tip in typology_bars["encoding"]["tooltip"]])
        captions = [item.value for item in app.get("caption")]
        self.assertTrue(any("not final case outcomes" in caption for caption in captions) or
                        any("No decisions have been recorded" in item.value for item in app.get("info")))
        self.assertTrue(any("X-axis: calendar month based on the alert source date" in caption for caption in captions))
        monthly_volume = json.loads(charts[4].proto.spec)
        self.assertEqual(monthly_volume["layer"][0]["encoding"]["x"]["title"], "Alert month (source date)")
        self.assertEqual(monthly_volume["layer"][0]["encoding"]["y"]["title"], "Number of stored alerts")

    def test_recorded_action_charts_name_both_axes(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run(timeout=30)
        app.session_state["user_name"] = "Chart Reviewer"
        app.session_state["user_role"] = "Investigator"
        app.switch_page("pages/5_Analytics.py").run(timeout=30)
        self.assertFalse(app.exception)
        captions = [item.value for item in app.get("caption")]
        if not app.get("info"):
            self.assertTrue(any("Y-axis: investigator or reviewer display name" in caption for caption in captions))
            self.assertTrue(any("Y-axis: recorded human action" in caption for caption in captions))
        charts = app.get("vega_lite_chart")
        if len(charts) >= 7:
            by_person = json.loads(charts[-2].proto.spec)
            by_action = json.loads(charts[-1].proto.spec)
            self.assertEqual(
                by_person["layer"][0]["encoding"]["y"]["title"],
                "Investigator or reviewer (display name)",
            )
            self.assertEqual(
                by_person["layer"][0]["encoding"]["x"]["title"],
                "Number of saved human actions",
            )
            self.assertEqual(
                by_action["layer"][0]["encoding"]["y"]["title"],
                "Recorded human action type",
            )


if __name__ == "__main__":
    unittest.main()
