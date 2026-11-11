# PHANTOM — New Customer Onboarding & Screening Flow Specification

## 1. Input Labels & Privacy Rules

| Field | Type | Storage Rule | Purpose |
|---|---|---|---|
| `customer_reference` | String | Plaintext (Unique) | Core identifier in core banking system |
| `full_name` | String | Plaintext / Sanitized | Customer legal name |
| `date_of_birth` | Date (YYYY-MM-DD) | Plaintext | Age verification (flags < 18 or > 110) |
| `email` | String | **Masked (`d***@mail.com`) + Salted SHA-256** | Contact matching & disposable email domain check |
| `phone` | String | **Masked (`+91-98***-***01`) + Salted SHA-256** | Multi-account linkage |
| `country` | ISO-2 String | Plaintext | FATF / high-risk jurisdiction screening |
| `address` | String | **Salted SHA-256 Hash Only** | Cross-customer address sharing detection |
| `declared_monthly_income` | Float | Plaintext | Baseline for activity & volume checks |
| `device_id` | String | **Masked + Salted SHA-256** | Hardware collision detection (`ONB_001` / `RULE_005`) |
| `ip_address` | String | **Salted SHA-256 Hash Only** | Network IP collision detection |
| `id_document_number` | String | **Masked + Salted SHA-256** | Identity deduplication (`ONB_003`) |

> [!IMPORTANT]
> **Privacy Guarantee:** Raw email, phone, address, government ID numbers, and IP addresses are **never** logged, written to the audit trail, stored in the database, or transmitted in blockchain payloads. Only salted SHA-256 hashes and masked strings are retained.

---

## 2. Decision Matrix

### Stage 1: Onboarding Assessment
| Composite Score | Decision | Action Taken |
|:---:|:---:|---|
| **0.00 – 29.99** | `APPROVE` | Immediate automated account activation. |
| **30.00 – 59.99** | `ENHANCED_DUE_DILIGENCE` | Account provisionally created with lowered transfer limits; flagged for secondary verification. |
| **60.00 – 79.99** | `MANUAL_REVIEW` | Escalated to compliance queue for human analyst review. |
| **80.00 – 100.00** | `ESCALATE` | High-risk block; SAR filing ticket initiated. |

### Stage 2: Pre-Transaction Screening (Real-Time, <500ms)
| Score / Triggers | Decision | Real-Time Action |
|:---:|:---:|---|
| **0.00 – 19.99** | `ALLOW` | Payment processed immediately with zero friction. |
| **20.00 – 59.99** | `ALLOW_WITH_MONITORING` | Payment cleared; accounts tagged for monitoring. |
| **60.00 – 79.99** | `HOLD_FOR_REVIEW` | Payment held in escrow buffer; real-time alert pushed to analyst dashboard. |
| **80.00 – 100.00 / Cycle Closure** | `BLOCK` | Payment rejected; alert generated; investigation candidate flagged. |

---

## 3. Example API Invocations (cURL)

### A. Onboard a New Customer
```bash
curl -X POST http://localhost:8000/api/analytics/onboard-customer \
  -H "Content-Type: application/json" \
  -H "X-Internal-API-Key: dev-key" \
  -d '{
    "customer_reference": "CUST-CORP-9021",
    "full_name": "Devraj Singhania",
    "country": "IN",
    "declared_monthly_income": 450000.0,
    "email": "devraj@singhania-holdings.in",
    "phone": "+919820011223",
    "accounts": [
      {
        "account_number": "ACC-0001-9041",
        "account_type": "CURRENT",
        "bank_code": "HDFC"
      }
    ],
    "identity_attributes": {
      "device_id": "DEV-PHANTOM-103",
      "ip_address": "103.21.244.12"
    }
  }'
```

### Response
```json
{
  "customer_id": "11111111-1111-4111-8111-000000000001",
  "customer_reference": "CUST-CORP-9021",
  "assessment": {
    "onboarding_score": 45.0,
    "risk_level": "MEDIUM",
    "decision": "ENHANCED_DUE_DILIGENCE",
    "checks": [
      {
        "rule_id": "ONB_001",
        "name": "Shared Device / IP with Existing Accounts",
        "score": 30.0,
        "reason": "1 shared hardware/network collision(s) detected",
        "evidence": { "match_count": 1 }
      }
    ],
    "matched_entities": [
      {
        "attribute_type": "DEVICE",
        "attribute_value_masked": "DEV-PH***103",
        "matched_customer_id": "11111111-1111-4111-8111-000000000002"
      }
    ]
  },
  "privacy_verified": true
}
```

### B. Pre-Transaction Screening (Real-Time)
```bash
curl -X POST http://localhost:8000/api/analytics/screen-transaction \
  -H "Content-Type: application/json" \
  -H "X-Internal-API-Key: dev-key" \
  -d '{
    "transaction_reference": "TX-RTGS-9901",
    "sender_account_id": "22222222-2222-4222-8222-000000000001",
    "receiver_account_id": "22222222-2222-4222-8222-000000000002",
    "amount": 480000.0,
    "currency": "INR",
    "transaction_type": "RTGS",
    "device_id": "DEV-PHANTOM-103"
  }'
```

---

## 4. System Boundaries & Legal Disclaimer

> [!WARNING]
> **Decision Support Tool Only:** PHANTOM is an intelligence and graph anomaly screening engine designed to assist human AML/CFT investigators. It **does NOT perform legal identity document authentication, global sanctions screening (OFAC/UN lists), or Politically Exposed Person (PEP) verification**. Sanctions and PEP screening interfaces are defined as future extension hooks and should be integrated with external certified compliance providers.

