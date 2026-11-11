"""PHANTOM Analytics — Network analysis wrapper (hub & community detection)."""

from __future__ import annotations

from typing import Any

from .graph_analysis import TransactionGraphEngine


def analyze_network(
    transactions: list[dict[str, Any]],
) -> dict[str, Any]:
    """High-level wrapper: build graph → centralities + communities."""
    engine = TransactionGraphEngine()
    engine.load_transactions(transactions)

    centralities = engine.calculate_centralities()
    communities = engine.detect_communities()

    hubs = [
        node_id
        for node_id, metrics in centralities.items()
        if metrics.get("is_hub")
    ]

    return {
        "centralities": centralities,
        "communities": communities,
        "hubs": hubs,
        "node_count": engine.graph.number_of_nodes(),
        "edge_count": engine.graph.number_of_edges(),
    }
