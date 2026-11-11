import React, { useState } from 'react';
import { NetworkCanvas } from '../components/network/NetworkCanvas';
import { NodeInspector } from '../components/network/NodeInspector';
import { SearchBar } from '../components/ui/SearchBar';
import { ShieldAlert, RefreshCw, ZoomIn, Layers } from 'lucide-react';

export const NetworkExplorer: React.FC = () => {
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRisk, setFilterRisk] = useState('ALL');
  const [maxNodes, setMaxNodes] = useState(150);

  const handleSpotlightPhantomRing = () => {
    setSearchTerm('ACC-0044');
    setFilterRisk('ALL');
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] space-y-4">
      {/* Top Filter Bar */}
      <div className="bg-phantom-surface border border-phantom-border rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-1 min-w-[280px] max-w-md">
          <SearchBar
            value={searchTerm}
            onChange={setSearchTerm}
            placeholder="Search account (e.g. ACC-0001-9041)..."
            className="w-full"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 bg-slate-900 border border-phantom-border rounded-lg p-1 text-xs font-mono">
            {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((lvl) => (
              <button
                key={lvl}
                onClick={() => setFilterRisk(lvl)}
                className={`px-2.5 py-1 rounded transition-colors ${
                  filterRisk === lvl
                    ? 'bg-cyan-500 text-slate-950 font-bold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2 bg-slate-900 border border-phantom-border px-3 py-1.5 rounded-lg text-xs font-mono text-slate-400">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            <span>Cap:</span>
            <select
              value={maxNodes}
              onChange={(e) => setMaxNodes(Number(e.target.value))}
              className="bg-transparent text-slate-200 focus:outline-none"
            >
              <option value={50}>50</option>
              <option value={150}>150</option>
              <option value={300}>300</option>
              <option value={500}>500</option>
              <option value={1000}>1,000</option>
            </select>
          </div>

          <button
            onClick={handleSpotlightPhantomRing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 hover:bg-rose-500/20 text-xs font-mono font-bold transition-colors"
          >
            <ShieldAlert className="w-3.5 h-3.5" /> Spotlight Phantom Ring
          </button>
        </div>
      </div>

      {/* Main Canvas + Inspector */}
      <div className="flex-1 flex min-h-0 relative">
        <div className="flex-1 h-full min-h-0">
          <NetworkCanvas
            onSelectNode={setSelectedNode}
            filterRisk={filterRisk}
            searchTerm={searchTerm}
            maxNodes={maxNodes}
          />
        </div>
        {selectedNode && (
          <NodeInspector node={selectedNode} onClose={() => setSelectedNode(null)} />
        )}
      </div>
    </div>
  );
};

