"""Pytest suite for New Customer Onboarding & Real-Time Pre-Transaction Screening."""

import time
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.config import ANALYTICS_API_KEY
from app.graph_analysis import TransactionGraphEngine
from app.main import app
from app.onboarding_risk import (
    OnboardingRiskEngine,
    mask_email,
    mask_phone,
    salted_hash,
)
from app.screening_engine import PreTransactionScreeningEngine

client = TestClient(app)
AUTH_HEADERS = {"X-Internal-API-Key": ANALYTICS_API_KEY}


# ── Unit Tests: Onboarding Risk Assessment ─────────────────────────────

def test_onboarding_clean_customer_approves() -> None:
    engine = OnboardingRiskEngine()
    cust_data = {
        "customer_reference": "CUST-CLEAN-01",
        "full_name": "Aarav Sharma",
        "country": "IN",
        "date_of_birth": "1990-05-15",
        "declared_monthly_income": 85000.0,
        "customer_type": "INDIVIDUAL",
        "identity_hash": salted_hash("CUST-CLEAN-01:Aarav Sharma"),
    }
    accounts = [{"account_type": "SAVINGS", "bank_code": "HDFC"}]
    attrs = [{"attribute_type": "DEVICE", "attribute_hash": salted_hash("CLEAN-DEV-99")}]

    res = engine.assess_customer(cust_data, accounts, attrs)
    assert res["onboarding_score"] < 30.0
    assert res["decision"] == "APPROVE"
    assert res["risk_level"] == "LOW"


def test_onboarding_suspicious_device_sharing_gets_enhanced_or_higher() -> None:
    # Seed existing attribute with a high-risk entity
    existing_attrs = [
        {
            "attribute_type": "DEVICE",
            "attribute_hash": salted_hash("SHARED-DEV-001"),
            "attribute_value_masked": "DEV-PHANTOM-103",
            "customer_id": "cust-bad-1",
            "risk_level": "CRITICAL",
            "risk_score": 94.0,
        }
    ]
    engine = OnboardingRiskEngine(existing_attributes=existing_attrs)
    cust_data = {
        "customer_reference": "CUST-SUSP-01",
        "full_name": "Rahul Verma",
        "country": "IN",
        "date_of_birth": "1992-08-20",
    }
    accounts = [{"account_type": "SAVINGS", "bank_code": "ICICI"}]
    attrs = [{"attribute_type": "DEVICE", "attribute_hash": salted_hash("SHARED-DEV-001")}]

    res = engine.assess_customer(cust_data, accounts, attrs)
    assert res["onboarding_score"] >= 30.0
    assert res["decision"] in ("ENHANCED_DUE_DILIGENCE", "MANUAL_REVIEW", "ESCALATE")
    onb1 = next(c for c in res["checks"] if c["rule_id"] == "ONB_001")
    assert onb1["score"] >= 15.0
    assert len(res["matched_entities"]) >= 1


def test_onboarding_duplicate_identity_triggers_onb_003() -> None:
    h = salted_hash("DUP-CUST:Priya Singh")
    existing_custs = [{"id": "c-001", "customer_reference": "C001", "identity_hash": h}]
    engine = OnboardingRiskEngine(existing_customers=existing_custs)

    cust_data = {
        "customer_reference": "CUST-DUP-NEW",
        "full_name": "Priya Singh",
        "identity_hash": h,
    }
    res = engine.assess_customer(cust_data, [], [])
    onb3 = next(c for c in res["checks"] if c["rule_id"] == "ONB_003")
    assert onb3["score"] == 20.0
    assert "Duplicate identity match found" in onb3["reason"]


def test_onboarding_privacy_no_raw_pii_stored() -> None:
    raw_email = "secret_user@example.com"
    raw_phone = "+919876543210"

    masked_e = mask_email(raw_email)
    masked_p = mask_phone(raw_phone)
    h_e = salted_hash(raw_email)

    assert "@" in masked_e and "secret_user" not in masked_e
    assert "987654" not in masked_p
    assert raw_email not in h_e
    assert len(h_e) == 64


# ── Unit Tests: Real-Time Pre-Transaction Screening ────────────────────

