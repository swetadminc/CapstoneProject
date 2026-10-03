# -*- coding: utf-8 -*-
"""
Admin / Knowledge Base Inspector — internal view, not part of the investigator UI.

Purpose: give whoever is presenting a way to prove, live, exactly how the RAG
knowledge base is built — the documents, the chunking, the index, and a real
search running against it — rather than asserting it on a slide.
"""
import os
import sqlite3
import sys
import streamlit as st
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.knowledge_search import search, suggest_terms, DB_PATH
from ui_common import require_login, role_warning, page_banner, page_flow, get_admin_passcode, render_context_copilot

st.set_page_config(page_title="InvestigateIQ — Admin", page_icon="🔐", layout="wide")
user_name, user_role = require_login()
render_context_copilot("Admin — Knowledge Base", st.session_state.get("active_case_id"))

ADMIN_PASSCODE = get_admin_passcode()

page_banner("🔐", "Admin — Knowledge Base Inspector", "Inspect the retrieval sources used to support investigation drafts.")
page_flow("Show what guidance the copilot can retrieve", [
    ("Unlock", "Enter the admin passcode."),
    ("Inspect", "View fictional playbooks, document chunks and index contents."),
    ("Search", "Try the keyword retrieval used to ground report drafts."),
], "This is a synthetic teaching knowledge base, not an approved bank or RBI policy repository.")
st.markdown(
    """
    <style>
    .iq-chip { display:inline-block; background:#EEF3FB; color:#2E63BF; border:1px solid #2E63BF;
               border-radius:6px; padding:2px 8px; font-size:12px; margin-right:6px; }
    </style>
    """,
    unsafe_allow_html=True,
)
st.write("")
role_warning(user_role, "Admin")

# --- Passcode gate ---
if "kb_admin_unlocked" not in st.session_state:
    st.session_state.kb_admin_unlocked = False

if not st.session_state.kb_admin_unlocked:
    st.info("This passcode is a limited access gate, not production-grade authentication or authorization.")
    code = st.text_input("Admin passcode", type="password",
                         help="Limited access gate for the knowledge-base screen; not bank-grade authentication.")
    if st.button("Unlock", help="Open the read-only knowledge-base explorer after checking the passcode."):
        if code == ADMIN_PASSCODE:
            st.session_state.kb_admin_unlocked = True
            st.rerun()
        else:
            st.error("Incorrect passcode.")
    st.stop()

if not os.path.exists(DB_PATH):
    st.error(f"Database not found at `{DB_PATH}`.")
    st.stop()

conn = sqlite3.connect(DB_PATH)

# --- 1. Corpus overview ---
st.subheader("1 · What the knowledge base is built from")
n_docs = conn.execute("SELECT COUNT(*) FROM knowledge_base").fetchone()[0]
n_chunks = conn.execute("SELECT COUNT(*) FROM knowledge_chunks").fetchone()[0]
n_terms = conn.execute("SELECT COUNT(*) FROM knowledge_chunks_fts_vocab").fetchone()[0]
avg_words = pd.read_sql("SELECT word_count FROM knowledge_chunks", conn)["word_count"].mean()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Source documents (OKF)", n_docs,
          help="Synthetic playbook documents available to the retrieval workflow.")
c2.metric("Chunks (\"tiles\")", n_chunks,
          help="Smaller source passages that can be retrieved and cited.")
c3.metric("Indexed terms (vocabulary)", n_terms,
          help="Distinct indexed terms in the SQLite full-text search vocabulary.")
c4.metric("Avg. words / chunk", f"{avg_words:.0f}",
          help="Average passage size; this is descriptive, not a retrieval-quality score.")

