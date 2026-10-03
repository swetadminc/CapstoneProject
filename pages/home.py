# -*- coding: utf-8 -*-
"""
InvestigateIQ — landing page / dashboard home.

Moved out of app.py when app.py became a pure st.navigation() router (see
app.py's docstring for why — the short version: Streamlit's classic
pages/-directory auto-discovery derives every sidebar label from the raw
filename, which is why the entry point used to show up as the literal,
lowercase "app" in the nav. st.navigation() lets every page — including
this one — get a real title and icon instead.

The hero below is a real animated component (st.components.v1.html, not
just CSS) — a drifting particle network on a canvas, deliberately styled
like a transaction/entity graph rather than generic decoration, since
that's literally what this product investigates. It renders in its own
iframe, which is why it carries a fixed dark gradient instead of reading
the app's light/dark toggle: same principle already used for the .iq-banner
across every other page (see ui_common.py) — a self-contained dark section
that stays legible regardless of the surrounding theme, not adaptive body
copy.
"""
import os
import sqlite3
import sys
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.runtime_db import get_latest_decision_per_case, resolve_status
from project_identity import COURSE_LABEL, GROUP_LABEL, PROJECT_DESCRIPTION, PROJECT_NAME
from ui_common import ROLES, require_login, page_flow, render_context_copilot

st.set_page_config(page_title="InvestigateIQ", page_icon="🔎", layout="wide")
user_name, user_role = require_login(allow_guest=True)
render_context_copilot("Home", st.session_state.get("active_case_id"))

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "investigateiq.db")

# ---------------------------------------------------------------------
# Hero — animated particle-network canvas + staggered text reveal.
# Runs in its own sandboxed iframe (components.html), so it has its own
# complete <style>/<script> — nothing from the outer page's CSS or
# session state (like dark_mode) reaches in here, which is exactly why
# it's a fixed, self-contained dark section rather than a theme-aware one.
# ---------------------------------------------------------------------
components.html(
    """
    <!doctype html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        html, body { margin: 0; padding: 0; overflow: hidden; }
        .hero {
            position: relative; width: 100%; height: 320px; border-radius: 16px;
            background: linear-gradient(135deg, #060B16 0%, #12203D 45%, #1F3B73 100%);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            box-shadow: 0 10px 40px rgba(6,11,22,0.35);
        }
        canvas { position: absolute; inset: 0; width: 100%; height: 100%; }
        .hero-content {
            position: relative; z-index: 2; height: 100%;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            text-align: center; padding: 0 24px; color: #F2F5FA;
        }
        .eyebrow {
            font-size: 12.5px; font-weight: 700; letter-spacing: 2.5px; color: #8FC1FF;
            opacity: 0; animation: rise 0.6s cubic-bezier(.16,1,.3,1) 0.05s forwards;
        }
        h1 {
            margin: 10px 0 0 0; font-size: 52px; font-weight: 800; letter-spacing: -1px;
            background: linear-gradient(90deg, #FFFFFF, #BFD9FF);
            -webkit-background-clip: text; background-clip: text; color: transparent;
            opacity: 0; animation: rise 0.7s cubic-bezier(.16,1,.3,1) 0.15s forwards;
        }
        .tagline {
            margin: 12px 0 0 0; font-size: 19px; font-weight: 500; color: #E8EDF7;
            opacity: 0; animation: rise 0.7s cubic-bezier(.16,1,.3,1) 0.28s forwards;
        }
        .sub {
            margin: 8px 0 0 0; font-size: 14px; color: #9FB0C9; max-width: 560px; line-height: 1.5;
            opacity: 0; animation: rise 0.7s cubic-bezier(.16,1,.3,1) 0.4s forwards;
        }
        .fictional {
            margin-top: 22px; font-size: 11px; color: #6E85A8; letter-spacing: 0.5px;
            opacity: 0; animation: rise 0.7s cubic-bezier(.16,1,.3,1) 0.55s forwards;
        }
        @keyframes rise { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
        @media (prefers-reduced-motion: reduce) {
            .eyebrow, h1, .tagline, .sub, .fictional { animation: none !important; opacity: 1 !important; }
        }
        @media (max-width: 600px) {
            h1 { font-size: 38px; }
            .tagline { font-size: 16px; }
            .sub { font-size: 12px; }
        }
    </style>
    </head>
    <body>
    <div class="hero">
        <canvas id="net"></canvas>
        <div class="hero-content">
            <div class="eyebrow">AI-POWERED AML INVESTIGATION COPILOT</div>
            <h1>InvestigateIQ</h1>
            <p class="tagline">Trace the evidence. Own the decision.</p>
            <p class="sub">A six-step investigation workflow gathers evidence, links findings to
            transaction records and playbook guidance, and checks selected citations and claims
            before an investigator reviews the draft.</p>
            <div class="fictional">Sample environment · all customer and transaction data is fictional</div>
        </div>
    </div>
    <script>
        const canvas = document.getElementById('net');
        const ctx = canvas.getContext('2d');
        const dpr = window.devicePixelRatio || 1;
        let W, H;
        function resize() {
            W = canvas.width = canvas.offsetWidth * dpr;
            H = canvas.height = canvas.offsetHeight * dpr;
        }
        window.addEventListener('resize', resize);
        resize();

        const N = 44;
        const particles = [];
        for (let i = 0; i < N; i++) {
            particles.push({
                x: Math.random() * W, y: Math.random() * H,
                vx: (Math.random() - 0.5) * 0.3, vy: (Math.random() - 0.5) * 0.3,
                r: (Math.random() * 1.5 + 0.9) * dpr,
            });
        }
        const LINK_DIST = 125 * dpr;

        function tick() {
            ctx.clearRect(0, 0, W, H);
            for (const p of particles) {
                p.x += p.vx; p.y += p.vy;
                if (p.x < 0 || p.x > W) p.vx *= -1;
                if (p.y < 0 || p.y > H) p.vy *= -1;
            }
            for (let i = 0; i < N; i++) {
                for (let j = i + 1; j < N; j++) {
                    const a = particles[i], b = particles[j];
                    const dx = a.x - b.x, dy = a.y - b.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < LINK_DIST) {
                        ctx.strokeStyle = 'rgba(143,193,255,' + ((1 - dist / LINK_DIST) * 0.45) + ')';
                        ctx.lineWidth = 1;
                        ctx.beginPath();
                        ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
                        ctx.stroke();
                    }
                }
            }
            for (const p of particles) {
                ctx.fillStyle = 'rgba(242,245,250,0.85)';
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
                ctx.fill();
            }
            requestAnimationFrame(tick);
        }
        tick();
    </script>
    </body>
    </html>
    """,
    height=320,
    scrolling=False,
)

