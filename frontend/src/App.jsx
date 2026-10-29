import React, { useEffect, useState } from 'react';
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
      <Sidebar currentTab={currentTab} setTab={setTab} conflictCount={conflictCount} />

      <div className="main-wrapper">
        <header className="topbar">
          <h1 className="page-title">{titles[currentTab] || 'Dashboard'}</h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <span style={{ fontSize: '0.85rem', color: '#64748b' }}>
              System Status: <span style={{ color: '#16a34a', fontWeight: 600 }}>● Connected</span>
            </span>
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
