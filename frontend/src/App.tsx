import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { Landing } from './pages/Landing';
import { Login } from './pages/Login';
import { Signup } from './pages/Signup';
import { Dashboard } from './pages/Dashboard';
import { NetworkExplorer } from './pages/NetworkExplorer';
import { Transactions } from './pages/Transactions';
import { NewCustomer } from './pages/NewCustomer';
import { Identities } from './pages/Identities';
import { RiskIntelligence } from './pages/RiskIntelligence';
import { Alerts } from './pages/Alerts';
import { Investigations } from './pages/Investigations';
import { InvestigationDetail } from './pages/InvestigationDetail';
import { BlockchainVerification } from './pages/BlockchainVerification';
import { AuditLogs } from './pages/AuditLogs';
import { DataImport } from './pages/DataImport';
import { Settings } from './pages/Settings';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />

        {/* Protected App Shell */}
        <Route element={<AppShell />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/network" element={<NetworkExplorer />} />
          <Route path="/transactions" element={<Transactions />} />
          <Route path="/customers/new" element={<NewCustomer />} />
          <Route path="/identities" element={<Identities />} />
          <Route path="/risk-intelligence" element={<RiskIntelligence />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/investigations" element={<Investigations />} />
          <Route path="/investigations/:id" element={<InvestigationDetail />} />
          <Route path="/blockchain" element={<BlockchainVerification />} />
          <Route path="/audit-logs" element={<AuditLogs />} />
          <Route path="/data-import" element={<DataImport />} />
          <Route path="/settings" element={<Settings />} />
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

