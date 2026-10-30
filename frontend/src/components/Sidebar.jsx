import React from 'react';
import {
  LayoutDashboard,
  AlertTriangle,
  FileText,
  ShieldAlert,
  FileSpreadsheet,
  FileCheck2,
  Car,
  X,
  Radio,
} from 'lucide-react';

export function Sidebar({ currentTab, setTab, conflictCount = 0, isOpen = false, onClose = () => {} }) {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    {
      id: 'pcns',
      label: 'PCN Violations',
      icon: AlertTriangle,
      badge: conflictCount > 0 ? `${conflictCount} Conflict` : null,
      badgeColor: 'conflict',
    },
    { id: 'contracts', label: 'Contracts & Fleet', icon: FileText },
    { id: 'issues', label: 'Data Quality', icon: ShieldAlert },
    { id: 'reports', label: 'Daily Report', icon: FileCheck2 },
    { id: 'imports', label: 'Excel Import', icon: FileSpreadsheet },
  ];

  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
      {/* Brand Header */}
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <div className="logo-icon-wrap">
            <Car size={20} color="#ffffff" />
          </div>
          <div className="logo-text-wrap">
            <span className="logo-title">KA Rentals</span>
            <span className="logo-subtitle">FLEET AUTOMATION</span>
          </div>
        </div>

        {/* Mobile Close Button */}
        <button
          type="button"
          className="sidebar-close-btn"
          onClick={onClose}
          aria-label="Close navigation"
        >
          <X size={20} />
        </button>
      </div>

      {/* Navigation Links */}
      <div className="nav-section-label">MAIN NAVIGATION</div>
      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => {
                setTab(item.id);
                onClose();
              }}
            >
              <div className="nav-icon-wrap">
                <Icon size={18} />
              </div>
              <span className="nav-label">{item.label}</span>
              {item.badge && (
                <span className={`nav-badge ${item.badgeColor === 'conflict' ? 'badge-pulse' : ''}`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Modern Sidebar Footer */}
      <div className="sidebar-footer">
        <div className="footer-status-row">
          <span className="live-dot" />
          <span className="status-text">Cloud Engine Active</span>
        </div>
        <div className="footer-subtext">KA Fleet Platform • v0.1.0 UK</div>
      </div>
    </aside>
  );
}
