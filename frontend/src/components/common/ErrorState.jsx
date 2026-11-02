import React from 'react';
import { AlertOctagon, Terminal } from 'lucide-react';

export default function ErrorState({ 
  title = "Telemetry Synchronization Failure", 
  message = "Failed to communicate with CloudGuard FastAPI backend.",
  details = null
}) {
  return (
    <div className="w-full p-8 bg-rose-950/20 border border-rose-900/40 rounded-2xl text-left">
      <div className="flex items-start gap-4">
        <div className="p-3 rounded-xl bg-rose-900/30 border border-rose-800/50 text-rose-400 shrink-0">
          <AlertOctagon className="w-6 h-6" />
        </div>
        <div className="flex-1">
          <h3 className="text-base font-semibold text-rose-200 mb-1">{title}</h3>
          <p className="text-sm text-rose-300/80 mb-3">{message}</p>
          {details && (
            <div className="mt-3 p-3 bg-slate-950/80 rounded-xl border border-slate-800 font-mono text-xs text-rose-300 overflow-x-auto flex items-start gap-2">
              <Terminal className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
              <span>{typeof details === 'string' ? details : JSON.stringify(details, null, 2)}</span>
            </div>
          )}
          <div className="mt-3 text-xs text-slate-400">
            CloudGuard reporting engine is operating in read-only observation mode. Verify API network reachability and database service status.
          </div>
        </div>
      </div>
    </div>
  );
}
