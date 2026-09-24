"""
Phase 13 REST API Foundation & Service-Boundary Integration Tests.
Verifies:
1. Authentication (unauthenticated -> 401, inactive user -> 401/403, active staff -> 200).
2. Authorization & Facility Scope (permitted role, forbidden role, facility isolation).
3. IAM API (role assignment, facility transfer via domain services).
4. Visits API (token allocation).
5. Diagnostics API (orders, results, verification, immutability 409, amendment).
6. Pharmacy & Inventory API (read-only batch stock, dispensing, insufficient stock 409, direct patch 405).
7. Procurement API (PO creation, approval, GRN receiving + inventory posting).
8. Follow-Up API (completion validation, mismatch 409).
9. Operational Alerts API (facility isolation).
10. Audit API (read-only admin restricted, non-admin 403).
"""
import datetime
from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.geography.models import State, District, Taluk, Zone, Ward
from apps.facilities.models import Facility, Department
from apps.accounts.models import Person, StaffProfile, User, RoleMaster, StaffRoleAssignment, StaffFacilityAssignment
from apps.patients.models import Patient
from apps.visits.models import Visit
from apps.consultations.models import Consultation, Prescription, PrescriptionItem
from apps.laboratory.models import DiagnosticTestMaster, DiagnosticOrder, Specimen, TestRequest, DiagnosticResult
from apps.pharmacy.models import MedicineMaster, MedicineBatch, InventoryLedger, Vendor, PurchaseOrder, PurchaseOrderItem
from apps.referrals.models import ReferralOrder, FollowUpTask
from apps.alerts.models import OperationalAlert
from apps.audit.models import AuditLogEntry


