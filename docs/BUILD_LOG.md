# PHANTOM — Build Log

## Phase 0: Audit and Plan
- **Timestamp**: 2026-11-11
- **Built**:
  - Read `PHANTOM_Project_Documentation.md` and `PAPER_ANALYSIS.md` completely.
  - Located real 6.36M-row PaySim dataset (`PS_20174392719_1491204439457_log.csv`, 493.5 MB) in `archive/` and copied to `data/raw/`.
  - Scaffolded full repository directory structure matching documentation Section 5.
  - Created `.gitignore`, `.env.example`, `Makefile`, `README.md`, `architecture.md`, `docs/architecture.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/DECISIONS.md`, `docs/BUILD_LOG.md`, `.github/workflows/ci.yml`.
- **Verification**: Running `make setup` to install Python, Frontend, and Blockchain dependencies.

## Phase 1: Data Layer & PaySim Streaming Adapter
- **Timestamp**: 2026-11-11
- **Built**:
  - Completed `supabase/migrations/20261006000001_initial_schema.sql` (18 tables, 19+ indexes, auto-profile trigger), `20261006000002_advanced_analytics.sql` (8 PL/pgSQL functions + 1 view + DML audit trigger), `20261006000003_rls_policies.sql` (RLS across all 18 tables), `supabase/seed.sql`, `database/schema.sql`, `supabase/config.toml`.
  - Implemented `scripts/paysim_adapter.py` (two-pass chunked streaming, seed=42, zero balance column usage, deterministic SHA-256 hashes, 40 shared device/IP groups, 25 injected rings, Operation Phantom Ring).
  - Implemented `scripts/seed_supabase.py` (dual-mode PostgreSQL / SQLite loader), `scripts/generate_demo_data.py`, `scripts/validate_sql.py`, and `analytics/tests/test_paysim_adapter.py`.
- **Gate Results**:
  - `validate_sql.py`: PASSED (18 tables, 19 indexes, 8 functions + 1 view, 18 RLS tables).
  - `pytest tests/test_paysim_adapter.py -v`: 4 passed in 5.74s.
  - Real PaySim run (6,362,620 rows): retained 8,213/8,213 fraud rows (100%), 57,481 neighbor rows, 4,186 stratified normal rows + 98 injected ring rows + 3 Phantom Ring rows = 69,981 transactions, 82,218 accounts, 46,408 customers, 92,816 identity attributes, 427 relationships.
  - `seed_supabase.py`: loaded all rows into `data/phantom_local.db` with `PRAGMA foreign_key_check: 0 violations`.
