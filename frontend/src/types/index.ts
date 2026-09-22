export type Role =
  | 'DISTRICT_OFFICER'
  | 'HOSPITAL_ADMIN'
  | 'DOCTOR'
  | 'NURSE'
  | 'LAB_TECHNICIAN'
  | 'PHARMACIST';

export interface User {
  id: number;
  username: string;
  full_name: string;
  email: string;
  phone: string;
  role: Role;
  role_display: string;
  assigned_facility: number | null;
  facility_name?: string;
  facility_type?: string;
  assigned_district: number | null;
  district_name?: string;
}

export type FacilityType =
  | 'MAIN_HOSPITAL'
  | 'REFERRAL_HOSPITAL'
  | 'SECONDARY_HOSPITAL'
  | 'UPHC'
  | 'NAMMA_CLINIC'
  | 'URBAN_CLINIC'
  | 'RURAL_CLINIC'
  | 'VILLAGE_CLINIC'
  | 'DIAGNOSTIC_CENTER'
  | 'OTHER';

export interface FacilityRelationship {
  id: number;
  source_facility: number;
  source_name?: string;
  source_type?: string;
  destination_facility: number;
  destination_name?: string;
  destination_type?: string;
  relationship_type: 'PARENT' | 'REFERRAL' | 'SPECIALIST' | 'EMERGENCY' | 'DIAGNOSTIC' | 'SUPPORT' | 'TELECONSULTATION';
  service: string;
  priority: string;
  distance_km: number;
  active: boolean;
  notes: string;
}

export interface Facility {
  id: number;
  facility_code: string;
  facility_name: string;
  facility_type: FacilityType;
  parent_facility: number | null;
  parent_name?: string;
  district: number;
  district_name?: string;
  zone?: number | null;
  zone_name?: string;
  ward?: number | null;
  ward_name?: string;
  city_or_ulb: string;
  urban_rural: 'URBAN' | 'RURAL';
  address: string;
  latitude: number;
  longitude: number;
  population_served: number;
  vulnerable_population: number;
  phone: string;
  email: string;
  opening_time: string;
  closing_time: string;
  emergency_available: boolean;
  lab_available: boolean;
  pharmacy_available: boolean;
  teleconsultation_available: boolean;
  bed_capacity: number;
  services: string;
  specialists: string;
  status: string;
  outgoing_relationships?: FacilityRelationship[];
  incoming_relationships?: FacilityRelationship[];
}

export interface NetworkNode {
  id: string;
  code: string;
  name: string;
  type: FacilityType;
  district: string;
  lat: number;
  lng: number;
  emergency: boolean;
}

export interface NetworkLink {
  id: string;
  source: string;
  target: string;
  type: string;
  priority?: string;
  distance_km?: number;
  color?: string;
}

export interface Patient {
  id: number;
  patient_id: string;
  name: string;
  date_of_birth: string | null;
  age: number;
  gender: 'MALE' | 'FEMALE' | 'OTHER';
  mobile: string;
  address: string;
  ward?: number | null;
  ward_name?: string;
  district?: number | null;
  district_name?: string;
  ABHA_ID_DEMO: string;
  emergency_contact: string;
  vulnerability_information: string;
  registration_date: string;
  registered_at_facility?: number | null;
  facility_name?: string;
}

export interface Token {
  id: number;
  token_number: number;
  priority: 'NORMAL' | 'HIGH' | 'EMERGENCY' | 'SENIOR_CITIZEN';
  status: string;
}

export interface Visit {
  id: number;
  visit_id: string;
  patient: number;
  patient_details?: Patient;
  facility: number;
  facility_name?: string;
  visit_date: string;
  opd_date?: string;
  visit_type: string;
  status: string;
  current_queue?: string;
  chief_complaint: string;
  assigned_doctor?: number | null;
  assigned_doctor_name?: string;
  priority?: string;
  arrival_time?: string;
  waiting_time_minutes?: number;
  status_history_list?: any[];
  token_details?: Token;
}


