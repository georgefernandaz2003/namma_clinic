"""
Comprehensive Test Suite for Public Health Intelligence Forecasting & Seasonal Analysis
STEP 2 Module Verification

Tests all 17 required scenarios:
1. weekly time-series generation
2. zero-case weeks preserved
3. forecast with sufficient data
4. insufficient historical data
5. forecast values are non-negative
6. forecast bounds are valid
7. seasonal analysis with sufficient data
8. seasonal analysis with insufficient data
9. Hospital Admin facility isolation
10. District Officer district isolation
11. cross-district request -> 403
12. cross-hospital request -> 403
13. invalid weeks parameter -> 400
14. invalid months parameter -> 400
15. empty database -> safe response
16. as_of_date produces deterministic results
17. no fake/random values are generated
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

from apps.surveillance.intelligence_forecast_services import (
    build_disease_time_series,
    generate_disease_forecast,
    calculate_seasonal_pattern,
    generate_forecast_summary
)

User = get_user_model()


class PublicHealthForecastingStep2TestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # 1. State & 2 Distinct Districts for cross-district testing
        cls.state = State.objects.create(name='Karnataka', code='KA')
        cls.district_central = District.objects.create(state=cls.state, name='BBMP Central', code='KA-BU')
        cls.district_rural = District.objects.create(state=cls.state, name='Bengaluru Rural', code='KA-BR')

        # Zones & Wards
        cls.zone1 = Zone.objects.create(district=cls.district_central, name='East Zone', code='Z-EAST')
        cls.zone_rural = Zone.objects.create(district=cls.district_rural, name='Hoskote Zone', code='Z-HOS')

        cls.ward12 = Ward.objects.create(zone=cls.zone1, ward_number=12, name='Indiranagar Ward', population=25000)
        cls.ward_rural = Ward.objects.create(zone=cls.zone_rural, ward_number=1, name='Varthur Rural Ward', population=18000)

        # 2. Facilities
        cls.fac_hosp1 = Facility.objects.create(
            facility_code='HOSP-01', facility_name='Victoria General Hospital', facility_type='MAIN_HOSPITAL',
            state=cls.state, district=cls.district_central, zone=cls.zone1, ward=cls.ward12
        )
        cls.fac_clinic1 = Facility.objects.create(
            facility_code='CLINIC-01', facility_name='Indiranagar Namma Clinic', facility_type='NAMMA_CLINIC',
            state=cls.state, district=cls.district_central, zone=cls.zone1, ward=cls.ward12
        )
        cls.fac_rural = Facility.objects.create(
            facility_code='RURAL-01', facility_name='Varthur Rural Health Centre', facility_type='RURAL_CLINIC',
            state=cls.state, district=cls.district_rural, zone=cls.zone_rural, ward=cls.ward_rural
        )

        # 3. Users
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
            patient_id='P-C01', name='Ramesh B.', age=40, gender='MALE',
            ward=cls.ward12, district=cls.district_central, registered_at_facility=cls.fac_hosp1
        )
        cls.patient_rural = Patient.objects.create(
            patient_id='P-R01', name='Suresh K.', age=50, gender='MALE',
            ward=cls.ward_rural, district=cls.district_rural, registered_at_facility=cls.fac_rural
        )

        # 5. Deterministic Fixed as_of_date for rigorous reproducibility
        # 2026-10-04 (Sunday)
        cls.fixed_as_of = datetime.date(2026, 10, 4)

        # Populate deterministic Dengue cases at fac_hosp1:
        # Week 0 (0-6 days before as_of: Sep 28 - Oct 04): 5 cases
        for d in [0, 1, 2, 4, 6]:
            DiseaseCase.objects.create(
                disease_name='Dengue Fever', patient=cls.patient_central,
                facility=cls.fac_hosp1, ward=cls.ward12,
                report_date=cls.fixed_as_of - datetime.timedelta(days=d)
            )

        # Week 1 (7-13 days before as_of: Sep 21 - Sep 27): 4 cases
        for d in [7, 8, 10, 12]:
            DiseaseCase.objects.create(
                disease_name='Dengue Fever', patient=cls.patient_central,
                facility=cls.fac_hosp1, ward=cls.ward12,
                report_date=cls.fixed_as_of - datetime.timedelta(days=d)
            )

        # Week 2 (14-20 days before as_of: Sep 14 - Sep 20): 3 cases
        for d in [14, 16, 18]:
            DiseaseCase.objects.create(
                disease_name='Dengue Fever', patient=cls.patient_central,
                facility=cls.fac_hosp1, ward=cls.ward12,
                report_date=cls.fixed_as_of - datetime.timedelta(days=d)
            )

        # Week 3 (21-27 days before as_of: Sep 07 - Sep 13): 2 cases
        for d in [22, 25]:
            DiseaseCase.objects.create(
                disease_name='Dengue Fever', patient=cls.patient_central,
                facility=cls.fac_hosp1, ward=cls.ward12,
                report_date=cls.fixed_as_of - datetime.timedelta(days=d)
            )

        # Week 4 (28-34 days before as_of: Aug 31 - Sep 06): 0 cases (Deliberate ZERO-CASE WEEK)

        # Week 5 (35-41 days before as_of: Aug 24 - Aug 30): 1 case
        DiseaseCase.objects.create(
            disease_name='Dengue Fever', patient=cls.patient_central,
            facility=cls.fac_hosp1, ward=cls.ward12,
            report_date=cls.fixed_as_of - datetime.timedelta(days=36)
        )

        # Additional historical monthly cases in July (to test seasonality > 10 cases)
        # July 2026 (~75-85 days before as_of)
        for d in [75, 78, 80, 82]:
            DiseaseCase.objects.create(
                disease_name='Dengue Fever', patient=cls.patient_central,
                facility=cls.fac_hosp1, ward=cls.ward12,
                report_date=cls.fixed_as_of - datetime.timedelta(days=d)
            )

        # Total Dengue cases at fac_hosp1 = 5 + 4 + 3 + 2 + 0 + 1 + 4 = 19 cases.

        # Rural disease case (isolated)
        DiseaseCase.objects.create(
            disease_name='Malaria', patient=cls.patient_rural,
            facility=cls.fac_rural, ward=cls.ward_rural,
            report_date=cls.fixed_as_of - datetime.timedelta(days=2)
        )

    def setUp(self):
        self.client = APIClient()

    # 1. Weekly time-series generation
    def test_01_weekly_time_series_generation(self):
        """Generates continuous 7-day weekly time series."""
        ts = build_disease_time_series(
            facility_ids=[self.fac_hosp1.id],
            disease_name='Dengue Fever',
            as_of_date=self.fixed_as_of,
            weeks_count=6
        )
        series = ts['series']
        self.assertEqual(len(series), 6)

        # Check structure
        for w in series:
            self.assertIn('week_start', w)
            self.assertIn('week_end', w)
            self.assertIn('cases', w)
            start_dt = datetime.datetime.strptime(w['week_start'], '%Y-%m-%d').date()
            end_dt = datetime.datetime.strptime(w['week_end'], '%Y-%m-%d').date()
            self.assertEqual((end_dt - start_dt).days, 6)

        # Check consecutive continuity
        for i in range(len(series) - 1):
            curr_end = datetime.datetime.strptime(series[i]['week_end'], '%Y-%m-%d').date()
            next_start = datetime.datetime.strptime(series[i + 1]['week_start'], '%Y-%m-%d').date()
            self.assertEqual(curr_end + datetime.timedelta(days=1), next_start)

    # 2. Zero-case weeks preserved
    def test_02_zero_case_weeks_preserved(self):
        """Zero-case weeks are explicitly preserved without omission."""
        ts = build_disease_time_series(
            facility_ids=[self.fac_hosp1.id],
            disease_name='Dengue Fever',
            as_of_date=self.fixed_as_of,
            weeks_count=6
        )
        series = ts['series']
        # Week index 1 (corresponding to 28-34 days ago) has 0 cases
        zero_week = next((w for w in series if w['cases'] == 0), None)
        self.assertIsNotNone(zero_week)
        self.assertEqual(zero_week['cases'], 0)

    # 3. Forecast with sufficient data
    def test_03_forecast_with_sufficient_data(self):
        """Generates WMA forecast when data meets minimum threshold."""
        ts = build_disease_time_series(
            facility_ids=[self.fac_hosp1.id],
            disease_name='Dengue Fever',
            as_of_date=self.fixed_as_of,
            weeks_count=6
        )
        forecast = generate_disease_forecast(ts['series'], horizon_weeks=4)
        self.assertEqual(forecast['status'], 'AVAILABLE')
        self.assertEqual(forecast['horizon_weeks'], 4)
        self.assertEqual(len(forecast['points']), 4)
        self.assertEqual(forecast['method'], 'WEIGHTED_MOVING_AVERAGE')

    # 4. Insufficient historical data
    def test_04_insufficient_historical_data(self):
        """Returns INSUFFICIENT_DATA status without forcing predictions when data is sparse."""
        # Query disease with 0 cases
        ts_empty = build_disease_time_series(
            facility_ids=[self.fac_hosp1.id],
            disease_name='NonExistentFever',
            as_of_date=self.fixed_as_of,
            weeks_count=4
        )
        forecast_empty = generate_disease_forecast(ts_empty['series'], horizon_weeks=4)
        self.assertEqual(forecast_empty['status'], 'INSUFFICIENT_DATA')
        self.assertEqual(len(forecast_empty['points']), 0)
        self.assertIn('Insufficient historical', forecast_empty['explanation'])

    # 5. Forecast values are non-negative
    def test_05_forecast_values_non_negative(self):
        """Forecast predicted values and bounds must never be negative."""
        ts = build_disease_time_series(
            facility_ids=[self.fac_hosp1.id],
            disease_name='Dengue Fever',
            as_of_date=self.fixed_as_of,
            weeks_count=6
        )
        forecast = generate_disease_forecast(ts['series'], horizon_weeks=4)
        for pt in forecast['points']:
            self.assertGreaterEqual(pt['predicted_cases'], 0.0)
            self.assertGreaterEqual(pt['lower_bound'], 0.0)
            self.assertGreaterEqual(pt['upper_bound'], 0.0)

    # 6. Forecast bounds are valid
    def test_06_forecast_bounds_valid(self):
        """Upper bound >= predicted_cases >= lower_bound."""
        ts = build_disease_time_series(
            facility_ids=[self.fac_hosp1.id],
            disease_name='Dengue Fever',
            as_of_date=self.fixed_as_of,
            weeks_count=6
        )
        forecast = generate_disease_forecast(ts['series'], horizon_weeks=4)
        for pt in forecast['points']:
            self.assertGreaterEqual(pt['upper_bound'], pt['predicted_cases'])
            self.assertGreaterEqual(pt['predicted_cases'], pt['lower_bound'])

    # 7. Seasonal analysis with sufficient data
    def test_07_seasonal_analysis_with_sufficient_data(self):
        """Evaluates seasonal clustering across calendar months with sufficient records."""
        seasonal = calculate_seasonal_pattern(
            facility_ids=[self.fac_hosp1.id],
            disease_name='Dengue Fever',
            as_of_date=self.fixed_as_of,
            months_count=12
        )
        self.assertIn(seasonal['seasonal_status'], ['DETECTED', 'WEAK'])
        self.assertIsNotNone(seasonal['highest_case_month'])
        self.assertIsNotNone(seasonal['lowest_case_month'])
        self.assertEqual(len(seasonal['monthly_patterns']), 12)
        self.assertGreaterEqual(seasonal['seasonal_strength'], 0.0)

    # 8. Seasonal analysis with insufficient data
    def test_08_seasonal_analysis_with_insufficient_data(self):
        """Returns NOT_ENOUGH_DATA when volume is under the 10-case threshold."""
        seasonal = calculate_seasonal_pattern(
            facility_ids=[self.fac_rural.id],
            disease_name='Malaria',  # only 1 case in DB
            as_of_date=self.fixed_as_of,
            months_count=12
        )
        self.assertEqual(seasonal['seasonal_status'], 'NOT_ENOUGH_DATA')
        self.assertEqual(seasonal['seasonal_strength'], 0.0)
        self.assertIn('Insufficient historical', seasonal['explanation'])

    # 9. Hospital Admin facility isolation
    def test_09_hospital_admin_facility_isolation(self):
        """Hospital Admin successfully accesses own hospital forecast."""
        self.client.force_authenticate(user=self.user_hosp_admin)
        res = self.client.get(
            f"{reverse('intelligence_forecast')}?facility={self.fac_hosp1.id}&disease=Dengue%20Fever&date={self.fixed_as_of}"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['disease'], 'Dengue Fever')
        self.assertEqual(res.data['forecast']['status'], 'AVAILABLE')

    # 10. District Officer district isolation
    def test_10_district_officer_district_isolation(self):
        """District Officer accesses forecast across assigned district."""
        self.client.force_authenticate(user=self.user_dist_central)
        res = self.client.get(
            f"{reverse('intelligence_forecast')}?district={self.district_central.id}&disease=Dengue%20Fever&date={self.fixed_as_of}"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['scope']['district_id'], self.district_central.id)

    # 11. Cross-district request -> 403
    def test_11_cross_district_request_forbidden(self):
        """District Officer querying another district returns HTTP 403."""
        self.client.force_authenticate(user=self.user_dist_central)
        res_fc = self.client.get(
            f"{reverse('intelligence_forecast')}?district={self.district_rural.id}"
        )
        self.assertEqual(res_fc.status_code, status.HTTP_403_FORBIDDEN)

        res_seas = self.client.get(
            f"{reverse('intelligence_seasonality')}?district={self.district_rural.id}"
        )
        self.assertEqual(res_seas.status_code, status.HTTP_403_FORBIDDEN)

    # 12. Cross-hospital request -> 403
    def test_12_cross_hospital_request_forbidden(self):
        """Hospital Admin querying another facility returns HTTP 403."""
        self.client.force_authenticate(user=self.user_hosp_admin)
        res_fc = self.client.get(
            f"{reverse('intelligence_forecast')}?facility={self.fac_clinic1.id}"
        )
        self.assertEqual(res_fc.status_code, status.HTTP_403_FORBIDDEN)

        res_seas = self.client.get(
            f"{reverse('intelligence_seasonality')}?facility={self.fac_clinic1.id}"
        )
        self.assertEqual(res_seas.status_code, status.HTTP_403_FORBIDDEN)

    # 13. Invalid weeks parameter -> 400
    def test_13_invalid_weeks_parameter_bad_request(self):
        """Invalid weeks parameter returns HTTP 400 Bad Request."""
        self.client.force_authenticate(user=self.user_hosp_admin)
        for bad_val in ['abc', '-5', '0']:
            res = self.client.get(f"{reverse('intelligence_forecast')}?weeks={bad_val}")
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('Invalid weeks parameter', res.data['error'])

    # 14. Invalid months parameter -> 400
    def test_14_invalid_months_parameter_bad_request(self):
        """Invalid months parameter returns HTTP 400 Bad Request."""
        self.client.force_authenticate(user=self.user_hosp_admin)
        for bad_val in ['text', '-1', '0']:
            res = self.client.get(f"{reverse('intelligence_seasonality')}?months={bad_val}")
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('Invalid months parameter', res.data['error'])

    # 15. Empty database -> safe response
    def test_15_empty_database_safe_response(self):
        """Empty disease dataset produces safe INSUFFICIENT_DATA response without 500 errors."""
        self.client.force_authenticate(user=self.user_hosp_admin)
        res = self.client.get(
            f"{reverse('intelligence_forecast')}?disease=UnknownRareDisease&date={self.fixed_as_of}"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['forecast']['status'], 'INSUFFICIENT_DATA')
        self.assertEqual(res.data['seasonality']['seasonal_status'], 'NOT_ENOUGH_DATA')

    # 16. as_of_date produces deterministic results
    def test_16_as_of_date_produces_deterministic_results(self):
        """Identical as_of_date produces identical results across consecutive runs."""
        ts1 = build_disease_time_series(
            facility_ids=[self.fac_hosp1.id],
            disease_name='Dengue Fever',
            as_of_date=self.fixed_as_of,
            weeks_count=6
        )
        ts2 = build_disease_time_series(
            facility_ids=[self.fac_hosp1.id],
            disease_name='Dengue Fever',
            as_of_date=self.fixed_as_of,
            weeks_count=6
        )
        self.assertEqual(ts1['series'], ts2['series'])
        self.assertEqual(ts1['total_cases_in_series'], ts2['total_cases_in_series'])

    # 17. No fake/random values are generated
    def test_17_no_fake_random_values_generated(self):
        """Total cases in historical series match actual database records."""
        ts = build_disease_time_series(
            facility_ids=[self.fac_hosp1.id],
            disease_name='Dengue Fever',
            as_of_date=self.fixed_as_of,
            weeks_count=52
        )
        db_count = DiseaseCase.objects.filter(
            facility=self.fac_hosp1,
            disease_name='Dengue Fever',
            report_date__lte=self.fixed_as_of
        ).count()
        # All 19 cases recorded within the 52-week period
        self.assertEqual(ts['total_cases_in_series'], db_count)
        self.assertEqual(db_count, 19)
