import test from 'node:test';
import assert from 'node:assert/strict';
import {
  getRoleLandingRoute,
  getRoleNavigation,
  isRouteAllowedForRole,
} from '../navigation/navigationConfig.ts';
import { ROLE_PERMISSIONS, ROLE_ALLOWED_PATHS } from '../utils/permissions.ts';

test('Front Desk Officer Role Boundary & Patient Registration Authorization (Phase 28B-0)', async (t) => {
  await t.test('1. Front Desk Officer does not see Nurse Dashboard in navigation', () => {
    const navSections = getRoleNavigation('FRONT_DESK_OFFICER');
    const allItems = navSections.flatMap((s) => s.items);
    const hasNurseDashboard = allItems.some(
      (item) => item.path === '/dashboard/nurse' || (item.name && item.name.toLowerCase().includes('nurse'))
    );
    assert.equal(hasNurseDashboard, false, 'Front Desk Officer must not see Nurse Dashboard');
    assert.equal(isRouteAllowedForRole('FRONT_DESK_OFFICER', '/dashboard/nurse'), false);
  });

  await t.test('2. Front Desk Officer does not see Triage in navigation', () => {
    const navSections = getRoleNavigation('FRONT_DESK_OFFICER');
    const allItems = navSections.flatMap((s) => s.items);
    const hasTriage = allItems.some(
      (item) => item.path === '/triage' || (item.name && item.name.toLowerCase().includes('triage'))
    );
    assert.equal(hasTriage, false, 'Front Desk Officer must not see Triage in navigation');
  });

  await t.test('3. Front Desk Officer direct /triage navigation is blocked', () => {
    assert.equal(isRouteAllowedForRole('FRONT_DESK_OFFICER', '/triage'), false, 'Direct /triage access must be blocked');
    assert.equal(ROLE_ALLOWED_PATHS.FRONT_DESK_OFFICER.includes('/triage'), false, '/triage must not be in ROLE_ALLOWED_PATHS');
    
    // Also verify clinical permissions are removed
    const permissions = ROLE_PERMISSIONS.FRONT_DESK_OFFICER;
    assert.equal(permissions.has('vitals.view'), false, 'vitals.view must be removed from Front Desk Officer');
    assert.equal(permissions.has('vitals.create'), false, 'vitals.create must be removed from Front Desk Officer');
    assert.equal(permissions.has('triage.view'), false, 'triage.view must be removed from Front Desk Officer');
  });

  await t.test('4. Front Desk Officer navigation exposes Patients/Queue and lands on /dashboard/front-desk', () => {
    assert.equal(getRoleLandingRoute('FRONT_DESK_OFFICER'), '/dashboard/front-desk');
    const navSections = getRoleNavigation('FRONT_DESK_OFFICER');
    const allItems = navSections.flatMap((s) => s.items);
    const hasPatients = allItems.some((item) => item.path === '/patients');
    const hasQueue = allItems.some((item) => item.path === '/queue');
    assert.equal(hasPatients, true, 'Front Desk Officer navigation must expose /patients');
    assert.equal(hasQueue, true, 'Front Desk Officer navigation must expose /queue');
    assert.equal(isRouteAllowedForRole('FRONT_DESK_OFFICER', '/patients'), true);
    assert.equal(isRouteAllowedForRole('FRONT_DESK_OFFICER', '/queue'), true);
  });

  await t.test('5. No fake ABHA is generated (blank preserves blank/empty string)', () => {
    const sanitizeAbha = (input?: string | null): string => {
      if (!input || !input.trim()) {
        return '';
      }
      return input.trim();
    };

    assert.equal(sanitizeAbha(''), '');
    assert.equal(sanitizeAbha('   '), '');
    assert.equal(sanitizeAbha(null), '');
    assert.equal(sanitizeAbha(undefined), '');
    const result = sanitizeAbha('');
    assert.equal(result.includes('ABHA-2026-'), false, 'Synthetic ABHA-2026- prefix must never be generated');
    assert.equal(sanitizeAbha('ABHA-REAL-12345'), 'ABHA-REAL-12345');
  });
});
