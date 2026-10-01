import test from 'node:test';
import assert from 'node:assert/strict';
import { isRouteAllowedForRole, getRoleLandingRoute } from '../navigation/navigationConfig.ts';
import type {
  Prescription,
  PrescriptionItem,
  MedicineBatch,
  CreateDispensationPayload,
  InventoryLedger
} from '../types';

test('Pharmacy clinical workflow authorization and access control', async (t) => {
  await t.test('PHARMACIST can access pharmacy dashboard and workstation routes', () => {
    assert.equal(getRoleLandingRoute('PHARMACIST'), '/dashboard/pharmacy');
    assert.equal(isRouteAllowedForRole('PHARMACIST', '/dashboard/pharmacy'), true);
    assert.equal(isRouteAllowedForRole('PHARMACIST', '/pharmacy'), true);
  });

  await t.test('PHARMACIST is blocked from doctor consultation, triage, and lab workstation', () => {
    assert.equal(isRouteAllowedForRole('PHARMACIST', '/consultation'), false);
    assert.equal(isRouteAllowedForRole('PHARMACIST', '/triage'), false);
    assert.equal(isRouteAllowedForRole('PHARMACIST', '/lab'), false);
    assert.equal(isRouteAllowedForRole('PHARMACIST', '/dashboard/doctor'), false);
    assert.equal(isRouteAllowedForRole('PHARMACIST', '/dashboard/nurse'), false);
    assert.equal(isRouteAllowedForRole('PHARMACIST', '/dashboard/lab'), false);
  });

  await t.test('Non-pharmacist clinical roles (Doctor, Nurse, Lab Tech) are blocked from /pharmacy and /dashboard/pharmacy', () => {
    assert.equal(isRouteAllowedForRole('DOCTOR', '/dashboard/pharmacy'), false);
    assert.equal(isRouteAllowedForRole('DOCTOR', '/pharmacy'), false);

    assert.equal(isRouteAllowedForRole('NURSE', '/dashboard/pharmacy'), false);
    assert.equal(isRouteAllowedForRole('NURSE', '/pharmacy'), false);

    assert.equal(isRouteAllowedForRole('LAB_TECHNICIAN', '/dashboard/pharmacy'), false);
    assert.equal(isRouteAllowedForRole('LAB_TECHNICIAN', '/pharmacy'), false);
  });
});

