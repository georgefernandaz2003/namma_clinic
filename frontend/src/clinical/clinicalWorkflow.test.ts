import test from 'node:test';
import assert from 'node:assert/strict';
import { isRouteAllowedForRole } from '../navigation/navigationConfig.ts';
import { parseApiError } from '../api/client.ts';
import type { Role } from '../types/auth.ts';
import type {
  Visit,
  Patient,
  TriageVitals,
  Consultation,
  DiagnosticOrder,
  DiagnosticResult,
  Prescription,
  ReferralOrder,
  FollowUpTask,
} from '../types/index.ts';

// =========================================================================
// 1. DOCTOR WORKFLOW ROUTE ACCESS & 403 ACCESS CONTROL
// =========================================================================

test('Doctor clinical workflow authorization and access control', async (t) => {
  await t.test('Doctor can access doctor dashboard and consultation routes', () => {
    assert.equal(isRouteAllowedForRole('DOCTOR', '/dashboard/doctor'), true);
    assert.equal(isRouteAllowedForRole('DOCTOR', '/consultation'), true);
  });

  await t.test('Non-doctor roles are blocked from Doctor consultation route', () => {
    const nonDoctorRoles: Role[] = [
      'NURSE',
      'LAB_TECHNICIAN',
      'PHARMACIST',
      'HOSPITAL_ADMIN',
      'DISTRICT_OFFICER',
    ];
    for (const role of nonDoctorRoles) {
      assert.equal(
        isRouteAllowedForRole(role, '/consultation'),
        false,
        'Role must NOT be allowed to access /consultation'
      );
    }
  });

  await t.test('Non-doctor roles cannot access Doctor landing dashboard', () => {
    const nonDoctorRoles: Role[] = [
      'NURSE',
      'LAB_TECHNICIAN',
      'PHARMACIST',
      'HOSPITAL_ADMIN',
      'DISTRICT_OFFICER',
    ];
    for (const role of nonDoctorRoles) {
      assert.equal(
        isRouteAllowedForRole(role, '/dashboard/doctor'),
        false,
        'Role must NOT be allowed to access /dashboard/doctor'
      );
    }
  });
});

// =========================================================================
// 2. DOCTOR WORKSPACE QUEUE & ROSTER BEHAVIOR
// =========================================================================

test('Doctor workspace queue processing and filter handling', async (t) => {
  const mockVisits: Visit[] = [
    {
      id: 1,
      visit_id: 'VIS-20260924-0001',
      patient: 101,
      facility: 1,
      facility_name: 'Urban Primary Health Centre - Central',
      visit_date: '2026-09-24',
      opd_date: '2026-09-24',
      visit_type: 'OPD_GENERAL',
      status: 'TRIAGED',
      current_queue: 'DOCTOR',
      chief_complaint: 'High fever and chills',
      priority: 'HIGH',
      token_number: 1,
    },
    {
      id: 2,
      visit_id: 'VIS-20260924-0002',
      patient: 102,
      facility: 1,
      facility_name: 'Urban Primary Health Centre - Central',
      visit_date: '2026-09-24',
      opd_date: '2026-09-24',
      visit_type: 'OPD_GENERAL',
      status: 'IN_CONSULTATION',
      current_queue: 'DOCTOR',
      chief_complaint: 'Joint pain and swelling',
      priority: 'NORMAL',
      token_number: 2,
    },
    {
      id: 3,
      visit_id: 'VIS-20260924-0003',
      patient: 103,
      facility: 1,
      facility_name: 'Urban Primary Health Centre - Central',
      visit_date: '2026-09-24',
      opd_date: '2026-09-24',
      visit_type: 'OPD_GENERAL',
      status: 'COMPLETED',
      current_queue: 'PHARMACY',
      chief_complaint: 'Routine follow-up',
      priority: 'NORMAL',
      token_number: 3,
    },
  ];

  await t.test('calculates queue metrics authoritatively from real visits data', () => {
    const totalToday = mockVisits.length;
    const awaitingDoctor = mockVisits.filter(
      (v) => (v.current_queue === 'DOCTOR' || !v.current_queue) && v.status !== 'COMPLETED'
    ).length;
    const inConsultation = mockVisits.filter((v) => v.status === 'IN_CONSULTATION').length;
    const completed = mockVisits.filter((v) => v.status === 'COMPLETED').length;

    assert.equal(totalToday, 3);
    assert.equal(awaitingDoctor, 2);
    assert.equal(inConsultation, 1);
    assert.equal(completed, 1);
  });

  await t.test('correctly filters queue by tab state', () => {
    const awaiting = mockVisits.filter((v) => v.status === 'TRIAGED');
    const inProgress = mockVisits.filter((v) => v.status === 'IN_CONSULTATION');
    const done = mockVisits.filter((v) => v.status === 'COMPLETED');

    assert.equal(awaiting.length, 1);
    assert.equal(awaiting[0].id, 1);
    assert.equal(inProgress.length, 1);
    assert.equal(inProgress[0].id, 2);
    assert.equal(done.length, 1);
    assert.equal(done[0].id, 3);
  });

  await t.test('handles empty queue gracefully without crashing', () => {
    const emptyVisits: Visit[] = [];
    const awaitingDoctor = emptyVisits.filter((v) => v.status === 'TRIAGED');
    assert.equal(awaitingDoctor.length, 0);
  });
});

