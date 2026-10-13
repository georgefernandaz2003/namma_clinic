import time
from datetime import timedelta
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
import jwt

from apps.geography.models import State, District
from apps.facilities.models import Facility, FacilityTypeChoices
from apps.accounts.models import RoleChoices

User = get_user_model()


class JWTSecurityAndHardeningTests(APITestCase):
    """
    Comprehensive security test suite covering:
    1. Protected endpoint without token -> 401
    2. Protected endpoint with invalid token -> 401
    3. Protected endpoint with malformed token -> 401
    4. Protected endpoint with expired token -> 401
    5. Tampered token -> 401
    6. Valid token -> existing authenticated behavior
    7. Inactive user -> rejected (401)
    8. Deleted/nonexistent user represented by token -> rejected (401)
    9. Refresh token works correctly
    10. Rotated refresh token cannot be reused (blacklisted -> 401)
    11. Logout/revocation behavior
    12. Existing RBAC still works with valid JWT
    13. Existing facility/district authorization still works with valid JWT
    14. JWT/token values are never returned in error responses
    """

    def setUp(self):
        self.state = State.objects.create(name='Karnataka', code='KA')
        self.district_1 = District.objects.create(name='Bengaluru Urban', code='BLR-U', state=self.state)
        self.district_2 = District.objects.create(name='Mysuru', code='MYS', state=self.state)

        self.facility_a = Facility.objects.create(
            facility_code='FAC-001',
            facility_name='Facility A (District 1)',
            facility_type=FacilityTypeChoices.UPHC,
            state=self.state,
            district=self.district_1
        )
        self.facility_b = Facility.objects.create(
            facility_code='FAC-002',
            facility_name='Facility B (District 1)',
            facility_type=FacilityTypeChoices.NAMMA_CLINIC,
            state=self.state,
            district=self.district_1
        )

        self.doctor = User.objects.create_user(
            username='dr_sharma',
            password='Password123!',
            role=RoleChoices.DOCTOR,
            assigned_facility=self.facility_a,
            full_name='Dr. Sharma'
        )

        self.admin = User.objects.create_user(
            username='admin_facility_a',
            password='Password123!',
            role=RoleChoices.HOSPITAL_ADMIN,
            assigned_facility=self.facility_a,
            full_name='Admin Facility A'
        )

        self.district_officer = User.objects.create_user(
            username='do_bengaluru',
            password='Password123!',
            role=RoleChoices.DISTRICT_OFFICER,
            assigned_district=self.district_1,
            full_name='District Officer Bengaluru'
        )

        self.protected_url = '/api/auth/me/'

    # 1. Protected endpoint without token -> 401
    def test_1_protected_endpoint_without_token_returns_401(self):
        client = APIClient()
        response = client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data.get('detail'), 'Authentication credentials were not provided.')

    # 2. Protected endpoint with invalid token -> 401
    def test_2_protected_endpoint_with_invalid_token_returns_401(self):
        client = APIClient()
        # Token signed with wrong secret key
        wrong_token = jwt.encode(
            {'user_id': self.doctor.id, 'exp': time.time() + 900},
            'completely-different-wrong-signing-key',
            algorithm='HS256'
        )
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {wrong_token}')
        response = client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data.get('code'), 'token_not_valid')

    # 3. Protected endpoint with malformed token -> 401
    def test_3_protected_endpoint_with_malformed_token_returns_401(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer not-a-valid-jwt-token-format')
        response = client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data.get('code'), 'token_not_valid')

    # 4. Protected endpoint with expired token -> 401
    def test_4_protected_endpoint_with_expired_token_returns_401(self):
        client = APIClient()
        token = AccessToken.for_user(self.doctor)
        # Manually force expiration into the past
        token.set_exp(lifetime=-timedelta(minutes=10))
        expired_token_str = str(token)

        client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired_token_str}')
        response = client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data.get('code'), 'token_not_valid')

    # 5. Tampered token -> 401
    def test_5_protected_endpoint_with_tampered_token_returns_401(self):
        client = APIClient()
        valid_token = str(AccessToken.for_user(self.doctor))
        # Tamper the signature portion of the JWT
        parts = valid_token.split('.')
        tampered_sig = 'X' + parts[2][1:] if parts[2][0] != 'X' else 'Y' + parts[2][1:]
        tampered_token = f'{parts[0]}.{parts[1]}.{tampered_sig}'

        client.credentials(HTTP_AUTHORIZATION=f'Bearer {tampered_token}')
        response = client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data.get('code'), 'token_not_valid')

    # 6. Valid token -> existing authenticated behavior
    def test_6_protected_endpoint_with_valid_token_succeeds(self):
        client = APIClient()
        token = str(AccessToken.for_user(self.doctor))
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'dr_sharma')
        self.assertEqual(response.data['role'], 'DOCTOR')

    # 7. Inactive user -> rejected (401)
    def test_7_inactive_user_token_is_rejected_with_401(self):
        client = APIClient()
        token = str(AccessToken.for_user(self.doctor))

        # Deactivate user after token creation
        self.doctor.is_active = False
        self.doctor.save()

        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data.get('code'), 'user_inactive')

    # 8. Deleted/nonexistent user represented by token -> rejected (401)
    def test_8_deleted_or_nonexistent_user_token_is_rejected_with_401(self):
        client = APIClient()
        temp_user = User.objects.create_user(
            username='temp_user_to_delete',
            password='Password123!',
            role=RoleChoices.DOCTOR,
            assigned_facility=self.facility_a
        )
        token = str(AccessToken.for_user(temp_user))
        # Delete user
        temp_user.delete()

        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data.get('code'), 'user_not_found')

    # 9. Refresh token works correctly
    def test_9_refresh_token_obtains_new_access_token(self):
        client = APIClient()
        refresh = RefreshToken.for_user(self.doctor)

        response = client.post('/api/auth/token/refresh/', {'refresh': str(refresh)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

        # Verify new access token authenticates successfully
        new_access = response.data['access']
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_access}')
        profile_res = client.get(self.protected_url)
        self.assertEqual(profile_res.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_res.data['username'], 'dr_sharma')

    # 10. Rotated refresh token cannot be reused if rotation/blacklisting is enabled
    def test_10_rotated_refresh_token_cannot_be_reused(self):
        client = APIClient()
        initial_refresh = str(RefreshToken.for_user(self.doctor))

        # First use: should rotate and succeed
        first_refresh_res = client.post('/api/auth/token/refresh/', {'refresh': initial_refresh})
        self.assertEqual(first_refresh_res.status_code, status.HTTP_200_OK)
        new_refresh = first_refresh_res.data.get('refresh')
        self.assertNotEqual(initial_refresh, new_refresh)

        # Re-use of previous refresh token must be rejected with 401
        reuse_res = client.post('/api/auth/token/refresh/', {'refresh': initial_refresh})
        self.assertEqual(reuse_res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(reuse_res.data.get('code'), 'token_not_valid')

        # The new rotated refresh token should work
        second_refresh_res = client.post('/api/auth/token/refresh/', {'refresh': new_refresh})
        self.assertEqual(second_refresh_res.status_code, status.HTTP_200_OK)

    # 11. Logout/revocation behavior
    def test_11_logout_endpoint_revokes_refresh_token(self):
        client = APIClient()
        refresh = RefreshToken.for_user(self.doctor)
        refresh_str = str(refresh)

        # Call logout endpoint
        logout_res = client.post('/api/auth/logout/', {'refresh': refresh_str})
        self.assertEqual(logout_res.status_code, status.HTTP_200_OK)
        self.assertIn('revoked', logout_res.data.get('detail', '').lower())

        # Verify revoked token cannot be refreshed
        refresh_res = client.post('/api/auth/token/refresh/', {'refresh': refresh_str})
        self.assertEqual(refresh_res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(refresh_res.data.get('code'), 'token_not_valid')

    # 12. Existing RBAC still works with valid JWT
    def test_12_rbac_enforcement_with_valid_jwt(self):
        client = APIClient()
        # Doctor has clinical role -> cannot manage users (staff.create)
        doc_token = str(AccessToken.for_user(self.doctor))
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {doc_token}')
        res = client.post('/api/users/', {
            'username': 'new_staff',
            'password': 'password123',
            'role': RoleChoices.NURSE,
            'assigned_facility': self.facility_a.id
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Hospital Admin has staff.create -> can create Nurse in their facility
        admin_token = str(AccessToken.for_user(self.admin))
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')
        res_admin = client.post('/api/users/', {
            'username': 'nurse_rekha',
            'password': 'Password123!',
            'role': RoleChoices.NURSE,
            'assigned_facility': self.facility_a.id,
            'full_name': 'Nurse Rekha'
        })
        self.assertEqual(res_admin.status_code, status.HTTP_201_CREATED)

    # 13. Existing facility/district authorization still works with valid JWT
    def test_13_facility_and_district_scoping_enforced_with_jwt(self):
        client = APIClient()
        admin_token = str(AccessToken.for_user(self.admin))
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')

        # Admin cannot create user for Facility B (outside assigned facility)
        res_cross = client.post('/api/users/', {
            'username': 'nurse_fac_b',
            'password': 'Password123!',
            'role': RoleChoices.NURSE,
            'assigned_facility': self.facility_b.id,
            'full_name': 'Nurse B'
        })
        self.assertEqual(res_cross.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('assigned_facility', res_cross.data)

    # 14. JWT/token values are never returned in error responses
    def test_14_token_values_never_returned_in_error_responses(self):
        client = APIClient()
        dummy_secret_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.sensitive_payload.signature'
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {dummy_secret_token}')

        response = client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Check response content for leakage of secret payload or token string
        response_str = str(response.data)
        self.assertNotIn(dummy_secret_token, response_str)
        self.assertNotIn('sensitive_payload', response_str)
        self.assertNotIn(settings.SECRET_KEY, response_str)
        self.assertNotIn(settings.SIMPLE_JWT['SIGNING_KEY'], response_str)
