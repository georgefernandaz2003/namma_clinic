"""
Comprehensive Tests for Public Health Intelligence Alerts & Action Layer - STEP 4
Verifies all required capabilities:
1. Signal creation (Trend, Locality, Forecast, Seasonality)
2. Signal deduplication (fingerprint-based, no duplicate active alerts)
3. Configurable threshold behavior (INTELLIGENCE_LOCALITY_SHARE_THRESHOLD)
4. Facility isolation (Hospital Admin restricted to own facility)
5. District isolation (District Officer restricted to own district)
6. Cross-facility access rejected with HTTP 403
7. Lifecycle state transitions (NEW -> ACKNOWLEDGED -> RESOLVED)
8. Invalid lifecycle transition rejection (Cannot acknowledge RESOLVED alert)
9. Audit logging for creation, evaluation, acknowledgement, resolution
10. Data safety: No alert when signal conditions not met, insufficient data
"""

import datetime
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.geography.models import State, District, Zone, Ward
from apps.facilities.models import Facility
from apps.patients.models import Patient
from apps.surveillance.models import DiseaseCase
from apps.alerts.models import Alert
from apps.audit.models import AuditLog

from apps.surveillance.intelligence_alert_services import (
    evaluate_intelligence_alerts,
    evaluate_facility_intelligence_signals,
    generate_alert_fingerprint,
    acknowledge_alert,
    resolve_alert,
    INTELLIGENCE_LOCALITY_SHARE_THRESHOLD
)

User = get_user_model()


class PublicHealthIntelligenceAlertsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # 1. State & 2 Distinct Districts
        cls.state = State.objects.create(name='Karnataka', code='KA')
        cls.district_central = District.objects.create(state=cls.state, name='BBMP Central', code='KA-BU')
        cls.district_rural = District.objects.create(state=cls.state, name='Bengaluru Rural', code='KA-BR')

        # Zones & Wards
        cls.zone_central = Zone.objects.create(district=cls.district_central, name='Central Zone', code='Z-CEN')
        cls.zone_rural = Zone.objects.create(district=cls.district_rural, name='Rural Zone', code='Z-RUR')

        cls.ward_indiranagar = Ward.objects.create(
            zone=cls.zone_central, ward_number=101, name='Indiranagar', population=30000
        )
        cls.ward_ulsoor = Ward.objects.create(
            zone=cls.zone_central, ward_number=102, name='Ulsoor', population=20000
        )
        cls.ward_rural = Ward.objects.create(
            zone=cls.zone_rural, ward_number=201, name='Hosakote Rural', population=15000
        )

        # Facilities
        cls.hospital_a = Facility.objects.create(
            facility_code='HOSP-A',
            facility_name='General Hospital Central A',
            facility_type='COMMUNITY_HEALTH_CENTRE',
            state=cls.state,
            district=cls.district_central,
            zone=cls.zone_central,
            ward=cls.ward_indiranagar
        )
        cls.phc_b = Facility.objects.create(
            facility_code='PHC-B',
            facility_name='Urban PHC Central B',
            facility_type='PRIMARY_HEALTH_CENTRE',
            state=cls.state,
            district=cls.district_central,
            zone=cls.zone_central,
            ward=cls.ward_ulsoor
        )
        cls.hospital_rural = Facility.objects.create(
            facility_code='HOSP-RUR',
            facility_name='Rural Sub-District Hospital',
            facility_type='SUB_DISTRICT_HOSPITAL',
            state=cls.state,
            district=cls.district_rural,
            zone=cls.zone_rural,
            ward=cls.ward_rural
        )

        # Patients
        cls.patient_a = Patient.objects.create(
            patient_id='P-A01', name='Ramesh Kumar', mobile='9876543210', age=35, gender='MALE',
            registered_at_facility=cls.hospital_a, ward=cls.ward_indiranagar, district=cls.district_central
        )
        cls.patient_b = Patient.objects.create(
            patient_id='P-B01', name='Priya Sharma', mobile='9876543211', age=28, gender='FEMALE',
            registered_at_facility=cls.hospital_a, ward=cls.ward_ulsoor, district=cls.district_central
        )
        cls.patient_rural = Patient.objects.create(
            patient_id='P-R01', name='Anil Gowda', mobile='9876543212', age=45, gender='MALE',
            registered_at_facility=cls.hospital_rural, ward=cls.ward_rural, district=cls.district_rural
        )

        # Users
        cls.user_admin_a = User.objects.create_user(
            username='admin_hosp_a', password='password123', role='HOSPITAL_ADMIN',
            assigned_facility=cls.hospital_a
        )
        cls.user_admin_rural = User.objects.create_user(
            username='admin_hosp_rural', password='password123', role='HOSPITAL_ADMIN',
            assigned_facility=cls.hospital_rural
        )
        cls.user_dist_central = User.objects.create_user(
            username='officer_central', password='password123', role='DISTRICT_OFFICER',
            assigned_district=cls.district_central
        )
        cls.user_dist_rural = User.objects.create_user(
            username='officer_rural', password='password123', role='DISTRICT_OFFICER',
            assigned_district=cls.district_rural
        )
        cls.user_doctor_a = User.objects.create_user(
            username='doctor_a', password='password123', role='DOCTOR',
            assigned_facility=cls.hospital_a
        )

        cls.client = APIClient()

    def setUp(self):
        self.as_of = datetime.date(2026, 10, 6)
        self.client = APIClient()

    # -----------------------------------------------------------------------
    # 1. Signal Creation Tests
    # -----------------------------------------------------------------------
    def test_disease_trend_increase_signal_created(self):
        """Increasing trend triggers WARNING alert with correct metadata."""
        # Previous period: 1 Dengue case (e.g. 10 days ago)
        DiseaseCase.objects.create(
            facility=self.hospital_a, patient=self.patient_a, disease_name='Dengue Fever',
            report_date=self.as_of - datetime.timedelta(days=10), ward=self.ward_indiranagar
        )
        # Current period: 6 Dengue cases (last 6 days)
        for d in range(1, 7):
            DiseaseCase.objects.create(
                facility=self.hospital_a, patient=self.patient_a, disease_name='Dengue Fever',
                report_date=self.as_of - datetime.timedelta(days=d), ward=self.ward_indiranagar
            )

        res = evaluate_facility_intelligence_signals(self.hospital_a, as_of_date=self.as_of, actor_user=self.user_admin_a)
        trend_alerts = [a for a in res['alerts'] if a.alert_type == 'INTELLIGENCE_TREND']

        self.assertEqual(len(trend_alerts), 1)
        alert = trend_alerts[0]
        self.assertEqual(alert.severity, 'WARNING')
        self.assertEqual(alert.status, 'NEW')
        self.assertIn('Dengue Fever', alert.title)
        self.assertEqual(alert.metadata['current_cases'], 6)
        self.assertEqual(alert.metadata['previous_cases'], 1)
        self.assertEqual(alert.metadata['trend_direction'], 'INCREASING')
        self.assertGreater(alert.metadata['percentage_change'], 0)

    def test_high_locality_concentration_signal_created(self):
        """Locality exceeding threshold (>= 25%) triggers WARNING alert."""
        # 5 cases in Indiranagar, 1 in Ulsoor -> Indiranagar share = 5/6 = 83.3% > 25%
        for d in range(1, 6):
            DiseaseCase.objects.create(
                facility=self.hospital_a, patient=self.patient_a, disease_name='Chikungunya',
                report_date=self.as_of - datetime.timedelta(days=d), ward=self.ward_indiranagar
            )
        DiseaseCase.objects.create(
            facility=self.hospital_a, patient=self.patient_b, disease_name='Chikungunya',
            report_date=self.as_of - datetime.timedelta(days=1), ward=self.ward_ulsoor
        )

        res = evaluate_facility_intelligence_signals(self.hospital_a, as_of_date=self.as_of, actor_user=self.user_admin_a)
        locality_alerts = [a for a in res['alerts'] if a.alert_type == 'INTELLIGENCE_LOCALITY']

        self.assertTrue(len(locality_alerts) >= 1)
        indira_alert = next((a for a in locality_alerts if 'Indiranagar' in a.title), None)
        self.assertIsNotNone(indira_alert)
        self.assertEqual(indira_alert.severity, 'WARNING')
        self.assertEqual(indira_alert.metadata['locality'], 'Indiranagar')
        self.assertEqual(indira_alert.metadata['current_cases'], 5)
        self.assertGreaterEqual(indira_alert.metadata['locality_share'], INTELLIGENCE_LOCALITY_SHARE_THRESHOLD)

    def test_forecast_surveillance_signal_created(self):
        """Elevated forecast projection produces WARNING forecast surveillance signal."""
        # Seed 6 consecutive weeks of increasing Dengue cases ending on as_of
        for w in range(6, 0, -1):
            count_for_week = (7 - w) * 5  # 5, 10, 15, 20, 25, 30
            case_date = self.as_of - datetime.timedelta(days=(w - 1) * 7 + 1)
            for _ in range(count_for_week):
                DiseaseCase.objects.create(
                    facility=self.hospital_a, patient=self.patient_a, disease_name='Dengue Fever',
                    report_date=case_date, ward=self.ward_indiranagar
                )

        res = evaluate_facility_intelligence_signals(self.hospital_a, as_of_date=self.as_of, actor_user=self.user_admin_a)
        forecast_alerts = [a for a in res['alerts'] if a.alert_type == 'INTELLIGENCE_FORECAST']

        self.assertEqual(len(forecast_alerts), 1)
        alert = forecast_alerts[0]
        self.assertEqual(alert.severity, 'WARNING')
        self.assertIn("Forecast Surveillance Signal", alert.title)
        self.assertIn("Forecast indicates elevated future case volume", alert.description)
        self.assertIn('predicted_cases', alert.metadata)
        self.assertIn('historical_baseline', alert.metadata)

    def test_seasonal_surveillance_signal_created(self):
        """Detected seasonal peak matching current month triggers INFO seasonal signal."""
        current_month = self.as_of.month
        # Seed >= 15 cases in October 2026 (inside 12-month observation window)
        for i in range(15):
            d_date = datetime.date(2026, current_month, (i % 5) + 1)
            DiseaseCase.objects.create(
                facility=self.hospital_a, patient=self.patient_a, disease_name='Influenza',
                report_date=d_date, ward=self.ward_indiranagar
            )
        # Add 1 case in March 2026 (inside window)
        DiseaseCase.objects.create(
            facility=self.hospital_a, patient=self.patient_a, disease_name='Influenza',
            report_date=datetime.date(2026, 3, 10), ward=self.ward_indiranagar
        )

        res = evaluate_facility_intelligence_signals(self.hospital_a, as_of_date=self.as_of, actor_user=self.user_admin_a)
        seasonal_alerts = [a for a in res['alerts'] if a.alert_type == 'INTELLIGENCE_SEASONALITY']

        self.assertEqual(len(seasonal_alerts), 1)
        alert = seasonal_alerts[0]
        self.assertEqual(alert.severity, 'INFO')
        self.assertIn("Seasonal Surveillance Signal", alert.title)
        self.assertEqual(alert.metadata['seasonal_status'], 'DETECTED')
        self.assertEqual(alert.metadata['current_month'], current_month)

    # -----------------------------------------------------------------------
    # 2. Alert Deduplication Tests
    # -----------------------------------------------------------------------
    def test_duplicate_evaluation_does_not_create_duplicate_alerts(self):
        """Repeated evaluations must NOT create duplicate alerts for active signals."""
        for d in range(1, 5):
            DiseaseCase.objects.create(
                facility=self.hospital_a, patient=self.patient_a, disease_name='Cholera',
                report_date=self.as_of - datetime.timedelta(days=d), ward=self.ward_indiranagar
            )

        # First evaluation
        res1 = evaluate_facility_intelligence_signals(self.hospital_a, as_of_date=self.as_of, actor_user=self.user_admin_a)
        count_run1 = Alert.objects.filter(facility=self.hospital_a, metadata__disease='Cholera').count()
        self.assertGreater(count_run1, 0)
        self.assertGreater(res1['created_count'], 0)

        # Second evaluation immediately after
        res2 = evaluate_facility_intelligence_signals(self.hospital_a, as_of_date=self.as_of, actor_user=self.user_admin_a)
        count_run2 = Alert.objects.filter(facility=self.hospital_a, metadata__disease='Cholera').count()

        # Alert count must NOT increase
        self.assertEqual(count_run1, count_run2)
        self.assertEqual(res2['created_count'], 0)
        self.assertGreater(res2['updated_count'], 0)

    # -----------------------------------------------------------------------
    # 3. Data Safety & Insufficient Data Tests
    # -----------------------------------------------------------------------
    def test_no_alert_when_trend_is_normal_or_decreasing(self):
        """Decreasing or stable trend does NOT produce an increasing trend signal."""
        # Previous period: 10 cases
        for d in range(8, 14):
            DiseaseCase.objects.create(
                facility=self.hospital_a, patient=self.patient_a, disease_name='Typhoid',
                report_date=self.as_of - datetime.timedelta(days=d), ward=self.ward_indiranagar
            )
        # Current period: 2 cases (decrease of 80%)
        for d in range(1, 3):
            DiseaseCase.objects.create(
                facility=self.hospital_a, patient=self.patient_a, disease_name='Typhoid',
                report_date=self.as_of - datetime.timedelta(days=d), ward=self.ward_indiranagar
            )

        res = evaluate_facility_intelligence_signals(self.hospital_a, as_of_date=self.as_of, actor_user=self.user_admin_a)
        trend_alerts = [a for a in res['alerts'] if a.alert_type == 'INTELLIGENCE_TREND' and a.metadata.get('disease') == 'Typhoid']
        self.assertEqual(len(trend_alerts), 0)

    def test_insufficient_forecast_data_does_not_create_forecast_alert(self):
        """Fewer than minimum required weeks/cases does not create forecast alert."""
        # Only 1 case total
        DiseaseCase.objects.create(
            facility=self.hospital_a, patient=self.patient_a, disease_name='RareFever',
            report_date=self.as_of - datetime.timedelta(days=2), ward=self.ward_indiranagar
        )
        res = evaluate_facility_intelligence_signals(self.hospital_a, as_of_date=self.as_of, actor_user=self.user_admin_a)
        fc_alerts = [a for a in res['alerts'] if a.alert_type == 'INTELLIGENCE_FORECAST' and a.metadata.get('disease') == 'RareFever']
        self.assertEqual(len(fc_alerts), 0)

    def test_insufficient_seasonality_data_does_not_create_seasonal_alert(self):
        """Fewer than 10 cases over historical months does not create seasonal alert."""
        for d in range(1, 4):
            DiseaseCase.objects.create(
                facility=self.hospital_a, patient=self.patient_a, disease_name='ScrubTyphus',
                report_date=self.as_of - datetime.timedelta(days=d * 10), ward=self.ward_indiranagar
            )
        res = evaluate_facility_intelligence_signals(self.hospital_a, as_of_date=self.as_of, actor_user=self.user_admin_a)
        seas_alerts = [a for a in res['alerts'] if a.alert_type == 'INTELLIGENCE_SEASONALITY' and a.metadata.get('disease') == 'ScrubTyphus']
        self.assertEqual(len(seas_alerts), 0)

    # -----------------------------------------------------------------------
    # 4. Lifecycle Transitions & Auditing
    # -----------------------------------------------------------------------
    def test_alert_lifecycle_and_audit_logging(self):
        """NEW -> ACKNOWLEDGED -> RESOLVED transitions correctly with audit entries."""
        alert = Alert.objects.create(
            alert_type='INTELLIGENCE_TREND',
            severity='WARNING',
            facility=self.hospital_a,
            district=self.district_central,
            title='Test Trend Alert',
            description='Test',
            status='NEW'
        )

        # 1. Acknowledge
        acknowledge_alert(alert, self.user_admin_a)
        alert.refresh_from_db()
        self.assertEqual(alert.status, 'ACKNOWLEDGED')
        self.assertIsNotNone(alert.acknowledged_at)
        self.assertEqual(alert.acknowledged_by, self.user_admin_a)

        audit_ack = AuditLog.objects.filter(action='ALERT_ACKNOWLEDGED', facility=self.hospital_a).first()
        self.assertIsNotNone(audit_ack)
        self.assertEqual(audit_ack.user, self.user_admin_a)

        # 2. Resolve
        resolve_alert(alert, self.user_admin_a, resolution_notes='Reviewed by clinical team')
        alert.refresh_from_db()
        self.assertEqual(alert.status, 'RESOLVED')
        self.assertIsNotNone(alert.resolved_at)
        self.assertEqual(alert.resolved_by, self.user_admin_a)
        self.assertEqual(alert.resolution_notes, 'Reviewed by clinical team')

        audit_res = AuditLog.objects.filter(action='ALERT_RESOLVED', facility=self.hospital_a).first()
        self.assertIsNotNone(audit_res)

        # 3. Invalid transition: cannot acknowledge resolved alert
        with self.assertRaises(ValueError):
            acknowledge_alert(alert, self.user_admin_a)

    # -----------------------------------------------------------------------
    # 5. API RBAC, Scoping & Cross-Facility Isolation
    # -----------------------------------------------------------------------
    def test_hospital_admin_can_only_see_own_facility_alerts(self):
        """Hospital Admin sees only alerts belonging to their assigned facility."""
        Alert.objects.create(
            alert_type='INTELLIGENCE_TREND', severity='WARNING', facility=self.hospital_a,
            title='Hospital A Alert', description='Test A', status='NEW'
        )
        Alert.objects.create(
            alert_type='INTELLIGENCE_TREND', severity='WARNING', facility=self.hospital_rural,
            title='Rural Hospital Alert', description='Test Rural', status='NEW'
        )

        self.client.force_authenticate(user=self.user_admin_a)
        url = '/api/surveillance/intelligence/alerts/'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        results = resp.data.get('results', [])
        facility_ids = [r['facility'] for r in results]
        self.assertTrue(all(f == self.hospital_a.id for f in facility_ids))
        self.assertNotIn(self.hospital_rural.id, facility_ids)

    def test_cross_facility_query_rejected_with_403(self):
        """Hospital Admin requesting another facility scope gets HTTP 403."""
        self.client.force_authenticate(user=self.user_admin_a)
        url = f'/api/surveillance/intelligence/alerts/?facility={self.hospital_rural.id}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_cross_facility_alert_mutation_rejected_with_403(self):
        """Hospital Admin attempting to PATCH/acknowledge another facility's alert gets 403."""
        alert_rural = Alert.objects.create(
            alert_type='INTELLIGENCE_TREND', severity='WARNING', facility=self.hospital_rural,
            title='Rural Hospital Alert', description='Test Rural', status='NEW'
        )

        self.client.force_authenticate(user=self.user_admin_a)
        url = f'/api/surveillance/intelligence/alerts/{alert_rural.id}/'
        resp = self.client.patch(url, {'status': 'ACKNOWLEDGED'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_district_officer_sees_all_facilities_in_assigned_district(self):
        """District Officer can see alerts across facilities inside their assigned district."""
        Alert.objects.create(
            alert_type='INTELLIGENCE_TREND', severity='WARNING', facility=self.hospital_a,
            district=self.district_central, title='Central A Alert', description='Test A', status='NEW'
        )
        Alert.objects.create(
            alert_type='INTELLIGENCE_TREND', severity='WARNING', facility=self.phc_b,
            district=self.district_central, title='Central B Alert', description='Test B', status='NEW'
        )
        Alert.objects.create(
            alert_type='INTELLIGENCE_TREND', severity='WARNING', facility=self.hospital_rural,
            district=self.district_rural, title='Rural Alert', description='Test R', status='NEW'
        )

        self.client.force_authenticate(user=self.user_dist_central)
        url = '/api/surveillance/intelligence/alerts/'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        results = resp.data.get('results', [])
        facility_ids = set(r['facility'] for r in results)
        self.assertIn(self.hospital_a.id, facility_ids)
        self.assertIn(self.phc_b.id, facility_ids)
        self.assertNotIn(self.hospital_rural.id, facility_ids)

    def test_manual_evaluate_endpoint_security(self):
        """Evaluate endpoint validates role and scope."""
        # Hospital Admin evaluates own facility: OK
        self.client.force_authenticate(user=self.user_admin_a)
        url = '/api/surveillance/intelligence/alerts/evaluate/'
        resp = self.client.post(url, {'facility': self.hospital_a.id, 'date': '2026-10-06'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data.get('status'), 'success')

        # Hospital Admin evaluates another facility: 403
        resp_bad = self.client.post(url, {'facility': self.hospital_rural.id, 'date': '2026-10-06'}, format='json')
        self.assertEqual(resp_bad.status_code, status.HTTP_403_FORBIDDEN)
