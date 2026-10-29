import React from 'react';

export function KPICard({ title, value, subtitle, icon: Icon, color = 'blue' }) {
  const colorMap = {
    blue: { bg: '#eff6ff', text: '#2563eb' },
    green: { bg: '#dcfce7', text: '#16a34a' },
    amber: { bg: '#fef3c7', text: '#d97706' },
    red: { bg: '#fee2e2', text: '#dc2626' },
    purple: { bg: '#f3e8ff', text: '#7c3aed' },
  };

  const scheme = colorMap[color] || colorMap.blue;

  return (
    <div className="kpi-card">
      <div className="kpi-header">
        <span className="kpi-title">{title}</span>
        {Icon && (
          <div className="kpi-icon" style={{ backgroundColor: scheme.bg, color: scheme.text }}>
            <Icon size={20} />
          </div>
        )}
      </div>
      <div>
        <div className="kpi-value">{value}</div>
        {subtitle && <div className="kpi-subtitle">{subtitle}</div>}
      </div>
    </div>
  );
}
