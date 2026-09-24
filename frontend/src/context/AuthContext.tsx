import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import apiClient, { parseApiError } from '../api/client';
import type { UserProfile, Facility } from '../types';

interface AuthContextType {
  user: UserProfile | null;
  activeFacility: Facility | null;
  allFacilities: Facility[];
  token: string | null;
  loading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  setActiveFacility: (facility: Facility) => void;
  refreshUserData: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [activeFacility, setActiveFacilityState] = useState<Facility | null>(null);
  const [allFacilities, setAllFacilities] = useState<Facility[]>([]);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('access_token'));
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const clearError = () => setError(null);

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('active_facility_id');
    setToken(null);
    setUser(null);
    setActiveFacilityState(null);
    setError(null);
  }, []);

  const refreshUserData = useCallback(async () => {
    const currentToken = localStorage.getItem('access_token');
    if (!currentToken) {
      setLoading(false);
      return;
    }

    try {
      // 1. Fetch authenticated user profile
      const userRes = await apiClient.get<UserProfile>('auth/me/');
      const userData = userRes.data;

      // Populate facility name/type from facility_details if not top-level
      if (userData.facility_details) {
        userData.facility_name = userData.facility_name || userData.facility_details.facility_name;
        userData.facility_type = userData.facility_type || userData.facility_details.facility_type;
        userData.district_name = userData.district_name || userData.facility_details.district_name;
      }
      setUser(userData);

      // 2. Fetch accessible facilities
      try {
        const facRes = await apiClient.get<{ results?: Facility[] } | Facility[]>('facilities/');
        const facs: Facility[] = Array.isArray(facRes.data)
          ? facRes.data
          : facRes.data.results || [];
        setAllFacilities(facs);

        const userFacId = userData.assigned_facility;
        if (userData.role !== 'DISTRICT_OFFICER' && userFacId) {
          const userFac = facs.find((f) => f.id === userFacId);
          if (userFac) {
            setActiveFacilityState(userFac);
          } else if (facs.length > 0) {
            setActiveFacilityState(facs[0]);
          }
        } else {
          const savedFacId = localStorage.getItem('active_facility_id');
          if (savedFacId) {
            const found = facs.find((f) => f.id === parseInt(savedFacId, 10));
            if (found) setActiveFacilityState(found);
            else if (facs.length > 0) setActiveFacilityState(facs[0]);
          } else if (facs.length > 0) {
            setActiveFacilityState(facs[0]);
          }
        }
      } catch (facErr) {
        console.warn('Could not retrieve full facilities list', facErr);
      }
    } catch (e) {
      console.error('Session initialization error:', e);
      logout();
    } finally {
      setLoading(false);
    }
  }, [logout]);

  useEffect(() => {
    refreshUserData();
  }, [refreshUserData]);

  const login = async (username: string, password: string) => {
    setError(null);
    try {
      const res = await apiClient.post<{ access: string; refresh: string }>('auth/token/', {
        username: username.trim(),
        password,
      });

      const { access, refresh } = res.data;
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      setToken(access);

      // Immediately fetch profile
      const userRes = await apiClient.get<UserProfile>('auth/me/', {
        headers: { Authorization: `Bearer ${access}` },
      });
      const userData = userRes.data;
      if (userData.facility_details) {
        userData.facility_name = userData.facility_name || userData.facility_details.facility_name;
        userData.facility_type = userData.facility_type || userData.facility_details.facility_type;
        userData.district_name = userData.district_name || userData.facility_details.district_name;
      }
      setUser(userData);
    } catch (err: unknown) {
      const parsedMsg = parseApiError(err);
      setError(parsedMsg);
      throw new Error(parsedMsg);
    }
  };

  const setActiveFacility = (facility: Facility) => {
    if (
      user &&
      user.role !== 'DISTRICT_OFFICER' &&
      user.assigned_facility &&
      user.assigned_facility !== facility.id
    ) {
      console.warn('Facility selection restricted to assigned operational scope.');
      return;
    }
    setActiveFacilityState(facility);
    localStorage.setItem('active_facility_id', facility.id.toString());
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        activeFacility,
        allFacilities,
        token,
        loading,
        error,
        login,
        logout,
        setActiveFacility,
        refreshUserData,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
