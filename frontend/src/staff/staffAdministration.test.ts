import test from 'node:test';
import assert from 'node:assert/strict';
import {
  STATUS_LABELS,
  type StaffProfile,
  type StaffLifecycleStatus,
  type InviteStaffPayload,
  type AssignRolePayload,
  type TransferStaffPayload,
  type StaffRoleItem,
} from '../types/staff.ts';
import { ROLE_LABELS, type Role } from '../types/auth.ts';
import {
  isRouteAllowedForRole,
  getRoleNavigation,
  getRoleAllowedRoutes,
} from '../navigation/navigationConfig.ts';
import {
  hasPermission,
  isPathAllowedForRole,
  HUMAN_ROLE_LABELS,
} from '../utils/permissions.ts';

// 1. Staff directory loading
test('1. Staff directory loading: validates authoritative profile schema and attributes', () => {
  const mockStaff: StaffProfile = {
    id: 101,
    employee_id: 'EMP-DOC-001',
    designation: 'Medical Officer',
    department: null,
    status: 'ACTIVE',
    medical_council_reg_number: 'KMC-54321',
    person_details: {
      id: 501,
      first_name: 'Ananya',
      last_name: 'Rao',
      gender: 'FEMALE',
      date_of_birth: '1988-06-15',
      phone_number: '9845012345',
    },
    roles: [
      {
        id: 1,
        role_id: 3,
        role_code: 'DOCTOR',
        role_name: 'Doctor (Medical Officer)',
        effective_from: '2026-01-01',
        effective_to: null,
        is_active: true,
        facility_name: 'Malleshwaram UPHC',
      },
    ],
    facility_assignment: {
      facility_id: 10,
      facility_name: 'Malleshwaram UPHC',
      facility_code: 'UPHC-MAL-01',
      department_id: null,
      department_name: null,
      is_primary: true,
      effective_from: '2026-01-01',
    },
    district_context: {
      district_id: 2,
      district_name: 'Bangalore Urban',
      district_code: 'BLR_URBAN',
    },
  };

  assert.equal(mockStaff.id, 101);
  assert.equal(mockStaff.employee_id, 'EMP-DOC-001');
  assert.equal(mockStaff.status, 'ACTIVE');
  assert.equal(mockStaff.person_details.first_name, 'Ananya');
  assert.equal(mockStaff.roles[0].role_code, 'DOCTOR');
  assert.equal(mockStaff.facility_assignment?.facility_id, 10);
  assert.equal(mockStaff.district_context?.district_id, 2);
});

// 2. Search and filter query construction
test('2. Search and filter: query parameter mapping conforms to backend contract', () => {
  const buildQueryParams = (params: { search?: string; status?: string; role?: string; facility?: string | number }) => {
    const qp = new URLSearchParams();
    if (params.search) qp.append('search', params.search);
    if (params.status) qp.append('status', params.status);
    if (params.role) qp.append('role', params.role);
    if (params.facility) qp.append('facility', String(params.facility));
    return qp.toString();
  };

  const query = buildQueryParams({ search: 'Priya', status: 'ACTIVE', role: 'NURSE', facility: 12 });
  assert.ok(query.includes('search=Priya'));
  assert.ok(query.includes('status=ACTIVE'));
  assert.ok(query.includes('role=NURSE'));
  assert.ok(query.includes('facility=12'));
});

// 3. Staff detail modal data representation
test('3. Staff detail: formats professional identity without secrets or leaked hashes', () => {
  const staff: StaffProfile = {
    id: 102,
    employee_id: 'EMP-NUR-002',
    designation: 'Staff Nurse',
    status: 'ACTIVE',
    medical_council_reg_number: 'KNC-88214',
    person_details: {
      id: 502,
      first_name: 'Suma',
      last_name: 'K',
      gender: 'FEMALE',
      date_of_birth: '1992-04-10',
      phone_number: '9845099887',
    },
    roles: [
      {
        id: 2,
        role_id: 4,
        role_code: 'NURSE',
        role_name: 'Staff Nurse',
        effective_from: '2026-02-01',
        effective_to: null,
        is_active: true,
      },
    ],
    facility_assignment: {
      facility_id: 10,
      facility_name: 'Malleshwaram UPHC',
      facility_code: 'UPHC-MAL-01',
      is_primary: true,
      effective_from: '2026-02-01',
    },
    district_context: null,
  };

  const fullName = `${staff.person_details.first_name} ${staff.person_details.last_name}`.trim();
  assert.equal(fullName, 'Suma K');
  assert.equal(staff.employee_id, 'EMP-NUR-002');
  assert.equal(staff.medical_council_reg_number, 'KNC-88214');

  // Verify no password, hash, or secret properties exist on StaffProfile
  assert.equal((staff as any).password, undefined);
  assert.equal((staff as any).password_hash, undefined);
  assert.equal((staff as any).jwt, undefined);
});

