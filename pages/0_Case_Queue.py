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
from ui_common import require_login, page_banner, page_flow, severity_badge, status_badge, render_context_copilot

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
FLASHLIGHT_SVG = (
    '<svg class="iq-flashlight-svg" viewBox="0 0 36 36" width="22" height="22" '
    'fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" '
    'stroke-linejoin="round" focusable="false" aria-hidden="true">'
    '<path d="M4 15.5h14v7H4a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2Z"/>'
    '<path d="m18 14 8-2.5v15L18 24Z"/>'
    '<path d="M29 13.5 33 11M29 19h5M29 24.5l4 2.5"/>'
    '<path d="M7 15.5v7" opacity=".55"/>'
    '</svg>'
)
INFO_SVG = (
    '<svg class="iq-kpi-info-icon" viewBox="0 0 20 20" fill="none" '
    'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" '
    'focusable="false" aria-hidden="true">'
    '<circle cx="10" cy="10" r="8"/><path d="M10 9v5"/>'
    '<circle cx="10" cy="6.2" r="1" fill="currentColor" stroke="none"/>'
    '</svg>'
)
kpis = [
    (FLASHLIGHT_SVG, "Total alerts", len(df), "iq-kpi-blue", "All stored fictional alerts", "Count of all alert rows in this queue, including any saved fictional-intake cases. This is not a live bank feed."),
    ("🕒", "Open", int((df["queue_status"] == "Open").sum()), "iq-kpi-amber", "Awaiting review", "Cases whose current status is Open. An alert is a signal for review, not a fraud finding."),
    ("📨", "Info requested", int((df["queue_status"] == "Info Requested").sum()), "iq-kpi-blue", "Waiting for records", "Cases whose latest recorded human action requested more information. It does not mean the requested documents were received or verified."),
    ("🚨", "Escalated", int((df["queue_status"] == "Escalated").sum()), "iq-kpi-red", "Sent to Compliance queue", "Cases whose latest recorded human action was escalation. No external regulatory report is filed automatically."),
    ("✅", "Human closed", int(df["queue_status"].str.startswith("Closed").sum()), "iq-kpi-green", "Recorded decision", "Cases closed by a recorded human action in this application. A close decision is not proof that funds are lawful."),
    ("🧩", "Demo closed", int((df["queue_status"] == "Demo closed — simulated").sum()), "iq-kpi-green", "Fictional example", "A clearly marked simulated closure with mutually consistent fictional transaction and document-summary rows. No human close action or authentic document is implied."),
    ("📋", "Source closed", int((df["queue_status"] == "Source closed — unverified").sum()), "iq-kpi-amber", "Evidence not established", "Imported alerts labelled closed by the source workbook, without an auditable close action in this application. Most lack case-specific supporting documents; do not treat these as verified legitimate activity."),
    ("🔥", "High severity", int((df["severity"] == "High").sum()), "iq-kpi-red", "Source priority label", "Alerts labelled High in the fictional source data. Severity is independent of case status, so this count overlaps the status cards."),
]
known_status = df["queue_status"].isin(["Open", "Info Requested", "Escalated", "Source closed — unverified", "Demo closed — simulated"]) | df["queue_status"].str.startswith("Closed")
other_status_count = int((~known_status).sum())
if other_status_count:
    kpis.append(("🔄", "Other workflow", other_status_count, "iq-kpi-blue", "Additional review states",
                 "Cases with another recorded workflow status, such as returned to an investigator or referred by Compliance."))
cards = []
for icon, label, value, accent, detail, definition in kpis:
    cards.append(
        f'<div class="iq-card iq-kpi-card {accent}" role="group" '
        f'aria-label="{escape(label)}: {value:,}. {escape(definition)}" title="{escape(definition)}">'
        f'<div class="iq-kpi-top"><span class="iq-kpi-icon" aria-hidden="true">{icon}</span>'
        f'<span class="iq-kpi-help" aria-hidden="true">{INFO_SVG}</span></div>'
        f'<div class="iq-kpi-label">{escape(label)}</div>'
        f'<div class="iq-kpi-value">{value:,}</div>'
        f'<div class="iq-kpi-detail">{escape(detail)}</div></div>'
    )
