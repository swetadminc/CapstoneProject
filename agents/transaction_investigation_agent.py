# -*- coding: utf-8 -*-
"""
Transaction Investigation Agent — third of the six specialist agents (see
alert_triage_agent.py for the roadmap reference).

Owns the one job the LLM must never be trusted to do: the actual arithmetic.
Computes the account's baseline spending, pulls the transactions in the
alert's review window, and flags whether that window came up empty. Every
number here is computed by plain code — the LLM only ever interprets these
results, never recalculates them.
"""
import sqlite3

from data.knowledge_search import DB_PATH


class TransactionInvestigationAgent:
    name = "Transaction Investigation Agent"

    def run(self, account_id: str, alert_date: str, window_days: int = 10) -> dict:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Baseline: average transaction amount for this account, excluding
        # the alert window itself, so the "how unusual is this" comparison
        # is fair.
        baseline_row = cur.execute(
            """SELECT AVG(amount) as avg_amt, COUNT(*) as n FROM transactions
               WHERE account_id = ? AND txn_datetime < ?""",
            (account_id, alert_date),
        ).fetchone()
        baseline_avg = baseline_row["avg_amt"] or 0
        baseline_n = baseline_row["n"]

        # Bounded on both ends: some accounts have multiple historical
        # alerts (e.g. the frozen C1/C2 twin case both sit on ACC-1004), so
        # an unbounded ">= alert_date" filter would pull in a LATER,
        # unrelated alert's transactions too if this alert is the older of
        # the two. window_days matches the R2 rapid-pass-through rule's own
        # review period.
        window_txns = cur.execute(
            """SELECT txn_id, txn_datetime, direction, amount, counterparty_name,
                      counterparty_account_id, reference_text
               FROM transactions
               WHERE account_id = ? AND txn_datetime >= ?
                 AND txn_datetime <= datetime(?, '+' || ? || ' days')
               ORDER BY txn_datetime""",
            (account_id, alert_date, alert_date, window_days),
        ).fetchall()
        window_txns = [dict(r) for r in window_txns]

        # Broader per-case verification (pending item #6) found that 24 of
        # the 41 alerts in the dataset have zero transactions in that strict
        # window — most alerts were generated without a real anchoring
        # trigger_transaction_id, so alert_date doesn't reliably line up
        # with actual account activity. Fallback: show the nearest real
        # transactions to alert_date instead, clearly labeled downstream as
        # NOT within the review window, so the report is still grounded in
        # real data rather than a dead end. This never affects a case that
        # already has real in-window evidence (including the frozen C1/C2
        # hero scenario and the structuring case, CASE-041).
        evidence_window_empty = len(window_txns) == 0
        if evidence_window_empty:
            nearest = cur.execute(
                """SELECT txn_id, txn_datetime, direction, amount, counterparty_name,
                          counterparty_account_id, reference_text
                   FROM transactions
                   WHERE account_id = ?
                   ORDER BY ABS(julianday(txn_datetime) - julianday(?))
                   LIMIT 5""",
                (account_id, alert_date),
            ).fetchall()
            window_txns = sorted((dict(r) for r in nearest), key=lambda t: t["txn_datetime"])

        conn.close()

        # deviation_ratio is only meaningful against a real in-window
        # trigger transaction — with the nearest-activity fallback there is
        # no such transaction, so leave it unset rather than imply a false
        # precision.
        if evidence_window_empty:
            deviation_ratio = None
        else:
            trigger_amt = window_txns[0]["amount"]
            deviation_ratio = round(trigger_amt / baseline_avg, 1) if baseline_avg else None

        return {
            "baseline_avg_amount": round(baseline_avg, 2),
            "baseline_txn_count": baseline_n,
            "deviation_ratio": deviation_ratio,
            "window_transactions": window_txns,
            "evidence_window_empty": evidence_window_empty,
        }
