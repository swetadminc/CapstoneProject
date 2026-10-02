# -*- coding: utf-8 -*-
"""
Investigation Agent demo — runs the real pipeline (DB -> deterministic
analysis -> RAG retrieval -> Gemini -> Grounding Validator) against a chosen
case, then the Ask-the-Copilot chat panel, a real Human Decision panel, and
a real, persistent Audit Log.

Implements the full Investigation Workspace wireframe (CEO Playbook,
Section 7): the two-panel Evidence/Copilot layout, the Human Decision
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
from agents.chat_agent import ask_question, answer_from_saved_evidence, answer_fictional_case_question
from agents.imported_copilot import answer_imported_case_question
from agents.grounding_validator import GroundingValidator
from agents.transaction_investigation_agent import anchor_cached_evidence
from data.runtime_db import record_human_decision, get_audit_log, get_human_actions, log_audit_event
from data.fictional_intake import (
    assess_fictional_case, fictional_intake_enabled, fictional_intake_path, init_fictional_intake,
    list_fictional_cases, read_fictional_case,
)
from ui_common import require_login, page_banner, page_flow, plain_text_html
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


st.set_page_config(page_title="InvestigateIQ — Investigation Workspace", page_icon="🕵️", layout="wide")
user_name, user_role = require_login()

page_banner("🕵️", "Investigation Workspace",
            "Recorded activity → evidence checks → draft or calculated review → human decision → audit log")
page_flow("Review evidence and make a documented human decision", [
    ("Choose a case", "Select an alert and cached replay or live analysis."),
    ("Review the draft", "Inspect evidence, retrieved guidance and selected validation checks."),
    ("Ask or export", "Question the copilot and download the draft report if useful."),
    ("Decide and audit", "Record a reasoned human decision; inspect the audit history."),
], "Case-scoped database questions, exact source-chunk citations and limited saved-evidence Q&A work without a model connection. Free-form AI chat needs a model key; the copilot never makes the final decision.")
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
        SELECT a.case_id, c.name, a.alert_type FROM alerts a
        JOIN customers c ON c.customer_id = a.customer_id
        ORDER BY a.alert_date DESC
    """).fetchall()
    conn.close()
    hero_ids = {"CASE-001", "CASE-002"}
    options = {}
    for cid, name, atype in rows:
        label = f"{cid} — {name} (older cached comparison; owner ambiguous)" if cid in hero_ids else f"{cid} — {name}"
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

# If the queue dashboard sent us here with a specific case, default to it.
default_idx = 0
preselect = st.session_state.pop("selected_case_id", None)
if preselect:
    for i, label in enumerate(labels):
        if CASES[label] == preselect:
            default_idx = i
            # The queue's explicit choice takes precedence over any earlier
            # selection; subsequent reruns retain the widget's own keyed value.
            st.session_state.pop("investigation_case_choice", None)
            break

choice = st.selectbox("Choose a case to investigate", labels, index=default_idx,
                      key="investigation_case_choice",
                      help="Choose one fictional alert. CASE-001 and CASE-002 have older cached comparisons but unresolved account ownership.")
