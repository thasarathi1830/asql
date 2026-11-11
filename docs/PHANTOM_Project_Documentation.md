# PHANTOM — Identity & Transaction Network Intelligence System
## Comprehensive Project Documentation

> **Tagline:** *"Uncover the hidden network behind every transaction."*

| Field | Detail |
|---|---|
| **Project Name** | PHANTOM |
| **Full Title** | Identity & Transaction Network Intelligence System |
| **Domain** | Financial Crime Detection, Anti-Money Laundering (AML), Network Intelligence |
| **License** | MIT |
| **Architecture** | Managed Cloud (Zero Docker / Zero Kubernetes) |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement & Motivation](#2-problem-statement--motivation)
3. [System Architecture](#3-system-architecture)
4. [Technology Stack](#4-technology-stack)
5. [Project Directory Structure](#5-project-directory-structure)
6. [Database Design (PostgreSQL / Supabase)](#6-database-design-postgresql--supabase)
7. [Advanced SQL Analytics](#7-advanced-sql-analytics)
8. [Row Level Security (RLS) & Access Control](#8-row-level-security-rls--access-control)
9. [Neo4j Graph Database Model](#9-neo4j-graph-database-model)
10. [Python Analytics & Risk Engine](#10-python-analytics--risk-engine)
11. [Explainable 8-Factor Risk Scoring](#11-explainable-8-factor-risk-scoring)
12. [Blockchain Tamper-Evident Verification](#12-blockchain-tamper-evident-verification)
13. [Frontend Application (React + TypeScript)](#13-frontend-application-react--typescript)
14. [REST API & Edge Functions](#14-rest-api--edge-functions)
15. [End-to-End Data Flow](#15-end-to-end-data-flow)
16. [Pre-Seeded Case Study: Operation Phantom Ring](#16-pre-seeded-case-study-operation-phantom-ring)
17. [CI/CD Pipeline](#17-cicd-pipeline)
18. [Cloud Deployment Guide](#18-cloud-deployment-guide)
19. [Local Development Setup](#19-local-development-setup)
20. [Verification Checklist](#20-verification-checklist)
21. [Development Roadmap](#21-development-roadmap)

---

## 1. Executive Summary

**PHANTOM** is a blockchain-backed identity and transaction network intelligence platform designed to uncover hidden relationships between seemingly unrelated digital identities, bank accounts, and financial transfers.

Traditional fraud prevention engines evaluate transactions in isolation against rule thresholds. In contrast, **PHANTOM** constructs and interrogates the **entire relationship network** to identify:

- **Circular money flows** (A → B → C → A)
- **Rapid pass-through mule conduits** (inflows drained within minutes)
- **Transaction structuring (smurfing)** just beneath regulatory limits
- **Hardware collisions** (multiple accounts sharing mobile device fingerprints)
- **High-degree intermediary hubs** (elevated betweenness centrality)
- **Cryptographic record tampering** using tamper-evident EVM blockchain proofs

> **Architecture Principle:** PHANTOM uses modern managed cloud services (Vercel, Supabase, Neo4j Aura, Railway/Render) and **does not require Docker or Kubernetes**.

---

## 2. Problem Statement & Motivation

### The Gap in Traditional AML Systems

| Traditional Approach | PHANTOM Approach |
|---|---|
| Rule-based threshold checks on isolated transactions | Network-wide relationship graph analysis |
| Post-hoc batch processing | Near real-time alerting with Supabase Realtime |
| Opaque, black-box risk scoring | Fully explainable, additive 8-factor risk scores |
| No tamper-evidence for audit trails | Blockchain-backed SHA-256 cryptographic proof |
| Manual investigation tools | Interactive Cytoscape.js graph exploration with node inspection |

### Key Challenges Addressed

1. **Money Laundering Detection**: Circular flows where funds cycle through intermediaries and return to origin.
2. **Mule Account Identification**: Accounts that receive and immediately drain funds, acting as pass-through conduits.
3. **Smurfing / Structuring**: Breaking large transactions into smaller amounts just below reporting thresholds.
4. **Identity Clustering**: Multiple seemingly independent accounts sharing hardware devices, IP addresses, or phone numbers.
5. **Audit Integrity**: Ensuring investigation records cannot be retroactively altered without detection.

---

## 3. System Architecture

### High-Level Architecture Diagram

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
             │ • PostgreSQL 15+ (Source of │             │ • FastAPI / Pydantic        │
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
             │                             │             │                             │
             │ • Customer / Account Nodes  │             │ • PhantomAuditRegistry.sol  │
             │ • Device / IP / Hash Nodes  │             │ • SHA-256 Canonical Hashes  │
             │ • Multi-Hop Cypher Traversal│             │ • Tamper-Evident Audit Proof│
             │ • Community Detection       │             │ • EVM-compatible Registry   │
             └─────────────────────────────┘             └─────────────────────────────┘
```

### Component Responsibilities

| Component | Role |
|---|---|
| **Vercel (Frontend)** | Hosts the React 18 SPA with Cytoscape.js for interactive network graph visualization |
| **Supabase Cloud** | PostgreSQL database (source of truth), Row Level Security (RLS), authentication, file storage, and real-time event subscriptions |
| **Python Analytics Microservice** | FastAPI-powered risk scoring engine using NetworkX for graph algorithms and Pandas for data analysis |
| **Neo4j Aura** | Property graph database for multi-hop Cypher traversal, community detection, and shortest path queries |
| **EVM Blockchain (Sepolia)** | Tamper-evident cryptographic hash registry via the PhantomAuditRegistry.sol Solidity smart contract |

---

## 4. Technology Stack

### Frontend

| Technology | Purpose |
|---|---|
| React 18 | UI component library |
| TypeScript | Static type safety |
| Vite | Build tool & dev server |
| Tailwind CSS | Utility-first CSS framework |
| Cytoscape.js | Interactive network graph rendering |
| Recharts | Data visualization charts (Area, Pie, Bar) |
| Lucide Icons | Icon library |
| React Router v6 | Client-side routing |
| TanStack Query | Server state management |

### Backend & Database

| Technology | Purpose |
|---|---|
| Supabase Cloud | PostgreSQL 15+, Auth, RLS, Storage, Realtime, Edge Functions |
| Python 3.11+ | Analytics microservice runtime |
| FastAPI | REST API framework with Pydantic validation |
| NetworkX | Graph algorithms (cycles, centrality, shortest path, community detection) |
| Pandas | Data manipulation and sliding window analysis |
| NumPy | Numerical computations |
| scikit-learn | Machine learning utilities |

### Graph & Blockchain

| Technology | Purpose |
|---|---|
| Neo4j Aura | Hosted graph database with Cypher query language |
| Solidity 0.8.20 | Smart contract language for PhantomAuditRegistry.sol |
| Hardhat | Ethereum development environment for testing & deployment |
| Ethers.js / Web3 | Blockchain interaction from frontend and backend |
| EVM Testnet (Sepolia) | Public testnet for contract deployment |

### DevOps & CI/CD

| Technology | Purpose |
|---|---|
| GitHub Actions | Continuous Integration pipeline |
| Vercel | Frontend hosting & automatic deployments |
| Railway / Render | Python analytics microservice hosting |

---

## 5. Project Directory Structure

```
phantom/
├── frontend/                          # React + TypeScript SPA
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/                # Sidebar, Topbar, AppShell
│   │   │   ├── network/               # Cytoscape.js canvas, inspector, controls
│   │   │   └── ui/                    # RiskBadge, StatCard, SearchBar, Modal
│   │   ├── pages/                     # 15 Full feature views
│   │   │   ├── Landing.tsx            # High-impact intelligence landing page
│   │   │   ├── Login.tsx              # Supabase auth / Demo login
│   │   │   ├── Signup.tsx             # User registration
│   │   │   ├── Dashboard.tsx          # Intelligence Command Center
│   │   │   ├── NetworkExplorer.tsx    # Cytoscape interactive graph
│   │   │   ├── Transactions.tsx       # Transaction explorer & verification
│   │   │   ├── Identities.tsx         # Identity cluster explorer
│   │   │   ├── RiskIntelligence.tsx   # Risk factor analytics
│   │   │   ├── Alerts.tsx             # Real-time alert triage
│   │   │   ├── Investigations.tsx     # Investigation workspace
│   │   │   ├── InvestigationDetail.tsx# Case file, notes, timeline, export
│   │   │   ├── BlockchainVerification.tsx  # Tamper verification tool
│   │   │   ├── AuditLogs.tsx          # Immutable audit trail
│   │   │   ├── DataImport.tsx         # CSV ingestion pipeline
│   │   │   └── Settings.tsx           # System configuration & health
│   │   ├── lib/
│   │   │   ├── supabase.ts            # Supabase client initialization
│   │   │   ├── demoData.ts            # Comprehensive demo/mock data (17KB)
│   │   │   └── blockchainVerifier.ts  # Frontend blockchain verification
│   │   ├── types/                     # TypeScript interfaces
│   │   ├── App.tsx                    # Route configuration
│   │   ├── main.tsx                   # Application entry point
│   │   └── index.css                  # Global styles
│   ├── package.json
│   ├── vite.config.ts
│   └── .env.example
│
├── analytics/                         # Python FastAPI Microservice
│   ├── app/
│   │   ├── main.py                    # FastAPI entrypoint with CORS
│   │   ├── risk_engine.py             # 8-Factor Explainable Risk Scoring (200 LOC)
│   │   ├── graph_analysis.py          # NetworkX cycle & centrality (171 LOC)
│   │   ├── anomaly_detection.py       # Mule pass-through & dormant activation (104 LOC)
│   │   ├── network_analysis.py        # Hub & community detection wrapper
│   │   ├── structuring_engine.py      # Smurfing detection engine (85 LOC)
│   │   ├── blockchain.py              # Canonical JSON hasher & verifier
│   │   ├── config.py                  # Environment configuration
│   │   └── routers/
│   │       ├── analytics.py           # Analytics API router
│   │       └── health.py              # Health check router
│   ├── tests/                         # 14 Pytest unit & integration tests
│   ├── requirements.txt               # Python dependencies
│   └── .env.example
│
├── supabase/                          # Supabase Configuration & Migrations
│   ├── migrations/
│   │   ├── 20261006000001_initial_schema.sql        # 18 tables (12,664 bytes)
│   │   ├── 20261006000002_advanced_analytics.sql    # 8 PL/pgSQL functions (17,164 bytes)
│   │   └── 20261006000003_rls_policies.sql          # RLS across all 18 tables (8,125 bytes)
│   ├── functions/
│   │   ├── calculate-risk/index.ts
│   │   ├── verify-blockchain/index.ts
│   │   └── health/index.ts
│   ├── seed.sql                       # Demo data seed (10,878 bytes)
│   ├── tests/
│   └── config.toml
│
├── blockchain/                        # Solidity Smart Contract
│   ├── contracts/
│   │   └── PhantomAuditRegistry.sol   # Tamper-evident EVM contract (162 LOC)
│   ├── scripts/
│   │   └── deploy.ts                  # Hardhat deployment script
│   ├── test/
│   │   └── PhantomAuditRegistry.test.ts
│   ├── hardhat.config.ts
│   └── package.json
│
├── database/
│   └── schema.sql                     # Standalone schema reference
│
├── scripts/                           # Utility Scripts
│   ├── generate_demo_data.py          # Generates 1,000 customers, 1,500 accounts, 20K tx
│   ├── seed_supabase.py               # Loads seed data into Supabase PostgreSQL
│   ├── sync_neo4j.py                  # Syncs nodes and edges to Neo4j Aura
│   └── run_risk_analysis.py           # Risk analysis runner
│
├── data/                              # Data directory
├── .github/
│   └── workflows/
│       └── ci.yml                     # CI: Lint, Test, Typecheck, Build
│
├── .env.example                       # Root environment variables template
├── architecture.md                    # Detailed architecture documentation
├── README.md                          # Project README
└── .gitignore
```

---

## 6. Database Design (PostgreSQL / Supabase)

### Overview

The operational source of truth is **PostgreSQL 15+** hosted on Supabase, featuring:
- UUID primary keys via `uuid-ossp` extension
- `pgcrypto` extension for cryptographic operations
- Strict foreign key constraints with `ON DELETE CASCADE/RESTRICT/SET NULL`
- B-Tree and GIN indexes for enterprise query performance
- Row Level Security (RLS) enabled on all 18 tables
- CHECK constraints for enum-like fields

### Entity-Relationship Diagram

```
PROFILES ──────┬──── INVESTIGATIONS ───── INVESTIGATION_ENTITIES
               │             │
               │    INVESTIGATION_NOTES
               │
               └──── AUDIT_LOGS

CUSTOMERS ─────┬──── ACCOUNTS ────────┬──── TRANSACTIONS ──── BLOCKCHAIN_RECORDS
               │          │           │
   IDENTITY_ATTRIBUTES    │    ACCOUNT_RELATIONSHIPS
                          │
                     RISK_SCORES ──── RISK_FACTORS
                          │
                        ALERTS
```

### Complete Table Specifications (18 Tables)

#### Table 1: `profiles`
| Column | Type | Constraints |
|---|---|---|
| `id` | UUID (PK) | References `auth.users(id) ON DELETE CASCADE` |
| `full_name` | TEXT | NOT NULL |
| `email` | TEXT | UNIQUE, NOT NULL |
| `role` | TEXT | CHECK IN ('ADMIN', 'INVESTIGATOR', 'ANALYST', 'VIEWER'), DEFAULT 'INVESTIGATOR' |
| `badge_number` | TEXT | |
| `avatar_url` | TEXT | |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() |

#### Table 2: `customers`
| Column | Type | Constraints |
|---|---|---|
| `id` | UUID (PK) | DEFAULT uuid_generate_v4() |
| `customer_reference` | VARCHAR(64) | UNIQUE, NOT NULL |
| `name` | VARCHAR(255) | NOT NULL |
| `email_masked` | VARCHAR(255) | NOT NULL |
| `phone_masked` | VARCHAR(64) | NOT NULL |
| `country` | CHAR(2) | NOT NULL, DEFAULT 'IN' |
| `identity_hash` | VARCHAR(64) | NOT NULL |
| `risk_score` | NUMERIC(5,2) | CHECK (0 <= score <= 100), DEFAULT 0.00 |
| `risk_level` | VARCHAR(20) | CHECK IN ('LOW','MEDIUM','HIGH','CRITICAL'), DEFAULT 'LOW' |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() |

#### Table 3: `accounts`
| Column | Type | Constraints |
|---|---|---|
| `id` | UUID (PK) | DEFAULT uuid_generate_v4() |
| `account_number_masked` | VARCHAR(64) | UNIQUE, NOT NULL |
| `customer_id` | UUID (FK) | References customers(id) ON DELETE RESTRICT |
| `account_type` | VARCHAR(32) | CHECK IN ('SAVINGS','CURRENT','ESCROW','CORPORATE','CRYPTO_WALLET') |
| `bank_code` | VARCHAR(32) | NOT NULL, DEFAULT 'HDFC' |
| `country` | CHAR(2) | NOT NULL, DEFAULT 'IN' |
| `status` | VARCHAR(20) | CHECK IN ('ACTIVE','FROZEN','RESTRICTED','CLOSED') |
| `risk_score` | NUMERIC(5,2) | CHECK (0 <= score <= 100), DEFAULT 0.00 |
| `risk_level` | VARCHAR(20) | CHECK IN ('LOW','MEDIUM','HIGH','CRITICAL') |
| `is_dormant` | BOOLEAN | NOT NULL, DEFAULT FALSE |
| `last_activity_at` | TIMESTAMPTZ | |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() |

#### Table 4: `transactions`
| Column | Type | Constraints |
|---|---|---|
| `id` | UUID (PK) | DEFAULT uuid_generate_v4() |
| `transaction_reference` | VARCHAR(64) | UNIQUE, NOT NULL |
| `sender_account_id` | UUID (FK) | References accounts(id) ON DELETE RESTRICT |
| `receiver_account_id` | UUID (FK) | References accounts(id) ON DELETE RESTRICT |
| `amount` | NUMERIC(15,2) | NOT NULL, CHECK (amount > 0) |
| `currency` | VARCHAR(10) | NOT NULL, DEFAULT 'INR' |
| `transaction_type` | VARCHAR(32) | CHECK IN ('WIRE','UPI','NEFT','RTGS','INTERNAL_TRANSFER','ATM') |
| `transaction_timestamp` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() |
| `location` | VARCHAR(128) | |
| `device_id` | VARCHAR(64) | |
| `ip_hash` | VARCHAR(64) | |
| `status` | VARCHAR(20) | CHECK IN ('PENDING','COMPLETED','FLAGGED','BLOCKED') |
| `blockchain_hash` | VARCHAR(66) | |
| `blockchain_tx_id` | VARCHAR(66) | |
| `verification_status` | VARCHAR(20) | CHECK IN ('PENDING','VERIFIED','TAMPERED'), DEFAULT 'VERIFIED' |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() |

#### Table 5: `identity_attributes`
| Column | Type | Constraints |
|---|---|---|
| `id` | UUID (PK) | DEFAULT uuid_generate_v4() |
| `customer_id` | UUID (FK) | References customers(id) ON DELETE CASCADE |
| `attribute_type` | VARCHAR(32) | CHECK IN ('EMAIL','PHONE','DEVICE','IP','ADDRESS','DOCUMENT','BANK_ACCOUNT') |
| `attribute_hash` | VARCHAR(64) | NOT NULL |
| `attribute_value_masked` | VARCHAR(255) | NOT NULL |
| `confidence` | NUMERIC(3,2) | CHECK (0 <= confidence <= 1.00), DEFAULT 1.00 |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() |

#### Table 6: `account_relationships`
| Column | Type | Constraints |
|---|---|---|
| `id` | UUID (PK) | DEFAULT uuid_generate_v4() |
| `source_account_id` | UUID (FK) | References accounts(id) ON DELETE CASCADE |
| `target_account_id` | UUID (FK) | References accounts(id) ON DELETE CASCADE |
| `relationship_type` | VARCHAR(64) | CHECK IN ('SHARED_DEVICE','SHARED_IP','CIRCULAR_FLOW','RAPID_PASS_THROUGH','COUNTERPARTY','SAME_CUSTOMER') |
| `confidence` | NUMERIC(3,2) | DEFAULT 0.85 |
| `evidence_count` | INT | DEFAULT 1 |
| `metadata` | JSONB | DEFAULT '{}' |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() |
| **UNIQUE** | | (source_account_id, target_account_id, relationship_type) |

#### Table 7: `risk_scores`
| Column | Type | Constraints |
|---|---|---|
| `id` | UUID (PK) | DEFAULT uuid_generate_v4() |
| `entity_type` | VARCHAR(32) | CHECK IN ('ACCOUNT','CUSTOMER') |
| `entity_id` | UUID | NOT NULL |
| `score` | NUMERIC(5,2) | CHECK (0 <= score <= 100) |
| `risk_level` | VARCHAR(20) | CHECK IN ('LOW','MEDIUM','HIGH','CRITICAL') |
| `reasons` | JSONB | DEFAULT '[]' |
| `calculated_at` | TIMESTAMPTZ | DEFAULT NOW() |

#### Table 8: `risk_factors`
| Column | Type | Constraints |
|---|---|---|
| `id` | UUID (PK) | DEFAULT uuid_generate_v4() |
| `risk_score_id` | UUID (FK) | References risk_scores(id) ON DELETE CASCADE |
| `rule_id` | VARCHAR(32) | NOT NULL |
| `rule_name` | VARCHAR(128) | NOT NULL |
| `severity` | VARCHAR(20) | CHECK IN ('LOW','MEDIUM','HIGH','CRITICAL') |
| `weight` | NUMERIC(5,2) | NOT NULL |
| `evidence` | JSONB | DEFAULT '{}' |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() |

#### Table 9: `fraud_rules`
| Column | Type | Constraints |
|---|---|---|
| `id` | UUID (PK) | DEFAULT uuid_generate_v4() |
| `rule_id` | VARCHAR(32) | UNIQUE, NOT NULL |
| `name` | VARCHAR(128) | NOT NULL |
| `description` | TEXT | NOT NULL |
| `default_weight` | NUMERIC(5,2) | NOT NULL |
| `severity` | VARCHAR(20) | CHECK IN ('LOW','MEDIUM','HIGH','CRITICAL') |
| `is_active` | BOOLEAN | DEFAULT TRUE |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() |

#### Table 10: `alerts`
| Column | Type | Constraints |
|---|---|---|
| `id` | UUID (PK) | DEFAULT uuid_generate_v4() |
| `entity_type` | VARCHAR(32) | CHECK IN ('ACCOUNT','CUSTOMER','TRANSACTION','NETWORK') |
| `entity_id` | UUID | NOT NULL |
| `alert_type` | VARCHAR(64) | NOT NULL |
| `severity` | VARCHAR(20) | CHECK IN ('LOW','MEDIUM','HIGH','CRITICAL') |
| `title` | VARCHAR(255) | NOT NULL |
| `description` | TEXT | NOT NULL |
| `evidence` | JSONB | DEFAULT '{}' |
| `status` | VARCHAR(20) | CHECK IN ('NEW','IN_REVIEW','ESCALATED','DISMISSED'), DEFAULT 'NEW' |
| `assigned_to` | UUID (FK) | References profiles(id) ON DELETE SET NULL |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() |

#### Table 11: `investigations`
| Column | Type | Constraints |
|---|---|---|
| `id` | UUID (PK) | DEFAULT uuid_generate_v4() |
| `investigator_id` | UUID (FK) | References profiles(id) ON DELETE SET NULL |
| `case_number` | VARCHAR(64) | UNIQUE, NOT NULL |
| `title` | VARCHAR(255) | NOT NULL |
| `description` | TEXT | NOT NULL |
| `priority` | VARCHAR(20) | CHECK IN ('LOW','MEDIUM','HIGH','URGENT'), DEFAULT 'MEDIUM' |
| `status` | VARCHAR(20) | CHECK IN ('OPEN','IN_PROGRESS','PENDING_REVIEW','CLOSED'), DEFAULT 'OPEN' |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() |

#### Table 12: `investigation_entities`
| Column | Type | Constraints |
|---|---|---|
| `id` | UUID (PK) | DEFAULT uuid_generate_v4() |
| `investigation_id` | UUID (FK) | References investigations(id) ON DELETE CASCADE |
| `entity_type` | VARCHAR(32) | CHECK IN ('ACCOUNT','CUSTOMER','TRANSACTION','DEVICE','IP') |
| `entity_id` | UUID | NOT NULL |
| `notes` | TEXT | |
| `added_at` | TIMESTAMPTZ | DEFAULT NOW() |
| **UNIQUE** | | (investigation_id, entity_type, entity_id) |

#### Table 13: `investigation_notes`
| Column | Type | Constraints |
|---|---|---|
| `id` | UUID (PK) | DEFAULT uuid_generate_v4() |
| `investigation_id` | UUID (FK) | References investigations(id) ON DELETE CASCADE |
| `author_id` | UUID (FK) | References profiles(id) ON DELETE SET NULL |
| `content` | TEXT | NOT NULL |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() |

#### Table 14: `blockchain_records`
| Column | Type | Constraints |
|---|---|---|
| `id` | UUID (PK) | DEFAULT uuid_generate_v4() |
| `record_hash` | VARCHAR(66) | UNIQUE, NOT NULL |
| `record_type` | VARCHAR(32) | CHECK IN ('TRANSACTION','IDENTITY','INVESTIGATION') |
| `canonical_payload` | JSONB | NOT NULL |
| `blockchain_tx_id` | VARCHAR(66) | NOT NULL |
| `block_number` | BIGINT | DEFAULT 0 |
| `submitter_address` | VARCHAR(42) | DEFAULT '0x9965507D...' |
| `status` | VARCHAR(20) | CHECK IN ('VERIFIED','TAMPERED'), DEFAULT 'VERIFIED' |
| `verified_at` | TIMESTAMPTZ | DEFAULT NOW() |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() |

#### Table 15: `audit_logs`
| Column | Type | Constraints |
|---|---|---|
| `id` | UUID (PK) | DEFAULT uuid_generate_v4() |
| `user_id` | UUID (FK) | References profiles(id) ON DELETE SET NULL |
| `action` | VARCHAR(64) | NOT NULL |
| `entity_type` | VARCHAR(32) | NOT NULL |
| `entity_id` | UUID | NOT NULL |
| `previous_hash` | VARCHAR(66) | |
| `current_hash` | VARCHAR(66) | |
| `blockchain_tx_id` | VARCHAR(66) | |
| `details` | JSONB | DEFAULT '{}' |
| `timestamp` | TIMESTAMPTZ | DEFAULT NOW() |

#### Table 16: `network_clusters`
| Column | Type | Constraints |
|---|---|---|
| `id` | UUID (PK) | DEFAULT uuid_generate_v4() |
| `cluster_name` | VARCHAR(128) | NOT NULL |
| `entity_ids` | JSONB | DEFAULT '[]' |
| `risk_score` | NUMERIC(5,2) | DEFAULT 50.00 |
| `description` | TEXT | NOT NULL |
| `detected_at` | TIMESTAMPTZ | DEFAULT NOW() |

#### Table 17: `ingestion_jobs`
| Column | Type | Constraints |
|---|---|---|
| `id` | UUID (PK) | DEFAULT uuid_generate_v4() |
| `filename` | VARCHAR(255) | NOT NULL |
| `total_records` | INT | DEFAULT 0 |
| `processed_records` | INT | DEFAULT 0 |
| `status` | VARCHAR(20) | CHECK IN ('PENDING','PROCESSING','COMPLETED','FAILED'), DEFAULT 'PENDING' |
| `error_log` | TEXT | |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() |

#### Table 18: `system_events`
| Column | Type | Constraints |
|---|---|---|
| `id` | UUID (PK) | DEFAULT uuid_generate_v4() |
| `event_type` | VARCHAR(64) | NOT NULL |
| `severity` | VARCHAR(20) | DEFAULT 'INFO' |
| `payload` | JSONB | DEFAULT '{}' |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() |

### Database Indexes (20 Performance Indexes)

```sql
-- Customer & Account lookup
idx_customers_risk_level        ON customers(risk_level)
idx_customers_identity_hash     ON customers(identity_hash)
idx_accounts_customer_id        ON accounts(customer_id)
idx_accounts_risk_level         ON accounts(risk_level)
idx_accounts_status             ON accounts(status)
idx_accounts_is_dormant         ON accounts(is_dormant)

-- Transaction performance
idx_transactions_sender         ON transactions(sender_account_id)
idx_transactions_receiver       ON transactions(receiver_account_id)
idx_transactions_timestamp      ON transactions(transaction_timestamp DESC)
idx_transactions_amount         ON transactions(amount)
idx_transactions_blockchain_hash ON transactions(blockchain_hash)

-- Identity & relationship joins
idx_identity_attrs_hash         ON identity_attributes(attribute_hash)
idx_identity_attrs_customer     ON identity_attributes(customer_id)
idx_account_rel_source          ON account_relationships(source_account_id)
idx_account_rel_target          ON account_relationships(target_account_id)

-- Alert & investigation triage
idx_alerts_severity             ON alerts(severity)
idx_alerts_status               ON alerts(status)
idx_investigations_status       ON investigations(status)

-- Blockchain verification
idx_blockchain_records_hash     ON blockchain_records(record_hash)
```

---

## 7. Advanced SQL Analytics

PHANTOM implements **8 advanced PL/pgSQL functions** and **1 view** using PostgreSQL's most powerful features: Recursive CTEs, Window Functions (LAG, LEAD, SUM OVER, COUNT OVER, AVG OVER, MIN OVER), and self-joins.

### Function A: `find_transaction_paths()`
- **Purpose**: Multi-hop transaction path discovery using Recursive CTE
- **Parameters**: `p_start_account_id` (UUID), `p_max_depth` (INT, default 4)
- **Algorithm**: BFS-style recursive expansion following transaction chains, with cycle prevention via `NOT (receiver = ANY(path_nodes))` and chronological ordering
- **Returns**: Source, destination, full path array, depth, cumulative amount, transaction IDs

### Function B: `detect_transaction_cycles()`
- **Purpose**: Circular money flow detection (A -> B -> C -> A)
- **Parameters**: `p_lookback_days` (INT, default 30), `p_min_amount` (NUMERIC, default 50,000)
- **Algorithm**: Recursive CTE that expands paths and closes when `current_node = origin`, constrained to 72-hour windows and 5-hop maximum depth
- **Returns**: Cycle signature, length, accounts involved, total cycled volume, time window

### Function C: `calculate_transaction_velocity()`
- **Purpose**: Transaction velocity & burst anomaly detection using Window Functions
- **Parameters**: `p_account_id` (UUID), `p_window_hours` (INT, default 24)
- **Window Functions Used**:
  - `LAG()` — previous transaction amount and timestamp
  - `SUM() OVER (RANGE)` — rolling sum within time window
  - `COUNT() OVER (RANGE)` — rolling count within time window
  - `AVG() OVER (RANGE)` — rolling average within time window
- **Returns**: Per-transaction metrics with velocity spike flags

### Function D: `detect_structuring()`
- **Purpose**: Smurfing pattern detection (transactions below 1L threshold)
- **Parameters**: `p_threshold_min` (default 80,000), `p_threshold_max` (default 99,999), `p_window_hours` (24), `p_min_tx_count` (3)
- **Algorithm**: Window function aggregation within sliding time windows, filtering for accounts with >=3 transactions in the structuring band
- **Returns**: Flagged accounts with suspicious transaction counts and amounts

### Function E: `detect_rapid_pass_through()`
- **Purpose**: Mule account detection via rapid inflow -> outflow matching
- **Parameters**: `p_max_delay_hours` (INT, default 2), `p_retain_ratio_max` (NUMERIC, default 0.10)
- **Algorithm**: Self-join on transactions table matching inflows to subsequent outflows within time window where retained ratio <= 10%
- **Returns**: Mule account ID, inbound/outbound details, delay in minutes, retained ratio

### Function F: `detect_dormant_activation()`
- **Purpose**: Dormant account burst activation detection
- **Parameters**: `p_dormant_days` (INT, default 60), `p_min_burst_amount` (NUMERIC, default 1,00,000)
- **Window Function**: `LAG(transaction_timestamp)` to compute gap between consecutive transactions
- **Returns**: Accounts with >60-day gaps followed by high-value bursts

### Function G: `calculate_counterparty_metrics()`
- **Purpose**: In/out volume analysis and counterparty frequency metrics
- **Parameters**: `p_account_id` (UUID)
- **Returns**: Total sent/received, counts, unique counterparties, net flow, in/out ratio

### View H: `view_shared_identity_clusters`
- **Purpose**: Identity attribute collision detection across customers
- **Algorithm**: Self-join on `identity_attributes` by `attribute_hash` and `attribute_type` with `customer_a < customer_b` deduplication
- **Returns**: Linked customer pairs sharing devices, IPs, phones, or emails

---

## 8. Row Level Security (RLS) & Access Control

### RLS Enabled Tables
All **18 tables** have RLS enabled via `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`.

### Role Hierarchy

| Role | Capabilities |
|---|---|
| **ADMIN** | Full read/write on all tables, user management |
| **INVESTIGATOR** | Read all data, create/update investigations and alerts, add notes |
| **ANALYST** | Read all data, view audit logs |
| **VIEWER** | Read-only access to operational data |

### Key Policies

| Policy | Table | Access |
|---|---|---|
| Authenticated users can read | customers, accounts, transactions, identity_attributes, account_relationships, risk_scores, risk_factors, fraud_rules, blockchain_records, network_clusters | SELECT for all authenticated |
| Investigators & Admins can update | alerts | UPDATE with role check |
| Investigators & Admins can create | investigations | INSERT with role check |
| Assigned investigators can update | investigations | UPDATE with ownership + role check |
| Investigators & Admins can manage | investigation_entities, investigation_notes | ALL / INSERT with role + author check |
| Auditors can read | audit_logs | SELECT for ADMIN, INVESTIGATOR, ANALYST |
| System insert | audit_logs | INSERT for all authenticated (immutable) |

### Auto-Profile Trigger
A PostgreSQL trigger `on_auth_user_created` automatically creates a `profiles` row when a new user signs up via Supabase Auth, extracting `full_name`, `email`, and `role` from the auth metadata.

---

## 9. Neo4j Graph Database Model

### Node Types

| Label | Properties |
|---|---|
| `:Customer` | `id`, `name`, `customer_reference`, `risk_level` |
| `:Account` | `id`, `account_number_masked`, `risk_score`, `bank_code` |
| `:Device` | `device_id` |
| `:IP` | `ip_hash` |
| `:Email` | `email_hash` |
| `:Phone` | `phone_hash` |
| `:Transaction` | `id`, `reference`, `amount`, `timestamp` |

### Relationship Types (Edges)

| Relationship | Pattern | Properties |
|---|---|---|
| `OWNS` | `(Customer)->(Account)` | - |
| `TRANSFERRED` | `(Account)->(Account)` | `amount`, `tx_id`, `timestamp` |
| `USES` | `(Customer)->(Device)` | - |
| `CONNECTS_FROM` | `(Customer)->(IP)` | - |
| `HAS_EMAIL` | `(Customer)->(Email)` | - |
| `HAS_PHONE` | `(Customer)->(Phone)` | - |
| `LINKED_TO` | `(Account)->(Account)` | `reason`, `weight` |

### Sync Process
The `scripts/sync_neo4j.py` script performs idempotent synchronization from PostgreSQL to Neo4j Aura, projecting customers, accounts, transactions, and identity attributes into the graph.

---

## 10. Python Analytics & Risk Engine

### Module Architecture

| Module | File | Lines | Purpose |
|---|---|---|---|
| **FastAPI App** | `main.py` | 28 | Application entry point with CORS middleware |
| **Risk Engine** | `risk_engine.py` | 200 | 8-factor explainable risk scoring with `RiskScoringEngine` class |
| **Graph Analysis** | `graph_analysis.py` | 171 | `TransactionGraphEngine` class using NetworkX for cycles, centrality, paths, communities |
| **Anomaly Detection** | `anomaly_detection.py` | 104 | `AnomalyEngine` class for mule detection and dormant activation |
| **Structuring Engine** | `structuring_engine.py` | 85 | `StructuringEngine` class for smurfing pattern detection |
| **Blockchain Module** | `blockchain.py` | ~70 | Canonical JSON serialization and SHA-256 hash computation |
| **Network Analysis** | `network_analysis.py` | ~35 | Hub & community detection wrapper |
| **Config** | `config.py` | ~30 | Environment variable management |

### Graph Analysis Engine (`TransactionGraphEngine`)

The `TransactionGraphEngine` class wraps NetworkX's `DiGraph` and provides:

1. **`load_transactions()`** — Builds a directed weighted graph from transaction data. Aggregates multiple transactions between the same pair into edge weight sums.

2. **`detect_cycles(max_length=5)`** — Uses `nx.simple_cycles()` to find all elementary cycles up to the specified length. Calculates total cycled volume and risk score boost.

3. **`calculate_centralities()`** — Computes for every node:
   - Betweenness Centrality
   - Degree Centrality
   - In-Degree / Out-Degree
   - PageRank (weighted)
   - Hub classification (betweenness > 0.40 or degree >= 10)

4. **`find_shortest_path(source, target)`** — Uses `nx.shortest_path()` with volume computation along the path.

5. **`get_neighbors_subgraph(node_id, depth=1)`** — BFS-based ego subgraph extraction for Cytoscape.js visualization.

6. **`detect_communities()`** — Uses `greedy_modularity_communities()` for community detection, flagging suspicious clusters (>=3 members, volume >1L).

### Anomaly Detection Engine (`AnomalyEngine`)

1. **`detect_rapid_pass_through()`** — Identifies mule accounts by matching inflows to outflows within a 2-hour window where >=85% of funds are forwarded (retained ratio <= 10%).

2. **`detect_dormant_activation()`** — Uses Pandas to compute inter-transaction gaps per account. Flags accounts dormant for >60 days that suddenly execute transfers >= 1,00,000.

### Structuring Engine (`StructuringEngine`)

1. **`detect_structuring_patterns()`** — Sliding window analysis over transactions in the 80K-99.9K band. Flags accounts with >=3 transactions within any 24-hour window.

2. **`analyze_repeated_counterparties()`** — Identifies unusually tight and frequent counterparty corridors (>=5 transactions between same pair).

### Dependencies

```
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.5.0
networkx>=3.2
pandas>=2.1.0
numpy>=1.26.0
scikit-learn>=1.3.0
httpx>=0.25.0
python-dotenv>=1.0.0
pytest>=7.4.0
```

---

## 11. Explainable 8-Factor Risk Scoring

PHANTOM avoids opaque black-box models. Every risk score is calculated transparently from **0 to 100** with auditable factor attributions.

### Scoring Formula

```
Risk Score = min(100, Sum of all Factor Weights)
```

### Risk Level Classification

| Score Range | Level | Color |
|---|---|---|
| 0 - 29 | LOW | Green |
| 30 - 59 | MEDIUM | Amber |
| 60 - 79 | HIGH | Orange |
| 80 - 100 | CRITICAL | Red |

### Complete Rule Catalog

| Rule Code | Rule Name | Max Points | Detection Mechanism | Evidence |
|---|---|---|---|---|
| **RULE_001** | Circular Money Flow | 25 pts | Johnson's Elementary Cycles algorithm (NetworkX `simple_cycles`) + PostgreSQL Recursive CTEs | Cycle count, cycle paths |
| **RULE_002** | Rapid Pass-Through / Mule | 20 pts | Inflows drained >90% within 120 minutes with <10% retained | Mule events, delay minutes, retained ratio |
| **RULE_003** | Transaction Structuring (Smurfing) | 20 pts | Clusters of transfers in 80K-99.9K range within 24h windows | Structured amount, tx count |
| **RULE_004** | Dormant Account Surge | 15 pts | >60 days dormancy followed by sudden high-value burst transfers | Dormant days, burst amount |
| **RULE_005** | Shared Identity Cluster | 15 pts | Hardware device fingerprint / IP address collisions across accounts | Shared device/IP count |
| **RULE_006** | High Network Centrality | 15 pts | Betweenness centrality >0.40 or degree >=10 (structural intermediary hub) | Betweenness value, hub flag |
| **RULE_007** | Suspicious Counterparty Association | 15 pts | Direct capital transfers to/from previously flagged entities | Risky counterparty count |
| **RULE_008** | Velocity Anomaly | 10 pts | Transaction frequency spiking >400% over 30-day rolling baseline | Spike count |

### Scoring Implementation Details

- Points are **additive** — each triggered rule contributes its weight
- Some rules use **scaled scoring** (e.g., RULE_001: 12.5 pts per cycle, max 25)
- Final score is **capped at 100**
- Every factor includes a **human-readable explanation string**
- Full **evidence payload** (JSONB) is stored with each factor for audit

---

## 12. Blockchain Tamper-Evident Verification

### Smart Contract: `PhantomAuditRegistry.sol`

**Solidity version**: 0.8.20
**Deployed on**: EVM-compatible testnet (Sepolia)

#### Zero PII On-Chain Policy
No customer names, phone numbers, account numbers, or financial values ever touch the public blockchain. Only cryptographic SHA-256 hashes are stored.

#### Data Structure

```solidity
struct AuditRecord {
    bytes32 recordHash;      // SHA-256 of canonical JSON
    uint8 recordType;        // 1=TRANSACTION, 2=IDENTITY, 3=INVESTIGATION
    string recordId;         // Reference ID (e.g., transaction reference)
    uint256 timestamp;       // Block timestamp
    address submitter;       // Address that registered the hash
    bool exists;             // Existence flag
}
```

#### Contract Functions

| Function | Visibility | Purpose |
|---|---|---|
| `registerRecordHash(bytes32, uint8, string)` | public | Register a canonical hash with type and reference ID |
| `registerTransactionHash(bytes32, string)` | external | Shortcut for transaction hash registration |
| `registerIdentityHash(bytes32, string)` | external | Shortcut for identity attribute hash registration |
| `registerInvestigationHash(bytes32, string)` | external | Shortcut for investigation snapshot registration |
| `verifyRecord(bytes32)` | external view | Check if hash exists and return audit details |
| `getRecord(bytes32)` | external view | Return full AuditRecord struct |
| `getTotalRecords()` | external view | Count of registered records |
| `getRecordHashes(uint256, uint256)` | external view | Paginated hash retrieval for indexing |

#### Tamper Detection Flow

```
1. Database record -> Canonical JSON (sorted keys, stripped runtime fields)
2. Canonical JSON -> SHA-256 digest (0x...)
3. SHA-256 hash -> Registered on PhantomAuditRegistry.sol
4. Verification: Recalculate hash from DB record -> Compare against on-chain storage
5. Match -> VERIFIED    |  Mismatch -> TAMPERED
```

#### Security Features
- **Custom errors**: `RecordAlreadyExists`, `InvalidRecordHash` (gas-efficient)
- **Event logging**: `RecordRegistered` event with indexed fields for off-chain indexing
- **Immutability**: Once registered, hashes cannot be modified or deleted
- **Duplicate prevention**: Reverts if hash already exists

---

## 13. Frontend Application (React + TypeScript)

### Application Routes

| Route | Component | Description |
|---|---|---|
| `/` | `Landing` | High-impact intelligence landing page with feature showcase |
| `/login` | `Login` | Supabase authentication with 1-Click Demo Login |
| `/signup` | `Signup` | New user registration |
| `/dashboard` | `Dashboard` | Intelligence Command Center with charts and alerts |
| `/network` | `NetworkExplorer` | Interactive Cytoscape.js network graph |
| `/transactions` | `Transactions` | Transaction explorer with blockchain verification |
| `/identities` | `Identities` | Identity cluster explorer |
| `/risk` | `RiskIntelligence` | Risk factor analytics and scored entity list |
| `/alerts` | `Alerts` | Real-time alert triage queue |
| `/investigations` | `Investigations` | Investigation case workspace |
| `/investigations/:id` | `InvestigationDetail` | Individual case file with notes, timeline, export |
| `/blockchain` | `BlockchainVerification` | Tamper verification tool with toggle test |
| `/audit` | `AuditLogs` | Immutable audit trail viewer |
| `/import` | `DataImport` | CSV ingestion pipeline |
| `/settings` | `Settings` | System health & configuration |

### Component Library

| Directory | Components |
|---|---|
| `components/layout/` | `AppShell` (Sidebar + Topbar wrapper for authenticated routes) |
| `components/network/` | Cytoscape.js canvas, node inspector, graph controls |
| `components/ui/` | `StatCard`, `RiskBadge`, `SearchBar`, `Modal`, `AlertToast` |

### Key Frontend Features

1. **Interactive Network Graph** — Cytoscape.js-powered visualization with:
   - Drag, zoom, pan controls
   - Node click inspection (account details, risk score, relationships)
   - Cycle highlight and path tracing
   - Multi-hop neighborhood expansion

2. **Dashboard** — Intelligence Command Center featuring:
   - 8 telemetry stat cards (accounts, customers, transactions, risk, alerts, cycles, blockchain, investigations)
   - Intraday transaction volume area chart (Recharts)
   - Risk tier breakdown pie/donut chart
   - Flagged entity watchlist with RiskBadge indicators
   - Active alerts queue with triage actions
   - Operation Phantom Ring spotlight banner

3. **Blockchain Verification** — Interactive tamper testing with:
   - One-click hash recalculation
   - Visual VERIFIED / TAMPERED status display
   - Simulated tampering toggle for demonstration

4. **Investigation Workspace** — Case file management:
   - Case notes and timeline
   - Entity linking to accounts, customers, transactions
   - PDF, JSON, and CSV export

5. **Demo Mode** — Comprehensive offline demo data (`demoData.ts`, 17KB) enabling full platform evaluation without a live database connection.

---

## 14. REST API & Edge Functions

### Supabase Edge Functions

| Endpoint | Method | Purpose |
|---|---|---|
| `/functions/v1/calculate-risk` | POST | Triggers Python analytics engine or internal CTE-based scoring |
| `/functions/v1/verify-blockchain` | POST | Checks record hash against EVM smart contract |
| `/functions/v1/ingest-transactions` | POST | Validates CSV imports, persists to PostgreSQL |
| `/functions/v1/generate-report` | POST | Compiles investigation case file (PDF/JSON/CSV) |
| `/functions/v1/graph-query` | GET | Returns neighborhood subgraph for Cytoscape.js |
| `/functions/v1/health` | GET | Cross-service health check |

### Python Analytics Service Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/analytics/risk-score` | POST | Computes 8-factor explainable risk score |
| `/api/analytics/detect-cycles` | POST | Multi-hop cycle detection (A -> B -> C -> A) |
| `/api/analytics/detect-structuring` | POST | Smurfing detection under regulatory thresholds |
| `/api/analytics/detect-rapid-passthrough` | POST | Mule account intermediary draining detection |
| `/api/analytics/centrality` | POST | Degree, Betweenness, and PageRank calculation |
| `/api/analytics/verify-blockchain` | POST | Cryptographic hash validation |
| `/api/health` | GET | Health monitoring endpoint |

### API Documentation
When running locally, interactive documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 15. End-to-End Data Flow

```
Step 1: INGESTION
  CSV / API -> Ingestion Service -> Supabase DB (PostgreSQL) -> Event Trigger

Step 2: GRAPH PROJECTION
  PostgreSQL Transaction Rows -> Neo4j Graph (Nodes & Edges via sync_neo4j.py)

Step 3: ADVANCED SQL & PYTHON RISK ENGINE
  PostgreSQL Recursive CTEs + NetworkX Graph Analysis -> 8 Risk Factors (0-100)

Step 4: CRYPTOGRAPHIC PROOF
  Canonical JSON Payload -> SHA-256 -> PhantomAuditRegistry (EVM Blockchain)

Step 5: ALERTING & TRIAGE
  Score > 60 (High) or > 80 (Critical) -> Supabase Realtime Event -> UI Alert Banner

Step 6: INVESTIGATION WORKSPACE
  Investigator searches -> Explores Cytoscape Graph -> Gathers Proof -> Exports Case Dossier
```

---

## 16. Pre-Seeded Case Study: Operation Phantom Ring

PHANTOM includes a complete end-to-end financial crime case study demonstrating all system capabilities.

### Transaction Flow

```
Customer C001 (Devraj Singhania)
            |
   Account ACC-0001-9041 (HDFC)
            |
        Rs.480,000 (RTGS)
            v
   Account ACC-0044-7721 (ICICI) <----+
            |                         |
        Rs.470,000 (RTGS)             | Shares Device
            v                         | DEV-PHANTOM-103
   Account ACC-0078-3319 (SBI)   -----+
            |
        Rs.465,000 (RTGS)
            v
   Account ACC-0001-9041 (Cycle Closed)
```

### Investigation Findings

| Metric | Value |
|---|---|
| **Total Cycled Amount** | Rs.1,415,000 |
| **Cycle Duration** | 4.25 hours |
| **Number of Hops** | 3 (ACC-0001 -> ACC-0044 -> ACC-0078 -> ACC-0001) |
| **Shared Hardware Device** | DEV-PHANTOM-103 |
| **Betweenness Centrality** | 0.810 |
| **Composite Risk Score** | **94.0 / 100 (CRITICAL)** |

### Rules Triggered

| Rule | Points | Evidence |
|---|---|---|
| RULE_001: Circular Flow | 25 pts | 3-hop closed loop within 4.25 hours |
| RULE_002: Rapid Pass-Through | 20 pts | Funds drained >90% within 2 hours at each hop |
| RULE_003: Structuring | 20 pts | Amounts Rs.465K-Rs.480K (just below Rs.5L threshold) |
| RULE_005: Shared Device | 15 pts | DEV-PHANTOM-103 collision across 2 accounts |
| RULE_006: High Centrality | 15 pts | Betweenness 0.810 (structural bottleneck) |
| **Total** | **94 pts** | **CRITICAL** |

### Case Reference
- **Case Number**: INV-2026-PHANTOM-001
- **Assigned To**: Agent Vikram Rathore (FIU Taskforce)
- **Priority**: URGENT

---

## 17. CI/CD Pipeline

### GitHub Actions Workflow (`ci.yml`)

The CI pipeline runs on push to `main`/`develop` and on pull requests to `main`. It consists of **3 parallel jobs**:

#### Job 1: Python Analytics & Risk Engine Tests
```
- Python 3.11 setup with pip caching
- Install dependencies from analytics/requirements.txt
- Run: pytest tests/ -v
- Verifies: 14 unit & integration tests
```

#### Job 2: Frontend Typecheck and Production Build
```
- Node.js 20 setup with npm caching
- npm ci in frontend/
- Run: npm run build (TypeScript + Vite)
- Environment: Mock Supabase URL, demo mode enabled
```

#### Job 3: Blockchain Smart Contract Tests
```
- Node.js 20 setup
- npm ci in blockchain/
- Run: npx hardhat test
- Verifies: Contract compilation, deployment, and test assertions
```

---

## 18. Cloud Deployment Guide

### Step 1: Create Supabase Project
Visit supabase.com, create a new project, and note the **Project URL** and **Publishable Anon Key**.

### Step 2: Run Database Migrations
Execute in Supabase SQL Editor in sequential order:
1. `supabase/migrations/20261006000001_initial_schema.sql` — 18 tables, indexes
2. `supabase/migrations/20261006000002_advanced_analytics.sql` — 8 PL/pgSQL functions + 1 view
3. `supabase/migrations/20261006000003_rls_policies.sql` — RLS policies for all 18 tables
4. `supabase/seed.sql` — Demo data (Operation Phantom Ring)

### Step 3: Configure Supabase Auth
Add your Vercel deployment URL under **Authentication > URL Configuration**.

### Step 4: Configure Storage
Ensure buckets exist: `transaction-imports`, `investigation-reports`, `evidence`.

### Step 5: Create Neo4j Aura Database
Create a free Neo4j Aura instance and copy the connection URI (`neo4j+s://...`), username, and password.

### Step 6: Deploy Python Analytics Microservice
Deploy `analytics/` to Railway, Render, or Fly.io:
- **Build**: `pip install -r requirements.txt`
- **Start**: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

### Step 7: Deploy Blockchain Smart Contract
```bash
cd blockchain
npm install
npx hardhat run scripts/deploy.ts --network sepolia
```

### Step 8: Configure Environment Variables (Vercel)
```
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=your-supabase-publishable-key
VITE_ANALYTICS_API_URL=https://your-analytics-service.up.railway.app
VITE_ENABLE_DEMO_MODE=true
```

### Step 9: Deploy Frontend to Vercel
- **Framework Preset**: Vite
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`

### Step 10: Smoke Test
Visit the Vercel URL, click **"1-Click Demo Login"**, and verify dashboard, network graph, and blockchain verification.

---

## 19. Local Development Setup

### Prerequisites
- Node.js v20+
- Python 3.11+
- Git

### Run Python Analytics Engine
```bash
cd analytics
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Run Tests
```bash
cd analytics
pytest tests/ -v
```

### Run React Frontend
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 20. Verification Checklist

- [x] Zero Dockerfiles, docker-compose, or container orchestration
- [x] Zero Kubernetes manifests or Helm charts
- [x] Managed cloud architecture (Vercel + Supabase + Neo4j Aura + EVM Testnet)
- [x] 18 PostgreSQL tables with UUID PKs, FK constraints, and CHECK constraints
- [x] 20 performance indexes for enterprise query speeds
- [x] 8 Advanced PL/pgSQL functions (Recursive CTEs + Window Functions)
- [x] Row Level Security (RLS) enabled across all 18 tables
- [x] 4 user roles with granular RBAC policies (ADMIN, INVESTIGATOR, ANALYST, VIEWER)
- [x] Python FastAPI analytics engine with 8 detection modules
- [x] 8-factor explainable risk scoring (0-100) with audit trail
- [x] NetworkX graph analysis (cycles, centrality, shortest path, communities)
- [x] Solidity smart contract for tamper-evident blockchain verification
- [x] Cytoscape.js interactive graph with cycle highlight and node inspector
- [x] Blockchain tamper-evident verification with interactive test toggle
- [x] 15 frontend pages (Landing, Dashboard, Network, Transactions, etc.)
- [x] 1-Click evaluator demo login (Agent Vikram Rathore)
- [x] PDF, JSON, and CSV investigation report export
- [x] End-to-end case study: Operation Phantom Ring (Rs.1.415M circular flow)
- [x] 100% backend unit and integration test pass rate (14/14 tests)
- [x] 3-job CI/CD pipeline (Python tests, Frontend build, Blockchain tests)
- [x] Pre-seeded demo data: 1,000 customers, 1,500 accounts, 20,000 transactions

---

## 21. Development Roadmap

| Phase | Title | Status | Description |
|---|---|---|---|
| Phase 1 | Architecture & Repository Scaffolding | Complete | Architecture docs, directory hierarchy, all subdirectories created |
| Phase 2 | PostgreSQL Schema & Advanced SQL | Complete | 18-table schema with RLS, UUIDs, indexes, audit trail, 8 PL/pgSQL functions |
| Phase 3 | Python Analytics & Risk Engine | Complete | NetworkX graph traversal, cycle detection, structuring, mule detection, explainable scoring, 14 Pytest tests |
| Phase 4 | Blockchain Smart Contract | Complete | Solidity contract, Hardhat config, deployment script, canonical hashing module |
| Phase 5 | Demo Dataset & Operation Phantom Ring | Complete | Realistic synthetic data generator, bundled seed data, case study |
| Phase 6 | Frontend Development | Complete | 15 pages with Cytoscape.js graph, interactive dashboard, investigations workspace |
| Phase 7 | Supabase Edge Functions & Health Check | Complete | Edge function definitions, health endpoint, verification endpoints |
| Phase 8 | End-to-End Verification & CI/CD | Complete | Build verified, tests passing, zero hardcoded localhost, README deployment guide |

---

## File Statistics Summary

| Category | Count | Total Size |
|---|---|---|
| Frontend Pages | 15 files | ~121 KB |
| Frontend Components | 3 directories | ~15 KB |
| Frontend Library | 3 files | ~20 KB |
| Python Analytics Modules | 8 files | ~30 KB |
| SQL Migrations | 3 files | ~38 KB |
| SQL Seed Data | 1 file | ~11 KB |
| Smart Contract | 1 file | ~5 KB |
| Scripts | 4 files | ~20 KB |
| CI/CD | 1 file | ~2 KB |
| Documentation | 3 files | ~30 KB |
| **Total** | **~40+ files** | **~292+ KB** |

---

> **MIT License.** Developed for advanced financial crime network intelligence and regulatory compliance research.
>
> *Document generated on: October 2026*
