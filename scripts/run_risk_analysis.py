"""PHANTOM Risk Analysis Runner.

Reads processed CSVs from data/processed/, constructs the transaction graph,
runs all 8 explainable risk rules across every account (using the PaySim-calibrated
profile for PaySim accounts and ensuring Operation Phantom Ring is scored),
and persists risk_scores.csv, risk_factors.csv, alerts.csv, and network_clusters.csv
(plus updates local SQLite DB if present).

Usage:
    python scripts/run_risk_analysis.py --profile paysim
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "analytics"))

from app.graph_analysis import TransactionGraphEngine  # noqa: E402
from app.risk_engine import RiskScoringEngine  # noqa: E402

NAMESPACE_PHANTOM = uuid.UUID("7a8b9c0d-1e2f-4a3b-8c4d-5e6f7a8b9c0d")
PHANTOM_RING_IDS = {
    "22222222-2222-4222-8222-000000000001",
    "22222222-2222-4222-8222-000000000002",
    "22222222-2222-4222-8222-000000000003",
}


def run_risk_pipeline(
    processed_dir: Path | None = None,
    profile: str = "paysim",
    db_path: Path | None = None,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    processed_dir = processed_dir or (ROOT_DIR / "data" / "processed")
    db_path = db_path or (ROOT_DIR / "data" / "phantom_local.db")

    acct_df = pd.read_csv(processed_dir / "accounts.csv", keep_default_na=False)
    tx_df = pd.read_csv(processed_dir / "transactions.csv", keep_default_na=False)
    id_df = pd.read_csv(processed_dir / "identity_attributes.csv", keep_default_na=False)

    print(f"[RiskRunner] Loaded {len(acct_df):,} accounts and {len(tx_df):,} transactions (profile={profile})")

    # Build lightweight transaction dicts
    tx_records = tx_df[
        ["id", "sender_account_id", "receiver_account_id", "amount", "transaction_timestamp", "transaction_type"]
    ].to_dict(orient="records")

    graph_engine = TransactionGraphEngine()
    graph_engine.load_transactions(tx_records)
    print(
        f"[RiskRunner] Graph built: {graph_engine.graph.number_of_nodes():,} nodes, "
        f"{graph_engine.graph.number_of_edges():,} edges in {time.perf_counter() - t0:.2f}s"
    )

    # Identify shared DEVICE / IP collisions across distinct customers
    attr_custs = id_df.groupby(["attribute_type", "attribute_hash"])["customer_id"].nunique()
    shared_keys = set(attr_custs[attr_custs >= 2].index.tolist())

    id_by_cust: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in id_df.itertuples(index=False):
        key = (row.attribute_type, row.attribute_hash)
        if key in shared_keys:
            id_by_cust[str(row.customer_id)].append({
                "attribute_type": row.attribute_type,
                "attribute_hash": row.attribute_hash,
                "value": row.attribute_value_masked,
                "is_collision": True,
            })

    identity_attrs_by_account: dict[str, list[dict[str, Any]]] = {}
    for row in acct_df[["id", "customer_id"]].itertuples(index=False):
        cid = str(row.customer_id)
        if cid in id_by_cust:
            identity_attrs_by_account[str(row.id)] = id_by_cust[cid]

    # Note: Do NOT leak paysim_is_fraud labels into counterparty_flags during scoring!
    # We run an unsupervised pass first, then propagate high-risk (>=60) neighbors in pass 2 (RULE_007).
    account_ids = acct_df["id"].astype(str).tolist()
    scorer = RiskScoringEngine(profile=profile)

    pass1_scores = scorer.score_batch(
        account_ids=account_ids,
        transactions=tx_records,
        identity_attrs_by_account=identity_attrs_by_account,
        graph_engine=graph_engine,
        counterparty_flags=None,
    )

    # Pass 2: flag counterparties with pass1 score >= 60 (purely from unsupervised signals, zero label leakage)
    flagged_cp = {
        r["account_id"]: True
        for r in pass1_scores
        if r["risk_score"] >= 60.0
    }
    final_scores = scorer.score_batch(
        account_ids=account_ids,
        transactions=tx_records,
        identity_attrs_by_account=identity_attrs_by_account,
        graph_engine=graph_engine,
        counterparty_flags=flagged_cp,
    )

    risk_scores_rows: list[dict[str, Any]] = []
    risk_factors_rows: list[dict[str, Any]] = []
    alerts_rows: list[dict[str, Any]] = []

    for res in final_scores:
        aid = res["account_id"]
        score = res["risk_score"]
        level = res["risk_level"]
        rs_id = str(uuid.uuid5(NAMESPACE_PHANTOM, f"risk_score:{aid}"))
        triggered = [f for f in res["factors"] if f["score"] > 0]
        reasons = [f"{f['rule']}: {f['description']}" for f in triggered]

        risk_scores_rows.append({
            "id": rs_id,
            "entity_type": "ACCOUNT",
            "entity_id": aid,
            "score": score,
            "risk_level": level,
            "reasons": json.dumps(reasons),
        })

        for f in triggered:
            rf_id = str(uuid.uuid5(NAMESPACE_PHANTOM, f"risk_factor:{aid}:{f['rule']}"))
            risk_factors_rows.append({
                "id": rf_id,
                "risk_score_id": rs_id,
                "rule_id": f["rule"],
                "rule_name": f["rule"],
                "severity": level,
                "weight": f["score"],
                "evidence": json.dumps(f["evidence"]),
            })

        if score >= 60.0:
            al_id = str(uuid.uuid5(NAMESPACE_PHANTOM, f"alert:{aid}"))
            alerts_rows.append({
                "id": al_id,
                "entity_type": "ACCOUNT",
                "entity_id": aid,
                "alert_type": triggered[0]["rule"] if triggered else "HIGH_RISK",
                "severity": level,
                "title": f"{level} Risk Account Detected ({score:.1f}/100)",
                "description": res["explanation"].replace("\n", " | "),
                "evidence": json.dumps({"rules": [f["rule"] for f in triggered], "score": score}),
                "status": "NEW" if level == "HIGH" else "ESCALATED",
                "created_at": "2026-06-30T23:59:00Z",
            })

    # Network clusters from cycles + communities
    cycles = graph_engine.detect_cycles(
        max_length=scorer.profile.get("cycle_max_length", 5),
        time_window_hours=scorer.profile.get("cycle_time_window_hours", 72),
    )
    cluster_rows: list[dict[str, Any]] = []
    for idx, c in enumerate(cycles[:100]):
        cid = str(uuid.uuid5(NAMESPACE_PHANTOM, f"cluster_cycle:{idx}:{'-'.join(c['cycle'])}"))
        cluster_rows.append({
            "id": cid,
            "cluster_name": f"Circular Ring #{idx + 1}",
            "entity_ids": json.dumps(c["cycle"]),
            "risk_score": min(100.0, 65.0 + c["risk_boost"]),
            "description": f"{c['length']}-hop closed loop (volume={c['total_volume']:,.2f})",
        })

    rs_df = pd.DataFrame(risk_scores_rows)
    rf_df = pd.DataFrame(risk_factors_rows)
    al_df = pd.DataFrame(alerts_rows)
    cl_df = pd.DataFrame(cluster_rows)

    rs_df.to_csv(processed_dir / "risk_scores.csv", index=False)
    rf_df.to_csv(processed_dir / "risk_factors.csv", index=False)
    al_df.to_csv(processed_dir / "alerts.csv", index=False)
    cl_df.to_csv(processed_dir / "network_clusters.csv", index=False)

    # Persist into SQLite if available
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        conn.execute("DELETE FROM risk_factors;")
        conn.execute("DELETE FROM risk_scores;")
        conn.execute("DELETE FROM alerts;")
        conn.execute("DELETE FROM network_clusters;")
        rs_df.to_sql("risk_scores", conn, if_exists="append", index=False)
        if not rf_df.empty:
            rf_df.to_sql("risk_factors", conn, if_exists="append", index=False)
        if not al_df.empty:
            al_df[["id", "entity_type", "entity_id", "alert_type", "severity", "title", "description", "evidence", "status", "created_at"]].to_sql(
                "alerts", conn, if_exists="append", index=False
            )
        if not cl_df.empty:
            cl_df.to_sql("network_clusters", conn, if_exists="append", index=False)
        conn.commit()
        conn.close()

    elapsed = time.perf_counter() - t0
    level_counts = rs_df["risk_level"].value_counts().to_dict()
    summary = {
        "elapsed_seconds": round(elapsed, 2),
        "accounts_scored": len(rs_df),
        "risk_factors_logged": len(rf_df),
        "alerts_generated": len(al_df),
        "cycles_detected": len(cycles),
        "risk_distribution": level_counts,
    }
    print(f"[RiskRunner] Completed in {elapsed:.2f}s -> {json.dumps(summary)}")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="PHANTOM Risk Analysis Runner")
    parser.add_argument("--profile", type=str, default="paysim", choices=["default", "paysim"])
    args = parser.parse_args()
    run_risk_pipeline(profile=args.profile)


if __name__ == "__main__":
    main()

