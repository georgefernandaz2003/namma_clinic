import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { isRouteAllowedForRole } from '../../navigation/navigationConfig';
import DashboardLayout from '../../layouts/DashboardLayout';
import LoadingSpinner from './LoadingSpinner';
import ForbiddenCard from './ForbiddenCard';
import type { Role } from '../../types/auth';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: Role[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
  const { token, user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="h-screen bg-slate-50 flex items-center justify-center">
        <LoadingSpinner size="lg" label="Validating Namma Clinic session..." />
      </div>
    );
  }

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  // 1. Explicit allowedRoles check if defined on the route
  if (allowedRoles && allowedRoles.length > 0) {
    const isRoleAllowed = user?.role && allowedRoles.includes(user.role);
    if (!isRoleAllowed) {
      return (
        <DashboardLayout>
          <ForbiddenCard
            role={user?.role}
            roleDisplay={user?.role_display}
            requestedPath={location.pathname}
          />
        </DashboardLayout>
      );
    }
  }

  // 2. Global route matrix permission check
  const isAllowed = isRouteAllowedForRole(user?.role, location.pathname);

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

export default ProtectedRoute;
