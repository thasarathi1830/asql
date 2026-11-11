import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import {
  LayoutDashboard,
  Network,
  ArrowLeftRight,
  UserPlus,
  Users,
  ShieldAlert,
  Bell,
  Briefcase,
  Cpu,
  FileCheck2,
  Database,
  Settings,
  Shield,
  Activity,
  Terminal,
} from 'lucide-react';
import { isCloudMode } from '../../lib/supabase';

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/network', label: 'Network Graph', icon: Network },
  { to: '/customers/new', label: 'New Customer', icon: UserPlus, highlight: true },
  { to: '/transactions', label: 'Transactions', icon: ArrowLeftRight },
  { to: '/identities', label: 'Identity Clusters', icon: Users },
  { to: '/risk-intelligence', label: 'Risk Intelligence', icon: ShieldAlert },
  { to: '/alerts', label: 'Alerts', icon: Bell },
  { to: '/investigations', label: 'Investigations', icon: Briefcase },
  { to: '/blockchain', label: 'Blockchain Audit', icon: Cpu },
  { to: '/audit-logs', label: 'Audit Trail', icon: FileCheck2 },
  { to: '/data-import', label: 'Data Ingestion', icon: Database },
  { to: '/settings', label: 'Settings', icon: Settings },
];

export const AppShell: React.FC = () => {
  return (
    <div className="flex h-screen bg-phantom-bg text-slate-100 overflow-hidden font-sans">
      {/* Sidebar */}
      <aside className="w-64 flex flex-col border-r border-phantom-border bg-slate-950/60 backdrop-blur-md select-none">
        {/* Brand */}
        <div className="h-16 flex items-center gap-3 px-6 border-b border-phantom-border">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Shield className="w-5 h-5 text-slate-950" />
          </div>
          <div>
            <h1 className="font-bold tracking-wider text-sm text-slate-100 font-mono">PHANTOM</h1>
            <p className="text-[10px] text-slate-400 font-mono tracking-tight">AML INTELLIGENCE</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all group ${
                    isActive
                      ? 'bg-phantom-accent/15 text-phantom-accent border border-phantom-accent/30 font-semibold'
                      : item.highlight
                      ? 'text-cyan-400 hover:bg-slate-900 border border-cyan-500/20'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                  }`
                }
              >
                <Icon className="w-4 h-4 transition-transform group-hover:scale-110" />
                <span>{item.label}</span>
                {item.highlight && (
                  <span className="ml-auto text-[9px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300">
                    REALTIME
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Mode pill & bottom system status */}
        <div className="p-4 border-t border-phantom-border bg-slate-950/40">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-slate-400 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              STATUS
            </span>
            <span className="px-2 py-0.5 rounded bg-slate-800 text-[10px] font-semibold text-slate-300 border border-slate-700">
              {isCloudMode ? 'CLOUD MODE' : 'LOCAL DUAL-MODE'}
            </span>
          </div>
          <div className="mt-2 text-[10px] text-slate-500 font-mono truncate">
            EVM: Sepolia (Local / Dual)
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Topbar */}
        <header className="h-16 flex items-center justify-between px-8 border-b border-phantom-border bg-phantom-surface/40 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <Activity className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-mono text-slate-300">
              PAY-SIM ENGINE ACTIVE: 82,218 ACCOUNTS / 69,981 TXS
            </span>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900 border border-phantom-border text-xs font-mono text-slate-400">
              <Terminal className="w-3.5 h-3.5 text-cyan-400" />
              <span>ROLE: FIU_INVESTIGATOR</span>
            </div>
            <div className="w-8 h-8 rounded-full bg-slate-800 border border-phantom-border flex items-center justify-center font-bold text-xs text-cyan-400">
              VR
            </div>
          </div>
        </header>

        {/* Page Content View */}
        <main className="flex-1 overflow-y-auto p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

