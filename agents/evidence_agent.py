# -*- coding: utf-8 -*-
"""
Evidence Agent — fifth of the six specialist agents (see
alert_triage_agent.py for the roadmap reference).

Owns everything outside the transaction ledger that supports an
investigation: retrieving relevant playbook guidance from the RAG knowledge
base (FTS5/BM25 keyword search today), and pulling any documents already on
file for this case. This is where "what does policy say to do here" and
"what evidence has already been collected" come together, before the
Investigation Summary Agent reasons over all of it.
"""
import sqlite3

from data.knowledge_search import DB_PATH, search as search_knowledge


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
        return {
            "guidance": self.guidance_for(alert, k=k),
            "documents": self.documents_for(case_id),
        }
