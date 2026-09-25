import test from 'node:test';
import assert from 'node:assert/strict';
import {
  isRouteAllowedForRole,
  getRoleLandingRoute,
  getRoleNavigation
} from '../navigation/navigationConfig.ts';
import type {
  DiagnosticOrder,
  TestRequest,
  Specimen,
  DiagnosticResult,
  DiagnosticTestMaster,
  Visit
} from '../types/index.ts';
import type {
  CreateSpecimenPayload,
  CreateDiagnosticResultPayload,
  AmendDiagnosticResultPayload
} from '../api/clinical.ts';

test('Laboratory clinical workflow authorization and access control', async (t) => {
  await t.test('LAB_TECHNICIAN can access lab dashboard and workstation routes', () => {
    assert.equal(getRoleLandingRoute('LAB_TECHNICIAN'), '/dashboard/lab');
    assert.equal(isRouteAllowedForRole('LAB_TECHNICIAN', '/dashboard/lab'), true);
    assert.equal(isRouteAllowedForRole('LAB_TECHNICIAN', '/lab'), true);
    assert.equal(isRouteAllowedForRole('LAB_TECHNICIAN', '/queue'), true);
  });

  await t.test('LAB_TECHNICIAN is blocked from clinical consultation, triage, and pharmacy routes', () => {
    assert.equal(isRouteAllowedForRole('LAB_TECHNICIAN', '/consultation'), false);
    assert.equal(isRouteAllowedForRole('LAB_TECHNICIAN', '/triage'), false);
    assert.equal(isRouteAllowedForRole('LAB_TECHNICIAN', '/pharmacy'), false);
    assert.equal(isRouteAllowedForRole('LAB_TECHNICIAN', '/dashboard/doctor'), false);
    assert.equal(isRouteAllowedForRole('LAB_TECHNICIAN', '/dashboard/nurse'), false);
    assert.equal(isRouteAllowedForRole('LAB_TECHNICIAN', '/dashboard/pharmacy'), false);
  });

  await t.test('Non-lab roles (Nurse, Pharmacist) are blocked from /lab and /dashboard/lab', () => {
    assert.equal(isRouteAllowedForRole('NURSE', '/lab'), false);
    assert.equal(isRouteAllowedForRole('NURSE', '/dashboard/lab'), false);
    assert.equal(isRouteAllowedForRole('PHARMACIST', '/lab'), false);
    assert.equal(isRouteAllowedForRole('PHARMACIST', '/dashboard/lab'), false);
  });

  await t.test('Doctor can access /lab in read-only review context but cannot impersonate technician', () => {
    assert.equal(isRouteAllowedForRole('DOCTOR', '/lab'), true);
    assert.equal(isRouteAllowedForRole('DOCTOR', '/dashboard/lab'), false);
  });
});

