"""Read-only, presenter-friendly proof of the synthetic retrieval workflow."""

import os
import sqlite3
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.knowledge_search import DB_PATH, search
from ui_common import require_login, page_banner, page_flow

REPO = "https://github.com/swetadminc/CapstoneProject/blob/main"

st.set_page_config(page_title="InvestigateIQ — Evidence & RAG", page_icon="🧩", layout="wide")
require_login(allow_guest=True)
page_banner("🧩", "Evidence & RAG", "Trace a saved recommendation back to its synthetic source document and searchable chunks.")
page_flow("Show how source guidance becomes retrievable evidence", [
    ("Open a source", "Choose a synthetic playbook document or follow a citation from an investigation."),
    ("Inspect chunks", "Compare the original body with the metadata and two-sentence body chunks."),
    ("Try retrieval", "Search the same SQLite FTS5 index used by the evidence agent."),
    ("Inspect the code", "Follow links to the chunking, retrieval and citation-checking implementation."),
], "This page shows retrieval provenance, not proof that every AI-generated sentence is correct. No vector embeddings are used.")

if not os.path.isfile(DB_PATH):
    st.error("The synthetic knowledge-base database is unavailable.")
    st.stop()

with sqlite3.connect(DB_PATH) as conn:
    conn.row_factory = sqlite3.Row
    docs = conn.execute(
        "SELECT doc_id, scenario_id, title, escalation_criteria, body, source_file "
        "FROM knowledge_base ORDER BY doc_id"
    ).fetchall()
    total_chunks = conn.execute("SELECT COUNT(*) FROM knowledge_chunks").fetchone()[0]

if not docs:
    st.warning("No synthetic source documents are indexed yet.")
    st.stop()

doc_by_id = {row["doc_id"]: row for row in docs}
st.caption(f"{len(docs)} synthetic source documents · {total_chunks} indexed chunks · SQLite FTS5 keyword retrieval")
st.info("A saved investigation cites a source document ID. That identifies the source playbook, but does not by itself prove which individual chunk supported every sentence. Review the text and original records before relying on a draft.")

requested_doc = st.session_state.pop("rag_doc_id", None) or st.query_params.get("doc")
doc_ids = list(doc_by_id)
if requested_doc in doc_by_id:
    st.session_state["rag_doc_choice"] = requested_doc
elif st.session_state.get("rag_doc_choice") not in doc_by_id:
    st.session_state["rag_doc_choice"] = doc_ids[0]
selected_doc = st.selectbox(
    "Source document", doc_ids, key="rag_doc_choice",
    format_func=lambda doc_id: f"{doc_id} — {doc_by_id[doc_id]['title']}",
    help="Select any synthetic playbook document; citations from an investigation preselect the source.",
)
doc = doc_by_id[selected_doc]

st.subheader("1 · Original source document")
st.caption(f"{doc['doc_id']} · scenario: {doc['scenario_id']} · source file: Product Docs/dataset/knowledge_base/{doc['source_file']}")
st.markdown(f"**Escalation criteria in source:** {doc['escalation_criteria']}")
with st.container(border=True):
    st.markdown(doc["body"])

st.subheader("2 · How this document was split")
st.write(
    "The builder makes one metadata chunk from the title and escalation criteria. "
    "It then splits the body at sentence-ending punctuation and groups two sentences per body chunk. "
    "Small passages make a retrieved result easier to inspect than a whole-document match."
)
with sqlite3.connect(DB_PATH) as conn:
    conn.row_factory = sqlite3.Row
    chunks = conn.execute(
        "SELECT chunk_id, chunk_index, chunk_type, word_count, chunk_text "
        "FROM knowledge_chunks WHERE doc_id=? ORDER BY chunk_index", (selected_doc,)
    ).fetchall()

highlight = st.session_state.pop("rag_chunk_id", None)
st.caption(f"{len(chunks)} chunks for this document. Each card shows the exact text stored in the retrieval index.")
for chunk in chunks:
    with st.container(border=True):
        label = f"{chunk['chunk_id']} · {chunk['chunk_type']} · {chunk['word_count']} words"
        if chunk["chunk_id"] == highlight:
            st.success(f"Retrieved for the selected investigation: {label}")
        else:
            st.markdown(f"**{label}**")
        st.write(chunk["chunk_text"])

st.subheader("3 · Search the index")
st.caption("This is lexical RAG retrieval: SQLite FTS5 matches indexed terms and BM25 ranks the matching chunks. It is not vector or semantic search.")
query = st.text_input("Question or keywords", placeholder="e.g. structuring cash deposits", help="Run the same retrieval function used by the evidence agent.")
if query.strip():
    results = search(query, k=5)
    if not results:
        st.warning("No indexed chunks matched those terms. Try a different phrase.")
    for result in results:
        with st.container(border=True):
            st.markdown(f"**{result['chunk_id']}** · {result['doc_id']} · BM25 display score {result['score']}")
            st.write(result["chunk_text"])

st.subheader("4 · Inspect the implementation")
st.write("These files show the exact source-to-chunk, retrieval and report-checking steps behind this page.")
links = [
    ("Chunk builder", "data/build_database.py"),
    ("FTS5 retrieval", "data/knowledge_search.py"),
    ("Evidence agent", "agents/evidence_agent.py"),
    ("Grounding checks", "agents/grounding_validator.py"),
]
for label, path in links:
    st.markdown(f"- [{label} — `{path}`]({REPO}/{path})")
st.caption("All source documents and case data shown here are fictional course material. Human review remains necessary.")
