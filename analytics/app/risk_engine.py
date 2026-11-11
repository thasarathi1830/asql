"""PHANTOM Analytics — Risk scoring engine (8 explainable rules)."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from .anomaly_detection import AnomalyEngine
from .config import RISK_PROFILES, RULE_WEIGHTS
from .graph_analysis import TransactionGraphEngine
from .structuring_engine import StructuringEngine


def _risk_level(score: float) -> str:
    if score >= 80:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 30:
        return "MEDIUM"
    return "LOW"


def _parse_ts(tx: dict[str, Any]) -> datetime | None:
    ts = tx.get("transaction_timestamp") or tx.get("transaction_date") or tx.get("created_at")
    if not ts:
        return None
    if isinstance(ts, datetime):
        return ts
    if isinstance(ts, str):
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return None


class RiskScoringEngine:
    """Score an account's risk across 8 explainable rules (0-100)."""

    def __init__(
        self,
        rule_weights: dict[str, int] | None = None,
        profile: str = "default",
    ) -> None:
        self.weights = dict(rule_weights or RULE_WEIGHTS)
        self.profile_name = profile
        self.profile = dict(RISK_PROFILES.get(profile, RISK_PROFILES["default"]))

    def score_account(
        self,
        account_id: str,
        transactions: list[dict[str, Any]],
        identity_attrs: list[dict[str, Any]] | None = None,
        graph_engine: TransactionGraphEngine | None = None,
        counterparty_flags: dict[str, bool] | None = None,
        velocity_spikes: list[dict[str, Any]] | None = None,
        structuring_threshold_min: float | None = None,
        structuring_threshold_max: float | None = None,
        structuring_window_hours: int | None = None,
        structuring_min_tx_count: int | None = None,
        rapid_pass_max_delay_hours: int | None = None,
        rapid_pass_retain_ratio_max: float | None = None,
        dormant_days: int | None = None,
        dormant_min_burst: float | None = None,
        precomputed_cycles: list[dict[str, Any]] | None = None,
        precomputed_centralities: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Score *account_id* and return breakdown with human explanation."""
        tmin = self.profile["structuring_threshold_min"] if structuring_threshold_min is None else structuring_threshold_min
        tmax = self.profile["structuring_threshold_max"] if structuring_threshold_max is None else structuring_threshold_max
        swin = self.profile["structuring_window_hours"] if structuring_window_hours is None else structuring_window_hours
        scnt = self.profile["structuring_min_tx_count"] if structuring_min_tx_count is None else structuring_min_tx_count
        rdel = self.profile["rapid_pass_max_delay_hours"] if rapid_pass_max_delay_hours is None else rapid_pass_max_delay_hours
        rret = self.profile["rapid_pass_retain_ratio_max"] if rapid_pass_retain_ratio_max is None else rapid_pass_retain_ratio_max
        ddays = self.profile["dormant_days"] if dormant_days is None else dormant_days
        dburst = self.profile["dormant_min_burst"] if dormant_min_burst is None else dormant_min_burst

        factors: list[dict[str, Any]] = []
        total = 0.0

        r001 = self._rule_001(account_id, graph_engine, precomputed_cycles)
        factors.append(r001)
        total += r001["score"]

        r002 = self._rule_002(account_id, transactions, rdel, rret)
        factors.append(r002)
        total += r002["score"]

        r003 = self._rule_003(account_id, transactions, tmin, tmax, swin, scnt)
        factors.append(r003)
        total += r003["score"]

        r004 = self._rule_004(account_id, transactions, ddays, dburst)
        factors.append(r004)
        total += r004["score"]

        r005 = self._rule_005(account_id, identity_attrs)
        factors.append(r005)
        total += r005["score"]

        r006 = self._rule_006(account_id, graph_engine, precomputed_centralities)
        factors.append(r006)
        total += r006["score"]

        r007 = self._rule_007(account_id, graph_engine, counterparty_flags)
        factors.append(r007)
        total += r007["score"]

        r008 = self._rule_008(velocity_spikes)
        factors.append(r008)
        total += r008["score"]

        final_score = round(min(100.0, total), 2)
        explanation = self._build_explanation(factors, final_score)

        return {
            "account_id": account_id,
            "risk_score": final_score,
            "risk_level": _risk_level(final_score),
            "factors": factors,
            "explanation": explanation,
        }

    def score_batch(
        self,
        account_ids: list[str],
        transactions: list[dict[str, Any]],
        identity_attrs_by_account: dict[str, list[dict[str, Any]]] | None = None,
        graph_engine: TransactionGraphEngine | None = None,
        counterparty_flags: dict[str, bool] | None = None,
    ) -> list[dict[str, Any]]:
        """High-throughput batch scoring for 70K+ transactions in O(|E|)."""
        if graph_engine is None:
            graph_engine = TransactionGraphEngine()
            graph_engine.load_transactions(transactions)

        all_cycles = graph_engine.detect_cycles(
            max_length=self.profile.get("cycle_max_length", 5),
            time_window_hours=self.profile.get("cycle_time_window_hours", 72),
        )
        cycles_by_acct: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for c in all_cycles:
            for node in c["cycle"]:
                cycles_by_acct[str(node)].append(c)

        centralities = graph_engine.calculate_centralities()

        # Index transactions by account
        tx_by_acct: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for tx in transactions:
            s = str(tx["sender_account_id"])
            r = str(tx["receiver_account_id"])
            tx_by_acct[s].append(tx)
            if r != s:
                tx_by_acct[r].append(tx)

        # Detect velocity spikes (>400% over baseline or >=4 tx in 24h with >=3x average)
        spikes_by_acct: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for aid, atxs in tx_by_acct.items():
            if len(atxs) >= 5:
                dated = [(t, _parse_ts(t)) for t in atxs]
                dated = [(t, d) for t, d in dated if d is not None]
                dated.sort(key=lambda x: x[1])
                if len(dated) >= 5:
                    total_span_days = max(1.0, (dated[-1][1] - dated[0][1]).total_seconds() / 86400.0)
                    daily_rate = len(dated) / total_span_days
                    # Check 24h sliding count
                    left = 0
                    for right in range(len(dated)):
                        while dated[right][1] - dated[left][1] > timedelta(hours=24):
                            left += 1
                        burst_24h = right - left + 1
                        if burst_24h >= max(5, daily_rate * 4.0):
                            spikes_by_acct[aid].append({
                                "burst_24h": burst_24h,
                                "baseline_daily_rate": round(daily_rate, 3),
                            })
                            break

        results: list[dict[str, Any]] = []
        id_map = identity_attrs_by_account or {}
        for aid in account_ids:
            res = self.score_account(
                account_id=aid,
                transactions=tx_by_acct.get(aid, []),
                identity_attrs=id_map.get(aid),
                graph_engine=graph_engine,
                counterparty_flags=counterparty_flags,
                velocity_spikes=spikes_by_acct.get(aid),
                precomputed_cycles=cycles_by_acct.get(aid, []),
                precomputed_centralities=centralities,
            )
            results.append(res)
        return results

    # ── Individual rules ──────────────────────────────────────────────

    def _rule_001(
        self,
        account_id: str,
        graph_engine: TransactionGraphEngine | None,
        precomputed_cycles: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """RULE_001 — Cyclic fund flow. 12.5 per cycle (or 24-25 for >=1M ring), max 25."""
        max_score = self.weights["RULE_001"]
        if precomputed_cycles is not None:
            involving = precomputed_cycles
        elif graph_engine is not None:
            cycles = graph_engine.detect_cycles()
            involving = [c for c in cycles if account_id in c["cycle"]]
        else:
            return self._factor("RULE_001", 0, max_score, "No graph data")

        n = len(involving)
        if n == 0:
            return self._factor("RULE_001", 0, max_score, "No cycles detected", {"cycles": []})

        max_vol = max((c.get("total_volume", 0.0) for c in involving), default=0.0)
        if n >= 2:
            score = float(max_score)
        elif max_vol >= 1_000_000:
            score = 24.0
        else:
            score = min(float(max_score), 12.5 * n)
        desc = f"{n} cycle(s) involving account (max vol={max_vol:,.0f})"
        return self._factor("RULE_001", score, max_score, desc, {"cycles": involving})

    def _rule_002(
        self, account_id: str, transactions: list[dict], max_delay: int, retain_max: float
    ) -> dict[str, Any]:
        """RULE_002 — Mule behaviour. Binary 20 if any pass-through event."""
        max_score = self.weights["RULE_002"]
        events = AnomalyEngine.detect_rapid_pass_through(
            transactions, account_id, max_delay, retain_max
        )
        score = float(max_score) if events else 0.0
        desc = f"{len(events)} rapid pass-through event(s)" if events else "No mule behaviour"
        return self._factor("RULE_002", score, max_score, desc, {"events": events})

    def _rule_003(
        self, account_id: str, transactions: list[dict],
        tmin: float, tmax: float, window: int, min_count: int,
    ) -> dict[str, Any]:
        """RULE_003 — Structuring. Binary 20 if any structuring pattern."""
        max_score = self.weights["RULE_003"]
        patterns = StructuringEngine.detect_structuring_patterns(
            transactions, account_id, tmin, tmax, window, min_count
        )
        score = float(max_score) if patterns else 0.0
        desc = f"{len(patterns)} structuring pattern(s)" if patterns else "No structuring"
        return self._factor("RULE_003", score, max_score, desc, {"patterns": patterns})

    def _rule_004(
        self, account_id: str, transactions: list[dict],
        dormant_days: int, min_burst: float,
    ) -> dict[str, Any]:
        """RULE_004 — Dormant activation. Binary 15 if any dormancy burst."""
        max_score = self.weights["RULE_004"]
        events = AnomalyEngine.detect_dormant_activation(
            transactions, account_id, dormant_days, min_burst
        )
        score = float(max_score) if events else 0.0
        desc = f"{len(events)} dormancy burst(s)" if events else "No dormant activation"
        return self._factor("RULE_004", score, max_score, desc, {"events": events})

    def _rule_005(
        self, account_id: str, identity_attrs: list[dict] | None
    ) -> dict[str, Any]:
        """RULE_005 — Shared-identity collision. 7.5 per collision, max 15."""
        max_score = self.weights["RULE_005"]
        if not identity_attrs:
            return self._factor("RULE_005", 0, max_score, "No identity data")

        collisions = [a for a in identity_attrs if a.get("is_collision") or a.get("shared")]
        n = len(collisions)
        score = min(float(max_score), 7.5 * n)
        desc = f"{n} identity collision(s)" if n else "No identity collisions"
        return self._factor("RULE_005", score, max_score, desc, {"collisions": collisions})

    def _rule_006(
        self,
        account_id: str,
        graph_engine: TransactionGraphEngine | None,
        precomputed_centralities: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """RULE_006 — Network hub. 15 if hub, 8 if betweenness>=0.20."""
        max_score = self.weights["RULE_006"]
        if precomputed_centralities is not None:
            centralities = precomputed_centralities
        elif graph_engine is not None:
            centralities = graph_engine.calculate_centralities()
        else:
            return self._factor("RULE_006", 0, max_score, "No graph data")

        node_data = centralities.get(account_id)
        if node_data is None:
            return self._factor("RULE_006", 0, max_score, "Account not in graph")

        b = node_data["betweenness"]
        is_hub = node_data["is_hub"]

        if is_hub:
            score = 15.0
            desc = f"Network hub (betweenness={b:.3f})"
        elif b >= 0.20:
            score = 8.0
            desc = f"Elevated centrality (betweenness={b:.3f})"
        else:
            score = 0.0
            desc = f"Normal centrality (betweenness={b:.3f})"

        return self._factor("RULE_006", score, max_score, desc, {"centrality": node_data})

    def _rule_007(
        self,
        account_id: str,
        graph_engine: TransactionGraphEngine | None,
        counterparty_flags: dict[str, bool] | None,
    ) -> dict[str, Any]:
        """RULE_007 — Risky counterparties. 5 per risky, max 15."""
        max_score = self.weights["RULE_007"]
        if graph_engine is None or not counterparty_flags or account_id not in graph_engine.graph:
            return self._factor("RULE_007", 0, max_score, "No counterparty data")

        risky = []
        for nbr in graph_engine.graph.neighbors(account_id):
            if counterparty_flags.get(nbr, False):
                risky.append(nbr)
        for pred in graph_engine.graph.predecessors(account_id):
            if counterparty_flags.get(pred, False) and pred not in risky:
                risky.append(pred)

        n = len(risky)
        score = min(float(max_score), 5.0 * n)
        desc = f"{n} risky counterpart(y/ies)" if n else "No risky counterparties"
        return self._factor("RULE_007", score, max_score, desc, {"risky": risky})

    def _rule_008(self, velocity_spikes: list[dict] | None) -> dict[str, Any]:
        """RULE_008 — Velocity spike. 5 per spike, max 10."""
        max_score = self.weights["RULE_008"]
        if not velocity_spikes:
            return self._factor("RULE_008", 0, max_score, "No velocity spikes")

        n = len(velocity_spikes)
        score = min(float(max_score), 5.0 * n)
        desc = f"{n} velocity spike(s)"
        return self._factor("RULE_008", score, max_score, desc, {"spikes": velocity_spikes})

    # ── Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _factor(
        rule: str,
        score: float,
        max_score: int,
        description: str,
        evidence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "rule": rule,
            "score": score,
            "max_score": max_score,
            "description": description,
            "evidence": evidence or {},
        }

    @staticmethod
    def _build_explanation(factors: list[dict], final_score: float) -> str:
        lines = [f"Risk Score: {final_score:.1f} ({_risk_level(final_score)})"]
        for f in factors:
            if f["score"] > 0:
                lines.append(f"  {f['rule']}: +{f['score']:.1f}/{f['max_score']} — {f['description']}")
        return "\n".join(lines)