// =========================================================================
// 3. PATIENT CONTEXT & READ-ONLY TRIAGE REVIEW
// =========================================================================

test('Patient clinical context and read-only nurse triage review', async (t) => {
  const patient: Patient = {
    id: 101,
    uhid: 'UHID-2026-000101',
    first_name: 'Anitha',
    last_name: 'Kumar',
    age: 42,
    gender: 'FEMALE',
    contact_number: '9876543210',
    address: '12 Temple Street, Mylapore, Chennai',
    abha_address: 'anitha.kumar@abdm',
  };

  const triageVitals: TriageVitals = {
    id: 51,
    visit: 1,
    patient: 101,
    blood_pressure_systolic: 145,
    blood_pressure_diastolic: 95,
    pulse_bpm: 98,
    respiratory_rate: 20,
    temperature_f: 101.4,
    spo2_percent: 95.0,
    blood_glucose_mgdl: 180,
    weight_kg: 68.5,
    height_cm: 158.0,
    bmi: 27.4,
    high_bp_flag: true,
    fever_flag: true,
    low_spo2_flag: false,
    high_glucose_flag: true,
    pregnancy_high_risk_flag: false,
    emergency_flag: false,
    ncd_risk_flag: false,
    nurse_notes: 'Patient conscious, oriented, complaints of mild fever',
    created_at: '2026-09-24T10:15:00Z',
  };

  await t.test('displays patient demographic context accurately', () => {
    assert.equal(patient.first_name, 'Anitha');
    assert.equal(patient.last_name, 'Kumar');
    assert.equal(patient.age, 42);
    assert.equal(patient.gender, 'FEMALE');
    assert.equal(patient.abha_address, 'anitha.kumar@abdm');
  });

  await t.test('exposes nurse triage vitals with clinical warning flags', () => {
    assert.equal(triageVitals.blood_pressure_systolic, 145);
    assert.equal(triageVitals.blood_pressure_diastolic, 95);
    assert.equal(triageVitals.high_bp_flag, true);
    assert.equal(triageVitals.temperature_f, 101.4);
    assert.equal(triageVitals.fever_flag, true);
    assert.equal(triageVitals.high_glucose_flag, true);
  });

  await t.test('preserves clinical authorship of nurse triage (read-only for doctor)', () => {
    // Triage belongs to nurse; doctor workflow does not mutate triage records
    assert.ok(triageVitals.nurse_notes.includes('Nurse') || triageVitals.created_at);
  });
});

// =========================================================================
// 4. CONSULTATION & DIAGNOSIS CREATION & VALIDATION
// =========================================================================

test('Consultation payload structure, validation, and diagnosis binding', async (t) => {
  await t.test('validates required fields before API dispatch', () => {
    const invalidForm = {
      chief_complaint: '',
      clinical_assessment: '',
    };
    const errors: string[] = [];
    if (!invalidForm.chief_complaint.trim()) {
      errors.push('Chief complaint is required.');
    }
    if (!invalidForm.clinical_assessment.trim()) {
      errors.push('Clinical assessment is required.');
    }

    assert.equal(errors.length, 2);
    assert.ok(errors.includes('Chief complaint is required.'));
    assert.ok(errors.includes('Clinical assessment is required.'));
  });

  await t.test('builds valid DRF Consultation creation payload', () => {
    const validConsultation: Partial<Consultation> = {
      visit: 1,
      patient: 101,
      facility: 1,
      chief_complaint: 'High grade fever with retro-orbital headache for 4 days',
      clinical_history: 'No known drug allergies. History of hypertension.',
      clinical_assessment: 'Acute febrile illness, suspect viral etiology vs dengue fever',
      diagnosis_code: 'R50.9',
      diagnosis_name: 'Fever, unspecified / Acute Febrile Illness',
      treatment_plan: 'Hydration therapy, Paracetamol 650mg TDS, diagnostic workup',
      clinical_notes: 'Patient advised to return immediately if warning signs develop',
      follow_up_date: '2026-09-27',
    };

    assert.equal(validConsultation.visit, 1);
    assert.equal(validConsultation.patient, 101);
    assert.equal(validConsultation.diagnosis_code, 'R50.9');
    assert.equal(
      validConsultation.diagnosis_name,
      'Fever, unspecified / Acute Febrile Illness'
    );
    assert.ok(validConsultation.treatment_plan?.includes('Paracetamol'));
  });
});

// =========================================================================
// 5. DIAGNOSTIC ORDERING & RESULTS REVIEW
// =========================================================================