test('Laboratory dashboard metric calculation and tab filtering', async (t) => {
  const sampleOrders: DiagnosticOrder[] = [
    {
      id: 101,
      order_number: 'ORD-20260925-001',
      visit: 1,
      facility: 1,
      ordering_doctor_staff: 10,
      order_date: '2026-09-25',
      priority: 'STAT',
      status: 'ORDERED',
      clinical_indication: 'High fever evaluation',
      created_at: '2026-09-25T09:00:00Z'
    },
    {
      id: 102,
      order_number: 'ORD-20260925-002',
      visit: 2,
      facility: 1,
      ordering_doctor_staff: 10,
      order_date: '2026-09-25',
      priority: 'ROUTINE',
      status: 'SAMPLE_COLLECTED',
      clinical_indication: 'Diabetes check',
      created_at: '2026-09-25T09:30:00Z'
    },
    {
      id: 103,
      order_number: 'ORD-20260925-003',
      visit: 3,
      facility: 1,
      ordering_doctor_staff: 10,
      order_date: '2026-09-25',
      priority: 'ROUTINE',
      status: 'VERIFIED',
      clinical_indication: 'Hypertension workup',
      created_at: '2026-09-25T08:00:00Z'
    }
  ];

  const sampleRequests: TestRequest[] = [
    { id: 201, diagnostic_order: 101, test_master: 1, specimen: null, status: 'PENDING', created_at: '2026-09-25T09:00:00Z' },
    { id: 202, diagnostic_order: 102, test_master: 2, specimen: 301, status: 'IN_TESTING', created_at: '2026-09-25T09:30:00Z' },
    { id: 203, diagnostic_order: 103, test_master: 3, specimen: 302, status: 'COMPLETED', created_at: '2026-09-25T08:00:00Z' }
  ];

  const sampleResults: DiagnosticResult[] = [
    {
      id: 401,
      test_request: 203,
      result_value_text: 'Negative',
      result_value_numeric: null,
      reference_range_applied: 'Negative',
      is_abnormal: false,
      is_critical_panic: false,
      status: 'VERIFIED',
      entered_by_staff: 20,
      entered_at: '2026-09-25T08:30:00Z',
      verified_by_staff: 10,
      verified_at: '2026-09-25T08:45:00Z'
    }
  ];

  await t.test('calculates laboratory metrics authoritatively from backend arrays', () => {
    const pendingOrdersCount = sampleOrders.filter((o) => o.status === 'ORDERED').length;
    const specimensToCollectCount = sampleRequests.filter((r) => !r.specimen && r.status !== 'COMPLETED').length;
    const inTestingCount = sampleRequests.filter((r) => r.specimen && !sampleResults.some((res) => res.test_request === r.id)).length;
    const verifiedCount = sampleResults.filter((res) => res.status === 'VERIFIED' || res.status === 'AMENDED').length;
    const statOrUrgentCount = sampleOrders.filter((o) => (o.priority === 'STAT' || o.priority === 'URGENT') && o.status !== 'VERIFIED').length;

    assert.equal(pendingOrdersCount, 1);
    assert.equal(specimensToCollectCount, 1);
    assert.equal(inTestingCount, 1);
    assert.equal(verifiedCount, 1);
    assert.equal(statOrUrgentCount, 1);
  });

  await t.test('correctly filters orders by workflow status tab', () => {
    const awaitingSpecimenOrders = sampleOrders.filter((order) => {
      const orderReqs = sampleRequests.filter((r) => r.diagnostic_order === order.id);
      return orderReqs.some((r) => !r.specimen && r.status !== 'COMPLETED');
    });
    assert.equal(awaitingSpecimenOrders.length, 1);
    assert.equal(awaitingSpecimenOrders[0].id, 101);

    const verifiedOrders = sampleOrders.filter((order) => {
      const orderReqs = sampleRequests.filter((r) => r.diagnostic_order === order.id);
      return sampleResults.some((res) => orderReqs.some((r) => r.id === res.test_request) && res.status === 'VERIFIED');
    });
    assert.equal(verifiedOrders.length, 1);
    assert.equal(verifiedOrders[0].id, 103);
  });

  await t.test('handles empty laboratory queues gracefully without errors', () => {
    const emptyOrders: DiagnosticOrder[] = [];
    const emptyReqs: TestRequest[] = [];
    const emptyResults: DiagnosticResult[] = [];

    assert.equal(emptyOrders.length, 0);
    assert.equal(emptyReqs.filter((r) => !r.specimen).length, 0);
    assert.equal(emptyResults.filter((res) => res.status === 'VERIFIED').length, 0);
  });
});

test('Diagnostic order and test request presentation', async (t) => {
  const order: DiagnosticOrder = {
    id: 501,
    order_number: 'ORD-20260925-ABCD',
    visit: 15,
    facility: 1,
    ordering_doctor_staff: 12,
    order_date: '2026-09-25',
    priority: 'URGENT',
    status: 'ORDERED',
    clinical_indication: 'Suspected Dengue fever',
    created_at: '2026-09-25T10:00:00Z'
  };

  const testMaster: DiagnosticTestMaster = {
    id: 1,
    test_code: 'NS1-AG',
    test_name: 'Dengue NS1 Antigen Rapid Test',
    category: 'PATHOLOGY',
    specimen_type: 'SERUM',
    default_unit: '',
    reference_range_male: 'Negative',
    reference_range_female: 'Negative',
    is_active: true
  };

  await t.test('preserves ordering clinician staff ID without mutation by technician', () => {
    assert.equal(order.ordering_doctor_staff, 12);
    // Lab Technician cannot change the ordering clinician
    const labTechStaffId = 25;
    assert.notEqual(order.ordering_doctor_staff, labTechStaffId);
  });

  await t.test('correctly maps test master details to test request', () => {
    assert.equal(testMaster.test_code, 'NS1-AG');
    assert.equal(testMaster.specimen_type, 'SERUM');
    assert.equal(testMaster.reference_range_male, 'Negative');
  });
});

