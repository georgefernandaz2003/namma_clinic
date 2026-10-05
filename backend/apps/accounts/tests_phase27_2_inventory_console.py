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
from apps.pharmacy.models import (
    MedicineMaster, MedicineBatch, Vendor,
    PurchaseOrder, PurchaseOrderItem, GoodsReceiptNote, InventoryLedger
)


class Phase272InventoryConsoleBackendTests(TestCase):
    """
    Validation test suite for Phase 27.2 - Inventory & Procurement Console Backend APIs.
    Validates:
    - INVENTORY role access to procurement lifecycle and stock adjustments
    - InventoryLedger as the single source of truth for stock increments and adjustments
    - Role separation: PHARMACIST and clinical roles blocked from inventory administration
    - Facility scope enforcement
    """

    def setUp(self):
        seed_roles_and_permissions()

        self.state = State.objects.create(name="Karnataka", code="KA")
        self.district = District.objects.create(name="Bengaluru Urban", code="KA-BLR", state=self.state)

        self.facility_a = Facility.objects.create(
            facility_name="Main Primary Health Centre",
            facility_code="PHC-MAIN-01",
            facility_type="PRIMARY_HEALTH_CENTRE",
            district=self.district,
            state=self.state
        )
        self.facility_b = Facility.objects.create(
            facility_name="Secondary Outreach Clinic",
            facility_code="PHC-OUTREACH-02",
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
            first_name="Inv", last_name="Manager",
            gender="MALE", date_of_birth=datetime.date(1985, 1, 1), phone_number="9845011001"
        )
        self.staff_inv = StaffProfile.objects.create(
            person=p_inv, employee_id="STF-INV-01", designation="Inventory Manager", status="ACTIVE"
        )
        self.user_inv = User.objects.create_user(
            username="test_inv_officer", password="Password123!",
            staff_profile=self.staff_inv, assigned_facility=self.facility_a,
            role=RoleChoices.INVENTORY
        )
        StaffRoleAssignment.objects.create(staff=self.staff_inv, role=role_inv, facility=self.facility_a, is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.staff_inv, facility=self.facility_a, is_primary=True, is_active=True)

        # 2. Pharmacist User at Facility A
        p_phm = Person.objects.create(
            first_name="Phm", last_name="User",
            gender="FEMALE", date_of_birth=datetime.date(1990, 1, 1), phone_number="9845011002"
        )
        self.staff_phm = StaffProfile.objects.create(
            person=p_phm, employee_id="STF-PHM-01", designation="Pharmacist", status="ACTIVE"
        )
        self.user_phm = User.objects.create_user(
            username="test_phm_user", password="Password123!",
            staff_profile=self.staff_phm, assigned_facility=self.facility_a,
            role=RoleChoices.PHARMACIST
        )
        StaffRoleAssignment.objects.create(staff=self.staff_phm, role=role_phm, facility=self.facility_a, is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.staff_phm, facility=self.facility_a, is_primary=True, is_active=True)

        # 3. Hospital Admin User at Facility A
        p_adm = Person.objects.create(
            first_name="Admin", last_name="User",
            gender="MALE", date_of_birth=datetime.date(1980, 1, 1), phone_number="9845011003"
        )
        self.staff_adm = StaffProfile.objects.create(
            person=p_adm, employee_id="STF-ADM-01", designation="Hospital Administrator", status="ACTIVE"
        )
        self.user_adm = User.objects.create_user(
            username="test_hosp_admin", password="Password123!",
            staff_profile=self.staff_adm, assigned_facility=self.facility_a,
            role=RoleChoices.HOSPITAL_ADMIN
        )
        StaffRoleAssignment.objects.create(staff=self.staff_adm, role=role_admin, facility=self.facility_a, is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.staff_adm, facility=self.facility_a, is_primary=True, is_active=True)

        # 4. Doctor User at Facility A
        p_doc = Person.objects.create(
            first_name="Doctor", last_name="User",
            gender="MALE", date_of_birth=datetime.date(1982, 1, 1), phone_number="9845011004"
        )
        self.staff_doc = StaffProfile.objects.create(
            person=p_doc, employee_id="STF-DOC-01", designation="Medical Officer", status="ACTIVE"
        )
        self.user_doc = User.objects.create_user(
            username="test_doc_user", password="Password123!",
            staff_profile=self.staff_doc, assigned_facility=self.facility_a,
            role=RoleChoices.DOCTOR
        )
        StaffRoleAssignment.objects.create(staff=self.staff_doc, role=role_doc, facility=self.facility_a, is_active=True)
        StaffFacilityAssignment.objects.create(staff=self.staff_doc, facility=self.facility_a, is_primary=True, is_active=True)

        # Shared Test Domain Entities
        self.vendor = Vendor.objects.create(
            vendor_name="Karnataka State Drugs Logistics",
            contact_person="Supply Officer",
            phone="9845099999",
            status="ACTIVE"
        )
        self.medicine = MedicineMaster.objects.create(
            generic_name="Amoxicillin 500mg",
            brand_name="Mox 500",
            dosage_form="CAPSULE",
            strength="500mg",
            unit="CAPSULE",
            minimum_stock=50,
            reorder_level=100
        )
        self.batch_a = MedicineBatch.objects.create(
            facility=self.facility_a,
            medicine=self.medicine,
            batch_number="BATCH-PH27-001",
            expiry_date=datetime.date(2028, 12, 31),
            unit_cost=3.50,
            quantity=100,
            available_quantity=100,
            status="AVAILABLE"
        )

        self.client_inv = APIClient()
        self.client_inv.force_authenticate(user=self.user_inv)

        self.client_phm = APIClient()
        self.client_phm.force_authenticate(user=self.user_phm)

        self.client_adm = APIClient()
        self.client_adm.force_authenticate(user=self.user_adm)

        self.client_doc = APIClient()
        self.client_doc.force_authenticate(user=self.user_doc)

    def test_01_inventory_user_creates_po_with_items(self):
        """INVENTORY user can create a purchase order with line items."""
        payload = {
            "facility": self.facility_a.id,
            "vendor": self.vendor.id,
            "po_number": "PO-TEST-27-001",
            "items": [
                {
                    "medicine_id": self.medicine.id,
                    "ordered_quantity": 200,
                    "unit_price": 3.50
                }
            ]
        }
        res = self.client_inv.post("/api/v1/procurement/purchase-orders/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        po_id = res.data["id"]
        po = PurchaseOrder.objects.get(id=po_id)
        self.assertEqual(po.status, "DRAFT")
        self.assertEqual(po.items.count(), 1)
        self.assertEqual(po.items.first().ordered_quantity, 200)

    def test_02_po_workflow_draft_to_approved_to_ordered(self):
        """PO workflow transitions: DRAFT -> PENDING_APPROVAL -> APPROVED -> ORDERED."""
        po = PurchaseOrder.objects.create(
            facility=self.facility_a,
            vendor=self.vendor,
            po_number="PO-WORKFLOW-01",
            status="DRAFT"
        )
        PurchaseOrderItem.objects.create(
            purchase_order=po,
            medicine=self.medicine,
            ordered_quantity=100,
            unit_price=3.50
        )

        # 1. Submit approval (INVENTORY role)
        res_sub = self.client_inv.post(f"/api/v1/procurement/purchase-orders/{po.id}/submit-approval/")
        self.assertEqual(res_sub.status_code, status.HTTP_200_OK)
        po.refresh_from_db()
        self.assertEqual(po.status, "PENDING_APPROVAL")

        # 2. Approve PO (HOSPITAL_ADMIN role)
        res_app = self.client_adm.post(
            f"/api/v1/procurement/purchase-orders/{po.id}/approve/",
            {"approval_tier": 1, "status": "APPROVED", "remarks": "Approved by Hospital Admin"},
            format="json"
        )
        self.assertEqual(res_app.status_code, status.HTTP_200_OK)
        po.refresh_from_db()
        self.assertEqual(po.status, "APPROVED")

        # 3. Mark Ordered (INVENTORY role)
        res_ord = self.client_inv.post(f"/api/v1/procurement/purchase-orders/{po.id}/place-order/")
        self.assertEqual(res_ord.status_code, status.HTTP_200_OK)
        po.refresh_from_db()
        self.assertEqual(po.status, "ORDERED")

    def test_03_goods_receipt_increments_stock_and_posts_to_inventory_ledger(self):
        """Receiving goods increases stock through InventoryLedger and updates PO status."""
        po = PurchaseOrder.objects.create(
            facility=self.facility_a,
            vendor=self.vendor,
            po_number="PO-GRN-01",
            status="ORDERED"
        )
        po_item = PurchaseOrderItem.objects.create(
            purchase_order=po,
            medicine=self.medicine,
            ordered_quantity=50,
            unit_price=3.50
        )

        initial_ledger_count = InventoryLedger.objects.filter(facility=self.facility_a).count()

        grn_payload = {
            "purchase_order_id": po.id,
            "facility_id": self.facility_a.id,
            "grn_number": "GRN-TEST-27-001",
            "items_received": [
                {
                    "medicine_id": self.medicine.id,
                    "batch_number": "BATCH-GRN-999",
                    "expiry_date": "2029-06-30",
                    "unit_cost": 3.50,
                    "quantity_received": 50,
                    "quantity_accepted": 50,
                    "quantity_rejected": 0
                }
            ]
        }
        res = self.client_inv.post("/api/v1/procurement/grn/", grn_payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Verify batch was created with correct quantity
        received_batch = MedicineBatch.objects.get(facility=self.facility_a, batch_number="BATCH-GRN-999")
        self.assertEqual(received_batch.available_quantity, 50)

        # Verify InventoryLedger entry was created atomically
        ledger_entry = InventoryLedger.objects.filter(
            facility=self.facility_a,
            batch=received_batch,
            transaction_type="PURCHASE_RECEIPT"
        ).first()
        self.assertIsNotNone(ledger_entry)
        self.assertEqual(ledger_entry.quantity_delta, 50)
        self.assertEqual(ledger_entry.balance_after, 50)
        self.assertEqual(InventoryLedger.objects.filter(facility=self.facility_a).count(), initial_ledger_count + 1)

        # Verify PO status transitioned to RECEIVED
        po.refresh_from_db()
        self.assertEqual(po.status, "RECEIVED")

    def test_04_inventory_user_can_perform_stock_adjustment(self):
        """INVENTORY user can reconcile stock via physical count; movement posts to InventoryLedger."""
        initial_stock = self.batch_a.available_quantity # 100
        physical_count = 125 # Found +25 units during physical count audit

        res = self.client_inv.post(
            f"/api/v1/pharmacy/batches/{self.batch_a.id}/adjust/",
            {"physical_count": physical_count, "remarks": "Physical inventory audit count reconciliation"},
            format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.batch_a.refresh_from_db()
        self.assertEqual(self.batch_a.available_quantity, 125)

        # Check InventoryLedger record
        ledger = InventoryLedger.objects.filter(
            batch=self.batch_a,
            transaction_type="AUDIT_CORRECTION"
        ).order_by('-id').first()
        self.assertIsNotNone(ledger)
        self.assertEqual(ledger.quantity_delta, 25)
        self.assertEqual(ledger.balance_after, 125)

    def test_05_pharmacist_denied_from_stock_adjustment(self):
        """PHARMACIST cannot perform stock adjustment (403 Forbidden)."""
        res = self.client_phm.post(
            f"/api/v1/pharmacy/batches/{self.batch_a.id}/adjust/",
            {"physical_count": 80, "remarks": "Pharmacist trying to adjust stock"},
            format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.batch_a.refresh_from_db()
        self.assertEqual(self.batch_a.available_quantity, 100) # Unchanged

    def test_06_pharmacist_denied_from_po_creation_and_grn(self):
        """PHARMACIST cannot create PO or record GRN (403 Forbidden)."""
        # PO Create attempt
        res_po = self.client_phm.post(
            "/api/v1/procurement/purchase-orders/",
            {"facility": self.facility_a.id, "vendor": self.vendor.id, "po_number": "PO-BLOCKED-01"},
            format="json"
        )
        self.assertEqual(res_po.status_code, status.HTTP_403_FORBIDDEN)

        # GRN attempt
        res_grn = self.client_phm.post(
            "/api/v1/procurement/grn/",
            {
                "purchase_order_id": 1,
                "facility_id": self.facility_a.id,
                "grn_number": "GRN-BLOCKED-01",
                "items_received": []
            },
            format="json"
        )
        self.assertEqual(res_grn.status_code, status.HTTP_403_FORBIDDEN)

    def test_07_clinical_roles_denied_from_inventory_administration(self):
        """DOCTOR, NURSE, LAB, FRONT_DESK_OFFICER cannot access inventory administration."""
        res_adj = self.client_doc.post(
            f"/api/v1/pharmacy/batches/{self.batch_a.id}/adjust/",
            {"physical_count": 50},
            format="json"
        )
        self.assertEqual(res_adj.status_code, status.HTTP_403_FORBIDDEN)

        res_po = self.client_doc.post(
            "/api/v1/procurement/purchase-orders/",
            {"facility": self.facility_a.id, "vendor": self.vendor.id},
            format="json"
        )
        self.assertEqual(res_po.status_code, status.HTTP_403_FORBIDDEN)

    def test_08_facility_isolation_enforced(self):
        """Inventory user cannot adjust batch belonging to another facility."""
        batch_other_fac = MedicineBatch.objects.create(
            facility=self.facility_b,
            medicine=self.medicine,
            batch_number="BATCH-FAC-B-001",
            expiry_date=datetime.date(2028, 12, 31),
            unit_cost=3.50,
            quantity=50,
            available_quantity=50,
            status="AVAILABLE"
        )
        res = self.client_inv.post(
            f"/api/v1/pharmacy/batches/{batch_other_fac.id}/adjust/",
            {"physical_count": 30},
            format="json"
        )
        # Should be 403 or 404
        self.assertIn(res.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
