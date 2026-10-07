/**
 * Staff Administration API Service
 * Authoritative Backend Endpoints: apps/accounts/api_v1.py
 */
import apiClient, { parseApiError } from './client';
import type {
  StaffProfile,
  InviteStaffPayload,
  AssignRolePayload,
  AssignFacilityPayload,
  TransferStaffPayload,
  StaffRoleItem,
  StaffFacilityContext,
  CreateFacilityPayload
} from '../types/staff';
import type { Facility } from '../types';

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/**
 * Fetch staff profiles scoped to the current administrator's authority.
 * DHO -> district staff; Clinic Admin -> facility staff.
 */
export const fetchStaffProfiles = async (params?: {
  search?: string;
  status?: string;
  role?: string;
  facility?: string | number;
}): Promise<StaffProfile[]> => {
  try {
    const queryParams = new URLSearchParams();
    if (params?.search) queryParams.append('search', params.search);
    if (params?.status) queryParams.append('status', params.status);
    if (params?.role) queryParams.append('role', params.role);
    if (params?.facility) queryParams.append('facility', String(params.facility));

    const qs = queryParams.toString();
    const url = `v1/accounts/staff-profiles/${qs ? `?${qs}` : ''}`;
    const res = await apiClient.get<PaginatedResponse<StaffProfile> | StaffProfile[]>(url);

    if (Array.isArray(res.data)) {
      return res.data;
    }
    return res.data.results || [];
  } catch (err: unknown) {
    throw new Error(parseApiError(err));
  }
};

/**
 * Fetch single staff profile detail.
 */
export const fetchStaffProfileDetail = async (id: number): Promise<StaffProfile> => {
  try {
    const res = await apiClient.get<StaffProfile>(`v1/accounts/staff-profiles/${id}/`);
    return res.data;
  } catch (err: unknown) {
    throw new Error(parseApiError(err));
  }
};

/**
 * Invite a new staff member (starts in INVITED status).
 */
export const inviteStaff = async (payload: InviteStaffPayload): Promise<StaffProfile> => {
  try {
    const res = await apiClient.post<StaffProfile>('v1/accounts/staff-profiles/invite/', payload);
    return res.data;
  } catch (err: unknown) {
    throw new Error(parseApiError(err));
  }
};

/**
 * Activate a staff member, enabling operational authorization.
 */
export const activateStaff = async (id: number, temporary_password?: string): Promise<StaffProfile> => {
  try {
    const payload = temporary_password ? { temporary_password } : {};
    const res = await apiClient.post<StaffProfile>(`v1/accounts/staff-profiles/${id}/activate/`, payload);
    return res.data;
  } catch (err: unknown) {
    throw new Error(parseApiError(err));
  }
};

/**
 * Suspend staff, revoking operational access.
 */
export const suspendStaff = async (id: number, reason?: string): Promise<StaffProfile> => {
  try {
    const res = await apiClient.post<StaffProfile>(`v1/accounts/staff-profiles/${id}/suspend/`, { reason });
    return res.data;
  } catch (err: unknown) {
    throw new Error(parseApiError(err));
  }
};

/**
 * Deactivate staff, terminating active postings and role assignments.
 */
export const deactivateStaff = async (id: number, reason?: string): Promise<StaffProfile> => {
  try {
    const res = await apiClient.post<StaffProfile>(`v1/accounts/staff-profiles/${id}/deactivate/`, { reason });
    return res.data;
  } catch (err: unknown) {
    throw new Error(parseApiError(err));
  }
};

/**
 * Assign an operational role to a staff member.
 */
export const assignStaffRole = async (id: number, payload: AssignRolePayload): Promise<StaffRoleItem> => {
  try {
    const res = await apiClient.post<StaffRoleItem>(`v1/accounts/staff-profiles/${id}/assign-role/`, payload);
    return res.data;
  } catch (err: unknown) {
    throw new Error(parseApiError(err));
  }
};

/**
 * End an individual active role assignment.
 */
export const endStaffRole = async (roleAssignmentId: number, endDate?: string): Promise<StaffRoleItem> => {
  try {
    const res = await apiClient.post<StaffRoleItem>(
      `v1/accounts/role-assignments/${roleAssignmentId}/end-assignment/`,
      { end_date: endDate }
    );
    return res.data;
  } catch (err: unknown) {
    throw new Error(parseApiError(err));
  }
};

/**
 * Assign staff to a facility.
 */
export const assignStaffFacility = async (
  id: number,
  payload: AssignFacilityPayload
): Promise<StaffFacilityContext> => {
  try {
    const res = await apiClient.post<StaffFacilityContext>(`v1/accounts/staff-profiles/${id}/assign-facility/`, payload);
    return res.data;
  } catch (err: unknown) {
    throw new Error(parseApiError(err));
  }
};

/**
 * Atomically transfer staff to a new primary facility.
 */
export const transferStaff = async (
  id: number,
  payload: TransferStaffPayload
): Promise<StaffFacilityContext> => {
  try {
    const res = await apiClient.post<StaffFacilityContext>(`v1/accounts/staff-profiles/${id}/transfer/`, payload);
    return res.data;
  } catch (err: unknown) {
    throw new Error(parseApiError(err));
  }
};

/**
 * DHO creation of a new clinic facility.
 */
export const createClinicFacility = async (payload: CreateFacilityPayload): Promise<Facility> => {
  try {
    const res = await apiClient.post<Facility>('v1/organization/facilities/', payload);
    return res.data;
  } catch (err: unknown) {
    throw new Error(parseApiError(err));
  }
};