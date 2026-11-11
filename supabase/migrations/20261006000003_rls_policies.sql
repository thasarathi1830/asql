-- ============================================================================
-- PHANTOM — Row Level Security (RLS) Policies across all 18 tables
-- Roles: ADMIN, INVESTIGATOR, ANALYST, VIEWER
-- ============================================================================

-- Helper function to retrieve current user's role from profiles
CREATE OR REPLACE FUNCTION public.get_user_role()
RETURNS TEXT AS $$
    SELECT role FROM public.profiles WHERE id = auth.uid();
$$ LANGUAGE sql STABLE SECURITY DEFINER;

-- Enable RLS on ALL 18 tables
ALTER TABLE profiles               ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers              ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounts               ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions           ENABLE ROW LEVEL SECURITY;
ALTER TABLE identity_attributes    ENABLE ROW LEVEL SECURITY;
ALTER TABLE account_relationships  ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_scores            ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_factors           ENABLE ROW LEVEL SECURITY;
ALTER TABLE fraud_rules            ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE investigations         ENABLE ROW LEVEL SECURITY;
ALTER TABLE investigation_entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE investigation_notes    ENABLE ROW LEVEL SECURITY;
ALTER TABLE blockchain_records     ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs             ENABLE ROW LEVEL SECURITY;
ALTER TABLE network_clusters       ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingestion_jobs         ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_events          ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 1. PROFILES
-- ============================================================================
CREATE POLICY "Users can view own profile or admins view all"
    ON profiles FOR SELECT TO authenticated
    USING (id = auth.uid() OR public.get_user_role() IN ('ADMIN', 'INVESTIGATOR', 'ANALYST'));

CREATE POLICY "Users can update own profile"
    ON profiles FOR UPDATE TO authenticated
    USING (id = auth.uid())
    WITH CHECK (id = auth.uid());

CREATE POLICY "Admins manage all profiles"
    ON profiles FOR ALL TO authenticated
    USING (public.get_user_role() = 'ADMIN')
    WITH CHECK (public.get_user_role() = 'ADMIN');

-- ============================================================================
-- 2-9, 14, 16: OPERATIONAL & INTELLIGENCE READ TABLES
-- ============================================================================
CREATE POLICY "Authenticated read customers" ON customers FOR SELECT TO authenticated USING (true);
CREATE POLICY "Admins write customers" ON customers FOR ALL TO authenticated
    USING (public.get_user_role() = 'ADMIN') WITH CHECK (public.get_user_role() = 'ADMIN');

CREATE POLICY "Authenticated read accounts" ON accounts FOR SELECT TO authenticated USING (true);
CREATE POLICY "Admins write accounts" ON accounts FOR ALL TO authenticated
    USING (public.get_user_role() = 'ADMIN') WITH CHECK (public.get_user_role() = 'ADMIN');

CREATE POLICY "Authenticated read transactions" ON transactions FOR SELECT TO authenticated USING (true);
CREATE POLICY "Admins and investigators insert transactions" ON transactions FOR INSERT TO authenticated
    WITH CHECK (public.get_user_role() IN ('ADMIN', 'INVESTIGATOR'));
CREATE POLICY "Admins update transactions" ON transactions FOR UPDATE TO authenticated
    USING (public.get_user_role() = 'ADMIN') WITH CHECK (public.get_user_role() = 'ADMIN');

CREATE POLICY "Authenticated read identity_attributes" ON identity_attributes FOR SELECT TO authenticated USING (true);
CREATE POLICY "Admins write identity_attributes" ON identity_attributes FOR ALL TO authenticated
    USING (public.get_user_role() = 'ADMIN') WITH CHECK (public.get_user_role() = 'ADMIN');

CREATE POLICY "Authenticated read account_relationships" ON account_relationships FOR SELECT TO authenticated USING (true);
CREATE POLICY "Admins write account_relationships" ON account_relationships FOR ALL TO authenticated
    USING (public.get_user_role() = 'ADMIN') WITH CHECK (public.get_user_role() = 'ADMIN');

CREATE POLICY "Authenticated read risk_scores" ON risk_scores FOR SELECT TO authenticated USING (true);
CREATE POLICY "Admins write risk_scores" ON risk_scores FOR ALL TO authenticated
    USING (public.get_user_role() = 'ADMIN') WITH CHECK (public.get_user_role() = 'ADMIN');

CREATE POLICY "Authenticated read risk_factors" ON risk_factors FOR SELECT TO authenticated USING (true);
CREATE POLICY "Admins write risk_factors" ON risk_factors FOR ALL TO authenticated
    USING (public.get_user_role() = 'ADMIN') WITH CHECK (public.get_user_role() = 'ADMIN');

CREATE POLICY "Authenticated read fraud_rules" ON fraud_rules FOR SELECT TO authenticated USING (true);
CREATE POLICY "Admins manage fraud_rules" ON fraud_rules FOR ALL TO authenticated
    USING (public.get_user_role() = 'ADMIN') WITH CHECK (public.get_user_role() = 'ADMIN');

