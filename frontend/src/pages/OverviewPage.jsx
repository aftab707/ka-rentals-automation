import React, { useEffect, useState } from 'react';
import {
  Car,
  FileCheck,
  AlertTriangle,
  Flame,
  ShieldAlert,
  ArrowRight,
  Clock,
} from 'lucide-react';
import { api } from '../services/api';
import { KPICard } from '../components/KPICard';
import { StatusBadge } from '../components/StatusBadge';

export function OverviewPage({ setTab }) {
  const [summary, setSummary] = useState(null);
  const [urgentPCNs, setUrgentPCNs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [sumRes, pcnRes] = await Promise.all([
          api.getDashboardSummary(),
          api.getPCNs({ status: 'action_needed', size: 5 }),
        ]);
        setSummary(sumRes);
        setUrgentPCNs(pcnRes.items || []);
        setError(null);
      } catch (err) {
        setError(err.message || 'Failed to load dashboard overview data.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="state-container">
        <div className="spinner"></div>
        <p>Loading fleet overview...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert-box alert-danger">
        <AlertTriangle size={20} />
        <div>
          <strong>Error loading dashboard:</strong> {error}
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Latest Import Banner */}
      {summary?.latest_import && (
        <div className="alert-box alert-info">
          <Clock size={18} />
          <div>
            <strong>Latest Workbook Import:</strong> {summary.latest_import.filename} (
            {new Date(summary.latest_import.started_at).toLocaleString()}) — Status:{' '}
            <StatusBadge status={summary.latest_import.status} />
          </div>
        </div>
      )}

      {/* Critical Conflict Banner */}
      {summary?.conflict_pcns > 0 && (
        <div className="alert-box alert-danger" style={{ cursor: 'pointer' }} onClick={() => setTab('pcns')}>
          <Flame size={20} />
          <div>
            <strong>Action Required:</strong> Detected {summary.conflict_pcns} PCN ticket with cross-sheet status conflict! Click to inspect conflicting records.
          </div>
        </div>
      )}

      {/* KPIs Grid */}
      <div className="kpi-grid">
        <KPICard
          title="Fleet Vehicles"
          value={summary?.total_vehicles || 0}
          subtitle="Total operational vehicles"
          icon={Car}
          color="blue"
        />
        <KPICard
          title="Signed Contracts"
          value={summary?.active_contracts || 0}
          subtitle={`${summary?.unsigned_contracts || 0} unsigned/pending`}
          icon={FileCheck}
          color="green"
        />
        <KPICard
          title="Action Needed PCNs"
          value={summary?.action_needed_pcns || 0}
          subtitle={`${summary?.unpaid_pcns || 0} additional unpaid fines`}
          icon={AlertTriangle}
          color="amber"
        />
        <KPICard
          title="Status Conflicts"
          value={summary?.conflict_pcns || 0}
          subtitle="Contradicting multi-sheet fines"
          icon={Flame}
          color="purple"
        />
        <KPICard
          title="Data Quality Issues"
          value={summary?.total_issues || 0}
          subtitle={`${summary?.critical_issues || 0} critical anomalies`}
          icon={ShieldAlert}
          color="red"
        />
      </div>

      {/* Urgent Action Needed PCNs Preview */}
      <div className="card-panel">
        <div className="panel-header">
          <h2 className="panel-title">Urgent Action Needed PCNs</h2>
          <button className="btn btn-outline" onClick={() => setTab('pcns')}>
            View All PCNs <ArrowRight size={16} />
          </button>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Ticket Number</th>
                <th>Vehicle Reg</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Driver / Handle</th>
                <th>Source Sheet</th>
              </tr>
            </thead>
            <tbody>
              {urgentPCNs.length === 0 ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '24px' }}>
                    No urgent action needed PCNs found.
                  </td>
                </tr>
              ) : (
                urgentPCNs.map((pcn) => (
                  <tr key={pcn.id}>
                    <td style={{ fontWeight: 600 }}>{pcn.ticket_number}</td>
                    <td>
                      {pcn.normalized_registration ? (
                        <span className="reg-pill">{pcn.normalized_registration}</span>
                      ) : (
                        <span style={{ color: '#94a3b8' }}>—</span>
                      )}
                    </td>
                    <td>{pcn.fine_amount ? `£${pcn.fine_amount.toFixed(2)}` : '—'}</td>
                    <td>
                      <StatusBadge status={pcn.normalized_status} />
                    </td>
                    <td>{pcn.customer_name_raw || '—'}</td>
                    <td style={{ color: '#64748b', fontSize: '0.8rem' }}>
                      {pcn.source_sheet} (row {pcn.source_row})
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
