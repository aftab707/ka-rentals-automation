import React, { useEffect, useState } from 'react';
import { ShieldAlert, AlertTriangle, ChevronLeft, ChevronRight } from 'lucide-react';
import { api } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';

export function DataQualityPage() {
  const [issues, setIssues] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [severityFilter, setSeverityFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const pageSize = 25;

  useEffect(() => {
    async function loadIssues() {
      try {
        setLoading(true);
        const data = await api.getDataQualityIssues({
          severity: severityFilter || undefined,
          category: categoryFilter || undefined,
          page,
          size: pageSize,
        });
        setIssues(data.items || []);
        setTotal(data.total || 0);
        setPages(data.pages || 1);
        setError(null);
      } catch (err) {
        setError(err.message || 'Failed to retrieve data quality issues.');
      } finally {
        setLoading(false);
      }
    }
    loadIssues();
  }, [severityFilter, categoryFilter, page]);

  return (
    <div className="card-panel">
      <div className="panel-header">
        <div>
          <h2 className="panel-title">Data Quality & Anomaly Audit ({total})</h2>
          <p style={{ fontSize: '0.8rem', color: '#64748b' }}>
            Automated alerts for missing fields, placeholder dates, status conflicts, and header anomalies
          </p>
        </div>

        <div className="filter-bar">
          <select
            className="select-filter"
            value={severityFilter}
            onChange={(e) => {
              setSeverityFilter(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="warning">Warning</option>
            <option value="info">Info</option>
          </select>

          <select
            className="select-filter"
            value={categoryFilter}
            onChange={(e) => {
              setCategoryFilter(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All Categories</option>
            <option value="pcn">PCN Violations</option>
            <option value="contract">Contracts</option>
            <option value="customer">Customer Details</option>
            <option value="excel_structure">Excel Structure</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="alert-box alert-danger" style={{ margin: '16px' }}>
          <AlertTriangle size={18} />
          <div>{error}</div>
        </div>
      )}

      {loading ? (
        <div className="state-container">
          <div className="spinner"></div>
          <p>Auditing data quality records...</p>
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Severity</th>
                <th>Category</th>
                <th>Issue Code</th>
                <th>Identifier</th>
                <th>Description</th>
                <th>Raw Value</th>
                <th>Source Location</th>
              </tr>
            </thead>
            <tbody>
              {issues.length === 0 ? (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '36px' }}>
                    No issues found matching your filter criteria.
                  </td>
                </tr>
              ) : (
                issues.map((i) => (
                  <tr key={i.id}>
                    <td>
                      <StatusBadge status={i.severity} />
                    </td>
                    <td style={{ textTransform: 'capitalize', fontWeight: 500 }}>{i.category}</td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.8rem', fontWeight: 600 }}>
                      {i.issue_type}
                    </td>
                    <td>{i.record_identifier || '—'}</td>
                    <td>{i.description}</td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: '#b91c1c' }}>
                      {i.raw_value ? String(i.raw_value).slice(0, 40) : '—'}
                    </td>
                    <td style={{ color: '#64748b', fontSize: '0.8rem' }}>
                      {i.source_sheet} (row {i.source_row})
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      <div className="pagination">
        <div>
          Showing page <strong>{page}</strong> of <strong>{pages}</strong> ({total} total records)
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            className="btn btn-outline"
            disabled={page <= 1 || loading}
            onClick={() => setPage(page - 1)}
          >
            <ChevronLeft size={16} /> Previous
          </button>
          <button
            className="btn btn-outline"
            disabled={page >= pages || loading}
            onClick={() => setPage(page + 1)}
          >
            Next <ChevronRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
