"""PHANTOM PaySim Streaming Adapter (Seeded, Memory-Safe).

Streams the 6.3M-row PaySim dataset in chunks without loading the full CSV into RAM,
retains 100% of fraud transactions and fraud-adjacent network context, performs
stratified sampling to reach the target row budget (default 70,000), enriches missing
identity/device/IP attributes deterministically, injects ~25 synthetic laundering rings
plus the pre-seeded Operation Phantom Ring case study, and outputs FK-safe CSVs.

Usage:
    python scripts/paysim_adapter.py --target 70000 --seed 42
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# Allow importing canonical blockchain hashing from analytics
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "analytics"))
from app.blockchain import compute_hash  # noqa: E402

NAMESPACE_PHANTOM = uuid.UUID("7a8b9c0d-1e2f-4a3b-8c4d-5e6f7a8b9c0d")
SIM_START = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
BANK_CODES = ["HDFC", "ICICI", "SBI", "AXIS", "KOTAK", "PNB"]
INDIAN_FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan",
    "Krishna", "Ishaan", "Shaurya", "Atharva", "Ananya", "Diya", "Saanvi",
    "Aadhya", "Kiara", "Pari", "Riya", "Myra", "Kavya", "Meera", "Neha",
    "Priya", "Rohan", "Vikram", "Siddharth", "Karan", "Nikhil", "Pooja",
    "Rahul", "Sneha", "Tanvi", "Varun", "Yash", "Dev", "Rajesh", "Sunita",
]
INDIAN_LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Patel", "Singh", "Kumar", "Mehta", "Malhotra",
    "Kapoor", "Joshi", "Nair", "Reddy", "Iyer", "Rao", "Kulkarni", "Desai",
    "Agarwal", "Banerjee", "Chatterjee", "Bhat", "Saxena", "Tiwari", "Chopra",
    "Bose", "Menon", "Mishra", "Pandey", "Trivedi", "Sinha", "Dutta",
]
INDIAN_CITIES = [
    "Mumbai, IN", "Delhi, IN", "Bengaluru, IN", "Hyderabad, IN",
    "Chennai, IN", "Pune, IN", "Kolkata, IN", "Ahmedabad, IN",
]

# Only read non-balance columns from PaySim CSV (balance columns are NEVER used!)
PAYSIM_SAFE_COLS = ["step", "type", "amount", "nameOrig", "nameDest", "isFraud", "isFlaggedFraud"]

TX_TYPE_MAP = {
    "TRANSFER": "WIRE",
    "CASH_OUT": "ATM",
    "PAYMENT": "UPI",
    "CASH_IN": "INTERNAL_TRANSFER",
    "DEBIT": "NEFT",
}


def det_uuid(kind: str, key: str) -> str:
    """Deterministic UUIDv5 derived from entity kind and key."""
    return str(uuid.uuid5(NAMESPACE_PHANTOM, f"{kind}:{key}"))


def det_hash(text: str) -> str:
    """Deterministic SHA-256 hex string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def det_int(text: str) -> int:
    """Deterministic integer from SHA-256 prefix."""
    return int(det_hash(text)[:16], 16)


def mask_account(raw_name: str) -> str:
    """Mask raw PaySim account ID while guaranteeing uniqueness."""
    prefix = raw_name[0] if raw_name else "C"
    tail = raw_name[-4:] if len(raw_name) >= 4 else raw_name
    h4 = det_hash(raw_name)[:6].upper()
    return f"{prefix}***{tail}-{h4}"


