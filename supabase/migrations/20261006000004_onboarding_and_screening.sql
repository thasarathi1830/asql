-- ============================================================================
-- PHANTOM Migration 004: New Customer Onboarding & Real-Time Screening
-- ============================================================================

-- 1. Onboarding Rules Table
CREATE TABLE IF NOT EXISTS onboarding_rules (
    rule_id         VARCHAR(20) PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    max_score       NUMERIC(5,2) NOT NULL CHECK (max_score >= 0 AND max_score <= 100),
    severity        VARCHAR(20) NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    description     TEXT NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed Onboarding Rules
INSERT INTO onboarding_rules (rule_id, name, max_score, severity, description) VALUES
('ONB_001', 'Shared Device / IP with Existing Accounts', 30.00, 'CRITICAL', 'Hardware fingerprint or IP hash collision with existing network accounts'),
('ONB_002', 'Linked to Flagged / Investigated Entities', 30.00, 'CRITICAL', 'Direct identity attribute match with HIGH/CRITICAL entity or active investigation'),
('ONB_003', 'Duplicate / Near-Duplicate Identity', 20.00, 'HIGH', 'Exact identity hash match or fuzzy name+DOB match with registered customer'),
('ONB_004', 'Cluster Membership Link', 15.00, 'HIGH', 'Customer identifiers intersect with known financial crime clusters'),
('ONB_005', 'High-Risk Country or Account Type', 10.00, 'MEDIUM', 'High-risk jurisdiction or high-risk account type (CRYPTO_WALLET, ESCROW)'),
('ONB_006', 'Data Quality and Consistency', 10.00, 'MEDIUM', 'Disposable email, age anomaly, or phone country code mismatch'),
('ONB_007', 'Income vs Expected Activity', 10.00, 'MEDIUM', 'Initial declared monthly income anomaly or transaction velocity mismatch')
ON CONFLICT (rule_id) DO NOTHING;

-- 2. Onboarding Assessments Table
CREATE TABLE IF NOT EXISTS onboarding_assessments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id         UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    score               NUMERIC(5,2) NOT NULL CHECK (score >= 0.00 AND score <= 100.00),
    risk_level          VARCHAR(20) NOT NULL CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    decision            VARCHAR(30) NOT NULL CHECK (decision IN ('APPROVE', 'ENHANCED_DUE_DILIGENCE', 'MANUAL_REVIEW', 'ESCALATE')),
    checks              JSONB NOT NULL DEFAULT '[]'::jsonb,
    matched_entities    JSONB NOT NULL DEFAULT '[]'::jsonb,
    assessed_by         VARCHAR(50) NOT NULL DEFAULT 'SYSTEM_AUTO',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_onboarding_assessments_customer_id ON onboarding_assessments(customer_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_assessments_decision ON onboarding_assessments(decision);

-- 3. Risk Score History Table (Continuous Monitoring)
CREATE TABLE IF NOT EXISTS risk_score_history (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id         UUID REFERENCES customers(id) ON DELETE SET NULL,
    account_id          UUID REFERENCES accounts(id) ON DELETE SET NULL,
    previous_score      NUMERIC(5,2) NOT NULL,
    current_score       NUMERIC(5,2) NOT NULL,
    delta               NUMERIC(5,2) NOT NULL,
    risk_level          VARCHAR(20) NOT NULL,
    reasons             JSONB NOT NULL DEFAULT '[]'::jsonb,
    previous_hash       VARCHAR(66),
    current_hash        VARCHAR(66) NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_risk_score_history_customer ON risk_score_history(customer_id);
CREATE INDEX IF NOT EXISTS idx_risk_score_history_account ON risk_score_history(account_id);
CREATE INDEX IF NOT EXISTS idx_risk_score_history_created_at ON risk_score_history(created_at DESC);

-- 4. Screening Decisions Table (Pre-Transaction Real-Time Decisions)
CREATE TABLE IF NOT EXISTS screening_decisions (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_reference   VARCHAR(64) UNIQUE NOT NULL,
    sender_account_id       VARCHAR(64) NOT NULL,
    receiver_account_id     VARCHAR(64) NOT NULL,
    amount                  NUMERIC(15,2) NOT NULL CHECK (amount > 0),
    currency                VARCHAR(3) NOT NULL DEFAULT 'INR',
    decision                VARCHAR(30) NOT NULL CHECK (decision IN ('ALLOW', 'ALLOW_WITH_MONITORING', 'HOLD_FOR_REVIEW', 'BLOCK')),
    score                   NUMERIC(5,2) NOT NULL CHECK (score >= 0.00 AND score <= 100.00),
    rules_triggered         JSONB NOT NULL DEFAULT '[]'::jsonb,
    reasons                 JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence                JSONB NOT NULL DEFAULT '{}'::jsonb,
    latency_ms              NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_screening_decisions_tx_ref ON screening_decisions(transaction_reference);
CREATE INDEX IF NOT EXISTS idx_screening_decisions_decision ON screening_decisions(decision);
CREATE INDEX IF NOT EXISTS idx_screening_decisions_sender ON screening_decisions(sender_account_id);
CREATE INDEX IF NOT EXISTS idx_screening_decisions_created_at ON screening_decisions(created_at DESC);

-- 5. Helper Function: Match Identity Attributes by Type and Hash
CREATE OR REPLACE FUNCTION fn_match_identities_by_hash(
    p_attribute_type VARCHAR,
    p_attribute_hash VARCHAR
)
RETURNS TABLE (
    attribute_id UUID,
    customer_id UUID,
    attribute_type VARCHAR,
    attribute_value_masked VARCHAR,
    customer_reference VARCHAR,
    customer_name VARCHAR,
    customer_risk_score NUMERIC(5,2),
    customer_risk_level VARCHAR
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        ia.id AS attribute_id,
        ia.customer_id,
        ia.attribute_type,
        ia.attribute_value_masked,
        c.customer_reference,
        c.name AS customer_name,
        c.risk_score AS customer_risk_score,
        c.risk_level AS customer_risk_level
    FROM identity_attributes ia
    JOIN customers c ON c.id = ia.customer_id
    WHERE ia.attribute_type = p_attribute_type
      AND ia.attribute_hash = p_attribute_hash;
$$;

-- 6. Enable RLS and Assign Policies
ALTER TABLE onboarding_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE onboarding_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_score_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE screening_decisions ENABLE ROW LEVEL SECURITY;

CREATE POLICY rls_onboarding_rules_select ON onboarding_rules FOR SELECT TO authenticated USING (TRUE);
CREATE POLICY rls_onboarding_rules_admin ON onboarding_rules FOR ALL TO authenticated USING (auth.jwt() ->> 'role' = 'ADMIN');

CREATE POLICY rls_onboarding_assessments_select ON onboarding_assessments FOR SELECT TO authenticated USING (TRUE);
CREATE POLICY rls_onboarding_assessments_insert ON onboarding_assessments FOR INSERT TO authenticated WITH CHECK (auth.jwt() ->> 'role' IN ('ADMIN', 'INVESTIGATOR', 'ANALYST'));

CREATE POLICY rls_risk_score_history_select ON risk_score_history FOR SELECT TO authenticated USING (TRUE);
CREATE POLICY rls_risk_score_history_insert ON risk_score_history FOR INSERT TO authenticated WITH CHECK (auth.jwt() ->> 'role' IN ('ADMIN', 'INVESTIGATOR', 'ANALYST'));

CREATE POLICY rls_screening_decisions_select ON screening_decisions FOR SELECT TO authenticated USING (TRUE);
CREATE POLICY rls_screening_decisions_insert ON screening_decisions FOR INSERT TO authenticated WITH CHECK (auth.jwt() ->> 'role' IN ('ADMIN', 'INVESTIGATOR', 'ANALYST'));

