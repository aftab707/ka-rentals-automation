import React, { useEffect, useState } from 'react';
import { Search, AlertTriangle, ExternalLink, ChevronLeft, ChevronRight, Flame } from 'lucide-react';
import { api } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';

export function PCNsPage() {
  const [pcns, setPcns] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [conflictOnly, setConflictOnly] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const pageSize = 25;

  useEffect(() => {
    async function loadPCNs() {
      try {
        setLoading(true);
        const data = await api.getPCNs({
          status: statusFilter || undefined,
          has_conflict: conflictOnly ? true : undefined,
          search: searchTerm || undefined,
          page,
          size: pageSize,
        });
        setPcns(data.items || []);
        setTotal(data.total || 0);
        setPages(data.pages || 1);
        setError(null);
      } catch (err) {
        setError(err.message || 'Failed to retrieve PCN records.');
      } finally {
        setLoading(false);
      }
    }

    const timer = setTimeout(() => {
      loadPCNs();
    }, 200);

    return () => clearTimeout(timer);
  }, [statusFilter, conflictOnly, searchTerm, page]);

  return (
    <div className="card-panel">
      <div className="panel-header">
        <div>
          <h2 className="panel-title">PCN / Parking Charge Notices ({total})</h2>
          <p style={{ fontSize: '0.8rem', color: '#64748b' }}>
            Consolidated notices across Outstanding PCN, paying needed, Sheet15, and driver tabs
          </p>
        </div>

        <div className="filter-bar">
          <input
            type="text"
            className="search-input"
            placeholder="Search ticket, reg, or driver..."
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
            <option value="unpaid">Unpaid</option>
            <option value="action_needed">Action Needed</option>
            <option value="conflict">Status Conflict</option>
            <option value="needs_review">Needs Review</option>
            <option value="paid">Paid</option>
            <option value="unknown">Unknown</option>
          </select>

          <button
            type="button"
            className={`btn ${conflictOnly ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => {
              setConflictOnly(!conflictOnly);
              setPage(1);
            }}
          >
            <Flame size={16} /> Conflicts Only
          </button>
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
          <p>Loading PCN records...</p>
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Ticket Reference</th>
                <th>Vehicle Reg</th>
                <th>Issue Date</th>
                <th>Fine Amount</th>
                <th>Status</th>
                <th>Driver Reference</th>
                <th>Portal Link</th>
                <th>Traceability (Sheet / Row)</th>
              </tr>
            </thead>
            <tbody>
              {pcns.length === 0 ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: '36px' }}>
                    No PCN records found matching your filters.
                  </td>
                </tr>
              ) : (
                pcns.map((pcn) => (
                  <tr key={pcn.id} style={pcn.has_conflict ? { backgroundColor: '#fef2f2' } : {}}>
                    <td>
                      <div style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                        {pcn.ticket_number}
                        {pcn.has_conflict && (
                          <span title={pcn.conflict_notes} style={{ color: '#dc2626', cursor: 'help' }}>
                            <Flame size={16} />
                          </span>
                        )}
                      </div>
                      {pcn.conflict_notes && (
                        <div style={{ fontSize: '0.75rem', color: '#b91c1c', marginTop: '2px' }}>
                          {pcn.conflict_notes}
                        </div>
                      )}
                    </td>
                    <td>
                      {pcn.normalized_registration ? (
                        <span className="reg-pill">{pcn.normalized_registration}</span>
                      ) : (
                        <span style={{ color: '#94a3b8' }}>—</span>
                      )}
                    </td>
                    <td>{pcn.issue_date || '—'}</td>
                    <td style={{ fontWeight: 600 }}>
                      {pcn.fine_amount ? `£${pcn.fine_amount.toFixed(2)}` : '—'}
                    </td>
                    <td>
                      <StatusBadge status={pcn.normalized_status} />
                    </td>
                    <td>{pcn.customer_name_raw || '—'}</td>
                    <td>
                      {pcn.payment_url ? (
                        <a
                          href={pcn.payment_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{
                            color: '#2563eb',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                            textDecoration: 'none',
                            fontSize: '0.8rem',
                          }}
                        >
                          Pay Portal <ExternalLink size={13} />
                        </a>
                      ) : (
                        <span style={{ color: '#94a3b8' }}>—</span>
                      )}
                    </td>
                    <td style={{ color: '#64748b', fontSize: '0.8rem' }}>
                      {pcn.source_sheet} (row {pcn.source_row})
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination controls */}
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
