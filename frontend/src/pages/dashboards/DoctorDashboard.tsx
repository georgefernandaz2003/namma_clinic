import React from 'react';
import RoleDashboardFoundation from './RoleDashboardFoundation';

export const DoctorDashboard: React.FC = () => {
  return <RoleDashboardFoundation expectedRole="DOCTOR" />;
};

export default DoctorDashboard;
