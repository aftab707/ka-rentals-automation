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
  Car,
  User,
  Calendar,
  Sparkles,
  ShieldCheck,
} from 'lucide-react';
import { api } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';

const POPULAR_MODELS = [
  'Nissan Juke',
  'Mercedes GLC',
  'Kia Niro',
  'Tesla Model 3',
  'BMW 2 Series',
  'BMW X3',
  'MG HS',
  'MG ZS EV',
  'Toyota Corolla Hybrid',
  'Ford Kuga',
  'Citroën Berlingo',
  'Hyundai Kona',
];

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

  // Form Fields & Interactive Dropdown Selection
  const [selectedVehicleReg, setSelectedVehicleReg] = useState('');
  const [isManualVehicle, setIsManualVehicle] = useState(false);
  const [formReg, setFormReg] = useState('');
  const [formModel, setFormModel] = useState('');
  const [isManualModel, setIsManualModel] = useState(false);
  const [formDriverName, setFormDriverName] = useState('');
  const [formEmail, setFormEmail] = useState('');
  const [formPhone, setFormPhone] = useState('');
  const [formLicense, setFormLicense] = useState('');
  const [formAddress, setFormAddress] = useState('');
  const [formRate, setFormRate] = useState('325');
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

  // Handle vehicle dropdown change
  function handleVehicleDropdownChange(e) {
    const val = e.target.value;
    setSelectedVehicleReg(val);

    if (val === '__custom__') {
      setIsManualVehicle(true);
      setFormReg('');
      setFormModel('');
      setIsManualModel(true);
    } else if (val) {
      setIsManualVehicle(false);
      setFormReg(val);
      const matched = vehicles.find(
        (v) => v.normalized_registration === val.replace(/\s+/g, '').toUpperCase()
      );
      if (matched && matched.make_model) {
        setFormModel(matched.make_model);
        setIsManualModel(false);
      } else {
        setFormModel('');
      }
    } else {
      setIsManualVehicle(false);
      setFormReg('');
      setFormModel('');
    }
  }

  // Handle model dropdown change
  function handleModelDropdownChange(e) {
    const val = e.target.value;
    if (val === '__custom__') {
      setIsManualModel(true);
      setFormModel('');
    } else {
      setIsManualModel(false);
      setFormModel(val);
    }
  }

  // Quick date helper
  function setQuickDate(daysAhead) {
    const d = new Date();
    d.setDate(d.getDate() + daysAhead);
    setFormStartDate(d.toISOString().split('T')[0]);
  }

  function setNextMonday() {
    const d = new Date();
    const day = d.getDay();
    const diff = d.getDate() + ((7 - day + 1) % 7 || 7);
    const nextMon = new Date(d.setDate(diff));
    setFormStartDate(nextMon.toISOString().split('T')[0]);
  }

  // Form Submission
  async function handleCreateHire(e) {
    e.preventDefault();
    const regToSubmit = formReg.trim();
    if (!regToSubmit) {
      alert('Please select or enter a Vehicle Registration.');
      return;
    }
    if (!formDriverName.trim()) {
      alert('Please enter Driver Full Name.');
      return;
    }
    if (!formEmail.trim() || !formEmail.includes('@')) {
      alert('A valid Driver Email is mandatory for DocuSign digital delivery.');
      return;
    }

    try {
      setSubmitting(true);
      const res = await api.createContract({
        vehicle_registration: regToSubmit,
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
      setSelectedVehicleReg('');
      setFormReg('');
      setFormModel('');
      setFormDriverName('');
      setFormEmail('');
      setFormPhone('');
      setFormLicense('');
      setFormAddress('');

      loadData();
    } catch (err) {
      alert(`Error creating agreement: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  }

  // Quick Action: Send DocuSign
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
      alert(`DocuSign dispatch failed: ${err.message}`);
    } finally {
      setActionLoadingId(null);
    }
  }

  // Quick Action: Sync Status
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

  // Quick Action: Webhook Simulation
  async function handleSimulateWebhook(contract) {
    if (!contract.docusign_envelope_id) {
      alert('Please dispatch a DocuSign agreement first before simulating webhook.');
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

  // Selected vehicle details for preview
  const activeVehicleObj = vehicles.find(
    (v) => v.normalized_registration === formReg.replace(/\s+/g, '').toUpperCase()
  );

  return (
    <div>
      {/* Toast Notification Banner */}
      {notification && (
        <div
          className={`alert-box ${notification.type === 'success' ? 'alert-success' : 'alert-info'}`}
          style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {notification.type === 'success' ? <CheckCircle2 size={18} /> : <RefreshCw size={18} />}
            <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>{notification.message}</span>
          </div>
          <button
            onClick={() => setNotification(null)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit' }}
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* Main Panel */}
      <div className="card-panel">
        <div className="panel-header">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
              <h2 className="panel-title" style={{ margin: 0, fontSize: '1.2rem' }}>
                Fleet Rental Agreements ({total})
              </h2>
              <button
                className="btn btn-primary"
                onClick={() => setShowModal(true)}
                style={{ padding: '8px 16px', fontWeight: 600, gap: '8px' }}
              >
                <PlusCircle size={17} /> New Hire Agreement
              </button>
            </div>
            <p style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '4px' }}>
              Direct driver onboarding, automated contract creation, and DocuSign digital execution
            </p>
          </div>

          {/* Interactive Filter Pills & Search */}
          <div className="filter-bar">
            <div className="filter-pills">
              <button
                className={`filter-pill ${statusFilter === '' ? 'active' : ''}`}
                onClick={() => {
                  setStatusFilter('');
                  setPage(1);
                }}
              >
                All ({total})
              </button>
              <button
                className={`filter-pill ${statusFilter === 'signed' ? 'active' : ''}`}
                onClick={() => {
                  setStatusFilter('signed');
                  setPage(1);
                }}
              >
                Signed
              </button>
              <button
                className={`filter-pill ${statusFilter === 'not_signed' ? 'active' : ''}`}
                onClick={() => {
                  setStatusFilter('not_signed');
                  setPage(1);
                }}
              >
                Not Signed
              </button>
              <button
                className={`filter-pill ${statusFilter === 'no_contract' ? 'active' : ''}`}
                onClick={() => {
                  setStatusFilter('no_contract');
                  setPage(1);
                }}
              >
                No Contract
              </button>
            </div>

            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <input
                type="text"
                className="search-input"
                placeholder="Search plate, driver, model..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setPage(1);
                }}
                style={{ paddingLeft: '32px' }}
              />
              <Search
                size={16}
                color="#94a3b8"
                style={{ position: 'absolute', left: '10px', pointerEvents: 'none' }}
              />
            </div>
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
                  <th style={{ textAlign: 'right' }}>Signature Actions</th>
                </tr>
              </thead>
              <tbody>
                {contracts.length === 0 ? (
                  <tr>
                    <td colSpan="8" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
                      No agreements found matching your search.
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

                      {/* DocuSign Tracking */}
                      <td>
                        {c.normalized_status === 'signed' ? (
                          <span
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '5px',
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

                      {/* Actions */}
                      <td style={{ textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', gap: '6px', alignItems: 'center' }}>
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
                                title="Sync status with DocuSign"
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
                                  border: '1px solid #bbf7d0',
                                }}
                                title="Simulate driver signature webhook"
                                disabled={actionLoadingId === c.id}
                                onClick={() => handleSimulateWebhook(c)}
                              >
                                Simulate Sign
                              </button>
                            </>
                          )}

                          {c.normalized_status === 'signed' && (
                            <span style={{ fontSize: '0.75rem', color: '#16a34a', fontWeight: 600 }}>
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

      {/* INTERACTIVE NEW HIRE MODAL */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div
              style={{
                padding: '20px 24px',
                borderBottom: '1px solid #e2e8f0',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                backgroundColor: '#f8fafc',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div
                  style={{
                    backgroundColor: '#eff6ff',
                    padding: '8px',
                    borderRadius: '8px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <FileSignature size={22} color="#2563eb" />
                </div>
                <div>
                  <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700, color: '#0f172a' }}>
                    Onboard Driver & New Hire Agreement
                  </h3>
                  <p style={{ margin: 0, fontSize: '0.78rem', color: '#64748b' }}>
                    Creates contract, registers driver compliance, and prepares DocuSign envelope
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowModal(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: '#64748b',
                  padding: '4px',
                }}
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleCreateHire} style={{ padding: '24px' }}>
              {/* SECTION 1: VEHICLE SELECTION (DROPDOWNS) */}
              <div style={{ marginBottom: '20px' }}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '0.85rem',
                    fontWeight: 700,
                    color: '#0f172a',
                    marginBottom: '10px',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                  }}
                >
                  <Car size={16} color="#2563eb" /> 1. Vehicle Selection
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  {/* Vehicle Registration Dropdown */}
                  <div>
                    <label className="form-label">Fleet Vehicle Registration *</label>
                    <select
                      className="form-control"
                      value={selectedVehicleReg}
                      onChange={handleVehicleDropdownChange}
                      required
                    >
                      <option value="">-- Choose from Fleet Vehicles ({vehicles.length}) --</option>
                      {vehicles.map((v) => (
                        <option key={v.id} value={v.registration}>
                          {v.registration} {v.make_model ? `(${v.make_model})` : ''}
                        </option>
                      ))}
                      <option value="__custom__">➕ Enter Unlisted / New Plate...</option>
                    </select>

                    {/* Manual Plate Input (if custom chosen) */}
                    {isManualVehicle && (
                      <input
                        type="text"
                        placeholder="Enter Registration (e.g. AB22 XYZ)"
                        value={formReg}
                        onChange={(e) => setFormReg(e.target.value.toUpperCase())}
                        className="form-control"
                        style={{ marginTop: '8px' }}
                        required
                      />
                    )}
                  </div>

                  {/* Vehicle Model Dropdown */}
                  <div>
                    <label className="form-label">Vehicle Make & Model</label>
                    <select
                      className="form-control"
                      value={isManualModel ? '__custom__' : formModel}
                      onChange={handleModelDropdownChange}
                    >
                      <option value="">-- Select Vehicle Model --</option>
                      {POPULAR_MODELS.map((model) => (
                        <option key={model} value={model}>
                          {model}
                        </option>
                      ))}
                      <option value="__custom__">➕ Other / Custom Model...</option>
                    </select>

                    {/* Manual Model Input (if custom chosen) */}
                    {isManualModel && (
                      <input
                        type="text"
                        placeholder="e.g. Toyota Corolla Hybrid"
                        value={formModel}
                        onChange={(e) => setFormModel(e.target.value)}
                        className="form-control"
                        style={{ marginTop: '8px' }}
                      />
                    )}
                  </div>
                </div>

                {/* Selected Vehicle Preview Chip */}
                {formReg && (
                  <div className="selected-vehicle-card">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span className="reg-pill">{formReg}</span>
                      <div>
                        <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#0f172a' }}>
                          {formModel || 'Model unspecified'}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                          {activeVehicleObj?.assigned_driver
                            ? `Currently Assigned: ${activeVehicleObj.assigned_driver}`
                            : 'Available for hire agreement'}
                        </div>
                      </div>
                    </div>
                    <span
                      style={{
                        fontSize: '0.72rem',
                        fontWeight: 600,
                        backgroundColor: '#dbeafe',
                        color: '#1e40af',
                        padding: '3px 8px',
                        borderRadius: '4px',
                      }}
                    >
                      Ready for Contract
                    </span>
                  </div>
                )}
              </div>

              {/* SECTION 2: DRIVER COMPLIANCE DETAILS */}
              <div style={{ marginBottom: '20px' }}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '0.85rem',
                    fontWeight: 700,
                    color: '#0f172a',
                    marginBottom: '10px',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                  }}
                >
                  <User size={16} color="#2563eb" /> 2. Driver Personal & Compliance Info
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '12px' }}>
                  <div>
                    <label className="form-label">Driver Full Name *</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Trelawny Edwards"
                      value={formDriverName}
                      onChange={(e) => setFormDriverName(e.target.value)}
                      className="form-control"
                    />
                  </div>

                  <div>
                    <label className="form-label">
                      Driver Email (For DocuSign Delivery) *
                    </label>
                    <input
                      type="email"
                      required
                      placeholder="driver@example.co.uk"
                      value={formEmail}
                      onChange={(e) => setFormEmail(e.target.value)}
                      className="form-control"
                      style={{
                        borderColor: formEmail && formEmail.includes('@') ? '#16a34a' : undefined,
                      }}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '12px' }}>
                  <div>
                    <label className="form-label">Contact Phone</label>
                    <input
                      type="text"
                      placeholder="e.g. 07123456789"
                      value={formPhone}
                      onChange={(e) => setFormPhone(e.target.value)}
                      className="form-control"
                    />
                  </div>

                  <div>
                    <label className="form-label">UK Driving License Number</label>
                    <input
                      type="text"
                      placeholder="e.g. EDWAR011295TPGYP"
                      value={formLicense}
                      onChange={(e) => setFormLicense(e.target.value.toUpperCase())}
                      className="form-control"
                    />
                  </div>
                </div>

                <div>
                  <label className="form-label">Address & Postcode</label>
                  <input
                    type="text"
                    placeholder="e.g. 37 Penrith Road, Croydon CR7 8PN"
                    value={formAddress}
                    onChange={(e) => setFormAddress(e.target.value)}
                    className="form-control"
                  />
                </div>
              </div>

              {/* SECTION 3: RENTAL TERMS & PRESETS */}
              <div style={{ marginBottom: '20px' }}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '0.85rem',
                    fontWeight: 700,
                    color: '#0f172a',
                    marginBottom: '10px',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                  }}
                >
                  <Calendar size={16} color="#2563eb" /> 3. Rental Terms & Rate
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '12px' }}>
                  <div>
                    <label className="form-label">Weekly Rental Rate (£)</label>
                    <input
                      type="number"
                      step="0.01"
                      required
                      placeholder="325"
                      value={formRate}
                      onChange={(e) => setFormRate(e.target.value)}
                      className="form-control"
                    />
                    <div style={{ display: 'flex', gap: '6px', marginTop: '6px' }}>
                      <span style={{ fontSize: '0.7rem', color: '#64748b' }}>Presets:</span>
                      {['200', '250', '300', '325'].map((amt) => (
                        <button
                          key={amt}
                          type="button"
                          className="quick-btn"
                          onClick={() => setFormRate(amt)}
                        >
                          £{amt}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="form-label">Start Date</label>
                    <input
                      type="date"
                      required
                      value={formStartDate}
                      onChange={(e) => setFormStartDate(e.target.value)}
                      className="form-control"
                    />
                    <div style={{ display: 'flex', gap: '6px', marginTop: '6px' }}>
                      <button
                        type="button"
                        className="quick-btn"
                        onClick={() => setQuickDate(0)}
                      >
                        Today
                      </button>
                      <button
                        type="button"
                        className="quick-btn"
                        onClick={() => setQuickDate(1)}
                      >
                        Tomorrow
                      </button>
                      <button
                        type="button"
                        className="quick-btn"
                        onClick={setNextMonday}
                      >
                        Next Monday
                      </button>
                    </div>
                  </div>
                </div>

                <div>
                  <label className="form-label">Hire Duration</label>
                  <select
                    className="form-control"
                    value={formDuration}
                    onChange={(e) => setFormDuration(e.target.value)}
                  >
                    <option value="7 days">7 Days (1 Week)</option>
                    <option value="14 days">14 Days (2 Weeks)</option>
                    <option value="28 days">28 Days (Standard 4 Weeks Agreement)</option>
                    <option value="90 days">90 Days (3 Months Extended)</option>
                  </select>
                </div>
              </div>

              {/* SECTION 4: DOCUSIGN TOGGLE */}
              <div
                style={{
                  padding: '14px 16px',
                  backgroundColor: '#f8fafc',
                  border: '1px solid #bfdbfe',
                  borderRadius: '8px',
                  marginBottom: '20px',
                }}
              >
                <label style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={formSendDocuSign}
                    onChange={(e) => setFormSendDocuSign(e.target.checked)}
                    style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                  />
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#1e40af' }}>
                        Dispatch DocuSign Agreement to driver immediately
                      </span>
                      <ShieldCheck size={16} color="#2563eb" />
                    </div>
                    <span style={{ display: 'block', fontSize: '0.75rem', color: '#64748b', marginTop: '2px' }}>
                      Renders standard 6-page contract with Section 10 PCN liability transfer under Road Traffic Offenders Act 1988.
                    </span>
                  </div>
                </label>
              </div>

              {/* LIVE SUMMARY BANNER */}
              {formReg && formDriverName && (
                <div
                  style={{
                    backgroundColor: '#f0fdf4',
                    border: '1px solid #bbf7d0',
                    borderRadius: '8px',
                    padding: '10px 14px',
                    marginBottom: '20px',
                    fontSize: '0.82rem',
                    color: '#166534',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                  }}
                >
                  <Sparkles size={16} color="#16a34a" />
                  <span>
                    <strong>Summary:</strong> {formReg} ({formModel || 'Model TBD'}) • Driver: <strong>{formDriverName}</strong> • Rate: <strong>£{formRate}/wk</strong> • DocuSign: {formSendDocuSign ? 'Auto-Dispatch Enabled' : 'Draft Only'}
                  </span>
                </div>
              )}

              {/* BUTTONS */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => setShowModal(false)}
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={submitting}
                  style={{ padding: '10px 20px', fontWeight: 600 }}
                >
                  {submitting ? (
                    <>
                      <div className="spinner" style={{ width: '15px', height: '15px', margin: 0 }}></div>
                      Dispatching to DocuSign...
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
