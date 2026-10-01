"""Regression checks for the dark-mode sidebar contrast bug."""

import re
import unittest

from ui_common import _DARK_OVERRIDE_CSS, _GLOBAL_CSS


class SidebarContrastTests(unittest.TestCase):
    def test_dark_mode_replaces_light_main_gradient(self):
        self.assertIsNotNone(re.search(
            r'\[data-testid="stAppViewContainer"\].*?\{\s*background:',
            _GLOBAL_CSS,
            re.S,
        ))
        dark_rule = re.search(
            r'\[data-testid="stAppViewContainer"\],.*?\{([^}]+)\}',
            _DARK_OVERRIDE_CSS,
            re.S,
        )
        self.assertIsNotNone(dark_rule)
        self.assertRegex(dark_rule.group(1), r'\bbackground:\s*#0F1826\s*!important')

    def test_dark_mode_replaces_light_sidebar_gradient(self):
        self.assertRegex(_GLOBAL_CSS, r'\[data-testid="stSidebar"\]\s*\{\s*background:\s*linear-gradient')
        dark_rule = re.search(r'\[data-testid="stSidebar"\]\s*\{([^}]+)\}', _DARK_OVERRIDE_CSS)
        self.assertIsNotNone(dark_rule)
        self.assertRegex(dark_rule.group(1), r'\bbackground:\s*#16213A\s*!important')

    def test_icons_and_bordered_cards_have_both_theme_styles(self):
        for css in (_GLOBAL_CSS, _DARK_OVERRIDE_CSS):
            self.assertIn('.iq-banner-icon', css)
            self.assertIn('.iq-nav-icon', css)
            self.assertIn('[data-testid="stSidebarNavLink"] [data-testid="stIconEmoji"]', css)
            self.assertIn('[class*="st-key-iq_bordered_"]', css)
        self.assertIn('.iq-team-card', _DARK_OVERRIDE_CSS)
        self.assertIn('.iq-flow-steps li', _DARK_OVERRIDE_CSS)


if __name__ == "__main__":
    unittest.main()
