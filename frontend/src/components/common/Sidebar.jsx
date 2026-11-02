import React from 'react';
import { LayoutDashboard, Server, ShieldCheck, FileText, LineChart } from 'lucide-react';

export const NAV_ITEMS = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard, description: 'KPIs, SLA targets & DR pipeline' },
  { id: 'applications', label: 'Applications', icon: Server, description: 'Protected workloads & DB metadata' },
  { id: 'recovery-tests', label: 'Recovery Tests', icon: ShieldCheck, description: 'Drill execution history & checks' },
  { id: 'reports', label: 'Reports', icon: FileText, description: 'Auditable compliance reports' },
  { id: 'monitoring', label: 'Monitoring', icon: LineChart, description: 'RTO / RPO trends & failure analytics' },
];

export default function Sidebar({ activeTab, onSelectTab }) {
  return (
    <aside className="w-full md:w-64 bg-[#0B0F19] md:min-h-[calc(100vh-65px)] border-b md:border-b-0 md:border-r border-slate-800/80 p-3 md:p-4 shrink-0">
      <div className="flex md:flex-col gap-1.5 overflow-x-auto md:overflow-x-visible pb-2 md:pb-0 scrollbar-none">
        <div className="hidden md:block px-3 py-2 text-[10px] font-bold uppercase tracking-wider text-slate-500">
          Navigation
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-left text-xs font-medium transition-all whitespace-nowrap md:whitespace-normal ${
                isActive
                  ? 'bg-gradient-to-r from-cyan-950/80 to-blue-950/50 text-cyan-300 border border-cyan-800/60 shadow-sm shadow-cyan-950/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border border-transparent'
              }`}
            >
              <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-cyan-400' : 'text-slate-500'}`} />
              <div className="flex-1">
                <div className="font-semibold">{item.label}</div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Scope Disclaimer Box */}
      <div className="hidden md:block mt-8 p-3.5 bg-slate-950/80 border border-slate-800/80 rounded-xl text-[11px] text-slate-400">
        <div className="font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
          CloudGuard Architecture
        </div>
        <p className="leading-relaxed text-slate-500 text-[10px]">
          Verification-only engine. Analyzes sandbox restore health without touching production databases or triggering automated failovers.
        </p>
      </div>
    </aside>
  );
}
