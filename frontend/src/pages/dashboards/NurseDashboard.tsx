import React from 'react';
import RoleDashboardFoundation from './RoleDashboardFoundation';

export const NurseDashboard: React.FC = () => {
  return <RoleDashboardFoundation expectedRole="NURSE" />;
};

export default NurseDashboard;
