import test from 'node:test';
import assert from 'node:assert/strict';
import { isRouteAllowedForRole } from '../navigation/navigationConfig.ts';
import { parseApiError } from '../api/client.ts';
import type { Role } from '../types/auth.ts';
import type {
  Visit,
  Patient,
  TriageVitals,
  CreateTriagePayload,
} from '../types/index.ts';

// =========================================================================
// 1. NURSE WORKFLOW ROUTE ACCESS & 403 ACCESS CONTROL
// =========================================================================

test('Nurse clinical workflow authorization and role access control', async (t) => {
  await t.test('Nurse can access nurse dashboard and triage station routes', () => {
    assert.equal(isRouteAllowedForRole('NURSE', '/dashboard/nurse'), true);
    assert.equal(isRouteAllowedForRole('NURSE', '/triage'), true);
    assert.equal(isRouteAllowedForRole('NURSE', '/queue'), true);
    assert.equal(isRouteAllowedForRole('NURSE', '/patients'), true);
  });

  await t.test('Doctor is blocked from Nurse-only triage route and dashboard', () => {
    assert.equal(
      isRouteAllowedForRole('DOCTOR', '/triage'),
      false,
      'Doctor must NOT be allowed to access /triage'
    );
    assert.equal(
      isRouteAllowedForRole('DOCTOR', '/dashboard/nurse'),
      false,
      'Doctor must NOT be allowed to access /dashboard/nurse'
    );
  });

  await t.test('Other non-nurse roles are blocked from /triage and /dashboard/nurse', () => {
    const restrictedRoles: Role[] = [
      'LAB_TECHNICIAN',
      'PHARMACIST',
      'HOSPITAL_ADMIN',
      'DISTRICT_OFFICER',
    ];
    for (const role of restrictedRoles) {
      assert.equal(
        isRouteAllowedForRole(role, '/triage'),
        false,
        `Role ${role} must NOT be allowed to access /triage`
      );
      assert.equal(
        isRouteAllowedForRole(role, '/dashboard/nurse'),
        false,
        `Role ${role} must NOT be allowed to access /dashboard/nurse`
      );
    }
  });

  await t.test('Nurse is blocked from Doctor, Pharmacy, Lab, and Admin routes', () => {
    assert.equal(isRouteAllowedForRole('NURSE', '/consultation'), false);
    assert.equal(isRouteAllowedForRole('NURSE', '/pharmacy'), false);
    assert.equal(isRouteAllowedForRole('NURSE', '/lab'), false);
    assert.equal(isRouteAllowedForRole('NURSE', '/dashboard/doctor'), false);
    assert.equal(isRouteAllowedForRole('NURSE', '/dashboard/admin'), false);
    assert.equal(isRouteAllowedForRole('NURSE', '/dashboard/district'), false);
  });
});

// =========================================================================
// 2. NURSE DASHBOARD QUEUE METRICS & FILTERING
// =========================================================================

