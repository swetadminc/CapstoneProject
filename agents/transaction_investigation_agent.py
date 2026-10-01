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


def anchor_cached_evidence(evidence: dict, alert: dict) -> dict:
    """Refresh a stored report's ratio from a real, cited trigger if possible.

    Older cached reports may have calculated a ratio from the first window
    transaction even when the source alert identified no trigger at all.
    Keep the cache file unchanged, but do not replay that unsupported number.
    """
    checked = dict(evidence)
    trigger_id = alert.get("trigger_transaction_id")
    trigger_txn = next(
        (txn for txn in evidence.get("window_transactions", []) if txn.get("txn_id") == trigger_id),
        None,
    ) if trigger_id and not evidence.get("evidence_window_empty") else None
    baseline = evidence.get("baseline_avg_amount")
    checked["trigger_transaction_id"] = trigger_id if trigger_txn else None
    checked["deviation_ratio"] = (
        round(trigger_txn["amount"] / baseline, 1)
        if trigger_txn and baseline else None
    )
    return checked


class TransactionInvestigationAgent:
    name = "Transaction Investigation Agent"

    def run(self, account_id: str, alert_date: str, window_days: int = 10,
            trigger_txn_id: str = None) -> dict:
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

        # Broader per-case verification found that 24 of the 42 current
        # fictional alerts have zero transactions in that strict
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

        # Never infer the trigger from the first convenient transaction.
        # Most fictional alerts have no trigger_transaction_id, even when
        # activity happens to fall inside the review window. An unanchored
        # ratio would imply precision that the source alert cannot support.
        trigger_txn = next((t for t in window_txns if t["txn_id"] == trigger_txn_id), None)
        deviation_ratio = (
            round(trigger_txn["amount"] / baseline_avg, 1)
            if trigger_txn and not evidence_window_empty and baseline_avg else None
        )

        return {
            "baseline_avg_amount": round(baseline_avg, 2),
            "baseline_txn_count": baseline_n,
            "deviation_ratio": deviation_ratio,
            "trigger_transaction_id": trigger_txn_id if trigger_txn else None,
            "window_transactions": window_txns,
            "evidence_window_empty": evidence_window_empty,
        }
