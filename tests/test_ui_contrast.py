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

    def test_queue_kpis_are_compact_with_a_gradient_edge(self):
        self.assertRegex(_GLOBAL_CSS, r'\.iq-card\.iq-kpi-card\s*\{[^}]*min-height:\s*82px')
        self.assertRegex(_GLOBAL_CSS, r'\.iq-card\.iq-kpi-card\s*\{[^}]*linear-gradient\([^;]+border-box')
        self.assertIn('repeat(auto-fit, minmax(200px, 1fr))', _GLOBAL_CSS)
        self.assertIn('@container (min-width: 800px) and (max-width: 1199px)', _GLOBAL_CSS)
        self.assertIn('@container (min-width: 1200px)', _GLOBAL_CSS)
        self.assertIn('--iq-kpi-accent: #27844E', _GLOBAL_CSS)

    def test_home_navigation_cards_are_compact_and_have_hover_feedback(self):
        nav_rule = re.search(r'\[class\*="st-key-iq_bordered_nav_"\]\s*\{([^}]+)\}', _GLOBAL_CSS)
        self.assertIsNotNone(nav_rule)
        self.assertRegex(nav_rule.group(1), r'\bmin-height:\s*128px')
        self.assertIn('linear-gradient', nav_rule.group(1))
        self.assertIn('[class*="st-key-iq_bordered_nav_"]:hover', _GLOBAL_CSS)
        self.assertIn('translateY(-3px)', _GLOBAL_CSS)

    def test_floating_copilot_context_wraps_page_and_case_badge(self):
        self.assertIn('.iq-floating-context {', _GLOBAL_CSS)
        self.assertIn('flex-wrap: wrap', _GLOBAL_CSS)
        self.assertIn('.iq-floating-page', _GLOBAL_CSS)

    def test_floating_chat_replies_are_compact_and_visually_distinct(self):
        self.assertRegex(_GLOBAL_CSS, r'\.iq-chat-message\s*\{[^}]*font-size:\s*13px')
        self.assertIn('.iq-chat-message.iq-chat-assistant {', _GLOBAL_CSS)
        self.assertIn('transform: rotate(-0.22deg)', _GLOBAL_CSS)
        self.assertIn('color: #075F66', _GLOBAL_CSS)

    def test_dark_mode_tooltip_icons_have_a_high_contrast_shared_treatment(self):
        self.assertIn('--iq-tooltip-icon: #B8D8FF', _DARK_OVERRIDE_CSS)
        self.assertIn('[data-testid="stTooltipIcon"]', _DARK_OVERRIDE_CSS)
        self.assertIn('fill: var(--iq-tooltip-icon) !important', _DARK_OVERRIDE_CSS)
        self.assertIn('focus-within', _DARK_OVERRIDE_CSS)

    def test_dark_mode_preserves_text_contrast_for_chips_and_evidence_tabs(self):
        self.assertIn('.stApp .iq-chip {', _DARK_OVERRIDE_CSS)
        self.assertIn('color: #D5E8FF !important', _DARK_OVERRIDE_CSS)
        self.assertIn('.stApp .st-key-rag_view', _DARK_OVERRIDE_CSS)
        self.assertIn('color: #D9E9FF !important', _DARK_OVERRIDE_CSS)
        self.assertIn('button[aria-pressed="true"]', _DARK_OVERRIDE_CSS)
        self.assertIn('[role="radio"][aria-checked="true"]', _DARK_OVERRIDE_CSS)


if __name__ == "__main__":
    unittest.main()
