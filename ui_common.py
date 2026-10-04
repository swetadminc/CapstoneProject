# -*- coding: utf-8 -*-
"""
Shared session identity — pending item #2 ("Login / role-based access") —
plus the shared design system (colors, banner, badges, cards) every page
uses, added when the six pages' hand-duplicated `.iq-banner` CSS block was
pulled out into one place.

Deliberately still mock auth (no password, no real user database) — that
matches the documented NFR scope everywhere else in this build (see the
Admin passcode gates). What this adds is a single place to say who you are
and what role you're acting in, instead of retyping your name into a
different text box on every page. Every page that records a decision still
requires that name explicitly at submit time — this doesn't remove that
requirement, it just removes the retyping.
"""
import os
import sqlite3
from html import escape
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
from project_identity import COURSE_LABEL, GROUP_LABEL, PROJECT_SLOGAN

ROLES = ["Investigator", "Team Lead", "Compliance Officer", "Admin"]
_ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
LOGO_ICON = os.path.join(_ASSETS_DIR, "logo_icon.svg")
LOGO_FULL_LIGHT = os.path.join(_ASSETS_DIR, "logo_full.svg")
LOGO_FULL_DARK = os.path.join(_ASSETS_DIR, "logo_full_dark.svg")


def get_admin_passcode() -> str:
    """Use deployment environment first, then an ignored local secret."""
    configured = os.environ.get("ADMIN_PASSCODE")
    if configured:
        return configured
    try:
        local_secret = st.secrets.get("ADMIN_PASSCODE")
    except StreamlitSecretNotFoundError:
        local_secret = None
    return str(local_secret) if local_secret else "investigateiq-admin"


def plain_text_html(value: object, muted: bool = False) -> str:
    """Display untrusted source/model text without turning URLs into links."""
    style = "font-size:0.875rem;color:var(--iq-text-secondary);" if muted else ""
    return f'<div style="white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.5;{style}">{escape(str(value))}</div>'

