# -*- coding: utf-8 -*-
"""
Investigation Agent demo — runs the real pipeline (DB -> deterministic
analysis -> RAG retrieval -> Gemini -> Grounding Validator) against a chosen
case, then the Ask-the-Copilot chat panel, a real Human Decision panel, and
a real, persistent Audit Log.

This is a first working slice, not the finished Investigation Workspace UI
from the CEO Playbook (Section 7) — no case-queue dashboard yet. It exists
to prove the pipeline end to end, including the human-in-the-loop boundary,
and give the team something real to demo today while the full workspace UI
is built.
"""
import json
import os
import sqlite3
import sys
import time
import datetime
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.investigation_agent import investigate, GEMINI_API_KEY, GEMINI_MODEL
from agents.chat_agent import ask_question
from data.runtime_db import record_human_decision, get_audit_log, get_human_actions, log_audit_event

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


st.set_page_config(page_title="InvestigateIQ — Investigation Demo", page_icon="🕵️", layout="wide")

st.markdown(
    """
    <style>
    .iq-banner { background-color: #1A2A4A; color: white; padding: 14px 22px; border-radius: 10px; }
    .iq-banner h1 { margin: 0; font-size: 22px; }
    .iq-banner p { margin: 2px 0 0 0; color: #C9D6E8; font-size: 13px; }
    .status-verified { color: #27844E; font-weight: 600; }
    .status-inferred { color: #6E6E6E; font-weight: 600; }
    .status-missing { color: #B57808; font-weight: 600; }
    .status-conflicting { color: #B02A2A; font-weight: 600; }
    .decision-box { border: 2px solid #27844E; border-radius: 10px; padding: 16px; background: #F4FBF7; }
    .audit-row { font-family: monospace; font-size: 12.5px; padding: 3px 0; border-bottom: 1px solid #eee; }
    </style>
    <div class="iq-banner">
        <h1>🕵️ Investigation Agent — Live Demo</h1>
        <p>Real pipeline: database → deterministic analysis → RAG retrieval → Gemini → Grounding Validator → human decision → audit log</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")

@st.cache_data(ttl=30)
def load_case_options():
    """All 40 alerts, not just the two hero cases — the queue dashboard can
    send any of them here. Hero cases are pinned to the top and labeled."""
    conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "investigateiq.db"))
    rows = conn.execute("""
        SELECT a.case_id, c.name, a.alert_type FROM alerts a
        JOIN customers c ON c.customer_id = a.customer_id
        ORDER BY a.alert_date DESC
    """).fetchall()
    conn.close()
    hero_ids = {"CASE-001": "suspicious", "CASE-002": "legitimate twin"}
    options = {}
    for cid, name, atype in rows:
        label = f"{cid} — {name} ({hero_ids[cid]}, demo)" if cid in hero_ids else f"{cid} — {name}"
        options[label] = cid
    # pin hero cases first
    ordered = {k: v for k, v in options.items() if v in hero_ids}
    ordered.update({k: v for k, v in options.items() if v not in hero_ids})
    return ordered

CASES = load_case_options()
labels = list(CASES.keys())

# If the queue dashboard sent us here with a specific case, default to it.
default_idx = 0
preselect = st.session_state.pop("selected_case_id", None)
if preselect:
    for i, label in enumerate(labels):
        if CASES[label] == preselect:
            default_idx = i
            break

choice = st.selectbox("Choose a case to investigate", labels, index=default_idx)
case_id = CASES[choice]

cached = load_cached(case_id)
mode_options = ["Cached (instant, zero API cost)", "Live (real Gemini call)"]
if not cached:
    mode_options = ["Live (real Gemini call)"]
    st.warning(f"No cached report found for {case_id} — run `scripts/generate_cached_reports.py` to create one.")
mode = st.radio("Mode", mode_options, horizontal=True,
                 help="Cached replays a pre-validated real run (see CEO Playbook, Section 12 — demo reliability). "
                      "Use Live to prove it's not scripted when asked.")
use_cache = mode.startswith("Cached")

if use_cache:
    st.caption(f"Cached report generated {cached['generated_at']} · model `{cached['model']}`")
else:
    if not GEMINI_API_KEY:
        st.error("GEMINI_API_KEY is not set in this environment. Live mode cannot run.")
        st.stop()
    st.caption(f"Model: `{GEMINI_MODEL}`")

run = st.button("▶ Run investigation", type="primary")

# Session state holds the last result per case, so it survives the reruns
# that clicking a checkbox or the decision-submit button triggers — without
# this, every widget interaction would silently re-run (or worse, re-call
# the live API) instead of just updating the page.
state_key = f"result_{case_id}"

if run:
    if use_cache:
        result = {"context": cached["context"], "evidence": cached["evidence"],
                  "guidance": cached["guidance"], "report": cached["report"]}
        elapsed = 0.0
        log_audit_event(case_id, actor="system", action="report_replayed_from_cache",
                         details={"cached_at": cached["generated_at"], "model": cached["model"]})
    else:
        with st.spinner(f"Running the full pipeline for {case_id}... (live Gemini call, a few seconds)"):
            t0 = time.time()
            try:
                result = investigate(case_id)
            except Exception as e:
                st.error(f"Investigation failed: {e}")
                st.stop()
            elapsed = time.time() - t0
    st.session_state[state_key] = {"result": result, "elapsed": elapsed, "use_cache": use_cache}

if state_key in st.session_state:
    saved = st.session_state[state_key]
    result, elapsed, use_cache = saved["result"], saved["elapsed"], saved["use_cache"]
    context, evidence, guidance, report = result["context"], result["evidence"], result["guidance"], result["report"]

    status_msg = f"Validator result: **{report['_validator_result']}**"
    st.success(f"Done in {elapsed:.1f}s. {status_msg}" if not use_cache else status_msg)
    if report["_validator_notes"]:
        with st.expander(f"⚠️ Grounding Validator made {len(report['_validator_notes'])} correction(s) — click to see what and why"):
            for note in report["_validator_notes"]:
                st.write(f"- {note}")
    else:
        st.caption("Grounding Validator: every citation checked out — no corrections needed.")

    st.divider()
    st.subheader(f"{context['customer']['name']} — {context['alert']['alert_type']}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Baseline avg. amount", f"₹{evidence['baseline_avg_amount']:,.0f}")
    c2.metric("Deviation ratio", f"{evidence['deviation_ratio']}x" if evidence["deviation_ratio"] else "—")
    c3.metric("Transactions in window", len(evidence["window_transactions"]))
    c4.metric("Prior cases found", len(evidence["prior_cases"]))

    st.divider()
    st.subheader("Findings")
    status_class = {
        "Verified": "status-verified", "Inferred": "status-inferred",
        "Missing": "status-missing", "Conflicting": "status-conflicting",
    }
    accepted_flags = []
    for i, f in enumerate(report["findings"]):
        with st.container(border=True):
            cls = status_class.get(f["evidence_status"], "")
            cols = st.columns([0.06, 0.94])
            accept = cols[0].checkbox("Accept", key=f"accept_{case_id}_{i}", value=True, label_visibility="collapsed")
            with cols[1]:
                st.markdown(f"**[{f['type'].upper()}]** &nbsp; <span class='{cls}'>{f['evidence_status']}</span>", unsafe_allow_html=True)
                st.write(f["description"])
                st.caption(f["why_it_matters"])
                if f.get("supporting_txn_ids"):
                    st.code(", ".join(f["supporting_txn_ids"]), language=None)
            accepted_flags.append(accept)

    st.divider()
    st.subheader("Investigation questions")
    for q in report["investigation_questions"]:
        st.write(f"- {q}")

    st.divider()
    st.subheader("Recommended next steps (RAG-grounded — every step cites a real playbook doc)")
    for step in report["recommended_next_steps"]:
        st.markdown(f"- {step['step']}  \n  `[Retrieved: {step['playbook_doc_id']}]`")

    st.divider()
    st.subheader("Narrative summary")
    st.write(report["narrative_summary"])

    with st.expander("Raw evidence passed to the model (for full transparency)"):
        st.json({
            "window_transactions": evidence["window_transactions"],
            "relationships": evidence["relationships"],
            "documents": evidence["documents"],
            "knowledge_chunks_retrieved": [g["chunk_id"] for g in guidance],
        })

    # -------------------------------------------------------------
    # Ask the Copilot — grounded, cited, multi-turn chat over this case's
    # own evidence. Every answer runs through the same citation-checking
    # discipline as the report (agents/chat_agent.py), and every exchange
    # is written to the audit log — this always makes a live Gemini call
    # (there's nothing sensible to "cache" for an arbitrary question).
    # -------------------------------------------------------------
    st.divider()
    st.subheader("💬 Ask the Copilot")

    chat_key = f"chat_{case_id}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []
    chat_history = st.session_state[chat_key]

    if not GEMINI_API_KEY:
        st.info("GEMINI_API_KEY is not set — chat requires a live model call and can't run in this environment.")
    else:
        SUGGESTED = [
            "Why was this alert triggered?",
            "What should I do next?",
            "Has this customer been flagged before?",
            "Who are the counterparties?",
        ]
        st.caption("Suggested questions:")
        sugg_cols = st.columns(len(SUGGESTED))
        clicked_question = None
        for i, sq in enumerate(SUGGESTED):
            if sugg_cols[i].button(sq, key=f"sugg_{case_id}_{i}"):
                clicked_question = sq

        for turn in chat_history:
            with st.chat_message(turn["role"]):
                st.write(turn["content"])
                if turn.get("citations"):
                    st.caption("Sources: " + ", ".join(turn["citations"]))
                if turn.get("validator_notes"):
                    st.caption(f"⚠️ {len(turn['validator_notes'])} citation(s) adjusted by the Grounding Validator")

        typed_question = st.chat_input("Ask a question about this case...")
        question = clicked_question or typed_question

        if question:
            with st.chat_message("user"):
                st.write(question)
            chat_history.append({"role": "user", "content": question})

            with st.chat_message("assistant"):
                with st.spinner("Thinking... (live Gemini call)"):
                    try:
                        answer = ask_question(case_id, question, chat_history[:-1], context, evidence, guidance)
                    except Exception as e:
                        st.error(f"Could not get an answer: {e}")
                        answer = None
                if answer:
                    st.write(answer["answer"])
                    citations = answer["cited_txn_ids"] + [f"[{d}]" for d in answer["cited_doc_ids"]]
                    if citations:
                        st.caption("Sources: " + ", ".join(citations))
                    if answer["validator_notes"]:
                        with st.expander(f"⚠️ {len(answer['validator_notes'])} citation(s) adjusted"):
                            for n in answer["validator_notes"]:
                                st.write(f"- {n}")
            if answer:
                chat_history.append({
                    "role": "assistant", "content": answer["answer"],
                    "citations": answer["cited_txn_ids"] + [f"[{d}]" for d in answer["cited_doc_ids"]],
                    "validator_notes": answer["validator_notes"],
                })
            st.rerun()

    # -------------------------------------------------------------
    # Human Decision panel — the accountable action. Separate visual
    # treatment from everything above, on purpose: the AI panel is a
    # draft, this is the only place a real decision gets recorded.
    # -------------------------------------------------------------
    st.divider()
    st.markdown('<div class="decision-box">', unsafe_allow_html=True)
    st.subheader("✅ Human Decision")
    st.caption("This is the accountable action. The AI cannot close, escalate, or file anything on its own (BR1, BR4).")

    investigator = st.text_input("Your name (investigator)", key=f"investigator_{case_id}")
    action = st.radio(
        "Decision",
        ["Close — no concern", "Request more information", "Escalate to Compliance"],
        key=f"action_{case_id}",
    )
    rationale = st.text_area("Rationale (required)", key=f"rationale_{case_id}",
                              placeholder="Explain the decision — this is required, and it's what gets audited.")
    submit = st.button("Submit decision", type="primary", key=f"submit_{case_id}")

    if submit:
        n_findings = len(report["findings"])
        accepted_idx = [i for i, a in enumerate(accepted_flags) if a]
        rejected_idx = [i for i in range(n_findings) if i not in accepted_idx]
        action_code = {"Close — no concern": "close", "Request more information": "request_info",
                       "Escalate to Compliance": "escalate"}[action]

        if not investigator.strip():
            st.error("Investigator name is required.")
        elif not rationale.strip():
            st.error("Rationale is required — a decision cannot be recorded without one (BR4).")
        else:
            try:
                record_human_decision(
                    case_id=case_id, investigator=investigator.strip(), action=action_code,
                    rationale=rationale.strip(),
                    findings_accepted=[report["findings"][i]["description"] for i in accepted_idx],
                    findings_rejected=[report["findings"][i]["description"] for i in rejected_idx],
                )
                st.success(f"Decision recorded: **{action}** by {investigator}. Written to the audit log below.")
            except Exception as e:
                st.error(f"Could not record decision: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

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
        with st.container(border=True):
            for row in audit_rows:
                actor_label = {"ai": "🤖 AI", "human": "🧑 Human", "system": "⚙️ System"}.get(row["actor"], row["actor"])
                name = f" ({row['actor_name']})" if row.get("actor_name") else ""
                st.markdown(
                    f"<div class='audit-row'>{fmt_ts(row['timestamp'])} &nbsp; "
                    f"<b>{actor_label}{name}</b> &nbsp; — &nbsp; {row['action']}</div>",
                    unsafe_allow_html=True,
                )
        with st.expander("Full audit detail (JSON)"):
            st.json(audit_rows)

st.divider()
st.caption(
    "This is a first working slice of the Investigation Agent, not the final Investigation Workspace UI "
    "(that's the CEO Playbook, Section 7 build). All customer/transaction data is fictional."
)
