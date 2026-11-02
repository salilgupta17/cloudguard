import React from 'react';
import { Database, Info } from 'lucide-react';

export default function EmptyState({ 
  icon: Icon = Database, 
  title = "No Records Found", 
  description = "No disaster recovery records match the specified criteria.",
  hint = "Records are generated automatically during scheduled or orchestrated verification drills."
}) {
  return (
    <div className="w-full p-12 flex flex-col items-center justify-center text-center bg-slate-900/40 border border-slate-800 rounded-2xl">
      <div className="w-14 h-14 rounded-2xl bg-slate-800/80 border border-slate-700/80 flex items-center justify-center text-slate-400 mb-4 shadow-inner">
        <Icon className="w-7 h-7 text-cyan-400" />
      </div>
      <h3 className="text-lg font-semibold text-slate-100 mb-1">{title}</h3>
      <p className="text-sm text-slate-400 max-w-md mb-3">{description}</p>
      {hint && (
        <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-950/60 px-3 py-1.5 rounded-lg border border-slate-800/80">
          <Info className="w-3.5 h-3.5 text-cyan-400/80 shrink-0" />
          <span>{hint}</span>
        </div>
      )}
    </div>
  );
}