st.markdown('<div class="iq-kpi-region"><div class="iq-kpi-grid">' + ''.join(cards) + '</div></div>',
            unsafe_allow_html=True)
st.caption("Only recorded human actions count as Human closed. Source-closed cases have not been independently substantiated here. High severity is a separate source label "
           "and can overlap any status. Hover over a card or open the definitions below.")
with st.expander("What these queue numbers mean"):
    for _, label, _, _, _, definition in kpis:
        st.markdown(f"**{label}:** {definition}")

st.divider()

# ------------------------------------------------------------------
# Filters
# ------------------------------------------------------------------
fc1, fc2, fc3, fc4 = st.columns([1.2, 1.2, 1.2, 2])
severity_filter = fc1.multiselect("Severity", sorted(df["severity"].unique()), default=[],
                                  help="The alert priority label supplied by the fictional source data, such as High or Medium. It is not a fraud verdict. Select one or more values, or leave empty to show all.")
status_filter = fc2.multiselect("Status", sorted(df["queue_status"].unique()), default=[],
                                help="Current workflow state. A latest recorded human action overrides the original source status; Info Requested does not mean documents were received, and Escalated does not mean a report was filed.")
scenario_filter = fc3.multiselect("Scenario", sorted(df["scenario_id"].unique()), default=[],
                                  help="The rule or typology identifier attached to the fictional alert, such as rapid movement or structuring. It describes why review was prompted, not a proven crime.")
search = fc4.text_input("Search customer name", placeholder="e.g. Apex",
                        help="Find a stored fictional customer by any part of its name. This does not search transactions, account IDs or external people.")

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
queue_column_widths = [1.6, 2.2, 2.6, 1.3, 1.3, 1.7, 1.6]
header = st.columns(queue_column_widths)
for col, label in zip(header, ["Case", "Customer", "Alert Type", "Severity", "Status", "Rule(s)", "Action"]):
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
    cols = st.columns(queue_column_widths)
    hero_tag = ' <span class="iq-hero-badge">CACHED</span>' if row["has_cache"] else ""
    cols[0].markdown(f'<span class="iq-queue-row"></span><span class="iq-mobile-label">Case: </span>'
                      f'`{row["case_id"]}`{hero_tag}', unsafe_allow_html=True)
    customer_label = escape(str(row["customer_name"]))
    if row["case_id"] in {"CASE-001", "CASE-002"}:
        customer_label += '<br><small>Shared source account · ownership unresolved</small>'
    cols[1].markdown(f'<span class="iq-mobile-label">Customer: </span>{customer_label}',
                      unsafe_allow_html=True)
    cols[2].markdown(f'<span class="iq-mobile-label">Alert type: </span>{escape(str(row["alert_type"]))}',
                      unsafe_allow_html=True)
    cols[3].markdown(f'<span class="iq-mobile-label">Severity: </span>{severity_badge(row["severity"])}',
                      unsafe_allow_html=True)
    cols[4].markdown(f'<span class="iq-mobile-label">Status: </span>{status_badge(row["queue_status"])}',
                      unsafe_allow_html=True)
    rule_text = escape(str(row["trigger_rule"] or "—"))
    cols[5].markdown(f'<span class="iq-mobile-label">Rule(s): </span>'
                     f'<span class="iq-queue-rule" title="{rule_text}" aria-label="{rule_text}">{rule_text}</span>',
                      unsafe_allow_html=True)
    # A short visible label and vector icon make the action recognizable even
    # when the table is narrower; the tooltip names the exact case.
    if cols[6].button("Open", icon=":material/open_in_new:", key=f"inv_{row['case_id']}",
                       help=f"Open {row['case_id']} in the Investigation Workspace to inspect recorded activity, source passages and the human decision form.",
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
render_context_copilot("Case Queue", st.session_state.get("active_case_id"))