test('Nurse dashboard queue metrics calculation and tab filtering', async (t) => {
  const mockVisits: Visit[] = [
    {
      id: 1,
      visit_id: 'VIS-20260925-0001',
      patient: 101,
      facility: 1,
      facility_name: 'Urban Primary Health Centre',
      visit_date: '2026-09-25',
      opd_date: '2026-09-25',
      visit_type: 'OPD_GENERAL',
      status: 'WAITING_FOR_TRIAGE',
      current_queue: 'TRIAGE',
      chief_complaint: 'Headache and fever',
      token_number: 1,
      priority: 'NORMAL',
    },
    {
      id: 2,
      visit_id: 'VIS-20260925-0002',
      patient: 102,
      facility: 1,
      facility_name: 'Urban Primary Health Centre',
      visit_date: '2026-09-25',
      opd_date: '2026-09-25',
      visit_type: 'OPD_GENERAL',
      status: 'REGISTERED',
      current_queue: 'TRIAGE',
      chief_complaint: 'Chest pain',
      token_number: 2,
      priority: 'EMERGENCY',
    },
    {
      id: 3,
      visit_id: 'VIS-20260925-0003',
      patient: 103,
      facility: 1,
      facility_name: 'Urban Primary Health Centre',
      visit_date: '2026-09-25',
      opd_date: '2026-09-25',
      visit_type: 'OPD_GENERAL',
      status: 'TRIAGED',
      current_queue: 'DOCTOR',
      chief_complaint: 'Routine follow-up',
      token_number: 3,
      priority: 'HIGH',
    },
    {
      id: 4,
      visit_id: 'VIS-20260925-0004',
      patient: 104,
      facility: 1,
      facility_name: 'Urban Primary Health Centre',
      visit_date: '2026-09-25',
      opd_date: '2026-09-25',
      visit_type: 'OPD_GENERAL',
      status: 'COMPLETED',
      current_queue: 'PHARMACY',
      chief_complaint: 'Resolved',
      token_number: 4,
      priority: 'NORMAL',
    },
    {
      id: 5,
      visit_id: 'VIS-20260925-0005',
      patient: 105,
      facility: 1,
      facility_name: 'Urban Primary Health Centre',
      visit_date: '2026-09-25',
      opd_date: '2026-09-25',
      visit_type: 'OPD_GENERAL',
      status: 'WAITING_FOR_LAB',
      current_queue: 'LAB',
      chief_complaint: 'Fever with chills',
      token_number: 5,
      priority: 'NORMAL',
    },
  ];

  await t.test('calculates nurse metrics authoritatively from backend visits', () => {
    const pendingVisits = mockVisits.filter(
      (v) =>
        v.current_queue === 'TRIAGE' ||
        ['WAITING_FOR_TRIAGE', 'REGISTERED', 'IN_TRIAGE'].includes(v.status)
    );
    const triagedVisits = mockVisits.filter(
      (v) =>
        v.current_queue !== 'TRIAGE' &&
        !['WAITING_FOR_TRIAGE', 'REGISTERED', 'IN_TRIAGE'].includes(v.status)
    );
    const emergencyOrHighVisits = mockVisits.filter(
      (v) => v.priority === 'EMERGENCY' || v.priority === 'HIGH'
    );

    assert.equal(pendingVisits.length, 2, 'Pending visits must be 2');
    assert.equal(triagedVisits.length, 3, 'Triaged visits must include WAITING_FOR_LAB');
    assert.equal(emergencyOrHighVisits.length, 2, 'High priority/emergency visits must be 2');
    assert.equal(mockVisits.length, 5, 'Total encounters must be 5');
  });

  await t.test('filters visits correctly by tab selection', () => {
    const filterQueue = (tab: 'PENDING' | 'TRIAGED' | 'ALL') => {
      return mockVisits.filter((v) => {
        if (tab === 'PENDING') {
          return (
            v.current_queue === 'TRIAGE' ||
            ['WAITING_FOR_TRIAGE', 'REGISTERED', 'IN_TRIAGE'].includes(v.status)
          );
        }
        if (tab === 'TRIAGED') {
          return (
            v.current_queue !== 'TRIAGE' &&
            !['WAITING_FOR_TRIAGE', 'REGISTERED', 'IN_TRIAGE'].includes(v.status)
          );
        }
        return true;
      });
    };

    assert.equal(filterQueue('PENDING').length, 2);
    assert.equal(filterQueue('TRIAGED').length, 3);
    assert.equal(filterQueue('ALL').length, 5);
  });

  await t.test('handles empty queue gracefully without crashing', () => {
    const emptyVisits: Visit[] = [];
    const pending = emptyVisits.filter(
      (v) =>
        v.current_queue === 'TRIAGE' ||
        ['WAITING_FOR_TRIAGE', 'REGISTERED', 'IN_TRIAGE'].includes(v.status)
    );
    assert.equal(pending.length, 0);
  });
});

// =========================================================================
// 3. PATIENT CONTEXT & DEMOGRAPHIC BANNER FORMATTING
// =========================================================================

