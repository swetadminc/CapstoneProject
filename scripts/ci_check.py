# -*- coding: utf-8 -*-
"""
CI sanity check: rebuilds the database and asserts the basic invariants the
rest of the app depends on. Run in GitHub Actions on every push/PR so a
broken dataset, a broken chunker, or a broken FTS index is caught before it
ever reaches a Railway build — Railway build minutes aren't free forever,
CI minutes on a small check like this effectively are.

Run: python scripts/ci_check.py
Exits non-zero (fails the CI job) on any failed check.
"""
import sqlite3
import subprocess
import sys
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(REPO_ROOT, "data", "investigateiq.db")

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)
        print(f"  FAIL: {message}")
    else:
        print(f"  ok:   {message}")


def main():
    print("Rebuilding database...")
    result = subprocess.run(
        [sys.executable, os.path.join(REPO_ROOT, "data", "build_database.py")],
        capture_output=True, text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        print("FATAL: build_database.py itself failed.")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("\nChecking table row counts...")
    expected_min = {
        "customers": 500, "accounts": 600, "transactions": 9000, "relationships": 100,
        "alerts": 30, "past_cases": 20, "documents": 10, "knowledge_base": 10, "knowledge_chunks": 20,
        "case_evidence_sources": 1700, "case_evidence_chunks": 4000,
    }
    for table, minimum in expected_min.items():
        n = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        check(n >= minimum, f"{table} has {n} rows (expected >= {minimum})")

    print("\nChecking the frozen demo scenario (C1/C2) is present...")
    row = cur.execute("SELECT name FROM customers WHERE customer_id='CUST-1004'").fetchone()
    check(row is not None and row[0] == "Apex Global Trading Ltd.", "hero customer CUST-1004 exists with the right name")

    n_alerts = cur.execute("SELECT COUNT(*) FROM alerts WHERE customer_id='CUST-1004'").fetchone()[0]
    check(n_alerts == 2, f"hero customer has exactly 2 alerts (found {n_alerts}) — the C1/C2 twin case")

    print("\nChecking every alert scenario has RAG/playbook coverage...")
    print("(this exists because that gap was real: 33/40 cases had zero grounded next-steps until it was fixed)")
    alert_scenarios = {r[0] for r in cur.execute("SELECT DISTINCT scenario_id FROM alerts").fetchall()}
    kb_scenarios = {r[0] for r in cur.execute("SELECT DISTINCT scenario_id FROM knowledge_base").fetchall()}
    uncovered = alert_scenarios - kb_scenarios
    check(not uncovered, f"every alert scenario_id has at least one knowledge_base doc (uncovered: {uncovered or 'none'})")

    print("\nChecking the FTS5 knowledge index actually returns results...")
    sys.path.insert(0, os.path.join(REPO_ROOT))
    from data.knowledge_search import search
    results = search("source of funds", k=1)
    check(len(results) > 0, "keyword search returns at least one result for a known query")
    if results:
        check(results[0]["score"] > 0, "top result has a positive BM25 score")

    print("\nChecking case evidence provenance and honest coverage...")
    case_count = cur.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    covered = cur.execute(
        "SELECT COUNT(DISTINCT case_id) FROM case_evidence_sources WHERE category='transaction_record'"
    ).fetchone()[0]
    check(covered == case_count, f"all {case_count} cases have a transaction evidence packet")
    check(cur.execute("SELECT COUNT(*) FROM case_evidence_sources WHERE is_original_upload=1").fetchone()[0] == 0,
          "generated samples are not represented as original uploaded files")
    check(cur.execute("SELECT COUNT(*) FROM case_evidence_chunks_fts WHERE case_evidence_chunks_fts MATCH 'fictional'").fetchone()[0] > 0,
          "case evidence FTS5 index contains searchable fictional-source text")
    collisions = {row[0] for row in cur.execute(
        "SELECT account_id FROM accounts GROUP BY account_id HAVING COUNT(DISTINCT customer_id)>1"
    )}
    check(collisions == {"ACC-1004"},
          f"only the documented, guarded workbook account-ID collision is present ({sorted(collisions)})")

    conn.close()

    print()
    if failures:
        print(f"{len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
