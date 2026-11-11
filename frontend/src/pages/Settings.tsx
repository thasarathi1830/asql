import React, { useState } from 'react';
import { Settings as SettingsIcon, Shield, Server, CheckCircle2 } from 'lucide-react';
import { isCloudMode } from '../lib/supabase';

export const Settings: React.FC = () => {
  const [apiKey, setApiKey] = useState('dev-key');
  const [mode, setMode] = useState(isCloudMode ? 'cloud' : 'local');
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-phantom-border">
        <div>
          <div className="flex items-center gap-2">
            <SettingsIcon className="w-5 h-5 text-cyan-400" />
            <h2 className="text-lg font-bold font-mono text-slate-100">System Configuration & Dual-Mode</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Manage PHANTOM execution profile, API key authentication, and cloud infrastructure bindings
          </p>
        </div>
      </div>

      <form onSubmit={handleSave} className="p-6 rounded-xl bg-phantom-surface border border-phantom-border shadow-xl space-y-6">
        <div>
          <label className="block text-xs font-mono text-slate-400 mb-1.5">Execution Mode</label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setMode('local')}
              className={`p-4 rounded-xl border text-left transition-all ${
                mode === 'local'
                  ? 'bg-cyan-500/10 border-cyan-500/40 text-cyan-300'
                  : 'bg-slate-900 border-slate-800 text-slate-400'
              }`}
            >
              <div className="text-xs font-mono font-bold">LOCAL FALLBACK MODE</div>
              <p className="text-[11px] text-slate-400 mt-1">In-memory NetworkX graph + SQLite + Local Hardhat Node (Zero external credentials required)</p>
            </button>

            <button
              type="button"
              onClick={() => setMode('cloud')}
              className={`p-4 rounded-xl border text-left transition-all ${
                mode === 'cloud'
                  ? 'bg-cyan-500/10 border-cyan-500/40 text-cyan-300'
                  : 'bg-slate-900 border-slate-800 text-slate-400'
              }`}
            >
              <div className="text-xs font-mono font-bold">MANAGED CLOUD MODE</div>
              <p className="text-[11px] text-slate-400 mt-1">Supabase Postgres + Neo4j Aura + Ethereum Sepolia Testnet</p>
            </button>
          </div>
        </div>

        <div>
          <label className="block text-xs font-mono text-slate-400 mb-1.5">Internal Analytics API Key</label>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
          />
          <p className="text-[11px] text-slate-500 mt-1 font-mono">Passed in X-Internal-API-Key header to secure Python microservices.</p>
        </div>

        <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
          {saved && (
            <span className="text-xs font-mono text-emerald-400 flex items-center gap-1">
              <CheckCircle2 className="w-4 h-4" /> Configuration Updated
            </span>
          )}
          <button
            type="submit"
            className="ml-auto px-5 py-2.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs font-mono transition-all shadow-lg shadow-cyan-500/20"
          >
            Save Configuration
          </button>
        </div>
      </form>
    </div>
  );
};

