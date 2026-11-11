"""PHANTOM Analytics — Transaction graph engine (NetworkX)."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

import networkx as nx


def _parse_ts(tx: dict[str, Any]) -> datetime | None:
    ts = tx.get("transaction_timestamp") or tx.get("transaction_date") or tx.get("created_at")
    if not ts:
        return None
    if isinstance(ts, datetime):
        return ts
    if isinstance(ts, str):
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return None


class TransactionGraphEngine:
    """Build and analyse a directed transaction graph."""

    def __init__(self) -> None:
        self.graph: nx.DiGraph = nx.DiGraph()
        self._transactions: list[dict[str, Any]] = []
        self._cached_cycles: dict[tuple[int, int], list[dict[str, Any]]] = {}
        self._cached_centralities: dict[str, dict[str, Any]] | None = None

    # ── Graph construction ────────────────────────────────────────────

    def load_transactions(self, transactions: list[dict[str, Any]]) -> None:
        """Build a :class:`nx.DiGraph` with aggregated edge weights."""
        self._transactions = list(transactions)
        self.graph = nx.DiGraph()
        self._cached_cycles = {}
        self._cached_centralities = None

        edge_agg: dict[tuple[str, str], dict[str, Any]] = defaultdict(
            lambda: {"total_amount": 0.0, "count": 0, "timestamps": []}
        )

        for tx in transactions:
            src = str(tx["sender_account_id"])
            dst = str(tx["receiver_account_id"])
            amt = float(tx["amount"])
            ts = _parse_ts(tx)
            edge_agg[(src, dst)]["total_amount"] += amt
            edge_agg[(src, dst)]["count"] += 1
            if ts is not None:
                edge_agg[(src, dst)]["timestamps"].append(ts)

        for (src, dst), data in edge_agg.items():
            self.graph.add_edge(
                src,
                dst,
                weight=data["total_amount"],
                count=data["count"],
                timestamps=sorted(data["timestamps"]),
            )

    # ── Cycle detection ───────────────────────────────────────────────

    def detect_cycles(
        self,
        max_length: int = 5,
        time_window_hours: int = 72,
    ) -> list[dict[str, Any]]:
        """Detect simple cycles up to *max_length* with optional time-window filter."""
        cache_key = (max_length, time_window_hours)
        if cache_key in self._cached_cycles:
            return self._cached_cycles[cache_key]

        results: list[dict[str, Any]] = []
        # On massive graphs, prune to nodes with both in_degree >= 1 and out_degree >= 1 (strongly connected >= 2)
        for scc in nx.strongly_connected_components(self.graph):
            if len(scc) < 2:
                continue
            sub = self.graph.subgraph(scc)
            for cycle in nx.simple_cycles(sub, length_bound=max_length):
                if len(cycle) < 2:
                    continue

                all_ts: list[datetime] = []
                total_volume = 0.0
                for i in range(len(cycle)):
                    src = cycle[i]
                    dst = cycle[(i + 1) % len(cycle)]
                    edata = sub.get_edge_data(src, dst)
                    if edata:
                        all_ts.extend(edata.get("timestamps", []))
                        total_volume += edata.get("weight", 0.0)

                if all_ts:
                    span = max(all_ts) - min(all_ts)
                    if span > timedelta(hours=time_window_hours):
                        continue

                risk_boost = min(25.0, 12.5 * len(cycle) / max_length * 2)
                results.append({
                    "cycle": cycle,
                    "length": len(cycle),
                    "total_volume": round(total_volume, 2),
                    "risk_boost": round(risk_boost, 2),
                })

        self._cached_cycles[cache_key] = results
        return results

    # ── Centrality metrics ────────────────────────────────────────────

    def calculate_centralities(self) -> dict[str, dict[str, Any]]:
        """Return centrality metrics for every node."""
        if self._cached_centralities is not None:
            return self._cached_centralities

        g = self.graph
        n = g.number_of_nodes()
        if n == 0:
            return {}

        k_sample = min(n, 80) if n > 150 else None
        betweenness = nx.betweenness_centrality(
            g, k=k_sample, weight="weight", seed=42 if k_sample else None
        )
        degree = nx.degree_centrality(g)
        in_deg = nx.in_degree_centrality(g)
        out_deg = nx.out_degree_centrality(g)
        try:
            pagerank = nx.pagerank(g, weight="weight")
        except nx.PowerIterationFailedConvergence:
            pagerank = {node: 0.0 for node in g.nodes}

        result: dict[str, dict[str, Any]] = {}
        for node in g.nodes:
            b = betweenness.get(node, 0.0)
            d = g.degree(node)
            is_hub = b > 0.40 or d >= 10
            result[node] = {
                "betweenness": round(b, 4),
                "degree": round(degree.get(node, 0.0), 4),
                "in_degree": round(in_deg.get(node, 0.0), 4),
                "out_degree": round(out_deg.get(node, 0.0), 4),
                "pagerank": round(pagerank.get(node, 0.0), 6),
                "is_hub": is_hub,
                "raw_degree": d,
            }
        self._cached_centralities = result
        return result

    # ── Shortest path ─────────────────────────────────────────────────

    def find_shortest_path(
        self, source: str, target: str
    ) -> dict[str, Any] | None:
        """Return shortest path between *source* and *target* with total volume."""
        try:
            path = nx.shortest_path(self.graph, source, target)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

        volume = 0.0
        for i in range(len(path) - 1):
            edata = self.graph.get_edge_data(path[i], path[i + 1])
            if edata:
                volume += edata.get("weight", 0.0)
        return {"path": path, "total_volume": volume}

    # ── Ego sub-graph ─────────────────────────────────────────────────

    def get_neighbors_subgraph(
        self, node_id: str, depth: int = 1
    ) -> dict[str, Any]:
        """BFS ego subgraph serialised for Cytoscape."""
        if node_id not in self.graph:
            return {"nodes": [], "edges": []}

        ego = nx.ego_graph(self.graph.to_undirected(), node_id, radius=depth)
        sub = self.graph.subgraph(ego.nodes)
        nodes = [{"data": {"id": n}} for n in sub.nodes]
        edges = [
            {
                "data": {
                    "source": u,
                    "target": v,
                    "weight": d.get("weight", 0),
                }
            }
            for u, v, d in sub.edges(data=True)
        ]
        return {"nodes": nodes, "edges": edges}

    # ── Community detection ───────────────────────────────────────────

    def detect_communities(
        self, min_members: int = 3, min_volume: float = 100_000
    ) -> list[dict[str, Any]]:
        """Greedy modularity communities on the undirected projection."""
        ug = self.graph.to_undirected()
        if ug.number_of_nodes() == 0:
            return []

        communities = list(nx.community.greedy_modularity_communities(ug, weight="weight"))
        results: list[dict[str, Any]] = []
        for idx, comm in enumerate(communities):
            members = list(comm)
            sub = self.graph.subgraph(members)
            volume = sum(d.get("weight", 0) for _, _, d in sub.edges(data=True))
            suspicious = len(members) >= min_members and volume > min_volume
            results.append({
                "community_id": idx,
                "members": members,
                "member_count": len(members),
                "total_volume": round(volume, 2),
                "suspicious": suspicious,
            })
        return results
