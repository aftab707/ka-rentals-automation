import React, { useEffect, useState } from 'react';
import {
  Search,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  PlusCircle,
  FileSignature,
  Send,
  CheckCircle2,
  RefreshCw,
  X,
  ExternalLink,
} from 'lucide-react';
import { api } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';

export function ContractsPage() {
  const [contracts, setContracts] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notification, setNotification] = useState(null);

  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState(null);

  // Form Fields
  const [formReg, setFormReg] = useState('');
  const [formModel, setFormModel] = useState('');
  const [formDriverName, setFormDriverName] = useState('');
  const [formEmail, setFormEmail] = useState('');
  const [formPhone, setFormPhone] = useState('');
  const [formLicense, setFormLicense] = useState('');
  const [formAddress, setFormAddress] = useState('');
  const [formRate, setFormRate] = useState('250');
  const [formStartDate, setFormStartDate] = useState(new Date().toISOString().split('T')[0]);
  const [formDuration, setFormDuration] = useState('28 days');
  const [formSendDocuSign, setFormSendDocuSign] = useState(true);

  const pageSize = 20;

  async function loadData() {
    try {
      setLoading(true);
      const [contractsData, vehiclesData] = await Promise.all([
        api.getContracts({
          status: statusFilter || undefined,
          search: searchTerm || undefined,
          page,
          size: pageSize,
        }),
        api.getVehicles().catch(() => []),
      ]);
      setContracts(contractsData.items || []);
      setTotal(contractsData.total || 0);
      setPages(contractsData.pages || 1);
      setVehicles(vehiclesData || []);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to retrieve contract records.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = setTimeout(() => {
      loadData();
    }, 200);
    return () => clearTimeout(timer);
  }, [statusFilter, searchTerm, page]);

  function handleVehicleSelect(reg) {
    setFormReg(reg);
    const found = vehicles.find((v) => v.normalized_registration === reg.replace(/\s+/g, '').toUpperCase());
    if (found && found.make_model) {
      setFormModel(found.make_model);
    }
  }

  async function handleCreateHire(e) {
    e.preventDefault();
    if (!formReg.trim() || !formDriverName.trim() || !formEmail.trim()) {
      alert('Vehicle Registration, Driver Name, and Driver Email are mandatory.');
      return;
    }

    try {
      setSubmitting(true);
      const res = await api.createContract({
        vehicle_registration: formReg.trim(),
        vehicle_model: formModel.trim() || undefined,
        customer_name: formDriverName.trim(),
        customer_email: formEmail.trim(),
        customer_phone: formPhone.trim() || undefined,
        customer_license: formLicense.trim() || undefined,
        customer_address: formAddress.trim() || undefined,
        rate: formRate ? parseFloat(formRate) : undefined,
        start_date: formStartDate || undefined,
        hire_duration: formDuration,
        send_docusign: formSendDocuSign,
      });

      setShowModal(false);
      setNotification({
        type: 'success',
        message: formSendDocuSign
          ? `✓ Agreement created and DocuSign envelope dispatched to ${formEmail}!`
          : `✓ Agreement for ${res.vehicle_registration} created successfully!`,
      });

      // Reset form
      setFormReg('');
      setFormModel('');
      setFormDriverName('');
      setFormEmail('');
      setFormPhone('');
      setFormLicense('');
      setFormAddress('');

      loadData();
    } catch (err) {
      alert(`Error creating contract: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSendDocuSign(contract) {
    const email = prompt(`Enter driver's email address to send DocuSign agreement:`, 'driver@example.com');
    if (!email || !email.trim()) return;

    try {
      setActionLoadingId(contract.id);
      const res = await api.sendContractDocuSign(contract.id, {
        signer_email: email.trim(),
        signer_name: contract.customer_name_raw || 'KA Rentals Driver',
      });
      setNotification({
        type: 'success',
        message: `✓ DocuSign envelope dispatched to ${email}! Envelope ID: ${res.envelope_id}`,
      });
      loadData();
    } catch (err) {
      alert(`DocuSign send failed: ${err.message}`);
    } finally {
      setActionLoadingId(null);
    }
  }

  async function handleCheckDocuSignStatus(contract) {
    try {
      setActionLoadingId(contract.id);
      const res = await api.checkDocuSignStatus(contract.id);
      setNotification({
        type: 'info',
        message: `DocuSign Status for ${contract.vehicle_registration}: ${res.status.toUpperCase()} (${res.message})`,
      });
      loadData();
    } catch (err) {
      alert(`Status check failed: ${err.message}`);
    } finally {
      setActionLoadingId(null);
    }
  }

  async function handleSimulateWebhook(contract) {
    if (!contract.docusign_envelope_id) {
      alert('Please send a DocuSign agreement first before simulating webhook.');
      return;
    }

    try {
      setActionLoadingId(contract.id);
      await api.triggerDocuSignWebhook({
        envelopeId: contract.docusign_envelope_id,
        status: 'completed',
        event: 'envelope-completed',
      });
      setNotification({
        type: 'success',
        message: `✓ Webhook Simulated! Driver signature received for ${contract.vehicle_registration}. Status updated to SIGNED!`,
      });
      loadData();
    } catch (err) {
      alert(`Webhook simulation failed: ${err.message}`);
    } finally {
      setActionLoadingId(null);
    }
  }

  return (
    <div>
      {/* Toast Notification */}
      {notification && (
        <div
          className={`alert-box ${notification.type === 'success' ? 'alert-success' : 'alert-info'}`}
          style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {notification.type === 'success' ? <CheckCircle2 size={18} /> : <RefreshCw size={18} />}
            <span>{notification.message}</span>
          </div>
          <button
            onClick={() => setNotification(null)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit' }}
          >
            <X size={16} />
          </button>
        </div>
      )}

      <div className="card-panel">
        <div className="panel-header">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <h2 className="panel-title" style={{ margin: 0 }}>
                Fleet Rental Agreements ({total})
              </h2>
              <button className="btn btn-primary" onClick={() => setShowModal(true)}>
                <PlusCircle size={16} /> New Hire Agreement
              </button>
            </div>
            <p style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '4px' }}>
              Direct driver onboarding, automated contract creation, and DocuSign digital execution
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
            <p>Loading fleet agreements & signature states...</p>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Registration</th>
                  <th>Vehicle Model</th>
                  <th>Customer / Driver</th>
                  <th>Rental Rate</th>
                  <th>Start Date</th>
                  <th>Agreement Status</th>
                  <th>DocuSign Tracking</th>
                  <th>Signature Actions</th>
                </tr>
              </thead>
              <tbody>
                {contracts.length === 0 ? (
                  <tr>
                    <td colSpan="8" style={{ textAlign: 'center', padding: '36px' }}>
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
                      <td style={{ fontWeight: 600 }}>{c.customer_name_raw || '—'}</td>
                      <td style={{ fontWeight: 600 }}>
                        {c.rate ? `£${c.rate} ${c.payment_period || '/wk'}` : '—'}
                      </td>
                      <td>{c.start_date || <span style={{ color: '#dc2626' }}>Invalid/Missing</span>}</td>
                      <td>
                        <StatusBadge status={c.normalized_status} />
                      </td>

                      {/* DocuSign Tracking Column */}
                      <td>
                        {c.normalized_status === 'signed' ? (
                          <span
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px',
                              fontSize: '0.8rem',
                              fontWeight: 600,
                              color: '#16a34a',
                              backgroundColor: '#dcfce7',
                              padding: '3px 8px',
                              borderRadius: '4px',
                            }}
                          >
                            <CheckCircle2 size={13} /> Completed
                          </span>
                        ) : c.docusign_status ? (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                            <span
                              style={{
                                fontSize: '0.75rem',
                                fontWeight: 600,
                                color: '#b45309',
                                backgroundColor: '#fef3c7',
                                padding: '2px 6px',
                                borderRadius: '4px',
                                display: 'inline-block',
                              }}
                            >
                              ⏳ {c.docusign_status.toUpperCase()}
                            </span>
                            <span style={{ fontSize: '0.7rem', color: '#64748b', fontFamily: 'monospace' }}>
                              ID: {c.docusign_envelope_id ? `${c.docusign_envelope_id.slice(0, 8)}...` : '—'}
                            </span>
                          </div>
                        ) : (
                          <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Not Dispatched</span>
                        )}
                      </td>

                      {/* Actions Column */}
                      <td>
                        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                          {c.normalized_status !== 'signed' && !c.docusign_envelope_id && (
                            <button
                              className="btn btn-outline"
                              style={{ padding: '4px 10px', fontSize: '0.75rem', color: '#2563eb' }}
                              disabled={actionLoadingId === c.id}
                              onClick={() => handleSendDocuSign(c)}
                            >
                              <Send size={13} /> Send DocuSign
                            </button>
                          )}

                          {c.docusign_envelope_id && c.normalized_status !== 'signed' && (
                            <>
                              <button
                                className="btn btn-outline"
                                style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                                title="Check status with DocuSign"
                                disabled={actionLoadingId === c.id}
                                onClick={() => handleCheckDocuSignStatus(c)}
                              >
                                <RefreshCw size={12} /> Sync
                              </button>

                              <button
                                className="btn btn-outline"
                                style={{
                                  padding: '4px 8px',
                                  fontSize: '0.75rem',
                                  color: '#16a34a',
                                  backgroundColor: '#f0fdf4',
                                }}
                                title="Simulate driver signing webhook"
                                disabled={actionLoadingId === c.id}
                                onClick={() => handleSimulateWebhook(c)}
                              >
                                Simulate Sign
                              </button>
                            </>
                          )}

                          {c.normalized_status === 'signed' && (
                            <span style={{ fontSize: '0.75rem', color: '#16a34a', fontWeight: 500 }}>
                              Active Agreement
                            </span>
                          )}
                        </div>
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

      {/* NEW HIRE AGREEMENT MODAL */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-card">
            <div
              style={{
                padding: '20px 24px',
                borderBottom: '1px solid #e2e8f0',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <FileSignature size={22} color="#2563eb" />
                <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700 }}>
                  Onboard Driver & New Hire Agreement
                </h3>
              </div>
              <button
                onClick={() => setShowModal(false)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleCreateHire} style={{ padding: '24px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '6px' }}>
                    Vehicle Registration *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. LP21 FYB"
                    value={formReg}
                    onChange={(e) => setFormReg(e.target.value.toUpperCase())}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                  />
                  {vehicles.length > 0 && (
                    <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginTop: '6px' }}>
                      <span style={{ fontSize: '0.7rem', color: '#64748b' }}>Quick select:</span>
                      {vehicles.slice(0, 4).map((v) => (
                        <button
                          key={v.id}
                          type="button"
                          onClick={() => handleVehicleSelect(v.registration)}
                          style={{
                            fontSize: '0.68rem',
                            padding: '1px 5px',
                            background: '#f1f5f9',
                            border: '1px solid #cbd5e1',
                            borderRadius: '3px',
                            cursor: 'pointer',
                          }}
                        >
                          {v.registration}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '6px' }}>
                    Vehicle Model
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Toyota Corolla Hybrid"
                    value={formModel}
                    onChange={(e) => setFormModel(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '6px' }}>
                    Driver Full Name *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Trelawny Edwards"
                    value={formDriverName}
                    onChange={(e) => setFormDriverName(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '6px' }}>
                    Driver Email (For DocuSign) *
                  </label>
                  <input
                    type="email"
                    required
                    placeholder="e.g. driver@email.com"
                    value={formEmail}
                    onChange={(e) => setFormEmail(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '6px' }}>
                    Phone Number
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. 07123456789"
                    value={formPhone}
                    onChange={(e) => setFormPhone(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '6px' }}>
                    UK Driving License Number
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. EDWAR011295TPGYP"
                    value={formLicense}
                    onChange={(e) => setFormLicense(e.target.value.toUpperCase())}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '6px' }}>
                  Address & Postcode
                </label>
                <input
                  type="text"
                  placeholder="e.g. 37 Penrith Road, CR7 8PN"
                  value={formAddress}
                  onChange={(e) => setFormAddress(e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '6px' }}>
                    Weekly Hire Rate (£)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="e.g. 250"
                    value={formRate}
                    onChange={(e) => setFormRate(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '6px' }}>
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={formStartDate}
                    onChange={(e) => setFormStartDate(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                  />
                </div>
              </div>

              <div
                style={{
                  padding: '12px 14px',
                  backgroundColor: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: '6px',
                  marginBottom: '20px',
                }}
              >
                <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={formSendDocuSign}
                    onChange={(e) => setFormSendDocuSign(e.target.checked)}
                    style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                  />
                  <div>
                    <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#0f172a' }}>
                      Dispatch DocuSign Agreement to driver immediately
                    </span>
                    <span style={{ display: 'block', fontSize: '0.75rem', color: '#64748b' }}>
                      Generates 6-page legal hire agreement with Section 10 PCN liability transfer.
                    </span>
                  </div>
                </label>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => setShowModal(false)}
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? (
                    <>
                      <div className="spinner" style={{ width: '14px', height: '14px', margin: 0 }}></div>
                      Processing & Dispatching...
                    </>
                  ) : (
                    <>
                      <Send size={15} /> Create & Dispatch Agreement
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
