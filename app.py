# -*- coding: utf-8 -*-
"""
InvestigateIQ — landing page / dashboard home.

Confirms the deploy pipeline and database connection work, gives an
at-a-glance view of the current queue, and routes to the actual product
(Case Queue -> Investigation Workspace). This used to be a "placeholder,
nothing built yet" page; it no longer is one — see
Product Docs/BUILD-STATUS.md for the full, current picture.
"""
import sqlite3
import os
import streamlit as st
from ui_common import require_login, page_banner

st.set_page_config(page_title="InvestigateIQ", page_icon="🔎", layout="wide")
user_name, user_role = require_login()

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "investigateiq.db")

page_banner("🔎", "InvestigateIQ", "AI-Powered AML Investigation Copilot")
st.markdown(
    '<div class="iq-badge iq-status-escalate" style="margin: 10px 0 18px 0;">'
    'PROTOTYPE — fictional data · AI assists, the investigator decides</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------
# Queue snapshot — the same numbers Case Queue shows, so this page is a
# real dashboard home, not just a list of links to click through.
# ---------------------------------------------------------------------
if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    total_alerts = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    open_alerts = conn.execute("SELECT COUNT(*) FROM alerts WHERE status = 'Open'").fetchone()[0]
    high_sev = conn.execute("SELECT COUNT(*) FROM alerts WHERE severity = 'High'").fetchone()[0]
    escalated = conn.execute("SELECT COUNT(*) FROM alerts WHERE status = 'Escalated'").fetchone()[0]
    conn.close()

    k1, k2, k3, k4 = st.columns(4)
    for col, label, value in [
        (k1, "Total alerts", total_alerts), (k2, "Open", open_alerts),
        (k3, "High severity", high_sev), (k4, "Escalated", escalated),
    ]:
        col.markdown(
            f'<div class="iq-card"><div class="iq-kpi-label">{label}</div>'
            f'<div class="iq-kpi-value">{value:,}</div></div>',
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

cols = st.columns(3)
for i, (icon, label, help_text, target) in enumerate(NAV_CARDS):
    with cols[i % 3]:
        with st.container(border=True):
            st.markdown(f'<p class="iq-nav-title">{icon} {label}</p>', unsafe_allow_html=True)
            st.caption(help_text)
            st.page_link(target, label="Open →")

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
    Analytics · Global Search · RAG knowledge base covering all four alert scenarios.

    See **`Product Docs/BUILD-STATUS.md`** for the full, current breakdown of what's built vs. still open —
    that file is kept accurate; this page is a summary of it.
    """
)

st.caption("InvestigateIQ · Capstone Project — Leadership with AI, IIT Mumbai · All data is fictional.")