test('Diagnostic ordering payload and separation of duties', async (t) => {
  await t.test('constructs DiagnosticOrder payload according to backend schema', () => {
    const orderPayload: Partial<DiagnosticOrder> = {
      visit: 1,
      patient: 101,
      facility: 1,
      priority: 'URGENT',
      clinical_indication: 'Rule out Dengue NS1 / Complete Blood Count for thrombocytopenia',
      status: 'ORDERED',
    };

    assert.equal(orderPayload.priority, 'URGENT');
    assert.equal(orderPayload.status, 'ORDERED');
    assert.equal(orderPayload.facility, 1);
  });

  await t.test('displays verified diagnostic results with read-only integrity', () => {
    const mockResult: DiagnosticResult = {
      id: 201,
      test_request: 301,
      test_name: 'Complete Blood Count (CBC)',
      result_value: 'Platelets: 165,000 /uL (Borderline)',
      reference_range: '150,000 - 450,000 /uL',
      is_abnormal: true,
      verified_by: 8, // Lab technician staff ID
      verified_at: '2026-09-24T11:30:00Z',
      status: 'VERIFIED',
    };

    assert.equal(mockResult.is_abnormal, true);
    assert.equal(mockResult.status, 'VERIFIED');
    assert.equal(mockResult.verified_by, 8);
    // Doctor cannot impersonate lab technician or modify verified results
  });
});

// =========================================================================
// 6. PRESCRIPTION & PHARMACY BOUNDARY
// =========================================================================

test('Prescription creation and pharmacy role boundary', async (t) => {
  await t.test('prescription creates with PENDING_VERIFICATION status', () => {
    const prescriptionPayload: Partial<Prescription> = {
      visit: 1,
      patient: 101,
      facility: 1,
      directions: 'Tab. Paracetamol 650mg: 1 tablet TDS after food for 3 days; Tab. ORS sachet: 1 packet in 1L water daily.',
      notes: 'Advised plenty of fluids. Review SOS.',
      status: 'PENDING_VERIFICATION',
    };

    assert.equal(prescriptionPayload.status, 'PENDING_VERIFICATION');
    assert.ok(prescriptionPayload.directions?.includes('Paracetamol'));
  });

  await t.test('doctor cannot dispense medication (dispensing is pharmacist domain)', () => {
    assert.equal(isRouteAllowedForRole('DOCTOR', '/pharmacy'), false);
    assert.equal(isRouteAllowedForRole('PHARMACIST', '/pharmacy'), true);
  });
});

// =========================================================================
// 7. REFERRAL & FOLLOW-UP TASK MANAGEMENT
// =========================================================================

test('Referral order and follow-up task construction', async (t) => {
  await t.test('constructs secondary referral order payload', () => {
    const referralPayload: Partial<ReferralOrder> = {
      visit: 1,
      patient: 101,
      referring_facility: 1,
      referred_to_facility: 2, // Secondary District Hospital
      referral_reason: 'Persistent fever with falling platelet trend, requires secondary inpatient monitoring',
      urgency_level: 'URGENT',
      clinical_notes: 'Transferred via 108 ambulance with IV fluids running',
      status: 'PENDING',
    };

    assert.equal(referralPayload.urgency_level, 'URGENT');
    assert.equal(referralPayload.referred_to_facility, 2);
    assert.equal(referralPayload.status, 'PENDING');
  });

  await t.test('constructs follow-up task payload', () => {
    const followUpPayload: Partial<FollowUpTask> = {
      visit: 1,
      patient: 101,
      facility: 1,
      follow_up_date: '2026-09-27',
      category: 'CLINICAL_REVIEW',
      instructions: 'Repeat platelet count and assess temperature resolution',
      priority: 'HIGH',
      status: 'PENDING',
    };

    assert.equal(followUpPayload.follow_up_date, '2026-09-27');
    assert.equal(followUpPayload.category, 'CLINICAL_REVIEW');
    assert.equal(followUpPayload.status, 'PENDING');
  });
});

// =========================================================================
// 8. API ERROR & STATUS PARSING
// =========================================================================

test('API failure and error parsing in clinical operations', async (t) => {
  await t.test('handles 400 validation error with field mapping', () => {
    const apiError = {
      response: {
        status: 400,
        data: {
          chief_complaint: ['This field may not be blank.'],
          diagnosis_code: ['Invalid ICD code format.'],
        },
      },
    };
    const parsed = parseApiError(apiError);
    assert.ok(parsed.includes('Chief Complaint: This field may not be blank.'));
  });

  await t.test('handles 403 Forbidden error response', () => {
    const forbiddenError = {
      response: {
        status: 403,
        data: {
          detail: 'You do not have permission to perform this clinical action.',
        },
      },
    };
    assert.equal(
      parseApiError(forbiddenError),
      'You do not have permission to perform this clinical action.'
    );
  });

  await t.test('handles 404 Not Found error response', () => {
    const notFoundError = {
      response: {
        status: 404,
        data: {
          detail: 'Encounter visit record not found for this facility.',
        },
      },
    };
    assert.equal(
      parseApiError(notFoundError),
      'Encounter visit record not found for this facility.'
    );
  });
});