export interface TriageVitals {
  id: number;
  visit: number;
  patient: number;
  patient_name?: string;
  blood_pressure_systolic: number;
  blood_pressure_diastolic: number;
  pulse_bpm: number;
  temperature_f: number;
  spo2_percent: number;
  respiratory_rate: number;
  height_cm: number;
  weight_kg: number;
  bmi: number;
  blood_glucose_mgdl: number;
  high_bp_flag: boolean;
  high_glucose_flag: boolean;
  fever_flag: boolean;
  low_spo2_flag: boolean;
  pregnancy_high_risk_flag: boolean;
  emergency_flag: boolean;
  ncd_risk_flag: boolean;
  nurse_notes: string;
  created_at: string;
}

export interface PrescriptionItem {
  id?: number;
  medicine_name: string;
  dosage: string;
  frequency: string;
  duration_days: number;
  quantity: number;
  dispensed_quantity?: number;
  remaining_quantity?: number;
  status: 'PENDING' | 'PARTIALLY_DISPENSED' | 'DISPENSED';
}

export interface Prescription {
  id: number;
  consultation: number;
  patient: number;
  patient_name?: string;
  doctor?: number;
  doctor_name?: string;
  facility: number;
  date: string;
  status:
    | 'PENDING_VERIFICATION'
    | 'VERIFIED'
    | 'ON_HOLD'
    | 'REJECTED'
    | 'PARTIALLY_DISPENSED'
    | 'DISPENSED'
    | 'CANCELLED'
    | 'EXPIRED'
    | 'ACTIVE'
    | string;
  verified_by?: number | null;
  verified_by_name?: string | null;
  verified_at?: string | null;
  verification_notes?: string;
  rejection_reason?: string;
  items: PrescriptionItem[];
}

export interface Consultation {
  id: number;
  visit: number;
  patient: number;
  patient_name?: string;
  doctor?: number;
  doctor_name?: string;
  facility: number;
  facility_name?: string;
  chief_complaint: string;
  clinical_history: string;
  clinical_assessment: string;
  diagnosis_code: string;
  diagnosis_name: string;
  treatment_plan: string;
  follow_up_date: string | null;
  clinical_notes: string;
  created_at: string;
  prescription?: Prescription;
}

export interface LabTestMaster {
  id: number;
  code: string;
  name: string;
  category: string;
  reference_range: string;
  unit: string;
}

export interface LabSample {
  id: number;
  sample_type: string;
  sample_code: string;
  collected_at: string;
}

export interface LabResult {
  id: number;
  result_value: string;
  unit: string;
  reference_range: string;
  interpretation_flag: 'NORMAL' | 'HIGH' | 'LOW' | 'CRITICAL';
  verified_by_name?: string;
  verified_at: string;
  notes: string;
}

export interface LabToken {
  id: number;
  token_number: number;
  token_code: string;
  visit: number;
  visit_id_str?: string;
  facility: number;
  facility_name?: string;
  date: string;
  status: 'ORDERED' | 'IN_PROGRESS' | 'COMPLETED';
  created_at: string;
}

export interface LabOrder {
  id: number;
  lab_token?: number | null;
  lab_token_code?: string;
  lab_token_status?: string;
  visit?: number | null;
  consultation?: number | null;
  patient: number;
  patient_name?: string;
  patient_mobile?: string;
  test_master: number;
  test_name?: string;
  test_code?: string;
  facility: number;
  facility_name?: string;
  order_date: string;
  status: 'ORDERED' | 'SAMPLE_COLLECTED' | 'RESULT_ENTRY' | 'VERIFIED';
  sample?: LabSample;
  sample_details?: LabSample;
  result?: LabResult;
}

