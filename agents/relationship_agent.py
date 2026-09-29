# -*- coding: utf-8 -*-
"""
Relationship Agent — fourth of the six specialist agents (see
alert_triage_agent.py for the roadmap reference).

Owns counterparty relationship checks: for every counterparty seen in the
transaction window, is there a known, verified relationship on file, or has
that counterparty been flagged before? Kept separate from transaction
analysis because "who is this money moving to/from" is a distinct
investigative question from "how much money moved."
"""
import sqlite3

from data.knowledge_search import DB_PATH


class RelationshipAgent:
    name = "Relationship Agent"

    def run(self, account_id: str, window_transactions: list) -> dict:
        counterparty_ids = {
            t["counterparty_account_id"] for t in window_transactions if t["counterparty_account_id"]
        }
        if not counterparty_ids:
            return {"relationships": []}

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        relationships = []
        for cp_id in counterparty_ids:
            rel = cur.execute(
                """SELECT relationship_type, source, verified, start_date, previously_flagged
                   FROM relationships WHERE account_from = ? AND account_to = ?""",
                (account_id, cp_id),
            ).fetchone()
            relationships.append({"counterparty_account_id": cp_id, "relationship": dict(rel) if rel else None})

        conn.close()
        return {"relationships": relationships}