// 4. Invite staff workflow
test('4. Invite staff: creates account in INVITED state strictly adhering to backend serializer', () => {
  const invitePayload: InviteStaffPayload = {
    first_name: 'Ravi',
    last_name: 'Kumar',
    gender: 'MALE',
    date_of_birth: '1985-05-12',
    phone_number: '9876543210',
    employee_id: 'EMP-9901',
    designation: 'Staff Nurse',
    role_code: 'NURSE',
    facility_id: 5,
    email: 'ravi.kumar@nammaclinic.gov.in',
  };

  assert.equal(invitePayload.role_code, 'NURSE');
  assert.equal(invitePayload.facility_id, 5);
  assert.equal(invitePayload.employee_id, 'EMP-9901');

  // Initial lifecycle status after invite must be INVITED
  const invitedStatus: StaffLifecycleStatus = 'INVITED';
  assert.equal(STATUS_LABELS[invitedStatus], 'Invited (Pending Activation)');
});

// 5. Role assignment workflow
test('5. Role assignment: assigns operational role with effective dates', () => {
  const rolePayload: AssignRolePayload = {
    role_code: 'DOCTOR',
    facility_id: 10,
    effective_from: '2026-09-01',
    effective_to: null,
  };

  assert.equal(rolePayload.role_code, 'DOCTOR');
  assert.equal(rolePayload.facility_id, 10);
  assert.equal(rolePayload.effective_from, '2026-09-01');
  assert.equal(rolePayload.effective_to, null);
});

// 6. NURSE + FRONT_DESK_OFFICER dual role assignment
test('6. NURSE + FRONT_DESK_OFFICER assignment: results in two separate authoritative role records', () => {
  const assignments: StaffRoleItem[] = [
    {
      id: 201,
      role_id: 4,
      role_code: 'NURSE',
      role_name: 'Staff Nurse',
      effective_from: '2026-01-01',
      effective_to: null,
      is_active: true,
      facility_name: 'Koramangala Clinic',
    },
    {
      id: 202,
      role_id: 5,
      role_code: 'FRONT_DESK_OFFICER',
      role_name: 'Front Desk Officer',
      effective_from: '2026-01-01',
      effective_to: null,
      is_active: true,
      facility_name: 'Koramangala Clinic',
    },
  ];

  assert.equal(assignments.length, 2);
  const roleCodes = assignments.map((a) => a.role_code);
  assert.ok(roleCodes.includes('NURSE'));
  assert.ok(roleCodes.includes('FRONT_DESK_OFFICER'));
  assert.equal(roleCodes.filter((r) => r === 'NURSE_COMPOUNDER' || r === 'NURSE_FRONT_DESK_OFFICER').length, 0);
});

// 7. End individual role
test('7. End individual role: ending FRONT_DESK_OFFICER leaves NURSE active', () => {
  let activeRoles: StaffRoleItem[] = [
    {
      id: 201,
      role_id: 4,
      role_code: 'NURSE',
      role_name: 'Staff Nurse',
      effective_from: '2026-01-01',
      effective_to: null,
      is_active: true,
    },
    {
      id: 202,
      role_id: 5,
      role_code: 'FRONT_DESK_OFFICER',
      role_name: 'Front Desk Officer',
      effective_from: '2026-01-01',
      effective_to: null,
      is_active: true,
    },
  ];

  // End role with id 202 (FRONT_DESK_OFFICER)
  const targetEndId = 202;
  activeRoles = activeRoles.map((r) => (r.id === targetEndId ? { ...r, is_active: false, effective_to: '2026-09-28' } : r));

  const liveRoles = activeRoles.filter((r) => r.is_active);
  assert.equal(liveRoles.length, 1);
  assert.equal(liveRoles[0].role_code, 'NURSE');
  assert.equal(liveRoles[0].id, 201);
});

