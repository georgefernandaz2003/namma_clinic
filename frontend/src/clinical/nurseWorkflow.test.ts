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
      chief_complaint: 'High fever and headache',
      priority: 'EMERGENCY',
      token_number: 1,
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
      chief_complaint: 'Body pain',
      priority: 'NORMAL',
      token_number: 2,
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
      chief_complaint: 'Follow-up hypertension',
      priority: 'NORMAL',
      token_number: 3,
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
      current_queue: 'COMPLETED',
      chief_complaint: 'Routine checkup',
      priority: 'NORMAL',
      token_number: 4,
    },
  ];

  await t.test('calculates nurse metrics authoritatively from backend visits', () => {
    const totalToday = mockVisits.length;
    const pendingTriage = mockVisits.filter(
      (v) =>
        v.current_queue === 'TRIAGE' ||
        ['WAITING_FOR_TRIAGE', 'REGISTERED', 'IN_TRIAGE'].includes(v.status)
    ).length;
    const triagedToday = mockVisits.filter(
      (v) =>
        ['TRIAGED', 'WAITING_FOR_DOCTOR', 'IN_CONSULTATION', 'COMPLETED'].includes(v.status) &&
        v.current_queue !== 'TRIAGE'
    ).length;
    const emergencyOrHigh = mockVisits.filter(
      (v) => v.priority === 'EMERGENCY' || v.priority === 'HIGH'
    ).length;

    assert.equal(totalToday, 4);
    assert.equal(pendingTriage, 2);
    assert.equal(triagedToday, 2);
    assert.equal(emergencyOrHigh, 1);
  });

  await t.test('filters visits correctly by tab selection', () => {
    const pendingList = mockVisits.filter(
      (v) =>
        v.current_queue === 'TRIAGE' ||
        ['WAITING_FOR_TRIAGE', 'REGISTERED', 'IN_TRIAGE'].includes(v.status)
    );
    const triagedList = mockVisits.filter(
      (v) =>
        ['TRIAGED', 'WAITING_FOR_DOCTOR', 'IN_CONSULTATION', 'COMPLETED'].includes(v.status) &&
        v.current_queue !== 'TRIAGE'
    );

    assert.equal(pendingList.length, 2);
    assert.equal(pendingList[0].id, 1);
    assert.equal(pendingList[1].id, 2);

    assert.equal(triagedList.length, 2);
    assert.equal(triagedList[0].id, 3);
    assert.equal(triagedList[1].id, 4);
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
// 3. PATIENT CONTEXT & DEMOGRAPHICS IN TRIAGE
// =========================================================================

test('Patient demographic context and encounter banner formatting', async (t) => {
  const patient: Patient = {
    id: 101,
    patient_id: 'PAT-20260925-00101',
    name: 'Meena Sundaram',
    first_name: 'Meena',
    last_name: 'Sundaram',
    age: 38,
    gender: 'FEMALE',
    mobile: '9840112233',
    address: '45 Lake View Road, Chennai',
    ABHA_ID_DEMO: 'meena.sundaram@abdm',
    blood_group: 'B+',
    emergency_contact: '9840112234',
    vulnerability_information: 'None',
    registration_date: '2026-09-25',
  };

  const visit: Visit = {
    id: 1,
    visit_id: 'VIS-20260925-0001',
    patient: 101,
    facility: 1,
    visit_date: '2026-09-25',
    opd_date: '2026-09-25',
    visit_type: 'OPD_GENERAL',
    status: 'WAITING_FOR_TRIAGE',
    current_queue: 'TRIAGE',
    chief_complaint: 'Fever and chills for 2 days',
    priority: 'EMERGENCY',
    token_number: 5,
  };

  await t.test('exposes all required patient demographics for intake', () => {
    assert.equal(patient.name, 'Meena Sundaram');
    assert.equal(patient.age, 38);
    assert.equal(patient.gender, 'FEMALE');
    assert.equal(patient.blood_group, 'B+');
    assert.equal(patient.mobile, '9840112233');
    assert.equal(patient.ABHA_ID_DEMO, 'meena.sundaram@abdm');
  });

  await t.test('exposes encounter token and priority', () => {
    assert.equal(visit.token_number, 5);
    assert.equal(visit.priority, 'EMERGENCY');
    assert.equal(visit.current_queue, 'TRIAGE');
  });
});

// =========================================================================
// 4. TRIAGE FORM PHYSIOLOGICAL VALIDATION
// =========================================================================

test('Triage form physiological range validation', async (t) => {
  const validateVitals = (form: {
    sys: number;
    dia: number;
    pulse: number;
    temp: number;
    spo2: number;
    resp: number;
    height: number;
    weight: number;
    glucose: number;
  }): string[] => {
    const errors: string[] = [];
    if (form.sys < 50 || form.sys > 300) errors.push('Systolic BP out of range (50-300)');
    if (form.dia < 30 || form.dia > 200) errors.push('Diastolic BP out of range (30-200)');
    if (form.dia >= form.sys) errors.push('Diastolic BP cannot exceed or equal Systolic BP');
    if (form.pulse < 30 || form.pulse > 250) errors.push('Pulse out of range (30-250)');
    if (form.temp < 90 || form.temp > 110) errors.push('Temperature out of range (90-110)');
    if (form.spo2 < 50 || form.spo2 > 100) errors.push('SpO2 out of range (50-100)');
    if (form.resp < 5 || form.resp > 60) errors.push('Resp rate out of range (5-60)');
    if (form.height < 30 || form.height > 260) errors.push('Height out of range (30-260)');
    if (form.weight < 1 || form.weight > 350) errors.push('Weight out of range (1-350)');
    if (form.glucose < 20 || form.glucose > 800) errors.push('Glucose out of range (20-800)');
    return errors;
  };

  await t.test('passes validation with normal physiological vitals', () => {
    const valid = {
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
    const errors = validateVitals(valid);
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
// 5. CLINICAL WARNING THRESHOLDS & REAL-TIME BMI
// =========================================================================

test('Clinical warning thresholds evaluation and BMI computation', async (t) => {
  const computeBmi = (heightCm: number, weightKg: number): number => {
    const hM = heightCm / 100.0;
    return parseFloat((weightKg / (hM * hM)).toFixed(1));
  };

  const evaluateWarnings = (vitals: {
    sys: number;
    dia: number;
    temp: number;
    spo2: number;
    glucose: number;
    emergency: boolean;
  }) => {
    return {
      high_bp: vitals.sys >= 140 || vitals.dia >= 90,
      fever: vitals.temp >= 100.4,
      low_spo2: vitals.spo2 < 95,
      high_glucose: vitals.glucose >= 160,
      emergency: vitals.emergency,
    };
  };

  await t.test('accurately calculates BMI from height and weight', () => {
    const bmi = computeBmi(165, 65);
    assert.equal(bmi, 23.9);
  });

  await t.test('triggers automated clinical warning flags when thresholds are exceeded', () => {
    const abnormal = {
      sys: 150,
      dia: 95,
      temp: 101.5,
      spo2: 93,
      glucose: 185,
      emergency: true,
    };
    const warnings = evaluateWarnings(abnormal);
    assert.equal(warnings.high_bp, true);
    assert.equal(warnings.fever, true);
    assert.equal(warnings.low_spo2, true);
    assert.equal(warnings.high_glucose, true);
    assert.equal(warnings.emergency, true);
  });

  await t.test('does not trigger warnings for normotensive, euglycemic, afebrile vitals', () => {
    const normal = {
      sys: 118,
      dia: 78,
      temp: 98.4,
      spo2: 99,
      glucose: 105,
      emergency: false,
    };
    const warnings = evaluateWarnings(normal);
    assert.equal(warnings.high_bp, false);
    assert.equal(warnings.fever, false);
    assert.equal(warnings.low_spo2, false);
    assert.equal(warnings.high_glucose, false);
    assert.equal(warnings.emergency, false);
  });
});

// =========================================================================
// 6. TRIAGE CREATION PAYLOAD & DOCTOR HANDOFF
// =========================================================================

test('Triage payload construction and Doctor queue handoff lifecycle', async (t) => {
  await t.test('builds valid DRF TriageVitals creation payload', () => {
    const payload: CreateTriagePayload = {
      visit: 1,
      patient: 101,
      blood_pressure_systolic: 130,
      blood_pressure_diastolic: 85,
      pulse_bpm: 76,
      temperature_f: '98.6',
      spo2_percent: 99,
      respiratory_rate: 18,
      height_cm: '165.0',
      weight_kg: '65.0',
      blood_glucose_mgdl: 110,
      pregnancy_high_risk_flag: false,
      emergency_flag: false,
      ncd_risk_flag: false,
      nurse_notes: 'Patient alert and ambulatory. Mild throat irritation.',
    };

    assert.equal(payload.visit, 1);
    assert.equal(payload.patient, 101);
    assert.equal(payload.blood_pressure_systolic, 130);
    assert.equal(payload.pulse_bpm, 76);
    assert.equal(payload.temperature_f, '98.6');
  });

  await t.test('handoff: visit transitions to TRIAGED and DOCTOR queue', () => {
    // Before triage
    const initialVisit: Partial<Visit> = {
      id: 1,
      status: 'WAITING_FOR_TRIAGE',
      current_queue: 'TRIAGE',
    };

    // After successful triage, visit is updated
    const updatedVisit: Partial<Visit> = {
      ...initialVisit,
      status: 'TRIAGED',
      current_queue: 'DOCTOR',
    };

    assert.equal(updatedVisit.status, 'TRIAGED');
    assert.equal(updatedVisit.current_queue, 'DOCTOR');

    // Doctor workflow consumes visits where current_queue === 'DOCTOR' or status === 'TRIAGED'
    const isReadyForDoctor =
      updatedVisit.current_queue === 'DOCTOR' ||
      ['TRIAGED', 'WAITING_FOR_DOCTOR'].includes(updatedVisit.status || '');
    assert.equal(isReadyForDoctor, true);
  });
});

// =========================================================================
// 7. ALREADY-RECORDED TRIAGE & AUTHORSHIP DISPLAY
// =========================================================================

test('Handling of already-recorded triage and clinical authorship integrity', async (t) => {
  const existingTriage: TriageVitals = {
    id: 10,
    visit: 1,
    patient: 101,
    nurse: 2, // Nurse user ID
    blood_pressure_systolic: 130,
    blood_pressure_diastolic: 85,
    pulse_bpm: 76,
    temperature_f: '98.6',
    spo2_percent: 99,
    respiratory_rate: 18,
    height_cm: '165.0',
    weight_kg: '65.0',
    bmi: '23.9',
    blood_glucose_mgdl: 110,
    high_bp_flag: false,
    high_glucose_flag: false,
    fever_flag: false,
    low_spo2_flag: false,
    pregnancy_high_risk_flag: false,
    emergency_flag: false,
    ncd_risk_flag: false,
    nurse_notes: 'Initial intake completed by Staff Nurse',
    created_at: '2026-09-25T10:00:00Z',
  };

  await t.test('preserves nurse authorship metadata', () => {
    assert.equal(existingTriage.nurse, 2);
    assert.ok(existingTriage.created_at);
    assert.equal(existingTriage.nurse_notes, 'Initial intake completed by Staff Nurse');
  });

  await t.test('formats recorded vitals correctly for display', () => {
    assert.equal(
      `${existingTriage.blood_pressure_systolic}/${existingTriage.blood_pressure_diastolic} mmHg`,
      '130/85 mmHg'
    );
    assert.equal(`${existingTriage.pulse_bpm} bpm`, '76 bpm');
    assert.equal(`${existingTriage.temperature_f}°F`, '98.6°F');
  });
});

// =========================================================================
// 8. API ERROR RESPONSES IN TRIAGE OPERATIONS
// =========================================================================

test('API error parsing for Triage operations', async (t) => {
  await t.test('handles duplicate triage error for same visit (400)', () => {
    const duplicateError = {
      response: {
        status: 400,
        data: {
          visit: ['triage vitals with this visit already exists.'],
        },
      },
    };
    const parsed = parseApiError(duplicateError);
    assert.ok(parsed.includes('Visit: triage vitals with this visit already exists.'));
  });

  await t.test('handles 403 Forbidden error', () => {
    const forbidden = {
      response: {
        status: 403,
        data: {
          detail: 'You do not have permission to record triage for this facility.',
        },
      },
    };
    const parsed = parseApiError(forbidden);
    assert.equal(parsed, 'You do not have permission to record triage for this facility.');
  });
});
