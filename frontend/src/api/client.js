/**
 * CloudGuard API Client
 * Centralized, typed API service connecting the React dashboard
 * to real FastAPI backend endpoints.
 * Strictly read-only monitoring; no execution or remediation actions.
 */

const API_BASE = import.meta.env.VITE_API_URL || '';

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url, {
      headers: {
        'Accept': 'application/json',
        ...(options.headers || {})
      },
      ...options
    });

    if (!res.ok) {
      const errText = await res.text().catch(() => '');
      let errorDetail = `HTTP ${res.status}: ${res.statusText}`;
      try {
        const parsed = JSON.parse(errText);
        if (parsed.detail) {
          errorDetail = typeof parsed.detail === 'string' ? parsed.detail : JSON.stringify(parsed.detail);
        }
      } catch {
        if (errText) errorDetail = errText;
      }
      const error = new Error(errorDetail);
      error.status = res.status;
      throw error;
    }

    // Check if json
    const contentType = res.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      return await res.json();
    }
    return await res.text();
  } catch (err) {
    console.error(`[CloudGuard API] Request to ${endpoint} failed:`, err);
    throw err;
  }
}

export const api = {
  // Health & Readiness
  getHealth: () => request('/health'),
  getReadiness: () => request('/ready'),

  // Recovery Tests
  getRecoveryTests: (params = {}) => {
    const query = new URLSearchParams();
    if (params.application_name) query.append('application_name', params.application_name);
    if (params.status && params.status !== 'ALL') query.append('status', params.status);
    if (params.limit) query.append('limit', params.limit.toString());
    const qs = query.toString();
    return request(`/api/v1/recovery-tests${qs ? `?${qs}` : ''}`);
  },

  getRecoveryTestById: (testId) => request(`/api/v1/recovery-tests/${testId}`),

  // Validations
  getValidations: (testId = null, validationType = null) => {
    const query = new URLSearchParams();
    if (testId) query.append('test_id', testId);
    if (validationType) query.append('validation_type', validationType);
    const qs = query.toString();
    return request(`/api/v1/validations${qs ? `?${qs}` : ''}`);
  },

  // Backups
  getBackups: (params = {}) => {
    const query = new URLSearchParams();
    if (params.application_name) query.append('application_name', params.application_name);
    if (params.limit) query.append('limit', params.limit.toString());
    const qs = query.toString();
    return request(`/api/v1/backups${qs ? `?${qs}` : ''}`);
  },

  // Reports
  getReports: (params = {}) => {
    const query = new URLSearchParams();
    if (params.status && params.status !== 'ALL') query.append('status', params.status);
    if (params.limit) query.append('limit', params.limit.toString());
    const qs = query.toString();
    return request(`/api/v1/reports${qs ? `?${qs}` : ''}`);
  },

  getReportById: (reportId) => request(`/api/v1/reports/${reportId}`),

  getReportHtml: (reportId) => request(`/api/v1/reports/${reportId}/html`),

  getDownloadUrl: (reportId, format = 'pdf') => {
    return `${API_BASE}/api/v1/reports/${reportId}/download?format=${format}`;
  },

  // Protected Applications
  getApplications: () => request('/api/v1/applications'),
  getApplicationDetails: (appName) => request(`/api/v1/applications/${appName}`),
};
