import React from 'react';
import { CheckCircle2, XCircle, AlertTriangle, RefreshCw, Clock, HelpCircle } from 'lucide-react';

export default function StatusBadge({ status, size = 'sm' }) {
  const normalized = (status || '').toUpperCase();

  const isSmall = size === 'sm';
  const sizeClasses = isSmall 
    ? 'px-2.5 py-0.5 text-xs' 
    : 'px-3 py-1 text-sm font-semibold';

  if (normalized === 'SUCCESS' || normalized === 'PASS' || normalized === 'PASSED') {
    return (
      <span className={`inline-flex items-center gap-1.5 rounded-full font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-800/70 ${sizeClasses}`}>
        <CheckCircle2 className={isSmall ? "w-3.5 h-3.5" : "w-4 h-4"} />
        {normalized}
      </span>
    );
  }

  if (normalized === 'FAILED' || normalized === 'FAIL' || normalized === 'ERROR') {
    return (
      <span className={`inline-flex items-center gap-1.5 rounded-full font-semibold bg-rose-950/80 text-rose-400 border border-rose-800/70 ${sizeClasses}`}>
        <XCircle className={isSmall ? "w-3.5 h-3.5" : "w-4 h-4"} />
        {normalized}
      </span>
    );
  }

  if (normalized === 'RUNNING') {
    return (
      <span className={`inline-flex items-center gap-1.5 rounded-full font-semibold bg-cyan-950/80 text-cyan-400 border border-cyan-800/70 ${sizeClasses}`}>
        <RefreshCw className={`${isSmall ? "w-3.5 h-3.5" : "w-4 h-4"} animate-spin`} />
        RUNNING
      </span>
    );
  }

  if (normalized === 'PENDING') {
    return (
      <span className={`inline-flex items-center gap-1.5 rounded-full font-semibold bg-amber-950/80 text-amber-400 border border-amber-800/70 ${sizeClasses}`}>
        <Clock className={isSmall ? "w-3.5 h-3.5" : "w-4 h-4"} />
        PENDING
      </span>
    );
  }

  if (normalized === 'DEGRADED' || normalized === 'INCOMPLETE') {
    return (
      <span className={`inline-flex items-center gap-1.5 rounded-full font-semibold bg-amber-950/80 text-amber-300 border border-amber-700/70 ${sizeClasses}`}>
        <AlertTriangle className={isSmall ? "w-3.5 h-3.5" : "w-4 h-4"} />
        {normalized}
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full font-semibold bg-slate-800 text-slate-300 border border-slate-700 ${sizeClasses}`}>
      <HelpCircle className={isSmall ? "w-3.5 h-3.5" : "w-4 h-4"} />
      {normalized || 'UNKNOWN'}
    </span>
  );
}
