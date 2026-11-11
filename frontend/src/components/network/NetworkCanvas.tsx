import React, { useEffect, useRef } from 'react';
import cytoscape, { Core } from 'cytoscape';
import { demoAccounts, demoTransactions, demoIdentityAttributes, demoClusters } from '../../lib/demoData';

interface NetworkCanvasProps {
  onSelectNode?: (node: any) => void;
  filterRisk?: string;
  searchTerm?: string;
  maxNodes?: number;
}

export const NetworkCanvas: React.FC<NetworkCanvasProps> = ({
  onSelectNode,
  filterRisk = 'ALL',
  searchTerm = '',
  maxNodes = 200,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Filter accounts up to maxNodes
    let filteredAccts = demoAccounts;
    if (filterRisk !== 'ALL') {
      filteredAccts = filteredAccts.filter((a) => a.risk_level === filterRisk);
    }
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      filteredAccts = filteredAccts.filter(
        (a) =>
          a.account_number_masked.toLowerCase().includes(q) ||
          a.bank_code.toLowerCase().includes(q) ||
          a.id.toLowerCase().includes(q)
      );
    }

    const acctSlice = filteredAccts.slice(0, maxNodes);
    const acctIdSet = new Set(acctSlice.map((a) => a.id));

    // Nodes
    const elements: any[] = acctSlice.map((a) => {
      const isCritical = a.risk_level === 'CRITICAL';
      const isPhantom = a.account_number_masked.includes('ACC-0001') || a.account_number_masked.includes('ACC-0044') || a.account_number_masked.includes('ACC-0078');
      return {
        data: {
          id: a.id,
          label: a.account_number_masked,
          bank: a.bank_code,
          score: a.risk_score,
          risk: a.risk_level,
          isPhantom,
          size: isPhantom ? 36 : Math.max(16, Math.min(32, a.risk_score / 3)),
        },
      };
    });

    // Transaction Edges
    demoTransactions.forEach((tx) => {
      if (acctIdSet.has(tx.sender_account_id) && acctIdSet.has(tx.receiver_account_id)) {
        elements.push({
          data: {
            id: `tx-${tx.id}`,
            source: tx.sender_account_id,
            target: tx.receiver_account_id,
            label: `Rs.${Number(tx.amount).toLocaleString()}`,
            amount: Number(tx.amount),
            isCycle: tx.amount > 450000,
          },
        });
      }
    });

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#10b981',
            label: 'data(label)',
            color: '#cbd5e1',
            'font-size': '9px',
            'font-family': 'monospace',
            'text-valign': 'bottom',
            'text-margin-y': 5,
            width: 'data(size)',
            height: 'data(size)',
            'border-width': 2,
            'border-color': '#334155',
          },
        },
        {
          selector: 'node[risk = "MEDIUM"]',
          style: {
            'background-color': '#f59e0b',
            'border-color': '#d97706',
          },
        },
        {
          selector: 'node[risk = "HIGH"]',
          style: {
            'background-color': '#f97316',
            'border-color': '#ea580c',
          },
        },
        {
          selector: 'node[risk = "CRITICAL"]',
          style: {
            'background-color': '#f43f5e',
            'border-color': '#e11d48',
            'border-width': 3,
            color: '#fda4af',
            'font-weight': 'bold',
          },
        },
        {
          selector: 'node[?isPhantom]',
          style: {
            'border-color': '#06b6d4',
            'border-width': 3,
          },
        },
        {
          selector: 'edge',
          style: {
            width: 1.5,
            'line-color': '#334155',
            'target-arrow-color': '#475569',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'arrow-scale': 0.8,
          },
        },
        {
          selector: 'edge[?isCycle]',
          style: {
            width: 3,
            'line-color': '#f43f5e',
            'target-arrow-color': '#f43f5e',
            'line-style': 'solid',
          },
        },
      ],
      layout: {
        name: 'cose',
        animate: false,
        padding: 40,
        nodeRepulsion: () => 450000,
        idealEdgeLength: () => 100,
      },
      minZoom: 0.2,
      maxZoom: 3.0,
      wheelSensitivity: 0.2,
    });

    cy.on('tap', 'node', (evt) => {
      const node = evt.target.data();
      if (onSelectNode) {
        onSelectNode(node);
      }
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, [filterRisk, searchTerm, maxNodes, onSelectNode]);

  return (
    <div className="relative w-full h-full min-h-[500px] bg-slate-950 rounded-xl border border-phantom-border overflow-hidden">
      <div ref={containerRef} className="w-full h-full min-h-[500px]" />
      <div className="absolute bottom-4 left-4 flex items-center gap-3 bg-slate-900/90 border border-slate-800 px-3 py-1.5 rounded-lg text-xs font-mono text-slate-400">
        <span className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Low
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> Med
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 rounded-full bg-orange-500" /> High
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" /> Critical Ring
        </span>
      </div>
    </div>
  );
};

