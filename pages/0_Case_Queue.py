# -*- coding: utf-8 -*-
"""
Case Queue Dashboard — Screen 2 from the UI wireframe (Product Docs,
09-UI-Wireframes-and-Screen-Designs.md), built for real.

The conceptual landing page of the actual product: every open alert from
the (mock) monitoring system, filterable, with a live decision status pulled
from the persistent audit trail — not a static mockup image.

Two cases (CASE-001, CASE-002) are the frozen, pre-cached demo scenario and
are marked accordingly. The other cases are real alerts from the same
dataset, investigable live through the same agent — nothing here is faked
to pad the count.
"""
import os
import sys
import sqlite3
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.knowledge_search import DB_PATH
from data.runtime_db import get_latest_decision_per_case

HERO_CASES = {"CASE-001", "CASE-002"}
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "cached_reports")

st.set_page_config(page_title="InvestigateIQ — Case Queue", page_icon="🗂️", layout="wide")

st.markdown(
    """
    <style>
    .iq-banner { background-color: #1A2A4A; color: white; padding: 14px 22px; border-radius: 10px; }
    .iq-banner h1 { margin: 0; font-size: 22px; }
    .iq-banner p { margin: 2px 0 0 0; color: #C9D6E8; font-size: 13px; }
    .case-row { border: 1px solid #E0E0E0; border-radius: 8px; padding: 10px 16px; margin-bottom: 6px; }
    .sev-high { color: #B02A2A; font-weight: 700; }
    .sev-medium { color: #B57808; font-weight: 700; }
    .sev-low { color: #27844E; font-weight: 700; }
    .status-open { background: #FFF3D6; color: #B57808; padding: 2px 8px; border-radius: 5px; font-size: 12px; font-weight: 600; }
    .status-escalate { background: #FCE2E2; color: #B02A2A; padding: 2px 8px; border-radius: 5px; font-size: 12px; font-weight: 600; }
    .status-close { background: #E8F3EC; color: #27844E; padding: 2px 8px; border-radius: 5px; font-size: 12px; font-weight: 600; }
    .status-info { background: #EEF3FB; color: #2E63BF; padding: 2px 8px; border-radius: 5px; font-size: 12px; font-weight: 600; }
    .hero-badge { background: #2E63BF; color: white; padding: 1px 7px; border-radius: 5px; font-size: 11px; margin-left: 6px; }
    </style>
    <div class="iq-banner">
        <h1>🗂️ Case Queue</h1>
        <p>Every open alert from the monitoring system — filter, review, and open a case to investigate</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")


@st.cache_data(ttl=30)
def load_queue():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("""
        SELECT a.alert_id, a.case_id, a.customer_id, a.account_id, a.alert_type,
               a.scenario_id, a.trigger_rule, a.alert_date, a.severity, a.status,
               c.name AS customer_name, c.type AS customer_type, c.risk_rating
        FROM alerts a
        JOIN customers c ON c.customer_id = a.customer_id
        ORDER BY a.alert_date DESC
    """, conn)
    conn.close()
    return df


df = load_queue()
decisions = get_latest_decision_per_case()

# Derive a live "queue status" per case: a human decision overrides the
# original alert.status; otherwise it's whatever the alert record says.
def queue_status(row):
    d = decisions.get(row["case_id"])
    if d:
        return {"close": "Closed", "escalate": "Escalated", "request_info": "Info Requested"}.get(d["action"], d["action"])
    # Normalize the raw alert status ("Closed - No Concern") to the same
    # vocabulary a human decision produces ("Closed"), so KPI counts and
    # badge colors are consistent regardless of which source set the status.
    raw = row["status"]
    if raw.startswith("Closed"):
        return "Closed"
    return raw

df["queue_status"] = df.apply(queue_status, axis=1)
df["has_cache"] = df["case_id"].isin(HERO_CASES)

# ------------------------------------------------------------------
# KPI strip
# ------------------------------------------------------------------
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total alerts", len(df))
c2.metric("Open", int((df["queue_status"] == "Open").sum()))
c3.metric("High severity", int((df["severity"] == "High").sum()))
c4.metric("Escalated", int((df["queue_status"] == "Escalated").sum()))
c5.metric("Closed", int((df["queue_status"] == "Closed").sum()))

st.divider()

# ------------------------------------------------------------------
# Filters
# ------------------------------------------------------------------
fc1, fc2, fc3, fc4 = st.columns([1.2, 1.2, 1.2, 2])
severity_filter = fc1.multiselect("Severity", sorted(df["severity"].unique()), default=[])
status_filter = fc2.multiselect("Status", sorted(df["queue_status"].unique()), default=[])
scenario_filter = fc3.multiselect("Scenario", sorted(df["scenario_id"].unique()), default=[])
search = fc4.text_input("Search customer name", placeholder="e.g. Apex")

filtered = df.copy()
if severity_filter:
    filtered = filtered[filtered["severity"].isin(severity_filter)]
if status_filter:
    filtered = filtered[filtered["queue_status"].isin(status_filter)]
if scenario_filter:
    filtered = filtered[filtered["scenario_id"].isin(scenario_filter)]
if search:
    filtered = filtered[filtered["customer_name"].str.contains(search, case=False, na=False)]

st.caption(f"Showing {len(filtered)} of {len(df)} alerts")

# ------------------------------------------------------------------
# Queue table
# ------------------------------------------------------------------
sev_class = {"High": "sev-high", "Medium": "sev-medium", "Low": "sev-low"}
status_class = {"Open": "status-open", "Escalated": "status-escalate", "Closed": "status-close", "Info Requested": "status-info"}

header = st.columns([1.6, 2.2, 2.6, 1.3, 1.3, 1.5, 1.2])
for col, label in zip(header, ["Case", "Customer", "Alert Type", "Severity", "Status", "Rule(s)", ""]):
    col.markdown(f"**{label}**")

for _, row in filtered.iterrows():
    cols = st.columns([1.6, 2.2, 2.6, 1.3, 1.3, 1.5, 1.2])
    hero_tag = " <span class='hero-badge'>DEMO</span>" if row["has_cache"] else ""
    cols[0].markdown(f"`{row['case_id']}`{hero_tag}", unsafe_allow_html=True)
    cols[1].write(f"{row['customer_name']}")
    cols[2].write(row["alert_type"])
    cols[3].markdown(f"<span class='{sev_class.get(row['severity'],'')}'>{row['severity']}</span>", unsafe_allow_html=True)
    cols[4].markdown(f"<span class='{status_class.get(row['queue_status'],'')}'>{row['queue_status']}</span>", unsafe_allow_html=True)
    cols[5].caption(row["trigger_rule"] or "—")
    if cols[6].button("Investigate →", key=f"inv_{row['case_id']}"):
        st.session_state["selected_case_id"] = row["case_id"]
        st.switch_page("pages/2_Investigation_Demo.py")

if len(filtered) == 0:
    st.info("No alerts match the current filters.")

st.divider()
st.caption(
    "CASE-001 and CASE-002 are the frozen twin-case demo scenario (pre-cached, fully validated — see the CEO "
    "Playbook). Every other case here is a real alert from the same synthetic dataset and can be investigated "
    "live through the same agent, but has not been individually pre-validated — expect Live mode only, no cache. "
    "All data is fictional."
)
