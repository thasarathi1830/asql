import React, { useState } from 'react';
import { demoTransactions } from '../lib/demoData';
import { SearchBar } from '../components/ui/SearchBar';
import { ArrowLeftRight, ShieldCheck, ShieldAlert, Cpu, Zap, Play, CheckCircle2, AlertOctagon } from 'lucide-react';
import { formatHash } from '../lib/blockchainVerifier';
import { Link } from 'react-router-dom';

export const Transactions: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [page, setPage] = useState(1);
  const pageSize = 15;

  // Screening interactive state
  const [isScreeningOpen, setIsScreeningOpen] = useState(true);
  const [senderInput, setSenderInput] = useState('ACC-0001-9041');
  const [receiverInput, setReceiverInput] = useState('ACC-0044-7721');
  const [amountInput, setAmountInput] = useState('480000');
  const [deviceInput, setDeviceInput] = useState('DEV-PHANTOM-103');
  const [screenResult, setScreenResult] = useState<any>(null);
  const [isScreeningLoading, setIsScreeningLoading] = useState(false);

  const handleScreenSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsScreeningLoading(true);
    const amt = parseFloat(amountInput) || 0;

    // Simulate sub-500ms screening evaluation
    setTimeout(() => {
      const isRing = (senderInput.includes('ACC-0001') && receiverInput.includes('ACC-0044')) || amt >= 450000;
      const decision = isRing ? 'HOLD_FOR_REVIEW' : amt > 200000 ? 'ALLOW_WITH_MONITORING' : 'ALLOW';
      const riskScore = isRing ? 65.0 : amt > 200000 ? 35.0 : 5.0;

      const rules = [];
      if (isRing) {
        rules.push({
          rule_id: 'RULE_001',
          name: 'Circular Money Flow (Cycle Closure)',
          score: 25.0,
          reason: 'Transaction closes 3-hop circular RTGS loop',
        });
        if (deviceInput.includes('DEV-PHANTOM-103')) {
          rules.push({
            rule_id: 'RULE_005',
            name: 'Shared Identity / Device Collision',
            score: 15.0,
            reason: 'Hardware fingerprint collision with DEV-PHANTOM-103',
          });
        }
      }

      setScreenResult({
        transaction_reference: `TX-SCR-${Date.now().toString().slice(-6)}`,
        decision,
        risk_score: riskScore,
        latency_ms: 0.18,
        rules,
        evaluated_at: new Date().toISOString(),
      });
      setIsScreeningLoading(false);
    }, 120);
  };

  // Filter transactions
  const filtered = demoTransactions.filter((tx) => {
    if (typeFilter !== 'ALL' && tx.transaction_type !== typeFilter) return false;
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      return (
        tx.transaction_reference.toLowerCase().includes(q) ||
        tx.sender_account_id.toLowerCase().includes(q) ||
        tx.receiver_account_id.toLowerCase().includes(q) ||
        (tx.blockchain_hash && tx.blockchain_hash.toLowerCase().includes(q))
      );
    }
    return true;
  });

  const totalPages = Math.ceil(filtered.length / pageSize);
  const pageItems = filtered.slice((page - 1) * pageSize, page * pageSize);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Real-Time Pre-Transaction Screening Panel */}
      <div className="bg-phantom-surface border border-cyan-500/30 rounded-xl p-6 shadow-xl relative overflow-hidden">
        <div className="flex items-center justify-between pb-4 border-b border-phantom-border">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-cyan-400" />
            <h2 className="text-base font-bold text-slate-100 font-mono tracking-tight">
              Pre-Transaction Real-Time AML Screener
            </h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-500/20 text-cyan-300">
              TARGET &lt; 500ms
            </span>
          </div>
          <button
            onClick={() => setIsScreeningOpen(!isScreeningOpen)}
            className="text-xs font-mono text-cyan-400 hover:underline"
          >
            {isScreeningOpen ? 'Collapse Panel' : 'Expand Panel'}
          </button>
        </div>

        {isScreeningOpen && (
          <div className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Form */}
            <form onSubmit={handleScreenSubmit} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-mono text-slate-400 mb-1">Sender Account</label>
                  <input
                    type="text"
                    value={senderInput}
                    onChange={(e) => setSenderInput(e.target.value)}
                    required
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-mono text-slate-400 mb-1">Receiver Account</label>
                  <input
                    type="text"
                    value={receiverInput}
                    onChange={(e) => setReceiverInput(e.target.value)}
                    required
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 font-mono"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-mono text-slate-400 mb-1">Amount (INR)</label>
                  <input
                    type="number"
                    value={amountInput}
                    onChange={(e) => setAmountInput(e.target.value)}
                    required
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-mono text-slate-400 mb-1">Device Fingerprint</label>
                  <input
                    type="text"
                    value={deviceInput}
                    onChange={(e) => setDeviceInput(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 font-mono"
                  />
                </div>
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="submit"
                  disabled={isScreeningLoading}
                  className="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-colors"
                >
                  <Play className="w-3.5 h-3.5" />
                  {isScreeningLoading ? 'Simulating Graph Path...' : 'Screen Payment in Real-Time'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setSenderInput('ACC-BENIGN-001');
                    setReceiverInput('ACC-BENIGN-002');
                    setAmountInput('15000');
                    setDeviceInput('DEV-CLEAN-01');
                  }}
                  className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono"
                >
                  Load Clean
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setSenderInput('ACC-0001-9041');
                    setReceiverInput('ACC-0044-7721');
                    setAmountInput('480000');
                    setDeviceInput('DEV-PHANTOM-103');
                  }}
                  className="px-3 py-2 rounded-lg bg-rose-950/40 border border-rose-500/30 hover:bg-rose-900/40 text-rose-300 text-xs font-mono"
                >
                  Load Ring
                </button>
              </div>
            </form>

            {/* Live Result View */}
            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-4 flex flex-col justify-between">
              {screenResult ? (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-slate-400">DECISION:</span>
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-mono font-bold border ${
                        screenResult.decision === 'HOLD_FOR_REVIEW'
                          ? 'bg-rose-500/10 text-rose-400 border-rose-500/30 animate-pulse'
                          : screenResult.decision === 'ALLOW_WITH_MONITORING'
                          ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                          : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                      }`}
                    >
                      {screenResult.decision}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-400">Latency:</span>
                    <span className="text-cyan-400 font-bold">{screenResult.latency_ms} ms</span>
                  </div>
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-400">Simulated Risk Score:</span>
                    <span className="text-slate-200 font-bold">{screenResult.risk_score} / 100</span>
                  </div>

                  <div className="pt-2 border-t border-slate-800">
                    <span className="text-[11px] font-mono text-slate-400 uppercase">Triggered Rules:</span>
                    {screenResult.rules.length > 0 ? (
                      <div className="mt-1 space-y-1">
                        {screenResult.rules.map((r: any) => (
                          <div key={r.rule_id} className="text-xs text-rose-300 font-mono flex items-center gap-1.5">
                            <AlertOctagon className="w-3.5 h-3.5" />
                            {r.rule_id}: {r.reason} (+{r.score} pts)
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-emerald-400 font-mono mt-1 flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Cleared real-time graph checks
                      </p>
                    )}
                  </div>
                </div>
              ) : (
                <div className="h-full flex items-center justify-center text-xs font-mono text-slate-500">
                  Ready to screen payment. Fill form and click Screen.
                </div>
              )}

              {screenResult?.decision === 'HOLD_FOR_REVIEW' && (
                <div className="mt-3 pt-3 border-t border-slate-800 flex gap-2">
                  <Link
                    to="/investigations/INV-2026-PHANTOM-001"
                    className="flex-1 py-1.5 text-center rounded bg-rose-600 hover:bg-rose-500 text-slate-950 font-bold text-xs font-mono"
                  >
                    Open Investigation Ticket
                  </Link>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Main Ledger Table */}
      <div className="bg-phantom-surface border border-phantom-border rounded-xl p-6 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-phantom-border">
          <div className="flex-1 min-w-[280px] max-w-md">
            <SearchBar value={searchTerm} onChange={setSearchTerm} placeholder="Search tx ref or hash..." />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-slate-400">Type:</span>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="bg-slate-900 border border-phantom-border rounded-lg px-3 py-1.5 text-xs text-slate-200 font-mono"
            >
              <option value="ALL">ALL TYPES</option>
              <option value="RTGS">RTGS</option>
              <option value="NEFT">NEFT</option>
              <option value="UPI">UPI</option>
              <option value="WIRE">WIRE</option>
            </select>
          </div>
        </div>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-900/60 text-slate-400 border-b border-phantom-border">
              <tr>
                <th className="py-3 px-4">TX REFERENCE</th>
                <th className="py-3 px-4">SENDER</th>
                <th className="py-3 px-4">RECEIVER</th>
                <th className="py-3 px-4">AMOUNT</th>
                <th className="py-3 px-4">TYPE</th>
                <th className="py-3 px-4">STATUS</th>
                <th className="py-3 px-4">BLOCKCHAIN HASH</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {pageItems.map((tx) => (
                <tr key={tx.id} className="hover:bg-slate-900/40 transition-colors">
                  <td className="py-3 px-4 font-bold text-cyan-400">{tx.transaction_reference}</td>
                  <td className="py-3 px-4 text-slate-300">{formatHash(tx.sender_account_id, 4)}</td>
                  <td className="py-3 px-4 text-slate-300">{formatHash(tx.receiver_account_id, 4)}</td>
                  <td className="py-3 px-4 font-bold text-slate-100">
                    Rs.{Number(tx.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-3 px-4 text-slate-400">{tx.transaction_type}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        tx.status === 'FLAGGED'
                          ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                          : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                      }`}
                    >
                      {tx.status || 'COMPLETED'}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-400 flex items-center gap-1.5">
                    <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                    <span>{formatHash(tx.blockchain_hash || '', 6)}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="mt-4 pt-4 border-t border-phantom-border flex items-center justify-between text-xs font-mono text-slate-400">
          <span>
            Page {page} of {totalPages || 1} ({filtered.length} transactions)
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1 rounded bg-slate-900 border border-phantom-border hover:bg-slate-800 disabled:opacity-50"
            >
              PREV
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="px-3 py-1 rounded bg-slate-900 border border-phantom-border hover:bg-slate-800 disabled:opacity-50"
            >
              NEXT
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

