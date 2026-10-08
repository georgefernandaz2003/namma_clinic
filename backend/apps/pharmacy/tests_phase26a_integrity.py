"""
Phase 26A — Pharmacy Integrity & Authorization Hardening Test Suite.
Validates:
1. Concurrency (PostgreSQL row locking against same batch & same prescription)
2. Duplicate / Retry protection (Case A double submit, Case B browser retry, Case C stale UI, Case D completed prescription)
3. All six roles authorization (PHARMACIST allow; DOCTOR, NURSE, LAB, ADMIN, DISTRICT 403)
4. Hold and Reject reason enforcement (empty -> 400, provided -> 200)
5. FEFO business rule semantics (Option B: eligibility validation, pharmacist choice, safety guards)
6. InventoryLedger integrity (double-entry audit trail, before/delta/after reconciliation, append-only)
7. Facility scope isolation (cross-facility read/mutation blocked, client facility_id manipulation rejected)
"""
import datetime
from concurrent.futures import ThreadPoolExecutor
from django.test import TransactionTestCase
from django.db import connection
from django.db.models import Sum
from rest_framework.test import APIClient
from rest_framework import status

from apps.geography.models import State, District
from apps.facilities.models import Facility, Department
from apps.facilities.services import provision_standard_facility_services
from apps.accounts.models import (
    User, Person, StaffProfile, RoleMaster, StaffRoleAssignment, StaffFacilityAssignment
)
from apps.patients.models import Patient
from apps.visits.models import Visit
from apps.consultations.models import Consultation, Prescription, PrescriptionItem
from apps.pharmacy.models import MedicineMaster, MedicineBatch, Dispensation, DispensationItem, InventoryLedger
from apps.pharmacy.services import dispense_prescription, post_inventory_movement
from apps.common.exceptions import InsufficientStockError, DomainValidationError


