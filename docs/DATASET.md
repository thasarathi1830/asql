# PHANTOM — Dataset Provenance, Sampling & Enrichment Specification

## 1. Primary Dataset Citation

PHANTOM uses the real **PaySim** synthetic financial mobile-money simulator dataset:

> E. A. Lopez-Rojas, A. Elmir, and S. Axelsson, *"PaySim: A financial mobile money simulator for fraud detection"*, in *Proceedings of the 28th European Modeling and Simulation Symposium (EMSS)*, Larnaca, Cyprus, 2016, pp. 249–255.

- **Raw File**: `data/raw/PS_20174392719_1491204439457_log.csv` (6,362,620 rows; 493.5 MB).
- **Columns**: `step, type, amount, nameOrig, oldbalanceOrg, newbalanceOrig, nameDest, oldbalanceDest, newbalanceDest, isFraud, isFlaggedFraud`.

## 2. PaySim Ground Rules Enforced

1. **Temporal Mapping**: 1 `step` = 1 hour (744 steps = 31 days). Mapped to `transaction_timestamp` starting from `2026-06-01T00:00:00Z` with deterministic intra-hour minute/second offsets.
2. **Leakage Prevention (Balance Columns Excluded)**: In PaySim, fraud transactions are cancelled by the simulator, leaving deterministic artifacts in `oldbalanceOrg/newbalanceOrig/oldbalanceDest/newbalanceDest`. PHANTOM **never reads or uses any balance column** as a detection feature.
3. **Fraud Scope**: In PaySim, `isFraud=1` occurs exclusively in `TRANSFER` and `CASH_OUT` transactions.
4. **Merchants**: Accounts starting with `M` are merchants and mapped to `account_type = 'CORPORATE'`.

## 3. Streaming Sampling Methodology (`scripts/paysim_adapter.py`, `seed=42`)

To process all 6.36M rows safely on a laptop without loading the CSV into RAM, `paysim_adapter.py` executes a two-pass streaming scan (`chunksize=100,000`):

1. **100% Fraud Retention**: Every row with `isFraud == 1` (8,213 rows) is retained.
2. **100% Fraud-Neighborhood Context**: Every normal transaction whose `nameOrig` or `nameDest` touches any fraud account is retained to preserve graph topology.
3. **Stratified Normal Background**: Remaining `TRANSFER`/`CASH_OUT` (~60% of remaining budget) and `PAYMENT`/`CASH_IN`/`DEBIT` (~40% of remaining budget) are sampled deterministically to reach ~70,000 total transactions.
4. Sampling metadata is written to `data/processed/sampling_report.json`.

## 4. Real vs Synthetic Enrichment vs Injected Patterns

| Field / Table | Origin | Tag (`data_source`) | Notes |
|---|---|---|---|
| `transactions` (PaySim rows) | Real PaySim | `PAYSIM_REAL` | `amount`, `step` -> timestamp, `type` mapped, `paysim_is_fraud` preserved |
| `accounts` (PaySim accounts) | Derived from PaySim `nameOrig`/`nameDest` | `PAYSIM_DERIVED` | Masked account number, deterministic `bank_code` & `account_type` |
| `customers` (Indian names, masked email/phone) | Synthetic Enrichment | `SYNTHETIC_ENRICHMENT` | Seeded grouping (~1.3 accounts/customer) |
| `identity_attributes` (`DEVICE`, `IP`) | Synthetic Enrichment | `SYNTHETIC_ENRICHMENT` | Base device/IP per customer + 40 shared-device/IP groups (`RULE_005`) |
| `transactions` (25 planted rings) | Injected Patterns | `INJECTED_RING` | 3–5 hop loops, amounts <500K, closed within 6h (`RULE_001`) |
| Operation Phantom Ring (`C001–C003`, `ACC-0001-9041`, etc.) | Pre-seeded Case Study | `PHANTOM_RING_SEED` | Exact documentation Section 16 case study |

All ground-truth labels in `data/processed/ground_truth.csv` carry `source ∈ {PAYSIM, INJECTED}` so `analytics/evaluation/evaluate.py` reports real PaySim performance separately from injected patterns.