CREATE POLICY "Authenticated read blockchain_records" ON blockchain_records FOR SELECT TO authenticated USING (true);
CREATE POLICY "Investigators and admins insert blockchain_records" ON blockchain_records FOR INSERT TO authenticated
    WITH CHECK (public.get_user_role() IN ('ADMIN', 'INVESTIGATOR'));

CREATE POLICY "Authenticated read network_clusters" ON network_clusters FOR SELECT TO authenticated USING (true);
CREATE POLICY "Admins write network_clusters" ON network_clusters FOR ALL TO authenticated
    USING (public.get_user_role() = 'ADMIN') WITH CHECK (public.get_user_role() = 'ADMIN');

-- ============================================================================
-- 10. ALERTS
-- ============================================================================
CREATE POLICY "Authenticated read alerts" ON alerts FOR SELECT TO authenticated USING (true);
CREATE POLICY "Investigators and admins update alerts" ON alerts FOR UPDATE TO authenticated
    USING (public.get_user_role() IN ('ADMIN', 'INVESTIGATOR'))
    WITH CHECK (public.get_user_role() IN ('ADMIN', 'INVESTIGATOR'));
CREATE POLICY "Admins insert alerts" ON alerts FOR INSERT TO authenticated
    WITH CHECK (public.get_user_role() IN ('ADMIN', 'INVESTIGATOR'));

-- ============================================================================
-- 11. INVESTIGATIONS
-- ============================================================================
CREATE POLICY "Authenticated read investigations" ON investigations FOR SELECT TO authenticated USING (true);
CREATE POLICY "Investigators and admins create investigations" ON investigations FOR INSERT TO authenticated
    WITH CHECK (public.get_user_role() IN ('ADMIN', 'INVESTIGATOR'));
CREATE POLICY "Assigned investigators or admins update investigations" ON investigations FOR UPDATE TO authenticated
    USING (public.get_user_role() = 'ADMIN' OR (public.get_user_role() = 'INVESTIGATOR' AND (investigator_id = auth.uid() OR investigator_id IS NULL)))
    WITH CHECK (public.get_user_role() IN ('ADMIN', 'INVESTIGATOR'));

-- ============================================================================
-- 12. INVESTIGATION ENTITIES
-- ============================================================================
CREATE POLICY "Authenticated read investigation_entities" ON investigation_entities FOR SELECT TO authenticated USING (true);
CREATE POLICY "Investigators and admins manage investigation_entities" ON investigation_entities FOR ALL TO authenticated
    USING (public.get_user_role() IN ('ADMIN', 'INVESTIGATOR'))
    WITH CHECK (public.get_user_role() IN ('ADMIN', 'INVESTIGATOR'));

-- ============================================================================
-- 13. INVESTIGATION NOTES
-- ============================================================================
CREATE POLICY "Authenticated read investigation_notes" ON investigation_notes FOR SELECT TO authenticated USING (true);
CREATE POLICY "Investigators and admins insert investigation_notes" ON investigation_notes FOR INSERT TO authenticated
    WITH CHECK (public.get_user_role() IN ('ADMIN', 'INVESTIGATOR') AND (author_id = auth.uid() OR author_id IS NULL));
CREATE POLICY "Admins manage investigation_notes" ON investigation_notes FOR ALL TO authenticated
    USING (public.get_user_role() = 'ADMIN') WITH CHECK (public.get_user_role() = 'ADMIN');

-- ============================================================================
-- 15. AUDIT LOGS (Immutable Append-Only)
-- ============================================================================
CREATE POLICY "Auditors read audit_logs" ON audit_logs FOR SELECT TO authenticated
    USING (public.get_user_role() IN ('ADMIN', 'INVESTIGATOR', 'ANALYST'));
CREATE POLICY "Authenticated immutable insert audit_logs" ON audit_logs FOR INSERT TO authenticated
    WITH CHECK (true);

-- ============================================================================
-- 17. INGESTION JOBS
-- ============================================================================
CREATE POLICY "Authenticated read ingestion_jobs" ON ingestion_jobs FOR SELECT TO authenticated USING (true);
CREATE POLICY "Investigators and admins manage ingestion_jobs" ON ingestion_jobs FOR ALL TO authenticated
    USING (public.get_user_role() IN ('ADMIN', 'INVESTIGATOR'))
    WITH CHECK (public.get_user_role() IN ('ADMIN', 'INVESTIGATOR'));

-- ============================================================================
-- 18. SYSTEM EVENTS
-- ============================================================================
CREATE POLICY "Auditors read system_events" ON system_events FOR SELECT TO authenticated
    USING (public.get_user_role() IN ('ADMIN', 'INVESTIGATOR', 'ANALYST'));
CREATE POLICY "Admins insert system_events" ON system_events FOR INSERT TO authenticated
    WITH CHECK (public.get_user_role() IN ('ADMIN', 'INVESTIGATOR'));