def test_screening_cycle_closure_triggers_rule_001() -> None:
    g = TransactionGraphEngine()
    # Existing graph: ACC_B -> ACC_C -> ACC_A
    g.load_transactions([
        {"sender_account_id": "ACC_B", "receiver_account_id": "ACC_C", "amount": 100000},
        {"sender_account_id": "ACC_C", "receiver_account_id": "ACC_A", "amount": 100000},
    ])
    screener = PreTransactionScreeningEngine(graph_engine=g)

    # Screening new transaction: ACC_A -> ACC_B (completes loop A -> B -> C -> A)
    tx = {
        "transaction_reference": "TX-SCR-001",
        "sender_account_id": "ACC_A",
        "receiver_account_id": "ACC_B",
        "amount": 95000,
    }
    res = screener.screen_transaction(tx)
    assert any(r["rule_id"] == "RULE_001" for r in res["rules_triggered"])
    assert res["decision"] in ("ALLOW_WITH_MONITORING", "HOLD_FOR_REVIEW", "BLOCK")


def test_screening_idempotency() -> None:
    screener = PreTransactionScreeningEngine()
    tx = {
        "transaction_reference": "TX-IDEMP-001",
        "sender_account_id": "S1",
        "receiver_account_id": "R1",
        "amount": 50000,
    }
    res1 = screener.screen_transaction(tx)
    assert res1["is_cached"] is False

    res2 = screener.screen_transaction(tx)
    assert res2["is_cached"] is True
    assert res1["decision"] == res2["decision"]
    assert res1["risk_score"] == res2["risk_score"]


def test_screening_latency_under_500ms() -> None:
    g = TransactionGraphEngine()
    # Populate a synthetic reference graph of 1,000 edges
    synthetic_txs = [
        {"sender_account_id": f"NODE_{i % 200}", "receiver_account_id": f"NODE_{(i + 1) % 200}", "amount": 5000}
        for i in range(1000)
    ]
    g.load_transactions(synthetic_txs)
    screener = PreTransactionScreeningEngine(graph_engine=g)

    latencies = []
    for i in range(50):
        tx = {
            "transaction_reference": f"TX-LAT-{i}",
            "sender_account_id": f"NODE_{i}",
            "receiver_account_id": f"NODE_{(i + 5) % 200}",
            "amount": 25000,
        }
        res = screener.screen_transaction(tx)
        latencies.append(res["latency_ms"])

    p95 = np.percentile(latencies, 95)
    print(f"\n[Screening Latency] p50: {np.percentile(latencies, 50):.2f}ms, p95: {p95:.2f}ms, p99: {np.percentile(latencies, 99):.2f}ms")
    assert p95 < 500.0, f"Screening p95 latency violated: {p95}ms >= 500ms"


def test_api_onboarding_and_screening_endpoints() -> None:
    # 1. Test Onboarding endpoint
    onb_payload = {
        "customer_reference": "CUST-API-TEST-01",
        "full_name": "Kavita Nair",
        "country": "IN",
        "email": "kavita.nair@sample.in",
        "phone": "+919812345678",
        "accounts": [{"account_number": "ACC-1234-5678", "account_type": "SAVINGS"}],
    }
    r_onb = client.post("/api/analytics/onboard-customer", json=onb_payload, headers=AUTH_HEADERS)
    assert r_onb.status_code == 200
    data = r_onb.json()
    assert data["customer_reference"] == "CUST-API-TEST-01"
    assert "onboarding_score" in data["assessment"]

    # 2. Test Screening endpoint
    scr_payload = {
        "transaction_reference": "TX-API-SCR-01",
        "sender_account_id": "ACC_ORIGIN",
        "receiver_account_id": "ACC_TARGET",
        "amount": 45000.0,
    }
    r_scr = client.post("/api/analytics/screen-transaction", json=scr_payload, headers=AUTH_HEADERS)
    assert r_scr.status_code == 200
    scr_data = r_scr.json()
    assert scr_data["decision"] in ("ALLOW", "ALLOW_WITH_MONITORING", "HOLD_FOR_REVIEW", "BLOCK")
    assert scr_data["latency_ms"] < 500.0

