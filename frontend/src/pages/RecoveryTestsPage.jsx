import React, { useState, useMemo } from 'react';
import { 
  ShieldCheck, Filter, Search, Calendar, Eye, AlertOctagon, 
  CheckCircle2, XCircle, Clock, Database, Server, Activity, 
  FileText, Terminal, AlertTriangle 
} from 'lucide-react';
import StatusBadge from '../components/common/StatusBadge';
import LoadingState from '../components/common/LoadingState';
import EmptyState from '../components/common/EmptyState';
import ErrorState from '../components/common/ErrorState';
import Modal from '../components/common/Modal';
import { api } from '../api/client';

export default function RecoveryTestsPage({ 
  tests = [], 
  loading = false, 
  error = null 
}) {
  // Filters
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [dateFilter, setDateFilter] = useState('ALL'); // ALL, TODAY, WEEK

  // Detail Modal State
  const [selectedTest, setSelectedTest] = useState(null);
  const [testValidations, setTestValidations] = useState([]);
  const [testReportData, setTestReportData] = useState(null);
  const [modalLoading, setModalLoading] = useState(false);

  // Filtered Tests
  const filteredTests = useMemo(() => {
    return tests.filter((t) => {
      // Status filter
      if (statusFilter !== 'ALL' && t.status !== statusFilter) {
        return false;
      }
      // Search filter (test_id, application_name, backup_id)
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesId = t.test_id.toLowerCase().includes(q);
        const matchesApp = t.application_name.toLowerCase().includes(q);
        const matchesBkp = (t.backup_id || '').toLowerCase().includes(q);
        if (!matchesId && !matchesApp && !matchesBkp) return false;
      }
      // Date filter
      if (dateFilter !== 'ALL' && t.started_at) {
        const testDate = new Date(t.started_at);
        const now = new Date();
        if (dateFilter === 'TODAY') {
          const isToday = testDate.toDateString() === now.toDateString();
          if (!isToday) return false;
        } else if (dateFilter === 'WEEK') {
          const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
          if (testDate < sevenDaysAgo) return false;
        }
      }
      return true;
    });
  }, [tests, statusFilter, searchQuery, dateFilter]);

  const handleOpenDetailModal = async (test) => {
    setSelectedTest(test);
    setModalLoading(true);
    setTestValidations([]);
    setTestReportData(null);

    try {
      // Fetch validations and report data in parallel
      const [valRes, repRes] = await Promise.allSettled([
        api.getValidations(test.test_id),
        api.getReportById(test.test_id)
      ]);

      if (valRes.status === 'fulfilled') {
        setTestValidations(valRes.value);
      }
      if (repRes.status === 'fulfilled') {
        setTestReportData(repRes.value);
      }
    } catch (err) {
      console.error("Failed to load drill details:", err);
    } finally {
      setModalLoading(false);
    }
  };

  if (loading && tests.length === 0) {
    return <LoadingState message="Fetching recovery drill history..." rows={6} />;
  }

  if (error) {
    return <ErrorState title="Failed to Load Recovery Tests" message={error.message || String(error)} />;
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Recovery Test Executions</h2>
          <p className="text-sm text-slate-400 mt-1">
            Historical disaster recovery drill runs, validation stage checks, and diagnostic logs.
          </p>
        </div>
        <div className="text-xs text-slate-400 bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800 font-mono">
          Showing <strong>{filteredTests.length}</strong> of <strong>{tests.length}</strong> drills
        </div>
      </div>

      {/* Filters Bar */}
      <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by Test ID, Application, or Backup ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950/80 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/80 transition"
          />
        </div>

        {/* Status Filter */}
        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-slate-400 hidden sm:block" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-950/80 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500/80 transition"
          >
            <option value="ALL">All Statuses</option>
            <option value="SUCCESS">SUCCESS / PASS</option>
            <option value="FAILED">FAILED / ERROR</option>
            <option value="RUNNING">RUNNING</option>
            <option value="PENDING">PENDING</option>
          </select>

          {/* Date Filter */}
          <select
            value={dateFilter}
            onChange={(e) => setDateFilter(e.target.value)}
            className="bg-slate-950/80 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500/80 transition"
          >
            <option value="ALL">All Dates</option>
            <option value="TODAY">Today</option>
            <option value="WEEK">Last 7 Days</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        {filteredTests.length === 0 ? (
          <EmptyState 
            icon={ShieldCheck}
            title="No Matching Recovery Tests" 
            description={tests.length === 0 ? "No drills have been recorded yet." : "No tests match the current filter criteria."}
            hint="Adjust filters or search query to view historical drill records."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-950/60 text-slate-400 text-xs uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3.5">Test ID</th>
                  <th className="px-6 py-3.5">Application</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5">Drill Duration</th>
                  <th className="px-6 py-3.5">Backup Reference</th>
                  <th className="px-6 py-3.5">Executed At</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {filteredTests.map((test) => (
                  <tr key={test.test_id} className="hover:bg-slate-800/40 transition">
                    <td className="px-6 py-4 font-mono text-xs text-cyan-300 font-semibold">
                      {test.test_id.slice(0, 8)}...
                    </td>
                    <td className="px-6 py-4 font-medium text-white">
                      {test.application_name}
                      <span className="block text-[11px] text-slate-400 font-normal capitalize">
                        {test.environment}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={test.status} />
                    </td>
                    <td className="px-6 py-4 text-xs font-mono text-slate-200">
                      {test.restore_duration_seconds ? `${test.restore_duration_seconds.toFixed(2)}s` : '—'}
                    </td>
                    <td className="px-6 py-4 font-mono text-xs text-slate-400">
                      {test.backup_id}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-400">
                      {new Date(test.started_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => handleOpenDetailModal(test)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700/80 text-cyan-300 hover:text-cyan-200 text-xs font-medium border border-slate-700/80 transition"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspect Checks</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Drill Detail & Validation Checks Modal */}
      <Modal
        isOpen={!!selectedTest}
        onClose={() => setSelectedTest(null)}
        title={`Recovery Drill Inspection: ${selectedTest?.test_id ? selectedTest.test_id.slice(0, 8) : ''}`}
        subtitle={`${selectedTest?.application_name || ''} (${selectedTest?.environment || 'production'})`}
        maxWidth="max-w-4xl"
      >
        {selectedTest && (
          <div className="space-y-6">
            {/* Header Summary Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800">
                <span className="text-slate-500 block text-[10px] uppercase">Final Outcome</span>
                <div className="mt-1"><StatusBadge status={selectedTest.status} /></div>
              </div>
              <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800">
                <span className="text-slate-500 block text-[10px] uppercase">Restore Duration</span>
                <span className="text-sm font-bold font-mono text-cyan-400 block mt-1">
                  {selectedTest.restore_duration_seconds ? `${selectedTest.restore_duration_seconds.toFixed(2)}s` : 'N/A'}
                </span>
              </div>
              <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800">
                <span className="text-slate-500 block text-[10px] uppercase">Backup ID</span>
                <span className="text-xs font-mono text-slate-300 block mt-1 truncate" title={selectedTest.backup_id}>
                  {selectedTest.backup_id}
                </span>
              </div>
              <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800">
                <span className="text-slate-500 block text-[10px] uppercase">Sandbox DB</span>
                <span className="text-xs font-mono text-slate-300 block mt-1 truncate" title={selectedTest.isolated_target_db}>
                  {selectedTest.isolated_target_db || 'cloudguard_isolated_test'}
                </span>
              </div>
            </div>

            {/* Modal Content - Loading vs Loaded */}
            {modalLoading ? (
              <LoadingState message="Retrieving validation check results and diagnostic traces..." rows={4} />
            ) : (
              <>
                {/* Detected Failures Alert (if any) */}
                {(testReportData?.detected_failures && testReportData.detected_failures.length > 0) || selectedTest.error_details ? (
                  <div className="p-4 rounded-xl bg-rose-950/30 border border-rose-900/60 space-y-3">
                    <div className="flex items-center gap-2 text-rose-400 font-semibold text-xs">
                      <AlertOctagon className="w-4 h-4 shrink-0" />
                      <span>Detected Failures &amp; Diagnostic Issues</span>
                    </div>

                    {testReportData?.detected_failures?.map((f, idx) => (
                      <div key={idx} className="p-3 bg-slate-950/80 rounded-lg border border-rose-900/40 text-xs">
                        <div className="font-semibold text-rose-300 flex items-center justify-between">
                          <span>[{f.category}] {f.check_name}</span>
                        </div>
                        <p className="text-slate-300 mt-1">{f.error_message}</p>
                        {f.observed_value && (
                          <div className="text-[11px] font-mono text-slate-400 mt-1">
                            Observed: <code className="text-rose-400">{f.observed_value}</code> | Expected: <code className="text-emerald-400">{f.expected_value}</code>
                          </div>
                        )}
                      </div>
                    ))}

                    {selectedTest.error_details && !testReportData?.detected_failures?.length && (
                      <div className="p-3 bg-slate-950/80 rounded-lg border border-rose-900/40 text-xs text-rose-300 font-mono">
                        {selectedTest.error_details}
                      </div>
                    )}
                  </div>
                ) : null}

                {/* Granular Validation Checks List */}
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                    <span>Stage-by-Stage Verification Checks</span>
                  </h4>

                  {testValidations.length === 0 ? (
                    <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800 text-xs text-slate-400 text-center">
                      No discrete validation check records found for this test run.
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {testValidations.map((v) => {
                        let parsed = {};
                        try {
                          parsed = typeof v.details_json === 'string' ? JSON.parse(v.details_json) : v.details_json;
                        } catch {}
                        return (
                          <div 
                            key={v.id} 
                            className="p-3.5 bg-slate-950/80 rounded-xl border border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-2"
                          >
                            <div className="flex items-center gap-3">
                              {v.passed ? (
                                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                              ) : (
                                <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
                              )}
                              <div>
                                <span className="font-semibold text-xs text-white">
                                  {v.validation_type.replace(/_/g, ' ')}
                                </span>
                                {parsed.observed_value && (
                                  <div className="text-[11px] font-mono text-slate-400 mt-0.5">
                                    Observed: {parsed.observed_value} (Expected: {parsed.expected_value})
                                  </div>
                                )}
                              </div>
                            </div>
                            <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                              v.passed 
                                ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/80' 
                                : 'bg-rose-950 text-rose-400 border border-rose-800/80'
                            }`}>
                              {v.passed ? 'PASSED' : 'FAILED'}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Execution Logs Snippet */}
                {selectedTest.logs && (
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-2">
                      <Terminal className="w-4 h-4 text-indigo-400" />
                      <span>Execution Logs</span>
                    </h4>
                    <pre className="p-4 bg-slate-950 rounded-xl border border-slate-800 font-mono text-[11px] text-slate-300 max-h-48 overflow-y-auto whitespace-pre-wrap">
                      {selectedTest.logs}
                    </pre>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
