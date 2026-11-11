"""PHANTOM — Real-Time Pre-Transaction Screening Engine (Stage 2).

Evaluates incoming transactions in <500ms using an in-memory graph snapshot,
running incremental cycle, pass-through, structuring, dormant, device collision,
and counterparty checks without waiting for offline batch runs.
"""

from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

import networkx as nx

from .anomaly_detection import AnomalyEngine
from .blockchain import canonical_json, compute_hash
from .graph_analysis import TransactionGraphEngine
from .onboarding_risk import salted_hash
from .structuring_engine import StructuringEngine


class PreTransactionScreeningEngine:
    """Sub-500ms real-time transaction screening engine."""

    def __init__(
        self,
        graph_engine: TransactionGraphEngine | None = None,
        account_scores: dict[str, float] | None = None,
        account_last_activity: dict[str, datetime] | None = None,
        recent_transactions_by_account: dict[str, list[dict[str, Any]]] | None = None,
        device_ip_to_accounts: dict[str, set[str]] | None = None,
    ) -> None:
        self.graph_engine = graph_engine or TransactionGraphEngine()
        self.account_scores = account_scores or {}
        self.account_last_activity = account_last_activity or {}
        self.recent_txs = recent_transactions_by_account or defaultdict(list)
        self.device_ip_to_accounts = device_ip_to_accounts or defaultdict(set)
        self._decisions_cache: dict[str, dict[str, Any]] = {}

    def screen_transaction(self, tx: dict[str, Any]) -> dict[str, Any]:
        """Screen a single transaction and return explainable decision in <500ms."""
        t0 = time.perf_counter()
        tx_ref = str(tx.get("transaction_reference", ""))

        # Idempotency check: return cached decision if already evaluated
        if tx_ref and tx_ref in self._decisions_cache:
            cached = dict(self._decisions_cache[tx_ref])
            cached["is_cached"] = True
            return cached

        sender = str(tx.get("sender_account_id", ""))
        receiver = str(tx.get("receiver_account_id", ""))
        amount = float(tx.get("amount", 0.0))
        currency = str(tx.get("currency", "INR"))
        raw_ts = tx.get("transaction_timestamp") or tx.get("timestamp") or datetime.utcnow().isoformat()
        if isinstance(raw_ts, str):
            ts = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
        else:
            ts = raw_ts

        device_id = str(tx.get("device_id", "")).strip()
        raw_ip = str(tx.get("ip_address", "") or tx.get("ip_hash", "")).strip()
        ip_h = salted_hash(raw_ip) if raw_ip and not raw_ip.startswith("ip_hash_") else raw_ip

        rules_triggered: list[dict[str, Any]] = []
        total_score = 0.0

        # 1. Incremental RULE_001: Cycle closure check
        # If receiver already has a directed path back to sender within <= 4 hops, adding sender -> receiver closes a loop
        r001_score = 0.0
        r001_evidence = {}
        if sender in self.graph_engine.graph and receiver in self.graph_engine.graph:
            try:
                # Check shortest path from receiver to sender
                path = nx.shortest_path(self.graph_engine.graph, receiver, sender)
                if 2 <= len(path) <= 5:
                    r001_score = 25.0
                    r001_evidence = {"closing_cycle": path + [receiver], "cycle_length": len(path)}
                    rules_triggered.append({
                        "rule_id": "RULE_001",
                        "name": "Circular Money Flow (Cycle Closure)",
                        "score": 25.0,
                        "severity": "CRITICAL",
                        "reason": f"Transaction closes a {len(path)}-hop cycle ({' -> '.join(path[:3])}...)",
                        "evidence": r001_evidence,
                    })
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                pass
        total_score += r001_score

        # 2. Incremental RULE_002: Rapid pass-through / mule drain
        r002_score = 0.0
        sender_recent = self.recent_txs.get(sender, [])
        # Look for recent inflows within 2 hours
        two_hours_ago = ts - timedelta(hours=2)
        recent_inflows = [
            t for t in sender_recent
            if str(t.get("receiver_account_id")) == sender and t.get("_ts", ts) >= two_hours_ago
        ]
        if recent_inflows:
            inflow_sum = sum(float(t.get("amount", 0)) for t in recent_inflows)
            if inflow_sum > 0 and (amount / inflow_sum) >= 0.85:
                r002_score = 20.0
                rules_triggered.append({
                    "rule_id": "RULE_002",
                    "name": "Rapid Pass-Through / Mule Drain",
                    "score": 20.0,
                    "severity": "HIGH",
                    "reason": f"Payment drains {amount / inflow_sum * 100:.1f}% of recent inflow within 2 hours",
                    "evidence": {"inflow_amount": inflow_sum, "drain_ratio": round(amount / inflow_sum, 3)},
                })
        total_score += r002_score

        # 3. Incremental RULE_003: Structuring check
        r003_score = 0.0
        is_sub_threshold = (80_000 <= amount <= 99_999) or (450_000 <= amount <= 499_999)
        if is_sub_threshold:
            one_day_ago = ts - timedelta(hours=24)
            sender_outflows = [
                t for t in sender_recent
                if str(t.get("sender_account_id")) == sender and t.get("_ts", ts) >= one_day_ago
                and ((80_000 <= float(t.get("amount", 0)) <= 99_999) or (450_000 <= float(t.get("amount", 0)) <= 499_999))
            ]
            if len(sender_outflows) >= 2:  # this transaction makes it >= 3
                r003_score = 20.0
                rules_triggered.append({
                    "rule_id": "RULE_003",
                    "name": "Transaction Structuring (Smurfing)",
                    "score": 20.0,
                    "severity": "HIGH",
                    "reason": f"Extends structuring cluster to {len(sender_outflows) + 1} transfers below regulatory threshold",
                    "evidence": {"cluster_count": len(sender_outflows) + 1, "band": "Sub-reporting threshold"},
                })
        total_score += r003_score

        # 4. Incremental RULE_004: Dormant account surge
        r004_score = 0.0
        last_act = self.account_last_activity.get(sender)
        if last_act and (ts - last_act).days >= 60 and amount >= 100_000:
            r004_score = 15.0
            rules_triggered.append({
                "rule_id": "RULE_004",
                "name": "Dormant Account Surge",
                "score": 15.0,
                "severity": "MEDIUM",
                "reason": f"Sender dormant for {(ts - last_act).days} days followed by large transfer (Rs.{amount:,.0f})",
                "evidence": {"dormancy_days": (ts - last_act).days, "amount": amount},
            })
        total_score += r004_score

        # 5. Incremental RULE_005: Hardware / IP collision
        r005_score = 0.0
        device_collision = bool(device_id and len(self.device_ip_to_accounts.get(device_id, set()) - {sender}) >= 1)
        ip_collision = bool(ip_h and len(self.device_ip_to_accounts.get(ip_h, set()) - {sender}) >= 1)
        if device_collision or ip_collision:
            r005_score = 15.0
            rules_triggered.append({
                "rule_id": "RULE_005",
                "name": "Shared Identity / Device Collision",
                "score": 15.0,
                "severity": "HIGH",
                "reason": "Transaction submitted from hardware device or IP shared across distinct accounts",
                "evidence": {"device_collision": device_collision, "ip_collision": ip_collision},
            })
        total_score += r005_score

        # 6. Incremental RULE_007: Risky Counterparty
        r007_score = 0.0
        rcv_score = self.account_scores.get(receiver, 0.0)
        snd_score = self.account_scores.get(sender, 0.0)
        if rcv_score >= 60.0 or snd_score >= 60.0:
            r007_score = 15.0
            rules_triggered.append({
                "rule_id": "RULE_007",
                "name": "Suspicious Counterparty Association",
                "score": 15.0,
                "severity": "HIGH",
                "reason": f"Counterparty has elevated risk score (Receiver: {rcv_score:.1f}, Sender: {snd_score:.1f})",
                "evidence": {"receiver_risk": rcv_score, "sender_risk": snd_score},
            })
        total_score += r007_score

        # 7. Incremental RULE_008: Velocity Spike
        r008_score = 0.0
        one_hour_ago = ts - timedelta(hours=1)
        recent_hourly = [t for t in sender_recent if t.get("_ts", ts) >= one_hour_ago]
        if len(recent_hourly) >= 5:
            r008_score = 10.0
            rules_triggered.append({
                "rule_id": "RULE_008",
                "name": "Velocity Anomaly",
                "score": 10.0,
                "severity": "MEDIUM",
                "reason": f"High burst velocity: {len(recent_hourly) + 1} transactions in past 60 minutes",
                "evidence": {"hourly_count": len(recent_hourly) + 1},
            })
        total_score += r008_score

        final_score = round(min(100.0, total_score), 2)
        decision = self._classify_decision(final_score, rules_triggered)
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        reasons = [r["reason"] for r in rules_triggered]
        if not reasons:
            reasons = ["Transaction cleared all real-time fraud rules"]

        result = {
            "transaction_reference": tx_ref,
            "sender_account_id": sender,
            "receiver_account_id": receiver,
            "amount": amount,
            "currency": currency,
            "decision": decision,
            "risk_score": final_score,
            "rules_triggered": rules_triggered,
            "reasons": reasons,
            "evidence": {
                "sender_risk": snd_score,
                "receiver_risk": rcv_score,
                "rules_count": len(rules_triggered),
            },
            "latency_ms": latency_ms,
            "evaluated_at": datetime.utcnow().isoformat() + "Z",
            "is_cached": False,
        }

        if tx_ref:
            self._decisions_cache[tx_ref] = result

        return result

    def accept_transaction(self, tx: dict[str, Any]) -> dict[str, Any]:
        """Commit transaction to graph and state after approval."""
        sender = str(tx.get("sender_account_id", ""))
        receiver = str(tx.get("receiver_account_id", ""))
        amt = float(tx.get("amount", 0.0))
        raw_ts = tx.get("transaction_timestamp") or tx.get("timestamp") or datetime.utcnow().isoformat()
        ts = datetime.fromisoformat(raw_ts.replace("Z", "+00:00")) if isinstance(raw_ts, str) else raw_ts

        # Update in-memory graph
        if self.graph_engine.graph.has_edge(sender, receiver):
            self.graph_engine.graph[sender][receiver]["weight"] += amt
            self.graph_engine.graph[sender][receiver]["count"] += 1
        else:
            self.graph_engine.graph.add_edge(sender, receiver, weight=amt, count=1)

        # Update last activity
        self.account_last_activity[sender] = ts
        self.account_last_activity[receiver] = ts

        # Append to recent transactions
        stored_tx = {**tx, "_ts": ts, "amount": amt}
        self.recent_txs[sender].append(stored_tx)
        self.recent_txs[receiver].append(stored_tx)

        # Update device/IP index
        dev = str(tx.get("device_id", "")).strip()
        if dev:
            self.device_ip_to_accounts[dev].add(sender)
        ip = str(tx.get("ip_address", "") or tx.get("ip_hash", "")).strip()
        if ip:
            self.device_ip_to_accounts[ip].add(sender)

        # Compute canonical hash
        c_hash = compute_hash(tx)
        return {
            "status": "COMMITTED",
            "blockchain_hash": c_hash,
            "committed_at": datetime.utcnow().isoformat() + "Z",
        }

    @staticmethod
    def _classify_decision(score: float, rules_triggered: list[dict[str, Any]] | None = None) -> str:
        # Critical rule triggers like cycle closure escalate directly to HOLD_FOR_REVIEW or BLOCK
        has_critical = any(r.get("severity") == "CRITICAL" for r in (rules_triggered or []))
        if score >= 80.0:
            return "BLOCK"
        if score >= 60.0 or has_critical:
            return "HOLD_FOR_REVIEW"
        if score >= 20.0:
            return "ALLOW_WITH_MONITORING"
        return "ALLOW"
