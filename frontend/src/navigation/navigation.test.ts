import test from 'node:test';
import assert from 'node:assert/strict';
import {
  ROLE_DASHBOARD_ROUTES,
  getRoleLandingRoute,
  getRoleNavigation,
  getRoleAllowedRoutes,
  isRouteAllowedForRole,
  formatScopeDisplay,
} from './navigationConfig.ts';
import type { Role } from '../types/auth.ts';

const ALL_SIX_ROLES: Role[] = [
  'DISTRICT_OFFICER',
  'HOSPITAL_ADMIN',
  'DOCTOR',
  'NURSE',
  'LAB_TECHNICIAN',
  'PHARMACIST',
];

test('1. Role -> landing route mapping', async (t) => {
  await t.test('all six roles map to correct dedicated dashboard routes', () => {
    assert.equal(getRoleLandingRoute('DISTRICT_OFFICER'), '/dashboard/district');
    assert.equal(getRoleLandingRoute('HOSPITAL_ADMIN'), '/dashboard/admin');
    assert.equal(getRoleLandingRoute('DOCTOR'), '/dashboard/doctor');
    assert.equal(getRoleLandingRoute('NURSE'), '/dashboard/nurse');
    assert.equal(getRoleLandingRoute('LAB_TECHNICIAN'), '/dashboard/lab');
    assert.equal(getRoleLandingRoute('PHARMACIST'), '/dashboard/pharmacy');
  });

  await t.test('unauthenticated or null role maps to /login', () => {
    assert.equal(getRoleLandingRoute(null), '/login');
    assert.equal(getRoleLandingRoute(undefined), '/login');
    assert.equal(getRoleLandingRoute('UNKNOWN_ROLE' as any), '/login');
  });
});

test('2. Navigation visibility by role', async (t) => {
  for (const role of ALL_SIX_ROLES) {
    await t.test(`navigation items are populated for ${role}`, () => {
      const sections = getRoleNavigation(role);
      assert.ok(sections.length > 0, `Role ${role} must have at least one nav section`);

      const allItems = sections.flatMap((s) => s.items);
      assert.ok(allItems.length >= 2, `Role ${role} must have at least 2 nav items`);

      // Landing route must be in the navigation items
      const hasLanding = allItems.some((item) => item.path === ROLE_DASHBOARD_ROUTES[role]);
      assert.ok(hasLanding, `Role ${role} must have its landing route in navigation`);
    });
  }

  await t.test('DOCTOR has clinical consultation and diagnostic orders in nav', () => {
    const docItems = getRoleNavigation('DOCTOR').flatMap((s) => s.items);
    assert.ok(docItems.some((i) => i.path === '/consultation'));
    assert.ok(docItems.some((i) => i.path === '/lab'));
    assert.ok(docItems.some((i) => i.path === '/patients'));
  });

  await t.test('NURSE has triage and follow-up in nav', () => {
    const nurseItems = getRoleNavigation('NURSE').flatMap((s) => s.items);
    assert.ok(nurseItems.some((i) => i.path === '/triage'));
    assert.ok(nurseItems.some((i) => i.path === '/patients'));
    assert.ok(nurseItems.some((i) => i.path === '/outreach'));
  });

  await t.test('PHARMACIST has pharmacy and drug ledger in nav', () => {
    const pharmItems = getRoleNavigation('PHARMACIST').flatMap((s) => s.items);
    assert.ok(pharmItems.some((i) => i.path === '/pharmacy'));
    assert.ok(pharmItems.some((i) => i.path === '/queue'));
  });

  await t.test('LAB_TECHNICIAN has diagnostics lab in nav', () => {
    const labItems = getRoleNavigation('LAB_TECHNICIAN').flatMap((s) => s.items);
    assert.ok(labItems.some((i) => i.path === '/lab'));
    assert.ok(labItems.some((i) => i.path === '/queue'));
  });

  await t.test('HOSPITAL_ADMIN has facility operations and ARS in nav', () => {
    const adminItems = getRoleNavigation('HOSPITAL_ADMIN').flatMap((s) => s.items);
    assert.ok(adminItems.some((i) => i.path === '/facilities'));
    assert.ok(adminItems.some((i) => i.path === '/ars'));
    assert.ok(adminItems.some((i) => i.path === '/quality'));
  });

  await t.test('DISTRICT_OFFICER has district oversight, compliance, and audit in nav', () => {
    const distItems = getRoleNavigation('DISTRICT_OFFICER').flatMap((s) => s.items);
    assert.ok(distItems.some((i) => i.path === '/network'));
    assert.ok(distItems.some((i) => i.path === '/compliance'));
    assert.ok(distItems.some((i) => i.path === '/audit'));
    assert.ok(distItems.some((i) => i.path === '/surveillance'));
  });
});