# The hero's own "Open the Case Queue" button lives HERE, not inside the
# iframe above — components.html's sandbox is missing allow-top-navigation,
# so a plain <a target="_top"> inside it is silently blocked by the
# browser (confirmed by testing: the click registered but nothing
# navigated). st.page_link is the same real, working navigation used
# everywhere else in the app. Scoped with container(key=...) rather than
# a markdown open/close div pair — the latter doesn't actually wrap
# anything at the DOM level (each st.markdown call is its own sibling
# node), a real Streamlit-rendering quirk hit more than once this build.
with st.container(key="hero_cta"):
    _cta_cols = st.columns([1, 1, 1])
    with _cta_cols[1]:
        st.page_link("pages/0_Case_Queue.py", label="Open the Case Queue →", use_container_width=True,
                     help="Start with preloaded fictional alerts; choosing a case opens the investigation workflow.")

st.caption(f"{GROUP_LABEL} · {COURSE_LABEL} · Fictional customer and transaction data")
intro_col, demo_col = st.columns([1.7, 1])
with intro_col:
    st.subheader("What InvestigateIQ does")
    st.markdown(f"**{PROJECT_NAME} — {PROJECT_DESCRIPTION}.**")
    st.write(
        "InvestigateIQ helps an investigator turn a fictional monitoring alert into an "
        "evidence-linked draft, review that draft, and record a reasoned human decision. "
        "Escalated cases then move to a separate Compliance review."
    )
    st.caption("The AI assists; it does not make the final decision or file anything with a regulator.")
    st.page_link("pages/7_Project_Team.py", label="Meet the project and team →",
                 help="See the project identity, draft team roster, and display settings.")
