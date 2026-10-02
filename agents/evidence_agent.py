# -*- coding: utf-8 -*-
"""
Evidence Agent — fifth of the six specialist agents (see
alert_triage_agent.py for the roadmap reference).

Owns everything outside the transaction ledger that supports an
investigation: retrieving relevant playbook guidance and fictional case
source passages from two separately scoped FTS5/BM25 indexes, then pulling
document-summary rows on file. Retrieval is not independent verification.
"""
import sqlite3
from contextlib import closing

from data.knowledge_search import DB_PATH, search as search_knowledge
from data.case_evidence import search_case_chunks


class EvidenceAgent:
    name = "Evidence Agent"

    def guidance_for(self, alert: dict, k: int = 4) -> list:
        query = f"{alert['alert_type']} {alert['scenario_id']}"
        return search_knowledge(query, k=k, scenario_id=alert.get("scenario_id"))

    def documents_for(self, case_id: str) -> list:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        documents = cur.execute(
            """SELECT doc_id, doc_type, doc_date, extracted_summary, verified
               FROM documents WHERE case_id = ?""",
            (case_id,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in documents]

    def run(self, alert: dict, case_id: str, k: int = 4) -> dict:
        with closing(sqlite3.connect(DB_PATH)) as conn:
            activity = search_case_chunks(conn, case_id, f"{alert['alert_type']} transaction explanation", limit=max(1, k // 2))
            identity = search_case_chunks(conn, case_id, "KYC profile declared source funds", limit=max(1, k - len(activity)))
            case_chunks = list({row["chunk_id"]: row for row in activity + identity}.values())
        return {
            "guidance": self.guidance_for(alert, k=k),
            "documents": self.documents_for(case_id),
            "case_chunks": case_chunks,
        }
