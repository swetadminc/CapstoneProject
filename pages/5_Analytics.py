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
import altair as alt
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.knowledge_search import DB_PATH
from data.runtime_db import get_all_human_actions, get_latest_decision_per_case, resolve_status
from ui_common import require_login, page_banner, page_flow, render_context_copilot

st.set_page_config(page_title="InvestigateIQ — Analytics", page_icon="📊", layout="wide")
user_name, user_role = require_login()
render_context_copilot("Analytics", st.session_state.get("active_case_id"))

page_banner("📊", "Analytics", "Trends across the alert population and investigator activity")
page_flow("Summarize the fictional alert population and recorded human activity", [
    ("Load records", "Read alerts and any saved investigator decisions."),
    ("Compare groups", "View severity, scenario, status and time-based summaries."),
    ("Interpret", "Use patterns to guide review, not to infer model accuracy."),
], "These charts describe fictional records; they do not measure real-world crime-detection performance.")
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
latest_decisions = get_latest_decision_per_case()
df["current_status"] = df.apply(
    lambda row: resolve_status(row["status"], latest_decisions.get(row["case_id"])), axis=1
)


def category_chart(counts: pd.Series, category_title: str, count_title: str,
                   color: str, descriptions: dict[str, str] | None = None):
    """Horizontal count chart with explicit axes, values, and a plain-English hover card."""
    chart_data = counts.rename("count").rename_axis("category").reset_index()
    chart_data["category"] = chart_data["category"].astype(str)
    chart_data["description"] = chart_data["category"].map(descriptions or {}).fillna(
        "A category recorded in the fictional source data; this count is not a finding of wrongdoing."
    )
    y_encoding = alt.Y(
        "category:N",
        title=category_title,
        sort="-x",
        axis=alt.Axis(labelLimit=350, labelFontSize=12, titleFontSize=13, titlePadding=14),
    )
    x_encoding = alt.X(
        "count:Q",
        title=count_title,
        axis=alt.Axis(tickMinStep=1, labelFontSize=12, titleFontSize=13, titlePadding=14),
    )
    bars = (
        alt.Chart(chart_data)
        .mark_bar(color=color, cornerRadiusEnd=5, size=24)
        .encode(
            y=y_encoding,
            x=x_encoding,
            tooltip=[alt.Tooltip("category:N", title=category_title),
                     alt.Tooltip("count:Q", title=count_title, format=",d"),
                     alt.Tooltip("description:N", title="What this means")],
        )
    )
    values = alt.Chart(chart_data).mark_text(
        align="right", baseline="middle", dx=-8, color="#FFFFFF", fontSize=12, fontWeight=700
    ).encode(
        y=alt.Y("category:N", sort="-x"),
        x=alt.X("count:Q"),
        text=alt.Text("count:Q", format=",d"),
    )
    return (bars + values).properties(height=max(170, 48 * len(chart_data)))


def chart_display_name(value: object) -> str:
    """Make an accidental numeric display name understandable in the activity chart."""
    name = str(value or "").strip()
    if not name:
        return "Unnamed reviewer"
    if name.isdigit():
        return f"Demo investigator {name}"
    return name


SCENARIO_DESCRIPTIONS = {
    "amount-anomaly": "Recorded alert category for an amount that needs comparison with the customer's expected activity.",
    "dormant-reactivation": "Recorded alert category for activity after a period of little or no activity.",
    "rapid-movement-of-funds": "Recorded alert category for money moving onward soon after it arrives; the same funds are not proven to have moved.",
    "structuring": "Recorded alert category for a pattern of smaller transactions that needs human review.",
    "velocity": "Recorded alert category for transaction frequency that needs review.",
}

col1, col2 = st.columns(2)
with col1:
    st.subheader("Alerts by severity")
    st.caption("Number of stored alerts in each source severity label. High is a review priority, not a fraud finding.")
    sev_order = ["High", "Medium", "Low"]
    sev_counts = df["severity"].value_counts().reindex(sev_order).fillna(0).astype(int)
    st.altair_chart(category_chart(sev_counts, "Recorded severity", "Number of stored alerts", "#B02A2A"),
                    use_container_width=True)

with col2:
    st.subheader("Alerts by typology")
    st.caption("Each bar counts alerts with that recorded scenario label. Hover over a bar for its full name, count, and meaning.")
    scen_counts = df["scenario_id"].value_counts()
    st.altair_chart(category_chart(scen_counts, "Recorded alert typology", "Number of stored alerts",
                                  "#2E63BF", SCENARIO_DESCRIPTIONS), use_container_width=True)

col3, col4 = st.columns(2)
with col3:
    st.subheader("Alerts by current status")
    st.caption("Latest displayed status for each case. Source-closed, simulated demo closure, and recorded human close are distinct. None proves that funds are lawful.")
    status_counts = df["current_status"].value_counts()
    st.altair_chart(category_chart(status_counts, "Current case status", "Number of cases", "#27844E", {
        "Source closed — unverified": "The imported workbook marked this alert closed, but this application has no recorded investigator close action or complete supporting evidence for that outcome.",
        "Demo closed — simulated": "A fictional example with linked transaction and document-summary rows. It has no authentic original files or recorded human close action.",
        "Closed": "A human close action was recorded here with a rationale; that decision does not prove the funds were lawful.",
    }),
                    use_container_width=True)

