import React, { useEffect, useRef, useState } from 'react';
import { Upload, CheckCircle2, AlertTriangle, FileSpreadsheet } from 'lucide-react';
import { api } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';

export function ImportsPage() {
  const [imports, setImports] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [uploadError, setUploadError] = useState(null);
  const [loading, setLoading] = useState(true);
  const fileInputRef = useRef(null);

  async function loadHistory() {
    try {
      setLoading(true);
      const data = await api.getImports(20);
      setImports(data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadHistory();
  }, []);

  async function handleFileSelect(e) {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      setUploadError(null);
      setUploadSuccess(null);

      const result = await api.uploadExcelFile(file);
      setUploadSuccess(
        `Import completed successfully! Cleaned & synchronized ${result.customers_count} customers, ${result.contracts_count} contracts, ${result.vehicles_count} vehicles, and ${result.pcns_count} PCN records.`
      );
      loadHistory();
    } catch (err) {
      setUploadError(err.message || 'File upload and processing failed.');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  }

  return (
    <div>
      {/* Upload Dropzone */}
      <div className="card-panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Upload Excel Workbook</h2>
            <p style={{ fontSize: '0.8rem', color: '#64748b' }}>
              Upload new or updated KA rentals DB workbook (.xlsx, .xls) for automated idempotent sync
            </p>
          </div>
        </div>

        <div style={{ padding: '24px' }}>
          {uploadSuccess && (
            <div className="alert-box alert-info">
              <CheckCircle2 size={18} color="#16a34a" />
              <div>{uploadSuccess}</div>
            </div>
          )}

          {uploadError && (
            <div className="alert-box alert-danger">
              <AlertTriangle size={18} />
              <div>{uploadError}</div>
            </div>
          )}

          <div
            className="upload-dropzone"
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              type="file"
              ref={fileInputRef}
              accept=".xlsx,.xls"
              style={{ display: 'none' }}
              onChange={handleFileSelect}
            />
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
              <div style={{ width: 48, height: 48, borderRadius: 24, background: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#2563eb' }}>
                <Upload size={24} />
              </div>
              <div style={{ fontWeight: 600, fontSize: '1rem' }}>
                {uploading ? 'Processing & Cleaning Workbook...' : 'Click to select or drop KA rentals DB.xlsx here'}
              </div>
              <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                Supported formats: .xlsx, .xls (Max 25MB). Zero loss atomic processing.
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Import History Table */}
      <div className="card-panel">
        <div className="panel-header">
          <h2 className="panel-title">Import Run Audit History</h2>
        </div>

        {loading ? (
          <div className="state-container">
            <div className="spinner"></div>
            <p>Loading import history...</p>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Run ID</th>
                  <th>Source File</th>
                  <th>Status</th>
                  <th>Started At</th>
                  <th>Customers</th>
                  <th>Vehicles</th>
                  <th>Contracts</th>
                  <th>PCNs</th>
                  <th>Issues</th>
                </tr>
              </thead>
              <tbody>
                {imports.length === 0 ? (
                  <tr>
                    <td colSpan="9" style={{ textAlign: 'center', padding: '36px' }}>
                      No workbook imports recorded yet.
                    </td>
                  </tr>
                ) : (
                  imports.map((run) => (
                    <tr key={run.id}>
                      <td style={{ fontWeight: 600 }}>#{run.id}</td>
                      <td>
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                          <FileSpreadsheet size={16} color="#16a34a" />
                          {run.filename}
                        </span>
                      </td>
                      <td>
                        <StatusBadge status={run.status} />
                      </td>
                      <td>{new Date(run.started_at).toLocaleString()}</td>
                      <td>{run.customers_count}</td>
                      <td>{run.vehicles_count}</td>
                      <td>{run.contracts_count}</td>
                      <td>{run.pcns_count}</td>
                      <td>{run.issues_count}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