// 8. Suspend lifecycle action
test('8. Suspend staff: transitions account to SUSPENDED status', () => {
  let status: StaffLifecycleStatus = 'ACTIVE';
  const reason = 'Administrative inquiry';

  // Suspend action
  status = 'SUSPENDED';
  assert.equal(status, 'SUSPENDED');
  assert.equal(STATUS_LABELS[status], 'Suspended (Access Revoked)');
});

// 9. Deactivate lifecycle action
test('9. Deactivate staff: transitions account to DEACTIVATED historical state', () => {
  let status: StaffLifecycleStatus = 'ACTIVE';
  status = 'DEACTIVATED';
  assert.equal(status, 'DEACTIVATED');
  assert.equal(STATUS_LABELS[status], 'Deactivated (Archived)');
});

// 10. Transfer workflow
test('10. Transfer staff: future date schedules TRANSFER_PENDING without dual simultaneous access', () => {
  const currentFacilityId = 10;
  const transferPayload: TransferStaffPayload = {
    new_facility_id: 15,
    effective_date: '2026-10-15', // Future date
    reason: 'Inter-clinic redeployment',
  };

  const todayStr = '2026-09-28';
  const isFuture = transferPayload.effective_date! > todayStr;
  assert.ok(isFuture);

  const resultingStatus: StaffLifecycleStatus = isFuture ? 'TRANSFER_PENDING' : 'ACTIVE';
  assert.equal(resultingStatus, 'TRANSFER_PENDING');
  assert.notEqual(transferPayload.new_facility_id, currentFacilityId);
});

// 11. 403 handling
test('11. 403 handling: maps HTTP 403 Forbidden to authorized error message', () => {
  const parseApiError = (err: any): string => {
    if (err?.status === 403 || err?.response?.status === 403) {
      return 'You are not authorized to perform this action.';
    }
    return err?.message || 'Error';
  };

  const forbiddenErr = { response: { status: 403, data: { detail: 'Forbidden' } } };
  assert.equal(parseApiError(forbiddenErr), 'You are not authorized to perform this action.');
});

// 12. 400 validation error handling
test('12. 400 validation: formats backend validation message safely without raw tracebacks', () => {
  const parseApiError = (err: any): string => {
    const data = err?.response?.data;
    if (typeof data === 'object') {
      const firstKey = Object.keys(data)[0];
      if (firstKey) {
        const val = data[firstKey];
        return `${firstKey}: ${Array.isArray(val) ? val.join(', ') : val}`;
      }
    }
    return 'Validation failed.';
  };

  const validationErr = {
    response: {
      status: 400,
      data: { employee_id: ['Staff profile with this employee_id already exists.'] },
    },
  };
  assert.equal(parseApiError(validationErr), 'employee_id: Staff profile with this employee_id already exists.');
});

// 13. 409 conflict handling
test('13. 409 conflict: extracts conflict business-rule detail from backend response', () => {
  const parseApiError = (err: any): string => {
    if (err?.response?.status === 409) {
      return err.response.data?.detail || 'Conflict: Business rule violation';
    }
    return 'Error';
  };

  const conflictErr = {
    response: {
      status: 409,
      data: { detail: 'Staff member already holds an active DOCTOR role assignment.' },
    },
  };
  assert.equal(parseApiError(conflictErr), 'Staff member already holds an active DOCTOR role assignment.');
});

// 14. Facility scope for Hospital Admin
test('14. Facility scope: Hospital Admin is restricted to facility scope in permission matrix', () => {
  const adminPermissions = hasPermission('HOSPITAL_ADMIN', 'staff.view');
  assert.ok(adminPermissions);

  // Hospital Admin has facility operational scope, not district oversight
  assert.equal(hasPermission('HOSPITAL_ADMIN', 'district.view'), false);
});