with col4:
    st.subheader("High-severity share by typology")
    high_share = (
        df.assign(is_high=df["severity"] == "High")
        .groupby("scenario_id")["is_high"]
        .mean()
        .mul(100)
        .round(1)
    )
    share_data = high_share.rename("share_percent").rename_axis("typology").reset_index()
    st.altair_chart(
        alt.Chart(share_data).mark_bar(color="#B57808", cornerRadiusEnd=5, size=24).encode(
            y=alt.Y("typology:N", title="Recorded alert typology", sort="-x",
                    axis=alt.Axis(labelLimit=350, labelFontSize=12)),
            x=alt.X("share_percent:Q", title="Share labelled High severity (%)", scale=alt.Scale(domain=[0, 100])),
            tooltip=[alt.Tooltip("typology:N", title="Full typology"),
                     alt.Tooltip("share_percent:Q", title="Share labelled High severity", format=".1f")],
        ).properties(height=max(170, 48 * len(share_data))), use_container_width=True,
    )
    st.caption("Percentage of that typology's stored alerts labelled High severity; not the probability of crime.")

st.divider()
st.subheader("Stored alert records by month")
st.caption(
    "Each bar shows how many fictional alert records have a source date in that calendar month. "
    "This describes when records were dated; it is not a fraud trend or a measure of risk."
)
monthly = (
    df.set_index("alert_date")
    .resample("MS")
    .size()
    .rename("alert_count")
    .rename_axis("month")
    .reset_index()
)
monthly["month_label"] = monthly["month"].dt.strftime("%B %Y")
monthly_chart = (
    alt.Chart(monthly)
    .mark_bar(color="#2E63BF", cornerRadiusTopLeft=5, cornerRadiusTopRight=5, size=34)
    .encode(
        x=alt.X(
            "month:T",
            title="Alert month (source date)",
            axis=alt.Axis(format="%b %Y", labelAngle=-35, labelFontSize=12,
                          titleFontSize=13, titlePadding=14),
        ),
        y=alt.Y(
            "alert_count:Q",
            title="Number of stored alerts",
            axis=alt.Axis(tickMinStep=1, labelFontSize=12, titleFontSize=13, titlePadding=14),
        ),
        tooltip=[
            alt.Tooltip("month_label:N", title="Alert month"),
            alt.Tooltip("alert_count:Q", title="Stored alerts", format=",d"),
        ],
    )
    .properties(height=280)
)
monthly_values = alt.Chart(monthly).mark_text(
    baseline="top", dy=6, color="#FFFFFF", fontSize=12, fontWeight=700
).encode(
    x=alt.X("month:T"),
    y=alt.Y("alert_count:Q"),
    text=alt.Text("alert_count:Q", format=",d"),
)
st.altair_chart(monthly_chart + monthly_values, use_container_width=True)
st.caption(
    f"X-axis: calendar month based on the alert source date. Y-axis: number of stored alerts. "
    f"Source dates span {df['alert_date'].min().date()} to {df['alert_date'].max().date()}."
)

st.divider()
st.subheader("Recorded human actions")
if decisions.empty:
    st.info("No decisions have been recorded yet — this fills in as investigators work the queue.")
else:
    decisions["chart_display_name"] = decisions["investigator"].map(chart_display_name)
    by_investigator = decisions["chart_display_name"].value_counts()
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("#### Actions saved by person")
        st.caption(
            "Each bar is one person's saved workflow actions. "
            "Y-axis: investigator or reviewer display name. X-axis: number of saved human actions. "
            "This is not a count of unique cases or a productivity score."
        )
        st.altair_chart(
            category_chart(
                by_investigator,
                "Investigator or reviewer (display name)",
                "Number of saved human actions",
                "#2E63BF",
                {name: "Saved workflow actions attributed to this display name; not a staff-performance rating."
                 for name in by_investigator.index},
            ),
            use_container_width=True,
        )
    with c2:
        st.markdown("#### Actions saved by type")
        st.caption(
            "Each bar groups saved Investigator and Compliance actions by action type. "
            "Y-axis: recorded human action. X-axis: number of saved actions. "
            "One case can have several actions, so these bars are not final case outcomes."
        )
        action_labels = {
            "close": "Closed", "escalate": "Escalated", "request_info": "Info Requested",
            "compliance_ack": "Acknowledged", "compliance_return": "Returned to Investigator",
            "compliance_refer": "Referred",
        }
        mix = decisions["action"].map(lambda a: action_labels.get(a, a)).value_counts()
        st.altair_chart(category_chart(mix, "Recorded human action type", "Number of saved human actions", "#087E74", {
            "Closed": "An investigator recorded a close action with a rationale; this is not proof that funds were lawful.",
            "Escalated": "An investigator sent a case for Compliance review.",
            "Info Requested": "An investigator requested more information before deciding.",
            "Acknowledged": "A Compliance reviewer acknowledged a case already escalated.",
            "Returned to Investigator": "Compliance returned a case for more investigation.",
            "Referred": "Compliance recorded a referral; this app does not submit a regulatory report.",
        }), use_container_width=True)

st.divider()
st.caption(
    "All figures are live queries against the reference dataset (rebuilt on every deploy) and the persistent "
    "runtime database (decisions/audit log) — nothing on this page is a static mockup. All data is fictional."
)
