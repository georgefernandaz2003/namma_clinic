import apiClient from './client';
import type {
  Visit,
  Patient,
  TriageVitals,
  Consultation,
  DiagnosticTestMaster,
  DiagnosticOrder,
  TestRequest,
  DiagnosticResult,
  MedicineMaster,
  Prescription,
  ReferralOrder,
  FollowUpTask,
  Facility
} from '../types';

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface CreateConsultationPayload {
  visit: number;
  patient: number;
  facility: number;
  chief_complaint: string;
  clinical_history?: string;
  clinical_assessment?: string;
  diagnosis_code: string;
  diagnosis_name: string;
  treatment_plan?: string;
  follow_up_date?: string | null;
  clinical_notes?: string;
}

export interface CreateDiagnosticOrderPayload {
  visit: number;
  facility: number;
  priority?: 'ROUTINE' | 'URGENT' | 'STAT';
  clinical_indication?: string;
  order_date?: string;
}

export interface CreatePrescriptionPayload {
  consultation: number;
  patient: number;
  facility: number;
  notes: string;
}

export interface CreateReferralOrderPayload {
  patient: number;
  visit: number;
  source_facility: number;
  destination_facility: number;
  reason: string;
  urgency?: 'ROUTINE' | 'URGENT' | 'EMERGENCY';
  clinical_summary?: string;
}

export interface CreateFollowUpTaskPayload {
  patient: number;
  facility: number;
  due_date: string;
  category?: 'GENERAL' | 'NCD_ROUTINE' | 'POST_REFERRAL' | 'LAB_REVIEW';
  originating_visit?: number | null;
  referral?: number | null;
  clinical_instructions?: string;
}

// 1. Visits & Encounters
export const getVisits = async (params?: Record<string, string | number>): Promise<Visit[]> => {
  const query = params ? '?' + new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString() : '';
  const res = await apiClient.get<PaginatedResponse<Visit> | Visit[]>(`v1/visits/${query}`);
  if (Array.isArray(res.data)) return res.data;
  return res.data.results || [];
};

export const getVisit = async (visitId: number): Promise<Visit> => {
  const res = await apiClient.get<Visit>(`v1/visits/${visitId}/`);
  return res.data;
};

export const updateVisit = async (visitId: number, data: Partial<Visit>): Promise<Visit> => {
  const res = await apiClient.patch<Visit>(`v1/visits/${visitId}/`, data);
  return res.data;
};

// 2. Patients
export const getPatient = async (patientId: number): Promise<Patient> => {
  const res = await apiClient.get<Patient>(`v1/patients/${patientId}/`);
  return res.data;
};

// 3. Triage
export const getTriageVitals = async (visitId: number): Promise<TriageVitals | null> => {
  try {
    const res = await apiClient.get<PaginatedResponse<TriageVitals> | TriageVitals[]>(`v1/clinical/triage/?visit=${visitId}`);
    const items = Array.isArray(res.data) ? res.data : res.data.results || [];
    return items.length > 0 ? items[0] : null;
  } catch {
    return null;
  }
};

// 4. Consultations
export const getConsultations = async (params?: Record<string, string | number>): Promise<Consultation[]> => {
  const query = params ? '?' + new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString() : '';
  const res = await apiClient.get<PaginatedResponse<Consultation> | Consultation[]>(`v1/clinical/consultations/${query}`);
  if (Array.isArray(res.data)) return res.data;
  return res.data.results || [];
};

export const createConsultation = async (payload: CreateConsultationPayload): Promise<Consultation> => {
  const res = await apiClient.post<Consultation>('v1/clinical/consultations/', payload);
  return res.data;
};

// 5. Diagnostics
export const getDiagnosticTestMasters = async (): Promise<DiagnosticTestMaster[]> => {
  const res = await apiClient.get<PaginatedResponse<DiagnosticTestMaster> | DiagnosticTestMaster[]>('v1/diagnostics/tests/');
  if (Array.isArray(res.data)) return res.data;
  return res.data.results || [];
};

export const createDiagnosticOrder = async (payload: CreateDiagnosticOrderPayload): Promise<DiagnosticOrder> => {
  const res = await apiClient.post<DiagnosticOrder>('v1/diagnostics/orders/', payload);
  return res.data;
};

export const createTestRequest = async (payload: { diagnostic_order: number; test_master: number }): Promise<TestRequest> => {
  const res = await apiClient.post<TestRequest>('v1/diagnostics/requests/', payload);
  return res.data;
};

export const getDiagnosticOrders = async (params?: Record<string, string | number>): Promise<DiagnosticOrder[]> => {
  const query = params ? '?' + new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString() : '';
  const res = await apiClient.get<PaginatedResponse<DiagnosticOrder> | DiagnosticOrder[]>(`v1/diagnostics/orders/${query}`);
  if (Array.isArray(res.data)) return res.data;
  return res.data.results || [];
};

export const getDiagnosticResults = async (): Promise<DiagnosticResult[]> => {
  const res = await apiClient.get<PaginatedResponse<DiagnosticResult> | DiagnosticResult[]>('v1/diagnostics/results/');
  if (Array.isArray(res.data)) return res.data;
  return res.data.results || [];
};

// 6. Pharmacy & Medicines
export const getMedicines = async (): Promise<MedicineMaster[]> => {
  const res = await apiClient.get<PaginatedResponse<MedicineMaster> | MedicineMaster[]>('v1/pharmacy/medicines/');
  if (Array.isArray(res.data)) return res.data;
  return res.data.results || [];
};

export const createPrescription = async (payload: CreatePrescriptionPayload): Promise<Prescription> => {
  const res = await apiClient.post<Prescription>('v1/pharmacy/prescriptions/', payload);
  return res.data;
};

export const getPrescriptions = async (params?: Record<string, string | number>): Promise<Prescription[]> => {
  const query = params ? '?' + new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString() : '';
  const res = await apiClient.get<PaginatedResponse<Prescription> | Prescription[]>(`v1/pharmacy/prescriptions/${query}`);
  if (Array.isArray(res.data)) return res.data;
  return res.data.results || [];
};

// 7. Facilities (for referrals)
export const getFacilities = async (): Promise<Facility[]> => {
  const res = await apiClient.get<PaginatedResponse<Facility> | Facility[]>('v1/organization/facilities/');
  if (Array.isArray(res.data)) return res.data;
  return res.data.results || [];
};

// 8. Referrals
export const createReferralOrder = async (payload: CreateReferralOrderPayload): Promise<ReferralOrder> => {
  const res = await apiClient.post<ReferralOrder>('v1/referrals/orders/', payload);
  return res.data;
};

// 9. Follow-Up
export const createFollowUpTask = async (payload: CreateFollowUpTaskPayload): Promise<FollowUpTask> => {
  const res = await apiClient.post<FollowUpTask>('v1/referrals/followups/', payload);
  return res.data;
};

export const getFollowUpTasks = async (params?: Record<string, string | number>): Promise<FollowUpTask[]> => {
  const query = params ? '?' + new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString() : '';
  const res = await apiClient.get<PaginatedResponse<FollowUpTask> | FollowUpTask[]>(`v1/referrals/followups/${query}`);
  if (Array.isArray(res.data)) return res.data;
  return res.data.results || [];
};
