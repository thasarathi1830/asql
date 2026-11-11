import React, { useState, useEffect, useRef } from 'react';
import cytoscape, { Core } from 'cytoscape';
import {
  UserPlus,
  ShieldCheck,
  ShieldAlert,
  Lock,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCcw,
  Sparkles,
} from 'lucide-react';
import { RiskBadge } from '../components/ui/RiskBadge';

export const NewCustomer: React.FC = () => {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [assessmentResult, setAssessmentResult] = useState<any>(null);

  // Form State
  const [customerRef, setCustomerRef] = useState('CUST-NEW-108');
  const [fullName, setFullName] = useState('Vikramaditya Mehta');
  const [dob, setDob] = useState('1988-04-12');
  const [email, setEmail] = useState('v.mehta@exports-asia.in');
  const [phone, setPhone] = useState('+919820199203');
  const [country, setCountry] = useState('IN');
  const [income, setIncome] = useState('250000');
  const [customerType, setCustomerType] = useState('INDIVIDUAL');
  const [accountNumber, setAccountNumber] = useState('ACC-9921-4412');
  const [accountType, setAccountType] = useState('SAVINGS');
  const [bankCode, setBankCode] = useState('HDFC');
  const [deviceId, setDeviceId] = useState('DEV-PHANTOM-103');
  const [ipAddress, setIpAddress] = useState('103.21.244.12');

  const miniCyRef = useRef<HTMLDivElement>(null);
  const cyInstance = useRef<Core | null>(null);

  const handleLoadClean = () => {
    setCustomerRef('CUST-CLEAN-992');
    setFullName('Ananya Deshmukh');
    setDob('1994-09-18');
    setEmail('ananya.deshmukh@cleanmail.in');
    setPhone('+919876500112');
    setCountry('IN');
    setIncome('180000');
    setCustomerType('INDIVIDUAL');
    setAccountNumber('ACC-8832-1002');
    setAccountType('SAVINGS');
    setBankCode('SBI');
    setDeviceId('DEV-CLEAN-UNIQUE-77');
    setIpAddress('14.139.122.45');
    setAssessmentResult(null);
  };

  const handleLoadSuspicious = () => {
    setCustomerRef('CUST-SUSP-771');
    setFullName('Rajesh Kumar (Alias)');
    setDob('1985-11-23');
    setEmail('r.kumar@disposable-temp.com');
    setPhone('+919820011223');
    setCountry('IN');
    setIncome('25000');
    setCustomerType('BUSINESS');
    setAccountNumber('ACC-0044-7721');
    setAccountType('CURRENT');
    setBankCode('ICICI');
    setDeviceId('DEV-PHANTOM-103'); // Known Phantom Ring device
    setIpAddress('103.21.244.12');
    setAssessmentResult(null);
  };

  const handleAssess = () => {
    setLoading(true);
    setTimeout(() => {
      const isSuspicious = deviceId.includes('PHANTOM') || email.includes('disposable') || income === '25000';
      const score = isSuspicious ? 65.0 : 10.0;
      const decision = isSuspicious ? 'MANUAL_REVIEW' : 'APPROVE';
      const riskLevel = isSuspicious ? 'HIGH' : 'LOW';

      const checks = [];
      if (deviceId.includes('PHANTOM')) {
        checks.push({
          rule_id: 'ONB_001',
          name: 'Shared Device / IP with Existing Accounts',
          score: 30.0,
          reason: 'Hardware fingerprint DEV-PHANTOM-103 matches Operation Phantom Ring',
          evidence: { match_type: 'DEVICE_FINGERPRINT', collision_count: 2 },
        });
        checks.push({
          rule_id: 'ONB_002',
          name: 'Linked to Flagged / Investigated Entities',
          score: 30.0,
          reason: 'Entity shares identifiers with active case INV-2026-PHANTOM-001',
          evidence: { case: 'INV-2026-PHANTOM-001' },
        });
      }
      if (email.includes('disposable')) {
        checks.push({
          rule_id: 'ONB_006',
          name: 'Data Quality and Consistency',
          score: 5.0,
          reason: 'Disposable or temporary email provider detected',
          evidence: { domain: 'disposable-temp.com' },
        });
      }

      const res = {
        customer_reference: customerRef,
        onboarding_score: score,
        risk_level: riskLevel,
        decision,
        checks,
        matched_entities: isSuspicious
          ? [
              {
                attribute_type: 'DEVICE',
                attribute_value_masked: 'DEV-PH***103',
                matched_account: 'ACC-0044-7721',
                customer_name: 'Devraj Singhania (C001)',
              },
              {
                attribute_type: 'IP_HASH',
                attribute_value_masked: '103.21.***.12',
                matched_account: 'ACC-0078-3319',
                customer_name: 'Rohan Malhotra (C002)',
              },
            ]
          : [],
        assessed_at: new Date().toISOString(),
      };

      setAssessmentResult(res);
      setLoading(false);
      setStep(5);
    }, 450);
  };

  // Render mini Cytoscape cluster when assessment completes
  useEffect(() => {
    if (step === 5 && miniCyRef.current && assessmentResult) {
      const isSuspicious = assessmentResult.decision !== 'APPROVE';
      const elements: any[] = [
        {
          data: {
            id: 'new_cust',
            label: `NEW: ${fullName}`,
            type: 'NEW',
            color: isSuspicious ? '#f43f5e' : '#10b981',
          },
        },
      ];

      if (isSuspicious) {
        elements.push(
          {
            data: {
              id: 'dev_node',
              label: 'DEV-PHANTOM-103',
              type: 'DEVICE',
              color: '#06b6d4',
            },
          },
          {
            data: {
              id: 'phantom_c1',
              label: 'C001: Devraj Singhania',
              type: 'EXISTING',
              color: '#f43f5e',
            },
          },
          {
            data: {
              id: 'phantom_c2',
              label: 'C002: Rohan Malhotra',
              type: 'EXISTING',
              color: '#f43f5e',
            },
          },
          { data: { id: 'e1', source: 'new_cust', target: 'dev_node', label: 'SHARES_DEVICE' } },
          { data: { id: 'e2', source: 'dev_node', target: 'phantom_c1', label: 'SHARED' } },
          { data: { id: 'e3', source: 'dev_node', target: 'phantom_c2', label: 'SHARED' } }
        );
      }

      const cy = cytoscape({
        container: miniCyRef.current,
        elements,
        style: [
          {
            selector: 'node',
            style: {
              'background-color': 'data(color)',
              label: 'data(label)',
              color: '#f1f5f9',
              'font-size': '10px',
              'font-family': 'monospace',
              'text-valign': 'bottom',
              'text-margin-y': 4,
              width: 24,
              height: 24,
            },
          },
          {
            selector: 'edge',
            style: {
              width: 2,
              'line-color': '#06b6d4',
              'line-style': 'dashed',
              'target-arrow-shape': 'none',
              label: 'data(label)',
              'font-size': '8px',
              'font-family': 'monospace',
              color: '#94a3b8',
            },
          },
        ],
        layout: {
          name: 'circle',
          padding: 20,
        },
      });
      cyInstance.current = cy;
      return () => {
        cy.destroy();
      };
    }
  }, [step, assessmentResult, fullName]);

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header & Sample Loaders */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-phantom-border">
        <div>
          <div className="flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-cyan-400" />
            <h2 className="text-lg font-bold font-mono text-slate-100">New Customer Onboarding & Screening</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Pre-onboarding linkage analysis & identity collision screening (ONB_001 – ONB_007)
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleLoadClean}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 hover:bg-slate-800 text-slate-300 text-xs font-mono transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5 text-emerald-400" /> Load Clean Example
          </button>
          <button
            onClick={handleLoadSuspicious}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-950/40 border border-rose-500/30 hover:bg-rose-900/40 text-rose-300 text-xs font-mono font-bold transition-colors"
          >
            <AlertTriangle className="w-3.5 h-3.5 text-rose-400" /> Load Suspicious Example
          </button>
        </div>
      </div>

      {/* Stepper Navigation */}
      <div className="flex items-center justify-between bg-phantom-surface border border-phantom-border rounded-xl p-3 text-xs font-mono">
        {[
          { num: 1, label: '1. Customer' },
          { num: 2, label: '2. Accounts' },
          { num: 3, label: '3. Identity & Device' },
          { num: 4, label: '4. Privacy Shield' },
          { num: 5, label: '5. Assessment Result' },
        ].map((s) => (
          <button
            key={s.num}
            onClick={() => setStep(s.num)}
            className={`px-3 py-1 rounded transition-colors ${
              step === s.num
                ? 'bg-cyan-500 text-slate-950 font-bold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* Wizard Steps */}
      <div className="bg-phantom-surface border border-phantom-border rounded-xl p-6 shadow-xl">
        {step === 1 && (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-slate-200 font-mono">Step 1: Customer Demographics</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Customer Reference ID</label>
                <input
                  type="text"
                  value={customerRef}
                  onChange={(e) => setCustomerRef(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Full Legal Name</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200"
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Date of Birth</label>
                <input
                  type="date"
                  value={dob}
                  onChange={(e) => setDob(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Country (ISO-2)</label>
                <input
                  type="text"
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Declared Monthly Income (INR)</label>
                <input
                  type="number"
                  value={income}
                  onChange={(e) => setIncome(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Customer Entity Type</label>
                <select
                  value={customerType}
                  onChange={(e) => setCustomerType(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 font-mono"
                >
                  <option value="INDIVIDUAL">INDIVIDUAL</option>
                  <option value="BUSINESS">BUSINESS / CORPORATE</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end pt-4">
              <button
                onClick={() => setStep(2)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs font-mono"
              >
                Next: Accounts <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-slate-200 font-mono">Step 2: Associated Bank Account(s)</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Account Number</label>
                <input
                  type="text"
                  value={accountNumber}
                  onChange={(e) => setAccountNumber(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Account Type</label>
                <select
                  value={accountType}
                  onChange={(e) => setAccountType(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 font-mono"
                >
                  <option value="SAVINGS">SAVINGS</option>
                  <option value="CURRENT">CURRENT</option>
                  <option value="ESCROW">ESCROW (High-Risk)</option>
                  <option value="CRYPTO_WALLET">CRYPTO_WALLET (High-Risk)</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Bank Code</label>
                <input
                  type="text"
                  value={bankCode}
                  onChange={(e) => setBankCode(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 font-mono"
                />
              </div>
            </div>
            <div className="flex justify-between pt-4">
              <button
                onClick={() => setStep(1)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-slate-800 text-slate-300 text-xs font-mono"
              >
                <ArrowLeft className="w-4 h-4" /> Back
              </button>
              <button
                onClick={() => setStep(3)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs font-mono"
              >
                Next: Identity & Device <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-slate-200 font-mono">Step 3: Identity & Device Signals</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Hardware Device ID</label>
                <input
                  type="text"
                  value={deviceId}
                  onChange={(e) => setDeviceId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">IP Address</label>
                <input
                  type="text"
                  value={ipAddress}
                  onChange={(e) => setIpAddress(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Email Address</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200"
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Phone Number</label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 font-mono"
                />
              </div>
            </div>
            <div className="flex justify-between pt-4">
              <button
                onClick={() => setStep(2)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-slate-800 text-slate-300 text-xs font-mono"
              >
                <ArrowLeft className="w-4 h-4" /> Back
              </button>
              <button
                onClick={() => setStep(4)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs font-mono"
              >
                Next: Review Privacy Shield <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {step === 4 && (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-slate-200 font-mono">Step 4: Privacy Shield Verification</h3>
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
              <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold font-mono">
                <Lock className="w-4 h-4" />
                ZERO-PII COMMITMENT ACTIVE
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Raw emails, phone numbers, and IP addresses are masked and hashed before ingestion. Only salted SHA-256 digests are compared against existing network identity clusters.
              </p>
              <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-2 border-t border-slate-800">
                <div className="text-slate-400">Masked Email: <span className="text-slate-200">{email.slice(0, 2)}***@{email.split('@')[1] || 'mail.in'}</span></div>
                <div className="text-slate-400">Masked Phone: <span className="text-slate-200">{phone.slice(0, 5)}***{phone.slice(-2)}</span></div>
                <div className="text-slate-400">Device Hash: <span className="text-cyan-400">SHA256(DEV-...)</span></div>
                <div className="text-slate-400">IP Hash: <span className="text-cyan-400">SHA256(IP-...)</span></div>
              </div>
            </div>

            <div className="flex justify-between pt-4">
              <button
                onClick={() => setStep(3)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-slate-800 text-slate-300 text-xs font-mono"
              >
                <ArrowLeft className="w-4 h-4" /> Back
              </button>
              <button
                onClick={handleAssess}
                disabled={loading}
                className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs font-mono transition-all shadow-lg shadow-cyan-500/20"
              >
                <Play className="w-4 h-4" />
                {loading ? 'Executing Onboarding Assessment...' : 'Run Onboarding Assessment'}
              </button>
            </div>
          </div>
        )}

        {step === 5 && assessmentResult && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-slate-900 border border-phantom-border">
              <div>
                <span className="text-xs font-mono text-slate-400">ONBOARDING ASSESSMENT FOR</span>
                <h3 className="text-lg font-bold font-mono text-slate-100">{fullName} ({customerRef})</h3>
              </div>
              <div className="flex items-center gap-3">
                <RiskBadge level={assessmentResult.risk_level} score={assessmentResult.onboarding_score} size="lg" />
                <span
                  className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold border ${
                    assessmentResult.decision === 'APPROVE'
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                      : assessmentResult.decision === 'MANUAL_REVIEW'
                      ? 'bg-orange-500/10 text-orange-400 border-orange-500/30'
                      : 'bg-rose-500/10 text-rose-400 border-rose-500/30 animate-pulse'
                  }`}
                >
                  DECISION: {assessmentResult.decision}
                </span>
              </div>
            </div>

            {/* Split View: Triggered Rules & Mini Cytoscape Graph */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Rules & Evidence */}
              <div className="space-y-3">
                <h4 className="text-xs font-mono uppercase text-slate-400">Triggered Onboarding Checks</h4>
                {assessmentResult.checks.length > 0 ? (
                  assessmentResult.checks.map((c: any) => (
                    <div key={c.rule_id} className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-rose-400 font-mono">{c.rule_id}: {c.name}</span>
                        <span className="text-xs font-mono font-bold text-slate-300">+{c.score} pts</span>
                      </div>
                      <p className="text-xs text-slate-300">{c.reason}</p>
                    </div>
                  ))
                ) : (
                  <div className="p-4 rounded-lg bg-emerald-950/20 border border-emerald-500/30 text-emerald-400 text-xs font-mono flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4" /> Zero identity collisions or fraud links detected.
                  </div>
                )}
              </div>

              {/* Mini Cluster Graph */}
              <div className="space-y-3">
                <h4 className="text-xs font-mono uppercase text-slate-400">Identity Cluster Visualizer</h4>
                <div
                  ref={miniCyRef}
                  className="w-full h-64 bg-slate-950 rounded-xl border border-phantom-border"
                />
              </div>
            </div>

            <div className="flex justify-between pt-4 border-t border-phantom-border">
              <button
                onClick={() => setStep(1)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-slate-800 text-slate-300 text-xs font-mono"
              >
                <RotateCcw className="w-3.5 h-3.5" /> Start New Assessment
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

