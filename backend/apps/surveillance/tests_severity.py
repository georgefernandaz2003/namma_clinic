"""
Tests for Prompt 4: Severity Analysis in Public Health Intelligence.

Covers all 24 required scenarios:
1. Severity validation.
2. Invalid severity -> HTTP 400.
3. Historical severity counts.
4. All severity categories represented.
5. Zero-count severity categories.
6. UNKNOWN severity handling.
7. Monthly severity trends.
8. Disease + severity filtering.
9. Disease + age + severity filtering.
10. Disease + gender + severity filtering.
11. Disease + age + gender + severity filtering.
12. Facility + severity filtering.
13. District + severity filtering.
14. Unauthorized facility + severity -> 403.
15. Unauthorized district + severity -> 403.
16. Severity age-group matrix.
17. Severity gender matrix.
18. Severity age-gender matrix.
19. Existing historical response fields preserved.
20. Existing demographic response fields preserved.
21. No severity filter preserves existing behavior.
22. Severity counts equal monthly total case counts.
23. Age calculation still uses DiseaseCase.report_date.
24. No N+1 query pattern introduced.
"""

import datetime
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.facilities.models import Facility
from apps.geography.models import District, State, Ward, Zone
from apps.patients.models import Patient
from apps.surveillance.models import DiseaseCase
from apps.surveillance.demographic_services import (
    SEVERITY_MILD,
    SEVERITY_MODERATE,
    SEVERITY_SEVERE,
    SEVERITY_UNKNOWN,
    SEVERITY_CHOICES,
    normalize_severity,
    validate_severity_param,
    build_severity_demographic_matrices,
)
from apps.surveillance.intelligence_services import (
    aggregate_historical_disease,
    calculate_disease_trends,
    aggregate_disease_by_locality,
    aggregate_hospital_level,
    aggregate_district_level,
)

User = get_user_model()