with demo_col:
    with st.container(border=True, key="iq_bordered_home_demo"):
        if user_name:
            st.markdown("#### Workspace ready")
            st.write(f"**{user_name}** · {user_role}")
            st.caption("Use the sidebar to change your display identity or light/dark setting.")
        else:
            st.markdown("#### Enter your workspace")
            st.caption("Choose a display name and role for attribution. This environment does not authenticate users.")
            demo_name = st.text_input("Your name", key="home_demo_name",
                                      help="Display name attributed to decisions and audit events.")
            demo_role = st.radio("Your role", ROLES, horizontal=True, key="home_demo_role",
                                 help="A workflow label only; this environment does not enforce role-based access.")
            if st.button("Open workspace", type="primary", key="home_demo_continue",
                         help="Open the workspace with this display name and role."):
                if not demo_name.strip():
                    st.error("Please enter your name.")
                else:
                    st.session_state["user_name"] = demo_name.strip()
                    st.session_state["user_role"] = demo_role
                    st.rerun()

st.subheader("Watch how InvestigateIQ works")
_walkthrough_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "investigateiq_walkthrough.mp4")
_poster_path = os.path.join(os.path.dirname(_walkthrough_path), "investigateiq_walkthrough_poster.png")
if os.path.exists(_walkthrough_path):
    if os.path.exists(_poster_path):
        cover_col, description_col = st.columns([1, 2])
        with cover_col:
            st.image(_poster_path, caption="InvestigateIQ product walkthrough", width="stretch")
        with description_col:
            st.markdown("#### Follow a case, step by step")
            st.write("Follow a selected case through its recorded activity, Copilot questions, and cited evidence. Use the live screens below to inspect the current workflow yourself.")
            st.caption("The recording uses captured product screens and an example case; live records may change. No case finding determines whether funds are lawful or unlawful.")
    st.video(_walkthrough_path)
    st.caption("Full narrated product walkthrough. Use the page links below to inspect every step yourself.")
else:
    st.info("The captioned walkthrough is being prepared. The flowchart and page guides below explain the workflow in the meantime.")

st.subheader("The investigation journey")
st.image(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "landing_workflow.svg"), width="stretch")
page_flow("Understand the complete workflow before opening a screen", [
    ("Alert arrives", "Choose a preloaded fictional case in the Case Queue."),
    ("Copilot drafts", "Review evidence, synthetic guidance and selected validation checks."),
    ("Human decides", "An investigator records a reasoned decision and audit event."),
    ("Compliance follows up", "Escalated cases receive a separate human review."),
], "Search and Analytics help explore the fictional data; admin screens show retrieval and rule previews. No regulatory filing is automated.")

# ---------------------------------------------------------------------
# Queue snapshot — the same numbers Case Queue shows, so this page is a
# real dashboard home, not just a list of links to click through.
# Staggered .iq-rise entrance so the cards cascade in under the hero.
# ---------------------------------------------------------------------
if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    alert_rows = conn.execute("SELECT case_id, status, severity FROM alerts").fetchall()
    conn.close()
    decisions = get_latest_decision_per_case()
    statuses = [resolve_status(r["status"], decisions.get(r["case_id"])) for r in alert_rows]

    total_alerts = len(alert_rows)
    open_alerts = statuses.count("Open")
    high_sev = sum(1 for r in alert_rows if r["severity"] == "High")
    escalated = statuses.count("Escalated")

    st.write("")
    k1, k2, k3, k4 = st.columns(4)
    for i, (col, icon, label, value, accent) in enumerate([
        (k1, "📊", "Preloaded alerts", total_alerts, "iq-kpi-blue"), (k2, "🕒", "Preloaded open", open_alerts, "iq-kpi-amber"),
        (k3, "🔥", "High severity", high_sev, "iq-kpi-red"), (k4, "🚨", "Escalated", escalated, "iq-kpi-red"),
    ]):
        col.markdown(
            f'<div class="iq-card {accent} iq-rise iq-stagger-{i+1}"><div class="iq-kpi-icon">{icon}</div>'
            f'<div class="iq-kpi-label">{label}</div><div class="iq-kpi-value">{value:,}</div></div>',
            unsafe_allow_html=True,
        )
    st.write("")

st.subheader("Start here")

