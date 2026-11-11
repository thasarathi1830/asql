"""PHANTOM Analytics — Environment configuration."""

import os

# ── Mode ──────────────────────────────────────────────────────────────
PHANTOM_MODE = os.getenv("PHANTOM_MODE", "local")  # "cloud" | "local"

# ── Database ──────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:54322/postgres")

# ── Supabase ──────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "http://localhost:54321")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# ── Neo4j ─────────────────────────────────────────────────────────────
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# ── API ───────────────────────────────────────────────────────────────
ANALYTICS_API_KEY = os.getenv("ANALYTICS_API_KEY", "dev-key")

# ── Risk-rule weights (RULE_001 … RULE_008) ───────────────────────────
RULE_WEIGHTS = {
    "RULE_001": 25,   # Cyclic fund flow
    "RULE_002": 20,   # Mule-account behaviour
    "RULE_003": 20,   # Structuring / smurfing
    "RULE_004": 15,   # Dormant-account activation
    "RULE_005": 15,   # Shared-identity collision
    "RULE_006": 15,   # Network hub / high centrality
    "RULE_007": 15,   # Risky counterparties
    "RULE_008": 10,   # Transaction velocity spike
}

# ── Risk profiles ─────────────────────────────────────────────────────
RISK_PROFILES = {
    "default": {
        "structuring_threshold_min": 80_000,
        "structuring_threshold_max": 99_999,
        "structuring_window_hours": 24,
        "structuring_min_tx_count": 3,
        "dormant_days": 60,
        "dormant_min_burst": 100_000,
        "rapid_pass_max_delay_hours": 2,
        "rapid_pass_retain_ratio_max": 0.10,
        "cycle_max_length": 5,
        "cycle_time_window_hours": 72,
    },
    "paysim": {
        "structuring_threshold_min": 200_000,
        "structuring_threshold_max": 499_999,
        "structuring_window_hours": 48,
        "structuring_min_tx_count": 4,
        "dormant_days": 90,
        "dormant_min_burst": 500_000,
        "rapid_pass_max_delay_hours": 4,
        "rapid_pass_retain_ratio_max": 0.15,
        "cycle_max_length": 6,
        "cycle_time_window_hours": 168,
    },
}