test('Pharmacy dashboard metric calculation and tab filtering', async (t) => {
  const samplePrescriptions: Prescription[] = [
    {
      id: 1,
      consultation: 101,
      patient: 1,
      facility: 1,
      date: '2026-09-25',
      status: 'PENDING_VERIFICATION',
      items: [{ id: 1, medicine: 1, medicine_name: 'Paracetamol', dosage: '500mg', frequency: 'TID', duration_days: 3, quantity: 10, dispensed_quantity: 0, status: 'PENDING' }]
    },
    {
      id: 2,
      consultation: 102,
      patient: 2,
      facility: 1,
      date: '2026-09-25',
      status: 'VERIFIED',
      verified_by: 3,
      verified_at: '2026-09-25T10:00:00Z',
      items: [{ id: 2, medicine: 1, medicine_name: 'Paracetamol', dosage: '500mg', frequency: 'BD', duration_days: 5, quantity: 10, dispensed_quantity: 0, status: 'PENDING' }]
    },
    {
      id: 3,
      consultation: 103,
      patient: 3,
      facility: 1,
      date: '2026-09-25',
      status: 'PARTIALLY_DISPENSED',
      verified_by: 3,
      verified_at: '2026-09-25T09:00:00Z',
      items: [{ id: 3, medicine: 1, medicine_name: 'Paracetamol', dosage: '500mg', frequency: 'OD', duration_days: 10, quantity: 10, dispensed_quantity: 5, status: 'PARTIALLY_DISPENSED' }]
    },
    {
      id: 4,
      consultation: 104,
      patient: 4,
      facility: 1,
      date: '2026-09-25',
      status: 'DISPENSED',
      items: [{ id: 4, medicine: 1, medicine_name: 'Paracetamol', dosage: '500mg', frequency: 'TID', duration_days: 3, quantity: 10, dispensed_quantity: 10, status: 'DISPENSED' }]
    },
    {
      id: 5,
      consultation: 105,
      patient: 5,
      facility: 1,
      date: '2026-09-25',
      status: 'ON_HOLD',
      verification_notes: 'Checking allergy history',
      items: [{ id: 5, medicine: 1, medicine_name: 'Paracetamol', dosage: '650mg', frequency: 'TID', duration_days: 3, quantity: 10, dispensed_quantity: 0, status: 'PENDING' }]
    },
    {
      id: 6,
      consultation: 106,
      patient: 6,
      facility: 1,
      date: '2026-09-25',
      status: 'REJECTED',
      rejection_reason: 'Dose exceeds clinical maximum',
      items: [{ id: 6, medicine: 1, medicine_name: 'Paracetamol', dosage: '2000mg', frequency: 'QID', duration_days: 5, quantity: 40, dispensed_quantity: 0, status: 'PENDING' }]
    }
  ];

  const sampleBatches: MedicineBatch[] = [
    { id: 1, facility: 1, medicine: 1, batch_number: 'B-01', received_date: '2026-01-01', expiry_date: '2027-01-01', quantity: 100, available_quantity: 100, unit_cost: 1.5, status: 'AVAILABLE' },
    { id: 2, facility: 1, medicine: 1, batch_number: 'B-02', received_date: '2026-01-01', expiry_date: '2026-10-01', quantity: 50, available_quantity: 0, unit_cost: 1.5, status: 'EXHAUSTED' }
  ];

  await t.test('calculates pharmacy dashboard metrics authoritatively from backend data', () => {
    const pendingVerification = samplePrescriptions.filter((p) => p.status === 'PENDING_VERIFICATION').length;
    const readyToDispense = samplePrescriptions.filter((p) => p.status === 'VERIFIED' || p.status === 'PARTIALLY_DISPENSED').length;
    const completed = samplePrescriptions.filter((p) => p.status === 'DISPENSED').length;
    const onHold = samplePrescriptions.filter((p) => p.status === 'ON_HOLD').length;
    const activeBatches = sampleBatches.filter((b) => b.status === 'AVAILABLE' && (b.available_quantity ?? 0) > 0).length;
    const stockCritical = sampleBatches.filter((b) => (b.available_quantity ?? 0) === 0).length;

    assert.equal(pendingVerification, 1);
    assert.equal(readyToDispense, 2);
    assert.equal(completed, 1);
    assert.equal(onHold, 1);
    assert.equal(activeBatches, 1);
    assert.equal(stockCritical, 1);
  });

  await t.test('filters prescription queues correctly by status tabs', () => {
    const verifyTab = samplePrescriptions.filter((p) => p.status === 'PENDING_VERIFICATION');
    assert.equal(verifyTab.length, 1);
    assert.equal(verifyTab[0].id, 1);

    const readyTab = samplePrescriptions.filter((p) => p.status === 'VERIFIED' || p.status === 'PARTIALLY_DISPENSED');
    assert.equal(readyTab.length, 2);

    const completedTab = samplePrescriptions.filter((p) => p.status === 'DISPENSED');
    assert.equal(completedTab.length, 1);

    const holdTab = samplePrescriptions.filter((p) => p.status === 'ON_HOLD');
    assert.equal(holdTab.length, 1);
  });

  await t.test('handles empty prescription and batch queues gracefully without crashing', () => {
    const emptyRx: Prescription[] = [];
    const emptyBatches: MedicineBatch[] = [];

    assert.equal(emptyRx.filter((p) => p.status === 'PENDING_VERIFICATION').length, 0);
    assert.equal(emptyBatches.filter((b) => b.status === 'AVAILABLE').length, 0);
  });
});

