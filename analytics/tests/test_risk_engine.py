"""Pytest suite for 8-factor RiskScoringEngine including Operation Phantom Ring."""

from datetime import datetime, timedelta, timezone

from app.graph_analysis import TransactionGraphEngine
from app.risk_engine import RiskScoringEngine


def _ts(hours_offset: float = 0.0, days_offset: int = 0) -> str:
    base = datetime(2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc)
    return (base + timedelta(days=days_offset, hours=hours_offset)).isoformat()


def test_risk_scoring_low_risk_negative() -> None:
    txs = [
        {"sender_account_id": "A1", "receiver_account_id": "M1", "amount": 500.0, "transaction_timestamp": _ts(0)},
        {"sender_account_id": "A1", "receiver_account_id": "M2", "amount": 1200.0, "transaction_timestamp": _ts(5)},
    ]
    g = TransactionGraphEngine()
    g.load_transactions(txs)
    res = RiskScoringEngine().score_account("A1", txs, graph_engine=g)
    assert res["risk_score"] == 0.0
    assert res["risk_level"] == "LOW"


def test_rule_001_circular_flow_positive() -> None:
    txs = [
        {"sender_account_id": "A", "receiver_account_id": "B", "amount": 50000.0, "transaction_timestamp": _ts(0)},
        {"sender_account_id": "B", "receiver_account_id": "C", "amount": 49000.0, "transaction_timestamp": _ts(1)},
        {"sender_account_id": "C", "receiver_account_id": "A", "amount": 48000.0, "transaction_timestamp": _ts(2)},
    ]
    g = TransactionGraphEngine()
    g.load_transactions(txs)
    res = RiskScoringEngine().score_account("A", txs, graph_engine=g)
    r001 = next(f for f in res["factors"] if f["rule"] == "RULE_001")
    assert r001["score"] == 12.5


def test_rule_002_rapid_passthrough_positive() -> None:
    txs = [
        {"sender_account_id": "SRC", "receiver_account_id": "MULE", "amount": 100000.0, "transaction_timestamp": _ts(0)},
        {"sender_account_id": "MULE", "receiver_account_id": "DST", "amount": 96000.0, "transaction_timestamp": _ts(1)},
    ]
    res = RiskScoringEngine().score_account("MULE", txs)
    r002 = next(f for f in res["factors"] if f["rule"] == "RULE_002")
    assert r002["score"] == 20.0


def test_rule_003_structuring_positive() -> None:
    txs = [
        {"sender_account_id": "SMURF", "receiver_account_id": "R1", "amount": 85000.0, "transaction_timestamp": _ts(0)},
        {"sender_account_id": "SMURF", "receiver_account_id": "R2", "amount": 92000.0, "transaction_timestamp": _ts(2)},
        {"sender_account_id": "SMURF", "receiver_account_id": "R3", "amount": 97000.0, "transaction_timestamp": _ts(4)},
    ]
    res = RiskScoringEngine().score_account("SMURF", txs)
    r003 = next(f for f in res["factors"] if f["rule"] == "RULE_003")
    assert r003["score"] == 20.0


def test_rule_004_dormant_surge_positive_and_negative() -> None:
    txs_pos = [
        {"sender_account_id": "D1", "receiver_account_id": "X1", "amount": 1000.0, "transaction_timestamp": _ts(days_offset=0)},
        {"sender_account_id": "D1", "receiver_account_id": "X2", "amount": 250000.0, "transaction_timestamp": _ts(days_offset=65)},
    ]
    res_pos = RiskScoringEngine().score_account("D1", txs_pos)
    assert next(f for f in res_pos["factors"] if f["rule"] == "RULE_004")["score"] == 15.0

    txs_neg = [
        {"sender_account_id": "D2", "receiver_account_id": "X1", "amount": 1000.0, "transaction_timestamp": _ts(days_offset=0)},
        {"sender_account_id": "D2", "receiver_account_id": "X2", "amount": 250000.0, "transaction_timestamp": _ts(days_offset=10)},
    ]
    res_neg = RiskScoringEngine().score_account("D2", txs_neg)
    assert next(f for f in res_neg["factors"] if f["rule"] == "RULE_004")["score"] == 0.0


def test_rule_005_shared_identity_and_rule_007_counterparty() -> None:
    txs = [
        {"sender_account_id": "U1", "receiver_account_id": "BAD1", "amount": 25000.0, "transaction_timestamp": _ts(0)},
        {"sender_account_id": "BAD2", "receiver_account_id": "U1", "amount": 25000.0, "transaction_timestamp": _ts(1)},
    ]
    g = TransactionGraphEngine()
    g.load_transactions(txs)
    res = RiskScoringEngine().score_account(
        "U1",
        txs,
        identity_attrs=[{"attribute_type": "DEVICE", "is_collision": True}],
        graph_engine=g,
        counterparty_flags={"BAD1": True, "BAD2": True},
        velocity_spikes=[{"burst_24h": 12}],
    )
    assert next(f for f in res["factors"] if f["rule"] == "RULE_005")["score"] == 7.5
    assert next(f for f in res["factors"] if f["rule"] == "RULE_007")["score"] == 10.0
    assert next(f for f in res["factors"] if f["rule"] == "RULE_008")["score"] == 5.0


