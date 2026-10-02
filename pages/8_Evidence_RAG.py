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
from data.fund_flow import case_transactions, trace_transaction
from data.incoming_monitor import detect_pass_through
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
    ("Search guidance", "Separately inspect the playbook chunks used by the evidence agent."),
], "Current investigations retrieve both case passages and separate playbook guidance through SQLite FTS5; older saved reports may predate the case index. No vector embeddings are used. Retrieval does not establish lawful funds.")

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
view = st.segmented_control(
    "Explore evidence", ["Case records", "Source & chunks", "Search the index", "Method & code"],
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
    left, right, third = st.columns(3)
    left.metric("Case source records", len(sources))
    right.metric("Illustrative identity records", coverage["sample_identity_records"])
    third.metric("Original files uploaded", coverage["original_uploaded_files"])
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
    st.subheader(f"Transaction path · {len(transactions)} recorded rows for this account")
    st.caption("Select any row to inspect its recorded direction, endpoints, KYC fields and possible onward activity. The count covers this account's whole available history, not just the alert window.")
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
