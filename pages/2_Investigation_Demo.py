# -*- coding: utf-8 -*-
"""
Investigation Agent demo — runs the real pipeline (DB -> deterministic
analysis -> RAG retrieval -> Gemini -> Grounding Validator) live against a
chosen case and shows the validated report.

This is a first working slice, not the finished Investigation Workspace UI
from the CEO Playbook (Section 7) — no chat panel, no human decision panel
yet. It exists to prove the pipeline end to end and give the team something
real to demo today while the full workspace is built.
"""
import json
import os
import sys
import time
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.investigation_agent import investigate, GEMINI_API_KEY, GEMINI_MODEL

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "cached_reports")


def load_cached(case_id):
    path = os.path.join(CACHE_DIR, f"{case_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)

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
    </style>
    <div class="iq-banner">
        <h1>🕵️ Investigation Agent — Live Demo</h1>
        <p>Real pipeline: database → deterministic analysis → RAG retrieval → Gemini → Grounding Validator</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")

CASES = {
    "CASE-001 — Apex Global Trading (suspicious)": "CASE-001",
    "CASE-002 — Apex Global Trading (legitimate twin)": "CASE-002",
}
choice = st.selectbox("Choose a case to investigate", list(CASES.keys()))
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

if run:
    if use_cache:
        result = {"context": cached["context"], "evidence": cached["evidence"],
                  "guidance": cached["guidance"], "report": cached["report"]}
        elapsed = 0.0
        st.info("Replaying a cached, previously-validated real run — no API call made just now.")
    else:
        with st.spinner(f"Running the full pipeline for {case_id}... (live Gemini call, a few seconds)"):
            t0 = time.time()
            try:
                result = investigate(case_id)
            except Exception as e:
                st.error(f"Investigation failed: {e}")
                st.stop()
            elapsed = time.time() - t0

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
    for f in report["findings"]:
        with st.container(border=True):
            cls = status_class.get(f["evidence_status"], "")
            st.markdown(f"**[{f['type'].upper()}]** &nbsp; <span class='{cls}'>{f['evidence_status']}</span>", unsafe_allow_html=True)
            st.write(f["description"])
            st.caption(f["why_it_matters"])
            if f.get("supporting_txn_ids"):
                st.code(", ".join(f["supporting_txn_ids"]), language=None)

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

st.divider()
st.caption(
    "This is a first working slice of the Investigation Agent, not the final Investigation Workspace UI "
    "(that's the CEO Playbook, Section 7 build). All customer/transaction data is fictional."
)
