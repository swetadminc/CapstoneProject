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
import pandas as pd
import os

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
]


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


def load_knowledge_base(conn):
    """RAG source table: every OKF playbook document, ready to query today by
    scenario_id/keyword. Embeddings (for real vector similarity search) are a
    separate, additive step once an LLM/embedding API key is wired in — the
    schema below already has a slot for it (embedding column, NULL until then)."""
    rows = []
    if os.path.isdir(KB_DIR):
        for fname in sorted(os.listdir(KB_DIR)):
            if not fname.endswith(".md"):
                continue
            meta, body = parse_okf_file(os.path.join(KB_DIR, fname))
            rows.append({
                "doc_id": meta.get("id"),
                "scenario_id": meta.get("scenario_id"),
                "title": meta.get("title"),
                "escalation_criteria": meta.get("escalation_criteria"),
                "version": meta.get("version"),
                "last_updated": meta.get("last_updated"),
                "body": body,
                "source_file": fname,
                "embedding": None,
            })
    df = pd.DataFrame(rows)
    df.to_sql("knowledge_base", conn, if_exists="replace", index=False)
    return len(df)


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

    counts["knowledge_base"] = load_knowledge_base(conn)

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