# ---------------------------------------------------------------------------
# Design system — one shared CSS block instead of six copies of the same
# .iq-banner rules. Colors are CSS custom properties, redeclared under a
# second <style> block when dark mode is on (see _DARK_OVERRIDE_CSS below)
# so the small set of custom components here (banner, badges, cards) adapt.
#
# This can't be done with a plain `prefers-color-scheme: dark` media query:
# Streamlit removes its own user-facing Settings > Theme switcher entirely
# as soon as ANY `[theme]` key is set in .streamlit/config.toml (confirmed
# empirically — the menu option disappears, not just the default value),
# and the OS-level color-scheme preference isn't otherwise wired to
# anything Streamlit renders. Since the custom navy primaryColor in
# config.toml is worth keeping for brand consistency, dark mode here is a
# real, in-app toggle (see require_login()'s sidebar) driven by
# st.session_state — Python decides which CSS block to emit, not the
# browser.
# ---------------------------------------------------------------------------
_GLOBAL_CSS = """
<style>
:root {
    --iq-navy: #1A2A4A;
    --iq-navy-light: #C9D6E8;
    --iq-primary: #2E63BF;
    --iq-card-bg: #FFFFFF;
    --iq-card-border: #E3E7EE;
    --iq-text-secondary: #5B6B85;
    --iq-heading: var(--iq-navy);
    --iq-sev-high-bg: #FCE2E2; --iq-sev-high: #B02A2A;
    --iq-sev-medium-bg: #FFF3D6; --iq-sev-medium: #B57808;
    --iq-sev-low-bg: #E8F3EC; --iq-sev-low: #27844E;
    --iq-status-open-bg: #FFF3D6; --iq-status-open: #B57808;
    --iq-status-escalate-bg: #FCE2E2; --iq-status-escalate: #B02A2A;
    --iq-status-close-bg: #E8F3EC; --iq-status-close: #27844E;
    --iq-status-info-bg: #EEF3FB; --iq-status-info: #2E63BF;
}
/* Light mode isn't flat white — it's a soft blue radiance instead, the
   light-side counterpart to dark mode's navy (see _DARK_OVERRIDE_CSS
   below, which overrides this background-color outright for dark mode).
   Two overlapping radial glows (upper-left, upper-right) fading into a
   pale blue base, rather than one centered blob, so it reads as ambient
   light rather than a single spotlight. */
[data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background:
        radial-gradient(ellipse 900px 560px at 12% -8%, rgba(139, 180, 255, 0.30), transparent 60%),
        radial-gradient(ellipse 760px 520px at 92% 4%, rgba(120, 165, 255, 0.20), transparent 58%),
        #F4F8FF;
}
[data-testid="stMainBlockContainer"] {
    /* Streamlit's default 96px top padding leaves a large blank band above
       the first banner. 48px keeps content below its 60px overlay header. */
    padding-top: 48px !important;
}
[data-testid="stSidebar"] {
    background: linear-gradient(165deg, #EAF1FF 0%, #F4F8FF 55%);
}
.iq-card {
    box-shadow: 0 1px 3px rgba(26,42,74,0.06);
}
.iq-banner {
    background: linear-gradient(135deg, var(--iq-navy), #24365E);
    color: white; padding: 16px 24px; border-radius: 12px;
    box-shadow: 0 2px 10px rgba(26,42,74,0.18); margin-bottom: 4px;
}
.iq-banner h1 { margin: 0; font-size: 22px; }
.iq-banner p { margin: 4px 0 0 0; color: var(--iq-navy-light); font-size: 13px; }
.iq-banner-icon {
    display: inline-flex; align-items: center; justify-content: center;
    width: 36px; height: 36px; margin-right: 7px; vertical-align: middle;
    background: #EAF2FF; border: 1px solid #B9D0F5; border-radius: 10px;
    font-size: 23px; line-height: 1;
}
[data-testid="stSidebarNavLink"] [data-testid="stIconEmoji"] {
    display: inline-flex; align-items: center; justify-content: center;
    width: 27px; height: 27px; flex: 0 0 27px;
    background: #DCEAFF; border: 1px solid #B8CEF0; border-radius: 8px;
}
.iq-card {
    background: var(--iq-card-bg); border: 1px solid var(--iq-card-border);
    border-radius: 12px; padding: 16px 20px;
}
.iq-brand-slogan {
    margin: 5px 0 15px; padding: 9px 11px; border-left: 3px solid #2E63BF;
    border-radius: 0 9px 9px 0; background: #E5EFFD;
    color: #173C78; font-size: 13px; font-weight: 700; line-height: 1.45;
}
[class*="st-key-iq_bordered_"] {
    background: #FBFCFF !important; border: 1.5px solid #B8CAE6 !important;
    border-radius: 14px !important;
}
.iq-flow {
    --iq-flow-connector: #477ABD;
    margin: 8px 0 14px; padding: 10px 14px;
    border: 2.5px solid transparent; border-radius: 16px;
    background: linear-gradient(120deg, #F8FBFF, #EDF5FF 60%, #F5F0FF) padding-box,
                linear-gradient(120deg, #659CF0, #8DCFC7, #B79AEF) border-box;
    box-shadow: 0 4px 16px rgba(31, 75, 136, 0.11);
}
.iq-flow-heading { color: var(--iq-heading); font-weight: 800; font-size: 14px; margin-bottom: 1px; }
.iq-flow-heading::before { content: '🧭'; margin-right: 8px; }
.iq-flow-purpose, .iq-flow-note { color: var(--iq-text-secondary); font-size: 12px; line-height: 1.35; }
.iq-flow-steps { display: flex; gap: 20px; list-style: none; padding: 0; margin: 8px 0 5px; }
.iq-flow-steps li {
    --iq-step-border: #8FB9EE; --iq-step-bg: #F0F6FF; --iq-step-icon-bg: #DDEBFF;
    position: relative; box-sizing: border-box; flex: 1; min-width: 0;
    display: grid; grid-template-columns: 27px minmax(0, 1fr);
    column-gap: 8px; row-gap: 2px; align-content: start;
    border: 1.5px solid var(--iq-step-border); border-radius: 11px;
    background: var(--iq-step-bg); padding: 8px 9px;
    box-shadow: 0 2px 7px rgba(28, 61, 106, 0.06);
}
.iq-flow-steps li:nth-child(4n+2) {
    --iq-step-border: #C6A2F0; --iq-step-bg: #F9F3FF; --iq-step-icon-bg: #EEDDFF;
}
.iq-flow-steps li:nth-child(4n+3) {
    --iq-step-border: #7ECDBD; --iq-step-bg: #EEFAF5; --iq-step-icon-bg: #D9F5EC;
}
.iq-flow-steps li:nth-child(4n+4) {
    --iq-step-border: #E9BB72; --iq-step-bg: #FFF9EC; --iq-step-icon-bg: #FFF0D2;
}
.iq-flow-steps li:not(:last-child)::after {
    content: ''; position: absolute; right: -19px; top: 50%;
    width: 17px; height: 5px; transform: translateY(-50%);
    background: radial-gradient(circle, var(--iq-flow-connector) 2px, transparent 2.5px) 0 0 / 9px 5px repeat-x;
    animation: iq-flow-dots 1.5s linear infinite;
}
.iq-flow-steps li:not(:last-child)::before {
    content: ''; position: absolute; right: -21px; top: calc(50% - 4px);
    width: 7px; height: 7px; border-top: 2px solid var(--iq-flow-connector);
    border-right: 2px solid var(--iq-flow-connector); transform: rotate(45deg);
}
@keyframes iq-flow-dots { to { background-position: 9px 0; } }
.iq-flow-step-head { grid-row: 1 / span 2; display: flex; flex-direction: column; align-items: center; gap: 2px; }
.iq-flow-icon {
    display: inline-flex; align-items: center; justify-content: center;
    width: 25px; height: 25px; flex: 0 0 25px;
    border-radius: 7px; background: var(--iq-step-icon-bg);
    font-size: 14px; line-height: 1;
}
.iq-flow-number { color: var(--iq-heading); font-size: 8px; font-weight: 800; letter-spacing: .01em; white-space: nowrap; }
.iq-flow-title { display: block; grid-column: 2; color: var(--iq-heading); font-size: 12px; font-weight: 700; margin: 0; }
.iq-flow-detail { grid-column: 2; color: var(--iq-text-secondary); font-size: 11px; line-height: 1.3; }
.iq-team-grid {
    display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px;
    margin: 12px 0 22px;
}
.iq-team-card {
    box-sizing: border-box; min-height: 278px; padding: 20px;
    border: 2px solid #A8C3E8; border-radius: 18px;
    background: #F7FAFF; box-shadow: 0 5px 18px rgba(26, 42, 74, 0.10);
}
.iq-team-initials {
    display: flex; align-items: center; justify-content: center;
    width: 46px; height: 46px; border-radius: 13px; margin-bottom: 11px;
    background: var(--iq-primary); color: #FFFFFF; font-size: 18px; font-weight: 800;
}
.iq-team-name { margin: 0 0 6px; color: var(--iq-heading); font-size: 18px; font-weight: 700; }
.iq-team-role { margin: 0 0 10px; color: #2455A5; font-size: 14px; font-weight: 700; line-height: 1.35; }
.iq-team-note { margin: 0; color: var(--iq-text-secondary); font-size: 13px; line-height: 1.45; }
@media (max-width: 900px) { .iq-team-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 560px) { .iq-team-grid { grid-template-columns: 1fr; } }
@media (max-width: 800px) {
    .iq-flow-steps { flex-direction: column; gap: 16px; }
    .iq-flow-steps li:not(:last-child)::after {
        right: auto; left: 50%; top: auto; bottom: -14px;
        width: 5px; height: 11px; transform: translateX(-50%);
        background: radial-gradient(circle, var(--iq-flow-connector) 2px, transparent 2.5px) 0 0 / 5px 9px repeat-y;
        animation-name: iq-flow-dots-vertical;
    }
    .iq-flow-steps li:not(:last-child)::before {
        right: auto; left: calc(50% - 4px); top: auto; bottom: -16px;
        transform: rotate(135deg);
    }
}
@keyframes iq-flow-dots-vertical { to { background-position: 0 9px; } }
@media (prefers-reduced-motion: reduce) {
    .iq-flow-steps li:not(:last-child)::after { animation: none; }
}
.iq-badge {
    display: inline-block; padding: 2px 10px; border-radius: 20px;
    font-size: 12px; font-weight: 600; white-space: nowrap;
}
.iq-sev-high { background: var(--iq-sev-high-bg); color: var(--iq-sev-high); }
.iq-sev-medium { background: var(--iq-sev-medium-bg); color: var(--iq-sev-medium); }
.iq-sev-low { background: var(--iq-sev-low-bg); color: var(--iq-sev-low); }
.iq-status-open { background: var(--iq-status-open-bg); color: var(--iq-status-open); }
.iq-status-escalate { background: var(--iq-status-escalate-bg); color: var(--iq-status-escalate); }
.iq-status-close { background: var(--iq-status-close-bg); color: var(--iq-status-close); }
.iq-status-info { background: var(--iq-status-info-bg); color: var(--iq-status-info); }
.iq-hero-badge { background: var(--iq-primary); color: white; padding: 1px 7px; border-radius: 5px; font-size: 11px; margin-left: 6px; }
.iq-nav-title { font-size: 17px; font-weight: 700; color: var(--iq-heading); margin: 0 0 2px 0; line-height: 1.3; }
.iq-nav-detail {
    color: var(--iq-text-secondary); font-size: 13px; line-height: 1.45;
    margin: 0; padding-left: 10px; border-left: 2px dotted var(--iq-card-border);
}
.iq-nav-icon {
    display: inline-flex; align-items: center; justify-content: center;
    width: 28px; height: 28px; margin-right: 8px; vertical-align: middle;
    background: #EAF2FF; border: 1px solid #B9D0F5; border-radius: 8px;
    font-size: 17px;
}
/* Keep the shared Copilot on the page, independent of the collapsible
   Streamlit sidebar. The closed launcher is deliberately small; the open
   panel stays inside the viewport and scrolls its own conversation. */
[class*="st-key-iq_floating_copilot_"] {
    position: fixed !important; right: 22px; bottom: 20px; z-index: 100002;
    box-sizing: border-box; margin: 0 !important;
}
.st-key-iq_floating_copilot_closed {
    width: auto; max-width: calc(100vw - 32px);
    border-radius: 999px; box-shadow: 0 9px 28px rgba(13, 34, 73, .28);
}
.st-key-iq_floating_copilot_closed button {
    background: linear-gradient(120deg, #2E63BF, #087E74) !important;
    border: 1.5px solid #7BE0D3 !important;
    border-radius: 999px !important; min-height: 48px;
    padding: 9px 19px !important; color: #FFFFFF !important;
    font-weight: 750 !important;
    animation: iq-launcher-attention 4s ease-in-out infinite;
}
.st-key-iq_floating_copilot_closed button * { color: #FFFFFF !important; }
.st-key-iq_floating_copilot_closed button:hover {
    background: linear-gradient(120deg, #2456AA, #056D65) !important;
    animation-play-state: paused; transform: translateY(-1px);
}
@keyframes iq-launcher-attention {
    0%, 70%, 100% { box-shadow: 0 5px 15px rgba(13, 84, 113, .23); }
    82% { box-shadow: 0 0 0 7px rgba(40, 179, 165, .17), 0 9px 25px rgba(13, 84, 113, .30); }
}
.st-key-iq_floating_copilot_open {
    top: 68px; bottom: auto;
    width: min(390px, calc(100vw - 32px));
    min-width: min(320px, calc(100vw - 24px)); min-height: 250px;
    max-width: calc(100vw - 24px);
    max-height: min(680px, calc(100vh - 82px)); overflow-y: auto;
    resize: both; scrollbar-width: thin;
    overscroll-behavior: contain; padding: 10px 12px;
    border: 1.5px solid #91B8F0; border-radius: 18px;
    background: var(--iq-card-bg); color: var(--iq-heading);
    box-shadow: 0 16px 45px rgba(13, 34, 73, .30);
}
.st-key-iq_floating_copilot_open:has(.iq-chat-expanded) {
    width: min(650px, calc(100vw - 32px));
    max-height: calc(100vh - 82px);
}
.st-key-iq_floating_chat_history {
    height: auto !important;
    min-height: 105px; max-height: clamp(180px, calc(100vh - 450px), 340px) !important;
    flex: 0 0 auto !important;
    overflow-y: auto; scrollbar-width: thin;
    margin: 3px 0 !important; padding: 8px !important;
    border: 1.5px solid #91B8F0; border-radius: 12px;
    background: #F3F7FF;
}
.st-key-iq_floating_copilot_open:has(.iq-chat-expanded) .st-key-iq_floating_chat_history {
    height: auto !important;
    max-height: clamp(210px, calc(100vh - 420px), 460px) !important;
}
.st-key-iq_floating_chat_history > * { flex: 0 0 auto !important; }
.iq-chat-message {
    width: fit-content; max-width: 93%; margin: 8px 0 12px;
    padding: 9px 11px; border: 1px solid var(--iq-card-border);
    border-radius: 13px; background: var(--iq-card-bg);
    overflow-wrap: anywhere;
}
.iq-chat-message.iq-chat-user {
    margin-left: auto; background: #E5EFFD; border-color: #A7C5EF;
}
.iq-chat-message.iq-chat-assistant { margin-right: auto; }
.iq-chat-message.iq-chat-assistant[data-iq-latest-answer="true"] {
    border-color: #3AAFA2; box-shadow: 0 0 0 2px rgba(58, 175, 162, .16);
}
.iq-chat-speaker {
    display: block; margin-bottom: 4px; font-size: 11px;
    font-weight: 800; color: var(--iq-text-secondary);
}
.st-key-iq_floating_copilot_open [data-testid="stFormSubmitButton"] button {
    background: linear-gradient(120deg, #087E74, #0A9A89) !important;
    border: 1.5px solid #51C8B8 !important;
    color: #FFFFFF !important; min-width: 0 !important;
    padding: 0 6px !important;
}
.st-key-iq_floating_copilot_open [data-testid="stFormSubmitButton"] button * {
    color: #FFFFFF !important;
}
.st-key-iq_floating_copilot_open [data-testid="stFormSubmitButton"] button:disabled {
    background: #354661 !important; border-color: #647895 !important;
    opacity: 1 !important;
}
.st-key-iq_floating_copilot_open [data-testid="stForm"] {
    position: sticky; bottom: 0; z-index: 2;
    background: var(--iq-card-bg);
}
[class*="st-key-inv_"] button {
    background: linear-gradient(120deg, #087E74, #0A9A89) !important;
    border: 1.5px solid #51C8B8 !important;
    color: #FFFFFF !important;
    min-height: 38px; padding: 0 8px !important;
    font-size: 13px; font-weight: 750; white-space: nowrap;
    box-shadow: 0 2px 7px rgba(8, 126, 116, .18);
}
[class*="st-key-inv_"] button * { color: #FFFFFF !important; }
.iq-queue-header { white-space: nowrap; }
.iq-queue-rule {
    display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2;
    overflow: hidden; overflow-wrap: anywhere; line-height: 1.4;
}
[class*="st-key-inv_"] button:hover {
    background: linear-gradient(120deg, #05695F, #087E74) !important;
}
[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(120deg, #087E74, #0A9A89) !important;
    border-color: #51C8B8 !important; color: #FFFFFF !important;
}
.st-key-iq_floating_header [data-testid="stHorizontalBlock"] {
    align-items: center !important; gap: 6px !important;
}
.st-key-iq_floating_header { cursor: grab; user-select: none; touch-action: none; }
.st-key-iq_floating_header:active { cursor: grabbing; }
.st-key-iq_floating_header button { cursor: pointer; }
.st-key-iq_floating_copilot_open [data-testid="stHorizontalBlock"]:has(.iq-floating-title) {
    align-items: center !important; gap: 6px !important;
}
.st-key-iq_floating_copilot_open [data-testid="stHorizontalBlock"]:has(.iq-floating-title) [data-testid="stColumn"]:first-child {
    flex: 1 1 auto !important; min-width: 0 !important;
}
.st-key-iq_floating_copilot_open [data-testid="stHorizontalBlock"]:has(.iq-floating-title) [data-testid="stColumn"]:nth-child(2),
.st-key-iq_floating_copilot_open [data-testid="stHorizontalBlock"]:has(.iq-floating-title) [data-testid="stColumn"]:nth-child(3) {
    flex: 0 0 42px !important; width: 42px !important; min-width: 42px !important;
}
.st-key-iq_floating_header [data-testid="stColumn"]:first-child {
    flex: 1 1 auto !important; min-width: 0 !important;
}
.st-key-iq_floating_header [data-testid="stColumn"]:nth-child(2),
.st-key-iq_floating_header [data-testid="stColumn"]:nth-child(3) {
    flex: 0 0 42px !important; width: 42px !important; min-width: 42px !important;
}
.st-key-iq_floating_header [data-testid="stButton"] button {
    width: 42px !important; min-width: 42px !important;
    height: 42px !important; min-height: 42px !important; padding: 0 !important;
}
.iq-floating-title {
    display: flex; align-items: center; min-height: 42px;
    color: var(--iq-heading); font-size: 16px; font-weight: 800; line-height: 1.2;
}
.iq-floating-context { color: var(--iq-text-secondary); font-size: 12px; line-height: 1.25; }
.iq-selected-case, .iq-workspace-case-badge strong {
    display: inline-block; padding: 2px 8px; border-radius: 8px;
    background: #2058B2; border: 1px solid #7FB5FF;
    color: #FFFFFF; font-weight: 800; letter-spacing: .03em;
}
.iq-workspace-case-badge { margin: 4px 0 10px; color: var(--iq-text-secondary); font-size: 14px; }
.iq-suggestion-preview {
    margin: 2px 0 6px; padding: 6px 9px; border-radius: 8px;
    border: 1px solid var(--iq-card-border); color: var(--iq-heading);
    background: var(--iq-card-bg); font-size: 12px; line-height: 1.4;
    overflow-wrap: anywhere;
}
.st-key-iq_floating_copilot_open [data-testid="stSelectbox"] { margin-bottom: 0 !important; }
.st-key-iq_floating_copilot_open [data-testid="stButton"] button {
    border: 1.5px solid #91B8F0 !important;
}
.st-key-iq_floating_copilot_open button:hover { border-color: #3FA6D5 !important; }
[role="option"] { white-space: normal !important; overflow-wrap: anywhere; }
@media (max-width: 600px) {
    [class*="st-key-iq_floating_copilot_"] { right: 12px; bottom: 12px; }
    .st-key-iq_floating_copilot_open {
        top: 68px; bottom: auto;
        width: calc(100vw - 24px); max-height: calc(100vh - 80px);
        resize: none;
    }
    .st-key-iq_floating_chat_history {
        height: auto !important;
        max-height: clamp(140px, calc(100vh - 430px), 280px) !important;
        min-height: 100px;
    }
    .st-key-iq_floating_copilot_open [data-testid="stHorizontalBlock"] {
        flex-direction: row !important; flex-wrap: nowrap !important;
    }
    .st-key-iq_floating_copilot_open [data-testid="stHorizontalBlock"] [data-testid="stColumn"] {
        min-width: 0 !important;
    }
    .st-key-iq_floating_copilot_open [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:first-child {
        flex: 1 1 auto !important;
    }
    .st-key-iq_floating_copilot_open [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:last-child {
        flex: 0 0 70px !important;
    }
    .st-key-iq_floating_copilot_open .st-key-iq_floating_header [data-testid="stColumn"]:nth-child(2),
    .st-key-iq_floating_copilot_open .st-key-iq_floating_header [data-testid="stColumn"]:nth-child(3) {
        flex: 0 0 42px !important; width: 42px !important; min-width: 42px !important;
    }
    .st-key-iq_floating_copilot_open [data-testid="stFormSubmitButton"] button {
        min-width: 0 !important; padding: 0 6px !important;
    }
}
@media (prefers-reduced-motion: reduce) {
    .st-key-iq_floating_copilot_closed button { animation: none !important; }
}
.iq-kpi-label { color: var(--iq-text-secondary); font-size: 12px; margin-bottom: 1px; }
.iq-kpi-value { font-size: 23px; font-weight: 700; line-height: 1.15; color: var(--iq-heading); }
.iq-kpi-region { container-type: inline-size; width: 100%; }
.iq-kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 9px; margin: 4px 0 7px; }
.iq-card.iq-kpi-card {
    --iq-kpi-accent: #2E63BF;
    position: relative; min-height: 82px; box-sizing: border-box;
    padding: 9px 32px 9px 46px; border: 2px solid transparent !important;
    background:
        linear-gradient(125deg, color-mix(in srgb, var(--iq-kpi-accent) 11%, var(--iq-card-bg)), var(--iq-card-bg) 76%) padding-box,
        linear-gradient(135deg, var(--iq-kpi-accent), #B9D0EC 55%, var(--iq-kpi-accent)) border-box !important;
    box-shadow: 0 3px 10px rgba(30, 66, 118, .10);
}
.iq-kpi-top { position: absolute; inset: 9px 9px auto 9px; display: flex; align-items: flex-start; justify-content: space-between; }
.iq-kpi-detail { color: var(--iq-text-secondary); font-size: 11px; line-height: 1.25; margin-top: 2px; }
.iq-kpi-help { color: var(--iq-primary); display: inline-flex; align-items: center; justify-content: center; width: 18px; height: 18px; }
.iq-kpi-info-icon { display: block; width: 18px; height: 18px; }
@container (min-width: 800px) and (max-width: 1199px) {
    .iq-kpi-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@container (min-width: 1200px) {
    .iq-kpi-grid { grid-template-columns: repeat(6, minmax(0, 1fr)); }
}
@media (max-width: 799px) { .iq-kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; } }
@media (max-width: 350px) { .iq-kpi-grid { grid-template-columns: 1fr; } }
/* A compact tinted surface plus a full gradient edge keeps each status
   distinct without six oversized white blocks. */
.iq-kpi-blue { --iq-kpi-accent: #2E63BF !important; }
.iq-kpi-amber { --iq-kpi-accent: #B47A08 !important; }
.iq-kpi-red { --iq-kpi-accent: #BD3535 !important; }
.iq-kpi-green { --iq-kpi-accent: #27844E !important; }
.iq-kpi-icon {
    display: inline-flex; align-items: center; justify-content: center;
    width: 26px; height: 26px; border-radius: 8px; font-size: 14px;
    margin: 0;
}
.iq-kpi-blue .iq-kpi-icon { background: var(--iq-status-info-bg); }
.iq-flashlight-svg { color: #2459AB; display: block; }
.iq-kpi-amber .iq-kpi-icon { background: var(--iq-sev-medium-bg); }
.iq-kpi-red .iq-kpi-icon { background: var(--iq-sev-high-bg); }
.iq-kpi-green .iq-kpi-icon { background: var(--iq-sev-low-bg); }
.st-key-human_decision_panel {
    border: 2px solid var(--iq-sev-low) !important;
    background: rgba(39,132,78,0.07);
}
.iq-escalation-card {
    border: 2px solid var(--iq-sev-high); border-radius: 10px; padding: 14px 18px;
    margin-bottom: 10px; background: rgba(176,42,42,0.06);
}

/* ------------------------------------------------------------------
   Motion — real page-load animation, not just static CSS. .iq-rise
   fades+slides an element up on mount; add .iq-stagger-N (1-8) for a
   staggered reveal across a row of cards/KPIs so they cascade in
   rather than all popping at once. Respects reduced-motion.
   ------------------------------------------------------------------ */
@keyframes iq-rise-in {
    from { opacity: 0; transform: translateY(14px); }
    to { opacity: 1; transform: translateY(0); }
}
.iq-rise {
    animation: iq-rise-in 0.55s cubic-bezier(0.16, 1, 0.3, 1) both;
}
.iq-stagger-1 { animation-delay: 0.05s; }
.iq-stagger-2 { animation-delay: 0.12s; }
.iq-stagger-3 { animation-delay: 0.19s; }
.iq-stagger-4 { animation-delay: 0.26s; }
.iq-stagger-5 { animation-delay: 0.33s; }
.iq-stagger-6 { animation-delay: 0.40s; }
.iq-stagger-7 { animation-delay: 0.47s; }
.iq-stagger-8 { animation-delay: 0.54s; }

.st-key-hero_cta { margin-top: -20px; margin-bottom: 10px; position: relative; z-index: 3; }
.st-key-hero_cta [data-testid="stPageLink-NavLink"] {
    background: #2E63BF !important; border-radius: 999px !important;
    padding: 10px 20px !important; justify-content: center !important;
    box-shadow: 0 6px 18px rgba(46,99,191,0.45); border: none !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.st-key-hero_cta [data-testid="stPageLink-NavLink"]:hover {
    transform: translateY(-2px); box-shadow: 0 10px 26px rgba(46,99,191,0.6);
}
.st-key-hero_cta [data-testid="stPageLink-NavLink"] * {
    color: white !important; font-weight: 700 !important; font-size: 15px !important;
}

.iq-card, [class*="st-key-iq_bordered_"] {
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

/* Keep the home navigation informative without leaving a large blank panel. */
[class*="st-key-iq_bordered_nav_"] {
    min-height: 164px;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
}
[class*="st-key-iq_bordered_nav_"] > [data-testid="stElementContainer"]:last-child {
    margin-top: auto;
}

/* Mobile responsiveness for the Case Queue table — reported: "the tiles
   get misaligned, and the text gets misaligned. If the alert type is
   quite big, then it also gets misaligned." st.columns() DOES stack
   vertically below Streamlit's own ~640px breakpoint on its own, but
   that's exactly the problem: a wide header row (Case / Customer / Alert
   Type / Severity / Status / Rule(s)) and each data row both collapse
   into one long vertical list with nothing connecting a value to what it
   means once the column grid that lined them up is gone. Rather than
   fight Streamlit's own column-stacking (fragile — it's not designed to
   be overridden), each cell gets a label prefix that's invisible on
   desktop (where the header row already provides that context) and
   appears only once stacked, and the now-redundant header row itself
   hides at that same breakpoint. */
.iq-mobile-label { display: none; font-weight: 600; color: var(--iq-text-secondary); }
@media (max-width: 640px) {
    .iq-mobile-label { display: inline; }
    .iq-queue-rule { display: inline; overflow: visible; }
    [data-testid="stHorizontalBlock"]:has(.iq-queue-header) { display: none; }
    [data-testid="stHorizontalBlock"]:has(.iq-queue-row) {
        border-bottom: 1px solid var(--iq-card-border); padding-bottom: 8px; margin-bottom: 8px;
    }
}
[class*="st-key-iq_bordered_nav_"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 24px rgba(26,42,74,0.14);
}

@media (prefers-reduced-motion: reduce) {
    .iq-rise, [class*="st-key-iq_bordered_nav_"]:hover {
        animation: none !important; transition: none !important; transform: none !important;
    }
}
</style>
"""

