"""PHANTOM Analytics — Structuring / smurfing detection."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any


def _parse_ts(tx: dict[str, Any]) -> datetime:
    ts = tx.get("transaction_timestamp") or tx.get("transaction_date") or tx.get("created_at")
    if isinstance(ts, datetime):
        return ts
    if isinstance(ts, str):
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    raise ValueError("Transaction missing valid timestamp")


class StructuringEngine:
    """Detect transaction structuring (smurfing) patterns."""

    @staticmethod
    def detect_structuring_patterns(
        transactions: list[dict[str, Any]],
        account_id: str,
        threshold_min: float = 80_000,
        threshold_max: float = 99_999,
        window_hours: int = 24,
        min_tx_count: int = 3,
        extra_bands: list[tuple[float, float]] | None = None,
    ) -> list[dict[str, Any]]:
        """Find clusters of transactions just below regulatory reporting thresholds.

        Flags when >= *min_tx_count* transactions from *account_id* fall within
        [*threshold_min*, *threshold_max*] (or any band in *extra_bands*) inside
        a sliding *window_hours* window.
        """
        bands = [(threshold_min, threshold_max)]
        if extra_bands:
            bands.extend(extra_bands)

        patterns: list[dict[str, Any]] = []
        for low, high in bands:
            relevant: list[dict[str, Any]] = []
            for tx in transactions:
                if str(tx.get("sender_account_id")) != account_id:
                    continue
                amt = float(tx["amount"])
                if low <= amt <= high:
                    relevant.append({**tx, "_ts": _parse_ts(tx), "amount": amt})

            if len(relevant) < min_tx_count:
                continue

            relevant.sort(key=lambda x: x["_ts"])
            i = 0
            while i < len(relevant):
                window_end = relevant[i]["_ts"] + timedelta(hours=window_hours)
                cluster = [relevant[i]]
                j = i + 1
                while j < len(relevant) and relevant[j]["_ts"] <= window_end:
                    cluster.append(relevant[j])
                    j += 1

                if len(cluster) >= min_tx_count:
                    patterns.append({
                        "account_id": account_id,
                        "band": f"{int(low)}-{int(high)}",
                        "transaction_count": len(cluster),
                        "total_amount": sum(c["amount"] for c in cluster),
                        "window_start": cluster[0]["_ts"].isoformat(),
                        "window_end": cluster[-1]["_ts"].isoformat(),
                        "amounts": [c["amount"] for c in cluster],
                    })
                i = j if j > i + 1 else i + 1

        return patterns

    @staticmethod
    def analyze_repeated_counterparties(
        transactions: list[dict[str, Any]],
        account_id: str,
        min_count: int = 5,
    ) -> list[dict[str, Any]]:
        """Identify counterparties transacted with >= *min_count* times."""
        counter: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"count": 0, "total_amount": 0.0}
        )

        for tx in transactions:
            sender = str(tx.get("sender_account_id", ""))
            receiver = str(tx.get("receiver_account_id", ""))
            amt = float(tx["amount"])

            if sender == account_id and receiver != account_id:
                counter[receiver]["count"] += 1
                counter[receiver]["total_amount"] += amt
            elif receiver == account_id and sender != account_id:
                counter[sender]["count"] += 1
                counter[sender]["total_amount"] += amt

        return [
            {
                "counterparty_id": cp,
                "transaction_count": data["count"],
                "total_amount": data["total_amount"],
            }
            for cp, data in counter.items()
            if data["count"] >= min_count
        ]
