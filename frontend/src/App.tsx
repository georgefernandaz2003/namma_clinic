import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { isPathAllowedForRole } from './utils/permissions';
import { DashboardLayout } from './layouts/DashboardLayout';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { HealthcareNetwork } from './pages/HealthcareNetwork';
import { Facilities } from './pages/Facilities';
import { Patients } from './pages/Patients';
import { PatientDetail } from './pages/PatientDetail';
import { Queue } from './pages/Queue';
import { Triage } from './pages/Triage';
import { Consultation } from './pages/Consultation';
import { Laboratory } from './pages/Laboratory';
import { Pharmacy } from './pages/Pharmacy';
import { Referrals } from './pages/Referrals';
import { FollowUps } from './pages/FollowUps';
import { NCD } from './pages/NCD';
import { Surveillance } from './pages/Surveillance';
import { Outreach } from './pages/Outreach';
import { Wellness } from './pages/Wellness';
import { ARS } from './pages/ARS';
import { Quality } from './pages/Quality';
import { Infrastructure } from './pages/Infrastructure';
import { Reports } from './pages/Reports';
import { Alerts } from './pages/Alerts';
import { Integrations } from './pages/Integrations';
import { Compliance } from './pages/Compliance';
import { Audit } from './pages/Audit';
import LoadingSpinner from './components/common/LoadingSpinner';
import ForbiddenCard from './components/common/ForbiddenCard';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { token, user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="h-screen bg-slate-50 flex items-center justify-center">
        <LoadingSpinner size="lg" label="Initializing Namma Clinic Console..." />
      </div>
    );
  }

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  const isAllowed = isPathAllowedForRole(user?.role, location.pathname);

  return (
    <DashboardLayout>
      {isAllowed ? (
        children
      ) : (
        <ForbiddenCard
          role={user?.role}
          roleDisplay={user?.role_display}
          requestedPath={location.pathname}
        />
      )}
    </DashboardLayout>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/network" element={<ProtectedRoute><HealthcareNetwork /></ProtectedRoute>} />
          <Route path="/facilities" element={<ProtectedRoute><Facilities /></ProtectedRoute>} />
          <Route path="/patients" element={<ProtectedRoute><Patients /></ProtectedRoute>} />
          <Route path="/patients/:id" element={<ProtectedRoute><PatientDetail /></ProtectedRoute>} />
          <Route path="/queue" element={<ProtectedRoute><Queue /></ProtectedRoute>} />
          <Route path="/triage" element={<ProtectedRoute><Triage /></ProtectedRoute>} />
          <Route path="/consultation" element={<ProtectedRoute><Consultation /></ProtectedRoute>} />
          <Route path="/lab" element={<ProtectedRoute><Laboratory /></ProtectedRoute>} />
          <Route path="/pharmacy" element={<ProtectedRoute><Pharmacy /></ProtectedRoute>} />
          <Route path="/referrals" element={<ProtectedRoute><Referrals /></ProtectedRoute>} />
          <Route path="/followups" element={<ProtectedRoute><FollowUps /></ProtectedRoute>} />
          <Route path="/ncd" element={<ProtectedRoute><NCD /></ProtectedRoute>} />
          <Route path="/surveillance" element={<ProtectedRoute><Surveillance /></ProtectedRoute>} />
          <Route path="/outreach" element={<ProtectedRoute><Outreach /></ProtectedRoute>} />
          <Route path="/wellness" element={<ProtectedRoute><Wellness /></ProtectedRoute>} />
          <Route path="/ars" element={<ProtectedRoute><ARS /></ProtectedRoute>} />
          <Route path="/quality" element={<ProtectedRoute><Quality /></ProtectedRoute>} />
          <Route path="/infrastructure" element={<ProtectedRoute><Infrastructure /></ProtectedRoute>} />
          <Route path="/reports" element={<ProtectedRoute><Reports /></ProtectedRoute>} />
          <Route path="/alerts" element={<ProtectedRoute><Alerts /></ProtectedRoute>} />
          <Route path="/integrations" element={<ProtectedRoute><Integrations /></ProtectedRoute>} />
          <Route path="/compliance" element={<ProtectedRoute><Compliance /></ProtectedRoute>} />
          <Route path="/audit" element={<ProtectedRoute><Audit /></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
