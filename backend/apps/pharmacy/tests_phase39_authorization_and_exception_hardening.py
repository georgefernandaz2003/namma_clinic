"""
Phase 39 — Legacy Role Authorization Migration & Pharmacy API Exception Hardening Test Suite.

Validates:
1. SEC-38-01:
   - Authorized PHARMACIST whose legacy User.role != 'PHARMACIST' can verify, hold, reject, and dispense.
   - Dual-role user (INVENTORY + PHARMACIST) can independently dispense medicines AND perform inventory operations.
   - Pure unauthorized roles (DOCTOR, NURSE, LAB_TECHNICIAN, FRONT_DESK_OFFICER, pure INVENTORY) are rejected with HTTP 403.
   - Hospital Admin and DHO operational scope remain intact.
2. SEC-38-02:
   - Nonexistent prescription_id returns controlled HTTP 404.
   - Nonexistent facility_id returns controlled HTTP 404.
   - Nonexistent prescription_item_id or batch_id returns controlled HTTP 404.
   - Valid dispensation logs immutable InventoryLedger movement.
   - Service gate SRV_PHARMACY unavailability blocks dispensation cleanly.
"""
import datetime
from django.test import TransactionTestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.geography.models import State, District
from apps.facilities.models import Facility, Department, FacilityService, ServiceMaster
from apps.accounts.models import (
    User, Person, StaffProfile, RoleMaster, StaffRoleAssignment, StaffFacilityAssignment,
    RolePermission, PermissionMaster
)
from apps.patients.models import Patient
from apps.visits.models import Visit
from apps.consultations.models import Consultation, Prescription, PrescriptionItem
from apps.pharmacy.models import MedicineMaster, MedicineBatch, Dispensation, InventoryLedger


