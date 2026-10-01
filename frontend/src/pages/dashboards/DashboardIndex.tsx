import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { getRoleLandingRoute } from '../../navigation/navigationConfig';
import LoadingSpinner from '../../components/common/LoadingSpinner';

export const DashboardIndex: React.FC = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="h-64 flex items-center justify-center">
        <LoadingSpinner size="lg" label="Routing to role console..." />
      </div>
    );
  }

  if (!user || !user.role) {
    return <Navigate to="/login" replace />;
  }

  const destination = getRoleLandingRoute(user.role);
  return <Navigate to={destination} replace />;
};

export default DashboardIndex;
