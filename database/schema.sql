-- ============================================================================
-- PHANTOM — Initial Schema Migration
-- 18 Tables, 20 Indexes, Extensions, Auto-Profile Trigger
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- TABLE 1: profiles
-- ============================================================================
CREATE TABLE profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name   TEXT        NOT NULL,
    email       TEXT        UNIQUE NOT NULL,
    role        TEXT        NOT NULL DEFAULT 'INVESTIGATOR'
                            CHECK (role IN ('ADMIN', 'INVESTIGATOR', 'ANALYST', 'VIEWER')),
    badge_number TEXT,
    avatar_url  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- TABLE 2: customers
-- ============================================================================
CREATE TABLE customers (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_reference  VARCHAR(64)   UNIQUE NOT NULL,
    name                VARCHAR(255)  NOT NULL,
    email_masked        VARCHAR(255)  NOT NULL,
    phone_masked        VARCHAR(64)   NOT NULL,
    country             CHAR(2)       NOT NULL DEFAULT 'IN',
    identity_hash       VARCHAR(64)   NOT NULL,
    risk_score          NUMERIC(5,2)  DEFAULT 0.00
                                      CHECK (risk_score >= 0 AND risk_score <= 100),
    risk_level          VARCHAR(20)   DEFAULT 'LOW'
                                      CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- TABLE 3: accounts
-- ============================================================================
CREATE TABLE accounts (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_number_masked   VARCHAR(64)   UNIQUE NOT NULL,
    customer_id             UUID          NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    account_type            VARCHAR(32)   CHECK (account_type IN ('SAVINGS', 'CURRENT', 'ESCROW', 'CORPORATE', 'CRYPTO_WALLET')),
    bank_code               VARCHAR(32)   NOT NULL DEFAULT 'HDFC',
    country                 CHAR(2)       NOT NULL DEFAULT 'IN',
    status                  VARCHAR(20)   CHECK (status IN ('ACTIVE', 'FROZEN', 'RESTRICTED', 'CLOSED')),
    risk_score              NUMERIC(5,2)  DEFAULT 0.00
                                          CHECK (risk_score >= 0 AND risk_score <= 100),
    risk_level              VARCHAR(20)   CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    is_dormant              BOOLEAN       NOT NULL DEFAULT FALSE,
    last_activity_at        TIMESTAMPTZ,
    created_at              TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- TABLE 4: transactions
-- ============================================================================
CREATE TABLE transactions (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_reference   VARCHAR(64)   UNIQUE NOT NULL,
    sender_account_id       UUID          NOT NULL REFERENCES accounts(id) ON DELETE RESTRICT,
    receiver_account_id     UUID          NOT NULL REFERENCES accounts(id) ON DELETE RESTRICT,
    amount                  NUMERIC(15,2) NOT NULL CHECK (amount > 0),
    currency                VARCHAR(10)   NOT NULL DEFAULT 'INR',
    transaction_type        VARCHAR(32)   CHECK (transaction_type IN ('WIRE', 'UPI', 'NEFT', 'RTGS', 'INTERNAL_TRANSFER', 'ATM')),
    transaction_timestamp   TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    location                VARCHAR(128),
    device_id               VARCHAR(64),
    ip_hash                 VARCHAR(64),
    status                  VARCHAR(20)   CHECK (status IN ('PENDING', 'COMPLETED', 'FLAGGED', 'BLOCKED')),
    blockchain_hash         VARCHAR(66),
    blockchain_tx_id        VARCHAR(66),
    verification_status     VARCHAR(20)   DEFAULT 'VERIFIED'
                                          CHECK (verification_status IN ('PENDING', 'VERIFIED', 'TAMPERED')),
    created_at              TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- TABLE 5: identity_attributes
-- ============================================================================
CREATE TABLE identity_attributes (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id             UUID          NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    attribute_type          VARCHAR(32)   CHECK (attribute_type IN ('EMAIL', 'PHONE', 'DEVICE', 'IP', 'ADDRESS', 'DOCUMENT', 'BANK_ACCOUNT')),
    attribute_hash          VARCHAR(64)   NOT NULL,
    attribute_value_masked  VARCHAR(255)  NOT NULL,
    confidence              NUMERIC(3,2)  DEFAULT 1.00
                                          CHECK (confidence >= 0 AND confidence <= 1.00),
    created_at              TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- TABLE 6: account_relationships
-- ============================================================================
CREATE TABLE account_relationships (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_account_id       UUID          NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    target_account_id       UUID          NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    relationship_type       VARCHAR(64)   CHECK (relationship_type IN ('SHARED_DEVICE', 'SHARED_IP', 'CIRCULAR_FLOW', 'RAPID_PASS_THROUGH', 'COUNTERPARTY', 'SAME_CUSTOMER')),
    confidence              NUMERIC(3,2)  DEFAULT 0.85,
    evidence_count          INT           DEFAULT 1,
    metadata                JSONB         DEFAULT '{}',
    created_at              TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    UNIQUE (source_account_id, target_account_id, relationship_type)
);

-- ============================================================================
-- TABLE 7: risk_scores
-- ============================================================================
CREATE TABLE risk_scores (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type     VARCHAR(32)   CHECK (entity_type IN ('ACCOUNT', 'CUSTOMER')),
    entity_id       UUID          NOT NULL,
    score           NUMERIC(5,2)  CHECK (score >= 0 AND score <= 100),
    risk_level      VARCHAR(20)   CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    reasons         JSONB         DEFAULT '[]',
    calculated_at   TIMESTAMPTZ   DEFAULT NOW()
);

-- ============================================================================
-- TABLE 8: risk_factors
-- ============================================================================
CREATE TABLE risk_factors (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    risk_score_id   UUID          NOT NULL REFERENCES risk_scores(id) ON DELETE CASCADE,
    rule_id         VARCHAR(32)   NOT NULL,
    rule_name       VARCHAR(128)  NOT NULL,
    severity        VARCHAR(20)   CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    weight          NUMERIC(5,2)  NOT NULL,
    evidence        JSONB         DEFAULT '{}',
    created_at      TIMESTAMPTZ   DEFAULT NOW()
);

-- ============================================================================
-- TABLE 9: fraud_rules
-- ============================================================================
CREATE TABLE fraud_rules (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id         VARCHAR(32)   UNIQUE NOT NULL,
    name            VARCHAR(128)  NOT NULL,
    description     TEXT          NOT NULL,
    default_weight  NUMERIC(5,2)  NOT NULL,
    severity        VARCHAR(20)   CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    is_active       BOOLEAN       DEFAULT TRUE,
    created_at      TIMESTAMPTZ   DEFAULT NOW()
);

-- ============================================================================
-- TABLE 10: alerts
-- ============================================================================
CREATE TABLE alerts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type     VARCHAR(32)   CHECK (entity_type IN ('ACCOUNT', 'CUSTOMER', 'TRANSACTION', 'NETWORK')),
    entity_id       UUID          NOT NULL,
    alert_type      VARCHAR(64)   NOT NULL,
    severity        VARCHAR(20)   CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    title           VARCHAR(255)  NOT NULL,
    description     TEXT          NOT NULL,
    evidence        JSONB         DEFAULT '{}',
    status          VARCHAR(20)   DEFAULT 'NEW'
                                  CHECK (status IN ('NEW', 'IN_REVIEW', 'ESCALATED', 'DISMISSED')),
    assigned_to     UUID          REFERENCES profiles(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ   DEFAULT NOW()
);

-- ============================================================================
-- TABLE 11: investigations
-- ============================================================================
CREATE TABLE investigations (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    investigator_id     UUID          REFERENCES profiles(id) ON DELETE SET NULL,
    case_number         VARCHAR(64)   UNIQUE NOT NULL,
    title               VARCHAR(255)  NOT NULL,
    description         TEXT          NOT NULL,
    priority            VARCHAR(20)   DEFAULT 'MEDIUM'
                                      CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT')),
    status              VARCHAR(20)   DEFAULT 'OPEN'
                                      CHECK (status IN ('OPEN', 'IN_PROGRESS', 'PENDING_REVIEW', 'CLOSED')),
    created_at          TIMESTAMPTZ   DEFAULT NOW(),
    updated_at          TIMESTAMPTZ   DEFAULT NOW()
);

-- ============================================================================
-- TABLE 12: investigation_entities
-- ============================================================================
CREATE TABLE investigation_entities (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    investigation_id    UUID          NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    entity_type         VARCHAR(32)   CHECK (entity_type IN ('ACCOUNT', 'CUSTOMER', 'TRANSACTION', 'DEVICE', 'IP')),
    entity_id           UUID          NOT NULL,
    notes               TEXT,
    added_at            TIMESTAMPTZ   DEFAULT NOW(),
    UNIQUE (investigation_id, entity_type, entity_id)
);

-- ============================================================================
-- TABLE 13: investigation_notes
-- ============================================================================
CREATE TABLE investigation_notes (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    investigation_id    UUID          NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    author_id           UUID          REFERENCES profiles(id) ON DELETE SET NULL,
    content             TEXT          NOT NULL,
    created_at          TIMESTAMPTZ   DEFAULT NOW()
);

-- ============================================================================
-- TABLE 14: blockchain_records
-- ============================================================================
CREATE TABLE blockchain_records (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    record_hash         VARCHAR(66)   UNIQUE NOT NULL,
    record_type         VARCHAR(32)   CHECK (record_type IN ('TRANSACTION', 'IDENTITY', 'INVESTIGATION')),
    canonical_payload   JSONB         NOT NULL,
    blockchain_tx_id    VARCHAR(66)   NOT NULL,
    block_number        BIGINT        DEFAULT 0,
    submitter_address   VARCHAR(42)   DEFAULT '0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc',
    status              VARCHAR(20)   DEFAULT 'VERIFIED'
                                      CHECK (status IN ('VERIFIED', 'TAMPERED')),
    verified_at         TIMESTAMPTZ   DEFAULT NOW(),
    created_at          TIMESTAMPTZ   DEFAULT NOW()
);

-- ============================================================================
-- TABLE 15: audit_logs
-- ============================================================================
CREATE TABLE audit_logs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID          REFERENCES profiles(id) ON DELETE SET NULL,
    action              VARCHAR(64)   NOT NULL,
    entity_type         VARCHAR(32)   NOT NULL,
    entity_id           UUID          NOT NULL,
    previous_hash       VARCHAR(66),
    current_hash        VARCHAR(66),
    blockchain_tx_id    VARCHAR(66),
    details             JSONB         DEFAULT '{}',
    timestamp           TIMESTAMPTZ   DEFAULT NOW()
);

-- ============================================================================
-- TABLE 16: network_clusters
-- ============================================================================
CREATE TABLE network_clusters (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cluster_name    VARCHAR(128)  NOT NULL,
    entity_ids      JSONB         DEFAULT '[]',
    risk_score      NUMERIC(5,2)  DEFAULT 50.00,
    description     TEXT          NOT NULL,
    detected_at     TIMESTAMPTZ   DEFAULT NOW()
);

-- ============================================================================
-- TABLE 17: ingestion_jobs
-- ============================================================================
CREATE TABLE ingestion_jobs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename            VARCHAR(255)  NOT NULL,
    total_records       INT           DEFAULT 0,
    processed_records   INT           DEFAULT 0,
    status              VARCHAR(20)   DEFAULT 'PENDING'
                                      CHECK (status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')),
    error_log           TEXT,
    created_at          TIMESTAMPTZ   DEFAULT NOW(),
    updated_at          TIMESTAMPTZ   DEFAULT NOW()
);

-- ============================================================================
-- TABLE 18: system_events
-- ============================================================================
CREATE TABLE system_events (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type      VARCHAR(64)   NOT NULL,
    severity        VARCHAR(20)   DEFAULT 'INFO',
    payload         JSONB         DEFAULT '{}',
    created_at      TIMESTAMPTZ   DEFAULT NOW()
);

-- ============================================================================
-- INDEXES (20 B-Tree Performance Indexes)
-- ============================================================================

-- Customer & Account lookup
CREATE INDEX idx_customers_risk_level        ON customers(risk_level);
CREATE INDEX idx_customers_identity_hash     ON customers(identity_hash);
CREATE INDEX idx_accounts_customer_id        ON accounts(customer_id);
CREATE INDEX idx_accounts_risk_level         ON accounts(risk_level);
CREATE INDEX idx_accounts_status             ON accounts(status);
CREATE INDEX idx_accounts_is_dormant         ON accounts(is_dormant);

-- Transaction performance
CREATE INDEX idx_transactions_sender         ON transactions(sender_account_id);
CREATE INDEX idx_transactions_receiver       ON transactions(receiver_account_id);
CREATE INDEX idx_transactions_timestamp      ON transactions(transaction_timestamp DESC);
CREATE INDEX idx_transactions_amount         ON transactions(amount);
CREATE INDEX idx_transactions_blockchain_hash ON transactions(blockchain_hash);

-- Identity & relationship joins
CREATE INDEX idx_identity_attrs_hash         ON identity_attributes(attribute_hash);
CREATE INDEX idx_identity_attrs_customer     ON identity_attributes(customer_id);
CREATE INDEX idx_account_rel_source          ON account_relationships(source_account_id);
CREATE INDEX idx_account_rel_target          ON account_relationships(target_account_id);

-- Alert & investigation triage
CREATE INDEX idx_alerts_severity             ON alerts(severity);
CREATE INDEX idx_alerts_status               ON alerts(status);
CREATE INDEX idx_investigations_status       ON investigations(status);

-- Blockchain verification
CREATE INDEX idx_blockchain_records_hash     ON blockchain_records(record_hash);

-- ============================================================================
-- AUTO-PROFILE TRIGGER
-- Creates a profiles row when a new user signs up via Supabase Auth
-- ============================================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, full_name, email, role)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data ->> 'full_name', 'Unknown'),
        COALESCE(NEW.email, ''),
        COALESCE(NEW.raw_user_meta_data ->> 'role', 'INVESTIGATOR')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();
