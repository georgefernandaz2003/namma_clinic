import test from 'node:test';
import assert from 'node:assert/strict';
import type { Patient } from '../types/index.ts';

// State machine simulating the exact Patients.tsx registration workflow logic
interface PatientRegistrationState {
  showRegisterModal: boolean;
  registering: boolean;
  registeredPatient: Patient | null;
  showSuccessModal: boolean;
  regError: string | null;
  patientListRefreshed: boolean;
  formFields: {
    name: string;
    age: string;
    gender: 'MALE' | 'FEMALE' | 'OTHER';
    mobile: string;
    address: string;
    abhaId: string;
    vulnerability: string;
  };
}

function createInitialState(): PatientRegistrationState {
  return {
    showRegisterModal: true,
    registering: false,
    registeredPatient: null,
    showSuccessModal: false,
    regError: null,
    patientListRefreshed: false,
    formFields: {
      name: 'Rajesh Gowda',
      age: '35',
      gender: 'MALE',
      mobile: '9876543210',
      address: 'Malleshwaram 4th Cross',
      abhaId: '14-1234-5678-9012',
      vulnerability: 'Slum Resident / Low Income Group',
    },
  };
}

async function executeRegisterWorkflow(
  state: PatientRegistrationState,
  apiPostFn: () => Promise<{ data: Patient }>,
  loadPatientsFn: () => Promise<void>
): Promise<{ success: boolean; preventedDuplicateCall?: boolean }> {
  // Double-submit prevention guard
  if (state.registering) {
    return { success: false, preventedDuplicateCall: true };
  }

  state.registering = true;
  state.regError = null;

  try {
    const res = await apiPostFn();
    const newPat = res.data;
    state.showRegisterModal = false;
    state.registeredPatient = newPat;
    state.showSuccessModal = true;
    state.regError = null;

    // Reset form fields
    state.formFields = {
      name: '',
      age: '',
      gender: 'MALE',
      mobile: '',
      address: '',
      abhaId: '',
      vulnerability: 'Slum Resident / Low Income Group',
    };

    await loadPatientsFn();
    state.patientListRefreshed = true;
    return { success: true };
  } catch (err: any) {
    let msg = 'Failed to register patient.';
    if (err.response?.data?.error) {
      msg = err.response.data.error;
    } else if (err.response?.data?.detail) {
      msg = err.response.data.detail;
    } else if (err.response?.data && typeof err.response.data === 'object') {
      msg = Object.entries(err.response.data)
        .map(([k, v]) => `${k.toUpperCase()}: ${Array.isArray(v) ? v.join(', ') : v}`)
        .join('\n');
    }
    state.regError = msg;
    state.showSuccessModal = false;
    state.registeredPatient = null;
    return { success: false };
  } finally {
    state.registering = false;
  }
}

function handleCloseSuccessModal(
  state: PatientRegistrationState,
  loadPatientsFn: () => Promise<void>
): void {
  state.showSuccessModal = false;
  state.registeredPatient = null;
  loadPatientsFn();
  state.patientListRefreshed = true;
}

