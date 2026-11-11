"""Pytest suite for StructuringEngine and AnomalyEngine."""

from datetime import datetime, timedelta, timezone

from app.anomaly_detection import AnomalyEngine
from app.structuring_engine import StructuringEngine


def _ts(hours: float = 0.0, days: int = 0) -> str:
    return (datetime(2026, 6, 15, 0, 0, 0, tzinfo=timezone.utc) + timedelta(days=days, hours=hours)).isoformat()


def test_structuring_detection_positive_and_negative() -> None:
    txs = [
        {"sender_account_id": "S1", "receiver_account_id": "R1", "amount": 85000, "transaction_timestamp": _ts(0)},
        {"sender_account_id": "S1", "receiver_account_id": "R2", "amount": 91000, "transaction_timestamp": _ts(3)},
        {"sender_account_id": "S1", "receiver_account_id": "R3", "amount": 99000, "transaction_timestamp": _ts(6)},
        # Outside window (>24h apart) for S2
        {"sender_account_id": "S2", "receiver_account_id": "R1", "amount": 85000, "transaction_timestamp": _ts(0)},
        {"sender_account_id": "S2", "receiver_account_id": "R2", "amount": 91000, "transaction_timestamp": _ts(30)},
        {"sender_account_id": "S2", "receiver_account_id": "R3", "amount": 99000, "transaction_timestamp": _ts(60)},
    ]
    assert len(StructuringEngine.detect_structuring_patterns(txs, "S1")) == 1
    assert len(StructuringEngine.detect_structuring_patterns(txs, "S2")) == 0


def test_repeated_counterparties() -> None:
    txs = [
        {"sender_account_id": "A", "receiver_account_id": "B", "amount": 10000, "transaction_timestamp": _ts(i)}
        for i in range(6)
    ]
    res = StructuringEngine.analyze_repeated_counterparties(txs, "A", min_count=5)
    assert len(res) == 1
    assert res[0]["counterparty_id"] == "B"
    assert res[0]["transaction_count"] == 6


def test_mule_rapid_passthrough_and_dormant() -> None:
    txs = [
        {"sender_account_id": "ORG", "receiver_account_id": "MULE", "amount": 200000, "transaction_timestamp": _ts(0)},
        {"sender_account_id": "MULE", "receiver_account_id": "END", "amount": 192000, "transaction_timestamp": _ts(1.5)},
    ]
    events = AnomalyEngine.detect_rapid_pass_through(txs, "MULE", max_delay_hours=2, retain_ratio_max=0.10)
    assert len(events) == 1
    assert events[0]["drain_ratio"] == 0.96

    dormant_txs = [
        {"sender_account_id": "D1", "receiver_account_id": "X", "amount": 500, "transaction_timestamp": _ts(days=0)},
        {"sender_account_id": "D1", "receiver_account_id": "Y", "amount": 150000, "transaction_timestamp": _ts(days=62)},
    ]
    d_events = AnomalyEngine.detect_dormant_activation(dormant_txs, "D1")
    assert len(d_events) == 1
    assert d_events[0]["dormant_gap_days"] == 62

