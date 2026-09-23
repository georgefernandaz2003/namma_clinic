import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';
import type { User, Facility } from '../types';

interface AuthContextType {
  user: User | null;
  activeFacility: Facility | null;
  allFacilities: Facility[];
  token: string | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  setActiveFacility: (facility: Facility | null) => void;
  refreshUserData: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [activeFacility, setActiveFacilityState] = useState<Facility | null>(null);
  const [allFacilities, setAllFacilities] = useState<Facility[]>([]);
  const [token, setToken] = useState<string | null>(localStorage.getItem('access_token'));
  const [loading, setLoading] = useState<boolean>(true);

  const refreshUserData = async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const userRes = await api.get('auth/me/');
      setUser(userRes.data);
      
      const facRes = await api.get('facilities/');
      const facs: Facility[] = facRes.data.results || facRes.data || [];
      setAllFacilities(facs);

      const userFacId = userRes.data.assigned_facility;
      if (userRes.data.role !== 'DISTRICT_OFFICER') {
        if (userFacId) {
          const userFac = facs.find(f => f.id === userFacId);
          if (userFac) setActiveFacilityState(userFac);
          else if (facs.length > 0) setActiveFacilityState(facs[0]);
        } else if (facs.length > 0) {
          setActiveFacilityState(facs[0]);
        }
      } else {
        // District Officer defaults to district-wide (null) unless a specific facility was explicitly saved
        const savedFacId = localStorage.getItem('active_facility_id');
        if (savedFacId) {
          const found = facs.find(f => f.id === parseInt(savedFacId));
          if (found) setActiveFacilityState(found);
          else setActiveFacilityState(null);
        } else {
          setActiveFacilityState(null);
        }
      }

    } catch (e) {
      console.error('Auth verification failed', e);
      logout();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshUserData();
  }, [token]);

  const login = async (username: string, password: string) => {
    const res = await api.post('auth/token/', { username, password });
    const accessToken = res.data.access;
    const refreshToken = res.data.refresh;
    
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    setToken(accessToken);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('active_facility_id');
    setToken(null);
    setUser(null);
    setActiveFacilityState(null);
  };

  const setActiveFacility = (facility: Facility | null) => {
    if (facility && user && user.role !== 'DISTRICT_OFFICER' && user.assigned_facility && user.assigned_facility !== facility.id) {
      console.warn('Facility switching is restricted to your assigned facility scope.');
      return;
    }
    setActiveFacilityState(facility);
    if (facility) {
      localStorage.setItem('active_facility_id', facility.id.toString());
    } else {
      localStorage.removeItem('active_facility_id');
    }
  };


  return (
    <AuthContext.Provider
      value={{
        user,
        activeFacility,
        allFacilities,
        token,
        loading,
        login,
        logout,
        setActiveFacility,
        refreshUserData
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};
