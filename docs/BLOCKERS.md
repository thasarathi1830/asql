# PHANTOM — Environment & External Blockers

All core software, data processing, risk scoring, evaluation, smart contract, API, and frontend components build and run locally in `PHANTOM_MODE=local`.

The only items unavailable in this local execution environment are external managed cloud credentials:

1. **Supabase Cloud Project Credentials (`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL`)**:
   - Not provisioned in this environment.
   - **Fallback Active**: `scripts/seed_supabase.py` loads all processed data into local SQLite (`data/phantom_local.db`) with `PRAGMA foreign_keys = ON` and verifies zero FK violations; SQL migrations are validated with `sqlglot` (PostgreSQL dialect).
2. **Neo4j Aura Instance (`NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`)**:
   - Not provisioned in this environment.
   - **Fallback Active**: `scripts/sync_neo4j.py` executes its deterministic NetworkX projection fallback in `PHANTOM_MODE=local` and verifies cycle parity with the Python analytics engine.
3. **Sepolia Testnet RPC & Deployer Key (`SEPOLIA_RPC_URL`, `DEPLOYER_PRIVATE_KEY`)**:
   - Not provisioned in this environment.
   - **Fallback Active**: Blockchain anchoring and tamper detection run against the local Hardhat EVM network (`npx hardhat test` and local Hardhat EVM script).
4. **PaySim Dataset Status**:
   - **Resolved**: The real 6,362,620-row PaySim dataset (`PS_20174392719_1491204439457_log.csv`, 493.5 MB) was found in `archive/` and copied to `data/raw/PS_20174392719_1491204439457_log.csv`. All data and evaluation runs use the real PaySim dataset.
