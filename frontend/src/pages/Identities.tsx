import React, { useState } from 'react';
import { demoClusters, demoIdentityAttributes } from '../lib/demoData';
import { Users, Smartphone, Globe, ShieldAlert, ExternalLink } from 'lucide-react';
import { SearchBar } from '../components/ui/SearchBar';
import { Link } from 'react-router-dom';

export const Identities: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredClusters = demoClusters.filter((c) => {
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      return (
        c.cluster_name.toLowerCase().includes(q) ||
        c.description.toLowerCase().includes(q) ||
        c.id.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-phantom-border">
        <div>
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5 text-cyan-400" />
            <h2 className="text-lg font-bold font-mono text-slate-100">Shared Identity & Device Clusters</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Detecting coordinated mule rings sharing hardware fingerprints, IP subnets, or proxy networks
          </p>
        </div>

        <div className="w-full sm:w-80">
          <SearchBar value={searchTerm} onChange={setSearchTerm} placeholder="Filter clusters..." />
        </div>
      </div>

      {/* Cluster Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredClusters.map((cluster) => {
          const members = JSON.parse(cluster.entity_ids || '[]');
          const isPhantom = cluster.cluster_name.includes('Phantom');
          return (
            <div
              key={cluster.id}
              className={`p-5 rounded-xl border ${
                isPhantom
                  ? 'bg-rose-950/20 border-rose-500/40 shadow-rose-950/50'
                  : 'bg-phantom-surface border-phantom-border'
              } shadow-lg space-y-4`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-1.5">
                    {isPhantom ? (
                      <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-amber-500" />
                    )}
                    <span className="text-xs font-mono font-bold text-slate-200">{cluster.cluster_name}</span>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500 break-all">{cluster.id}</span>
                </div>
                <span
                  className={`px-2 py-0.5 rounded text-xs font-mono font-bold ${
                    cluster.risk_score >= 80
                      ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                      : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                  }`}
                >
                  {cluster.risk_score.toFixed(1)}
                </span>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">{cluster.description}</p>

              <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs font-mono text-slate-400">
                <span>{members.length} Linked Accounts</span>
                <Link
                  to="/network"
                  className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
                >
                  Explore <ExternalLink className="w-3 h-3" />
                </Link>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

