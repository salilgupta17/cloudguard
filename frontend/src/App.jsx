import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/common/Navbar';
import Sidebar from './components/common/Sidebar';
import OverviewPage from './pages/OverviewPage';
import ApplicationsPage from './pages/ApplicationsPage';
import RecoveryTestsPage from './pages/RecoveryTestsPage';
import ReportsPage from './pages/ReportsPage';
import MonitoringPage from './pages/MonitoringPage';
import { api } from './api/client';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  
  // Data state
  const [tests, setTests] = useState([]);
  const [reports, setReports] = useState([]);
  const [backups, setBackups] = useState([]);
  const [applications, setApplications] = useState([]);
  const [healthStatus, setHealthStatus] = useState({ status: 'checking' });
  
  // Loading & Error states
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState(null);

  // Fetch all dashboard data from real FastAPI endpoints
  const fetchAllData = useCallback(async (isManualRefresh = false) => {
    if (isManualRefresh) {
      setIsRefreshing(true);
    }
    setError(null);

    try {
      // 1. Health check (independent failure tolerance)
      api.getReadiness()
        .then(setHealthStatus)
        .catch(() => setHealthStatus({ status: 'offline' }));

      // 2. Fetch business telemetry in parallel
      const [testsRes, reportsRes, backupsRes, appsRes] = await Promise.allSettled([
        api.getRecoveryTests({ limit: 100 }),
        api.getReports({ limit: 100 }),
        api.getBackups({ limit: 100 }),
        api.getApplications()
      ]);

      if (testsRes.status === 'fulfilled') {
        setTests(Array.isArray(testsRes.value) ? testsRes.value : []);
      } else {
        console.error("Failed fetching recovery tests:", testsRes.reason);
      }

      if (reportsRes.status === 'fulfilled') {
        setReports(Array.isArray(reportsRes.value) ? reportsRes.value : []);
      } else {
        console.error("Failed fetching reports:", reportsRes.reason);
      }

      if (backupsRes.status === 'fulfilled') {
        setBackups(Array.isArray(backupsRes.value) ? backupsRes.value : []);
      } else {
        console.error("Failed fetching backups:", backupsRes.reason);
      }

      if (appsRes.status === 'fulfilled') {
        setApplications(Array.isArray(appsRes.value) ? appsRes.value : []);
      } else {
        console.error("Failed fetching applications:", appsRes.reason);
      }

      // If all data queries failed, set error
      if (
        testsRes.status === 'rejected' &&
        reportsRes.status === 'rejected' &&
        backupsRes.status === 'rejected'
      ) {
        setError(new Error("Unable to connect to CloudGuard FastAPI backend. Please verify the API server is running on port 8000."));
      }
    } catch (err) {
      console.error("Fatal dashboard synchronization error:", err);
      setError(err);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  // Initial load and periodic polling
  useEffect(() => {
    fetchAllData();
    const interval = setInterval(() => {
      fetchAllData();
    }, 10000);
    return () => clearInterval(interval);
  }, [fetchAllData]);

  return (
    <div className="min-h-screen bg-[#0B0F19] text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-white">
      {/* Top Navbar */}
      <Navbar 
        healthStatus={healthStatus} 
        onRefresh={() => fetchAllData(true)} 
        isRefreshing={isRefreshing} 
      />

      {/* Main Content Layout */}
      <div className="flex-1 flex flex-col md:flex-row">
        {/* Left Sidebar */}
        <Sidebar activeTab={activeTab} onSelectTab={setActiveTab} />

        {/* Dynamic Page Container */}
        <main className="flex-1 p-4 md:p-8 max-w-7xl mx-auto w-full">
          {activeTab === 'overview' && (
            <OverviewPage
              tests={tests}
              reports={reports}
              applications={applications}
              loading={loading}
              error={error}
              onNavigateToTests={() => setActiveTab('recovery-tests')}
              onNavigateToReports={() => setActiveTab('reports')}
            />
          )}

          {activeTab === 'applications' && (
            <ApplicationsPage
              applications={applications}
              backups={backups}
              tests={tests}
              loading={loading}
              error={error}
            />
          )}

          {activeTab === 'recovery-tests' && (
            <RecoveryTestsPage
              tests={tests}
              loading={loading}
              error={error}
            />
          )}

          {activeTab === 'reports' && (
            <ReportsPage
              reports={reports}
              loading={loading}
              error={error}
            />
          )}

          {activeTab === 'monitoring' && (
            <MonitoringPage
              tests={tests}
              reports={reports}
              loading={loading}
              error={error}
            />
          )}
        </main>
      </div>

      {/* Audit Platform Footer */}
      <footer className="border-t border-slate-900 bg-[#070A11] px-6 py-4 text-center text-xs text-slate-500">
        <p>
          CloudGuard V1 — AWS Disaster Recovery Verification and Monitoring Platform.
        </p>
        <p className="text-[11px] text-slate-600 mt-0.5">
          Read-only audit observations. Sandbox restore verification only; no automated production interventions.
        </p>
      </footer>
    </div>
  );
}
