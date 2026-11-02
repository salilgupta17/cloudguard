import React, { useState } from 'react';
import { 
  FileText, Download, Eye, ShieldCheck, CheckCircle2, 
  XCircle, Clock, AlertTriangle, ExternalLink, Code 
} from 'lucide-react';
import StatusBadge from '../components/common/StatusBadge';
import LoadingState from '../components/common/LoadingState';
import EmptyState from '../components/common/EmptyState';
import ErrorState from '../components/common/ErrorState';
import Modal from '../components/common/Modal';
import { api } from '../api/client';

export default function ReportsPage({ 
  reports = [], 
  loading = false, 
  error = null 
}) {
  const [selectedReport, setSelectedReport] = useState(null);
  const [previewTab, setPreviewTab] = useState('summary'); // summary, html, json
  const [reportDetails, setReportDetails] = useState(null);
  const [htmlContent, setHtmlContent] = useState('');
  const [previewLoading, setPreviewLoading] = useState(false);

  const handleOpenPreview = async (report) => {
    setSelectedReport(report);
    setPreviewTab('summary');
    setPreviewLoading(true);
    setReportDetails(null);
    setHtmlContent('');

    const targetId = report.test_id || report.report_id;

    try {
      // Fetch JSON details and HTML preview in parallel
      const [jsonRes, htmlRes] = await Promise.allSettled([
        api.getReportById(targetId),
        api.getReportHtml(targetId)
      ]);

      if (jsonRes.status === 'fulfilled') {
        setReportDetails(jsonRes.value);
      }
      if (htmlRes.status === 'fulfilled') {
        setHtmlContent(htmlRes.value);
      }
    } catch (err) {
      console.error("Failed to load report preview:", err);
    } finally {
      setPreviewLoading(false);
    }
  };

  if (loading && reports.length === 0) {
    return <LoadingState message="Cataloging auditable disaster recovery reports..." rows={5} />;
  }

  if (error) {
    return <ErrorState title="Failed to Load Disaster Recovery Reports" message={error.message || String(error)} />;
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Disaster Recovery Reports</h2>
          <p className="text-sm text-slate-400 mt-1">
            Formal audit-ready recovery reports containing all 15 compliance items in JSON, PDF, and HTML.
          </p>
        </div>
        <div className="text-xs text-slate-400 bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800 font-mono">
          <strong>{reports.length}</strong> reports generated
        </div>
      </div>

      {/* Reports Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        {reports.length === 0 ? (
          <EmptyState 
            icon={FileText}
            title="No DR Reports Cataloged" 
            description="Reports are generated automatically upon completion of a disaster recovery verification drill."
            hint="Trigger drills to generate compliant JSON, PDF, and HTML audit artifacts."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-950/60 text-slate-400 text-xs uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3.5">Report ID</th>
                  <th className="px-6 py-3.5">Test Reference</th>
                  <th className="px-6 py-3.5">Outcome</th>
                  <th className="px-6 py-3.5">Observed RTO</th>
                  <th className="px-6 py-3.5">Backup Age (RPO)</th>
                  <th className="px-6 py-3.5">Generated At</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {reports.map((r) => {
                  const targetId = r.test_id || r.report_id;
                  return (
                    <tr key={r.report_id} className="hover:bg-slate-800/40 transition">
                      <td className="px-6 py-4 font-mono text-xs text-cyan-300 font-semibold">
                        {r.report_id.slice(0, 8)}...
                      </td>
                      <td className="px-6 py-4 font-mono text-xs text-slate-300">
                        {r.test_id ? `${r.test_id.slice(0, 8)}...` : 'N/A'}
                      </td>
                      <td className="px-6 py-4">
                        <StatusBadge status={r.status} />
                      </td>
                      <td className="px-6 py-4 font-mono text-xs text-slate-300">
                        {typeof r.rto_seconds === 'number' ? `${r.rto_seconds.toFixed(2)}s` : '—'}
                      </td>
                      <td className="px-6 py-4 font-mono text-xs text-slate-400">
                        {typeof r.rpo_minutes === 'number' ? `${r.rpo_minutes.toFixed(1)} min` : '—'}
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-400">
                        {new Date(r.created_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 text-right space-x-2">
                        {/* Preview Button */}
                        <button
                          onClick={() => handleOpenPreview(r)}
                          className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700/80 text-cyan-300 text-xs font-medium border border-slate-700/80 transition"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>Preview</span>
                        </button>

                        {/* Download PDF */}
                        <a
                          href={api.getDownloadUrl(targetId, 'pdf')}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-cyan-950/80 hover:bg-cyan-900 text-cyan-300 text-xs font-medium border border-cyan-800/80 transition"
                          title="Download official PDF report"
                        >
                          <Download className="w-3.5 h-3.5" />
                          <span>PDF</span>
                        </a>

                        {/* Download JSON */}
                        <a
                          href={api.getDownloadUrl(targetId, 'json')}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-indigo-950/80 hover:bg-indigo-900 text-indigo-300 text-xs font-medium border border-indigo-800/80 transition"
                          title="Download machine-readable JSON report"
                        >
                          <Download className="w-3.5 h-3.5" />
                          <span>JSON</span>
                        </a>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Report Preview Modal */}
      <Modal
        isOpen={!!selectedReport}
        onClose={() => setSelectedReport(null)}
        title={`Disaster Recovery Report Preview: ${selectedReport?.report_id ? selectedReport.report_id.slice(0, 8) : ''}`}
        subtitle={`Test ID: ${selectedReport?.test_id || 'N/A'}`}
        maxWidth="max-w-5xl"
      >
        {selectedReport && (
          <div className="space-y-4">
            {/* Action Bar inside Modal: Tabs & Direct Downloads */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
              {/* Tabs */}
              <div className="flex gap-2">
                <button
                  onClick={() => setPreviewTab('summary')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                    previewTab === 'summary'
                      ? 'bg-cyan-950 text-cyan-300 border border-cyan-800'
                      : 'bg-slate-900 text-slate-400 hover:text-white'
                  }`}
                >
                  Executive Summary
                </button>
                <button
                  onClick={() => setPreviewTab('html')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                    previewTab === 'html'
                      ? 'bg-cyan-950 text-cyan-300 border border-cyan-800'
                      : 'bg-slate-900 text-slate-400 hover:text-white'
                  }`}
                >
                  Rendered HTML View
                </button>
                <button
                  onClick={() => setPreviewTab('json')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                    previewTab === 'json'
                      ? 'bg-cyan-950 text-cyan-300 border border-cyan-800'
                      : 'bg-slate-900 text-slate-400 hover:text-white'
                  }`}
                >
                  Raw 15-Item JSON
                </button>
              </div>

              {/* Direct Downloads */}
              <div className="flex items-center gap-2">
                <a
                  href={api.getDownloadUrl(selectedReport.test_id || selectedReport.report_id, 'pdf')}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-semibold shadow-sm transition"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download PDF</span>
                </a>
                <a
                  href={api.getDownloadUrl(selectedReport.test_id || selectedReport.report_id, 'json')}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold border border-slate-700 transition"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download JSON</span>
                </a>
              </div>
            </div>

            {/* Modal Body Based on Tab */}
            {previewLoading ? (
              <LoadingState message="Compiling report formats..." rows={5} />
            ) : previewTab === 'summary' ? (
              <div className="space-y-4">
                {/* 15-Item Key Metrics Grid */}
                {reportDetails && (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                    <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800">
                      <span className="text-slate-500 block text-[10px] uppercase">Application</span>
                      <strong className="text-white block mt-0.5 truncate">{reportDetails.application_name}</strong>
                    </div>
                    <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800">
                      <span className="text-slate-500 block text-[10px] uppercase">Final Outcome</span>
                      <div className="mt-1"><StatusBadge status={reportDetails.final_status} /></div>
                    </div>
                    <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800">
                      <span className="text-slate-500 block text-[10px] uppercase">Observed Duration</span>
                      <strong className="text-cyan-400 block mt-0.5 font-mono">{reportDetails.recovery_drill_duration_seconds?.toFixed(2)}s</strong>
                    </div>
                    <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800">
                      <span className="text-slate-500 block text-[10px] uppercase">Backup Freshness</span>
                      <strong className="text-indigo-400 block mt-0.5 font-mono">{reportDetails.backup_age_minutes?.toFixed(1)}m</strong>
                    </div>
                  </div>
                )}

                {/* Executive Summary Text */}
                <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Executive Summary</h4>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {selectedReport.summary || reportDetails?.executive_summary || 'Disaster recovery verification drill completed.'}
                  </p>
                </div>

                {/* Methodological Caveats */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="p-3.5 bg-slate-950/90 rounded-xl border border-slate-800">
                    <strong className="text-cyan-400 block mb-1">RTO Boundary Note:</strong>
                    <p className="text-[11px] text-slate-400 leading-relaxed">
                      {reportDetails?.rto_methodological_note || 
                        "Observed recovery drill duration reflects synthetic sandbox restore + validation time. Actual production RTO includes DNS cutover, traffic diversion, and application cluster scaling."}
                    </p>
                  </div>
                  <div className="p-3.5 bg-slate-950/90 rounded-xl border border-slate-800">
                    <strong className="text-indigo-400 block mb-1">RPO Boundary Note:</strong>
                    <p className="text-[11px] text-slate-400 leading-relaxed">
                      {reportDetails?.rpo_methodological_note || 
                        "Backup age reflects snapshot freshness at drill execution. Actual RPO requires transaction log replay and ledger audit; snapshot age alone does not guarantee zero data loss."}
                    </p>
                  </div>
                </div>

                {/* Health Checks Breakdown */}
                {reportDetails && (
                  <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">System Health &amp; Integrity Breakdown</h4>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${reportDetails.database_health?.passed ? 'bg-emerald-400' : 'bg-rose-400'}`}></span>
                        <span className="text-slate-300">Database Health</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${reportDetails.docker_application_health?.passed ? 'bg-emerald-400' : 'bg-rose-400'}`}></span>
                        <span className="text-slate-300">Docker App Health</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${reportDetails.api_validation_results?.passed ? 'bg-emerald-400' : 'bg-rose-400'}`}></span>
                        <span className="text-slate-300">API Probes</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${reportDetails.data_integrity_checks?.passed ? 'bg-emerald-400' : 'bg-rose-400'}`}></span>
                        <span className="text-slate-300">Data Integrity</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : previewTab === 'html' ? (
              <div className="rounded-xl overflow-hidden border border-slate-800 bg-white">
                <iframe
                  title="HTML Report Preview"
                  srcDoc={htmlContent}
                  className="w-full h-[550px] border-0"
                  sandbox="allow-same-origin"
                />
              </div>
            ) : (
              <pre className="p-4 bg-slate-950 rounded-xl border border-slate-800 font-mono text-[11px] text-cyan-300 max-h-[500px] overflow-auto">
                {reportDetails ? JSON.stringify(reportDetails, null, 2) : 'No JSON payload available'}
              </pre>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
