/**
 * API service layer communicating with the FastAPI backend.
 * Uses Vite reverse proxy (/api) or VITE_API_BASE_URL environment variable.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        Accept: 'application/json',
        ...(options.headers || {}),
      },
    });

    if (!res.ok) {
      let errorMsg = `Server responded with ${res.status}`;
      try {
        const errJson = await res.json();
        if (errJson.detail) {
          errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
        }
      } catch (_) {
        // Fallback to default message
      }
      throw new Error(errorMsg);
    }

    return await res.json();
  } catch (err) {
    console.error(`API Error [${endpoint}]:`, err);
    throw err;
  }
}

export const api = {
  getHealth: () => request('/api/health'),

  getDashboardSummary: () => request('/api/dashboard/summary'),

  getPCNs: ({ status, registration, has_conflict, search, page = 1, size = 50 } = {}) => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (registration) params.append('registration', registration);
    if (has_conflict !== undefined && has_conflict !== null && has_conflict !== '') {
      params.append('has_conflict', String(has_conflict));
    }
    if (search) params.append('search', search);
    params.append('page', String(page));
    params.append('size', String(size));
    return request(`/api/pcns?${params.toString()}`);
  },

  getContracts: ({ status, search, page = 1, size = 50 } = {}) => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (search) params.append('search', search);
    params.append('page', String(page));
    params.append('size', String(size));
    return request(`/api/contracts?${params.toString()}`);
  },

  getVehicles: () => request('/api/vehicles'),

  getDataQualityIssues: ({ severity, category, page = 1, size = 50 } = {}) => {
    const params = new URLSearchParams();
    if (severity) params.append('severity', severity);
    if (category) params.append('category', category);
    params.append('page', String(page));
    params.append('size', String(size));
    return request(`/api/data-quality/issues?${params.toString()}`);
  },

  getImports: (limit = 20) => request(`/api/imports?limit=${limit}`),

  uploadExcelFile: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return request('/api/import/excel', {
      method: 'POST',
      body: formData,
    });
  },

  getReportPreview: () => request('/api/reports/preview', { method: 'POST' }),

  getOperationalReport: () => request('/api/reports/daily/json'),

  getOperationalReportHtml: async () => {
    const res = await fetch(`${BASE_URL}/api/reports/daily/html`);
    if (!res.ok) throw new Error(`Server responded with ${res.status}`);
    return await res.text();
  },

  sendMockEmail: (payload) =>
    request('/api/reports/email/mock-send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload || {}),
    }),
};
