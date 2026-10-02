"""Deterministic pass-through alert calculation for a newly supplied transaction batch.

This is a calculation component, not a live bank connection. A caller must
authenticate and validate a real source before exposing it as an API. It flags
activity for review; it cannot decide whether money is lawful or trace fungible
funds through subsequent accounts.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation


REQUIRED_FIELDS = {"txn_id", "account_id", "txn_datetime", "direction", "amount",
                   "status", "counterparty_account_id"}


def _when(value: object) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError("Transaction timestamps must be ISO 8601 dates/times") from exc
    if parsed.tzinfo is not None:
        raise ValueError("Use one consistent local ledger time zone; mixed time zones are not supported")
    return parsed


def validate_batch(rows: list[dict]) -> list[dict]:
    """Normalize a small fictional feed without executing or trusting source text."""
    if not rows or len(rows) > 500:
        raise ValueError("Provide 1–500 transaction rows")
    seen = set()
    normalized = []
    for index, raw in enumerate(rows, start=1):
        missing = REQUIRED_FIELDS - set(raw)
        if missing:
            raise ValueError(f"Row {index} is missing: {', '.join(sorted(missing))}")
        txn_id = str(raw["txn_id"]).strip()
        account_id = str(raw["account_id"]).strip()
        if not txn_id or not account_id or txn_id in seen:
            raise ValueError(f"Row {index} has an empty or duplicate transaction/account ID")
        seen.add(txn_id)
        direction = str(raw["direction"]).strip().upper()
        if direction not in {"CR", "DR"}:
            raise ValueError(f"Row {index} direction must be CR or DR")
        status = str(raw["status"]).strip().title()
        if status not in {"Completed", "Pending"}:
            raise ValueError(f"Row {index} status must be Completed or Pending")
        try:
            amount = Decimal(str(raw["amount"]).strip())
        except InvalidOperation as exc:
            raise ValueError(f"Row {index} amount is not numeric") from exc
        if not amount.is_finite() or amount <= 0:
            raise ValueError(f"Row {index} amount must be finite and positive")
        counterparty = str(raw.get("counterparty_account_id") or "").strip()
        normalized.append({"txn_id": txn_id, "account_id": account_id,
                           "txn_datetime": _when(raw["txn_datetime"]),
                           "direction": direction, "amount": amount,
                           "status": status, "counterparty_account_id": counterparty})
    return sorted(normalized, key=lambda row: row["txn_datetime"])


def detect_pass_through(rows: list[dict], monthly_baseline: object,
                        multiplier: object = 5, outbound_percent: object = 80,
                        minimum_beneficiaries: int = 3) -> list[dict]:
    """Evaluate non-overlapping 24h windows anchored at the first credit.

    R1 uses aggregate incoming value versus a supplied historical monthly
    average. R2 compares aggregate outgoing value and distinct beneficiaries.
    This is an account-activity proxy, never proof that a receipt funded a debit.
    """
    entries = validate_batch(rows)
    try:
        baseline = Decimal(str(monthly_baseline))
        ratio_threshold = Decimal(str(multiplier))
        outbound_threshold = Decimal(str(outbound_percent))
    except InvalidOperation as exc:
        raise ValueError("Baseline and thresholds must be numeric") from exc
    if not all(value.is_finite() for value in (baseline, ratio_threshold, outbound_threshold)):
        raise ValueError("Baseline and thresholds must be finite")
    if baseline <= 0 or ratio_threshold <= 0 or not 0 < outbound_threshold <= 100 or minimum_beneficiaries < 1:
        raise ValueError("Baseline and thresholds must be positive; outbound percent must not exceed 100")
    account_ids = {row["account_id"] for row in entries}
    if len(account_ids) != 1:
        raise ValueError("A batch must contain one monitored account; submit accounts separately")

    completed = [row for row in entries if row["status"] == "Completed"]
    candidates = []
    covered_until = None
    for anchor in completed:
        if anchor["direction"] != "CR" or (covered_until is not None and anchor["txn_datetime"] <= covered_until):
            continue
        end = anchor["txn_datetime"] + timedelta(hours=24)
        covered_until = end
        window = [row for row in completed if anchor["txn_datetime"] <= row["txn_datetime"] <= end]
        incoming = [row for row in window if row["direction"] == "CR"]
        outgoing = [row for row in window if row["direction"] == "DR"]
        total_in = sum((row["amount"] for row in incoming), Decimal(0))
        total_out = sum((row["amount"] for row in outgoing), Decimal(0))
        beneficiaries = {row["counterparty_account_id"] for row in outgoing if row["counterparty_account_id"]}
        ratio = total_in / baseline
        outbound_ratio = total_out / total_in * 100 if total_in else Decimal(0)
        if ratio >= ratio_threshold and outbound_ratio >= outbound_threshold and len(beneficiaries) >= minimum_beneficiaries:
            candidates.append({
                "account_id": anchor["account_id"], "window_start": anchor["txn_datetime"].isoformat(),
                "window_end": end.isoformat(), "incoming": float(total_in), "outgoing": float(total_out),
                "baseline": float(baseline), "incoming_multiplier": round(float(ratio), 2),
                "outbound_percent": round(float(outbound_ratio), 2),
                "beneficiary_count": len(beneficiaries),
                "credit_txn_ids": [row["txn_id"] for row in incoming],
                "debit_txn_ids": [row["txn_id"] for row in outgoing],
                "assessment": "Activity meets illustrative review thresholds; no finding of unlawful funds.",
            })
    # Earliest qualifying non-overlapping window gives one stable signal for
    # this small batch. A production monitor would need durable deduplication.
    return candidates[:1]


def make_fictional_lab_batch(incoming_amount: int, outgoing_amount: int) -> list[dict]:
    """Create ten clearly fictional rows for the read-only on-site rule lab.

    No identity, bank account number, user-uploaded file, or saved case is
    involved. Altering either amount changes the monitor's actual input.
    """
    for label, value in (("Incoming", incoming_amount), ("Outgoing", outgoing_amount)):
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100_000_000:
            raise ValueError(f"{label} amount must be an integer between 1 and 100,000,000")
    rows = []
    for index in range(1, 11):
        credit = index <= 4
        rows.append({
            "txn_id": f"TXN-LAB-{index:02d}",
            "account_id": "ACC-LAB-001",
            "txn_datetime": f"2026-10-01T09:{(index-1)*10:02d}:00" if index <= 6 else
                            f"2026-10-01T10:{(index-7)*10:02d}:00",
            "direction": "CR" if credit else "DR",
            "amount": incoming_amount if credit else outgoing_amount,
            "status": "Completed",
            "counterparty_account_id": f"EXT-LAB-{'S' if credit else 'B'}{index if credit else index-4:02d}",
        })
    return rows
