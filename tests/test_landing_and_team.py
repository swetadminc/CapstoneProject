"""Smoke checks for the public landing and draft roster screens."""

import unittest
from pathlib import Path
from xml.etree import ElementTree

from streamlit.testing.v1 import AppTest

from project_identity import PROJECT_SLOGAN, ROSTER_NOTE, TEAM_MEMBERS, TEAM_RESPONSIBILITIES

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


class LandingAndTeamTests(unittest.TestCase):
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
        self.assertEqual(len(app.expander), 0)

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

    def test_selected_case_survives_investigation_rerun(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
        app.text_input(key="home_demo_name").input("Case Reviewer")
        app.button(key="home_demo_continue").click().run(timeout=30)
        app.session_state["selected_case_id"] = "CASE-041"
        app.switch_page("pages/2_Investigation_Demo.py").run(timeout=30)
        self.assertIn("CASE-041", app.selectbox(key="investigation_case_choice").value)
        app.run(timeout=30)
        self.assertIn("CASE-041", app.selectbox(key="investigation_case_choice").value)

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
