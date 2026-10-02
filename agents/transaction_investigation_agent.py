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
from contextlib import closing
from datetime import datetime, timedelta

from data.knowledge_search import DB_PATH


def anchor_cached_evidence(evidence: dict, alert: dict) -> dict:
    """Refresh a stored report's ratio from a real, cited trigger if possible.

    Older cached reports may have calculated a ratio from the first window
    transaction even when the source alert identified no trigger at all.
    Keep the cache file unchanged, but do not replay that unsupported number.
    """
    checked = dict(evidence)
    with closing(sqlite3.connect(DB_PATH)) as conn:
        owner_rows = conn.execute(
            "SELECT COUNT(*) FROM accounts WHERE account_id=?", (alert["account_id"],)
        ).fetchone()[0]
    checked["account_ownership_ambiguous"] = owner_rows != 1
    trigger_id = alert.get("trigger_transaction_id")
    trigger_txn = next(
        (txn for txn in evidence.get("window_transactions", []) if txn.get("txn_id") == trigger_id),
        None,
    ) if trigger_id and not evidence.get("evidence_window_empty") else None
    baseline = evidence.get("baseline_avg_amount")
    checked["trigger_transaction_id"] = trigger_id if trigger_txn and not checked["account_ownership_ambiguous"] else None
    checked["deviation_ratio"] = (
        round(trigger_txn["amount"] / baseline, 1)
        if trigger_txn and baseline and not checked["account_ownership_ambiguous"] else None
    )
    return checked


class TransactionInvestigationAgent:
    name = "Transaction Investigation Agent"

    def run(self, account_id: str, alert_date: str, window_days: int = 10,
            trigger_txn_id: str = None) -> dict:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        owner_count = cur.execute(
            "SELECT COUNT(*) FROM accounts WHERE account_id=?", (account_id,)
        ).fetchone()[0]
        account_ownership_ambiguous = owner_count != 1

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
        # Separate monthly-credit baseline for the matched 24-hour activity
        # rule. This is not the single-transaction average used above.
        monthly_credit_row = cur.execute(
            "SELECT SUM(amount) AS total FROM transactions WHERE account_id=? AND direction='CR' "
            "AND julianday(txn_datetime)>=julianday(date(?, 'start of month', '-6 months')) "
            "AND julianday(txn_datetime)<julianday(date(?, 'start of month'))",
            (account_id, alert_date, alert_date),
        ).fetchone()
        monthly_credit_baseline = round((monthly_credit_row["total"] or 0) / 6, 2)

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
               WHERE account_id = ? AND julianday(txn_datetime) >= julianday(?)
                 AND julianday(txn_datetime) < julianday(?, '+' || ? || ' days')
               ORDER BY txn_datetime""",
            (account_id, alert_date, alert_date, window_days),
        ).fetchall()
        window_txns = [dict(r) for r in window_txns]

        # Broader per-case verification found that many original workbook
        # alerts have zero transactions in that strict
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
            if trigger_txn and not evidence_window_empty and baseline_avg and not account_ownership_ambiguous else None
        )
        activity_24h = None
        if trigger_txn and not evidence_window_empty and not account_ownership_ambiguous:
            anchor = datetime.fromisoformat(trigger_txn["txn_datetime"])
            end = anchor + timedelta(hours=24)
            scoped = [t for t in window_txns if anchor <= datetime.fromisoformat(t["txn_datetime"]) <= end]
            incoming = [t for t in scoped if t["direction"] == "CR"]
            outgoing = [t for t in scoped if t["direction"] == "DR"]
            incoming_total = sum(t["amount"] for t in incoming)
            outgoing_total = sum(t["amount"] for t in outgoing)
            activity_24h = {
                "incoming_total": incoming_total,
                "outgoing_total": outgoing_total,
                "historical_monthly_credit": monthly_credit_baseline,
                "incoming_monthly_multiplier": round(incoming_total / monthly_credit_baseline, 2)
                if monthly_credit_baseline else None,
                "outgoing_to_incoming_pct": round(outgoing_total / incoming_total * 100, 2)
                if incoming_total else None,
                "distinct_beneficiaries": len({t["counterparty_account_id"] for t in outgoing
                                               if t["counterparty_account_id"]}),
                "credit_txn_ids": [t["txn_id"] for t in incoming],
                "debit_txn_ids": [t["txn_id"] for t in outgoing],
                "caveat": "Aggregate activity is an alert proxy, not proof that the incoming funds financed the outgoing payments.",
            }

        return {
            "baseline_avg_amount": round(baseline_avg, 2),
            "baseline_txn_count": baseline_n,
            "deviation_ratio": deviation_ratio,
            "trigger_transaction_id": trigger_txn_id if trigger_txn and not account_ownership_ambiguous else None,
            "window_transactions": window_txns,
            "evidence_window_empty": evidence_window_empty,
            "activity_24h": activity_24h,
            "account_ownership_ambiguous": account_ownership_ambiguous,
        }
