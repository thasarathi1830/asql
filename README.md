# PHANTOM — Identity & Transaction Network Intelligence System

> *"Uncover the hidden network behind every transaction."*

**PHANTOM** is a blockchain-backed identity and transaction network intelligence platform designed to uncover hidden relationships between digital identities, bank accounts, and financial transfers. Built with a zero-Docker managed cloud architecture (Vercel, Supabase, Neo4j Aura, FastAPI, Sepolia EVM) and a complete **local dual-mode** (`PHANTOM_MODE=local`) for offline development and evaluation.

---

## Quick Start (Local Mode in 5 Commands)

```bash
# 1. Install all Python, Frontend, and Blockchain dependencies
make setup

# 2. Stream & sample PaySim (6.3M rows -> ~70K sample + Operation Phantom Ring)
make data

# 3. Load processed data into local SQLite / PostgreSQL
make db

# 4. Run 8-factor explainable risk scoring & scientific evaluation
make analyze

# 5. Run full test suite & end-to-end verification
make test && make all
```

To launch interactive local services:
```bash
# Terminal 1: FastAPI Analytics Engine (http://localhost:8000/docs)
make api

# Terminal 2: React + Cytoscape.js Command Center (http://localhost:3000)
cd frontend && npm run dev
```

---

## Architecture

```
  Vercel / Browser (React 18 + TS + Cytoscape.js + Recharts)
          │
          ├──────────────────────────┬──────────────────────────┐
          ▼                          ▼                          ▼
   Supabase Cloud             Python FastAPI              EVM Blockchain
  • 18 PG Tables + RLS       • NetworkX Graph Engine     • PhantomAuditRegistry.sol
  • 8 PL/pgSQL Functions     • 8-Factor Risk Scoring     • Zero-PII SHA-256 Proofs
  • Edge Functions           • Mule & Structuring        • Hardhat (local) / Sepolia
          │
          ▼
   Neo4j Aura (Property Graph / NetworkX local fallback)
```

---

## Key Capabilities

- **Explainable 8-Factor Risk Scoring (`0–100`)**: Circular flows (`RULE_001`), rapid pass-through mule drains (`RULE_002`), structuring/smurfing (`RULE_003`), dormant account surges (`RULE_004`), shared device/IP clusters (`RULE_005`), structural centrality hubs (`RULE_006`), risky counterparties (`RULE_007`), and velocity spikes (`RULE_008`).
- **Pre-Seeded Case Study — Operation Phantom Ring**: `ACC-0001-9041` -> `ACC-0044-7721` -> `ACC-0078-3319` -> `ACC-0001-9041` (Rs.1,415,000 cycled in 4.25h, shared `DEV-PHANTOM-103`, score **94.0 CRITICAL**).
- **Zero-PII Cryptographic Auditability**: Canonical JSON + SHA-256 commitments anchored on `PhantomAuditRegistry.sol` with instant `VERIFIED` / `TAMPERED` verification.
- **PaySim Real-Dataset Integration**: Streaming adapter processes all 6,362,620 PaySim rows with 100% fraud retention while keeping real PaySim fraud, synthetic enrichment, and injected patterns strictly separated.

---

## Cloud Mode Setup

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for step-by-step deployment to Supabase, Neo4j Aura, Railway/Render, Vercel, and Ethereum Sepolia.

---

## Documentation Index

- [Architecture](docs/architecture.md)
- [Design Decisions](docs/DECISIONS.md)
- [PaySim Dataset & Provenance](docs/DATASET.md)
- [Evaluation Results](docs/EVALUATION.md)
- [Cloud Deployment Guide](docs/DEPLOYMENT.md)
- [Build Log](docs/BUILD_LOG.md)
- [Completion Matrix](docs/COMPLETION_MATRIX.md)

## License

MIT License
