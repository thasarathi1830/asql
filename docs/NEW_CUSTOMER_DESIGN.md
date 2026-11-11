# PHANTOM — New Customer Onboarding & Real-Time Screening Architecture Design

## 1. System Overview & Reuse Architecture

This design extends PHANTOM with **pre-onboarding risk scoring** and **sub-500ms pre-transaction screening**, strictly honoring privacy (zero raw PII persisted), determinism, and explainability.

```
+-----------------------------------------------------------------------------------------+
|                                    INPUT GATEWAY                                        |
|  Customer Data (Full Name, DOB, Income) | Accounts | Identity Hashes (Device, IP, Phone)|
+-----------------------------------------------------------------------------------------+
                                             |
                                             v
               +-------------------------------------------------------------+
               | PRIVACY SHIELD: Salted SHA-256 Hashing + Masking            |
               | Raw email/phone/address/IP/ID stripped prior to persistence |
               +-------------------------------------------------------------+
                                             |
                      +----------------------+----------------------+
                      |                                             |
                      v                                             v
        [STAGE 1: ONBOARDING ENGINE]                  [STAGE 2: SCREENING ENGINE]
        (analytics/app/onboarding_risk.py)            (analytics/app/screening_engine.py)
        - ONB_001: Shared Device / IP (30pts)         - Incremental RULE_001 (Cycle Close)
        - ONB_002: Flagged Entity Links (30pts)       - Incremental RULE_002 (Mule Drain)
        - ONB_003: Near-Duplicate Identity (20pts)    - Incremental RULE_003 (Structuring)
        - ONB_004: Cluster Membership (15pts)         - Incremental RULE_004 (Dormant Surge)
        - ONB_005: High-Risk Country/Type (10pts)     - Incremental RULE_005 (Device Collision)
        - ONB_006: Data Consistency/Age (10pts)       - Incremental RULE_007 (Risky CP)
        - ONB_007: Income vs Volume (10pts)           - Incremental RULE_008 (Velocity Spike)
                      |                                             |
                      v                                             v
       Decisions:                                    Decisions (p95 < 500ms):
       - APPROVE (<30)                               - ALLOW (<30)
       - ENHANCED_DUE_DILIGENCE (30-59)              - ALLOW_WITH_MONITORING (30-59)
       - MANUAL_REVIEW (60-79)                       - HOLD_FOR_REVIEW (60-79)
       - ESCALATE (>=80)                             - BLOCK (>=80)
                      |                                             |
                      +----------------------+----------------------+
                                             |
                                             v
                      +---------------------------------------------+
                      | CONTINUOUS MONITORING & AUDIT TRAIL         |
                      | (scripts/monitor.py & blockchain anchoring) |
                      +---------------------------------------------+
```

## 2. Reused Modules & Functions
- `analytics/app/risk_engine.py`: Reused for the 8-factor mathematical model, rule weights, thresholds, and score capping.
- `analytics/app/graph_analysis.py`: `TransactionGraphEngine` reused for in-memory graph topology and cycle checking.
- `analytics/app/anomaly_detection.py`: Reused for rapid pass-through and dormant activation checks.
- `analytics/app/structuring_engine.py`: Reused for sub-regulatory threshold window searches.
- `analytics/app/blockchain.py`: Reused for canonical JSON serialization, SHA-256 computation, and verification.

## 3. New Modules & Extensions
- `supabase/migrations/20261006000004_onboarding_and_screening.sql`: DB tables for onboarding assessments, rules, score history, and screening decisions.
- `analytics/app/onboarding_risk.py`: Implements ONB_001 to ONB_007 with privacy validation.
- `analytics/app/screening_engine.py`: Cached graph snapshot with incremental O(k) path verification achieving <500ms p95 latency.
- `analytics/app/routers/screening.py`: Endpoints for `/onboard-customer`, `/screen-transaction`, `/screen-batch`, `/customers/{id}/risk-timeline`, `/reassess/{id}`.
- `scripts/build_onboarding_scenarios.py`: Creates 230 labelled test scenarios against the PaySim dataset.
- `frontend/src/pages/NewCustomer.tsx`: 5-step onboarding wizard with live Cytoscape cluster preview.