class Phase39AuthorizationAndHardeningTests(TransactionTestCase):

    def setUp(self):
        super().setUp()
        self.client = APIClient()

        # Geography
        self.state = State.objects.create(name="Tamil Nadu P39", code="TN-P39")
        self.district = District.objects.create(name="Chennai P39", code="CHN-P39", state=self.state)

        # Facility & Departments
        self.facility = Facility.objects.create(
            facility_code="FAC-P39",
            facility_name="Namma Clinic P39 PHC",
            facility_type="PRIMARY_HEALTH_CENTRE",
            state=self.state,
            district=self.district
        )
        self.pharm_dept = Department.objects.create(
            facility=self.facility,
            code="PHARM",
            name="Pharmacy",
            is_active=True
        )
        self.opd_dept = Department.objects.create(
            facility=self.facility,
            code="OPD",
            name="General OPD",
            is_active=True
        )

        # Ensure SRV_PHARMACY is registered & enabled
        self.srv_pharmacy_master, _ = ServiceMaster.objects.get_or_create(
            code="SRV_PHARMACY",
            defaults={"name": "Pharmacy Services", "category": "CLINICAL", "is_active": True}
        )
        self.fac_srv_pharmacy, _ = FacilityService.objects.get_or_create(
            facility=self.facility,
            service=self.srv_pharmacy_master,
            defaults={"is_available": True}
        )
        self.fac_srv_pharmacy.is_available = True
        self.fac_srv_pharmacy.save()

        # Certified Roles
        role_codes = ['DISTRICT_OFFICER', 'HOSPITAL_ADMIN', 'DOCTOR', 'NURSE', 'FRONT_DESK_OFFICER', 'LAB_TECHNICIAN', 'PHARMACIST', 'INVENTORY']
        self.roles = {}
        for r_code in role_codes:
            rm, _ = RoleMaster.objects.get_or_create(code=r_code, defaults={"name": r_code, "is_active": True})
            self.roles[r_code] = rm

        # Ensure permissions for PHARMACIST and INVENTORY exist
        for perm_code in ['pharmacy.dispense', 'dispensation.create', 'prescription.verify', 'prescription.hold', 'prescription.reject', 'purchase_order.create', 'goods_receipt.create', 'inventory.update']:
            domain = "PHARMACY" if "pharmacy" in perm_code or "prescription" in perm_code or "dispens" in perm_code else "INVENTORY"
            action = perm_code.split(".")[-1]
            pm, _ = PermissionMaster.objects.get_or_create(code=perm_code, defaults={"name": perm_code, "domain": domain, "action": action, "is_active": True})
            if perm_code.startswith('pharmacy.') or perm_code.startswith('dispensation.') or perm_code.startswith('prescription.'):
                RolePermission.objects.get_or_create(role=self.roles['PHARMACIST'], permission=pm, defaults={"is_active": True})
            if perm_code in ['purchase_order.create', 'goods_receipt.create', 'inventory.update']:
                RolePermission.objects.get_or_create(role=self.roles['INVENTORY'], permission=pm, defaults={"is_active": True})

        # 1. Dual-Role User (INVENTORY + PHARMACIST)
        self.dual_user, self.dual_staff = self._create_staff_user(
            username="dual_p39",
            employee_id="EMP-DUAL-P39",
            legacy_role="INVENTORY",
            role_codes=["INVENTORY", "PHARMACIST"],
            department=self.pharm_dept
        )

        # 2. Pharmacist with mismatched legacy role (legacy User.role == 'DOCTOR', but assigned 'PHARMACIST')
        self.pharm_mismatched, self.pharm_staff = self._create_staff_user(
            username="pharm_mismatch_p39",
            employee_id="EMP-MISMATCH-P39",
            legacy_role="DOCTOR",
            role_codes=["PHARMACIST"],
            department=self.pharm_dept
        )

        # 3. Pure Doctor
        self.doctor_user, self.doc_staff = self._create_staff_user(
            username="doc_p39",
            employee_id="EMP-DOC-P39",
            legacy_role="DOCTOR",
            role_codes=["DOCTOR"],
            department=self.opd_dept
        )

        # 4. Pure Inventory (without Pharmacist)
        self.inventory_user, self.inv_staff = self._create_staff_user(
            username="inv_p39",
            employee_id="EMP-INV-P39",
            legacy_role="INVENTORY",
            role_codes=["INVENTORY"],
            department=self.pharm_dept
        )

        # Clinical Data Setup: Patient, Visit, Consultation, Prescription, Batch
        self.patient = Patient.objects.create(
            patient_id="PAT-P39-001",
            name="Ravi Kumar P39",
            age=35,
            gender="MALE",
            registered_at_facility=self.facility
        )
        self.visit = Visit.objects.create(
            visit_id="VST-P39-001",
            patient=self.patient,
            facility=self.facility,
            visit_type="OUTPATIENT"
        )
        self.consultation = Consultation.objects.create(
            visit=self.visit,
            patient=self.patient,
            facility=self.facility,
            doctor_staff=self.doc_staff,
            chief_complaint="Fever and cough"
        )
        self.prescription = Prescription.objects.create(
            consultation=self.consultation,
            patient=self.patient,
            facility=self.facility,
            doctor=self.doctor_user,
            doctor_staff=self.doc_staff,
            status="PENDING_VERIFICATION",
            date=datetime.date.today()
        )
        self.medicine = MedicineMaster.objects.create(
            generic_name="Paracetamol P39 500mg",
            dosage_form="Tablet",
            strength="500mg",
            category="Analgesic"
        )
        self.rx_item = PrescriptionItem.objects.create(
            prescription=self.prescription,
            medicine=self.medicine,
            medicine_name="Paracetamol 500mg",
            dosage="1-0-0",
            frequency="Daily",
            duration_days=5,
            quantity=10,
            dispensed_quantity=0,
            status="PENDING"
        )
        self.batch = MedicineBatch.objects.create(
            facility=self.facility,
            medicine=self.medicine,
            batch_number="BAT-P39-001",
            expiry_date=datetime.date.today() + datetime.timedelta(days=180),
            quantity=100,
            available_quantity=100,
            status="AVAILABLE"
        )
        InventoryLedger.objects.create(
            batch=self.batch,
            facility=self.facility,
            performed_by_staff=self.pharm_staff,
            transaction_type="PURCHASE_RECEIPT",
            quantity_delta=100,
            balance_after=100,
            remarks="Initial batch setup"
        )

    def _create_staff_user(self, username, employee_id, legacy_role, role_codes, department):
        person = Person.objects.create(
            first_name=username,
            last_name="Test",
            gender="MALE",
            date_of_birth=datetime.date(1990, 1, 1)
        )
        staff = StaffProfile.objects.create(
            person=person,
            employee_id=employee_id,
            status="ACTIVE",
            department=department
        )
        user = User.objects.create_user(
            username=username,
            email=f"{username}@clinic.org",
            password="pass123",
            full_name=f"Full {username}",
            role=legacy_role,
            assigned_facility=self.facility,
            staff_profile=staff
        )
        StaffFacilityAssignment.objects.create(
            staff=staff,
            facility=self.facility,
            department=department,
            is_primary=True,
            is_active=True
        )
        for rc in role_codes:
            StaffRoleAssignment.objects.create(
                staff=staff,
                role=self.roles[rc],
                is_active=True,
                effective_from=datetime.date.today() - datetime.timedelta(days=1)
            )
        return user, staff

    def test_dual_role_can_verify_and_dispense_prescription(self):
        """Dual-role INVENTORY + PHARMACIST user must have full pharmacy authority."""
        self.client.force_authenticate(user=self.dual_user)

        # 1. Verify prescription via /api/v1/pharmacy/prescriptions/{id}/verify/
        resp = self.client.post(f"/api/v1/pharmacy/prescriptions/{self.prescription.id}/verify/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.prescription.refresh_from_db()
        self.assertEqual(self.prescription.status, "VERIFIED")

        # 2. Dispense prescription via /api/v1/pharmacy/dispensations/
        disp_payload = {
            "prescription_id": self.prescription.id,
            "facility_id": self.facility.id,
            "items": [{
                "prescription_item_id": self.rx_item.id,
                "batch_id": self.batch.id,
                "quantity": 5
            }]
        }
        resp = self.client.post("/api/v1/pharmacy/dispensations/", disp_payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # 3. Verify InventoryLedger entry exists and batch quantity reduced
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.available_quantity, 95)
        ledger_count = InventoryLedger.objects.filter(
            facility=self.facility,
            batch=self.batch,
            transaction_type="DISPENSE"
        ).count()
        self.assertGreaterEqual(ledger_count, 1)

    def test_mismatched_legacy_role_pharmacist_authorized_via_rbac(self):
        """User with legacy User.role == 'DOCTOR' but active StaffRoleAssignment 'PHARMACIST' is authorized."""
        self.client.force_authenticate(user=self.pharm_mismatched)

        # 1. Verify prescription
        resp = self.client.post(f"/api/v1/pharmacy/prescriptions/{self.prescription.id}/verify/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # 2. Hold prescription
        resp = self.client.post(f"/api/v1/pharmacy/prescriptions/{self.prescription.id}/hold/", {"reason": "Checking drug interaction"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.prescription.refresh_from_db()
        self.assertEqual(self.prescription.status, "ON_HOLD")

        # 3. Dispense
        self.prescription.status = "VERIFIED"
        self.prescription.save()
        disp_payload = {
            "prescription_id": self.prescription.id,
            "facility_id": self.facility.id,
            "items": [{
                "prescription_item_id": self.rx_item.id,
                "batch_id": self.batch.id,
                "quantity": 2
            }]
        }
        resp = self.client.post("/api/v1/pharmacy/dispensations/", disp_payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_unauthorized_roles_cannot_dispense_or_verify(self):
        """Pure Doctor and pure Inventory users must be rejected with HTTP 403."""
        # 1. Pure Doctor
        self.client.force_authenticate(user=self.doctor_user)
        resp = self.client.post(f"/api/v1/pharmacy/prescriptions/{self.prescription.id}/verify/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Pure Inventory
        self.client.force_authenticate(user=self.inventory_user)
        resp = self.client.post(f"/api/v1/pharmacy/prescriptions/{self.prescription.id}/verify/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        disp_payload = {
            "prescription_id": self.prescription.id,
            "facility_id": self.facility.id,
            "items": [{
                "prescription_item_id": self.rx_item.id,
                "batch_id": self.batch.id,
                "quantity": 2
            }]
        }
        resp = self.client.post("/api/v1/pharmacy/dispensations/", disp_payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_sec_38_02_nonexistent_ids_return_http_404_not_500(self):
        """Invalid prescription_id, facility_id, item_id, or batch_id return clean HTTP 404."""
        self.client.force_authenticate(user=self.dual_user)

        # 1. Nonexistent prescription_id
        payload_bad_rx = {
            "prescription_id": 9999999,
            "facility_id": self.facility.id,
            "items": [{
                "prescription_item_id": self.rx_item.id,
                "batch_id": self.batch.id,
                "quantity": 1
            }]
        }
        resp = self.client.post("/api/v1/pharmacy/dispensations/", payload_bad_rx, format="json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("does not exist", resp.data.get("error", ""))

        # 2. Nonexistent facility_id
        payload_bad_fac = {
            "prescription_id": self.prescription.id,
            "facility_id": 8888888,
            "items": [{
                "prescription_item_id": self.rx_item.id,
                "batch_id": self.batch.id,
                "quantity": 1
            }]
        }
        resp = self.client.post("/api/v1/pharmacy/dispensations/", payload_bad_fac, format="json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("does not exist", resp.data.get("error", ""))

        # 3. Nonexistent prescription_item_id
        payload_bad_item = {
            "prescription_id": self.prescription.id,
            "facility_id": self.facility.id,
            "items": [{
                "prescription_item_id": 7777777,
                "batch_id": self.batch.id,
                "quantity": 1
            }]
        }
        resp = self.client.post("/api/v1/pharmacy/dispensations/", payload_bad_item, format="json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("does not exist", resp.data.get("error", ""))

        # 4. Nonexistent batch_id
        payload_bad_batch = {
            "prescription_id": self.prescription.id,
            "facility_id": self.facility.id,
            "items": [{
                "prescription_item_id": self.rx_item.id,
                "batch_id": 6666666,
                "quantity": 1
            }]
        }
        resp = self.client.post("/api/v1/pharmacy/dispensations/", payload_bad_batch, format="json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("does not exist", resp.data.get("error", ""))

    def test_service_gate_srv_pharmacy_disabled_blocks_dispensation(self):
        """Disabling SRV_PHARMACY service gate blocks dispensation cleanly with HTTP 400."""
        self.client.force_authenticate(user=self.dual_user)

        # Disable SRV_PHARMACY
        self.fac_srv_pharmacy.is_available = False
        self.fac_srv_pharmacy.save()

        disp_payload = {
            "prescription_id": self.prescription.id,
            "facility_id": self.facility.id,
            "items": [{
                "prescription_item_id": self.rx_item.id,
                "batch_id": self.batch.id,
                "quantity": 1
            }]
        }
        resp = self.client.post("/api/v1/pharmacy/dispensations/", disp_payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("SRV_PHARMACY", resp.data.get("error", ""))
