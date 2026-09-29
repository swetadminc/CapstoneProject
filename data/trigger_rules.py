# -*- coding: utf-8 -*-
"""
Live rule evaluation — makes the Admin rule-config screen's thresholds
actually mean something, rather than a form that saves a number nobody
sees the effect of.

The dataset's alerts table is fixed (generated once, deterministic — see
data/build_database.py) and is NOT regenerated when thresholds change; that
would risk breaking the frozen C1/C2 hero scenario. Instead, this module
recomputes R1/R2 against the real transaction data using whatever
thresholds are currently configured, so an admin can see "how many accounts
would trigger under these settings" before saving — the live effect of the
change, without touching the frozen dataset.
"""
import sqlite3
from data.knowledge_search import DB_PATH


def would_trigger_r1(conn, account_id: str, as_of: str, deviation_multiplier: float):
    """R1: does the largest credit up to `as_of` exceed deviation_multiplier
    times the account's trailing average credit amount?"""
    baseline = conn.execute(
        "SELECT AVG(amount) FROM transactions WHERE account_id=? AND direction='CR' AND txn_datetime < ?",
        (account_id, as_of),
    ).fetchone()[0]
    if not baseline:
        return False, None, None
    peak = conn.execute(
        "SELECT MAX(amount) FROM transactions WHERE account_id=? AND direction='CR' AND txn_datetime = ?",
        (account_id, as_of),
    ).fetchone()[0]
    if not peak:
        return False, baseline, None
    ratio = peak / baseline
    return ratio >= deviation_multiplier, baseline, ratio


def would_trigger_r2(conn, account_id: str, trigger_txn_datetime: str, trigger_amount: float,
                      pass_through_pct: float, window_hours: float):
    """R2: does at least pass_through_pct% of trigger_amount leave the
    account within window_hours across at least 2 outbound transactions?"""
    rows = conn.execute(
        """SELECT amount FROM transactions
           WHERE account_id=? AND direction='DR' AND txn_datetime >= ?
             AND txn_datetime <= datetime(?, '+' || ? || ' hours')""",
        (account_id, trigger_txn_datetime, trigger_txn_datetime, window_hours),
    ).fetchall()
    if len(rows) < 2:
        return False, 0.0
    total_out = sum(r[0] for r in rows)
    pct = (total_out / trigger_amount) * 100 if trigger_amount else 0
    return pct >= pass_through_pct, pct


def preview_trigger_counts(thresholds: dict, sample_limit: int = 200) -> dict:
    """Runs R1 (and R2 where R1 fires) across a sample of internal accounts'
    largest credit transactions, using the GIVEN thresholds (not necessarily
    what's saved) — this is what powers the admin screen's live "if you save
    this, here's roughly what would trigger" preview.

    sample_limit caps how many accounts get checked, purely so the preview
    stays fast in this SQLite-per-request setup; it's a preview, not a
    production monitoring pass."""
    conn = sqlite3.connect(DB_PATH)
    dev_mult = thresholds[("R1", "deviation_multiplier")]
    pass_pct = thresholds[("R2", "pass_through_pct")]
    window_h = thresholds[("R2", "window_hours")]

    accounts = conn.execute(
        "SELECT DISTINCT account_id FROM transactions WHERE direction='CR' LIMIT ?", (sample_limit,)
    ).fetchall()

    r1_only = 0
    r1_and_r2 = 0
    checked = 0
    triggered_examples = []

    for (account_id,) in accounts:
        checked += 1
        # Find this account's largest single credit — the most likely R1 candidate.
        peak_row = conn.execute(
            "SELECT txn_id, amount, txn_datetime FROM transactions "
            "WHERE account_id=? AND direction='CR' ORDER BY amount DESC LIMIT 1",
            (account_id,),
        ).fetchone()
        if not peak_row:
            continue
        txn_id, amount, txn_dt = peak_row
        fires_r1, baseline, ratio = would_trigger_r1(conn, account_id, txn_dt, dev_mult)
        if not fires_r1:
            continue
        r1_only += 1
        fires_r2, pct = would_trigger_r2(conn, account_id, txn_dt, amount, pass_pct, window_h)
        if fires_r2:
            r1_and_r2 += 1
            if len(triggered_examples) < 8:
                triggered_examples.append({
                    "account_id": account_id, "txn_id": txn_id, "amount": amount,
                    "deviation_ratio": round(ratio, 1) if ratio else None, "pass_through_pct": round(pct, 1),
                })

    conn.close()
    return {
        "accounts_checked": checked,
        "r1_only_count": r1_only,
        "r1_and_r2_count": r1_and_r2,
        "examples": triggered_examples,
    }