def test_score_cap_at_100() -> None:
    # Trigger all 8 rules to exceed 100 raw points (max sum = 135) -> must cap at 100.0
    txs = [
        {"sender_account_id": "X", "receiver_account_id": "A", "amount": 1000.0, "transaction_timestamp": _ts(days_offset=-70)},
        {"sender_account_id": "X", "receiver_account_id": "A", "amount": 95000.0, "transaction_timestamp": _ts(0)},
        {"sender_account_id": "A", "receiver_account_id": "B", "amount": 95000.0, "transaction_timestamp": _ts(0.2)},
        {"sender_account_id": "B", "receiver_account_id": "X", "amount": 94000.0, "transaction_timestamp": _ts(0.4)},
        {"sender_account_id": "X", "receiver_account_id": "C", "amount": 91000.0, "transaction_timestamp": _ts(0.5)},
        {"sender_account_id": "C", "receiver_account_id": "X", "amount": 90000.0, "transaction_timestamp": _ts(0.6)},
        {"sender_account_id": "X", "receiver_account_id": "D", "amount": 88000.0, "transaction_timestamp": _ts(0.7)},
    ]
    g = TransactionGraphEngine()
    g.load_transactions(txs)
    res = RiskScoringEngine().score_account(
        "X",
        txs,
        identity_attrs=[{"is_collision": True}, {"is_collision": True}],
        graph_engine=g,
        counterparty_flags={"A": True, "B": True, "C": True},
        velocity_spikes=[{"s": 1}, {"s": 2}],
    )
    assert res["risk_score"] == 100.0
    assert res["risk_level"] == "CRITICAL"


def test_operation_phantom_ring_scores_94_critical() -> None:
    """Verify Documentation Section 16: Operation Phantom Ring scores exactly 94.0 CRITICAL
    with RULE_001, RULE_002, RULE_003, RULE_005, and RULE_006 triggered."""
    txs = [
        # Core 3-hop RTGS cycle (Rs.480K -> Rs.470K -> Rs.465K = Rs.1,415,000 in 4.25h)
        {
            "sender_account_id": "ACC-0001-9041",
            "receiver_account_id": "ACC-0044-7721",
            "amount": 480000.0,
            "transaction_timestamp": "2026-06-15T10:00:00+00:00",
        },
        {
            "sender_account_id": "ACC-0044-7721",
            "receiver_account_id": "ACC-0078-3319",
            "amount": 470000.0,
            "transaction_timestamp": "2026-06-15T11:45:00+00:00",
        },
        {
            "sender_account_id": "ACC-0078-3319",
            "receiver_account_id": "ACC-0001-9041",
            "amount": 465000.0,
            "transaction_timestamp": "2026-06-15T14:15:00+00:00",
        },
        # Structuring splits below Rs.5L threshold from ACC-0044-7721
        {
            "sender_account_id": "ACC-0044-7721",
            "receiver_account_id": "ACC-EXT-1",
            "amount": 490000.0,
            "transaction_timestamp": "2026-06-15T12:10:00+00:00",
        },
        {
            "sender_account_id": "ACC-0044-7721",
            "receiver_account_id": "ACC-EXT-2",
            "amount": 485000.0,
            "transaction_timestamp": "2026-06-15T12:20:00+00:00",
        },
    ]
    g = TransactionGraphEngine()
    g.load_transactions(txs)
    res = RiskScoringEngine().score_account(
        account_id="ACC-0044-7721",
        transactions=txs,
        identity_attrs=[
            {"attribute_type": "DEVICE", "value": "DEV-PHANTOM-103", "is_collision": True},
            {"attribute_type": "IP", "value": "103.21.***.44", "is_collision": True},
        ],
        graph_engine=g,
        structuring_threshold_min=450_000,
        structuring_threshold_max=499_999,
    )
    triggered = {f["rule"]: f["score"] for f in res["factors"] if f["score"] > 0}
    assert triggered == {
        "RULE_001": 24.0,
        "RULE_002": 20.0,
        "RULE_003": 20.0,
        "RULE_005": 15.0,
        "RULE_006": 15.0,
    }
    assert res["risk_score"] == 94.0
    assert res["risk_level"] == "CRITICAL"

