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
from ui_common import require_login

st.set_page_config(page_title="InvestigateIQ", page_icon="🔎", layout="wide")
user_name, user_role = require_login()

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
            position: relative; width: 100%; height: 420px; border-radius: 16px;
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
    </style>
    </head>
    <body>
    <div class="hero">
        <canvas id="net"></canvas>
        <div class="hero-content">
            <div class="eyebrow">AI-POWERED AML INVESTIGATION COPILOT</div>
            <h1>InvestigateIQ</h1>
            <p class="tagline">AI drafts the evidence. You make the call.</p>
            <p class="sub">A six-agent pipeline gathers evidence, cites real transactions and playbook
            guidance, and a Grounding Validator checks every claim before a human ever sees it.</p>
            <div class="fictional">Prototype · all customer and transaction data is fictional</div>
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
    height=400,
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
        st.page_link("pages/0_Case_Queue.py", label="Open the Case Queue →", use_container_width=True)

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
        (k1, "📊", "Total alerts", total_alerts, "iq-kpi-blue"), (k2, "🕒", "Open", open_alerts, "iq-kpi-amber"),
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
    ("🗂️", "Case Queue", "All alerts — the real entry point", "pages/0_Case_Queue.py"),
    ("🕵️", "Investigation Workspace", "Evidence, chat, decision, audit log", "pages/2_Investigation_Demo.py"),
    ("🛡️", "Compliance Queue", "Escalated cases awaiting review", "pages/3_Compliance_Queue.py"),
    ("📊", "Analytics", "Trends across the alert population", "pages/5_Analytics.py"),
    ("🔍", "Global Search", "Find a customer, account, or transaction", "pages/6_Global_Search.py"),
    ("🔐", "Admin: Knowledge Base", "Passcode: IQ-Demo-2026", "pages/1_Admin_Knowledge_Base.py"),
    ("⚙️", "Admin: Rule Config", "Passcode: IQ-Demo-2026", "pages/4_Admin_Rule_Config.py"),
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
    for j, (icon, label, help_text, target) in enumerate(row):
        with cols[j]:
            st.markdown(f'<div class="iq-rise iq-stagger-{j + 1}">', unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown(f'<p class="iq-nav-title">{icon} {label}</p>', unsafe_allow_html=True)
                st.caption(help_text)
                st.page_link(target, label="Open →")
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
    Case Queue (all alerts, filters, KPIs) · six-agent Investigation pipeline (real Gemini calls,
    RAG-grounded, validated) · Chat panel (grounded, cited, multi-turn) · Human Decision panel (mandatory
    rationale) · Persistent audit log (survives redeploys) · Compliance Queue · Admin Rule Config ·
    Analytics · Global Search · RAG knowledge base covering five alert scenarios.

    See **`Product Docs/BUILD-STATUS.md`** for the full, current breakdown of what's built vs. still open —
    that file is kept accurate; this page is a summary of it.
    """
)

st.caption("InvestigateIQ · Capstone Project — Leadership with AI, IIT Mumbai · All data is fictional.")
