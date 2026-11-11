import React from 'react';
import { demoInvestigations } from '../lib/demoData';
import { Briefcase, ArrowRight, ShieldAlert, Clock, UserCheck } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Investigations: React.FC = () => {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-phantom-border">
        <div>
          <div className="flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-cyan-400" />
            <h2 className="text-lg font-bold font-mono text-slate-100">Financial Crime Investigations</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Active AML intelligence case dossiers, prosecution evidence packages, and court-admissible audit logs
          </p>
        </div>

        <button className="px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs font-mono transition-all">
          + Create Investigation
        </button>
      </div>

      {/* Cases List */}
      <div className="space-y-4">
        {demoInvestigations.map((inv) => (
          <div
            key={inv.id}
            className="p-6 rounded-xl bg-phantom-surface border border-phantom-border hover:border-cyan-500/40 transition-colors shadow-xl space-y-4"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold font-mono text-cyan-400">{inv.case_number}</span>
                <span className="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30">
                  {inv.priority}
                </span>
                <span className="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                  {inv.status}
                </span>
              </div>
              <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
                <Clock className="w-3.5 h-3.5" />
                <span>Opened: {new Date(inv.created_at).toLocaleDateString()}</span>
              </div>
            </div>

            <div>
              <h3 className="text-base font-bold text-slate-100">{inv.title}</h3>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">{inv.description}</p>
            </div>

            <div className="pt-4 border-t border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
                <UserCheck className="w-4 h-4 text-cyan-400" />
                <span>Lead: <strong className="text-slate-200">{inv.assigned_to}</strong></span>
              </div>
              <Link
                to={`/investigations/${inv.case_number}`}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-cyan-400 text-xs font-mono font-bold border border-slate-700 transition-colors"
              >
                Open Investigation Dossier <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

