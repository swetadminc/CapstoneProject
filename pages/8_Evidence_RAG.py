"""Read-only, presenter-friendly proof of the synthetic retrieval workflow."""

import inspect
import os
import sqlite3
import sys
from contextlib import closing

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.build_database import chunk_body
from data.knowledge_search import DB_PATH, search
from data.case_evidence import case_evidence_coverage, chunk_source_text, search_case_chunks
from data.fund_flow import case_transactions, case_window_links, trace_transaction
from data.incoming_monitor import detect_pass_through, make_fictional_lab_batch
from data.fictional_intake import (
    assess_fictional_case, fictional_intake_enabled, init_fictional_intake, intake_fictional_batch, make_generated_fictional_batch,
    fictional_intake_path, read_fictional_case, search_fictional_chunks,
)
from agents.evidence_agent import EvidenceAgent
from agents.grounding_validator import GroundingValidator
from ui_common import require_login, page_banner, page_flow

st.set_page_config(page_title="InvestigateIQ — Evidence & RAG", page_icon="🧩", layout="wide")
require_login(allow_guest=True)
page_banner("🧩", "Evidence & RAG", "Inspect fictional case records, their exact chunks, and separately indexed investigation guidance.")
page_flow("Follow a record from source to review", [
    ("Choose a case", "See the customer profile, illustrative identity records, alert and transaction packet."),
    ("Inspect source and chunks", "Compare complete generated text with each exact indexed paragraph."),
    ("Check coverage", "See what is missing, including original documents and independent verification."),
    ("Test and search", "Recalculate a fictional alert, then inspect the separate playbook chunks."),
], "Source-database investigations retrieve case passages and separate playbook guidance through SQLite FTS5; older saved reports may predate the case index. Fictional Intake has its own case-scoped chunk search and calculated review. No vector embeddings are used, and retrieval does not establish lawful funds.")

if not os.path.isfile(DB_PATH):
    st.error("The synthetic knowledge-base database is unavailable.")
    st.stop()

with closing(sqlite3.connect(DB_PATH)) as conn:
    conn.row_factory = sqlite3.Row
    docs = conn.execute(
        "SELECT doc_id, scenario_id, title, escalation_criteria, body, source_file "
        "FROM knowledge_base ORDER BY doc_id"
    ).fetchall()
    total_chunks = conn.execute("SELECT COUNT(*) FROM knowledge_chunks").fetchone()[0]
    case_options = conn.execute(
        "SELECT a.case_id, c.name FROM alerts a JOIN customers c ON c.customer_id=a.customer_id ORDER BY a.case_id"
    ).fetchall()

if not docs:
    st.warning("No synthetic source documents are indexed yet.")
    st.stop()

doc_by_id = {row["doc_id"]: row for row in docs}
st.caption(f"{len(docs)} synthetic source documents · {total_chunks} indexed chunks · SQLite FTS5 keyword retrieval")
st.info("A saved investigation cites a source document ID. That identifies the source playbook, but does not by itself prove which individual chunk supported every sentence. Review the text and original records before relying on a draft.")

query_doc = st.query_params.get("doc")
requested_doc = st.session_state.pop("rag_doc_id", None) or query_doc
if query_doc is not None:
    # A deep link chooses the initial document, but must not override later
    # manual selections on every Streamlit rerun.
    del st.query_params["doc"]
doc_ids = list(doc_by_id)
if requested_doc in doc_by_id:
    st.session_state["rag_doc_choice"] = requested_doc
    st.session_state["rag_view"] = "Source & chunks"
elif st.session_state.get("rag_doc_choice") not in doc_by_id:
    st.session_state["rag_doc_choice"] = doc_ids[0]

def open_chunk(doc_id: str, chunk_id: str) -> None:
    """Move from a search result to its exact in-site source passage."""
    st.session_state["rag_doc_choice"] = doc_id
    st.session_state["rag_chunk_id"] = chunk_id
    st.session_state["rag_view"] = "Source & chunks"


def open_case_chunk(doc_id: str, chunk_id: str) -> None:
    """Keep a selected ledger row linked to its exact case passage on this page."""
    st.session_state["rag_case_doc_id"] = doc_id
    st.session_state["rag_case_chunk_id"] = chunk_id
    st.session_state["rag_view"] = "Case records"


if "rag_view" not in st.session_state:
    st.session_state["rag_view"] = "Case records"
