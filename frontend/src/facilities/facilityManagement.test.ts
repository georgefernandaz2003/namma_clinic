import test from 'node:test';
import assert from 'node:assert/strict';
import type { Facility, FacilityType } from '../types/index.ts';
import type { UserProfile, Role } from '../types/auth.ts';

// Helper matching DHO authority check in Facilities page
function isDHOUser(user: Partial<UserProfile> | null): boolean {
  if (!user) return false;
  return Boolean(
    user.role === 'DISTRICT_OFFICER' ||
    user.roles?.includes('DISTRICT_OFFICER') ||
    user.is_superuser
  );
}

// Helper validating facility payload
function validateFacilityPayload(payload: Partial<Facility>): { valid: boolean; error?: string } {
  if (!payload.facility_name?.trim()) {
    return { valid: false, error: 'Facility Name is required.' };
  }
  if (!payload.facility_code?.trim()) {
    return { valid: false, error: 'Facility Code is required.' };
  }
  if (!payload.facility_type) {
    return { valid: false, error: 'Facility Type is required.' };
  }
  if (payload.status && !['ACTIVE', 'INACTIVE'].includes(payload.status)) {
    return { valid: false, error: "Facility status must be 'ACTIVE' or 'INACTIVE'." };
  }
  return { valid: true };
}

test('1. DHO role detection: DISTRICT_OFFICER is authorized for facility management', () => {
  const dhoUser: Partial<UserProfile> = {
    id: 1,
    role: 'DISTRICT_OFFICER',
    assigned_district: 1,
    district_name: 'Bengaluru Urban',
  };
  assert.equal(isDHOUser(dhoUser), true);
});

test('2. Multi-role assignment: User with secondary DISTRICT_OFFICER role is authorized', () => {
  const multiRoleUser: Partial<UserProfile> = {
    id: 2,
    role: 'DOCTOR',
    roles: ['DOCTOR', 'DISTRICT_OFFICER'],
    assigned_district: 1,
  };
  assert.equal(isDHOUser(multiRoleUser), true);
});

test('3. Superuser override: Superuser has facility administration authority', () => {
  const superuser: Partial<UserProfile> = {
    id: 99,
    role: 'HOSPITAL_ADMIN',
    is_superuser: true,
  };
  assert.equal(isDHOUser(superuser), true);
});

test('4. Hospital Admin role is restricted from facility management actions', () => {
  const adminUser: Partial<UserProfile> = {
    id: 3,
    role: 'HOSPITAL_ADMIN',
    roles: ['HOSPITAL_ADMIN'],
    assigned_facility: 1,
    is_superuser: false,
  };
  assert.equal(isDHOUser(adminUser), false);
});

test('5. Clinical and Operational roles are strictly restricted from facility creation/editing', () => {
  const nonDhoRoles: Role[] = [
    'DOCTOR',
    'NURSE',
    'FRONT_DESK_OFFICER',
    'LAB_TECHNICIAN',
    'PHARMACIST',
    'INVENTORY',
  ];

  for (const role of nonDhoRoles) {
    const user: Partial<UserProfile> = {
      id: 10,
      role,
      roles: [role],
      assigned_facility: 1,
      is_superuser: false,
    };
    assert.equal(isDHOUser(user), false, `Role ${role} should not have DHO facility governance`);
  }
});

test('6. Null or unauthenticated user is rejected', () => {
  assert.equal(isDHOUser(null), false);
  assert.equal(isDHOUser(undefined as any), false);
});

test('7. Facility payload validation: valid payload passes', () => {
  const validPayload: Partial<Facility> = {
    facility_name: 'Namma Clinic - Ward 101 Indiranagar',
    facility_code: 'NC-BLR-101',
    facility_type: 'NAMMA_CLINIC',
    status: 'ACTIVE',
    district: 1,
  };
  const result = validateFacilityPayload(validPayload);
  assert.equal(result.valid, true);
  assert.equal(result.error, undefined);
});

test('8. Facility payload validation: rejects missing facility name', () => {
  const invalidPayload: Partial<Facility> = {
    facility_name: '',
    facility_code: 'NC-BLR-101',
    facility_type: 'NAMMA_CLINIC',
  };
  const result = validateFacilityPayload(invalidPayload);
  assert.equal(result.valid, false);
  assert.match(result.error || '', /Facility Name is required/);
});

test('9. Facility payload validation: rejects missing facility code', () => {
  const invalidPayload: Partial<Facility> = {
    facility_name: 'Namma Clinic',
    facility_code: '   ',
    facility_type: 'NAMMA_CLINIC',
  };
  const result = validateFacilityPayload(invalidPayload);
  assert.equal(result.valid, false);
  assert.match(result.error || '', /Facility Code is required/);
});

test('10. Facility status management: allows valid ACTIVE and INACTIVE states', () => {
  const activePayload: Partial<Facility> = {
    facility_name: 'Namma Clinic',
    facility_code: 'NC-BLR-101',
    facility_type: 'NAMMA_CLINIC',
    status: 'ACTIVE',
  };
  assert.equal(validateFacilityPayload(activePayload).valid, true);

  const inactivePayload: Partial<Facility> = {
    facility_name: 'Namma Clinic',
    facility_code: 'NC-BLR-101',
    facility_type: 'NAMMA_CLINIC',
    status: 'INACTIVE',
  };
  assert.equal(validateFacilityPayload(inactivePayload).valid, true);
});

test('11. Facility status management: rejects invalid status string', () => {
  const invalidPayload: Partial<Facility> = {
    facility_name: 'Namma Clinic',
    facility_code: 'NC-BLR-101',
    facility_type: 'NAMMA_CLINIC',
    status: 'PENDING_APPROVAL',
  };
  const result = validateFacilityPayload(invalidPayload);
  assert.equal(result.valid, false);
  assert.match(result.error || '', /ACTIVE.*INACTIVE/);
});
