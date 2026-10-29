import React from 'react';

export function StatusBadge({ status, type = 'status' }) {
  if (!status) return <span className="badge badge-unknown">Unknown</span>;

  const s = String(status).toLowerCase();
  let badgeClass = 'badge-unknown';
  let label = status;

  if (s === 'paid' || s === 'signed') {
    badgeClass = 'badge-paid';
    label = s === 'paid' ? 'Paid' : 'Signed';
  } else if (s === 'unpaid' || s === 'not_signed') {
    badgeClass = 'badge-unpaid';
    label = s === 'unpaid' ? 'Unpaid' : 'Not Signed';
  } else if (s === 'action_needed' || s === 'warning') {
    badgeClass = 'badge-action_needed';
    label = s === 'action_needed' ? 'Action Needed' : 'Warning';
  } else if (s === 'conflict' || s === 'critical') {
    badgeClass = 'badge-conflict';
    label = s === 'conflict' ? 'Conflict' : 'Critical';
  } else if (s === 'needs_review' || s === 'info' || s === 'no_contract') {
    badgeClass = 'badge-needs_review';
    label = s === 'needs_review' ? 'Needs Review' : (s === 'no_contract' ? 'No Contract' : s);
  }

  return <span className={`badge ${badgeClass}`}>{label}</span>;
}
