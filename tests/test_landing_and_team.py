"""Smoke checks for the public landing and draft roster screens."""

import unittest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree

from streamlit.testing.v1 import AppTest

from project_identity import PROJECT_SLOGAN, ROSTER_NOTE, TEAM_MEMBERS, TEAM_RESPONSIBILITIES
from scripts.build_ui_walkthrough import SCENES
from ui_common import severity_badge, status_badge

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


class LandingAndTeamTests(unittest.TestCase):
    def test_every_screen_loads_with_public_fictional_intake_enabled(self):
        pages = (
            "pages/home.py", "pages/7_Project_Team.py", "pages/0_Case_Queue.py",
            "pages/2_Investigation_Demo.py", "pages/3_Compliance_Queue.py",
            "pages/5_Analytics.py", "pages/6_Global_Search.py",
            "pages/8_Evidence_RAG.py", "pages/1_Admin_Knowledge_Base.py",
            "pages/4_Admin_Rule_Config.py",
        )
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {
                "RAILWAY_PUBLIC_DOMAIN": "investigateiq.example",
                "FICTIONAL_INTAKE_DB_PATH": str(Path(directory) / "public-smoke.db"),
            }):
                os.environ.pop("ENABLE_FICTIONAL_INTAKE", None)
                for page in pages:
                    with self.subTest(page=page):
                        app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
                        app.session_state["user_name"] = "Case Reviewer"
                        app.session_state["user_role"] = "Investigator"
                        app.switch_page(page).run(timeout=30)
                        self.assertFalse(app.exception)

    def test_walkthrough_distinguishes_saved_case_from_public_fictional_intake(self):
        narration = " ".join(scene["narration"].lower() for scene in SCENES)
        screens = {scene["screen"] for scene in SCENES}
        self.assertTrue({"22_public_intake_form.jpg", "24_public_intake_chunks.jpg",
                         "25_public_intake_review.jpg", "26_public_intake_compliance.jpg"} <= screens)
        self.assertIn("fictional intake", narration)
        self.assertTrue("not uploaded bank documents" in narration or
                        "no bank document or third-party alert is uploaded" in narration)
        self.assertTrue("a no-concern closure is not offered" in narration or
                        "cannot close this incomplete packet as no concern" in narration)
        self.assertNotIn("forty two alerts", narration)
        self.assertNotIn("four expandable steps", narration)
        self.assertNotIn("capstone", narration)

    def test_unknown_badge_text_is_html_escaped(self):
        self.assertEqual(severity_badge('<script>alert(1)</script>'), '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertEqual(status_badge('<img src=x>'), '&lt;img src=x&gt;')

    def test_brand_assets_are_valid_svg_with_readable_slogan(self):
        assets = APP_PATH.parent / "assets"
        for name in ("logo_icon.svg", "logo_full.svg", "logo_full_dark.svg"):
            self.assertEqual(ElementTree.parse(assets / name).getroot().tag,
                             "{http://www.w3.org/2000/svg}svg")
        self.assertEqual(PROJECT_SLOGAN, "Trace the evidence. Own the decision.")

    def test_roster_keeps_sweta_last_without_implying_a_lead_role(self):
        self.assertEqual(TEAM_MEMBERS[-1], "Sweta Singh")
        self.assertEqual(set(TEAM_RESPONSIBILITIES), set(TEAM_MEMBERS))

    def test_guest_can_see_landing_video_before_identity(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
        self.assertFalse(app.exception)
        self.assertEqual(len(app.get("video")), 1)
        self.assertEqual(app.text_input(key="home_demo_name").label, "Your name")
        self.assertEqual(app.button(key="home_demo_continue").label, "Open workspace")
        page = "\n".join(element.value for element in app.get("markdown"))
        self.assertNotIn("Enter the demo", page)
        self.assertIn(PROJECT_SLOGAN, page)
        self.assertIn('aria-label="How this page works"', page)
        self.assertEqual([item.label for item in app.expander], ["ℹ️ Help & definitions"])
        self.assertIn(("Seed Alerts", "44"), [(metric.label, metric.value) for metric in app.metric])

    def test_guest_can_enter_workspace_from_home(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
        self.assertEqual(app.radio(key="home_demo_role").value, "Investigator")
        app.text_input(key="home_demo_name").input("Case Reviewer")
        app.button(key="home_demo_continue").click().run(timeout=30)
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["user_name"], "Case Reviewer")
        self.assertEqual(app.session_state["user_role"], "Investigator")

    def test_guest_can_choose_another_role_with_radio_buttons(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
        app.radio(key="home_demo_role").set_value("Compliance Officer")
        app.text_input(key="home_demo_name").input("Case Reviewer")
        app.button(key="home_demo_continue").click().run(timeout=30)
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["user_role"], "Compliance Officer")

    def test_team_page_shows_source_roster_without_assigned_roles(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
        app.switch_page("pages/7_Project_Team.py").run(timeout=30)
        self.assertFalse(app.exception)
        page = "\n".join(element.value for element in app.get("markdown"))
        for member in TEAM_MEMBERS:
            self.assertIn(member, page)
        self.assertEqual(page.count('class="iq-team-card"'), len(TEAM_MEMBERS))
        self.assertLess(page.index("Team member: Rahul Chainani"), page.index("Team member: Sweta Singh"))
        self.assertIn("Application development &amp; integration", page)
        self.assertIn("Course linkage &amp; project explanation", page)
        self.assertIn("not claims about work already completed", ROSTER_NOTE)
        self.assertNotIn("CEO / Product Visionary", page)
        self.assertNotIn("Solution Architect", page)

    def test_team_settings_can_switch_theme(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
        app.switch_page("pages/7_Project_Team.py").run(timeout=30)
        app.button(key="team_theme_button").click().run(timeout=30)
        self.assertFalse(app.exception)
        self.assertTrue(app.session_state["dark_mode_toggle"])
        page = "\n".join(element.value for element in app.get("markdown"))
        self.assertIn("border-color: #729BDD !important", page)

    def test_home_sidebar_toggle_applies_dark_styles(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
        app.sidebar.toggle(key="dark_mode_toggle").set_value(True).run(timeout=30)
        self.assertFalse(app.exception)
        self.assertTrue(app.session_state["dark_mode_toggle"])
        page = "\n".join(element.value for element in app.get("markdown"))
        self.assertIn("background: #0F1826 !important", page)

    def test_dark_mode_survives_navigation_to_case_queue(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
        app.sidebar.toggle(key="dark_mode_toggle").set_value(True).run(timeout=30)
        app.switch_page("pages/0_Case_Queue.py").run(timeout=30)
        self.assertFalse(app.exception)
        self.assertTrue(app.session_state["iq_dark_mode"])
        self.assertTrue(app.session_state["dark_mode_toggle"])
        page = "\n".join(element.value for element in app.get("markdown"))
        self.assertIn("background: #0F1826 !important", page)

    def test_queue_search_treats_brackets_as_plain_text(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
        app.text_input(key="home_demo_name").input("Case Reviewer")
        app.button(key="home_demo_continue").click().run(timeout=30)
        app.switch_page("pages/0_Case_Queue.py").run(timeout=30)
        search = next(item for item in app.text_input if item.label == "Search customer name")
        search.set_value("[").run(timeout=30)
        self.assertFalse(app.exception)

    def test_queue_cards_define_all_workflow_states_and_severity_overlap(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=90)
        app.session_state["user_name"] = "Case Reviewer"
        app.session_state["user_role"] = "Investigator"
        app.switch_page("pages/0_Case_Queue.py").run(timeout=90)
        self.assertFalse(app.exception)
        page = "\n".join(item.value for item in app.get("markdown"))
        self.assertEqual(page.count('class="iq-card iq-kpi-card'), 6)
        self.assertIn('class="iq-flashlight-svg"', page)
        self.assertIn("Info requested", page)
        self.assertTrue(any("High severity is a separate source label" in item.value
                            for item in app.get("caption")))
        self.assertTrue(any(item.label == "What these queue numbers mean"
                            for item in app.get("expander")))

    def test_selected_case_survives_investigation_rerun(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
        app.text_input(key="home_demo_name").input("Case Reviewer")
        app.button(key="home_demo_continue").click().run(timeout=30)
        app.session_state["selected_case_id"] = "CASE-041"
        app.switch_page("pages/2_Investigation_Demo.py").run(timeout=30)
        self.assertIn("CASE-041", app.selectbox(key="investigation_case_choice").value)
        labels = app.selectbox(key="investigation_case_choice").options
        self.assertFalse(any("legitimate twin" in label or "suspicious, cached" in label for label in labels))
        self.assertTrue(any("CASE-001" in label and "owner ambiguous" in label for label in labels))
        app.run(timeout=30)
        self.assertIn("CASE-041", app.selectbox(key="investigation_case_choice").value)
        app.button(key="floating_copilot_open").click().run(timeout=30)
        suggestion = app.selectbox(key="context_copilot_suggestion_CASE-041_0")
        suggestion.set_value("Why was this alert triggered?").run(timeout=30)
        self.assertIn("CASE-041", app.selectbox(key="investigation_case_choice").value)
        self.assertEqual(app.session_state["active_case_id"], "CASE-041")

    def test_new_matched_case_offers_current_database_calculation(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
        app.text_input(key="home_demo_name").input("Case Reviewer")
        app.button(key="home_demo_continue").click().run(timeout=30)
        app.session_state["selected_case_id"] = "CASE-043"
        app.switch_page("pages/2_Investigation_Demo.py").run(timeout=30)
        self.assertFalse(app.exception)
        self.assertIn("CASE-043", app.selectbox(key="investigation_case_choice").value)
        mode = next(item for item in app.radio if item.label == "Mode")
        self.assertIn("Calculated (current database, no AI call)", mode.options)


if __name__ == "__main__":
    unittest.main()
