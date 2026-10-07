"""
Phase 27.1: Inventory Role Foundation & Boundary Tests.

Verifies:
1. INVENTORY exists in RoleChoices and RoleMaster as an independent operational role.
2. No composite roles (PHARMACY_INVENTORY, INVENTORY_PHARMACIST, STORE_PHARMACIST) exist.
3. INVENTORY-only user receives inventory & procurement permissions and is blocked from clinical/dispensing.
4. PHARMACIST-only user retains prescription & dispensing permissions + stock read, but is blocked from inventory administration & procurement.
5. Dual-role user (INVENTORY + PHARMACIST) receives clean union of permissions via two independent StaffRoleAssignment records.
6. Role lifecycle (active/inactive) properly governs permissions without cross-contamination.
7. REST API endpoints enforce the role boundaries:
   - PO create and GRN create blocked for Pharmacy-only user (403).
   - Dispensation and Prescription verification blocked for Inventory-only user (403).
   - Batch read permitted for both roles (200).
   - Dual-role user permitted for both workflows.
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
import datetime

from apps.accounts.models import (
    User, RoleChoices, RoleMaster, PermissionMaster, RolePermission,
    Person, StaffProfile, StaffRoleAssignment
)
from apps.accounts.services import seed_roles_and_permissions
from apps.accounts.permissions import (
    has_role_permission, get_user_role_permissions, get_user_active_role_codes
)
from apps.facilities.models import Facility
from apps.geography.models import State, District
from apps.pharmacy.models import Vendor, PurchaseOrder, MedicineMaster, MedicineBatch
from apps.visits.models import Visit
from apps.consultations.models import Consultation, Prescription, PrescriptionItem
from apps.patients.models import Patient


class InventoryRoleFoundationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        seed_roles_and_permissions()

        # Geography & Facility
        self.state = State.objects.create(name="Karnataka", code="KA")
        self.district = District.objects.create(name="Bengaluru Urban", code="KA-BLR", state=self.state)
        self.facility = Facility.objects.create(
            facility_code="PHC-INV-01",
            facility_name="Namma Clinic Inventory Test Facility",
            facility_type="PRIMARY_HEALTH_CENTRE",
            district=self.district,
            state=self.state
        )

        self.role_inventory = RoleMaster.objects.get(code="INVENTORY")
        self.role_pharmacist = RoleMaster.objects.get(code="PHARMACIST")

        # 1. Inventory-Only Staff
        self.person_inv = Person.objects.create(
            first_name="Ramesh", last_name="Kumar", gender="MALE",
            date_of_birth=datetime.date(1985, 3, 15), phone_number="9844001001"
        )
        self.profile_inv = StaffProfile.objects.create(
            person=self.person_inv, employee_id="STF-INV-01", designation="Inventory Manager", status="ACTIVE"
        )
        self.user_inv = User.objects.create_user(
            username="test_inventory_user", password="Password123!",
            staff_profile=self.profile_inv, assigned_facility=self.facility, role=RoleChoices.INVENTORY
        )
        self.sra_inv = StaffRoleAssignment.objects.create(
            staff=self.profile_inv, role=self.role_inventory, facility=self.facility, is_active=True
        )

        # 2. Pharmacy-Only Staff
        self.person_pharm = Person.objects.create(
            first_name="Pooja", last_name="Hegde", gender="FEMALE",
            date_of_birth=datetime.date(1990, 7, 20), phone_number="9844002002"
        )
        self.profile_pharm = StaffProfile.objects.create(
            person=self.person_pharm, employee_id="STF-PHM-01", designation="Pharmacist", status="ACTIVE"
        )
        self.user_pharm = User.objects.create_user(
            username="test_pharmacist_user", password="Password123!",
            staff_profile=self.profile_pharm, assigned_facility=self.facility, role=RoleChoices.PHARMACIST
        )
        self.sra_pharm = StaffRoleAssignment.objects.create(
            staff=self.profile_pharm, role=self.role_pharmacist, facility=self.facility, is_active=True
        )

        # 3. Dual-Role Staff (Inventory + Pharmacy)
        self.person_dual = Person.objects.create(
            first_name="Anand", last_name="Rao", gender="MALE",
            date_of_birth=datetime.date(1988, 11, 5), phone_number="9844003003"
        )
        self.profile_dual = StaffProfile.objects.create(
            person=self.person_dual, employee_id="STF-DUAL-01", designation="Pharmacist & Store Keeper", status="ACTIVE"
        )
        self.user_dual = User.objects.create_user(
            username="test_dual_user", password="Password123!",
            staff_profile=self.profile_dual, assigned_facility=self.facility, role=RoleChoices.PHARMACIST
        )
        # Note: TWO INDEPENDENT StaffRoleAssignment records on the same StaffProfile!
        self.sra_dual_inv = StaffRoleAssignment.objects.create(
            staff=self.profile_dual, role=self.role_inventory, facility=self.facility, is_active=True
        )
        self.sra_dual_pharm = StaffRoleAssignment.objects.create(
            staff=self.profile_dual, role=self.role_pharmacist, facility=self.facility, is_active=True
        )

        # Domain Test Data
        self.vendor = Vendor.objects.create(
            vendor_name="Karnataka Antibiotics Ltd",
            facility=self.facility,
            contact_person="V. Murthy",
            phone="9845012345"
        )
        self.medicine = MedicineMaster.objects.create(
            generic_name="Paracetamol",
            brand_name="Dolo 650",
            strength="650mg",
            dosage_form="TABLET"
        )
        self.batch = MedicineBatch.objects.create(
            medicine=self.medicine,
            facility=self.facility,
            batch_number="BATCH-INV-001",
            expiry_date=datetime.date.today() + datetime.timedelta(days=365),
            available_quantity=200,
            quantity=200,
            unit_cost=1.50
        )
        self.patient = Patient.objects.create(
            patient_id="PAT-TEST-2701",
            name="Vijay Kumar",
            gender="MALE",
            mobile="9988776655",
            address="Bengaluru",
            district=self.district,
            registered_at_facility=self.facility
        )
        self.visit = Visit.objects.create(
            visit_id="VIS-TEST-2701",
            patient=self.patient,
            facility=self.facility,
            status="IN_CONSULTATION"
        )
        self.consultation = Consultation.objects.create(
            visit=self.visit,
            patient=self.patient,
            doctor=self.user_pharm,
            facility=self.facility,
            chief_complaint="Fever",
            diagnosis_name="Viral Fever"
        )
        self.prescription = Prescription.objects.create(
            consultation=self.consultation,
            patient=self.patient,
            facility=self.facility,
            doctor=self.user_pharm,
            status="PENDING_VERIFICATION"
        )
        self.prescription_item = PrescriptionItem.objects.create(
            prescription=self.prescription,
            medicine=self.medicine,
            medicine_name="Paracetamol",
            quantity=10,
            dosage="1-0-1"
        )

    def test_01_authoritative_role_catalogue_has_inventory_role(self):
        """1. INVENTORY role exists in RoleChoices and RoleMaster."""
        self.assertIn("INVENTORY", RoleChoices.values)
        self.assertTrue(RoleMaster.objects.filter(code="INVENTORY").exists())
        role = RoleMaster.objects.get(code="INVENTORY")
        self.assertIn(role.name, ["Inventory Officer", "Inventory Manager"])
        self.assertEqual(role.scope_level, "FACILITY")
        self.assertTrue(role.is_active)

    def test_02_composite_roles_are_strictly_forbidden(self):
        """2. No composite roles exist in RoleChoices or RoleMaster."""
        forbidden_roles = ["PHARMACY_INVENTORY", "INVENTORY_PHARMACIST", "STORE_PHARMACIST"]
        for role_code in forbidden_roles:
            self.assertNotIn(role_code, RoleChoices.values)
            self.assertFalse(RoleMaster.objects.filter(code=role_code).exists())

    def test_03_inventory_only_user_permissions(self):
        """3. INVENTORY-only user has inventory & procurement perms, denied clinical & dispensing."""
        perms = get_user_role_permissions(self.user_inv)
        active_roles = get_user_active_role_codes(self.user_inv)

        self.assertEqual(active_roles, {"INVENTORY"})

        # Allowed Inventory & Procurement permissions
        expected_inventory_perms = {
            "inventory.read", "inventory.adjust", "medicine_batch.read",
            "purchase_order.create", "purchase_order.read", "purchase_order.update",
            "goods_receipt.create"
        }
        for p in expected_inventory_perms:
            self.assertIn(p, perms, f"Inventory user must have {p}")
            self.assertTrue(has_role_permission(self.user_inv, p))

        # Denied Clinical & Dispensing permissions
        denied_perms = {
            "prescription.read", "prescription.verify", "prescription.hold",
            "prescription.reject", "dispensation.create", "dispensation.read"
        }
        for p in denied_perms:
            self.assertNotIn(p, perms, f"Inventory user must NOT have {p}")
            self.assertFalse(has_role_permission(self.user_inv, p))

    def test_04_pharmacist_only_user_permissions(self):
        """4. PHARMACIST-only user has clinical & dispensing perms + read stock, denied inventory admin."""
        perms = get_user_role_permissions(self.user_pharm)
        active_roles = get_user_active_role_codes(self.user_pharm)

        self.assertEqual(active_roles, {"PHARMACIST"})

        # Allowed Clinical & Dispensing permissions
        expected_pharm_perms = {
            "prescription.read", "prescription.verify", "prescription.hold",
            "prescription.reject", "dispensation.create", "dispensation.read",
            "inventory.read", "medicine_batch.read"
        }
        for p in expected_pharm_perms:
            self.assertIn(p, perms, f"Pharmacist must have {p}")
            self.assertTrue(has_role_permission(self.user_pharm, p))

        # Denied Inventory Administration & Procurement permissions
        denied_inventory_perms = {
            "inventory.adjust", "goods_receipt.create",
            "purchase_order.create", "purchase_order.read", "purchase_order.update"
        }
        for p in denied_inventory_perms:
            self.assertNotIn(p, perms, f"Pharmacist must NOT have {p}")
            self.assertFalse(has_role_permission(self.user_pharm, p))

    def test_05_dual_role_user_permission_union(self):
        """5. StaffProfile with two independent StaffRoleAssignment records has exact union of permissions."""
        active_roles = get_user_active_role_codes(self.user_dual)
        self.assertEqual(active_roles, {"INVENTORY", "PHARMACIST"})

        perms = get_user_role_permissions(self.user_dual)

        # Has both Inventory permissions...
        self.assertTrue(has_role_permission(self.user_dual, "inventory.adjust"))
        self.assertTrue(has_role_permission(self.user_dual, "goods_receipt.create"))
        self.assertTrue(has_role_permission(self.user_dual, "purchase_order.create"))

        # ...and Pharmacy dispensing permissions!
        self.assertTrue(has_role_permission(self.user_dual, "dispensation.create"))
        self.assertTrue(has_role_permission(self.user_dual, "prescription.verify"))

        # Inactive role lifecycle: deactivating INVENTORY revokes only inventory admin perms
        self.sra_dual_inv.is_active = False
        self.sra_dual_inv.save()

        active_roles_after = get_user_active_role_codes(self.user_dual)
        self.assertEqual(active_roles_after, {"PHARMACIST"})
        self.assertFalse(has_role_permission(self.user_dual, "goods_receipt.create"))
        self.assertFalse(has_role_permission(self.user_dual, "inventory.adjust"))
        # Pharmacy permissions remain intact!
        self.assertTrue(has_role_permission(self.user_dual, "dispensation.create"))
        self.assertTrue(has_role_permission(self.user_dual, "prescription.verify"))

    def test_06_api_inventory_only_user_blocked_from_dispensing(self):
        """6. API: INVENTORY-only user gets 403 Forbidden when attempting to dispense."""
        self.client.force_authenticate(user=self.user_inv)
        payload = {
            "prescription_id": self.prescription.id,
            "facility_id": self.facility.id,
            "items": [{"prescription_item_id": self.prescription_item.id, "batch_id": self.batch.id, "quantity": 5}]
        }
        res = self.client.post("/api/v1/pharmacy/dispensations/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_07_api_inventory_only_user_blocked_from_verifying_prescription(self):
        """7. API: INVENTORY-only user gets 403 Forbidden when attempting to verify prescription."""
        self.client.force_authenticate(user=self.user_inv)
        res = self.client.post(f"/api/v1/pharmacy/prescriptions/{self.prescription.id}/verify/", {"notes": "Test"})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_08_api_pharmacist_blocked_from_creating_purchase_order(self):
        """8. API: PHARMACIST-only user gets 403 Forbidden when attempting to create a Purchase Order."""
        self.client.force_authenticate(user=self.user_pharm)
        payload = {
            "facility": self.facility.id,
            "vendor": self.vendor.id,
            "order_date": str(datetime.date.today()),
            "po_number": "PO-TEST-403"
        }
        res = self.client.post("/api/v1/procurement/purchase-orders/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_09_api_pharmacist_blocked_from_creating_goods_receipt(self):
        """9. API: PHARMACIST-only user gets 403 Forbidden when attempting to record a Goods Receipt Note."""
        po = PurchaseOrder.objects.create(
            facility=self.facility,
            vendor=self.vendor,
            po_number="PO-TEST-002",
            status="APPROVED"
        )
        self.client.force_authenticate(user=self.user_pharm)
        payload = {
            "purchase_order_id": po.id,
            "facility_id": self.facility.id,
            "grn_number": "GRN-TEST-403",
            "items_received": [{
                "medicine_id": self.medicine.id,
                "batch_number": "BATCH-NEW-01",
                "expiry_date": str(datetime.date.today() + datetime.timedelta(days=365)),
                "unit_cost": 2.0,
                "quantity_received": 100,
                "quantity_accepted": 100,
                "quantity_rejected": 0
            }]
        }
        res = self.client.post("/api/v1/procurement/grn/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_10_api_inventory_only_user_allowed_purchase_order_creation(self):
        """10. API: INVENTORY-only user successfully creates Purchase Order."""
        self.client.force_authenticate(user=self.user_inv)
        payload = {
            "facility": self.facility.id,
            "vendor": self.vendor.id,
            "order_date": str(datetime.date.today()),
            "po_number": "PO-INV-201"
        }
        res = self.client.post("/api/v1/procurement/purchase-orders/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["po_number"], "PO-INV-201")

    def test_11_api_stock_batches_viewable_by_both_roles(self):
        """11. API: Both INVENTORY and PHARMACY users can read medicine batches."""
        # Pharmacist can view batches (needed for dispensing)
        self.client.force_authenticate(user=self.user_pharm)
        res_pharm = self.client.get("/api/v1/pharmacy/batches/")
        self.assertEqual(res_pharm.status_code, status.HTTP_200_OK)

        # Inventory user can view batches
        self.client.force_authenticate(user=self.user_inv)
        res_inv = self.client.get("/api/v1/pharmacy/batches/")
        self.assertEqual(res_inv.status_code, status.HTTP_200_OK)
