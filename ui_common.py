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
import streamlit as st

ROLES = ["Investigator", "Team Lead", "Compliance Officer", "Admin"]

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
.iq-banner {
    background: linear-gradient(135deg, var(--iq-navy), #24365E);
    color: white; padding: 16px 24px; border-radius: 12px;
    box-shadow: 0 2px 10px rgba(26,42,74,0.18); margin-bottom: 4px;
}
.iq-banner h1 { margin: 0; font-size: 22px; }
.iq-banner p { margin: 4px 0 0 0; color: var(--iq-navy-light); font-size: 13px; }
.iq-card {
    background: var(--iq-card-bg); border: 1px solid var(--iq-card-border);
    border-radius: 12px; padding: 16px 20px;
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
.iq-kpi-label { color: var(--iq-text-secondary); font-size: 13px; margin-bottom: 2px; }
.iq-kpi-value { font-size: 26px; font-weight: 700; color: var(--iq-heading); }
.iq-decision-box {
    border: 2px solid var(--iq-sev-low); border-radius: 10px; padding: 16px;
    background: rgba(39,132,78,0.07);
}
.iq-escalation-card {
    border: 2px solid var(--iq-sev-high); border-radius: 10px; padding: 14px 18px;
    margin-bottom: 10px; background: rgba(176,42,42,0.06);
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
/* Streamlit's own chrome — these are its documented-by-convention
   data-testid hooks (stable across 1.x releases, widely relied on by the
   Streamlit community for exactly this kind of app-level theming) rather
   than internal class names, which do change between versions. */
[data-testid="stAppViewContainer"], [data-testid="stHeader"],
[data-testid="stBottomBlockContainer"], [data-testid="stMain"] {
    background-color: #0F1826 !important;
}
[data-testid="stSidebar"] { background-color: #16213A !important; }
[data-testid="stAppViewContainer"] *, [data-testid="stSidebar"] *,
[data-testid="stHeader"] * {
    color: #E8EDF7 !important;
}
[data-testid="stCaptionContainer"], .iq-kpi-label, small, caption { color: #9FB0C9 !important; }
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background-color: #1B2536 !important; color: #E8EDF7 !important;
    border-color: #2E3B52 !important;
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
    "Info Requested": "iq-status-info", "Closed (Compliance)": "iq-status-close",
    "Returned to Investigator": "iq-status-info", "Referred (Compliance)": "iq-status-escalate",
}


def inject_global_styles():
    """Idempotent within a page render — safe to call once per page (done
    automatically inside require_login()). Streamlit dedupes identical
    <style> blocks across reruns on its own. Emits the dark override block
    second, after the base :root declaration, so its redeclared custom
    properties win by CSS source order — no class-toggling needed."""
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)
    if st.session_state.get("dark_mode"):
        st.markdown(_DARK_OVERRIDE_CSS, unsafe_allow_html=True)


def page_banner(icon: str, title: str, subtitle: str):
    """Replaces the six copies of the same hand-written .iq-banner markup
    that used to live at the top of every page."""
    st.markdown(
        f'<div class="iq-banner"><h1>{icon} {title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def severity_badge(severity: str) -> str:
    """Returns an HTML pill for a severity value — pass through st.markdown
    with unsafe_allow_html=True. Falls back to plain text for an unknown
    value rather than an empty/broken badge."""
    cls = _SEVERITY_CLASS.get(severity)
    return f'<span class="iq-badge {cls}">{severity}</span>' if cls else str(severity)


def status_badge(status: str) -> str:
    cls = _STATUS_CLASS.get(status)
    return f'<span class="iq-badge {cls}">{status}</span>' if cls else str(status)


def require_login():
    """Call near the top of every page. Shows a one-time name+role form if
    the session doesn't have an identity yet; otherwise renders the small
    sidebar identity badge and returns (name, role) immediately."""
    inject_global_styles()
    if "user_name" not in st.session_state or "user_role" not in st.session_state:
        st.markdown("### 👤 Who's using InvestigateIQ?")
        st.caption(
            "Prototype-level identity, not real authentication (no password) — matches the mock-auth scope "
            "used throughout this build. This is what gets attributed on every decision you record."
        )
        name = st.text_input("Your name")
        role = st.selectbox("Your role", ROLES)
        if st.button("Continue", type="primary"):
            if not name.strip():
                st.error("Please enter your name.")
            else:
                st.session_state["user_name"] = name.strip()
                st.session_state["user_role"] = role
                st.rerun()
        st.stop()

    with st.sidebar:
        st.markdown(f"**👤 {st.session_state['user_name']}**")
        st.caption(f"Role: {st.session_state['user_role']}")
        # Explicit value= (not just key=) — each page in a classic
        # pages/-directory multipage app is a fresh script/module, and a
        # freshly-instantiated st.toggle(key=...) does not reliably pick up
        # a same-named session_state entry that was last written by a
        # DIFFERENT page's run of this same widget; passing value=
        # explicitly forces it to read the persisted flag every time
        # instead of silently falling back to its own False default.
        st.session_state["dark_mode"] = st.toggle(
            "🌙 Dark mode", value=st.session_state.get("dark_mode", False), key="dark_mode_toggle",
        )
        if st.button("Switch user", key="switch_user_btn"):
            del st.session_state["user_name"]
            del st.session_state["user_role"]
            st.rerun()

    return st.session_state["user_name"], st.session_state["user_role"]


def role_warning(current_role: str, expected_role: str):
    """Soft nudge, not a hard block — matches the mock-auth scope. A hard,
    convincing-looking access-control wall here would overstate what this
    prototype's auth actually is."""
    if current_role != expected_role:
        st.warning(
            f"You're logged in as **{current_role}**. This screen is normally used by **{expected_role}** — "
            "you can still proceed (mock auth, no real access control), but the attribution below will reflect "
            "your actual logged-in identity."
        )