NAV_CARDS = [
    ("👥", "Project & Team", "Product aim, group details, and responsibility plan.", "See the planned responsibility areas for each member.", "pages/7_Project_Team.py"),
    ("🗂️", "Case Queue", "Filter alerts by customer, status, and severity.", "Choose a case to begin an investigation.", "pages/0_Case_Queue.py"),
    ("🕵️", "Investigation Workspace", "Ask case questions and inspect cited records.", "Review findings, decide, and check the audit trail.", "pages/2_Investigation_Demo.py"),
    ("🛡️", "Compliance Queue", "Review cases escalated by an investigator.", "Record a separate human follow-up; no automatic filing.", "pages/3_Compliance_Queue.py"),
    ("📊", "Analytics", "Explore alert volumes and severity patterns.", "Read workload trends, not fraud verdicts.", "pages/5_Analytics.py"),
    ("🔍", "Global Search", "Find a customer, account, or transaction.", "Open the matching record for its context.", "pages/6_Global_Search.py"),
    ("🧩", "Evidence & RAG", "Inspect fictional KYC, alerts, and ledger sources.", "Compare source text, exact chunks, and evidence gaps.", "pages/8_Evidence_RAG.py"),
    ("🔐", "Admin: Knowledge Base", "Browse the indexed investigation guidance.", "Check the source text behind a retrieved passage.", "pages/1_Admin_Knowledge_Base.py"),
    ("⚙️", "Admin: Rule Config", "Preview thresholds against fictional alerts.", "A red match means review, not proven wrongdoing.", "pages/4_Admin_Rule_Config.py"),
]

# Fresh st.columns(3) per row of 3, rather than one set of columns indexed
# by i % 3 — Streamlit stacks a *set* of columns in order when it collapses
# them on mobile. Reusing one set across all 7 cards meant mobile showed
# card 0, then card 3, then card 6 (column 0's cards), then column 1's,
# then column 2's — the reading order (Case Queue, Investigation
# Workspace, ...) got scrambled into a column-major order instead.
# Building columns fresh per row keeps each row's own stack in order, and
# concatenated across rows that's the original reading order.
for row_start in range(0, len(NAV_CARDS), 3):
    row = NAV_CARDS[row_start:row_start + 3]
    cols = st.columns(3)
    for j, (icon, label, help_text, next_step, target) in enumerate(row):
        with cols[j]:
            st.markdown(f'<div class="iq-rise iq-stagger-{j + 1}">', unsafe_allow_html=True)
            with st.container(border=True, key=f"iq_bordered_nav_{row_start + j}"):
                st.markdown(f'<p class="iq-nav-title"><span class="iq-nav-icon" aria-hidden="true">{icon}</span>{label}</p>', unsafe_allow_html=True)
                st.caption(help_text)
                st.markdown(f'<p class="iq-nav-detail">{next_step}</p>', unsafe_allow_html=True)
                st.page_link(target, label="Open →", help=help_text)
            st.markdown('</div>', unsafe_allow_html=True)

st.divider()
st.subheader("System health")

if not os.path.exists(DB_PATH):
    st.error(f"Database not found at `{DB_PATH}`. Run `python data/build_database.py` and redeploy.")
else:
    try:
        conn = sqlite3.connect(DB_PATH)
        tables = ["customers", "accounts", "transactions", "relationships", "alerts", "past_cases", "documents", "knowledge_base", "knowledge_chunks"]
        counts = {}
        for t in tables:
            counts[t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]

        st.success("Connected to `data/investigateiq.db` — live query below, not hardcoded numbers.")

        cols = st.columns(4)
        labels = {
            "customers": "Customers", "accounts": "Accounts", "transactions": "Transactions",
            "alerts": "Alerts", "knowledge_base": "KB Documents", "knowledge_chunks": "KB Chunks",
            "past_cases": "Past Cases", "documents": "Documents",
        }
        for i, (t, label) in enumerate(labels.items()):
            with cols[i % 4]:
                st.metric(label, f"{counts[t]:,}")

        conn.close()
    except Exception as e:
        st.error(f"Database query failed: {e}")

st.divider()
st.subheader("What's actually built")
st.markdown(
    """
    Case Queue (all alerts, filters, KPIs) · six-step investigation workflow (Gemini-assisted
    report drafting, playbook retrieval, selected grounding checks) · Chat panel (multi-turn with
    evidence references) · Human Decision panel (mandatory
    rationale) · Persistent audit log (survives redeploys) · Compliance Queue · Admin Rule Config ·
    Analytics · Global Search · RAG knowledge base covering five alert scenarios.

    See **`Product Docs/BUILD-STATUS.md`** for the detailed build history and
    **`Product Docs/16-Course-Source-Evidence-Register.md`** for current evidence and limitations.
    """
)

st.caption(f"{PROJECT_NAME} · {GROUP_LABEL} · {COURSE_LABEL} · All data is fictional.")