case_id = CASES[choice]

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
    s1.metric("Completed rows", assessment["observed"]["completed_transaction_rows"])
    s2.metric("Incoming (INR)", f"₹{assessment['observed']['incoming_inr']:,.0f}")
    s3.metric("Outgoing (INR)", f"₹{assessment['observed']['outgoing_inr']:,.0f}")
    s4.metric("Original identity files", packet["original_identity_files"])
    st.caption("Observed amounts come from completed fictional ledger rows. The historical baseline and generated profile are assertions; counterparty KYC, independent source-of-funds records, and settlement proof are absent.")
    with st.expander(f"Recorded transaction rows · {len(packet['transactions'])}"):
        st.dataframe(packet["transactions"], hide_index=True, height=350)
    with st.expander(f"Evidence gaps · {len(assessment['missing_evidence'])}", expanded=True):
        for gap in assessment["missing_evidence"]:
            st.warning(gap)
    st.write(assessment["recommended_action"])
    if st.button("Inspect source records and exact chunks", key=f"fic_evidence_{case_id}"):
        st.session_state["fictional_intake_case_id"] = case_id
        st.session_state["rag_view"] = "Fictional Intake"
        st.switch_page("pages/8_Evidence_RAG.py")
    st.subheader("💬 Ask the Copilot")
    st.caption("Ask about this case in your own words. Answers are calculated from its stored fictional rows; "
               "this is evidence-backed Q&A, not a live AI model or a verdict.")
    chat_key = f"fictional_chat_{case_id}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []
    with st.container(height=600, border=True, key=f"fictional_chat_box_{case_id}"):
        for turn_index, turn in enumerate(st.session_state[chat_key]):
            with st.chat_message(turn["role"]):
                st.markdown(plain_text_html(turn["content"]), unsafe_allow_html=True)
                if turn.get("sources"):
                    st.caption("Stored sources: " + ", ".join(turn["sources"]))
                    if st.button("Inspect cited records and chunks", key=f"fic_chat_sources_{case_id}_{turn_index}"):
                        st.session_state["fictional_intake_case_id"] = case_id
                        st.session_state["rag_view"] = "Fictional Intake"
                        if turn.get("chunk_ids"):
                            st.session_state["fictional_intake_chunk_id"] = turn["chunk_ids"][0]
                        st.switch_page("pages/8_Evidence_RAG.py")
    suggestions = [
        "Show me the transaction sequence: when, from whom, and to whom.",
        "How many transactions are stored in one month, and which need review?",
        "Why did this case trigger review?",
        "What KYC and counterparty evidence is missing?",
        "Can you establish the source of funds?",
        "Can we say the funds are illegal?",
    ]
    suggestion_cols = st.columns(2)
    for index, suggested in enumerate(suggestions):
        if suggestion_cols[index % 2].button(suggested, key=f"fic_question_{case_id}_{index}",
                                             use_container_width=True):
            st.session_state[f"fic_clicked_q_{case_id}"] = suggested
    typed_question = st.chat_input("Ask the copilot about this case...", key=f"fic_chat_input_{case_id}")
    question = st.session_state.pop(f"fic_clicked_q_{case_id}", None) or typed_question
    if question:
        response = answer_fictional_case_question(question, packet, assessment)
        st.session_state[chat_key].append({"role": "user", "content": question})
        st.session_state[chat_key].append({"role": "assistant", "content": response["answer"],
                                           "sources": response["sources"], "chunk_ids": response["chunk_ids"]})
        st.rerun()
    decision_panel = st.container(border=True)
    decision_panel.subheader("Human review action")
    decision_panel.caption("Only a named human can record a follow-up. Closing as no concern is unavailable for this packet because independent evidence is missing.")
    investigator = decision_panel.text_input("Your name (investigator)", value=user_name,
                                            key=f"fic_investigator_{case_id}")
    action = decision_panel.radio("Decision", ["Request more information", "Escalate for Compliance review"],
                                  key=f"fic_action_{case_id}")
    rationale = decision_panel.text_area("Rationale (required)", key=f"fic_rationale_{case_id}")
    if decision_panel.button("Submit decision", type="primary", key=f"fic_submit_{case_id}"):
        if not investigator.strip() or not rationale.strip():
            decision_panel.error("A named investigator and written rationale are required.")
        else:
            action_code = "request_info" if action.startswith("Request") else "escalate"
            record_human_decision(case_id, investigator.strip(), action_code,
                                  rationale.strip(), findings_accepted=[], findings_rejected=[])
            decision_panel.success("Human action and audit entry recorded.")
    history = get_human_actions(case_id)
    if history:
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
mode_options = ["Cached (instant, zero API cost)"] if cached else []
mode_options.append("Calculated (current database, no AI call)")
if GEMINI_API_KEY:
    mode_options.append("AI draft (live Gemini call)")
if not cached:
    st.caption(f"No saved report for {case_id}. A current-database calculation is available below.")
mode = st.radio("Mode", mode_options, horizontal=True,
                 help="Cached replays a saved report; Calculated recomputes the case from source rows without an AI call; AI draft calls Gemini when configured.")
