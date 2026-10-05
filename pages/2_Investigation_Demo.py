# -*- coding: utf-8 -*-
"""
Investigation Agent demo — runs the real pipeline (DB -> deterministic
analysis -> RAG retrieval -> Gemini -> Grounding Validator) against a chosen
case, then the shared floating Copilot, a real Human Decision panel, and
a real, persistent Audit Log.

Implements the full Investigation Workspace wireframe (CEO Playbook,
Section 7): full-width evidence with a floating Copilot, the Human Decision
panel, and the persistent Audit Log below.
"""
import json
from html import escape
import os
import sqlite3
import sys
import time
import datetime
from contextlib import closing
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.investigation_agent import investigate, GEMINI_API_KEY, GEMINI_MODEL
from data.case_evidence import case_evidence_index_status
from data.knowledge_search import DB_PATH
from agents.grounding_validator import GroundingValidator
from agents.transaction_investigation_agent import anchor_cached_evidence
from agents.evidence_confidence import calculate_evidence_confidence
from data.runtime_db import record_human_decision, get_audit_log, get_human_actions, log_audit_event
from data.fictional_intake import (
    assess_fictional_case, fictional_intake_enabled, fictional_intake_path, init_fictional_intake,
    list_fictional_cases, read_fictional_case,
)
from ui_common import require_login, page_banner, page_flow, plain_text_html, render_context_copilot
from report_pdf import build_report_pdf

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "cached_reports")


def load_cached(case_id):
    path = os.path.join(CACHE_DIR, f"{case_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def fmt_ts(iso_ts):
    try:
        return datetime.datetime.fromisoformat(iso_ts).strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return iso_ts


ACTION_LABELS = {
    "close": "Close — no concern",
    "request_info": "Request more information",
    "escalate": "Escalate to Compliance",
    "compliance_ack": "Compliance acknowledged — no further action",
    "compliance_return": "Returned to investigator by Compliance",
    "compliance_refer": "Referred onward by Compliance (recorded only)",
}


def show_recorded_action(panel, action_row):
    """Show the stored action, never a draft widget's potentially stale value."""
    label = ACTION_LABELS.get(action_row["action"], action_row["action"])
    panel.success(f"Recorded human action: **{label}**")
    panel.write(f"By: {action_row['investigator']} · {fmt_ts(action_row['timestamp'])}")
    panel.markdown("**Saved rationale**")
    panel.markdown(plain_text_html(action_row["rationale"]), unsafe_allow_html=True)
    panel.caption("This record and its audit entry are read-only. A later workflow step, if allowed, "
                  "creates a separate action; it does not edit this one.")


st.set_page_config(page_title="InvestigateIQ — Investigation Workspace", page_icon="🕵️", layout="wide")
user_name, user_role = require_login()

page_banner("🕵️", "Investigation Workspace",
            "Recorded activity → evidence checks → draft or calculated review → human decision → audit log")
page_flow("Review evidence and make a documented human decision", [
    ("Choose a case", "Select an alert and cached replay or live analysis."),
    ("Review the draft", "Inspect evidence, retrieved guidance and selected validation checks."),
    ("Ask or export", "Question the copilot and download the draft report if useful."),
    ("Decide and audit", "Record a reasoned human decision; inspect the audit history."),
], "The floating Copilot answers bounded case questions from stored rows and exact source chunks. It does not verify outside-bank facts or make the final decision.")
st.markdown(
    """
    <style>
    .status-verified { color: #27844E; font-weight: 600; }
    .status-inferred { color: #6E6E6E; font-weight: 600; }
    .status-missing { color: #B57808; font-weight: 600; }
    .status-conflicting { color: #B02A2A; font-weight: 600; }
    .audit-row { font-family: monospace; font-size: 12.5px; padding: 3px 0; border-bottom: 1px solid var(--iq-card-border); }
    </style>
    """,
    unsafe_allow_html=True,
)
st.write("")

@st.cache_data(ttl=30)
def load_case_options():
    """All available alerts, not just the two hero cases — the queue dashboard can
    send any of them here. Hero cases are pinned to the top and labeled."""
    conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "investigateiq.db"))
    rows = conn.execute("""
        SELECT a.case_id, c.name, a.alert_type, a.status, a.alert_date FROM alerts a
        JOIN customers c ON c.customer_id = a.customer_id
        ORDER BY a.alert_date DESC
    """).fetchall()
    conn.close()
    hero_ids = {"CASE-001", "CASE-002"}
    options = {}
    for cid, name, atype, source_status, alert_date in rows:
        if cid in hero_ids:
            source_label = "Open source alert" if source_status == "Open" else "Source closed, outcome unverified"
            label = (f"{cid} — {source_label} · {alert_date} · {name} "
                     "(shared account; owner ambiguous)")
        else:
            label = f"{cid} — {name}"
        options[label] = cid
    # pin hero cases first
    ordered = {k: v for k, v in options.items() if v in hero_ids}
    ordered.update({k: v for k, v in options.items() if v not in hero_ids})
    return ordered

