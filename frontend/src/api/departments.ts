/**
 * Department API Service
 * Authoritative Backend Endpoints: apps/facilities/api_v1.py -> DepartmentViewSet
 */
import apiClient, { parseApiError } from './client';
import type { Department, CreateDepartmentPayload, UpdateDepartmentPayload } from '../types';

export const fetchDepartments = async (facilityId?: number): Promise<Department[]> => {
  try {
    const params = facilityId ? { facility: facilityId } : undefined;
    const res = await apiClient.get<any>('v1/organization/departments/', { params });
    const results = res.data?.results || res.data || [];
    return results;
  } catch (err: unknown) {
    throw new Error(parseApiError(err));
  }
};

export const createDepartment = async (payload: CreateDepartmentPayload): Promise<Department> => {
  try {
    const res = await apiClient.post<Department>('v1/organization/departments/', payload);
    return res.data;
  } catch (err: unknown) {
    throw new Error(parseApiError(err));
  }
};

export const updateDepartment = async (id: number, payload: UpdateDepartmentPayload): Promise<Department> => {
  try {
    const res = await apiClient.patch<Department>(`v1/organization/departments/${id}/`, payload);
    return res.data;
  } catch (err: unknown) {
    throw new Error(parseApiError(err));
  }
};

export const deleteDepartment = async (id: number): Promise<void> => {
  try {
    await apiClient.delete(`v1/organization/departments/${id}/`);
  } catch (err: unknown) {
    throw new Error(parseApiError(err));
  }
};
