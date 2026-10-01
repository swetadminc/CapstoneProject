"""Read-only, presenter-friendly proof of the synthetic retrieval workflow."""

import inspect
import os
import sqlite3
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.build_database import chunk_body
from data.knowledge_search import DB_PATH, search
from agents.evidence_agent import EvidenceAgent
from agents.grounding_validator import GroundingValidator
from ui_common import require_login, page_banner, page_flow

st.set_page_config(page_title="InvestigateIQ — Evidence & RAG", page_icon="🧩", layout="wide")
require_login(allow_guest=True)
page_banner("🧩", "Evidence & RAG", "Trace a saved recommendation back to its synthetic source document and searchable chunks.")
page_flow("Show how source guidance becomes retrievable evidence", [
    ("Open a source", "Choose a synthetic playbook document or follow a citation from an investigation."),
    ("Inspect chunks", "Compare the original body with the metadata and two-sentence body chunks."),
    ("Try retrieval", "Search the same SQLite FTS5 index used by the evidence agent."),
    ("Inspect the code", "Expand the chunking, retrieval and citation-checking implementation below without leaving this page."),
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

query_doc = st.query_params.get("doc")
requested_doc = st.session_state.pop("rag_doc_id", None) or query_doc
if query_doc is not None:
    # A deep link chooses the initial document, but must not override later
    # manual selections on every Streamlit rerun.
    del st.query_params["doc"]
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
st.write("Open any step below to see the actual Python used by this product. You can stay on this page while comparing the code with the source document and search results above.")
implementation = [
    ("1 · Split the document", "data/build_database.py", "Groups source sentences into small, ordered chunks that can be inspected individually.", chunk_body),
    ("2 · Retrieve matching chunks", "data/knowledge_search.py", "Uses a parameterized SQLite FTS5 query and BM25 ranking; no embeddings or vector database are used.", search),
    ("3 · Gather case guidance", "agents/evidence_agent.py", "Limits the playbook search to the alert scenario and returns the selected guidance with case documents.", EvidenceAgent.guidance_for),
    ("4 · Check draft citations", "agents/grounding_validator.py", "Checks selected transaction and document IDs, required citations, ratio claims, and unsupported conclusion wording. This is not proof that every sentence is correct.", GroundingValidator.validate),
]
for title, path, explanation, function in implementation:
    with st.expander(title):
        st.write(explanation)
        st.markdown(f"**Source file:** `{path}` · **Function:** `{function.__qualname__}`")
        st.code(inspect.getsource(function), language="python")
st.caption("All source documents and case data shown here are fictional course material. Human review remains necessary.")
