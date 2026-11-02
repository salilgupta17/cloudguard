import React from 'react';
import { Loader2 } from 'lucide-react';

export default function LoadingState({ message = "Loading disaster recovery telemetry...", rows = 3 }) {
  return (
    <div className="w-full p-8 flex flex-col items-center justify-center text-center">
      <div className="flex items-center gap-3 text-cyan-400 mb-4">
        <Loader2 className="w-6 h-6 animate-spin text-cyan-400" />
        <span className="text-sm font-medium text-slate-300">{message}</span>
      </div>
      <div className="w-full max-w-2xl space-y-3">
        {Array.from({ length: rows }).map((_, i) => (
          <div 
            key={i} 
            className="h-12 w-full bg-slate-800/40 rounded-xl animate-pulse border border-slate-800/60"
            style={{ animationDelay: `${i * 150}ms` }}
          />
        ))}
      </div>
    </div>
  );
}
