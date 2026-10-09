import apiClient from './client';
import type {
  Visit,
  Patient,
  TriageVitals,
  CreateTriagePayload,
  Consultation,
  DiagnosticTestMaster,
  DiagnosticOrder,
  TestRequest,
  Specimen,
  DiagnosticResult,
  DiagnosticResultAmendment,
  MedicineMaster,
  MedicineBatch,
  Prescription,
  Dispensation,
  CreateDispensationPayload,
  InventoryLedger,
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

export interface CreateSpecimenPayload {
  diagnostic_order: number;
  barcode_identifier: string;
  specimen_type: string;
  test_request_ids?: number[];
}

export interface CreateDiagnosticResultPayload {
  test_request: number;
  result_value_text?: string;
  result_value_numeric?: number | null;
  reference_range_applied?: string;
  is_abnormal?: boolean;
  is_critical_panic?: boolean;
}

export interface AmendDiagnosticResultPayload {
  amendment_reason: string;
  amended_value_text?: string;
  amended_value_numeric?: number | null;
}

export interface CreatePrescriptionItemPayload {
  medicine?: number;
  medicine_id?: number;
  medicine_name?: string;
  dosage?: string;
  frequency?: string;
  duration_days?: number;
  quantity?: number;
}

export interface CreatePrescriptionPayload {
  consultation: number;
  patient: number;
  facility: number;
  notes: string;
  items?: CreatePrescriptionItemPayload[];
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
    const matched = items.find((item) => {
      const vId = typeof item.visit === 'object' && item.visit !== null ? (item.visit as any).id : item.visit;
      return Number(vId) === Number(visitId);
    });
    return matched || null;
  } catch {
    return null;
  }
};

export const createTriageVitals = async (payload: CreateTriagePayload): Promise<TriageVitals> => {
  const res = await apiClient.post<TriageVitals>('v1/clinical/triage/', payload);
  return res.data;
};

export const updateTriageVitals = async (triageId: number, payload: Partial<CreateTriagePayload>): Promise<TriageVitals> => {
  const res = await apiClient.patch<TriageVitals>(`v1/clinical/triage/${triageId}/`, payload);
  return res.data;
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

export const updateConsultation = async (consultationId: number, payload: Partial<CreateConsultationPayload>): Promise<Consultation> => {
  const res = await apiClient.patch<Consultation>(`v1/clinical/consultations/${consultationId}/`, payload);
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

export const getDiagnosticOrder = async (orderId: number): Promise<DiagnosticOrder> => {
  const res = await apiClient.get<DiagnosticOrder>(`v1/diagnostics/orders/${orderId}/`);
  return res.data;
};

export const getTestRequests = async (params?: Record<string, string | number>): Promise<TestRequest[]> => {
  const query = params ? '?' + new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString() : '';
  const res = await apiClient.get<PaginatedResponse<TestRequest> | TestRequest[]>(`v1/diagnostics/requests/${query}`);
  if (Array.isArray(res.data)) return res.data;
  return res.data.results || [];
};

export const getSpecimens = async (params?: Record<string, string | number>): Promise<Specimen[]> => {
  const query = params ? '?' + new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString() : '';
  const res = await apiClient.get<PaginatedResponse<Specimen> | Specimen[]>(`v1/diagnostics/specimens/${query}`);
  if (Array.isArray(res.data)) return res.data;
  return res.data.results || [];
};

export const createSpecimen = async (payload: CreateSpecimenPayload): Promise<Specimen> => {
  const res = await apiClient.post<Specimen>('v1/diagnostics/specimens/', payload);
  return res.data;
};

export const getDiagnosticResults = async (params?: Record<string, string | number>): Promise<DiagnosticResult[]> => {
  const query = params ? '?' + new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString() : '';
  const res = await apiClient.get<PaginatedResponse<DiagnosticResult> | DiagnosticResult[]>(`v1/diagnostics/results/${query}`);
  if (Array.isArray(res.data)) return res.data;
  return res.data.results || [];
};

export const createDiagnosticResult = async (payload: CreateDiagnosticResultPayload): Promise<DiagnosticResult> => {
  const res = await apiClient.post<DiagnosticResult>('v1/diagnostics/results/', payload);
  return res.data;
};

export const verifyDiagnosticResult = async (resultId: number): Promise<DiagnosticResult> => {
  const res = await apiClient.post<DiagnosticResult>(`v1/diagnostics/results/${resultId}/verify/`);
  return res.data;
};

export const amendDiagnosticResult = async (resultId: number, payload: AmendDiagnosticResultPayload): Promise<DiagnosticResult> => {
  const res = await apiClient.post<DiagnosticResult>(`v1/diagnostics/results/${resultId}/amend/`, payload);
  return res.data;
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

export const getPrescription = async (id: number): Promise<Prescription> => {
  const res = await apiClient.get<Prescription>(`v1/pharmacy/prescriptions/${id}/`);
  return res.data;
};

export const verifyPrescription = async (id: number, notes?: string): Promise<Prescription> => {
  const res = await apiClient.post<Prescription>(`v1/pharmacy/prescriptions/${id}/verify/`, { notes: notes || '', reason: notes || '' });
  return res.data;
};

export const holdPrescription = async (id: number, notes?: string): Promise<Prescription> => {
  const res = await apiClient.post<Prescription>(`v1/pharmacy/prescriptions/${id}/hold/`, { notes: notes || '' });
  return res.data;
};

export const releaseHoldPrescription = async (id: number, notes?: string): Promise<Prescription> => {
  const res = await apiClient.post<Prescription>(`v1/pharmacy/prescriptions/${id}/release-hold/`, { notes: notes || '' });
  return res.data;
};

export const rejectPrescription = async (id: number, reason: string): Promise<Prescription> => {
  const res = await apiClient.post<Prescription>(`v1/pharmacy/prescriptions/${id}/reject/`, { reason });
  return res.data;
};

export const getMedicineBatches = async (params?: Record<string, string | number>): Promise<MedicineBatch[]> => {
  const query = params ? '?' + new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString() : '';
  const res = await apiClient.get<PaginatedResponse<MedicineBatch> | MedicineBatch[]>(`v1/pharmacy/batches/${query}`);
  if (Array.isArray(res.data)) return res.data;
  return res.data.results || [];
};

export const getDispensations = async (params?: Record<string, string | number>): Promise<Dispensation[]> => {
  const query = params ? '?' + new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString() : '';
  const res = await apiClient.get<PaginatedResponse<Dispensation> | Dispensation[]>(`v1/pharmacy/dispensations/${query}`);
  if (Array.isArray(res.data)) return res.data;
  return res.data.results || [];
};

export const createDispensation = async (payload: CreateDispensationPayload): Promise<Dispensation> => {
  const res = await apiClient.post<Dispensation>('v1/pharmacy/dispensations/', payload);
  return res.data;
};

export const getInventoryLedger = async (params?: Record<string, string | number>): Promise<InventoryLedger[]> => {
  const query = params ? '?' + new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString() : '';
  const res = await apiClient.get<PaginatedResponse<InventoryLedger> | InventoryLedger[]>(`v1/pharmacy/ledger/${query}`);
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

export const adjustMedicineBatch = async (
  batchId: number,
  payload: { physical_count?: number; quantity_delta?: number; remarks?: string }
): Promise<MedicineBatch> => {
  const res = await apiClient.post<MedicineBatch>(`v1/pharmacy/batches/${batchId}/adjust/`, payload);
  return res.data;
};