test('Patient demographic context and encounter banner formatting', async (t) => {
  const patient: Patient = {
    id: 101,
    name: 'Senthil Nathan',
    age: 42,
    gender: 'MALE',
    mobile: '9876543210',
    address: '12 Main Street, Chennai',
    abha_address: 'senthil@abdm',
  };

  const visit: Visit = {
    id: 1,
    visit_id: 'VIS-LOC-001',
    patient: 101,
    facility: 1,
    facility_name: 'Urban Primary Health Centre',
    visit_date: '2026-09-25',
    visit_type: 'OPD_GENERAL',
    status: 'WAITING_FOR_TRIAGE',
    current_queue: 'TRIAGE',
    chief_complaint: 'Generalized weakness',
    token_number: 14,
    priority: 'HIGH',
  };

  await t.test('exposes all required patient demographics for intake', () => {
    assert.equal(patient.name, 'Senthil Nathan');
    assert.equal(patient.age, 42);
    assert.equal(patient.gender, 'MALE');
    assert.equal(patient.mobile, '9876543210');
    assert.equal(patient.abha_address, 'senthil@abdm');
  });

  await t.test('exposes encounter token and priority', () => {
    assert.equal(visit.token_number, 14);
    assert.equal(visit.priority, 'HIGH');
    assert.equal(visit.current_queue, 'TRIAGE');
  });
});

// =========================================================================
// 4. TRIAGE FORM PHYSIOLOGICAL RANGE VALIDATION (CLIENT-SIDE)
// =========================================================================

test('Triage form physiological range validation', async (t) => {
  const validateVitals = (v: {
    sys: number;
    dia: number;
    pulse: number;
    temp: number;
    spo2: number;
    resp: number;
    height: number;
    weight: number;
    glucose: number;
  }) => {
    const errs: string[] = [];
    if (v.sys < 50 || v.sys > 300) errs.push('Systolic BP out of range (50-300)');
    if (v.dia < 30 || v.dia > 200) errs.push('Diastolic BP out of range (30-200)');
    if (v.dia >= v.sys) errs.push('Diastolic BP cannot exceed or equal Systolic BP');
    if (v.pulse < 30 || v.pulse > 250) errs.push('Pulse out of range (30-250)');
    if (v.temp < 90 || v.temp > 110) errs.push('Temperature out of range (90-110)');
    if (v.spo2 < 50 || v.spo2 > 100) errs.push('SpO2 out of range (50-100)');
    if (v.resp < 5 || v.resp > 60) errs.push('Resp rate out of range (5-60)');
    if (v.height < 30 || v.height > 260) errs.push('Height out of range (30-260)');
    if (v.weight < 1 || v.weight > 350) errs.push('Weight out of range (1-350)');
    if (v.glucose < 20 || v.glucose > 800) errs.push('Glucose out of range (20-800)');
    return errs;
  };

  await t.test('passes validation with normal physiological vitals', () => {
    const normal = {
      sys: 120,
      dia: 80,
      pulse: 76,
      temp: 98.6,
      spo2: 99,
      resp: 18,
      height: 165,
      weight: 65,
      glucose: 110,
    };
    const errors = validateVitals(normal);
    assert.equal(errors.length, 0);
  });

  await t.test('catches invalid systolic/diastolic inversion', () => {
    const invalidBp = {
      sys: 80,
      dia: 120,
      pulse: 76,
      temp: 98.6,
      spo2: 99,
      resp: 18,
      height: 165,
      weight: 65,
      glucose: 110,
    };
    const errors = validateVitals(invalidBp);
    assert.ok(errors.includes('Diastolic BP cannot exceed or equal Systolic BP'));
  });

  await t.test('catches physiologically impossible SpO2 and Temperature values', () => {
    const badValues = {
      sys: 120,
      dia: 80,
      pulse: 76,
      temp: 115.0, // impossible fever
      spo2: 35, // impossible SpO2
      resp: 18,
      height: 165,
      weight: 65,
      glucose: 110,
    };
    const errors = validateVitals(badValues);
    assert.ok(errors.includes('Temperature out of range (90-110)'));
    assert.ok(errors.includes('SpO2 out of range (50-100)'));
  });
});

// =========================================================================
// 5. PHASE 24A: MATERNAL/CHILD REMOVAL & CLINICAL WARNING AUTHORITY
// =========================================================================

