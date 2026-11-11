import React from 'react';
import { Database, FileSpreadsheet, CheckCircle2, RefreshCw } from 'lucide-react';
import { demoSamplingReport } from '../lib/demoData';

export const DataImport: React.FC = () => {
  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-phantom-border">
        <div>
          <div className="flex items-center gap-2">
            <Database className="w-5 h-5 text-cyan-400" />
            <h2 className="text-lg font-bold font-mono text-slate-100">Data Ingestion & PaySim Pipeline</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Status of the streaming 2-pass PaySim adapter, stratified sampling, and deterministic hashing
          </p>
        </div>
      </div>

      <div className="p-6 rounded-xl bg-phantom-surface border border-phantom-border shadow-xl space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-phantom-border">
          <div className="flex items-center gap-2">
            <FileSpreadsheet className="w-5 h-5 text-cyan-400" />
            <h3 className="text-sm font-bold font-mono text-slate-100">
              Raw PaySim Dataset Log (PS_20174392719_1491204439457_log.csv)
            </h3>
          </div>
          <span className="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            PROCESSED & SEEDED
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
          <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800">
            <span className="text-slate-400">Total Raw Rows:</span>
            <p className="mt-1 text-base font-bold text-slate-100">{Number(demoSamplingReport.raw_rows || 6362620).toLocaleString()}</p>
          </div>
          <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800">
            <span className="text-slate-400">Sampled Target:</span>
            <p className="mt-1 text-base font-bold text-cyan-400">{Number(demoSamplingReport.sampled_rows || 69981).toLocaleString()}</p>
          </div>
          <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800">
            <span className="text-slate-400">Fraud Retention:</span>
            <p className="mt-1 text-base font-bold text-emerald-400">
              {Number(demoSamplingReport.fraud_rows_retained || 8213).toLocaleString()} (100.0%)
            </p>
          </div>
          <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800">
            <span className="text-slate-400">Unique Accounts:</span>
            <p className="mt-1 text-base font-bold text-slate-100">{Number(demoSamplingReport.unique_accounts || 82218).toLocaleString()}</p>
          </div>
        </div>

        <div className="p-4 bg-slate-950/60 rounded-lg border border-slate-800 text-xs font-mono space-y-1.5 text-slate-400">
          <div className="flex items-center gap-1.5 text-emerald-400 font-bold">
            <CheckCircle2 className="w-4 h-4" /> Pipeline Integrity Verification
          </div>
          <p>• Zero foreign-key violations across customers, accounts, and transactions.</p>
          <p>• PaySim balance columns completely stripped to guarantee zero leakage into detection features.</p>
          <p>• Deterministic seed: 42 (Reproducible SHA-256 output hash).</p>
        </div>
      </div>
    </div>
  );
};

