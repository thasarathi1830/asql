-- ============================================================================
-- PHANTOM — Pre-Seeded Case Study: Operation Phantom Ring + 8 Fraud Rules
-- ============================================================================

-- 1. Seed all 8 Explainable Fraud Rules
INSERT INTO fraud_rules (rule_id, name, description, default_weight, severity, is_active) VALUES
('RULE_001', 'Circular Money Flow', 'Johnson elementary cycle detection & recursive CTE closed-loop funds movement (A->B->C->A) within 72h', 25.00, 'CRITICAL', TRUE),
('RULE_002', 'Rapid Pass-Through / Mule', 'Inflows drained >85-90% within 120 minutes with <=10% retained balance', 20.00, 'HIGH', TRUE),
('RULE_003', 'Transaction Structuring (Smurfing)', 'Clusters of >=3 transfers in sub-reporting threshold bands within 24h windows', 20.00, 'HIGH', TRUE),
('RULE_004', 'Dormant Account Surge', 'Account dormant >60 days followed by sudden high-value burst transfer >= Rs.100,000', 15.00, 'MEDIUM', TRUE),
('RULE_005', 'Shared Identity Cluster', 'Hardware device fingerprint, IP, phone, or email collisions across distinct accounts/customers', 15.00, 'HIGH', TRUE),
('RULE_006', 'High Network Centrality', 'Structural intermediary hub with Betweenness Centrality >0.40 or Degree >=10', 15.00, 'HIGH', TRUE),
('RULE_007', 'Suspicious Counterparty Association', 'Direct transfers to/from previously flagged high-risk or fraud accounts', 15.00, 'MEDIUM', TRUE),
('RULE_008', 'Velocity Anomaly', 'Transaction frequency spiking >400% over 30-day rolling baseline', 10.00, 'MEDIUM', TRUE)
ON CONFLICT (rule_id) DO NOTHING;

-- 2. Seed Operation Phantom Ring Customers
INSERT INTO customers (id, customer_reference, name, email_masked, phone_masked, country, identity_hash, risk_score, risk_level) VALUES
('11111111-1111-4111-8111-000000000001', 'C001', 'Devraj Singhania', 'd***@singhania-holdings.in', '+91-98***-***01', 'IN', 'a1b2c3d4e5f60001a1b2c3d4e5f60001a1b2c3d4e5f60001a1b2c3d4e5f60001', 94.00, 'CRITICAL'),
('11111111-1111-4111-8111-000000000002', 'C002', 'Rohan Malhotra', 'r***@malhotra-ventures.in', '+91-98***-***02', 'IN', 'b2c3d4e5f6a10002b2c3d4e5f6a10002b2c3d4e5f6a10002b2c3d4e5f6a10002', 88.00, 'CRITICAL'),
('11111111-1111-4111-8111-000000000003', 'C003', 'Vikramaditya Mehta', 'v***@mehta-exports.in', '+91-98***-***03', 'IN', 'c3d4e5f6a1b20003c3d4e5f6a1b20003c3d4e5f6a1b20003c3d4e5f6a1b20003', 86.00, 'CRITICAL')
ON CONFLICT (customer_reference) DO NOTHING;

-- 3. Seed Operation Phantom Ring Accounts
INSERT INTO accounts (id, account_number_masked, customer_id, account_type, bank_code, country, status, risk_score, risk_level, is_dormant, last_activity_at) VALUES
('22222222-2222-4222-8222-000000000001', 'ACC-0001-9041', '11111111-1111-4111-8111-000000000001', 'CURRENT', 'HDFC', 'IN', 'ACTIVE', 94.00, 'CRITICAL', FALSE, '2026-06-15T14:15:00Z'),
('22222222-2222-4222-8222-000000000002', 'ACC-0044-7721', '11111111-1111-4111-8111-000000000002', 'SAVINGS', 'ICICI', 'IN', 'ACTIVE', 92.00, 'CRITICAL', FALSE, '2026-06-15T12:00:00Z'),
('22222222-2222-4222-8222-000000000003', 'ACC-0078-3319', '11111111-1111-4111-8111-000000000003', 'SAVINGS', 'SBI', 'IN', 'ACTIVE', 90.00, 'CRITICAL', FALSE, '2026-06-15T14:15:00Z')
ON CONFLICT (account_number_masked) DO NOTHING;

