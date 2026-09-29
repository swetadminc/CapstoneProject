# -*- coding: utf-8 -*-
"""
InvestigateIQ — landing / system-health page.

Confirms the deploy pipeline and database connection work, and routes to
the actual product (Case Queue -> Investigation Workspace). This used to be
a "placeholder, nothing built yet" page; it no longer is one — see
Product Docs/BUILD-STATUS.md for the full, current picture.
"""
import sqlite3
import os
import streamlit as st
import pandas as pd
from ui_common import require_login

st.set_page_config(page_title="InvestigateIQ", page_icon="🔎", layout="centered")
user_name, user_role = require_login()

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "investigateiq.db")

st.markdown(
    """
    <style>
    .iq-banner {
        background-color: #1A2A4A; color: white; padding: 18px 24px;
        border-radius: 10px; margin-bottom: 6px;
    }
    .iq-banner h1 { margin: 0; font-size: 28px; }
    .iq-banner p { margin: 4px 0 0 0; color: #C9D6E8; font-size: 15px; }
    .iq-proto {
        background-color: #FCE2E2; color: #B02A2A; padding: 8px 14px;
        border-radius: 6px; font-size: 13px; margin-top: 14px; margin-bottom: 20px;
    }
    </style>
    <div class="iq-banner">
        <h1>InvestigateIQ</h1>
        <p>AI-Powered AML Investigation Copilot</p>
    </div>
    <div class="iq-proto">PROTOTYPE — fictional data · AI assists, the investigator decides</div>
    """,
    unsafe_allow_html=True,
)

st.subheader("Start here")
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.page_link("pages/0_Case_Queue.py", label="🗂️ Case Queue", help="All alerts — the real entry point")
with c2:
    st.page_link("pages/2_Investigation_Demo.py", label="🕵️ Investigation Workspace", help="Evidence, chat, decision, audit log")
with c3:
    st.page_link("pages/3_Compliance_Queue.py", label="🛡️ Compliance Queue", help="Escalated cases")
with c4:
    st.page_link("pages/1_Admin_Knowledge_Base.py", label="🔐 Admin: Knowledge Base", help="Passcode: IQ-Demo-2026")
with c5:
    st.page_link("pages/4_Admin_Rule_Config.py", label="⚙️ Admin: Rule Config", help="Passcode: IQ-Demo-2026")

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
    Case Queue (all alerts, filters, KPIs) · Investigation Agent (real Gemini calls, RAG-grounded,
    validated) · Chat panel (grounded, cited, multi-turn) · Human Decision panel (mandatory rationale) ·
    Persistent audit log (survives redeploys) · RAG knowledge base covering all three alert scenarios.

    See **`Product Docs/BUILD-STATUS.md`** for the full, current breakdown of what's built vs. still open —
    that file is kept accurate; this page is a summary of it.
    """
)

st.caption("InvestigateIQ · Capstone Project — Leadership with AI, IIT Mumbai · All data is fictional.")
