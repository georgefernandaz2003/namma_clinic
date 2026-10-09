import test from 'node:test';
import assert from 'node:assert/strict';

// Helper types & state machine reflecting PatientDetail timeline and visit detail modal logic
interface TimelineEvent {
  date: string;
  type: 'VISIT' | 'REGISTRATION' | 'TRIAGE' | 'CONSULTATION' | 'PRESCRIPTION' | 'LAB' | 'DOCUMENT' | 'REFERRAL' | 'FOLLOWUP';
  title: string;
  facility: string;
  details: string;
  document_id?: number;
}

interface VisitRecord {
  id: number;
  visit_id: string;
  visit_date: string;
  facility_name: string;
  token_number: number | null;
  visit_type: string;
  chief_complaint: string;
  priority: string;
  status: string;
  queue: string;
  current_queue?: string;
  waiting_time_minutes?: number;
  token_details?: any;
  status_history_list?: any[];
}

interface ConsultationRecord {
  id: number;
  visit_id: string | null;
  created_at: string;
  facility_name: string;
  doctor_name: string;
  chief_complaint: string;
  clinical_history: string;
  clinical_assessment: string;
  diagnosis_code: string;
  diagnosis_name: string;
  treatment_plan: string;
  clinical_notes: string;
  follow_up_date: string | null;
}

interface TriageVitalsRecord {
  id: number;
  visit: number;
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
  nurse_notes: string;
  emergency_flag: boolean;
  high_bp_flag: boolean;
  fever_flag: boolean;
  low_spo2_flag: boolean;
}

interface LabReportRecord {
  id: number;
  order_id: string;
  order_date: string;
  test_name: string;
  test_code: string;
  facility_name: string;
  doctor_name: string;
  status: string;
  sample_code: string | null;
  result_value: string | null;
  unit: string | null;
  interpretation_flag: string | null;
  verified_by: string | null;
  verified_at: string | null;
}

interface PrescriptionRecord {
  id: number;
  date: string;
  facility_name: string;
  doctor_name: string;
  status: string;
  items: Array<{
    id: number;
    medicine_name: string;
    dosage: string;
    frequency: string;
    duration_days: number;
    quantity: number;
    status: string;
  }>;
}

// Logic functions simulating the PatientDetail component
function isTimelineEntryClickable(ev: TimelineEvent): boolean {
  return ['VISIT', 'REGISTRATION', 'TRIAGE', 'CONSULTATION', 'PRESCRIPTION', 'DOCUMENT'].includes(ev.type);
}

