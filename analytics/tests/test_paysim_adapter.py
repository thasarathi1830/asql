"""Pytest suite for PHANTOM PaySim streaming adapter."""

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

import sys
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))
from paysim_adapter import PAYSIM_SAFE_COLS, run_adapter  # noqa: E402


def _make_mini_paysim_csv(path: Path, n_normal: int = 400, n_fraud: int = 12) -> None:
    """Create a minimal deterministic PaySim-formatted CSV fixture for unit testing."""
    rows = []
    for i in range(n_normal):
        tx_type = ["PAYMENT", "TRANSFER", "CASH_OUT", "CASH_IN", "DEBIT"][i % 5]
        dest = f"M{100000 + i}" if tx_type == "PAYMENT" else f"C{200000 + (i % 80)}"
        rows.append({
            "step": (i % 100) + 1,
            "type": tx_type,
            "amount": round(1000.0 + (i * 137.5) % 90000.0, 2),
            "nameOrig": f"C{100000 + (i % 90)}",
            "oldbalanceOrg": 50000.0,
            "newbalanceOrig": 40000.0,
            "nameDest": dest,
            "oldbalanceDest": 10000.0,
            "newbalanceDest": 20000.0,
            "isFraud": 0,
            "isFlaggedFraud": 0,
        })
    for j in range(n_fraud // 2):
        amt = 125000.0 + j * 10000.0
        step = 10 + j * 5
        mule = f"C9900{j}"
        rows.append({
            "step": step, "type": "TRANSFER", "amount": amt,
            "nameOrig": f"C8800{j}", "oldbalanceOrg": amt, "newbalanceOrig": 0.0,
            "nameDest": mule, "oldbalanceDest": 0.0, "newbalanceDest": 0.0,
            "isFraud": 1, "isFlaggedFraud": 0,
        })
        rows.append({
            "step": step, "type": "CASH_OUT", "amount": amt,
            "nameOrig": mule, "oldbalanceOrg": amt, "newbalanceOrig": 0.0,
            "nameDest": f"C7700{j}", "oldbalanceDest": 0.0, "newbalanceDest": amt,
            "isFraud": 1, "isFlaggedFraud": 0,
        })
    pd.DataFrame(rows).to_csv(path, index=False)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_adapter_fraud_retention_and_target(tmp_path: Path) -> None:
    raw_csv = tmp_path / "mini_paysim.csv"
    _make_mini_paysim_csv(raw_csv, n_normal=450, n_fraud=12)
    out_dir = tmp_path / "out"

    report = run_adapter(raw_csv, out_dir, target=300, seed=42, chunksize=100)
    assert report["fraud_retention_rate"] == 1.0
    assert report["retained_fraud_rows"] == 12
    assert report["balance_columns_used"] is False

    tx_df = pd.read_csv(out_dir / "transactions.csv")
    assert int(tx_df["paysim_is_fraud"].sum()) == 12
    # Target ~300 (includes 3 Phantom Ring + injected rings)
    assert 200 <= len(tx_df) <= 450


def test_adapter_foreign_key_integrity(tmp_path: Path) -> None:
    raw_csv = tmp_path / "mini_paysim.csv"
    _make_mini_paysim_csv(raw_csv, n_normal=300, n_fraud=6)
    out_dir = tmp_path / "out"
    run_adapter(raw_csv, out_dir, target=250, seed=42, chunksize=100)

    cust_df = pd.read_csv(out_dir / "customers.csv")
    acct_df = pd.read_csv(out_dir / "accounts.csv")
    tx_df = pd.read_csv(out_dir / "transactions.csv")
    id_df = pd.read_csv(out_dir / "identity_attributes.csv")
    rel_df = pd.read_csv(out_dir / "account_relationships.csv")

    cust_ids = set(cust_df["id"])
    acct_ids = set(acct_df["id"])

    assert set(acct_df["customer_id"]).issubset(cust_ids)
    assert set(tx_df["sender_account_id"]).issubset(acct_ids)
    assert set(tx_df["receiver_account_id"]).issubset(acct_ids)
    assert set(id_df["customer_id"]).issubset(cust_ids)
    if len(rel_df) > 0:
        assert set(rel_df["source_account_id"]).issubset(acct_ids)
        assert set(rel_df["target_account_id"]).issubset(acct_ids)


def test_adapter_determinism(tmp_path: Path) -> None:
    raw_csv = tmp_path / "mini_paysim.csv"
    _make_mini_paysim_csv(raw_csv, n_normal=250, n_fraud=6)

    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"
    run_adapter(raw_csv, out1, target=200, seed=42, chunksize=80)
    run_adapter(raw_csv, out2, target=200, seed=42, chunksize=80)

    for fname in ["customers.csv", "accounts.csv", "transactions.csv", "ground_truth.csv"]:
        assert _sha256_file(out1 / fname) == _sha256_file(out2 / fname)


def test_adapter_no_balance_columns_used(tmp_path: Path) -> None:
    for bcol in ["oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest"]:
        assert bcol not in PAYSIM_SAFE_COLS

    raw_csv = tmp_path / "mini_paysim.csv"
    _make_mini_paysim_csv(raw_csv, n_normal=150, n_fraud=4)
    out_dir = tmp_path / "out"
    run_adapter(raw_csv, out_dir, target=120, seed=42, chunksize=50)

    tx_df = pd.read_csv(out_dir / "transactions.csv")
    for bcol in ["oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest"]:
        assert bcol not in tx_df.columns
    # Every transaction has a deterministic 0x-prefixed SHA-256 hash
    assert tx_df["blockchain_hash"].str.startswith("0x").all()
    assert (tx_df["blockchain_hash"].str.len() == 66).all()

