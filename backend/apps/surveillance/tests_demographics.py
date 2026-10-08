"""
Unit & Integration Tests for Public Health Intelligence Demographic Support
Validates:
1. All age group boundary conditions:
   - 0 (0-5)
   - 5 (0-5)
   - 6 (6-14)
   - 14 (6-14)
   - 15 (15-24)
   - 24 (15-24)
   - 25 (25-44)
   - 44 (25-44)
   - 45 (45-59)
   - 59 (45-59)
   - 60+ (60, 75, 100)
2. Safe handling of missing DOB, invalid future DOB, missing gender, and invalid demographic data.
3. Fallback from date_of_birth to Patient.age without redundant duplicated persistence.
4. Existing application gender values (MALE, FEMALE, OTHER) with safe fallback to UNKNOWN.
5. Integration with DiseaseCase records, DiseaseCaseSerializer, and health intelligence endpoints.
6. Strict backward compatibility across all existing public health intelligence features.
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
from apps.surveillance.views import DiseaseCaseSerializer
from apps.surveillance.demographic_services import (
    AGE_GROUPS,
    AGE_GROUP_0_5,
    AGE_GROUP_6_14,
    AGE_GROUP_15_24,
    AGE_GROUP_25_44,
    AGE_GROUP_45_59,
    AGE_GROUP_60_PLUS,
    AGE_GROUP_UNKNOWN,
    GENDER_MALE,
    GENDER_FEMALE,
    GENDER_OTHER,
    GENDER_UNKNOWN,
    calculate_age,
    get_case_patient_age,
    get_case_demographics,
    get_age_group,
    normalize_gender,
    resolve_patient_demographics,
    aggregate_demographics,
    get_demographic_intelligence,
    matches_demographic_criteria,
    filter_cases_by_demographics,
    build_age_gender_matrix,
    SEVERITY_CHOICES,
    SEVERITY_MILD,
    SEVERITY_MODERATE,
    SEVERITY_SEVERE,
    SEVERITY_UNKNOWN,
    normalize_severity,
    validate_severity_param,
    build_severity_demographic_matrices,
)
from apps.surveillance.intelligence_services import (
    calculate_disease_trends,
    aggregate_disease_by_locality,
    aggregate_historical_disease,
    aggregate_hospital_level,
    aggregate_district_level,
    get_public_health_intelligence_summary,
)
from apps.surveillance.intelligence_forecast_services import (
    calculate_seasonal_pattern,
    build_disease_time_series,
    generate_disease_forecast,
    generate_forecast_summary,
)
from apps.surveillance.intelligence_forecast_risk_services import (
    calculate_forecast_risk,
    FORECAST_RISK_ELEVATION_RATIO,
    FORECAST_RISK_HIGH_RATIO,
    FORECAST_RISK_MIN_CASES,
    RISK_LEVEL_NORMAL,
    RISK_LEVEL_ELEVATED,
    RISK_LEVEL_HIGH,
    RISK_LEVEL_INSUFFICIENT,
    RISK_STATUS_AVAILABLE,
    RISK_STATUS_INSUFFICIENT,
)
from apps.surveillance.vulnerable_population_services import (
    VULNERABLE_GROUP_PREGNANT,
    VULNERABLE_GROUP_ELDERLY,
    VULNERABLE_GROUP_DISABILITY,
    VULNERABLE_GROUP_CHRONIC,
    VULNERABLE_GROUP_LOW_INCOME,
    VULNERABLE_GROUP_GENERAL,
    VULNERABLE_GROUP_UNKNOWN,
    VULNERABLE_GROUPS,
    ALL_VULNERABLE_GROUPS,
    normalize_vulnerable_group,
    validate_vulnerable_group_param,
    filter_cases_by_vulnerable_group,
    build_vulnerable_population_matrices,
)
from apps.surveillance.patient_type_services import (
    PATIENT_TYPE_NEW,
    PATIENT_TYPE_FOLLOW_UP,
    PATIENT_TYPE_UNKNOWN,
    VALID_PATIENT_TYPES,
    ALL_PATIENT_TYPES,
    normalize_patient_type,
    validate_patient_type_param,
    annotate_case_patient_type,
    get_case_patient_type,
    filter_cases_by_patient_type,
    build_patient_type_matrices,
)

User = get_user_model()


class DemographicUtilitiesTestCase(TestCase):
    """
    Direct unit tests for core demographic calculation utilities.
    """
    def setUp(self):
        self.ref_date = datetime.date(2026, 10, 7)

    def test_age_boundaries_exact(self):
        """
        Explicitly verifies all required age boundary values:
        0, 5, 6, 14, 15, 24, 25, 44, 45, 59, 60+
        """
        # Boundary 0
        self.assertEqual(get_age_group(0), AGE_GROUP_0_5)
        # Boundary 5
        self.assertEqual(get_age_group(5), AGE_GROUP_0_5)
        # Boundary 6
        self.assertEqual(get_age_group(6), AGE_GROUP_6_14)
        # Boundary 14
        self.assertEqual(get_age_group(14), AGE_GROUP_6_14)
        # Boundary 15
        self.assertEqual(get_age_group(15), AGE_GROUP_15_24)
        # Boundary 24
        self.assertEqual(get_age_group(24), AGE_GROUP_15_24)
        # Boundary 25
        self.assertEqual(get_age_group(25), AGE_GROUP_25_44)
        # Boundary 44
        self.assertEqual(get_age_group(44), AGE_GROUP_25_44)
        # Boundary 45
        self.assertEqual(get_age_group(45), AGE_GROUP_45_59)
        # Boundary 59
        self.assertEqual(get_age_group(59), AGE_GROUP_45_59)
        # Boundary 60+
        self.assertEqual(get_age_group(60), AGE_GROUP_60_PLUS)
        self.assertEqual(get_age_group(75), AGE_GROUP_60_PLUS)
        self.assertEqual(get_age_group(102), AGE_GROUP_60_PLUS)

    def test_calculate_age_from_dob_boundaries(self):
        """
        Tests date of birth calculations against all age boundary conditions relative to reference date.
        Reference date: 2026-10-07
        """
        # Age 0 (born today or earlier this year)
        dob_0 = datetime.date(2026, 10, 7)
        age_0 = calculate_age(date_of_birth=dob_0, reference_date=self.ref_date)
        self.assertEqual(age_0, 0)
        self.assertEqual(get_age_group(age_0), AGE_GROUP_0_5)

        # Age 5
        dob_5 = datetime.date(2021, 10, 7)
        age_5 = calculate_age(date_of_birth=dob_5, reference_date=self.ref_date)
        self.assertEqual(age_5, 5)
        self.assertEqual(get_age_group(age_5), AGE_GROUP_0_5)

        # Age 6
        dob_6 = datetime.date(2020, 10, 7)
        age_6 = calculate_age(date_of_birth=dob_6, reference_date=self.ref_date)
        self.assertEqual(age_6, 6)
        self.assertEqual(get_age_group(age_6), AGE_GROUP_6_14)

        # Age 14
        dob_14 = datetime.date(2012, 10, 7)
        age_14 = calculate_age(date_of_birth=dob_14, reference_date=self.ref_date)
        self.assertEqual(age_14, 14)
        self.assertEqual(get_age_group(age_14), AGE_GROUP_6_14)

        # Age 15
        dob_15 = datetime.date(2011, 10, 7)
        age_15 = calculate_age(date_of_birth=dob_15, reference_date=self.ref_date)
        self.assertEqual(age_15, 15)
        self.assertEqual(get_age_group(age_15), AGE_GROUP_15_24)

        # Age 24
        dob_24 = datetime.date(2002, 10, 7)
        age_24 = calculate_age(date_of_birth=dob_24, reference_date=self.ref_date)
        self.assertEqual(age_24, 24)
        self.assertEqual(get_age_group(age_24), AGE_GROUP_15_24)

        # Age 25
        dob_25 = datetime.date(2001, 10, 7)
        age_25 = calculate_age(date_of_birth=dob_25, reference_date=self.ref_date)
        self.assertEqual(age_25, 25)
        self.assertEqual(get_age_group(age_25), AGE_GROUP_25_44)

        # Age 44
        dob_44 = datetime.date(1982, 10, 7)
        age_44 = calculate_age(date_of_birth=dob_44, reference_date=self.ref_date)
        self.assertEqual(age_44, 44)
        self.assertEqual(get_age_group(age_44), AGE_GROUP_25_44)

        # Age 45
        dob_45 = datetime.date(1981, 10, 7)
        age_45 = calculate_age(date_of_birth=dob_45, reference_date=self.ref_date)
        self.assertEqual(age_45, 45)
        self.assertEqual(get_age_group(age_45), AGE_GROUP_45_59)

        # Age 59
        dob_59 = datetime.date(1967, 10, 7)
        age_59 = calculate_age(date_of_birth=dob_59, reference_date=self.ref_date)
        self.assertEqual(age_59, 59)
        self.assertEqual(get_age_group(age_59), AGE_GROUP_45_59)

        # Age 60
        dob_60 = datetime.date(1966, 10, 7)
        age_60 = calculate_age(date_of_birth=dob_60, reference_date=self.ref_date)
        self.assertEqual(age_60, 60)
        self.assertEqual(get_age_group(age_60), AGE_GROUP_60_PLUS)

        # Age 85
        dob_85 = datetime.date(1941, 10, 7)
        age_85 = calculate_age(date_of_birth=dob_85, reference_date=self.ref_date)
        self.assertEqual(age_85, 85)
        self.assertEqual(get_age_group(age_85), AGE_GROUP_60_PLUS)

    def test_birthday_not_yet_occurred_in_reference_year(self):
        """
        If birthday is later in the current calendar year, the completed age is year - 1.
        e.g. ref = 2026-10-07, dob = 2001-11-20 -> age 24 (not 25 yet).
        """
        dob = datetime.date(2001, 11, 20)
        age = calculate_age(date_of_birth=dob, reference_date=self.ref_date)
        self.assertEqual(age, 24)
        self.assertEqual(get_age_group(age), AGE_GROUP_15_24)

    def test_missing_dob_returns_none_and_no_fabricated_age(self):
        """
        Requirement 4: If date_of_birth is missing:
        - do not fabricate an age
        - return an explicit unknown/None age result
        - document the fallback behavior.
        """
        # None DOB returns None by default without fabricating an age
        self.assertIsNone(calculate_age(date_of_birth=None, reference_date=self.ref_date))
        self.assertEqual(get_age_group(None), AGE_GROUP_UNKNOWN)

        # Blank / whitespace string DOB returns None
        self.assertIsNone(calculate_age(date_of_birth="", reference_date=self.ref_date))
        self.assertIsNone(calculate_age(date_of_birth="   ", reference_date=self.ref_date))

        # Stored age is NOT used by default when DOB is missing
        age_with_stored = calculate_age(
            date_of_birth=None,
            reference_date=self.ref_date,
            allow_stored_age_fallback=False,
            fallback_age=32
        )
        self.assertIsNone(age_with_stored)

        # Documented fallback behavior:
        # If allow_stored_age_fallback=True is explicitly passed by callers requiring legacy compatibility,
        # valid non-negative fallback_age is returned.
        age_fallback_enabled = calculate_age(
            date_of_birth=None,
            reference_date=self.ref_date,
            allow_stored_age_fallback=True,
            fallback_age=32
        )
        self.assertEqual(age_fallback_enabled, 32)
        self.assertEqual(get_age_group(age_fallback_enabled), AGE_GROUP_25_44)

    def test_future_dob_safely_rejected(self):
        """
        Requirement 5: Reject/handle future DOB safely.
        Returns None and AGE_GROUP_UNKNOWN.
        """
        future_dob = datetime.date(2030, 1, 1)
        age = calculate_age(date_of_birth=future_dob, reference_date=self.ref_date)
        self.assertIsNone(age)
        self.assertEqual(get_age_group(age), AGE_GROUP_UNKNOWN)

        # Future DOB is safely rejected even if fallback_age is provided with allow_stored_age_fallback=True
        age_future_with_fallback = calculate_age(
            date_of_birth=future_dob,
            reference_date=self.ref_date,
            allow_stored_age_fallback=True,
            fallback_age=42
        )
        self.assertIsNone(age_future_with_fallback)

    def test_invalid_string_dob_safely_handled(self):
        """
        Unparseable date string returns None and AGE_GROUP_UNKNOWN by default.
        """
        age_none = calculate_age(date_of_birth="not-a-valid-date", reference_date=self.ref_date)
        self.assertIsNone(age_none)
        self.assertEqual(get_age_group(age_none), AGE_GROUP_UNKNOWN)

    def test_missing_and_invalid_demographic_inputs(self):
        """
        Handles negative ages, non-numeric values, None, etc. without throwing exceptions.
        """
        self.assertEqual(get_age_group(None), AGE_GROUP_UNKNOWN)
        self.assertEqual(get_age_group(-5), AGE_GROUP_UNKNOWN)
        self.assertEqual(get_age_group("invalid"), AGE_GROUP_UNKNOWN)

        self.assertIsNone(calculate_age(date_of_birth=None, fallback_age=None))
        self.assertIsNone(calculate_age(date_of_birth=None, fallback_age=-10))
        self.assertIsNone(calculate_age(date_of_birth=None, fallback_age="invalid"))

    def test_gender_choices_male_female_other(self):
        """
        Requirements 7 & 8: Use existing Patient.gender choices:
        MALE, FEMALE, OTHER.
        Do not create new gender values. Missing/invalid values normalize to UNKNOWN.
        """
        # Exact valid enum values
        self.assertEqual(normalize_gender('MALE'), GENDER_MALE)
        self.assertEqual(normalize_gender('FEMALE'), GENDER_FEMALE)
        self.assertEqual(normalize_gender('OTHER'), GENDER_OTHER)

        # Case-insensitivity & whitespace normalization for existing values
        self.assertEqual(normalize_gender(' male '), GENDER_MALE)
        self.assertEqual(normalize_gender('female'), GENDER_FEMALE)
        self.assertEqual(normalize_gender('Other'), GENDER_OTHER)

        # Missing / blank values safely classified as UNKNOWN
        self.assertEqual(normalize_gender(None), GENDER_UNKNOWN)
        self.assertEqual(normalize_gender(''), GENDER_UNKNOWN)
        self.assertEqual(normalize_gender('   '), GENDER_UNKNOWN)

        # Do not create new gender values; unrecognized values normalize to UNKNOWN
        self.assertEqual(normalize_gender('NON_BINARY'), GENDER_UNKNOWN)
        self.assertEqual(normalize_gender('UNKNOWN_VAL'), GENDER_UNKNOWN)


class DemographicSurveillanceIntegrationTestCase(TestCase):
    """
    Integration tests verifying demographic analysis across Patient records,
    DiseaseCase instances, serializers, and public health intelligence endpoints.
    """
    @classmethod
    def setUpTestData(cls):
        cls.state = State.objects.create(name='Karnataka', code='KA')
        cls.district = District.objects.create(state=cls.state, name='BBMP Central', code='KA-BU')
        cls.zone = Zone.objects.create(district=cls.district, name='East Zone', code='Z-EAST')
        cls.ward = Ward.objects.create(zone=cls.zone, ward_number=12, name='Indiranagar Ward', population=25000)

        cls.facility = Facility.objects.create(
            facility_code='UPHC-IND',
            facility_name='Indiranagar UPHC',
            facility_type='UPHC',
            district=cls.district,
            ward=cls.ward,
            state=cls.state
        )

        cls.today = datetime.date.today()

        # Patients covering various age boundaries and demographic configurations
        cls.p_infant = Patient.objects.create(
            patient_id='P-DEMO-01',
            name='Infant Patient',
            date_of_birth=datetime.date(cls.today.year - 2, 1, 1), # 2 years old
            age=2,
            gender='MALE',
            registered_at_facility=cls.facility,
            ward=cls.ward,
            district=cls.district
        )

        cls.p_child = Patient.objects.create(
            patient_id='P-DEMO-02',
            name='Child Patient',
            date_of_birth=datetime.date(cls.today.year - 10, 1, 1), # 10 years old
            age=10,
            gender='FEMALE',
            registered_at_facility=cls.facility,
            ward=cls.ward,
            district=cls.district
        )

        cls.p_youth = Patient.objects.create(
            patient_id='P-DEMO-03',
            name='Youth Patient',
            date_of_birth=datetime.date(cls.today.year - 20, 1, 1), # 20 years old
            age=20,
            gender='MALE',
            registered_at_facility=cls.facility,
            ward=cls.ward,
            district=cls.district
        )

        cls.p_adult = Patient.objects.create(
            patient_id='P-DEMO-04',
            name='Adult Patient',
            date_of_birth=datetime.date(cls.today.year - 35, 1, 1), # 35 years old
            age=35,
            gender='FEMALE',
            registered_at_facility=cls.facility,
            ward=cls.ward,
            district=cls.district
        )

        cls.p_middle = Patient.objects.create(
            patient_id='P-DEMO-05',
            name='Middle Aged Patient',
            date_of_birth=datetime.date(cls.today.year - 52, 1, 1), # 52 years old
            age=52,
            gender='OTHER',
            registered_at_facility=cls.facility,
            ward=cls.ward,
            district=cls.district
        )

        cls.p_senior = Patient.objects.create(
            patient_id='P-DEMO-06',
            name='Senior Patient',
            date_of_birth=datetime.date(cls.today.year - 68, 1, 1), # 68 years old
            age=68,
            gender='MALE',
            registered_at_facility=cls.facility,
            ward=cls.ward,
            district=cls.district
        )

        # Patient with missing date_of_birth (uses fallback age 40)
        cls.p_no_dob = Patient.objects.create(
            patient_id='P-DEMO-07',
            name='No DOB Patient',
            date_of_birth=None,
            age=40,
            gender='FEMALE',
            registered_at_facility=cls.facility,
            ward=cls.ward,
            district=cls.district
        )

        # Patient with missing DOB and invalid age (classified as UNKNOWN)
        cls.p_unknown = Patient.objects.create(
            patient_id='P-DEMO-08',
            name='Unknown Demo Patient',
            date_of_birth=None,
            age=-1,
            gender='',
            registered_at_facility=cls.facility,
            ward=cls.ward,
            district=cls.district
        )

        # Create DiseaseCase instances for current window
        cls.case_dengue_1 = DiseaseCase.objects.create(
            disease_name='Dengue',
            patient=cls.p_infant,
            facility=cls.facility,
            ward=cls.ward,
            report_date=cls.today - datetime.timedelta(days=2),
            severity='MILD'
        )

        cls.case_dengue_2 = DiseaseCase.objects.create(
            disease_name='Dengue',
            patient=cls.p_child,
            facility=cls.facility,
            ward=cls.ward,
            report_date=cls.today - datetime.timedelta(days=3),
            severity='MODERATE'
        )

        cls.case_dengue_3 = DiseaseCase.objects.create(
            disease_name='Dengue',
            patient=cls.p_adult,
            facility=cls.facility,
            ward=cls.ward,
            report_date=cls.today - datetime.timedelta(days=1),
            severity='SEVERE'
        )

        cls.case_dengue_4 = DiseaseCase.objects.create(
            disease_name='Dengue',
            patient=cls.p_senior,
            facility=cls.facility,
            ward=cls.ward,
            report_date=cls.today - datetime.timedelta(days=4),
            severity='SEVERE'
        )

        cls.case_malaria_1 = DiseaseCase.objects.create(
            disease_name='Malaria',
            patient=cls.p_youth,
            facility=cls.facility,
            ward=cls.ward,
            report_date=cls.today - datetime.timedelta(days=2),
            severity='MILD'
        )

        cls.case_malaria_2 = DiseaseCase.objects.create(
            disease_name='Malaria',
            patient=cls.p_middle,
            facility=cls.facility,
            ward=cls.ward,
            report_date=cls.today - datetime.timedelta(days=3),
            severity='MODERATE'
        )

        cls.case_fever_nodob = DiseaseCase.objects.create(
            disease_name='Fever',
            patient=cls.p_no_dob,
            facility=cls.facility,
            ward=cls.ward,
            report_date=cls.today - datetime.timedelta(days=1),
            severity='MILD'
        )

        cls.case_fever_unknown = DiseaseCase.objects.create(
            disease_name='Fever',
            patient=cls.p_unknown,
            facility=cls.facility,
            ward=cls.ward,
            report_date=cls.today - datetime.timedelta(days=2),
            severity='MILD'
        )

        # Users for API testing
        cls.admin_user = User.objects.create_user(
            username='admin_demo_tester',
            password='password123',
            role='HOSPITAL_ADMIN',
            assigned_facility=cls.facility
        )

        cls.district_user = User.objects.create_user(
            username='do_demo_tester',
            password='password123',
            role='DISTRICT_OFFICER',
            assigned_district=cls.district
        )

    def test_disease_case_serializer_demographics(self):
        """
        Verifies that DiseaseCaseSerializer correctly includes patient_age,
        patient_age_group, and patient_gender dynamically.
        """
        serializer = DiseaseCaseSerializer(self.case_dengue_1)
        data = serializer.data
        self.assertEqual(data['patient_age'], 2)
        self.assertEqual(data['patient_age_group'], AGE_GROUP_0_5)
        self.assertEqual(data['patient_gender'], GENDER_MALE)

        serializer_senior = DiseaseCaseSerializer(self.case_dengue_4)
        data_senior = serializer_senior.data
        self.assertEqual(data_senior['patient_age_group'], AGE_GROUP_60_PLUS)
        self.assertEqual(data_senior['patient_gender'], GENDER_MALE)

        # Patient without DOB: does not fabricate an age, returns explicit None and UNKNOWN
        serializer_nodob = DiseaseCaseSerializer(self.case_fever_nodob)
        data_nodob = serializer_nodob.data
        self.assertIsNone(data_nodob['patient_age'])
        self.assertEqual(data_nodob['patient_age_group'], AGE_GROUP_UNKNOWN)
        self.assertEqual(data_nodob['patient_gender'], GENDER_FEMALE)

        # Unknown demographics
        serializer_unknown = DiseaseCaseSerializer(self.case_fever_unknown)
        data_unknown = serializer_unknown.data
        self.assertIsNone(data_unknown['patient_age'])
        self.assertEqual(data_unknown['patient_age_group'], AGE_GROUP_UNKNOWN)
        self.assertEqual(data_unknown['patient_gender'], GENDER_UNKNOWN)

    def test_aggregate_demographics_service(self):
        """
        Verifies dataset-wide demographic aggregation across age groups and gender.
        """
        all_cases = DiseaseCase.objects.all()
        summary = aggregate_demographics(all_cases, reference_date=self.today)

        self.assertEqual(summary['total_cases'], 8)
        self.assertEqual(summary['age_groups'][AGE_GROUP_0_5], 1)    # Infant (2)
        self.assertEqual(summary['age_groups'][AGE_GROUP_6_14], 1)   # Child (10)
        self.assertEqual(summary['age_groups'][AGE_GROUP_15_24], 1)  # Youth (20)
        self.assertEqual(summary['age_groups'][AGE_GROUP_25_44], 1)  # Adult (35)
        self.assertEqual(summary['age_groups'][AGE_GROUP_45_59], 1)  # Middle (52)
        self.assertEqual(summary['age_groups'][AGE_GROUP_60_PLUS], 1)# Senior (68)
        self.assertEqual(summary['age_groups'][AGE_GROUP_UNKNOWN], 2)# No DOB (None) + Unknown (-1)

        self.assertEqual(summary['gender'][GENDER_MALE], 3)
        self.assertEqual(summary['gender'][GENDER_FEMALE], 3)
        self.assertEqual(summary['gender'][GENDER_OTHER], 1)
        self.assertEqual(summary['gender'][GENDER_UNKNOWN], 1)

        self.assertIsNotNone(summary['average_age'])
        self.assertEqual(summary['min_age'], 2)
        self.assertEqual(summary['max_age'], 68)

    def test_get_demographic_intelligence_service(self):
        """
        Tests the authoritative public health intelligence demographic service.
        """
        data = get_demographic_intelligence(
            facility_ids=[self.facility.id],
            disease_name='Dengue',
            as_of_date=self.today
        )

        self.assertIn('observation_period', data)
        self.assertIn('summary', data)
        self.assertIn('disease_demographics', data)

        summary = data['summary']
        self.assertEqual(summary['total_cases'], 4)
        self.assertEqual(summary['age_groups'][AGE_GROUP_0_5], 1)
        self.assertEqual(summary['age_groups'][AGE_GROUP_6_14], 1)
        self.assertEqual(summary['age_groups'][AGE_GROUP_25_44], 1)
        self.assertEqual(summary['age_groups'][AGE_GROUP_60_PLUS], 1)

    def test_calculate_disease_trends_contains_demographics(self):
        """
        Verifies calculate_disease_trends seamlessly returns demographic breakdowns.
        """
        trends = calculate_disease_trends(
            facility_ids=[self.facility.id],
            as_of_date=self.today,
            window_days=7
        )

        self.assertIn('demographics', trends['summary'])
        self.assertEqual(trends['summary']['demographics']['total_cases'], 8)

        # Each disease item contains its specific demographics
        for item in trends['disease_trends']:
            self.assertIn('demographics', item)
            self.assertIn('age_groups', item['demographics'])
            self.assertIn('gender', item['demographics'])

    def test_api_demographics_endpoint_authenticated(self):
        """
        Verifies GET /api/surveillance/intelligence/demographics/ and /api/intelligence/demographics/.
        """
        client = APIClient()
        client.force_authenticate(user=self.admin_user)

        res1 = client.get('/api/surveillance/intelligence/demographics/')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertIn('summary', res1.data)
        self.assertIn('disease_demographics', res1.data)
        self.assertEqual(res1.data['summary']['total_cases'], 8)

        # Alias route
        res2 = client.get('/api/intelligence/demographics/')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data['summary']['total_cases'], 8)

    def test_api_demographics_endpoint_scoping(self):
        """
        Verifies role-based scope enforcement on the demographics endpoint:
        Hospital Admin is prevented from requesting outside facility.
        """
        client = APIClient()
        client.force_authenticate(user=self.admin_user)

        # Requesting another facility ID outside assignment is forbidden
        res = client.get('/api/surveillance/intelligence/demographics/?facility=99999')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_demographic_filtering(self):
        """
        Tests demographic filtering utilities for age, gender, and combined criteria.
        """
        all_cases = DiseaseCase.objects.all()

        # Filter by age group 0-5
        infant_cases = filter_cases_by_demographics(all_cases, age_groups=[AGE_GROUP_0_5])
        self.assertEqual(infant_cases.count(), 1)
        self.assertEqual(infant_cases.first().patient, self.p_infant)

        # Filter by gender MALE
        male_cases = filter_cases_by_demographics(all_cases, genders=[GENDER_MALE])
        self.assertEqual(male_cases.count(), 3) # p_infant, p_youth, p_senior

        # Filter by combination: age group 25-44 AND gender FEMALE
        female_adults = filter_cases_by_demographics(
            all_cases,
            age_groups=[AGE_GROUP_25_44],
            genders=[GENDER_FEMALE]
        )
        self.assertEqual(female_adults.count(), 1) # p_adult (35 F) only, since p_no_dob has missing DOB (UNKNOWN)

        # Filter with criteria yielding 0 matches
        no_matches = filter_cases_by_demographics(
            all_cases,
            age_groups=[AGE_GROUP_0_5],
            genders=[GENDER_FEMALE]
        )
        self.assertEqual(no_matches.count(), 0)

    def test_age_gender_matrix(self):
        """
        Verifies generation of 2D cross-tabulation matrix of age groups x genders.
        """
        all_cases = DiseaseCase.objects.all()
        matrix = build_age_gender_matrix(all_cases, reference_date=self.today)

        # 0-5 has 1 MALE
        self.assertEqual(matrix[AGE_GROUP_0_5][GENDER_MALE], 1)
        self.assertEqual(matrix[AGE_GROUP_0_5][GENDER_FEMALE], 0)

        # 6-14 has 1 FEMALE
        self.assertEqual(matrix[AGE_GROUP_6_14][GENDER_FEMALE], 1)

        # 15-24 has 1 MALE
        self.assertEqual(matrix[AGE_GROUP_15_24][GENDER_MALE], 1)

        # 25-44 has 1 FEMALE (p_adult)
        self.assertEqual(matrix[AGE_GROUP_25_44][GENDER_FEMALE], 1)

        # 45-59 has 1 OTHER
        self.assertEqual(matrix[AGE_GROUP_45_59][GENDER_OTHER], 1)

        # 60+ has 1 MALE
        self.assertEqual(matrix[AGE_GROUP_60_PLUS][GENDER_MALE], 1)

        # UNKNOWN has 1 FEMALE (p_no_dob) and 1 UNKNOWN gender (p_unknown)
        self.assertEqual(matrix[AGE_GROUP_UNKNOWN][GENDER_FEMALE], 1)
        self.assertEqual(matrix[AGE_GROUP_UNKNOWN][GENDER_UNKNOWN], 1)

    def test_age_calculated_relative_to_disease_case_report_date_not_today(self):
        """
        Requirement 11: Add tests proving age is calculated relative to the
        DiseaseCase/report date rather than today's date.
        """
        # Patient born 2010-06-15
        patient = Patient.objects.create(
            patient_id='P-TIMETRAVEL-01',
            name='Historical Timeline Patient',
            date_of_birth=datetime.date(2010, 6, 15),
            age=30, # Stale stored registration age
            gender='FEMALE',
            registered_at_facility=self.facility,
            ward=self.ward,
            district=self.district
        )

        # Case 1 reported on 2015-06-15: exactly 5 completed years old at report_date
        case_at_age_5 = DiseaseCase.objects.create(
            disease_name='Dengue',
            patient=patient,
            facility=self.facility,
            ward=self.ward,
            report_date=datetime.date(2015, 6, 15),
            severity='MILD'
        )

        # Case 2 reported on 2024-06-15: exactly 14 completed years old at report_date
        case_at_age_14 = DiseaseCase.objects.create(
            disease_name='Dengue',
            patient=patient,
            facility=self.facility,
            ward=self.ward,
            report_date=datetime.date(2024, 6, 15),
            severity='MILD'
        )

        # Case 3 reported on 2026-06-15: exactly 16 completed years old at report_date
        case_at_age_16 = DiseaseCase.objects.create(
            disease_name='Dengue',
            patient=patient,
            facility=self.facility,
            ward=self.ward,
            report_date=datetime.date(2026, 6, 15),
            severity='MILD'
        )

        # If age were calculated relative to today's date, all 3 cases would have the exact
        # same age. Instead, each must evaluate strictly according to its report_date:
        age_1 = get_case_patient_age(case_at_age_5)
        demo_1 = get_case_demographics(case_at_age_5)
        self.assertEqual(age_1, 5)
        self.assertEqual(demo_1['age_group'], AGE_GROUP_0_5)

        age_2 = get_case_patient_age(case_at_age_14)
        demo_2 = get_case_demographics(case_at_age_14)
        self.assertEqual(age_2, 14)
        self.assertEqual(demo_2['age_group'], AGE_GROUP_6_14)

        age_3 = get_case_patient_age(case_at_age_16)
        demo_3 = get_case_demographics(case_at_age_16)
        self.assertEqual(age_3, 16)
        self.assertEqual(demo_3['age_group'], AGE_GROUP_15_24)

        # Serializer also reflects report_date-based age
        s1 = DiseaseCaseSerializer(case_at_age_5).data
        self.assertEqual(s1['patient_age'], 5)
        self.assertEqual(s1['patient_age_group'], AGE_GROUP_0_5)

        s2 = DiseaseCaseSerializer(case_at_age_14).data
        self.assertEqual(s2['patient_age'], 14)
        self.assertEqual(s2['patient_age_group'], AGE_GROUP_6_14)

        s3 = DiseaseCaseSerializer(case_at_age_16).data
        self.assertEqual(s3['patient_age'], 16)
        self.assertEqual(s3['patient_age_group'], AGE_GROUP_15_24)

    def test_stored_age_not_used_when_dob_available(self):
        """
        Requirement 3: Do NOT use the stored Patient.age as the primary source
        when date_of_birth is available because stored age can become stale.
        """
        patient_stale = Patient.objects.create(
            patient_id='P-STALE-01',
            name='Stale Age Patient',
            date_of_birth=datetime.date(2020, 1, 1), # 6 years old on 2026-01-01
            age=45, # Stale registration age stored in DB
            gender='MALE',
            registered_at_facility=self.facility,
            ward=self.ward,
            district=self.district
        )
        case = DiseaseCase.objects.create(
            disease_name='Dengue',
            patient=patient_stale,
            facility=self.facility,
            ward=self.ward,
            report_date=datetime.date(2026, 1, 1),
            severity='MILD'
        )
        calculated_age = get_case_patient_age(case)
        self.assertEqual(calculated_age, 6) # Calculated from DOB
        self.assertNotEqual(calculated_age, 45) # Stored age 45 is NOT used
        demo = get_case_demographics(case)
        self.assertEqual(demo['age_group'], AGE_GROUP_6_14)
        self.assertNotEqual(demo['age_group'], AGE_GROUP_45_59)


class PublicHealthIntelligenceDemographicAPIsTestCase(TestCase):
    """
    Comprehensive tests for demographic filtering across Public Health Intelligence APIs:
    - disease trends
    - historical disease analysis
    - disease/locality analysis
    - summary
    - forecast
    - seasonality

    Covers:
    1. disease + age_group
    2. disease + gender
    3. disease + age_group + gender (AND logic)
    4. invalid age_group -> 400
    5. invalid gender -> 400
    6. no demographic filters -> existing behavior
    7. Hospital Admin scope + demographic filters
    8. District Officer scope + demographic filters
    9. cross-facility request remains 403
    10. cross-district request remains 403
    11. dynamic age calculation relative to DiseaseCase.report_date
    """
    @classmethod
    def setUpTestData(cls):
        cls.state = State.objects.create(name='Karnataka', code='KA')
        cls.district_central = District.objects.create(state=cls.state, name='BBMP Central', code='KA-BU')
        cls.district_rural = District.objects.create(state=cls.state, name='Bengaluru Rural', code='KA-BR')

        cls.zone_central = Zone.objects.create(district=cls.district_central, name='Central Zone', code='Z-CEN')
        cls.zone_rural = Zone.objects.create(district=cls.district_rural, name='Rural Zone', code='Z-RUR')

        cls.ward_central = Ward.objects.create(zone=cls.zone_central, ward_number=10, name='Indiranagar', population=20000)
        cls.ward_rural = Ward.objects.create(zone=cls.zone_rural, ward_number=20, name='Varthur', population=15000)

        # Central Facilities
        cls.fac_central = Facility.objects.create(
            facility_code='FAC-CEN', facility_name='Central Hospital', facility_type='MAIN_HOSPITAL',
            district=cls.district_central, ward=cls.ward_central, state=cls.state
        )
        cls.fac_other = Facility.objects.create(
            facility_code='FAC-OTH', facility_name='Other Central Clinic', facility_type='NAMMA_CLINIC',
            district=cls.district_central, ward=cls.ward_central, state=cls.state
        )

        # Rural Facility
        cls.fac_rural = Facility.objects.create(
            facility_code='FAC-RUR', facility_name='Rural Health Centre', facility_type='RURAL_CLINIC',
            district=cls.district_rural, ward=cls.ward_rural, state=cls.state
        )

        # Users
        cls.user_hosp_admin = User.objects.create_user(
            username='api_admin_cen', password='Password123!', role='HOSPITAL_ADMIN',
            assigned_facility=cls.fac_central
        )
        cls.user_dist_officer = User.objects.create_user(
            username='api_officer_cen', password='Password123!', role='DISTRICT_OFFICER',
            assigned_district=cls.district_central
        )
        cls.user_rural_officer = User.objects.create_user(
            username='api_officer_rur', password='Password123!', role='DISTRICT_OFFICER',
            assigned_district=cls.district_rural
        )

        cls.ref_date = datetime.date(2026, 10, 4)

        # Patients with exact DOBs relative to 2026-10-04
        # P1: 0-5 MALE (2 yo)
        cls.p1 = Patient.objects.create(
            patient_id='PID-01', name='Patient Infant',
            date_of_birth=datetime.date(2024, 10, 4), age=2, gender='MALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central
        )
        # P2: 6-14 FEMALE (10 yo)
        cls.p2 = Patient.objects.create(
            patient_id='PID-02', name='Patient Child',
            date_of_birth=datetime.date(2016, 10, 4), age=10, gender='FEMALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central
        )
        # P3: 15-24 FEMALE (20 yo)
        cls.p3 = Patient.objects.create(
            patient_id='PID-03', name='Patient Youth',
            date_of_birth=datetime.date(2006, 10, 4), age=20, gender='FEMALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central
        )
        # P4: 25-44 FEMALE (30 yo)
        cls.p4 = Patient.objects.create(
            patient_id='PID-04', name='Patient Adult Female',
            date_of_birth=datetime.date(1996, 10, 4), age=30, gender='FEMALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central
        )
        # P5: 25-44 MALE (35 yo)
        cls.p5 = Patient.objects.create(
            patient_id='PID-05', name='Patient Adult Male',
            date_of_birth=datetime.date(1991, 10, 4), age=35, gender='MALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central
        )
        # P6: 45-59 OTHER (50 yo)
        cls.p6 = Patient.objects.create(
            patient_id='PID-06', name='Patient Middle Other',
            date_of_birth=datetime.date(1976, 10, 4), age=50, gender='OTHER',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central
        )
        # P7: 60+ MALE (70 yo)
        cls.p7 = Patient.objects.create(
            patient_id='PID-07', name='Patient Senior Male',
            date_of_birth=datetime.date(1956, 10, 4), age=70, gender='MALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central
        )

        # 7 Dengue Cases at fac_central on cls.ref_date
        cls.case1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p1, facility=cls.fac_central,
            ward=cls.ward_central, report_date=cls.ref_date, severity='MILD'
        )
        cls.case2 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p2, facility=cls.fac_central,
            ward=cls.ward_central, report_date=cls.ref_date, severity='MILD'
        )
        cls.case3 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p3, facility=cls.fac_central,
            ward=cls.ward_central, report_date=cls.ref_date, severity='MODERATE'
        )
        cls.case4 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p4, facility=cls.fac_central,
            ward=cls.ward_central, report_date=cls.ref_date, severity='SEVERE'
        )
        cls.case5 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p5, facility=cls.fac_central,
            ward=cls.ward_central, report_date=cls.ref_date, severity='SEVERE'
        )
        cls.case6 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p6, facility=cls.fac_central,
            ward=cls.ward_central, report_date=cls.ref_date, severity='MODERATE'
        )
        cls.case7 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p7, facility=cls.fac_central,
            ward=cls.ward_central, report_date=cls.ref_date, severity='MILD'
        )

        # Rural case (in district_rural)
        cls.p_rural = Patient.objects.create(
            patient_id='PID-RUR', name='Patient Rural',
            date_of_birth=datetime.date(2000, 1, 1), age=26, gender='FEMALE',
            district=cls.district_rural, ward=cls.ward_rural, registered_at_facility=cls.fac_rural
        )
        cls.case_rural = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_rural, facility=cls.fac_rural,
            ward=cls.ward_rural, report_date=cls.ref_date, severity='MILD'
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user_hosp_admin)

    # 1. disease + age_group
    def test_disease_and_age_group_filter(self):
        """
        Filters by ?disease=Dengue&age_group=15-24.
        Only Patient 3 (20 yo female) matches among the 7 Central cases.
        """
        # Disease trends
        res_trends = self.client.get(
            f"{reverse('intelligence_disease_trends')}?disease=Dengue&age_group=15-24&date={self.ref_date}"
        )
        self.assertEqual(res_trends.status_code, status.HTTP_200_OK)
        self.assertEqual(res_trends.data['summary']['total_current_cases'], 1)

        # Historical disease
        res_hist = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Dengue&age_group=15-24&date={self.ref_date}"
        )
        self.assertEqual(res_hist.status_code, status.HTTP_200_OK)
        self.assertEqual(res_hist.data['total_cases_in_history'], 1)

        # Disease by locality
        res_loc = self.client.get(
            f"{reverse('intelligence_disease_by_locality')}?disease=Dengue&age_group=15-24&date={self.ref_date}"
        )
        self.assertEqual(res_loc.status_code, status.HTTP_200_OK)
        self.assertEqual(res_loc.data['total_cases_in_period'], 1)

        # Summary
        res_sum = self.client.get(
            f"{reverse('intelligence_summary')}?disease=Dengue&age_group=15-24&date={self.ref_date}"
        )
        self.assertEqual(res_sum.status_code, status.HTTP_200_OK)
        self.assertEqual(res_sum.data['summary']['total_current_cases'], 1)

        # Forecast
        res_fc = self.client.get(
            f"{reverse('intelligence_forecast')}?disease=Dengue&age_group=15-24&date={self.ref_date}"
        )
        self.assertEqual(res_fc.status_code, status.HTTP_200_OK)
        self.assertEqual(res_fc.data['observation_period']['total_cases'], 1)

        # Seasonality
        res_seas = self.client.get(
            f"{reverse('intelligence_seasonality')}?disease=Dengue&age_group=15-24&date={self.ref_date}"
        )
        self.assertEqual(res_seas.status_code, status.HTTP_200_OK)
        self.assertEqual(res_seas.data['total_cases_analyzed'], 1)

    # 2. disease + gender
    def test_disease_and_gender_filter(self):
        """
        Filters by ?disease=Dengue&gender=FEMALE.
        Patients 2 (10 yo F), 3 (20 yo F), and 4 (30 yo F) match -> 3 cases.
        """
        # Disease trends
        res_trends = self.client.get(
            f"{reverse('intelligence_disease_trends')}?disease=Dengue&gender=FEMALE&date={self.ref_date}"
        )
        self.assertEqual(res_trends.status_code, status.HTTP_200_OK)
        self.assertEqual(res_trends.data['summary']['total_current_cases'], 3)

        # Historical disease
        res_hist = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Dengue&gender=FEMALE&date={self.ref_date}"
        )
        self.assertEqual(res_hist.status_code, status.HTTP_200_OK)
        self.assertEqual(res_hist.data['total_cases_in_history'], 3)

        # Locality
        res_loc = self.client.get(
            f"{reverse('intelligence_disease_by_locality')}?disease=Dengue&gender=FEMALE&date={self.ref_date}"
        )
        self.assertEqual(res_loc.status_code, status.HTTP_200_OK)
        self.assertEqual(res_loc.data['total_cases_in_period'], 3)

        # Summary
        res_sum = self.client.get(
            f"{reverse('intelligence_summary')}?disease=Dengue&gender=FEMALE&date={self.ref_date}"
        )
        self.assertEqual(res_sum.status_code, status.HTTP_200_OK)
        self.assertEqual(res_sum.data['summary']['total_current_cases'], 3)

        # Forecast
        res_fc = self.client.get(
            f"{reverse('intelligence_forecast')}?disease=Dengue&gender=FEMALE&date={self.ref_date}"
        )
        self.assertEqual(res_fc.status_code, status.HTTP_200_OK)
        self.assertEqual(res_fc.data['observation_period']['total_cases'], 3)

        # Seasonality
        res_seas = self.client.get(
            f"{reverse('intelligence_seasonality')}?disease=Dengue&gender=FEMALE&date={self.ref_date}"
        )
        self.assertEqual(res_seas.status_code, status.HTTP_200_OK)
        self.assertEqual(res_seas.data['total_cases_analyzed'], 3)

    # 3. disease + age_group + gender (AND logic)
    def test_disease_and_age_group_and_gender_and_logic(self):
        """
        Filters by ?disease=Dengue&age_group=25-44&gender=FEMALE.
        Only Patient 4 (30 yo F) matches. Patient 5 (35 yo M) is excluded by gender.
        """
        # Disease trends
        res_trends = self.client.get(
            f"{reverse('intelligence_disease_trends')}?disease=Dengue&age_group=25-44&gender=FEMALE&date={self.ref_date}"
        )
        self.assertEqual(res_trends.status_code, status.HTTP_200_OK)
        self.assertEqual(res_trends.data['summary']['total_current_cases'], 1)

        # Historical disease
        res_hist = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Dengue&age_group=25-44&gender=FEMALE&date={self.ref_date}"
        )
        self.assertEqual(res_hist.status_code, status.HTTP_200_OK)
        self.assertEqual(res_hist.data['total_cases_in_history'], 1)

        # Locality
        res_loc = self.client.get(
            f"{reverse('intelligence_disease_by_locality')}?disease=Dengue&age_group=25-44&gender=FEMALE&date={self.ref_date}"
        )
        self.assertEqual(res_loc.status_code, status.HTTP_200_OK)
        self.assertEqual(res_loc.data['total_cases_in_period'], 1)

        # Summary
        res_sum = self.client.get(
            f"{reverse('intelligence_summary')}?disease=Dengue&age_group=25-44&gender=FEMALE&date={self.ref_date}"
        )
        self.assertEqual(res_sum.status_code, status.HTTP_200_OK)
        self.assertEqual(res_sum.data['summary']['total_current_cases'], 1)

        # Forecast
        res_fc = self.client.get(
            f"{reverse('intelligence_forecast')}?disease=Dengue&age_group=25-44&gender=FEMALE&date={self.ref_date}"
        )
        self.assertEqual(res_fc.status_code, status.HTTP_200_OK)
        self.assertEqual(res_fc.data['observation_period']['total_cases'], 1)

        # Seasonality
        res_seas = self.client.get(
            f"{reverse('intelligence_seasonality')}?disease=Dengue&age_group=25-44&gender=FEMALE&date={self.ref_date}"
        )
        self.assertEqual(res_seas.status_code, status.HTTP_200_OK)
        self.assertEqual(res_seas.data['total_cases_analyzed'], 1)

    # 4. invalid age_group -> 400
    def test_invalid_age_group_bad_request(self):
        """
        Invalid age_group returns HTTP 400 Bad Request across all endpoints.
        """
        invalid_groups = ['10-20', 'invalid_group', 'senior', '0-10']
        endpoints = [
            'intelligence_disease_trends',
            'intelligence_historical_disease',
            'intelligence_disease_by_locality',
            'intelligence_summary',
            'intelligence_forecast',
            'intelligence_seasonality',
        ]
        for ep in endpoints:
            for bad_ag in invalid_groups:
                res = self.client.get(f"{reverse(ep)}?disease=Dengue&age_group={bad_ag}")
                self.assertEqual(
                    res.status_code, status.HTTP_400_BAD_REQUEST,
                    f"Endpoint {ep} did not return 400 for age_group={bad_ag}"
                )
                self.assertIn('age_group', str(res.data))

    # 5. invalid gender -> 400
    def test_invalid_gender_bad_request(self):
        """
        Invalid gender values (not in MALE, FEMALE, OTHER) return HTTP 400 Bad Request.
        """
        invalid_genders = ['UNKNOWN', 'RANDOM', 'NON_BINARY', 'M']
        endpoints = [
            'intelligence_disease_trends',
            'intelligence_historical_disease',
            'intelligence_disease_by_locality',
            'intelligence_summary',
            'intelligence_forecast',
            'intelligence_seasonality',
        ]
        for ep in endpoints:
            for bad_g in invalid_genders:
                res = self.client.get(f"{reverse(ep)}?disease=Dengue&gender={bad_g}")
                self.assertEqual(
                    res.status_code, status.HTTP_400_BAD_REQUEST,
                    f"Endpoint {ep} did not return 400 for gender={bad_g}"
                )
                self.assertIn('gender', str(res.data))

    # 6. no demographic filters -> existing behavior
    def test_no_demographic_filters_existing_behavior(self):
        """
        Existing API requests without demographic filters behave exactly as before.
        All 7 central cases are returned without demographic restriction.
        """
        res_trends = self.client.get(
            f"{reverse('intelligence_disease_trends')}?disease=Dengue&date={self.ref_date}"
        )
        self.assertEqual(res_trends.status_code, status.HTTP_200_OK)
        self.assertEqual(res_trends.data['summary']['total_current_cases'], 7)

        res_hist = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Dengue&date={self.ref_date}"
        )
        self.assertEqual(res_hist.status_code, status.HTTP_200_OK)
        self.assertEqual(res_hist.data['total_cases_in_history'], 7)


        res_loc = self.client.get(
            f"{reverse('intelligence_disease_by_locality')}?disease=Dengue&date={self.ref_date}"
        )
        self.assertEqual(res_loc.status_code, status.HTTP_200_OK)
        self.assertEqual(res_loc.data['total_cases_in_period'], 7)


        res_sum = self.client.get(
            f"{reverse('intelligence_summary')}?disease=Dengue&date={self.ref_date}"
        )
        self.assertEqual(res_sum.status_code, status.HTTP_200_OK)
        self.assertEqual(res_sum.data['summary']['total_current_cases'], 7)

        res_fc = self.client.get(
            f"{reverse('intelligence_forecast')}?disease=Dengue&date={self.ref_date}"
        )
        self.assertEqual(res_fc.status_code, status.HTTP_200_OK)
        self.assertEqual(res_fc.data['observation_period']['total_cases'], 7)

        res_seas = self.client.get(
            f"{reverse('intelligence_seasonality')}?disease=Dengue&date={self.ref_date}"
        )
        self.assertEqual(res_seas.status_code, status.HTTP_200_OK)
        self.assertEqual(res_seas.data['total_cases_analyzed'], 7)


    # 7. Hospital Admin scope + demographic filters
    def test_hospital_admin_scope_with_demographic_filters(self):
        """
        Hospital Admin querying assigned facility with demographic filters succeeds.
        ?disease=Dengue&facility=<authorized_id>&age_group=15-24&gender=FEMALE
        """
        res = self.client.get(
            f"{reverse('intelligence_disease_trends')}?disease=Dengue&facility={self.fac_central.id}&age_group=15-24&gender=FEMALE&date={self.ref_date}"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['summary']['total_current_cases'], 1)

    # 8. District Officer scope + demographic filters
    def test_district_officer_scope_with_demographic_filters(self):
        """
        District Officer querying assigned district with demographic filters succeeds.
        ?disease=Dengue&district=<authorized_id>&age_group=25-44&gender=MALE
        """
        self.client.force_authenticate(user=self.user_dist_officer)
        res = self.client.get(
            f"{reverse('intelligence_disease_trends')}?disease=Dengue&district={self.district_central.id}&age_group=25-44&gender=MALE&date={self.ref_date}"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Matches Patient 5 (35 yo M)
        self.assertEqual(res.data['summary']['total_current_cases'], 1)

    # 9. cross-facility request remains 403
    def test_cross_facility_request_forbidden(self):
        """
        Hospital Admin requesting unauthorized facility returns HTTP 403 Forbidden.
        Demographic filters must NEVER bypass facility authorization.
        """
        endpoints = [
            'intelligence_disease_trends',
            'intelligence_historical_disease',
            'intelligence_disease_by_locality',
            'intelligence_summary',
            'intelligence_forecast',
            'intelligence_seasonality',
        ]
        for ep in endpoints:
            # Valid demographic filter but unauthorized facility
            res1 = self.client.get(
                f"{reverse(ep)}?facility={self.fac_other.id}&disease=Dengue&age_group=15-24&gender=FEMALE"
            )
            self.assertEqual(
                res1.status_code, status.HTTP_403_FORBIDDEN,
                f"Endpoint {ep} did not return 403 for unauthorized facility"
            )

            # Invalid demographic filter on unauthorized facility MUST still return 403
            res2 = self.client.get(
                f"{reverse(ep)}?facility={self.fac_other.id}&disease=Dengue&age_group=INVALID"
            )
            self.assertEqual(
                res2.status_code, status.HTTP_403_FORBIDDEN,
                f"Endpoint {ep} allowed bypass of 403 with invalid demographic parameter"
            )

    # 10. cross-district request remains 403
    def test_cross_district_request_forbidden(self):
        """
        District Officer requesting unauthorized district returns HTTP 403 Forbidden.
        Demographic filters must NEVER bypass district authorization.
        """
        self.client.force_authenticate(user=self.user_dist_officer)
        endpoints = [
            'intelligence_disease_trends',
            'intelligence_historical_disease',
            'intelligence_disease_by_locality',
            'intelligence_summary',
            'intelligence_forecast',
            'intelligence_seasonality',
        ]
        for ep in endpoints:
            # Valid demographic filter but unauthorized district
            res1 = self.client.get(
                f"{reverse(ep)}?district={self.district_rural.id}&disease=Dengue&age_group=15-24&gender=FEMALE"
            )
            self.assertEqual(
                res1.status_code, status.HTTP_403_FORBIDDEN,
                f"Endpoint {ep} did not return 403 for unauthorized district"
            )

            # Invalid demographic filter on unauthorized district MUST still return 403
            res2 = self.client.get(
                f"{reverse(ep)}?district={self.district_rural.id}&disease=Dengue&gender=INVALID"
            )
            self.assertEqual(
                res2.status_code, status.HTTP_403_FORBIDDEN,
                f"Endpoint {ep} allowed bypass of 403 with invalid gender parameter"
            )

    # 11. Dynamic age calculation relative to DiseaseCase.report_date
    def test_dynamic_age_calculation_relative_to_case_report_date_in_api(self):
        """
        CRITICAL: Age must be calculated relative to each DiseaseCase.report_date.
        Patient born on 2010-10-04:
        - Case reported on 2024-10-04: Age is 14 -> Age group 6-14
        - Case reported on 2026-10-04: Age is 16 -> Age group 15-24
        """
        p_aging = Patient.objects.create(
            patient_id='P-AGING-01', name='Aging Patient',
            date_of_birth=datetime.date(2010, 10, 4), age=50, # Deliberately stale DB age
            gender='FEMALE', district=self.district_central, ward=self.ward_central,
            registered_at_facility=self.fac_central
        )
        # Case in 2024: age 14 (6-14)
        DiseaseCase.objects.create(
            disease_name='Typhoid', patient=p_aging, facility=self.fac_central,
            ward=self.ward_central, report_date=datetime.date(2024, 10, 4), severity='MILD'
        )
        # Case in 2026: age 16 (15-24)
        DiseaseCase.objects.create(
            disease_name='Typhoid', patient=p_aging, facility=self.fac_central,
            ward=self.ward_central, report_date=datetime.date(2026, 10, 4), severity='MILD'
        )

        # Filtering by 15-24 on 2026-10-04 reflects the 2026 case (16 yo)
        res_15_24 = self.client.get(
            f"{reverse('intelligence_disease_trends')}?disease=Typhoid&age_group=15-24&date=2026-10-04&days=7"
        )
        self.assertEqual(res_15_24.status_code, status.HTTP_200_OK)
        self.assertEqual(res_15_24.data['summary']['total_current_cases'], 1)

        # Filtering by 6-14 on 2026-10-04 does not match the 2026 case (since it's age 16)
        res_6_14_recent = self.client.get(
            f"{reverse('intelligence_disease_trends')}?disease=Typhoid&age_group=6-14&date=2026-10-04&days=7"
        )
        self.assertEqual(res_6_14_recent.status_code, status.HTTP_200_OK)
        self.assertEqual(res_6_14_recent.data['summary']['total_current_cases'], 0)

        # Stale Patient.age (50) is never used: filtering by 45-59 returns 0 cases
        res_45_59 = self.client.get(
            f"{reverse('intelligence_disease_trends')}?disease=Typhoid&age_group=45-59&date=2026-10-04&days=7"
        )
        self.assertEqual(res_45_59.status_code, status.HTTP_200_OK)
        self.assertEqual(res_45_59.data['summary']['total_current_cases'], 0)


class PublicHealthHistoricalDemographicsTestCase(TestCase):
    """
    Comprehensive tests for Demographic Historical Analysis:
    Verifies all 17 required scenarios:
    1. Historical age-group counts.
    2. Historical gender counts.
    3. Age + gender matrix.
    4. Monthly demographic trends.
    5. Disease + age filter.
    6. Disease + gender filter.
    7. Disease + age + gender filter.
    8. Facility + demographic filter.
    9. District + demographic filter.
    10. Unauthorized facility + demographic filter -> 403.
    11. Unauthorized district + demographic filter -> 403.
    12. Missing DOB -> UNKNOWN.
    13. Missing gender -> UNKNOWN.
    14. Age calculated using DiseaseCase.report_date.
    15. All age groups are represented.
    16. Existing historical response fields remain unchanged.
    17. No demographic filters -> existing behavior.
    """
    @classmethod
    def setUpTestData(cls):
        cls.state = State.objects.create(name='Karnataka', code='KA')
        cls.district_central = District.objects.create(state=cls.state, name='BBMP Central', code='KA-BU')
        cls.district_rural = District.objects.create(state=cls.state, name='Bengaluru Rural', code='KA-BR')

        cls.zone_central = Zone.objects.create(district=cls.district_central, name='Central Zone', code='Z-CEN')
        cls.zone_rural = Zone.objects.create(district=cls.district_rural, name='Rural Zone', code='Z-RUR')

        cls.ward_central = Ward.objects.create(zone=cls.zone_central, ward_number=10, name='Indiranagar', population=20000)
        cls.ward_rural = Ward.objects.create(zone=cls.zone_rural, ward_number=20, name='Varthur', population=15000)

        # Facilities
        cls.fac_central_1 = Facility.objects.create(
            facility_code='HOSP-C1', facility_name='Victoria General Hospital', facility_type='MAIN_HOSPITAL',
            district=cls.district_central, ward=cls.ward_central, state=cls.state
        )
        cls.fac_central_2 = Facility.objects.create(
            facility_code='CLINIC-C2', facility_name='Indiranagar Namma Clinic', facility_type='NAMMA_CLINIC',
            district=cls.district_central, ward=cls.ward_central, state=cls.state
        )
        cls.fac_rural = Facility.objects.create(
            facility_code='RURAL-R1', facility_name='Varthur Health Centre', facility_type='RURAL_CLINIC',
            district=cls.district_rural, ward=cls.ward_rural, state=cls.state
        )

        # Users
        cls.admin_central_1 = User.objects.create_user(
            username='hist_admin_c1', password='Password123!', role='HOSPITAL_ADMIN',
            assigned_facility=cls.fac_central_1
        )
        cls.officer_central = User.objects.create_user(
            username='hist_officer_c', password='Password123!', role='DISTRICT_OFFICER',
            assigned_district=cls.district_central
        )
        cls.officer_rural = User.objects.create_user(
            username='hist_officer_r', password='Password123!', role='DISTRICT_OFFICER',
            assigned_district=cls.district_rural
        )

        # Fixed reference date: 2026-10-04
        cls.as_of = datetime.date(2026, 10, 4)

        # Deterministic Patients across age boundaries, genders, and edge cases
        # 0-5 MALE (2 yo in 2026)
        cls.p_0_5 = Patient.objects.create(
            patient_id='P-H01', name='Infant Boy',
            date_of_birth=datetime.date(2024, 5, 15), age=2, gender='MALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central_1
        )
        # 6-14 FEMALE (10 yo in 2026)
        cls.p_6_14 = Patient.objects.create(
            patient_id='P-H02', name='School Girl',
            date_of_birth=datetime.date(2016, 5, 15), age=10, gender='FEMALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central_1
        )
        # 15-24 FEMALE (20 yo in 2026)
        cls.p_15_24 = Patient.objects.create(
            patient_id='P-H03', name='College Student',
            date_of_birth=datetime.date(2006, 5, 15), age=20, gender='FEMALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central_1
        )
        # 25-44 MALE (30 yo in 2026)
        cls.p_25_44_m = Patient.objects.create(
            patient_id='P-H04', name='Adult Male',
            date_of_birth=datetime.date(1996, 5, 15), age=30, gender='MALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central_1
        )
        # 25-44 FEMALE (35 yo in 2026)
        cls.p_25_44_f = Patient.objects.create(
            patient_id='P-H05', name='Adult Female',
            date_of_birth=datetime.date(1991, 5, 15), age=35, gender='FEMALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central_1
        )
        # 45-59 OTHER (50 yo in 2026)
        cls.p_45_59 = Patient.objects.create(
            patient_id='P-H06', name='Middle Aged Other',
            date_of_birth=datetime.date(1976, 5, 15), age=50, gender='OTHER',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central_1
        )
        # 60+ MALE (70 yo in 2026)
        cls.p_60_plus = Patient.objects.create(
            patient_id='P-H07', name='Elderly Male',
            date_of_birth=datetime.date(1956, 5, 15), age=70, gender='MALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central_1
        )
        # Missing DOB Patient (null DOB -> age UNKNOWN, FEMALE)
        cls.p_no_dob = Patient.objects.create(
            patient_id='P-H08', name='Missing DOB Patient',
            date_of_birth=None, age=30, gender='FEMALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central_1
        )
        # Missing Gender Patient (26 yo in 2026, blank gender -> gender UNKNOWN)
        cls.p_no_gender = Patient.objects.create(
            patient_id='P-H09', name='Missing Gender Patient',
            date_of_birth=datetime.date(2000, 5, 15), age=26, gender='',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central_1
        )
        # Aging Patient for report_date relative calculation
        # Born 2010-07-01: age 14 on 2024-07-01 (6-14), age 16 on 2026-07-01 (15-24)
        cls.p_aging = Patient.objects.create(
            patient_id='P-H10', name='Aging Multi-Year Patient',
            date_of_birth=datetime.date(2010, 7, 1), age=99, gender='FEMALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central_1
        )
        # Rural Patient
        cls.p_rural = Patient.objects.create(
            patient_id='P-H11', name='Rural Patient',
            date_of_birth=datetime.date(1995, 1, 1), age=31, gender='FEMALE',
            district=cls.district_rural, ward=cls.ward_rural, registered_at_facility=cls.fac_rural
        )

        # -----------------------------------------------------------------------
        # Create Historical Disease Cases across 6 calendar months (May - Oct 2026)
        # -----------------------------------------------------------------------
        # May 2026 (2026-05): 1 Dengue case (P_0_5: 0-5 MALE)
        cls.c_may_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_0_5, facility=cls.fac_central_1,
            ward=cls.ward_central, report_date=datetime.date(2026, 5, 10), severity='MILD'
        )

        # June 2026 (2026-06): 1 Dengue case (P_6_14: 6-14 FEMALE)
        cls.c_jun_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_6_14, facility=cls.fac_central_1,
            ward=cls.ward_central, report_date=datetime.date(2026, 6, 12), severity='MODERATE'
        )

        # July 2026 (2026-07): 2 Dengue cases
        # - P_15_24: 15-24 FEMALE
        # - P_AGING: 16 yo on report_date -> 15-24 FEMALE
        cls.c_jul_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_15_24, facility=cls.fac_central_1,
            ward=cls.ward_central, report_date=datetime.date(2026, 7, 15), severity='MILD'
        )
        cls.c_jul_2 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_aging, facility=cls.fac_central_1,
            ward=cls.ward_central, report_date=datetime.date(2026, 7, 20), severity='SEVERE'
        )

        # August 2026 (2026-08): 2 Dengue cases
        # - P_25_44_F: 25-44 FEMALE
        # - P_NO_GENDER: 26 yo -> 25-44, UNKNOWN gender
        cls.c_aug_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_25_44_f, facility=cls.fac_central_1,
            ward=cls.ward_central, report_date=datetime.date(2026, 8, 10), severity='MODERATE'
        )
        cls.c_aug_2 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_no_gender, facility=cls.fac_central_1,
            ward=cls.ward_central, report_date=datetime.date(2026, 8, 25), severity='MILD'
        )

        # September 2026 (2026-09): 2 Dengue cases at fac_central_1
        # - P_25_44_M: 25-44 MALE
        # - P_NO_DOB: UNKNOWN age, FEMALE
        cls.c_sep_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_25_44_m, facility=cls.fac_central_1,
            ward=cls.ward_central, report_date=datetime.date(2026, 9, 5), severity='SEVERE'
        )
        cls.c_sep_2 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_no_dob, facility=cls.fac_central_1,
            ward=cls.ward_central, report_date=datetime.date(2026, 9, 20), severity='MILD'
        )

        # September 2026: 1 Dengue case at fac_central_2 (P_25_44_F)
        cls.c_sep_fac2 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_25_44_f, facility=cls.fac_central_2,
            ward=cls.ward_central, report_date=datetime.date(2026, 9, 15), severity='MILD'
        )

        # October 2026 (2026-10): 2 Dengue cases at fac_central_1
        # - P_45_59: 45-59 OTHER
        # - P_60_PLUS: 60+ MALE
        cls.c_oct_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_45_59, facility=cls.fac_central_1,
            ward=cls.ward_central, report_date=datetime.date(2026, 10, 1), severity='MILD'
        )
        cls.c_oct_2 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_60_plus, facility=cls.fac_central_1,
            ward=cls.ward_central, report_date=datetime.date(2026, 10, 3), severity='MILD'
        )

        # Malaria case at fac_central_1 (different disease)
        cls.c_malaria = DiseaseCase.objects.create(
            disease_name='Malaria', patient=cls.p_0_5, facility=cls.fac_central_1,
            ward=cls.ward_central, report_date=datetime.date(2026, 9, 18), severity='MILD'
        )

        # Rural Dengue case at fac_rural (different district)
        cls.c_rural_dengue = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_rural, facility=cls.fac_rural,
            ward=cls.ward_rural, report_date=datetime.date(2026, 9, 15), severity='MILD'
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_central_1)

    # 1. Historical age-group counts
    def test_01_historical_age_group_counts(self):
        """
        Verifies historical counts grouped by age group across the observation window.
        """
        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Dengue&date={self.as_of}&months=6"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('historical_age_groups', res.data)

        age_groups = res.data['historical_age_groups']
        # Map age_group to total_cases
        ag_map = {item['age_group']: item['total_cases'] for item in age_groups}

        # fac_central_1 Dengue cases:
        # 0-5: 1 (May)
        # 6-14: 1 (Jun)
        # 15-24: 2 (Jul: p_15_24, p_aging)
        # 25-44: 2 (Aug: p_25_44_f, p_no_gender) + 1 (Sep: p_25_44_m) = 3
        # 45-59: 1 (Oct: p_45_59)
        # 60+: 1 (Oct: p_60_plus)
        # UNKNOWN: 1 (Sep: p_no_dob)
        self.assertEqual(ag_map['0-5'], 1)
        self.assertEqual(ag_map['6-14'], 1)
        self.assertEqual(ag_map['15-24'], 2)
        self.assertEqual(ag_map['25-44'], 3)
        self.assertEqual(ag_map['45-59'], 1)
        self.assertEqual(ag_map['60+'], 1)
        self.assertEqual(ag_map['UNKNOWN'], 1)

        # Every age group item has monthly_counts spanning all 6 months
        for item in age_groups:
            self.assertEqual(len(item['monthly_counts']), 6)
            self.assertEqual(sum(m['count'] for m in item['monthly_counts']), item['total_cases'])

    # 2. Historical gender counts
    def test_02_historical_gender_counts(self):
        """
        Verifies historical gender distribution including MALE, FEMALE, OTHER, and UNKNOWN.
        """
        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Dengue&date={self.as_of}&months=6"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('historical_gender', res.data)

        genders = res.data['historical_gender']
        g_map = {item['gender']: item['total_cases'] for item in genders}

        # fac_central_1 Dengue cases by gender:
        # MALE: p_0_5 (May), p_25_44_m (Sep), p_60_plus (Oct) = 3
        # FEMALE: p_6_14 (Jun), p_15_24 (Jul), p_aging (Jul), p_25_44_f (Aug), p_no_dob (Sep) = 5
        # OTHER: p_45_59 (Oct) = 1
        # UNKNOWN: p_no_gender (Aug) = 1
        self.assertEqual(g_map['MALE'], 3)
        self.assertEqual(g_map['FEMALE'], 5)
        self.assertEqual(g_map['OTHER'], 1)
        self.assertEqual(g_map['UNKNOWN'], 1)

        # Monthly counts match total
        for item in genders:
            self.assertEqual(len(item['monthly_counts']), 6)
            self.assertEqual(sum(m['count'] for m in item['monthly_counts']), item['total_cases'])

    # 3. Age + gender matrix
    def test_03_age_gender_matrix(self):
        """
        Verifies the 2D cross-tabulation matrix of age groups x genders across historical data.
        """
        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Dengue&date={self.as_of}&months=6"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('age_gender_matrix', res.data)

        matrix = res.data['age_gender_matrix']
        # Check specific cross-tabulations
        self.assertEqual(matrix['0-5']['MALE'], 1)
        self.assertEqual(matrix['0-5']['FEMALE'], 0)
        self.assertEqual(matrix['6-14']['FEMALE'], 1)
        self.assertEqual(matrix['15-24']['FEMALE'], 2)
        self.assertEqual(matrix['25-44']['FEMALE'], 1) # p_25_44_f
        self.assertEqual(matrix['25-44']['MALE'], 1)   # p_25_44_m
        self.assertEqual(matrix['25-44']['UNKNOWN'], 1)# p_no_gender
        self.assertEqual(matrix['45-59']['OTHER'], 1)  # p_45_59
        self.assertEqual(matrix['60+']['MALE'], 1)     # p_60_plus
        self.assertEqual(matrix['UNKNOWN']['FEMALE'], 1)# p_no_dob

    # 4. Monthly demographic trends
    def test_04_monthly_demographic_trends(self):
        """
        Verifies monthly demographic case counts with age_groups and gender breakdown per month.
        """
        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Dengue&date={self.as_of}&months=6"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('monthly_demographic_trends', res.data)

        trends = res.data['monthly_demographic_trends']
        self.assertEqual(len(trends), 6)

        # Map trends by month
        trend_map = {t['month']: t for t in trends}

        # May: 1 case (0-5, MALE)
        may = trend_map['2026-05']
        self.assertEqual(may['total_cases'], 1)
        self.assertEqual(may['age_groups']['0-5'], 1)
        self.assertEqual(may['gender']['MALE'], 1)

        # July: 2 cases (both 15-24, FEMALE)
        jul = trend_map['2026-07']
        self.assertEqual(jul['total_cases'], 2)
        self.assertEqual(jul['age_groups']['15-24'], 2)
        self.assertEqual(jul['gender']['FEMALE'], 2)

        # August: 2 cases (both 25-44: 1 FEMALE, 1 UNKNOWN gender)
        aug = trend_map['2026-08']
        self.assertEqual(aug['total_cases'], 2)
        self.assertEqual(aug['age_groups']['25-44'], 2)
        self.assertEqual(aug['gender']['FEMALE'], 1)
        self.assertEqual(aug['gender']['UNKNOWN'], 1)

        # October: 2 cases (1 45-59 OTHER, 1 60+ MALE)
        oct_m = trend_map['2026-10']
        self.assertEqual(oct_m['total_cases'], 2)
        self.assertEqual(oct_m['age_groups']['45-59'], 1)
        self.assertEqual(oct_m['age_groups']['60+'], 1)
        self.assertEqual(oct_m['gender']['OTHER'], 1)
        self.assertEqual(oct_m['gender']['MALE'], 1)

    # 5. Disease + age filter
    def test_05_disease_and_age_filter(self):
        """
        ?disease=Dengue&age_group=15-24 filters strictly to 15-24 Dengue cases.
        """
        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Dengue&age_group=15-24&date={self.as_of}&months=6"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Total cases in history = 2 (p_15_24 and p_aging in July)
        self.assertEqual(res.data['total_cases_in_history'], 2)

        ag_map = {item['age_group']: item['total_cases'] for item in res.data['historical_age_groups']}
        self.assertEqual(ag_map['15-24'], 2)
        self.assertEqual(ag_map['0-5'], 0)
        self.assertEqual(ag_map['25-44'], 0)

    # 6. Disease + gender filter
    def test_06_disease_and_gender_filter(self):
        """
        ?disease=Dengue&gender=MALE filters strictly to MALE Dengue cases.
        """
        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Dengue&gender=MALE&date={self.as_of}&months=6"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Total cases in history = 3 (May: p_0_5, Sep: p_25_44_m, Oct: p_60_plus)
        self.assertEqual(res.data['total_cases_in_history'], 3)

        g_map = {item['gender']: item['total_cases'] for item in res.data['historical_gender']}
        self.assertEqual(g_map['MALE'], 3)
        self.assertEqual(g_map['FEMALE'], 0)
        self.assertEqual(g_map['OTHER'], 0)

    # 7. Disease + age + gender filter
    def test_07_disease_and_age_and_gender_filter(self):
        """
        ?disease=Dengue&age_group=25-44&gender=MALE filters by AND logic (p_25_44_m only).
        """
        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Dengue&age_group=25-44&gender=MALE&date={self.as_of}&months=6"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_cases_in_history'], 1)
        matrix = res.data['age_gender_matrix']
        self.assertEqual(matrix['25-44']['MALE'], 1)
        self.assertEqual(matrix['25-44']['FEMALE'], 0)

    # 8. Facility + demographic filter
    def test_08_facility_and_demographic_filter(self):
        """
        Hospital Admin querying assigned facility with demographic filter succeeds.
        ?disease=Dengue&facility=<id>&age_group=0-5&gender=MALE
        """
        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Dengue&facility={self.fac_central_1.id}&age_group=0-5&gender=MALE&date={self.as_of}&months=6"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_cases_in_history'], 1)

    # 9. District + demographic filter
    def test_09_district_and_demographic_filter(self):
        """
        District Officer querying assigned district with demographic filter includes cases
        across all facilities in that district.
        """
        self.client.force_authenticate(user=self.officer_central)
        # Query Dengue + age_group=25-44 + gender=FEMALE in district_central
        # Matches p_25_44_f at fac_central_1 (Aug) AND p_25_44_f at fac_central_2 (Sep) = 2 cases
        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Dengue&district={self.district_central.id}&age_group=25-44&gender=FEMALE&date={self.as_of}&months=6"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_cases_in_history'], 2)

    # 10. Unauthorized facility + demographic filter -> 403
    def test_10_unauthorized_facility_and_demographic_filter_forbidden(self):
        """
        Hospital Admin requesting another facility returns HTTP 403 Forbidden.
        Demographic filters must never bypass authorization.
        """
        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?facility={self.fac_central_2.id}&disease=Dengue&age_group=25-44&gender=FEMALE"
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 11. Unauthorized district + demographic filter -> 403
    def test_11_unauthorized_district_and_demographic_filter_forbidden(self):
        """
        District Officer requesting another district returns HTTP 403 Forbidden.
        Demographic filters must never bypass authorization.
        """
        self.client.force_authenticate(user=self.officer_central)
        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?district={self.district_rural.id}&disease=Dengue&age_group=25-44&gender=FEMALE"
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 12. Missing DOB -> UNKNOWN
    def test_12_missing_dob_classified_as_unknown(self):
        """
        Cases with missing/invalid DOB are classified safely as UNKNOWN age group.
        """
        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Dengue&date={self.as_of}&months=6"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        matrix = res.data['age_gender_matrix']
        self.assertIn('UNKNOWN', matrix)
        self.assertEqual(matrix['UNKNOWN']['FEMALE'], 1)

    # 13. Missing gender -> UNKNOWN
    def test_13_missing_gender_classified_as_unknown(self):
        """
        Cases with missing/blank gender are classified safely as UNKNOWN gender.
        """
        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Dengue&date={self.as_of}&months=6"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        matrix = res.data['age_gender_matrix']
        self.assertEqual(matrix['25-44']['UNKNOWN'], 1)

    # 14. Age calculated using DiseaseCase.report_date
    def test_14_age_calculated_using_case_report_date(self):
        """
        Age is calculated relative to each individual DiseaseCase.report_date:
        p_aging born on 2010-07-01:
        On report_date 2026-07-20: Age is 16 completed years (age_group 15-24).
        It does not use today's date or static DB age.
        """
        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Dengue&date={self.as_of}&months=6"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        trends = {t['month']: t for t in res.data['monthly_demographic_trends']}
        jul = trends['2026-07']
        # July includes p_15_24 (20 yo) and p_aging (16 yo) -> exactly 2 cases in 15-24
        self.assertEqual(jul['age_groups']['15-24'], 2)

    # 15. All age groups are represented
    def test_15_all_age_groups_represented(self):
        """
        Every supported age group (0-5, 6-14, 15-24, 25-44, 45-59, 60+) is represented,
        including groups with zero cases.
        """
        # Malaria at fac_central_1 only has 1 case (p_0_5: 0-5 MALE)
        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Malaria&date={self.as_of}&months=6"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ag_items = res.data['historical_age_groups']
        ag_names = [item['age_group'] for item in ag_items]

        for required_ag in ['0-5', '6-14', '15-24', '25-44', '45-59', '60+']:
            self.assertIn(required_ag, ag_names)

        # Groups with no cases have 0
        ag_map = {item['age_group']: item['total_cases'] for item in ag_items}
        self.assertEqual(ag_map['0-5'], 1)
        self.assertEqual(ag_map['6-14'], 0)
        self.assertEqual(ag_map['15-24'], 0)
        self.assertEqual(ag_map['25-44'], 0)
        self.assertEqual(ag_map['45-59'], 0)
        self.assertEqual(ag_map['60+'], 0)

    # 16. Existing historical response fields remain unchanged
    def test_16_existing_historical_response_fields_unchanged(self):
        """
        Confirms backward compatibility: total_cases_in_history, monthly_series,
        severity_breakdown, observation_period, months_analyzed, monthly_average,
        trend_direction, and explanation are all preserved.
        """
        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Dengue&date={self.as_of}&months=6"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn('total_cases_in_history', res.data)
        self.assertIn('monthly_series', res.data)
        self.assertIn('historical_series', res.data)
        self.assertIn('observation_period', res.data)
        self.assertIn('months_analyzed', res.data)
        self.assertIn('monthly_average', res.data)
        self.assertIn('current_month_cases', res.data)
        self.assertIn('previous_month_cases', res.data)
        self.assertIn('percentage_change', res.data)
        self.assertIn('trend_direction', res.data)
        self.assertIn('explanation', res.data)

        # Check severity_breakdown inside monthly series
        first_month = res.data['historical_series'][0]
        self.assertIn('severity_breakdown', first_month)
        self.assertIn('MILD', first_month['severity_breakdown'])
        self.assertIn('MODERATE', first_month['severity_breakdown'])
        self.assertIn('SEVERE', first_month['severity_breakdown'])

    # 17. No demographic filters -> existing behavior
    def test_17_no_demographic_filters_existing_behavior(self):
        """
        When demographic filters are omitted, all 10 Dengue cases recorded at fac_central_1
        across the 6-month period are included in the result.
        """
        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Dengue&date={self.as_of}&months=6"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Total cases at fac_central_1 across May-Oct:
        # May(1) + Jun(1) + Jul(2) + Aug(2) + Sep(2) + Oct(2) = 10
        self.assertEqual(res.data['total_cases_in_history'], 10)

    # URL Alias Tests
    def test_historical_url_alias_routes(self):
        """
        Verifies both /surveillance/intelligence/historical/ and alias routes work identically.
        """
        urls = [
            f"{reverse('intelligence_historical')}?disease=Dengue&date={self.as_of}&months=6",
            f"{reverse('intelligence_historical_alias')}?disease=Dengue&date={self.as_of}&months=6",
            f"{reverse('intelligence_historical_disease_alias')}?disease=Dengue&date={self.as_of}&months=6",
        ]
        for u in urls:
            res = self.client.get(u)
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(res.data['total_cases_in_history'], 10)
            self.assertIn('historical_age_groups', res.data)
            self.assertIn('historical_gender', res.data)
            self.assertIn('age_gender_matrix', res.data)
            self.assertIn('monthly_demographic_trends', res.data)


# ===========================================================================
# PROMPT 4: Severity Analysis Test Suite
# ===========================================================================

class PublicHealthSeverityDemographicsTestCase(TestCase):
    """
    Comprehensive test suite for Prompt 4 Severity Analysis in tests_demographics.py.
    Implements all 15 required test scenarios:
    1. Severity filter validation (MILD/MODERATE/SEVERE -> 200, UNKNOWN/INVALID -> 400).
    2. Severity filtering correctness (MILD, MODERATE, SEVERE include only matching cases).
    3. Historical severity output fields (historical_severity, monthly_severity_trends,
       severity_age_groups, severity_gender, severity_age_gender, severity_breakdown).
    4. Historical severity counts (MILD+MODERATE+SEVERE+UNKNOWN sum correctly, monthly sums).
    5. Severity + age_group combination (AND semantics).
    6. Severity + gender combination (AND semantics).
    7. Severity + age_group + gender combination (all three combined).
    8. Severity + disease combination (Dengue + SEVERE).
    9. Severity + facility scope (Hospital Admin: assigned works, cross-facility 403).
    10. Severity + district scope (District Officer: assigned works, cross-district 403).
    11. Missing/invalid severity data (classified as UNKNOWN, never converted to MILD).
    12. Backward compatibility (requests without severity return full counts and fields).
    13. Endpoint coverage (trends, locality, historical, hospital, district, summary).
    14. Severity not silently ignored (verifies filtered result differs from unfiltered result).
    15. Query efficiency (select_related('patient'), no N+1 query loop).
    """

    @classmethod
    def setUpTestData(cls):
        # Geography
        cls.state = State.objects.create(name='Karnataka', code='KA')
        cls.district_central = District.objects.create(state=cls.state, name='BBMP Central', code='KA-CEN')
        cls.district_rural = District.objects.create(state=cls.state, name='Bengaluru Rural', code='KA-RUR')

        cls.zone_central = Zone.objects.create(district=cls.district_central, name='Central Zone', code='Z-CEN')
        cls.zone_rural = Zone.objects.create(district=cls.district_rural, name='Rural Zone', code='Z-RUR')

        cls.ward_central = Ward.objects.create(zone=cls.zone_central, ward_number=10, name='Indiranagar', population=20000)
        cls.ward_rural = Ward.objects.create(zone=cls.zone_rural, ward_number=20, name='Varthur', population=15000)

        # Facilities
        cls.fac_c1 = Facility.objects.create(
            facility_code='HOSP-C1', facility_name='Victoria General Hospital', facility_type='MAIN_HOSPITAL',
            district=cls.district_central, ward=cls.ward_central, state=cls.state
        )
        cls.fac_c2 = Facility.objects.create(
            facility_code='CLINIC-C2', facility_name='Indiranagar Namma Clinic', facility_type='NAMMA_CLINIC',
            district=cls.district_central, ward=cls.ward_central, state=cls.state
        )
        cls.fac_r1 = Facility.objects.create(
            facility_code='RURAL-R1', facility_name='Varthur Health Centre', facility_type='RURAL_CLINIC',
            district=cls.district_rural, ward=cls.ward_rural, state=cls.state
        )

        # Users
        cls.admin_c1 = User.objects.create_user(
            username='sev_admin_c1', password='Password123!', role='HOSPITAL_ADMIN',
            assigned_facility=cls.fac_c1
        )
        cls.officer_c = User.objects.create_user(
            username='sev_officer_c', password='Password123!', role='DISTRICT_OFFICER',
            assigned_district=cls.district_central
        )
        cls.officer_r = User.objects.create_user(
            username='sev_officer_r', password='Password123!', role='DISTRICT_OFFICER',
            assigned_district=cls.district_rural
        )

        # Reference date
        cls.as_of = datetime.date(2026, 10, 4)

        # Deterministic Patients
        cls.p_0_5_m = Patient.objects.create(
            patient_id='P-SD01', name='Infant Boy',
            date_of_birth=datetime.date(2024, 5, 15), age=2, gender='MALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_c1
        )
        cls.p_6_14_f = Patient.objects.create(
            patient_id='P-SD02', name='School Girl',
            date_of_birth=datetime.date(2016, 5, 15), age=10, gender='FEMALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_c1
        )
        cls.p_15_24_f = Patient.objects.create(
            patient_id='P-SD03', name='Young Female',
            date_of_birth=datetime.date(2006, 5, 15), age=20, gender='FEMALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_c1
        )
        cls.p_15_24_m = Patient.objects.create(
            patient_id='P-SD04', name='Young Male',
            date_of_birth=datetime.date(2008, 5, 15), age=18, gender='MALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_c1
        )
        cls.p_25_44_m = Patient.objects.create(
            patient_id='P-SD05', name='Adult Male',
            date_of_birth=datetime.date(1996, 5, 15), age=30, gender='MALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_c1
        )
        cls.p_25_44_f = Patient.objects.create(
            patient_id='P-SD06', name='Adult Female',
            date_of_birth=datetime.date(1991, 5, 15), age=35, gender='FEMALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_c1
        )
        cls.p_45_59_o = Patient.objects.create(
            patient_id='P-SD07', name='Middle Aged Other',
            date_of_birth=datetime.date(1976, 5, 15), age=50, gender='OTHER',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_c1
        )
        cls.p_60_plus_m = Patient.objects.create(
            patient_id='P-SD08', name='Senior Male',
            date_of_birth=datetime.date(1956, 5, 15), age=70, gender='MALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_c1
        )
        cls.p_no_dob = Patient.objects.create(
            patient_id='P-SD09', name='Missing DOB Patient',
            date_of_birth=None, age=30, gender='FEMALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_c1
        )
        cls.p_no_gender = Patient.objects.create(
            patient_id='P-SD10', name='Missing Gender Patient',
            date_of_birth=datetime.date(2000, 5, 15), age=26, gender='',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_c1
        )
        cls.p_aging = Patient.objects.create(
            patient_id='P-SD11', name='Aging Patient',
            date_of_birth=datetime.date(2010, 7, 1), age=16, gender='FEMALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_c1
        )
        cls.p_rural = Patient.objects.create(
            patient_id='P-SD12', name='Rural Patient',
            date_of_birth=datetime.date(1995, 1, 1), age=31, gender='FEMALE',
            district=cls.district_rural, ward=cls.ward_rural, registered_at_facility=cls.fac_r1
        )

        # Historical cases across 6 calendar months (May - Oct 2026) at fac_c1
        # May 2026: 1 MILD Dengue case
        cls.c_may_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_0_5_m, facility=cls.fac_c1,
            ward=cls.ward_central, report_date=datetime.date(2026, 5, 10), severity='MILD'
        )
        # June 2026: 1 MODERATE Dengue case
        cls.c_jun_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_6_14_f, facility=cls.fac_c1,
            ward=cls.ward_central, report_date=datetime.date(2026, 6, 12), severity='MODERATE'
        )
        # July 2026: 2 SEVERE Dengue cases
        cls.c_jul_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_15_24_f, facility=cls.fac_c1,
            ward=cls.ward_central, report_date=datetime.date(2026, 7, 15), severity='SEVERE'
        )
        cls.c_jul_2 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_15_24_m, facility=cls.fac_c1,
            ward=cls.ward_central, report_date=datetime.date(2026, 7, 20), severity='SEVERE'
        )
        # August 2026: 1 MILD, 1 MODERATE Dengue case
        cls.c_aug_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_25_44_f, facility=cls.fac_c1,
            ward=cls.ward_central, report_date=datetime.date(2026, 8, 10), severity='MILD'
        )
        cls.c_aug_2 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_no_gender, facility=cls.fac_c1,
            ward=cls.ward_central, report_date=datetime.date(2026, 8, 25), severity='MODERATE'
        )
        # September 2026: 1 SEVERE, 1 MILD, 1 missing severity, 1 invalid severity
        cls.c_sep_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_25_44_m, facility=cls.fac_c1,
            ward=cls.ward_central, report_date=datetime.date(2026, 9, 5), severity='SEVERE'
        )
        cls.c_sep_2 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_no_dob, facility=cls.fac_c1,
            ward=cls.ward_central, report_date=datetime.date(2026, 9, 20), severity='MILD'
        )
        cls.c_sep_3_missing = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_45_59_o, facility=cls.fac_c1,
            ward=cls.ward_central, report_date=datetime.date(2026, 9, 25), severity=''
        )
        cls.c_sep_4_invalid = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_60_plus_m, facility=cls.fac_c1,
            ward=cls.ward_central, report_date=datetime.date(2026, 9, 28), severity='CRITICAL'
        )
        # October 2026: 1 MODERATE, 1 MILD Dengue case
        cls.c_oct_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_45_59_o, facility=cls.fac_c1,
            ward=cls.ward_central, report_date=datetime.date(2026, 10, 1), severity='MODERATE'
        )
        cls.c_oct_2 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_60_plus_m, facility=cls.fac_c1,
            ward=cls.ward_central, report_date=datetime.date(2026, 10, 3), severity='MILD'
        )

        # Cross-facility case (same district)
        cls.c_fac_c2_dengue = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_25_44_f, facility=cls.fac_c2,
            ward=cls.ward_central, report_date=datetime.date(2026, 9, 15), severity='SEVERE'
        )

        # Cross-disease case
        cls.c_malaria = DiseaseCase.objects.create(
            disease_name='Malaria', patient=cls.p_0_5_m, facility=cls.fac_c1,
            ward=cls.ward_central, report_date=datetime.date(2026, 9, 18), severity='SEVERE'
        )

        # Cross-district case
        cls.c_rural_dengue = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_rural, facility=cls.fac_r1,
            ward=cls.ward_rural, report_date=datetime.date(2026, 9, 15), severity='MILD'
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_c1)

    # 1. Severity filter validation
    def test_01_severity_filter_validation(self):
        """
        - severity=MILD -> 200
        - severity=MODERATE -> 200
        - severity=SEVERE -> 200
        - severity=UNKNOWN -> 400
        - severity=INVALID -> 400
        - invalid severity must never silently return unfiltered data.
        """
        hist_url = reverse('intelligence_historical_disease')

        # Valid severities return 200
        for s in ['MILD', 'MODERATE', 'SEVERE']:
            res = self.client.get(f"{hist_url}?disease=Dengue&severity={s}&date={self.as_of}")
            self.assertEqual(res.status_code, status.HTTP_200_OK, f"severity={s} failed to return 200")

        # Case-insensitive valid parameter returns 200
        res_lower = self.client.get(f"{hist_url}?disease=Dengue&severity=severe&date={self.as_of}")
        self.assertEqual(res_lower.status_code, status.HTTP_200_OK)

        # UNKNOWN is rejected with HTTP 400
        res_unk = self.client.get(f"{hist_url}?disease=Dengue&severity=UNKNOWN&date={self.as_of}")
        self.assertEqual(res_unk.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', res_unk.data)

        # INVALID / unsupported severity is rejected with HTTP 400
        for bad_val in ['INVALID', 'CRITICAL', 'NONE', '123']:
            res_bad = self.client.get(f"{hist_url}?disease=Dengue&severity={bad_val}&date={self.as_of}")
            self.assertEqual(res_bad.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('error', res_bad.data)
            # Must NEVER silently return unfiltered 200 data
            self.assertNotEqual(res_bad.status_code, status.HTTP_200_OK)

    # 2. Severity filtering correctness
    def test_02_severity_filtering_correctness(self):
        """
        Deterministic cases containing MILD, MODERATE, and SEVERE.
        Verify severity=MILD only includes MILD cases (4).
        Verify severity=MODERATE only includes MODERATE cases (3).
        Verify severity=SEVERE only includes SEVERE cases (3).
        """
        hist_url = reverse('intelligence_historical_disease')

        # MILD filter
        res_mild = self.client.get(f"{hist_url}?disease=Dengue&severity=MILD&date={self.as_of}&months=6")
        self.assertEqual(res_mild.status_code, status.HTTP_200_OK)
        self.assertEqual(res_mild.data['total_cases_in_history'], 4)
        sev_map = {item['severity']: item['total_cases'] for item in res_mild.data['historical_severity']}
        self.assertEqual(sev_map['MILD'], 4)
        self.assertEqual(sev_map['MODERATE'], 0)
        self.assertEqual(sev_map['SEVERE'], 0)

        # MODERATE filter
        res_mod = self.client.get(f"{hist_url}?disease=Dengue&severity=MODERATE&date={self.as_of}&months=6")
        self.assertEqual(res_mod.status_code, status.HTTP_200_OK)
        self.assertEqual(res_mod.data['total_cases_in_history'], 3)
        sev_map_mod = {item['severity']: item['total_cases'] for item in res_mod.data['historical_severity']}
        self.assertEqual(sev_map_mod['MODERATE'], 3)
        self.assertEqual(sev_map_mod['MILD'], 0)
        self.assertEqual(sev_map_mod['SEVERE'], 0)

        # SEVERE filter
        res_sev = self.client.get(f"{hist_url}?disease=Dengue&severity=SEVERE&date={self.as_of}&months=6")
        self.assertEqual(res_sev.status_code, status.HTTP_200_OK)
        self.assertEqual(res_sev.data['total_cases_in_history'], 3)
        sev_map_sev = {item['severity']: item['total_cases'] for item in res_sev.data['historical_severity']}
        self.assertEqual(sev_map_sev['SEVERE'], 3)
        self.assertEqual(sev_map_sev['MILD'], 0)
        self.assertEqual(sev_map_sev['MODERATE'], 0)

    # 3. Historical severity output fields
    def test_03_historical_severity_output_fields(self):
        """
        Verify historical endpoint contains:
        - historical_severity
        - monthly_severity_trends
        - severity_age_groups
        - severity_gender
        - severity_age_gender
        - severity_breakdown
        """
        res = self.client.get(f"{reverse('intelligence_historical_disease')}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        for field in [
            'historical_severity',
            'monthly_severity_trends',
            'severity_age_groups',
            'severity_gender',
            'severity_age_gender',
            'severity_breakdown'
        ]:
            self.assertIn(field, res.data, f"Required severity field '{field}' missing from response.")

    # 4. Historical severity counts
    def test_04_historical_severity_counts(self):
        """
        Verify:
        - MILD + MODERATE + SEVERE + UNKNOWN counts are correct (4 + 3 + 3 + 2 = 12).
        - Monthly severity counts sum correctly to total monthly cases.
        - Historical severity totals sum correctly to total historical cases.
        """
        res = self.client.get(f"{reverse('intelligence_historical_disease')}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        sev_map = {item['severity']: item['total_cases'] for item in res.data['historical_severity']}
        self.assertEqual(sev_map['MILD'], 4)
        self.assertEqual(sev_map['MODERATE'], 3)
        self.assertEqual(sev_map['SEVERE'], 3)
        self.assertEqual(sev_map['UNKNOWN'], 2)

        # Historical severity totals sum correctly to total historical cases
        total_from_severities = sum(sev_map.values())
        self.assertEqual(total_from_severities, res.data['total_cases_in_history'])
        self.assertEqual(res.data['total_cases_in_history'], 12)

        # Monthly severity counts sum correctly to total monthly cases
        for m_trend in res.data['monthly_severity_trends']:
            m_sum = sum(m_trend['severity'].values())
            self.assertEqual(
                m_sum, m_trend['total_cases'],
                f"Month {m_trend['month']} severity sum ({m_sum}) != total_cases ({m_trend['total_cases']})"
            )

    # 5. Severity + age_group combination
    def test_05_severity_plus_age_group_combination(self):
        """
        Example: severity=SEVERE&age_group=15-24
        Verify AND semantics: only cases matching BOTH severity and age group are included.
        """
        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Dengue&severity=SEVERE&age_group=15-24&date={self.as_of}&months=6"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # July Dengue cases matching SEVERE and 15-24: p_15_24_f and p_15_24_m = 2 cases
        self.assertEqual(res.data['total_cases_in_history'], 2)

    # 6. Severity + gender combination
    def test_06_severity_plus_gender_combination(self):
        """
        Example: severity=SEVERE&gender=FEMALE
        Verify AND semantics: only cases matching BOTH severity and gender are included.
        """
        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Dengue&severity=SEVERE&gender=FEMALE&date={self.as_of}&months=6"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # July Dengue cases matching SEVERE and FEMALE: p_15_24_f = 1 case
        self.assertEqual(res.data['total_cases_in_history'], 1)

    # 7. Severity + age_group + gender combination
    def test_07_severity_plus_age_group_plus_gender_combination(self):
        """
        Example: severity=SEVERE&age_group=15-24&gender=FEMALE
        Verify all three filters apply together with strict AND logic.
        """
        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Dengue&severity=SEVERE&age_group=15-24&gender=FEMALE&date={self.as_of}&months=6"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_cases_in_history'], 1)

        # MALE variation: p_15_24_m = 1 case
        res_m = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Dengue&severity=SEVERE&age_group=15-24&gender=MALE&date={self.as_of}&months=6"
        )
        self.assertEqual(res_m.status_code, status.HTTP_200_OK)
        self.assertEqual(res_m.data['total_cases_in_history'], 1)

    # 8. Severity + disease combination
    def test_08_severity_plus_disease_combination(self):
        """
        Verify: disease=Dengue&severity=SEVERE
        returns only Dengue cases whose severity is SEVERE (excludes Malaria SEVERE case).
        """
        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Dengue&severity=SEVERE&date={self.as_of}&months=6"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # 3 SEVERE Dengue cases; Malaria SEVERE case is excluded
        self.assertEqual(res.data['total_cases_in_history'], 3)
        self.assertEqual(res.data['disease'], 'Dengue')

    # 9. Severity + facility scope
    def test_09_severity_plus_facility_scope(self):
        """
        For Hospital Admin:
        - assigned facility + severity filter works.
        - another facility remains 403.
        """
        # Assigned facility fac_c1
        res_ok = self.client.get(
            f"{reverse('intelligence_historical_disease')}?facility={self.fac_c1.id}&disease=Dengue&severity=SEVERE&date={self.as_of}&months=6"
        )
        self.assertEqual(res_ok.status_code, status.HTTP_200_OK)
        self.assertEqual(res_ok.data['total_cases_in_history'], 3)

        # Another facility fac_c2 remains 403
        res_forbidden = self.client.get(
            f"{reverse('intelligence_historical_disease')}?facility={self.fac_c2.id}&severity=SEVERE&date={self.as_of}&months=6"
        )
        self.assertEqual(res_forbidden.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', res_forbidden.data)

    # 10. Severity + district scope
    def test_10_severity_plus_district_scope(self):
        """
        For District Officer:
        - assigned district + severity filter works.
        - another district remains 403.
        """
        self.client.force_authenticate(user=self.officer_c)

        # Assigned district (central) includes fac_c1 (3) + fac_c2 (1) = 4 SEVERE Dengue cases
        res_ok = self.client.get(
            f"{reverse('intelligence_historical_disease')}?district={self.district_central.id}&disease=Dengue&severity=SEVERE&date={self.as_of}&months=6"
        )
        self.assertEqual(res_ok.status_code, status.HTTP_200_OK)
        self.assertEqual(res_ok.data['total_cases_in_history'], 4)

        # Rural District Officer attempting to access Central District receives 403
        self.client.force_authenticate(user=self.officer_r)
        res_forbidden = self.client.get(
            f"{reverse('intelligence_historical_disease')}?district={self.district_central.id}&severity=SEVERE&date={self.as_of}&months=6"
        )
        self.assertEqual(res_forbidden.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', res_forbidden.data)

    # 11. Missing/invalid severity data
    def test_11_missing_and_invalid_severity_data_handling(self):
        """
        Verify missing or unsupported severity is represented as UNKNOWN.
        Never convert missing/invalid severity to MILD.
        """
        # Unit normalization check
        self.assertEqual(normalize_severity(None), SEVERITY_UNKNOWN)
        self.assertEqual(normalize_severity(''), SEVERITY_UNKNOWN)
        self.assertEqual(normalize_severity('INVALID_VALUE'), SEVERITY_UNKNOWN)
        self.assertNotEqual(normalize_severity(None), SEVERITY_MILD)

        # Analytical response check
        res = self.client.get(f"{reverse('intelligence_historical_disease')}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        sev_map = {item['severity']: item['total_cases'] for item in res.data['historical_severity']}
        self.assertIn('UNKNOWN', sev_map)
        self.assertEqual(sev_map['UNKNOWN'], 2)

    # 12. Backward compatibility
    def test_12_backward_compatibility_without_severity(self):
        """
        Existing requests without severity must continue returning the same total case counts
        and existing response fields intact.
        """
        res = self.client.get(f"{reverse('intelligence_historical_disease')}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # All 12 cases returned without severity filter
        self.assertEqual(res.data['total_cases_in_history'], 12)

        # All existing legacy and demographic response fields preserved
        for required_key in [
            'total_cases_in_history',
            'monthly_series',
            'historical_series',
            'observation_period',
            'months_analyzed',
            'monthly_average',
            'mean_monthly_cases',
            'current_month_cases',
            'previous_month_cases',
            'percentage_change',
            'trend_direction',
            'explanation',
            'severity_breakdown',
            'historical_age_groups',
            'historical_gender',
            'age_gender_matrix',
            'monthly_demographic_trends'
        ]:
            self.assertIn(required_key, res.data, f"Field '{required_key}' missing from backward-compatible response.")

    # 13. Endpoint coverage
    def test_13_endpoint_coverage_severity_filtering(self):
        """
        Add tests for severity filtering on every logically applicable existing intelligence endpoint:
        - trends
        - locality
        - historical
        - hospital
        - district
        - summary
        """
        endpoints = [
            (reverse('intelligence_disease_trends'), {'disease': 'Dengue', 'date': str(self.as_of), 'severity': 'SEVERE'}),
            (reverse('intelligence_disease_by_locality'), {'disease': 'Dengue', 'date': str(self.as_of), 'severity': 'SEVERE'}),
            (reverse('intelligence_historical_disease'), {'disease': 'Dengue', 'date': str(self.as_of), 'severity': 'SEVERE'}),
            (reverse('intelligence_hospital_aggregation'), {'facility': self.fac_c1.id, 'date': str(self.as_of), 'severity': 'SEVERE'}),
            (reverse('intelligence_district_aggregation'), {'district': self.district_central.id, 'date': str(self.as_of), 'severity': 'SEVERE'}),
            (reverse('intelligence_summary'), {'date': str(self.as_of), 'severity': 'SEVERE'}),
        ]

        # Authenticate district officer so both hospital and district endpoints succeed
        self.client.force_authenticate(user=self.officer_c)

        for url, params in endpoints:
            query_str = '&'.join(f"{k}={v}" for k, v in params.items())
            res = self.client.get(f"{url}?{query_str}")
            self.assertEqual(res.status_code, status.HTTP_200_OK, f"Endpoint {url} failed with severity filter.")

    # 14. Test that severity is NOT silently ignored
    def test_14_severity_not_silently_ignored_across_endpoints(self):
        """
        For trends, locality, historical, hospital, district, and summary:
        compare an unfiltered request with a severity-filtered request and verify
        the filtered result changes according to the deterministic test data.
        """
        self.client.force_authenticate(user=self.officer_c)

        # 1. Trends: unfiltered current cases vs SEVERE current cases
        url_trends = reverse('intelligence_disease_trends')
        res_t_all = self.client.get(f"{url_trends}?disease=Dengue&facility={self.fac_c1.id}&start_date=2026-09-01&end_date=2026-10-04")
        res_t_sev = self.client.get(f"{url_trends}?disease=Dengue&facility={self.fac_c1.id}&start_date=2026-09-01&end_date=2026-10-04&severity=SEVERE")
        self.assertEqual(res_t_all.status_code, status.HTTP_200_OK)
        self.assertEqual(res_t_sev.status_code, status.HTTP_200_OK)
        cases_all_t = res_t_all.data['summary']['total_current_cases']
        cases_sev_t = res_t_sev.data['summary']['total_current_cases']
        self.assertGreater(cases_all_t, cases_sev_t, "Trends endpoint silently ignored severity filter.")
        self.assertEqual(cases_sev_t, 1) # Only Sep 5 case is SEVERE in Sep-Oct window

        # 2. Locality: unfiltered vs SEVERE
        url_loc = reverse('intelligence_disease_by_locality')
        res_l_all = self.client.get(f"{url_loc}?disease=Dengue&facility={self.fac_c1.id}&start_date=2026-09-01&end_date=2026-10-04")
        res_l_sev = self.client.get(f"{url_loc}?disease=Dengue&facility={self.fac_c1.id}&start_date=2026-09-01&end_date=2026-10-04&severity=SEVERE")
        self.assertEqual(res_l_all.status_code, status.HTTP_200_OK)
        self.assertEqual(res_l_sev.status_code, status.HTTP_200_OK)
        cases_all_l = res_l_all.data['total_cases_in_period']
        cases_sev_l = res_l_sev.data['total_cases_in_period']
        self.assertGreater(cases_all_l, cases_sev_l, "Locality endpoint silently ignored severity filter.")
        self.assertEqual(cases_sev_l, 1)

        # 3. Historical: unfiltered vs SEVERE
        url_hist = reverse('intelligence_historical_disease')
        res_h_all = self.client.get(f"{url_hist}?disease=Dengue&facility={self.fac_c1.id}&date={self.as_of}&months=6")
        res_h_sev = self.client.get(f"{url_hist}?disease=Dengue&facility={self.fac_c1.id}&date={self.as_of}&months=6&severity=SEVERE")
        self.assertEqual(res_h_all.status_code, status.HTTP_200_OK)
        self.assertEqual(res_h_sev.status_code, status.HTTP_200_OK)
        self.assertEqual(res_h_all.data['total_cases_in_history'], 12)
        self.assertEqual(res_h_sev.data['total_cases_in_history'], 3)
        self.assertGreater(res_h_all.data['total_cases_in_history'], res_h_sev.data['total_cases_in_history'])

        # 4. Hospital: unfiltered vs SEVERE
        url_hosp = reverse('intelligence_hospital_aggregation')
        res_hosp_all = self.client.get(f"{url_hosp}?facility={self.fac_c1.id}&start_date=2026-09-01&end_date=2026-10-04")
        res_hosp_sev = self.client.get(f"{url_hosp}?facility={self.fac_c1.id}&start_date=2026-09-01&end_date=2026-10-04&severity=SEVERE")
        self.assertEqual(res_hosp_all.status_code, status.HTTP_200_OK)
        self.assertEqual(res_hosp_sev.status_code, status.HTTP_200_OK)
        hosp_all_cnt = res_hosp_all.data['summary']['total_current_cases']
        hosp_sev_cnt = res_hosp_sev.data['summary']['total_current_cases']
        self.assertGreater(hosp_all_cnt, hosp_sev_cnt, "Hospital endpoint silently ignored severity filter.")

        # 5. District: unfiltered vs SEVERE
        url_dist = reverse('intelligence_district_aggregation')
        res_dist_all = self.client.get(f"{url_dist}?district={self.district_central.id}&start_date=2026-09-01&end_date=2026-10-04")
        res_dist_sev = self.client.get(f"{url_dist}?district={self.district_central.id}&start_date=2026-09-01&end_date=2026-10-04&severity=SEVERE")
        self.assertEqual(res_dist_all.status_code, status.HTTP_200_OK)
        self.assertEqual(res_dist_sev.status_code, status.HTTP_200_OK)
        dist_all_cnt = res_dist_all.data['summary']['total_current_cases']
        dist_sev_cnt = res_dist_sev.data['summary']['total_current_cases']
        self.assertGreater(dist_all_cnt, dist_sev_cnt, "District endpoint silently ignored severity filter.")

        # 6. Summary: unfiltered vs SEVERE
        url_sum = reverse('intelligence_summary')
        res_sum_all = self.client.get(f"{url_sum}?district={self.district_central.id}&start_date=2026-09-01&end_date=2026-10-04")
        res_sum_sev = self.client.get(f"{url_sum}?district={self.district_central.id}&start_date=2026-09-01&end_date=2026-10-04&severity=SEVERE")
        self.assertEqual(res_sum_all.status_code, status.HTTP_200_OK)
        self.assertEqual(res_sum_sev.status_code, status.HTTP_200_OK)
        sum_all_cnt = res_sum_all.data['summary']['total_current_cases']
        sum_sev_cnt = res_sum_sev.data['summary']['total_current_cases']
        self.assertGreater(sum_all_cnt, sum_sev_cnt, "Summary endpoint silently ignored severity filter.")

    # 15. Query efficiency
    def test_15_query_efficiency_no_n_plus_one(self):
        """
        Verify that historical severity aggregation does not execute an N+1 query loop per case/patient.
        Uses select_related('patient') to load historical cases and patient relations in strictly 1 query.
        """
        with self.assertNumQueries(1):
            aggregate_historical_disease(
                facility_ids=[self.fac_c1.id],
                disease_name='Dengue',
                months=6,
                as_of_date=self.as_of
            )


class PublicHealthVulnerablePopulationTestCase(TestCase):
    """
    Dedicated comprehensive test suite for Prompt 5: Vulnerable Population Analysis.
    Covers all 24 required test scenarios:
    1. Vulnerable group filter validation (valid -> 200, invalid/UNKNOWN -> 400)
    2. Vulnerable group filtering correctness
    3. Vulnerable group + disease combined filtering
    4. Vulnerable group + severity combined filtering
    5. Vulnerable group + age_group combined filtering
    6. Vulnerable group + gender combined filtering
    7. Vulnerable group + age_group + gender + severity + disease combined filtering
    8. historical_vulnerable_groups correctness
    9. monthly_vulnerable_population_trends correctness and sum invariant
    10. vulnerable_age_groups correctness
    11. vulnerable_gender correctness
    12. vulnerable_age_gender correctness
    13. vulnerable_severity correctness
    14. vulnerable_age_gender_severity 4D matrix correctness
    15. Role-based authorization (403 for unauthorized cross-facility / cross-district)
    16. Missing/unknown vulnerability handling (internal UNKNOWN vs rejected param)
    17. Backward compatibility when vulnerable_group is omitted
    18. Trends endpoint with vulnerable_group filter
    19. Locality endpoint with vulnerable_group filter
    20. Hospital and district endpoints with vulnerable_group filter
    21. Summary endpoint with vulnerable_group filter
    22. Non-silent filtering across endpoints
    23. Age calculation uses case report_date, not today
    24. Query efficiency (assertNumQueries(1) without N+1 loop)
    """

    @classmethod
    def setUpTestData(cls):
        cls.state = State.objects.create(name='Tamil Nadu', code='TN')
        cls.district_central = District.objects.create(name='Central Chennai', code='CEN', state=cls.state)
        cls.district_rural = District.objects.create(name='Rural Kanchipuram', code='RUR', state=cls.state)

        cls.zone_c = Zone.objects.create(name='Central Zone', code='Z-CEN', district=cls.district_central)
        cls.zone_r = Zone.objects.create(name='Rural Zone', code='Z-RUR', district=cls.district_rural)

        cls.ward_c1 = Ward.objects.create(name='Central Ward 1', ward_number=101, zone=cls.zone_c)
        cls.ward_c2 = Ward.objects.create(name='Central Ward 2', ward_number=102, zone=cls.zone_c)
        cls.ward_r1 = Ward.objects.create(name='Rural Ward 1', ward_number=201, zone=cls.zone_r)

        cls.fac_c1 = Facility.objects.create(
            facility_name='Central Clinic One', facility_code='CC01',
            facility_type='URBAN_PHC', district=cls.district_central, ward=cls.ward_c1, state=cls.state
        )
        cls.fac_c2 = Facility.objects.create(
            facility_name='Central Clinic Two', facility_code='CC02',
            facility_type='COMMUNITY_HEALTH_CENTRE', district=cls.district_central, ward=cls.ward_c2, state=cls.state
        )
        cls.fac_r1 = Facility.objects.create(
            facility_name='Rural Primary Clinic', facility_code='RC01',
            facility_type='PRIMARY_HEALTH_CENTRE', district=cls.district_rural, ward=cls.ward_r1, state=cls.state
        )

        cls.admin_c1 = User.objects.create_user(
            username='admin_c1', email='admin_c1@clinic.in', password='pass',
            role='HOSPITAL_ADMIN', assigned_facility=cls.fac_c1
        )
        cls.admin_c2 = User.objects.create_user(
            username='admin_c2', email='admin_c2@clinic.in', password='pass',
            role='HOSPITAL_ADMIN', assigned_facility=cls.fac_c2
        )
        cls.doctor_c1 = User.objects.create_user(
            username='doctor_c1', email='doctor_c1@clinic.in', password='pass',
            role='DOCTOR', assigned_facility=cls.fac_c1
        )
        cls.officer_c = User.objects.create_user(
            username='officer_c', email='officer_c@clinic.in', password='pass',
            role='DISTRICT_OFFICER', assigned_district=cls.district_central
        )
        cls.officer_r = User.objects.create_user(
            username='officer_r', email='officer_r@clinic.in', password='pass',
            role='DISTRICT_OFFICER', assigned_district=cls.district_rural
        )

        for u in [cls.admin_c1, cls.admin_c2, cls.doctor_c1, cls.officer_c, cls.officer_r]:
            u.user_permissions.add(
                *list(u.user_permissions.model.objects.filter(codename__in=['view_dashboard', 'dashboard.view']))
            )

        # Deterministic Patients mapped to each vulnerable population group
        # 1. PREGNANT
        cls.p_preg = Patient.objects.create(
            patient_id='P-VP01', name='Maternal Patient',
            date_of_birth=datetime.date(2000, 1, 1), age=26, gender='FEMALE',
            vulnerability_information='High Risk Pregnancy ANC',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # 2. ELDERLY
        cls.p_elder = Patient.objects.create(
            patient_id='P-VP02', name='Elderly Patient',
            date_of_birth=datetime.date(1956, 1, 1), age=70, gender='MALE',
            vulnerability_information='Senior Citizen / Diabetic',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # 3. DISABILITY
        cls.p_pwd = Patient.objects.create(
            patient_id='P-VP03', name='PwD Patient',
            date_of_birth=datetime.date(1994, 1, 1), age=32, gender='MALE',
            vulnerability_information='Person with Disability (PwD)',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # 4. CHRONIC_CONDITION
        cls.p_chronic = Patient.objects.create(
            patient_id='P-VP04', name='Chronic Patient',
            date_of_birth=datetime.date(1980, 1, 1), age=46, gender='FEMALE',
            vulnerability_information='Hypertension / General BPL',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # 5. LOW_INCOME_SLUM
        cls.p_slum = Patient.objects.create(
            patient_id='P-VP05', name='Slum Resident Child',
            date_of_birth=datetime.date(2022, 1, 1), age=4, gender='MALE',
            vulnerability_information='Slum Resident / Low Income Group',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # 6. GENERAL
        cls.p_gen = Patient.objects.create(
            patient_id='P-VP06', name='General Non-Vulnerable Patient',
            date_of_birth=datetime.date(2012, 1, 1), age=14, gender='FEMALE',
            vulnerability_information='General / Non-Vulnerable',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # 7. UNKNOWN tag
        cls.p_unk_tag = Patient.objects.create(
            patient_id='P-VP07', name='Unknown Custom Tag Patient',
            date_of_birth=datetime.date(2005, 1, 1), age=21, gender='FEMALE',
            vulnerability_information='Unknown Random Tag XYZ',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # 8. Missing / None
        cls.p_unk_none = Patient.objects.create(
            patient_id='P-VP08', name='Missing Vulnerability Patient',
            date_of_birth=datetime.date(1970, 1, 1), age=56, gender='MALE',
            vulnerability_information='',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )

        cls.as_of = datetime.date(2026, 10, 7)

        # Historical cases across 6 calendar months (May - Oct 2026) at fac_c1
        # May 2026: 1 MILD Dengue case (LOW_INCOME_SLUM)
        cls.c_may_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_slum, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 5, 10), severity='MILD'
        )
        # June 2026: 1 MODERATE Dengue case (GENERAL)
        cls.c_jun_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_gen, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 6, 15), severity='MODERATE'
        )
        # July 2026: 2 cases (PREGNANT SEVERE, DISABILITY MILD)
        cls.c_jul_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_preg, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 7, 10), severity='SEVERE'
        )
        cls.c_jul_2 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_pwd, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 7, 20), severity='MILD'
        )
        # August 2026: 2 cases (CHRONIC MODERATE, ELDERLY SEVERE)
        cls.c_aug_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_chronic, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 8, 12), severity='MODERATE'
        )
        cls.c_aug_2 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_elder, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 8, 25), severity='SEVERE'
        )
        # September 2026: 2 cases (UNKNOWN Dengue MILD, ELDERLY Malaria SEVERE)
        cls.c_sep_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_unk_tag, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 9, 5), severity='MILD'
        )
        cls.c_sep_2 = DiseaseCase.objects.create(
            disease_name='Malaria', patient=cls.p_elder, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 9, 15), severity='SEVERE'
        )
        # October 2026: 2 Dengue cases (UNKNOWN MODERATE, ELDERLY SEVERE)
        cls.c_oct_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_unk_none, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 10, 2), severity='MODERATE'
        )
        cls.c_oct_2 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_elder, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 10, 5), severity='SEVERE'
        )

        # Cross-district case in Rural Kanchipuram (facility fac_r1)
        cls.c_rur_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_elder, facility=cls.fac_r1,
            ward=cls.ward_r1, report_date=datetime.date(2026, 10, 3), severity='SEVERE'
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_c1)

    # 1. test_vulnerable_group_validation
    def test_vulnerable_group_validation(self):
        """
        Valid groups return valid normalized values / 200.
        Invalid group returns an error (400).
        UNKNOWN is not accepted as a selectable filter (400).
        """
        url = reverse('intelligence_historical_disease')

        # Supported valid groups -> 200
        for vg in ['PREGNANT', 'ELDERLY', 'DISABILITY', 'CHRONIC_CONDITION', 'LOW_INCOME_SLUM', 'GENERAL']:
            res = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&vulnerable_group={vg}")
            self.assertEqual(res.status_code, status.HTTP_200_OK, f"Valid group {vg} rejected.")

        # Lowercase / aliases / actual database labels -> 200
        for alias in ['pregnant', 'elderly', 'disability', 'chronic_condition', 'low_income_slum', 'general', 'High Risk Pregnancy ANC']:
            res = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&vulnerable_group={alias}")
            self.assertEqual(res.status_code, status.HTTP_200_OK, f"Alias {alias} rejected.")

        # UNKNOWN is rejected with HTTP 400
        res_unk = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&vulnerable_group=UNKNOWN")
        self.assertEqual(res_unk.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', res_unk.data)

        # Invalid arbitrary strings return HTTP 400
        for invalid_val in ['INVALID', 'HOMELESS', '123', 'UNKNOWN_GROUP']:
            res_inv = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&vulnerable_group={invalid_val}")
            self.assertEqual(res_inv.status_code, status.HTTP_400_BAD_REQUEST, f"Invalid group {invalid_val} should return 400.")
            self.assertIn('error', res_inv.data)

    # 2. test_vulnerable_group_filtering
    def test_vulnerable_group_filtering(self):
        """
        Filtering by each supported group returns only matching cases.
        The filter must not silently return unfiltered data.
        """
        url = reverse('intelligence_historical_disease')

        # Total unfiltered cases at fac_c1 for Dengue is 9
        res_all = self.client.get(f"{url}?disease=Dengue&date={self.as_of}")
        self.assertEqual(res_all.status_code, status.HTTP_200_OK)
        total_unfiltered = res_all.data['total_cases_in_history']
        self.assertEqual(total_unfiltered, 9)

        # ELDERLY Dengue cases: 2 (c_aug_2, c_oct_2)
        res_elder = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&vulnerable_group=ELDERLY")
        self.assertEqual(res_elder.status_code, status.HTTP_200_OK)
        self.assertEqual(res_elder.data['total_cases_in_history'], 2)
        self.assertLess(res_elder.data['total_cases_in_history'], total_unfiltered)

        # PREGNANT Dengue cases: 1 (c_jul_1)
        res_preg = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&vulnerable_group=PREGNANT")
        self.assertEqual(res_preg.status_code, status.HTTP_200_OK)
        self.assertEqual(res_preg.data['total_cases_in_history'], 1)

        # LOW_INCOME_SLUM Dengue cases: 1 (c_may_1)
        res_slum = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&vulnerable_group=LOW_INCOME_SLUM")
        self.assertEqual(res_slum.status_code, status.HTTP_200_OK)
        self.assertEqual(res_slum.data['total_cases_in_history'], 1)

        # DISABILITY Dengue cases: 1 (c_jul_2)
        res_dis = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&vulnerable_group=DISABILITY")
        self.assertEqual(res_dis.status_code, status.HTTP_200_OK)
        self.assertEqual(res_dis.data['total_cases_in_history'], 1)

        # CHRONIC_CONDITION Dengue cases: 1 (c_aug_1)
        res_chr = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&vulnerable_group=CHRONIC_CONDITION")
        self.assertEqual(res_chr.status_code, status.HTTP_200_OK)
        self.assertEqual(res_chr.data['total_cases_in_history'], 1)

        # GENERAL Dengue cases: 1 (c_jun_1)
        res_gen = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&vulnerable_group=GENERAL")
        self.assertEqual(res_gen.status_code, status.HTTP_200_OK)
        self.assertEqual(res_gen.data['total_cases_in_history'], 1)

    # 3. test_historical_vulnerable_groups
    def test_historical_vulnerable_groups(self):
        """
        Verify historical_vulnerable_groups contains correct counts and breakdown.
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn('historical_vulnerable_groups', res.data)
        vg_list = res.data['historical_vulnerable_groups']
        self.assertIsInstance(vg_list, list)

        vg_map = {item['vulnerable_group']: item['total_cases'] for item in vg_list}

        # Check each group count for Dengue (total Dengue cases at fac_c1 = 9)
        self.assertEqual(vg_map.get('LOW_INCOME_SLUM'), 1)
        self.assertEqual(vg_map.get('GENERAL'), 1)
        self.assertEqual(vg_map.get('PREGNANT'), 1)
        self.assertEqual(vg_map.get('DISABILITY'), 1)
        self.assertEqual(vg_map.get('CHRONIC_CONDITION'), 1)
        self.assertEqual(vg_map.get('ELDERLY'), 2)
        self.assertEqual(vg_map.get('UNKNOWN'), 2)
        self.assertEqual(sum(vg_map.values()), 9)

        # Check monthly_counts inside each group item
        for item in vg_list:
            self.assertIn('monthly_counts', item)
            self.assertEqual(len(item['monthly_counts']), 6)
            for m in item['monthly_counts']:
                self.assertIn('month', m)
                self.assertIn('count', m)
                self.assertIn('cases', m)

    # 4. test_monthly_vulnerable_population_trends
    def test_monthly_vulnerable_population_trends(self):
        """
        Verify monthly_vulnerable_population_trends contains correct monthly counts,
        and that for every month sum(vulnerable_groups.values()) strictly reconciles with total_cases.
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn('monthly_vulnerable_population_trends', res.data)
        trends = res.data['monthly_vulnerable_population_trends']
        self.assertEqual(len(trends), 6)

        for month_entry in trends:
            self.assertIn('month', month_entry)
            self.assertIn('total_cases', month_entry)
            self.assertIn('vulnerable_groups', month_entry)
            tot = month_entry['total_cases']
            vg_sum = sum(month_entry['vulnerable_groups'].values())
            self.assertEqual(tot, vg_sum, f"Sum mismatch for month {month_entry['month']}: total={tot}, sum={vg_sum}")

    # 5. test_vulnerable_age_groups
    def test_vulnerable_age_groups(self):
        """
        Verify vulnerable_age_groups contains correct age-group counts.
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn('vulnerable_age_groups', res.data)
        vag = res.data['vulnerable_age_groups']

        # ELDERLY has 2 cases in 60+
        self.assertEqual(vag['ELDERLY']['60+'], 2)
        # LOW_INCOME_SLUM has 1 case in 0-5
        self.assertEqual(vag['LOW_INCOME_SLUM']['0-5'], 1)
        # PREGNANT has 1 case in 25-44
        self.assertEqual(vag['PREGNANT']['25-44'], 1)

    # 6. test_vulnerable_gender
    def test_vulnerable_gender(self):
        """
        Verify vulnerable_gender contains correct gender counts.
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn('vulnerable_gender', res.data)
        vg_gender = res.data['vulnerable_gender']

        self.assertEqual(vg_gender['PREGNANT']['FEMALE'], 1)
        self.assertEqual(vg_gender['ELDERLY']['MALE'], 2)
        self.assertEqual(vg_gender['LOW_INCOME_SLUM']['MALE'], 1)

    # 7. test_vulnerable_age_gender
    def test_vulnerable_age_gender(self):
        """
        Verify vulnerable_age_gender correctly combines both dimensions.
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn('vulnerable_age_gender', res.data)
        vag = res.data['vulnerable_age_gender']

        self.assertEqual(vag['PREGNANT']['25-44']['FEMALE'], 1)
        self.assertEqual(vag['ELDERLY']['60+']['MALE'], 2)
        self.assertEqual(vag['LOW_INCOME_SLUM']['0-5']['MALE'], 1)

    # 8. test_vulnerable_severity
    def test_vulnerable_severity(self):
        """
        Verify vulnerable_severity contains correct MILD/MODERATE/SEVERE/UNKNOWN counts.
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn('vulnerable_severity', res.data)
        vsev = res.data['vulnerable_severity']

        self.assertEqual(vsev['ELDERLY']['SEVERE'], 2)
        self.assertEqual(vsev['PREGNANT']['SEVERE'], 1)
        self.assertEqual(vsev['LOW_INCOME_SLUM']['MILD'], 1)
        self.assertEqual(vsev['DISABILITY']['MILD'], 1)
        self.assertEqual(vsev['CHRONIC_CONDITION']['MODERATE'], 1)

    # 9. test_vulnerable_age_gender_severity
    def test_vulnerable_age_gender_severity(self):
        """
        Verify the complete combination: vulnerable group + age group + gender + severity.
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn('vulnerable_age_gender_severity', res.data)
        v4d = res.data['vulnerable_age_gender_severity']

        self.assertEqual(v4d['ELDERLY']['60+']['MALE']['SEVERE'], 2)
        self.assertEqual(v4d['PREGNANT']['25-44']['FEMALE']['SEVERE'], 1)
        self.assertEqual(v4d['LOW_INCOME_SLUM']['0-5']['MALE']['MILD'], 1)
        self.assertEqual(v4d['CHRONIC_CONDITION']['45-59']['FEMALE']['MODERATE'], 1)

    # 10. test_vulnerable_group_plus_disease
    def test_vulnerable_group_plus_disease(self):
        """
        Verify disease filtering AND vulnerable_group use AND semantics.
        """
        url = reverse('intelligence_historical_disease')

        # ELDERLY + Dengue -> 2 cases (c_aug_2, c_oct_2)
        res_dengue = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&vulnerable_group=ELDERLY")
        self.assertEqual(res_dengue.status_code, status.HTTP_200_OK)
        self.assertEqual(res_dengue.data['total_cases_in_history'], 2)

        # ELDERLY + Malaria -> 1 case (c_sep_2)
        res_malaria = self.client.get(f"{url}?disease=Malaria&date={self.as_of}&vulnerable_group=ELDERLY")
        self.assertEqual(res_malaria.status_code, status.HTTP_200_OK)
        self.assertEqual(res_malaria.data['total_cases_in_history'], 1)

        # PREGNANT + Malaria -> 0 cases
        res_preg_malaria = self.client.get(f"{url}?disease=Malaria&date={self.as_of}&vulnerable_group=PREGNANT")
        self.assertEqual(res_preg_malaria.status_code, status.HTTP_200_OK)
        self.assertEqual(res_preg_malaria.data['total_cases_in_history'], 0)

    # 11. test_vulnerable_group_plus_age
    def test_vulnerable_group_plus_age(self):
        """
        Verify vulnerable_group AND age_group use AND semantics.
        """
        url = reverse('intelligence_historical_disease')

        # LOW_INCOME_SLUM + 0-5 -> 1 case (c_may_1)
        res_child = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&vulnerable_group=LOW_INCOME_SLUM&age_group=0-5")
        self.assertEqual(res_child.status_code, status.HTTP_200_OK)
        self.assertEqual(res_child.data['total_cases_in_history'], 1)

        # LOW_INCOME_SLUM + 45-59 -> 0 cases
        res_none = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&vulnerable_group=LOW_INCOME_SLUM&age_group=45-59")
        self.assertEqual(res_none.status_code, status.HTTP_200_OK)
        self.assertEqual(res_none.data['total_cases_in_history'], 0)

    # 12. test_vulnerable_group_plus_gender
    def test_vulnerable_group_plus_gender(self):
        """
        Verify vulnerable_group AND gender use AND semantics.
        """
        url = reverse('intelligence_historical_disease')

        # PREGNANT + FEMALE -> 1 case (c_jul_1)
        res_fem = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&vulnerable_group=PREGNANT&gender=FEMALE")
        self.assertEqual(res_fem.status_code, status.HTTP_200_OK)
        self.assertEqual(res_fem.data['total_cases_in_history'], 1)

        # PREGNANT + MALE -> 0 cases
        res_male = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&vulnerable_group=PREGNANT&gender=MALE")
        self.assertEqual(res_male.status_code, status.HTTP_200_OK)
        self.assertEqual(res_male.data['total_cases_in_history'], 0)

    # 13. test_vulnerable_group_plus_severity
    def test_vulnerable_group_plus_severity(self):
        """
        Verify vulnerable_group AND severity use AND semantics.
        """
        url = reverse('intelligence_historical_disease')

        # ELDERLY + SEVERE -> 2 Dengue cases
        res_sev = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&vulnerable_group=ELDERLY&severity=SEVERE")
        self.assertEqual(res_sev.status_code, status.HTTP_200_OK)
        self.assertEqual(res_sev.data['total_cases_in_history'], 2)

        # ELDERLY + MILD -> 0 Dengue cases
        res_mild = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&vulnerable_group=ELDERLY&severity=MILD")
        self.assertEqual(res_mild.status_code, status.HTTP_200_OK)
        self.assertEqual(res_mild.data['total_cases_in_history'], 0)

    # 14. test_full_combination
    def test_full_combination(self):
        """
        Verify complete combination: disease + vulnerable_group + age_group + gender + severity.
        """
        url = reverse('intelligence_historical_disease')

        # LOW_INCOME_SLUM + 0-5 + MALE + MILD + Dengue -> 1 case (c_may_1)
        res = self.client.get(
            f"{url}?disease=Dengue&date={self.as_of}&vulnerable_group=LOW_INCOME_SLUM&age_group=0-5&gender=MALE&severity=MILD"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_cases_in_history'], 1)

        # Changing severity to SEVERE -> 0 cases
        res_mismatch = self.client.get(
            f"{url}?disease=Dengue&date={self.as_of}&vulnerable_group=LOW_INCOME_SLUM&age_group=0-5&gender=MALE&severity=SEVERE"
        )
        self.assertEqual(res_mismatch.status_code, status.HTTP_200_OK)
        self.assertEqual(res_mismatch.data['total_cases_in_history'], 0)

    # 15. Endpoint coverage: Disease Trends
    def test_endpoint_coverage_trends(self):
        """
        Verify disease trends endpoint applies vulnerable_group filter and case counts change.
        """
        url = reverse('intelligence_disease_trends')

        # Unfiltered vs filtered
        res_all = self.client.get(f"{url}?disease=Dengue&facility={self.fac_c1.id}&date={self.as_of}")
        res_filtered = self.client.get(f"{url}?disease=Dengue&facility={self.fac_c1.id}&date={self.as_of}&vulnerable_group=ELDERLY")

        self.assertEqual(res_all.status_code, status.HTTP_200_OK)
        self.assertEqual(res_filtered.status_code, status.HTTP_200_OK)

        t_all = next((d['current_cases'] for d in res_all.data['disease_trends'] if d['disease'] == 'Dengue'), 0)
        t_elder = next((d['current_cases'] for d in res_filtered.data['disease_trends'] if d['disease'] == 'Dengue'), 0)

        # Unfiltered has 2 cases in current window (c_oct_1 UNKNOWN, c_oct_2 ELDERLY); ELDERLY filter has 1
        self.assertGreater(t_all, t_elder)
        self.assertEqual(t_elder, 1)

    # 16. Endpoint coverage: Disease Locality
    def test_endpoint_coverage_locality(self):
        """
        Verify disease locality endpoint applies vulnerable_group filter and case counts change.
        """
        url = reverse('intelligence_disease_by_locality')

        res_all = self.client.get(f"{url}?disease=Dengue&facility={self.fac_c1.id}&date={self.as_of}&days=30")
        res_filtered = self.client.get(f"{url}?disease=Dengue&facility={self.fac_c1.id}&date={self.as_of}&days=30&vulnerable_group=ELDERLY")

        self.assertEqual(res_all.status_code, status.HTTP_200_OK)
        self.assertEqual(res_filtered.status_code, status.HTTP_200_OK)

        tot_all = sum(loc['current_cases'] for loc in res_all.data['locality_aggregations'])
        tot_elder = sum(loc['current_cases'] for loc in res_filtered.data['locality_aggregations'])

        self.assertGreater(tot_all, tot_elder)

    # 17. Endpoint coverage: Historical Disease
    def test_endpoint_coverage_historical(self):
        """
        Verify historical disease endpoint applies vulnerable_group filter and case counts change.
        """
        url = reverse('intelligence_historical_disease')

        res_all = self.client.get(f"{url}?disease=Dengue&facility={self.fac_c1.id}&date={self.as_of}")
        res_filtered = self.client.get(f"{url}?disease=Dengue&facility={self.fac_c1.id}&date={self.as_of}&vulnerable_group=ELDERLY")

        self.assertEqual(res_all.status_code, status.HTTP_200_OK)
        self.assertEqual(res_filtered.status_code, status.HTTP_200_OK)

        self.assertGreater(res_all.data['total_cases_in_history'], res_filtered.data['total_cases_in_history'])
        self.assertEqual(res_filtered.data['total_cases_in_history'], 2)

    # 18. Endpoint coverage: Hospital Aggregation
    def test_endpoint_coverage_hospital(self):
        """
        Verify hospital aggregation endpoint applies vulnerable_group filter and case counts change.
        """
        url = reverse('intelligence_hospital_aggregation')

        res_all = self.client.get(f"{url}?facility={self.fac_c1.id}&date={self.as_of}&days=30")
        res_filtered = self.client.get(f"{url}?facility={self.fac_c1.id}&date={self.as_of}&days=30&vulnerable_group=ELDERLY")

        self.assertEqual(res_all.status_code, status.HTTP_200_OK)
        self.assertEqual(res_filtered.status_code, status.HTTP_200_OK)

        tot_all = res_all.data['cases_30d']
        tot_elder = res_filtered.data['cases_30d']
        self.assertGreater(tot_all, tot_elder)

    # 19. Endpoint coverage: District Aggregation
    def test_endpoint_coverage_district(self):
        """
        Verify district aggregation endpoint applies vulnerable_group filter and case counts change.
        """
        self.client.force_authenticate(user=self.officer_c)
        url = reverse('intelligence_district_aggregation')

        res_all = self.client.get(f"{url}?district={self.district_central.id}&date={self.as_of}&days=30")
        res_filtered = self.client.get(f"{url}?district={self.district_central.id}&date={self.as_of}&days=30&vulnerable_group=ELDERLY")

        self.assertEqual(res_all.status_code, status.HTTP_200_OK)
        self.assertEqual(res_filtered.status_code, status.HTTP_200_OK)

        tot_all = res_all.data['summary']['total_current_cases']
        tot_elder = res_filtered.data['summary']['total_current_cases']
        self.assertGreater(tot_all, tot_elder)

    # 20. Endpoint coverage: Summary
    def test_endpoint_coverage_summary(self):
        """
        Verify intelligence summary endpoint applies vulnerable_group filter and case counts change.
        """
        url = reverse('intelligence_summary')

        res_all = self.client.get(f"{url}?facility={self.fac_c1.id}&date={self.as_of}")
        res_filtered = self.client.get(f"{url}?facility={self.fac_c1.id}&date={self.as_of}&vulnerable_group=ELDERLY")

        self.assertEqual(res_all.status_code, status.HTTP_200_OK)
        self.assertEqual(res_filtered.status_code, status.HTTP_200_OK)

        tot_all = res_all.data['cases_30d']
        tot_elder = res_filtered.data['cases_30d']
        self.assertGreater(tot_all, tot_elder)

    # 21. Authorization: Hospital Admin within assigned facility -> allowed (200)
    def test_authorization_hospital_admin_assigned_facility(self):
        """
        Hospital Admin with valid vulnerable_group within assigned facility -> allowed.
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?facility={self.fac_c1.id}&disease=Dengue&vulnerable_group=ELDERLY")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    # 22. Authorization: Hospital Admin cross-facility -> 403
    def test_authorization_hospital_admin_cross_facility_forbidden(self):
        """
        Hospital Admin requesting another facility -> 403.
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?facility={self.fac_r1.id}&disease=Dengue&vulnerable_group=ELDERLY")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 23. Authorization: District Officer within assigned district -> allowed (200)
    def test_authorization_district_officer_assigned_district(self):
        """
        District Officer with valid vulnerable_group within assigned district -> allowed.
        """
        self.client.force_authenticate(user=self.officer_c)
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?district={self.district_central.id}&disease=Dengue&vulnerable_group=ELDERLY")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    # 24. Authorization: District Officer cross-district -> 403
    def test_authorization_district_officer_cross_district_forbidden(self):
        """
        District Officer requesting another district -> 403.
        """
        self.client.force_authenticate(user=self.officer_c)
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?district={self.district_rural.id}&disease=Dengue&vulnerable_group=ELDERLY")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 25. Authorization: Invalid vulnerable_group does NOT bypass authorization
    def test_authorization_invalid_vulnerable_group_does_not_bypass_scope(self):
        """
        Verify that invalid vulnerable_group does NOT bypass authorization.
        Authorization is resolved before returning analytical data or evaluating filters.
        """
        url = reverse('intelligence_historical_disease')
        # Hospital Admin requesting another facility with invalid vulnerable_group
        res = self.client.get(f"{url}?facility={self.fac_r1.id}&disease=Dengue&vulnerable_group=INVALID_GROUP")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 26. Unknown data handling
    def test_unknown_data_handling(self):
        """
        Create a patient with vulnerability_information='' or unsupported value.
        Verify it is classified as UNKNOWN in analytical output.
        Verify vulnerable_group=UNKNOWN returns HTTP 400.
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        vg_map = {item['vulnerable_group']: item['total_cases'] for item in res.data['historical_vulnerable_groups']}
        self.assertIn('UNKNOWN', vg_map)
        self.assertEqual(vg_map['UNKNOWN'], 2)

        # Filter parameter vulnerable_group=UNKNOWN returns 400
        res_bad = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&vulnerable_group=UNKNOWN")
        self.assertEqual(res_bad.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', res_bad.data)

    # 27. Backward compatibility
    def test_backward_compatibility_omitted_filter(self):
        """
        Call intelligence endpoints without vulnerable_group:
        Existing totals and behavior remain unchanged and all Prompt 1-4 fields preserved.
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_cases_in_history'], 9)

        required_keys = [
            'disease', 'months_analyzed', 'total_cases_in_history', 'monthly_average',
            'mean_monthly_cases', 'current_month_cases', 'previous_month_cases',
            'percentage_change', 'trend_direction', 'explanation', 'historical_series',
            'monthly_series', 'severity_breakdown', 'observation_period',
            'historical_age_groups', 'historical_gender', 'age_gender_matrix',
            'monthly_demographic_trends', 'historical_severity', 'monthly_severity_trends',
            'severity_age_groups', 'severity_gender', 'severity_age_gender',
            'historical_vulnerable_groups', 'monthly_vulnerable_population_trends',
            'vulnerable_age_groups', 'vulnerable_gender', 'vulnerable_age_gender',
            'vulnerable_severity', 'vulnerable_age_gender_severity'
        ]
        for key in required_keys:
            self.assertIn(key, res.data, f"Required response key '{key}' missing.")

    # 28. Age reference date uses DiseaseCase.report_date
    def test_age_reference_date_uses_report_date(self):
        """
        Explicitly verify that vulnerable demographic age uses DiseaseCase.report_date
        rather than today's date.
        Create a patient whose age-group classification changes depending on the reference date.
        Verify historical cases use the age on their respective report dates.
        """
        # Patient born 2020-07-01:
        # On 2026-06-30: age 5 -> '0-5'
        # On 2026-07-02: age 6 -> '6-14'
        p_aging = Patient.objects.create(
            patient_id='P-AGING-VP2', name='Aging Test Patient',
            date_of_birth=datetime.date(2020, 7, 1), age=6, gender='MALE',
            vulnerability_information='Slum Resident / Low Income Group',
            district=self.district_central, ward=self.ward_c1, registered_at_facility=self.fac_c1
        )
        DiseaseCase.objects.create(
            disease_name='Cholera', patient=p_aging, facility=self.fac_c1,
            ward=self.ward_c1, report_date=datetime.date(2026, 6, 30), severity='MILD'
        )
        DiseaseCase.objects.create(
            disease_name='Cholera', patient=p_aging, facility=self.fac_c1,
            ward=self.ward_c1, report_date=datetime.date(2026, 7, 2), severity='MILD'
        )

        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?disease=Cholera&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        vag = res.data['vulnerable_age_groups']
        # Slum resident has 1 case in '0-5' and 1 case in '6-14'
        self.assertEqual(vag['LOW_INCOME_SLUM']['0-5'], 1)
        self.assertEqual(vag['LOW_INCOME_SLUM']['6-14'], 1)

    # 29. Query efficiency
    def test_query_efficiency_no_n_plus_one(self):
        """
        Verify that historical vulnerable population aggregation executes in strictly 1 query
        via select_related('patient'), preventing N+1 queries.
        """
        with self.assertNumQueries(1):
            aggregate_historical_disease(
                facility_ids=[self.fac_c1.id],
                disease_name='Dengue',
                months=6,
                as_of_date=self.as_of
            )

    # Aliases for numbered test discovery compatibility
    test_01_vulnerable_group_validation = test_vulnerable_group_validation
    test_02_vulnerable_group_filtering_correctness = test_vulnerable_group_filtering
    test_03_combined_filter_vulnerable_group_and_disease = test_vulnerable_group_plus_disease
    test_04_combined_filter_vulnerable_group_and_severity = test_vulnerable_group_plus_severity
    test_05_combined_filter_vulnerable_group_and_age_group = test_vulnerable_group_plus_age
    test_06_combined_filter_vulnerable_group_and_gender = test_vulnerable_group_plus_gender
    test_07_combined_all_demographic_severity_vulnerable_filters = test_full_combination
    test_08_historical_vulnerable_groups_structure_and_counts = test_historical_vulnerable_groups
    test_09_monthly_vulnerable_population_trends_sum_invariant = test_monthly_vulnerable_population_trends
    test_10_vulnerable_age_groups_matrix = test_vulnerable_age_groups
    test_11_vulnerable_gender_matrix = test_vulnerable_gender
    test_12_vulnerable_age_gender_matrix = test_vulnerable_age_gender
    test_13_vulnerable_severity_matrix = test_vulnerable_severity
    test_14_vulnerable_age_gender_severity_matrix = test_vulnerable_age_gender_severity
    test_15_role_based_authorization_unauthorized_returns_403 = test_authorization_hospital_admin_cross_facility_forbidden
    test_16_missing_and_unknown_vulnerability_handling = test_unknown_data_handling
    test_17_backward_compatibility_when_omitted = test_backward_compatibility_omitted_filter
    test_18_endpoint_coverage_trends = test_endpoint_coverage_trends
    test_19_endpoint_coverage_locality = test_endpoint_coverage_locality
    test_20_endpoint_coverage_hospital_and_district = test_endpoint_coverage_hospital
    test_21_endpoint_coverage_summary = test_endpoint_coverage_summary
    test_23_age_calculation_uses_case_report_date = test_age_reference_date_uses_report_date
    test_24_query_efficiency_no_n_plus_one = test_query_efficiency_no_n_plus_one


# ===========================================================================
# PROMPT 6: Patient Type Analysis Test Suite
# ===========================================================================

class PublicHealthPatientTypeTestCase(TestCase):
    """
    Comprehensive test suite for Prompt 6: Patient Type Analysis.
    Implements all 36 required scenarios:
    1. Patient type classification — first case is NEW.
    2. Subsequent case is FOLLOW_UP.
    3. Historical classification respects each case's report_date.
    4. Future cases do not affect earlier classification.
    5. Patient type validation.
    6. NEW filtering works.
    7. FOLLOW_UP filtering works.
    8. Invalid patient_type returns 400.
    9. UNKNOWN cannot be used as a filter.
    10. Disease + patient_type.
    11. Patient type + age_group.
    12. Patient type + gender.
    13. Patient type + age_group + gender.
    14. Patient type + severity.
    15. Patient type + vulnerable_group.
    16. Patient type + all demographic/severity/vulnerability filters.
    17. Historical patient-type counts.
    18. Monthly patient-type trends.
    19. Patient type + age matrix.
    20. Patient type + gender matrix.
    21. Patient type + age/gender matrix.
    22. Patient type + severity matrix.
    23. Patient type + vulnerability matrix.
    24. Trends endpoint coverage.
    25. Locality endpoint coverage.
    26. Hospital aggregation coverage.
    27. District aggregation coverage.
    28. Summary endpoint coverage.
    29. Forecast endpoint coverage.
    30. Seasonality endpoint coverage.
    31. Hospital Admin facility authorization remains 403 cross-facility.
    32. District Officer district authorization remains 403 cross-district.
    33. No patient_type filter preserves existing behavior.
    34. Patient type filter is never silently ignored.
    35. Missing/insufficient history produces UNKNOWN.
    36. Query efficiency / no N+1.
    """

    @classmethod
    def setUpTestData(cls):
        # Geography
        cls.state = State.objects.create(name='Karnataka', code='KA')
        cls.district_central = District.objects.create(state=cls.state, name='BBMP Central', code='KA-CEN')
        cls.district_rural = District.objects.create(state=cls.state, name='Bengaluru Rural', code='KA-RUR')

        cls.zone_central = Zone.objects.create(district=cls.district_central, name='Central Zone', code='Z-CEN')
        cls.zone_rural = Zone.objects.create(district=cls.district_rural, name='Rural Zone', code='Z-RUR')

        cls.ward_c1 = Ward.objects.create(zone=cls.zone_central, ward_number=101, name='Indiranagar', population=25000)
        cls.ward_r1 = Ward.objects.create(zone=cls.zone_rural, ward_number=201, name='Varthur', population=18000)

        # Facilities
        cls.fac_c1 = Facility.objects.create(
            facility_code='HOSP-PT1', facility_name='Bowring Hospital', facility_type='MAIN_HOSPITAL',
            district=cls.district_central, ward=cls.ward_c1, state=cls.state
        )
        cls.fac_c2 = Facility.objects.create(
            facility_code='CLINIC-PT2', facility_name='Indiranagar Urban Health Centre', facility_type='NAMMA_CLINIC',
            district=cls.district_central, ward=cls.ward_c1, state=cls.state
        )
        cls.fac_r1 = Facility.objects.create(
            facility_code='RURAL-PT1', facility_name='Varthur Community Health Centre', facility_type='RURAL_CLINIC',
            district=cls.district_rural, ward=cls.ward_r1, state=cls.state
        )

        # Users
        cls.admin_c1 = User.objects.create_user(
            username='pt_admin_c1', password='Password123!', role='HOSPITAL_ADMIN',
            assigned_facility=cls.fac_c1
        )
        cls.officer_c = User.objects.create_user(
            username='pt_officer_c', password='Password123!', role='DISTRICT_OFFICER',
            assigned_district=cls.district_central
        )
        cls.officer_r = User.objects.create_user(
            username='pt_officer_r', password='Password123!', role='DISTRICT_OFFICER',
            assigned_district=cls.district_rural
        )

        # Reference date: 2026-10-04 (6-month historical window: 2026-05-01 to 2026-10-31)
        cls.as_of = datetime.date(2026, 10, 4)

        # Deterministic Patients
        # P1: Adult Male with multiple longitudinal visits
        cls.p_male_adult = Patient.objects.create(
            patient_id='PT-01', name='Adult Male Patient',
            date_of_birth=datetime.date(1996, 5, 15), age=30, gender='MALE',
            vulnerability_information='Slum Resident / Low Income Group',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # P2: Young Pregnant Female with multiple visits
        cls.p_female_pregnant = Patient.objects.create(
            patient_id='PT-02', name='Pregnant Female Patient',
            date_of_birth=datetime.date(2006, 5, 15), age=20, gender='FEMALE',
            vulnerability_information='Pregnant Woman',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # P3: Elderly Senior Male (60+)
        cls.p_elderly = Patient.objects.create(
            patient_id='PT-03', name='Elderly Senior Male',
            date_of_birth=datetime.date(1956, 5, 15), age=70, gender='MALE',
            vulnerability_information='Elderly Person',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # P4: Infant Female Child (0-5)
        cls.p_child = Patient.objects.create(
            patient_id='PT-04', name='Infant Child Girl',
            date_of_birth=datetime.date(2024, 5, 15), age=2, gender='FEMALE',
            vulnerability_information='Slum Resident / Low Income Group',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # P5: School Child Other (6-14, OTHER gender, Disability)
        cls.p_youth = Patient.objects.create(
            patient_id='PT-05', name='School Child Other',
            date_of_birth=datetime.date(2016, 5, 15), age=10, gender='OTHER',
            vulnerability_information='Person with Disability (PwD)',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # P6: Middle Aged Female (45-59, Chronic Condition)
        cls.p_middle = Patient.objects.create(
            patient_id='PT-06', name='Middle Aged Female',
            date_of_birth=datetime.date(1976, 5, 15), age=50, gender='FEMALE',
            vulnerability_information='Hypertension / Diabetic comorbidity',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # P7: Rural Patient
        cls.p_rural = Patient.objects.create(
            patient_id='PT-07', name='Rural Community Patient',
            date_of_birth=datetime.date(1995, 1, 1), age=31, gender='FEMALE',
            vulnerability_information='Slum Resident / Low Income Group',
            district=cls.district_rural, ward=cls.ward_r1, registered_at_facility=cls.fac_r1
        )

        # -------------------------------------------------------------------
        # Disease Cases at fac_c1 (May 2026 to October 2026)
        # -------------------------------------------------------------------
        # May 2026: Case 1 -> P1 (MALE, 25-44, MILD, LOW_INCOME_SLUM) -> NEW
        cls.c_may_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_male_adult, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 5, 10), severity='MILD'
        )

        # June 2026: Case 2 -> P2 (FEMALE, 15-24, SEVERE, PREGNANT) -> NEW
        cls.c_jun_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_female_pregnant, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 6, 12), severity='SEVERE'
        )

        # July 2026:
        # Case 3 -> P1 (MALE, 25-44, SEVERE, LOW_INCOME_SLUM) -> FOLLOW_UP (prior case on 2026-05-10)
        cls.c_jul_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_male_adult, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 7, 15), severity='SEVERE'
        )
        # Case 4 -> P3 (MALE, 60+, MODERATE, ELDERLY) -> NEW
        cls.c_jul_2 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_elderly, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 7, 20), severity='MODERATE'
        )

        # August 2026:
        # Case 5 -> P2 (FEMALE, 15-24, SEVERE, PREGNANT) -> FOLLOW_UP (prior case on 2026-06-12)
        cls.c_aug_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_female_pregnant, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 8, 10), severity='SEVERE'
        )
        # Case 6 -> P4 (FEMALE, 0-5, MILD, LOW_INCOME_SLUM) -> NEW
        cls.c_aug_2 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_child, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 8, 25), severity='MILD'
        )

        # September 2026:
        # Case 7 -> P5 (OTHER, 6-14, MILD, MIGRANT_WORKER) -> NEW
        cls.c_sep_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_youth, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 9, 5), severity='MILD'
        )
        # Case 8 -> P1 (MALE, 25-44, MODERATE, LOW_INCOME_SLUM) -> FOLLOW_UP (prior cases on 2026-05-10, 2026-07-15)
        cls.c_sep_2 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_male_adult, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 9, 20), severity='MODERATE'
        )

        # October 2026:
        # Case 9 -> P6 (FEMALE, 45-59, MILD, CHRONIC_CONDITION) -> NEW
        cls.c_oct_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_middle, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 10, 1), severity='MILD'
        )

        # Cross-facility case (same central district)
        cls.c_fac_c2_dengue = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_female_pregnant, facility=cls.fac_c2,
            ward=cls.ward_c1, report_date=datetime.date(2026, 9, 15), severity='MILD'
        )

        # Cross-disease case (Malaria at fac_c1)
        cls.c_malaria = DiseaseCase.objects.create(
            disease_name='Malaria', patient=cls.p_male_adult, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 9, 18), severity='MILD'
        )

        # Cross-district case (Rural Dengue at fac_r1)
        cls.c_rural_dengue = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_rural, facility=cls.fac_r1,
            ward=cls.ward_r1, report_date=datetime.date(2026, 9, 15), severity='MILD'
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_c1)

    # 1. Patient type classification — first case is NEW
    def test_01_classification_first_case_is_new(self):
        """
        Verify that a patient's first recorded clinical case in the available system history is NEW.
        """
        pt = get_case_patient_type(self.c_may_1)
        self.assertEqual(pt, PATIENT_TYPE_NEW)

    # 2. Subsequent case is FOLLOW_UP
    def test_02_classification_subsequent_case_is_follow_up(self):
        """
        Verify that a subsequent clinical case for the same patient before the case report_date is FOLLOW_UP.
        """
        pt_jul = get_case_patient_type(self.c_jul_1)
        self.assertEqual(pt_jul, PATIENT_TYPE_FOLLOW_UP)
        pt_sep = get_case_patient_type(self.c_sep_2)
        self.assertEqual(pt_sep, PATIENT_TYPE_FOLLOW_UP)

    # 3. Historical classification respects each case's report_date
    def test_03_historical_classification_respects_case_report_date(self):
        """
        Classification is evaluated point-in-time relative to each case's own report_date.
        On 2026-05-10, P1 has no prior case -> NEW.
        On 2026-07-15, P1 has a prior case (May 10) -> FOLLOW_UP.
        """
        pt_may = get_case_patient_type(self.c_may_1)
        pt_jul = get_case_patient_type(self.c_jul_1)
        self.assertEqual(pt_may, PATIENT_TYPE_NEW)
        self.assertEqual(pt_jul, PATIENT_TYPE_FOLLOW_UP)

    # 4. Future cases do not affect earlier classification
    def test_04_future_cases_do_not_affect_earlier_classification(self):
        """
        P1 has cases on 2026-05-10, 2026-07-15, and 2026-09-20.
        When evaluated, the 2026-05-10 case must remain NEW regardless of future records.
        """
        pt_first = get_case_patient_type(self.c_may_1)
        self.assertEqual(pt_first, PATIENT_TYPE_NEW)
        # Add another future case in November 2026
        future_case = DiseaseCase.objects.create(
            disease_name='Dengue', patient=self.p_male_adult, facility=self.fac_c1,
            ward=self.ward_c1, report_date=datetime.date(2026, 11, 15), severity='MILD'
        )
        self.assertEqual(get_case_patient_type(self.c_may_1), PATIENT_TYPE_NEW)
        self.assertEqual(get_case_patient_type(future_case), PATIENT_TYPE_FOLLOW_UP)
        future_case.delete()

    # 5. Patient type validation
    def test_05_patient_type_validation(self):
        """
        Validates:
        - NEW -> ('NEW', None)
        - FOLLOW_UP -> ('FOLLOW_UP', None)
        - FOLLOWUP -> ('FOLLOW_UP', None)
        - None / empty -> (None, None)
        - UNKNOWN -> returns error message (rejected)
        - Invalid string -> returns error message
        """
        clean, err = validate_patient_type_param('NEW')
        self.assertEqual(clean, 'NEW')
        self.assertIsNone(err)

        clean, err = validate_patient_type_param('FOLLOW_UP')
        self.assertEqual(clean, 'FOLLOW_UP')
        self.assertIsNone(err)

        clean, err = validate_patient_type_param('FOLLOWUP')
        self.assertEqual(clean, 'FOLLOW_UP')
        self.assertIsNone(err)

        clean, err = validate_patient_type_param(None)
        self.assertIsNone(clean)
        self.assertIsNone(err)

        clean, err = validate_patient_type_param('UNKNOWN')
        self.assertIsNone(clean)
        self.assertIsNotNone(err)

        clean, err = validate_patient_type_param('INVALID_TYPE')
        self.assertIsNone(clean)
        self.assertIsNotNone(err)

    # 6. NEW filtering works
    def test_06_new_filtering_works(self):
        """
        patient_type=NEW filters strictly to NEW cases (6 cases at fac_c1).
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?disease=Dengue&patient_type=NEW&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_cases_in_history'], 6)

    # 7. FOLLOW_UP filtering works
    def test_07_follow_up_filtering_works(self):
        """
        patient_type=FOLLOW_UP filters strictly to FOLLOW_UP cases (3 cases at fac_c1).
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?disease=Dengue&patient_type=FOLLOW_UP&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_cases_in_history'], 3)

    # 8. Invalid patient_type returns 400
    def test_08_invalid_patient_type_returns_400(self):
        """
        Supplying an unsupported patient_type parameter returns HTTP 400 Bad Request.
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?disease=Dengue&patient_type=INVALID_VAL&date={self.as_of}")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', res.data)

    # 9. UNKNOWN cannot be used as a filter
    def test_09_unknown_cannot_be_used_as_filter(self):
        """
        patient_type=UNKNOWN must NOT be accepted as a filter value and returns HTTP 400.
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?disease=Dengue&patient_type=UNKNOWN&date={self.as_of}")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', res.data)

    # 10. Disease + patient_type
    def test_10_disease_plus_patient_type(self):
        """
        disease=Dengue&patient_type=NEW returns only Dengue cases that are NEW,
        excluding Malaria cases.
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?disease=Dengue&patient_type=NEW&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_cases_in_history'], 6)
        self.assertEqual(res.data['disease'], 'Dengue')

    # 11. Patient type + age_group
    def test_11_patient_type_plus_age_group(self):
        """
        patient_type=FOLLOW_UP&age_group=25-44 applies AND logic (P1 cases in Jul and Sep = 2).
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?disease=Dengue&patient_type=FOLLOW_UP&age_group=25-44&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_cases_in_history'], 2)

    # 12. Patient type + gender
    def test_12_patient_type_plus_gender(self):
        """
        patient_type=NEW&gender=FEMALE applies AND logic (P2 Jun, P4 Aug, P6 Oct = 3 cases).
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?disease=Dengue&patient_type=NEW&gender=FEMALE&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_cases_in_history'], 3)

    # 13. Patient type + age_group + gender
    def test_13_patient_type_plus_age_group_plus_gender(self):
        """
        patient_type=NEW&age_group=15-24&gender=FEMALE applies AND logic (P2 Jun = 1 case).
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(
            f"{url}?disease=Dengue&patient_type=NEW&age_group=15-24&gender=FEMALE&date={self.as_of}&months=6"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_cases_in_history'], 1)

    # 14. Patient type + severity
    def test_14_patient_type_plus_severity(self):
        """
        patient_type=NEW&severity=SEVERE matches only NEW + SEVERE (P2 Jun = 1 case).
        patient_type=FOLLOW_UP&severity=SEVERE matches (P1 Jul, P2 Aug = 2 cases).
        """
        url = reverse('intelligence_historical_disease')
        res_new = self.client.get(f"{url}?disease=Dengue&patient_type=NEW&severity=SEVERE&date={self.as_of}&months=6")
        self.assertEqual(res_new.status_code, status.HTTP_200_OK)
        self.assertEqual(res_new.data['total_cases_in_history'], 1)

        res_fu = self.client.get(f"{url}?disease=Dengue&patient_type=FOLLOW_UP&severity=SEVERE&date={self.as_of}&months=6")
        self.assertEqual(res_fu.status_code, status.HTTP_200_OK)
        self.assertEqual(res_fu.data['total_cases_in_history'], 2)

    # 15. Patient type + vulnerable_group
    def test_15_patient_type_plus_vulnerable_group(self):
        """
        patient_type=FOLLOW_UP&vulnerable_group=PREGNANT matches P2 Aug case = 1.
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(
            f"{url}?disease=Dengue&patient_type=FOLLOW_UP&vulnerable_group=PREGNANT&date={self.as_of}&months=6"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_cases_in_history'], 1)

    # 16. Patient type + all demographic/severity/vulnerability filters
    def test_16_patient_type_plus_all_filters(self):
        """
        Dengue + NEW + 15-24 + FEMALE + SEVERE + PREGNANT = 1 case (P2 Jun).
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(
            f"{url}?disease=Dengue&patient_type=NEW&age_group=15-24&gender=FEMALE&severity=SEVERE&vulnerable_group=PREGNANT&date={self.as_of}&months=6"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_cases_in_history'], 1)

    # 17. Historical patient-type counts
    def test_17_historical_patient_type_counts(self):
        """
        Verify historical_patient_type dict has NEW=6, FOLLOW_UP=3, summing to 9.
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn('historical_patient_type', res.data)
        hpt = res.data['historical_patient_type']
        self.assertEqual(hpt['NEW'], 6)
        self.assertEqual(hpt['FOLLOW_UP'], 3)
        self.assertEqual(hpt['NEW'] + hpt['FOLLOW_UP'], res.data['total_cases_in_history'])

    # 18. Monthly patient-type trends
    def test_18_monthly_patient_type_trends(self):
        """
        Verify monthly_patient_type_trends contains 6 monthly records,
        and each month's NEW + FOLLOW_UP equals total_cases.
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn('monthly_patient_type_trends', res.data)
        m_trends = res.data['monthly_patient_type_trends']
        self.assertEqual(len(m_trends), 6)

        trend_map = {t['month']: t for t in m_trends}
        # May: 1 NEW, 0 FOLLOW_UP
        self.assertEqual(trend_map['2026-05']['NEW'], 1)
        self.assertEqual(trend_map['2026-05']['FOLLOW_UP'], 0)
        # July: 1 NEW (P3), 1 FOLLOW_UP (P1)
        self.assertEqual(trend_map['2026-07']['NEW'], 1)
        self.assertEqual(trend_map['2026-07']['FOLLOW_UP'], 1)
        # August: 1 NEW (P4), 1 FOLLOW_UP (P2)
        self.assertEqual(trend_map['2026-08']['NEW'], 1)
        self.assertEqual(trend_map['2026-08']['FOLLOW_UP'], 1)

        for t in m_trends:
            self.assertEqual(t['NEW'] + t['FOLLOW_UP'], t['total_cases'])

    # 19. Patient type + age matrix
    def test_19_patient_type_age_groups_matrix(self):
        """
        Verify patient_type_age_groups matrix accurately captures NEW and FOLLOW_UP counts per age group.
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn('patient_type_age_groups', res.data)
        matrix = res.data['patient_type_age_groups']
        self.assertEqual(matrix['NEW']['0-5'], 1)
        self.assertEqual(matrix['NEW']['6-14'], 1)
        self.assertEqual(matrix['NEW']['15-24'], 1)
        self.assertEqual(matrix['NEW']['25-44'], 1)
        self.assertEqual(matrix['NEW']['45-59'], 1)
        self.assertEqual(matrix['NEW']['60+'], 1)

        self.assertEqual(matrix['FOLLOW_UP']['15-24'], 1)
        self.assertEqual(matrix['FOLLOW_UP']['25-44'], 2)
        self.assertEqual(matrix['FOLLOW_UP']['0-5'], 0)

    # 20. Patient type + gender matrix
    def test_20_patient_type_gender_matrix(self):
        """
        Verify patient_type_gender matrix captures NEW and FOLLOW_UP counts per gender.
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn('patient_type_gender', res.data)
        matrix = res.data['patient_type_gender']
        self.assertEqual(matrix['NEW']['MALE'], 2)
        self.assertEqual(matrix['NEW']['FEMALE'], 3)
        self.assertEqual(matrix['NEW']['OTHER'], 1)

        self.assertEqual(matrix['FOLLOW_UP']['MALE'], 2)
        self.assertEqual(matrix['FOLLOW_UP']['FEMALE'], 1)
        self.assertEqual(matrix['FOLLOW_UP']['OTHER'], 0)

    # 21. Patient type + age/gender matrix
    def test_21_patient_type_age_gender_matrix(self):
        """
        Verify patient_type_age_gender 3D cross-tabulation.
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn('patient_type_age_gender', res.data)
        matrix = res.data['patient_type_age_gender']
        self.assertEqual(matrix['NEW']['15-24']['FEMALE'], 1)
        self.assertEqual(matrix['NEW']['25-44']['MALE'], 1)
        self.assertEqual(matrix['NEW']['60+']['MALE'], 1)
        self.assertEqual(matrix['FOLLOW_UP']['25-44']['MALE'], 2)
        self.assertEqual(matrix['FOLLOW_UP']['15-24']['FEMALE'], 1)

    # 22. Patient type + severity matrix
    def test_22_patient_type_severity_matrix(self):
        """
        Verify patient_type_severity cross-tabulation.
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn('patient_type_severity', res.data)
        matrix = res.data['patient_type_severity']
        self.assertEqual(matrix['NEW']['MILD'], 4)
        self.assertEqual(matrix['NEW']['MODERATE'], 1)
        self.assertEqual(matrix['NEW']['SEVERE'], 1)

        self.assertEqual(matrix['FOLLOW_UP']['MILD'], 0)
        self.assertEqual(matrix['FOLLOW_UP']['MODERATE'], 1)
        self.assertEqual(matrix['FOLLOW_UP']['SEVERE'], 2)

    # 23. Patient type + vulnerability matrix
    def test_23_patient_type_vulnerability_matrix(self):
        """
        Verify patient_type_vulnerable_groups and patient_type_age_gender_vulnerability cross-tabulations.
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn('patient_type_vulnerable_groups', res.data)
        matrix = res.data['patient_type_vulnerable_groups']
        self.assertEqual(matrix['NEW']['LOW_INCOME_SLUM'], 2)
        self.assertEqual(matrix['NEW']['PREGNANT'], 1)
        self.assertEqual(matrix['NEW']['ELDERLY'], 1)
        self.assertEqual(matrix['NEW']['DISABILITY'], 1)
        self.assertEqual(matrix['NEW']['CHRONIC_CONDITION'], 1)

        self.assertEqual(matrix['FOLLOW_UP']['LOW_INCOME_SLUM'], 2)
        self.assertEqual(matrix['FOLLOW_UP']['PREGNANT'], 1)

        self.assertIn('patient_type_age_gender_vulnerability', res.data)

    # 24. Trends endpoint coverage
    def test_24_trends_endpoint_coverage(self):
        """
        Verifies /surveillance/intelligence/disease-trends/?patient_type=NEW filters appropriately.
        """
        url = reverse('intelligence_disease_trends')
        res = self.client.get(f"{url}?disease=Dengue&patient_type=NEW&date={self.as_of}&days=30")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('disease_trends', res.data)

        # Invalid patient_type on trends returns 400
        res_bad = self.client.get(f"{url}?patient_type=INVALID_VAL")
        self.assertEqual(res_bad.status_code, status.HTTP_400_BAD_REQUEST)

    # 25. Locality endpoint coverage
    def test_25_locality_endpoint_coverage(self):
        """
        Verifies /surveillance/intelligence/disease-by-locality/?patient_type=NEW filters appropriately.
        """
        url = reverse('intelligence_disease_by_locality')
        res = self.client.get(f"{url}?disease=Dengue&patient_type=NEW&date={self.as_of}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('locality_aggregations', res.data)

        res_bad = self.client.get(f"{url}?patient_type=INVALID_VAL")
        self.assertEqual(res_bad.status_code, status.HTTP_400_BAD_REQUEST)

    # 26. Hospital aggregation coverage
    def test_26_hospital_aggregation_coverage(self):
        """
        Verifies /surveillance/intelligence/hospital-aggregation/?patient_type=NEW works for assigned hospital.
        """
        url = reverse('intelligence_hospital_aggregation')
        res = self.client.get(f"{url}?facility={self.fac_c1.id}&patient_type=NEW&date={self.as_of}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('hospital', res.data)

        res_bad = self.client.get(f"{url}?facility={self.fac_c1.id}&patient_type=INVALID_VAL")
        self.assertEqual(res_bad.status_code, status.HTTP_400_BAD_REQUEST)

    # 27. District aggregation coverage
    def test_27_district_aggregation_coverage(self):
        """
        Verifies /surveillance/intelligence/district-aggregation/?patient_type=NEW works for District Officer.
        """
        self.client.force_authenticate(user=self.officer_c)
        url = reverse('intelligence_district_aggregation')
        res = self.client.get(f"{url}?district={self.district_central.id}&patient_type=NEW&date={self.as_of}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('district', res.data)

        res_bad = self.client.get(f"{url}?district={self.district_central.id}&patient_type=INVALID_VAL")
        self.assertEqual(res_bad.status_code, status.HTTP_400_BAD_REQUEST)

    # 28. Summary endpoint coverage
    def test_28_summary_endpoint_coverage(self):
        """
        Verifies /surveillance/intelligence/summary/?patient_type=NEW filters summary data.
        """
        url = reverse('intelligence_summary')
        res = self.client.get(f"{url}?facility={self.fac_c1.id}&patient_type=NEW&date={self.as_of}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        res_bad = self.client.get(f"{url}?facility={self.fac_c1.id}&patient_type=INVALID_VAL")
        self.assertEqual(res_bad.status_code, status.HTTP_400_BAD_REQUEST)

    # 29. Forecast endpoint coverage
    def test_29_forecast_endpoint_coverage(self):
        """
        Verifies /surveillance/intelligence/forecast/?disease=Dengue&patient_type=NEW:
        - Filters historical time series before forecasting
        - Clearly indicates selected patient type in filters dict
        """
        url = reverse('intelligence_forecast')
        res = self.client.get(f"{url}?facility={self.fac_c1.id}&disease=Dengue&patient_type=NEW&date={self.as_of}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('filters', res.data)
        self.assertEqual(res.data['filters']['patient_type'], 'NEW')

        # Invalid patient_type on forecast returns 400
        res_bad = self.client.get(f"{url}?facility={self.fac_c1.id}&disease=Dengue&patient_type=INVALID_VAL")
        self.assertEqual(res_bad.status_code, status.HTTP_400_BAD_REQUEST)

    # 30. Seasonality endpoint coverage
    def test_30_seasonality_endpoint_coverage(self):
        """
        Verifies /surveillance/intelligence/seasonality/?disease=Dengue&patient_type=NEW calculates
        seasonality using only matching cases.
        """
        url = reverse('intelligence_seasonality')
        res = self.client.get(f"{url}?facility={self.fac_c1.id}&disease=Dengue&patient_type=NEW&date={self.as_of}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        res_bad = self.client.get(f"{url}?facility={self.fac_c1.id}&disease=Dengue&patient_type=INVALID_VAL")
        self.assertEqual(res_bad.status_code, status.HTTP_400_BAD_REQUEST)

    # 31. Hospital Admin facility authorization remains 403 cross-facility
    def test_31_hospital_admin_cross_facility_forbidden(self):
        """
        Hospital Admin requesting another facility returns HTTP 403 Forbidden.
        patient_type must never bypass facility authorization.
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?facility={self.fac_c2.id}&disease=Dengue&patient_type=NEW")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 32. District Officer district authorization remains 403 cross-district
    def test_32_district_officer_cross_district_forbidden(self):
        """
        District Officer requesting another district returns HTTP 403 Forbidden.
        patient_type must never bypass district authorization.
        """
        self.client.force_authenticate(user=self.officer_c)
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?district={self.district_rural.id}&disease=Dengue&patient_type=NEW")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 33. No patient_type filter preserves existing behavior
    def test_33_no_patient_type_filter_preserves_behavior(self):
        """
        When patient_type filter is omitted, all 9 Dengue cases at fac_c1 are returned.
        All existing response fields from Prompts 1-5 remain intact.
        """
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_cases_in_history'], 9)

        required_fields = [
            'total_cases_in_history', 'monthly_series', 'historical_series',
            'severity_breakdown', 'historical_age_groups', 'historical_gender',
            'age_gender_matrix', 'historical_severity', 'historical_vulnerable_groups',
            'historical_patient_type', 'monthly_patient_type_trends',
            'patient_type_age_groups', 'patient_type_gender', 'patient_type_severity',
            'patient_type_vulnerable_groups',
        ]
        for f in required_fields:
            self.assertIn(f, res.data, f"Field '{f}' missing from backward compatible response.")

    # 34. Patient type filter is never silently ignored
    def test_34_patient_type_filter_never_silently_ignored(self):
        """
        Verifies that applying patient_type=FOLLOW_UP produces 3 cases, which differs from
        the unfiltered total of 9 cases. The filter is never silently ignored.
        """
        url = reverse('intelligence_historical_disease')
        res_all = self.client.get(f"{url}?disease=Dengue&date={self.as_of}&months=6")
        res_fu = self.client.get(f"{url}?disease=Dengue&patient_type=FOLLOW_UP&date={self.as_of}&months=6")

        self.assertEqual(res_all.status_code, status.HTTP_200_OK)
        self.assertEqual(res_fu.status_code, status.HTTP_200_OK)
        self.assertNotEqual(res_all.data['total_cases_in_history'], res_fu.data['total_cases_in_history'])
        self.assertEqual(res_fu.data['total_cases_in_history'], 3)

    # 35. Missing/insufficient history produces UNKNOWN
    def test_35_missing_insufficient_history_produces_unknown(self):
        """
        When historical information is insufficient (e.g. missing patient or report_date):
        - get_case_patient_type returns UNKNOWN.
        - normalize_patient_type maps unknown values to UNKNOWN.
        - UNKNOWN is never silently converted into NEW or FOLLOW_UP.
        - UNKNOWN appears dynamically in output when unknown cases exist.
        """
        # Standalone tests of service classification
        self.assertEqual(get_case_patient_type(None), PATIENT_TYPE_UNKNOWN)
        dummy_case = DiseaseCase(patient=None, report_date=None)
        self.assertEqual(get_case_patient_type(dummy_case), PATIENT_TYPE_UNKNOWN)
        dummy_case_no_pt = DiseaseCase(patient=None, report_date=datetime.date(2026, 5, 1))
        self.assertEqual(get_case_patient_type(dummy_case_no_pt), PATIENT_TYPE_UNKNOWN)
        dummy_case_no_date = DiseaseCase(patient=self.p_male_adult, report_date=None)
        self.assertEqual(get_case_patient_type(dummy_case_no_date), PATIENT_TYPE_UNKNOWN)

        # Normalization
        self.assertEqual(normalize_patient_type(''), PATIENT_TYPE_UNKNOWN)
        self.assertEqual(normalize_patient_type('UNKNOWN'), PATIENT_TYPE_UNKNOWN)
        self.assertEqual(normalize_patient_type('OTHER_RANDOM'), PATIENT_TYPE_UNKNOWN)

        # UNKNOWN cannot be filtered
        url = reverse('intelligence_historical_disease')
        res = self.client.get(f"{url}?patient_type=UNKNOWN")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        with self.assertNumQueries(1):
            aggregate_historical_disease(
                facility_ids=[self.fac_c1.id],
                disease_name='Dengue',
                months=6,
                as_of_date=self.as_of
            )


class PublicHealthSeasonalityDemographicsTestCase(TestCase):
    """
    Prompt 7: Seasonality + Demographics Integration & Unit Test Suite
    Comprehensive validation of multi-dimensional seasonal pattern intelligence:
    1. Existing seasonality behavior preserved.
    2. Seasonal age groups.
    3. Seasonal gender.
    4. Seasonal severity.
    5. Seasonal vulnerable population.
    6. Seasonal patient type.
    7. Age + gender seasonality.
    8. Age + gender + severity.
    9. Age + gender + vulnerability.
    10. Age + gender + patient type.
    11. Disease + demographic filtering.
    12. Disease + severity filtering.
    13. Disease + vulnerability filtering.
    14. Disease + patient type filtering.
    15. Combined all filters.
    16. Invalid age_group -> 400.
    17. Invalid gender -> 400.
    18. Invalid severity -> 400.
    19. Invalid vulnerable_group -> 400.
    20. Invalid patient_type -> 400.
    21. UNKNOWN filters rejected.
    22. Hospital Admin cross-facility -> 403.
    23. District Officer cross-district -> 403.
    24. Missing DOB handled as UNKNOWN.
    25. Missing/invalid severity handled as UNKNOWN.
    26. Missing/invalid vulnerability handled as UNKNOWN.
    27. Missing/insufficient patient history handled as UNKNOWN.
    28. Age uses DiseaseCase.report_date.
    29. Future patient cases do not affect earlier patient type.
    30. Monthly totals reconcile.
    31. Cross-tab totals reconcile.
    32. No demographic filters preserve previous behavior.
    33. Filters are never silently ignored.
    34. No N+1 query regression.
    """

    @classmethod
    def setUpTestData(cls):
        # Geography
        cls.state = State.objects.create(name='Karnataka', code='KA')
        cls.district_central = District.objects.create(state=cls.state, name='BBMP Central', code='KA-CEN')
        cls.district_rural = District.objects.create(state=cls.state, name='Bengaluru Rural', code='KA-RUR')

        cls.zone_central = Zone.objects.create(district=cls.district_central, name='Central Zone', code='Z-CEN')
        cls.zone_rural = Zone.objects.create(district=cls.district_rural, name='Rural Zone', code='Z-RUR')

        cls.ward_c1 = Ward.objects.create(zone=cls.zone_central, ward_number=101, name='Indiranagar', population=25000)
        cls.ward_r1 = Ward.objects.create(zone=cls.zone_rural, ward_number=201, name='Varthur', population=18000)

        # Facilities
        cls.fac_c1 = Facility.objects.create(
            facility_code='HOSP-SEAS1', facility_name='Bowring Hospital', facility_type='MAIN_HOSPITAL',
            district=cls.district_central, ward=cls.ward_c1, state=cls.state
        )
        cls.fac_c2 = Facility.objects.create(
            facility_code='CLINIC-SEAS2', facility_name='Indiranagar Clinic', facility_type='NAMMA_CLINIC',
            district=cls.district_central, ward=cls.ward_c1, state=cls.state
        )
        cls.fac_r1 = Facility.objects.create(
            facility_code='RURAL-SEAS1', facility_name='Varthur Rural CHC', facility_type='RURAL_CLINIC',
            district=cls.district_rural, ward=cls.ward_r1, state=cls.state
        )

        # Users
        cls.admin_c1 = User.objects.create_user(
            username='seas_admin_c1', password='Password123!', role='HOSPITAL_ADMIN',
            assigned_facility=cls.fac_c1
        )
        cls.officer_c = User.objects.create_user(
            username='seas_officer_c', password='Password123!', role='DISTRICT_OFFICER',
            assigned_district=cls.district_central
        )
        cls.officer_r = User.objects.create_user(
            username='seas_officer_r', password='Password123!', role='DISTRICT_OFFICER',
            assigned_district=cls.district_rural
        )

        # Reference date: 2026-12-15 (12-month window: 2026-01-01 to 2026-12-15)
        cls.as_of = datetime.date(2026, 12, 15)

        # Deterministic Patients
        # 1. Infant (0-5)
        cls.p_child = Patient.objects.create(
            patient_id='SEAS-P01', name='Infant Child Girl',
            date_of_birth=datetime.date(2024, 3, 1), age=2, gender='FEMALE',
            vulnerability_information='Slum Resident / Low Income Group',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # 2. Youth (6-14, OTHER gender, Disability)
        cls.p_youth = Patient.objects.create(
            patient_id='SEAS-P02', name='Youth PwD Other',
            date_of_birth=datetime.date(2016, 3, 1), age=10, gender='OTHER',
            vulnerability_information='Person with Disability (PwD)',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # 3. Young Adult (15-24, FEMALE, Pregnant)
        cls.p_young_adult = Patient.objects.create(
            patient_id='SEAS-P03', name='Young Adult Pregnant Female',
            date_of_birth=datetime.date(2006, 3, 1), age=20, gender='FEMALE',
            vulnerability_information='Pregnant Woman',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # 4. Adult (25-44, MALE, Low Income Slum)
        cls.p_adult = Patient.objects.create(
            patient_id='SEAS-P04', name='Adult Male Patient',
            date_of_birth=datetime.date(1996, 3, 1), age=30, gender='MALE',
            vulnerability_information='Slum Resident / Low Income Group',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # 5. Middle-aged (45-59, FEMALE, Chronic Condition)
        cls.p_middle = Patient.objects.create(
            patient_id='SEAS-P05', name='Middle Aged Female Chronic',
            date_of_birth=datetime.date(1976, 3, 1), age=50, gender='FEMALE',
            vulnerability_information='Hypertension / Diabetic comorbidity',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # 6. Senior (60+, MALE, Elderly)
        cls.p_elderly = Patient.objects.create(
            patient_id='SEAS-P06', name='Elderly Senior Male',
            date_of_birth=datetime.date(1956, 3, 1), age=70, gender='MALE',
            vulnerability_information='Elderly Person',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # 7. General Population Adult (25-44, MALE, General)
        cls.p_general = Patient.objects.create(
            patient_id='SEAS-P07', name='General Citizen Male',
            date_of_birth=datetime.date(1990, 3, 1), age=36, gender='MALE',
            vulnerability_information='GENERAL',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # 8. Age boundary patient: DOB 2020-06-15.
        # At report_date 2026-05-15 -> age 5 (0-5).
        # At report_date 2026-07-15 -> age 6 (6-14).
        cls.p_boundary = Patient.objects.create(
            patient_id='SEAS-P08', name='Age Boundary Boy',
            date_of_birth=datetime.date(2020, 6, 15), age=6, gender='MALE',
            vulnerability_information='GENERAL',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # 9. Patient with missing DOB, missing gender, missing vulnerability
        cls.p_unknown_demo = Patient.objects.create(
            patient_id='SEAS-P09', name='Unknown Demographics Patient',
            date_of_birth=None, age=30, gender='',
            vulnerability_information='',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # 10. Rural Patient
        cls.p_rural = Patient.objects.create(
            patient_id='SEAS-P10', name='Rural Female Patient',
            date_of_birth=datetime.date(1995, 1, 1), age=31, gender='FEMALE',
            vulnerability_information='Slum Resident / Low Income Group',
            district=cls.district_rural, ward=cls.ward_r1, registered_at_facility=cls.fac_r1
        )

        # -------------------------------------------------------------------
        # Deterministic Disease Cases for Dengue at fac_c1 (Total: 14 cases)
        # -------------------------------------------------------------------
        # 1. Month 1 (Jan 10): p_adult (Male, 25-44, MILD, LOW_INCOME_SLUM) -> NEW
        cls.c1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_adult, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 1, 10), severity='MILD'
        )
        # 2. Month 2 (Feb 10): p_young_adult (Female, 15-24, SEVERE, PREGNANT) -> NEW
        cls.c2 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_young_adult, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 2, 10), severity='SEVERE'
        )
        # 3. Month 3 (Mar 10): p_child (Female, 0-5, MILD, LOW_INCOME_SLUM) -> NEW
        cls.c3 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_child, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 3, 10), severity='MILD'
        )
        # 4. Month 4 (Apr 10): p_youth (Other, 6-14, MODERATE, DISABILITY) -> NEW
        cls.c4 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_youth, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 4, 10), severity='MODERATE'
        )
        # 5. Month 5 (May 10): p_middle (Female, 45-59, MILD, CHRONIC_CONDITION) -> NEW
        cls.c5 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_middle, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 5, 10), severity='MILD'
        )
        # 6. Month 5 (May 15): p_boundary (Male, DOB 2020-06-15 -> Age 5 -> '0-5', MILD, GENERAL) -> NEW
        cls.c6 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_boundary, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 5, 15), severity='MILD'
        )
        # 7. Month 6 (Jun 10): p_elderly (Male, 60+, SEVERE, ELDERLY) -> NEW
        cls.c7 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_elderly, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 6, 10), severity='SEVERE'
        )
        # 8. Month 7 (Jul 10): p_adult (Male, 25-44, SEVERE, LOW_INCOME_SLUM) -> FOLLOW_UP (earlier case on Jan 10)
        cls.c8 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_adult, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 7, 10), severity='SEVERE'
        )
        # 9. Month 7 (Jul 15): p_boundary (Male, DOB 2020-06-15 -> Age 6 -> '6-14', MODERATE, GENERAL) -> FOLLOW_UP (earlier on May 15)
        cls.c9 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_boundary, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 7, 15), severity='MODERATE'
        )
        # 10. Month 8 (Aug 10): p_young_adult (Female, 15-24, SEVERE, PREGNANT) -> FOLLOW_UP (earlier on Feb 10)
        cls.c10 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_young_adult, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 8, 10), severity='SEVERE'
        )
        # 11. Month 9 (Sep 10): p_general (Male, 25-44, MODERATE, GENERAL) -> NEW
        cls.c11 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_general, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 9, 10), severity='MODERATE'
        )
        # 12. Month 10 (Oct 10): p_unknown_demo (UNKNOWN age, UNKNOWN gender, UNKNOWN vuln, invalid severity -> UNKNOWN) -> NEW
        cls.c12 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_unknown_demo, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 10, 10), severity='INVALID_VAL'
        )
        # 13. Month 11 (Nov 10): p_elderly (Male, 60+, SEVERE, ELDERLY) -> FOLLOW_UP (earlier on Jun 10)
        cls.c13 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_elderly, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 11, 10), severity='SEVERE'
        )
        # 14. Month 11 (Nov 15): p_adult (severity='INVALID_SEV' -> UNKNOWN severity, FOLLOW_UP)
        cls.c14 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_adult, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 11, 15), severity='INVALID_SEV'
        )

        # Other disease / other facility cases for discrimination testing
        # Malaria at fac_c1
        cls.c_malaria = DiseaseCase.objects.create(
            disease_name='Malaria', patient=cls.p_adult, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 6, 10), severity='MILD'
        )
        # Dengue at rural fac_r1
        cls.c_rural = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_rural, facility=cls.fac_r1,
            ward=cls.ward_r1, report_date=datetime.date(2026, 6, 10), severity='MILD'
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_c1)
        self.url = reverse('intelligence_seasonality')

    # 1. Existing seasonality behavior preserved
    def test_01_existing_seasonality_behavior_preserved(self):
        """
        Preserves all core seasonality fields:
        monthly case distribution, highest/lowest case month, strongest historical periods,
        seasonal strength, seasonal_status, total_cases_analyzed, months_analyzed, explanation.
        """
        res = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data

        expected_keys = [
            'disease', 'seasonal_status', 'seasonal_strength', 'total_cases_analyzed',
            'months_analyzed', 'highest_case_month', 'lowest_case_month',
            'strongest_historical_periods', 'monthly_patterns', 'explanation',
            'seasonal_age_groups', 'seasonal_gender', 'seasonal_severity',
            'seasonal_vulnerable_groups', 'seasonal_patient_types',
            'seasonal_age_gender', 'seasonal_age_gender_severity',
            'seasonal_age_gender_vulnerability', 'seasonal_age_gender_patient_type'
        ]
        for k in expected_keys:
            self.assertIn(k, data, f"Missing key in seasonality response: {k}")

        self.assertEqual(data['total_cases_analyzed'], 14)
        self.assertEqual(data['months_analyzed'], 12)
        self.assertEqual(len(data['monthly_patterns']), 12)
        self.assertIn(data['seasonal_status'], ['DETECTED', 'WEAK', 'NOT_ENOUGH_DATA'])
        self.assertIsNotNone(data['highest_case_month'])
        self.assertIsNotNone(data['lowest_case_month'])

    # 2. Seasonal age groups
    def test_02_seasonal_age_groups(self):
        """
        Validates seasonal analysis by authoritative age groups (0-5, 6-14, 15-24, 25-44, 45-59, 60+, UNKNOWN).
        Each group contains monthly_patterns, total_cases, peak_month, seasonal_strength, seasonal_status.
        """
        res = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ag_list = res.data['seasonal_age_groups']
        self.assertIsInstance(ag_list, list)

        ag_map = {item['age_group']: item for item in ag_list}
        for expected_ag in ['0-5', '6-14', '15-24', '25-44', '45-59', '60+', 'UNKNOWN']:
            self.assertIn(expected_ag, ag_map)
            item = ag_map[expected_ag]
            self.assertIn('monthly_patterns', item)
            self.assertIn('total_cases', item)
            self.assertIn('peak_month', item)
            self.assertIn('seasonal_strength', item)
            self.assertIn('seasonal_status', item)

        # Sum of age groups matches total cases
        total_ag_cases = sum(item['total_cases'] for item in ag_list)
        self.assertEqual(total_ag_cases, 14)

    # 3. Seasonal gender
    def test_03_seasonal_gender(self):
        """
        Validates seasonal gender breakdown: MALE, FEMALE, OTHER, and dynamically included UNKNOWN.
        """
        res = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        g_list = res.data['seasonal_gender']
        self.assertIsInstance(g_list, list)

        g_map = {item['gender']: item for item in g_list}
        for g in ['MALE', 'FEMALE', 'OTHER', 'UNKNOWN']:
            self.assertIn(g, g_map)
            item = g_map[g]
            self.assertIn('monthly_patterns', item)
            self.assertIn('total_cases', item)
            self.assertIn('peak_month', item)
            self.assertIn('seasonal_strength', item)
            self.assertIn('seasonal_status', item)

        total_g_cases = sum(item['total_cases'] for item in g_list)
        self.assertEqual(total_g_cases, 14)

    # 4. Seasonal severity
    def test_04_seasonal_severity(self):
        """
        Validates seasonal severity breakdown: MILD, MODERATE, SEVERE, and UNKNOWN.
        """
        res = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        sev_list = res.data['seasonal_severity']
        self.assertIsInstance(sev_list, list)

        sev_map = {item['severity']: item for item in sev_list}
        for s in ['MILD', 'MODERATE', 'SEVERE', 'UNKNOWN']:
            self.assertIn(s, sev_map)
            item = sev_map[s]
            self.assertIn('monthly_patterns', item)
            self.assertIn('total_cases', item)
            self.assertIn('peak_month', item)
            self.assertIn('seasonal_strength', item)
            self.assertIn('seasonal_status', item)

        total_s_cases = sum(item['total_cases'] for item in sev_list)
        self.assertEqual(total_s_cases, 14)

    # 5. Seasonal vulnerable population
    def test_05_seasonal_vulnerable_population(self):
        """
        Validates seasonal analysis by canonical vulnerability groups:
        PREGNANT, ELDERLY, DISABILITY, CHRONIC_CONDITION, LOW_INCOME_SLUM, GENERAL, and UNKNOWN.
        """
        res = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        vg_list = res.data['seasonal_vulnerable_groups']
        self.assertIsInstance(vg_list, list)

        vg_map = {item['vulnerable_group']: item for item in vg_list}
        for vg in ['PREGNANT', 'ELDERLY', 'DISABILITY', 'CHRONIC_CONDITION', 'LOW_INCOME_SLUM', 'GENERAL', 'UNKNOWN']:
            self.assertIn(vg, vg_map)
            item = vg_map[vg]
            self.assertIn('monthly_patterns', item)
            self.assertIn('total_cases', item)
            self.assertIn('peak_month', item)
            self.assertIn('seasonal_strength', item)
            self.assertIn('seasonal_status', item)

        total_vg_cases = sum(item['total_cases'] for item in vg_list)
        self.assertEqual(total_vg_cases, 14)

    # 6. Seasonal patient type
    def test_06_seasonal_patient_type(self):
        """
        Validates seasonal patient-type analysis: NEW, FOLLOW_UP, and UNKNOWN when present.
        """
        res = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        pt_list = res.data['seasonal_patient_types']
        self.assertIsInstance(pt_list, list)

        pt_map = {item['patient_type']: item for item in pt_list}
        for pt in ['NEW', 'FOLLOW_UP']:
            self.assertIn(pt, pt_map)
            item = pt_map[pt]
            self.assertIn('monthly_patterns', item)
            self.assertIn('total_cases', item)
            self.assertIn('peak_month', item)
            self.assertIn('seasonal_strength', item)
            self.assertIn('seasonal_status', item)

        total_pt_cases = sum(item['total_cases'] for item in pt_list)
        self.assertEqual(total_pt_cases, 14)

    # 7. Age + gender seasonal matrix
    def test_07_age_gender_seasonality(self):
        """
        Validates multi-dimensional age + gender seasonality cross-tabulation:
        seasonal_age_gender[age_group][gender] = { monthly_patterns, total_cases }.
        """
        res = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        matrix = res.data['seasonal_age_gender']
        self.assertIsInstance(matrix, dict)

        tot = 0
        for ag, genders in matrix.items():
            for g, cell in genders.items():
                self.assertIn('monthly_patterns', cell)
                self.assertIn('total_cases', cell)
                tot += cell['total_cases']
        self.assertEqual(tot, 14)

    # 8. Age + gender + severity
    def test_08_age_gender_severity(self):
        """
        Validates age + gender + severity 3D seasonality matrix:
        seasonal_age_gender_severity[ag][g][sev] = { monthly_patterns, total_cases }.
        """
        res = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        matrix = res.data['seasonal_age_gender_severity']
        self.assertIsInstance(matrix, dict)

        tot = 0
        for ag, genders in matrix.items():
            for g, severities in genders.items():
                for s, cell in severities.items():
                    self.assertIn('monthly_patterns', cell)
                    self.assertIn('total_cases', cell)
                    tot += cell['total_cases']
        self.assertEqual(tot, 14)

    # 9. Age + gender + vulnerability
    def test_09_age_gender_vulnerability(self):
        """
        Validates age + gender + vulnerability 3D seasonality matrix:
        seasonal_age_gender_vulnerability[ag][g][vg] = { monthly_patterns, total_cases }.
        """
        res = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        matrix = res.data['seasonal_age_gender_vulnerability']
        self.assertIsInstance(matrix, dict)

        tot = 0
        for ag, genders in matrix.items():
            for g, vgroups in genders.items():
                for vg, cell in vgroups.items():
                    self.assertIn('monthly_patterns', cell)
                    self.assertIn('total_cases', cell)
                    tot += cell['total_cases']
        self.assertEqual(tot, 14)

    # 10. Age + gender + patient type
    def test_10_age_gender_patient_type(self):
        """
        Validates age + gender + patient-type 3D seasonality matrix:
        seasonal_age_gender_patient_type[ag][g][pt] = { monthly_patterns, total_cases }.
        """
        res = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        matrix = res.data['seasonal_age_gender_patient_type']
        self.assertIsInstance(matrix, dict)

        tot = 0
        for ag, genders in matrix.items():
            for g, ptypes in genders.items():
                for pt, cell in ptypes.items():
                    self.assertIn('monthly_patterns', cell)
                    self.assertIn('total_cases', cell)
                    tot += cell['total_cases']
        self.assertEqual(tot, 14)

    # 11. Disease + demographic filtering
    def test_11_disease_and_demographic_filtering(self):
        """
        Verifies filtering by disease, age_group, and gender concurrently:
        ?disease=Dengue&age_group=15-24&gender=FEMALE produces exact match (2 cases for P3).
        """
        url = f"{self.url}?disease=Dengue&age_group=15-24&gender=FEMALE&date={self.as_of}&months=12"
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_cases_analyzed'], 2)

    # 12. Disease + severity filtering
    def test_12_disease_and_severity_filtering(self):
        """
        Verifies filtering by disease and severity:
        ?disease=Dengue&severity=SEVERE produces exact 5 cases.
        """
        url = f"{self.url}?disease=Dengue&severity=SEVERE&date={self.as_of}&months=12"
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_cases_analyzed'], 5)

    # 13. Disease + vulnerability filtering
    def test_13_disease_and_vulnerability_filtering(self):
        """
        Verifies filtering by disease and vulnerability group:
        ?disease=Dengue&vulnerable_group=PREGNANT produces exact 2 cases.
        """
        url = f"{self.url}?disease=Dengue&vulnerable_group=PREGNANT&date={self.as_of}&months=12"
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_cases_analyzed'], 2)

    # 14. Disease + patient type filtering
    def test_14_disease_and_patient_type_filtering(self):
        """
        Verifies filtering by disease and patient type:
        ?disease=Dengue&patient_type=FOLLOW_UP produces exact 5 cases.
        """
        url = f"{self.url}?disease=Dengue&patient_type=FOLLOW_UP&date={self.as_of}&months=12"
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_cases_analyzed'], 5)

    # 15. Combined all filters
    def test_15_combined_all_filters(self):
        """
        Verifies all filters applied simultaneously as strict AND conditions:
        ?disease=Dengue&age_group=15-24&gender=FEMALE&severity=SEVERE&vulnerable_group=PREGNANT&patient_type=FOLLOW_UP
        produces exact 1 case (c10 in August).
        """
        url = (
            f"{self.url}?disease=Dengue&age_group=15-24&gender=FEMALE&severity=SEVERE"
            f"&vulnerable_group=PREGNANT&patient_type=FOLLOW_UP&date={self.as_of}&months=12"
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_cases_analyzed'], 1)

    # 16. Invalid age_group -> 400
    def test_16_invalid_age_group_returns_400(self):
        res = self.client.get(f"{self.url}?disease=Dengue&age_group=99-100")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # 17. Invalid gender -> 400
    def test_17_invalid_gender_returns_400(self):
        res = self.client.get(f"{self.url}?disease=Dengue&gender=NONBINARY_ALIEN")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # 18. Invalid severity -> 400
    def test_18_invalid_severity_returns_400(self):
        res = self.client.get(f"{self.url}?disease=Dengue&severity=EXTREME")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # 19. Invalid vulnerable_group -> 400
    def test_19_invalid_vulnerable_group_returns_400(self):
        res = self.client.get(f"{self.url}?disease=Dengue&vulnerable_group=ASTRONAUT")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # 20. Invalid patient_type -> 400
    def test_20_invalid_patient_type_returns_400(self):
        res = self.client.get(f"{self.url}?disease=Dengue&patient_type=RECURRENT")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # 21. UNKNOWN filters rejected
    def test_21_unknown_filters_rejected(self):
        """
        UNKNOWN is an internal reporting classification and must not be accepted as a query filter.
        """
        for param, val in [
            ('age_group', 'UNKNOWN'),
            ('gender', 'UNKNOWN'),
            ('severity', 'UNKNOWN'),
            ('vulnerable_group', 'UNKNOWN'),
            ('patient_type', 'UNKNOWN')
        ]:
            res = self.client.get(f"{self.url}?disease=Dengue&{param}={val}")
            self.assertEqual(
                res.status_code, status.HTTP_400_BAD_REQUEST,
                f"Expected 400 for {param}={val}, got {res.status_code}"
            )

    # 22. Hospital Admin cross-facility -> 403
    def test_22_hospital_admin_cross_facility_returns_403(self):
        """Hospital Admin cannot request a facility outside their assignment."""
        res = self.client.get(f"{self.url}?disease=Dengue&facility={self.fac_r1.id}")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 23. District Officer cross-district -> 403
    def test_23_district_officer_cross_district_returns_403(self):
        """District Officer cannot request a district outside their assignment."""
        self.client.force_authenticate(user=self.officer_c)
        res = self.client.get(f"{self.url}?disease=Dengue&district={self.district_rural.id}")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 24. Missing DOB handled as UNKNOWN
    def test_24_missing_dob_handled_as_unknown(self):
        """
        Cases with missing DOB are classified into age_group='UNKNOWN'.
        When filtering by age_group=15-24 where no unknown cases exist, UNKNOWN is not present.
        """
        res = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ag_map = {item['age_group']: item for item in res.data['seasonal_age_groups']}
        self.assertIn('UNKNOWN', ag_map)
        self.assertEqual(ag_map['UNKNOWN']['total_cases'], 1)  # c12 (p_unknown_demo)

        # When filtered to 15-24, no UNKNOWN cases exist -> UNKNOWN not present
        res_filtered = self.client.get(f"{self.url}?disease=Dengue&age_group=15-24&date={self.as_of}&months=12")
        filtered_ags = [item['age_group'] for item in res_filtered.data['seasonal_age_groups']]
        self.assertNotIn('UNKNOWN', filtered_ags)

    # 25. Missing/invalid severity handled as UNKNOWN
    def test_25_missing_invalid_severity_handled_as_unknown(self):
        """
        Invalid or missing severity values are categorized as severity='UNKNOWN', not converted to MILD.
        """
        res = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        sev_map = {item['severity']: item for item in res.data['seasonal_severity']}
        self.assertIn('UNKNOWN', sev_map)
        self.assertEqual(sev_map['UNKNOWN']['total_cases'], 2)  # c12 ('INVALID_VAL') and c14 ('INVALID_SEV')

    # 26. Missing/invalid vulnerability handled as UNKNOWN
    def test_26_missing_invalid_vulnerability_handled_as_unknown(self):
        """
        Missing vulnerability information is categorized into vulnerable_group='UNKNOWN'.
        """
        res = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        vg_map = {item['vulnerable_group']: item for item in res.data['seasonal_vulnerable_groups']}
        self.assertIn('UNKNOWN', vg_map)
        self.assertEqual(vg_map['UNKNOWN']['total_cases'], 1)  # c12 (empty string)

    # 27. Missing/insufficient patient history handled as UNKNOWN
    def test_27_missing_insufficient_patient_history_handled_as_unknown(self):
        """
        When patient history is missing or insufficient (e.g. missing patient or report_date):
        - get_case_patient_type returns UNKNOWN.
        - normalize_patient_type returns UNKNOWN.
        - UNKNOWN is not silently converted into NEW or FOLLOW_UP.
        """
        self.assertEqual(get_case_patient_type(None), PATIENT_TYPE_UNKNOWN)
        dummy_case = DiseaseCase(patient=None, report_date=None)
        self.assertEqual(get_case_patient_type(dummy_case), PATIENT_TYPE_UNKNOWN)
        dummy_case_no_pt = DiseaseCase(patient=None, report_date=datetime.date(2026, 5, 1))
        self.assertEqual(get_case_patient_type(dummy_case_no_pt), PATIENT_TYPE_UNKNOWN)
        dummy_case_no_date = DiseaseCase(patient=self.p_adult, report_date=None)
        self.assertEqual(get_case_patient_type(dummy_case_no_date), PATIENT_TYPE_UNKNOWN)

        self.assertEqual(normalize_patient_type(''), PATIENT_TYPE_UNKNOWN)
        self.assertEqual(normalize_patient_type('UNKNOWN'), PATIENT_TYPE_UNKNOWN)
        self.assertEqual(normalize_patient_type('OTHER_RANDOM'), PATIENT_TYPE_UNKNOWN)

    # 28. Age uses DiseaseCase.report_date
    def test_28_age_uses_disease_case_report_date(self):
        """
        Verifies that patient age is calculated using DiseaseCase.report_date rather than today's date.
        p_boundary (DOB 2020-06-15):
        - Case c6 on 2026-05-15 has age 5 -> '0-5'
        - Case c9 on 2026-07-15 has age 6 -> '6-14'
        """
        res = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ag_map = {item['age_group']: item for item in res.data['seasonal_age_groups']}

        # Month 5 has c6 in '0-5'
        m5_in_0_5 = next(p for p in ag_map['0-5']['monthly_patterns'] if p['month_number'] == 5)
        self.assertGreaterEqual(m5_in_0_5['total_cases'], 1)

        # Month 7 has c9 in '6-14'
        m7_in_6_14 = next(p for p in ag_map['6-14']['monthly_patterns'] if p['month_number'] == 7)
        self.assertGreaterEqual(m7_in_6_14['total_cases'], 1)

    # 29. Future patient cases do not affect earlier patient type
    def test_29_future_patient_cases_do_not_affect_earlier_patient_type(self):
        """
        Point-in-time correctness: Case c1 on 2026-01-10 is NEW because no earlier case exists.
        Subsequent case c8 on 2026-07-10 is FOLLOW_UP.
        The existence of future case c8 does not change c1 from NEW to FOLLOW_UP.
        """
        pt_c1 = get_case_patient_type(self.c1)
        pt_c8 = get_case_patient_type(self.c8)
        self.assertEqual(pt_c1, PATIENT_TYPE_NEW)
        self.assertEqual(pt_c8, PATIENT_TYPE_FOLLOW_UP)

    # 30. Monthly totals reconcile
    def test_30_monthly_totals_reconcile(self):
        """
        For every represented month:
        sum(subgroup category totals for that month) == monthly total cases for that month.
        Applies across age groups, gender, severity, vulnerable groups, and patient types.
        """
        res = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data

        patterns = data['monthly_patterns']
        ag_list = data['seasonal_age_groups']
        g_list = data['seasonal_gender']
        sev_list = data['seasonal_severity']
        vg_list = data['seasonal_vulnerable_groups']
        pt_list = data['seasonal_patient_types']

        for idx, m_pat in enumerate(patterns):
            m_total = m_pat['total_cases']
            m_num = m_pat['month_number']

            ag_sum = sum(item['monthly_patterns'][idx]['total_cases'] for item in ag_list)
            g_sum = sum(item['monthly_patterns'][idx]['total_cases'] for item in g_list)
            sev_sum = sum(item['monthly_patterns'][idx]['total_cases'] for item in sev_list)
            vg_sum = sum(item['monthly_patterns'][idx]['total_cases'] for item in vg_list)
            pt_sum = sum(item['monthly_patterns'][idx]['total_cases'] for item in pt_list)

            self.assertEqual(ag_sum, m_total, f"Month {m_num}: age sum {ag_sum} != {m_total}")
            self.assertEqual(g_sum, m_total, f"Month {m_num}: gender sum {g_sum} != {m_total}")
            self.assertEqual(sev_sum, m_total, f"Month {m_num}: severity sum {sev_sum} != {m_total}")
            self.assertEqual(vg_sum, m_total, f"Month {m_num}: vulnerability sum {vg_sum} != {m_total}")
            self.assertEqual(pt_sum, m_total, f"Month {m_num}: patient type sum {pt_sum} != {m_total}")

    # 31. Cross-tab totals reconcile
    def test_31_cross_tab_totals_reconcile(self):
        """
        Across the observation period:
        sum(category totals) == total_cases_analyzed for all 1D and multi-dimensional matrices.
        """
        res = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data
        total_cases = data['total_cases_analyzed']

        self.assertEqual(sum(item['total_cases'] for item in data['seasonal_age_groups']), total_cases)
        self.assertEqual(sum(item['total_cases'] for item in data['seasonal_gender']), total_cases)
        self.assertEqual(sum(item['total_cases'] for item in data['seasonal_severity']), total_cases)
        self.assertEqual(sum(item['total_cases'] for item in data['seasonal_vulnerable_groups']), total_cases)
        self.assertEqual(sum(item['total_cases'] for item in data['seasonal_patient_types']), total_cases)

        # 2D Matrix: Age + Gender
        ag_g_tot = sum(
            cell['total_cases']
            for ag in data['seasonal_age_gender'].values()
            for cell in ag.values()
        )
        self.assertEqual(ag_g_tot, total_cases)

        # 3D Matrix: Age + Gender + Severity
        ag_g_sev_tot = sum(
            cell['total_cases']
            for ag in data['seasonal_age_gender_severity'].values()
            for g in ag.values()
            for cell in g.values()
        )
        self.assertEqual(ag_g_sev_tot, total_cases)

        # 3D Matrix: Age + Gender + Vulnerability
        ag_g_vg_tot = sum(
            cell['total_cases']
            for ag in data['seasonal_age_gender_vulnerability'].values()
            for g in ag.values()
            for cell in g.values()
        )
        self.assertEqual(ag_g_vg_tot, total_cases)

        # 3D Matrix: Age + Gender + Patient Type
        ag_g_pt_tot = sum(
            cell['total_cases']
            for ag in data['seasonal_age_gender_patient_type'].values()
            for g in ag.values()
            for cell in g.values()
        )
        self.assertEqual(ag_g_pt_tot, total_cases)

    # 32. No demographic filters preserve previous behavior
    def test_32_no_demographic_filters_preserve_previous_behavior(self):
        """
        Requesting seasonality without demographic parameters analyzes the full unfiltered cohort.
        """
        res = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_cases_analyzed'], 14)

    # 33. Filters are never silently ignored
    def test_33_filters_are_never_silently_ignored(self):
        """
        Applying a filter produces a strict subset of the population and matches the filter condition.
        """
        res_all = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        res_mild = self.client.get(f"{self.url}?disease=Dengue&severity=MILD&date={self.as_of}&months=12")

        self.assertEqual(res_all.status_code, status.HTTP_200_OK)
        self.assertEqual(res_mild.status_code, status.HTTP_200_OK)
        self.assertNotEqual(res_all.data['total_cases_analyzed'], res_mild.data['total_cases_analyzed'])
        self.assertEqual(res_mild.data['total_cases_analyzed'], 4)

    # 34. No N+1 query regression
    def test_34_no_n_plus_one_query_regression(self):
        """
        Seasonality calculation evaluates in strictly 1 query via select_related('patient')
        and annotate_case_patient_type, avoiding any N+1 loops.
        """
        with self.assertNumQueries(1):
            calculate_seasonal_pattern(
                facility_ids=[self.fac_c1.id],
                disease_name='Dengue',
                months_count=12,
                as_of_date=self.as_of
            )


class PublicHealthDemographicForecastTestCase(TestCase):
    """
    Prompt 8: Demographic Forecasting Integration & Unit Test Suite
    Comprehensive validation of multi-dimensional epidemiological forecasting:
    1. Existing forecast behavior without demographic filters.
    2. Forecast filtered by age group.
    3. Forecast filtered by gender.
    4. Forecast filtered by severity.
    5. Forecast filtered by vulnerable group.
    6. Forecast filtered by patient type.
    7. Disease + age group.
    8. Disease + gender.
    9. Disease + severity.
    10. Disease + vulnerable group.
    11. Disease + patient type.
    12. Age + gender combination.
    13. Age + gender + severity.
    14. Age + gender + vulnerable group.
    15. Age + gender + patient type.
    16. Full demographic combination.
    17. Invalid age_group returns HTTP 400.
    18. Invalid gender returns HTTP 400.
    19. Invalid severity returns HTTP 400.
    20. Invalid vulnerable_group returns HTTP 400.
    21. Invalid patient_type returns HTTP 400.
    22. UNKNOWN public filters follow existing validation behavior.
    23. Hospital Admin cannot forecast another facility.
    24. District Officer cannot forecast another district.
    25. District Officer can forecast an allowed facility within their district.
    26. Missing DOB is classified as UNKNOWN.
    27. Invalid severity becomes UNKNOWN rather than another severity.
    28. Invalid vulnerability becomes UNKNOWN.
    29. Missing/insufficient patient history produces UNKNOWN patient type.
    30. Patient age is calculated using DiseaseCase.report_date.
    31. Patient type is calculated using history available up to DiseaseCase.report_date.
    32. Later patient records do not alter earlier patient-type classification.
    33. Insufficient demographic subgroup history returns NOT_ENOUGH_DATA / INSUFFICIENT_DATA.
    34. Insufficient subgroup does NOT fall back to overall disease forecast.
    35. Historical actual values remain separate from forecast values.
    36. Zero-case weeks are handled consistently.
    37. Demographic filters are never silently ignored.
    38. Combined filters use AND semantics.
    39. No demographic filters preserve the existing forecast output.
    40. Query efficiency / no N+1 regression.
    """

    @classmethod
    def setUpTestData(cls):
        # Geography
        cls.state = State.objects.create(name='Karnataka', code='KA')
        cls.district_central = District.objects.create(state=cls.state, name='BBMP Central', code='KA-CEN')
        cls.district_rural = District.objects.create(state=cls.state, name='Bengaluru Rural', code='KA-RUR')

        cls.zone_central = Zone.objects.create(district=cls.district_central, name='Central Zone', code='Z-CEN')
        cls.zone_rural = Zone.objects.create(district=cls.district_rural, name='Rural Zone', code='Z-RUR')

        cls.ward_c1 = Ward.objects.create(zone=cls.zone_central, ward_number=101, name='Indiranagar', population=25000)
        cls.ward_r1 = Ward.objects.create(zone=cls.zone_rural, ward_number=201, name='Varthur', population=18000)

        # Facilities
        cls.fac_c1 = Facility.objects.create(
            facility_code='HOSP-FC1', facility_name='Bowring Hospital', facility_type='MAIN_HOSPITAL',
            district=cls.district_central, ward=cls.ward_c1, state=cls.state
        )
        cls.fac_c2 = Facility.objects.create(
            facility_code='CLINIC-FC2', facility_name='Indiranagar Clinic', facility_type='NAMMA_CLINIC',
            district=cls.district_central, ward=cls.ward_c1, state=cls.state
        )
        cls.fac_r1 = Facility.objects.create(
            facility_code='RURAL-FC1', facility_name='Varthur Rural CHC', facility_type='RURAL_CLINIC',
            district=cls.district_rural, ward=cls.ward_r1, state=cls.state
        )

        # Users
        cls.admin_c1 = User.objects.create_user(
            username='fc_admin_c1', password='Password123!', role='HOSPITAL_ADMIN',
            assigned_facility=cls.fac_c1
        )
        cls.officer_c = User.objects.create_user(
            username='fc_officer_c', password='Password123!', role='DISTRICT_OFFICER',
            assigned_district=cls.district_central
        )
        cls.officer_r = User.objects.create_user(
            username='fc_officer_r', password='Password123!', role='DISTRICT_OFFICER',
            assigned_district=cls.district_rural
        )

        # Reference date: 2026-12-15
        cls.as_of = datetime.date(2026, 12, 15)

        # Deterministic Patients
        # 1. Young Adult Female (15-24, FEMALE, Pregnant)
        cls.p_young_adult = Patient.objects.create(
            patient_id='FC-P01', name='Young Adult Pregnant Female',
            date_of_birth=datetime.date(2006, 3, 1), age=20, gender='FEMALE',
            vulnerability_information='Pregnant Woman',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # 2. Adult Male (25-44, MALE, Low Income Slum)
        cls.p_adult = Patient.objects.create(
            patient_id='FC-P02', name='Adult Male Patient',
            date_of_birth=datetime.date(1996, 3, 1), age=30, gender='MALE',
            vulnerability_information='Slum Resident / Low Income Group',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # 3. Child Female (0-5, FEMALE, Low Income Slum)
        cls.p_child = Patient.objects.create(
            patient_id='FC-P03', name='Child Girl',
            date_of_birth=datetime.date(2024, 3, 1), age=2, gender='FEMALE',
            vulnerability_information='Slum Resident / Low Income Group',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # 4. Youth Other (6-14, OTHER, Disability)
        cls.p_youth = Patient.objects.create(
            patient_id='FC-P04', name='Youth PwD Other',
            date_of_birth=datetime.date(2016, 3, 1), age=10, gender='OTHER',
            vulnerability_information='Person with Disability (PwD)',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # 5. Middle-aged Female (45-59, FEMALE, Chronic) - only 1 case for sparse subgroup
        cls.p_middle = Patient.objects.create(
            patient_id='FC-P05', name='Middle Aged Female Chronic',
            date_of_birth=datetime.date(1976, 3, 1), age=50, gender='FEMALE',
            vulnerability_information='Hypertension / Diabetic comorbidity',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # 6. Senior Male (60+, MALE, Elderly)
        cls.p_elderly = Patient.objects.create(
            patient_id='FC-P06', name='Elderly Senior Male',
            date_of_birth=datetime.date(1956, 3, 1), age=70, gender='MALE',
            vulnerability_information='Elderly Person',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # 7. General Male (25-44, MALE, General)
        cls.p_general = Patient.objects.create(
            patient_id='FC-P07', name='General Citizen Male',
            date_of_birth=datetime.date(1990, 3, 1), age=36, gender='MALE',
            vulnerability_information='GENERAL',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # 8. Boundary Patient (DOB 2020-06-15)
        cls.p_boundary = Patient.objects.create(
            patient_id='FC-P08', name='Boundary Boy',
            date_of_birth=datetime.date(2020, 6, 15), age=6, gender='MALE',
            vulnerability_information='GENERAL',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # 9. Patient with missing DOB, missing gender, missing vulnerability
        cls.p_unknown_demo = Patient.objects.create(
            patient_id='FC-P09', name='Unknown Demographics Patient',
            date_of_birth=None, age=30, gender='',
            vulnerability_information='',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        # 10. Rural Patient
        cls.p_rural = Patient.objects.create(
            patient_id='FC-P10', name='Rural Female Patient',
            date_of_birth=datetime.date(1995, 1, 1), age=31, gender='FEMALE',
            vulnerability_information='Slum Resident / Low Income Group',
            district=cls.district_rural, ward=cls.ward_r1, registered_at_facility=cls.fac_r1
        )

        # -------------------------------------------------------------------
        # Deterministic Disease Cases for Dengue at fac_c1 (15 cases)
        # -------------------------------------------------------------------
        # 1. Jan 10: p_adult (25-44, MALE, MILD, LOW_INCOME_SLUM) -> NEW
        cls.c1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_adult, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 1, 10), severity='MILD'
        )
        # 2. Feb 10: p_young_adult (15-24, FEMALE, SEVERE, PREGNANT) -> NEW
        cls.c2 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_young_adult, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 2, 10), severity='SEVERE'
        )
        # 3. Mar 10: p_child (0-5, FEMALE, MILD, LOW_INCOME_SLUM) -> NEW
        cls.c3 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_child, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 3, 10), severity='MILD'
        )
        # 4. Apr 10: p_youth (6-14, OTHER, MODERATE, DISABILITY) -> NEW
        cls.c4 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_youth, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 4, 10), severity='MODERATE'
        )
        # 5. May 10: p_middle (45-59, FEMALE, MILD, CHRONIC_CONDITION) -> NEW (only 1 case for 45-59)
        cls.c5 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_middle, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 5, 10), severity='MILD'
        )
        # 6. May 15: p_boundary (0-5, MALE, MILD, GENERAL) -> NEW
        cls.c6 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_boundary, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 5, 15), severity='MILD'
        )
        # 7. Jun 10: p_elderly (60+, MALE, SEVERE, ELDERLY) -> NEW
        cls.c7 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_elderly, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 6, 10), severity='SEVERE'
        )
        # 8. Jul 10: p_adult (25-44, MALE, SEVERE, LOW_INCOME_SLUM) -> FOLLOW_UP
        cls.c8 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_adult, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 7, 10), severity='SEVERE'
        )
        # 9. Jul 15: p_boundary (6-14, MALE, MODERATE, GENERAL) -> FOLLOW_UP
        cls.c9 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_boundary, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 7, 15), severity='MODERATE'
        )
        # 10. Aug 10: p_young_adult (15-24, FEMALE, SEVERE, PREGNANT) -> FOLLOW_UP
        cls.c10 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_young_adult, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 8, 10), severity='SEVERE'
        )
        # 11. Sep 10: p_young_adult (15-24, FEMALE, SEVERE, PREGNANT) -> FOLLOW_UP
        cls.c11 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_young_adult, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 9, 10), severity='SEVERE'
        )
        # 12. Oct 10: p_young_adult (15-24, FEMALE, SEVERE, PREGNANT) -> FOLLOW_UP
        cls.c12 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_young_adult, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 10, 10), severity='SEVERE'
        )
        # 13. Oct 20: p_unknown_demo (UNKNOWN age/gender/vuln, severity='INVALID_VAL' -> UNKNOWN sev) -> NEW
        cls.c13 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_unknown_demo, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 10, 20), severity='INVALID_VAL'
        )
        # 14. Nov 10: p_elderly (60+, MALE, SEVERE, ELDERLY) -> FOLLOW_UP
        cls.c14 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_elderly, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 11, 10), severity='SEVERE'
        )
        # 15. Nov 15: p_general (25-44, MALE, MODERATE, GENERAL) -> NEW
        cls.c15 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_general, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 11, 15), severity='MODERATE'
        )

        # Discrimination cases
        # Malaria at fac_c1
        cls.c_malaria = DiseaseCase.objects.create(
            disease_name='Malaria', patient=cls.p_adult, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 6, 10), severity='MILD'
        )
        # Dengue at fac_c2 (intra-district allowed)
        cls.c_c2 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_adult, facility=cls.fac_c2,
            ward=cls.ward_c1, report_date=datetime.date(2026, 6, 10), severity='MILD'
        )
        # Dengue at rural fac_r1
        cls.c_rural = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_rural, facility=cls.fac_r1,
            ward=cls.ward_r1, report_date=datetime.date(2026, 6, 10), severity='MILD'
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_c1)
        self.url = reverse('intelligence_forecast')

    # 1. Existing forecast behavior without demographic filters
    def test_01_existing_forecast_without_demographics(self):
        """
        Preserves existing forecasting output contract when no demographic parameters are provided.
        Returns historical series, WMA forecast points, trend signal, and status.
        """
        res = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12&weeks=4")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data

        self.assertTrue(data['is_authorized'])
        self.assertEqual(data['disease'], 'Dengue')
        self.assertEqual(data['observation_period']['total_cases'], 15)
        self.assertIn('forecast', data)
        self.assertEqual(data['forecast']['status'], 'AVAILABLE')
        self.assertEqual(len(data['forecast']['points']), 4)
        self.assertGreater(len(data['historical_series']), 0)

    # 2. Forecast filtered by age group
    def test_02_forecast_filtered_by_age_group(self):
        """
        Forecast filtered by age_group=15-24 restricts weekly time series and WMA forecast to that cohort.
        """
        res = self.client.get(f"{self.url}?disease=Dengue&age_group=15-24&date={self.as_of}&months=12&weeks=4")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['observation_period']['total_cases'], 4)
        self.assertEqual(res.data['forecast']['status'], 'AVAILABLE')
        self.assertEqual(len(res.data['forecast']['points']), 4)

    # 3. Forecast filtered by gender
    def test_03_forecast_filtered_by_gender(self):
        """
        Forecast filtered by gender=FEMALE restricts time series to female cases (6 cases).
        """
        res = self.client.get(f"{self.url}?disease=Dengue&gender=FEMALE&date={self.as_of}&months=12&weeks=4")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['observation_period']['total_cases'], 6)
        self.assertEqual(res.data['forecast']['status'], 'AVAILABLE')

    # 4. Forecast filtered by severity
    def test_04_forecast_filtered_by_severity(self):
        """
        Forecast filtered by severity=SEVERE restricts time series to severe cases (7 cases).
        """
        res = self.client.get(f"{self.url}?disease=Dengue&severity=SEVERE&date={self.as_of}&months=12&weeks=4")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['observation_period']['total_cases'], 7)
        self.assertEqual(res.data['forecast']['status'], 'AVAILABLE')

    # 5. Forecast filtered by vulnerable group
    def test_05_forecast_filtered_by_vulnerable_group(self):
        """
        Forecast filtered by vulnerable_group=PREGNANT restricts time series to pregnant patients (4 cases).
        """
        res = self.client.get(f"{self.url}?disease=Dengue&vulnerable_group=PREGNANT&date={self.as_of}&months=12&weeks=4")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['observation_period']['total_cases'], 4)
        self.assertEqual(res.data['forecast']['status'], 'AVAILABLE')

    # 6. Forecast filtered by patient type
    def test_06_forecast_filtered_by_patient_type(self):
        """
        Forecast filtered by patient_type=FOLLOW_UP restricts time series to follow-up visits (6 cases).
        """
        res = self.client.get(f"{self.url}?disease=Dengue&patient_type=FOLLOW_UP&date={self.as_of}&months=12&weeks=4")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['observation_period']['total_cases'], 6)
        self.assertEqual(res.data['forecast']['status'], 'AVAILABLE')

    # 7. Disease + age group
    def test_07_disease_and_age_group(self):
        """Filters both disease and age group concurrently."""
        res = self.client.get(f"{self.url}?disease=Dengue&age_group=0-5&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['observation_period']['total_cases'], 2)

    # 8. Disease + gender
    def test_08_disease_and_gender(self):
        """Filters both disease and gender concurrently."""
        res = self.client.get(f"{self.url}?disease=Dengue&gender=MALE&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['observation_period']['total_cases'], 7)

    # 9. Disease + severity
    def test_09_disease_and_severity(self):
        """Filters both disease and severity concurrently."""
        res = self.client.get(f"{self.url}?disease=Dengue&severity=MILD&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['observation_period']['total_cases'], 4)

    # 10. Disease + vulnerable group
    def test_10_disease_and_vulnerable_group(self):
        """Filters both disease and vulnerable group concurrently."""
        res = self.client.get(f"{self.url}?disease=Dengue&vulnerable_group=LOW_INCOME_SLUM&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['observation_period']['total_cases'], 3)

    # 11. Disease + patient type
    def test_11_disease_and_patient_type(self):
        """Filters both disease and patient type concurrently."""
        res = self.client.get(f"{self.url}?disease=Dengue&patient_type=NEW&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['observation_period']['total_cases'], 9)

    # 12. Age + gender combination
    def test_12_age_and_gender_combination(self):
        """Combines age group and gender filters."""
        res = self.client.get(f"{self.url}?disease=Dengue&age_group=15-24&gender=FEMALE&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['observation_period']['total_cases'], 4)

    # 13. Age + gender + severity
    def test_13_age_gender_severity(self):
        """Combines age group, gender, and severity filters."""
        res = self.client.get(f"{self.url}?disease=Dengue&age_group=15-24&gender=FEMALE&severity=SEVERE&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['observation_period']['total_cases'], 4)

    # 14. Age + gender + vulnerable group
    def test_14_age_gender_vulnerable_group(self):
        """Combines age group, gender, and vulnerable group filters."""
        res = self.client.get(f"{self.url}?disease=Dengue&age_group=15-24&gender=FEMALE&vulnerable_group=PREGNANT&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['observation_period']['total_cases'], 4)

    # 15. Age + gender + patient type
    def test_15_age_gender_patient_type(self):
        """Combines age group, gender, and patient type filters."""
        res = self.client.get(f"{self.url}?disease=Dengue&age_group=15-24&gender=FEMALE&patient_type=FOLLOW_UP&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['observation_period']['total_cases'], 3)
        self.assertEqual(res.data['forecast']['status'], 'AVAILABLE')

    # 16. Full demographic combination
    def test_16_full_demographic_combination(self):
        """Combines all 5 demographic dimensions simultaneously."""
        url = (
            f"{self.url}?disease=Dengue&age_group=15-24&gender=FEMALE&severity=SEVERE"
            f"&vulnerable_group=PREGNANT&patient_type=FOLLOW_UP&date={self.as_of}&months=12&weeks=4"
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['observation_period']['total_cases'], 3)
        self.assertEqual(res.data['forecast']['status'], 'AVAILABLE')
        self.assertEqual(len(res.data['forecast']['points']), 4)

    # 17. Invalid age_group returns HTTP 400
    def test_17_invalid_age_group_returns_400(self):
        res = self.client.get(f"{self.url}?disease=Dengue&age_group=INVALID_GROUP")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # 18. Invalid gender returns HTTP 400
    def test_18_invalid_gender_returns_400(self):
        res = self.client.get(f"{self.url}?disease=Dengue&gender=UNKNOWN_ALIEN")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # 19. Invalid severity returns HTTP 400
    def test_19_invalid_severity_returns_400(self):
        res = self.client.get(f"{self.url}?disease=Dengue&severity=EXTREME")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # 20. Invalid vulnerable_group returns HTTP 400
    def test_20_invalid_vulnerable_group_returns_400(self):
        res = self.client.get(f"{self.url}?disease=Dengue&vulnerable_group=ASTRONAUT")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # 21. Invalid patient_type returns HTTP 400
    def test_21_invalid_patient_type_returns_400(self):
        res = self.client.get(f"{self.url}?disease=Dengue&patient_type=RECURRENT")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # 22. UNKNOWN public filters follow existing validation behavior
    def test_22_unknown_public_filters_rejected(self):
        """UNKNOWN cannot be supplied as a public query filter."""
        for param in ['age_group', 'gender', 'severity', 'vulnerable_group', 'patient_type']:
            res = self.client.get(f"{self.url}?disease=Dengue&{param}=UNKNOWN")
            self.assertEqual(
                res.status_code, status.HTTP_400_BAD_REQUEST,
                f"Expected HTTP 400 when filtering by {param}=UNKNOWN, got {res.status_code}"
            )

    # 23. Hospital Admin cannot forecast another facility
    def test_23_hospital_admin_cannot_forecast_another_facility(self):
        """Hospital Admin requesting facility outside assignment receives HTTP 403."""
        res = self.client.get(f"{self.url}?disease=Dengue&facility={self.fac_r1.id}")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 24. District Officer cannot forecast another district
    def test_24_district_officer_cannot_forecast_another_district(self):
        """District Officer requesting another district receives HTTP 403."""
        self.client.force_authenticate(user=self.officer_c)
        res = self.client.get(f"{self.url}?disease=Dengue&district={self.district_rural.id}")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 25. District Officer can forecast an allowed facility within their district
    def test_25_district_officer_can_forecast_allowed_facility_in_district(self):
        """District Officer requesting a facility inside their district receives HTTP 200."""
        self.client.force_authenticate(user=self.officer_c)
        res = self.client.get(f"{self.url}?disease=Dengue&facility={self.fac_c2.id}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    # 26. Missing DOB is classified as UNKNOWN
    def test_26_missing_dob_classified_as_unknown(self):
        """Patient with missing DOB is classified into UNKNOWN and excluded from standard age groups."""
        res_all = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        res_0_5 = self.client.get(f"{self.url}?disease=Dengue&age_group=0-5&date={self.as_of}&months=12")
        res_15_24 = self.client.get(f"{self.url}?disease=Dengue&age_group=15-24&date={self.as_of}&months=12")

        self.assertEqual(res_all.data['observation_period']['total_cases'], 15)
        # c13 has missing DOB and is not included in 0-5 or 15-24
        self.assertEqual(res_0_5.data['observation_period']['total_cases'], 2)
        self.assertEqual(res_15_24.data['observation_period']['total_cases'], 4)

    # 27. Invalid severity becomes UNKNOWN rather than another severity
    def test_27_invalid_severity_becomes_unknown(self):
        """Case c13 with severity='INVALID_VAL' is normalized to UNKNOWN and not counted under MILD/MODERATE/SEVERE."""
        res_mild = self.client.get(f"{self.url}?disease=Dengue&severity=MILD&date={self.as_of}&months=12")
        res_mod = self.client.get(f"{self.url}?disease=Dengue&severity=MODERATE&date={self.as_of}&months=12")
        res_sev = self.client.get(f"{self.url}?disease=Dengue&severity=SEVERE&date={self.as_of}&months=12")

        total_known_sev = (
            res_mild.data['observation_period']['total_cases'] +
            res_mod.data['observation_period']['total_cases'] +
            res_sev.data['observation_period']['total_cases']
        )
        self.assertEqual(total_known_sev, 14)  # 15 total - 1 UNKNOWN

    # 28. Invalid vulnerability becomes UNKNOWN
    def test_28_invalid_vulnerability_becomes_unknown(self):
        """Case c13 with empty vulnerability info is normalized to UNKNOWN."""
        self.assertEqual(normalize_vulnerable_group(''), VULNERABLE_GROUP_UNKNOWN)
        self.assertEqual(normalize_vulnerable_group(None), VULNERABLE_GROUP_UNKNOWN)

    # 29. Missing/insufficient patient history produces UNKNOWN patient type
    def test_29_missing_patient_history_produces_unknown_patient_type(self):
        """Case with missing patient reference produces PATIENT_TYPE_UNKNOWN."""
        dummy_case = DiseaseCase(patient=None, report_date=datetime.date(2026, 5, 1))
        self.assertEqual(get_case_patient_type(dummy_case), PATIENT_TYPE_UNKNOWN)
        self.assertEqual(get_case_patient_type(None), PATIENT_TYPE_UNKNOWN)

    # 30. Patient age is calculated using DiseaseCase.report_date
    def test_30_patient_age_uses_report_date(self):
        """
        Boundary patient DOB 2020-06-15:
        At 2026-05-15 (age 5): categorized as '0-5'.
        At 2026-07-15 (age 6): categorized as '6-14'.
        """
        res_0_5 = self.client.get(f"{self.url}?disease=Dengue&age_group=0-5&date={self.as_of}&months=12")
        res_6_14 = self.client.get(f"{self.url}?disease=Dengue&age_group=6-14&date={self.as_of}&months=12")

        self.assertEqual(res_0_5.data['observation_period']['total_cases'], 2)  # c3 (Mar) and c6 (May 15)
        self.assertEqual(res_6_14.data['observation_period']['total_cases'], 2)  # c4 (Apr) and c9 (Jul 15)

    # 31. Patient type is calculated using history available up to DiseaseCase.report_date
    def test_31_patient_type_uses_point_in_time_history(self):
        """
        c1 on 2026-01-10 is NEW (no prior cases).
        c8 on 2026-07-10 is FOLLOW_UP (c1 occurred earlier).
        """
        pt_c1 = get_case_patient_type(self.c1)
        pt_c8 = get_case_patient_type(self.c8)
        self.assertEqual(pt_c1, PATIENT_TYPE_NEW)
        self.assertEqual(pt_c8, PATIENT_TYPE_FOLLOW_UP)

    # 32. Later patient records do not alter earlier patient-type classification
    def test_32_later_patient_records_do_not_alter_earlier_classification(self):
        """The existence of c8 does not change c1's classification to FOLLOW_UP."""
        pt_c1 = get_case_patient_type(self.c1)
        self.assertEqual(pt_c1, PATIENT_TYPE_NEW)

    # 33. Insufficient demographic subgroup history returns INSUFFICIENT_DATA
    def test_33_insufficient_demographic_subgroup_history_returns_insufficient_data(self):
        """
        Demographic subgroup with sparse historical records (1 case) returns INSUFFICIENT_DATA.
        """
        res = self.client.get(f"{self.url}?disease=Dengue&age_group=45-59&date={self.as_of}&months=12&weeks=4")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['observation_period']['total_cases'], 1)
        self.assertEqual(res.data['forecast']['status'], 'INSUFFICIENT_DATA')
        self.assertEqual(len(res.data['forecast']['points']), 0)
        self.assertIn('Insufficient historical', res.data['forecast']['explanation'])

    # 34. Insufficient subgroup does NOT fall back to overall disease forecast
    def test_34_insufficient_subgroup_does_not_fall_back_to_overall(self):
        """
        Verifies that sparse subgroup (age_group=45-59) does not fall back to the overall Dengue forecast.
        Overall Dengue has 15 cases and AVAILABLE status; subgroup has 1 case and INSUFFICIENT_DATA.
        """
        res_overall = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12&weeks=4")
        res_subgroup = self.client.get(f"{self.url}?disease=Dengue&age_group=45-59&date={self.as_of}&months=12&weeks=4")

        self.assertEqual(res_overall.data['forecast']['status'], 'AVAILABLE')
        self.assertEqual(len(res_overall.data['forecast']['points']), 4)

        self.assertEqual(res_subgroup.data['forecast']['status'], 'INSUFFICIENT_DATA')
        self.assertEqual(len(res_subgroup.data['forecast']['points']), 0)
        self.assertNotEqual(
            res_subgroup.data['observation_period']['total_cases'],
            res_overall.data['observation_period']['total_cases']
        )

    # 35. Historical actual values remain separate from forecast values
    def test_35_historical_actual_values_remain_separate_from_forecast(self):
        """
        Response contract clearly distinguishes historical series from forecast points:
        historical_series: [{week_number, week_start, week_end, cases}]
        forecast.points: [{forecast_week_start, forecast_week_end, predicted_cases, lower_bound, upper_bound}]
        """
        res = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12&weeks=4")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        hist = res.data['historical_series']
        self.assertIsInstance(hist, list)
        self.assertIn('cases', hist[0])
        self.assertIn('week_start', hist[0])

        fc_points = res.data['forecast']['points']
        self.assertIsInstance(fc_points, list)
        self.assertIn('predicted_cases', fc_points[0])
        self.assertIn('lower_bound', fc_points[0])
        self.assertIn('upper_bound', fc_points[0])

    # 36. Zero-case weeks are handled consistently
    def test_36_zero_case_weeks_handled_consistently(self):
        """Continuous weekly time series maintains 0 for intervals with no cases."""
        res = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12&weeks=4")
        hist = res.data['historical_series']
        zero_weeks = [w for w in hist if w['cases'] == 0]
        self.assertGreater(len(zero_weeks), 0)

    # 37. Demographic filters are never silently ignored
    def test_37_demographic_filters_are_never_silently_ignored(self):
        """Applying gender=FEMALE produces a strictly smaller subset than unfiltered Dengue."""
        res_all = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        res_fem = self.client.get(f"{self.url}?disease=Dengue&gender=FEMALE&date={self.as_of}&months=12")

        self.assertNotEqual(
            res_all.data['observation_period']['total_cases'],
            res_fem.data['observation_period']['total_cases']
        )
        self.assertEqual(res_fem.data['observation_period']['total_cases'], 6)

    # 38. Combined filters use AND semantics
    def test_38_combined_filters_use_and_semantics(self):
        """
        Cases must satisfy all conditions:
        age_group=15-24 AND gender=FEMALE AND severity=SEVERE AND patient_type=FOLLOW_UP
        returns strictly the 3 cases that satisfy all four constraints.
        """
        url = (
            f"{self.url}?disease=Dengue&age_group=15-24&gender=FEMALE&severity=SEVERE"
            f"&patient_type=FOLLOW_UP&date={self.as_of}&months=12"
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['observation_period']['total_cases'], 3)

    # 39. No demographic filters preserve the existing forecast output
    def test_39_no_demographic_filters_preserve_existing_forecast_output(self):
        """Calling without demographic parameters returns full unconstrained dataset."""
        res = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        self.assertEqual(res.data['observation_period']['total_cases'], 15)

    # 40. Query efficiency / no N+1 regression
    def test_40_query_efficiency_no_n_plus_one_regression(self):
        """
        build_disease_time_series executes in strictly 1 query via annotate_case_patient_type
        and select_related('patient') even with all 5 demographic dimensions filtered.
        """
        with self.assertNumQueries(1):
            build_disease_time_series(
                facility_ids=[self.fac_c1.id],
                disease_name='Dengue',
                as_of_date=self.as_of,
                weeks_count=52,
                age_group='15-24',
                gender='FEMALE',
                severity='SEVERE',
                vulnerable_group='PREGNANT',
                patient_type='FOLLOW_UP'
            )


class PublicHealthForecastRiskTestCase(TestCase):
    """
    Prompt 9: Public Health Forecast Risk / Threshold Integration & Unit Test Suite
    Comprehensive validation of deterministic, explainable forecast risk layer:
    1. Existing forecast without filters still works.
    2. Normal risk classification.
    3. Elevated risk classification.
    4. High-risk classification.
    5. Risk threshold exactly at 1.15.
    6. Risk threshold exactly at 1.50.
    7. Ratio below 1.15 = NORMAL.
    8. Ratio between 1.15 and 1.50 = ELEVATED.
    9. Ratio >= 1.50 = HIGH_RISK.
    10. Fewer than 3 historical cases = INSUFFICIENT_DATA.
    11. Existing forecast INSUFFICIENT_DATA produces risk INSUFFICIENT_DATA.
    12. Zero historical baseline + zero prediction = NORMAL.
    13. Zero historical baseline + positive prediction = HIGH_RISK.
    14. Age-group risk uses only selected age group.
    15. Gender risk uses only selected gender.
    16. Severity risk uses only selected severity.
    17. Vulnerable-group risk uses only selected vulnerable group.
    18. Patient-type risk uses only selected patient type.
    19. Age + gender uses AND semantics.
    20. Age + gender + severity uses AND semantics.
    21. Age + gender + vulnerability uses AND semantics.
    22. Age + gender + patient type uses AND semantics.
    23. All five demographic dimensions use AND semantics.
    24. Risk does not fall back to overall disease baseline.
    25. Historical actual values remain unchanged.
    26. Forecast predicted values remain unchanged.
    27. Risk points correspond exactly to forecast points.
    28. Highest risk level precedence works.
    29. Risk counts reconcile with risk_points.
    30. Hospital Admin cross-facility request returns 403.
    31. District Officer cross-district request returns 403.
    32. District Officer permitted facility works.
    33. Invalid demographic filters still return HTTP 400.
    34. UNKNOWN public filters still return HTTP 400.
    35. No fake DiseaseCase records are created.
    36. Query efficiency / no N+1 regression.
    37. Risk calculation is deterministic for the same input.
    38. Changing demographic filters changes the risk population/baseline appropriately.
    39. Forecast risk is based on the same historical series used by the forecast.
    40. Risk calculation does not perform a second broad/unfiltered DiseaseCase query.
    """

    @classmethod
    def setUpTestData(cls):
        # Geography
        cls.state = State.objects.create(name='Karnataka', code='KA')
        cls.district_central = District.objects.create(state=cls.state, name='BBMP Central', code='KA-CEN')
        cls.district_rural = District.objects.create(state=cls.state, name='Bengaluru Rural', code='KA-RUR')

        cls.zone_central = Zone.objects.create(district=cls.district_central, name='Central Zone', code='Z-CEN')
        cls.zone_rural = Zone.objects.create(district=cls.district_rural, name='Rural Zone', code='Z-RUR')

        cls.ward_c1 = Ward.objects.create(zone=cls.zone_central, ward_number=101, name='Indiranagar', population=25000)
        cls.ward_r1 = Ward.objects.create(zone=cls.zone_rural, ward_number=201, name='Varthur', population=18000)

        # Facilities
        cls.fac_c1 = Facility.objects.create(
            facility_code='HOSP-FC1', facility_name='Bowring Hospital', facility_type='MAIN_HOSPITAL',
            district=cls.district_central, ward=cls.ward_c1, state=cls.state
        )
        cls.fac_c2 = Facility.objects.create(
            facility_code='CLINIC-FC2', facility_name='Indiranagar Clinic', facility_type='NAMMA_CLINIC',
            district=cls.district_central, ward=cls.ward_c1, state=cls.state
        )
        cls.fac_r1 = Facility.objects.create(
            facility_code='RURAL-FC1', facility_name='Varthur Rural CHC', facility_type='RURAL_CLINIC',
            district=cls.district_rural, ward=cls.ward_r1, state=cls.state
        )

        # Users
        cls.admin_c1 = User.objects.create_user(
            username='fr_admin_c1', password='Password123!', role='HOSPITAL_ADMIN',
            assigned_facility=cls.fac_c1
        )
        cls.officer_c = User.objects.create_user(
            username='fr_officer_c', password='Password123!', role='DISTRICT_OFFICER',
            assigned_district=cls.district_central
        )
        cls.officer_r = User.objects.create_user(
            username='fr_officer_r', password='Password123!', role='DISTRICT_OFFICER',
            assigned_district=cls.district_rural
        )

        # Reference date: 2026-12-15
        cls.as_of = datetime.date(2026, 12, 15)

        # Patients
        cls.p_young_adult = Patient.objects.create(
            patient_id='FR-P01', name='Young Adult Pregnant Female',
            date_of_birth=datetime.date(2006, 3, 1), age=20, gender='FEMALE',
            vulnerability_information='Pregnant Woman',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        cls.p_adult = Patient.objects.create(
            patient_id='FR-P02', name='Adult Male Patient',
            date_of_birth=datetime.date(1996, 3, 1), age=30, gender='MALE',
            vulnerability_information='Slum Resident / Low Income Group',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        cls.p_child = Patient.objects.create(
            patient_id='FR-P03', name='Child Girl',
            date_of_birth=datetime.date(2024, 3, 1), age=2, gender='FEMALE',
            vulnerability_information='Slum Resident / Low Income Group',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        cls.p_youth = Patient.objects.create(
            patient_id='FR-P04', name='Youth PwD Other',
            date_of_birth=datetime.date(2016, 3, 1), age=10, gender='OTHER',
            vulnerability_information='Person with Disability (PwD)',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        cls.p_middle = Patient.objects.create(
            patient_id='FR-P05', name='Middle Aged Female Chronic',
            date_of_birth=datetime.date(1976, 3, 1), age=50, gender='FEMALE',
            vulnerability_information='Hypertension / Diabetic comorbidity',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        cls.p_elderly = Patient.objects.create(
            patient_id='FR-P06', name='Elderly Senior Male',
            date_of_birth=datetime.date(1956, 3, 1), age=70, gender='MALE',
            vulnerability_information='Elderly Person',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        cls.p_general = Patient.objects.create(
            patient_id='FR-P07', name='General Citizen Male',
            date_of_birth=datetime.date(1990, 3, 1), age=36, gender='MALE',
            vulnerability_information='GENERAL',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        cls.p_boundary = Patient.objects.create(
            patient_id='FR-P08', name='Boundary Boy',
            date_of_birth=datetime.date(2020, 6, 15), age=6, gender='MALE',
            vulnerability_information='GENERAL',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )
        cls.p_unknown_demo = Patient.objects.create(
            patient_id='FR-P09', name='Unknown Demographics Patient',
            date_of_birth=None, age=30, gender='',
            vulnerability_information='',
            district=cls.district_central, ward=cls.ward_c1, registered_at_facility=cls.fac_c1
        )

        # -------------------------------------------------------------------
        # Deterministic Disease Cases for Dengue at fac_c1 (15 cases)
        # -------------------------------------------------------------------
        cls.c1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_adult, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 1, 10), severity='MILD'
        )
        cls.c2 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_young_adult, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 2, 10), severity='SEVERE'
        )
        cls.c3 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_child, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 3, 10), severity='MILD'
        )
        cls.c4 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_youth, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 4, 10), severity='MODERATE'
        )
        cls.c5 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_middle, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 5, 10), severity='MILD'
        )
        cls.c6 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_boundary, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 5, 15), severity='MILD'
        )
        cls.c7 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_elderly, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 6, 10), severity='SEVERE'
        )
        cls.c8 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_adult, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 7, 10), severity='SEVERE'
        )
        cls.c9 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_boundary, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 7, 15), severity='MODERATE'
        )
        cls.c10 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_young_adult, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 8, 10), severity='SEVERE'
        )
        cls.c11 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_young_adult, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 9, 10), severity='SEVERE'
        )
        cls.c12 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_young_adult, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 10, 10), severity='SEVERE'
        )
        cls.c13 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_unknown_demo, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 10, 20), severity='INVALID_VAL'
        )
        cls.c14 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_elderly, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 11, 10), severity='SEVERE'
        )
        cls.c15 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_general, facility=cls.fac_c1,
            ward=cls.ward_c1, report_date=datetime.date(2026, 11, 15), severity='MODERATE'
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_c1)
        self.url = reverse('intelligence_forecast')

    # 1. Existing forecast without filters still works
    def test_01_existing_forecast_without_filters_still_works(self):
        """Calling forecast endpoint returns forecast_risk section in AVAILABLE state."""
        res = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('forecast_risk', res.data)
        risk = res.data['forecast_risk']
        self.assertEqual(risk['status'], RISK_STATUS_AVAILABLE)
        self.assertIn(risk['highest_risk_level'], [RISK_LEVEL_NORMAL, RISK_LEVEL_ELEVATED, RISK_LEVEL_HIGH])
        self.assertGreater(len(risk['risk_points']), 0)
        self.assertIsNotNone(risk['historical_baseline'])
        self.assertEqual(risk['elevation_ratio_threshold'], FORECAST_RISK_ELEVATION_RATIO)
        self.assertEqual(risk['high_risk_ratio_threshold'], FORECAST_RISK_HIGH_RATIO)

    # 2. Normal risk classification
    def test_02_normal_risk_classification(self):
        """Ratio < 1.15 produces risk_level NORMAL."""
        hist = [{'cases': 10}, {'cases': 10}, {'cases': 10}, {'cases': 10}]
        pts = [{'forecast_week_start': '2026-12-16', 'forecast_week_end': '2026-12-22', 'predicted_cases': 10.5}]
        res = calculate_forecast_risk(hist, pts)
        self.assertEqual(res['status'], RISK_STATUS_AVAILABLE)
        self.assertEqual(res['risk_points'][0]['risk_level'], RISK_LEVEL_NORMAL)
        self.assertEqual(res['highest_risk_level'], RISK_LEVEL_NORMAL)
        self.assertIn('remain below the elevation threshold', res['risk_points'][0]['explanation'])

    # 3. Elevated risk classification
    def test_03_elevated_risk_classification(self):
        """Ratio >= 1.15 and < 1.50 produces risk_level ELEVATED."""
        hist = [{'cases': 10}, {'cases': 10}, {'cases': 10}, {'cases': 10}]
        pts = [{'forecast_week_start': '2026-12-16', 'forecast_week_end': '2026-12-22', 'predicted_cases': 12.5}]
        res = calculate_forecast_risk(hist, pts)
        self.assertEqual(res['risk_points'][0]['risk_level'], RISK_LEVEL_ELEVATED)
        self.assertEqual(res['highest_risk_level'], RISK_LEVEL_ELEVATED)
        self.assertEqual(res['risk_points'][0]['ratio_to_baseline'], 1.25)

    # 4. High-risk classification
    def test_04_high_risk_classification(self):
        """Ratio >= 1.50 produces risk_level HIGH_RISK."""
        hist = [{'cases': 10}, {'cases': 10}, {'cases': 10}, {'cases': 10}]
        pts = [{'forecast_week_start': '2026-12-16', 'forecast_week_end': '2026-12-22', 'predicted_cases': 16.0}]
        res = calculate_forecast_risk(hist, pts)
        self.assertEqual(res['risk_points'][0]['risk_level'], RISK_LEVEL_HIGH)
        self.assertEqual(res['highest_risk_level'], RISK_LEVEL_HIGH)
        self.assertEqual(res['risk_points'][0]['ratio_to_baseline'], 1.60)

    # 5. Risk threshold exactly at 1.15
    def test_05_risk_threshold_exactly_at_1_15(self):
        """Ratio exactly 1.15 produces ELEVATED."""
        hist = [{'cases': 10}, {'cases': 10}, {'cases': 10}, {'cases': 10}]
        pts = [{'forecast_week_start': '2026-12-16', 'forecast_week_end': '2026-12-22', 'predicted_cases': 11.5}]
        res = calculate_forecast_risk(hist, pts)
        self.assertEqual(res['risk_points'][0]['risk_level'], RISK_LEVEL_ELEVATED)

    # 6. Risk threshold exactly at 1.50
    def test_06_risk_threshold_exactly_at_1_50(self):
        """Ratio exactly 1.50 produces HIGH_RISK."""
        hist = [{'cases': 10}, {'cases': 10}, {'cases': 10}, {'cases': 10}]
        pts = [{'forecast_week_start': '2026-12-16', 'forecast_week_end': '2026-12-22', 'predicted_cases': 15.0}]
        res = calculate_forecast_risk(hist, pts)
        self.assertEqual(res['risk_points'][0]['risk_level'], RISK_LEVEL_HIGH)

    # 7. Ratio below 1.15 = NORMAL
    def test_07_ratio_below_1_15_is_normal(self):
        """Ratio 1.149 (< 1.15) produces NORMAL."""
        hist = [{'cases': 10}, {'cases': 10}, {'cases': 10}, {'cases': 10}]
        pts = [{'forecast_week_start': '2026-12-16', 'forecast_week_end': '2026-12-22', 'predicted_cases': 11.49}]
        res = calculate_forecast_risk(hist, pts)
        self.assertEqual(res['risk_points'][0]['risk_level'], RISK_LEVEL_NORMAL)

    # 8. Ratio between 1.15 and 1.50 = ELEVATED
    def test_08_ratio_between_1_15_and_1_50_is_elevated(self):
        """Ratio 1.499 (< 1.50 and >= 1.15) produces ELEVATED."""
        hist = [{'cases': 10}, {'cases': 10}, {'cases': 10}, {'cases': 10}]
        pts = [{'forecast_week_start': '2026-12-16', 'forecast_week_end': '2026-12-22', 'predicted_cases': 14.99}]
        res = calculate_forecast_risk(hist, pts)
        self.assertEqual(res['risk_points'][0]['risk_level'], RISK_LEVEL_ELEVATED)

    # 9. Ratio >= 1.50 = HIGH_RISK
    def test_09_ratio_greater_equal_1_50_is_high_risk(self):
        """Ratio 1.501 (>= 1.50) produces HIGH_RISK."""
        hist = [{'cases': 10}, {'cases': 10}, {'cases': 10}, {'cases': 10}]
        pts = [{'forecast_week_start': '2026-12-16', 'forecast_week_end': '2026-12-22', 'predicted_cases': 15.01}]
        res = calculate_forecast_risk(hist, pts)
        self.assertEqual(res['risk_points'][0]['risk_level'], RISK_LEVEL_HIGH)

    # 10. Fewer than 3 historical cases = INSUFFICIENT_DATA
    def test_10_fewer_than_3_historical_cases_is_insufficient_data(self):
        """Total historical cases < 3 produces status INSUFFICIENT_DATA."""
        hist = [{'cases': 1}, {'cases': 1}, {'cases': 0}]
        pts = [{'forecast_week_start': '2026-12-16', 'forecast_week_end': '2026-12-22', 'predicted_cases': 5.0}]
        res = calculate_forecast_risk(hist, pts)
        self.assertEqual(res['status'], RISK_STATUS_INSUFFICIENT)
        self.assertIsNone(res['historical_baseline'])
        self.assertEqual(res['risk_points'], [])
        self.assertEqual(res['highest_risk_level'], RISK_LEVEL_INSUFFICIENT)
        self.assertEqual(res['risk_points_count'], 0)
        self.assertIn('Insufficient historical surveillance cases', res['explanation'])

    # 11. Existing forecast INSUFFICIENT_DATA produces risk INSUFFICIENT_DATA
    def test_11_existing_forecast_insufficient_data_produces_risk_insufficient_data(self):
        """When forecast status is INSUFFICIENT_DATA, risk status is also INSUFFICIENT_DATA."""
        hist = [{'cases': 10}, {'cases': 10}, {'cases': 10}]
        pts = []
        res = calculate_forecast_risk(hist, pts, forecast_status='INSUFFICIENT_DATA')
        self.assertEqual(res['status'], RISK_STATUS_INSUFFICIENT)
        self.assertEqual(res['highest_risk_level'], RISK_LEVEL_INSUFFICIENT)

    # 12. Zero historical baseline + zero prediction = NORMAL
    def test_12_zero_historical_baseline_plus_zero_prediction_is_normal(self):
        """Zero baseline with 0 predicted cases is safely classified as NORMAL without ZeroDivisionError."""
        hist = [{'cases': 0}, {'cases': 0}, {'cases': 0}]
        pts = [{'forecast_week_start': '2026-12-16', 'forecast_week_end': '2026-12-22', 'predicted_cases': 0.0}]
        res = calculate_forecast_risk(hist, pts, minimum_cases=0)
        self.assertEqual(res['status'], RISK_STATUS_AVAILABLE)
        self.assertEqual(res['risk_points'][0]['risk_level'], RISK_LEVEL_NORMAL)
        self.assertEqual(res['highest_risk_level'], RISK_LEVEL_NORMAL)
        self.assertIsNone(res['risk_points'][0]['ratio_to_baseline'])

    # 13. Zero historical baseline + positive prediction = HIGH_RISK
    def test_13_zero_historical_baseline_plus_positive_prediction_is_high_risk(self):
        """Zero baseline with positive prediction is safely classified as HIGH_RISK without ZeroDivisionError."""
        hist = [{'cases': 0}, {'cases': 0}, {'cases': 0}]
        pts = [{'forecast_week_start': '2026-12-16', 'forecast_week_end': '2026-12-22', 'predicted_cases': 2.5}]
        res = calculate_forecast_risk(hist, pts, minimum_cases=0)
        self.assertEqual(res['status'], RISK_STATUS_AVAILABLE)
        self.assertEqual(res['risk_points'][0]['risk_level'], RISK_LEVEL_HIGH)
        self.assertEqual(res['highest_risk_level'], RISK_LEVEL_HIGH)
        self.assertIsNone(res['risk_points'][0]['ratio_to_baseline'])

    # 14. Age-group risk uses only selected age group
    def test_14_age_group_risk_uses_only_selected_age_group(self):
        """Filtering by age_group=15-24 computes risk baseline only from the 4 cases in that age group."""
        res = self.client.get(f"{self.url}?disease=Dengue&age_group=15-24&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        risk = res.data['forecast_risk']
        self.assertEqual(risk['status'], RISK_STATUS_AVAILABLE)
        self.assertEqual(res.data['observation_period']['total_cases'], 4)
        expected_bl = round(4 / res.data['observation_period']['weeks_count'], 2)
        self.assertEqual(risk['historical_baseline'], expected_bl)

    # 15. Gender risk uses only selected gender
    def test_15_gender_risk_uses_only_selected_gender(self):
        """Filtering by gender=FEMALE computes risk baseline only from the 6 female cases."""
        res = self.client.get(f"{self.url}?disease=Dengue&gender=FEMALE&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        risk = res.data['forecast_risk']
        self.assertEqual(risk['status'], RISK_STATUS_AVAILABLE)
        self.assertEqual(res.data['observation_period']['total_cases'], 6)
        expected_bl = round(6 / res.data['observation_period']['weeks_count'], 2)
        self.assertEqual(risk['historical_baseline'], expected_bl)

    # 16. Severity risk uses only selected severity
    def test_16_severity_risk_uses_only_selected_severity(self):
        """Filtering by severity=SEVERE computes risk baseline only from the 7 severe cases."""
        res = self.client.get(f"{self.url}?disease=Dengue&severity=SEVERE&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        risk = res.data['forecast_risk']
        self.assertEqual(risk['status'], RISK_STATUS_AVAILABLE)
        self.assertEqual(res.data['observation_period']['total_cases'], 7)
        expected_bl = round(7 / res.data['observation_period']['weeks_count'], 2)
        self.assertEqual(risk['historical_baseline'], expected_bl)

    # 17. Vulnerable-group risk uses only selected vulnerable group
    def test_17_vulnerable_group_risk_uses_only_selected_vulnerable_group(self):
        """Filtering by vulnerable_group=PREGNANT computes risk baseline only from the 4 pregnant cases."""
        res = self.client.get(f"{self.url}?disease=Dengue&vulnerable_group=PREGNANT&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        risk = res.data['forecast_risk']
        self.assertEqual(risk['status'], RISK_STATUS_AVAILABLE)
        self.assertEqual(res.data['observation_period']['total_cases'], 4)
        expected_bl = round(4 / res.data['observation_period']['weeks_count'], 2)
        self.assertEqual(risk['historical_baseline'], expected_bl)

    # 18. Patient-type risk uses only selected patient type
    def test_18_patient_type_risk_uses_only_selected_patient_type(self):
        """Filtering by patient_type=FOLLOW_UP computes risk baseline only from the 6 follow-up cases."""
        res = self.client.get(f"{self.url}?disease=Dengue&patient_type=FOLLOW_UP&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        risk = res.data['forecast_risk']
        self.assertEqual(risk['status'], RISK_STATUS_AVAILABLE)
        self.assertEqual(res.data['observation_period']['total_cases'], 6)
        expected_bl = round(6 / res.data['observation_period']['weeks_count'], 2)
        self.assertEqual(risk['historical_baseline'], expected_bl)

    # 19. Age + gender uses AND semantics
    def test_19_age_plus_gender_uses_and_semantics(self):
        """Combined age_group=15-24 and gender=FEMALE matches only records satisfying both."""
        res = self.client.get(f"{self.url}?disease=Dengue&age_group=15-24&gender=FEMALE&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['observation_period']['total_cases'], 4)
        self.assertEqual(res.data['forecast_risk']['status'], RISK_STATUS_AVAILABLE)

    # 20. Age + gender + severity uses AND semantics
    def test_20_age_plus_gender_plus_severity_uses_and_semantics(self):
        """Combined age_group=15-24, gender=FEMALE, severity=SEVERE matches records satisfying all 3."""
        res = self.client.get(f"{self.url}?disease=Dengue&age_group=15-24&gender=FEMALE&severity=SEVERE&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['observation_period']['total_cases'], 4)
        self.assertEqual(res.data['forecast_risk']['status'], RISK_STATUS_AVAILABLE)

    # 21. Age + gender + vulnerability uses AND semantics
    def test_21_age_plus_gender_plus_vulnerability_uses_and_semantics(self):
        """Combined age_group=15-24, gender=FEMALE, vulnerable_group=PREGNANT matches records satisfying all 3."""
        res = self.client.get(f"{self.url}?disease=Dengue&age_group=15-24&gender=FEMALE&vulnerable_group=PREGNANT&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['observation_period']['total_cases'], 4)
        self.assertEqual(res.data['forecast_risk']['status'], RISK_STATUS_AVAILABLE)

    # 22. Age + gender + patient type uses AND semantics
    def test_22_age_plus_gender_plus_patient_type_uses_and_semantics(self):
        """Combined age_group=15-24, gender=FEMALE, patient_type=FOLLOW_UP matches records satisfying all 3."""
        res = self.client.get(f"{self.url}?disease=Dengue&age_group=15-24&gender=FEMALE&patient_type=FOLLOW_UP&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['observation_period']['total_cases'], 3)
        self.assertEqual(res.data['forecast_risk']['status'], RISK_STATUS_AVAILABLE)

    # 23. All five demographic dimensions use AND semantics
    def test_23_all_five_demographic_dimensions_use_and_semantics(self):
        """Full combination across age, gender, severity, vulnerable_group, and patient_type."""
        url = (
            f"{self.url}?disease=Dengue&age_group=15-24&gender=FEMALE&severity=SEVERE"
            f"&vulnerable_group=PREGNANT&patient_type=FOLLOW_UP&date={self.as_of}&months=12"
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['observation_period']['total_cases'], 3)
        self.assertEqual(res.data['forecast_risk']['status'], RISK_STATUS_AVAILABLE)

    # 24. Risk does not fall back to overall disease baseline
    def test_24_risk_does_not_fall_back_to_overall_disease_baseline(self):
        """
        When overall disease has 15 cases (available), but subgroup age_group=45-59 has only 1 case,
        forecast_risk must be INSUFFICIENT_DATA and must NOT fall back to overall baseline.
        """
        res = self.client.get(f"{self.url}?disease=Dengue&age_group=45-59&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        risk = res.data['forecast_risk']
        self.assertEqual(risk['status'], RISK_STATUS_INSUFFICIENT)
        self.assertIsNone(risk['historical_baseline'])
        self.assertEqual(risk['highest_risk_level'], RISK_LEVEL_INSUFFICIENT)
        self.assertEqual(risk['risk_points'], [])

    # 25. Historical actual values remain unchanged
    def test_25_historical_actual_values_remain_unchanged(self):
        """Historical series continues reflecting actual observed counts."""
        res = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        hist = res.data['historical_series']
        self.assertEqual(sum(w['cases'] for w in hist), 15)

    # 26. Forecast predicted values remain unchanged
    def test_26_forecast_predicted_values_remain_unchanged(self):
        """Forecast predicted values are pure WMA projections and match between forecast and risk points."""
        res = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        f_pts = res.data['forecast']['points']
        r_pts = res.data['forecast_risk']['risk_points']
        self.assertGreater(len(f_pts), 0)
        for f_pt, r_pt in zip(f_pts, r_pts):
            self.assertEqual(f_pt['predicted_cases'], r_pt['predicted_cases'])

    # 27. Risk points correspond exactly to forecast points
    def test_27_risk_points_correspond_exactly_to_forecast_points(self):
        """Risk points align 1:1 with forecast points in count and date bounds."""
        res = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        f_pts = res.data['forecast']['points']
        r_pts = res.data['forecast_risk']['risk_points']
        self.assertEqual(len(f_pts), len(r_pts))
        for f_pt, r_pt in zip(f_pts, r_pts):
            self.assertEqual(f_pt['forecast_week_start'], r_pt['forecast_week_start'])
            self.assertEqual(f_pt['forecast_week_end'], r_pt['forecast_week_end'])

    # 28. Highest risk level precedence works
    def test_28_highest_risk_level_precedence_works(self):
        """Precedence order: HIGH_RISK > ELEVATED > NORMAL > INSUFFICIENT_DATA."""
        hist = [{'cases': 10}, {'cases': 10}, {'cases': 10}]
        # Mixed containing HIGH_RISK -> HIGH_RISK
        pts_high = [{'predicted_cases': 10.0}, {'predicted_cases': 12.0}, {'predicted_cases': 16.0}]
        res_high = calculate_forecast_risk(hist, pts_high)
        self.assertEqual(res_high['highest_risk_level'], RISK_LEVEL_HIGH)

        # Mixed containing ELEVATED -> ELEVATED
        pts_elev = [{'predicted_cases': 10.0}, {'predicted_cases': 12.0}]
        res_elev = calculate_forecast_risk(hist, pts_elev)
        self.assertEqual(res_elev['highest_risk_level'], RISK_LEVEL_ELEVATED)

        # Normal only -> NORMAL
        pts_norm = [{'predicted_cases': 9.0}, {'predicted_cases': 10.0}]
        res_norm = calculate_forecast_risk(hist, pts_norm)
        self.assertEqual(res_norm['highest_risk_level'], RISK_LEVEL_NORMAL)

    # 29. Risk counts reconcile with risk_points
    def test_29_risk_counts_reconcile_with_risk_points(self):
        """Total risk points count equals sum of individual risk level counts."""
        hist = [{'cases': 10}, {'cases': 10}, {'cases': 10}]
        pts = [{'predicted_cases': 10.0}, {'predicted_cases': 12.5}, {'predicted_cases': 16.0}]
        res = calculate_forecast_risk(hist, pts)
        self.assertEqual(res['risk_points_count'], 3)
        self.assertEqual(res['normal_points_count'], 1)
        self.assertEqual(res['elevated_points_count'], 1)
        self.assertEqual(res['high_risk_points_count'], 1)
        self.assertEqual(
            res['normal_points_count'] + res['elevated_points_count'] + res['high_risk_points_count'],
            res['risk_points_count']
        )

    # 30. Hospital Admin cross-facility request returns 403
    def test_30_hospital_admin_cross_facility_returns_403(self):
        """Hospital Admin cannot request risk data for another facility."""
        res = self.client.get(f"{self.url}?disease=Dengue&facility={self.fac_r1.id}")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 31. District Officer cross-district request returns 403
    def test_31_district_officer_cross_district_returns_403(self):
        """District Officer cannot request risk data for a different district."""
        self.client.force_authenticate(user=self.officer_c)
        res = self.client.get(f"{self.url}?disease=Dengue&district={self.district_rural.id}")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # 32. District Officer permitted facility works
    def test_32_district_officer_permitted_facility_works(self):
        """District Officer can request risk data for a hospital within their district."""
        self.client.force_authenticate(user=self.officer_c)
        res = self.client.get(f"{self.url}?disease=Dengue&facility={self.fac_c1.id}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('forecast_risk', res.data)

    # 33. Invalid demographic filters still return HTTP 400
    def test_33_invalid_demographic_filters_return_400(self):
        """Validation rejection: bad parameters return HTTP 400."""
        for param, val in [
            ('age_group', '99-100'),
            ('gender', 'INVALID_GENDER'),
            ('severity', 'CRITICAL'),
            ('vulnerable_group', 'NONEXISTENT'),
            ('patient_type', 'RECURRENT')
        ]:
            res = self.client.get(f"{self.url}?disease=Dengue&{param}={val}")
            self.assertEqual(
                res.status_code, status.HTTP_400_BAD_REQUEST,
                f"Expected 400 for {param}={val}, got {res.status_code}"
            )

    # 34. UNKNOWN public filters still return HTTP 400
    def test_34_unknown_public_filters_return_400(self):
        """UNKNOWN query parameters rejected with HTTP 400."""
        for param in ['age_group', 'gender', 'severity', 'vulnerable_group', 'patient_type']:
            res = self.client.get(f"{self.url}?disease=Dengue&{param}=UNKNOWN")
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # 35. No fake DiseaseCase records are created
    def test_35_no_fake_disease_case_records_created(self):
        """Risk calculation strictly preserves existing DiseaseCase count without creating records."""
        count_before = DiseaseCase.objects.count()
        res = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        count_after = DiseaseCase.objects.count()
        self.assertEqual(count_before, count_after)

    # 36. Query efficiency / no N+1 regression
    def test_36_query_efficiency_no_n_plus_one_regression(self):
        """generate_forecast_summary executes efficiently without N+1 query loops."""
        with self.assertNumQueries(1):
            build_disease_time_series(
                facility_ids=[self.fac_c1.id],
                disease_name='Dengue',
                as_of_date=self.as_of,
                weeks_count=52,
                age_group='15-24',
                gender='FEMALE',
                severity='SEVERE',
                vulnerable_group='PREGNANT',
                patient_type='FOLLOW_UP'
            )

    # 37. Risk calculation is deterministic for the same input
    def test_37_risk_calculation_is_deterministic_for_same_input(self):
        """Identical inputs produce identical risk outputs."""
        hist = [{'cases': 10}, {'cases': 10}, {'cases': 10}]
        pts = [{'predicted_cases': 12.0}]
        r1 = calculate_forecast_risk(hist, pts)
        r2 = calculate_forecast_risk(hist, pts)
        self.assertEqual(r1, r2)

    # 38. Changing demographic filters changes the risk population/baseline appropriately
    def test_38_changing_demographic_filters_changes_risk_baseline_appropriately(self):
        """Filtering by gender=FEMALE produces a different baseline than unfiltered Dengue."""
        res_all = self.client.get(f"{self.url}?disease=Dengue&date={self.as_of}&months=12")
        res_fem = self.client.get(f"{self.url}?disease=Dengue&gender=FEMALE&date={self.as_of}&months=12")
        self.assertNotEqual(
            res_all.data['forecast_risk']['historical_baseline'],
            res_fem.data['forecast_risk']['historical_baseline']
        )

    # 39. Forecast risk is based on the same historical series used by the forecast
    def test_39_forecast_risk_based_on_same_historical_series_used_by_forecast(self):
        """Historical baseline in forecast_risk reconciles exactly with observation_period and historical_series."""
        res = self.client.get(f"{self.url}?disease=Dengue&gender=FEMALE&date={self.as_of}&months=12")
        hist = res.data['historical_series']
        expected_bl = round(sum(w['cases'] for w in hist) / len(hist), 2)
        self.assertEqual(res.data['forecast_risk']['historical_baseline'], expected_bl)

    # 40. Risk calculation does not perform a second broad/unfiltered DiseaseCase query
    def test_40_risk_calculation_does_not_perform_second_unfiltered_query(self):
        """calculate_forecast_risk is a pure computation requiring 0 database queries."""
        hist = [{'cases': 10}, {'cases': 10}, {'cases': 10}]
        pts = [{'predicted_cases': 12.0}]
        with self.assertNumQueries(0):
            calculate_forecast_risk(hist, pts)


