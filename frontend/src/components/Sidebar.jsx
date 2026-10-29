import React from 'react';
import {
  LayoutDashboard,
  AlertTriangle,
  FileText,
  ShieldAlert,
  FileSpreadsheet,
  FileCheck2,
  Car,
} from 'lucide-react';

export function Sidebar({ currentTab, setTab, conflictCount = 0 }) {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'pcns', label: 'PCN Violations', icon: AlertTriangle, badge: conflictCount > 0 ? `${conflictCount} Conflict` : null },
    { id: 'contracts', label: 'Contracts & Fleet', icon: FileText },
    { id: 'issues', label: 'Data Quality', icon: ShieldAlert },
    { id: 'reports', label: 'Daily Report', icon: FileCheck2 },
    { id: 'imports', label: 'Excel Import', icon: FileSpreadsheet },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <Car size={24} color="#38bdf8" />
          <span>KA Rentals</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => setTab(item.id)}
            >
              <Icon size={18} />
              <span>{item.label}</span>
              {item.badge && <span className="nav-badge">{item.badge}</span>}
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div>Fleet Automation Prototype</div>
        <div>v0.1.0 • UK Operations</div>
      </div>
    </aside>
  );
}