class PublicHealthSeverityTestCase(TestCase):
    """
    Comprehensive tests for Severity Analysis across Public Health Intelligence.
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
            username='sev_admin_c1', password='Password123!', role='HOSPITAL_ADMIN',
            assigned_facility=cls.fac_central_1
        )
        cls.officer_central = User.objects.create_user(
            username='sev_officer_c', password='Password123!', role='DISTRICT_OFFICER',
            assigned_district=cls.district_central
        )
        cls.officer_rural = User.objects.create_user(
            username='sev_officer_r', password='Password123!', role='DISTRICT_OFFICER',
            assigned_district=cls.district_rural
        )

        # Fixed reference date
        cls.as_of = datetime.date(2026, 10, 4)

        # Patients with deterministic demographics
        cls.p_0_5_m = Patient.objects.create(
            patient_id='P-S01', name='Infant Boy',
            date_of_birth=datetime.date(2024, 5, 15), age=2, gender='MALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central_1
        )
        cls.p_6_14_f = Patient.objects.create(
            patient_id='P-S02', name='School Girl',
            date_of_birth=datetime.date(2016, 5, 15), age=10, gender='FEMALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central_1
        )
        cls.p_15_24_f = Patient.objects.create(
            patient_id='P-S03', name='Young Female',
            date_of_birth=datetime.date(2006, 5, 15), age=20, gender='FEMALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central_1
        )
        cls.p_15_24_m = Patient.objects.create(
            patient_id='P-S04', name='Young Male',
            date_of_birth=datetime.date(2008, 5, 15), age=18, gender='MALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central_1
        )
        cls.p_25_44_m = Patient.objects.create(
            patient_id='P-S05', name='Adult Male',
            date_of_birth=datetime.date(1996, 5, 15), age=30, gender='MALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central_1
        )
        cls.p_25_44_f = Patient.objects.create(
            patient_id='P-S06', name='Adult Female',
            date_of_birth=datetime.date(1991, 5, 15), age=35, gender='FEMALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central_1
        )
        cls.p_45_59_o = Patient.objects.create(
            patient_id='P-S07', name='Middle Aged Other',
            date_of_birth=datetime.date(1976, 5, 15), age=50, gender='OTHER',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central_1
        )
        cls.p_60_plus_m = Patient.objects.create(
            patient_id='P-S08', name='Senior Male',
            date_of_birth=datetime.date(1956, 5, 15), age=70, gender='MALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central_1
        )
        cls.p_no_dob = Patient.objects.create(
            patient_id='P-S09', name='Missing DOB Patient',
            date_of_birth=None, age=30, gender='FEMALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central_1
        )
        cls.p_no_gender = Patient.objects.create(
            patient_id='P-S10', name='Missing Gender Patient',
            date_of_birth=datetime.date(2000, 5, 15), age=26, gender='',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central_1
        )
        cls.p_aging = Patient.objects.create(
            patient_id='P-S11', name='Aging Multi-Year Patient',
            date_of_birth=datetime.date(2010, 7, 1), age=16, gender='FEMALE',
            district=cls.district_central, ward=cls.ward_central, registered_at_facility=cls.fac_central_1
        )

        # -----------------------------------------------------------------------
        # Create Historical Disease Cases across 6 calendar months (May - Oct 2026)
        # -----------------------------------------------------------------------
        # May 2026: 1 MILD Dengue case
        cls.c_may_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_0_5_m, facility=cls.fac_central_1,
            ward=cls.ward_central, report_date=datetime.date(2026, 5, 10), severity='MILD'
        )

        # June 2026: 1 MODERATE Dengue case
        cls.c_jun_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_6_14_f, facility=cls.fac_central_1,
            ward=cls.ward_central, report_date=datetime.date(2026, 6, 12), severity='MODERATE'
        )

        # July 2026: 2 SEVERE Dengue cases
        cls.c_jul_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_15_24_f, facility=cls.fac_central_1,
            ward=cls.ward_central, report_date=datetime.date(2026, 7, 15), severity='SEVERE'
        )
        cls.c_jul_2 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_15_24_m, facility=cls.fac_central_1,
            ward=cls.ward_central, report_date=datetime.date(2026, 7, 20), severity='SEVERE'
        )

        # August 2026: 1 MILD, 1 MODERATE Dengue case
        cls.c_aug_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_25_44_f, facility=cls.fac_central_1,
            ward=cls.ward_central, report_date=datetime.date(2026, 8, 10), severity='MILD'
        )
        cls.c_aug_2 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_no_gender, facility=cls.fac_central_1,
            ward=cls.ward_central, report_date=datetime.date(2026, 8, 25), severity='MODERATE'
        )

        # September 2026: 1 SEVERE, 1 MILD, 1 missing severity, 1 invalid severity
        cls.c_sep_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_25_44_m, facility=cls.fac_central_1,
            ward=cls.ward_central, report_date=datetime.date(2026, 9, 5), severity='SEVERE'
        )
        cls.c_sep_2 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_no_dob, facility=cls.fac_central_1,
            ward=cls.ward_central, report_date=datetime.date(2026, 9, 20), severity='MILD'
        )
        cls.c_sep_3_missing_sev = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_45_59_o, facility=cls.fac_central_1,
            ward=cls.ward_central, report_date=datetime.date(2026, 9, 25), severity=''
        )
        cls.c_sep_4_invalid_sev = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_60_plus_m, facility=cls.fac_central_1,
            ward=cls.ward_central, report_date=datetime.date(2026, 9, 28), severity='CRITICAL'
        )

        # October 2026: 1 MODERATE, 1 MILD Dengue case
        cls.c_oct_1 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_45_59_o, facility=cls.fac_central_1,
            ward=cls.ward_central, report_date=datetime.date(2026, 10, 1), severity='MODERATE'
        )
        cls.c_oct_2 = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_60_plus_m, facility=cls.fac_central_1,
            ward=cls.ward_central, report_date=datetime.date(2026, 10, 3), severity='MILD'
        )

        # Multi-facility cases:
        # 1 SEVERE Dengue case at fac_central_2 (in same district)
        cls.c_fac2_dengue = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_25_44_f, facility=cls.fac_central_2,
            ward=cls.ward_central, report_date=datetime.date(2026, 9, 15), severity='SEVERE'
        )

        # Different disease: 1 SEVERE Malaria case at fac_central_1
        cls.c_malaria_severe = DiseaseCase.objects.create(
            disease_name='Malaria', patient=cls.p_0_5_m, facility=cls.fac_central_1,
            ward=cls.ward_central, report_date=datetime.date(2026, 9, 18), severity='SEVERE'
        )

        # Different district: 1 MILD Dengue case at fac_rural
        cls.c_rural_dengue = DiseaseCase.objects.create(
            disease_name='Dengue', patient=cls.p_0_5_m, facility=cls.fac_rural,
            ward=cls.ward_rural, report_date=datetime.date(2026, 9, 15), severity='MILD'
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_central_1)

    # 1. Severity validation utility
    def test_01_severity_validation(self):
        """
        Validates severity parameter values using centralized validation utility.
        """
        for valid_sev in ['MILD', 'MODERATE', 'SEVERE']:
            cleaned, err = validate_severity_param(valid_sev)
            self.assertEqual(cleaned, valid_sev)
            self.assertIsNone(err)

        # Case insensitivity
        cleaned, err = validate_severity_param('mild')
        self.assertEqual(cleaned, 'MILD')
        self.assertIsNone(err)

        # Empty or None -> (None, None)
        self.assertEqual(validate_severity_param(None), (None, None))
        self.assertEqual(validate_severity_param(''), (None, None))
        self.assertEqual(validate_severity_param('   '), (None, None))

        # UNKNOWN cannot be selected as filter
        cleaned, err = validate_severity_param('UNKNOWN')
        self.assertIsNone(cleaned)
        self.assertIn('Invalid severity', err)

        # Unsupported/invalid values
        cleaned, err = validate_severity_param('CRITICAL')
        self.assertIsNone(cleaned)
        self.assertIn('Invalid severity', err)

    # 2. Invalid severity -> HTTP 400
    def test_02_invalid_severity_http_400(self):
        """
        Verifies that querying an invalid severity returns HTTP 400 Bad Request.
        """
        url = reverse('intelligence_historical_disease')

        # Invalid string
        res = self.client.get(f"{url}?disease=Dengue&severity=CRITICAL&date={self.as_of}")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', res.data)

        # UNKNOWN should return 400
        res = self.client.get(f"{url}?disease=Dengue&severity=UNKNOWN&date={self.as_of}")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', res.data)

    # 3. Historical severity counts
    def test_03_historical_severity_counts(self):
        """
        Verifies historical counts grouped by severity across the observation window.
        """
        res = self.client.get(f"{reverse('intelligence_historical_disease')}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('historical_severity', res.data)

        sev_map = {item['severity']: item['total_cases'] for item in res.data['historical_severity']}

        # fac_central_1 Dengue cases:
        # MILD: May(1), Aug(1), Sep(1), Oct(1) = 4
        # MODERATE: Jun(1), Aug(1), Oct(1) = 3
        # SEVERE: Jul(2), Sep(1) = 3
        # UNKNOWN: Sep(2 - missing & invalid) = 2
        self.assertEqual(sev_map['MILD'], 4)
        self.assertEqual(sev_map['MODERATE'], 3)
        self.assertEqual(sev_map['SEVERE'], 3)
        self.assertEqual(sev_map['UNKNOWN'], 2)

    # 4. All severity categories represented
    def test_04_all_severity_categories_represented(self):
        """
        Verifies all supported clinical severities are present in historical_severity.
        """
        res = self.client.get(f"{reverse('intelligence_historical_disease')}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        returned_severities = [item['severity'] for item in res.data['historical_severity']]

        for s in ['MILD', 'MODERATE', 'SEVERE']:
            self.assertIn(s, returned_severities)

    # 5. Zero-count severity categories
    def test_05_zero_count_severity_categories(self):
        """
        Verifies that severity categories with zero cases are still represented with total_cases=0.
        """
        # Create a single test condition with only 1 MILD case
        DiseaseCase.objects.create(
            disease_name='Chikungunya', patient=self.p_0_5_m, facility=self.fac_central_1,
            ward=self.ward_central, report_date=datetime.date(2026, 9, 1), severity='MILD'
        )

        res = self.client.get(f"{reverse('intelligence_historical_disease')}?disease=Chikungunya&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        sev_map = {item['severity']: item['total_cases'] for item in res.data['historical_severity']}

        self.assertEqual(sev_map['MILD'], 1)
        self.assertEqual(sev_map['MODERATE'], 0)
        self.assertEqual(sev_map['SEVERE'], 0)

    # 6. UNKNOWN severity handling
    def test_06_unknown_severity_handling(self):
        """
        Verifies missing, blank, and unsupported severity values are classified as UNKNOWN
        and not silently converted to MILD.
        """
        self.assertEqual(normalize_severity(None), SEVERITY_UNKNOWN)
        self.assertEqual(normalize_severity(''), SEVERITY_UNKNOWN)
        self.assertEqual(normalize_severity('   '), SEVERITY_UNKNOWN)
        self.assertEqual(normalize_severity('CRITICAL'), SEVERITY_UNKNOWN)

        res = self.client.get(f"{reverse('intelligence_historical_disease')}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        sev_map = {item['severity']: item['total_cases'] for item in res.data['historical_severity']}
        self.assertIn('UNKNOWN', sev_map)
        self.assertEqual(sev_map['UNKNOWN'], 2)

    # 7. Monthly severity trends
    def test_07_monthly_severity_trends(self):
        """
        Verifies monthly severity trend structure and counts for each historical month.
        """
        res = self.client.get(f"{reverse('intelligence_historical_disease')}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('monthly_severity_trends', res.data)

        trends = {item['month']: item for item in res.data['monthly_severity_trends']}

        # July 2026: 2 cases, both SEVERE
        self.assertEqual(trends['2026-07']['total_cases'], 2)
        self.assertEqual(trends['2026-07']['severity']['SEVERE'], 2)
        self.assertEqual(trends['2026-07']['severity']['MILD'], 0)
        self.assertEqual(trends['2026-07']['severity']['MODERATE'], 0)
        self.assertEqual(trends['2026-07']['severity']['UNKNOWN'], 0)

        # September 2026: 4 cases (1 MILD, 1 SEVERE, 2 UNKNOWN)
        self.assertEqual(trends['2026-09']['total_cases'], 4)
        self.assertEqual(trends['2026-09']['severity']['MILD'], 1)
        self.assertEqual(trends['2026-09']['severity']['MODERATE'], 0)
        self.assertEqual(trends['2026-09']['severity']['SEVERE'], 1)
        self.assertEqual(trends['2026-09']['severity']['UNKNOWN'], 2)

    # 8. Disease + severity filtering
    def test_08_disease_plus_severity_filtering(self):
        """
        Verifies filtering by disease AND severity concurrently.
        """
        res = self.client.get(f"{reverse('intelligence_historical_disease')}?disease=Dengue&severity=SEVERE&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # 3 SEVERE Dengue cases at fac_central_1
        self.assertEqual(res.data['total_cases_in_history'], 3)
        sev_map = {item['severity']: item['total_cases'] for item in res.data['historical_severity']}
        self.assertEqual(sev_map['SEVERE'], 3)
        self.assertEqual(sev_map['MILD'], 0)
        self.assertEqual(sev_map['MODERATE'], 0)

    # 9. Disease + age + severity filtering
    def test_09_disease_plus_age_plus_severity_filtering(self):
        """
        Verifies filtering by disease AND age_group AND severity.
        """
        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Dengue&age_group=15-24&severity=SEVERE&date={self.as_of}&months=6"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # 2 cases in July: p_15_24_f and p_15_24_m
        self.assertEqual(res.data['total_cases_in_history'], 2)

    # 10. Disease + gender + severity filtering
    def test_10_disease_plus_gender_plus_severity_filtering(self):
        """
        Verifies filtering by disease AND gender AND severity.
        """
        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Dengue&gender=FEMALE&severity=SEVERE&date={self.as_of}&months=6"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # 1 case in July: p_15_24_f
        self.assertEqual(res.data['total_cases_in_history'], 1)

    # 11. Disease + age + gender + severity filtering
    def test_11_disease_plus_age_plus_gender_plus_severity_filtering(self):
        """
        Verifies filtering by disease AND age_group AND gender AND severity.
        """
        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?disease=Dengue&age_group=15-24&gender=MALE&severity=SEVERE&date={self.as_of}&months=6"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # 1 case in July: p_15_24_m
        self.assertEqual(res.data['total_cases_in_history'], 1)

    # 12. Facility + severity filtering
    def test_12_facility_plus_severity_filtering(self):
        """
        Verifies facility scoping combined with severity filtering for a District Officer.
        """
        self.client.force_authenticate(user=self.officer_central)

        # fac_central_1 has 3 SEVERE Dengue cases
        res1 = self.client.get(
            f"{reverse('intelligence_historical_disease')}?facility={self.fac_central_1.id}&disease=Dengue&severity=SEVERE&date={self.as_of}&months=6"
        )
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(res1.data['total_cases_in_history'], 3)

        # fac_central_2 has 1 SEVERE Dengue case
        res2 = self.client.get(
            f"{reverse('intelligence_historical_disease')}?facility={self.fac_central_2.id}&disease=Dengue&severity=SEVERE&date={self.as_of}&months=6"
        )
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data['total_cases_in_history'], 1)

    # 13. District + severity filtering
    def test_13_district_plus_severity_filtering(self):
        """
        Verifies district scoping combined with severity filtering returns all cases across facilities in district.
        """
        self.client.force_authenticate(user=self.officer_central)

        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?district={self.district_central.id}&disease=Dengue&severity=SEVERE&date={self.as_of}&months=6"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # 3 cases at fac_central_1 + 1 case at fac_central_2 = 4 SEVERE cases in central district
        self.assertEqual(res.data['total_cases_in_history'], 4)

    # 14. Unauthorized facility + severity -> 403
    def test_14_unauthorized_facility_plus_severity_403(self):
        """
        Verifies that Hospital Admin cannot access another facility even when severity filter is supplied.
        """
        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?facility={self.fac_central_2.id}&severity=SEVERE&date={self.as_of}"
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', res.data)

    # 15. Unauthorized district + severity -> 403
    def test_15_unauthorized_district_plus_severity_403(self):
        """
        Verifies that District Officer cannot access another district even when severity filter is supplied.
        """
        self.client.force_authenticate(user=self.officer_rural)

        res = self.client.get(
            f"{reverse('intelligence_historical_disease')}?district={self.district_central.id}&severity=SEVERE&date={self.as_of}"
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', res.data)

    # 16. Severity age-group matrix
    def test_16_severity_age_group_matrix(self):
        """
        Verifies the cross-analysis matrix between severity and age groups.
        """
        res = self.client.get(f"{reverse('intelligence_historical_disease')}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('severity_age_groups', res.data)

        sag = res.data['severity_age_groups']

        # SEVERE age distribution: 15-24: 2, 25-44: 1
        self.assertEqual(sag['SEVERE']['15-24'], 2)
        self.assertEqual(sag['SEVERE']['25-44'], 1)
        self.assertEqual(sag['SEVERE']['0-5'], 0)

        # MILD age distribution: 0-5: 1, 25-44: 1, 60+: 1, UNKNOWN: 1
        self.assertEqual(sag['MILD']['0-5'], 1)
        self.assertEqual(sag['MILD']['25-44'], 1)
        self.assertEqual(sag['MILD']['60+'], 1)
        self.assertEqual(sag['MILD']['UNKNOWN'], 1)

    # 17. Severity gender matrix
    def test_17_severity_gender_matrix(self):
        """
        Verifies the cross-analysis matrix between severity and gender.
        """
        res = self.client.get(f"{reverse('intelligence_historical_disease')}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('severity_gender', res.data)

        sg = res.data['severity_gender']

        # SEVERE gender distribution: MALE: 2 (p_15_24_m, p_25_44_m), FEMALE: 1 (p_15_24_f), OTHER: 0
        self.assertEqual(sg['SEVERE']['MALE'], 2)
        self.assertEqual(sg['SEVERE']['FEMALE'], 1)
        self.assertEqual(sg['SEVERE']['OTHER'], 0)

        # MODERATE gender distribution: FEMALE: 1 (p_6_14_f), OTHER: 1 (p_45_59_o), UNKNOWN: 1 (p_no_gender)
        self.assertEqual(sg['MODERATE']['FEMALE'], 1)
        self.assertEqual(sg['MODERATE']['OTHER'], 1)
        self.assertEqual(sg['MODERATE']['UNKNOWN'], 1)

    # 18. Severity age-gender matrix
    def test_18_severity_age_gender_matrix(self):
        """
        Verifies the 3-dimensional severity -> age_group -> gender matrix.
        """
        res = self.client.get(f"{reverse('intelligence_historical_disease')}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('severity_age_gender', res.data)

        sag = res.data['severity_age_gender']

        # SEVERE -> 15-24 -> MALE: 1, FEMALE: 1
        self.assertEqual(sag['SEVERE']['15-24']['MALE'], 1)
        self.assertEqual(sag['SEVERE']['15-24']['FEMALE'], 1)
        self.assertEqual(sag['SEVERE']['15-24']['OTHER'], 0)

        # SEVERE -> 25-44 -> MALE: 1, FEMALE: 0
        self.assertEqual(sag['SEVERE']['25-44']['MALE'], 1)
        self.assertEqual(sag['SEVERE']['25-44']['FEMALE'], 0)

    # 19. Existing historical response fields preserved
    def test_19_existing_historical_response_fields_preserved(self):
        """
        Backward compatibility check: all historical intelligence fields must remain intact.
        """
        res = self.client.get(f"{reverse('intelligence_historical_disease')}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        for expected_field in [
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
            'severity_breakdown'
        ]:
            self.assertIn(expected_field, res.data, f"Field '{expected_field}' missing from historical response.")

    # 20. Existing demographic response fields preserved
    def test_20_existing_demographic_response_fields_preserved(self):
        """
        Backward compatibility check: demographic fields from Prompt 3 remain intact.
        """
        res = self.client.get(f"{reverse('intelligence_historical_disease')}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        for expected_field in [
            'historical_age_groups',
            'historical_gender',
            'age_gender_matrix',
            'monthly_demographic_trends'
        ]:
            self.assertIn(expected_field, res.data, f"Field '{expected_field}' missing from historical response.")

    # 21. No severity filter preserves existing behavior
    def test_21_no_severity_filter_preserves_existing_behavior(self):
        """
        When severity is omitted, all severities are included without filtering.
        """
        res = self.client.get(f"{reverse('intelligence_historical_disease')}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # 12 total Dengue cases at fac_central_1
        self.assertEqual(res.data['total_cases_in_history'], 12)

    # 22. Severity counts equal monthly total case counts
    def test_22_severity_counts_equal_monthly_total_case_counts(self):
        """
        Verifies that for every month, the sum of severity counts equals total_cases.
        """
        res = self.client.get(f"{reverse('intelligence_historical_disease')}?disease=Dengue&date={self.as_of}&months=6")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        trends = res.data['monthly_severity_trends']
        for month_entry in trends:
            sev_dict = month_entry['severity']
            sum_severities = sum(sev_dict.values())
            self.assertEqual(
                sum_severities,
                month_entry['total_cases'],
                f"Month {month_entry['month']} sum of severities {sum_severities} != total_cases {month_entry['total_cases']}"
            )

    # 23. Age calculation still uses DiseaseCase.report_date
    def test_23_age_calculation_uses_disease_case_report_date(self):
        """
        Verifies that patient age is calculated relative to each individual DiseaseCase.report_date.
        """
        # p_aging was born 2010-07-01:
        # On 2024-07-01 (report_date) age was 14 -> 6-14 age group
        # On 2026-07-01 (report_date) age was 16 -> 15-24 age group
        c_early = DiseaseCase.objects.create(
            disease_name='Typhoid', patient=self.p_aging, facility=self.fac_central_1,
            ward=self.ward_central, report_date=datetime.date(2024, 7, 1), severity='MODERATE'
        )
        c_late = DiseaseCase.objects.create(
            disease_name='Typhoid', patient=self.p_aging, facility=self.fac_central_1,
            ward=self.ward_central, report_date=datetime.date(2026, 7, 1), severity='SEVERE'
        )

        sag, sg, sag_3d = build_severity_demographic_matrices([c_early, c_late])

        # c_early should be MODERATE in 6-14
        self.assertEqual(sag['MODERATE']['6-14'], 1)
        self.assertEqual(sag['MODERATE']['15-24'], 0)

        # c_late should be SEVERE in 15-24
        self.assertEqual(sag['SEVERE']['15-24'], 1)
        self.assertEqual(sag['SEVERE']['6-14'], 0)

    # 24. No N+1 query pattern introduced
    def test_24_no_n_plus_one_query_pattern(self):
        """
        Verifies that historical severity aggregation does not execute an N+1 query loop per case/patient.
        """
        # With 12 cases in the database, aggregation should execute strictly 1 query using select_related('patient')
        with self.assertNumQueries(1):
            aggregate_historical_disease(
                facility_ids=[self.fac_central_1.id],
                disease_name='Dengue',
                months=6,
                as_of_date=self.as_of
            )