use_cache = mode.startswith("Cached")
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
        m1.metric("Incoming", f"₹{activity['incoming_total']:,.0f}")
        m2.metric("Outgoing", f"₹{activity['outgoing_total']:,.0f}")
        m3.metric("Versus monthly credits", f"{activity['incoming_monthly_multiplier']}x")
        m4.metric("Outgoing / incoming", f"{activity['outgoing_to_incoming_pct']}%")
        st.caption(f"{activity['distinct_beneficiaries']} recorded outgoing beneficiary IDs. {activity['caveat']} The separate trigger/baseline ratio above compares one transaction with average transaction size, not the 24-hour total with monthly credits.")
    if evidence.get("evidence_window_empty"):
        st.caption("⚠️ No transactions fell inside this alert's review window — the transactions shown below "
                   "are the nearest ones in time, for background context only, not the trigger event.")

    st.divider()

    # -------------------------------------------------------------
    # Two-panel layout, matching the original wireframe (CEO Playbook,
    # Section 7): Evidence & Findings on the left, Ask the Copilot on the
    # right. Both are genuinely independent Streamlit columns — verified
    # st.chat_input works correctly inside a column in this Streamlit
    # version before relying on it here.
    # -------------------------------------------------------------
    col_evidence, col_chat = st.columns([1.15, 1])

    with col_evidence:
        st.subheader("📋 Evidence & Findings")
        st.page_link("pages/8_Evidence_RAG.py", label="🧩 See how source documents become searchable chunks",
                     help="Open the read-only Evidence & RAG page to inspect document text, chunks, retrieval and code links.")
        case_passages = evidence.get("case_chunks", [])
        with st.expander(f"Retrieved case passages · {len(case_passages)} indexed chunks"):
            st.caption("FTS5/BM25-selected fictional source passages. Their retrieval score is not a verification or a verdict.")
            for passage in case_passages:
                st.markdown(f"**{passage['chunk_id']}** · {passage['verification_status']}")
                st.write(passage["chunk_text"])
                if st.button("Open source and full chunk list", key=f"open_case_chunk_{case_id}_{passage['chunk_id']}"):
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
    # With a model connection, chat uses a live Gemini call and validates
    # citations. Without one, a limited Q&A reads only the saved report
    # and case evidence; it is explicitly labelled as non-generative.
    # ---------------------------------------------------------
    with col_chat:
        st.subheader("💬 Ask the Copilot")

        chat_key = f"chat_{case_id}"
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []
        chat_history = st.session_state[chat_key]

        offline_qa = not bool(GEMINI_API_KEY)
        if offline_qa:
            st.info("Ask about the selected case's stored transactions, month count, alert and KYC. "
                    "These database answers cite exact source chunks; broader free-form AI needs a model connection.")
        SUGGESTED = [
            "Why was this alert triggered?",
            "How many transactions were stored in one month, which need review, and is KYC verified?",
            "Show me the transaction sequence.",
            "Can you establish the source of funds?",
            "What evidence supports the concern?",
            "What is missing?",
            "What should I do next?",
        ]
        st.caption("Suggested questions:")
        for i, sq in enumerate(SUGGESTED):
            if st.button(sq, key=f"sugg_{case_id}_{i}", use_container_width=True,
                         help="Review an answer based on this case; the live model is used only when configured."):
                st.session_state[f"clicked_q_{case_id}"] = sq

        chat_box = st.container(height=600, border=True, key=f"iq_bordered_chat_{case_id}")
        with chat_box:
            for turn_index, turn in enumerate(chat_history):
                with st.chat_message(turn["role"]):
                    st.markdown(plain_text_html(turn["content"]), unsafe_allow_html=True)
                    if turn.get("source") == "saved_evidence":
                        st.caption("From saved case evidence · no live model call")
                    if turn.get("source") == "imported_case_database":
                        st.caption("From the selected case's stored account rows and exact source chunks · no model call")
                    if turn.get("citations"):
                        st.caption("Sources: " + ", ".join(turn["citations"]))
                    if turn.get("chunk_ids") and st.button(
                        "Inspect cited source chunk", key=f"copilot_chunk_{case_id}_{turn_index}"
                    ):
                        first_chunk = turn["chunk_ids"][0]
                        st.session_state["rag_case_id"] = case_id
                        st.session_state["rag_case_doc_id"] = first_chunk.rsplit("-C", 1)[0]
                        st.session_state["rag_case_chunk_id"] = first_chunk
                        st.switch_page("pages/8_Evidence_RAG.py")
                    if turn.get("validator_notes"):
                        st.caption(f"⚠️ {len(turn['validator_notes'])} citation(s) adjusted by the Grounding Validator")

        if offline_qa:
            st.caption("Review the cited source records before relying on an answer. Saved-evidence Q&A is limited to common case questions.")
        else:
            st.caption("Live model answer: review every cited source record before relying on it. Citation checks do not replace human judgement.")
        typed_question = st.chat_input("Ask a question about this case...")
        question = st.session_state.pop(f"clicked_q_{case_id}", None) or typed_question

        if question:
            chat_history.append({"role": "user", "content": question})
            structured = any(term in question.lower() for term in
                             ("month", "transaction", "trail", "sequence", "kyc", "identity",
                              "suspicious", "flagged", "source of funds", "origin of funds",
                              "counterparty", "counterparties", "how much", "amount",
                              "credit", "debit", "when", "where", "need review"))
            if structured:
                answer = answer_imported_case_question(question, case_id, evidence, report)
            elif offline_qa:
                answer = answer_from_saved_evidence(question, context, evidence, guidance, report)
            else:
                with st.spinner("Thinking... (live Gemini call)"):
                    try:
                        answer = ask_question(case_id, question, chat_history[:-1], context, evidence, guidance)
                    except Exception as e:
                        st.error(f"Could not get an answer: {e}")
                        answer = None
            if answer:
                chat_history.append({
                    "role": "assistant", "content": answer["answer"],
                    "citations": answer["sources"] if "sources" in answer else (
                        answer["cited_txn_ids"] + [f"[{d}]" for d in answer["cited_doc_ids"]]
                        + [f"[{c}]" for c in answer.get("cited_case_chunk_ids", [])]
                    ),
                    "validator_notes": answer.get("validator_notes", []), "source": answer.get("source"),
                    "chunk_ids": answer.get("chunk_ids", answer.get("cited_case_chunk_ids", [])),
                })
            st.rerun()

    # -------------------------------------------------------------
    # Human Decision panel — the accountable action. Separate visual
    # treatment from everything above, on purpose: the AI panel is a
    # draft, this is the only place a real decision gets recorded.
    # -------------------------------------------------------------
    st.divider()
    decision_panel = st.container(border=True, key="human_decision_panel")
    decision_panel.subheader("✅ Human Decision")
    decision_panel.caption("This is the accountable action. The AI cannot close, escalate, or file anything on its own (BR1, BR4).")

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
                decision_panel.success(f"Decision recorded: **{action}** by {investigator}. Written to the audit log below.")
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
