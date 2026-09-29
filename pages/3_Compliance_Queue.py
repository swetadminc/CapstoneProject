# -*- coding: utf-8 -*-
"""
Compliance / Escalation Queue — the last named gap from the original
requirements (F9 in the PRD: "Escalated cases appear in a Compliance role
view").

Deliberately narrow scope, matching the documented boundary: Compliance can
acknowledge, return a case to the investigator for more work, or record that
a case was referred onward — the tool drafts nothing and files nothing.
Regulatory reporting stays explicitly out of scope (CEO Playbook, PRD
out-of-scope list), same as everywhere else in this build.
"""
import os
import sys
import sqlite3
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.knowledge_search import DB_PATH
from data.runtime_db import get_latest_decision_per_case, get_human_actions, record_human_decision

st.set_page_config(page_title="InvestigateIQ — Compliance Queue", page_icon="🛡️", layout="wide")

st.markdown(
    """
    <style>
    .iq-banner { background-color: #1A2A4A; color: white; padding: 14px 22px; border-radius: 10px; }
    .iq-banner h1 { margin: 0; font-size: 22px; }
    .iq-banner p { margin: 2px 0 0 0; color: #C9D6E8; font-size: 13px; }
    .esc-card { border: 2px solid #B02A2A; border-radius: 10px; padding: 14px 18px; margin-bottom: 10px; background: #FFF9F9; }
    </style>
    <div class="iq-banner">
        <h1>🛡️ Compliance / Escalation Queue</h1>
        <p>Cases an investigator escalated — Compliance reviews, acknowledges, or sends back. Nothing here is filed automatically.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")

COMPLIANCE_ACTIONS = {
    "Acknowledge — no further action": "compliance_ack",
    "Return to investigator for more information": "compliance_return",
    "Referred onward (recorded only — not filed by this tool)": "compliance_refer",
}


@st.cache_data(ttl=15)
def load_case_context(case_ids):
    if not case_ids:
        return {}
    conn = sqlite3.connect(DB_PATH)
    placeholders = ",".join("?" * len(case_ids))
    rows = conn.execute(f"""
        SELECT a.case_id, a.alert_type, a.severity, a.scenario_id, c.name AS customer_name, c.risk_rating
        FROM alerts a JOIN customers c ON c.customer_id = a.customer_id
        WHERE a.case_id IN ({placeholders})
    """, case_ids).fetchall()
    conn.close()
    return {r[0]: {"alert_type": r[1], "severity": r[2], "scenario_id": r[3], "customer_name": r[4], "risk_rating": r[5]} for r in rows}


decisions = get_latest_decision_per_case()
escalated = {cid: d for cid, d in decisions.items() if d["action"] == "escalate"}
case_ctx = load_case_context(list(escalated.keys()))

c1, c2 = st.columns(2)
c1.metric("Cases awaiting Compliance review", len(escalated))
c2.metric("High-severity among them", sum(1 for cid in escalated if case_ctx.get(cid, {}).get("severity") == "High"))

st.divider()

if not escalated:
    st.info("No cases are currently escalated. Escalate a case from the Investigation Workspace to see it here.")
else:
    for case_id, decision in sorted(escalated.items(), key=lambda kv: kv[1]["timestamp"], reverse=True):
        ctx = case_ctx.get(case_id, {})
        with st.container():
            st.markdown('<div class="esc-card">', unsafe_allow_html=True)
            cols = st.columns([2.5, 1.5, 1])
            with cols[0]:
                st.markdown(f"**`{case_id}`** — {ctx.get('customer_name', '?')}")
                st.caption(f"{ctx.get('alert_type', '?')} · severity: {ctx.get('severity', '?')} · scenario: {ctx.get('scenario_id', '?')}")
            with cols[1]:
                st.caption(f"Escalated by **{decision['investigator']}**")
                st.caption(decision["timestamp"][:19].replace("T", " ") + " UTC")
            with cols[2]:
                if st.button("Open case →", key=f"open_{case_id}"):
                    st.session_state["selected_case_id"] = case_id
                    st.switch_page("pages/2_Investigation_Demo.py")

            # Show the investigator's own rationale for escalating — the
            # thing Compliance is actually being asked to review.
            history = get_human_actions(case_id)
            escalation_entries = [h for h in history if h["action"] == "escalate"]
            if escalation_entries:
                st.markdown(f"**Investigator's rationale:** {escalation_entries[-1]['rationale']}")

            # Has Compliance already acted on this one?
            compliance_entries = [h for h in history if h["action"].startswith("compliance_")]
            if compliance_entries:
                latest_c = compliance_entries[-1]
                label = {v: k for k, v in COMPLIANCE_ACTIONS.items()}.get(latest_c["action"], latest_c["action"])
                st.success(f"Compliance already acted: **{label}** by {latest_c['investigator']} — \"{latest_c['rationale']}\"")

            with st.expander("Compliance action"):
                officer = st.text_input("Your name (compliance officer)", key=f"officer_{case_id}")
                action_label = st.radio("Action", list(COMPLIANCE_ACTIONS.keys()), key=f"caction_{case_id}")
                rationale = st.text_area("Rationale (required)", key=f"crationale_{case_id}",
                                          placeholder="Why this action — this is required and gets audited, same as an investigator decision.")
                if st.button("Submit compliance action", key=f"csubmit_{case_id}", type="primary"):
                    if not officer.strip():
                        st.error("Your name is required.")
                    elif not rationale.strip():
                        st.error("Rationale is required.")
                    else:
                        try:
                            record_human_decision(
                                case_id=case_id, investigator=officer.strip(),
                                action=COMPLIANCE_ACTIONS[action_label], rationale=rationale.strip(),
                                findings_accepted=[], findings_rejected=[],
                            )
                            st.success("Recorded. Refresh to see it reflected above.")
                            st.cache_data.clear()
                        except Exception as e:
                            st.error(f"Could not record: {e}")

            st.markdown("</div>", unsafe_allow_html=True)

st.divider()
st.caption(
    "Scope note: this screen never drafts or files a regulatory report — that decision and action stay with "
    "Compliance/MLRO outside this tool, per the documented out-of-scope boundary. All data is fictional."
)
