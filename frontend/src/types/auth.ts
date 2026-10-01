/**
 * Authentication & IAM Types
 * Authoritative Backend Contract: docs/FRONTEND_API_CONTRACT.md (Section 2)
 */

export type Role =
  | 'DISTRICT_OFFICER'
  | 'HOSPITAL_ADMIN'
  | 'DOCTOR'
  | 'NURSE'
  | 'COMPOUNDER'
  | 'LAB_TECHNICIAN'
  | 'PHARMACIST'
  | 'INVENTORY';

export const ROLE_LABELS: Record<Role, string> = {
  DISTRICT_OFFICER: 'District Health Officer',
  HOSPITAL_ADMIN: 'Hospital Administrator (Clinic Admin)',
  DOCTOR: 'Doctor (Medical Officer)',
  NURSE: 'Staff Nurse',
  COMPOUNDER: 'Compounder',
  LAB_TECHNICIAN: 'Lab Technician',
  PHARMACIST: 'Pharmacist',
  INVENTORY: 'Inventory Manager',
};

export type ScopeType = 'DISTRICT' | 'FACILITY' | 'GLOBAL';

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface TokenRefreshRequest {
  refresh: string;
}

export interface TokenRefreshResponse {
  access: string;
}

export interface FacilitySummary {
  id: number;
  facility_code: string;
  facility_name: string;
  facility_type: string;
  district_name?: string;
}

export interface UserProfile {
  id: number;
  username: string;
  full_name: string;
  email: string;
  phone: string;
  role: Role;
  role_display: string;
  roles?: string[];
  assigned_facility: number | null;
  assigned_district: number | null;
  facility_details: FacilitySummary | null;
  facility_name?: string;
  facility_type?: string;
  district_name?: string;
  permissions: string[];
  scope_type: ScopeType;
  is_superuser?: boolean;
}

export type User = UserProfile;

export interface LoginCredentials {
  username: string;
  password: string;
}
