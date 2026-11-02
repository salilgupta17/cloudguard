import React from 'react';
import { ShieldCheck, RefreshCw, Radio, Cloud, Lock } from 'lucide-react';

export default function Navbar({ healthStatus, onRefresh, isRefreshing }) {
  const isReady = healthStatus?.status === 'ready' || healthStatus?.status === 'ok';

  return (
    <header className="sticky top-0 z-40 bg-[#0B0F19]/90 backdrop-blur-md border-b border-slate-800/80 px-6 py-3.5 flex items-center justify-between">
      {/* Brand Identity */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-gradient-to-tr from-cyan-500 via-sky-500 to-indigo-600 rounded-xl shadow-md shadow-cyan-500/20">
          <ShieldCheck className="w-6 h-6 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold tracking-tight text-white font-sans">CloudGuard</span>
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800/80">
              AWS DR Monitor
            </span>
          </div>
          <p className="text-xs text-slate-400 hidden sm:block">Automated Disaster Recovery Verification & Audit Reporting</p>
        </div>
      </div>

      {/* Badges & Actions */}
      <div className="flex items-center gap-3">
        {/* Read-Only Badge */}
        <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-[11px] text-slate-300">
          <Lock className="w-3.5 h-3.5 text-cyan-400" />
          <span>Audit-Only Platform</span>
        </div>

        {/* AWS Environment Indicator */}
        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-[11px] text-slate-300">
          <Cloud className="w-3.5 h-3.5 text-indigo-400" />
          <span>AWS Fargate Sandbox</span>
        </div>

        {/* API Readiness Heartbeat */}
        <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-slate-900/90 border border-slate-800 text-xs">
          <Radio className={`w-3.5 h-3.5 ${isReady ? 'text-emerald-400 animate-pulse' : 'text-rose-400'}`} />
          <span className="text-slate-400 hidden sm:inline">Backend:</span>
          {isReady ? (
            <span className="text-emerald-400 font-medium">Connected</span>
          ) : (
            <span className="text-rose-400 font-medium">Offline</span>
          )}
        </div>

        {/* Refresh Telemetry (No Remediation) */}
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700/80 active:bg-slate-900 text-slate-200 rounded-lg text-xs font-medium border border-slate-700/80 transition disabled:opacity-50 shadow-sm"
          title="Fetch latest recovery drill telemetry from backend"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-cyan-400' : 'text-slate-400'}`} />
          <span className="hidden sm:inline">Refresh Telemetry</span>
        </button>
      </div>
    </header>
  );
}
