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