export interface Vendor {
  id: number;
  vendor_code?: string;
  vendor_name?: string;
  name?: string;
  contact_person: string;
  phone: string;
  email: string;
  address: string;
  gst_number?: string;
  gstin?: string;
  status?: string;
  active?: boolean;
  purchase_orders_count?: number;
  po_count?: number;
  pending_orders?: number;
  completed_orders?: number;
  total_spend?: number;
  created_by_name?: string;
  created_at?: string;
  updated_at?: string;
}

export interface MedicineMaster {
  id: number;
  code: string;
  generic_name: string;
  brand_name: string;
  strength: string;
  dosage_form: string;
  unit: string;
  category: string;
  minimum_stock: number;
  reorder_level: number;
  total_available_stock?: number;
  stock_status?: 'NORMAL' | 'LOW_STOCK' | 'OUT_OF_STOCK';
}

export interface MedicineBatch {
  id: number;
  facility: number;
  facility_name?: string;
  medicine: number;
  medicine_name?: string;
  generic_name?: string;
  medicine_brand?: string;
  medicine_unit?: string;

  batch_number: string;
  vendor?: number | null;
  vendor_name?: string;
  supplier?: string;
  received_date: string;
  mfg_date?: string | null;
  expiry_date: string;
  quantity: number;
  available_quantity?: number;
  quarantined_quantity?: number;
  recalled_quantity?: number;
  damaged_quantity?: number;
  disposed_quantity?: number;
  is_dispensable?: boolean;
  expiry_bucket?: 'EXPIRED' | 'CRITICAL' | 'EXPIRING_SOON' | 'VALID' | string;
  unit_cost: number;
  status:
    | 'AVAILABLE'
    | 'QUARANTINED'
    | 'RECALLED'
    | 'DAMAGED'
    | 'DISPOSED'
    | 'EXHAUSTED'
    | 'ACTIVE'
    | 'EXPIRING_SOON'
    | 'EXPIRED'
    | 'LOW_STOCK'
    | 'NEAR_EXPIRY'
    | string;
  is_expired?: boolean;
  days_to_expiry?: number;
}

export interface DispensationReturn {
  id: number;
  facility: number;
  return_number: string;
  prescription_item: number;
  batch: number;
  returned_quantity: number;
  return_reason: string;
  patient_reported_issue?: string;
  status: 'PENDING_ASSESSMENT' | 'APPROVED_FOR_STOCK' | 'QUARANTINE' | 'DISPOSAL';
  assessment_notes?: string;
  initiated_by: number;
  assessed_by?: number;
  created_at: string;
  assessed_at?: string;
}

export interface BatchRecall {
  id: number;
  facility: number;
  recall_number: string;
  batch: number;
  batch_number?: string;
  recalled_quantity: number;
  recall_reason: string;
  regulatory_reference?: string;
  recall_class?: 'CLASS_I' | 'CLASS_II' | 'CLASS_III' | 'VOLUNTARY' | string;
  initiated_by: number;
  is_active: boolean;
  notes?: string;
  created_at: string;
}

export interface ColdChainLog {
  id: number;
  facility: number;
  equipment_identifier: string;
  recorded_temperature_celsius: number;
  min_acceptable_celsius?: number | null;
  max_acceptable_celsius?: number | null;
  reading_timestamp: string;
  status: 'IN_RANGE' | 'OUT_OF_RANGE' | 'UNCONFIGURED_RANGE';
  excursion_action_taken?: string;
  recorded_by: number;
  recorded_by_name?: string;
  notes?: string;
  created_at: string;
}

export interface PatientCounselling {
  id: number;
  facility: number;
  prescription: number;
  patient: number;
  dosage_instructions_given?: boolean | null;
  side_effects_explained?: boolean | null;
  storage_conditions_explained?: boolean | null;
  dietary_precautions_explained?: boolean | null;
  special_warnings_given?: boolean | null;
  patient_comprehension_confirmed?: boolean | null;
  counselled_by: number;
  counselled_at: string;
  notes?: string;
}

