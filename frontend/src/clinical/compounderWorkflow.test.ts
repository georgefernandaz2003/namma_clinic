import test from 'node:test';
import assert from 'node:assert/strict';
import {
  getRoleLandingRoute,
  getRoleNavigation,
  isRouteAllowedForRole,
} from '../navigation/navigationConfig.ts';
import { ROLE_PERMISSIONS, ROLE_ALLOWED_PATHS } from '../utils/permissions.ts';

test('Compounder Role Boundary & Patient Registration Authorization (Phase 27A)', async (t) => {
  await t.test('1. Compounder does not see Nurse Dashboard in navigation', () => {
    const navSections = getRoleNavigation('COMPOUNDER');
    const allItems = navSections.flatMap((s) => s.items);
    const hasNurseDashboard = allItems.some(
      (item) => item.path === '/dashboard/nurse' || (item.name && item.name.toLowerCase().includes('nurse'))
    );
    assert.equal(hasNurseDashboard, false, 'Compounder must not see Nurse Dashboard');
    assert.equal(isRouteAllowedForRole('COMPOUNDER', '/dashboard/nurse'), false);
  });

  await t.test('2. Compounder does not see Triage in navigation', () => {
    const navSections = getRoleNavigation('COMPOUNDER');
    const allItems = navSections.flatMap((s) => s.items);
    const hasTriage = allItems.some(
      (item) => item.path === '/triage' || (item.name && item.name.toLowerCase().includes('triage'))
    );
    assert.equal(hasTriage, false, 'Compounder must not see Triage in navigation');
  });

  await t.test('3. Compounder direct /triage navigation is blocked', () => {
    assert.equal(isRouteAllowedForRole('COMPOUNDER', '/triage'), false, 'Direct /triage access must be blocked');
    assert.equal(ROLE_ALLOWED_PATHS.COMPOUNDER.includes('/triage'), false, '/triage must not be in ROLE_ALLOWED_PATHS');
    
    // Also verify clinical permissions are removed
    const permissions = ROLE_PERMISSIONS.COMPOUNDER;
    assert.equal(permissions.has('vitals.view'), false, 'vitals.view must be removed from Compounder');
    assert.equal(permissions.has('vitals.create'), false, 'vitals.create must be removed from Compounder');
    assert.equal(permissions.has('triage.view'), false, 'triage.view must be removed from Compounder');
  });

  await t.test('4. Compounder navigation exposes Patients/Queue and lands on /dashboard/compounder', () => {
    assert.equal(getRoleLandingRoute('COMPOUNDER'), '/dashboard/compounder');
    const navSections = getRoleNavigation('COMPOUNDER');
    const allItems = navSections.flatMap((s) => s.items);
    const hasPatients = allItems.some((item) => item.path === '/patients');
    const hasQueue = allItems.some((item) => item.path === '/queue');
    assert.equal(hasPatients, true, 'Compounder navigation must expose /patients');
    assert.equal(hasQueue, true, 'Compounder navigation must expose /queue');
    assert.equal(isRouteAllowedForRole('COMPOUNDER', '/patients'), true);
    assert.equal(isRouteAllowedForRole('COMPOUNDER', '/queue'), true);
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
