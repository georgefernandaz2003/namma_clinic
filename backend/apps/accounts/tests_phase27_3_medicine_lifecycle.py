import datetime
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import (
    User, RoleChoices, RoleMaster, Person,
    StaffProfile, StaffRoleAssignment, StaffFacilityAssignment
)
from apps.accounts.services import seed_roles_and_permissions
from apps.facilities.models import Facility
from apps.geography.models import State, District
from apps.patients.models import Patient
from apps.visits.models import Visit
from apps.consultations.models import Consultation, Prescription, PrescriptionItem
from apps.pharmacy.models import (
    MedicineMaster, MedicineBatch, Vendor,
    PurchaseOrder, PurchaseOrderItem, GoodsReceiptNote,
    Dispensation, DispensationItem, InventoryLedger
)


class Phase273MedicineLifecycleTests(TestCase):
    """
    Comprehensive validation test suite for Phase 27.3:
    End-to-End Medicine Lifecycle Reconciliation.

    Traces one real medicine through:
    REQUEST -> APPROVAL -> PURCHASE ORDER -> ORDERED -> GRN/RECEIPT -> INVENTORY -> PRESCRIPTION -> DISPENSING -> RECONCILIATION
    """

    def setUp(self):
        seed_roles_and_permissions()

        self.state = State.objects.create(name="Tamil Nadu", code="TN")
        self.district = District.objects.create(name="Chennai", code="TN-CHN", state=self.state)

        self.facility_a = Facility.objects.create(
            facility_name="Namma Primary Health Clinic A",
            facility_code="NPHC-CHN-01",
            facility_type="PRIMARY_HEALTH_CENTRE",
            district=self.district,
            state=self.state
        )
        self.facility_b = Facility.objects.create(
            facility_name="Namma Urban Clinic B",
            facility_code="NPHC-CHN-02",
            facility_type="PRIMARY_HEALTH_CENTRE",
            district=self.district,
            state=self.state
        )

        role_inv = RoleMaster.objects.get(code=RoleChoices.INVENTORY)
        role_phm = RoleMaster.objects.get(code=RoleChoices.PHARMACIST)
        role_admin = RoleMaster.objects.get(code=RoleChoices.HOSPITAL_ADMIN)
        role_doc = RoleMaster.objects.get(code=RoleChoices.DOCTOR)

        # 1. Inventory User at Facility A
        p_inv = Person.objects.create(
            first_name="Kavitha", last_name="Rajan",
            gender="FEMALE", date_of_birth=datetime.date(1987, 3, 15), phone_number="9845022001"
        )
        self.staff_inv = StaffProfile.objects.create(
            person=p_inv, employee_id="STF-INV-CHN-01", designation="Inventory Manager", status="ACTIVE"
        )
        self.user_inv = User.objects.create_user(
            username="inv_officer_chn", password="Password123!",
            staff_profile=self.staff_inv, assigned_facility=self.facility_a,
            role=RoleChoices.INVENTORY
        )
        StaffRoleAssignment.objects.create(staff=self.staff_inv, role=role_inv, facility=self.facility_a, is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.staff_inv, facility=self.facility_a, is_primary=True, is_active=True)

        # 2. Hospital Admin at Facility A (Authorized Procurement Approver)
        p_adm = Person.objects.create(
            first_name="Dr. Senthil", last_name="Kumar",
            gender="MALE", date_of_birth=datetime.date(1978, 6, 20), phone_number="9845022002"
        )
        self.staff_adm = StaffProfile.objects.create(
            person=p_adm, employee_id="STF-ADM-CHN-01", designation="Hospital Administrator", status="ACTIVE"
        )
        self.user_adm = User.objects.create_user(
            username="admin_approver_chn", password="Password123!",
            staff_profile=self.staff_adm, assigned_facility=self.facility_a,
            role=RoleChoices.HOSPITAL_ADMIN
        )
        StaffRoleAssignment.objects.create(staff=self.staff_adm, role=role_admin, facility=self.facility_a, is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.staff_adm, facility=self.facility_a, is_primary=True, is_active=True)

        # 3. Doctor at Facility A (Prescriber)
        p_doc = Person.objects.create(
            first_name="Dr. Ananya", last_name="Swaminathan",
            gender="FEMALE", date_of_birth=datetime.date(1984, 8, 12), phone_number="9845022003"
        )
        self.staff_doc = StaffProfile.objects.create(
            person=p_doc, employee_id="STF-DOC-CHN-01", designation="Medical Officer", status="ACTIVE"
        )
        self.user_doc = User.objects.create_user(
            username="doc_prescriber_chn", password="Password123!",
            staff_profile=self.staff_doc, assigned_facility=self.facility_a,
            role=RoleChoices.DOCTOR
        )
        StaffRoleAssignment.objects.create(staff=self.staff_doc, role=role_doc, facility=self.facility_a, is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.staff_doc, facility=self.facility_a, is_primary=True, is_active=True)

        # 4. Pharmacist at Facility A (Dispenser)
        p_phm = Person.objects.create(
            first_name="Venkatesh", last_name="Murthy",
            gender="MALE", date_of_birth=datetime.date(1991, 11, 5), phone_number="9845022004"
        )
        self.staff_phm = StaffProfile.objects.create(
            person=p_phm, employee_id="STF-PHM-CHN-01", designation="Pharmacist", status="ACTIVE"
        )
        self.user_phm = User.objects.create_user(
            username="phm_dispenser_chn", password="Password123!",
            staff_profile=self.staff_phm, assigned_facility=self.facility_a,
            role=RoleChoices.PHARMACIST
        )
        StaffRoleAssignment.objects.create(staff=self.staff_phm, role=role_phm, facility=self.facility_a, is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.staff_phm, facility=self.facility_a, is_primary=True, is_active=True)

        # 5. Inventory User at Facility B (Facility Isolation Test)
        p_inv_b = Person.objects.create(
            first_name="Deepak", last_name="Nath",
            gender="MALE", date_of_birth=datetime.date(1989, 4, 18), phone_number="9845022005"
        )
        self.staff_inv_b = StaffProfile.objects.create(
            person=p_inv_b, employee_id="STF-INV-CHN-02", designation="Inventory Officer", status="ACTIVE"
        )
        self.user_inv_b = User.objects.create_user(
            username="inv_officer_fac_b", password="Password123!",
            staff_profile=self.staff_inv_b, assigned_facility=self.facility_b,
            role=RoleChoices.INVENTORY
        )
        StaffRoleAssignment.objects.create(staff=self.staff_inv_b, role=role_inv, facility=self.facility_b, is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.staff_inv_b, facility=self.facility_b, is_primary=True, is_active=True)

        # Domain Setup: Vendor, Medicine, Patient, Visit, Consultation
        self.vendor = Vendor.objects.create(
            vendor_name="Tamil Nadu Medical Services Corporation",
            contact_person="Logistics Officer",
            phone="9845098765",
            status="ACTIVE"
        )

        self.medicine = MedicineMaster.objects.create(
            generic_name="Azithromycin",
            brand_name="Azi-500",
            dosage_form="TABLET",
            strength="500mg",
            unit="TABLET",
            reorder_level=20
        )

        self.patient = Patient.objects.create(
            patient_id="PAT-LIFE-001",
            name="Meenakshi Amma",
            age=45,
            gender="FEMALE",
            registered_at_facility=self.facility_a
        )

        self.visit = Visit.objects.create(
            visit_id="VST-LIFE-001",
            patient=self.patient,
            facility=self.facility_a,
            visit_type="OUTPATIENT"
        )

        self.consultation = Consultation.objects.create(
            visit=self.visit,
            patient=self.patient,
            facility=self.facility_a,
            doctor=self.user_doc,
            doctor_staff=self.staff_doc,
            chief_complaint="Persistent bacterial throat infection",
            clinical_notes="Bacterial pharyngitis diagnosed, prescribing Azithromycin 500mg."
        )

    def test_complete_end_to_end_medicine_lifecycle_and_reconciliation(self):
        """
        Executes and reconciles:
        REQUEST -> APPROVAL -> PURCHASE ORDER -> ORDERED -> GRN/RECEIPT -> INVENTORY -> PRESCRIPTION -> DISPENSING -> RECONCILIATION
        """
        # Step 0: Initial stock balance for Azithromycin at Facility A is 0
        batches = MedicineBatch.objects.filter(medicine=self.medicine, facility=self.facility_a)
        self.assertEqual(batches.count(), 0)
        opening_stock = 0

        # Step 1: Inventory creates/submits medicine procurement request / PO
        client_inv = APIClient()
        client_inv.force_authenticate(user=self.user_inv)

        po_payload = {
            "facility": self.facility_a.id,
            "vendor": self.vendor.id,
            "po_number": "PO-LIFE-2026-001",
            "items": [
                {
                    "medicine_id": self.medicine.id,
                    "ordered_quantity": 100,
                    "unit_price": 12.50
                }
            ]
        }
        res_po = client_inv.post("/api/v1/procurement/purchase-orders/", po_payload, format="json")
        self.assertEqual(res_po.status_code, status.HTTP_201_CREATED)
        po_id = res_po.data["id"]
        self.assertEqual(res_po.data["status"], "DRAFT")

        # Submit PO for Approval
        res_submit = client_inv.post(f"/api/v1/procurement/purchase-orders/{po_id}/submit-approval/")
        self.assertEqual(res_submit.status_code, status.HTTP_200_OK)
        self.assertEqual(res_submit.data["status"], "PENDING_APPROVAL")

        # Step 2: RBAC Check - Inventory / Pharmacist / Doctor CANNOT approve PO
        client_phm = APIClient()
        client_phm.force_authenticate(user=self.user_phm)
        res_phm_app = client_phm.post(f"/api/v1/procurement/purchase-orders/{po_id}/approve/", {"remarks": "Unauthorized"}, format="json")
        self.assertEqual(res_phm_app.status_code, status.HTTP_403_FORBIDDEN)

        res_inv_app = client_inv.post(f"/api/v1/procurement/purchase-orders/{po_id}/approve/", {"remarks": "Self approve"}, format="json")
        self.assertEqual(res_inv_app.status_code, status.HTTP_403_FORBIDDEN)

        # Authorized Approver (Hospital Admin with purchase_order.approve) approves PO
        client_adm = APIClient()
        client_adm.force_authenticate(user=self.user_adm)
        res_adm_app = client_adm.post(f"/api/v1/procurement/purchase-orders/{po_id}/approve/", {"approval_tier": 1, "status": "APPROVED", "remarks": "Budget authorized"}, format="json")
        self.assertEqual(res_adm_app.status_code, status.HTTP_200_OK)
        self.assertEqual(res_adm_app.data["status"], "APPROVED")

        # Step 3: PO placed with vendor -> ORDERED
        res_order = client_inv.post(f"/api/v1/procurement/purchase-orders/{po_id}/place-order/")
        self.assertEqual(res_order.status_code, status.HTTP_200_OK)
        self.assertEqual(res_order.data["status"], "ORDERED")

        # Step 4: Inventory receives goods through GRN (100 units received)
        batch_num = "AZI-B26-001"
        expiry = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()
        grn_payload = {
            "purchase_order_id": po_id,
            "facility_id": self.facility_a.id,
            "grn_number": "GRN-LIFE-2026-001",
            "items": [
                {
                    "medicine_id": self.medicine.id,
                    "batch_number": batch_num,
                    "expiry_date": expiry,
                    "unit_cost": 12.50,
                    "quantity_received": 100,
                    "quantity_accepted": 100,
                    "quantity_rejected": 0
                }
            ]
        }
        res_grn = client_inv.post("/api/v1/procurement/grn/", grn_payload, format="json")
        self.assertEqual(res_grn.status_code, status.HTTP_201_CREATED)

        # Step 5: PostgreSQL + InventoryLedger reflect received quantity
        receipts_total = 100
        batch = MedicineBatch.objects.get(medicine=self.medicine, batch_number=batch_num, facility=self.facility_a)
        self.assertEqual(batch.available_quantity, 100)
        self.assertEqual(batch.quantity, 100)

        ledger_receipt = InventoryLedger.objects.filter(batch=batch, transaction_type="PURCHASE_RECEIPT").first()
        self.assertIsNotNone(ledger_receipt)
        self.assertEqual(ledger_receipt.quantity_delta, 100)
        self.assertEqual(ledger_receipt.balance_after, 100)

        # Step 6: Doctor creates prescription for this medicine (15 units)
        client_doc = APIClient()
        client_doc.force_authenticate(user=self.user_doc)
        rx_payload = {
            "consultation": self.consultation.id,
            "patient": self.patient.id,
            "facility": self.facility_a.id,
            "notes": "Azithromycin 500mg once daily for 5 days",
            "items": [
                {
                    "medicine": self.medicine.id,
                    "medicine_name": self.medicine.generic_name,
                    "dosage": "500mg",
                    "frequency": "OD",
                    "duration_days": 5,
                    "quantity": 15
                }
            ]
        }
        res_rx = client_doc.post("/api/v1/pharmacy/prescriptions/", rx_payload, format="json")
        self.assertEqual(res_rx.status_code, status.HTTP_201_CREATED)
        rx_id = res_rx.data["id"]
        rx = Prescription.objects.get(pk=rx_id)
        self.assertEqual(rx.status, "PENDING_VERIFICATION")
        rx_item = rx.items.first()
        self.assertEqual(rx_item.medicine_id, self.medicine.id)
        self.assertEqual(rx_item.quantity, 15)

        # Step 7: Pharmacist verifies and dispenses
        # Inventory cannot verify or dispense
        res_inv_vfy = client_inv.post(f"/api/v1/pharmacy/prescriptions/{rx_id}/verify/", {"notes": "Illegal verify"})
        self.assertEqual(res_inv_vfy.status_code, status.HTTP_403_FORBIDDEN)

        # Pharmacist verifies prescription
        res_vfy = client_phm.post(f"/api/v1/pharmacy/prescriptions/{rx_id}/verify/", {"notes": "Verified by registered pharmacist"}, format="json")
        self.assertEqual(res_vfy.status_code, status.HTTP_200_OK)
        self.assertEqual(res_vfy.data["status"], "VERIFIED")

        # Pharmacist executes dispensation
        dispense_payload = {
            "prescription_id": rx_id,
            "facility_id": self.facility_a.id,
            "items": [
                {
                    "prescription_item_id": rx_item.id,
                    "batch_id": batch.id,
                    "quantity": 15
                }
            ]
        }
        res_disp = client_phm.post("/api/v1/pharmacy/dispensations/", dispense_payload, format="json")
        self.assertEqual(res_disp.status_code, status.HTTP_201_CREATED)
        dispensed_total = 15

        # Step 8: InventoryLedger reflects the dispensing deduction
        batch.refresh_from_db()
        self.assertEqual(batch.available_quantity, 85)

        ledger_disp = InventoryLedger.objects.filter(batch=batch, transaction_type="DISPENSE").first()
        self.assertIsNotNone(ledger_disp)
        self.assertEqual(ledger_disp.quantity_delta, -15)
        self.assertEqual(ledger_disp.balance_after, 85)

        # Step 9: Stock Adjustment / Physical-count reconciliation (-5 units adjustment due to damage)
        res_adj = client_inv.post(
            f"/api/v1/pharmacy/batches/{batch.id}/adjust/",
            {"quantity_delta": -5, "remarks": "Physical stock count: 5 units expired/damaged during transit"},
            format="json"
        )
        self.assertEqual(res_adj.status_code, status.HTTP_200_OK)
        adjustments_total = -5

        batch.refresh_from_db()
        self.assertEqual(batch.available_quantity, 80)

        # Step 10: Quantitative Reconciliation Verification
        # Opening Stock (0) + Receipts (100) + Adjustments (-5) - Dispensing (15) = Closing Stock (80)
        closing_stock = batch.available_quantity
        calculated_stock = opening_stock + receipts_total + adjustments_total - dispensed_total
        self.assertEqual(closing_stock, calculated_stock)
        self.assertEqual(closing_stock, 80)

        # Verify sum of deltas across all InventoryLedger records matches closing stock
        all_ledgers = InventoryLedger.objects.filter(batch=batch).order_by("transaction_timestamp")
        self.assertEqual(all_ledgers.count(), 3)
        net_ledger_movement = sum(entry.quantity_delta for entry in all_ledgers)
        self.assertEqual(opening_stock + net_ledger_movement, closing_stock)

        # Step 11: Facility isolation verification
        # Facility B inventory cannot adjust Facility A batch
        client_inv_b = APIClient()
        client_inv_b.force_authenticate(user=self.user_inv_b)
        res_b_adj = client_inv_b.post(
            f"/api/v1/pharmacy/batches/{batch.id}/adjust/",
            {"quantity_delta": 10, "remarks": "Cross facility attempt"},
            format="json"
        )
        self.assertIn(res_b_adj.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