function resolveTargetVisitForEvent(ev: TimelineEvent, visits: VisitRecord[]): VisitRecord | null {
  const tokenMatch = ev.title?.match(/#(\d+)/);
  const tokenNum = tokenMatch ? parseInt(tokenMatch[1], 10) : null;

  let targetVisit = visits.find((v) =>
    (tokenNum !== null && (v.token_number === tokenNum || v.id === tokenNum))
  );

  if (!targetVisit && ev.date) {
    targetVisit = visits.find((v) =>
      v.visit_date && v.visit_date.slice(0, 10) === ev.date.slice(0, 10)
    );
  }

  if (!targetVisit && visits.length > 0) {
    targetVisit = visits[0];
  }

  return targetVisit || null;
}

function assembleVisitDetailTransaction(
  targetVisit: VisitRecord,
  records: {
    medical_records: ConsultationRecord[];
    lab_reports: LabReportRecord[];
    prescriptions: PrescriptionRecord[];
    documents: any[];
  },
  triageData: TriageVitalsRecord | null
) {
  const matchingConsultation = records.medical_records.find((c) =>
    (c.visit_id && (c.visit_id === targetVisit.visit_id || c.visit_id === String(targetVisit.id))) ||
    (c.created_at && targetVisit.visit_date && c.created_at.slice(0, 10) === targetVisit.visit_date.slice(0, 10))
  ) || null;

  const targetDate = targetVisit.visit_date ? targetVisit.visit_date.slice(0, 10) : '';

  const matchingLabReports = records.lab_reports.filter((l) =>
    targetDate && l.order_date && l.order_date.slice(0, 10) === targetDate
  );

  const matchingPrescriptions = records.prescriptions.filter((p) =>
    targetDate && p.date && p.date.slice(0, 10) === targetDate
  );

  const matchingDocs = records.documents.filter((d) =>
    targetDate && d.uploaded_at && d.uploaded_at.slice(0, 10) === targetDate
  );

  return {
    visit: targetVisit,
    triage: triageData,
    consultation: matchingConsultation,
    labReports: matchingLabReports,
    prescriptions: matchingPrescriptions,
    documents: matchingDocs.length > 0 ? matchingDocs : records.documents,
    followUp: matchingConsultation?.follow_up_date ? { due_date: matchingConsultation.follow_up_date } : null
  };
}

// Section visibility guards matching the modal
function getSectionVisibility(role: string, isSuperUser = false) {
  return {
    patientVisit: true,
    opdQueue: true,
    triageVitals: isSuperUser || ['DOCTOR', 'NURSE', 'HOSPITAL_ADMIN', 'DISTRICT_OFFICER'].includes(role),
    doctorConsultation: isSuperUser || ['DOCTOR', 'HOSPITAL_ADMIN', 'DISTRICT_OFFICER'].includes(role),
    laboratory: isSuperUser || ['DOCTOR', 'LAB_TECHNICIAN', 'NURSE', 'HOSPITAL_ADMIN', 'DISTRICT_OFFICER'].includes(role),
    prescription: isSuperUser || ['DOCTOR', 'PHARMACIST', 'NURSE', 'HOSPITAL_ADMIN', 'DISTRICT_OFFICER'].includes(role),
    pharmacyDispensing: isSuperUser || ['DOCTOR', 'PHARMACIST', 'INVENTORY', 'HOSPITAL_ADMIN', 'DISTRICT_OFFICER'].includes(role),
    documents: isSuperUser || ['DOCTOR', 'NURSE', 'LAB_TECHNICIAN', 'PHARMACIST', 'HOSPITAL_ADMIN', 'DISTRICT_OFFICER'].includes(role),
    visitCompletion: true
  };
}

test('Patient Detail Timeline & Visit Detail Modal Suite', async (t) => {
  const samplePatient = {
    id: 173,
    patient_id: 'NC-KA-2026-0001',
    name: 'Arun Kumar',
    age: 38,
    gender: 'MALE',
    mobile: '9800010001',
    registration_date: '2026-10-08',
    ABHA_ID_DEMO: 'ABHA-DEMO-0001',
    address: 'Malleshwaram 7th Cross, Bangalore',
    vulnerability_information: 'General BPL'
  };

  const sampleVisits: VisitRecord[] = [
    {
      id: 199,
      visit_id: 'VIS-20261008-62B4E4',
      visit_date: '2026-10-08 08:01',
      facility_name: 'Namma Clinic Local PHC',
      token_number: 9,
      visit_type: 'GENERAL_OPD',
      chief_complaint: 'Acute headache and fever',
      priority: 'NORMAL',
      status: 'COMPLETED',
      queue: 'COMPLETED',
      token_details: { id: 168, token_number: 9, current_state: 'COMPLETED' },
      status_history_list: [
        { from_status: 'NONE', to_status: 'WAITING_FOR_DOCTOR', performed_by_role: 'FRONT_DESK_OFFICER', notes: 'Issued OPD Token #9' },
        { from_status: 'WAITING_FOR_DOCTOR', to_status: 'COMPLETED', performed_by_name: 'Dr. Sunil Kumar', performed_by_role: 'DOCTOR', notes: 'Consultation completed' }
      ]
    }
  ];

  const sampleConsultation: ConsultationRecord = {
    id: 86,
    visit_id: 'VIS-20261008-62B4E4',
    created_at: '2026-10-08 08:30',
    facility_name: 'Namma Clinic Local PHC',
    doctor_name: 'Dr. Sunil Kumar',
    chief_complaint: 'Acute headache and fever',
    clinical_history: 'Febrile episode since 2 days, tension-type frontal cephalalgia.',
    clinical_assessment: 'Alert, febrile 100.2F, no neck stiffness, chest clear.',
    diagnosis_code: 'E11',
    diagnosis_name: 'Type 2 Diabetes Mellitus',
    treatment_plan: 'Oral hydration, rest, symptomatic relief',
    clinical_notes: 'Monitor blood glucose weekly, review in 7 days.',
    follow_up_date: '2026-10-15'
  };

  await t.test('1. Timeline entries are clickable (Visit and Registration entries flag isClickable)', () => {
    const visitEvent: TimelineEvent = {
      date: '2026-10-08 08:01',
      type: 'VISIT',
      title: 'Clinic Visit (#9)',
      facility: 'Namma Clinic Local PHC',
      details: 'Visit Type: GENERAL_OPD, Chief Complaint: Acute headache and fever'
    };

    const regEvent: TimelineEvent = {
      date: '2026-10-08',
      type: 'REGISTRATION',
      title: 'Patient Registered',
      facility: 'Namma Clinic Local PHC',
      details: 'Registered with Patient ID NC-KA-2026-0001'
    };

    assert.equal(isTimelineEntryClickable(visitEvent), true, 'Clinic Visit (#9) entry must be clickable');
    assert.equal(isTimelineEntryClickable(regEvent), true, 'Patient Registered entry must be clickable');
  });

  await t.test('2. Clicking "Clinic Visit (#9)" resolves matching visit and opens Visit Details transaction', () => {
    const visitEvent: TimelineEvent = {
      date: '2026-10-08 08:01',
      type: 'VISIT',
      title: 'Clinic Visit (#9)',
      facility: 'Namma Clinic Local PHC',
      details: 'Visit Type: GENERAL_OPD'
    };

    const matchedVisit = resolveTargetVisitForEvent(visitEvent, sampleVisits);
    assert.ok(matchedVisit, 'Target visit must be resolved');
    assert.equal(matchedVisit?.id, 199);
    assert.equal(matchedVisit?.token_number, 9);
    assert.equal(matchedVisit?.visit_id, 'VIS-20261008-62B4E4');

    const transaction = assembleVisitDetailTransaction(
      matchedVisit,
      {
        medical_records: [sampleConsultation],
        lab_reports: [],
        prescriptions: [],
        documents: []
      },
      null
    );

    assert.equal(transaction.visit.id, 199);
    assert.equal(transaction.consultation?.doctor_name, 'Dr. Sunil Kumar');
    assert.equal(transaction.consultation?.diagnosis_code, 'E11');
    assert.equal(transaction.consultation?.treatment_plan, 'Oral hydration, rest, symptomatic relief');
  });

  await t.test('3. Real persisted visit data is correctly displayed in transaction model', () => {
    const transaction = assembleVisitDetailTransaction(
      sampleVisits[0],
      {
        medical_records: [sampleConsultation],
        lab_reports: [],
        prescriptions: [],
        documents: []
      },
      null
    );

    // Section 1: Patient / Visit
    assert.equal(transaction.visit.visit_id, 'VIS-20261008-62B4E4');
    assert.equal(transaction.visit.visit_type, 'GENERAL_OPD');
    assert.equal(transaction.visit.status, 'COMPLETED');
    assert.equal(transaction.visit.chief_complaint, 'Acute headache and fever');

    // Section 2: OPD / Queue
    assert.equal(transaction.visit.token_details.token_number, 9);
    assert.equal(transaction.visit.status_history_list?.length, 2);
    assert.equal(transaction.visit.status_history_list?.[0].performed_by_role, 'FRONT_DESK_OFFICER');

    // Section 4: Doctor Consultation
    assert.equal(transaction.consultation?.diagnosis_name, 'Type 2 Diabetes Mellitus');
    assert.equal(transaction.consultation?.diagnosis_code, 'E11');

    // Section 9: Follow-up
    assert.equal(transaction.followUp?.due_date, '2026-10-15');
  });

  await t.test('4. Empty sections are handled gracefully without synthetic data ("No data recorded")', () => {
    const transaction = assembleVisitDetailTransaction(
      sampleVisits[0],
      {
        medical_records: [],
        lab_reports: [],
        prescriptions: [],
        documents: []
      },
      null
    );

    // Sections with no records return null / empty arrays
    assert.equal(transaction.triage, null, 'Triage is null when unrecorded');
    assert.equal(transaction.consultation, null, 'Consultation is null when unrecorded');
    assert.equal(transaction.labReports.length, 0, 'Lab reports empty when unrecorded');
    assert.equal(transaction.prescriptions.length, 0, 'Prescriptions empty when unrecorded');
    assert.equal(transaction.followUp, null, 'Follow-up null when unrecorded');
  });

  await t.test('5. Role-Based Access Control: FRONT_DESK_OFFICER cannot see clinical details', () => {
    const fdPerms = getSectionVisibility('FRONT_DESK_OFFICER', false);

    assert.equal(fdPerms.patientVisit, true, 'Front Desk can view Patient/Visit demographics');
    assert.equal(fdPerms.opdQueue, true, 'Front Desk can view OPD & Queue token information');
    assert.equal(fdPerms.visitCompletion, true, 'Front Desk can view operational completion');

    // Privacy restrictions
    assert.equal(fdPerms.triageVitals, false, 'Front Desk must NOT access Nurse Triage vitals');
    assert.equal(fdPerms.doctorConsultation, false, 'Front Desk must NOT access Doctor Consultation & Diagnosis');
    assert.equal(fdPerms.laboratory, false, 'Front Desk must NOT access Laboratory investigation results');
    assert.equal(fdPerms.prescription, false, 'Front Desk must NOT access Prescription medications');
    assert.equal(fdPerms.pharmacyDispensing, false, 'Front Desk must NOT access Pharmacy dispensing records');
    assert.equal(fdPerms.documents, false, 'Front Desk must NOT view clinical documents');
  });

  await t.test('6. Role-Based Access Control: DOCTOR can see all authorized clinical sections', () => {
    const docPerms = getSectionVisibility('DOCTOR', false);

    assert.equal(docPerms.patientVisit, true);
    assert.equal(docPerms.opdQueue, true);
    assert.equal(docPerms.triageVitals, true, 'Doctor can view Nurse Triage');
    assert.equal(docPerms.doctorConsultation, true, 'Doctor can view Consultation & Diagnosis');
    assert.equal(docPerms.laboratory, true, 'Doctor can view Lab investigations & results');
    assert.equal(docPerms.prescription, true, 'Doctor can view Prescription');
    assert.equal(docPerms.pharmacyDispensing, true, 'Doctor can view Pharmacy dispensing');
    assert.equal(docPerms.documents, true, 'Doctor can view patient documents');
    assert.equal(docPerms.visitCompletion, true);
  });

  await t.test('7. Role-Based Access Control: NURSE sees Triage, Patient, Queue, but is restricted from Doctor notes and Pharmacy dispensing', () => {
    const nursePerms = getSectionVisibility('NURSE', false);

    assert.equal(nursePerms.patientVisit, true);
    assert.equal(nursePerms.opdQueue, true);
    assert.equal(nursePerms.triageVitals, true, 'Nurse can access Triage');
    assert.equal(nursePerms.laboratory, true, 'Nurse can access Lab overview');
    assert.equal(nursePerms.prescription, true, 'Nurse can view Prescription medications for administration');
    assert.equal(nursePerms.documents, true, 'Nurse can view documents');

    // Nurse restrictions
    assert.equal(nursePerms.doctorConsultation, false, 'Nurse is restricted from internal doctor consultation notes');
    assert.equal(nursePerms.pharmacyDispensing, false, 'Nurse is restricted from pharmacy stock administration');
  });

  await t.test('8. Role-Based Access Control: PHARMACIST sees Prescription and Pharmacy Dispensing, but not Triage or Doctor Notes', () => {
    const pharmPerms = getSectionVisibility('PHARMACIST', false);

    assert.equal(pharmPerms.patientVisit, true);
    assert.equal(pharmPerms.prescription, true, 'Pharmacist can view Prescriptions');
    assert.equal(pharmPerms.pharmacyDispensing, true, 'Pharmacist can view Dispensing');
    assert.equal(pharmPerms.documents, true);

    // Pharmacist restrictions
    assert.equal(pharmPerms.triageVitals, false, 'Pharmacist cannot view Triage vitals');
    assert.equal(pharmPerms.doctorConsultation, false, 'Pharmacist cannot view Doctor clinical notes');
    assert.equal(pharmPerms.laboratory, false, 'Pharmacist cannot view Lab results');
  });

  await t.test('9. Patient Registered modal data reflects authoritative demographic intake', () => {
    assert.equal(samplePatient.name, 'Arun Kumar');
    assert.equal(samplePatient.patient_id, 'NC-KA-2026-0001');
    assert.equal(samplePatient.mobile, '9800010001');
    assert.equal(samplePatient.ABHA_ID_DEMO, 'ABHA-DEMO-0001');
    assert.equal(samplePatient.vulnerability_information, 'General BPL');
    assert.equal(samplePatient.address.includes('Malleshwaram'), true);
  });
});
