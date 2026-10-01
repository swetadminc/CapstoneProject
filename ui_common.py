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
import streamlit as st

ROLES = ["Investigator", "Team Lead", "Compliance Officer", "Admin"]
_ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
LOGO_ICON = os.path.join(_ASSETS_DIR, "logo_icon.svg")
LOGO_FULL_LIGHT = os.path.join(_ASSETS_DIR, "logo_full.svg")
LOGO_FULL_DARK = os.path.join(_ASSETS_DIR, "logo_full_dark.svg")

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
/* KPI tiles (Total/Open/High severity/Escalated/Closed) used to render
   identically regardless of what they meant — a colored left accent
   ties each one to the same red/amber/green vocabulary already used for
   severity and status badges elsewhere, instead of inventing a new
   palette, so "High severity" reads as urgent at a glance the same way
   its badge does. A left border, not a full tinted background, so it
   stays legible against both the light radiance and dark navy page
   backgrounds without needing separate light/dark variants. */
.iq-kpi-blue { border-left: 4px solid var(--iq-primary); }
.iq-kpi-amber { border-left: 4px solid var(--iq-sev-medium); }
.iq-kpi-red { border-left: 4px solid var(--iq-sev-high); }
.iq-kpi-green { border-left: 4px solid var(--iq-sev-low); }
.iq-kpi-icon {
    display: inline-flex; align-items: center; justify-content: center;
    width: 30px; height: 30px; border-radius: 9px; font-size: 15px;
    margin-bottom: 6px;
}
.iq-kpi-blue .iq-kpi-icon { background: var(--iq-status-info-bg); }
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

.iq-card, [data-testid="stVerticalBlockBorderWrapper"] {
    transition: transform 0.2s ease, box-shadow 0.2s ease;
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
    [data-testid="stHorizontalBlock"]:has(.iq-queue-header) { display: none; }
    [data-testid="stHorizontalBlock"]:has(.iq-queue-row) {
        border-bottom: 1px solid var(--iq-card-border); padding-bottom: 8px; margin-bottom: 8px;
    }
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.iq-nav-title):hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 24px rgba(26,42,74,0.14);
}

@media (prefers-reduced-motion: reduce) {
    .iq-rise, div[data-testid="stVerticalBlockBorderWrapper"]:has(.iq-nav-title):hover {
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
   "Ask the Copilot" chat history on Investigation Demo, the nav cards on
   Home, any other bordered container — kept its own light background in
   dark mode, because nothing here ever gave it one. Meanwhile the
   blanket "* { color: ... !important }" above forces the text INSIDE it
   to light gray regardless of that background — light text on a
   still-light box, unreadable. Same bug shape as the badges and
   backtick-code fixes elsewhere in this file, different component. */
[data-testid="stVerticalBlockBorderWrapper"], [data-testid="stChatMessage"],
[data-testid="stChatInput"], [data-testid="stChatInput"] textarea {
    background-color: #1B2536 !important; border-color: #2E3B52 !important;
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
    properties win by CSS source order — no class-toggling needed.

    Reads session_state["dark_mode_toggle"] — the toggle widget's OWN key,
    not a separately-assigned "dark_mode" flag. A prior version tracked
    dark mode under its own key, set by a plain assignment further down in
    require_login()'s sidebar block; since this function runs at the very
    top of the page, before that assignment line executes, it always read
    last run's value — every click looked like it took effect one rerun
    late (toggle showed the new state, but the background didn't change
    until the NEXT click). Streamlit updates a widget's own key-bound
    session_state entry before the script starts running, so reading that
    key directly here has no such lag — confirmed by testing repeated
    clicks in place on the same page, not just navigating between pages."""
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)
    if st.session_state.get("dark_mode_toggle"):
        st.markdown(_DARK_OVERRIDE_CSS, unsafe_allow_html=True)


def page_banner(icon: str, title: str, subtitle: str):
    """Replaces the six copies of the same hand-written .iq-banner markup
    that used to live at the top of every page."""
    st.markdown(
        f'<div class="iq-banner"><h1>{icon} {title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )
    st.caption("Prototype · all customer and transaction data is fictional")


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
    dark = bool(st.session_state.get("dark_mode_toggle"))
    st.logo(LOGO_FULL_DARK if dark else LOGO_FULL_LIGHT, icon_image=LOGO_ICON, size="large")

    if "user_name" not in st.session_state or "user_role" not in st.session_state:
        st.write("")
        lcol1, lcol2, lcol3 = st.columns([1, 2, 1])
        with lcol2:
            st.image(LOGO_FULL_DARK if dark else LOGO_FULL_LIGHT, use_container_width=True)
            st.write("")
            with st.container(border=True):
                st.markdown("#### 👤 Who's using InvestigateIQ?")
                st.caption(
                    "Prototype-level identity, not real authentication (no password) — matches the mock-auth "
                    "scope used throughout this build. This is what gets attributed on every decision you record."
                )
                name = st.text_input("Your name")
                role = st.selectbox("Your role", ROLES)
                if st.button("Continue", type="primary", use_container_width=True):
                    if not name.strip():
                        st.error("Please enter your name.")
                    else:
                        st.session_state["user_name"] = name.strip()
                        st.session_state["user_role"] = role
                        st.rerun()
        st.stop()

    with st.sidebar:
        st.caption("Capstone Group 7 · Leadership with AI, IIT Bombay")
        st.markdown(f"**👤 {st.session_state['user_name']}**")
        st.caption(f"Role: {st.session_state['user_role']}")
        # key= alone is enough — session_state["dark_mode_toggle"] persists
        # for the whole session (every page reads it, see
        # inject_global_styles() above), the same way user_name does.
        st.toggle("🌙 Dark mode", key="dark_mode_toggle")
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