requested_case = st.session_state.pop("rag_case_id", None)
if requested_case:
    st.session_state["rag_case_choice"] = requested_case
    st.session_state["rag_view"] = "Case records"
views = ["Case records", "Rule Lab", "Source & chunks", "Search the index", "Method & code"]
if fictional_intake_enabled():
    views.insert(2, "Fictional Intake")
view = st.segmented_control(
    "Explore evidence", views,
    key="rag_view", required=True,
    help="Switch between original sources, live retrieval results, and the actual implementation without leaving InvestigateIQ.",
)

if view == "Case records":
    labels = {row["case_id"]: f"{row['case_id']} — {row['name']}" for row in case_options}
    if st.session_state.get("rag_case_choice") not in labels:
        st.session_state["rag_case_choice"] = "CASE-043" if "CASE-043" in labels else next(iter(labels))
    case_id = st.selectbox("Case", list(labels), format_func=lambda value: labels[value], key="rag_case_choice")
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        coverage = case_evidence_coverage(conn, case_id)
        matched = conn.execute("SELECT * FROM matched_case_metadata WHERE case_id=?", (case_id,)).fetchone()
        sources = conn.execute(
            "SELECT * FROM case_evidence_sources WHERE customer_id=? AND (case_id IS NULL OR case_id=?) "
            "ORDER BY CASE category WHEN 'kyc_profile' THEN 0 WHEN 'identity_sample' THEN 1 "
            "WHEN 'alert_record' THEN 2 WHEN 'transaction_record' THEN 3 ELSE 4 END, doc_id",
            (coverage["customer_id"], case_id),
        ).fetchall()
    st.info("These records were generated from a fictional workbook or matched-case fixture. Illustrative PAN/Aadhaar/passport/licence text is not an original document or an independent KYC check. The case-document rows contain summaries only.")
    left, right, third, fourth = st.columns(4)
    left.metric("Case source records", len(sources))
    right.metric("Illustrative identity records", coverage["sample_identity_records"])
    third.metric("Original files uploaded", coverage["original_uploaded_files"])
    fourth.metric(
        "Counterparties without customer profile",
        coverage["unknown_counterparty_count"],
        help="Distinct counterparties on completed transaction rows in the ten-day review window with no mapped customer profile here. A profile is not verified KYC; another bank may hold records unavailable to this dataset.",
    )
    with st.expander("Evidence gaps and review boundary", expanded=True):
        for gap in coverage["gaps"]:
            st.warning(gap)
        st.write(coverage["conclusion"])
    if matched:
        with closing(sqlite3.connect(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            test_rows = [dict(row) for row in conn.execute(
                "SELECT * FROM transactions WHERE account_id=(SELECT account_id FROM alerts WHERE case_id=?) "
                "AND date(txn_datetime)='2026-10-01' ORDER BY txn_datetime", (case_id,),
            ).fetchall()]
            beneficiary_dates = {row["account_id"]: row["added_date"] for row in conn.execute(
                "SELECT account_id, added_date FROM matched_case_beneficiaries WHERE case_id=?", (case_id,),
            )}
        detected = detect_pass_through(test_rows, matched["historical_monthly_credit"])
        if detected:
            signal = detected[0]
            st.subheader("Recomputed ten-transaction alert")
            a, b, c, d = st.columns(4)
            a.metric("Incoming", f"₹{signal['incoming']:,.0f}")
            b.metric("Outgoing", f"₹{signal['outgoing']:,.0f}")
            c.metric("Versus monthly baseline", f"{signal['incoming_multiplier']}x")
            d.metric("Beneficiaries", signal["beneficiary_count"])
            st.caption(f"{signal['outbound_percent']}% outgoing/incoming. Both matched cases trigger the same review rule. These figures do not prove that a receipt funded a debit or determine the lawful purpose of funds.")
            with st.expander("Open the complete ten-row timeline and balance arithmetic"):
                running = matched["opening_balance"]
                timeline = []
                for row in test_rows:
                    running += row["amount"] if row["direction"] == "CR" else -row["amount"]
                    timeline.append({
                        "Transaction": row["txn_id"], "Time": row["txn_datetime"],
                        "Direction": row["direction"], "Amount (INR)": row["amount"],
                        "Counterparty": row["counterparty_account_id"],
                        "Beneficiary added": beneficiary_dates.get(row["counterparty_account_id"], "Not recorded"),
                        "Balance after (INR)": running,
                    })
                st.caption(f"Opening balance ₹{matched['opening_balance']:,.0f} is an explicitly fictional fixture assumption, not an uploaded bank statement. All external counterparties have unknown KYC in this dataset.")
                st.dataframe(timeline, hide_index=True)
                st.caption(f"Calculated closing balance ₹{running:,.0f}; fictional fixture expected ₹{matched['balance_after_batch']:,.0f}.")
    with closing(sqlite3.connect(DB_PATH)) as conn:
        transactions = case_transactions(conn, case_id)
        review_links = case_window_links(conn, case_id)
    st.subheader(f"Transaction path · {len(transactions)} recorded rows for this account")
    st.caption("Select any row to inspect its recorded direction, endpoints, KYC fields and possible onward activity. The count covers this account's whole available history, not just the alert window.")
    with st.expander(f"Review-window link register · {len(review_links)} row(s)"):
        st.caption("Every ledger row in the alert's ten-day review window is listed below. A customer ID or dataset KYC field is not proof of verified identity; original files are counted separately. A recorded endpoint does not prove opposite-side posting or onward movement.")
        if review_links:
            st.dataframe([{
                "Transaction": row["transaction_id"], "Time": row["time"],
                "Direction": row["direction"], "Amount (INR)": row["amount_inr"],
                "Source account": row["source_account"] or "Unknown",
                "Source customer": row["source_customer"] or "Not mapped",
                "Source KYC field": row["source_kyc_field"],
                "Source original files": row["source_original_files"],
                "Destination account": row["destination_account"] or "Unknown",
                "Destination customer": row["destination_customer"] or "Not mapped",
                "Destination KYC field": row["destination_kyc_field"],
                "Destination original files": row["destination_original_files"],
                "Link quality": row["link_status"].replace("_", " "),
            } for row in review_links], hide_index=True, height=min(420, 38 * len(review_links) + 45))
        else:
            st.info("No transaction rows fall inside this alert's review window. Nearby rows, if any, are background context only.")
    if transactions:
        transaction_map = {row["txn_id"]: row for row in transactions}
        txn_id = st.selectbox(
            "Transaction", list(transaction_map),
            format_func=lambda key: f"{key} · {transaction_map[key]['txn_datetime']} · {transaction_map[key]['direction']} · INR {transaction_map[key]['amount']:,.0f} · {transaction_map[key]['channel']}",
            help="Choose a transaction ID from the source ledger. Cash deposits have no inferred sender-account link.",
        )
        with closing(sqlite3.connect(DB_PATH)) as conn:
            trace = trace_transaction(conn, txn_id)
            ledger_doc_id = f"CASE-LEDGER-{case_id}"
            ledger_chunk = conn.execute(
                "SELECT chunk_id FROM case_evidence_chunks WHERE doc_id=? AND instr(chunk_text, ?) > 0 "
                "ORDER BY chunk_index LIMIT 1", (ledger_doc_id, txn_id),
            ).fetchone()
        st.caption(f"Record status: {trace['transaction']['status']} · Link quality: {trace['link_status']}")
        if ledger_chunk:
            st.button("Open this transaction's source chunk", key=f"case_txn_chunk_{case_id}_{txn_id}",
                      on_click=open_case_chunk, args=(ledger_doc_id, ledger_chunk[0]),
                      help="Jump to the exact indexed paragraph containing this transaction ID.")
        origin, arrow, target = st.columns([5, 1, 5])
        with origin.container(border=True):
            st.markdown("**Recorded source**")
            st.write(f"{trace['source']['account_id'] or 'Unknown'} · {trace['source']['name']}")
            st.caption(f"Customer: {trace['source']['customer_id'] or 'Unknown'} · Dataset KYC field: {trace['source']['dataset_kyc_status']} · Original identity files: {trace['source']['original_identity_files']}")
        arrow.markdown("### →")
        with target.container(border=True):
            st.markdown("**Recorded destination**")
            st.write(f"{trace['destination']['account_id'] or 'Unknown'} · {trace['destination']['name']}")
            st.caption(f"Customer: {trace['destination']['customer_id'] or 'Unknown'} · Dataset KYC field: {trace['destination']['dataset_kyc_status']} · Original identity files: {trace['destination']['original_identity_files']}")
        st.warning(trace["caveat"])
        if trace["mirror_transaction_id"]:
            st.success(f"Matching opposite-side posting: {trace['mirror_transaction_id']}")
        if trace["onward_candidates"]:
            with st.expander(f"Possible onward activity · {len(trace['onward_candidates'])} row(s)"):
                st.caption(trace["onward_caveat"])
                for onward in trace["onward_candidates"]:
                    st.write(f"{onward['txn_id']} · {onward['txn_datetime']} · INR {onward['amount']:,.0f} → {onward['counterparty_account_id'] or 'unknown endpoint'}")
        else:
            st.caption("No qualifying later outgoing row was found within three days in this dataset.")
    st.divider()
    st.subheader("Document lineage and chunks")
    source_map = {row["doc_id"]: row for row in sources}
    requested_case_doc = st.session_state.pop("rag_case_doc_id", None)
    case_doc_ids = list(source_map)
    selected = st.selectbox(
        "Case source", case_doc_ids,
        index=case_doc_ids.index(requested_case_doc) if requested_case_doc in source_map else 0,
        format_func=lambda key: f"{source_map[key]['document_type']} · {source_map[key]['title']}",
        help="Customer-wide profile and sample identity records appear for every case; case alert, transaction packet and summary rows appear where available.",
    )
    source = source_map[selected]
    st.caption(f"{source['doc_id']} · origin: {source['origin']} · status: {source['verification_status']} · source: {source['source_table']}")
    with st.expander("Source record IDs and content fingerprint"):
        st.code(source["source_record_ids"], language="json")
        st.caption(f"SHA-256 of displayed source text: {source['content_sha256']}")
    with st.expander("Read the complete source text"):
        st.write(source["body"])
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        passages = conn.execute(
            "SELECT chunk_id, chunk_index, chunk_text, word_count FROM case_evidence_chunks "
            "WHERE doc_id=? ORDER BY chunk_index", (selected,),
        ).fetchall()
    st.subheader("Exact indexed chunks")
    st.caption("Each paragraph of the displayed source becomes one ordered chunk. The original text is preserved exactly; this is a lexical FTS5 index, not an embedding store.")
    requested_case_chunk = st.session_state.pop("rag_case_chunk_id", None)
    for passage in passages:
        with st.expander(f"{passage['chunk_id']} · {passage['word_count']} words",
                         expanded=passage["chunk_id"] == requested_case_chunk):
            st.write(passage["chunk_text"])
    st.divider()
    st.subheader("Search this case's indexed records")
    case_query = st.text_input("Keywords", key="case_evidence_search", help="Search source-record chunks for this case and its customer; matching text is shown with its exact source ID.")
    if case_query.strip():
        from data.knowledge_search import _fts_query
        with closing(sqlite3.connect(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            try:
                hits = conn.execute(
                    "SELECT f.chunk_id, f.doc_id, f.chunk_text FROM case_evidence_chunks_fts f "
                    "WHERE case_evidence_chunks_fts MATCH ? AND f.customer_id=? "
                    "AND (f.case_id IS NULL OR f.case_id=?) ORDER BY bm25(case_evidence_chunks_fts) LIMIT 10",
                    (_fts_query(case_query), coverage["customer_id"], case_id),
                ).fetchall()
            except sqlite3.OperationalError:
                hits = []
        if not hits:
            st.write("No matching passage in this case's indexed records.")
        for hit in hits:
            with st.container(border=True):
                st.markdown(f"**{hit['chunk_id']}** · {hit['doc_id']}")
                st.write(hit["chunk_text"])

elif view == "Rule Lab":
    st.subheader("Recalculate a fictional alert")
    st.info("Change the three numbers below. The page generates ten fictional transaction rows in memory and runs the actual 24-hour alert calculation. Nothing is uploaded, saved, added to Case Queue, or sent to a bank.")
    a, b, c = st.columns(3)
    monthly_baseline = a.number_input("Historical monthly credit (INR)", min_value=1, max_value=100_000_000,
                                      value=80_000, step=10_000,
                                      help="Synthetic six-month monthly-credit baseline supplied to the calculation.")
    credit_amount = b.number_input("Each of four incoming transfers (INR)", min_value=1,
                                   max_value=100_000_000, value=300_000, step=10_000,
                                   help="Each generated credit uses this value; no real account is involved.")
    debit_amount = c.number_input("Each of six outgoing transfers (INR)", min_value=1,
                                  max_value=100_000_000, value=180_000, step=10_000,
                                  help="Each generated debit uses this value; beneficiaries are fictional and have unknown KYC.")
    lab_rows = make_fictional_lab_batch(int(credit_amount), int(debit_amount))
    lab_alerts = detect_pass_through(lab_rows, int(monthly_baseline))
    incoming_total = sum(row["amount"] for row in lab_rows if row["direction"] == "CR")
    outgoing_total = sum(row["amount"] for row in lab_rows if row["direction"] == "DR")
    incoming_ratio = incoming_total / monthly_baseline
    outgoing_percent = outgoing_total / incoming_total * 100
    beneficiary_count = len({row["counterparty_account_id"] for row in lab_rows if row["direction"] == "DR"})
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Four credits total", f"₹{incoming_total:,.0f}")
    m2.metric("Six debits total", f"₹{outgoing_total:,.0f}")
    m3.metric("Incoming / monthly baseline", f"{incoming_ratio:.2f}x")
    m4.metric("Outgoing / incoming", f"{outgoing_percent:.1f}%")
    st.dataframe([
        {"Rule check": "Incoming versus monthly baseline", "Observed": f"{incoming_ratio:.2f}x", "Required": "At least 5x", "Result": "Pass" if incoming_ratio >= 5 else "Below threshold"},
        {"Rule check": "Outgoing versus incoming", "Observed": f"{outgoing_percent:.1f}%", "Required": "At least 80%", "Result": "Pass" if outgoing_percent >= 80 else "Below threshold"},
        {"Rule check": "Distinct outgoing beneficiaries", "Observed": str(beneficiary_count), "Required": "At least 3", "Result": "Pass" if beneficiary_count >= 3 else "Below threshold"},
    ], hide_index=True)
    if lab_alerts:
        st.warning("Review signal: the generated rows meet all three illustrative conditions—at least 5x the monthly baseline, at least 80% outgoing/incoming, and at least three distinct beneficiaries inside 24 hours. This is not a fraud or legal finding.")
    else:
        st.success("No review signal under these fixed lab thresholds. This does not establish that the activity is safe or lawful.")
    with st.expander("Inspect all ten generated rows"):
        st.dataframe(lab_rows, hide_index=True)
    st.caption("The six fictional beneficiaries are distinct, have no KYC in this lab, and are not evidence of onward settlement. These fixed test thresholds are separate from the Admin Rule Config preview; neither creates a stored case or connects to a bank feed.")

elif view == "Fictional Intake":
    st.subheader("Create a fictional evidence packet")
    st.info("This course-only intake accepts numeric controls and generates synthetic IDs. It cannot accept names, bank account numbers or uploaded files. A qualifying batch is saved with labeled sample KYC text and exact searchable chunks. It appears in the Case Queue for a separate calculated review, not the six-agent or Gemini path.")
    with st.form("fictional_intake_form"):
        a, b, c = st.columns(3)
        baseline = a.number_input("Intake monthly baseline (INR)", min_value=1, max_value=100_000_000,
                                  value=80_000, step=10_000)
        credit = b.number_input("Intake incoming transfer (INR)", min_value=1, max_value=100_000_000,
                                value=300_000, step=10_000)
        debit = c.number_input("Intake outgoing transfer (INR)", min_value=1, max_value=100_000_000,
                               value=180_000, step=10_000)
        submitted = st.form_submit_button("Calculate and save fictional case")
    intake_path = fictional_intake_path()
    if submitted:
        rows = make_generated_fictional_batch(int(credit), int(debit), int(baseline))
        try:
            with closing(sqlite3.connect(intake_path)) as conn:
                result = intake_fictional_batch(conn, rows, int(baseline))
        except (ValueError, sqlite3.Error) as exc:
            st.error(f"Fictional intake was not saved: {exc}")
        else:
            if result["case_id"]:
                st.session_state["fictional_intake_case_id"] = result["case_id"]
                st.success(f"{'Saved' if result['created'] else 'Already saved'}: {result['case_id']}. This is a review signal, not a fraud finding.")
            else:
                st.info("These rows did not meet the fixed review thresholds, so no case was saved. This does not establish that the activity is lawful.")
    with closing(sqlite3.connect(intake_path)) as conn:
        init_fictional_intake(conn)
        saved_ids = [row[0] for row in conn.execute(
            "SELECT case_id FROM fictional_intake_cases ORDER BY rowid DESC LIMIT 50"
        )]
        if saved_ids:
            chosen = st.selectbox("Saved fictional case", saved_ids,
                                  index=saved_ids.index(st.session_state["fictional_intake_case_id"])
                                  if st.session_state.get("fictional_intake_case_id") in saved_ids else 0)
            packet = read_fictional_case(conn, chosen)
            assessment = assess_fictional_case(conn, chosen)
        else:
            packet = None
    if packet:
        if assessment["review_signal_recomputed"] and assessment["source_integrity_confirmed"]:
            st.info("The saved review signal is reproducible from its stored rows, and the generated source text matches its stored fingerprints and exact chunks. This does not verify identity or lawful funds.")
        else:
            st.error("The saved case failed a calculation or source-integrity check. Do not rely on its draft until the mismatch is reviewed.")
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Stored transactions", len(packet["transactions"]))
        s2.metric("Generated records", len(packet["documents"]))
        s3.metric("Indexed chunks", len(packet["chunks"]))
        s4.metric("Original identity files", packet["original_identity_files"])
        st.caption(assessment["recommended_action"])
        with st.expander(f"Evidence gaps requiring human review · {len(assessment['missing_evidence'])}"):
            for gap in assessment["missing_evidence"]:
                st.warning(gap)
        st.caption("All counterparty profiles and independent source-of-funds documents are missing. The generated PAN/passport references are deliberately invalid and never count as original KYC.")
        with st.expander("Inspect stored transaction rows"):
            st.dataframe(packet["transactions"], hide_index=True, height=350)
        document_by_id = {doc["doc_id"]: doc for doc in packet["documents"]}
        requested_intake_chunk = st.session_state.pop("fictional_intake_chunk_id", None)
        requested_intake_doc = requested_intake_chunk.rsplit("-C", 1)[0] if requested_intake_chunk else None
        document_ids = list(document_by_id)
        doc_id = st.selectbox("Generated source record", document_ids,
                              index=document_ids.index(requested_intake_doc)
                              if requested_intake_doc in document_by_id else 0)
        doc = document_by_id[doc_id]
        st.caption(f"{doc['category']} · {doc['verification_status']} · SHA-256 {doc['content_sha256']}")
        with st.expander("Read full generated source text"):
            st.text(doc["body"])
        chunk_by_id = {chunk["chunk_id"]: chunk for chunk in packet["chunks"]}
        source_chunks = [chunk for chunk in packet["chunks"] if chunk["doc_id"] == doc_id]
        st.caption(f"{len(source_chunks)} exact indexed passage(s) in this source record")
        for chunk in source_chunks:
            with st.expander(f"Passage {chunk['chunk_index'] + 1} · {doc['title']}",
                             expanded=chunk["chunk_id"] == requested_intake_chunk or
                             (requested_intake_chunk is None and chunk["chunk_index"] == 0)):
                st.caption(f"Chunk ID: {chunk['chunk_id']}")
                st.write(chunk["chunk_text"])
        phrase = st.text_input("Search this case's indexed chunks", key=f"fic_chunk_search_{chosen}",
                               help="FTS5 searches only this saved fictional case; a match is not verification.")
        if phrase.strip():
            if not assessment["source_integrity_confirmed"]:
                st.warning("Chunk search is unavailable while this packet fails its source-integrity check.")
            else:
                with closing(sqlite3.connect(intake_path)) as conn:
                    matches = search_fictional_chunks(conn, chosen, phrase)
                if matches:
                    st.caption(f"{len(matches)} matching passage(s) in this fictional case")
                    for index, match in enumerate(matches):
                        source = chunk_by_id[match["chunk_id"]]
                        title = document_by_id[match["doc_id"]]["title"]
                        with st.expander(f"{title} · passage {source['chunk_index'] + 1}",
                                         expanded=index == 0):
                            st.caption(f"Chunk ID: {match['chunk_id']}")
                            st.write(match["chunk_text"])
                else:
                    st.caption("No indexed passage matched this phrase in this case.")
    else:
        st.caption("No fictional intake case has been saved in this isolated store yet.")

elif view == "Source & chunks":
    selected_doc = st.selectbox(
        "Source document", doc_ids, key="rag_doc_choice",
        format_func=lambda doc_id: f"{doc_id} — {doc_by_id[doc_id]['title']}",
        help="Select a synthetic playbook; a citation from an investigation preselects its source.",
    )
    doc = doc_by_id[selected_doc]
    st.caption(f"{doc['doc_id']} · {doc['scenario_id']} · Product Docs/dataset/knowledge_base/{doc['source_file']}")
    st.markdown(f"**Escalation criteria in source:** {doc['escalation_criteria']}")
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        chunks = conn.execute(
            "SELECT chunk_id, chunk_index, chunk_type, word_count, chunk_text "
            "FROM knowledge_chunks WHERE doc_id=? ORDER BY chunk_index", (selected_doc,)
        ).fetchall()

    st.subheader("1 · Original source document")
    with st.expander("Read the complete source text"):
        st.markdown(doc["body"])

    st.subheader("2 · How this document was split")
    st.caption(
        "One metadata chunk holds the title and escalation criteria. The body is split at sentence endings "
        "and grouped into two-sentence chunks. Open any indexed passage below to compare its exact text."
    )
    highlight = st.session_state.pop("rag_chunk_id", None)
    st.write(f"{len(chunks)} indexed chunks in this document")
    for index, chunk in enumerate(chunks):
        preview = " ".join(chunk["chunk_text"].split())[:85]
        label = f"{chunk['chunk_id']} · {chunk['chunk_type']} · {preview}…"
        with st.expander(label, expanded=chunk["chunk_id"] == highlight or (highlight is None and index == 0)):
            if chunk["chunk_id"] == highlight:
                st.success("This is the chunk opened from the investigation or search result.")
            st.caption(f"{chunk['word_count']} words · exact text stored in the retrieval index")
            st.write(chunk["chunk_text"])

elif view == "Search the index":
    st.subheader("3 · Search the index")
    st.caption("SQLite FTS5 matches indexed terms and BM25 ranks the chunks. This is lexical retrieval, not vector or semantic search.")
    query = st.text_input("Question or keywords", placeholder="e.g. structuring cash deposits", help="Run the same retrieval function used by the evidence agent.")
    if query.strip():
        results = search(query, k=5)
        if not results:
            st.warning("No indexed chunks matched those terms. Try a different phrase.")
        for result in results:
            with st.container(border=True):
                st.markdown(f"**{result['chunk_id']}** · {result['doc_id']} · BM25 display score {result['score']}")
                st.write(result["chunk_text"])
                st.button("Open this chunk in its source", key=f"rag_open_{result['chunk_id']}",
                          on_click=open_chunk, args=(result["doc_id"], result["chunk_id"]))

else:
    st.subheader("4 · Inspect the implementation")
    st.write("Open a step to see the actual Python used by this product. The code stays on this site.")
    implementation = [
        ("1 · Calculate a review signal", "data/incoming_monitor.py", "Tests a supplied transaction batch against the illustrative 24-hour thresholds; this is not a live bank feed.", detect_pass_through),
        ("2 · Split guidance", "data/build_database.py", "Groups synthetic playbook sentences into ordered two-sentence chunks.", chunk_body),
        ("3 · Split case records", "data/case_evidence.py", "Preserves each generated record's paragraphs as exact, ordered chunks.", chunk_source_text),
        ("4 · Search case evidence", "data/case_evidence.py", "Restricts keyword retrieval to this case/customer and exposes source and verification status.", search_case_chunks),
        ("5 · Search guidance", "data/knowledge_search.py", "Uses SQLite FTS5 and BM25 to rank playbook passages; no embeddings are used.", search),
        ("6 · Inspect a transaction link", "data/fund_flow.py", "Shows recorded endpoints and KYC gaps without claiming that possible onward activity proves a money trail.", trace_transaction),
        ("7 · Gather context for the draft", "agents/evidence_agent.py", "Combines case passages, playbook guidance and document-summary rows.", EvidenceAgent.run),
        ("8 · Check draft citations", "agents/grounding_validator.py", "Checks selected IDs, references, ratios and unsupported conclusion wording; it cannot prove every sentence.", GroundingValidator.validate),
    ]
    for title, path, explanation, function in implementation:
        with st.expander(title):
            st.write(explanation)
            st.markdown(f"**Source file:** `{path}` · **Function:** `{function.__qualname__}`")
            st.code(inspect.getsource(function), language="python")
st.caption("All source documents and case data shown here are fictional course material. Human review remains necessary.")