-- 4. Seed Operation Phantom Ring 3-Hop RTGS Transactions (4.25 hours, Rs.1,415,000)
INSERT INTO transactions (id, transaction_reference, sender_account_id, receiver_account_id, amount, currency, transaction_type, transaction_timestamp, location, device_id, ip_hash, status, blockchain_hash, verification_status) VALUES
('33333333-3333-4333-8333-000000000001', 'TX-PHANTOM-001', '22222222-2222-4222-8222-000000000001', '22222222-2222-4222-8222-000000000002', 480000.00, 'INR', 'RTGS', '2026-06-15T10:00:00Z', 'Mumbai, IN', 'DEV-ORIGIN-001', 'ip_hash_phantom_01', 'FLAGGED', '0x1a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f801', 'VERIFIED'),
('33333333-3333-4333-8333-000000000002', 'TX-PHANTOM-002', '22222222-2222-4222-8222-000000000002', '22222222-2222-4222-8222-000000000003', 470000.00, 'INR', 'RTGS', '2026-06-15T11:45:00Z', 'Delhi, IN', 'DEV-PHANTOM-103', 'ip_hash_phantom_02', 'FLAGGED', '0x2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f80902', 'VERIFIED'),
('33333333-3333-4333-8333-000000000003', 'TX-PHANTOM-003', '22222222-2222-4222-8222-000000000003', '22222222-2222-4222-8222-000000000001', 465000.00, 'INR', 'RTGS', '2026-06-15T14:15:00Z', 'Bengaluru, IN', 'DEV-PHANTOM-103', 'ip_hash_phantom_02', 'FLAGGED', '0x3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f8091a03', 'VERIFIED')
ON CONFLICT (transaction_reference) DO NOTHING;

-- 5. Seed Shared Hardware Device DEV-PHANTOM-103 Collision
INSERT INTO identity_attributes (id, customer_id, attribute_type, attribute_hash, attribute_value_masked, confidence) VALUES
('44444444-4444-4444-8444-000000000001', '11111111-1111-4111-8111-000000000002', 'DEVICE', 'dev_hash_phantom_103', 'DEV-PHANTOM-103', 1.00),
('44444444-4444-4444-8444-000000000002', '11111111-1111-4111-8111-000000000003', 'DEVICE', 'dev_hash_phantom_103', 'DEV-PHANTOM-103', 1.00),
('44444444-4444-4444-8444-000000000003', '11111111-1111-4111-8111-000000000002', 'IP', 'ip_hash_phantom_02', '103.21.***.44', 0.95),
('44444444-4444-4444-8444-000000000004', '11111111-1111-4111-8111-000000000003', 'IP', 'ip_hash_phantom_02', '103.21.***.44', 0.95)
ON CONFLICT DO NOTHING;

-- 6. Seed Account Relationships
INSERT INTO account_relationships (source_account_id, target_account_id, relationship_type, confidence, evidence_count, metadata) VALUES
('22222222-2222-4222-8222-000000000002', '22222222-2222-4222-8222-000000000003', 'SHARED_DEVICE', 1.00, 1, '{"device_id": "DEV-PHANTOM-103"}'),
('22222222-2222-4222-8222-000000000001', '22222222-2222-4222-8222-000000000002', 'CIRCULAR_FLOW', 0.98, 1, '{"cycle": "ACC-0001-9041 -> ACC-0044-7721 -> ACC-0078-3319 -> ACC-0001-9041"}'),
('22222222-2222-4222-8222-000000000002', '22222222-2222-4222-8222-000000000003', 'RAPID_PASS_THROUGH', 0.96, 1, '{"delay_minutes": 105, "retained_ratio": 0.0208}')
ON CONFLICT (source_account_id, target_account_id, relationship_type) DO NOTHING;

-- 7. Seed Risk Score & Risk Factors (94.0 CRITICAL)
INSERT INTO risk_scores (id, entity_type, entity_id, score, risk_level, reasons) VALUES
('55555555-5555-4555-8555-000000000001', 'ACCOUNT', '22222222-2222-4222-8222-000000000001', 94.00, 'CRITICAL',
 '["RULE_001: 3-hop circular flow (Rs.1,415,000 in 4.25h)", "RULE_002: Rapid pass-through (>97% drained within 2h)", "RULE_003: Structuring just below Rs.5L threshold", "RULE_005: Shared device DEV-PHANTOM-103", "RULE_006: Betweenness centrality 0.810"]'::jsonb)
ON CONFLICT DO NOTHING;

