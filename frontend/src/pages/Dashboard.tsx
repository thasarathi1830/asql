import React from 'react';
import { Link } from 'react-router-dom';
import {
  Users,
  ArrowLeftRight,
  ShieldAlert,
  Cpu,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  ExternalLink,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { StatCard } from '../components/ui/StatCard';
import { RiskBadge } from '../components/ui/RiskBadge';
import {
  demoRiskDistribution,
  demoSamplingReport,
  demoAlerts,
  demoTransactions,
} from '../lib/demoData';

export const Dashboard: React.FC = () => {
  const chartData = [
    { name: 'LOW', count: demoRiskDistribution.LOW, color: '#10b981' },
    { name: 'MEDIUM', count: demoRiskDistribution.MEDIUM, color: '#f59e0b' },
    { name: 'HIGH', count: demoRiskDistribution.HIGH, color: '#f97316' },
    { name: 'CRITICAL', count: demoRiskDistribution.CRITICAL, color: '#f43f5e' },
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Operation Phantom Ring Spotlight Banner */}
      <div className="relative rounded-2xl bg-gradient-to-r from-rose-950/60 via-slate-900 to-cyan-950/40 border border-rose-500/40 p-6 shadow-2xl overflow-hidden">
        <div className="absolute top-0 right-0 transform translate-x-8 -translate-y-8 w-64 h-64 bg-rose-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30 flex items-center gap-1.5 animate-pulse">
                <AlertTriangle className="w-3.5 h-3.5" /> SPOTLIGHT: ACTIVE LAUNDERING RING
              </span>
              <RiskBadge level="CRITICAL" score={94.0} size="sm" />
            </div>
            <h2 className="text-xl font-bold text-slate-100 font-mono tracking-tight">
              Operation Phantom Ring (INV-2026-PHANTOM-001)
            </h2>
            <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
              Detected 3-hop circular RTGS money flow cycling <span className="text-cyan-400 font-mono font-bold">Rs.1,415,000</span> across HDFC, ICICI, and SBI within 4.25 hours linked by shared hardware fingerprint <span className="font-mono text-rose-400 font-semibold">DEV-PHANTOM-103</span>.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              to="/network"
              className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-all shadow-lg shadow-cyan-500/20"
            >
              Open Graph Canvas <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/investigations/INV-2026-PHANTOM-001"
              className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 font-medium text-xs transition-colors"
            >
              Dossier & Evidence <ExternalLink className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>

      {/* 4 StatCards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard
          title="Total Scored Accounts"
          value={Number(demoSamplingReport.unique_accounts || 82218).toLocaleString()}
          change="+100% PAYSIM"
          isPositive
          icon={<Users className="w-5 h-5" />}
          subtitle="All balance columns stripped"
        />
        <StatCard
          title="Monitored Transactions"
          value={Number(demoSamplingReport.sampled_rows || 69981).toLocaleString()}
          change="8,213 Real Fraud"
          isPositive
          icon={<ArrowLeftRight className="w-5 h-5" />}
          subtitle="100% fraud rows retained"
        />
        <StatCard
          title="Circular Rings Flagged"
          value="26 Rings"
          change="RULE_001 Active"
          isPositive={false}
          icon={<ShieldAlert className="w-5 h-5" />}
          subtitle="Max duration <= 72 hours"
        />
        <StatCard
          title="Audit Ledger Integrity"
          value="100% VERIFIED"
          change="EVM Testnet"
          isPositive
          icon={<Cpu className="w-5 h-5" />}
          subtitle="PhantomAuditRegistry.sol"
        />
      </div>

      {/* Grid: Risk Distribution + Recent Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Distribution Chart */}
        <div className="lg:col-span-1 bg-phantom-surface border border-phantom-border rounded-xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-phantom-border">
              <h3 className="text-sm font-semibold text-slate-200 font-mono flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-cyan-400" />
                Risk Score Distribution
              </h3>
              <span className="text-[11px] text-slate-400 font-mono">8-Factor Scale</span>
            </div>
            <div className="h-64 mt-4 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <XAxis dataKey="name" stroke="#64748b" fontSize={11} fontFamily="monospace" />
                  <YAxis stroke="#64748b" fontSize={11} fontFamily="monospace" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                    labelStyle={{ color: '#94a3b8', fontFamily: 'monospace' }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-phantom-border flex justify-between text-xs font-mono text-slate-400">
            <span>Critical Accounts: {demoRiskDistribution.CRITICAL}</span>
            <Link to="/risk-intelligence" className="text-cyan-400 hover:underline">
              Rule Config →
            </Link>
          </div>
        </div>

        {/* Real-Time Alerts Queue */}
        <div className="lg:col-span-2 bg-phantom-surface border border-phantom-border rounded-xl p-6">
          <div className="flex items-center justify-between pb-3 border-b border-phantom-border">
            <h3 className="text-sm font-semibold text-slate-200 font-mono flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              Priority Intelligence Alerts
            </h3>
            <Link to="/alerts" className="text-xs font-mono text-cyan-400 hover:underline">
              View All ({demoAlerts.length}) →
            </Link>
          </div>

          <div className="mt-4 space-y-3">
            {demoAlerts.slice(0, 4).map((al) => (
              <div
                key={al.id}
                className="p-4 rounded-lg bg-slate-900/60 border border-slate-800 flex items-start justify-between gap-4 hover:border-slate-700 transition-colors"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <RiskBadge level={al.severity} size="sm" />
                    <span className="text-xs font-mono text-slate-400">{al.alert_type}</span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      {new Date(al.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <h4 className="text-sm font-bold text-slate-100">{al.title}</h4>
                  <p className="text-xs text-slate-400 line-clamp-1">{al.description}</p>
                </div>
                <Link
                  to="/investigations/INV-2026-PHANTOM-001"
                  className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs font-mono whitespace-nowrap transition-colors"
                >
                  Triage Case
                </Link>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

