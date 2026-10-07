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

    def test_fallback_to_patient_age_when_dob_missing(self):
        """
        When date_of_birth is None or blank string, safely falls back to fallback_age.
        """
        # None DOB with valid fallback
        age1 = calculate_age(date_of_birth=None, fallback_age=32, reference_date=self.ref_date)
        self.assertEqual(age1, 32)
        self.assertEqual(get_age_group(age1), AGE_GROUP_25_44)

        # Blank string DOB with valid fallback
        age2 = calculate_age(date_of_birth="", fallback_age=12, reference_date=self.ref_date)
        self.assertEqual(age2, 12)
        self.assertEqual(get_age_group(age2), AGE_GROUP_6_14)

    def test_invalid_future_dob_safely_falls_back(self):
        """
        A date of birth in the future (after reference_date) is invalid.
        It must safely fall back to fallback_age, or return None if fallback_age is missing.
        """
        future_dob = datetime.date(2030, 1, 1)
        # Future DOB with fallback
        age_with_fallback = calculate_age(date_of_birth=future_dob, fallback_age=42, reference_date=self.ref_date)
        self.assertEqual(age_with_fallback, 42)
        self.assertEqual(get_age_group(age_with_fallback), AGE_GROUP_25_44)

        # Future DOB without fallback
        age_no_fallback = calculate_age(date_of_birth=future_dob, fallback_age=None, reference_date=self.ref_date)
        self.assertIsNone(age_no_fallback)
        self.assertEqual(get_age_group(age_no_fallback), AGE_GROUP_UNKNOWN)

    def test_invalid_string_dob_safely_falls_back(self):
        """
        Unparseable date string falls back to fallback_age or returns None.
        """
        age = calculate_age(date_of_birth="not-a-valid-date", fallback_age=50, reference_date=self.ref_date)
        self.assertEqual(age, 50)
        self.assertEqual(get_age_group(age), AGE_GROUP_45_59)

        age_none = calculate_age(date_of_birth="not-a-valid-date", fallback_age=None, reference_date=self.ref_date)
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

    def test_gender_normalization_and_validation(self):
        """
        Tests existing application gender values (MALE, FEMALE, OTHER) and safe UNKNOWN fallback.
        """
        # Exact valid enum values
        self.assertEqual(normalize_gender('MALE'), GENDER_MALE)
        self.assertEqual(normalize_gender('FEMALE'), GENDER_FEMALE)
        self.assertEqual(normalize_gender('OTHER'), GENDER_OTHER)

        # Case-insensitivity & whitespace
        self.assertEqual(normalize_gender(' male '), GENDER_MALE)
        self.assertEqual(normalize_gender('female'), GENDER_FEMALE)
        self.assertEqual(normalize_gender('Other'), GENDER_OTHER)

        # Missing / blank values
        self.assertEqual(normalize_gender(None), GENDER_UNKNOWN)
        self.assertEqual(normalize_gender(''), GENDER_UNKNOWN)
        self.assertEqual(normalize_gender('   '), GENDER_UNKNOWN)

        # Invalid / unknown choices
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

        # Patient without DOB falls back to age
        serializer_nodob = DiseaseCaseSerializer(self.case_fever_nodob)
        data_nodob = serializer_nodob.data
        self.assertEqual(data_nodob['patient_age'], 40)
        self.assertEqual(data_nodob['patient_age_group'], AGE_GROUP_25_44)
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
        self.assertEqual(summary['age_groups'][AGE_GROUP_25_44], 2)  # Adult (35) + No DOB (40)
        self.assertEqual(summary['age_groups'][AGE_GROUP_45_59], 1)  # Middle (52)
        self.assertEqual(summary['age_groups'][AGE_GROUP_60_PLUS], 1)# Senior (68)
        self.assertEqual(summary['age_groups'][AGE_GROUP_UNKNOWN], 1)# Unknown (-1)

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
        self.assertEqual(female_adults.count(), 2) # p_adult (35 F) and p_no_dob (40 F)

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

        # 25-44 has 2 FEMALE (p_adult and p_no_dob)
        self.assertEqual(matrix[AGE_GROUP_25_44][GENDER_FEMALE], 2)

        # 45-59 has 1 OTHER
        self.assertEqual(matrix[AGE_GROUP_45_59][GENDER_OTHER], 1)

        # 60+ has 1 MALE
        self.assertEqual(matrix[AGE_GROUP_60_PLUS][GENDER_MALE], 1)

        # UNKNOWN has 1 UNKNOWN gender
        self.assertEqual(matrix[AGE_GROUP_UNKNOWN][GENDER_UNKNOWN], 1)

