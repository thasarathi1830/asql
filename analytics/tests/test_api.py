"""Pytest suite for FastAPI endpoints and API key authentication."""

from fastapi.testclient import TestClient

from app.config import ANALYTICS_API_KEY
from app.main import app

client = TestClient(app)
AUTH_HEADERS = {"X-Internal-API-Key": ANALYTICS_API_KEY}


def test_health_endpoint() -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_auth_failure_returns_401_and_403() -> None:
    payload = {"transactions": []}
    resp_missing = client.post("/api/analytics/centrality", json=payload)
    assert resp_missing.status_code == 401

    resp_bad = client.post(
        "/api/analytics/centrality",
        json=payload,
        headers={"X-Internal-API-Key": "wrong-key"},
    )
    assert resp_bad.status_code == 403


def test_api_cycles_clusters_and_risk_score() -> None:
    txs = [
        {"sender_account_id": "A", "receiver_account_id": "B", "amount": 480000, "transaction_timestamp": "2026-06-15T10:00:00Z"},
        {"sender_account_id": "B", "receiver_account_id": "C", "amount": 470000, "transaction_timestamp": "2026-06-15T11:30:00Z"},
        {"sender_account_id": "C", "receiver_account_id": "A", "amount": 465000, "transaction_timestamp": "2026-06-15T13:00:00Z"},
    ]
    r_cyc = client.post("/api/analytics/detect-cycles", json={"transactions": txs}, headers=AUTH_HEADERS)
    assert r_cyc.status_code == 200
    assert len(r_cyc.json()["cycles"]) == 1

    r_clu = client.post("/api/analytics/clusters", json={"transactions": txs}, headers=AUTH_HEADERS)
    assert r_clu.status_code == 200
    assert r_clu.json()["node_count"] == 3

    r_score = client.post(
        "/api/analytics/risk-score",
        json={"account_id": "B", "transactions": txs},
        headers=AUTH_HEADERS,
    )
    assert r_score.status_code == 200
    assert r_score.json()["risk_score"] > 0

    r_batch = client.post(
        "/api/analytics/score-batch",
        json={"account_ids": ["A", "B", "C"], "transactions": txs},
        headers=AUTH_HEADERS,
    )
    assert r_batch.status_code == 200
    assert r_batch.json()["count"] == 3


def test_api_verify_blockchain() -> None:
    rec = {"id": "tx-1", "amount": 1000.0}
    r1 = client.post("/api/analytics/verify-blockchain", json={"record": rec}, headers=AUTH_HEADERS)
    assert r1.status_code == 200
    h = r1.json()["hash"]

    r2 = client.post(
        "/api/analytics/verify-blockchain",
        json={"record": rec, "expected_hash": h},
        headers=AUTH_HEADERS,
    )
    assert r2.status_code == 200
    assert r2.json()["valid"] is True
    assert r2.json()["status"] == "VERIFIED"

