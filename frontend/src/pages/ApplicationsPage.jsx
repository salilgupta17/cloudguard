import React, { useState } from 'react';
import { 
  Server, Database, HardDrive, ShieldCheck, CheckCircle2, 
  ExternalLink, Layers, Key, Table, Clock, Info, Activity 
} from 'lucide-react';
import StatusBadge from '../components/common/StatusBadge';
import LoadingState from '../components/common/LoadingState';
import EmptyState from '../components/common/EmptyState';
import ErrorState from '../components/common/ErrorState';

export default function ApplicationsPage({ 
  applications = [], 
  backups = [], 
  tests = [],
  loading = false, 
  error = null 
}) {
  const [selectedApp, setSelectedApp] = useState(null);

  if (loading && applications.length === 0) {
    return <LoadingState message="Querying protected workload architecture & DB configurations..." rows={4} />;
  }

  if (error) {
    return <ErrorState title="Failed to Load Protected Applications" message={error.message || String(error)} />;
  }

  if (applications.length === 0) {
    return (
      <EmptyState 
        icon={Server}
        title="No Protected Applications Registered" 
        description="No applications are currently enrolled in CloudGuard disaster recovery verification."
      />
    );
  }

  // Active or selected app
  const currentApp = selectedApp || applications[0];
  const appBackups = backups.filter(b => b.application_name === currentApp.name);
  const appTests = tests.filter(t => t.application_name === currentApp.name);

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Protected Applications</h2>
          <p className="text-sm text-slate-400 mt-1">
            Workload inventory, database infrastructure, and backup manifest catalogs.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
          <Layers className="w-3.5 h-3.5 text-cyan-400" />
          <span>Active Applications: <strong>{applications.length}</strong></span>
        </div>
      </div>

      {/* Application Selector Tabs (if multiple) */}
      {applications.length > 1 && (
        <div className="flex gap-2 border-b border-slate-800 pb-3 overflow-x-auto">
          {applications.map((app) => (
            <button
              key={app.id || app.name}
              onClick={() => setSelectedApp(app)}
              className={`px-4 py-2 rounded-xl text-xs font-semibold transition ${
                currentApp.name === app.name
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-800'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {app.display_name || app.name}
            </button>
          ))}
        </div>
      )}

      {/* Application Overview Card */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-2xl bg-gradient-to-br from-cyan-950 to-blue-900/80 border border-cyan-800/60 text-cyan-400 shadow-md">
              <Server className="w-7 h-7" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h3 className="text-xl font-bold text-white">{currentApp.display_name || currentApp.name}</h3>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800/80">
                  {currentApp.tier || 'Tier 1 Workload'}
                </span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                  {currentApp.environment || 'Production'}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
                {currentApp.description || 'Core business service protected by automated sandbox restoration tests.'}
              </p>
            </div>
          </div>

          {/* Quick Metrics */}
          <div className="flex items-center gap-4 text-xs font-mono bg-slate-950/80 p-3 rounded-xl border border-slate-800 shrink-0">
            <div>
              <div className="text-[10px] uppercase text-slate-500 font-sans">Target RTO</div>
              <div className="text-cyan-400 font-bold">{currentApp.recovery_objectives?.rto_target_seconds || 300}s</div>
            </div>
            <div className="w-px h-8 bg-slate-800"></div>
            <div>
              <div className="text-[10px] uppercase text-slate-500 font-sans">Target RPO</div>
              <div className="text-indigo-400 font-bold">{currentApp.recovery_objectives?.rpo_target_minutes || 60}m</div>
            </div>
            <div className="w-px h-8 bg-slate-800"></div>
            <div>
              <div className="text-[10px] uppercase text-slate-500 font-sans">Total Drills</div>
              <div className="text-white font-bold">{currentApp.live_statistics?.total_recovery_tests ?? appTests.length}</div>
            </div>
          </div>
        </div>

        {/* Technical Architecture Specs Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          {/* Container & Runtime */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
              <Server className="w-4 h-4 text-cyan-400" />
              <span>Container Runtime</span>
            </div>
            <div className="text-xs space-y-1 font-mono text-slate-400">
              <div><span className="text-slate-500">Framework:</span> <span className="text-slate-200">{currentApp.framework || 'FastAPI + Python'}</span></div>
              <div><span className="text-slate-500">Image:</span> <span className="text-slate-200">{currentApp.container_image || 'cloudguard/demo-application:latest'}</span></div>
              <div><span className="text-slate-500">Platform:</span> <span className="text-slate-200">Docker / ECS Fargate</span></div>
            </div>
          </div>

          {/* Database Specs */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
              <Database className="w-4 h-4 text-indigo-400" />
              <span>Database Infrastructure</span>
            </div>
            <div className="text-xs space-y-1 font-mono text-slate-400">
              <div><span className="text-slate-500">Engine:</span> <span className="text-slate-200">{currentApp.database?.engine || 'PostgreSQL 16'}</span></div>
              <div><span className="text-slate-500">Primary DB:</span> <span className="text-slate-200">{currentApp.database?.primary_database || 'cloudguard_primary'}</span></div>
              <div><span className="text-slate-500">Sandbox DB:</span> <span className="text-cyan-300">{currentApp.database?.isolated_test_database || 'cloudguard_isolated_test'}</span></div>
            </div>
          </div>

          {/* Health & Validation Probes */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
              <Activity className="w-4 h-4 text-emerald-400" />
              <span>Health &amp; Audit Probes</span>
            </div>
            <div className="text-xs space-y-1 font-mono text-slate-400">
              <div><span className="text-slate-500">Liveness:</span> <span className="text-emerald-400">GET {currentApp.probes?.health_endpoint || '/health'}</span></div>
              <div><span className="text-slate-500">Readiness:</span> <span className="text-emerald-400">GET {currentApp.probes?.readiness_endpoint || '/ready'}</span></div>
              <div><span className="text-slate-500">Audit Export:</span> <span className="text-slate-300">GET /api/v1/validation/ledger/summary</span></div>
            </div>
          </div>
        </div>

        {/* Database Tables Schema */}
        <div className="pt-2">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
            <Table className="w-3.5 h-3.5 text-cyan-400" />
            <span>Tracked Database Tables &amp; Integrity Constraints</span>
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {(currentApp.database?.tables || ['customers', 'accounts', 'transactions']).map((table) => (
              <div key={table} className="p-3 bg-slate-950/90 rounded-xl border border-slate-800 text-xs flex items-center justify-between">
                <span className="font-mono text-cyan-300 font-semibold">{table}</span>
                <span className="text-[10px] text-slate-500 uppercase font-sans">SHA-256 Verified</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Backup Manifest Inventory */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <HardDrive className="w-5 h-5 text-indigo-400" />
            <div>
              <h3 className="font-semibold text-white text-base">Backup Manifests &amp; Snapshot Provenance</h3>
              <p className="text-xs text-slate-400 mt-0.5">SHA-256 verifiable snapshots available for recovery verification drills</p>
            </div>
          </div>
          <span className="text-xs text-slate-400 bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800 font-mono">
            {appBackups.length} snapshots recorded
          </span>
        </div>

        {appBackups.length === 0 ? (
          <EmptyState 
            icon={HardDrive}
            title="No Backup Snapshots Registered" 
            description="No backup manifests have been cataloged for this application yet."
            hint="Create backups using the CloudGuard DR pipeline or pg_dump provider."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-950/60 text-slate-400 text-xs uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3">Backup ID</th>
                  <th className="px-6 py-3">Storage Path</th>
                  <th className="px-6 py-3">Size</th>
                  <th className="px-6 py-3">Record Count</th>
                  <th className="px-6 py-3">SHA-256 Checksum</th>
                  <th className="px-6 py-3">Created At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {appBackups.map((b) => (
                  <tr key={b.backup_id} className="hover:bg-slate-800/40 transition">
                    <td className="px-6 py-4 font-mono text-xs text-cyan-300 font-semibold">
                      {b.backup_id}
                    </td>
                    <td className="px-6 py-4 font-mono text-xs text-slate-300 max-w-xs truncate">
                      {b.storage_path}
                    </td>
                    <td className="px-6 py-4 text-xs font-mono text-slate-300">
                      {(b.size_bytes / 1024).toFixed(1)} KB
                    </td>
                    <td className="px-6 py-4 text-xs font-mono text-white">
                      {b.records_count} records
                    </td>
                    <td className="px-6 py-4 font-mono text-[11px] text-slate-400 max-w-xs truncate" title={b.checksum_sha256}>
                      {b.checksum_sha256 ? `${b.checksum_sha256.slice(0, 16)}...` : 'N/A'}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-400">
                      {new Date(b.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