class Phase13RestAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 1. Geography & Facilities
        self.state = State.objects.create(name="Karnataka", code="KA")
        self.district = District.objects.create(name="Bengaluru Urban", code="KA-BLR", state=self.state)
        self.taluk = Taluk.objects.create(name="Bengaluru East", code="TAL-BLR-E", district=self.district)
        self.zone = Zone.objects.create(name="Mahadevapura Zone", district=self.district)
        self.ward = Ward.objects.create(name="Varthur", ward_number=149, zone=self.zone)

        self.clinic_a = Facility.objects.create(
            facility_code="PHC-VARTHUR", facility_name="Varthur Clinic",
            facility_type="PRIMARY_HEALTH_CENTRE", district=self.district, state=self.state,
            zone=self.zone, ward=self.ward
        )
        self.clinic_b = Facility.objects.create(
            facility_code="PHC-WHITEFIELD", facility_name="Whitefield Clinic",
            facility_type="PRIMARY_HEALTH_CENTRE", district=self.district, state=self.state,
            zone=self.zone, ward=self.ward
        )
        self.dept_opd = Department.objects.create(facility=self.clinic_a, code="OPD", name="Outpatient")

        # 2. Roles
        self.role_admin = RoleMaster.objects.create(code="ADMIN", name="Facility Administrator")
        self.role_doc = RoleMaster.objects.create(code="DOCTOR", name="Medical Officer")
        self.role_nurse = RoleMaster.objects.create(code="NURSE", name="Staff Nurse")

        # 3. Users and Staff Profiles
        # Admin Staff & User
        self.person_admin = Person.objects.create(first_name="Admin", last_name="User", gender="MALE", date_of_birth="1975-01-01")
        self.admin_staff = StaffProfile.objects.create(
            person=self.person_admin, employee_id="ADM-API-1", designation="Hospital Administrator",
            department=self.dept_opd, status="ACTIVE"
        )
        StaffRoleAssignment.objects.create(staff=self.admin_staff, role=self.role_admin, effective_from="2026-01-01", is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.admin_staff, facility=self.clinic_a, is_primary=True, is_active=True)
        self.admin_user = User.objects.create_user(
            username="admin_api", password="password123", email="admin@clinic.org",
            role="ADMIN", assigned_facility=self.clinic_a, staff_profile=self.admin_staff
        )

        # Doctor Staff & User (Assigned to Clinic A)
        self.person_doc = Person.objects.create(first_name="Doctor", last_name="Sharma", gender="MALE", date_of_birth="1980-05-15")
        self.doc_staff = StaffProfile.objects.create(
            person=self.person_doc, employee_id="DOC-API-1", designation="Medical Officer",
            department=self.dept_opd, status="ACTIVE"
        )
        StaffRoleAssignment.objects.create(staff=self.doc_staff, role=self.role_doc, effective_from="2026-01-01", is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.doc_staff, facility=self.clinic_a, is_primary=True, is_active=True)
        self.doc_user = User.objects.create_user(
            username="doc_api", password="password123", email="doc@clinic.org",
            role="DOCTOR", assigned_facility=self.clinic_a, staff_profile=self.doc_staff
        )

        # Nurse Staff & User (Assigned to Clinic A)
        self.person_nurse = Person.objects.create(first_name="Nurse", last_name="Lalitha", gender="FEMALE", date_of_birth="1992-08-20")
        self.nurse_staff = StaffProfile.objects.create(
            person=self.person_nurse, employee_id="NUR-API-1", designation="Staff Nurse",
            department=self.dept_opd, status="ACTIVE"
        )
        StaffRoleAssignment.objects.create(staff=self.nurse_staff, role=self.role_nurse, effective_from="2026-01-01", is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.nurse_staff, facility=self.clinic_a, is_primary=True, is_active=True)
        self.nurse_user = User.objects.create_user(
            username="nurse_api", password="password123", email="nurse@clinic.org",
            role="NURSE", assigned_facility=self.clinic_a, staff_profile=self.nurse_staff
        )

        # Inactive User
        self.inactive_user = User.objects.create_user(
            username="inactive_api", password="password123", is_active=False
        )

        # Patients
        self.patient_a = Patient.objects.create(
            patient_id="PAT-API-A", person=self.person_doc, name="Patient Alpha",
            age=40, gender="MALE", mobile="9800012345", registered_at_facility=self.clinic_a
        )
        self.patient_b = Patient.objects.create(
            patient_id="PAT-API-B", person=self.person_nurse, name="Patient Beta",
            age=25, gender="FEMALE", mobile="9800067890", registered_at_facility=self.clinic_b
        )

        # Visit at Clinic A
        self.visit_a = Visit.objects.create(
            visit_id="VIS-API-A1", patient=self.patient_a, facility=self.clinic_a,
            visit_type="OPD", opd_date=datetime.date.today(), status="IN_CONSULTATION"
        )
        self.completed_visit_a = Visit.objects.create(
            visit_id="VIS-API-A2", patient=self.patient_a, facility=self.clinic_a,
            visit_type="OPD", opd_date=datetime.date.today(), status="COMPLETED"
        )
        self.consultation_a = Consultation.objects.create(
            visit=self.visit_a, patient=self.patient_a, facility=self.clinic_a,
            doctor_staff=self.doc_staff, chief_complaint="Cough & Cold"
        )

    # -------------------------------------------------------------------------
    # 1. AUTHENTICATION TESTS
    # -------------------------------------------------------------------------
    def test_01_unauthenticated_access_rejected_401(self):
        """Unauthenticated requests to protected endpoints return 401."""
        res = self.client.get('/api/v1/patients/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_02_inactive_user_rejected(self):
        """Inactive user credentials cannot perform operations."""
        self.client.force_authenticate(user=self.inactive_user)
        res = self.client.get('/api/v1/patients/')
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_03_authenticated_active_staff_succeeds(self):
        """Active authenticated clinical staff successfully queries API."""
        self.client.force_authenticate(user=self.doc_user)
        res = self.client.get('/api/v1/patients/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    # -------------------------------------------------------------------------
    # 2. AUTHORIZATION & FACILITY SCOPE TESTS
    # -------------------------------------------------------------------------
    def test_04_forbidden_role_for_admin_endpoint_returns_403(self):
        """Ordinary staff nurse cannot assign roles (RBAC 403)."""
        self.client.force_authenticate(user=self.nurse_user)
        payload = {
            "staff": self.doc_staff.id,
            "role": self.role_admin.id,
            "effective_from": str(datetime.date.today())
        }
        res = self.client.post('/api/v1/accounts/role-assignments/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_05_facility_scope_isolation_enforced(self):
        """Clinic A doctor only sees patients registered at Clinic A, not Clinic B."""
        self.client.force_authenticate(user=self.doc_user)
        res = self.client.get('/api/v1/patients/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        returned_ids = [p['id'] for p in res.data['results'] if 'results' in res.data] if 'results' in res.data else [p['id'] for p in res.data]
        self.assertIn(self.patient_a.id, returned_ids)
        self.assertNotIn(self.patient_b.id, returned_ids)

    # -------------------------------------------------------------------------
    # 3. VISITS & TOKEN ALLOCATION API TESTS
    # -------------------------------------------------------------------------
    def test_06_visit_token_allocation_via_service(self):
        """OPD token issuance invokes issue_opd_token service boundary."""
        self.client.force_authenticate(user=self.doc_user)
        res = self.client.post(f'/api/v1/visits/{self.visit_a.id}/issue-opd-token/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('token_number', res.data)
        self.assertEqual(res.data['status'], 'ISSUED')

    # -------------------------------------------------------------------------
    # 4. DIAGNOSTICS REST API TESTS
    # -------------------------------------------------------------------------
    def test_07_diagnostics_order_result_verification_immutability_and_amendment(self):
        """Diagnostic workflow via API: order -> result -> verify -> 409 re-verify -> amend."""
        self.client.force_authenticate(user=self.doc_user)
        test_cbc = DiagnosticTestMaster.objects.create(test_code="CBC-API", test_name="CBC Test", specimen_type="WHOLE_BLOOD")

        # 1. Create Diagnostic Order
        order_payload = {
            "visit": self.visit_a.id,
            "facility": self.clinic_a.id,
            "priority": "ROUTINE",
            "clinical_indication": "Routine workup"
        }
        res_order = self.client.post('/api/v1/diagnostics/orders/', order_payload, format='json')
        self.assertEqual(res_order.status_code, status.HTTP_201_CREATED)
        order_id = res_order.data['id']

        # 2. Create TestRequest
        req_payload = {"diagnostic_order": order_id, "test_master": test_cbc.id}
        res_req = self.client.post('/api/v1/diagnostics/requests/', req_payload, format='json')
        self.assertEqual(res_req.status_code, status.HTTP_201_CREATED)
        req_id = res_req.data['id']

        # 3. Record Result
        res_payload = {"test_request": req_id, "result_value_text": "13.5 g/dL"}
        res_res = self.client.post('/api/v1/diagnostics/results/', res_payload, format='json')
        self.assertEqual(res_res.status_code, status.HTTP_201_CREATED)
        result_id = res_res.data['id']

        # 4. Verify Result
        res_ver = self.client.post(f'/api/v1/diagnostics/results/{result_id}/verify/')
        self.assertEqual(res_ver.status_code, status.HTTP_200_OK)
        self.assertEqual(res_ver.data['status'], 'VERIFIED')

        # 5. Re-verification rejected with 409 Conflict
        res_ver_again = self.client.post(f'/api/v1/diagnostics/results/{result_id}/verify/')
        self.assertEqual(res_ver_again.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("VERIFIED", str(res_ver_again.data))

        # 6. Amend Result
        amend_payload = {"amendment_reason": "Typo correction", "amended_value_text": "13.8 g/dL"}
        res_amend = self.client.post(f'/api/v1/diagnostics/results/{result_id}/amend/', amend_payload, format='json')
        self.assertEqual(res_amend.status_code, status.HTTP_200_OK)
        self.assertEqual(res_amend.data['status'], 'AMENDED')
        self.assertEqual(res_amend.data['result_value_text'], '13.8 g/dL')

    # -------------------------------------------------------------------------
    # 5. PHARMACY & INVENTORY REST API TESTS
    # -------------------------------------------------------------------------
    def test_08_pharmacy_batch_direct_mutation_prohibited_and_dispense_api(self):
        """Direct batch PATCH returns 405; dispensing flows through domain service with 409 guard."""
        self.client.force_authenticate(user=self.doc_user)
        med = MedicineMaster.objects.create(generic_name="Paracetamol", strength="500 mg", dosage_form="Tablet")
        batch = MedicineBatch.objects.create(
            facility=self.clinic_a, medicine=med, batch_number="API-PARA-1",
            expiry_date=datetime.date.today() + datetime.timedelta(days=120),
            quantity=50, available_quantity=50
        )

        # Direct PATCH forbidden (405 Method Not Allowed)
        res_patch = self.client.patch(f'/api/v1/pharmacy/batches/{batch.id}/', {"available_quantity": 999}, format='json')
        self.assertEqual(res_patch.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Create Prescription & Item
        rx = Prescription.objects.create(
            consultation=self.consultation_a, patient=self.patient_a, facility=self.clinic_a, status="VERIFIED"
        )
        item = PrescriptionItem.objects.create(
            prescription=rx, medicine=med, medicine_name="Paracetamol 500mg",
            quantity=100, dispensed_quantity=0, status="PENDING"
        )

        # Dispense Medication via API
        dispense_payload = {
            "prescription_id": rx.id,
            "facility_id": self.clinic_a.id,
            "items": [{"prescription_item_id": item.id, "batch_id": batch.id, "quantity": 20}]
        }
        res_disp = self.client.post('/api/v1/pharmacy/dispensations/', dispense_payload, format='json')
        self.assertEqual(res_disp.status_code, status.HTTP_201_CREATED)

        batch.refresh_from_db()
        self.assertEqual(batch.available_quantity, 30)

        # Insufficient stock returns 409 Conflict
        dispense_too_much = {
            "prescription_id": rx.id,
            "facility_id": self.clinic_a.id,
            "items": [{"prescription_item_id": item.id, "batch_id": batch.id, "quantity": 60}]
        }
        res_fail = self.client.post('/api/v1/pharmacy/dispensations/', dispense_too_much, format='json')
        self.assertEqual(res_fail.status_code, status.HTTP_409_CONFLICT)

    # -------------------------------------------------------------------------
    # 6. PROCUREMENT API TESTS
    # -------------------------------------------------------------------------
    def test_09_procurement_po_approval_and_grn_posting_api(self):
        """Procurement REST endpoints: create PO -> approve -> receive GRN."""
        self.client.force_authenticate(user=self.admin_user)
        vendor = Vendor.objects.create(vendor_name="Pharma Dist KA", facility=self.clinic_a)
        med = MedicineMaster.objects.create(generic_name="Ciprofloxacin", strength="500 mg", dosage_form="Tablet")

        # 1. Create PO
        po_payload = {"facility": self.clinic_a.id, "vendor": vendor.id, "po_number": "PO-API-001"}
        res_po = self.client.post('/api/v1/procurement/purchase-orders/', po_payload, format='json')
        self.assertEqual(res_po.status_code, status.HTTP_201_CREATED)
        po_id = res_po.data['id']

        # 2. Approve PO
        res_app = self.client.post(f'/api/v1/procurement/purchase-orders/{po_id}/approve/', {"approval_tier": 1}, format='json')
        self.assertEqual(res_app.status_code, status.HTTP_200_OK)
        self.assertEqual(res_app.data['status'], 'APPROVED')

        # 3. Receive GRN
        grn_payload = {
            "purchase_order_id": po_id,
            "grn_number": "GRN-API-001",
            "facility_id": self.clinic_a.id,
            "items_received": [{
                "medicine_id": med.id,
                "batch_number": "CIPRO-BATCH-1",
                "expiry_date": str(datetime.date.today() + datetime.timedelta(days=365)),
                "unit_cost": "2.50",
                "quantity_received": 100,
                "quantity_accepted": 100
            }]
        }
        res_grn = self.client.post('/api/v1/procurement/grn/', grn_payload, format='json')
        self.assertEqual(res_grn.status_code, status.HTTP_201_CREATED)

        batch = MedicineBatch.objects.filter(facility=self.clinic_a, batch_number="CIPRO-BATCH-1").first()
        self.assertIsNotNone(batch)
        self.assertEqual(batch.available_quantity, 100)

    # -------------------------------------------------------------------------
    # 7. REFERRALS & FOLLOW-UP API TESTS
    # -------------------------------------------------------------------------
    def test_10_followup_completion_and_mismatch_rejection_api(self):
        """Follow-up completion requires completed visit; mismatch returns 409."""
        self.client.force_authenticate(user=self.doc_user)
        task = FollowUpTask.objects.create(patient=self.patient_a, facility=self.clinic_a, due_date=datetime.date.today())

        # Attempt with in-progress visit -> 409 Conflict
        res_inprog = self.client.post(
            f'/api/v1/referrals/followups/{task.id}/complete/',
            {"completed_in_visit_id": self.visit_a.id}, format='json'
        )
        self.assertEqual(res_inprog.status_code, status.HTTP_409_CONFLICT)

        # Complete with completed visit -> 200 OK
        res_ok = self.client.post(
            f'/api/v1/referrals/followups/{task.id}/complete/',
            {"completed_in_visit_id": self.completed_visit_a.id}, format='json'
        )
        self.assertEqual(res_ok.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.status, 'COMPLETED')

    # -------------------------------------------------------------------------
    # 8. ALERTS & AUDIT API TESTS
    # -------------------------------------------------------------------------
    def test_11_alerts_facility_isolation_and_audit_admin_restriction(self):
        """Alerts are facility scoped; audit log is restricted to admins (403 for nurse)."""
        OperationalAlert.objects.create(facility=self.clinic_a, alert_category="STOCK_OUT", title="Low Paracetamol", severity="HIGH")
        OperationalAlert.objects.create(facility=self.clinic_b, alert_category="EQUIPMENT", title="ECG Issue", severity="MEDIUM")

        self.client.force_authenticate(user=self.doc_user)
        res_alerts = self.client.get('/api/v1/alerts/')
        self.assertEqual(res_alerts.status_code, status.HTTP_200_OK)
        titles = [a['title'] for a in (res_alerts.data['results'] if 'results' in res_alerts.data else res_alerts.data)]
        self.assertIn("Low Paracetamol", titles)
        self.assertNotIn("ECG Issue", titles)

        # Nurse cannot read audit log (403)
        self.client.force_authenticate(user=self.nurse_user)
        res_audit_nurse = self.client.get('/api/v1/audit/')
        self.assertEqual(res_audit_nurse.status_code, status.HTTP_403_FORBIDDEN)

        # Admin can read audit log (200)
        self.client.force_authenticate(user=self.admin_user)
        res_audit_admin = self.client.get('/api/v1/audit/')
        self.assertEqual(res_audit_admin.status_code, status.HTTP_200_OK)
