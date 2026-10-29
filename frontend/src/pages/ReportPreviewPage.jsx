import React, { useEffect, useState } from 'react';
import {
  FileText,
  Mail,
  Send,
  AlertTriangle,
  Flame,
  ShieldAlert,
  RefreshCw,
  CheckCircle2,
  FileCheck,
  UserX,
  FileSignature,
} from 'lucide-react';
import { api } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';

export function ReportPreviewPage() {
  const [report, setReport] = useState(null);
  const [htmlContent, setHtmlContent] = useState('');
  const [activeTab, setActiveTab] = useState('actions'); // 'actions' | 'email-preview' | 'mock-send'
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Mock Email Form state
  const [recipientEmail, setRecipientEmail] = useState('operations-team@mock.karentals.internal');
  const [customSubject, setCustomSubject] = useState('');
  const [sendingMock, setSendingMock] = useState(false);
  const [sendResult, setSendResult] = useState(null);

  async function loadData() {
    try {
      setLoading(true);
      setError(null);
      const [jsonData, htmlData] = await Promise.all([
        api.getOperationalReport(),
        api.getOperationalReportHtml(),
      ]);
      setReport(jsonData);
      setHtmlContent(htmlData);
    } catch (err) {
      setError(err.message || 'Failed to generate operational report.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleSendMockEmail(e) {
    e.preventDefault();
    try {
      setSendingMock(true);
      setSendResult(null);
      const res = await api.sendMockEmail({
        recipient_email: recipientEmail,
        subject_override: customSubject.trim() || undefined,
      });
      setSendResult({
        success: true,
        data: res,
      });
    } catch (err) {
      setSendResult({
        success: false,
        message: err.message || 'Failed to dispatch mock email.',
      });
    } finally {
      setSendingMock(false);
    }
  }

  if (loading) {
    return (
      <div className="state-container">
        <div className="spinner"></div>
        <p>Compiling operational report & live HTML template...</p>
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
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 700, margin: 0 }}>Daily Operational Review & Email Preview</h2>
          <p style={{ color: '#64748b', fontSize: '0.85rem', marginTop: '4px' }}>
            Report ID: <span style={{ fontFamily: 'monospace', fontWeight: 600 }}>{report.report_id}</span> • Compiled{' '}
            {new Date(report.generated_at).toLocaleString()} • Safe Mock Mode
          </p>
        </div>
        <button className="btn btn-outline" onClick={loadData}>
          <RefreshCw size={16} /> Refresh Data
        </button>
      </div>

      {/* Safety Notice Banner */}
      <div
        style={{
          backgroundColor: '#eff6ff',
          border: '1px solid #bfdbfe',
          borderRadius: '8px',
          padding: '12px 18px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
        }}
      >
        <ShieldAlert size={22} color="#2563eb" />
        <div style={{ fontSize: '0.85rem', color: '#1e40af' }}>
          <strong>PROTOTYPE SANDBOX NOTICE:</strong> Real customer and authority communications are simulated.
          All reports adhere to strict data traceability (source sheet & row) and never invent arbitrary deadlines.
        </div>
      </div>

      {/* Executive KPI Bar */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '14px',
          marginBottom: '24px',
        }}
      >
        <div className="card-panel" style={{ padding: '16px' }}>
          <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#64748b', fontWeight: 600 }}>
            Total Fleet
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '4px' }}>{report.total_fleet_vehicles}</div>
          <div style={{ fontSize: '0.8rem', color: '#16a34a', marginTop: '2px' }}>
            {report.signed_contracts} signed contracts
          </div>
        </div>

        <div className="card-panel" style={{ padding: '16px' }}>
          <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#64748b', fontWeight: 600 }}>
            Open PCNs
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#d97706', marginTop: '4px' }}>
            {report.total_open_pcns}
          </div>
          <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '2px' }}>
            Total: £{report.total_unpaid_amount.toFixed(2)}
          </div>
        </div>

        <div
          className="card-panel"
          style={{ padding: '16px', backgroundColor: report.status_conflicts_count > 0 ? '#fef2f2' : undefined }}
        >
          <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#991b1b', fontWeight: 600 }}>
            Status Conflicts
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#dc2626', marginTop: '4px' }}>
            {report.status_conflicts_count}
          </div>
          <div style={{ fontSize: '0.8rem', color: '#991b1b', marginTop: '2px' }}>Critical multi-sheet issues</div>
        </div>

        <div className="card-panel" style={{ padding: '16px' }}>
          <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#64748b', fontWeight: 600 }}>
            Unsigned Contracts
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#475569', marginTop: '4px' }}>
            {report.unsigned_contracts}
          </div>
          <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '2px' }}>Require signature</div>
        </div>

        <div className="card-panel" style={{ padding: '16px' }}>
          <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#64748b', fontWeight: 600 }}>
            Incomplete Profiles
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#6366f1', marginTop: '4px' }}>
            {report.incomplete_customers?.length || 0}
          </div>
          <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '2px' }}>Missing compliance info</div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid #e2e8f0', marginBottom: '20px' }}>
        <button
          onClick={() => setActiveTab('actions')}
          style={{
            padding: '10px 18px',
            border: 'none',
            borderBottom: activeTab === 'actions' ? '3px solid #2563eb' : '3px solid transparent',
            background: 'none',
            fontWeight: activeTab === 'actions' ? 700 : 500,
            color: activeTab === 'actions' ? '#2563eb' : '#64748b',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '0.9rem',
          }}
        >
          <FileText size={17} /> Action Items & Categorized Audit
        </button>

        <button
          onClick={() => setActiveTab('email-preview')}
          style={{
            padding: '10px 18px',
            border: 'none',
            borderBottom: activeTab === 'email-preview' ? '3px solid #2563eb' : '3px solid transparent',
            background: 'none',
            fontWeight: activeTab === 'email-preview' ? 700 : 500,
            color: activeTab === 'email-preview' ? '#2563eb' : '#64748b',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '0.9rem',
          }}
        >
          <Mail size={17} /> HTML Email Preview
        </button>

        <button
          onClick={() => setActiveTab('mock-send')}
          style={{
            padding: '10px 18px',
            border: 'none',
            borderBottom: activeTab === 'mock-send' ? '3px solid #2563eb' : '3px solid transparent',
            background: 'none',
            fontWeight: activeTab === 'mock-send' ? 700 : 500,
            color: activeTab === 'mock-send' ? '#2563eb' : '#64748b',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '0.9rem',
          }}
        >
          <Send size={17} /> Mock Dispatcher
        </button>
      </div>

      {/* TAB 1: ACTION ITEMS & AUDIT */}
      {activeTab === 'actions' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Priority 1: Multi-Sheet Conflicts */}
          <div className="card-panel">
            <div className="panel-header" style={{ backgroundColor: '#fef2f2' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Flame size={20} color="#dc2626" />
                <h3 className="panel-title" style={{ color: '#991b1b' }}>
                  Priority 1: Multi-Sheet Status Conflicts ({report.conflicting_pcns?.length || 0})
                </h3>
              </div>
              <span className="badge badge-critical">Immediate Investigation</span>
            </div>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Ticket Ref</th>
                    <th>Conflict Description</th>
                    <th>Amount</th>
                    <th>Source Sheet & Row</th>
                    <th>Recommended Staff Action</th>
                  </tr>
                </thead>
                <tbody>
                  {report.conflicting_pcns?.length === 0 ? (
                    <tr>
                      <td colSpan="5" style={{ textAlign: 'center', padding: '20px', color: '#64748b' }}>
                        No status conflicts detected.
                      </td>
                    </tr>
                  ) : (
                    report.conflicting_pcns.map((c, idx) => (
                      <tr key={idx} style={{ backgroundColor: '#fff5f5' }}>
                        <td style={{ fontWeight: 700, fontFamily: 'monospace' }}>{c.identifier}</td>
                        <td style={{ color: '#b91c1c', fontSize: '0.85rem' }}>{c.description}</td>
                        <td style={{ fontWeight: 600 }}>{c.amount ? `£${c.amount.toFixed(2)}` : '—'}</td>
                        <td style={{ fontSize: '0.8rem', color: '#64748b' }}>
                          <span style={{ fontWeight: 600 }}>{c.source_sheet}</span> (row {c.source_row})
                        </td>
                        <td style={{ fontSize: '0.85rem', fontWeight: 600, color: '#991b1b' }}>
                          {c.recommended_action}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Priority 2: Action Needed PCNs */}
          <div className="card-panel">
            <div className="panel-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertTriangle size={20} color="#d97706" />
                <h3 className="panel-title">Priority 2: Immediate Action Needed PCNs ({report.action_needed_pcns?.length || 0})</h3>
              </div>
            </div>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Ticket Ref</th>
                    <th>Amount</th>
                    <th>Description</th>
                    <th>Source Sheet & Row</th>
                    <th>Recommended Staff Action</th>
                  </tr>
                </thead>
                <tbody>
                  {report.action_needed_pcns?.length === 0 ? (
                    <tr>
                      <td colSpan="5" style={{ textAlign: 'center', padding: '20px', color: '#64748b' }}>
                        No urgent action needed PCNs found.
                      </td>
                    </tr>
                  ) : (
                    report.action_needed_pcns.map((p, idx) => (
                      <tr key={idx}>
                        <td style={{ fontWeight: 600, fontFamily: 'monospace' }}>{p.identifier}</td>
                        <td style={{ fontWeight: 600, color: '#d97706' }}>
                          {p.amount ? `£${p.amount.toFixed(2)}` : '—'}
                        </td>
                        <td style={{ fontSize: '0.85rem' }}>{p.description}</td>
                        <td style={{ fontSize: '0.8rem', color: '#64748b' }}>
                          {p.source_sheet} (row {p.source_row})
                        </td>
                        <td style={{ fontSize: '0.85rem' }}>{p.recommended_action}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Priority 3: Unsigned Contracts & Missing Dates */}
          <div className="card-panel">
            <div className="panel-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FileSignature size={20} color="#475569" />
                <h3 className="panel-title">Priority 3: Contracts Requiring Action ({report.contracts_requiring_action?.length || 0})</h3>
              </div>
            </div>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Registration</th>
                    <th>Contract Status</th>
                    <th>Rate</th>
                    <th>Issue Detail</th>
                    <th>Source Sheet & Row</th>
                    <th>Recommended Action</th>
                  </tr>
                </thead>
                <tbody>
                  {report.contracts_requiring_action?.length === 0 ? (
                    <tr>
                      <td colSpan="6" style={{ textAlign: 'center', padding: '20px', color: '#64748b' }}>
                        All contracts signed and dates validated.
                      </td>
                    </tr>
                  ) : (
                    report.contracts_requiring_action.map((c, idx) => (
                      <tr key={idx}>
                        <td>
                          <span className="reg-pill">{c.identifier}</span>
                        </td>
                        <td>
                          <StatusBadge status={c.status} />
                        </td>
                        <td>{c.amount ? `£${c.amount}` : '—'}</td>
                        <td style={{ fontSize: '0.85rem', color: '#64748b' }}>{c.description}</td>
                        <td style={{ fontSize: '0.8rem', color: '#64748b' }}>
                          {c.source_sheet} (row {c.source_row})
                        </td>
                        <td style={{ fontSize: '0.85rem' }}>{c.recommended_action}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Priority 4: Incomplete Customer Profiles (Regulatory) */}
          <div className="card-panel">
            <div className="panel-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <UserX size={20} color="#6366f1" />
                <h3 className="panel-title">Priority 4: Incomplete Customer Profiles ({report.incomplete_customers?.length || 0})</h3>
              </div>
            </div>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Customer Identifier</th>
                    <th>Compliance Gap</th>
                    <th>Source Sheet & Row</th>
                    <th>Recommended Action</th>
                  </tr>
                </thead>
                <tbody>
                  {report.incomplete_customers?.length === 0 ? (
                    <tr>
                      <td colSpan="4" style={{ textAlign: 'center', padding: '20px', color: '#64748b' }}>
                        All customer profiles comply with regulatory requirements.
                      </td>
                    </tr>
                  ) : (
                    report.incomplete_customers.map((cust, idx) => (
                      <tr key={idx}>
                        <td style={{ fontWeight: 600 }}>{cust.identifier}</td>
                        <td style={{ fontSize: '0.85rem', color: '#b45309' }}>{cust.description}</td>
                        <td style={{ fontSize: '0.8rem', color: '#64748b' }}>
                          {cust.source_sheet} (row {cust.source_row})
                        </td>
                        <td style={{ fontSize: '0.85rem' }}>{cust.recommended_action}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: HTML EMAIL PREVIEW */}
      {activeTab === 'email-preview' && (
        <div className="card-panel">
          <div className="panel-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Mail size={20} color="#2563eb" />
              <h3 className="panel-title">Rendered HTML Email Template</h3>
            </div>
            <span style={{ fontSize: '0.8rem', color: '#64748b' }}>
              Standard email client format (responsive layout)
            </span>
          </div>

          <div style={{ padding: '20px', backgroundColor: '#f1f5f9' }}>
            <div
              style={{
                maxWidth: '820px',
                margin: '0 auto',
                backgroundColor: '#ffffff',
                border: '1px solid #cbd5e1',
                borderRadius: '8px',
                overflow: 'hidden',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
              }}
              dangerouslySetInnerHTML={{ __html: htmlContent }}
            />
          </div>
        </div>
      )}

      {/* TAB 3: MOCK SEND DISPATCHER */}
      {activeTab === 'mock-send' && (
        <div style={{ maxWidth: '680px', margin: '0 auto' }}>
          <div className="card-panel">
            <div className="panel-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Send size={20} color="#2563eb" />
                <h3 className="panel-title">Simulate Automated Daily Email Dispatch</h3>
              </div>
            </div>

            <form onSubmit={handleSendMockEmail} style={{ padding: '24px' }}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '6px' }}>
                  Mock Recipient Email
                </label>
                <input
                  type="email"
                  required
                  value={recipientEmail}
                  onChange={(e) => setRecipientEmail(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    borderRadius: '6px',
                    border: '1px solid #cbd5e1',
                    fontSize: '0.9rem',
                  }}
                  placeholder="e.g. operations-team@mock.karentals.internal"
                />
                <span style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px', display: 'block' }}>
                  Safe sandbox mode: No live emails are sent out to external servers.
                </span>
              </div>

              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '6px' }}>
                  Subject Line (Optional Override)
                </label>
                <input
                  type="text"
                  value={customSubject}
                  onChange={(e) => setCustomSubject(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    borderRadius: '6px',
                    border: '1px solid #cbd5e1',
                    fontSize: '0.9rem',
                  }}
                  placeholder={`KA Rentals Daily Operational Review [${report.report_id}]`}
                />
              </div>

              <button
                type="submit"
                disabled={sendingMock}
                className="btn btn-primary"
                style={{ width: '100%', justifyContent: 'center', padding: '12px' }}
              >
                {sendingMock ? (
                  <>
                    <div className="spinner" style={{ width: '16px', height: '16px' }}></div>
                    Dispatching Mock Email...
                  </>
                ) : (
                  <>
                    <Send size={16} /> Send Test Dispatch (Safe Mock Mode)
                  </>
                )}
              </button>
            </form>

            {sendResult && (
              <div style={{ padding: '0 24px 24px' }}>
                {sendResult.success ? (
                  <div className="alert-box alert-success" style={{ display: 'block' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                      <CheckCircle2 size={18} color="#16a34a" />
                      <strong style={{ fontSize: '0.9rem' }}>Mock Dispatch Successful</strong>
                    </div>
                    <div style={{ fontSize: '0.85rem', color: '#15803d' }}>
                      <div>
                        <strong>Status:</strong> {sendResult.data.status} (Mock Mode:{' '}
                        {String(sendResult.data.mock_mode)})
                      </div>
                      <div>
                        <strong>Recipient:</strong> {sendResult.data.recipient}
                      </div>
                      <div>
                        <strong>Subject:</strong> {sendResult.data.subject}
                      </div>
                      <div>
                        <strong>Sent At:</strong> {new Date(sendResult.data.sent_at).toLocaleString()}
                      </div>
                      <div style={{ marginTop: '8px', padding: '8px', backgroundColor: '#f0fdf4', borderRadius: '4px' }}>
                        <strong>Digest Snippet:</strong> {sendResult.data.message_preview_snippet}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="alert-box alert-danger">
                    <AlertTriangle size={18} />
                    <div>{sendResult.message}</div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
