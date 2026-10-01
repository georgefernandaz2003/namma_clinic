/**
 * Staff Administration & IAM Lifecycle Types
 * Authoritative Backend Contract: apps/accounts/api_v1.py
 */
import type { Role } from './auth';

export type StaffLifecycleStatus =
  | 'INVITED'
  | 'ACTIVE'
  | 'SUSPENDED'
  | 'TRANSFER_PENDING'
  | 'DEACTIVATED';

export const STATUS_LABELS: Record<StaffLifecycleStatus, string> = {
  INVITED: 'Invited (Pending Activation)',
  ACTIVE: 'Active',
  SUSPENDED: 'Suspended (Access Revoked)',
  TRANSFER_PENDING: 'Transfer Pending (Scheduled)',
  DEACTIVATED: 'Deactivated (Archived)',
};

export interface StaffRoleItem {
  id: number;
  role_id: number;
  role_code: string;
  role_name: string;
  effective_from: string;
  effective_to: string | null;
  is_active: boolean;
  facility_name?: string;
}

export interface StaffFacilityContext {
  facility_id: number;
  facility_name: string;
  facility_code: string;
  department_id?: number | null;
  department_name?: string | null;
  is_primary: boolean;
  effective_from: string;
}

export interface StaffDistrictContext {
  district_id: number;
  district_name: string;
  district_code?: string;
}

export interface PersonDetails {
  id: number;
  first_name: string;
  last_name: string;
  gender: string;
  date_of_birth: string;
  phone_number?: string;
}

export interface StaffProfile {
  id: number;
  employee_id: string;
  designation: string;
  department?: number | null;
  status: StaffLifecycleStatus;
  medical_council_reg_number?: string | null;
  person_details: PersonDetails;
  roles: StaffRoleItem[];
  facility_assignment: StaffFacilityContext | null;
  district_context: StaffDistrictContext | null;
}

export interface InviteStaffPayload {
  first_name: string;
  last_name: string;
  gender: string;
  date_of_birth: string;
  phone_number?: string;
  employee_id: string;
  designation: string;
  role_code?: Role | string;
  facility_id: number;
  department_id?: number | null;
  medical_council_reg_number?: string;
  email?: string;
  username?: string;
}

export interface AssignRolePayload {
  role_code: Role | string;
  facility_id?: number | null;
  effective_from?: string;
  effective_to?: string | null;
}

export interface AssignFacilityPayload {
  facility_id: number;
  department_id?: number | null;
  is_primary?: boolean;
  effective_from?: string;
  effective_to?: string | null;
}

export interface TransferStaffPayload {
  new_facility_id: number;
  new_department_id?: number | null;
  effective_date?: string;
  reason?: string;
}

export interface CreateFacilityPayload {
  facility_code: string;
  facility_name: string;
  facility_type: string;
  state: number;
  district: number;
  zone?: number | null;
  ward?: number | null;
  address?: string;
  status?: string;
}