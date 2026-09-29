# -*- coding: utf-8 -*-
"""
Alert Triage Agent — first of the six specialist agents from the documented
roadmap (Product Docs, Technical Architecture §5 / Delivery Plan Phase 3:
Triage, Transaction, Relationship, KYC, Evidence, Summary).

Owns exactly one job: given a case_id, pull the triggering alert and confirm
it's real. Nothing else reads the alerts table directly — every other agent
receives the alert dict this agent produces.
"""
import sqlite3

from data.knowledge_search import DB_PATH


class AlertTriageAgent:
    name = "Alert Triage Agent"

    def run(self, case_id: str) -> dict:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        alert = cur.execute(
            "SELECT * FROM alerts WHERE case_id = ?", (case_id,)
        ).fetchone()
        conn.close()

        if not alert:
            raise ValueError(f"No alert found for case_id={case_id}")

        return {"case_id": case_id, "alert": dict(alert)}
