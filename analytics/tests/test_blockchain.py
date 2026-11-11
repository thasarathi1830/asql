"""Pytest suite for Blockchain canonical JSON & SHA-256 tamper detection."""

from app.blockchain import canonical_json, compute_hash, verify_record


def test_canonical_json_determinism_and_volatile_stripping() -> None:
    rec1 = {
        "id": "tx-1",
        "amount": 480000.0,
        "sender_account_id": "ACC-1",
        "blockchain_hash": "0xold",
        "created_at": "2026-06-15T10:00:00Z",
    }
    rec2 = {
        "sender_account_id": "ACC-1",
        "amount": 480000.0,
        "id": "tx-1",
        "verification_status": "PENDING",
        "blockchain_tx_id": "0xabc",
    }
    assert canonical_json(rec1) == canonical_json(rec2)
    h1 = compute_hash(rec1)
    h2 = compute_hash(rec2)
    assert h1 == h2
    assert h1.startswith("0x") and len(h1) == 66


def test_tamper_detection_catches_amount_modification() -> None:
    original = {
        "id": "tx-phantom-1",
        "transaction_reference": "TX-PHANTOM-001",
        "sender_account_id": "ACC-0001-9041",
        "receiver_account_id": "ACC-0044-7721",
        "amount": 480000.0,
    }
    committed_hash = compute_hash(original)
    assert verify_record(original, committed_hash) is True

    tampered = dict(original, amount=48000.0)
    assert verify_record(tampered, committed_hash) is False