_DARK_OVERRIDE_CSS = """
<style>
:root {
    --iq-card-bg: #1B2536;
    --iq-card-border: #2E3B52;
    --iq-text-secondary: #9FB0C9;
    --iq-heading: #E8EDF7;
}
.st-key-iq_floating_chat_history { background: #142033 !important; border-color: #648AC4 !important; }
.iq-chat-message.iq-chat-user { background: #254267 !important; border-color: #648AC4 !important; }
.st-key-iq_floating_copilot_open { border-color: #79A9EA !important; }
.st-key-iq_floating_copilot_open [data-testid="stButton"] button,
.st-key-iq_floating_copilot_open [data-testid="stSelectbox"] .react-aria-ComboBox > div {
    border-color: #79A9EA !important;
}
.st-key-iq_floating_copilot_open [data-testid="stFormSubmitButton"] button {
    background: linear-gradient(120deg, #087E74, #0A9A89) !important;
    border-color: #66DDCD !important;
}
[class*="st-key-inv_"] button {
    background: linear-gradient(120deg, #087E74, #0A9A89) !important;
    border-color: #66DDCD !important; color: #FFFFFF !important;
}
.iq-team-card {
    background: #1D2D47 !important; border-color: #729BDD !important;
    box-shadow: 0 0 0 1px rgba(130, 170, 230, 0.22), 0 9px 24px rgba(0, 0, 0, 0.18);
}
.iq-banner-icon { background: #EAF2FF !important; border-color: #B9D0F5 !important; }
.iq-nav-icon { background: #EAF2FF !important; border-color: #B9D0F5 !important; }
[data-testid="stSidebarNavLink"] [data-testid="stIconEmoji"] {
    background: #DCEAFF !important; border-color: #8EB1E3 !important;
}
.iq-team-role { color: #A9C9FF !important; }
.iq-brand-slogan {
    background: #243B5A !important; border-left-color: #96C7FF !important;
    color: #E8F2FF !important;
}
.iq-card {
    background: #1D2D47 !important; border-color: #648AC4 !important;
}
.iq-flow {
    --iq-flow-connector: #A7C8FF;
    background: linear-gradient(135deg, #1B2A43, #1D3550) !important;
    border-color: #78A1DD !important;
}
.iq-flow-steps li {
    --iq-step-border: #76A8ED; --iq-step-bg: #233C62; --iq-step-icon-bg: #315584;
    background: var(--iq-step-bg) !important; border-color: var(--iq-step-border) !important;
}
.iq-flow-steps li:nth-child(4n+2) {
    --iq-step-border: #BE99ED; --iq-step-bg: #3A3056; --iq-step-icon-bg: #59437C;
}
.iq-flow-steps li:nth-child(4n+3) {
    --iq-step-border: #78D1BA; --iq-step-bg: #214C49; --iq-step-icon-bg: #2E6A60;
}
.iq-flow-steps li:nth-child(4n+4) {
    --iq-step-border: #E6B975; --iq-step-bg: #50432E; --iq-step-icon-bg: #75603B;
}
.iq-flow-icon { background: var(--iq-step-icon-bg) !important; }
.iq-kpi-icon {
    background: #2A4267 !important; box-shadow: inset 0 0 0 1px #6C91C6;
}
.iq-flashlight-svg { color: #C5DCFF !important; }
.iq-kpi-help { color: #A9C9FF !important; }
/* Streamlit's own chrome — these are its documented-by-convention
   data-testid hooks (stable across 1.x releases, widely relied on by the
   Streamlit community for exactly this kind of app-level theming) rather
   than internal class names, which do change between versions. */
[data-testid="stAppViewContainer"], [data-testid="stHeader"],
[data-testid="stBottomBlockContainer"], [data-testid="stMain"] {
    background: #0F1826 !important;
}
/* Both the main view and sidebar have light-mode gradients. Replacing only
   background-color leaves those images visible behind dark-mode text. */
[data-testid="stSidebar"] { background: #16213A !important; }
[data-testid="stAppViewContainer"] *, [data-testid="stSidebar"] *,
[data-testid="stHeader"] * {
    color: #E8EDF7 !important;
}
[data-testid="stCaptionContainer"], .iq-kpi-label, small, caption { color: #9FB0C9 !important; }
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {
    background-color: #1B2536 !important; color: #E8EDF7 !important;
    border-color: #2E3B52 !important;
}
/* st.selectbox / st.multiselect in this Streamlit version render as React
   Aria Components (.react-aria-ComboBox), not the older data-baseweb
   markup the first version of this rule assumed — confirmed by
   inspecting the live DOM, not guessed. That markup has no data-testid
   or data-baseweb of its own on the actual field box, so it's targeted
   via the stable ancestor + a direct-child combinator instead. */
[data-testid="stSelectbox"] .react-aria-ComboBox > div,
[data-testid="stMultiSelect"] .react-aria-ComboBox > div {
    background-color: #1B2536 !important; border-color: #2E3B52 !important;
}
[data-testid="stSelectbox"] input, [data-testid="stMultiSelect"] input {
    color: #E8EDF7 !important;
}
/* The dropdown popover (the option list shown after clicking in) portals
   straight to <body>, entirely outside stAppViewContainer — confirmed by
   walking the live DOM up from an open dropdown — so none of the rules
   above reach it no matter how they're scoped. stSelectboxVirtualDropdown
   is a real, stable Streamlit data-testid; [role="listbox"]/[role="option"]
   are the standard ARIA roles the same popover exposes, used as a second
   hook since Streamlit doesn't expose an equivalent testid for every
   nested piece. */
[data-testid="stSelectboxVirtualDropdown"], [role="listbox"] {
    background-color: #1B2536 !important;
}
[role="option"] {
    background-color: #1B2536 !important; color: #E8EDF7 !important;
}
/* The rule above sets the TYPED text color but never touched the
   placeholder — e.g. Case Queue's "Search customer name" field — which
   kept the browser's own default placeholder gray, unreadable against
   the now-dark input background. */
[data-testid="stTextInput"] input::placeholder, [data-testid="stTextArea"] textarea::placeholder {
    color: #6E85A8 !important; opacity: 1 !important;
}
/* Every bordered st.container(border=True) — findings cards and the
   floating Copilot history, the nav cards on
   Home, any other bordered container — kept its own light background in
   dark mode, because nothing here ever gave it one. Meanwhile the
   blanket "* { color: ... !important }" above forces the text INSIDE it
   to light gray regardless of that background — light text on a
   still-light box, unreadable. Same bug shape as the badges and
   backtick-code fixes elsewhere in this file, different component. */
[class*="st-key-iq_bordered_"], .st-key-human_decision_panel,
[data-testid="stChatMessage"],
[data-testid="stChatInput"], [data-testid="stChatInput"] textarea {
    background-color: #1D2D47 !important; border-color: #648AC4 !important;
}
[class*="st-key-iq_bordered_"], .st-key-human_decision_panel {
    border-width: 1.5px !important; border-style: solid !important;
    box-shadow: 0 0 0 1px rgba(105, 149, 212, 0.14) !important;
}
/* st.code()'s <pre> wrapper keeps its own light background even though
   the inline <code> rule further below already darkens the element
   nested inside it — the citation blocks under each finding
   (st.code(", ".join(txn_ids))) render as light padding around dark
   text, not fully dark. */
[data-testid="stCode"] pre {
    background-color: #1B2536 !important;
}
/* st.json() (the "Raw evidence passed to the model" expander) renders via
   the react-json-view library, which keeps its own light background
   regardless of app theme — same fix shape again. */
[data-testid="stJson"] .react-json-view {
    background-color: #1B2536 !important;
}
/* Streamlit expander summaries keep their light tint unless the interactive
   summary itself is themed; light text then disappears in dark mode. */
[data-testid="stExpander"] summary {
    background-color: #1D2D47 !important; border-color: #648AC4 !important;
}
[data-testid="stDataFrame"], [data-testid="stTable"] { filter: invert(0.92) hue-rotate(180deg); }
hr, [data-testid="stDivider"] { border-color: #2E3B52 !important; }
button[kind="secondary"] { background-color: #1B2536 !important; border-color: #2E3B52 !important; }
/* The blanket "* { color: ... !important }" above would otherwise clobber
   every badge's own red/amber/green text with light gray, making e.g. the
   High-severity or Escalated pill unreadable (light text on a light tint).
   Two classes beats one attribute selector on specificity, so these win
   regardless of source order even though both sides use !important. */
.iq-badge.iq-sev-high, .iq-badge.iq-status-escalate { color: var(--iq-sev-high) !important; }
.iq-badge.iq-sev-medium, .iq-badge.iq-status-open { color: var(--iq-sev-medium) !important; }
.iq-badge.iq-sev-low, .iq-badge.iq-status-close { color: var(--iq-sev-low) !important; }
.iq-badge.iq-status-info { color: var(--iq-status-info) !important; }
.iq-hero-badge.iq-hero-badge { color: white !important; }
/* st.markdown backtick-code spans (e.g. `CASE-001`) keep their own light
   background regardless of app theme — recolor the whole span, not just
   inherit the blanket light text color, or the text disappears (light
   text on a near-white background). */
code { background-color: #1B2536 !important; color: #7CC5FF !important; }
.iq-banner.iq-banner, .iq-banner.iq-banner * { color: white !important; }
.iq-banner p.iq-banner p { color: var(--iq-navy-light) !important; }
</style>
"""