CASES = dict(load_case_options())
if fictional_intake_enabled():
    with closing(sqlite3.connect(fictional_intake_path())) as intake_conn:
        init_fictional_intake(intake_conn)
        for item in list_fictional_cases(intake_conn):
            CASES[f"{item['case_id']} — generated fictional customer (calculated review)"] = item["case_id"]
labels = list(CASES.keys())

# Keep the selected case stable when another widget (including the floating
# Copilot) reruns this page. A selectbox index that falls back to zero on the
# next run can otherwise disagree with the active Copilot case.
preselect = st.session_state.pop("selected_case_id", None)
if preselect in CASES.values():
    st.session_state["investigation_selected_case_id"] = preselect
    # An explicit queue choice replaces any previous widget selection.
    st.session_state.pop("investigation_case_choice", None)
selected_id = st.session_state.get("investigation_selected_case_id")
default_idx = next((i for i, label in enumerate(labels) if CASES[label] == selected_id), 0)

choice = st.selectbox("Choose a case to investigate", labels, index=default_idx,
                      key="investigation_case_choice",
                      help="Choose one fictional alert. CASE-001 and CASE-002 have older cached comparisons but unresolved account ownership.")
case_id = CASES[choice]
st.session_state["investigation_selected_case_id"] = case_id
st.session_state["active_case_id"] = case_id
render_context_copilot("Investigation Workspace", case_id)
st.markdown(
    f'<div class="iq-workspace-case-badge">Selected case <strong>{escape(case_id)}</strong></div>',
    unsafe_allow_html=True,
)

if not case_id.startswith("FIC-CASE-"):
    with closing(sqlite3.connect(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                         "data", "investigateiq.db"))) as source_conn:
        source_status_row = source_conn.execute(
            "SELECT status FROM alerts WHERE case_id=?", (case_id,)).fetchone()
        case_doc_count = source_conn.execute(
            "SELECT COUNT(*) FROM documents WHERE case_id=?", (case_id,)).fetchone()[0]
    actions = get_human_actions(case_id)
    if source_status_row and source_status_row[0] == "Closed - Simulated Example":
        st.info("Fictional closure example: the linked invoice, service acceptance, supplier receipt, and review worksheet are generated summaries, not authentic files or a recorded human decision. Compare their IDs and amounts with the ledger. This does not establish that funds are lawful.")
    elif (source_status_row and source_status_row[0].startswith("Closed")
            and not (actions and actions[-1]["action"] == "close")):
        st.warning(
            f"Source-closed label, not a verified outcome: the imported alert says '{source_status_row[0]}', "
            f"but no human close action is recorded here. This case has {case_doc_count} case-specific "
            "document summary row(s), not original files. Review the source evidence, account ownership, "
            "and rationale before deciding; this label does not prove the funds were legitimate."
        )