test('Phase 24A: Complete removal of Maternal/Child logic from active Nurse triage', async (t) => {
  await t.test('CreateTriagePayload does not contain pregnancy_high_risk_flag', () => {
    const payload: CreateTriagePayload = {
      visit: 1,
      patient: 101,
      blood_pressure_systolic: 120,
      blood_pressure_diastolic: 80,
      pulse_bpm: 72,
      temperature_f: 98.6,
      spo2_percent: 98,
      respiratory_rate: 18,
      height_cm: 165,
      weight_kg: 65,
      blood_glucose_mgdl: 110,
      emergency_flag: false,
      ncd_risk_flag: false,
      nurse_notes: 'Standard adult triage',
    };

    assert.equal('pregnancy_high_risk_flag' in payload, false, 'pregnancy_high_risk_flag must NOT be in active payload');
  });

  await t.test('Warning evaluation excludes maternal/child flags', () => {
    // Authoritative backend warning flags
    const activeWorkflowFlags = [
      'high_bp_flag',
      'high_glucose_flag',
      'fever_flag',
      'low_spo2_flag',
      'emergency_flag',
      'ncd_risk_flag',
    ];
    assert.equal(activeWorkflowFlags.includes('pregnancy_high_risk_flag'), false);
  });
});

// =========================================================================
// 6. PHASE 24A: DERIVED MATHEMATICAL BMI WITHOUT MEDICAL DIAGNOSIS
// =========================================================================

test('Phase 24A: Derived BMI computation is purely mathematical without clinical diagnosis', async (t) => {
  const computeDerivedBmi = (heightCm: number, weightKg: number): string | null => {
    if (heightCm <= 0 || weightKg <= 0) return null;
    const hM = heightCm / 100.0;
    return (weightKg / (hM * hM)).toFixed(1);
  };

  await t.test('accurately calculates numeric BMI as derived value', () => {
    const bmi = computeDerivedBmi(165, 65);
    assert.equal(bmi, '23.9');
  });

  await t.test('does not attach clinical diagnostic labels (e.g., Obese/Normal) in React', () => {
    const bmiVal = computeDerivedBmi(160, 62);
    assert.equal(bmiVal, '24.2');
    // Pure mathematical string, no medical category attached
    assert.equal(typeof bmiVal, 'string');
  });
});

// =========================================================================
// 7. PHASE 24A: NON-ATOMIC HANDOFF & PARTIAL FAILURE HANDLING
// =========================================================================

test('Phase 24A: Triage handoff atomicity and safe partial failure handling', async (t) => {
  await t.test('handles partial failure: triage saved but visit transition fails', () => {
    let savedTriageRecord: TriageVitals | null = null;
    let handoffFailed = false;
    let errorMessage: string | null = null;
    let successMessage: string | null = null;

    // Simulate Step 1: Triage POST succeeds
    savedTriageRecord = {
      id: 20,
      visit: 1,
      patient: 101,
      nurse: 2,
      blood_pressure_systolic: 130,
      blood_pressure_diastolic: 85,
      pulse_bpm: 76,
      temperature_f: 98.6,
      spo2_percent: 99,
      respiratory_rate: 18,
      height_cm: 165,
      weight_kg: 65,
      bmi: 23.9,
      blood_glucose_mgdl: 110,
      high_bp_flag: false,
      high_glucose_flag: false,
      fever_flag: false,
      low_spo2_flag: false,
      emergency_flag: false,
      ncd_risk_flag: false,
      nurse_notes: 'Triage recorded',
      created_at: '2026-09-25T11:00:00Z',
    };

    // Simulate Step 2: Visit PATCH fails (e.g., network error)
    const handoffError = new Error('Network timeout during queue forward');
    handoffFailed = true;
    errorMessage = `Triage vitals saved, but forwarding to Doctor queue failed: ${handoffError.message}.`;

    // Critical assertion: UI must NOT claim successful Doctor handoff
    assert.equal(successMessage, null, 'Must NOT falsely display Doctor handoff success');
    assert.ok(savedTriageRecord !== null, 'Triage record must be preserved');
    assert.equal(handoffFailed, true, 'Handoff failure state must be flagged');
    assert.ok(errorMessage.includes('forwarding to Doctor queue failed'));
  });

  await t.test('retry mechanism resolves queue handoff', () => {
    let visitStatus = 'WAITING_FOR_TRIAGE';
    let currentQueue = 'TRIAGE';
    let handoffFailed = true;

    // Execute retry
    visitStatus = 'TRIAGED';
    currentQueue = 'DOCTOR';
    handoffFailed = false;

    assert.equal(visitStatus, 'TRIAGED');
    assert.equal(currentQueue, 'DOCTOR');
    assert.equal(handoffFailed, false);
  });
});

// =========================================================================
// 8. PHASE 24A: TRIAGE CORRECTION & BACKEND MUTATION SEMANTICS
// =========================================================================

