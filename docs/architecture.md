# PHANTOM — System Architecture

## Overview

**PHANTOM** (*Identity & Transaction Network Intelligence System*) is a zero-Docker, managed-cloud hybrid relational-graph AML and financial crime intelligence platform with cryptographic tamper-evident auditability.

## Architecture Diagram

```
                                  ┌───────────────────────────────┐
                                  │      Vercel / Browser         │
                                  │   React 18 + TS + Tailwind    │
                                  │ Cytoscape.js + Recharts + UI  │
                                  └───────────────┬───────────────┘
                                                  │
                            ┌─────────────────────┴─────────────────────┐
                            │ HTTPS / Supabase SDK & Edge Functions     │
                            ▼                                           ▼
             ┌─────────────────────────────┐             ┌─────────────────────────────┐
             │       SUPABASE CLOUD        │             │   PYTHON RISK & ANALYTICS   │
             │                             │             │      MICROSERVICE           │
             │ • PostgreSQL 15+ (Source of │             │ • FastAPI / Pydantic v2     │
             │   Truth & Advanced SQL CTEs)│             │ • NetworkX Graph Analytics  │
             │ • Supabase Auth (JWT/RLS)   │◄───────────►│ • Explainable Risk Scoring  │
             │ • Supabase Storage (CSVs)   │  Internal   │ • Anomaly & Cluster Mining  │
             │ • Supabase Realtime (Alerts)│  API Key    │ • Structuring / Mule Engine │
             └──────────────┬──────────────┘             └──────────────┬──────────────┘
                            │                                           │
                            │ Idempotent Sync                           │ Cryptographic Hashes
                            ▼                                           ▼
             ┌─────────────────────────────┐             ┌─────────────────────────────┐
             │         NEO4J AURA          │             │     BLOCKCHAIN LAYER        │
             │   (NetworkX in local mode)  │             │   (Hardhat in local mode)   │
             │ • Customer / Account Nodes  │             │ • PhantomAuditRegistry.sol  │
             │ • Device / IP / Hash Nodes  │             │ • SHA-256 Canonical Hashes  │
             │ • Multi-Hop Cypher Traversal│             │ • Tamper-Evident Audit Proof│
             │ • Community Detection       │             │ • EVM-compatible Registry   │
             └─────────────────────────────┘             └─────────────────────────────┘
```

## Dual-Mode Design (`PHANTOM_MODE`)

| Subsystem | `PHANTOM_MODE=cloud` | `PHANTOM_MODE=local` |
|---|---|---|
| Operational DB | Supabase PostgreSQL 15+ (with RLS) | Local SQLite (`data/phantom_local.db`) or local Postgres |
| Graph Engine | Neo4j Aura + NetworkX | NetworkX `DiGraph` |
| Blockchain | Sepolia EVM Testnet | Local Hardhat EVM Node (`127.0.0.1:8545`) |
| Frontend Data | Supabase SDK + Edge Functions + FastAPI | `demoData.ts` generated from real PaySim processed data |

## Key Subsystems

1. **PostgreSQL 18-Table Schema & 8 PL/pgSQL Analytics Functions**: Bounded recursive CTE cycle detection, sliding-window velocity & structuring detection, rapid pass-through self-joins, dormant activation, counterparty metrics, and identity collision views.
2. **Python FastAPI Microservice**: Johnson elementary cycles (`simple_cycles`), Brandes betweenness centrality, PageRank, greedy modularity communities, Pandas mule & dormant engines, 8-factor additive risk scoring `[0, 100]`.
3. **Zero-PII EVM Audit Registry (`PhantomAuditRegistry.sol`)**: Deterministic canonical JSON serialization -> SHA-256 (`bytes32`) -> immutable on-chain commitment.
4. **React 18 + Cytoscape.js Command Center**: 15 intelligence pages supporting 2,000-node subgraph rendering, cycle highlighting, hardware collision edges, and interactive tamper testing.
