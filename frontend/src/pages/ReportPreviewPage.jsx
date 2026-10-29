import React, { useEffect, useState } from 'react';
import { FileCheck2, AlertTriangle, Flame, ShieldAlert, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';

export function ReportPreviewPage() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  async function loadPreview() {
    try {
      setLoading(true);
      const data = await api.getReportPreview();
      setReport(data);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to generate operational report preview.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPreview();
  }, []);

  if (loading) {
    return (
      <div className="state-container">
        <div className="spinner"></div>
        <p>Compiling operational report preview...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert-box alert-danger">
        <AlertTriangle size={18} />
        <div>{error}</div>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Operational Daily Report Preview</h2>
          <p style={{ color: '#64748b', fontSize: '0.85rem' }}>
            Generated {new Date(report.generated_at).toLocaleString()} • Preview Mode (No live emails sent)
          </p>
        </div>
        <button className="btn btn-outline" onClick={loadPreview}>
          <RefreshCw size={16} /> Refresh Report
        </button>
      </div>

      {/* 1. Conflicting PCNs Section */}
      <div className="card-panel">
        <div className="panel-header" style={{ backgroundColor: '#fef2f2' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Flame size={20} color="#dc2626" />
            <h3 className="panel-title" style={{ color: '#991b1b' }}>
              Multi-Sheet Status Conflicts ({report.conflicts?.length || 0})
            </h3>
          </div>
          <span className="badge badge-critical">Immediate Investigation</span>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Ticket Reference</th>
                <th>Registration</th>
                <th>Conflict Details</th>
                <th>Source Traceability</th>
                <th>Recommended Action</th>
              </tr>
            </thead>
            <tbody>
              {report.conflicts?.length === 0 ? (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', padding: '24px' }}>
                    No status conflicts detected.
                  </td>
                </tr>
              ) : (
                report.conflicts.map((c) => (
                  <tr key={c.id}>
                    <td style={{ fontWeight: 600 }}>{c.ticket_number}</td>
                    <td>
                      <span className="reg-pill">{c.normalized_registration || '—'}</span>
                    </td>
                    <td style={{ color: '#b91c1c' }}>{c.conflict_notes}</td>
                    <td style={{ fontSize: '0.8rem', color: '#64748b' }}>
                      {c.source_sheet} (row {c.source_row})
                    </td>
                    <td>
                      <span style={{ fontWeight: 500, fontSize: '0.8rem' }}>
                        Check council portal before making double payments or marking unpaid.
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 2. Urgent Unpaid PCNs Section */}
      <div className="card-panel">
        <div className="panel-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={20} color="#d97706" />
            <h3 className="panel-title">Urgent PCNs Requiring Settlement ({report.urgent_pcns?.length || 0})</h3>
          </div>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Ticket Reference</th>
                <th>Registration</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Driver</th>
                <th>Portal Link</th>
              </tr>
            </thead>
            <tbody>
              {report.urgent_pcns?.slice(0, 10).map((p) => (
                <tr key={p.id}>
                  <td style={{ fontWeight: 600 }}>{p.ticket_number}</td>
                  <td>
                    <span className="reg-pill">{p.normalized_registration || '—'}</span>
                  </td>
                  <td style={{ fontWeight: 600 }}>{p.fine_amount ? `£${p.fine_amount.toFixed(2)}` : '—'}</td>
                  <td>
                    <StatusBadge status={p.normalized_status} />
                  </td>
                  <td>{p.customer_name_raw || '—'}</td>
                  <td>
                    {p.payment_url ? (
                      <a href={p.payment_url} target="_blank" rel="noopener noreferrer" style={{ color: '#2563eb' }}>
                        Open Portal
                      </a>
                    ) : (
                      '—'
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 3. Unsigned Contracts */}
      <div className="card-panel">
        <div className="panel-header">
          <h3 className="panel-title">Agreements Requiring Signature ({report.contracts_requiring_action?.length || 0})</h3>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Registration</th>
                <th>Driver Name</th>
                <th>Rate</th>
                <th>Status</th>
                <th>Issue Note</th>
              </tr>
            </thead>
            <tbody>
              {report.contracts_requiring_action?.map((cnt) => (
                <tr key={cnt.id}>
                  <td>
                    <span className="reg-pill">{cnt.normalized_registration}</span>
                  </td>
                  <td>{cnt.customer_name_raw || '—'}</td>
                  <td>{cnt.rate ? `£${cnt.rate}` : '—'}</td>
                  <td>
                    <StatusBadge status={cnt.normalized_status} />
                  </td>
                  <td style={{ color: '#64748b', fontSize: '0.8rem' }}>
                    Send contract for DocuSign / signature verification.
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
