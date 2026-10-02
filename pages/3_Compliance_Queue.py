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
from contextlib import closing
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.knowledge_search import DB_PATH
from data.fictional_intake import fictional_intake_enabled, fictional_intake_path, init_fictional_intake, list_fictional_cases
from data.runtime_db import get_latest_decision_per_case, get_human_actions, record_human_decision
from ui_common import require_login, role_warning, page_banner, page_flow, plain_text_html

st.set_page_config(page_title="InvestigateIQ — Compliance Queue", page_icon="🛡️", layout="wide")
user_name, user_role = require_login()

page_banner("🛡️", "Compliance / Escalation Queue",
            "Cases an investigator escalated — Compliance reviews, acknowledges, or sends back. Nothing here is filed automatically.")
page_flow("Handle cases an investigator has escalated", [
    ("Open an escalation", "See the case and the investigator's recorded rationale."),
    ("Review the context", "Read the rationale; open the Workspace if you need the evidence."),
    ("Record an action", "Acknowledge, return, or record a referral in the audit trail."),
], "A recorded referral is not a regulatory filing; a human officer remains responsible.")
st.write("")
role_warning(user_role, "Compliance Officer")

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
    context = {r[0]: {"alert_type": r[1], "severity": r[2], "scenario_id": r[3], "customer_name": r[4], "risk_rating": r[5]} for r in rows}
    if fictional_intake_enabled():
        with closing(sqlite3.connect(fictional_intake_path())) as intake_conn:
            init_fictional_intake(intake_conn)
            for item in list_fictional_cases(intake_conn):
                if item["case_id"] in case_ids:
                    context[item["case_id"]] = {
                        "alert_type": "Calculated fictional review signal", "severity": "Review",
                        "scenario_id": "rapid-movement-of-funds",
                        "customer_name": "Generated fictional customer", "risk_rating": "Not assessed",
                    }
    return context


decisions = get_latest_decision_per_case()
escalated = {cid: d for cid, d in decisions.items() if d["action"] == "escalate"}
case_ctx = load_case_context(list(escalated.keys()))

c1, c2 = st.columns(2)
c1.metric("Cases awaiting Compliance review", len(escalated),
          help="Cases whose latest investigator decision is escalation; not a count of regulatory filings.")
c2.metric("High-severity among them", sum(1 for cid in escalated if case_ctx.get(cid, {}).get("severity") == "High"),
          help="Escalated cases marked High severity in the fictional source alerts.")

st.divider()

if not escalated:
    st.info("No cases are currently escalated. Escalate a case from the Investigation Workspace to see it here.")
else:
    for case_id, decision in sorted(escalated.items(), key=lambda kv: kv[1]["timestamp"], reverse=True):
        ctx = case_ctx.get(case_id, {})
        with st.container(border=True, key=f"iq_bordered_escalation_{case_id}"):
            cols = st.columns([2.5, 1.5, 1])
            with cols[0]:
                st.markdown(f"**`{case_id}`** — {ctx.get('customer_name', '?')}")
                st.caption(f"{ctx.get('alert_type', '?')} · severity: {ctx.get('severity', '?')} · scenario: {ctx.get('scenario_id', '?')}")
            with cols[1]:
                st.caption(f"Escalated by **{decision['investigator']}**")
                st.caption(decision["timestamp"][:19].replace("T", " ") + " UTC")
            with cols[2]:
                if st.button("Open case →", key=f"open_{case_id}",
                             help="Open this alert in the Investigation Workspace to review its evidence and decision history."):
                    st.session_state["selected_case_id"] = case_id
                    st.switch_page("pages/2_Investigation_Demo.py")

            # Show the investigator's own rationale for escalating — the
            # thing Compliance is actually being asked to review.
            history = get_human_actions(case_id)
            escalation_entries = [h for h in history if h["action"] == "escalate"]
            if escalation_entries:
                st.markdown("**Investigator's rationale:**")
                st.markdown(plain_text_html(escalation_entries[-1]["rationale"]), unsafe_allow_html=True)

            # Has Compliance already acted on this one?
            compliance_entries = [h for h in history if h["action"].startswith("compliance_")]
            if compliance_entries:
                latest_c = compliance_entries[-1]
                label = {v: k for k, v in COMPLIANCE_ACTIONS.items()}.get(latest_c["action"], latest_c["action"])
                st.success(f"Compliance already acted: **{label}** by {latest_c['investigator']} — \"{latest_c['rationale']}\"")

            with st.expander("Compliance action"):
                officer = st.text_input(
                    "Your name (compliance officer)", value=user_name, key=f"officer_{case_id}",
                    help="Attributed on this action in the audit log below — required.",
                )
                action_label = st.radio(
                    "Action", list(COMPLIANCE_ACTIONS.keys()),
                    captions=[
                        "Escalation reviewed — no further action needed on this case.",
                        "Sends it back to the investigator for more evidence before Compliance can decide.",
                        "Recorded here only — this tool never drafts or files anything with a regulator (see the scope note below).",
                    ],
                    key=f"caction_{case_id}",
                    help="What happens to this escalation next.",
                )
                rationale = st.text_area(
                    "Rationale (required)", key=f"crationale_{case_id}",
                    placeholder="Why this action — this is required and gets audited, same as an investigator decision.",
                    help="Mandatory — same BR4 discipline as an investigator's own decision.",
                )
                if st.button("Submit compliance action", key=f"csubmit_{case_id}", type="primary",
                             help="Writes this action to the persistent audit log — cannot be undone from this screen."):
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


st.divider()
st.caption(
    "Scope note: this screen never drafts or files a regulatory report — that decision and action stay with "
    "Compliance/MLRO outside this tool, per the documented out-of-scope boundary. All data is fictional."
)
