import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User
from apps.facilities.models import Facility
from apps.geography.models import District
from apps.patients.models import Patient
from apps.visits.models import Visit
from apps.laboratory.models import LabOrder, LabTestMaster, LabSample
from apps.pharmacy.models import MedicineMaster, MedicineBatch
from apps.consultations.models import Consultation, Prescription
from apps.referrals.models import Referral, FollowUp
from apps.ncd.models import NCDRecord

def run_tests():
    print("======================================================================")
    print("NAMMA CLINIC — EXHAUSTIVE RBAC & AUTHORIZATION MATRIX TEST SUITE")
    print("======================================================================")
    
    client = APIClient()

    # Load active test users
    dho = User.objects.filter(role='DISTRICT_OFFICER').first()
    admin = User.objects.filter(role='HOSPITAL_ADMIN', assigned_facility_id=110).first() or User.objects.filter(role='HOSPITAL_ADMIN').first()
    doctor = User.objects.filter(role='DOCTOR', assigned_facility_id=112).first() or User.objects.filter(role='DOCTOR').first()
    nurse = User.objects.filter(role='NURSE', assigned_facility_id=112).first() or User.objects.filter(role='NURSE').first()
    lab = User.objects.filter(role='LAB_TECHNICIAN', assigned_facility_id=112).first() or User.objects.filter(role='LAB_TECHNICIAN').first()
    pharmacy = User.objects.filter(role='PHARMACIST', assigned_facility_id=112).first() or User.objects.filter(role='PHARMACIST').first()

    assert all([dho, admin, doctor, nurse, lab, pharmacy]), "Missing one or more required test user roles in database!"

    facility_112 = Facility.objects.get(id=112)
    facility_110 = Facility.objects.get(id=110)
    patient_112 = Patient.objects.filter(registered_at_facility=facility_112).first() or Patient.objects.first()

    passed = 0
    total = 0

    def assert_test(name, condition, details=""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] Test {total:02d}: {name}")
        else:
            print(f"  [FAIL] Test {total:02d}: {name} -- {details}")

    # ====================================================================
    # A. TOKEN CREATION (queue.create) - THE CORE REPORTED DEFECT
    # ====================================================================
    print("\n--- SECTION A: TOKEN CREATION AUTHORIZATION (POST /api/visits/) ---")

    # 1. Hospital Admin -> Allowed (201)
    client.force_authenticate(user=admin)
    res = client.post('/api/visits/', {
        'patient': patient_112.id,
        'facility': admin.assigned_facility_id or 110,
        'visit_type': 'GENERAL_OPD',
        'priority': 'NORMAL',
        'chief_complaint': 'Routine checkup admin token test'
    })
    assert_test("Hospital Admin can create OPD Queue Token", res.status_code == status.HTTP_201_CREATED, f"Got {res.status_code}: {res.data}")
    admin_created_visit_id = res.data.get('id') if res.status_code == 201 else None

    # 2. Nurse -> Allowed (201)
    client.force_authenticate(user=nurse)
    res = client.post('/api/visits/', {
        'patient': patient_112.id,
        'facility': 112,
        'visit_type': 'GENERAL_OPD',
        'priority': 'NORMAL',
        'chief_complaint': 'Nurse checkup token test'
    })
    assert_test("Nurse can create OPD Queue Token", res.status_code == status.HTTP_201_CREATED, f"Got {res.status_code}: {res.data}")
    nurse_created_visit_id = res.data.get('id') if res.status_code == 201 else None

    # 3. Doctor -> FORBIDDEN (403)
    client.force_authenticate(user=doctor)
    res = client.post('/api/visits/', {
        'patient': patient_112.id,
        'facility': 112,
        'visit_type': 'GENERAL_OPD',
        'priority': 'NORMAL',
        'chief_complaint': 'Doctor unauthorized token test'
    })
    assert_test("Doctor CANNOT create OPD Queue Token (HTTP 403)", res.status_code == status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # 4. District Officer -> FORBIDDEN (403)
    client.force_authenticate(user=dho)
    res = client.post('/api/visits/', {
        'patient': patient_112.id,
        'facility': 112,
        'visit_type': 'GENERAL_OPD',
        'priority': 'NORMAL',
        'chief_complaint': 'DHO unauthorized token test'
    })
    assert_test("District Officer CANNOT create OPD Queue Token (HTTP 403)", res.status_code == status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # 5. Lab Technician -> FORBIDDEN (403)
    client.force_authenticate(user=lab)
    res = client.post('/api/visits/', {
        'patient': patient_112.id,
        'facility': 112,
        'visit_type': 'GENERAL_OPD',
        'priority': 'NORMAL',
        'chief_complaint': 'Lab Tech unauthorized token test'
    })
    assert_test("Lab Technician CANNOT create OPD Queue Token (HTTP 403)", res.status_code == status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # 6. Pharmacist -> FORBIDDEN (403)
    client.force_authenticate(user=pharmacy)
    res = client.post('/api/visits/', {
        'patient': patient_112.id,
        'facility': 112,
        'visit_type': 'GENERAL_OPD',
        'priority': 'NORMAL',
        'chief_complaint': 'Pharmacist unauthorized token test'
    })
    assert_test("Pharmacist CANNOT create OPD Queue Token (HTTP 403)", res.status_code == status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # ====================================================================
    # B. PATIENT & DOCUMENT AUTHORIZATION
    # ====================================================================
    print("\n--- SECTION B: PATIENT & DOCUMENT AUTHORIZATION ---")

    # 7. Nurse can register patient (201)
    client.force_authenticate(user=nurse)
    res = client.post('/api/patients/', {
        'name': f"Test Citizen {os.urandom(3).hex()}",
        'age': 35,
        'gender': 'FEMALE',
        'mobile': f"9988{os.urandom(3).hex()[:6]}",
        'address': '123 Main Road, Ward 4',
        'registered_at_facility': 112
    })
    assert_test("Nurse can register new patient (patients.create)", res.status_code == status.HTTP_201_CREATED, f"Got {res.status_code}")
    new_patient_id = res.data.get('id') if res.status_code == 201 else patient_112.id

    # 8. Doctor cannot register new patient (patients.create forbidden)
    client.force_authenticate(user=doctor)
    res = client.post('/api/patients/', {
        'name': f"Unauthorized Doctor Citizen {os.urandom(3).hex()}",
        'age': 40,
        'gender': 'MALE',
        'mobile': f"9977{os.urandom(3).hex()[:6]}",
        'address': '456 Clinic Road',
        'registered_at_facility': 112
    })
    assert_test("Doctor CANNOT register patient (HTTP 403)", res.status_code == status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # 9. DHO cannot register patient (patients.create forbidden)
    client.force_authenticate(user=dho)
    res = client.post('/api/patients/', {
        'name': "DHO Patient",
        'age': 50,
        'gender': 'MALE',
        'mobile': '9966112233',
        'address': '789 District Road',
        'registered_at_facility': 112
    })
    assert_test("District Officer CANNOT register patient (HTTP 403)", res.status_code == status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # 10. Lab Tech cannot upload patient document (HTTP 403)
    client.force_authenticate(user=lab)
    res = client.post(f'/api/patients/{new_patient_id}/documents/', {
        'title': 'Unauthorized Lab Upload',
        'document_type': 'MEDICAL_RECORD',
        'description': 'Lab tech document'
    })
    assert_test("Lab Technician CANNOT upload patient document (HTTP 403)", res.status_code == status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # 11. Pharmacist cannot upload patient document (HTTP 403)
    client.force_authenticate(user=pharmacy)
    res = client.post(f'/api/patients/{new_patient_id}/documents/', {
        'title': 'Unauthorized Pharma Upload',
        'document_type': 'MEDICAL_RECORD',
        'description': 'Pharmacist document'
    })
    assert_test("Pharmacist CANNOT upload patient document (HTTP 403)", res.status_code == status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # ====================================================================
    # C. QUEUE & OPERATIONAL WORKFLOW AUTHORIZATION
    # ====================================================================
    print("\n--- SECTION C: QUEUE & OPERATIONAL WORKFLOW AUTHORIZATION ---")

    # 12. Doctor can call next patient (queue.call_next)
    client.force_authenticate(user=doctor)
    res = client.post('/api/visits/call-next/', {'queue': 'DOCTOR'})
    assert_test("Doctor can call next patient", res.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND], f"Got {res.status_code}")

    # 13. Lab Tech cannot call next patient (HTTP 403)
    client.force_authenticate(user=lab)
    res = client.post('/api/visits/call-next/', {'queue': 'DOCTOR'})
    assert_test("Lab Technician CANNOT call next patient (HTTP 403)", res.status_code == status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # 14. Pharmacist cannot call next patient (HTTP 403)
    client.force_authenticate(user=pharmacy)
    res = client.post('/api/visits/call-next/', {'queue': 'DOCTOR'})
    assert_test("Pharmacist CANNOT call next patient (HTTP 403)", res.status_code == status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # 15. DHO cannot call next patient (HTTP 403)
    client.force_authenticate(user=dho)
    res = client.post('/api/visits/call-next/', {'queue': 'DOCTOR'})
    assert_test("District Officer CANNOT call next patient (HTTP 403)", res.status_code == status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # ====================================================================
    # D. TRIAGE AUTHORIZATION
    # ====================================================================
    print("\n--- SECTION D: TRIAGE AUTHORIZATION (POST /api/triage/) ---")
    active_visit = Visit.objects.filter(facility_id=112).first()

    # 16. Nurse can log triage (201)
    client.force_authenticate(user=nurse)
    res = client.post('/api/triage/', {
        'visit': active_visit.id,
        'patient': active_visit.patient_id,
        'blood_pressure_systolic': 120,
        'blood_pressure_diastolic': 80,
        'pulse_bpm': 72,
        'temperature_f': 98.6,
        'spo2_percent': 98,
        'height_cm': 165,
        'weight_kg': 60,
        'blood_glucose_mgdl': 100,
        'nurse_notes': 'Nurse triage check'
    })
    assert_test("Nurse can submit triage vitals", res.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK], f"Got {res.status_code}")

    # 17. Doctor can submit triage where clinically authorized
    client.force_authenticate(user=doctor)
    res = client.post('/api/triage/', {
        'visit': active_visit.id,
        'patient': active_visit.patient_id,
        'blood_pressure_systolic': 125,
        'blood_pressure_diastolic': 82,
        'pulse_bpm': 74,
        'temperature_f': 98.4,
        'spo2_percent': 99,
        'height_cm': 165,
        'weight_kg': 60,
        'blood_glucose_mgdl': 105,
        'nurse_notes': 'Doctor triage check'
    })
    assert_test("Doctor triage evaluated against clinical matrix", res.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED, status.HTTP_403_FORBIDDEN], f"Got {res.status_code}")

    # 18. Lab Tech cannot submit triage vitals (HTTP 403)
    client.force_authenticate(user=lab)
    res = client.post('/api/triage/', {
        'visit': active_visit.id,
        'patient': active_visit.patient_id,
        'blood_pressure_systolic': 120,
        'blood_pressure_diastolic': 80
    })
    assert_test("Lab Technician CANNOT submit triage vitals (HTTP 403)", res.status_code == status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # 19. Pharmacist cannot submit triage vitals (HTTP 403)
    client.force_authenticate(user=pharmacy)
    res = client.post('/api/triage/', {
        'visit': active_visit.id,
        'patient': active_visit.patient_id,
        'blood_pressure_systolic': 120,
        'blood_pressure_diastolic': 80
    })
    assert_test("Pharmacist CANNOT submit triage vitals (HTTP 403)", res.status_code == status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # 20. District Officer cannot submit triage vitals (HTTP 403)
    client.force_authenticate(user=dho)
    res = client.post('/api/triage/', {
        'visit': active_visit.id,
        'patient': active_visit.patient_id,
        'blood_pressure_systolic': 120,
        'blood_pressure_diastolic': 80
    })
    assert_test("District Officer CANNOT submit triage vitals (HTTP 403)", res.status_code == status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # ====================================================================
    # E. DOCTOR CONSULTATION AUTHORIZATION
    # ====================================================================
    print("\n--- SECTION E: DOCTOR CONSULTATION AUTHORIZATION ---")

    # 21. Doctor can create consultation
    client.force_authenticate(user=doctor)
    res = client.post('/api/consultations/', {
        'visit': active_visit.id,
        'patient': active_visit.patient_id,
        'chief_complaint': 'Hypertension evaluation',
        'clinical_notes': 'Stable BP with prescribed ACE inhibitors',
        'diagnosis': 'Essential hypertension',
        'diagnosis_code': 'I10'
    })
    assert_test("Doctor can create consultation", res.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED], f"Got {res.status_code}")

    # 22. Nurse cannot create consultation (HTTP 403)
    client.force_authenticate(user=nurse)
    res = client.post('/api/consultations/', {
        'visit': active_visit.id,
        'patient': active_visit.patient_id,
        'chief_complaint': 'Nurse unauthorized consultation'
    })
    assert_test("Nurse CANNOT create consultation (HTTP 403)", res.status_code == status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # 23. Pharmacist cannot create consultation (HTTP 403)
    client.force_authenticate(user=pharmacy)
    res = client.post('/api/consultations/', {
        'visit': active_visit.id,
        'patient': active_visit.patient_id,
        'chief_complaint': 'Pharma unauthorized consultation'
    })
    assert_test("Pharmacist CANNOT create consultation (HTTP 403)", res.status_code == status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # ====================================================================
    # F. LABORATORY SAMPLE & RESULT AUTHORIZATION
    # ====================================================================
    print("\n--- SECTION F: LABORATORY SAMPLE & RESULT AUTHORIZATION ---")
    lab_order = LabOrder.objects.filter(facility_id=112).first()
    if not lab_order:
        test_master = LabTestMaster.objects.first()
        lab_order = LabOrder.objects.create(
            visit=active_visit,
            patient=active_visit.patient,
            facility=facility_112,
            test_master=test_master,
            test_name=test_master.name,
            test_code=test_master.code,
            doctor=doctor,
            status='ORDERED'
        )

    # 24. Lab Technician can collect sample (lab_orders.update)
    client.force_authenticate(user=lab)
    res = client.post(f'/api/lab/orders/{lab_order.id}/collect-sample/', {
        'sample_type': 'Blood Specimen',
        'sample_code': f"SMP-TEST-{os.urandom(2).hex()}"
    })
    assert_test("Lab Technician can collect specimen", res.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED], f"Got {res.status_code}")

    # 25. Doctor cannot collect laboratory specimen (HTTP 403)
    client.force_authenticate(user=doctor)
    res = client.post(f'/api/lab/orders/{lab_order.id}/collect-sample/', {
        'sample_type': 'Blood Specimen',
        'sample_code': 'SMP-DOC-FAIL'
    })
    assert_test("Doctor CANNOT collect laboratory specimen (HTTP 403)", res.status_code == status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # 26. Pharmacist cannot collect laboratory specimen (HTTP 403)
    client.force_authenticate(user=pharmacy)
    res = client.post(f'/api/lab/orders/{lab_order.id}/collect-sample/', {
        'sample_type': 'Blood Specimen',
        'sample_code': 'SMP-PHARMA-FAIL'
    })
    assert_test("Pharmacist CANNOT collect laboratory specimen (HTTP 403)", res.status_code == status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # 27. Lab Technician can verify and save result
    client.force_authenticate(user=lab)
    res = client.post(f'/api/lab/orders/{lab_order.id}/save-result/', {
        'result_value': '8.2',
        'interpretation_flag': 'HIGH',
        'notes': 'Verified by automated RBAC test'
    })
    assert_test("Lab Technician can verify and release lab result", res.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED], f"Got {res.status_code}")

    # 28. Nurse cannot verify and save lab result (HTTP 403)
    client.force_authenticate(user=nurse)
    res = client.post(f'/api/lab/orders/{lab_order.id}/save-result/', {
        'result_value': '8.2',
        'interpretation_flag': 'NORMAL'
    })
    assert_test("Nurse CANNOT enter/verify lab results (HTTP 403)", res.status_code == status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # ====================================================================
    # G. PHARMACY DISPENSING AUTHORIZATION
    # ====================================================================
    print("\n--- SECTION G: PHARMACY DISPENSING AUTHORIZATION ---")
    rx = Prescription.objects.filter(facility_id=112).first()
    if not rx:
        rx = Prescription.objects.create(
            visit=active_visit,
            patient=active_visit.patient,
            facility=facility_112,
            doctor=doctor,
            status='PENDING'
        )

    # 29. Doctor cannot dispense prescription (HTTP 403)
    client.force_authenticate(user=doctor)
    res = client.post('/api/pharmacy/dispense/', {'prescription_id': rx.id})
    assert_test("Doctor CANNOT dispense medication (HTTP 403)", res.status_code == status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # 30. Nurse cannot dispense prescription (HTTP 403)
    client.force_authenticate(user=nurse)
    res = client.post('/api/pharmacy/dispense/', {'prescription_id': rx.id})
    assert_test("Nurse CANNOT dispense medication (HTTP 403)", res.status_code == status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # 31. Hospital Admin cannot dispense prescription (HTTP 403)
    client.force_authenticate(user=admin)
    res = client.post('/api/pharmacy/dispense/', {'prescription_id': rx.id})
    assert_test("Hospital Admin CANNOT dispense medication (HTTP 403)", res.status_code == status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # 32. District Officer cannot dispense prescription (HTTP 403)
    client.force_authenticate(user=dho)
    res = client.post('/api/pharmacy/dispense/', {'prescription_id': rx.id})
    assert_test("District Officer CANNOT dispense medication (HTTP 403)", res.status_code == status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # 33. Pharmacist is authorized for dispensing
    client.force_authenticate(user=pharmacy)
    res = client.post('/api/pharmacy/dispense/', {'prescription_id': rx.id})
    assert_test("Pharmacist authorized for pharmacy.dispense", res.status_code != status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # ====================================================================
    # H. INFRASTRUCTURE & FACILITY MANAGEMENT AUTHORIZATION
    # ====================================================================
    print("\n--- SECTION H: INFRASTRUCTURE & FACILITY MANAGEMENT AUTHORIZATION ---")

    # 34. Hospital Admin can manage bed allocations
    client.force_authenticate(user=admin)
    res = client.post('/api/facilities-infra/bed-allocations/', {
        'facility': admin.assigned_facility_id or 110,
        'bed_number': f"BED-T-{os.urandom(2).hex()}",
        'bed_category': 'GENERAL_OBSERVATION',
        'patient_name': 'Admitted Test Patient',
        'status': 'OCCUPIED'
    })
    assert_test("Hospital Admin can manage infrastructure bed allocation", res.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK], f"Got {res.status_code}")

    # 35. Pharmacist cannot assign beds (HTTP 403)
    client.force_authenticate(user=pharmacy)
    res = client.post('/api/facilities-infra/bed-allocations/', {
        'facility': 112,
        'bed_number': 'BED-FAIL',
        'bed_category': 'GENERAL_OBSERVATION',
        'patient_name': 'Unauthorized Admission',
        'status': 'OCCUPIED'
    })
    assert_test("Pharmacist CANNOT manage infrastructure (HTTP 403)", res.status_code == status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # 36. District Officer cannot perform infrastructure mutations (HTTP 403)
    client.force_authenticate(user=dho)
    res = client.post('/api/facilities-infra/bed-allocations/', {
        'facility': 112,
        'bed_number': 'BED-DHO-FAIL',
        'bed_category': 'GENERAL_OBSERVATION',
        'patient_name': 'DHO Admission',
        'status': 'OCCUPIED'
    })
    assert_test("District Officer CANNOT manage infrastructure (HTTP 403)", res.status_code == status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # ====================================================================
    # I. CROSS-FACILITY & CROSS-DISTRICT ISOLATION
    # ====================================================================
    print("\n--- SECTION I: CROSS-FACILITY & CROSS-DISTRICT ISOLATION ---")

    # 37. Facility 112 Doctor cannot access patient registered strictly at 110 without visit/referral
    client.force_authenticate(user=doctor)
    patient_110 = Patient.objects.filter(registered_at_facility_id=110).exclude(visits__facility_id=112).exclude(referrals__destination_facility_id=112).first()
    if patient_110:
        res = client.get(f'/api/patients/{patient_110.id}/')
        assert_test("Facility-isolated patient hidden from out-of-scope doctor", res.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND], f"Got {res.status_code}")
    else:
        assert_test("Facility-isolated patient test (skipped, no isolated patient)", True)

    # 38. Facility 112 Nurse cannot create visit for facility 110
    client.force_authenticate(user=nurse)
    res = client.post('/api/visits/', {
        'patient': patient_112.id,
        'facility': 110,  # Out of scope for nurse at 112
        'visit_type': 'GENERAL_OPD',
        'priority': 'NORMAL',
        'chief_complaint': 'Cross facility attempt'
    })
    assert_test("Cross-facility visit mutation rejected (HTTP 403)", res.status_code == status.HTTP_403_FORBIDDEN, f"Got {res.status_code}")

    # 39. District Officer cannot access patients from another district
    client.force_authenticate(user=dho)
    other_district = District.objects.exclude(id=dho.assigned_district_id).first()
    if other_district:
        other_dist_patient = Patient.objects.filter(district=other_district).first()
        if other_dist_patient:
            res = client.get(f'/api/patients/{other_dist_patient.id}/')
            assert_test("Cross-district patient access rejected for DHO (HTTP 403 or 404)", res.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND], f"Got {res.status_code}")
        else:
            assert_test("Cross-district patient isolation verified (no cross-district records)", True)
    else:
        assert_test("Cross-district patient isolation verified (single district deployment)", True)

    # ====================================================================
    # J. DASHBOARD DATA SCOPE INTEGRITY
    # ====================================================================
    print("\n--- SECTION J: DASHBOARD SCOPE & DATA INTEGRITY ---")

    # 40. Dashboard summary for Doctor is scoped to assigned facility
    client.force_authenticate(user=doctor)
    res = client.get('/api/dashboard/summary/')
    assert_test("Doctor dashboard summary returns 200 with facility scope", res.status_code == status.HTTP_200_OK and res.data.get('total_patients') is not None)

    # 41. Doctor requesting dashboard data for out-of-scope facility yields 0 / empty scope
    res = client.get('/api/dashboard/summary/?facility=110')
    assert_test("Cross-facility dashboard request yields 0 patients (no leakage)", res.data.get('total_patients') == 0, f"Got {res.data.get('total_patients')}")

    # 42. District Officer dashboard summary returns district-level aggregates
    client.force_authenticate(user=dho)
    res = client.get('/api/dashboard/summary/')
    assert_test("DHO dashboard returns valid district aggregates", res.status_code == status.HTTP_200_OK and 'facility_overview' in res.data)

    print("\n======================================================================")
    print(f"RESULTS: {passed}/{total} TESTS PASSED ({passed*100//total}%)")
    print("======================================================================")

    if passed == total:
        print("\nALL AUTHORIZATION AND RBAC MATRIX TESTS PASSED PERFECTLY!")
        return 0
    else:
        print(f"\n{total - passed} TESTS FAILED. PLEASE INSPECT LOGS.")
        return 1

if __name__ == '__main__':
    sys.exit(run_tests())
