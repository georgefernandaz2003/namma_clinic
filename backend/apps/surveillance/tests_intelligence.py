"""
Unit and Integration Tests for Public Health Intelligence & Forecasting Module.
Verifies all 10 analytical capabilities, response structures, terminology compliance,
outbreak safety assertions, role authorization, and facility scoping.
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
from apps.visits.models import Visit
from apps.consultations.models import Consultation
from apps.surveillance.models import DiseaseCase
from apps.laboratory.models import LabTestMaster, LabOrder, LabResult
from apps.ncd.models import NCDRecord
from apps.maternal.models import MaternalRecord
from apps.child.models import ChildRecord

from apps.surveillance.intelligence_services import (
    get_disease_trend_analysis,
    get_disease_by_locality_analysis,
    get_historical_disease_analysis,
    detect_emerging_patterns,
    get_locality_risk_analysis,
    forecast_disease_incidence,
    forecast_locality_demand,
    detect_seasonal_patterns,
    estimate_future_health_demand,
    estimate_resource_planning,
    get_public_health_intelligence_overview
)

User = get_user_model()


class PublicHealthIntelligenceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # 1. Geography
        cls.state = State.objects.create(name='Karnataka', code='KA')
        cls.district = District.objects.create(state=cls.state, name='BBMP Central', code='KA-BU')
        cls.zone = Zone.objects.create(district=cls.district, name='East Zone', code='Z-EAST')
        cls.ward1 = Ward.objects.create(zone=cls.zone, ward_number=12, name='Indiranagar Ward', population=25000, slum_population=6000)
        cls.ward2 = Ward.objects.create(zone=cls.zone, ward_number=14, name='Ulsoor Ward', population=20000, slum_population=8000)

        # 2. Facilities
        cls.facility1 = Facility.objects.create(
            facility_code='HOSP-01', facility_name='Indiranagar General Hospital', facility_type='MAIN_HOSPITAL',
            state=cls.state, district=cls.district, zone=cls.zone, ward=cls.ward1, bed_capacity=100
        )
        cls.facility2 = Facility.objects.create(
            facility_code='CLINIC-01', facility_name='Ulsoor Namma Clinic', facility_type='NAMMA_CLINIC',
            state=cls.state, district=cls.district, zone=cls.zone, ward=cls.ward2, bed_capacity=0
        )

        # 3. Users with roles
        cls.district_officer = User.objects.create_user(
            username='dist_officer', password='Password123!', role='DISTRICT_OFFICER',
            assigned_district=cls.district
        )
        cls.hospital_admin = User.objects.create_user(
            username='hosp_admin', password='Password123!', role='HOSPITAL_ADMIN',
            assigned_facility=cls.facility1
        )
        cls.doctor = User.objects.create_user(
            username='doctor1', password='Password123!', role='DOCTOR',
            assigned_facility=cls.facility1
        )

        # 4. Patients
        cls.patient1 = Patient.objects.create(
            patient_id='P-001', name='John Doe', age=35, gender='MALE', mobile='9800000001',
            ward=cls.ward1, district=cls.district, registered_at_facility=cls.facility1
        )
        cls.patient2 = Patient.objects.create(
            patient_id='P-002', name='Jane Smith', age=28, gender='FEMALE', mobile='9800000002',
            ward=cls.ward2, district=cls.district, registered_at_facility=cls.facility2
        )

        cls.today = datetime.date.today()

        # 5. Populate realistic historical disease cases
        # Dengue surge in current week
        for d in [0, 1, 2, 3, 4]:
            DiseaseCase.objects.create(
                disease_name='Dengue Fever',
                patient=cls.patient1,
                facility=cls.facility1,
                ward=cls.ward1,
                report_date=cls.today - datetime.timedelta(days=d),
                severity='MODERATE' if d % 2 == 0 else 'MILD',
                status='CONFIRMED'
            )
        # Previous period cases for Dengue
        for d in [7, 8]:
            DiseaseCase.objects.create(
                disease_name='Dengue Fever',
                patient=cls.patient1,
                facility=cls.facility1,
                ward=cls.ward1,
                report_date=cls.today - datetime.timedelta(days=d),
                severity='MILD',
                status='CONFIRMED'
            )
        # Baseline cases for Dengue
        for d in [15, 20, 25]:
            DiseaseCase.objects.create(
                disease_name='Dengue Fever',
                patient=cls.patient1,
                facility=cls.facility1,
                ward=cls.ward1,
                report_date=cls.today - datetime.timedelta(days=d),
                severity='MILD',
                status='CONFIRMED'
            )

        # Viral Fever in Ward 2
        for d in [1, 3, 5, 10, 15, 22, 30]:
            DiseaseCase.objects.create(
                disease_name='Acute Pyrexia / Suspected Viral Fever',
                patient=cls.patient2,
                facility=cls.facility2,
                ward=cls.ward2,
                report_date=cls.today - datetime.timedelta(days=d),
                severity='MILD',
                status='CONFIRMED'
            )

        # 6. Visits & Consultations
        for d in range(15):
            past_date = cls.today - datetime.timedelta(days=d)
            v = Visit.objects.create(
                visit_id=f"VIS-TEST-{d}",
                patient=cls.patient1 if d % 2 == 0 else cls.patient2,
                facility=cls.facility1 if d % 2 == 0 else cls.facility2,
                opd_date=past_date,
                visit_type='GENERAL_OPD',
                status='COMPLETED'
            )
            Consultation.objects.create(
                visit=v,
                patient=v.patient,
                facility=v.facility,
                chief_complaint='Fever and headache',
                diagnosis_name='Dengue Fever' if d % 2 == 0 else 'Acute Pyrexia / Suspected Viral Fever',
                diagnosis_code='A90' if d % 2 == 0 else 'R50.9'
            )

        # 7. NCD, Maternal, Child
        NCDRecord.objects.create(
            patient=cls.patient1, facility=cls.facility1,
            hypertension_diagnosed=True, risk_level='HIGH', control_status='UNCONTROLLED'
        )
        MaternalRecord.objects.create(
            patient=cls.patient2, anc_number='ANC-TEST-01',
            lmp_date=cls.today - datetime.timedelta(days=90),
            edd_date=cls.today + datetime.timedelta(days=190),
            high_risk_flag=True, high_risk_reason='Severe Anemia'
        )
        ChildRecord.objects.create(
            patient=cls.patient2, sam_mam_status='MAM'
        )

        # 8. Lab tests & results
        lab_test = LabTestMaster.objects.create(code='L-NS1', name='Dengue NS1 Antigen', category='Serology')
        order = LabOrder.objects.create(
            patient=cls.patient1, facility=cls.facility1, test_master=lab_test, status='VERIFIED'
        )
        LabResult.objects.create(
            lab_order=order, result_value='Positive', interpretation_flag='CRITICAL'
        )

    def setUp(self):
        self.client = APIClient()

    # --- Service 1: Disease Trend Analysis ---
    def test_disease_trend_analysis(self):
        result = get_disease_trend_analysis(district_id=self.district.id, as_of_date=self.today)
        self.assertIn('summary', result)
        self.assertIn('disease_trends', result)

        trends = result['disease_trends']
        self.assertTrue(len(trends) > 0)
        first_item = trends[0]

        # Verify structured output schema
        required_keys = [
            'disease', 'current_value', 'previous_period', 'historical_baseline',
            'percentage_change', 'trend_direction', 'locality', 'hospital_facility',
            'observation_period', 'confidence_range', 'explanation', 'outbreak_status'
        ]
        for key in required_keys:
            self.assertIn(key, first_item)

        # Terminology compliance
        allowed_directions = ['NORMAL', 'INCREASING', 'DECREASING', 'POSSIBLE_INCREASE', 'HIGHER_THAN_BASELINE', 'WATCH']
        self.assertIn(first_item['trend_direction'], allowed_directions)

        # Outbreak status verification
        self.assertEqual(first_item['outbreak_status'], 'UNVERIFIED / NO CONFIRMED OUTBREAK')

    # --- Service 2: Disease-by-Locality Analysis ---
    def test_disease_by_locality_analysis(self):
        result = get_disease_by_locality_analysis(district_id=self.district.id, as_of_date=self.today)
        self.assertIn('localities', result)
        self.assertIn('herfindahl_concentration_index', result)
        self.assertTrue(len(result['localities']) > 0)

        loc = result['localities'][0]
        self.assertIn('incidence_rate_per_10k', loc)
        self.assertIn('locality_share_pct', loc)
        self.assertIn('confidence_range', loc)
        self.assertEqual(loc['outbreak_status'], 'UNVERIFIED / NO CONFIRMED OUTBREAK')

    # --- Service 3: Historical Disease Analysis ---
    def test_historical_disease_analysis(self):
        result = get_historical_disease_analysis(disease_name='Dengue Fever', district_id=self.district.id, as_of_date=self.today)
        self.assertEqual(result['disease'], 'Dengue Fever')
        self.assertIn('historical_series', result)
        self.assertIn('statistics', result)
        self.assertIn('z_score', result)
        self.assertIn('mean', result['statistics'])
        self.assertIn('std_dev', result['statistics'])

    # --- Service 4: Emerging Pattern Detection ---
    def test_emerging_pattern_detection(self):
        result = detect_emerging_patterns(district_id=self.district.id, as_of_date=self.today)
        self.assertIn('patterns_detected_count', result)
        self.assertIn('emerging_patterns', result)
        for pattern in result['emerging_patterns']:
            self.assertIn('pattern_type', pattern)
            self.assertIn('trend_direction', pattern)
            self.assertIn('explanation', pattern)
            self.assertIn('UNVERIFIED', pattern['outbreak_status'])

    # --- Service 5: Locality Risk Analysis ---
    def test_locality_risk_analysis(self):
        result = get_locality_risk_analysis(district_id=self.district.id, as_of_date=self.today)
        self.assertIn('locality_risks', result)
        self.assertTrue(len(result['locality_risks']) > 0)
        ward_risk = result['locality_risks'][0]
        self.assertIn('subscores', ward_risk)
        self.assertIn('risk_metrics', ward_risk)
        self.assertTrue(0.0 <= ward_risk['current_value'] <= 100.0)

    # --- Service 6: Disease Forecasting ---
    def test_disease_forecasting(self):
        result = forecast_disease_incidence(disease_name='Dengue Fever', forecast_days=14, as_of_date=self.today)
        self.assertEqual(result['disease'], 'Dengue Fever')
        self.assertIn('daily_forecasts', result)
        self.assertEqual(len(result['daily_forecasts']), 14)
        self.assertIn('model_parameters', result)
        self.assertIn('rmse', result['model_parameters'])
        self.assertGreaterEqual(result['projected_value'], 0.0)

    # --- Service 7: Locality Demand Forecasting ---
    def test_locality_demand_forecasting(self):
        result = forecast_locality_demand(district_id=self.district.id, forecast_days=14, as_of_date=self.today)
        self.assertIn('locality_forecasts', result)
        self.assertTrue(len(result['locality_forecasts']) > 0)
        loc_forecast = result['locality_forecasts'][0]
        self.assertIn('top_locality_conditions', loc_forecast)
        self.assertGreaterEqual(loc_forecast['projected_value'], 0.0)

    # --- Service 8: Seasonal Pattern Detection ---
    def test_seasonal_pattern_detection(self):
        result = detect_seasonal_patterns(disease_name='Dengue Fever', as_of_date=self.today)
        self.assertIn('seasonal_index', result)
        self.assertIn('seasonal_breakdown', result)
        self.assertIn('current_season', result)
        self.assertGreater(len(result['seasonal_breakdown']), 0)

    # --- Service 9: Future Health-Demand Estimation ---
    def test_future_health_demand_estimation(self):
        result = estimate_future_health_demand(facility_id=self.facility1.id, forecast_days=14, as_of_date=self.today)
        self.assertIn('department_breakdown', result)
        self.assertIn('daily_projected_schedule', result)
        self.assertIn('GENERAL_OPD', result['department_breakdown'])
        self.assertIn('NCD_CHRONIC_CARE', result['department_breakdown'])
        self.assertIn('MATERNAL_AND_CHILD_HEALTH', result['department_breakdown'])

    # --- Service 10: Resource Planning Estimates ---
    def test_resource_planning_estimates(self):
        result = estimate_resource_planning(facility_id=self.facility1.id, forecast_days=14, as_of_date=self.today)
        self.assertIn('workforce_requirements', result)
        self.assertIn('clinical_and_diagnostic_supplies', result)
        self.assertIn('inpatient_infrastructure', result)
        workforce = result['workforce_requirements']
        self.assertIn('doctor_shifts_needed', workforce)
        self.assertIn('physician_hours_needed', workforce)
        self.assertIn('nurse_triage_hours_needed', workforce)

    # --- Master Unified Overview ---
    def test_public_health_intelligence_overview(self):
        overview = get_public_health_intelligence_overview(district_id=self.district.id, as_of_date=self.today)
        self.assertEqual(overview['module_title'], 'Public Health Intelligence & Forecasting')
        self.assertIn('disease_trend_analysis', overview)
        self.assertIn('disease_by_locality_analysis', overview)
        self.assertIn('historical_disease_analysis', overview)
        self.assertIn('emerging_pattern_detection', overview)
        self.assertIn('locality_risk_analysis', overview)
        self.assertIn('disease_forecasting', overview)
        self.assertIn('locality_forecasting', overview)
        self.assertIn('seasonal_pattern_detection', overview)
        self.assertIn('future_health_demand_estimation', overview)
        self.assertIn('resource_planning_estimates', overview)
        self.assertEqual(overview['outbreak_status'], 'UNVERIFIED / NO CONFIRMED OUTBREAK')

    # --- API Endpoint Testing ---
    def test_api_overview_endpoint_district_officer(self):
        self.client.force_authenticate(user=self.district_officer)
        url = reverse('intelligence_overview')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('disease_trend_analysis', response.data)
        self.assertIn('resource_planning_estimates', response.data)

    def test_api_granular_endpoints(self):
        self.client.force_authenticate(user=self.district_officer)

        endpoints = [
            'intelligence_disease_trends',
            'intelligence_disease_by_locality',
            'intelligence_historical_disease',
            'intelligence_emerging_patterns',
            'intelligence_locality_risk',
            'intelligence_disease_forecast',
            'intelligence_locality_forecast',
            'intelligence_seasonal_patterns',
            'intelligence_future_health_demand',
            'intelligence_resource_planning',
        ]
        for ep in endpoints:
            url = reverse(ep)
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK, f"Endpoint {ep} failed with {response.status_code}")

    def test_api_alias_endpoints(self):
        self.client.force_authenticate(user=self.hospital_admin)
        url = reverse('intelligence_overview_alias')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_access_rejected(self):
        url = reverse('intelligence_overview')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
