import React, { useEffect, useState } from 'react';
import { Search, AlertTriangle, ChevronLeft, ChevronRight } from 'lucide-react';
import { api } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';

export function ContractsPage() {
  const [contracts, setContracts] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const pageSize = 20;

  useEffect(() => {
    async function loadContracts() {
      try {
        setLoading(true);
        const data = await api.getContracts({
          status: statusFilter || undefined,
          search: searchTerm || undefined,
          page,
          size: pageSize,
        });
        setContracts(data.items || []);
        setTotal(data.total || 0);
        setPages(data.pages || 1);
        setError(null);
      } catch (err) {
        setError(err.message || 'Failed to retrieve contract records.');
      } finally {
        setLoading(false);
      }
    }

    const timer = setTimeout(() => {
      loadContracts();
    }, 200);

    return () => clearTimeout(timer);
  }, [statusFilter, searchTerm, page]);

  return (
    <div className="card-panel">
      <div className="panel-header">
        <div>
          <h2 className="panel-title">Fleet Rental Agreements ({total})</h2>
          <p style={{ fontSize: '0.8rem', color: '#64748b' }}>
            Consolidated vehicle agreements from Current Contracts and pay day
          </p>
        </div>

        <div className="filter-bar">
          <input
            type="text"
            className="search-input"
            placeholder="Search registration, driver, model..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setPage(1);
            }}
          />

          <select
            className="select-filter"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All Statuses</option>
            <option value="signed">Signed</option>
            <option value="not_signed">Not Signed</option>
            <option value="no_contract">No Contract</option>
            <option value="unknown">Unknown</option>
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
          <p>Loading fleet agreements...</p>
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Registration</th>
                <th>Vehicle Model</th>
                <th>Customer / Driver</th>
                <th>Start Date</th>
                <th>End Date</th>
                <th>Rental Rate</th>
                <th>Hire Duration</th>
                <th>Status</th>
                <th>Traceability</th>
              </tr>
            </thead>
            <tbody>
              {contracts.length === 0 ? (
                <tr>
                  <td colSpan="9" style={{ textAlign: 'center', padding: '36px' }}>
                    No contracts found matching your filters.
                  </td>
                </tr>
              ) : (
                contracts.map((c) => (
                  <tr key={c.id}>
                    <td>
                      <span className="reg-pill">{c.normalized_registration}</span>
                    </td>
                    <td style={{ fontWeight: 500 }}>{c.vehicle_model || '—'}</td>
                    <td>{c.customer_name_raw || '—'}</td>
                    <td>{c.start_date || <span style={{ color: '#dc2626' }}>Invalid/Missing</span>}</td>
                    <td>{c.end_date || <span style={{ color: '#dc2626' }}>Invalid/Missing</span>}</td>
                    <td style={{ fontWeight: 600 }}>
                      {c.rate ? `£${c.rate} ${c.payment_period || ''}` : '—'}
                    </td>
                    <td>{c.hire_duration || '—'}</td>
                    <td>
                      <StatusBadge status={c.normalized_status} />
                    </td>
                    <td style={{ color: '#64748b', fontSize: '0.8rem' }}>
                      {c.source_sheet} (row {c.source_row})
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