_SEVERITY_CLASS = {"High": "iq-sev-high", "Medium": "iq-sev-medium", "Low": "iq-sev-low"}
_STATUS_CLASS = {
    "Open": "iq-status-open", "Escalated": "iq-status-escalate", "Closed": "iq-status-close",
    "Source closed — unverified": "iq-status-open",
    "Info Requested": "iq-status-info", "Closed (Compliance)": "iq-status-close",
    "Returned to Investigator": "iq-status-info", "Referred (Compliance)": "iq-status-escalate",
}


def inject_global_styles():
    """Idempotent within a page render — safe to call once per page (done
    automatically inside require_login()). Streamlit dedupes identical
    <style> blocks across reruns on its own. Emits the dark override block
    second, after the base :root declaration, so its redeclared custom
    properties win by CSS source order — no class-toggling needed.

    Reads a persistent session key. Streamlit can drop a widget's own key
    during multipage navigation, so the sidebar toggle copies its value
    into this non-widget key in an on_change callback before rerendering."""
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)
    if st.session_state.get("iq_dark_mode"):
        st.markdown(_DARK_OVERRIDE_CSS, unsafe_allow_html=True)


def _remember_theme_choice():
    st.session_state["iq_dark_mode"] = bool(st.session_state["dark_mode_toggle"])


