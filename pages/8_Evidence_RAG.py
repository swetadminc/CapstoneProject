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
    st.session_state["rag_view"] = "Source & chunks"
elif st.session_state.get("rag_doc_choice") not in doc_by_id:
    st.session_state["rag_doc_choice"] = doc_ids[0]

def open_chunk(doc_id: str, chunk_id: str) -> None:
    """Move from a search result to its exact in-site source passage."""
    st.session_state["rag_doc_choice"] = doc_id
    st.session_state["rag_chunk_id"] = chunk_id
    st.session_state["rag_view"] = "Source & chunks"


if "rag_view" not in st.session_state:
    st.session_state["rag_view"] = "Source & chunks"
view = st.segmented_control(
    "Explore evidence", ["Source & chunks", "Search the index", "Method & code"],
    key="rag_view", required=True,
    help="Switch between original sources, live retrieval results, and the actual implementation without leaving InvestigateIQ.",
)

if view == "Source & chunks":
    selected_doc = st.selectbox(
        "Source document", doc_ids, key="rag_doc_choice",
        format_func=lambda doc_id: f"{doc_id} — {doc_by_id[doc_id]['title']}",
        help="Select a synthetic playbook; a citation from an investigation preselects its source.",
    )
    doc = doc_by_id[selected_doc]
    st.caption(f"{doc['doc_id']} · {doc['scenario_id']} · Product Docs/dataset/knowledge_base/{doc['source_file']}")
    st.markdown(f"**Escalation criteria in source:** {doc['escalation_criteria']}")
    with sqlite3.connect(DB_PATH) as conn:
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