def find_input_csv(explicit: str | None) -> Path:
    """Locate the PaySim raw CSV, falling back to archive or fixture."""
    if explicit:
        p = Path(explicit)
        if p.exists():
            return p
    candidates = [
        ROOT_DIR / "data" / "raw" / "PS_20174392719_1491204439457_log.csv",
        ROOT_DIR / "archive" / "PS_20174392719_1491204439457_log.csv",
        ROOT_DIR / "data" / "raw" / "paysim_fixture.csv",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(
        "No PaySim CSV found in data/raw/ or archive/. Run generate_paysim_fixture.py first."
    )


def run_adapter(
    input_path: Path,
    output_dir: Path,
    target: int = 70_000,
    seed: int = 42,
    chunksize: int = 100_000,
) -> dict[str, Any]:
    """Execute the two-pass streaming PaySim adapter."""
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    print(f"[PHANTOM Adapter] Input: {input_path} | Target: {target:,} | Seed: {seed}")

    # ------------------------------------------------------------------
    # PASS 1: Stream to find all fraud rows, fraud accounts, & type counts
    # ------------------------------------------------------------------
    total_rows = 0
    fraud_rows_count = 0
    fraud_accounts: set[str] = set()
    non_fraud_type_counts: dict[str, int] = defaultdict(int)

    for chunk in pd.read_csv(input_path, usecols=PAYSIM_SAFE_COLS, chunksize=chunksize):
        total_rows += len(chunk)
        f_mask = chunk["isFraud"] == 1
        if f_mask.any():
            f_sub = chunk[f_mask]
            fraud_rows_count += len(f_sub)
            fraud_accounts.update(f_sub["nameOrig"].astype(str).tolist())
            fraud_accounts.update(f_sub["nameDest"].astype(str).tolist())
        nf_sub = chunk[~f_mask]
        for t_type, cnt in nf_sub["type"].value_counts().items():
            non_fraud_type_counts[str(t_type)] += int(cnt)

    print(
        f"[Pass 1] Total rows={total_rows:,}, Fraud rows={fraud_rows_count:,}, "
        f"Fraud accounts={len(fraud_accounts):,}"
    )

    # Pass 1.5 (quick count of fraud-touching non-fraud rows so sampling ratio is exact)
    touch_non_fraud_count = 0
    for chunk in pd.read_csv(input_path, usecols=PAYSIM_SAFE_COLS, chunksize=chunksize):
        nf = chunk[chunk["isFraud"] == 0]
        touch_mask = nf["nameOrig"].isin(fraud_accounts) | nf["nameDest"].isin(fraud_accounts)
        touch_non_fraud_count += int(touch_mask.sum())

    # Reserve ~120 rows for injected rings + Phantom Ring
    injected_reserve = 120
    remaining_budget = max(0, target - fraud_rows_count - touch_non_fraud_count - injected_reserve)

    # Allocate 60% of remaining budget to TRANSFER/CASH_OUT, 40% to PAYMENT/CASH_IN/DEBIT
    high_risk_types = {"TRANSFER", "CASH_OUT"}
    low_risk_types = {"PAYMENT", "CASH_IN", "DEBIT"}

    hr_total = sum(non_fraud_type_counts[t] for t in high_risk_types)
    lr_total = sum(non_fraud_type_counts[t] for t in low_risk_types)

    hr_budget = int(remaining_budget * 0.60)
    lr_budget = remaining_budget - hr_budget

    type_keep_prob: dict[str, float] = {}
    for t in high_risk_types:
        cnt = non_fraud_type_counts[t]
        type_keep_prob[t] = min(1.0, (hr_budget / max(1, hr_total)) * 1.02) if cnt > 0 else 0.0
    for t in low_risk_types:
        cnt = non_fraud_type_counts[t]
        type_keep_prob[t] = min(1.0, (lr_budget / max(1, lr_total)) * 1.02) if cnt > 0 else 0.0

    # ------------------------------------------------------------------
    # PASS 2: Stream and retain selected transactions
    # ------------------------------------------------------------------
    kept_frames: list[pd.DataFrame] = []
    retained_counts = {
        "fraud": 0,
        "fraud_neighbor": 0,
        "stratified_non_fraud": 0,
    }

    row_offset = 0
    for chunk in pd.read_csv(input_path, usecols=PAYSIM_SAFE_COLS, chunksize=chunksize):
        chunk = chunk.copy()
        chunk["_orig_idx"] = np.arange(row_offset, row_offset + len(chunk), dtype=np.int64)
        row_offset += len(chunk)

        f_mask = chunk["isFraud"] == 1
        nf_touch_mask = (~f_mask) & (
            chunk["nameOrig"].isin(fraud_accounts) | chunk["nameDest"].isin(fraud_accounts)
        )
        other_mask = (~f_mask) & (~nf_touch_mask)

        # Deterministic Bernoulli draw per remaining row
        probs = chunk["type"].map(type_keep_prob).fillna(0.0).to_numpy()
        draws = rng.random(len(chunk))
        strat_mask = other_mask & (draws < probs)

        retained_counts["fraud"] += int(f_mask.sum())
        retained_counts["fraud_neighbor"] += int(nf_touch_mask.sum())
        retained_counts["stratified_non_fraud"] += int(strat_mask.sum())

        keep_mask = f_mask | nf_touch_mask | strat_mask
        if keep_mask.any():
            kept = chunk.loc[keep_mask].copy()
            kept["_sample_reason"] = np.where(
                f_mask.loc[keep_mask],
                "PAYSIM_FRAUD",
                np.where(nf_touch_mask.loc[keep_mask], "FRAUD_NEIGHBOR", "STRATIFIED_NORMAL"),
            )
            kept_frames.append(kept)

    sampled_df = pd.concat(kept_frames, ignore_index=True)

    # Trim excess stratified rows deterministically if over budget
    non_essential = sampled_df[sampled_df["_sample_reason"] == "STRATIFIED_NORMAL"]
    max_non_essential = max(0, target - injected_reserve - (len(sampled_df) - len(non_essential)))
    if len(non_essential) > max_non_essential:
        drop_n = len(non_essential) - max_non_essential
        drop_idx = rng.choice(non_essential.index.to_numpy(), size=drop_n, replace=False)
        sampled_df = sampled_df.drop(index=drop_idx).reset_index(drop=True)
        retained_counts["stratified_non_fraud"] = max_non_essential

    # Guarantee minimum amount > 0 (schema CHECK (amount > 0))
    sampled_df["amount"] = sampled_df["amount"].clip(lower=1.00).round(2)

    print(
        f"[Pass 2] Retained {len(sampled_df):,} PaySim rows "
        f"(Fraud={retained_counts['fraud']:,}, Neighbor={retained_counts['fraud_neighbor']:,}, "
        f"Stratified={retained_counts['stratified_non_fraud']:,})"
    )

    # ------------------------------------------------------------------
    # ACCOUNTS & CUSTOMERS (Deterministic grouping ~1.3 accounts/customer)
    # ------------------------------------------------------------------
    unique_names = sorted(
        set(sampled_df["nameOrig"].astype(str)).union(set(sampled_df["nameDest"].astype(str)))
    )

    non_merchants = [n for n in unique_names if not n.startswith("M")]
    merchants = [n for n in unique_names if n.startswith("M")]

    num_non_merchant_custs = max(1, int(round(len(non_merchants) / 1.3)))
    cust_map: dict[str, str] = {}
    for name in non_merchants:
        bucket = det_int(f"cust_group:{name}") % num_non_merchant_custs
        cust_map[name] = f"CUST-PS-{bucket:06d}"
    for m_idx, name in enumerate(merchants):
        cust_map[name] = f"CUST-MERCH-{m_idx:06d}"

    # Build customers dict
    customers_rows: list[dict[str, Any]] = []
    customer_id_by_ref: dict[str, str] = {}
    seen_cust_refs: set[str] = set()

    # Pre-seed Operation Phantom Ring Customers (exact Section 16 specs)
    phantom_customers = [
        {
            "id": "11111111-1111-4111-8111-000000000001",
            "customer_reference": "C001",
            "name": "Devraj Singhania",
            "email_masked": "d***@singhania-holdings.in",
            "phone_masked": "+91-98***-***01",
            "country": "IN",
            "identity_hash": det_hash("C001:Devraj Singhania"),
            "risk_score": 0.00,
            "risk_level": "LOW",
            "data_source": "PHANTOM_RING_SEED",
        },
        {
            "id": "11111111-1111-4111-8111-000000000002",
            "customer_reference": "C002",
            "name": "Rohan Malhotra",
            "email_masked": "r***@malhotra-ventures.in",
            "phone_masked": "+91-98***-***02",
            "country": "IN",
            "identity_hash": det_hash("C002:Rohan Malhotra"),
            "risk_score": 0.00,
            "risk_level": "LOW",
            "data_source": "PHANTOM_RING_SEED",
        },
        {
            "id": "11111111-1111-4111-8111-000000000003",
            "customer_reference": "C003",
            "name": "Vikramaditya Mehta",
            "email_masked": "v***@mehta-exports.in",
            "phone_masked": "+91-98***-***03",
            "country": "IN",
            "identity_hash": det_hash("C003:Vikramaditya Mehta"),
            "risk_score": 0.00,
            "risk_level": "LOW",
            "data_source": "PHANTOM_RING_SEED",
        },
    ]
    for pc in phantom_customers:
        customers_rows.append(pc)
        customer_id_by_ref[pc["customer_reference"]] = pc["id"]
        seen_cust_refs.add(pc["customer_reference"])

    for raw_name in unique_names:
        cref = cust_map[raw_name]
        if cref in seen_cust_refs:
            continue
        seen_cust_refs.add(cref)
        cid = det_uuid("customer", cref)
        customer_id_by_ref[cref] = cid
        h_int = det_int(cref)
        fn = INDIAN_FIRST_NAMES[h_int % len(INDIAN_FIRST_NAMES)]
        ln = INDIAN_LAST_NAMES[(h_int // 37) % len(INDIAN_LAST_NAMES)]
        is_merch = cref.startswith("CUST-MERCH-")
        full_name = f"{fn} {ln} Enterprises" if is_merch else f"{fn} {ln}"
        email_masked = f"{fn[0].lower()}***{ln[:2].lower()}@mail.in"
        phone_masked = f"+91-9{(h_int % 9) + 1}***-**{h_int % 100:02d}"
        customers_rows.append(
            {
                "id": cid,
                "customer_reference": cref,
                "name": full_name,
                "email_masked": email_masked,
                "phone_masked": phone_masked,
                "country": "IN",
                "identity_hash": det_hash(f"{cref}:{full_name}"),
                "risk_score": 0.00,
                "risk_level": "LOW",
                "data_source": "SYNTHETIC_ENRICHMENT",
            }
        )

    # Build accounts
    accounts_rows: list[dict[str, Any]] = []
    account_id_by_name: dict[str, str] = {}
    account_cust_by_id: dict[str, str] = {}

    phantom_accounts = [
        {
            "id": "22222222-2222-4222-8222-000000000001",
            "account_number_masked": "ACC-0001-9041",
            "customer_id": "11111111-1111-4111-8111-000000000001",
            "account_type": "CURRENT",
            "bank_code": "HDFC",
            "country": "IN",
            "status": "ACTIVE",
            "risk_score": 0.00,
            "risk_level": "LOW",
            "is_dormant": False,
            "last_activity_at": "2026-06-15T14:15:00Z",
            "data_source": "PHANTOM_RING_SEED",
        },
        {
            "id": "22222222-2222-4222-8222-000000000002",
            "account_number_masked": "ACC-0044-7721",
            "customer_id": "11111111-1111-4111-8111-000000000002",
            "account_type": "SAVINGS",
            "bank_code": "ICICI",
            "country": "IN",
            "status": "ACTIVE",
            "risk_score": 0.00,
            "risk_level": "LOW",
            "is_dormant": False,
            "last_activity_at": "2026-06-15T12:00:00Z",
            "data_source": "PHANTOM_RING_SEED",
        },
        {
            "id": "22222222-2222-4222-8222-000000000003",
            "account_number_masked": "ACC-0078-3319",
            "customer_id": "11111111-1111-4111-8111-000000000003",
            "account_type": "SAVINGS",
            "bank_code": "SBI",
            "country": "IN",
            "status": "ACTIVE",
            "risk_score": 0.00,
            "risk_level": "LOW",
            "is_dormant": False,
            "last_activity_at": "2026-06-15T14:15:00Z",
            "data_source": "PHANTOM_RING_SEED",
        },
    ]
    for pa in phantom_accounts:
        accounts_rows.append(pa)
        account_id_by_name[pa["account_number_masked"]] = pa["id"]
        account_cust_by_id[pa["id"]] = pa["customer_id"]

    acct_types_non_merch = ["SAVINGS", "SAVINGS", "SAVINGS", "CURRENT", "ESCROW", "CRYPTO_WALLET"]
    for raw_name in unique_names:
        aid = det_uuid("account", raw_name)
        cid = customer_id_by_ref[cust_map[raw_name]]
        account_id_by_name[raw_name] = aid
        account_cust_by_id[aid] = cid
        h_val = det_int(raw_name)
        acc_type = "CORPORATE" if raw_name.startswith("M") else acct_types_non_merch[h_val % len(acct_types_non_merch)]
        bank_code = BANK_CODES[(h_val // 11) % len(BANK_CODES)]
        accounts_rows.append(
            {
                "id": aid,
                "account_number_masked": mask_account(raw_name),
                "customer_id": cid,
                "account_type": acc_type,
                "bank_code": bank_code,
                "country": "IN",
                "status": "ACTIVE",
                "risk_score": 0.00,
                "risk_level": "LOW",
                "is_dormant": False,
                "last_activity_at": SIM_START.isoformat(),
                "data_source": "PAYSIM_DERIVED",
            }
        )

    # ------------------------------------------------------------------
    # DEVICES & IPs (RULE_005: 40 groups of 3-6 accounts from different customers)
    # ------------------------------------------------------------------
    cust_device: dict[str, str] = {}
    cust_ip: dict[str, str] = {}
    for crow in customers_rows:
        cid = crow["id"]
        cust_device[cid] = f"DEV-{det_hash(f'dev:{cid}')[:10].upper()}"
        cust_ip[cid] = det_hash(f"ip:{cid}")[:32]

    # Operation Phantom Ring shared device DEV-PHANTOM-103 on C002 & C003
    cust_device["11111111-1111-4111-8111-000000000002"] = "DEV-PHANTOM-103"
    cust_device["11111111-1111-4111-8111-000000000003"] = "DEV-PHANTOM-103"
    cust_ip["11111111-1111-4111-8111-000000000002"] = det_hash("ip:phantom_ring_relay")[:32]
    cust_ip["11111111-1111-4111-8111-000000000003"] = det_hash("ip:phantom_ring_relay")[:32]

    # Select 40 groups of 3-6 accounts from distinct customers (preferring fraud accounts)
    fraud_acct_ids = [account_id_by_name[n] for n in sorted(fraud_accounts) if n in account_id_by_name]
    normal_non_merch_ids = [
        account_id_by_name[n] for n in non_merchants if n not in fraud_accounts
    ]

    injected_gt_rows: list[dict[str, Any]] = []
    ground_truth_rows: list[dict[str, Any]] = []
    account_relationships_map: dict[tuple[str, str, str], dict[str, Any]] = {}

    used_custs_for_sharing = {
        "11111111-1111-4111-8111-000000000001",
        "11111111-1111-4111-8111-000000000002",
        "11111111-1111-4111-8111-000000000003",
    }
    candidate_pool = fraud_acct_ids + normal_non_merch_ids
    pool_idx = 0

    for g_idx in range(40):
        group_size = int(rng.integers(3, 7))
        group_accts: list[str] = []
        group_custs: set[str] = set()
        while len(group_accts) < group_size and pool_idx < len(candidate_pool):
            cand_aid = candidate_pool[pool_idx]
            pool_idx += 1
            cand_cid = account_cust_by_id[cand_aid]
            if cand_cid in used_custs_for_sharing or cand_cid in group_custs:
                continue
            group_accts.append(cand_aid)
            group_custs.add(cand_cid)
            used_custs_for_sharing.add(cand_cid)

        if len(group_accts) < 3:
            break

        share_type = "DEVICE" if g_idx % 2 == 0 else "IP"
        shared_val = (
            f"DEV-SHARED-{g_idx:03d}" if share_type == "DEVICE" else det_hash(f"shared_ip_{g_idx}")[:32]
        )
        for aid in group_accts:
            cid = account_cust_by_id[aid]
            if share_type == "DEVICE":
                cust_device[cid] = shared_val
            else:
                cust_ip[cid] = shared_val
            injected_gt_rows.append(
                {
                    "group_id": f"SHARED_{share_type}_{g_idx:03d}",
                    "account_id": aid,
                    "customer_id": cid,
                    "pattern": f"SHARED_{share_type}_CLUSTER",
                    "shared_identifier": shared_val,
                }
            )
            ground_truth_rows.append(
                {
                    "account_id": aid,
                    "source": "INJECTED",
                    "pattern": f"SHARED_{share_type}_CLUSTER",
                    "expected_rules": "RULE_005",
                }
            )
        # Record pairwise account_relationships
        rel_type = "SHARED_DEVICE" if share_type == "DEVICE" else "SHARED_IP"
        for i in range(len(group_accts)):
            for j in range(i + 1, len(group_accts)):
                a1, a2 = sorted([group_accts[i], group_accts[j]])
                account_relationships_map[(a1, a2, rel_type)] = {
                    "id": det_uuid("rel", f"{a1}:{a2}:{rel_type}"),
                    "source_account_id": a1,
                    "target_account_id": a2,
                    "relationship_type": rel_type,
                    "confidence": 0.95,
                    "evidence_count": 1,
                    "metadata": json.dumps({"shared_identifier": shared_val, "data_source": "SYNTHETIC_ENRICHMENT"}),
                }

    # Build identity_attributes.csv
    identity_attrs_rows: list[dict[str, Any]] = []
    for crow in customers_rows:
        cid = crow["id"]
        dev = cust_device[cid]
        iph = cust_ip[cid]
        src_tag = "PHANTOM_RING_SEED" if crow["data_source"] == "PHANTOM_RING_SEED" else "SYNTHETIC_ENRICHMENT"
        identity_attrs_rows.append(
            {
                "id": det_uuid("id_attr_dev", f"{cid}:{dev}"),
                "customer_id": cid,
                "attribute_type": "DEVICE",
                "attribute_hash": det_hash(dev),
                "attribute_value_masked": dev,
                "confidence": 1.00,
                "data_source": src_tag,
            }
        )
        identity_attrs_rows.append(
            {
                "id": det_uuid("id_attr_ip", f"{cid}:{iph}"),
                "customer_id": cid,
                "attribute_type": "IP",
                "attribute_hash": iph,
                "attribute_value_masked": f"103.{det_int(iph) % 200}.***.{(det_int(iph) >> 8) % 250}",
                "confidence": 0.95,
                "data_source": src_tag,
            }
        )

    # ------------------------------------------------------------------
    # TRANSACTIONS (PaySim + 25 Injected Rings + Operation Phantom Ring)
    # ------------------------------------------------------------------
    tx_rows: list[dict[str, Any]] = []
    acct_last_ts: dict[str, str] = {}

    # Vectorized-style fast row iteration over sampled_df
    steps = sampled_df["step"].to_numpy()
    types = sampled_df["type"].astype(str).to_numpy()
    amounts = sampled_df["amount"].to_numpy()
    origs = sampled_df["nameOrig"].astype(str).to_numpy()
    dests = sampled_df["nameDest"].astype(str).to_numpy()
    frauds = sampled_df["isFraud"].to_numpy()
    orig_idxs = sampled_df["_orig_idx"].to_numpy()

    for idx in range(len(sampled_df)):
        step_val = int(steps[idx])
        ps_type = types[idx]
        amt = float(amounts[idx])
        orig_name = origs[idx]
        dest_name = dests[idx]
        is_f = int(frauds[idx])
        o_idx = int(orig_idxs[idx])

        sender_aid = account_id_by_name[orig_name]
        receiver_aid = account_id_by_name[dest_name]
        sender_cid = account_cust_by_id[sender_aid]

        min_off = o_idx % 60
        sec_off = (o_idx * 17) % 60
        ts = (SIM_START + timedelta(hours=step_val - 1, minutes=min_off, seconds=sec_off)).isoformat()
        tx_ref = f"TXN-PS-{o_idx:08d}"
        tx_id = det_uuid("tx", tx_ref)
        mapped_type = TX_TYPE_MAP.get(ps_type, "WIRE")
        city = INDIAN_CITIES[det_int(orig_name) % len(INDIAN_CITIES)]
        dev_id = cust_device[sender_cid]
        ip_h = cust_ip[sender_cid]
        status = "FLAGGED" if is_f == 1 else "COMPLETED"

        canonical_rec = {
            "id": tx_id,
            "transaction_reference": tx_ref,
            "sender_account_id": sender_aid,
            "receiver_account_id": receiver_aid,
            "amount": f"{amt:.2f}",
            "currency": "INR",
            "transaction_type": mapped_type,
            "transaction_timestamp": ts,
        }
        b_hash = compute_hash(canonical_rec)

        tx_rows.append(
            {
                "id": tx_id,
                "transaction_reference": tx_ref,
                "sender_account_id": sender_aid,
                "receiver_account_id": receiver_aid,
                "amount": f"{amt:.2f}",
                "currency": "INR",
                "transaction_type": mapped_type,
                "transaction_timestamp": ts,
                "location": city,
                "device_id": dev_id,
                "ip_hash": ip_h,
                "status": status,
                "blockchain_hash": b_hash,
                "blockchain_tx_id": "",
                "verification_status": "VERIFIED",
                "paysim_is_fraud": is_f,
                "data_source": "PAYSIM_REAL",
            }
        )
        acct_last_ts[sender_aid] = max(acct_last_ts.get(sender_aid, ts), ts)
        acct_last_ts[receiver_aid] = max(acct_last_ts.get(receiver_aid, ts), ts)

    # Record PAYSIM fraud ground truth
    paysim_fraud_df = sampled_df[sampled_df["isFraud"] == 1]
    seen_ps_gt: set[tuple[str, str]] = set()
    for _, row in paysim_fraud_df.iterrows():
        s_aid = account_id_by_name[str(row["nameOrig"])]
        d_aid = account_id_by_name[str(row["nameDest"])]
        ps_t = str(row["type"])
        if (s_aid, "PAYSIM_FRAUD_ORIGIN") not in seen_ps_gt:
            ground_truth_rows.append(
                {
                    "account_id": s_aid,
                    "source": "PAYSIM",
                    "pattern": f"PAYSIM_{ps_t}_FRAUD_ORIGIN",
                    "expected_rules": "RULE_007",
                }
            )
            seen_ps_gt.add((s_aid, "PAYSIM_FRAUD_ORIGIN"))
        if (d_aid, "PAYSIM_FRAUD_DEST") not in seen_ps_gt:
            ground_truth_rows.append(
                {
                    "account_id": d_aid,
                    "source": "PAYSIM",
                    "pattern": f"PAYSIM_{ps_t}_FRAUD_DEST",
                    "expected_rules": "RULE_002;RULE_007" if ps_t == "TRANSFER" else "RULE_007",
                }
            )
            seen_ps_gt.add((d_aid, "PAYSIM_FRAUD_DEST"))

    # Inject 25 planted laundering rings (3-5 hops, <500K, closed within 6 hours)
    ring_pool = [account_id_by_name[n] for n in non_merchants if n not in fraud_accounts]
    ring_cursor = 0
    for r_idx in range(25):
        hop_count = int(rng.integers(3, 6))
        if ring_cursor + hop_count > len(ring_pool):
            break
        ring_accts = ring_pool[ring_cursor : ring_cursor + hop_count]
        ring_cursor += hop_count

        base_time = SIM_START + timedelta(days=int(rng.integers(1, 28)), hours=int(rng.integers(0, 18)))
        start_amt = float(rng.integers(465_000, 496_000))
        step_minutes = int(300 // hop_count)  # closes well within 6 hours

        for h in range(hop_count):
            src = ring_accts[h]
            dst = ring_accts[(h + 1) % hop_count]
            hop_amt = round(start_amt * (1.0 - 0.015 * h), 2)
            hop_ts = (base_time + timedelta(minutes=step_minutes * h)).isoformat()
            tx_ref = f"TXN-RING-{r_idx:03d}-{h:02d}"
            tx_id = det_uuid("tx", tx_ref)
            src_cid = account_cust_by_id[src]
            canonical_rec = {
                "id": tx_id,
                "transaction_reference": tx_ref,
                "sender_account_id": src,
                "receiver_account_id": dst,
                "amount": f"{hop_amt:.2f}",
                "currency": "INR",
                "transaction_type": "RTGS",
                "transaction_timestamp": hop_ts,
            }
            tx_rows.append(
                {
                    "id": tx_id,
                    "transaction_reference": tx_ref,
                    "sender_account_id": src,
                    "receiver_account_id": dst,
                    "amount": f"{hop_amt:.2f}",
                    "currency": "INR",
                    "transaction_type": "RTGS",
                    "transaction_timestamp": hop_ts,
                    "location": "Mumbai, IN",
                    "device_id": cust_device[src_cid],
                    "ip_hash": cust_ip[src_cid],
                    "status": "FLAGGED",
                    "blockchain_hash": compute_hash(canonical_rec),
                    "blockchain_tx_id": "",
                    "verification_status": "VERIFIED",
                    "paysim_is_fraud": 0,
                    "data_source": "INJECTED_RING",
                }
            )
            account_relationships_map[(src, dst, "CIRCULAR_FLOW")] = {
                "id": det_uuid("rel", f"{src}:{dst}:CIRCULAR_FLOW"),
                "source_account_id": src,
                "target_account_id": dst,
                "relationship_type": "CIRCULAR_FLOW",
                "confidence": 0.97,
                "evidence_count": 1,
                "metadata": json.dumps({"ring_id": f"RING_{r_idx:03d}", "hops": hop_count}),
            }
            ground_truth_rows.append(
                {
                    "account_id": src,
                    "source": "INJECTED",
                    "pattern": "INJECTED_RING",
                    "expected_rules": "RULE_001;RULE_002",
                }
            )
            injected_gt_rows.append(
                {
                    "group_id": f"RING_{r_idx:03d}",
                    "account_id": src,
                    "customer_id": src_cid,
                    "pattern": "INJECTED_RING",
                    "shared_identifier": f"hops={hop_count}",
                }
            )

    # Inject Operation Phantom Ring (Section 16)
    phantom_txs = [
        (
            "33333333-3333-4333-8333-000000000001",
            "TX-PHANTOM-001",
            "22222222-2222-4222-8222-000000000001",
            "22222222-2222-4222-8222-000000000002",
            480000.00,
            "2026-06-15T10:00:00+00:00",
            "Mumbai, IN",
            "DEV-ORIGIN-001",
        ),
        (
            "33333333-3333-4333-8333-000000000002",
            "TX-PHANTOM-002",
            "22222222-2222-4222-8222-000000000002",
            "22222222-2222-4222-8222-000000000003",
            470000.00,
            "2026-06-15T11:45:00+00:00",
            "Delhi, IN",
            "DEV-PHANTOM-103",
        ),
        (
            "33333333-3333-4333-8333-000000000003",
            "TX-PHANTOM-003",
            "22222222-2222-4222-8222-000000000003",
            "22222222-2222-4222-8222-000000000001",
            465000.00,
            "2026-06-15T14:15:00+00:00",
            "Bengaluru, IN",
            "DEV-PHANTOM-103",
        ),
    ]
    for tid, tref, src, dst, amt, ts, loc, dev in phantom_txs:
        canonical_rec = {
            "id": tid,
            "transaction_reference": tref,
            "sender_account_id": src,
            "receiver_account_id": dst,
            "amount": f"{amt:.2f}",
            "currency": "INR",
            "transaction_type": "RTGS",
            "transaction_timestamp": ts,
        }
        tx_rows.append(
            {
                "id": tid,
                "transaction_reference": tref,
                "sender_account_id": src,
                "receiver_account_id": dst,
                "amount": f"{amt:.2f}",
                "currency": "INR",
                "transaction_type": "RTGS",
                "transaction_timestamp": ts,
                "location": loc,
                "device_id": dev,
                "ip_hash": det_hash("ip:phantom_ring_relay")[:32],
                "status": "FLAGGED",
                "blockchain_hash": compute_hash(canonical_rec),
                "blockchain_tx_id": "",
                "verification_status": "VERIFIED",
                "paysim_is_fraud": 0,
                "data_source": "PHANTOM_RING_SEED",
            }
        )
        ground_truth_rows.append(
            {
                "account_id": src,
                "source": "INJECTED",
                "pattern": "OPERATION_PHANTOM_RING",
                "expected_rules": "RULE_001;RULE_002;RULE_003;RULE_005;RULE_006",
            }
        )

    account_relationships_map[
        ("22222222-2222-4222-8222-000000000002", "22222222-2222-4222-8222-000000000003", "SHARED_DEVICE")
    ] = {
        "id": det_uuid("rel", "phantom_shared_dev"),
        "source_account_id": "22222222-2222-4222-8222-000000000002",
        "target_account_id": "22222222-2222-4222-8222-000000000003",
        "relationship_type": "SHARED_DEVICE",
        "confidence": 1.00,
        "evidence_count": 1,
        "metadata": json.dumps({"device_id": "DEV-PHANTOM-103"}),
    }

    # Update last_activity_at on accounts
    for arow in accounts_rows:
        if arow["id"] in acct_last_ts:
            arow["last_activity_at"] = acct_last_ts[arow["id"]]

    # ------------------------------------------------------------------
    # WRITE OUTPUTS (FK-safe order)
    # ------------------------------------------------------------------
    pd.DataFrame(customers_rows).to_csv(output_dir / "customers.csv", index=False)
    pd.DataFrame(accounts_rows).to_csv(output_dir / "accounts.csv", index=False)
    pd.DataFrame(tx_rows).to_csv(output_dir / "transactions.csv", index=False)
    pd.DataFrame(identity_attrs_rows).to_csv(output_dir / "identity_attributes.csv", index=False)
    pd.DataFrame(list(account_relationships_map.values())).to_csv(
        output_dir / "account_relationships.csv", index=False
    )
    pd.DataFrame(ground_truth_rows).drop_duplicates().to_csv(
        output_dir / "ground_truth.csv", index=False
    )
    pd.DataFrame(injected_gt_rows).to_csv(output_dir / "injected_ground_truth.csv", index=False)

    report = {
        "input_file": str(input_path),
        "seed": seed,
        "target_transactions": target,
        "total_raw_rows_scanned": total_rows,
        "raw_fraud_rows": fraud_rows_count,
        "retained_fraud_rows": retained_counts["fraud"],
        "fraud_retention_rate": 1.0 if fraud_rows_count > 0 else 0.0,
        "retained_fraud_neighbor_rows": retained_counts["fraud_neighbor"],
        "retained_stratified_normal_rows": retained_counts["stratified_non_fraud"],
        "injected_ring_transactions": sum(1 for t in tx_rows if t["data_source"] == "INJECTED_RING"),
        "phantom_ring_transactions": 3,
        "final_counts": {
            "customers": len(customers_rows),
            "accounts": len(accounts_rows),
            "transactions": len(tx_rows),
            "identity_attributes": len(identity_attrs_rows),
            "account_relationships": len(account_relationships_map),
            "ground_truth": len(pd.DataFrame(ground_truth_rows).drop_duplicates()),
        },
        "balance_columns_used": False,
        "simulation_start_utc": SIM_START.isoformat(),
    }
    with open(output_dir / "sampling_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"[PHANTOM Adapter] Wrote outputs to {output_dir}")
    print(json.dumps(report["final_counts"], indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="PHANTOM PaySim streaming data adapter")
    parser.add_argument("--input", type=str, default=None, help="Path to raw PaySim CSV")
    parser.add_argument("--output", type=str, default=str(ROOT_DIR / "data" / "processed"))
    parser.add_argument("--target", type=int, default=70_000, help="Target transaction count")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed")
    parser.add_argument("--chunksize", type=int, default=100_000, help="Streaming chunk size")
    args = parser.parse_args()

    input_path = find_input_csv(args.input)
    run_adapter(
        input_path=input_path,
        output_dir=Path(args.output),
        target=args.target,
        seed=args.seed,
        chunksize=args.chunksize,
    )


if __name__ == "__main__":
    main()
