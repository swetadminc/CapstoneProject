# -*- coding: utf-8 -*-
"""
Keyword retrieval over the OKF knowledge base, using SQLite's built-in FTS5
full-text search engine (inverted index + BM25 ranking) — no embedding API,
no vector database, no extra dependency, no network call.

This is deliberately the retrieval half of RAG built now, so it's not blocked
on an LLM/embedding API key. When one is available, `search()` can be swapped
for (or combined with) a vector similarity query against the same
knowledge_chunks table's `embedding` column — the schema already has that slot.

Usage (this is also exactly what the future Conclusion Agent's
retrieve_knowledge() tool will call):

    from data.knowledge_search import search
    results = search("what should I check for the source of funds")
    for r in results:
        print(r["chunk_id"], r["doc_id"], r["score"], r["chunk_text"])
"""
import sqlite3
import os
import re

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "investigateiq.db")


def _fts_query(user_query: str) -> str:
    """Turn free-text user input into a safe FTS5 MATCH expression: strip FTS5
    special characters, OR the terms together so partial keyword overlap still
    ranks (BM25 rewards matching more terms), and drop empty/too-short tokens."""
    terms = re.findall(r"[A-Za-z0-9]+", user_query.lower())
    terms = [t for t in terms if len(t) > 2]
    if not terms:
        return '""'
    return " OR ".join(terms)


def search(query: str, k: int = 3, scenario_id: str | None = None):
    """Return the top-k matching chunks for `query`, ranked by BM25 (lower is
    better in SQLite's bm25(); we invert it so higher score = more relevant)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    fts_expr = _fts_query(query)
    sql = """
        SELECT knowledge_chunks_fts.chunk_id, knowledge_chunks_fts.doc_id,
               knowledge_chunks_fts.scenario_id, knowledge_chunks_fts.chunk_text,
               bm25(knowledge_chunks_fts) AS rank,
               knowledge_base.title, knowledge_base.escalation_criteria
        FROM knowledge_chunks_fts
        JOIN knowledge_base ON knowledge_base.doc_id = knowledge_chunks_fts.doc_id
        WHERE knowledge_chunks_fts MATCH ?
    """
    params = [fts_expr]
    if scenario_id:
        sql += " AND knowledge_chunks_fts.scenario_id = ?"
        params.append(scenario_id)
    sql += " ORDER BY rank LIMIT ?"
    params.append(k)

    try:
        rows = cur.execute(sql, params).fetchall()
    except sqlite3.OperationalError:
        rows = []
    conn.close()

    return [
        {
            "chunk_id": r["chunk_id"],
            "doc_id": r["doc_id"],
            "doc_title": r["title"],
            "escalation_criteria": r["escalation_criteria"],
            "chunk_text": r["chunk_text"],
            "score": round(-r["rank"], 3),  # bm25() is "lower = better"; flip sign for intuitive "higher = better"
        }
        for r in rows
    ]


def suggest_terms(prefix: str, limit: int = 8):
    """Autocomplete: indexed words that start with `prefix`, for a smart search
    box. Powered by FTS5's own vocabulary table — no separate word list to
    maintain; it's always in sync with whatever is actually indexed."""
    if not prefix or len(prefix) < 2:
        return []
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT term FROM knowledge_chunks_fts_vocab WHERE term LIKE ? ORDER BY doc DESC LIMIT ?",
            (f"{prefix.lower()}%", limit),
        )
        rows = [r[0] for r in cur.fetchall()]
    except sqlite3.OperationalError:
        rows = []
    conn.close()
    return rows


if __name__ == "__main__":
    for q in ["source of funds", "escalate", "external account", "prior alerts"]:
        print(f"\nQuery: {q!r}")
        for r in search(q, k=2):
            print(f"  [{r['score']:>6}] {r['chunk_id']}  {r['chunk_text'][:80]}...")