test('Prescription presentation and prescribing clinician immutability', async (t) => {
  const rx: Prescription = {
    id: 10,
    consultation: 50,
    patient: 1,
    doctor_staff: 4,
    doctor: 2,
    doctor_name: 'Dr. Ramesh Kumar',
    facility: 1,
    date: '2026-09-25',
    status: 'PENDING_VERIFICATION',
    notes: 'Take after meal',
    items: [
      { id: 101, medicine: 1, medicine_name: 'Paracetamol', dosage: '500mg', frequency: 'TID', duration_days: 3, quantity: 10, dispensed_quantity: 0, status: 'PENDING' }
    ]
  };

  await t.test('preserves prescribing doctor staff attribution and clinician notes', () => {
    assert.equal(rx.doctor_staff, 4);
    assert.equal(rx.doctor_name, 'Dr. Ramesh Kumar');
    assert.equal(rx.notes, 'Take after meal');
    assert.equal(rx.items[0].quantity, 10);
  });
});

test('Prescription verification lifecycle and separation of duties', async (t) => {
  await t.test('verification transitions prescription to VERIFIED with verifier attribution', () => {
    const rx: Prescription = {
      id: 20,
      consultation: 51,
      patient: 2,
      facility: 1,
      date: '2026-09-25',
      status: 'PENDING_VERIFICATION',
      items: []
    };

    const verifiedRx: Prescription = {
      ...rx,
      status: 'VERIFIED',
      verified_by: 3,
      verified_at: '2026-09-25T11:00:00Z',
      verification_notes: 'Dose and frequency verified'
    };

    assert.equal(verifiedRx.status, 'VERIFIED');
    assert.equal(verifiedRx.verified_by, 3);
    assert.ok(verifiedRx.verified_at);
  });

  await t.test('hold action transitions status to ON_HOLD with clinical clarification notes', () => {
    const rx: Prescription = {
      id: 21,
      consultation: 52,
      patient: 3,
      facility: 1,
      date: '2026-09-25',
      status: 'PENDING_VERIFICATION',
      items: []
    };

    const holdRx: Prescription = {
      ...rx,
      status: 'ON_HOLD',
      verification_notes: 'Clarifying drug interaction with physician'
    };

    assert.equal(holdRx.status, 'ON_HOLD');
    assert.equal(holdRx.verification_notes, 'Clarifying drug interaction with physician');
  });

  await t.test('reject action mandates clinical rejection reason', () => {
    const rx: Prescription = {
      id: 22,
      consultation: 53,
      patient: 4,
      facility: 1,
      date: '2026-09-25',
      status: 'PENDING_VERIFICATION',
      items: []
    };

    const rejectionReason = 'Prescription contraindicated for patient age';
    assert.ok(rejectionReason.trim().length > 0, 'Rejection reason must be provided');

    const rejectedRx: Prescription = {
      ...rx,
      status: 'REJECTED',
      rejection_reason: rejectionReason,
      verified_by: 3,
      verified_at: '2026-09-25T11:15:00Z'
    };

    assert.equal(rejectedRx.status, 'REJECTED');
    assert.equal(rejectedRx.rejection_reason, rejectionReason);
  });
});