if case_id.startswith("FIC-CASE-"):
    with closing(sqlite3.connect(fictional_intake_path())) as intake_conn:
        packet = read_fictional_case(intake_conn, case_id)
        assessment = assess_fictional_case(intake_conn, case_id)
    st.info("This case came from the feature-gated fictional intake store. The review below recalculates stored rows and checks source integrity; it is not a six-agent or Gemini report, and no original KYC file was uploaded.")
    if assessment["review_signal_recomputed"] and assessment["source_integrity_confirmed"]:
        st.success("The stored alert calculation and generated-source fingerprints/chunks are reproducible.")
    else:
        st.error("A calculation or source-integrity check failed. Resolve this before relying on the packet.")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Completed rows", assessment["observed"]["completed_transaction_rows"],
              help="Completed fictional ledger rows used in the calculated review. Pending entries are excluded from money-movement totals.")
    s2.metric("Incoming (INR)", f"₹{assessment['observed']['incoming_inr']:,.0f}",
              help="Sum of completed incoming rows in this saved fictional packet; not independently verified source of funds.")
    s3.metric("Outgoing (INR)", f"₹{assessment['observed']['outgoing_inr']:,.0f}",
              help="Sum of completed outgoing rows in this packet; this does not prove the same money moved onward.")
    s4.metric("Original identity files", packet["original_identity_files"],
              help="Actual uploaded original identity files in the packet. Generated sample PAN/passport text is not counted.")
    st.caption("Observed amounts come from completed fictional ledger rows. The historical baseline and generated profile are assertions; counterparty KYC, independent source-of-funds records, and settlement proof are absent.")
    with st.expander(f"Recorded transaction rows · {len(packet['transactions'])}"):
        st.dataframe(packet["transactions"], hide_index=True, height=350)
    with st.expander(f"Evidence gaps · {len(assessment['missing_evidence'])}", expanded=True):
        for gap in assessment["missing_evidence"]:
            st.warning(gap)
    st.write(assessment["recommended_action"])
    if st.button("Inspect source records and exact chunks", key=f"fic_evidence_{case_id}",
                 help="Open the stored generated text, each exact indexed passage, and the missing-original evidence checks."):
        st.session_state["fictional_intake_case_id"] = case_id
        st.session_state["rag_view"] = "Fictional Intake"
        st.switch_page("pages/8_Evidence_RAG.py")
    decision_panel = st.container(border=True)
    decision_panel.subheader("Human review action")
    history = get_human_actions(case_id)
    latest = history[-1] if history else None
    if latest:
        show_recorded_action(decision_panel, latest)
    if latest is None or latest["action"] == "compliance_return":
        if latest:
            decision_panel.info("Compliance returned this case. A new investigator action can be "
                                "recorded below; the earlier action remains in the audit history.")
        else:
            decision_panel.caption("After reviewing the Copilot's cited answer, choose the next human action. "
                                   "The Copilot cannot submit a decision. Closing as no concern is unavailable "
                                   "because independent evidence is missing.")
        investigator = decision_panel.text_input("Your name (investigator)", value=user_name,
                                                key=f"fic_investigator_{case_id}",
                                                help="Required display name attached to this new human action; this is not identity authentication.")
        action = decision_panel.radio("Decision", ["Request more information", "Escalate for Compliance review"],
                                      key=f"fic_action_{case_id}",
                                      help="Request missing evidence or send a separate action to Compliance. Neither declares funds illegal or files a report.")
        rationale = decision_panel.text_area("Rationale (required)", key=f"fic_rationale_{case_id}",
                                             help="Write the evidence and gaps behind this action for the audit record.")
        if decision_panel.button("Submit decision", type="primary", key=f"fic_submit_{case_id}",
                                 help="Save a new human action and audit entry; a submitted action cannot be edited here."):
            if not investigator.strip() or not rationale.strip():
                decision_panel.error("A named investigator and written rationale are required.")
            else:
                action_code = "request_info" if action.startswith("Request") else "escalate"
                try:
                    record_human_decision(case_id, investigator.strip(), action_code,
                                          rationale.strip(), findings_accepted=[], findings_rejected=[])
                    st.rerun()
                except ValueError as exc:
                    decision_panel.error(str(exc))
    if history:
        latest_action = history[-1]["action"]
        if latest_action == "request_info":
            decision_panel.info("Latest human action: more information requested. Next: collect and "
                                "verify those records, then return to this case. This does not confirm "
                                "that any documents were received.")
        elif latest_action == "escalate":
            decision_panel.info("Latest human action: escalated. Next: Compliance can review this case "
                                "in the Compliance Queue. No external report has been filed.")
        with st.expander(f"Human action history · {len(history)}"):
            for item in history:
                st.write(f"{item['timestamp']} · {item['action']} · {item['investigator']}")
                st.markdown(plain_text_html(item["rationale"]), unsafe_allow_html=True)
    st.stop()

