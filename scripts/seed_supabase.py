"""PHANTOM Database Seeder (Dual-Mode: Cloud PostgreSQL/Supabase & Local SQLite/PG).

Bulk-loads processed CSVs from data/processed/ into PostgreSQL (using psycopg2
batched inserts / ON CONFLICT DO NOTHING) or local SQLite (when PHANTOM_MODE=local
and no Postgres server is available), verifying foreign-key integrity and printing
exact row counts.

Usage:
    python scripts/seed_supabase.py
"""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

SQLITE_SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS profiles (
    id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL DEFAULT 'INVESTIGATOR',
    badge_number TEXT,
    avatar_url TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customers (
    id TEXT PRIMARY KEY,
    customer_reference TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    email_masked TEXT NOT NULL,
    phone_masked TEXT NOT NULL,
    country TEXT NOT NULL DEFAULT 'IN',
    identity_hash TEXT NOT NULL,
    risk_score REAL DEFAULT 0.00,
    risk_level TEXT DEFAULT 'LOW',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,
    account_number_masked TEXT UNIQUE NOT NULL,
    customer_id TEXT NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    account_type TEXT NOT NULL,
    bank_code TEXT NOT NULL DEFAULT 'HDFC',
    country TEXT NOT NULL DEFAULT 'IN',
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    risk_score REAL DEFAULT 0.00,
    risk_level TEXT DEFAULT 'LOW',
    is_dormant INTEGER NOT NULL DEFAULT 0,
    last_activity_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    transaction_reference TEXT UNIQUE NOT NULL,
    sender_account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE RESTRICT,
    receiver_account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE RESTRICT,
    amount REAL NOT NULL CHECK (amount > 0),
    currency TEXT NOT NULL DEFAULT 'INR',
    transaction_type TEXT NOT NULL,
    transaction_timestamp TEXT NOT NULL,
    location TEXT,
    device_id TEXT,
    ip_hash TEXT,
    status TEXT NOT NULL,
    blockchain_hash TEXT,
    blockchain_tx_id TEXT,
    verification_status TEXT DEFAULT 'VERIFIED',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS identity_attributes (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    attribute_type TEXT NOT NULL,
    attribute_hash TEXT NOT NULL,
    attribute_value_masked TEXT NOT NULL,
    confidence REAL DEFAULT 1.00,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS account_relationships (
    id TEXT PRIMARY KEY,
    source_account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    target_account_id TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,
    confidence REAL DEFAULT 0.85,
    evidence_count INTEGER DEFAULT 1,
    metadata TEXT DEFAULT '{}',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (source_account_id, target_account_id, relationship_type)
);

CREATE TABLE IF NOT EXISTS risk_scores (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    score REAL NOT NULL,
    risk_level TEXT NOT NULL,
    reasons TEXT DEFAULT '[]',
    calculated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS risk_factors (
    id TEXT PRIMARY KEY,
    risk_score_id TEXT NOT NULL REFERENCES risk_scores(id) ON DELETE CASCADE,
    rule_id TEXT NOT NULL,
    rule_name TEXT NOT NULL,
    severity TEXT NOT NULL,
    weight REAL NOT NULL,
    evidence TEXT DEFAULT '{}',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fraud_rules (
    id TEXT PRIMARY KEY,
    rule_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    default_weight REAL NOT NULL,
    severity TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    evidence TEXT DEFAULT '{}',
    status TEXT DEFAULT 'NEW',
    assigned_to TEXT REFERENCES profiles(id) ON DELETE SET NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS investigations (
    id TEXT PRIMARY KEY,
    investigator_id TEXT REFERENCES profiles(id) ON DELETE SET NULL,
    case_number TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    priority TEXT DEFAULT 'MEDIUM',
    status TEXT DEFAULT 'OPEN',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS investigation_entities (
    id TEXT PRIMARY KEY,
    investigation_id TEXT NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    notes TEXT,
    added_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (investigation_id, entity_type, entity_id)
);

CREATE TABLE IF NOT EXISTS investigation_notes (
    id TEXT PRIMARY KEY,
    investigation_id TEXT NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    author_id TEXT REFERENCES profiles(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS blockchain_records (
    id TEXT PRIMARY KEY,
    record_hash TEXT UNIQUE NOT NULL,
    record_type TEXT NOT NULL,
    canonical_payload TEXT NOT NULL,
    blockchain_tx_id TEXT NOT NULL,
    block_number INTEGER DEFAULT 0,
    submitter_address TEXT,
    status TEXT DEFAULT 'VERIFIED',
    verified_at TEXT DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES profiles(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    previous_hash TEXT,
    current_hash TEXT,
    blockchain_tx_id TEXT,
    details TEXT DEFAULT '{}',
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS network_clusters (
    id TEXT PRIMARY KEY,
    cluster_name TEXT NOT NULL,
    entity_ids TEXT DEFAULT '[]',
    risk_score REAL DEFAULT 50.00,
    description TEXT NOT NULL,
    detected_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ingestion_jobs (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    total_records INTEGER DEFAULT 0,
    processed_records INTEGER DEFAULT 0,
    status TEXT DEFAULT 'PENDING',
    error_log TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS system_events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    severity TEXT DEFAULT 'INFO',
    payload TEXT DEFAULT '{}',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

TABLE_COLUMNS: dict[str, list[str]] = {
    "customers": [
        "id", "customer_reference", "name", "email_masked", "phone_masked",
        "country", "identity_hash", "risk_score", "risk_level",
    ],
    "accounts": [
        "id", "account_number_masked", "customer_id", "account_type", "bank_code",
        "country", "status", "risk_score", "risk_level", "is_dormant", "last_activity_at",
    ],
    "transactions": [
        "id", "transaction_reference", "sender_account_id", "receiver_account_id",
        "amount", "currency", "transaction_type", "transaction_timestamp",
        "location", "device_id", "ip_hash", "status", "blockchain_hash",
        "blockchain_tx_id", "verification_status",
    ],
    "identity_attributes": [
        "id", "customer_id", "attribute_type", "attribute_hash",
        "attribute_value_masked", "confidence",
    ],
    "account_relationships": [
        "id", "source_account_id", "target_account_id", "relationship_type",
        "confidence", "evidence_count", "metadata",
    ],
}


def seed_sqlite(processed_dir: Path, db_path: Path) -> dict[str, int]:
    """Load processed CSVs into local SQLite database with FK enforcement."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SQLITE_SCHEMA)
    conn.execute("PRAGMA foreign_keys = ON;")

    counts: dict[str, int] = {}
    load_order = [
        ("customers", "customers.csv"),
        ("accounts", "accounts.csv"),
        ("transactions", "transactions.csv"),
        ("identity_attributes", "identity_attributes.csv"),
        ("account_relationships", "account_relationships.csv"),
    ]

    for table, csv_name in load_order:
        csv_path = processed_dir / csv_name
        if not csv_path.exists():
            print(f"[seed] Skipping missing {csv_path}")
            continue
        df = pd.read_csv(csv_path, keep_default_na=False)
        cols = TABLE_COLUMNS[table]
        df = df[cols].copy()
        if "is_dormant" in df.columns:
            df["is_dormant"] = df["is_dormant"].apply(lambda x: 1 if str(x).lower() in ("true", "1") else 0)

        placeholders = ", ".join(["?"] * len(cols))
        col_list = ", ".join(cols)
        sql = f"INSERT OR IGNORE INTO {table} ({col_list}) VALUES ({placeholders})"

        rows = [tuple(r) for r in df.itertuples(index=False, name=None)]
        batch_size = 2000
        for i in range(0, len(rows), batch_size):
            conn.executemany(sql, rows[i : i + batch_size])
        conn.commit()
        cur = conn.execute(f"SELECT COUNT(*) FROM {table}")
        cnt = int(cur.fetchone()[0])
        counts[table] = cnt
        print(f"[seed:sqlite] {table}: {cnt:,} rows loaded")

    # Verify zero FK violations
    fk_errors = conn.execute("PRAGMA foreign_key_check;").fetchall()
    if fk_errors:
        conn.close()
        raise RuntimeError(f"Foreign key violations detected: {fk_errors[:5]}")
    print("[seed:sqlite] PRAGMA foreign_key_check: 0 violations")
    conn.close()
    return counts


def seed_postgres(processed_dir: Path, database_url: str) -> dict[str, int]:
    """Load processed CSVs into PostgreSQL (Supabase / local PG) using batched inserts."""
    import psycopg2
    from psycopg2.extras import execute_values

    conn = psycopg2.connect(database_url)
    counts: dict[str, int] = {}
    load_order = [
        ("customers", "customers.csv"),
        ("accounts", "accounts.csv"),
        ("transactions", "transactions.csv"),
        ("identity_attributes", "identity_attributes.csv"),
        ("account_relationships", "account_relationships.csv"),
    ]

    with conn.cursor() as cur:
        for table, csv_name in load_order:
            csv_path = processed_dir / csv_name
            if not csv_path.exists():
                continue
            df = pd.read_csv(csv_path, keep_default_na=False)
            cols = TABLE_COLUMNS[table]
            df = df[cols].copy()
            col_list = ", ".join(cols)
            sql = f"INSERT INTO {table} ({col_list}) VALUES %s ON CONFLICT DO NOTHING"
            rows = [tuple(r) for r in df.itertuples(index=False, name=None)]
            for i in range(0, len(rows), 1000):
                execute_values(cur, sql, rows[i : i + 1000], page_size=1000)
            conn.commit()
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            cnt = int(cur.fetchone()[0])
            counts[table] = cnt
            print(f"[seed:postgres] {table}: {cnt:,} rows loaded")
    conn.close()
    return counts


def main() -> None:
    mode = os.getenv("PHANTOM_MODE", "local").lower()
    database_url = os.getenv("DATABASE_URL", "")
    processed_dir = ROOT_DIR / "data" / "processed"

    if mode == "cloud" and database_url and "localhost" not in database_url:
        seed_postgres(processed_dir, database_url)
        return

    # Local mode: try local PG if explicitly reachable, otherwise SQLite
    if database_url and database_url.startswith("postgresql://"):
        try:
            import psycopg2

            conn = psycopg2.connect(database_url, connect_timeout=2)
            conn.close()
            seed_postgres(processed_dir, database_url)
            return
        except Exception:
            print("[seed] Local PostgreSQL unreachable; using SQLite fallback at data/phantom_local.db")

    seed_sqlite(processed_dir, ROOT_DIR / "data" / "phantom_local.db")


if __name__ == "__main__":
    main()
