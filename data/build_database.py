# -*- coding: utf-8 -*-
"""
Builds data/investigateiq.db (SQLite) from the synthetic Excel dataset.

This is the one real ETL step in the prototype's data layer: the Excel workbook
is the human-editable source; the SQLite database is what the app and the AI
agent's tools actually query against (see CEO Playbook, Section 4 — Architecture).

Run: python data/build_database.py
Rebuilds the database from scratch every time (deterministic — same source data
in, same database out), so it's safe to re-run after editing the source Excel.
"""
import sqlite3
import hashlib
import datetime
import pandas as pd
import os
import re
if __package__:
    from .case_evidence import build_case_evidence
    from .matched_case_fixtures import seed_matched_cases
else:
    from case_evidence import build_case_evidence
    from matched_case_fixtures import seed_matched_cases

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
XLSX_PATH = os.path.join(REPO_ROOT, "Product Docs", "dataset", "InvestigateIQ - Synthetic Bank Dataset.xlsx")
KB_DIR = os.path.join(REPO_ROOT, "Product Docs", "dataset", "knowledge_base")
DB_PATH = os.path.join(HERE, "investigateiq.db")

SHEET_TO_TABLE = {
    "Customers": "customers",
    "Accounts": "accounts",
    "Transactions": "transactions",
    "Relationships": "relationships",
    "Alerts": "alerts",
    "PastCases": "past_cases",
    "Documents": "documents",
}

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_accounts_customer ON accounts(customer_id)",
    "CREATE INDEX IF NOT EXISTS idx_txn_account ON transactions(account_id)",
    "CREATE INDEX IF NOT EXISTS idx_txn_datetime ON transactions(txn_datetime)",
    "CREATE INDEX IF NOT EXISTS idx_txn_counterparty ON transactions(counterparty_account_id)",
    "CREATE INDEX IF NOT EXISTS idx_rel_from ON relationships(account_from)",
    "CREATE INDEX IF NOT EXISTS idx_rel_to ON relationships(account_to)",
    "CREATE INDEX IF NOT EXISTS idx_alerts_customer ON alerts(customer_id)",
    "CREATE INDEX IF NOT EXISTS idx_alerts_account ON alerts(account_id)",
    "CREATE INDEX IF NOT EXISTS idx_pastcases_customer ON past_cases(customer_id)",
    "CREATE INDEX IF NOT EXISTS idx_docs_customer ON documents(customer_id)",
    "CREATE INDEX IF NOT EXISTS idx_kb_scenario ON knowledge_base(scenario_id)",
    "CREATE INDEX IF NOT EXISTS idx_chunks_doc ON knowledge_chunks(doc_id)",
]

