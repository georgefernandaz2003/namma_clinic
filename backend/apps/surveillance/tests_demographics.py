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
)
from apps.surveillance.intelligence_services import calculate_disease_trends

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


