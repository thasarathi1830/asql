import React from 'react';
import { RiskBadge } from '../ui/RiskBadge';
import { ShieldAlert, ExternalLink, Hash, Landmark, Activity } from 'lucide-react';
import { Link } from 'react-router-dom';

interface NodeInspectorProps {
  node: any;
  onClose: () => void;
}

export const NodeInspector: React.FC<NodeInspectorProps> = ({ node, onClose }) => {
  if (!node) return null;

  return (
    <div className="w-80 bg-phantom-surface/95 border-l border-phantom-border h-full p-6 flex flex-col justify-between overflow-y-auto">
      <div>
        <div className="flex items-center justify-between pb-4 border-b border-phantom-border">
          <span className="text-xs font-mono uppercase text-slate-400">Node Inspector</span>
          <button onClick={onClose} className="text-xs text-slate-400 hover:text-slate-200">
            CLOSE
          </button>
        </div>

        <div className="mt-4">
          <div className="text-lg font-bold font-mono text-slate-100">{node.label}</div>
          <div className="mt-2 flex items-center gap-2">
            <RiskBadge level={node.risk} score={node.score} />
            <span className="text-xs font-mono text-cyan-400 border border-cyan-500/30 px-2 py-0.5 rounded">
              {node.bank || 'HDFC'}
            </span>
          </div>
        </div>

        <div className="mt-6 space-y-4">
          <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800">
            <span className="text-xs text-slate-400 flex items-center gap-1.5">
              <Hash className="w-3.5 h-3.5 text-cyan-400" /> Account UUID
            </span>
            <p className="mt-1 font-mono text-[11px] text-slate-300 break-all">{node.id}</p>
          </div>

          <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800">
            <span className="text-xs text-slate-400 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-cyan-400" /> Betweenness Centrality
            </span>
            <p className="mt-1 font-mono text-sm font-bold text-slate-200">
              {node.isPhantom ? '0.810 (Intermediary Hub)' : '0.042'}
            </p>
          </div>

          {node.isPhantom && (
            <div className="p-3 bg-rose-950/30 border border-rose-500/30 rounded-lg">
              <div className="flex items-center gap-2 text-rose-400 text-xs font-bold font-mono">
                <ShieldAlert className="w-4 h-4" />
                OPERATION PHANTOM RING
              </div>
              <p className="mt-1 text-xs text-rose-200/80 leading-relaxed">
                Active member in 3-hop circular RTGS laundering ring (Rs.1,415,000 cycled in 4.25 hours).
              </p>
              <div className="mt-3">
                <Link
                  to="/investigations/INV-2026-PHANTOM-001"
                  className="inline-flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 font-mono underline"
                >
                  View Investigation Case <ExternalLink className="w-3 h-3" />
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="pt-4 border-t border-phantom-border">
        <Link
          to={`/transactions?account=${node.id}`}
          className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-semibold text-xs transition-colors"
        >
          View Account Ledger
        </Link>
      </div>
    </div>
  );
};