if st.button("🧩 Inspect this case's KYC, transaction records and chunks",
             help="Open the fictional source records and see the original-document and verification gaps."):
    st.session_state["rag_case_id"] = case_id
    st.switch_page("pages/8_Evidence_RAG.py")

cached = load_cached(case_id)
mode_options = ["Saved report (historical snapshot, no API call)"] if cached else []
mode_options.append("Calculated (current database, no AI call)")
if GEMINI_API_KEY:
    mode_options.append("AI draft (live Gemini call)")
if not cached:
    st.caption(f"No saved report for {case_id}. A current-database calculation is available below.")
mode = st.radio("Mode", mode_options, horizontal=True,
                 help="Saved report replays its historical evidence snapshot; Calculated recomputes the case from current source rows without an AI call; AI draft calls Gemini when configured.")
use_cache = mode.startswith("Saved report")
use_calculated = mode.startswith("Calculated")

if use_cache:
    st.caption(f"Cached report generated {cached['generated_at']} · model `{cached['model']}`")
else:
    st.caption("Current database · rule-based report · no model call" if use_calculated else f"Model: `{GEMINI_MODEL}`")

run = st.button("▶ Run investigation", type="primary",
                help="Build the case draft in the selected mode. Live mode calls Gemini; cached mode replays a saved example.")

# Session state holds the last result per case, so it survives the reruns
# that clicking a checkbox or the decision-submit button triggers — without
# this, every widget interaction would silently re-run (or worse, re-call
# the live API) instead of just updating the page.
state_key = f"result_{case_id}"

if run:
    if use_cache:
        checked_evidence = anchor_cached_evidence(cached["evidence"], cached["context"]["alert"])
        checked_report = GroundingValidator().validate(
            cached["report"], checked_evidence, cached["guidance"]
        )
        result = {"context": cached["context"], "evidence": checked_evidence,
                  "guidance": cached["guidance"], "report": checked_report}
        elapsed = 0.0
        log_audit_event(case_id, actor="system", action="report_replayed_from_cache",
                         details={"cached_at": cached["generated_at"], "model": cached["model"]})
    else:
        with st.spinner(f"Reviewing current records for {case_id}..." if use_calculated else
                        f"Running the full pipeline for {case_id}... (live Gemini call, a few seconds)"):
            t0 = time.time()
            try:
                result = investigate(case_id, draft_mode="calculated" if use_calculated else "model")
            except Exception as e:
                st.error(f"Investigation failed: {e}")
                st.stop()
            elapsed = time.time() - t0
    result["report"]["_evidence_confidence"] = calculate_evidence_confidence(
        result["report"], result["evidence"], result["guidance"]
    )
    st.session_state[state_key] = {"result": result, "elapsed": elapsed,
                                   "use_cache": use_cache, "use_calculated": use_calculated}

