import React, { useEffect, useState } from 'react';
import { Menu, Car } from 'lucide-react';
import { Sidebar } from './components/Sidebar';
import { OverviewPage } from './pages/OverviewPage';
import { PCNsPage } from './pages/PCNsPage';
import { ContractsPage } from './pages/ContractsPage';
import { DataQualityPage } from './pages/DataQualityPage';
import { ImportsPage } from './pages/ImportsPage';
import { ReportPreviewPage } from './pages/ReportPreviewPage';
import { api } from './services/api';

export function App() {
  const [currentTab, setTab] = useState('overview');
  const [conflictCount, setConflictCount] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    async function checkConflicts() {
      try {
        const sum = await api.getDashboardSummary();
        setConflictCount(sum.conflict_pcns || 0);
      } catch (_) {
        // Ignored on initial boot
      }
    }
    checkConflicts();
  }, [currentTab]);

  const titles = {
    overview: 'Operations Overview',
    pcns: 'PCN Infringement Notices',
    contracts: 'Rental Agreements & Fleet',
    issues: 'Data Quality & Anomaly Log',
    reports: 'Daily Report Preview',
    imports: 'Workbook Import & History',
  };

  return (
    <div className="app-layout">
      {/* Mobile Drawer Backdrop */}
      <div
        className={`sidebar-backdrop ${sidebarOpen ? 'open' : ''}`}
        onClick={() => setSidebarOpen(false)}
        aria-hidden="true"
      />

      {/* Modern Sidebar */}
      <Sidebar
        currentTab={currentTab}
        setTab={setTab}
        conflictCount={conflictCount}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="main-wrapper">
        <header className="topbar">
          <div className="topbar-left">
            <button
              type="button"
              className="mobile-menu-btn"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open Navigation Menu"
            >
              <Menu size={20} />
            </button>
            <div className="topbar-brand-mobile">
              <Car size={18} color="#2563eb" />
              <span>KA Rentals</span>
            </div>
            <h1 className="page-title">{titles[currentTab] || 'Dashboard'}</h1>
          </div>

          <div className="topbar-right">
            <div className="system-status-pill">
              <span className="live-dot" />
              <span className="status-label">Live API</span>
            </div>
          </div>
        </header>

        <main className="content-area">
          {currentTab === 'overview' && <OverviewPage setTab={setTab} />}
          {currentTab === 'pcns' && <PCNsPage />}
          {currentTab === 'contracts' && <ContractsPage />}
          {currentTab === 'issues' && <DataQualityPage />}
          {currentTab === 'reports' && <ReportPreviewPage />}
          {currentTab === 'imports' && <ImportsPage />}
        </main>
      </div>
    </div>
  );
}

export default App;
