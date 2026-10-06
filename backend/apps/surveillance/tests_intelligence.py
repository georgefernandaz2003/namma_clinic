"""
Comprehensive Backend Tests for Public Health Intelligence - STEP 1 Foundation
Verifies all 10 required capabilities:
1. disease aggregation
2. locality aggregation
3. previous-period calculation
4. percentage change
5. hospital scope
6. district scope
7. cross-district isolation
8. empty data
9. zero baseline
10. unknown locality
"""

import datetime
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.geography.models import State, District, Zone, Ward
from apps.facilities.models import Facility
from apps.patients.models import Patient
from apps.surveillance.models import DiseaseCase

from apps.surveillance.intelligence_services import (
    calculate_disease_trends,
    aggregate_disease_by_locality,
    aggregate_historical_disease,
    aggregate_hospital_level,
    aggregate_district_level,
    get_public_health_intelligence_summary,
    get_period_dates,
    compute_trend_status,
    resolve_facility_scope
)

User = get_user_model()


class PublicHealthIntelligenceStep1TestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # 1. State & 2 Distinct Districts for cross-district isolation testing
        cls.state = State.objects.create(name='Karnataka', code='KA')
        cls.district_central = District.objects.create(state=cls.state, name='BBMP Central', code='KA-BU')
        cls.district_rural = District.objects.create(state=cls.state, name='Bengaluru Rural', code='KA-BR')

        # Zones & Wards
        cls.zone1 = Zone.objects.create(district=cls.district_central, name='East Zone', code='Z-EAST')
        cls.zone_rural = Zone.objects.create(district=cls.district_rural, name='Hoskote Zone', code='Z-HOS')

        cls.ward12 = Ward.objects.create(zone=cls.zone1, ward_number=12, name='Indiranagar Ward', population=25000, slum_population=6000)
        cls.ward14 = Ward.objects.create(zone=cls.zone1, ward_number=14, name='Ulsoor Ward', population=20000, slum_population=4000)
        cls.ward_rural = Ward.objects.create(zone=cls.zone_rural, ward_number=1, name='Varthur Rural Ward', population=18000, slum_population=5000)

        # 2. Facilities across the 2 districts
        # District Central Facilities:
        cls.fac_hosp1 = Facility.objects.create(
            facility_code='HOSP-01', facility_name='Victoria General Hospital', facility_type='MAIN_HOSPITAL',
            state=cls.state, district=cls.district_central, zone=cls.zone1, ward=cls.ward12, bed_capacity=500
        )
        cls.fac_clinic1 = Facility.objects.create(
            facility_code='CLINIC-01', facility_name='Indiranagar Namma Clinic', facility_type='NAMMA_CLINIC',
            state=cls.state, district=cls.district_central, zone=cls.zone1, ward=cls.ward12, bed_capacity=0
        )
        # District Rural Facility:
        cls.fac_rural = Facility.objects.create(
            facility_code='RURAL-01', facility_name='Varthur Rural Health Centre', facility_type='RURAL_CLINIC',
            state=cls.state, district=cls.district_rural, zone=cls.zone_rural, ward=cls.ward_rural, bed_capacity=10
        )

        # 3. Users with strict role assignments
        cls.user_dist_central = User.objects.create_user(
            username='officer_central', password='Password123!', role='DISTRICT_OFFICER',
            assigned_district=cls.district_central
        )
        cls.user_dist_rural = User.objects.create_user(
            username='officer_rural', password='Password123!', role='DISTRICT_OFFICER',
            assigned_district=cls.district_rural
        )
        cls.user_hosp_admin = User.objects.create_user(
            username='admin_hosp1', password='Password123!', role='HOSPITAL_ADMIN',
            assigned_facility=cls.fac_hosp1
        )
        cls.user_doctor_clinic = User.objects.create_user(
            username='doc_clinic1', password='Password123!', role='DOCTOR',
            assigned_facility=cls.fac_clinic1
        )

        # 4. Patients
        cls.patient_central = Patient.objects.create(
            patient_id='P-C01', name='Ramesh B.', age=40, gender='MALE', mobile='9800000010',
            ward=cls.ward12, district=cls.district_central, registered_at_facility=cls.fac_hosp1
        )
        cls.patient_rural = Patient.objects.create(
            patient_id='P-R01', name='Suresh K.', age=50, gender='MALE', mobile='9800000020',
            ward=cls.ward_rural, district=cls.district_rural, registered_at_facility=cls.fac_rural
        )

        cls.today = datetime.date.today()

        # 5. Populate specific disease cases for calculations
        # Dengue in Indiranagar (reported by BOTH fac_hosp1 and fac_clinic1)
        # Current period (0 - 6 days ago):
        # 4 cases at fac_hosp1, 2 cases at fac_clinic1 -> total 6 cases
        for d in [0, 1, 2, 4]:
            DiseaseCase.objects.create(
                disease_name='Dengue Fever', patient=cls.patient_central,
                facility=cls.fac_hosp1, ward=cls.ward12,
                report_date=cls.today - datetime.timedelta(days=d), severity='MODERATE', status='CONFIRMED'
            )
        for d in [1, 3]:
            DiseaseCase.objects.create(
                disease_name='Dengue Fever', patient=cls.patient_central,
                facility=cls.fac_clinic1, ward=cls.ward12,
                report_date=cls.today - datetime.timedelta(days=d), severity='MILD', status='CONFIRMED'
            )

        # Previous period (7 - 13 days ago):
        # 2 cases at fac_hosp1, 1 case at fac_clinic1 -> total 3 cases
        for d in [8, 10]:
            DiseaseCase.objects.create(
                disease_name='Dengue Fever', patient=cls.patient_central,
                facility=cls.fac_hosp1, ward=cls.ward12,
                report_date=cls.today - datetime.timedelta(days=d), severity='MILD', status='CONFIRMED'
            )
        DiseaseCase.objects.create(
            disease_name='Dengue Fever', patient=cls.patient_central,
            facility=cls.fac_clinic1, ward=cls.ward12,
            report_date=cls.today - datetime.timedelta(days=12), severity='MILD', status='CONFIRMED'
        )

        # Cases in 30-day and 90-day intervals
        for d in [16, 22, 28, 45, 60, 80]:
            DiseaseCase.objects.create(
                disease_name='Dengue Fever', patient=cls.patient_central,
                facility=cls.fac_hosp1, ward=cls.ward14,
                report_date=cls.today - datetime.timedelta(days=d), severity='MILD', status='CONFIRMED'
            )

        # Cases with Unknown Locality (ward=None)
        DiseaseCase.objects.create(
            disease_name='Acute Pyrexia / Suspected Viral Fever', patient=cls.patient_central,
            facility=cls.fac_hosp1, ward=None,
            report_date=cls.today - datetime.timedelta(days=2), severity='MILD', status='CONFIRMED'
        )

        # District Rural disease cases (strictly in rural district)
        for d in [1, 2, 8]:
            DiseaseCase.objects.create(
                disease_name='Acute Gastroenteritis', patient=cls.patient_rural,
                facility=cls.fac_rural, ward=cls.ward_rural,
                report_date=cls.today - datetime.timedelta(days=d), severity='MODERATE', status='CONFIRMED'
            )

    def setUp(self):
        self.client = APIClient()

    # 1. Disease Aggregation Test
    def test_01_disease_aggregation(self):
        """Calculates current, previous, 7d, 30d, 90d, monthly counts, and percentage change."""
        res = calculate_disease_trends(
            facility_ids=[self.fac_hosp1.id, self.fac_clinic1.id],
            disease_name='Dengue Fever',
            as_of_date=self.today,
            window_days=7
        )
        self.assertIn('disease_trends', res)
        dengue_data = next((x for x in res['disease_trends'] if x['disease'] == 'Dengue Fever'), None)
        self.assertIsNotNone(dengue_data)

        # Verify accurate counts from database records
        self.assertEqual(dengue_data['current_cases'], 6)
        self.assertEqual(dengue_data['previous_period_cases'], 3)
        self.assertEqual(dengue_data['cases_7d'], 6)
        # 30-day interval includes current 6 + prev 3 + days 16, 22, 28 = 12 cases
        self.assertGreaterEqual(dengue_data['cases_30d'], 12)
        # 90-day interval includes all cases up to 80 days ago
        self.assertGreaterEqual(dengue_data['cases_90d'], 15)
        # Percentage change from 3 to 6 is +100.0%
        self.assertEqual(dengue_data['percentage_change'], 100.0)
        self.assertEqual(dengue_data['trend_direction'], 'INCREASING')

        # Historical monthly counts
        self.assertIn('historical_monthly_counts', dengue_data)
        self.assertEqual(len(dengue_data['historical_monthly_counts']), 6)

    # 2. Locality Aggregation Test
    def test_02_locality_aggregation(self):
        """Verifies disease cases by locality, multiple hospitals reporting, and locality share %."""
        res = aggregate_disease_by_locality(
            facility_ids=[self.fac_hosp1.id, self.fac_clinic1.id],
            disease_name='Dengue Fever',
            as_of_date=self.today,
            window_days=7
        )
        self.assertIn('locality_aggregations', res)
        indira_loc = next((x for x in res['locality_aggregations'] if x['locality']['name'] == 'Indiranagar Ward'), None)
        self.assertIsNotNone(indira_loc)

        self.assertEqual(indira_loc['current_cases'], 6)
        self.assertEqual(indira_loc['previous_period_cases'], 3)
        self.assertEqual(indira_loc['locality_share_pct'], 100.0)

        # Multiple hospitals reporting: both fac_hosp1 and fac_clinic1 reported in Indiranagar Ward
        self.assertEqual(indira_loc['reporting_hospitals_count'], 2)
        hosp_names = [h['hospital_name'] for h in indira_loc['reporting_hospitals']]
        self.assertIn('Victoria General Hospital', hosp_names)
        self.assertIn('Indiranagar Namma Clinic', hosp_names)

    # 3. Previous-Period Calculation Test
    def test_03_previous_period_calculation(self):
        """Verifies period math where previous period is an equal immediately preceding duration."""
        dates = get_period_dates(start_date=None, end_date=None, as_of_date='2026-10-15', window_days=10)
        # Current: 2026-10-06 to 2026-10-15 (10 days)
        self.assertEqual(str(dates['current_end']), '2026-10-15')
        self.assertEqual(str(dates['current_start']), '2026-10-06')
        self.assertEqual(dates['duration_days'], 10)
        # Previous: 2026-09-26 to 2026-10-05 (10 days)
        self.assertEqual(str(dates['previous_end']), '2026-10-05')
        self.assertEqual(str(dates['previous_start']), '2026-09-26')

    # 4. Percentage Change Test
    def test_04_percentage_change(self):
        """Verifies percentage change calculations across varying current and previous cases."""
        # Increase from 10 to 15 (+50%)
        status_1, pct_1, _ = compute_trend_status(15, 10)
        self.assertEqual(pct_1, 50.0)
        self.assertEqual(status_1, 'INCREASING')

        # Decrease from 20 to 10 (-50%)
        status_2, pct_2, _ = compute_trend_status(10, 20)
        self.assertEqual(pct_2, -50.0)
        self.assertEqual(status_2, 'DECREASING')

        # Slight upward from 10 to 11 (+10%)
        status_3, pct_3, _ = compute_trend_status(11, 10)
        self.assertEqual(pct_3, 10.0)
        self.assertEqual(status_3, 'POSSIBLE_INCREASE')

        # Stable from 10 to 10 (0%)
        status_4, pct_4, _ = compute_trend_status(10, 10)
        self.assertEqual(pct_4, 0.0)
        self.assertEqual(status_4, 'NORMAL')

    # 5. Hospital Scope Test
    def test_05_hospital_scope(self):
        """Hospital Admin only sees clinical data from their assigned hospital."""
        hosp_data = aggregate_hospital_level(
            facility_id=self.fac_hosp1.id,
            user=self.user_hosp_admin,
            as_of_date=self.today
        )
        self.assertEqual(hosp_data['hospital']['id'], self.fac_hosp1.id)
        # In current 7 days, fac_hosp1 recorded 4 Dengue cases (clinic had 2)
        dengue_hosp = next((x for x in hosp_data['diseases'] if x['disease'] == 'Dengue Fever'), None)
        self.assertIsNotNone(dengue_hosp)
        self.assertEqual(dengue_hosp['current_cases'], 4)

        # Attempt to access another hospital's data is rejected
        forbidden_data = aggregate_hospital_level(
            facility_id=self.fac_clinic1.id,
            user=self.user_hosp_admin,
            as_of_date=self.today
        )
        self.assertIn('error', forbidden_data)

    # 6. District Scope Test
    def test_06_district_scope(self):
        """District Officer sees all facilities inside their assigned district."""
        dist_data = aggregate_district_level(
            district_id=self.district_central.id,
            user=self.user_dist_central,
            as_of_date=self.today
        )
        self.assertEqual(dist_data['district']['id'], self.district_central.id)
        self.assertEqual(dist_data['district']['total_facilities'], 2)

        # Both facilities are in hospital comparison
        fac_names = [h['hospital_name'] for h in dist_data['hospital_comparison']]
        self.assertIn('Victoria General Hospital', fac_names)
        self.assertIn('Indiranagar Namma Clinic', fac_names)

        # District-wide Dengue total is 4 + 2 = 6
        dengue_dist = next((x for x in dist_data['diseases'] if x['disease'] == 'Dengue Fever'), None)
        self.assertEqual(dengue_dist['current_cases'], 6)

    # 7. Cross-District Isolation Test
    def test_07_cross_district_isolation(self):
        """Ensures complete isolation between different districts."""
        # Central officer queries Central: Gastroenteritis from Rural district MUST NOT be present
        central_res = calculate_disease_trends(
            district_id=self.district_central.id,
            as_of_date=self.today,
            window_days=7
        )
        gastro = next((x for x in central_res['disease_trends'] if x['disease'] == 'Acute Gastroenteritis'), None)
        self.assertIsNone(gastro)

        # Rural officer querying Central district is rejected
        rejected = aggregate_district_level(
            district_id=self.district_central.id,
            user=self.user_dist_rural,
            as_of_date=self.today
        )
        self.assertIn('error', rejected)

    # 8. Empty Data Test
    def test_08_empty_data(self):
        """Zero records return clean 0 counts and INSUFFICIENT_DATA status without errors."""
        future_date = self.today + datetime.timedelta(days=365)
        res = calculate_disease_trends(
            facility_ids=[self.fac_hosp1.id],
            disease_name='NonExistentDisease',
            as_of_date=future_date,
            window_days=7
        )
        self.assertEqual(res['summary']['total_current_cases'], 0)
        self.assertEqual(res['summary']['total_previous_cases'], 0)
        self.assertEqual(res['summary']['overall_trend_direction'], 'INSUFFICIENT_DATA')

    # 9. Zero Baseline Test
    def test_09_zero_baseline(self):
        """Handles transition from zero previous cases to positive current cases without division by zero."""
        # 0 previous, 4 current
        status_pos, pct_pos, expl = compute_trend_status(current_count=4, previous_count=0)
        self.assertIsNone(pct_pos)
        self.assertEqual(status_pos, 'INCREASING')
        self.assertIn('Zero cases in previous period', expl)

        # 0 previous, 1 current
        status_pos2, pct_pos2, _ = compute_trend_status(current_count=1, previous_count=0)
        self.assertIsNone(pct_pos2)
        self.assertEqual(status_pos2, 'POSSIBLE_INCREASE')

    # 10. Unknown Locality Test
    def test_10_unknown_locality(self):
        """Records with ward=None are safely aggregated under 'Unknown Locality'."""
        loc_res = aggregate_disease_by_locality(
            facility_ids=[self.fac_hosp1.id],
            disease_name='Acute Pyrexia / Suspected Viral Fever',
            as_of_date=self.today,
            window_days=7
        )
        unk_loc = next((x for x in loc_res['locality_aggregations'] if x['locality']['name'] == 'Unknown Locality'), None)
        self.assertIsNotNone(unk_loc)
        self.assertEqual(unk_loc['current_cases'], 1)
        self.assertIsNone(unk_loc['locality']['ward_id'])
        self.assertEqual(unk_loc['reporting_hospitals_count'], 1)

    # API Endpoint Tests
    def test_api_endpoints_hospital_admin(self):
        """Verifies API endpoints work with authenticated Hospital Admin."""
        self.client.force_authenticate(user=self.user_hosp_admin)

        # Trends
        res_trends = self.client.get(reverse('intelligence_disease_trends'))
        self.assertEqual(res_trends.status_code, status.HTTP_200_OK)

        # Locality
        res_loc = self.client.get(reverse('intelligence_disease_by_locality'))
        self.assertEqual(res_loc.status_code, status.HTTP_200_OK)

        # Historical
        res_hist = self.client.get(reverse('intelligence_historical_disease'))
        self.assertEqual(res_hist.status_code, status.HTTP_200_OK)

        # Hospital Aggregation
        res_hosp = self.client.get(f"{reverse('intelligence_hospital_aggregation')}?facility={self.fac_hosp1.id}")
        self.assertEqual(res_hosp.status_code, status.HTTP_200_OK)

        # Summary
        res_sum = self.client.get(reverse('intelligence_summary'))
        self.assertEqual(res_sum.status_code, status.HTTP_200_OK)

    def test_api_district_aggregation_endpoint(self):
        """Verifies District Aggregation endpoint works with District Officer."""
        self.client.force_authenticate(user=self.user_dist_central)
        res_dist = self.client.get(f"{reverse('intelligence_district_aggregation')}?district={self.district_central.id}")
        self.assertEqual(res_dist.status_code, status.HTTP_200_OK)
        self.assertEqual(res_dist.data['district']['id'], self.district_central.id)
