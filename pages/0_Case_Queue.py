# -*- coding: utf-8 -*-
"""
Case Queue Dashboard — Screen 2 from the UI wireframe (Product Docs,
09-UI-Wireframes-and-Screen-Designs.md), built for real.

The conceptual landing page of the actual product: every open alert from
the (mock) monitoring system, filterable, with a live decision status pulled
from the persistent audit trail — not a static mockup image.

CASE-001 and CASE-002 have older saved reports. Forty-two fictional alerts
come from a workbook; CASE-043/044 are calculated from fictional matched-case
transaction fixtures. None is a live third-party bank alert.
"""
import os
import sys
import sqlite3
from html import escape
from contextlib import closing
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.knowledge_search import DB_PATH
from data.fictional_intake import fictional_intake_enabled, fictional_intake_path, init_fictional_intake, list_fictional_cases
from data.runtime_db import get_latest_decision_per_case, resolve_status
from ui_common import require_login, page_banner, page_flow, severity_badge, status_badge

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "cached_reports")
CACHED_CASES = {name[:-5] for name in os.listdir(CACHE_DIR) if name.endswith(".json")}

st.set_page_config(page_title="InvestigateIQ — Case Queue", page_icon="🗂️", layout="wide")
user_name, user_role = require_login()

page_banner("🗂️", "Case Queue", "Fictional monitoring alerts — filter, review, and open a case to investigate")
page_flow("Find a fictional alert that needs an investigator's review", [
    ("Scan alerts", "See case counts, severity and current status."),
    ("Filter the queue", "Narrow by the fields shown below."),
    ("Open a case", "Move to the Investigation Workspace for evidence and a human decision."),
], "The queue combines fictional workbook alerts and two calculated test alerts; it does not receive live bank messages.")
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
if fictional_intake_enabled():
    with closing(sqlite3.connect(fictional_intake_path())) as intake_conn:
        init_fictional_intake(intake_conn)
        intake_cases = list_fictional_cases(intake_conn)
    if intake_cases:
        intake_df = pd.DataFrame([{
            "alert_id": f"FIC-ALERT-{case['case_id']}",
            "case_id": case["case_id"], "customer_id": case["customer_id"],
            "account_id": case["account_id"],
            "alert_type": "Calculated fictional review signal",
            "scenario_id": "rapid-movement-of-funds",
            "trigger_rule": "Calculated: 24h / 5x / 80% / 3 beneficiaries",
            "alert_date": case["alert_date"], "severity": "Review",
            "status": "Open", "customer_name": "Generated fictional customer",
            "customer_type": "Fictional", "risk_rating": "Not assessed",
        } for case in intake_cases])
        df = pd.concat([intake_df, df], ignore_index=True)
decisions = get_latest_decision_per_case()
df["queue_status"] = df.apply(lambda row: resolve_status(row["status"], decisions.get(row["case_id"])), axis=1)
df["has_cache"] = df["case_id"].isin(CACHED_CASES)

# ------------------------------------------------------------------
# KPI strip
# ------------------------------------------------------------------
kpis = [
    ("📊", "Total alerts", len(df), "iq-kpi-blue"),
    ("🕒", "Open", int((df["queue_status"] == "Open").sum()), "iq-kpi-amber"),
    ("🔥", "High severity", int((df["severity"] == "High").sum()), "iq-kpi-red"),
    ("🚨", "Escalated", int((df["queue_status"] == "Escalated").sum()), "iq-kpi-red"),
    ("✅", "Closed", int((df["queue_status"] == "Closed").sum()), "iq-kpi-green"),
]
for col, (icon, label, value, accent) in zip(st.columns(5), kpis):
    col.markdown(
        f'<div class="iq-card {accent}"><div class="iq-kpi-icon">{icon}</div>'
        f'<div class="iq-kpi-label">{label}</div><div class="iq-kpi-value">{value:,}</div></div>',
        unsafe_allow_html=True,
    )

st.divider()

# ------------------------------------------------------------------
# Filters
# ------------------------------------------------------------------
fc1, fc2, fc3, fc4 = st.columns([1.2, 1.2, 1.2, 2])
severity_filter = fc1.multiselect("Severity", sorted(df["severity"].unique()), default=[],
                                  help="Show alerts with any selected severity; leave empty to show all.")