st.markdown(
    """
    <span class="iq-chip" title="Open Knowledge Format: a Markdown document with YAML fields for its ID, scenario, title, escalation criteria and version, followed by guidance text.">Format: OKF (Open Knowledge Format)</span>
    <span class="iq-chip" title="Each playbook has one title-and-criteria metadata chunk; its body is grouped into ordered two-sentence passages.">Chunking: metadata chunk + 2-sentence body groups</span>
    <span class="iq-chip" title="SQLite full-text search maps words to matching passages. BM25 ranks keyword matches; its display score is not confidence or risk.">Index: SQLite FTS5 (inverted index, BM25 ranking)</span>
    <span class="iq-chip" title="The current search matches words in indexed text. It does not compare vector embeddings or infer semantic similarity.">Retrieval today: keyword / lexical</span>
    <span class="iq-chip" title="An embedding column exists in the schema, but no embedding model or vector search is active.">Vector / semantic: schema-ready, not yet built</span>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    "**RAG (Retrieval-Augmented Generation)** means finding relevant source passages first, "
    "then using those passages to support an answer or draft with citations. In this product, "
    "SQLite keyword search retrieves playbook and case-record passages. Some answers are "
    "deterministic calculations; an optional model can draft text from retrieved context. "
    "A citation identifies stored text, not independent proof."
)
st.markdown(
    "**OKF (Open Knowledge Format)** is the structured format of our synthetic playbook files: "
    "Markdown guidance plus YAML metadata such as document ID, scenario, title, version and "
    "escalation criteria. We split that text into small, citable chunks before indexing it. "
    "Case KYC and transaction records are stored and chunked separately; they are not OKF playbooks."
)

with st.expander("Exactly how a document becomes searchable chunks — the honest, full explanation"):
    st.markdown(
        """
        **1. Source.** Each playbook entry is authored as an OKF document — a markdown file with a YAML
        frontmatter block (`id`, `scenario_id`, `title`, `escalation_criteria`, `version`) and a prose body.
        See `Product Docs/dataset/knowledge_base/*.md` in the repo.

        **2. Chunking.** `data/build_database.py` splits each document into:
        - **1 metadata chunk** — the title and escalation criteria combined, so a query like *"when do I
          escalate?"* can match even if the exact wording isn't in the prose body.
        - **N body chunks** — the prose body is split into sentences (regex on sentence-ending punctuation),
          then grouped **2 sentences per chunk**. This keeps each chunk small and topically focused, which is
          what makes a retrieved chunk a specific, checkable claim rather than a whole document dump.

        This produced **{n_chunks} chunks from {n_docs} documents** — every one of them is browsable below.

        **3. Indexing.** All chunks are inserted into a **SQLite FTS5 virtual table** — a real full-text search
        engine built into SQLite: it tokenizes each chunk, builds an inverted index (term → which chunks
        contain it), and ranks matches with the **BM25** algorithm (the same ranking family classic keyword
        search engines use — weighs term frequency against how common/rare each term is across the corpus).

        **4. Retrieval.** `data/knowledge_search.py` — `search(query)` — turns a question into indexed terms,
        runs a `MATCH` query against the FTS5 index, and returns the top-k chunks ranked by BM25 score, each
        with its source document ID. The Evidence Agent and the legacy Chat Agent use this playbook
        search. The case-scoped Copilot also reads the selected case's separate evidence index and
        stored ledger; not every Copilot answer runs this playbook search.

        **5. What's NOT built yet, stated plainly.** There is no embedding model and no vector database —
        that's a deliberate choice for this phase (see the note below), not an oversight. The `embedding`
        column already exists on `knowledge_chunks`, currently `NULL` on every row, ready for that to be
        added later without a schema change.
        """.format(n_chunks=n_chunks, n_docs=n_docs)
    )

st.info(
    "**Why keyword search instead of vector embeddings, for now:** our knowledge base is small "
    f"({n_docs} documents, {n_chunks} chunks) — small enough that BM25 keyword ranking finds the right "
    "chunk reliably, without an embedding API call on every query. That removes one more live network "
    "dependency from an external model call (see CEO Playbook, Section 12 — Risks & Win Safeguards) and costs nothing "
    "to run. It's an explicit, defensible engineering trade-off for this phase, not a limitation we're "
    "hiding — semantic/vector search is the documented next step once an LLM/embedding API key is chosen."
)

st.divider()

# --- 2. Document browser ---
st.subheader("2 · The documents")
docs = pd.read_sql("SELECT doc_id, scenario_id, title, escalation_criteria, version FROM knowledge_base ORDER BY doc_id", conn)
st.dataframe(docs, hide_index=True, use_container_width=True)

selected_doc = st.selectbox("Open a document", docs["doc_id"].tolist(),
                            help="Choose a synthetic playbook source to inspect its text and searchable chunks.")
if selected_doc:
    row = conn.execute("SELECT body, source_file FROM knowledge_base WHERE doc_id=?", (selected_doc,)).fetchone()
    st.caption(f"Source file: `Product Docs/dataset/knowledge_base/{row[1]}`")
    st.markdown(row[0])

st.divider()

# --- 3. Chunk browser ---
st.subheader("3 · Every chunk (the \"tiles\") for that document")
chunks_df = pd.read_sql(
    "SELECT chunk_id, chunk_index, chunk_type, char_count, word_count, chunk_text "
    "FROM knowledge_chunks WHERE doc_id=? ORDER BY chunk_index",
    conn, params=(selected_doc,),
)
st.dataframe(chunks_df, hide_index=True, use_container_width=True)

with st.expander("See the full chunk map — all documents, all chunks, at once"):
    all_chunks = pd.read_sql(
        "SELECT doc_id, chunk_id, chunk_type, word_count, chunk_text FROM knowledge_chunks ORDER BY doc_id, chunk_index",
        conn,
    )
    st.dataframe(all_chunks, hide_index=True, use_container_width=True)

st.divider()

# --- 4. Live search demo, with autosuggest ---
st.subheader("4 · Live retrieval — search the index right now")
st.caption("This runs the live keyword retrieval function used for playbook guidance. Results depend "
           "on your query and the current index; case-record retrieval is a separate path.")
st.info("**BM25 score guide:** A higher displayed number means a stronger keyword match among "
        "results for this same search. It is not a percentage, confidence level, risk score, or "
        "proof. Scores from different searches are not directly comparable; read the actual "
        "passage and source before using it.")

if "kb_query" not in st.session_state:
    st.session_state.kb_query = ""

query = st.text_input("Type a question or keywords", key="kb_query", placeholder="e.g. source of funds",
                      help="Searches the local SQLite FTS5 keyword index; this is not semantic/vector search.")

if query and len(query) >= 2:
    last_word = query.strip().split(" ")[-1]
    suggestions = suggest_terms(last_word)
    suggestions = [s for s in suggestions if s.lower() != last_word.lower()]
    if suggestions:
        st.caption("Suggested (from the index's own vocabulary):")
        cols = st.columns(min(len(suggestions), 6))
        for i, term in enumerate(suggestions[:6]):
            if cols[i].button(term, key=f"sugg_{term}",
                              help="Replace your last word with this term from the indexed vocabulary."):
                words = query.strip().split(" ")[:-1]
                st.session_state.kb_query = " ".join(words + [term])
                st.rerun()

if query:
    results = search(query, k=5)
    if not results:
        st.warning("No chunks matched. Try different keywords.")
    for r in results:
        with st.container(border=True, key=f"iq_bordered_kb_{r['chunk_id']}"):
            cols = st.columns([1, 5])
            cols[0].metric("BM25 score", r["score"],
                           help="Keyword-match ranking for this query. We reverse SQLite's raw BM25 rank "
                                "so higher displayed values rank first. Compare only results from this "
                                "same query; it is not a 0–100 score, probability, risk, or confidence.")
            cols[1].markdown(f"**{r['chunk_id']}** · from *{r['doc_title']}* (`{r['doc_id']}`)")
            cols[1].write(r["chunk_text"])
            cols[1].caption(f"If cited by the Copilot, the investigator sees: "
                             f"\"[Retrieved: {r['doc_id']} — view source]\" and this is the exact chunk behind it.")

conn.close()