INSERT INTO risk_factors (risk_score_id, rule_id, rule_name, severity, weight, evidence) VALUES
('55555555-5555-4555-8555-000000000001', 'RULE_001', 'Circular Money Flow', 'CRITICAL', 25.00, '{"cycle_length": 3, "duration_hours": 4.25, "total_volume": 1415000}'::jsonb),
('55555555-5555-4555-8555-000000000001', 'RULE_002', 'Rapid Pass-Through / Mule', 'HIGH', 20.00, '{"delay_minutes": 105, "drain_ratio": 0.979}'::jsonb),
('55555555-5555-4555-8555-000000000001', 'RULE_003', 'Transaction Structuring (Smurfing)', 'HIGH', 20.00, '{"amounts": [480000, 470000, 465000], "band": "450K-500K"}'::jsonb),
('55555555-5555-4555-8555-000000000001', 'RULE_005', 'Shared Identity Cluster', 'HIGH', 14.00, '{"shared_device": "DEV-PHANTOM-103", "accounts": ["ACC-0044-7721", "ACC-0078-3319"]}'::jsonb),
('55555555-5555-4555-8555-000000000001', 'RULE_006', 'High Network Centrality', 'HIGH', 15.00, '{"betweenness": 0.810, "is_hub": true}'::jsonb)
ON CONFLICT DO NOTHING;

-- 8. Seed Alert & Investigation INV-2026-PHANTOM-001
INSERT INTO alerts (id, entity_type, entity_id, alert_type, severity, title, description, evidence, status) VALUES
('66666666-6666-4666-8666-000000000001', 'NETWORK', '22222222-2222-4222-8222-000000000001', 'CIRCULAR_RING', 'CRITICAL',
 'Operation Phantom Ring: 3-Hop Circular Flow (Rs.1.415M)',
 'Detected closed 3-hop RTGS laundering cycle between ACC-0001-9041, ACC-0044-7721, and ACC-0078-3319 within 4.25 hours with shared hardware device DEV-PHANTOM-103.',
 '{"score": 94.0, "device_id": "DEV-PHANTOM-103", "total_volume": 1415000}'::jsonb, 'ESCALATED')
ON CONFLICT DO NOTHING;

INSERT INTO investigations (id, case_number, title, description, priority, status) VALUES
('77777777-7777-4777-8777-000000000001', 'INV-2026-PHANTOM-001', 'Operation Phantom Ring — Multi-Bank RTGS Laundering Ring',
 'Assigned to Agent Vikram Rathore (FIU Taskforce). Coordinated 3-hop circular RTGS ring cycling Rs.1,415,000 across HDFC, ICICI, and SBI within 4.25 hours using shared device DEV-PHANTOM-103.',
 'URGENT', 'IN_PROGRESS')
ON CONFLICT (case_number) DO NOTHING;

INSERT INTO investigation_entities (investigation_id, entity_type, entity_id, notes) VALUES
('77777777-7777-4777-8777-000000000001', 'ACCOUNT', '22222222-2222-4222-8222-000000000001', 'Origin/return node ACC-0001-9041 (Devraj Singhania, HDFC)'),
('77777777-7777-4777-8777-000000000001', 'ACCOUNT', '22222222-2222-4222-8222-000000000002', 'Mule relay ACC-0044-7721 (ICICI) sharing DEV-PHANTOM-103'),
('77777777-7777-4777-8777-000000000001', 'ACCOUNT', '22222222-2222-4222-8222-000000000003', 'Mule relay ACC-0078-3319 (SBI) sharing DEV-PHANTOM-103')
ON CONFLICT (investigation_id, entity_type, entity_id) DO NOTHING;

INSERT INTO investigation_notes (investigation_id, content) VALUES
('77777777-7777-4777-8777-000000000001', '[Agent Vikram Rathore - FIU Taskforce] Initial triage confirmed 3-hop RTGS cycle completed in 4.25 hours with shared hardware fingerprint DEV-PHANTOM-103. Escalated for asset freeze and SAR filing.')
ON CONFLICT DO NOTHING;

INSERT INTO network_clusters (id, cluster_name, entity_ids, risk_score, description) VALUES
('88888888-8888-4888-8888-000000000001', 'Operation Phantom Ring',
 '["22222222-2222-4222-8222-000000000001", "22222222-2222-4222-8222-000000000002", "22222222-2222-4222-8222-000000000003"]'::jsonb,
 94.00, '3-hop circular RTGS ring (Rs.1,415,000) linked by DEV-PHANTOM-103')
ON CONFLICT DO NOTHING;
