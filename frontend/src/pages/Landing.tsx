import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, Network, Cpu, ArrowRight, Activity, Lock } from 'lucide-react';

export const Landing: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-slate-950">
      {/* Top Navbar */}
      <header className="h-20 border-b border-slate-900 px-8 flex items-center justify-between max-w-7xl mx-auto w-full">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
            <Shield className="w-6 h-6 text-cyan-400" />
          </div>
          <div>
            <h1 className="font-bold text-lg font-mono tracking-wider">PHANTOM</h1>
            <p className="text-[10px] text-cyan-400 font-mono tracking-widest">NETWORK AML INTELLIGENCE</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <Link
            to="/login"
            className="px-4 py-2 rounded-lg text-sm text-slate-300 hover:text-slate-100 font-medium transition-colors"
          >
            Sign In
          </Link>
          <Link
            to="/dashboard"
            className="px-5 py-2.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-sm transition-all shadow-lg shadow-cyan-500/20"
          >
            Launch Command Center
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 max-w-5xl mx-auto px-6 py-20 flex flex-col items-center text-center justify-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-mono mb-6">
          <Activity className="w-3.5 h-3.5 animate-pulse" />
          PAYSIM COMPLIANT & EVM AUDIT-ANCHORED
        </div>
        <h2 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-slate-100 max-w-4xl leading-tight">
          Next-Generation Identity & <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-teal-300">Transaction Network Intelligence</span>
        </h2>
        <p className="mt-6 text-base sm:text-lg text-slate-400 max-w-2xl leading-relaxed">
          Expose hidden circular laundering rings, rapid pass-through mule chains, and hardware device collisions across millions of accounts with sub-500ms explainable graph intelligence.
        </p>

        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <Link
            to="/dashboard"
            className="flex items-center gap-2 px-6 py-3.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-sm transition-all shadow-xl shadow-cyan-500/25"
          >
            Access Live Intelligence Dashboard <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            to="/customers/new"
            className="flex items-center gap-2 px-6 py-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-800 font-semibold text-sm transition-all"
          >
            Real-Time Customer Onboarding Flow
          </Link>
        </div>

        {/* Feature Grid */}
        <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-6 text-left w-full">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80">
            <Network className="w-8 h-8 text-cyan-400 mb-4" />
            <h3 className="font-bold text-base text-slate-200">8-Factor Graph Rules</h3>
            <p className="mt-2 text-xs text-slate-400 leading-relaxed">
              Topological elementary cycle detection, betweenness bottlenecks, and rapid mule pass-through scoring without balance leakage.
            </p>
          </div>
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80">
            <Lock className="w-8 h-8 text-cyan-400 mb-4" />
            <h3 className="font-bold text-base text-slate-200">Zero-PII Privacy Shield</h3>
            <p className="mt-2 text-xs text-slate-400 leading-relaxed">
              Salted SHA-256 attribute matching and masked identifiers prevent raw PII exposure across logs, audit trails, and on-chain records.
            </p>
          </div>
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80">
            <Cpu className="w-8 h-8 text-cyan-400 mb-4" />
            <h3 className="font-bold text-base text-slate-200">EVM Smart Contract Audit</h3>
            <p className="mt-2 text-xs text-slate-400 leading-relaxed">
              Immutable SHA-256 transaction and investigation anchoring on Ethereum Sepolia registry for tamper-evident prosecution packages.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};

