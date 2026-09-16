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
  priority: 'NORMAL' | 'EMERGENCY' | 'MATERNAL' | 'SENIOR_CITIZEN';
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
  visit_type: string;
  status: 'WAITING' | 'TRIAGED' | 'IN_CONSULTATION' | 'COMPLETED' | 'CANCELLED';
  chief_complaint: string;
  assigned_doctor?: number | null;
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
  status: 'PENDING' | 'DISPENSED';
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
  status: string;
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

export interface LabOrder {
  id: number;
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
  result?: LabResult;
}

export interface MedicineMaster {
  id: number;
  generic_name: string;
  brand_name: string;
  strength: string;
  dosage_form: string;
  unit: string;
  category: string;
  reorder_level: number;
}

export interface MedicineBatch {
  id: number;
  facility: number;
  facility_name?: string;
  medicine: number;
  medicine_name?: string;
  batch_number: string;
  supplier: string;
  received_date: string;
  expiry_date: string;
  quantity: number;
  unit_cost: number;
  status: 'ACTIVE' | 'LOW_STOCK' | 'NEAR_EXPIRY' | 'EXPIRED';
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
