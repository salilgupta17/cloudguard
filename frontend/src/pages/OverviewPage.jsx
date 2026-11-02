import React from 'react';
import { 
  ShieldCheck, Activity, Database, Server, RefreshCw, FileText, 
  CheckCircle2, XCircle, Clock, Zap, ArrowRight, AlertTriangle 
} from 'lucide-react';
import StatusBadge from '../components/common/StatusBadge';
import LoadingState from '../components/common/LoadingState';
import EmptyState from '../components/common/EmptyState';
import ErrorState from '../components/common/ErrorState';

export default function OverviewPage({ 
  tests = [], 
  reports = [], 
  applications = [],
  loading = false, 
  error = null,
  onNavigateToTests,
  onNavigateToReports
}) {
  if (loading && tests.length === 0) {
    return <LoadingState message="Aggregating disaster recovery drill telemetry..." rows={5} />;
  }

  if (error) {
    return <ErrorState title="Failed to Load Overview Metrics" message={error.message || String(error)} />;
  }

  // Real KPI calculations
  const totalTests = tests.length;
  const passedTests = tests.filter(t => t.status === 'SUCCESS').length;
  const failedTests = tests.filter(t => t.status === 'FAILED' || t.status === 'ERROR').length;
  const runningTests = tests.filter(t => t.status === 'RUNNING').length;

  // Latest test
  const latestTest = tests.length > 0 ? tests[0] : null;

  // Average recovery drill duration (restore_duration_seconds)
  const durations = tests
    .map(t => t.restore_duration_seconds)
    .filter(d => typeof d === 'number' && d > 0);
  const avgDuration = durations.length > 0
    ? (durations.reduce((acc, curr) => acc + curr, 0) / durations.length).toFixed(2)
    : 'N/A';

  const successRate = totalTests > 0 
    ? ((passedTests / totalTests) * 100).toFixed(1) 
    : '0.0';

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Page Title & Status */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Disaster Recovery Overview</h2>
          <p className="text-sm text-slate-400 mt-1">
            Real-time verification telemetry for isolated sandbox database and application restoration.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
          <Clock className="w-3.5 h-3.5 text-cyan-400" />
          <span>Latest Evaluation: <strong>{latestTest ? new Date(latestTest.started_at).toLocaleString() : 'No Drills Yet'}</strong></span>
        </div>
      </div>

      {/* KPI Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Tests */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
            <span>Total Recovery Tests</span>
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-extrabold text-white tracking-tight">{totalTests}</div>
          <div className="text-[11px] text-slate-500 mt-1.5 flex items-center gap-1">
            <span>{runningTests > 0 ? `${runningTests} active execution` : 'All historical drills'}</span>
          </div>
        </div>

        {/* Passed Tests */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
            <span>Passed Tests</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold text-emerald-400 tracking-tight">{passedTests}</div>
          <div className="text-[11px] text-slate-500 mt-1.5">
            {successRate}% overall success rate
          </div>
        </div>

        {/* Failed Tests */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
            <span>Failed Tests</span>
            <XCircle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-3xl font-extrabold text-rose-400 tracking-tight">{failedTests}</div>
          <div className="text-[11px] text-slate-500 mt-1.5">
            {failedTests === 0 ? 'Zero failures detected' : 'Diagnostic issues flagged'}
          </div>
        </div>

        {/* Average Recovery Duration */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
            <span>Avg Drill Duration</span>
            <Zap className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-3xl font-extrabold text-cyan-300 tracking-tight">
            {avgDuration === 'N/A' ? 'N/A' : `${avgDuration}s`}
          </div>
          <div className="text-[11px] text-slate-500 mt-1.5">
            Target SLA: &lt; 300.0s (RTO)
          </div>
        </div>

        {/* Latest Test Result */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
            <span>Latest Test Result</span>
            <Activity className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-1">
            {latestTest ? (
              <StatusBadge status={latestTest.status} size="lg" />
            ) : (
              <span className="text-xs text-slate-500 font-mono">No Runs</span>
            )}
          </div>
          <div className="text-[11px] text-slate-500 mt-2 truncate font-mono">
            {latestTest ? `${latestTest.application_name}` : 'Awaiting initial drill'}
          </div>
        </div>
      </div>

      {/* DR Pipeline Flow Diagram */}
      <div className="p-6 rounded-2xl bg-gradient-to-b from-slate-900/90 to-slate-950/90 border border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
              CloudGuard Disaster Recovery Architecture Flow
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Strictly isolated test loop — production state is never mutated.
            </p>
          </div>
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-950/80 text-cyan-400 border border-cyan-800/80 font-mono">
            Isolated Sandbox
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-6 gap-3 pt-2">
          {/* Step 1 */}
          <div className="flex flex-col items-center p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-center relative">
            <Server className="w-5 h-5 text-cyan-400 mb-2" />
            <span className="text-xs font-semibold text-slate-200">1. Demo Workload</span>
            <span className="text-[10px] text-slate-400 mt-0.5">FastAPI &amp; PostgreSQL</span>
          </div>

          {/* Step 2 */}
          <div className="flex flex-col items-center p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
            <Database className="w-5 h-5 text-indigo-400 mb-2" />
            <span className="text-xs font-semibold text-slate-200">2. Primary DB</span>
            <span className="text-[10px] text-slate-400 mt-0.5">Transactional Ledger</span>
          </div>

          {/* Step 3 */}
          <div className="flex flex-col items-center p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
            <RefreshCw className="w-5 h-5 text-emerald-400 mb-2" />
            <span className="text-xs font-semibold text-slate-200">3. Snapshot Manifest</span>
            <span className="text-[10px] text-slate-400 mt-0.5">pg_dump + SHA-256</span>
          </div>

          {/* Step 4 */}
          <div className="flex flex-col items-center p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
            <ShieldCheck className="w-5 h-5 text-amber-400 mb-2" />
            <span className="text-xs font-semibold text-slate-200">4. Isolated Restore</span>
            <span className="text-[10px] text-slate-400 mt-0.5">Target Sandbox DB</span>
          </div>

          {/* Step 5 */}
          <div className="flex flex-col items-center p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
            <Activity className="w-5 h-5 text-sky-400 mb-2" />
            <span className="text-xs font-semibold text-slate-200">5. Validation Suite</span>
            <span className="text-[10px] text-slate-400 mt-0.5">Checksum &amp; Health Probes</span>
          </div>

          {/* Step 6 */}
          <div className="flex flex-col items-center p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
            <FileText className="w-5 h-5 text-purple-400 mb-2" />
            <span className="text-xs font-semibold text-slate-200">6. DR Report</span>
            <span className="text-[10px] text-slate-400 mt-0.5">JSON, PDF &amp; HTML</span>
          </div>
        </div>
      </div>

      {/* SLA Benchmarks and Methodological Boundary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* RTO Benchmark Card */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold uppercase text-slate-400">Target RTO SLA</span>
            <span className="text-xs text-cyan-400 font-semibold">&lt; 300 Seconds</span>
          </div>
          <div className="text-xl font-bold text-white mb-2">
            Recovery Time Objective
          </div>
          <p className="text-xs text-slate-400 leading-relaxed mb-3">
            Measures restore duration and validation execution in the isolated test environment.
          </p>
          <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800/80 text-[11px] text-slate-400">
            <strong className="text-cyan-400 block mb-0.5">Methodological Distinction:</strong>
            Observed drill duration reflects synthetic sandbox restore + validation time. Actual production RTO includes DNS cutover, traffic diversion, and application cluster scaling.
          </div>
        </div>

        {/* RPO Benchmark Card */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold uppercase text-slate-400">Target RPO SLA</span>
            <span className="text-xs text-indigo-400 font-semibold">&lt; 60 Minutes</span>
          </div>
          <div className="text-xl font-bold text-white mb-2">
            Recovery Point Objective
          </div>
          <p className="text-xs text-slate-400 leading-relaxed mb-3">
            Monitors snapshot age and transaction ledger completeness against backup manifests.
          </p>
          <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800/80 text-[11px] text-slate-400">
            <strong className="text-indigo-400 block mb-0.5">Methodological Distinction:</strong>
            Backup age reflects snapshot freshness at drill execution. Actual RPO requires transaction log replay and ledger audit; snapshot age alone does not guarantee zero data loss.
          </div>
        </div>
      </div>

      {/* Recent Drill Activity Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-white text-base">Recent Recovery Drill Executions</h3>
            <p className="text-xs text-slate-400 mt-0.5">Automated validation runs recorded by CloudGuard</p>
          </div>
          {onNavigateToTests && (
            <button
              onClick={onNavigateToTests}
              className="flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 font-medium transition"
            >
              <span>View All Tests</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {totalTests === 0 ? (
          <EmptyState 
            title="No Recovery Tests Recorded" 
            description="No disaster recovery drills have been executed yet."
            hint="Trigger drills via the CloudGuard API or test pipeline to populate records."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-950/60 text-slate-400 text-xs uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3">Test ID</th>
                  <th className="px-6 py-3">Application</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Drill Duration</th>
                  <th className="px-6 py-3">Started At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {tests.slice(0, 5).map((test) => (
                  <tr key={test.test_id} className="hover:bg-slate-800/40 transition">
                    <td className="px-6 py-4 font-mono text-xs text-cyan-300">
                      {test.test_id.slice(0, 8)}...
                    </td>
                    <td className="px-6 py-4 font-medium text-white">
                      {test.application_name}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={test.status} />
                    </td>
                    <td className="px-6 py-4 text-xs font-mono text-slate-300">
                      {test.restore_duration_seconds ? `${test.restore_duration_seconds.toFixed(2)}s` : '—'}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-400">
                      {new Date(test.started_at).toLocaleString()}
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
