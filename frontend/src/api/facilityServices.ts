/**
 * Authoritative API Client for Facility Services and Service Catalog (Phase 33).
 */
import apiClient from './client';
import type { FacilityService, ServiceMaster } from '../types';

export const fetchFacilityServices = async (facilityId?: number): Promise<FacilityService[]> => {
  const url = facilityId ? `v1/organization/facility-services/?facility=${facilityId}` : 'v1/organization/facility-services/';
  const res = await apiClient.get<any>(url);
  return res.data?.results || res.data || [];
};

export const toggleFacilityService = async (id: number, isAvailable: boolean): Promise<FacilityService> => {
  const res = await apiClient.patch<FacilityService>(`v1/organization/facility-services/${id}/`, {
    is_available: isAvailable,
  });
  return res.data;
};

export const fetchServiceMasters = async (): Promise<ServiceMaster[]> => {
  const res = await apiClient.get<any>('v1/organization/services/');
  return res.data?.results || res.data || [];
};
