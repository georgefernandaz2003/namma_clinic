import React from 'react';
import RoleDashboardFoundation from './RoleDashboardFoundation';

export const AdminDashboard: React.FC = () => {
  return <RoleDashboardFoundation expectedRole="HOSPITAL_ADMIN" />;
};

export default AdminDashboard;