status_filter = fc2.multiselect("Status", sorted(df["queue_status"].unique()), default=[],
                                help="Current case status includes any recorded human decision.")
scenario_filter = fc3.multiselect("Scenario", sorted(df["scenario_id"].unique()), default=[],
                                  help="Filter by the fictional scenario ID attached to each alert.")
search = fc4.text_input("Search customer name", placeholder="e.g. Apex",
                        help="Matches part of a customer name, ignoring letter case.")

filtered = df.copy()
if severity_filter:
    filtered = filtered[filtered["severity"].isin(severity_filter)]
if status_filter:
    filtered = filtered[filtered["queue_status"].isin(status_filter)]
if scenario_filter:
    filtered = filtered[filtered["scenario_id"].isin(scenario_filter)]
if search:
    filtered = filtered[filtered["customer_name"].str.contains(search, case=False, na=False, regex=False)]

st.caption(f"Showing {len(filtered)} of {len(df)} alerts")

# ------------------------------------------------------------------
# Queue table
# ------------------------------------------------------------------
header = st.columns([1.6, 2.2, 2.6, 1.3, 1.3, 1.5, 1.2])
for col, label in zip(header, ["Case", "Customer", "Alert Type", "Severity", "Status", "Rule(s)", ""]):
    col.markdown(f'<span class="iq-queue-header"><strong>{label}</strong></span>', unsafe_allow_html=True)
st.markdown('<hr style="margin: 4px 0 8px 0; border-color: var(--iq-card-border);">', unsafe_allow_html=True)

# On a narrow viewport, Streamlit stacks these columns vertically on its
# own — but with the header row hidden at that same breakpoint (see
# ui_common.py), a bare "Coastal Wholesale Traders" or "Structuring -
# multiple transactions..." stacked in a long list with no header above
# it doesn't say what it IS. .iq-mobile-label prefixes are invisible on
# desktop (redundant next to the real header) and only appear once
# stacked.
for _, row in filtered.iterrows():
    cols = st.columns([1.6, 2.2, 2.6, 1.3, 1.3, 1.5, 1.2])
    hero_tag = ' <span class="iq-hero-badge">CACHED</span>' if row["has_cache"] else ""
    cols[0].markdown(f'<span class="iq-queue-row"></span><span class="iq-mobile-label">Case: </span>'
                      f'`{row["case_id"]}`{hero_tag}', unsafe_allow_html=True)
    cols[1].markdown(f'<span class="iq-mobile-label">Customer: </span>{escape(str(row["customer_name"]))}',
                      unsafe_allow_html=True)
    cols[2].markdown(f'<span class="iq-mobile-label">Alert type: </span>{escape(str(row["alert_type"]))}',
                      unsafe_allow_html=True)
    cols[3].markdown(f'<span class="iq-mobile-label">Severity: </span>{severity_badge(row["severity"])}',
                      unsafe_allow_html=True)
    cols[4].markdown(f'<span class="iq-mobile-label">Status: </span>{status_badge(row["queue_status"])}',
                      unsafe_allow_html=True)
    cols[5].markdown(f'<span class="iq-mobile-label">Rule(s): </span>{escape(str(row["trigger_rule"] or "—"))}',
                      unsafe_allow_html=True)
    # A full "Investigate →" label doesn't fit this column at most viewport
    # widths and silently truncates to "I.." — an icon-only button with a
    # real Streamlit tooltip (the `help` kwarg) says the same thing without
    # needing the space, and names the actual case rather than a generic
    # label.
    if cols[6].button("🔍", key=f"inv_{row['case_id']}", help=f"Investigate {row['case_id']}",
                       use_container_width=True):
        st.session_state["selected_case_id"] = row["case_id"]
        st.switch_page("pages/2_Investigation_Demo.py")

if len(filtered) == 0:
    st.info("No alerts match the current filters.")

st.divider()
st.caption(
    "CASE-001 and CASE-002 have older saved comparison reports. CASE-043 and CASE-044 were calculated "
    "from fictional matched-case transaction rows. Feature-gated FIC cases are calculated from newly entered numeric examples and use a separate source-integrity review. Other cases can use the six-stage investigation workflow; "
    "but not all have been individually reviewed; use Calculated mode when no saved report or model is available. "
    "All data is fictional."
)
