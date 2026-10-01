"""
Phase 18 Deployment Foundation & Production Hardening Test Suite.
Verifies healthz, readyz, password validators, static configuration,
environment-driven settings, and fail-fast production rules.
"""
import os
import subprocess
import sys
from unittest.mock import patch
from django.test import TestCase, Client
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework.test import APIClient
from apps.accounts.models import User, RoleMaster, StaffFacilityAssignment
from apps.facilities.models import Facility


class Phase18HealthProbesTests(TestCase):
    """Verifies unauthenticated healthz and readyz probe endpoints."""

    def setUp(self):
        self.client = Client()

    def test_healthz_liveness_probe_returns_200(self):
        """Liveness probe confirms application process is running."""
        response = self.client.get('/healthz')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'ok')

    def test_healthz_with_trailing_slash_returns_200(self):
        """Liveness probe works with trailing slash for container orchestrators."""
        response = self.client.get('/healthz/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'ok')

    def test_healthz_requires_no_authentication(self):
        """Liveness probe must not be blocked by DRF permission classes."""
        api_client = APIClient()
        response = api_client.get('/healthz')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_readyz_readiness_probe_database_connected(self):
        """Readiness probe verifies database connectivity returns 200."""
        response = self.client.get('/readyz')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'ready')
        self.assertEqual(data.get('database'), 'connected')

    def test_readyz_with_trailing_slash_returns_200(self):
        """Readiness probe works with trailing slash."""
        response = self.client.get('/readyz/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'ready')

    def test_readyz_database_failure_returns_503_without_leaking_internals(self):
        """Simulated database failure returns HTTP 503 and hides credentials/internals."""
        with patch('django.db.connection.cursor', side_effect=Exception('DB Connection Refused')):
            response = self.client.get('/readyz')
            self.assertEqual(response.status_code, 503)
            data = response.json()
            self.assertEqual(data.get('status'), 'not ready')
            self.assertEqual(data.get('database'), 'unavailable')
            # Verify no internals, hostnames, or credentials are in the response
            content_str = response.content.decode()
            self.assertNotIn('DB Connection Refused', content_str)
            self.assertNotIn('password', content_str)
            self.assertNotIn('postgres', content_str)


class Phase18PasswordValidationTests(TestCase):
    """Verifies that standard Django password validators reject weak credentials."""

    def test_password_validators_configured(self):
        """Ensure AUTH_PASSWORD_VALIDATORS is non-empty and contains standard validators."""
        self.assertTrue(len(settings.AUTH_PASSWORD_VALIDATORS) >= 4)
        validator_names = [v['NAME'] for v in settings.AUTH_PASSWORD_VALIDATORS]
        self.assertIn('django.contrib.auth.password_validation.MinimumLengthValidator', validator_names)
        self.assertIn('django.contrib.auth.password_validation.CommonPasswordValidator', validator_names)
        self.assertIn('django.contrib.auth.password_validation.NumericPasswordValidator', validator_names)

    def test_short_password_rejected(self):
        """Passwords under 8 characters must be rejected by validator."""
        with self.assertRaises(ValidationError) as ctx:
            validate_password('short7')
        self.assertTrue(any('too short' in msg for msg in ctx.exception.messages))

    def test_purely_numeric_password_rejected(self):
        """Entirely numeric passwords must be rejected."""
        with self.assertRaises(ValidationError) as ctx:
            validate_password('1234567890')
        self.assertTrue(any('entirely numeric' in msg for msg in ctx.exception.messages))

    def test_common_password_rejected(self):
        """Common dictionary passwords must be rejected."""
        with self.assertRaises(ValidationError) as ctx:
            validate_password('password123')
        self.assertTrue(any('too common' in msg for msg in ctx.exception.messages))

    def test_strong_password_accepted(self):
        """Strong passwords passing all validators raise no error."""
        try:
            validate_password('Namma#Clinic!2026Secure')
        except ValidationError:
            self.fail('Strong password unexpectedly failed validation')


class Phase18StaticAndMediaTests(TestCase):
    """Verifies static and media file contracts."""

    def test_static_root_configured(self):
        """STATIC_ROOT must be defined to allow collectstatic."""
        self.assertIsNotNone(settings.STATIC_ROOT)
        self.assertTrue(str(settings.STATIC_ROOT).endswith('staticfiles'))

    def test_static_url_configured(self):
        """STATIC_URL must start and end with /."""
        self.assertEqual(settings.STATIC_URL, '/static/')

    def test_media_root_configured(self):
        """MEDIA_ROOT must be defined."""
        self.assertIsNotNone(settings.MEDIA_ROOT)
        self.assertTrue(str(settings.MEDIA_ROOT).endswith('media'))


class Phase18ProductionFailFastTests(TestCase):
    """Verifies startup fail-fast behavior when production environment is misconfigured."""

    def _run_python_check_with_env(self, extra_env):
        env = os.environ.copy()
        env.update(extra_env)
        cmd = [sys.executable, 'manage.py', 'check']
        res = subprocess.run(cmd, cwd=str(settings.BASE_DIR), env=env, text=True, capture_output=True)
        return res

    def test_production_fails_when_secret_key_is_demo(self):
        """In production, using the demo SECRET_KEY must fail fast."""
        res = self._run_python_check_with_env({
            'DJANGO_ENV': 'production',
            'DJANGO_SECRET_KEY': 'django-insecure-namma-clinic-digital-health-platform-key-demo-only',
            'DATABASE_ENGINE': 'django.db.backends.postgresql',
            'DATABASE_NAME': 'test_db',
            'DATABASE_USER': 'test_user',
            'DATABASE_PASSWORD': 'test_password',
            'DATABASE_HOST': '127.0.0.1',
            'DJANGO_ALLOWED_HOSTS': 'clinic.gov.in',
        })
        self.assertNotEqual(res.returncode, 0)
        self.assertIn('DJANGO_SECRET_KEY must be provided from the environment and cannot be the default demo key', res.stderr)

    def test_production_fails_when_debug_is_true(self):
        """In production, DJANGO_DEBUG=True must fail fast."""
        res = self._run_python_check_with_env({
            'DJANGO_ENV': 'production',
            'DJANGO_DEBUG': 'True',
            'DJANGO_SECRET_KEY': 'a-super-secret-production-key-for-testing-12345',
            'DATABASE_ENGINE': 'django.db.backends.postgresql',
            'DATABASE_NAME': 'test_db',
            'DATABASE_USER': 'test_user',
            'DATABASE_PASSWORD': 'test_password',
            'DATABASE_HOST': '127.0.0.1',
            'DJANGO_ALLOWED_HOSTS': 'clinic.gov.in',
        })
        self.assertNotEqual(res.returncode, 0)
        self.assertIn('DJANGO_DEBUG must be False', res.stderr)

    def test_production_fails_when_wildcard_hosts(self):
        """In production, wildcard '*' in ALLOWED_HOSTS must fail fast."""
        res = self._run_python_check_with_env({
            'DJANGO_ENV': 'production',
            'DJANGO_SECRET_KEY': 'a-super-secret-production-key-for-testing-12345',
            'DJANGO_ALLOWED_HOSTS': '*',
            'DATABASE_ENGINE': 'django.db.backends.postgresql',
            'DATABASE_NAME': 'test_db',
            'DATABASE_USER': 'test_user',
            'DATABASE_PASSWORD': 'test_password',
            'DATABASE_HOST': '127.0.0.1',
        })
        self.assertNotEqual(res.returncode, 0)
        self.assertIn('cannot be empty or contain wildcard', res.stderr)

    def test_production_fails_when_sqlite_engine(self):
        """In production, using SQLite must fail fast."""
        res = self._run_python_check_with_env({
            'DJANGO_ENV': 'production',
            'DJANGO_SECRET_KEY': 'a-super-secret-production-key-for-testing-12345',
            'DJANGO_ALLOWED_HOSTS': 'clinic.gov.in',
            'DATABASE_ENGINE': 'django.db.backends.sqlite3',
        })
        self.assertNotEqual(res.returncode, 0)
        self.assertIn('SQLite is strictly prohibited', res.stderr)

    def test_production_passes_with_valid_configuration(self):
        """Production check passes when all mandatory configuration variables are properly set."""
        res = self._run_python_check_with_env({
            'DJANGO_ENV': 'production',
            'DJANGO_SECRET_KEY': 'a-super-secret-production-key-for-testing-12345',
            'DJANGO_ALLOWED_HOSTS': 'clinic.gov.in,api.clinic.gov.in',
            'DATABASE_ENGINE': 'django.db.backends.postgresql',
            'DATABASE_NAME': 'test_db',
            'DATABASE_USER': 'test_user',
            'DATABASE_PASSWORD': 'test_password',
            'DATABASE_HOST': '127.0.0.1',
            'DATABASE_PORT': '5432',
        })
        self.assertEqual(res.returncode, 0, f"Expected returncode 0 but got {res.returncode}. Stderr: {res.stderr}")
        self.assertIn('System check identified no issues', res.stdout)