def page_banner(icon: str, title: str, subtitle: str):
    """Replaces the six copies of the same hand-written .iq-banner markup
    that used to live at the top of every page."""
    st.markdown(
        f'<div class="iq-banner"><h1><span class="iq-banner-icon" aria-hidden="true">{icon}</span>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )
    st.caption("Sample environment · all customer and transaction data is fictional")


def page_flow(purpose: str, steps: list[tuple[str, str]], note: str = ""):
    """Visible, accessible explanation of a screen's actual workflow."""
    if not steps:
        raise ValueError("A page flow needs at least one step")
    icons = ("🔎", "📋", "✅", "🛡️")
    items = "".join(
        '<li><span class="iq-flow-step-head">'
        f'<span class="iq-flow-icon" aria-hidden="true">{icons[(index - 1) % len(icons)]}</span>'
        f'<span class="iq-flow-number">STEP {index:02d}</span></span>'
        f'<span class="iq-flow-title">{escape(title)}</span>'
        f'<span class="iq-flow-detail">{escape(detail)}</span></li>'
        for index, (title, detail) in enumerate(steps, 1)
    )
    note_html = f'<div class="iq-flow-note">{escape(note)}</div>' if note else ""
    st.markdown(
        '<section class="iq-flow" aria-label="How this page works">'
        '<div class="iq-flow-heading">How this page works</div>'
        f'<div class="iq-flow-purpose"><strong>Purpose:</strong> {escape(purpose)}</div>'
        f'<ol class="iq-flow-steps">{items}</ol>{note_html}</section>',
        unsafe_allow_html=True,
    )


def severity_badge(severity: str) -> str:
    """Returns an HTML pill for a severity value — pass through st.markdown
    with unsafe_allow_html=True. Falls back to plain text for an unknown
    value rather than an empty/broken badge."""
    cls = _SEVERITY_CLASS.get(severity)
    safe = escape(str(severity))
    return f'<span class="iq-badge {cls}">{safe}</span>' if cls else safe


def status_badge(status: str) -> str:
    cls = _STATUS_CLASS.get(status)
    safe = escape(str(status))
    return f'<span class="iq-badge {cls}">{safe}</span>' if cls else safe


def _sidebar_glossary() -> None:
    """Short, consistent definitions available from every workspace page."""
    with st.expander("ℹ️ Help & definitions"):
        st.markdown(
            "**Alert:** a stored activity pattern flagged for human review, not proof of crime.\n\n"
            "**Severity:** the source data's priority label; it does not determine the case outcome.\n\n"
            "**Status:** the latest recorded workflow state, including a human action when one exists.\n\n"
            "**KYC:** know-your-customer information. A dataset status or generated sample is not an "
            "independently verified identity file.\n\n"
            "**Evidence chunk:** a smaller indexed passage linked to its stored source record. "
            "A citation is a pointer, not proof that the source is authentic.\n\n"
            "**RAG:** retrieval-augmented generation—retrieve relevant passages before using them "
            "to support a draft or answer. This app uses keyword search, not vector embeddings.\n\n"
            "**BM25:** a keyword-match ranking used to order search results; not a probability, "
            "risk score or AI confidence.\n\n"
            "**Human decision:** an investigator's recorded action and written reason. "
            "The Copilot cannot submit it or file a regulatory report."
        )


def require_login(allow_guest: bool = False):
    """Call near the top of every page. Shows a one-time name+role form if
    the session doesn't have an identity yet; otherwise renders the small
    sidebar identity badge and returns (name, role) immediately. Public
    orientation screens may instead show the guest sidebar."""
    if "iq_dark_mode" not in st.session_state:
        st.session_state["iq_dark_mode"] = bool(st.session_state.get("dark_mode_toggle", False))
    # Widget keys may be reset when a Streamlit page changes. Restore the
    # sidebar switch from the persistent value before the widget is created.
    st.session_state["dark_mode_toggle"] = st.session_state["iq_dark_mode"]
    inject_global_styles()
    dark = bool(st.session_state["iq_dark_mode"])
    st.logo(LOGO_FULL_DARK if dark else LOGO_FULL_LIGHT, icon_image=LOGO_ICON, size="large")

    if "user_name" not in st.session_state or "user_role" not in st.session_state:
        if allow_guest:
            with st.sidebar:
                st.markdown(f'<div class="iq-brand-slogan">{escape(PROJECT_SLOGAN)}</div>', unsafe_allow_html=True)
                st.caption(f"{GROUP_LABEL} · {COURSE_LABEL}")
                st.caption("Guest view · fictional customer and transaction data")
                st.toggle("🌙 Dark mode", key="dark_mode_toggle",
                          on_change=_remember_theme_choice,
                          help="Switch the display theme for this browser session; it does not change case data.")
                _sidebar_glossary()
            return None, None
        st.write("")
        lcol1, lcol2, lcol3 = st.columns([1, 2, 1])
        with lcol2:
            st.image(LOGO_FULL_DARK if dark else LOGO_FULL_LIGHT, use_container_width=True)
            st.write("")
            with st.container(border=True, key="iq_bordered_login"):
                st.markdown("#### Enter your workspace")
                st.caption(
                    "Choose a display name and role for attribution. This environment does not authenticate users."
                )
                name = st.text_input("Your name", help="Display name recorded beside decisions and audit events.")
                role = st.radio("Your role", ROLES, horizontal=True,
                                help="A workflow label; this environment does not enforce role-based access.")
                if st.button("Continue", type="primary", use_container_width=True,
                             help="Open the workspace with this display name and role."):
                    if not name.strip():
                        st.error("Please enter your name.")
                    else:
                        st.session_state["user_name"] = name.strip()
                        st.session_state["user_role"] = role
                        st.rerun()
        st.stop()

    with st.sidebar:
        st.markdown(f'<div class="iq-brand-slogan">{escape(PROJECT_SLOGAN)}</div>', unsafe_allow_html=True)
        st.caption(f"{GROUP_LABEL} · {COURSE_LABEL}")
        st.markdown(f"**👤 {st.session_state['user_name']}**")
        st.caption(f"Role: {st.session_state['user_role']}")
        # key= alone is enough — session_state["dark_mode_toggle"] persists
        # for the whole session (every page reads it, see
        # inject_global_styles() above), the same way user_name does.
        st.toggle("🌙 Dark mode", key="dark_mode_toggle",
                  on_change=_remember_theme_choice,
                  help="Switch the display theme for this browser session; it does not change case data.")
        _sidebar_glossary()
        if st.button("Switch user", key="switch_user_btn",
                     help="Clear this display identity and choose another; saved decisions remain in the audit log."):
            del st.session_state["user_name"]
            del st.session_state["user_role"]
            st.session_state.pop("active_case_id", None)
            st.session_state.pop("selected_case_id", None)
            st.session_state.pop("iq_floating_copilot_open", None)
            st.rerun()

    return st.session_state["user_name"], st.session_state["user_role"]


def render_context_copilot(page: str, case_id: str | None = None,
                           chunk_id: str | None = None) -> None:
    """Floating Q&A shared across pages; history follows the selected case."""
    from agents.context_copilot import answer_context_question

    if not st.session_state.get("iq_floating_copilot_open", False):
        with st.container(key="iq_floating_copilot_closed"):
            if st.button("✦ Ask InvestigateIQ", key="floating_copilot_open",
                         help="Open the floating Copilot chat without leaving this page."):
                st.session_state["iq_floating_copilot_open"] = True
                st.rerun()
        return

    scope = case_id or f"page_{page.replace(' ', '_')}"
    history_key = (f"fictional_chat_{case_id}" if case_id and case_id.startswith("FIC-CASE-")
                   else f"chat_{case_id}" if case_id else f"context_chat_{scope}")
    with st.container(key="iq_floating_copilot_open"):
        with st.container(key="iq_floating_header"):
            title_col, expand_col, close_col = st.columns([5, 1, 1], vertical_alignment="center")
            with title_col:
                st.markdown('<div class="iq-floating-title" title="Drag this header to move the chat window">✦ InvestigateIQ Copilot</div>',
                            unsafe_allow_html=True)
            with expand_col:
                expanded = bool(st.session_state.get("iq_floating_copilot_expanded", False))
                if st.button("↙" if expanded else "⤢", key="floating_copilot_expand",
                             help="Make the conversation compact" if expanded else "Expand the conversation"):
                    st.session_state["iq_floating_copilot_expanded"] = not expanded
                    st.rerun()
            with close_col:
                if st.button("×", key="floating_copilot_close", help="Close the floating Copilot chat."):
                    st.session_state["iq_floating_copilot_open"] = False
                    st.rerun()
        # Streamlit rerenders the panel after each answer. Restore its position
        # and attach pointer dragging to the header, never to its controls.
        # This is supplementary to the keyboard-accessible expand/close buttons.
        st.html("""<script>
        (() => {
            const panel = document.querySelector('.st-key-iq_floating_copilot_open');
            const header = panel?.querySelector('.st-key-iq_floating_header');
            if (!panel || !header || header.dataset.iqDragReady) return;
            header.dataset.iqDragReady = 'true';
            const key = 'iq-copilot-position';
            const clamp = (value, max) => Math.max(8, Math.min(value, Math.max(8, max)));
            const place = (left, top) => {
                panel.style.left = clamp(left, innerWidth - panel.offsetWidth - 8) + 'px';
                panel.style.top = clamp(top, innerHeight - Math.min(panel.offsetHeight, 180)) + 'px';
                panel.style.right = 'auto';
                panel.style.bottom = 'auto';
            };
            const resetForMobile = () => {
                if (innerWidth > 600) return false;
                panel.style.left = '';
                panel.style.top = '';
                panel.style.right = '';
                panel.style.bottom = '';
                return true;
            };
            try {
                const saved = JSON.parse(sessionStorage.getItem(key) || 'null');
                if (!resetForMobile() && saved && Number.isFinite(saved.left) && Number.isFinite(saved.top))
                    place(saved.left, saved.top);
            } catch (_) { /* A corrupt preference must not hide the chat. */ }
            window.addEventListener('resize', () => {
                if (resetForMobile()) return;
                const rect = panel.getBoundingClientRect();
                if (rect.right > innerWidth || rect.bottom > innerHeight)
                    place(rect.left, rect.top);
            });
            let drag = null;
            header.addEventListener('pointerdown', event => {
                if (innerWidth <= 600 || event.button !== 0 || event.target.closest('button')) return;
                const rect = panel.getBoundingClientRect();
                drag = { x: event.clientX, y: event.clientY, left: rect.left, top: rect.top };
                event.preventDefault();
            });
            document.addEventListener('pointermove', event => {
                if (!drag) return;
                place(drag.left + event.clientX - drag.x, drag.top + event.clientY - drag.y);
            });
            document.addEventListener('pointerup', () => {
                if (!drag) return;
                drag = null;
                const rect = panel.getBoundingClientRect();
                sessionStorage.setItem(key, JSON.stringify({left: rect.left, top: rect.top}));
            });
        })();
        </script>""", unsafe_allow_javascript=True)
        if st.session_state.get("iq_floating_copilot_expanded", False):
            st.markdown('<span class="iq-chat-expanded" hidden></span>', unsafe_allow_html=True)
        st.markdown('<div class="iq-floating-context">' + escape(page) + ' · ' +
                    (f'<span class="iq-selected-case">Case {escape(case_id)}</span>'
                     if case_id else 'No case selected') + '</div>',
                    unsafe_allow_html=True)
        if "user_name" not in st.session_state:
            st.info("Enter your workspace with a display name to ask the Copilot.")
            return
        if case_id and page != "Investigation Workspace":
            if st.button("Open case workspace", key="open_case_copilot_global",
                         help="Open this selected case in the Investigation Workspace."):
                st.session_state["selected_case_id"] = case_id
                st.switch_page("pages/2_Investigation_Demo.py")
        elif not case_id and st.button("Choose a case", key="open_case_copilot_global",
                                       help="Choose a case from the Case Queue for case-specific questions."):
            st.switch_page("pages/0_Case_Queue.py")
        if chunk_id:
            st.caption(f"Selected passage: {chunk_id}")
        suggestions = (
            ["Why was this alert triggered?",
             "Summarize this case in plain English.",
             "How many transactions were stored in the latest month?",
             "How much money came in and went out in the latest month?",
             "Show the transaction sequence and recorded counterparties.",
             "Which transactions need review, and why?",
             "What does the KYC status actually verify?",
             "What KYC and counterparty evidence is missing?",
             "Can you establish the source of funds?",
             "What evidence should we request next?",
             "What closure evidence is stored for this case?",
             "Request more information.",
             "Explain for compliance review.",
             "Can we conclude that these funds are lawful or unlawful?"]
            if case_id else
            ["What am I looking at?", "What can I do on this page?", "How do I choose a case?",
             "What information can the Copilot actually verify?"]
        )
        if chunk_id:
            suggestions.insert(0, "Explain this evidence passage in plain English.")
        if case_id and case_id.startswith("FIC-CASE-"):
            suggestions.extend([
                "Show me the transaction sequence: when, from whom, and to whom.",
                "How many transactions are stored in one month, and which need review?",
                "Why did this case trigger review?",
                "Can we say the funds are illegal?",
            ])
        elif case_id:
            suggestions.extend([
                "How many transactions were stored in one month, which need review, and is KYC verified?",
                "Show me the transaction sequence.",
                "What evidence supports the concern?",
                "What evidence might contradict this alert?",
                "What is missing?",
                "What should I do next?",
            ])
        if case_id and os.path.isfile(os.path.join(os.path.dirname(__file__), "data", "cached_reports",
                                               f"{case_id}.json")):
            suggestions.append("Why does the saved report have zero case passages while current evidence has chunks?")
        suggestions = list(dict.fromkeys(suggestions))
        history = st.session_state.get(history_key, [])
        def render_chat_turn(turn_index: int) -> None:
            turn = history[turn_index]
            role_class = "iq-chat-user" if turn["role"] == "user" else "iq-chat-assistant"
            speaker = "You" if turn["role"] == "user" else "Copilot"
            st.markdown(
                f'<div class="iq-chat-message {role_class}" '
                f'{"data-iq-latest-answer=\"true\" " if turn["role"] == "assistant" and turn_index == len(history) - 1 else ""}'
                f'title="{escape(turn["content"], quote=True) if turn["role"] == "user" else ""}">'
                f'<span class="iq-chat-speaker">'
                f'{speaker}</span>{plain_text_html(turn["content"])}</div>',
                unsafe_allow_html=True,
            )
            if turn["role"] == "assistant" and turn.get("source") == "live_model":
                st.caption("Live model draft — review every cited source before relying on it.")
                if turn.get("sources"):
                    st.caption("Citations: " + ", ".join(turn["sources"]))
                if turn.get("validator_notes"):
                    st.caption(f"{len(turn['validator_notes'])} citation or claim check(s) adjusted by the Grounding Validator.")
            if turn["role"] == "assistant" and turn.get("chunk_ids"):
                ids = turn["chunk_ids"]
                st.caption("Evidence used: " + ", ".join(ids[:3]) +
                           (f" · {len(ids) - 3} more cited passage(s)" if len(ids) > 3 else "") +
                           ". These are stored sources, not independent verification.")
                if st.button("Inspect the first cited source", key=f"context_source_{scope}_{turn_index}",
                             help="Open the exact stored source passage and its verification status."):
                    first_chunk = turn["chunk_ids"][0]
                    if case_id and case_id.startswith("FIC-CASE-"):
                        st.session_state["fictional_intake_case_id"] = case_id
                        st.session_state["fictional_intake_chunk_id"] = first_chunk
                        st.session_state["context_pending_rag_view"] = "Fictional Intake"
                    elif case_id:
                        st.session_state["rag_case_id"] = case_id
                        st.session_state["rag_case_doc_id"] = first_chunk.rsplit("-C", 1)[0]
                        st.session_state["rag_case_chunk_id"] = first_chunk
                        st.session_state["context_pending_rag_view"] = "Case records"
                    st.switch_page("pages/8_Evidence_RAG.py")

        if len(history) > 2:
            with st.expander(f"Earlier messages ({len(history) - 2})"):
                for turn_index in range(max(0, len(history) - 20), len(history) - 2):
                    render_chat_turn(turn_index)
        with st.container(border=False, key="iq_floating_chat_history"):
            if not history:
                st.caption("Ask a question about this page or the selected case. Answers appear here.")
            else:
                st.caption("Latest exchange · hover over your question to read it in full")
            for turn_index in range(max(0, len(history) - 2), len(history)):
                render_chat_turn(turn_index)
        if st.session_state.pop(f"iq_copilot_focus_{scope}", False):
            # Static script only: no case text or user input enters JavaScript.
            # Focus the newly rendered reply in both the inner transcript and
            # the floating panel, without moving the underlying page.
            st.html("""<script>
                window.setTimeout(() => {
                    const panel = document.querySelector('.st-key-iq_floating_copilot_open');
                    const transcript = panel?.querySelector('.st-key-iq_floating_chat_history');
                    const reply = transcript?.querySelector('[data-iq-latest-answer="true"]');
                    if (!panel || !transcript || !reply) return;
                    transcript.scrollTop += reply.getBoundingClientRect().top
                        - transcript.getBoundingClientRect().top - 8;
                    panel.scrollTop = 0;
                }, 100);
            </script>""", unsafe_allow_javascript=True)

        # A new picker key after each exchange returns it to the neutral
        # suggestion prompt without clearing the investigator's chat history.
        suggestion_key = f"context_copilot_suggestion_{scope}_{len(history)}"
        selected_suggestion = st.selectbox("Suggested questions", [""] + suggestions, key=suggestion_key,
                     format_func=lambda value: value or "Suggested questions (optional)",
                     label_visibility="collapsed",
                     help="Pick a question and press Send, or type a different question in the message field.")
        if selected_suggestion:
            st.markdown('<div class="iq-suggestion-preview" title="' +
                        escape(selected_suggestion, quote=True) +
                        '">Selected question: ' + escape(selected_suggestion) + '</div>',
                        unsafe_allow_html=True)
        with st.form("context_copilot_form", clear_on_submit=True):
            message_col, send_col = st.columns([4, 1], vertical_alignment="bottom")
            with message_col:
                question = st.text_input("Message", key="context_copilot_question",
                                         placeholder="Or type your own question..." if selected_suggestion else
                                                     ("Ask about this case..." if case_id else "Ask about this page..."),
                                         label_visibility="collapsed",
                                         help="Typed text takes priority over a selected suggestion. Answers use the selected case or passage; unsupported facts are not guessed.")
            with send_col:
                submitted = st.form_submit_button("Send", use_container_width=True,
                                                   help="Send your question about the selected case to the Copilot. Answers should be checked against cited records before making a decision.")
        question_to_send = question.strip() or selected_suggestion
        if submitted and question_to_send:
            try:
                answer = answer_context_question(question_to_send, page, case_id, chunk_id)
                # Preserve the former workspace's optional open-ended model
                # path, but only after a real case result has been prepared.
                # Bounded database answers stay deterministic and cited.
                if (case_id and not case_id.startswith("FIC-CASE-")
                        and answer.get("source") == "imported_case_database"
                        and answer["answer"].startswith("Ask about this selected case's stored")
                        and st.session_state.get(f"result_{case_id}")):
                    from agents import investigation_agent
                    if investigation_agent.GEMINI_API_KEY:
                        from agents.chat_agent import ask_question
                        result = st.session_state[f"result_{case_id}"]["result"]
                        try:
                            live = ask_question(case_id, question_to_send, history,
                                                result["context"], result["evidence"],
                                                result["guidance"])
                            cited_chunks = live.get("cited_case_chunk_ids", [])
                            answer = {
                                "answer": live["answer"],
                                "chunk_ids": cited_chunks,
                                "sources": live.get("cited_txn_ids", [])
                                           + live.get("cited_doc_ids", []) + cited_chunks,
                                "source": "live_model",
                                "validator_notes": live.get("validator_notes", []),
                            }
                        except Exception:
                            answer = {
                                "answer": "The live model did not return an answer. No AI conclusion was generated. "
                                          "You can still review stored evidence or ask a bounded case question.",
                                "chunk_ids": [], "sources": [], "source": "model_unavailable",
                            }
            except (OSError, ValueError, sqlite3.Error) as exc:
                answer = {"answer": f"I could not read the selected case safely: {type(exc).__name__}. "
                                    "Try again after checking the stored case data.",
                          "chunk_ids": [], "sources": [], "source": "read_error"}
            history = st.session_state.setdefault(history_key, [])
            history.extend(({"role": "user", "content": question_to_send},
                            {"role": "assistant", "content": answer["answer"],
                             "chunk_ids": answer.get("chunk_ids", []),
                             "sources": answer.get("sources", []), "source": answer.get("source"),
                             "validator_notes": answer.get("validator_notes", [])}))
            st.session_state[f"iq_copilot_focus_{scope}"] = True
            st.rerun()


def role_warning(current_role: str, expected_role: str):
    """Soft nudge, not a hard block — matches the mock-auth scope. A hard,
    convincing-looking access-control wall here would overstate what this
    prototype's auth actually is."""
    if current_role != expected_role:
        st.warning(
            f"Your selected role is **{current_role}**. This screen is normally used by **{expected_role}**. "
            "Access is not enforced here; any action will be attributed to your selected display identity."
        )
