import React from 'react';
import RoleDashboardFoundation from './RoleDashboardFoundation';

export const PharmacyDashboard: React.FC = () => {
  return <RoleDashboardFoundation expectedRole="PHARMACIST" />;
};

export default PharmacyDashboard;