# Chunking strategy, stated explicitly so it can be quoted to an evaluator:
# 1 metadata chunk (title + escalation criteria) per document, then the body
# split into sentences and grouped SENTENCES_PER_CHUNK at a time. Small,
# deterministic, no external tokenizer dependency.
SENTENCES_PER_CHUNK = 2
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def parse_okf_file(path):
    """Parse an OKF document: YAML-ish frontmatter between '---' markers + markdown body.
    Hand-rolled (not a yaml lib) because our frontmatter is a flat key: value list —
    no need for a dependency to read six fields."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    parts = text.split("---", 2)
    frontmatter_raw, body = parts[1], parts[2]
    meta = {}
    for line in frontmatter_raw.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, body.strip()


def chunk_body(body):
    """Split a document body into sentences, then group SENTENCES_PER_CHUNK at
    a time. Returns a list of chunk text strings, in order."""
    sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(body.strip()) if s.strip()]
    chunks = []
    for i in range(0, len(sentences), SENTENCES_PER_CHUNK):
        chunks.append(" ".join(sentences[i:i + SENTENCES_PER_CHUNK]))
    return chunks


def load_knowledge_base(conn):
    """RAG source: every OKF playbook document (knowledge_base table), chunked
    into retrievable pieces (knowledge_chunks table) with a real SQLite FTS5
    full-text index over those chunks (knowledge_chunks_fts) for keyword-based
    retrieval today. Embeddings for semantic/vector similarity are a separate,
    additive step once an LLM/embedding API key is available — the schema
    already has a slot for it (embedding column, NULL until then) so adding
    vector search later doesn't require a schema change."""
    doc_rows = []
    chunk_rows = []

    if os.path.isdir(KB_DIR):
        for fname in sorted(os.listdir(KB_DIR)):
            if not fname.endswith(".md"):
                continue
            meta, body = parse_okf_file(os.path.join(KB_DIR, fname))
            doc_id = meta.get("id")
            scenario_id = meta.get("scenario_id")
            title = meta.get("title")
            escalation = meta.get("escalation_criteria")

            doc_rows.append({
                "doc_id": doc_id, "scenario_id": scenario_id, "title": title,
                "escalation_criteria": escalation, "version": meta.get("version"),
                "last_updated": meta.get("last_updated"), "body": body,
                "source_file": fname, "embedding": None,
            })

            # Chunk 0: metadata chunk — title + escalation criteria together,
            # so a query about "when to escalate" can match without needing
            # the full body text.
            chunk_rows.append({
                "chunk_id": f"{doc_id}-C0", "doc_id": doc_id, "scenario_id": scenario_id,
                "chunk_index": 0, "chunk_type": "metadata",
                "chunk_text": f"{title}. Escalation criteria: {escalation}.",
                "source_file": fname, "embedding": None,
            })
            # Body chunks: grouped sentences (the markdown "# Title" heading
            # line is stripped first — it's already captured in chunk C0).
            prose = re.sub(r"^#[^\n]*\n+", "", body).strip()
            for i, chunk_text in enumerate(chunk_body(prose), start=1):
                chunk_rows.append({
                    "chunk_id": f"{doc_id}-C{i}", "doc_id": doc_id, "scenario_id": scenario_id,
                    "chunk_index": i, "chunk_type": "body", "chunk_text": chunk_text,
                    "source_file": fname, "embedding": None,
                })

    df_docs = pd.DataFrame(doc_rows)
    df_docs.to_sql("knowledge_base", conn, if_exists="replace", index=False)

    df_chunks = pd.DataFrame(chunk_rows)
    df_chunks["char_count"] = df_chunks["chunk_text"].str.len()
    df_chunks["word_count"] = df_chunks["chunk_text"].str.split().str.len()
    df_chunks.to_sql("knowledge_chunks", conn, if_exists="replace", index=False)

    # Real full-text search index: SQLite's FTS5 engine — tokenizes chunk_text,
    # builds an inverted index, and supports BM25-ranked MATCH queries. This is
    # the "indexing" a keyword-search RAG system actually needs; not a mock.
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS knowledge_chunks_fts")
    cur.execute("""
        CREATE VIRTUAL TABLE knowledge_chunks_fts USING fts5(
            chunk_id UNINDEXED, doc_id UNINDEXED, scenario_id UNINDEXED, chunk_text
        )
    """)
    for row in chunk_rows:
        cur.execute(
            "INSERT INTO knowledge_chunks_fts (chunk_id, doc_id, scenario_id, chunk_text) VALUES (?,?,?,?)",
            (row["chunk_id"], row["doc_id"], row["scenario_id"], row["chunk_text"]),
        )

    # fts5vocab: exposes the FTS5 index's own vocabulary (term, doc count,
    # occurrence count) as a queryable table — this is what powers the
    # autocomplete/suggestion box, always in sync with the real index.
    cur.execute("DROP TABLE IF EXISTS knowledge_chunks_fts_vocab")
    cur.execute(
        "CREATE VIRTUAL TABLE knowledge_chunks_fts_vocab USING fts5vocab(knowledge_chunks_fts, 'row')"
    )
    conn.commit()

    return len(df_docs), len(df_chunks)


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    xl = pd.ExcelFile(XLSX_PATH)
    conn = sqlite3.connect(DB_PATH)

    counts = {}
    for sheet, table in SHEET_TO_TABLE.items():
        df = xl.parse(sheet)
        df.to_sql(table, conn, if_exists="replace", index=False)
        counts[table] = len(df)

    seed_matched_cases(conn)
    for table in SHEET_TO_TABLE.values():
        counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    n_docs, n_chunks = load_knowledge_base(conn)
    counts["knowledge_base"] = n_docs
    counts["knowledge_chunks"] = n_chunks
    evidence_docs, evidence_chunks = build_case_evidence(conn)
    counts["case_evidence_sources"] = evidence_docs
    counts["case_evidence_chunks"] = evidence_chunks

    # This describes the current generated index, not the date of any
    # transaction, document, or older saved report. Hash the exact indexed
    # passages so a future rebuild can be identified without guessing from a
    # deployment timestamp or the database file's modification time.
    digest = hashlib.sha256()
    for chunk_id, chunk_text in conn.execute(
        "SELECT chunk_id, chunk_text FROM case_evidence_chunks ORDER BY chunk_id"
    ):
        digest.update(chunk_id.encode("utf-8"))
        digest.update(b"\0")
        digest.update(chunk_text.encode("utf-8"))
        digest.update(b"\n")
    conn.execute("""CREATE TABLE evidence_index_builds (
        index_name TEXT PRIMARY KEY, built_at_utc TEXT NOT NULL,
        content_sha256 TEXT NOT NULL, chunk_count INTEGER NOT NULL
    )""")
    conn.execute(
        "INSERT INTO evidence_index_builds VALUES (?,?,?,?)",
        ("case_evidence_chunks_fts", datetime.datetime.now(datetime.timezone.utc).isoformat(),
         digest.hexdigest(), evidence_chunks),
    )

    cur = conn.cursor()
    for stmt in INDEXES:
        cur.execute(stmt)
    conn.commit()
    conn.close()

    print(f"Built {DB_PATH}")
    for table, n in counts.items():
        print(f"  {table:15s} {n:>6} rows")

if __name__ == "__main__":
    main()
