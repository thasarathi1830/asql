# PHANTOM — Implementation Plan & Section Mapping

This plan maps every numbered section (1–21) of `docs/PHANTOM_Project_Documentation.md` and `docs/PAPER_ANALYSIS.md` to concrete repository files, execution phases, and risks.

## Documentation Section Mapping (Sections 1–21)

| Section | Title | Mapped Files | Phase |
|---|---|---|---|
| 1 | Executive Summary | `README.md`, `docs/architecture.md`, `frontend/src/pages/Landing.tsx` | 0, 7 |
| 2 | Problem Statement & Motivation | `README.md`, `analytics/evaluation/evaluate.py`, `docs/EVALUATION.md` | 0, 3 |
| 3 | System Architecture | `docs/architecture.md`, `architecture.md`, `.env.example` | 0 |
| 4 | Technology Stack | `frontend/package.json`, `analytics/requirements.txt`, `blockchain/package.json` | 0 |
| 5 | Project Directory Structure | Entire repository tree (`frontend/`, `analytics/`, `supabase/`, `blockchain/`, `database/`, `scripts/`, `data/`, `.github/`) | 0 |
| 6 | Database Design (PostgreSQL / Supabase) | `supabase/migrations/20261006000001_initial_schema.sql`, `database/schema.sql`, `supabase/config.toml` | 1 |
| 7 | Advanced SQL Analytics | `supabase/migrations/20261006000002_advanced_analytics.sql` (8 functions + 1 view) | 1 |
| 8 | Row Level Security (RLS) & Access Control | `supabase/migrations/20261006000003_rls_policies.sql` | 1 |
| 9 | Neo4j Graph Database Model | `scripts/sync_neo4j.py`, `analytics/app/graph_analysis.py` | 5 |
| 10 | Python Analytics & Risk Engine | `analytics/app/main.py`, `config.py`, `graph_analysis.py`, `anomaly_detection.py`, `structuring_engine.py`, `network_analysis.py`, `blockchain.py`, `risk_engine.py` | 2 |
| 11 | Explainable 8-Factor Risk Scoring | `analytics/app/risk_engine.py`, `scripts/run_risk_analysis.py`, `analytics/tests/` | 2 |
| 12 | Blockchain Tamper-Evident Verification | `blockchain/contracts/PhantomAuditRegistry.sol`, `blockchain/hardhat.config.ts`, `blockchain/scripts/deploy.ts`, `blockchain/test/PhantomAuditRegistry.test.ts`, `analytics/app/blockchain.py`, `frontend/src/lib/blockchainVerifier.ts`, `frontend/src/pages/BlockchainVerification.tsx` | 4, 7 |
| 13 | Frontend Application (React + TypeScript) | `frontend/src/App.tsx`, `frontend/src/types/index.ts`, `frontend/src/lib/*`, `frontend/src/components/*`, `frontend/src/pages/*` (15 pages) | 7 |
| 14 | REST API & Edge Functions | `analytics/app/routers/analytics.py`, `health.py`, `supabase/functions/calculate-risk/index.ts`, `verify-blockchain/index.ts`, `health/index.ts`, `ingest-transactions/index.ts`, `generate-report/index.ts` | 6 |
| 15 | End-to-End Data Flow | `scripts/paysim_adapter.py`, `scripts/seed_supabase.py`, `scripts/run_risk_analysis.py`, `scripts/e2e_demo.py` | 1, 8 |
| 16 | Pre-Seeded Case Study: Operation Phantom Ring | `supabase/seed.sql`, `scripts/paysim_adapter.py`, `scripts/generate_demo_data.py`, `frontend/src/lib/demoData.ts` | 1, 2, 7 |
| 17 | CI/CD Pipeline | `.github/workflows/ci.yml` | 0 |
| 18 | Cloud Deployment Guide | `docs/DEPLOYMENT.md`, `README.md` | 0, 8 |
| 19 | Local Development Setup | `Makefile`, `README.md`, `.env.example` | 0 |
| 20 | Verification Checklist | `docs/COMPLETION_MATRIX.md`, `analytics/tests/`, `blockchain/test/` | 9 |
| 21 | Development Roadmap | `docs/BUILD_LOG.md`, `docs/COMPLETION_MATRIX.md` | 0, 9 |

## Risks & Mitigations

1. **No Live Cloud Credentials in Local Environment**: Mitigated via `PHANTOM_MODE=local|cloud` dual-mode architecture across SQLite/Postgres, NetworkX/Neo4j, Hardhat/Sepolia, and Demo/Supabase frontend.
2. **PaySim 6.3M Row Memory Pressure**: Mitigated via streaming chunked CSV processing (`chunksize=50000`) in `scripts/paysim_adapter.py`.
3. **PaySim Domain Gap (No Customers, Devices, IPs, Cycles)**: Mitigated by deterministic seeded enrichment (`SYNTHETIC_ENRICHMENT`) and explicit planted ground-truth rings (`INJECTED_RING`), kept strictly separated in `ground_truth.csv` and `evaluate.py`.
4. **Amount Scale Mismatch (PaySim vs INR ₹80K–₹99.9K)**: Mitigated via configurable profiles (`default` vs `paysim`) in `analytics/app/config.py`, documented in `docs/DECISIONS.md`.

## Order of Work

- **Phase 0**: Repo scaffolding, plan, decisions, CI/CD, dependency install (`make setup`).
- **Phase 1**: SQL migrations (18 tables, 8 functions, RLS), `seed.sql`, `paysim_adapter.py` on real 6.3M PaySim CSV, `seed_supabase.py`, `generate_demo_data.py`.
- **Phase 2**: Python analytics & risk engine, 14+ pytest tests, Phantom Ring = 94.0 CRITICAL, full 70K scoring run.
- **Phase 3**: Evaluation harness (`analytics/evaluation/evaluate.py`), `EVALUATION.md`, `evaluation_results.json`.
- **Phase 4**: Solidity `PhantomAuditRegistry.sol`, Hardhat tests, 100-record anchor + tamper detection E2E script.
- **Phase 5**: `sync_neo4j.py` with idempotent `MERGE`/`UNWIND` and NetworkX parity verification.
- **Phase 6**: FastAPI endpoints + Pydantic models + auth middleware + Supabase edge functions + API tests.
- **Phase 7**: All 15 React/TypeScript pages, Cytoscape explorer, Virtualized/paginated tables, vitest smoke tests, screenshots.
- **Phase 8**: `scripts/e2e_demo.py` and `make all` end-to-end validation.
- **Phase 9**: Final audit loop (up to 3 rounds), `docs/COMPLETION_MATRIX.md`, leftover checks.

