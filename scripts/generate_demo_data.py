"""PHANTOM Demo Data Generator (from real processed PaySim + Phantom Ring).

Reads data/processed/*.csv (plus risk_scores.csv / alerts.csv if available)
and emits frontend/src/lib/demoData.ts for offline/local frontend operation.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent


def generate_demo_ts(
    processed_dir: Path | None = None,
    out_path: Path | None = None,
) -> Path:
    processed_dir = processed_dir or (ROOT_DIR / "data" / "processed")
    out_path = out_path or (ROOT_DIR / "frontend" / "src" / "lib" / "demoData.ts")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    cust_df = pd.read_csv(processed_dir / "customers.csv", keep_default_na=False)
    acct_df = pd.read_csv(processed_dir / "accounts.csv", keep_default_na=False)
    tx_df = pd.read_csv(processed_dir / "transactions.csv", keep_default_na=False)
    id_df = pd.read_csv(processed_dir / "identity_attributes.csv", keep_default_na=False)
    rel_df = pd.read_csv(processed_dir / "account_relationships.csv", keep_default_na=False)

    risk_scores_path = processed_dir / "risk_scores.csv"
    alerts_path = processed_dir / "alerts.csv"
    sampling_path = processed_dir / "sampling_report.json"

    sampling_report = {}
    if sampling_path.exists():
        sampling_report = json.loads(sampling_path.read_text(encoding="utf-8"))

    # Prioritize Operation Phantom Ring + top risky / fraud accounts for demo slice
    phantom_ids = {
        "22222222-2222-4222-8222-000000000001",
        "22222222-2222-4222-8222-000000000002",
        "22222222-2222-4222-8222-000000000003",
    }

    if risk_scores_path.exists():
        rs_df = pd.read_csv(risk_scores_path, keep_default_na=False)
        top_accts = rs_df.sort_values("score", ascending=False).head(30)
        risk_dist = rs_df["risk_level"].value_counts().to_dict()
    else:
        rs_df = pd.DataFrame(columns=["entity_id", "score", "risk_level", "reasons"])
        top_accts = pd.DataFrame()
        risk_dist = {"LOW": len(acct_df) - 3, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 3}

    # Build top accounts list (Phantom Ring first + top scored PaySim/injected accounts)
    acct_by_id = acct_df.set_index("id").to_dict(orient="index")
    cust_by_id = cust_df.set_index("id").to_dict(orient="index")

    selected_acct_ids: list[str] = list(phantom_ids)
    if not top_accts.empty:
        for aid in top_accts["entity_id"].tolist():
            if aid not in selected_acct_ids and aid in acct_by_id:
                selected_acct_ids.append(aid)
    for aid in acct_df["id"].head(25).tolist():
        if aid not in selected_acct_ids:
            selected_acct_ids.append(aid)
    selected_acct_ids = selected_acct_ids[:30]

    rs_lookup = {}
    if not rs_df.empty:
        for _, r in rs_df.iterrows():
            rs_lookup[str(r["entity_id"])] = {
                "score": float(r["score"]),
                "risk_level": str(r["risk_level"]),
                "reasons": str(r["reasons"]),
            }

    demo_accounts = []
    selected_cust_ids = set()
    for aid in selected_acct_ids:
        a = acct_by_id[aid]
        cid = str(a["customer_id"])
        selected_cust_ids.add(cid)
        rs_info = rs_lookup.get(aid, {"score": float(a["risk_score"]), "risk_level": str(a["risk_level"]), "reasons": "[]"})
        if aid in phantom_ids and rs_info["score"] == 0:
            rs_info = {"score": 94.0 if aid.endswith("01") else 91.0, "risk_level": "CRITICAL", "reasons": "[]"}
        demo_accounts.append({
            "id": aid,
            "account_number_masked": a["account_number_masked"],
            "customer_id": cid,
            "customer_name": cust_by_id.get(cid, {}).get("name", "Unknown"),
            "account_type": a["account_type"],
            "bank_code": a["bank_code"],
            "country": a["country"],
            "status": a["status"],
            "risk_score": round(float(rs_info["score"]), 2),
            "risk_level": rs_info["risk_level"],
            "is_dormant": bool(a["is_dormant"]),
            "data_source": a.get("data_source", "PAYSIM_DERIVED"),
        })

    demo_customers = []
    for cid in sorted(selected_cust_ids):
        if cid in cust_by_id:
            c = cust_by_id[cid]
            demo_customers.append({
                "id": cid,
                "customer_reference": c["customer_reference"],
                "name": c["name"],
                "email_masked": c["email_masked"],
                "phone_masked": c["phone_masked"],
                "country": c["country"],
                "identity_hash": c["identity_hash"],
                "risk_score": float(c["risk_score"]),
                "risk_level": c["risk_level"],
                "data_source": c.get("data_source", "SYNTHETIC_ENRICHMENT"),
            })

    # Sample transactions: Phantom Ring + fraud + injected rings + normal mix (60 rows)
    phantom_tx = tx_df[tx_df["data_source"] == "PHANTOM_RING_SEED"]
    ring_tx = tx_df[tx_df["data_source"] == "INJECTED_RING"].head(20)
    fraud_tx = tx_df[tx_df["paysim_is_fraud"] == 1].head(25)
    normal_tx = tx_df[tx_df["paysim_is_fraud"] == 0].head(20)
    sample_tx_df = pd.concat([phantom_tx, ring_tx, fraud_tx, normal_tx]).drop_duplicates("id").head(65)

    demo_transactions = []
    for _, t in sample_tx_df.iterrows():
        demo_transactions.append({
            "id": str(t["id"]),
            "transaction_reference": str(t["transaction_reference"]),
            "sender_account_id": str(t["sender_account_id"]),
            "sender_label": acct_by_id.get(str(t["sender_account_id"]), {}).get("account_number_masked", str(t["sender_account_id"])),
            "receiver_account_id": str(t["receiver_account_id"]),
            "receiver_label": acct_by_id.get(str(t["receiver_account_id"]), {}).get("account_number_masked", str(t["receiver_account_id"])),
            "amount": float(t["amount"]),
            "currency": str(t["currency"]),
            "transaction_type": str(t["transaction_type"]),
            "transaction_timestamp": str(t["transaction_timestamp"]),
            "location": str(t["location"]),
            "device_id": str(t["device_id"]),
            "status": str(t["status"]),
            "blockchain_hash": str(t["blockchain_hash"]),
            "verification_status": str(t["verification_status"]),
            "paysim_is_fraud": int(t["paysim_is_fraud"]),
            "data_source": str(t.get("data_source", "PAYSIM_REAL")),
        })

    # Alerts
    demo_alerts = []
    if alerts_path.exists():
        al_df = pd.read_csv(alerts_path, keep_default_na=False).head(25)
        for _, r in al_df.iterrows():
            demo_alerts.append({
                "id": str(r["id"]),
                "entity_type": str(r["entity_type"]),
                "entity_id": str(r["entity_id"]),
                "alert_type": str(r["alert_type"]),
                "severity": str(r["severity"]),
                "title": str(r["title"]),
                "description": str(r["description"]),
                "status": str(r["status"]),
                "created_at": str(r["created_at"]),
            })
    if not demo_alerts:
        demo_alerts.append({
            "id": "66666666-6666-4666-8666-000000000001",
            "entity_type": "NETWORK",
            "entity_id": "22222222-2222-4222-8222-000000000001",
            "alert_type": "CIRCULAR_RING",
            "severity": "CRITICAL",
            "title": "Operation Phantom Ring: 3-Hop Circular Flow (Rs.1.415M)",
            "description": "3-hop RTGS cycle ACC-0001-9041 -> ACC-0044-7721 -> ACC-0078-3319 within 4.25h sharing DEV-PHANTOM-103.",
            "status": "ESCALATED",
            "created_at": "2026-06-15T14:20:00Z",
        })

    # Shared identity clusters for Identities page
    shared_groups = (
        id_df[id_df["attribute_type"] == "DEVICE"]
        .groupby("attribute_value_masked")["customer_id"]
        .apply(list)
        .reset_index()
    )
    shared_groups = shared_groups[shared_groups["customer_id"].apply(len) >= 2].head(15)
    demo_identity_clusters = []
    for _, sg in shared_groups.iterrows():
        cids = sg["customer_id"]
        demo_identity_clusters.append({
            "attribute_type": "DEVICE",
            "attribute_value": str(sg["attribute_value_masked"]),
            "customer_count": len(cids),
            "customers": [
                {"id": c, "name": cust_by_id.get(c, {}).get("name", c), "ref": cust_by_id.get(c, {}).get("customer_reference", "")}
                for c in cids[:6]
            ],
            "risk_level": "CRITICAL" if sg["attribute_value_masked"] == "DEV-PHANTOM-103" else "HIGH",
        })

    # Intraday / daily trend from transactions
    tx_df["_day"] = tx_df["transaction_timestamp"].astype(str).str.slice(0, 10)
    daily = (
        tx_df.groupby("_day")
        .agg(volume=("amount", "sum"), count=("id", "count"), flagged=("paysim_is_fraud", "sum"))
        .reset_index()
        .sort_values("_day")
        .head(30)
    )
    volume_trend = [
        {
            "date": str(r["_day"]),
            "volume": round(float(r["volume"]), 2),
            "count": int(r["count"]),
            "flagged": int(r["flagged"]),
        }
        for _, r in daily.iterrows()
    ]

    # Network graph elements (Phantom Ring + surrounding edges up to 60 nodes)
    graph_accts = set(phantom_ids)
    for t in demo_transactions[:35]:
        graph_accts.add(t["sender_account_id"])
        graph_accts.add(t["receiver_account_id"])

    acct_risk_map = {a["id"]: a for a in demo_accounts}
    graph_nodes = []
    for aid in list(graph_accts)[:80]:
        raw = acct_by_id.get(aid, {})
        meta = acct_risk_map.get(aid, {})
        rs = rs_lookup.get(aid, {})
        score = float(rs.get("score", meta.get("risk_score", 94.0 if aid.endswith("01") else 10.0)))
        level = str(rs.get("risk_level", meta.get("risk_level", "CRITICAL" if aid in phantom_ids else "LOW")))
        graph_nodes.append({
            "id": aid,
            "label": raw.get("account_number_masked", aid[:10]),
            "bank_code": raw.get("bank_code", "HDFC"),
            "account_type": raw.get("account_type", "SAVINGS"),
            "risk_score": round(score, 2),
            "risk_level": level,
            "centrality": 0.81 if aid in phantom_ids else round(min(0.75, 0.1 + (score / 150.0)), 3),
            "is_phantom_ring": aid in phantom_ids,
        })

    node_id_set = {n["id"] for n in graph_nodes}
    graph_edges = []
    for t in demo_transactions:
        if t["sender_account_id"] in node_id_set and t["receiver_account_id"] in node_id_set:
            graph_edges.append({
                "id": t["id"],
                "source": t["sender_account_id"],
                "target": t["receiver_account_id"],
                "amount": t["amount"],
                "type": "CIRCULAR_FLOW" if t["data_source"] in ("PHANTOM_RING_SEED", "INJECTED_RING") else "TRANSFER",
                "label": f"Rs.{t['amount']:,.0f}",
                "is_cycle": t["data_source"] in ("PHANTOM_RING_SEED", "INJECTED_RING"),
            })
    # Add shared device edges for Phantom Ring & sample relationships
    for _, rel in rel_df[rel_df["relationship_type"] == "SHARED_DEVICE"].head(10).iterrows():
        s_id = str(rel["source_account_id"])
        t_id = str(rel["target_account_id"])
        if s_id in node_id_set and t_id in node_id_set:
            graph_edges.append({
                "id": str(rel["id"]),
                "source": s_id,
                "target": t_id,
                "amount": 0,
                "type": "SHARED_DEVICE",
                "label": "DEV-PHANTOM-103" if s_id in phantom_ids else "SHARED_DEVICE",
                "is_cycle": False,
            })

    summary_stats = {
        "totalCustomers": int(len(cust_df)),
        "totalAccounts": int(len(acct_df)),
        "totalTransactions": int(len(tx_df)),
        "paysimFraudCount": int(tx_df["paysim_is_fraud"].sum()),
        "injectedRingCount": int((tx_df["data_source"] == "INJECTED_RING").sum()),
        "highRiskAccounts": int(sum(v for k, v in risk_dist.items() if k in ("HIGH", "CRITICAL"))),
        "criticalAlerts": int(sum(1 for a in demo_alerts if a["severity"] == "CRITICAL")),
        "detectedCycles": 26,
        "anchoredRecords": int(len(tx_df)),
        "activeInvestigations": 4,
        "riskDistribution": [
            {"name": "LOW", "value": int(risk_dist.get("LOW", 0)), "color": "#10b981"},
            {"name": "MEDIUM", "value": int(risk_dist.get("MEDIUM", 0)), "color": "#f59e0b"},
            {"name": "HIGH", "value": int(risk_dist.get("HIGH", 0)), "color": "#f97316"},
            {"name": "CRITICAL", "value": int(risk_dist.get("CRITICAL", 0)), "color": "#ef4444"},
        ],
        "samplingReport": sampling_report,
    }

    payload = {
        "SUMMARY_STATS": summary_stats,
        "DEMO_CUSTOMERS": demo_customers,
        "DEMO_ACCOUNTS": demo_accounts,
        "DEMO_TRANSACTIONS": demo_transactions,
        "DEMO_ALERTS": demo_alerts,
        "DEMO_IDENTITY_CLUSTERS": demo_identity_clusters,
        "DEMO_VOLUME_TREND": volume_trend,
        "DEMO_GRAPH_DATA": {"nodes": graph_nodes, "edges": graph_edges},
    }

    ts_lines = [
        "// AUTO-GENERATED BY scripts/generate_demo_data.py FROM REAL PROCESSED PAYSIM DATA.",
        "// Mode: DEMO / LOCAL FALLBACK",
        "",
        f"export const SUMMARY_STATS = {json.dumps(payload['SUMMARY_STATS'], indent=2)} as const;",
        "",
        f"export const DEMO_CUSTOMERS = {json.dumps(payload['DEMO_CUSTOMERS'], indent=2)};",
        "",
        f"export const DEMO_ACCOUNTS = {json.dumps(payload['DEMO_ACCOUNTS'], indent=2)};",
        "",
        f"export const DEMO_TRANSACTIONS = {json.dumps(payload['DEMO_TRANSACTIONS'], indent=2)};",
        "",
        f"export const DEMO_ALERTS = {json.dumps(payload['DEMO_ALERTS'], indent=2)};",
        "",
        f"export const DEMO_IDENTITY_CLUSTERS = {json.dumps(payload['DEMO_IDENTITY_CLUSTERS'], indent=2)};",
        "",
        f"export const DEMO_VOLUME_TREND = {json.dumps(payload['DEMO_VOLUME_TREND'], indent=2)};",
        "",
        f"export const DEMO_GRAPH_DATA = {json.dumps(payload['DEMO_GRAPH_DATA'], indent=2)};",
        "",
    ]
    out_path.write_text("\n".join(ts_lines), encoding="utf-8")
    print(f"[generate_demo_data] Wrote {out_path} ({out_path.stat().st_size:,} bytes)")
    return out_path


if __name__ == "__main__":
    generate_demo_ts()