test('3. Unauthorized route handling (role guard blocks mismatch)', async (t) => {
  await t.test('DOCTOR is blocked from admin, district, and compliance routes', () => {
    assert.equal(isRouteAllowedForRole('DOCTOR', '/dashboard/admin'), false);
    assert.equal(isRouteAllowedForRole('DOCTOR', '/dashboard/district'), false);
    assert.equal(isRouteAllowedForRole('DOCTOR', '/compliance'), false);
    assert.equal(isRouteAllowedForRole('DOCTOR', '/audit'), false);
    assert.equal(isRouteAllowedForRole('DOCTOR', '/ars'), false);
  });

  await t.test('NURSE is blocked from doctor consultation and admin routes', () => {
    assert.equal(isRouteAllowedForRole('NURSE', '/dashboard/doctor'), false);
    assert.equal(isRouteAllowedForRole('NURSE', '/consultation'), false);
    assert.equal(isRouteAllowedForRole('NURSE', '/compliance'), false);
    assert.equal(isRouteAllowedForRole('NURSE', '/audit'), false);
  });

  await t.test('LAB_TECHNICIAN is blocked from pharmacy, consultation, and triage', () => {
    assert.equal(isRouteAllowedForRole('LAB_TECHNICIAN', '/dashboard/pharmacy'), false);
    assert.equal(isRouteAllowedForRole('LAB_TECHNICIAN', '/consultation'), false);
    assert.equal(isRouteAllowedForRole('LAB_TECHNICIAN', '/triage'), false);
    assert.equal(isRouteAllowedForRole('LAB_TECHNICIAN', '/pharmacy'), false);
  });

  await t.test('PHARMACIST is blocked from doctor consultation, triage, and lab', () => {
    assert.equal(isRouteAllowedForRole('PHARMACIST', '/dashboard/doctor'), false);
    assert.equal(isRouteAllowedForRole('PHARMACIST', '/consultation'), false);
    assert.equal(isRouteAllowedForRole('PHARMACIST', '/triage'), false);
    assert.equal(isRouteAllowedForRole('PHARMACIST', '/lab'), false);
  });

  await t.test('HOSPITAL_ADMIN is blocked from direct clinical examine routes', () => {
    assert.equal(isRouteAllowedForRole('HOSPITAL_ADMIN', '/consultation'), false);
    assert.equal(isRouteAllowedForRole('HOSPITAL_ADMIN', '/triage'), false);
    assert.equal(isRouteAllowedForRole('HOSPITAL_ADMIN', '/dashboard/district'), false);
  });

  await t.test('cross-dashboard isolation: each role can only access its own dashboard', () => {
    for (const r1 of ALL_SIX_ROLES) {
      for (const r2 of ALL_SIX_ROLES) {
        const dest = ROLE_DASHBOARD_ROUTES[r2];
        if (r1 === r2) {
          assert.equal(isRouteAllowedForRole(r1, dest), true, `${r1} should access ${dest}`);
        } else {
          assert.equal(isRouteAllowedForRole(r1, dest), false, `${r1} must be blocked from ${dest}`);
        }
      }
    }
  });
});

test('4. Authenticated route handling', async (t) => {
  await t.test('all authenticated roles can access root and generic dashboard', () => {
    for (const role of ALL_SIX_ROLES) {
      assert.equal(isRouteAllowedForRole(role, '/'), true);
      assert.equal(isRouteAllowedForRole(role, '/dashboard'), true);
    }
  });

  await t.test('unauthenticated users (null/undefined) are blocked from all routes', () => {
    assert.equal(isRouteAllowedForRole(null, '/'), false);
    assert.equal(isRouteAllowedForRole(null, '/dashboard'), false);
    assert.equal(isRouteAllowedForRole(null, '/dashboard/doctor'), false);
    assert.equal(isRouteAllowedForRole(undefined, '/patients'), false);
  });
});

test('5. Facility/scope context formatting', async (t) => {
  await t.test('formats district oversight scope correctly', () => {
    const scope = formatScopeDisplay('DISTRICT', null, null, 'Bengaluru Urban');
    assert.equal(scope.isDistrict, true);
    assert.equal(scope.label, 'District Oversight Scope');
    assert.equal(scope.details, 'Bengaluru Urban Health Administration');
  });

  await t.test('formats facility operational scope with code and name', () => {
    const scope = formatScopeDisplay(
      'FACILITY',
      'Namma Clinic Local PHC',
      'PHC-LOCAL-01',
      'Bengaluru Urban'
    );
    assert.equal(scope.isDistrict, false);
    assert.equal(scope.label, 'Facility Operational Scope');
    assert.equal(scope.details, 'Namma Clinic Local PHC [PHC-LOCAL-01]');
  });

  await t.test('safely handles missing facility information without crashing', () => {
    const scope = formatScopeDisplay(undefined, null, null, null);
    assert.equal(scope.isDistrict, false);
    assert.equal(scope.label, 'Unassigned Scope');
    assert.equal(scope.details, 'No facility or district assigned');
  });
});

test('6. Fallback and unsupported roles handling', async (t) => {
  await t.test('no navigation returned for unsupported roles', () => {
    assert.deepEqual(getRoleNavigation('INVALID_ROLE' as any), []);
    assert.deepEqual(getRoleNavigation(null), []);
    assert.deepEqual(getRoleNavigation(undefined), []);
  });

  await t.test('no allowed routes returned for unsupported roles', () => {
    assert.deepEqual(getRoleAllowedRoutes('INVALID_ROLE' as any), []);
    assert.deepEqual(getRoleAllowedRoutes(null), []);
  });
});
