# -*- coding: utf-8 -*-
"""
InvestigateIQ — placeholder deployment.

This is not the Investigation Copilot yet (see CEO Playbook, Section 9: that's the
main build). This page exists to (a) prove the Railway <-> GitHub deploy pipeline
works end to end, and (b) prove the app can actually connect to and query the
real database the Copilot will run on — not just render static text.
"""
import sqlite3
import os
import streamlit as st
import pandas as pd

st.set_page_config(page_title="InvestigateIQ", page_icon="🔎", layout="centered")

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

st.subheader("Deployment is live 🎉")
st.write(
    "This page is a placeholder while the Investigation Copilot is being built. "
    "It's here to confirm the pipeline works: **GitHub → Railway → this app → the database.**"
)

st.divider()
st.subheader("Database connection")

if not os.path.exists(DB_PATH):
    st.error(f"Database not found at `{DB_PATH}`. Run `python data/build_database.py` and redeploy.")
else:
    try:
        conn = sqlite3.connect(DB_PATH)
        tables = ["customers", "accounts", "transactions", "relationships", "alerts", "past_cases", "documents"]
        counts = {}
        for t in tables:
            counts[t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]

        st.success("Connected to `data/investigateiq.db` — live query below, not hardcoded numbers.")

        cols = st.columns(4)
        labels = {
            "customers": "Customers", "accounts": "Accounts", "transactions": "Transactions",
            "relationships": "Relationships", "alerts": "Alerts", "past_cases": "Past Cases",
            "documents": "Documents",
        }
        for i, (t, label) in enumerate(labels.items()):
            with cols[i % 4]:
                st.metric(label, f"{counts[t]:,}")

        st.divider()
        st.subheader("The frozen demo scenario")
        hero = pd.read_sql(
            "SELECT customer_id, name, type, occupation_or_industry, risk_rating "
            "FROM customers WHERE customer_id = 'CUST-1004'", conn,
        )
        st.dataframe(hero, hide_index=True, use_container_width=True)

        alerts = pd.read_sql(
            "SELECT alert_id, case_id, severity, status, alert_date "
            "FROM alerts WHERE customer_id = 'CUST-1004' ORDER BY alert_date", conn,
        )
        st.caption("Both hero cases (C1 suspicious, C2 legitimate twin) are live in the database:")
        st.dataframe(alerts, hide_index=True, use_container_width=True)

        conn.close()
    except Exception as e:
        st.error(f"Database query failed: {e}")

st.divider()
st.subheader("Knowledge base — built and live today")
st.markdown(
    "The RAG knowledge base (OKF documents → chunked → indexed with SQLite FTS5) is already built and "
    "queryable, ahead of the agents that will use it. Open **Admin Knowledge Base** in the sidebar to see "
    "the documents, every chunk, and run a real keyword search against the index."
)

st.divider()
st.subheader("What's coming")
st.markdown(
    """
    - The Investigation Workspace — evidence panel, chat/Q&A, human decision panel
    - The AI agents (Context → Discovery → Evidence/Validation → Conclusion) with the Grounding Validator
    - The Conclusion Agent wired to the knowledge-base search that's already live (see above)
    - The full audit trail

    See the **CEO Playbook** in `Product Docs/` for the complete architecture, roles, and demo script.
    """
)

st.caption("InvestigateIQ · Capstone Project — Leadership with AI, IIT Mumbai · All data is fictional.")
