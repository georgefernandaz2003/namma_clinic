import test from 'node:test';
import assert from 'node:assert/strict';
import { parseApiError, getApiBaseUrl } from './client.ts';
import { ROLE_LABELS, type Role } from '../types/auth.ts';
import { isPathAllowedForRole } from '../utils/permissions.ts';

test('getApiBaseUrl returns valid default or configured base URL', () => {
  const url = getApiBaseUrl();
  assert.ok(url.startsWith('http'), 'Base URL must start with http/https');
  assert.ok(url.endsWith('/'), 'Base URL must end with trailing slash');
});

test('parseApiError handles various error response shapes', async (t) => {
  await t.test('handles string error', () => {
    assert.equal(parseApiError('Simple string error'), 'Simple string error');
  });

  await t.test('handles null/undefined error', () => {
    assert.equal(parseApiError(null), 'An unexpected error occurred.');
    assert.equal(parseApiError(undefined), 'An unexpected error occurred.');
  });

  await t.test('handles Network Error', () => {
    const error = { message: 'Network Error' };
    assert.equal(
      parseApiError(error),
      'Unable to connect to local Django server. Please ensure the backend is running.'
    );
  });

  await t.test('handles timeout ECONNABORTED error', () => {
    const error = { code: 'ECONNABORTED' };
    assert.equal(
      parseApiError(error),
      'Request timed out after 15 seconds. Please try again.'
    );
  });

  await t.test('extracts direct detail field', () => {
    const error = {
      response: {
        status: 401,
        data: { detail: 'Given token not valid for any token type' },
      },
    };
    assert.equal(parseApiError(error), 'Given token not valid for any token type');
  });

  await t.test('extracts custom error message string', () => {
    const error = {
      response: {
        status: 409,
        data: { error: 'Prescription is in status PENDING_VERIFICATION.' },
      },
    };
    assert.equal(parseApiError(error), 'Prescription is in status PENDING_VERIFICATION.');
  });

  await t.test('extracts JWT messages array', () => {
    const error = {
      response: {
        status: 401,
        data: {
          messages: [{ token_class: 'AccessToken', message: 'Token is invalid or expired' }],
        },
      },
    };
    assert.equal(parseApiError(error), 'Token is invalid or expired');
  });

  await t.test('extracts non_field_errors array', () => {
    const error = {
      response: {
        status: 400,
        data: {
          non_field_errors: ['Unable to log in with provided credentials.'],
        },
      },
    };
    assert.equal(parseApiError(error), 'Unable to log in with provided credentials.');
  });

  await t.test('extracts field validation errors dictionary', () => {
    const error = {
      response: {
        status: 400,
        data: {
          patient_name: ['This field is required.'],
        },
      },
    };
    assert.equal(parseApiError(error), 'Patient Name: This field is required.');
  });
});

test('Role definitions match 6 authoritative roles', () => {
  const expectedRoles: Role[] = [
    'DISTRICT_OFFICER',
    'HOSPITAL_ADMIN',
    'DOCTOR',
    'NURSE',
    'LAB_TECHNICIAN',
    'PHARMACIST',
  ];

  for (const role of expectedRoles) {
    assert.ok(ROLE_LABELS[role], `Role label must exist for ${role}`);
  }
});

test('Role permissions check validates routes correctly', () => {
  assert.equal(isPathAllowedForRole('DOCTOR', '/consultation'), true);
  assert.equal(isPathAllowedForRole('DOCTOR', '/compliance'), false);

  assert.equal(isPathAllowedForRole('NURSE', '/triage'), true);
  assert.equal(isPathAllowedForRole('NURSE', '/lab'), false);

  assert.equal(isPathAllowedForRole('DISTRICT_OFFICER', '/network'), true);
  assert.equal(isPathAllowedForRole('DISTRICT_OFFICER', '/audit'), true);
});
