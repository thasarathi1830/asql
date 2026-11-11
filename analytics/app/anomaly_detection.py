"""PHANTOM Analytics — Anomaly detection (rapid pass-through & dormant activation)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


def _parse_ts(tx: dict[str, Any]) -> datetime:
    ts = tx.get("transaction_timestamp") or tx.get("transaction_date") or tx.get("created_at")
    if isinstance(ts, datetime):
        return ts
    if isinstance(ts, str):
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    raise ValueError("Transaction missing valid timestamp")


class AnomalyEngine:
    """Detects behavioural anomalies on per-account transaction streams."""

    # ── Rapid pass-through ────────────────────────────────────────────

    @staticmethod
    def detect_rapid_pass_through(
        transactions: list[dict[str, Any]],
        account_id: str,
        max_delay_hours: int = 2,
        retain_ratio_max: float = 0.10,
    ) -> list[dict[str, Any]]:
        """Detect rapid pass-through (mule) behaviour.

        A pass-through event is recognised when:
        1. An inflow is followed by an outflow within *max_delay_hours*.
        2. The account retains <= *retain_ratio_max* of the inflow amount
           (drain ratio >= 0.85).
        """
        inflows: list[dict[str, Any]] = []
        outflows: list[dict[str, Any]] = []

        for tx in transactions:
            is_in = str(tx.get("receiver_account_id")) == account_id
            is_out = str(tx.get("sender_account_id")) == account_id
            if not (is_in or is_out):
                continue
            ts = _parse_ts(tx)
            entry = {**tx, "_ts": ts, "amount": float(tx["amount"])}
            if is_in:
                inflows.append(entry)
            if is_out:
                outflows.append(entry)

        if not inflows or not outflows:
            return []

        inflows.sort(key=lambda x: x["_ts"])
        outflows.sort(key=lambda x: x["_ts"])

        events: list[dict[str, Any]] = []
        used_outflows: set[int] = set()

        for inf in inflows:
            matched_out_total = 0.0
            for j, outf in enumerate(outflows):
                if j in used_outflows:
                    continue
                delay = outf["_ts"] - inf["_ts"]
                if timedelta(0) <= delay <= timedelta(hours=max_delay_hours):
                    matched_out_total += outf["amount"]
                    used_outflows.add(j)

            if inf["amount"] > 0 and matched_out_total > 0:
                drain_ratio = matched_out_total / inf["amount"]
                retain_ratio = abs(inf["amount"] - matched_out_total) / inf["amount"]
                if drain_ratio >= (1.0 - max(0.15, retain_ratio_max)) and retain_ratio <= retain_ratio_max:
                    events.append({
                        "inflow_amount": inf["amount"],
                        "outflow_total": matched_out_total,
                        "drain_ratio": round(drain_ratio, 4),
                        "retain_ratio": round(retain_ratio, 4),
                        "inflow_time": inf["_ts"].isoformat(),
                    })

        return events

    # ── Dormant-account activation ────────────────────────────────────

    @staticmethod
    def detect_dormant_activation(
        transactions: list[dict[str, Any]],
        account_id: str,
        dormant_days: int = 60,
        min_burst_amount: float = 100_000,
    ) -> list[dict[str, Any]]:
        """Detect dormant accounts that suddenly burst with activity."""
        acct_txs: list[dict[str, Any]] = []
        for tx in transactions:
            if str(tx.get("sender_account_id")) == account_id or str(tx.get("receiver_account_id")) == account_id:
                ts = _parse_ts(tx)
                acct_txs.append({**tx, "_ts": ts, "amount": float(tx["amount"])})

        if len(acct_txs) < 2:
            return []

        acct_txs.sort(key=lambda x: x["_ts"])

        events: list[dict[str, Any]] = []
        for i in range(1, len(acct_txs)):
            gap = acct_txs[i]["_ts"] - acct_txs[i - 1]["_ts"]
            if gap >= timedelta(days=dormant_days):
                burst_amount = sum(t["amount"] for t in acct_txs[i:])
                if burst_amount >= min_burst_amount:
                    events.append({
                        "dormant_gap_days": gap.days,
                        "burst_start": acct_txs[i]["_ts"].isoformat(),
                        "burst_amount": burst_amount,
                        "last_activity_before": acct_txs[i - 1]["_ts"].isoformat(),
                    })
        return events