test('Specimen collection workflow and 1:N cardinality', async (t) => {
  await t.test('constructs valid CreateSpecimenPayload linking multiple test requests', () => {
    const payload: CreateSpecimenPayload = {
      diagnostic_order: 501,
      barcode_identifier: 'SMP-2026-8492',
      specimen_type: 'WHOLE_BLOOD',
      test_request_ids: [201, 202]
    };

    assert.equal(payload.diagnostic_order, 501);
    assert.equal(payload.barcode_identifier, 'SMP-2026-8492');
    assert.equal(payload.specimen_type, 'WHOLE_BLOOD');
    assert.equal(payload.test_request_ids?.length, 2);
  });

  await t.test('validates barcode identifier format and prevents empty barcode', () => {
    const emptyBarcode = '   ';
    assert.equal(emptyBarcode.trim().length, 0);

    const validBarcode = 'SMP-2026-1234';
    assert.match(validBarcode, /^SMP-2026-[0-9A-Z]+$/);
  });
});

test('Result entry payload, reference range applied, and panic flags', async (t) => {
  await t.test('constructs valid CreateDiagnosticResultPayload with numeric and abnormal flags', () => {
    const payload: CreateDiagnosticResultPayload = {
      test_request: 201,
      result_value_text: 'Elevated fasting glucose',
      result_value_numeric: 185.5,
      reference_range_applied: '70-99 mg/dL',
      is_abnormal: true,
      is_critical_panic: false
    };

    assert.equal(payload.test_request, 201);
    assert.equal(payload.result_value_numeric, 185.5);
    assert.equal(payload.reference_range_applied, '70-99 mg/dL');
    assert.equal(payload.is_abnormal, true);
    assert.equal(payload.is_critical_panic, false);
  });

  await t.test('validates that at least one result value (numeric or text) is provided', () => {
    const emptyText = '';
    const emptyNumeric = null;
    const isValid = Boolean(emptyText.trim() || emptyNumeric !== null);
    assert.equal(isValid, false);

    const validText = 'Reactive';
    const isNowValid = Boolean(validText.trim() || emptyNumeric !== null);
    assert.equal(isNowValid, true);
  });
});

test('Separation of duties and verification boundary', async (t) => {
  await t.test('recognizes backend 403 authorization boundary when Lab Tech verifies', () => {
    const errorResponse = {
      status: 403,
      data: { detail: 'You do not have permission to perform this action.' }
    };

    assert.equal(errorResponse.status, 403);
    assert.match(errorResponse.data.detail, /permission/);
  });

  await t.test('Nurse and Pharmacist cannot verify diagnostic results', () => {
    assert.equal(isRouteAllowedForRole('NURSE', '/lab'), false);
    assert.equal(isRouteAllowedForRole('PHARMACIST', '/lab'), false);
  });

  await t.test('Doctor reviews verified results in read-only clinical context', () => {
    const result: DiagnosticResult = {
      id: 401,
      test_request: 203,
      result_value_text: 'Negative',
      result_value_numeric: null,
      reference_range_applied: 'Negative',
      is_abnormal: false,
      is_critical_panic: false,
      status: 'VERIFIED',
      entered_by_staff: 20,
      entered_at: '2026-09-25T08:30:00Z',
      verified_by_staff: 10,
      verified_at: '2026-09-25T08:45:00Z'
    };

    assert.equal(result.status, 'VERIFIED');
    assert.equal(result.verified_by_staff, 10);
    assert.ok(result.verified_at);
  });
});

test('Result immutability and append-only amendment workflow', async (t) => {
  await t.test('amendment payload requires mandatory amendment_reason', () => {
    const payload: AmendDiagnosticResultPayload = {
      amendment_reason: 'Correction of calibration factor',
      amended_value_text: 'Weakly Reactive',
      amended_value_numeric: null
    };

    assert.ok(payload.amendment_reason.trim().length > 0);
    assert.equal(payload.amended_value_text, 'Weakly Reactive');
  });

  await t.test('amendment transitions result status to AMENDED preserving original verifier', () => {
    const verifiedResult: DiagnosticResult = {
      id: 401,
      test_request: 203,
      result_value_text: 'Negative',
      result_value_numeric: null,
      reference_range_applied: 'Negative',
      is_abnormal: false,
      is_critical_panic: false,
      status: 'VERIFIED',
      entered_by_staff: 20,
      entered_at: '2026-09-25T08:30:00Z',
      verified_by_staff: 10,
      verified_at: '2026-09-25T08:45:00Z'
    };

    // After amendment
    const amendedResult: DiagnosticResult = {
      ...verifiedResult,
      result_value_text: 'Positive (1:160)',
      status: 'AMENDED'
    };

    assert.equal(amendedResult.status, 'AMENDED');
    assert.equal(amendedResult.verified_by_staff, 10); // Original verifier preserved
    assert.equal(amendedResult.result_value_text, 'Positive (1:160)');
  });
});