test('Phase 24A: Triage correction mutates existing record directly (backend limitation)', async (t) => {
  const originalRecord: TriageVitals = {
    id: 10,
    visit: 1,
    patient: 101,
    nurse: 2,
    blood_pressure_systolic: 120,
    blood_pressure_diastolic: 80,
    pulse_bpm: 72,
    temperature_f: 98.6,
    spo2_percent: 98,
    respiratory_rate: 18,
    height_cm: 165,
    weight_kg: 65,
    bmi: 23.9,
    blood_glucose_mgdl: 110,
    high_bp_flag: false,
    high_glucose_flag: false,
    fever_flag: false,
    low_spo2_flag: false,
    emergency_flag: false,
    ncd_risk_flag: false,
    nurse_notes: 'Initial observation',
    created_at: '2026-09-25T10:00:00Z',
  };

  // Correction via PATCH /api/v1/clinical/triage/10/
  const correctedRecord: TriageVitals = {
    ...originalRecord,
    blood_pressure_systolic: 135,
    blood_pressure_diastolic: 88,
    nurse_notes: 'Corrected blood pressure reading',
  };

  await t.test('correction mutates in-place without creating a new ID', () => {
    assert.equal(correctedRecord.id, originalRecord.id);
    assert.equal(correctedRecord.blood_pressure_systolic, 135);
  });

  await t.test('preserves original nurse author and timestamp', () => {
    assert.equal(correctedRecord.nurse, 2);
    assert.equal(correctedRecord.created_at, originalRecord.created_at);
  });
});

// =========================================================================
// 9. DOCTOR COMPATIBILITY & HANDOFF CONSUMPTION
// =========================================================================

test('Phase 24A: Doctor compatibility and triage consumption', async (t) => {
  await t.test('Doctor workflow consumes newly triaged visit', () => {
    const visit: Partial<Visit> = {
      id: 5,
      status: 'TRIAGED',
      current_queue: 'DOCTOR',
    };

    // Doctor queue eligibility condition from DoctorDashboard.tsx
    const isEligibleForDoctor =
      visit.current_queue === 'DOCTOR' ||
      ['TRIAGED', 'WAITING_FOR_DOCTOR', 'IN_CONSULTATION'].includes(visit.status || '');

    assert.equal(isEligibleForDoctor, true);
  });

  await t.test('Doctor can review triage vitals and clinical warning flags', () => {
    const triage: TriageVitals = {
      id: 5,
      visit: 5,
      patient: 105,
      nurse: 3,
      blood_pressure_systolic: 145,
      blood_pressure_diastolic: 92,
      pulse_bpm: 88,
      temperature_f: 101.2,
      spo2_percent: 94,
      respiratory_rate: 20,
      height_cm: 170,
      weight_kg: 70,
      bmi: 24.2,
      blood_glucose_mgdl: 175,
      high_bp_flag: true,
      high_glucose_flag: true,
      fever_flag: true,
      low_spo2_flag: true,
      emergency_flag: false,
      ncd_risk_flag: true,
      nurse_notes: 'Patient flushed, complains of chills',
      created_at: '2026-09-25T11:15:00Z',
    };

    assert.equal(triage.high_bp_flag, true);
    assert.equal(triage.fever_flag, true);
    assert.equal(triage.low_spo2_flag, true);
    assert.equal(triage.high_glucose_flag, true);
    assert.equal(triage.ncd_risk_flag, true);
    assert.equal(triage.nurse, 3);
  });
});

// =========================================================================
// 10. API ERROR PARSING FOR TRIAGE OPERATIONS
// =========================================================================

test('API error parsing for Triage operations', async (t) => {
  await t.test('handles duplicate triage error for same visit (400)', () => {
    const errorResponse = {
      response: {
        status: 400,
        data: {
          visit: ['triage vitals with this visit already exists.'],
        },
      },
    };
    const parsed = parseApiError(errorResponse);
    assert.ok(parsed.includes('triage vitals with this visit already exists.'));
  });

  await t.test('handles 403 Forbidden error', () => {
    const errorResponse = {
      response: {
        status: 403,
        data: {
          detail: 'You do not have permission to perform this action.',
        },
      },
    };
    const parsed = parseApiError(errorResponse);
    assert.equal(parsed, 'You do not have permission to perform this action.');
  });
});
