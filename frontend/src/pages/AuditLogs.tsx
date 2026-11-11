import React from 'react';
import { FileCheck2, ShieldCheck, Cpu } from 'lucide-react';
import { formatHash } from '../lib/blockchainVerifier';

export const AuditLogs: React.FC = () => {
  const auditEvents = [
    {
      id: 'AUD-001',
      action: 'RISK_SCORE_EVALUATION',
      entity_type: 'ACCOUNT',
      entity_id: 'ACC-0001-9041',
      actor: 'SYSTEM_ANALYTICS_DAEMON',
      prev_hash: '0x0000000000000000000000000000000000000000000000000000000000000000',
      curr_hash: '0x1a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f801',
      timestamp: '2026-06-15T10:00:05Z',
      status: 'CHAIN_VALID',
    },
    {
      id: 'AUD-002',
      action: 'CYCLE_DETECTION_FLAG',
      entity_type: 'CLUSTER',
      entity_id: 'Circular Ring #1',
      actor: 'ENGINE_RULE_001',
      prev_hash: '0x1a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f801',
      curr_hash: '0x2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f80902',
      timestamp: '2026-06-15T14:15:30Z',
      status: 'CHAIN_VALID',
    },
    {
      id: 'AUD-003',
      action: 'INVESTIGATION_OPENED',
      entity_type: 'INVESTIGATION',
      entity_id: 'INV-2026-PHANTOM-001',
      actor: 'agent.vikram@fiu.gov.in',
      prev_hash: '0x2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f80902',
      curr_hash: '0x3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f8091a03',
      timestamp: '2026-06-15T15:00:00Z',
      status: 'CHAIN_VALID',
    },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-phantom-border">
        <div>
          <div className="flex items-center gap-2">
            <FileCheck2 className="w-5 h-5 text-cyan-400" />
            <h2 className="text-lg font-bold font-mono text-slate-100">Immutable Audit Trail & Hash Chain</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Tamper-evident system activity log chained with SHA-256 state transitions
          </p>
        </div>
      </div>

      <div className="bg-phantom-surface border border-phantom-border rounded-xl p-6 shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-900/60 text-slate-400 border-b border-phantom-border">
              <tr>
                <th className="py-3 px-4">EVENT ID</th>
                <th className="py-3 px-4">ACTION</th>
                <th className="py-3 px-4">TARGET ENTITY</th>
                <th className="py-3 px-4">ACTOR / AGENT</th>
                <th className="py-3 px-4">PREVIOUS HASH</th>
                <th className="py-3 px-4">CURRENT HASH</th>
                <th className="py-3 px-4">CHAIN INTEGRITY</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {auditEvents.map((evt) => (
                <tr key={evt.id} className="hover:bg-slate-900/40 transition-colors">
                  <td className="py-3 px-4 font-bold text-cyan-400">{evt.id}</td>
                  <td className="py-3 px-4 text-slate-200">{evt.action}</td>
                  <td className="py-3 px-4 text-slate-300">{evt.entity_id}</td>
                  <td className="py-3 px-4 text-slate-400">{evt.actor}</td>
                  <td className="py-3 px-4 text-slate-500">{formatHash(evt.prev_hash, 4)}</td>
                  <td className="py-3 px-4 text-slate-300 font-bold">{formatHash(evt.curr_hash, 4)}</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 w-fit">
                      <ShieldCheck className="w-3 h-3" /> {evt.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

