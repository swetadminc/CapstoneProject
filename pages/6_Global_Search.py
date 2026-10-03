# -*- coding: utf-8 -*-
"""
Global Search — find a customer, account, or transaction without knowing
which case it belongs to first.

The Case Queue's filters only search within the current alert list; this searches
the full dataset (551 customers, ~9,940 transactions) by name, ID, or
reference text, and links straight into the Investigation Workspace for any
matching customer that has an alert. Read-only, parameterized queries only
— the search term never gets string-formatted into SQL.
"""
import os
import sys
import sqlite3
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.knowledge_search import DB_PATH
from ui_common import require_login, page_banner, page_flow, render_context_copilot

st.set_page_config(page_title="InvestigateIQ — Global Search", page_icon="🔍", layout="wide")
user_name, user_role = require_login()
render_context_copilot("Global Search", st.session_state.get("active_case_id"))

page_banner("🔍", "Global Search", "Find a customer, account, or transaction across the full dataset")
page_flow("Find a fictional record without knowing its case ID", [
    ("Enter a query", "Search a name, ID or transaction reference."),
    ("Review matches", "Inspect matching customers, accounts, transactions and alerts."),
    ("Open a case", "Follow a linked alert into the Investigation Workspace."),
], "Search is read-only; result lists are capped to keep review manageable.")
st.write("")

query = st.text_input(
    "Search", placeholder="Customer name, CUST-/ACC-/TXN-/CASE- ID, or transaction reference text",
    label_visibility="collapsed",
    help="Searches fictional customers, accounts, transactions and alerts. Enter at least two characters; each result list is capped at 25.",
)

if not query or len(query.strip()) < 2:
    st.caption("Type at least 2 characters to search. Searches customers, accounts, transactions, and alerts.")
    st.stop()

term = query.strip()
like = f"%{term}%"
conn = sqlite3.connect(DB_PATH)

# ---------------------------------------------------------------------
# Customers — by name or customer_id
# ---------------------------------------------------------------------
customers = pd.read_sql(
    """SELECT customer_id, name, type, occupation_or_industry, risk_rating, kyc_status
       FROM customers WHERE name LIKE ? OR customer_id LIKE ? LIMIT 25""",
    conn, params=(like, like),
)

# ---------------------------------------------------------------------
# Accounts — by account_id, or belonging to a matched customer
# ---------------------------------------------------------------------
accounts = pd.read_sql(
    """SELECT a.account_id, a.customer_id, c.name AS customer_name, a.type, a.status, a.risk_rating
       FROM accounts a JOIN customers c ON c.customer_id = a.customer_id
       WHERE a.account_id LIKE ? OR c.name LIKE ? LIMIT 25""",
    conn, params=(like, like),
)

# ---------------------------------------------------------------------
# Transactions — by txn_id, counterparty name, or reference text
# ---------------------------------------------------------------------
transactions = pd.read_sql(
    """SELECT t.txn_id, t.account_id, c.name AS customer_name, t.txn_datetime, t.direction,
              t.amount, t.counterparty_name, t.reference_text
       FROM transactions t
       JOIN accounts a ON a.account_id = t.account_id
       JOIN customers c ON c.customer_id = a.customer_id
       WHERE t.txn_id LIKE ? OR t.counterparty_name LIKE ? OR t.reference_text LIKE ?
       ORDER BY t.txn_datetime DESC LIMIT 25""",
    conn, params=(like, like, like),
)

# ---------------------------------------------------------------------
# Alerts / cases — by case_id, or belonging to a matched customer
# ---------------------------------------------------------------------
alerts = pd.read_sql(
    """SELECT al.case_id, al.alert_type, al.scenario_id, al.severity, al.status, c.name AS customer_name
       FROM alerts al JOIN customers c ON c.customer_id = al.customer_id
       WHERE al.case_id LIKE ? OR c.name LIKE ? LIMIT 25""",
    conn, params=(like, like),
)
conn.close()

total_hits = len(customers) + len(accounts) + len(transactions) + len(alerts)
st.caption(f"{total_hits} match(es) for “{term}”")

if total_hits == 0:
    st.info("No matches. Try a partial name, or an ID like CUST-1004, ACC-1385, TXN-19918, or CASE-001.")
    st.stop()

if not alerts.empty:
    st.subheader(f"Cases ({len(alerts)})")
    for _, row in alerts.iterrows():
        c1, c2, c3, c4, c5 = st.columns([1.3, 2.2, 2.4, 1, 1.4])
        c1.markdown(f"`{row['case_id']}`")
        c2.write(row["customer_name"])
        c3.write(row["alert_type"])
        c4.write(row["severity"])
        if c5.button("🔍", key=f"srch_case_{row['case_id']}", help=f"Investigate {row['case_id']}",
                     use_container_width=True):
            st.session_state["selected_case_id"] = row["case_id"]
            st.switch_page("pages/2_Investigation_Demo.py")
    st.divider()

if not customers.empty:
    st.subheader(f"Customers ({len(customers)})")
    st.dataframe(customers, hide_index=True, use_container_width=True)
    st.divider()

if not accounts.empty:
    st.subheader(f"Accounts ({len(accounts)})")
    st.dataframe(accounts, hide_index=True, use_container_width=True)
    st.divider()

if not transactions.empty:
    st.subheader(f"Transactions ({len(transactions)})")
    st.dataframe(transactions, hide_index=True, use_container_width=True)

st.caption("All data is fictional. Results capped at 25 per category — narrow the search term for a smaller list.")