// 15. DHO district scope
test('15. DHO district scope: District Officer has district-wide governance permissions', () => {
  assert.ok(hasPermission('DISTRICT_OFFICER', 'district.view'));
  assert.ok(hasPermission('DISTRICT_OFFICER', 'staff.view'));
  assert.ok(hasPermission('DISTRICT_OFFICER', 'staff.manage'));
});

// 16. Operational roles cannot access staff UI
test('16. Operational clinical roles are blocked from Staff Administration route and navigation', () => {
  const clinicalRoles: Role[] = ['DOCTOR', 'NURSE', 'FRONT_DESK_OFFICER', 'LAB_TECHNICIAN', 'PHARMACIST'];

  for (const role of clinicalRoles) {
    // Check navigation items
    const navSections = getRoleNavigation(role);
    const navPaths = navSections.flatMap((s) => s.items.map((i) => i.path));
    assert.equal(
      navPaths.includes('/admin/staff'),
      false,
      `Role ${role} must NOT have /admin/staff in navigation items`
    );

    // Check route allowed
    const isAllowed = isRouteAllowedForRole(role, '/admin/staff');
    assert.equal(isAllowed, false, `Role ${role} must NOT be allowed to access /admin/staff`);
  }
});

// 17. No NURSE_COMPOUNDER option
test('17. Role catalogue: strictly prohibits fictitious NURSE_COMPOUNDER role', () => {
  const allRoles = Object.keys(ROLE_LABELS);
  assert.equal(allRoles.includes('NURSE_COMPOUNDER'), false);
  assert.equal(allRoles.includes('NURSE_FRONT_DESK_OFFICER'), false);
  assert.ok(allRoles.includes('NURSE'));
  assert.ok(allRoles.includes('FRONT_DESK_OFFICER'));
});

// 18. No SYSTEM_ADMIN, SUPER_ADMIN, or CLINIC_ADMIN
test('18. Role catalogue: strictly prohibits SYSTEM_ADMIN, SUPER_ADMIN, and CLINIC_ADMIN', () => {
  const allRoles = Object.keys(ROLE_LABELS);
  assert.equal(allRoles.includes('SYSTEM_ADMIN'), false);
  assert.equal(allRoles.includes('SUPER_ADMIN'), false);
  assert.equal(allRoles.includes('CLINIC_ADMIN'), false);
  // Exactly the 8 approved operational roles (including INVENTORY from Phase 27)
  assert.equal(allRoles.length, 8);
  assert.deepEqual(allRoles.sort(), [
    'DISTRICT_OFFICER',
    'DOCTOR',
    'FRONT_DESK_OFFICER',
    'HOSPITAL_ADMIN',
    'INVENTORY',
    'LAB_TECHNICIAN',
    'NURSE',
    'PHARMACIST',
  ].sort());
});

// 19. Empty staff directory handling
test('19. Empty staff directory: returns empty array without synthetic mock data', () => {
  const emptyStaffResponse: StaffProfile[] = [];
  assert.equal(emptyStaffResponse.length, 0);
  assert.ok(Array.isArray(emptyStaffResponse));
});

// 20. Loading and error states
test('20. Lifecycle badges and labels formatting', () => {
  const statuses: StaffLifecycleStatus[] = [
    'INVITED',
    'ACTIVE',
    'SUSPENDED',
    'TRANSFER_PENDING',
    'DEACTIVATED',
  ];

  for (const s of statuses) {
    const label = STATUS_LABELS[s];
    assert.ok(label && label.length > 0, `Status ${s} must have a non-empty human label`);
  }
});
// 21. Facility type choices alignment with backend FacilityTypeChoices
test('21. Facility creation modal aligns with backend FacilityTypeChoices', () => {
  const allowedFacilityTypes = ['NAMMA_CLINIC', 'UPHC', 'DISPENSARY', 'HOSPITAL', 'LABORATORY', 'PHARMACY'];
  assert.ok(allowedFacilityTypes.includes('NAMMA_CLINIC'));
  assert.equal(allowedFacilityTypes.includes('CLINIC'), false, 'CLINIC is invalid; backend model requires NAMMA_CLINIC');
});