if state_key in st.session_state:
    saved = st.session_state[state_key]
    result, elapsed, use_cache = saved["result"], saved["elapsed"], saved["use_cache"]
    context, evidence, guidance, report = result["context"], result["evidence"], result["guidance"], result["report"]

    status_msg = f"Validator result: **{report['_validator_result']}**"
    completion_msg = f"Done in {elapsed:.1f}s. {status_msg}" if not use_cache else status_msg
    if report["_validator_notes"]:
        st.warning(completion_msg)
    else:
        st.success(completion_msg)
    if report["_validator_notes"]:
        with st.expander(f"⚠️ Grounding Validator recorded {len(report['_validator_notes'])} note(s) — review before deciding"):
            for note in report["_validator_notes"]:
                st.write(f"- {note}")
    else:
        st.caption("Grounding Validator: no issues found by its selected checks; human review is still required.")

    confidence = report.get("_evidence_confidence") or calculate_evidence_confidence(report, evidence, guidance)
    with st.container(border=True):
        st.markdown("### 🧭 Evidence confidence")
        st.caption(
            "A transparent, deterministic check of how well this draft is supported by the records supplied to this run."
        )
        confidence_score, confidence_rating, confidence_gaps = st.columns(3)
        confidence_score.metric(
            "Evidence support score", f"{confidence['score']} / 100",
            help="A support-coverage score for this draft, not a risk, fraud, or outcome prediction.",
        )
        confidence_rating.metric("Evidence support", confidence["rating"])
        confidence_gaps.metric("Known limitations", len(confidence["limitations"]))
        st.progress(confidence["score"], text=f"{confidence['rating']} evidence support for this draft")
        st.info(confidence["disclaimer"])
        with st.expander("How this score was calculated"):
            st.caption("The score is a visible rubric, not an opaque model confidence value.")
            for component in confidence["components"]:
                sign = "+" if component["points"] >= 0 else ""
                st.write(
                    f"**{component['label']}: {sign}{component['points']}** "
                    f"of {component['max_points']} — {component['reason']}"
                )
            if confidence["limitations"]:
                st.markdown("**What still needs human review**")
                for limitation in confidence["limitations"]:
                    st.write(f"- {limitation}")

    latest_decision = (get_human_actions(case_id) or [None])[-1]
    pdf_bytes = build_report_pdf(case_id, context, evidence, report, human_action=latest_decision)
    st.download_button(
        "⬇️ Download PDF report", data=pdf_bytes, file_name=f"{case_id}_investigation_report.pdf",
        mime="application/pdf",
        help="Download the draft and any recorded human action for review; this is not a regulatory filing.",
    )

    st.divider()
    st.subheader(f"{context['customer']['name']} — {context['alert']['alert_type']}")
    if context["alert"]["alert_id"].startswith("ALERT-TEST-"):
        st.caption("Calculated fictional test alert · the ten-transaction pattern was evaluated by code at database build time; no external bank feed was received.")
    else:
        st.caption(
            f"Recorded alert rule: {context['alert'].get('trigger_rule') or 'not supplied'} · "
            "this is source-dataset metadata, not a rule result independently recalculated by this screen."
        )
    if not context["alert"].get("trigger_transaction_id"):
        st.warning("This fictional alert has no trigger-transaction ID in the source data. "
                   "Do not treat its recorded rule label as independently verified.")
    if evidence.get("account_ownership_ambiguous"):
        st.error("Source-data collision: this account ID belongs to more than one customer row. The displayed transactions cannot be confidently attributed to this customer; review the source data before making a case decision.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Mixed-ID baseline (unreliable)" if evidence.get("account_ownership_ambiguous") else "Baseline avg. amount",
              f"₹{evidence['baseline_avg_amount']:,.0f}",
              help="This figure cannot be attributed to one customer when the account ID is duplicated in the source workbook. Otherwise it is historical context, not a verdict.")
    c2.metric("Trigger/baseline ratio", f"{evidence['deviation_ratio']}x"
              if evidence["deviation_ratio"] is not None else "-",
              help="Recomputed only when the source alert identifies a trigger transaction; a dash means it cannot be verified here.")
    c3.metric(
        "Nearby transactions (context only)" if evidence.get("evidence_window_empty") else "Transactions in review window",
        len(evidence["window_transactions"]),
        help="Transactions shown for review. When the alert window is empty, these are nearby context, not trigger evidence.",
    )
    c4.metric("Prior cases found", len(evidence["prior_cases"]),
              help="Earlier cases found in this fictional dataset; this does not imply guilt.")
    activity = evidence.get("activity_24h")
    if activity and context["alert"]["alert_id"].startswith("ALERT-TEST-"):
        st.subheader("24-hour alert calculation")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Incoming", f"₹{activity['incoming_total']:,.0f}",
                  help="Completed incoming amount in the calculated 24-hour fictional alert window.")
        m2.metric("Outgoing", f"₹{activity['outgoing_total']:,.0f}",
                  help="Completed outgoing amount in that window; not proof that the same funds were transferred.")
        m3.metric("Versus monthly credits", f"{activity['incoming_monthly_multiplier']}x",
                  help="24-hour incoming total divided by the supplied monthly-credit baseline; an illustrative review ratio, not a risk probability.")
        m4.metric("Outgoing / incoming", f"{activity['outgoing_to_incoming_pct']}%",
                  help="24-hour outgoing total divided by incoming total; an account-level proxy, not linked-hop tracing.")
        st.caption(f"{activity['distinct_beneficiaries']} recorded outgoing beneficiary IDs. {activity['caveat']} The separate trigger/baseline ratio above compares one transaction with average transaction size, not the 24-hour total with monthly credits.")
    if evidence.get("evidence_window_empty"):
        st.caption("⚠️ No transactions fell inside this alert's review window — the transactions shown below "
                   "are the nearest ones in time, for background context only, not the trigger event.")

    st.divider()

    # -------------------------------------------------------------
    # Full-width evidence; case questions use the single floating Copilot.
    # -------------------------------------------------------------
    col_evidence = st.container()

    with col_evidence:
        st.subheader("📋 Evidence & Findings")
        st.page_link("pages/8_Evidence_RAG.py", label="🧩 See how source documents become searchable chunks",
                     help="Open the read-only Evidence & RAG page to inspect document text, chunks, retrieval and code links.")
        case_passages = evidence.get("case_chunks", [])
        with closing(sqlite3.connect(DB_PATH)) as current_conn:
            index_status = case_evidence_index_status(current_conn, case_id)
        if use_cache:
            with st.container(border=True):
                st.markdown("**Saved Report Evidence — snapshot at generation time**")
                st.caption(f"Generated {cached.get('generated_at') or 'at an unrecorded time'} · "
                           f"{len(case_passages)} case passage(s), "
                           f"{len(evidence.get('window_transactions', []))} transaction row(s), "
                           f"{len(evidence.get('documents', []))} document summary record(s), and "
                           f"{len(guidance)} playbook passage(s) captured in this report. "
                           "This count does not describe the current index. "
                           "Historical index snapshot/version: not recorded. The available records "
                           "do not establish when additional current passages became available.")
            st.warning("Saved finding labels and validator checks belong to this historical draft. "
                       "They do not independently verify the alert rule, original KYC, or whether funds are lawful. "
                       "Choose Calculated mode to compare against current stored records.")
        with st.container(border=True):
            st.markdown("**Current Available Evidence — case-scoped index**")
            built_at = index_status["built_at_utc"] or "build time not recorded"
            st.caption(f"{index_status['source_count']} source record(s) · "
                       f"{index_status['chunk_count']} indexed passage(s) · index built {built_at}. "
                       "Indexing is not independent document verification.")
        label = (f"Saved report case passages · {len(case_passages)} captured" if use_cache else
                 f"Current run retrieved case passages · {len(case_passages)}")
        with st.expander(label):
            st.caption("These are passages captured for this report. The current index may differ. "
                       "Retrieval relevance is not verification or a verdict.")
            if not case_passages:
                st.info(("No case passages were captured in this saved report." if use_cache else
                         "This run retrieved no case passages.") +
                        " Open Evidence & RAG to inspect currently indexed case sources and chunks.")
            for passage in case_passages:
                st.markdown(f"**{passage['chunk_id']}** · {passage['verification_status']}")
                st.write(passage["chunk_text"])
                if st.button("Open source and full chunk list", key=f"open_case_chunk_{case_id}_{passage['chunk_id']}",
                             help="Inspect this exact case passage inside its complete stored source record."):
                    st.session_state["rag_case_id"] = case_id
                    st.session_state["rag_case_doc_id"] = passage["doc_id"]
                    st.session_state["rag_case_chunk_id"] = passage["chunk_id"]
                    st.switch_page("pages/8_Evidence_RAG.py")
        status_class = {
            "Verified": "status-verified", "Inferred": "status-inferred",
            "Missing": "status-missing", "Conflicting": "status-conflicting",
        }
        accepted_flags = []
        for i, f in enumerate(report["findings"]):
            with st.container(border=True, key=f"iq_bordered_finding_{case_id}_{i}"):
                cls = status_class.get(f["evidence_status"], "")
                fcols = st.columns([0.1, 0.9])
                accept = fcols[0].checkbox(
                    "Accept", key=f"accept_{case_id}_{i}", value=True, label_visibility="collapsed",
                    help="Include this draft finding among accepted findings when you submit a human decision. Uncheck if you reject it.",
                )
                with fcols[1]:
                    st.markdown(f"**[{f['type'].upper()}]** &nbsp; <span class='{cls}'>{f['evidence_status']}</span>", unsafe_allow_html=True)
                    st.markdown(plain_text_html(f["description"]), unsafe_allow_html=True)
                    st.markdown(plain_text_html(f["why_it_matters"], muted=True), unsafe_allow_html=True)
                    if f.get("supporting_txn_ids"):
                        st.code(", ".join(f["supporting_txn_ids"]), language=None)
                    if f.get("supporting_case_chunk_ids"):
                        st.caption("Case source chunks: " + ", ".join(f["supporting_case_chunk_ids"]))
                accepted_flags.append(accept)

        st.markdown("**Investigation questions**")
        for q in report["investigation_questions"]:
            st.markdown(plain_text_html(f"• {q}"), unsafe_allow_html=True)

        st.markdown("**Recommended next steps** (RAG-grounded — cites a real playbook doc)")
        if report["recommended_next_steps"]:
            for step_index, step in enumerate(report["recommended_next_steps"]):
                st.markdown(plain_text_html(step["step"]), unsafe_allow_html=True)
                st.markdown(plain_text_html(f"Retrieved source: {step['playbook_doc_id']}", muted=True), unsafe_allow_html=True)
                doc_id = step["playbook_doc_id"]
                if st.button(f"View {doc_id} source and all chunks →", key=f"rag_source_{case_id}_{step_index}",
                             help="Inspect the cited synthetic playbook document and every chunk indexed from it."):
                    st.session_state["rag_doc_id"] = doc_id
                    matching_chunk = next((g["chunk_id"] for g in guidance if g.get("doc_id") == doc_id), None)
                    if matching_chunk:
                        st.session_state["rag_chunk_id"] = matching_chunk
                    st.switch_page("pages/8_Evidence_RAG.py")
        else:
            st.caption("No grounded next step available from the knowledge base for this scenario.")

        st.markdown("**Narrative summary**")
        st.markdown(plain_text_html(report["narrative_summary"]), unsafe_allow_html=True)

        with st.expander("Raw evidence passed to the model (for full transparency)"):
            st.json({
                "evidence_window_empty": evidence.get("evidence_window_empty", False),
                "window_transactions": evidence["window_transactions"],
                "relationships": evidence["relationships"],
                "documents": evidence["documents"],
                "knowledge_chunks_retrieved": [g["chunk_id"] for g in guidance],
            })

    # ---------------------------------------------------------
    # The shared floating Copilot is the only case chat.
    # ---------------------------------------------------------

    # -------------------------------------------------------------
    # Human Decision panel — the accountable action. Separate visual
    # treatment from everything above, on purpose: the AI panel is a
    # draft, this is the only place a real decision gets recorded.
    # -------------------------------------------------------------
    st.divider()
    decision_panel = st.container(border=True, key="human_decision_panel")
    decision_panel.subheader("✅ Human Decision")
    decision_panel.caption("This is the accountable action. The AI cannot close, escalate, or file anything on its own (BR1, BR4).")

    history = get_human_actions(case_id)
    latest_action = history[-1] if history else None
    if latest_action:
        show_recorded_action(decision_panel, latest_action)
    if latest_action is None or latest_action["action"] == "compliance_return":
        if latest_action:
            decision_panel.info("Compliance returned this case. Record a new, separate investigator action below; the earlier decision remains unchanged.")
        investigator = decision_panel.text_input(
            "Your name (investigator)", value=user_name, key=f"investigator_{case_id}",
            help="Attributed on this decision in the audit log below — required.",
        )
        action = decision_panel.radio(
            "Decision",
            ["Close — no concern", "Request more information", "Escalate to Compliance"],
            captions=[
                "No further action — findings reviewed and don't warrant escalation.",
                "Not enough evidence either way — flags for follow-up, stays open.",
                "Sends this case to the Compliance Queue for a second review (see BR1: AI never escalates on its own).",
            ],
            key=f"action_{case_id}",
            help="What happens to this case next. This, not the AI's report above, is the decision of record.",
        )
        rationale = decision_panel.text_area(
            "Rationale (required)", key=f"rationale_{case_id}",
            placeholder="Explain the decision — this is required, and it's what gets audited.",
            help="Mandatory (BR4) — a decision can't be recorded without a written reason, regardless of which "
                 "option above is chosen.",
        )
        submit = decision_panel.button("Submit decision", type="primary", key=f"submit_{case_id}",
                            help="Writes this decision to the persistent audit log — cannot be undone from this screen.")

        if submit:
            n_findings = len(report["findings"])
            accepted_idx = [i for i, a in enumerate(accepted_flags) if a]
            rejected_idx = [i for i in range(n_findings) if i not in accepted_idx]
            action_code = {"Close — no concern": "close", "Request more information": "request_info",
                           "Escalate to Compliance": "escalate"}[action]

            if not investigator.strip():
                decision_panel.error("Investigator name is required.")
            elif not rationale.strip():
                decision_panel.error("Rationale is required — a decision cannot be recorded without one (BR4).")
            else:
                try:
                    record_human_decision(
                        case_id=case_id, investigator=investigator.strip(), action=action_code,
                        rationale=rationale.strip(),
                        findings_accepted=[report["findings"][i]["description"] for i in accepted_idx],
                        findings_rejected=[report["findings"][i]["description"] for i in rejected_idx],
                    )
                    st.rerun()
                except Exception as e:
                    decision_panel.error(f"Could not record decision: {e}")

    # -------------------------------------------------------------
    # Audit Log — every AI action and every human decision, in order.
    # Reads from the persistent runtime DB, not from this page's state.
    # -------------------------------------------------------------
    st.divider()
    st.subheader("📜 Audit Log")
    st.caption(f"Persisted on a mounted volume — survives redeploys. case_id: `{case_id}`")

    try:
        audit_rows = get_audit_log(case_id)
    except Exception as e:
        audit_rows = []
        st.error(f"Could not read audit log: {e}")

    if not audit_rows:
        st.caption("No audit events yet for this case.")
    else:
        with st.container(border=True, key=f"iq_bordered_audit_{case_id}"):
            for row in audit_rows:
                actor_label = {"ai": "🤖 AI", "human": "🧑 Human", "system": "⚙️ System"}.get(row["actor"], row["actor"])
                name = f" ({escape(str(row['actor_name']))})" if row.get("actor_name") else ""
                st.markdown(
                    f"<div class='audit-row'>{fmt_ts(row['timestamp'])} &nbsp; "
                    f"<b>{escape(actor_label)}{name}</b> &nbsp; — &nbsp; {escape(str(row['action']))}</div>",
                    unsafe_allow_html=True,
                )
        with st.expander("Full audit detail (JSON)"):
            st.json(audit_rows)

st.divider()
st.caption("All customer/transaction data is fictional.")