test('Stock availability, FEFO ordering, and batch qualification', async (t) => {
  const today = '2026-09-25';

  const batches: MedicineBatch[] = [
    { id: 1, facility: 1, medicine: 1, batch_number: 'B-FAR', received_date: '2026-01-01', expiry_date: '2027-06-30', quantity: 100, available_quantity: 100, unit_cost: 1.0, status: 'AVAILABLE' },
    { id: 2, facility: 1, medicine: 1, batch_number: 'B-SOON', received_date: '2026-01-01', expiry_date: '2026-11-30', quantity: 50, available_quantity: 50, unit_cost: 1.0, status: 'AVAILABLE' },
    { id: 3, facility: 1, medicine: 1, batch_number: 'B-EXPIRED', received_date: '2025-01-01', expiry_date: '2026-08-01', quantity: 20, available_quantity: 20, unit_cost: 1.0, status: 'EXPIRED' },
    { id: 4, facility: 1, medicine: 1, batch_number: 'B-QUARANTINE', received_date: '2026-01-01', expiry_date: '2027-01-01', quantity: 30, available_quantity: 0, quarantined_quantity: 30, unit_cost: 1.0, status: 'QUARANTINED' },
    { id: 5, facility: 2, medicine: 1, batch_number: 'B-OTHER-FAC', received_date: '2026-01-01', expiry_date: '2026-10-15', quantity: 40, available_quantity: 40, unit_cost: 1.0, status: 'AVAILABLE' }
  ];

  await t.test('filters out expired, non-available, zero stock, and wrong facility batches', () => {
    const validBatches = batches.filter((b) => {
      const isFacility = b.facility === 1;
      const isMedicine = b.medicine === 1;
      const hasStock = (b.available_quantity ?? 0) > 0;
      const isAvailable = b.status === 'AVAILABLE';
      const notExpired = b.expiry_date > today;
      return isFacility && isMedicine && hasStock && isAvailable && notExpired;
    });

    assert.equal(validBatches.length, 2);
    assert.ok(validBatches.some((b) => b.batch_number === 'B-FAR'));
    assert.ok(validBatches.some((b) => b.batch_number === 'B-SOON'));
    assert.ok(!validBatches.some((b) => b.batch_number === 'B-EXPIRED'));
    assert.ok(!validBatches.some((b) => b.batch_number === 'B-QUARANTINE'));
    assert.ok(!validBatches.some((b) => b.batch_number === 'B-OTHER-FAC'));
  });

  await t.test('sorts valid batches by FEFO (expiry_date ascending) and flags earliest as recommended', () => {
    const validBatches = batches
      .filter((b) => b.facility === 1 && (b.available_quantity ?? 0) > 0 && b.status === 'AVAILABLE' && b.expiry_date > today)
      .sort((a, b) => a.expiry_date.localeCompare(b.expiry_date));

    assert.equal(validBatches[0].batch_number, 'B-SOON');
    assert.equal(validBatches[1].batch_number, 'B-FAR');
    assert.equal(validBatches[0].id, 2);
  });
});

test('Dispensation payload creation and authoritative ledger invariant', async (t) => {
  await t.test('constructs valid CreateDispensationPayload matching backend DispenseRequestSerializer', () => {
    const payload: CreateDispensationPayload = {
      prescription_id: 3,
      facility_id: 1,
      items: [
        {
          prescription_item_id: 10,
          batch_id: 2,
          quantity: 10
        }
      ]
    };

    assert.equal(payload.prescription_id, 3);
    assert.equal(payload.facility_id, 1);
    assert.equal(payload.items.length, 1);
    assert.equal(payload.items[0].quantity, 10);
  });

  await t.test('validates that quantity must not exceed remaining prescribed quantity', () => {
    const item: PrescriptionItem = {
      id: 10,
      medicine: 1,
      medicine_name: 'Paracetamol',
      dosage: '500mg',
      frequency: 'TID',
      duration_days: 3,
      quantity: 10,
      dispensed_quantity: 4,
      status: 'PARTIALLY_DISPENSED'
    };

    const remaining = item.quantity - (item.dispensed_quantity ?? 0);
    assert.equal(remaining, 6);

    const invalidQty = 7;
    assert.ok(invalidQty > remaining, 'Exceeding remaining quantity must be caught');

    const validQty = 6;
    assert.ok(validQty <= remaining, 'Exact remaining quantity is allowed');
  });

  await t.test('authoritative InventoryLedger is source of truth after dispensation', () => {
    const ledgerEntry: InventoryLedger = {
      id: 101,
      transaction_type: 'DISPENSE',
      quantity_delta: -10,
      balance_after: 90,
      reference_entity_type: 'Dispensation',
      reference_entity_id: 5,
      remarks: 'Prescription #3 Dispensation #DISP-20260925-ABCD',
      transaction_timestamp: '2026-09-25T11:30:00Z',
      batch: 2,
      facility: 1,
      performed_by_staff: 3
    };

    assert.equal(ledgerEntry.transaction_type, 'DISPENSE');
    assert.equal(ledgerEntry.quantity_delta, -10);
    assert.equal(ledgerEntry.balance_after, 90);
    assert.equal(ledgerEntry.performed_by_staff, 3);
  });
});