test('Patient Registration Confirmation & Lifecycle Workflow Tests', async (t) => {
  const authoritativeBackendPatient: Patient = {
    id: 1042,
    patient_id: 'P20261008001',
    name: 'Rajesh Gowda',
    age: 35,
    gender: 'MALE',
    mobile: '9876543210',
    address: 'Malleshwaram 4th Cross',
    ward_name: 'Ward 45',
    district_name: 'Bengaluru Urban',
    facility_name: 'Malleshwaram UPHC',
    registration_date: '2026-10-08T10:00:00Z',
  };

  await t.test('1. Successful registration -> confirmation modal appears', async () => {
    const state = createInitialState();
    let loadCount = 0;

    const result = await executeRegisterWorkflow(
      state,
      async () => ({ data: authoritativeBackendPatient }),
      async () => {
        loadCount++;
      }
    );

    assert.equal(result.success, true);
    assert.equal(state.showSuccessModal, true, 'Confirmation modal must appear upon successful registration');
    assert.equal(state.registering, false, 'Registering state must reset to false upon completion');
    assert.equal(loadCount, 1, 'Patient list refresh must be called upon registration');
  });

  await t.test('2. Confirmation contains actual patient name from authoritative response', async () => {
    const state = createInitialState();
    await executeRegisterWorkflow(
      state,
      async () => ({ data: authoritativeBackendPatient }),
      async () => {}
    );

    assert.ok(state.registeredPatient, 'Authoritative patient object must be populated');
    assert.equal(state.registeredPatient?.name, 'Rajesh Gowda', 'Must display actual patient name');
    assert.notEqual(state.registeredPatient?.name, 'Mock Patient', 'Must not display fabricated patient name');
  });

  await t.test('3. Confirmation contains actual backend-returned patient ID', async () => {
    const state = createInitialState();
    await executeRegisterWorkflow(
      state,
      async () => ({ data: authoritativeBackendPatient }),
      async () => {}
    );

    assert.equal(state.registeredPatient?.patient_id, 'P20261008001', 'Must display authoritative patient_id');
    assert.equal(state.registeredPatient?.id, 1042, 'Must retain authoritative primary key id for navigation');
  });

  await t.test('4. Registration form modal is dismissed/inactive after success', async () => {
    const state = createInitialState();
    assert.equal(state.showRegisterModal, true, 'Registration modal was initially open');

    await executeRegisterWorkflow(
      state,
      async () => ({ data: authoritativeBackendPatient }),
      async () => {}
    );

    assert.equal(state.showRegisterModal, false, 'Registration modal must be closed/inactive');
    assert.equal(state.showSuccessModal, true, 'Only confirmation modal must be active');
    assert.equal(state.formFields.name, '', 'Form inputs must be cleared');
  });

  await t.test('5. Closing confirmation refreshes/revalidates patient list', async () => {
    const state = createInitialState();
    await executeRegisterWorkflow(
      state,
      async () => ({ data: authoritativeBackendPatient }),
      async () => {}
    );

    assert.equal(state.showSuccessModal, true);
    let refreshedListOnClose = false;

    handleCloseSuccessModal(state, async () => {
      refreshedListOnClose = true;
    });

    assert.equal(state.showSuccessModal, false, 'Confirmation modal must be dismissed');
    assert.equal(state.registeredPatient, null, 'Registered patient state must be cleared');
    assert.equal(refreshedListOnClose, true, 'Patient list must revalidate upon closing confirmation');
  });

  await t.test('6. Duplicate response (409) does NOT show success confirmation', async () => {
    const state = createInitialState();
    const duplicateError = {
      response: {
        status: 409,
        data: {
          error: 'A patient with matching demographic records (name and mobile) is already registered at this facility with ID: P20261008001.',
          existing_patient: {
            id: 1042,
            patient_id: 'P20261008001',
            name: 'Rajesh Gowda',
          },
        },
      },
    };

    const result = await executeRegisterWorkflow(
      state,
      async () => {
        throw duplicateError;
      },
      async () => {}
    );

    assert.equal(result.success, false);
    assert.equal(state.showSuccessModal, false, 'Confirmation modal must NOT appear on duplicate conflict');
    assert.equal(state.registeredPatient, null, 'No registered patient object should be set');
    assert.equal(state.showRegisterModal, true, 'Registration modal must remain open so user can review conflict');
    assert.match(state.regError || '', /already registered/i, 'Error banner must contain duplicate explanation');
    assert.equal(state.formFields.name, 'Rajesh Gowda', 'Form fields must be preserved');
  });

  await t.test('7. Registration validation error (400) does NOT show success confirmation', async () => {
    const state = createInitialState();
    const validationError = {
      response: {
        status: 400,
        data: {
          mobile: ['Mobile number must contain exactly 10 numeric digits.'],
        },
      },
    };

    const result = await executeRegisterWorkflow(
      state,
      async () => {
        throw validationError;
      },
      async () => {}
    );

    assert.equal(result.success, false);
    assert.equal(state.showSuccessModal, false, 'Confirmation modal must NOT appear on validation error');
    assert.equal(state.registeredPatient, null);
    assert.equal(state.showRegisterModal, true, 'Registration modal must remain open');
    assert.match(state.regError || '', /MOBILE.*10 numeric digits/i);
  });

  await t.test('8. Double-submit is prevented while registration is in progress', async () => {
    const state = createInitialState();
    state.registering = true; // Simulating currently pending in-flight request

    const result = await executeRegisterWorkflow(
      state,
      async () => ({ data: authoritativeBackendPatient }),
      async () => {}
    );

    assert.equal(result.success, false);
    assert.equal(result.preventedDuplicateCall, true, 'Second click must be blocked while registering is true');
    assert.equal(state.showSuccessModal, false, 'No duplicate modal transition');
  });

  await t.test('9. Backend server/network failure (500) does NOT show success confirmation', async () => {
    const state = createInitialState();
    const serverError = {
      response: {
        status: 500,
        data: {
          detail: 'Internal server error while processing database transaction.',
        },
      },
    };

    const result = await executeRegisterWorkflow(
      state,
      async () => {
        throw serverError;
      },
      async () => {}
    );

    assert.equal(result.success, false);
    assert.equal(state.showSuccessModal, false, 'Confirmation modal must NOT appear on 500 error');
    assert.equal(state.registeredPatient, null);
    assert.equal(state.registering, false, 'Registering state must reset so user can retry');
    assert.equal(state.showRegisterModal, true, 'Registration modal must remain accessible');
    assert.match(state.regError || '', /Internal server error/i);
  });
});
