import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/common/ProtectedRoute';
import { Login } from './pages/Login';
import DashboardIndex from './pages/dashboards/DashboardIndex';
import DistrictDashboard from './pages/dashboards/DistrictDashboard';
import AdminDashboard from './pages/dashboards/AdminDashboard';
import DoctorDashboard from './pages/dashboards/DoctorDashboard';
import NurseDashboard from './pages/dashboards/NurseDashboard';
import LabDashboard from './pages/dashboards/LabDashboard';
import PharmacyDashboard from './pages/dashboards/PharmacyDashboard';
import NotFound from './pages/NotFound';

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

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Authentication Route */}
          <Route path="/login" element={<Login />} />

          {/* Root and Dashboard Index Redirectors */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardIndex />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardIndex />
              </ProtectedRoute>
            }
          />

          {/* Role-Specific Dashboard Landing Routes */}
          <Route
            path="/dashboard/district"
            element={
              <ProtectedRoute allowedRoles={['DISTRICT_OFFICER']}>
                <DistrictDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard/admin"
            element={
              <ProtectedRoute allowedRoles={['HOSPITAL_ADMIN']}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard/doctor"
            element={
              <ProtectedRoute allowedRoles={['DOCTOR']}>
                <DoctorDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard/nurse"
            element={
              <ProtectedRoute allowedRoles={['NURSE']}>
                <NurseDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard/lab"
            element={
              <ProtectedRoute allowedRoles={['LAB_TECHNICIAN']}>
                <LabDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard/pharmacy"
            element={
              <ProtectedRoute allowedRoles={['PHARMACIST']}>
                <PharmacyDashboard />
              </ProtectedRoute>
            }
          />

          {/* Operational & Clinical Module Routes */}
          <Route path="/network" element={<ProtectedRoute><HealthcareNetwork /></ProtectedRoute>} />
          <Route path="/facilities" element={<ProtectedRoute><Facilities /></ProtectedRoute>} />
          <Route path="/patients" element={<ProtectedRoute><Patients /></ProtectedRoute>} />
          <Route path="/patients/:id" element={<ProtectedRoute><PatientDetail /></ProtectedRoute>} />
          <Route path="/queue" element={<ProtectedRoute><Queue /></ProtectedRoute>} />
          <Route path="/triage" element={<ProtectedRoute allowedRoles={['NURSE']}><Triage /></ProtectedRoute>} />
          <Route path="/consultation" element={<ProtectedRoute allowedRoles={['DOCTOR']}><Consultation /></ProtectedRoute>} />
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

          {/* Fallback & Not Found Handling */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
