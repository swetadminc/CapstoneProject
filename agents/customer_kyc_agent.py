# -*- coding: utf-8 -*-
"""
Customer / KYC Agent — second of the six specialist agents (see
alert_triage_agent.py for the roadmap reference).

Owns the customer's identity and history: who they are (customer + account
records, risk rating, KYC status, declared source of funds) and what's
happened with them before (prior cases). This is deliberately separate from
transaction analysis — a specialist "is this customer who they say they are"
check is a distinct concern from "is this specific transaction pattern
unusual."
"""
import sqlite3

from data.knowledge_search import DB_PATH


class CustomerKYCAgent:
    name = "Customer/KYC Agent"

    def run(self, alert: dict, case_id: str) -> dict:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        customer = dict(cur.execute(
            "SELECT * FROM customers WHERE customer_id = ?", (alert["customer_id"],)
        ).fetchone())

        account = dict(cur.execute(
            "SELECT * FROM accounts WHERE account_id = ?", (alert["account_id"],)
        ).fetchone())

        prior_cases = cur.execute(
            """SELECT case_id, disposition, rationale FROM past_cases
               WHERE customer_id = ? AND case_id != ?""",
            (customer["customer_id"], case_id),
        ).fetchall()
        prior_cases = [dict(r) for r in prior_cases]

        conn.close()
        return {"customer": customer, "account": account, "prior_cases": prior_cases}
