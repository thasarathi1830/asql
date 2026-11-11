export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface Customer {
  id: string;
  customer_reference: string;
  name: string;
  email_masked?: string;
  phone_masked?: string;
  country: string;
  identity_hash?: string;
  risk_score: number;
  risk_level: RiskLevel;
  data_source?: string;
}

export interface Account {
  id: string;
  account_number_masked: string;
  customer_id: string;
  account_type: 'SAVINGS' | 'CURRENT' | 'ESCROW' | 'CORPORATE' | 'CRYPTO_WALLET';
  bank_code: string;
  country: string;
  status: 'ACTIVE' | 'SUSPENDED' | 'FROZEN';
  risk_score: number;
  risk_level: RiskLevel;
  is_dormant?: boolean;
  last_activity_at?: string;
}

export interface Transaction {
  id: string;
  transaction_reference: string;
  sender_account_id: string;
  receiver_account_id: string;
  amount: number;
  currency: string;
  transaction_type: string;
  transaction_timestamp: string;
  location?: string;
  device_id?: string;
  ip_hash?: string;
  status?: string;
  blockchain_hash?: string;
  verification_status?: string;
  paysim_is_fraud?: number;
  data_source?: string;
}

export interface Alert {
  id: string;
  entity_type: string;
  entity_id: string;
  alert_type: string;
  severity: RiskLevel;
  title: string;
  description: string;
  evidence?: any;
  status: 'NEW' | 'ASSIGNED' | 'ESCALATED' | 'DISMISSED';
  created_at: string;
  source?: 'ONBOARDING' | 'SCREENING' | 'MONITORING';
}

export interface Investigation {
  id: string;
  case_number: string;
  title: string;
  description: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
  status: 'OPEN' | 'IN_PROGRESS' | 'PENDING_APPROVAL' | 'CLOSED';
  created_at: string;
  assigned_to?: string;
}

export interface GraphNode {
  data: {
    id: string;
    label: string;
    type: 'Account' | 'Customer' | 'Device' | 'IP';
    riskScore: number;
    riskLevel: RiskLevel;
    bankCode?: string;
    accountType?: string;
    betweenness?: number;
    isHub?: boolean;
  };
}

export interface GraphEdge {
  data: {
    id: string;
    source: string;
    target: string;
    amount?: number;
    weight?: number;
    type: string;
    isCycle?: boolean;
    timestamp?: string;
  };
}

export interface OnboardingAssessment {
  onboarding_score: number;
  risk_level: RiskLevel;
  decision: 'APPROVE' | 'ENHANCED_DUE_DILIGENCE' | 'MANUAL_REVIEW' | 'ESCALATE';
  checks: Array<{
    rule_id: string;
    name: string;
    score: number;
    max_score: number;
    reason: string;
    evidence: any;
  }>;
  matched_entities: Array<{
    attribute_type: string;
    attribute_value_masked: string;
    matched_customer_id: string;
  }>;
  assessed_at: string;
}

export interface ScreeningDecision {
  transaction_reference: string;
  sender_account_id: string;
  receiver_account_id: string;
  amount: number;
  currency: string;
  decision: 'ALLOW' | 'ALLOW_WITH_MONITORING' | 'HOLD_FOR_REVIEW' | 'BLOCK';
  risk_score: number;
  rules_triggered: Array<{
    rule_id: string;
    name: string;
    score: number;
    severity: string;
    reason: string;
    evidence: any;
  }>;
  reasons: string[];
  latency_ms: number;
  evaluated_at: string;
}