export interface GoodsReceiptNote {
  id: number;
  facility: number;
  grn_number: string;
  purchase_order: number;
  received_date: string;
  invoice_number?: string;
  received_by: number;
  status: 'DRAFT' | 'VERIFIED' | 'CANCELLED';
  notes?: string;
  created_at: string;
  items?: Array<{
    id?: number;
    medicine: number;
    medicine_name?: string;
    batch_number: string;
    expiry_date: string;
    received_quantity: number;
    accepted_quantity: number;
    rejected_quantity: number;
    rejection_reason?: string;
  }>;
}

export interface PurchaseOrderItem {
  id?: number;
  medicine: number;
  medicine_name?: string;
  medicine_brand?: string;
  medicine_strength?: string;
  medicine_unit?: string;
  ordered_quantity?: number;
  requested_quantity?: number;
  received_quantity: number;
  remaining_quantity?: number;
  unit_price?: number;
  unit_cost?: number;
  total_price?: number;
}

export interface PurchaseOrder {
  id: number;
  po_number: string;
  facility: number;
  facility_name?: string;
  vendor: number;
  vendor_name?: string;
  vendor_code?: string;
  order_date: string;
  expected_delivery: string | null;
  expected_delivery_date?: string | null;
  status: 'DRAFT' | 'PENDING_APPROVAL' | 'PENDING' | 'APPROVED' | 'ORDERED' | 'PARTIALLY_RECEIVED' | 'RECEIVED' | 'CANCELLED';
  total_amount: number;
  notes: string;
  created_by?: number | null;
  created_by_name?: string;
  approved_by?: number | null;
  approved_by_name?: string;
  approved_at?: string | null;
  rejected_by?: number | null;
  rejected_by_name?: string;
  rejected_at?: string | null;
  rejection_reason?: string;
  created_at: string;
  updated_at?: string;
  items: PurchaseOrderItem[];
}

export interface ProcurementSummaryKPIs {
  draft: number;
  pending_approval: number;
  approved: number;
  ordered: number;
  partially_received: number;
  received: number;
  cancelled: number;
  total_orders: number;
  total_spend: number;
}

export interface InventoryTransaction {
  id: number;
  facility: number;
  facility_name?: string;
  batch: number;
  batch_number?: string;
  medicine_name?: string;
  transaction_type: 'PURCHASE_RECEIVED' | 'DISPENSED' | 'RETURNED' | 'ADJUSTMENT' | 'DAMAGED' | 'EXPIRED' | 'ISSUED' | 'TRANSFERRED';
  quantity: number;
  reference_id: string;
  notes: string;
  created_by?: number | null;
  created_by_name?: string;
  timestamp: string;
}

export interface PharmacyDashboardKPIs {
  total_medicines: number;
  total_available_stock: number;
  low_stock_count: number;
  out_of_stock_count: number;
  expiring_soon_count: number;
  expired_count: number;
  pending_prescriptions_count: number;
  dispensed_today_count: number;
  pending_purchase_orders_count: number;
  total_vendors_count: number;
}

export interface PharmacyAlert {
  id: string;
  type: 'LOW_STOCK' | 'OUT_OF_STOCK' | 'EXPIRING_SOON' | 'EXPIRED' | 'PENDING_PO';
  title: string;
  description: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  medicine_id?: number;
  batch_id?: number;
  po_id?: number;
}

export interface PharmacyReportSummary {
  dispensing_summary: {
    dispensed_today: number;
    prescriptions_count: number;
  };
  stock_valuation: {
    total_batches: number;
    total_quantity: number;
    total_value: number;
  };
  consumption_summary: Array<{
    batch__medicine__generic_name: string;
    batch__medicine__brand_name: string;
    total_consumed: number;
  }>;
}

export interface ReferralResponse {
  id: number;
  doctor_name?: string;
  specialist_findings: string;
  treatment_summary: string;
  return_advice: string;
  responded_at: string;
}