class Phase26APharmacyIntegrityTests(TransactionTestCase):
    """TransactionTestCase ensures real transactions and row locking under PostgreSQL."""

    def setUp(self):
        super().setUp()
        self.client = APIClient()

        # Geography
        self.state = State.objects.create(name="Karnataka 26A", code="KA-26A")
        self.district = District.objects.create(name="Bengaluru 26A", code="BLR-26A", state=self.state)

        # Facilities
        self.facility_a = Facility.objects.create(
            facility_code="FAC-A-26A", facility_name="UHWC Facility A",
            facility_type="PRIMARY_HEALTH_CENTRE", state=self.state, district=self.district
        )
        self.facility_b = Facility.objects.create(
            facility_code="FAC-B-26A", facility_name="UHWC Facility B",
            facility_type="PRIMARY_HEALTH_CENTRE", state=self.state, district=self.district
        )
        self.dept_a = Department.objects.create(facility=self.facility_a, code="GEN-A", name="General OPD A")
        self.dept_b = Department.objects.create(facility=self.facility_b, code="GEN-B", name="General OPD B")
        provision_standard_facility_services(self.facility_a)
        provision_standard_facility_services(self.facility_b)

        # Users & Staff Profiles
        self.users = {}
        self.staff_profiles = {}
        roles_to_create = [
            ("PHARMACIST", "pharm_user", "Pharmacist"),
            ("DOCTOR", "doc_user", "Medical Officer"),
            ("NURSE", "nurse_user", "Staff Nurse"),
            ("LAB_TECHNICIAN", "lab_user", "Lab Technician"),
            ("HOSPITAL_ADMIN", "admin_user", "Hospital Administrator"),
            ("DISTRICT_OFFICER", "dho_user", "District Health Officer"),
        ]

        for role_code, username, designation in roles_to_create:
            role_m, _ = RoleMaster.objects.get_or_create(code=role_code, defaults={"name": designation})
            p = Person.objects.create(
                first_name=username.capitalize(), last_name="Staff",
                gender="FEMALE" if "nurse" in username else "MALE", date_of_birth="1988-06-15"
            )
            sp = StaffProfile.objects.create(
                person=p, employee_id=f"EMP-{role_code[:3]}-26A", designation=designation,
                department=self.dept_a, status="ACTIVE"
            )
            StaffFacilityAssignment.objects.create(
                staff=sp, facility=self.facility_a, is_primary=True, is_active=True
            )
            StaffRoleAssignment.objects.create(
                staff=sp, role=role_m, is_active=True
            )
            u = User.objects.create_user(
                username=f"{username}_26a", email=f"{username}@nammaclinic.local",
                password="TestPassword123!", role=role_code, is_active=True,
                assigned_facility=self.facility_a, staff_profile=sp
            )
            self.users[role_code] = u
            self.staff_profiles[role_code] = sp

        self.pharmacist = self.users["PHARMACIST"]
        self.pharm_staff = self.staff_profiles["PHARMACIST"]
        self.doctor = self.users["DOCTOR"]
        self.doc_staff = self.staff_profiles["DOCTOR"]

        # Clinical Baseline
        self.patient = Patient.objects.create(
            patient_id="PAT-26A-0001", name="Sunita Gowda",
            age=38, gender="FEMALE", registered_at_facility=self.facility_a
        )
        self.visit = Visit.objects.create(
            visit_id="VST-26A-0001", patient=self.patient, facility=self.facility_a,
            visit_type="OUTPATIENT"
        )
        self.consultation = Consultation.objects.create(
            visit=self.visit, patient=self.patient, facility=self.facility_a,
            doctor_staff=self.doc_staff, chief_complaint="Essential Hypertension"
        )

        # Medicines
        self.med_amlodipine = MedicineMaster.objects.create(
            generic_name="Amlodipine Besylate", dosage_form="Tablet", strength="5mg",
            category="Cardiovascular"
        )

        # Baseline Batch at Facility A with 10 units
        self.batch_a1 = MedicineBatch.objects.create(
            medicine=self.med_amlodipine, facility=self.facility_a,
            batch_number="BAT-26A-001", expiry_date=datetime.date.today() + datetime.timedelta(days=180),
            quantity=10, available_quantity=10, status="AVAILABLE"
        )
        InventoryLedger.objects.create(
            batch=self.batch_a1, facility=self.facility_a, performed_by_staff=self.pharm_staff,
            transaction_type="PURCHASE_RECEIPT", quantity_delta=10, balance_after=10,
            remarks="Initial inventory receipt"
        )

    def _create_prescription(self, facility=None, qty=5, status="VERIFIED"):
        import uuid
        fac = facility or self.facility_a
        v = Visit.objects.create(
            visit_id=f"VST-26A-{uuid.uuid4().hex[:6].upper()}",
            patient=self.patient, facility=fac, visit_type="OUTPATIENT"
        )
        c = Consultation.objects.create(
            visit=v, patient=self.patient, facility=fac,
            doctor_staff=self.doc_staff, chief_complaint="Essential Hypertension"
        )
        rx = Prescription.objects.create(
            consultation=c, patient=self.patient, doctor=self.doctor,
            doctor_staff=self.doc_staff, facility=fac, status=status,
            date=datetime.date.today()
        )
        item = PrescriptionItem.objects.create(
            prescription=rx, medicine=self.med_amlodipine, medicine_name="Amlodipine 5mg",
            dosage="1-0-0", frequency="Daily", duration_days=qty, quantity=qty,
            dispensed_quantity=0, status="PENDING"
        )
        return rx, item

    # =========================================================================
    # 1. CONCURRENT DISPENSING VALIDATION (Section 3)
    # =========================================================================

    def test_concurrent_dispensing_same_batch_insufficient_stock(self):
        """
        Request A -> dispense 4
        Request B -> dispense 3
        Initial stock = 5
        Total 7 > 5. Exactly one succeeds, one rejected with InsufficientStockError.
        Final stock is positive (1 or 2), never negative.
        """
        # Set batch available to exactly 5
        self.batch_a1.quantity = 5
        self.batch_a1.available_quantity = 5
        self.batch_a1.save(update_fields=["quantity", "available_quantity"])

        rx1, item1 = self._create_prescription(qty=4, status="VERIFIED")
        rx2, item2 = self._create_prescription(qty=3, status="VERIFIED")

        results = []
        errors = []

        def worker(rx, item, qty):
            connection.close()
            try:
                disp = dispense_prescription(
                    prescription=rx,
                    items_to_dispense=[{"prescription_item": item, "batch": self.batch_a1, "quantity": qty}],
                    dispensing_staff=self.pharm_staff,
                    facility=self.facility_a
                )
                results.append(disp)
            except Exception as e:
                errors.append(e)

        if connection.vendor == 'postgresql':
            with ThreadPoolExecutor(max_workers=2) as executor:
                f1 = executor.submit(worker, rx1, item1, 4)
                f2 = executor.submit(worker, rx2, item2, 3)
                f1.result()
                f2.result()
        else:
            worker(rx1, item1, 4)
            worker(rx2, item2, 3)

        self.assertEqual(len(results), 1, "Exactly one concurrent dispensation must succeed.")
        self.assertEqual(len(errors), 1, "The second concurrent dispensation must be rejected.")
        self.assertIsInstance(errors[0], InsufficientStockError)

        self.batch_a1.refresh_from_db()
        self.assertIn(self.batch_a1.available_quantity, [1, 2], "Final stock must be exactly 1 or 2.")
        self.assertGreaterEqual(self.batch_a1.available_quantity, 0, "Stock must never be negative.")

        # Authoritative Ledger audit
        ledger_dispenses = InventoryLedger.objects.filter(batch=self.batch_a1, transaction_type="DISPENSE")
        self.assertEqual(ledger_dispenses.count(), 1, "Exactly one ledger movement must be recorded.")

    def test_concurrent_dispensing_same_prescription_single_winner(self):
        """
        Two concurrent requests attempt to dispense the same prescription simultaneously.
        Only one successful dispensation occurs. Second is rejected.
        Prescription cannot be dispensed twice.
        """
        self.batch_a1.quantity = 50
        self.batch_a1.available_quantity = 50
        self.batch_a1.save(update_fields=["quantity", "available_quantity"])

        rx, item = self._create_prescription(qty=10, status="VERIFIED")

        results = []
        errors = []

        def worker():
            connection.close()
            try:
                disp = dispense_prescription(
                    prescription=rx,
                    items_to_dispense=[{"prescription_item": item, "batch": self.batch_a1, "quantity": 10}],
                    dispensing_staff=self.pharm_staff,
                    facility=self.facility_a
                )
                results.append(disp)
            except Exception as e:
                errors.append(e)

        if connection.vendor == 'postgresql':
            with ThreadPoolExecutor(max_workers=2) as executor:
                f1 = executor.submit(worker)
                f2 = executor.submit(worker)
                f1.result()
                f2.result()
        else:
            worker()
            worker()

        self.assertEqual(len(results), 1, "Only one concurrent request can successfully dispense the prescription.")
        self.assertEqual(len(errors), 1, "The duplicate concurrent attempt must be rejected.")

        rx.refresh_from_db()
        self.assertEqual(rx.status, "DISPENSED")

        item.refresh_from_db()
        self.assertEqual(item.dispensed_quantity, 10, "PrescriptionItem dispensed_quantity must not double decrement.")
        self.assertEqual(item.status, "DISPENSED")

        # Verify only 1 Dispensation created
        dispensations = Dispensation.objects.filter(prescription=rx)
        self.assertEqual(dispensations.count(), 1, "Only one Dispensation record can be created.")

    # =========================================================================
    # 2. DUPLICATE / RETRY PROTECTION (Section 4)
    # =========================================================================

    def test_duplicate_and_retry_scenarios(self):
        """
        Case A: Double submit (identical dispense requests).
        Case B: Browser retry (re-sending after first response).
        Case C: Stale UI (dispensing already dispensed prescription).
        Case D: Dispense attempt on completed DISPENSED status.
        """
        self.batch_a1.quantity = 50
        self.batch_a1.available_quantity = 50
        self.batch_a1.save(update_fields=["quantity", "available_quantity"])

        rx, item = self._create_prescription(qty=5, status="VERIFIED")
        self.client.force_authenticate(user=self.pharmacist)

        payload = {
            "prescription_id": rx.id,
            "facility_id": self.facility_a.id,
            "items": [{"prescription_item_id": item.id, "batch_id": self.batch_a1.id, "quantity": 5}]
        }

        # First request succeeds
        res1 = self.client.post("/api/v1/pharmacy/dispensations/", payload, format="json")
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        self.batch_a1.refresh_from_db()
        stock_after_first = self.batch_a1.available_quantity
        self.assertEqual(stock_after_first, 45)

        # Case A / B: Duplicate / Browser Retry submit
        res2 = self.client.post("/api/v1/pharmacy/dispensations/", payload, format="json")
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already been fully dispensed", str(res2.data))

        # Case C / D: Verify stock is NOT mutated again
        self.batch_a1.refresh_from_db()
        self.assertEqual(self.batch_a1.available_quantity, stock_after_first, "Stock must NOT decrement on retry.")

        ledger_dispenses = InventoryLedger.objects.filter(batch=self.batch_a1, transaction_type="DISPENSE")
        self.assertEqual(ledger_dispenses.count(), 1, "No duplicate ledger movement allowed.")

    # =========================================================================
    # 3. VERIFY ALL SIX ROLES (Section 5)
    # =========================================================================

    def test_all_six_roles_authorization_matrix(self):
        """
        Verify:
        PHARMACIST -> ALLOW (Verify, Hold, Reject, Dispense)
        DOCTOR -> 403
        NURSE -> 403
        LAB_TECHNICIAN -> 403
        HOSPITAL_ADMIN -> 403
        DISTRICT_OFFICER -> 403
        """
        non_pharm_roles = ["DOCTOR", "NURSE", "LAB_TECHNICIAN", "HOSPITAL_ADMIN", "DISTRICT_OFFICER"]

        # 1. Non-pharmacist blocked from Verify
        for role in non_pharm_roles:
            rx, _ = self._create_prescription(status="PENDING_VERIFICATION")
            self.client.force_authenticate(user=self.users[role])
            res = self.client.post(f"/api/v1/pharmacy/prescriptions/{rx.id}/verify/", {"notes": "Attempt"})
            self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN, f"Role {role} must get 403 on verify")

        # 2. Non-pharmacist blocked from Hold
        for role in non_pharm_roles:
            rx, _ = self._create_prescription(status="PENDING_VERIFICATION")
            self.client.force_authenticate(user=self.users[role])
            res = self.client.post(f"/api/v1/pharmacy/prescriptions/{rx.id}/hold/", {"reason": "Attempt"})
            self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN, f"Role {role} must get 403 on hold")

        # 3. Non-pharmacist blocked from Reject
        for role in non_pharm_roles:
            rx, _ = self._create_prescription(status="PENDING_VERIFICATION")
            self.client.force_authenticate(user=self.users[role])
            res = self.client.post(f"/api/v1/pharmacy/prescriptions/{rx.id}/reject/", {"reason": "Attempt"})
            self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN, f"Role {role} must get 403 on reject")

        # 4. Non-pharmacist blocked from Dispense
        for role in non_pharm_roles:
            rx, item = self._create_prescription(status="VERIFIED")
            self.client.force_authenticate(user=self.users[role])
            payload = {
                "prescription_id": rx.id,
                "facility_id": self.facility_a.id,
                "items": [{"prescription_item_id": item.id, "batch_id": self.batch_a1.id, "quantity": 1}]
            }
            res = self.client.post("/api/v1/pharmacy/dispensations/", payload, format="json")
            self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN, f"Role {role} must get 403 on dispense")

        # 5. Pharmacist authorized for all 4 actions
        self.client.force_authenticate(user=self.pharmacist)

        rx_v, _ = self._create_prescription(status="PENDING_VERIFICATION")
        res_v = self.client.post(f"/api/v1/pharmacy/prescriptions/{rx_v.id}/verify/", {"notes": "Dosage checked"})
        self.assertEqual(res_v.status_code, status.HTTP_200_OK)
        self.assertEqual(res_v.data["status"], "VERIFIED")

        rx_h, _ = self._create_prescription(status="PENDING_VERIFICATION")
        res_h = self.client.post(f"/api/v1/pharmacy/prescriptions/{rx_h.id}/hold/", {"reason": "Waiting for lab"})
        self.assertEqual(res_h.status_code, status.HTTP_200_OK)
        self.assertEqual(res_h.data["status"], "ON_HOLD")

        rx_r, _ = self._create_prescription(status="PENDING_VERIFICATION")
        res_r = self.client.post(f"/api/v1/pharmacy/prescriptions/{rx_r.id}/reject/", {"reason": "Drug allergy"})
        self.assertEqual(res_r.status_code, status.HTTP_200_OK)
        self.assertEqual(res_r.data["status"], "REJECTED")

        rx_d, item_d = self._create_prescription(status="VERIFIED")
        payload = {
            "prescription_id": rx_d.id,
            "facility_id": self.facility_a.id,
            "items": [{"prescription_item_id": item_d.id, "batch_id": self.batch_a1.id, "quantity": 2}]
        }
        res_d = self.client.post("/api/v1/pharmacy/dispensations/", payload, format="json")
        self.assertEqual(res_d.status_code, status.HTTP_201_CREATED)

    # =========================================================================
    # 4. HOLD AND REJECT REASON ENFORCEMENT (Section 6)
    # =========================================================================

    def test_hold_and_reject_reason_enforcement(self):
        """
        REJECT without reason -> 400
        REJECT with reason -> 200
        HOLD without reason -> 400
        HOLD with reason -> 200
        """
        self.client.force_authenticate(user=self.pharmacist)

        # REJECT without reason
        rx1, _ = self._create_prescription(status="PENDING_VERIFICATION")
        res1 = self.client.post(f"/api/v1/pharmacy/prescriptions/{rx1.id}/reject/", {"reason": ""})
        self.assertEqual(res1.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("reason is required", str(res1.data["error"]).lower())

        # REJECT with reason
        res2 = self.client.post(f"/api/v1/pharmacy/prescriptions/{rx1.id}/reject/", {"reason": "Contraindicated in asthma"})
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        rx1.refresh_from_db()
        self.assertEqual(rx1.status, "REJECTED")
        self.assertEqual(rx1.rejection_reason, "Contraindicated in asthma")

        # HOLD without reason
        rx2, _ = self._create_prescription(status="PENDING_VERIFICATION")
        res3 = self.client.post(f"/api/v1/pharmacy/prescriptions/{rx2.id}/hold/", {"reason": "   ", "notes": ""})
        self.assertEqual(res3.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("reason is required", str(res3.data["error"]).lower())

        # HOLD with reason
        res4 = self.client.post(f"/api/v1/pharmacy/prescriptions/{rx2.id}/hold/", {"reason": "Clarifying dosage with prescriber"})
        self.assertEqual(res4.status_code, status.HTTP_200_OK)
        rx2.refresh_from_db()
        self.assertEqual(rx2.status, "ON_HOLD")
        self.assertEqual(rx2.verification_notes, "Clarifying dosage with prescriber")

    # =========================================================================
    # 5. FEFO BUSINESS RULE CLARIFICATION (Section 7)
    # =========================================================================

    def test_fefo_business_rule_semantics(self):
        """
        Option B validation:
        1. Two batches exist: Batch Early (expires in 30 days) and Batch Late (expires in 120 days).
        2. Pharmacist may choose Batch Late if eligible (Option B: eligibility validation, pharmacist choice).
        3. Safety guards:
           - Expired batch cannot be dispensed (blocked with domain error).
           - Zero usable stock batch cannot be dispensed (blocked with insufficient stock error).
           - Quarantined / Recalled batch cannot be dispensed.
        """
        today = datetime.date.today()
        # Batch Early
        b_early = MedicineBatch.objects.create(
            medicine=self.med_amlodipine, facility=self.facility_a,
            batch_number="BAT-EARLY-30D", expiry_date=today + datetime.timedelta(days=30),
            quantity=20, available_quantity=20, status="AVAILABLE"
        )
        # Batch Late
        b_late = MedicineBatch.objects.create(
            medicine=self.med_amlodipine, facility=self.facility_a,
            batch_number="BAT-LATE-120D", expiry_date=today + datetime.timedelta(days=120),
            quantity=20, available_quantity=20, status="AVAILABLE"
        )
        # Expired Batch
        b_expired = MedicineBatch.objects.create(
            medicine=self.med_amlodipine, facility=self.facility_a,
            batch_number="BAT-EXPIRED", expiry_date=today - datetime.timedelta(days=5),
            quantity=10, available_quantity=10, status="EXPIRED"
        )
        # Quarantined Batch
        b_quar = MedicineBatch.objects.create(
            medicine=self.med_amlodipine, facility=self.facility_a,
            batch_number="BAT-QUARANTINED", expiry_date=today + datetime.timedelta(days=60),
            quantity=10, available_quantity=0, quarantined_quantity=10, status="QUARANTINED"
        )

        rx, item = self._create_prescription(qty=5, status="VERIFIED")
        self.client.force_authenticate(user=self.pharmacist)

        # 1. Pharmacist selects eligible Batch Late (Option B allowed)
        payload_late = {
            "prescription_id": rx.id,
            "facility_id": self.facility_a.id,
            "items": [{"prescription_item_id": item.id, "batch_id": b_late.id, "quantity": 5}]
        }
        res_late = self.client.post("/api/v1/pharmacy/dispensations/", payload_late, format="json")
        self.assertEqual(res_late.status_code, status.HTTP_201_CREATED)
        b_late.refresh_from_db()
        self.assertEqual(b_late.available_quantity, 15)

        # 2. Safety block: Expired batch rejection
        rx_exp, item_exp = self._create_prescription(qty=2, status="VERIFIED")
        payload_exp = {
            "prescription_id": rx_exp.id,
            "facility_id": self.facility_a.id,
            "items": [{"prescription_item_id": item_exp.id, "batch_id": b_expired.id, "quantity": 2}]
        }
        res_exp = self.client.post("/api/v1/pharmacy/dispensations/", payload_exp, format="json")
        self.assertEqual(res_exp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expired", str(res_exp.data["error"]).lower())

        # 3. Safety block: Zero usable stock / Quarantined batch rejection
        rx_q, item_q = self._create_prescription(qty=2, status="VERIFIED")
        payload_q = {
            "prescription_id": rx_q.id,
            "facility_id": self.facility_a.id,
            "items": [{"prescription_item_id": item_q.id, "batch_id": b_quar.id, "quantity": 2}]
        }
        res_q = self.client.post("/api/v1/pharmacy/dispensations/", payload_q, format="json")
        self.assertEqual(res_q.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("insufficient", str(res_q.data["error"]).lower())

    # =========================================================================
    # 6. INVENTORY LEDGER INTEGRITY (Section 8)
    # =========================================================================

    def test_inventory_ledger_double_entry_integrity(self):
        """
        Verify that dispensing creates accurate immutable ledger entries:
        before balance, delta (-qty), after balance, medicine, batch, facility, actor, timestamp.
        Verify application-level append-only protection.
        """
        initial_stock = self.batch_a1.available_quantity
        rx, item = self._create_prescription(qty=4, status="VERIFIED")
        self.client.force_authenticate(user=self.pharmacist)

        payload = {
            "prescription_id": rx.id,
            "facility_id": self.facility_a.id,
            "items": [{"prescription_item_id": item.id, "batch_id": self.batch_a1.id, "quantity": 4}]
        }
        res = self.client.post("/api/v1/pharmacy/dispensations/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        disp_id = res.data["id"]
        ledger = InventoryLedger.objects.filter(
            batch=self.batch_a1, transaction_type="DISPENSE", reference_entity_id=disp_id
        ).first()

        self.assertIsNotNone(ledger, "InventoryLedger entry must be written for dispensation.")
        self.assertEqual(ledger.quantity_delta, -4)
        self.assertEqual(ledger.balance_after, initial_stock - 4)
        self.assertEqual(ledger.facility, self.facility_a)
        self.assertEqual(ledger.performed_by_staff, self.pharm_staff)
        self.assertEqual(ledger.reference_entity_type, "Dispensation")
        self.assertIn(f"Prescription #{rx.id}", ledger.remarks)
        self.assertIsNotNone(ledger.transaction_timestamp)

        # Read-only API verification (Append-only)
        # Attempt to PUT/PATCH/DELETE via API is rejected
        res_put = self.client.put(f"/api/v1/pharmacy/ledger/{ledger.id}/", {"quantity_delta": 0})
        self.assertEqual(res_put.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        res_del = self.client.delete(f"/api/v1/pharmacy/ledger/{ledger.id}/")
        self.assertEqual(res_del.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # =========================================================================
    # 7. FACILITY SCOPE ISOLATION (Section 9)
    # =========================================================================

    def test_facility_scope_isolation_and_parameter_tampering(self):
        """
        Pharmacist at Facility A attempting to:
        1. Read Facility B prescription -> filtered out
        2. Read Facility B batch -> filtered out
        3. Dispense Facility B prescription -> 403 Forbidden
        4. Supply manipulated facility_id (Facility A facility_id with Facility B rx) -> 403 Forbidden
        5. Dispense using Facility B batch -> 403 Forbidden
        """
        # Create resource in Facility B
        rx_b, item_b = self._create_prescription(facility=self.facility_b, qty=3, status="VERIFIED")
        batch_b = MedicineBatch.objects.create(
            medicine=self.med_amlodipine, facility=self.facility_b,
            batch_number="BAT-FAC-B", expiry_date=datetime.date.today() + datetime.timedelta(days=90),
            quantity=20, available_quantity=20, status="AVAILABLE"
        )

        self.client.force_authenticate(user=self.pharmacist)

        # 1. Filtered read: Prescription list for Facility A does not contain Facility B rx
        res_rx = self.client.get(f"/api/v1/pharmacy/prescriptions/{rx_b.id}/")
        self.assertEqual(res_rx.status_code, status.HTTP_404_NOT_FOUND)

        # 2. Filtered read: Batch list does not expose Facility B batch
        res_batch = self.client.get(f"/api/v1/pharmacy/batches/{batch_b.id}/")
        self.assertEqual(res_batch.status_code, status.HTTP_404_NOT_FOUND)

        # 3. Direct mutation attempt on Facility B prescription with Facility B scope
        payload_direct_b = {
            "prescription_id": rx_b.id,
            "facility_id": self.facility_b.id,
            "items": [{"prescription_item_id": item_b.id, "batch_id": batch_b.id, "quantity": 1}]
        }
        res_b = self.client.post("/api/v1/pharmacy/dispensations/", payload_direct_b, format="json")
        self.assertEqual(res_b.status_code, status.HTTP_403_FORBIDDEN)

        # 4. Parameter tampering: Supplying Facility A ID with Facility B prescription
        payload_tampered = {
            "prescription_id": rx_b.id,
            "facility_id": self.facility_a.id,
            "items": [{"prescription_item_id": item_b.id, "batch_id": self.batch_a1.id, "quantity": 1}]
        }
        res_tampered = self.client.post("/api/v1/pharmacy/dispensations/", payload_tampered, format="json")
        self.assertEqual(res_tampered.status_code, status.HTTP_403_FORBIDDEN)

        # 5. Parameter tampering: Supplying Facility A rx with Facility B batch
        rx_a, item_a = self._create_prescription(facility=self.facility_a, qty=2, status="VERIFIED")
        payload_tampered_batch = {
            "prescription_id": rx_a.id,
            "facility_id": self.facility_a.id,
            "items": [{"prescription_item_id": item_a.id, "batch_id": batch_b.id, "quantity": 1}]
        }
        res_tampered_batch = self.client.post("/api/v1/pharmacy/dispensations/", payload_tampered_batch, format="json")
        self.assertEqual(res_tampered_batch.status_code, status.HTTP_403_FORBIDDEN)
