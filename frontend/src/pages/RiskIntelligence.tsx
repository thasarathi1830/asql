import React, { useState } from 'react';
import { demoFraudRules } from '../lib/demoData';
import { ShieldAlert, Sliders, CheckCircle2, RotateCcw, Save } from 'lucide-react';

export const RiskIntelligence: React.FC = () => {
  const [rules, setRules] = useState(demoFraudRules);
  const [savedMessage, setSavedMessage] = useState(false);

  const handleWeightChange = (ruleId: string, newWeight: number) => {
    setRules((prev) =>
      prev.map((r) => (r.rule_id === ruleId ? { ...r, default_weight: newWeight } : r))
    );
  };

  const handleToggleActive = (ruleId: string) => {
    setRules((prev) =>
      prev.map((r) => (r.rule_id === ruleId ? { ...r, is_active: !r.is_active } : r))
    );
  };

  const handleSave = () => {
    setSavedMessage(true);
    setTimeout(() => setSavedMessage(false), 2500);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-phantom-border">
        <div>
          <div className="flex items-center gap-2">
            <Sliders className="w-5 h-5 text-cyan-400" />
            <h2 className="text-lg font-bold font-mono text-slate-100">8-Factor Explainable Risk Engine</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Configure mathematical weights and activation thresholds for topological & behavioral rules
          </p>
        </div>

        <div className="flex items-center gap-3">
          {savedMessage && (
            <span className="text-xs font-mono text-emerald-400 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> Weights Synchronized
            </span>
          )}
          <button
            onClick={handleSave}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs font-mono transition-all"
          >
            <Save className="w-3.5 h-3.5" /> Update Engine Weights
          </button>
        </div>
      </div>

      {/* Rules Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {rules.map((rule) => {
          const isCritical = rule.severity === 'CRITICAL';
          return (
            <div
              key={rule.rule_id}
              className={`p-5 rounded-xl border bg-phantom-surface ${
                rule.is_active ? 'border-phantom-border' : 'border-slate-800 opacity-60'
              } space-y-4`}
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold font-mono text-cyan-400">{rule.rule_id}</span>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                        isCritical
                          ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                          : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                      }`}
                    >
                      {rule.severity}
                    </span>
                  </div>
                  <h3 className="mt-1 text-sm font-bold text-slate-100">{rule.name}</h3>
                </div>

                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rule.is_active}
                    onChange={() => handleToggleActive(rule.rule_id)}
                    className="sr-only peer"
                  />
                  <div className="w-9 h-5 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-cyan-500"></div>
                </label>
              </div>

              <p className="text-xs text-slate-400 leading-relaxed">{rule.description}</p>

              <div className="space-y-1.5 pt-2 border-t border-slate-800/80">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-slate-400">Rule Weight:</span>
                  <span className="text-cyan-400 font-bold">{rule.default_weight} pts</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="35"
                  step="1"
                  value={rule.default_weight}
                  onChange={(e) => handleWeightChange(rule.rule_id, Number(e.target.value))}
                  disabled={!rule.is_active}
                  className="w-full accent-cyan-400 bg-slate-800 h-1.5 rounded-lg cursor-pointer"
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

