"""Pytest suite for TransactionGraphEngine & network_analysis."""

from datetime import datetime, timedelta, timezone

from app.graph_analysis import TransactionGraphEngine
from app.network_analysis import analyze_network


def _ts(hours: float) -> str:
    return (datetime(2026, 6, 15, 0, 0, 0, tzinfo=timezone.utc) + timedelta(hours=hours)).isoformat()


def test_cycle_detection_and_time_window() -> None:
    txs = [
        {"sender_account_id": "A", "receiver_account_id": "B", "amount": 50000, "transaction_timestamp": _ts(0)},
        {"sender_account_id": "B", "receiver_account_id": "C", "amount": 49000, "transaction_timestamp": _ts(2)},
        {"sender_account_id": "C", "receiver_account_id": "A", "amount": 48000, "transaction_timestamp": _ts(4)},
        # Slow cycle (> 72h)
        {"sender_account_id": "X", "receiver_account_id": "Y", "amount": 50000, "transaction_timestamp": _ts(0)},
        {"sender_account_id": "Y", "receiver_account_id": "X", "amount": 50000, "transaction_timestamp": _ts(100)},
    ]
    g = TransactionGraphEngine()
    g.load_transactions(txs)
    cycles = g.detect_cycles(max_length=5, time_window_hours=72)
    assert len(cycles) == 1
    assert set(cycles[0]["cycle"]) == {"A", "B", "C"}
    assert cycles[0]["total_volume"] == 147000.0


def test_centrality_and_hub_classification() -> None:
    txs = []
    # Star hub H receiving from 5 nodes and sending to 5 nodes (degree = 10 -> hub)
    for i in range(5):
        txs.append({"sender_account_id": f"IN_{i}", "receiver_account_id": "HUB", "amount": 10000, "transaction_timestamp": _ts(i)})
        txs.append({"sender_account_id": "HUB", "receiver_account_id": f"OUT_{i}", "amount": 9500, "transaction_timestamp": _ts(i + 1)})
    g = TransactionGraphEngine()
    g.load_transactions(txs)
    cents = g.calculate_centralities()
    assert cents["HUB"]["is_hub"] is True
    assert cents["HUB"]["raw_degree"] == 10


def test_shortest_path_and_ego_subgraph() -> None:
    txs = [
        {"sender_account_id": "A", "receiver_account_id": "B", "amount": 1000, "transaction_timestamp": _ts(0)},
        {"sender_account_id": "B", "receiver_account_id": "C", "amount": 2000, "transaction_timestamp": _ts(1)},
    ]
    g = TransactionGraphEngine()
    g.load_transactions(txs)
    sp = g.find_shortest_path("A", "C")
    assert sp is not None
    assert sp["path"] == ["A", "B", "C"]
    assert sp["total_volume"] == 3000.0
    assert g.find_shortest_path("C", "A") is None

    ego = g.get_neighbors_subgraph("B", depth=1)
    assert len(ego["nodes"]) == 3
    assert len(ego["edges"]) == 2


def test_network_analysis_communities() -> None:
    txs = [
        {"sender_account_id": "A", "receiver_account_id": "B", "amount": 60000, "transaction_timestamp": _ts(0)},
        {"sender_account_id": "B", "receiver_account_id": "C", "amount": 60000, "transaction_timestamp": _ts(1)},
        {"sender_account_id": "C", "receiver_account_id": "A", "amount": 60000, "transaction_timestamp": _ts(2)},
    ]
    res = analyze_network(txs)
    assert res["node_count"] == 3
    assert res["edge_count"] == 3
    assert any(c["suspicious"] for c in res["communities"])