export interface Referral {
  id: number;
  referral_id: string;
  patient: number;
  patient_name?: string;
  patient_mobile?: string;
  source_facility: number;
  source_facility_name?: string;
  destination_facility: number;
  destination_facility_name?: string;
  referring_doctor_name?: string;
  reason: string;
  clinical_summary: string;
  required_service: string;
  urgency: 'ROUTINE' | 'URGENT' | 'EMERGENCY';
  referral_date: string;
  status: 'CREATED' | 'ACCEPTED' | 'IN_TRANSIT' | 'REACHED' | 'UNDER_TREATMENT' | 'FOLLOW_UP_PENDING' | 'COMPLETED' | 'CLOSED';
  response?: ReferralResponse;
}

export interface FollowUp {
  id: number;
  patient: number;
  patient_name?: string;
  facility: number;
  facility_name?: string;
  category: string;
  due_date: string;
  status: 'PENDING' | 'DUE_TODAY' | 'OVERDUE' | 'COMPLETED';
  notes: string;
}

export interface NCDRecord {
  id: number;
  patient: number;
  patient_name?: string;
  patient_mobile?: string;
  facility: number;
  facility_name?: string;
  screening_date: string;
  hypertension_diagnosed: boolean;
  diabetes_diagnosed: boolean;
  risk_level: string;
  control_status: string;
  last_bp: string;
  last_glucose: number;
  next_followup_due: string | null;
}

export interface DiseaseCase {
  id: number;
  disease_name: string;
  patient: number;
  patient_name?: string;
  facility: number;
  facility_name?: string;
  ward?: number | null;
  ward_name?: string;
  report_date: string;
  severity: string;
  status: string;
}

export interface OutreachActivity {
  id: number;
  facility: number;
  facility_name?: string;
  ward?: number | null;
  activity_type: string;
  activity_date: string;
  households_covered: number;
  persons_screened: number;
  vulnerable_identified: number;
  conducted_by: string;
  summary_notes: string;
}

export interface Alert {
  id: number;
  alert_type: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  facility: number;
  facility_name?: string;
  patient?: number | null;
  title: string;
  description: string;
  status: 'NEW' | 'ACKNOWLEDGED' | 'RESOLVED';
  created_at: string;
}

export interface IntegrationConfiguration {
  id: number;
  system_name: string;
  display_name: string;
  status: string;
  last_sync_time?: string | null;
  sync_status: string;
  notes: string;
}

export interface ComplianceItem {
  id: number;
  requirement_id: string;
  requirement_text: string;
  source_document: string;
  classification: string;
  application_module: string;
  status: 'FULLY_COVERED' | 'PARTIALLY_COVERED' | 'NOT_IMPLEMENTED' | 'OUT_OF_DIGITAL_SCOPE';
  explanation: string;
}

export interface AuditLog {
  id: number;
  username_snapshot: string;
  action: string;
  facility_name?: string;
  details: string;
  timestamp: string;
}

export interface PatientDocument {
  id: number;
  patient: number;
  patient_name?: string;
  patient_uhid?: string;
  document_type: 'MEDICAL_RECORD' | 'LAB_REPORT' | 'PRESCRIPTION' | 'DISCHARGE_SUMMARY' | 'REFERRAL_DOC' | 'OTHER';
  document_type_display?: string;
  title: string;
  description: string;
  file: string;
  file_url?: string;
  file_name: string;
  file_size: number;
  file_size_formatted?: string;
  mime_type: string;
  uploaded_at: string;
  uploaded_by?: number | null;
  uploaded_by_name?: string;
  facility?: number | null;
  facility_name?: string;
}

export interface PatientRecordsSummary {
  patient: Patient;
  total_visits: number;
  total_consultations: number;
  total_lab_reports: number;
  total_prescriptions: number;
  total_documents: number;
  recent_visits: Visit[];
  recent_consultations: Consultation[];
  recent_lab_reports: LabOrder[];
  recent_prescriptions: Prescription[];
  documents: PatientDocument[];
}

