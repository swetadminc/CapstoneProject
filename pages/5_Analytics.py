# -*- coding: utf-8 -*-
"""
Analytics — trends across the alert population and investigator activity.

Turns the Case Queue's flat table into something a team lead or compliance
manager would actually look at: severity/typology/status mix, alert volume
over time, and decision throughput by investigator. Every number here is a
live query against the same two databases every other page reads from
(data/investigateiq.db for alerts, the runtime DB for decisions) — nothing
is precomputed or faked for the chart.
"""
import os
import sys
import sqlite3
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.knowledge_search import DB_PATH
from data.runtime_db import get_all_human_actions
from ui_common import require_login, page_banner

st.set_page_config(page_title="InvestigateIQ — Analytics", page_icon="📊", layout="wide")
user_name, user_role = require_login()

page_banner("📊", "Analytics", "Trends across the alert population and investigator activity")
st.write("")


@st.cache_data(ttl=30)
def load_alerts():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        "SELECT case_id, customer_id, scenario_id, alert_type, severity, status, alert_date "
        "FROM alerts",
        conn,
    )
    conn.close()
    df["alert_date"] = pd.to_datetime(df["alert_date"])
    return df


df = load_alerts()
decisions = pd.DataFrame(get_all_human_actions())

col1, col2 = st.columns(2)
with col1:
    st.subheader("Alerts by severity")
    sev_order = ["High", "Medium", "Low"]
    sev_counts = df["severity"].value_counts().reindex(sev_order).fillna(0).astype(int)
    st.bar_chart(sev_counts, color="#B02A2A")

with col2:
    st.subheader("Alerts by typology")
    scen_counts = df["scenario_id"].value_counts()
    st.bar_chart(scen_counts, color="#2E63BF")

col3, col4 = st.columns(2)
with col3:
    st.subheader("Alerts by current status")
    status_counts = df["status"].value_counts()
    st.bar_chart(status_counts, color="#27844E")

with col4:
    st.subheader("High-severity share by typology")
    high_share = (
        df.assign(is_high=df["severity"] == "High")
        .groupby("scenario_id")["is_high"]
        .mean()
        .mul(100)
        .round(1)
    )
    st.bar_chart(high_share, color="#B57808")
    st.caption("% of that typology's alerts rated High severity")

st.divider()
st.subheader("Alert volume over time")
weekly = df.set_index("alert_date").resample("W").size().rename("alerts")
st.area_chart(weekly, color="#2E63BF")
st.caption(f"Weekly alert volume, {df['alert_date'].min().date()} to {df['alert_date'].max().date()}")

st.divider()
st.subheader("Decisions recorded, by investigator")
if decisions.empty:
    st.info("No decisions have been recorded yet — this fills in as investigators work the queue.")
else:
    by_investigator = decisions["investigator"].value_counts()
    c1, c2 = st.columns([1, 1])
    with c1:
        st.bar_chart(by_investigator, color="#2E63BF")
    with c2:
        st.markdown("**Decision mix**")
        action_labels = {
            "close": "Closed", "escalate": "Escalated", "request_info": "Info Requested",
            "compliance_ack": "Acknowledged", "compliance_return": "Returned to Investigator",
            "compliance_refer": "Referred",
        }
        mix = decisions["action"].map(lambda a: action_labels.get(a, a)).value_counts()
        st.dataframe(mix.rename("count"), use_container_width=True)

st.divider()
st.caption(
    "All figures are live queries against the reference dataset (rebuilt on every deploy) and the persistent "
    "runtime database (decisions/audit log) — nothing on this page is a static mockup. All data is fictional."
)
