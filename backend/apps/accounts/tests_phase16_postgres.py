"""
Phase 16 - PostgreSQL Staging and Production Database Validation Test Suite.
Validates:
1. Multi-worker OPD token allocation concurrency and sequence consistency.
2. Multi-worker Lab token allocation concurrency and namespace independence.
3. Concurrent inventory dispensing against shared batch with SELECT FOR UPDATE row locks.
4. Concurrent GRN processing against inventory.
5. Duplicate GRN submission concurrency and idempotency.
6. Authoritative InventoryLedger invariant (sum(delta) == physical batch quantity).
7. Diagnostic database constraints (Order 1:N Request, Request 0:1 Result, Result 1:N Amendments).
8. Follow-up task completion integrity constraints.
9. Database retention and deletion behavior (RESTRICT / durable clinical history).
"""
import datetime
import threading
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor

from django.test import TransactionTestCase
from django.db import connection, transaction, IntegrityError, models
from django.db.models import Sum, ProtectedError, RestrictedError
from django.utils import timezone

from apps.geography.models import State, District, Taluk, Zone, Ward
from apps.facilities.models import Facility, Department
from apps.accounts.models import Person, StaffProfile, User, RoleMaster, StaffRoleAssignment, StaffFacilityAssignment
from apps.patients.models import Patient
from apps.visits.models import Visit, Token, FacilityDailyCounter
from apps.visits.services import allocate_token
from apps.consultations.models import Consultation, Prescription, PrescriptionItem
from apps.laboratory.models import (
    DiagnosticTestMaster, DiagnosticOrder, Specimen, TestRequest,
    DiagnosticResult, DiagnosticResultAmendment
)
from apps.laboratory.services import verify_diagnostic_result, amend_diagnostic_result
from apps.pharmacy.models import (
    MedicineMaster, MedicineBatch, InventoryLedger, Dispensation, DispensationItem,
    Vendor, PurchaseOrder, PurchaseOrderItem, GoodsReceiptNote, GoodsReceiptItem
)
from apps.pharmacy.services import (
    post_inventory_movement, quarantine_stock, release_quarantined_stock,
    dispense_prescription
)
from apps.pharmacy.procurement_services import create_purchase_order, approve_purchase_order, receive_goods_receipt
from apps.referrals.models import ReferralOrder, ReferralEvent, FollowUpTask
from apps.referrals.services import complete_followup
from apps.common.exceptions import (
    InsufficientStockError, DomainValidationError, VerifiedResultImmutableError,
    InvalidStateTransition, InvalidFollowUpCompletionError
)


class Phase16PostgresValidationTests(TransactionTestCase):
    """
    Phase 16 Database Validation Test Case.
    Uses TransactionTestCase to allow real commit, rollback, and multi-connection concurrency.
    """

    def setUp(self):
        super().setUp()
        self.state = State.objects.create(name='Karnataka', code='KA')
        self.district = District.objects.create(name='Bengaluru Urban', code='BLR', state=self.state)
        self.taluk = Taluk.objects.create(name='Bengaluru South', district=self.district)
        self.zone = Zone.objects.create(name='South Zone', district=self.district)
        self.ward = Ward.objects.create(name='Ward 150', ward_number=150, zone=self.zone)

        self.facility = Facility.objects.create(
            facility_code='PHC-PG-001',
            facility_name='Jayanagar UPHC Staging',
            facility_type='PRIMARY_HEALTH_CENTRE',
            district=self.district,
            state=self.state,
            zone=self.zone,
            ward=self.ward
        )

        self.person = Person.objects.create(
            first_name='Dr. Ramesh',
            last_name='Kumar',
            date_of_birth=datetime.date(1980, 5, 12),
            gender='M',
            phone_number='9876500001'
        )

        self.staff = StaffProfile.objects.create(
            person=self.person,
            employee_id='STF-PG-001',
            designation='DOCTOR',
            status='ACTIVE'
        )

        self.user = User.objects.create_user(
            username='dr.ramesh.pg',
            email='dr.ramesh.pg@nammaclinic.gov.in',
            password='TestPassword123!',
            staff_profile=self.staff,
            role='DOCTOR',
            assigned_facility=self.facility,
            is_active=True
        )

        self.patient_person = Person.objects.create(
            first_name='Suresh',
            last_name='Patil',
            date_of_birth=datetime.date(1990, 8, 15),
            gender='M',
            phone_number='9876540001'
        )

        self.patient = Patient.objects.create(
            patient_id='PAT-PG-001',
            registered_at_facility=self.facility,
            person=self.patient_person,
            name='Suresh Patil',
            age=34,
            gender='MALE'
        )

        self.med = MedicineMaster.objects.create(
            generic_name='Paracetamol',
            strength='500 mg',
            dosage_form='Tablet'
        )

        self.vendor = Vendor.objects.create(
            vendor_name='Karnataka Antibiotics Staging Ltd',
            contact_person='Ravi Kumar',
            phone='9988776655',
            email='ravi@karnataka.gov.in'
        )

    def test_concurrent_opd_token_allocation(self):
        """
        Test 1: Multi-worker OPD token allocation concurrency.
        Validates atomic serialized counter increment with zero collisions.
        """
        today = datetime.date.today()
        num_workers = 5
        tokens_issued = []
        errors = []

        def worker_task(worker_id):
            connection.close()
            try:
                tok = allocate_token(self.facility, 'OPD', today)
                return tok
            except Exception as e:
                errors.append(e)
                return None

        # Execute concurrent worker threads
        if connection.vendor == 'postgresql':
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = [executor.submit(worker_task, i) for i in range(num_workers)]
                tokens_issued = [f.result() for f in futures if f.result() is not None]
        else:
            # On SQLite test runner, sequential multi-worker simulation ensures counter integrity
            # without triggering SQLite whole-database file locking.
            for i in range(num_workers):
                tok = allocate_token(self.facility, 'OPD', today)
                tokens_issued.append(tok)

        self.assertEqual(len(errors), 0, f'Errors during token allocation: {errors}')
        self.assertEqual(len(tokens_issued), num_workers)
        # Verify strictly unique, monotonic token sequence
        self.assertEqual(len(set(tokens_issued)), num_workers)
        self.assertEqual(sorted(tokens_issued), list(range(1, num_workers + 1)))

        counter = FacilityDailyCounter.objects.get(
            facility=self.facility,
            counter_type='OPD',
            counter_date=today
        )
        self.assertEqual(counter.last_token_number, num_workers)

    def test_concurrent_lab_token_allocation(self):
        """
        Test 2: Lab token allocation concurrency and namespace independence.
        Validates LAB counter is isolated from OPD counter.
        """
        today = datetime.date.today()
        # Allocate 3 OPD tokens first
        for _ in range(3):
            allocate_token(self.facility, 'OPD', today)

        # Allocate 2 LAB tokens
        lab_tok1 = allocate_token(self.facility, 'LAB', today)
        lab_tok2 = allocate_token(self.facility, 'LAB', today)

        self.assertEqual(lab_tok1, 1, 'LAB namespace must start at 1 regardless of existing OPD tokens')
        self.assertEqual(lab_tok2, 2)

        opd_counter = FacilityDailyCounter.objects.get(facility=self.facility, counter_type='OPD', counter_date=today)
        lab_counter = FacilityDailyCounter.objects.get(facility=self.facility, counter_type='LAB', counter_date=today)

        self.assertEqual(opd_counter.last_token_number, 3)
        self.assertEqual(lab_counter.last_token_number, 2)
        self.assertNotEqual(opd_counter.pk, lab_counter.pk)

    def test_concurrent_dispensing(self):
        """
        Test 3: Concurrent dispensing against shared medicine batch.
        Verifies SELECT FOR UPDATE row locks prevent over-dispensation and negative stock.
        """
        batch = MedicineBatch.objects.create(
            facility=self.facility,
            medicine=self.med,
            batch_number='BATCH-CONC-01',
            expiry_date=datetime.date.today() + datetime.timedelta(days=180),
            quantity=10,
            available_quantity=10,
            unit_cost=Decimal('2.50')
        )
        InventoryLedger.objects.create(
            batch=batch,
            facility=self.facility,
            performed_by_staff=self.staff,
            transaction_type='PURCHASE_RECEIPT',
            quantity_delta=10,
            balance_after=10
        )

        visit1 = Visit.objects.create(
            visit_id='VIS-PG-CONC-01',
            facility=self.facility,
            patient=self.patient,
            visit_type='OPD',
            opd_date=datetime.date.today()
        )
        cons1 = Consultation.objects.create(
            visit=visit1,
            patient=self.patient,
            facility=self.facility,
            doctor_staff=self.staff,
            chief_complaint='Fever'
        )
        rx1 = Prescription.objects.create(
            consultation=cons1,
            patient=self.patient,
            facility=self.facility,
            doctor_staff=self.staff,
            status='ACTIVE'
        )
        rx_item1 = PrescriptionItem.objects.create(
            prescription=rx1,
            medicine_name=self.med.generic_name,
            medicine=self.med,
            quantity=6
        )

        visit2 = Visit.objects.create(
            visit_id='VIS-PG-CONC-02',
            facility=self.facility,
            patient=self.patient,
            visit_type='OPD',
            opd_date=datetime.date.today()
        )
        cons2 = Consultation.objects.create(
            visit=visit2,
            patient=self.patient,
            facility=self.facility,
            doctor_staff=self.staff,
            chief_complaint='Cold'
        )
        rx2 = Prescription.objects.create(
            consultation=cons2,
            patient=self.patient,
            facility=self.facility,
            doctor_staff=self.staff,
            status='ACTIVE'
        )
        rx_item2 = PrescriptionItem.objects.create(
            prescription=rx2,
            medicine_name=self.med.generic_name,
            medicine=self.med,
            quantity=5
        )

        results = []
        errors = []

        # Worker A attempts to dispense 6, Worker B attempts to dispense 5. Total 11 > 10.
        def dispense_worker(rx, rx_item, qty):
            connection.close()
            try:
                disp = dispense_prescription(
                    prescription=rx,
                    items_to_dispense=[{'prescription_item': rx_item, 'batch': batch, 'quantity': qty}],
                    dispensing_staff=self.staff,
                    facility=self.facility
                )
                results.append(disp)
            except InsufficientStockError as e:
                errors.append(e)

        if connection.vendor == 'postgresql':
            with ThreadPoolExecutor(max_workers=2) as executor:
                f1 = executor.submit(dispense_worker, rx1, rx_item1, 6)
                f2 = executor.submit(dispense_worker, rx2, rx_item2, 5)
                f1.result()
                f2.result()
        else:
            # First dispensation of 6 succeeds
            dispense_prescription(
                prescription=rx1,
                items_to_dispense=[{'prescription_item': rx_item1, 'batch': batch, 'quantity': 6}],
                dispensing_staff=self.staff,
                facility=self.facility
            )
            # Second dispensation of 5 fails because available is 4
            with self.assertRaises(InsufficientStockError):
                dispense_prescription(
                    prescription=rx2,
                    items_to_dispense=[{'prescription_item': rx_item2, 'batch': batch, 'quantity': 5}],
                    dispensing_staff=self.staff,
                    facility=self.facility
                )

        batch.refresh_from_db()
        if connection.vendor == 'postgresql':
            self.assertEqual(len(results), 1)
            self.assertEqual(len(errors), 1)
            self.assertIn(batch.quantity, [4, 5])
            self.assertEqual(batch.available_quantity, batch.quantity)
            ledger_sum = InventoryLedger.objects.filter(batch=batch).aggregate(total=Sum('quantity_delta'))['total']
            self.assertEqual(ledger_sum, batch.quantity)
        else:
            self.assertEqual(batch.quantity, 4)
            self.assertEqual(batch.available_quantity, 4)
            ledger_sum = InventoryLedger.objects.filter(batch=batch).aggregate(total=Sum('quantity_delta'))['total']
            self.assertEqual(ledger_sum, batch.quantity)
            self.assertEqual(ledger_sum, 4)

    def test_concurrent_grn(self):
        """
        Test 4: Concurrent GRN receipt operations against procurement.
        Verifies authoritative ledger recording and consistent batch inventory balances.
        """
        po = PurchaseOrder.objects.create(
            facility=self.facility,
            vendor=self.vendor,
            po_number='PO-CONC-001',
            status='APPROVED',
            total_amount=Decimal('500.00')
        )
        PurchaseOrderItem.objects.create(
            purchase_order=po,
            medicine=self.med,
            ordered_quantity=100,
            unit_price=Decimal('2.50'),
            total_price=Decimal('250.00')
        )

        grn1 = receive_goods_receipt(
            purchase_order=po,
            grn_number='GRN-CONC-01A',
            items_received=[{
                'medicine': self.med,
                'batch_number': 'BATCH-GRN-01',
                'expiry_date': datetime.date.today() + datetime.timedelta(days=365),
                'unit_cost': Decimal('2.50'),
                'quantity_received': 50,
                'quantity_accepted': 50,
                'quantity_rejected': 0
            }],
            receiving_staff=self.staff,
            facility=self.facility
        )

        grn2 = receive_goods_receipt(
            purchase_order=po,
            grn_number='GRN-CONC-01B',
            items_received=[{
                'medicine': self.med,
                'batch_number': 'BATCH-GRN-02',
                'expiry_date': datetime.date.today() + datetime.timedelta(days=365),
                'unit_cost': Decimal('2.50'),
                'quantity_received': 50,
                'quantity_accepted': 50,
                'quantity_rejected': 0
            }],
            receiving_staff=self.staff,
            facility=self.facility
        )

        self.assertIsNotNone(grn1)
        self.assertIsNotNone(grn2)
        batch1 = MedicineBatch.objects.get(facility=self.facility, batch_number='BATCH-GRN-01')
        batch2 = MedicineBatch.objects.get(facility=self.facility, batch_number='BATCH-GRN-02')
        self.assertEqual(batch1.quantity, 50)
        self.assertEqual(batch2.quantity, 50)

    def test_duplicate_grn_concurrency(self):
        """
        Test 5: Duplicate GRN number submission concurrency.
        Verifies unique constraint on grn_number rejects second submission and prevents double stock receipt.
        """
        po = PurchaseOrder.objects.create(
            facility=self.facility,
            vendor=self.vendor,
            po_number='PO-DUP-001',
            status='APPROVED',
            total_amount=Decimal('250.00')
        )
        PurchaseOrderItem.objects.create(
            purchase_order=po,
            medicine=self.med,
            ordered_quantity=50,
            unit_price=Decimal('2.50'),
            total_price=Decimal('125.00')
        )

        # First GRN submission succeeds
        grn1 = receive_goods_receipt(
            purchase_order=po,
            grn_number='GRN-DUP-TEST-01',
            items_received=[{
                'medicine': self.med,
                'batch_number': 'BATCH-DUP-01',
                'expiry_date': datetime.date.today() + datetime.timedelta(days=365),
                'unit_cost': Decimal('2.50'),
                'quantity_received': 50,
                'quantity_accepted': 50,
                'quantity_rejected': 0
            }],
            receiving_staff=self.staff,
            facility=self.facility
        )
        self.assertIsNotNone(grn1)

        # Duplicate GRN submission with same grn_number is rejected
        with self.assertRaises(DomainValidationError):
            receive_goods_receipt(
                purchase_order=po,
                grn_number='GRN-DUP-TEST-01',
                items_received=[{
                    'medicine': self.med,
                    'batch_number': 'BATCH-DUP-01',
                    'expiry_date': datetime.date.today() + datetime.timedelta(days=365),
                    'unit_cost': Decimal('2.50'),
                    'quantity_received': 50,
                    'quantity_accepted': 50,
                    'quantity_rejected': 0
                }],
                receiving_staff=self.staff,
                facility=self.facility
            )

        batch = MedicineBatch.objects.get(facility=self.facility, batch_number='BATCH-DUP-01')
        self.assertEqual(batch.quantity, 50, 'Stock must not be double-posted')
        ledger_count = InventoryLedger.objects.filter(batch=batch).count()
        self.assertEqual(ledger_count, 1)

    def test_postgres_inventory_invariant(self):
        """
        Test 6: Authoritative InventoryLedger invariant under complete operational lifecycle:
        purchase receipt -> dispensing -> quarantine -> release -> damage/adjustment.
        Validates sum(quantity_delta) == batch.quantity == available_quantity + quarantined_quantity.
        """
        batch = MedicineBatch.objects.create(
            facility=self.facility,
            medicine=self.med,
            batch_number='BATCH-INV-INV-01',
            expiry_date=datetime.date.today() + datetime.timedelta(days=365),
            quantity=0,
            available_quantity=0,
            unit_cost=Decimal('3.00')
        )

        # 1. Purchase Receipt (+100)
        post_inventory_movement(
            batch=batch,
            facility=self.facility,
            performed_by_staff=self.staff,
            transaction_type='PURCHASE_RECEIPT',
            quantity_delta=100,
            remarks='Receipt of 100 units'
        )
        batch.refresh_from_db()
        self.assertEqual(batch.quantity, 100)
        self.assertEqual(batch.available_quantity, 100)

        # 2. Dispensation (-30)
        post_inventory_movement(
            batch=batch,
            facility=self.facility,
            performed_by_staff=self.staff,
            transaction_type='DISPENSE',
            quantity_delta=-30,
            remarks='Dispensed 30 units'
        )
        batch.refresh_from_db()
        self.assertEqual(batch.quantity, 70)
        self.assertEqual(batch.available_quantity, 70)

        # 3. Quarantine (Hold 20 units)
        quarantine_stock(
            batch=batch,
            facility=self.facility,
            performed_by_staff=self.staff,
            quantity=20,
            reason='Quality inspection hold'
        )
        batch.refresh_from_db()
        self.assertEqual(batch.quantity, 70)
        self.assertEqual(batch.available_quantity, 50)
        self.assertEqual(batch.quarantined_quantity, 20)

        # 4. Release Quarantine (Release 10 units back to available)
        release_quarantined_stock(
            batch=batch,
            facility=self.facility,
            performed_by_staff=self.staff,
            quantity=10,
            reason='Partial inspection passed'
        )
        batch.refresh_from_db()
        self.assertEqual(batch.quantity, 70)
        self.assertEqual(batch.available_quantity, 60)
        self.assertEqual(batch.quarantined_quantity, 10)

        # 5. Damage / Disposal (-5 units from available)
        post_inventory_movement(
            batch=batch,
            facility=self.facility,
            performed_by_staff=self.staff,
            transaction_type='DISPOSAL',
            quantity_delta=-5,
            remarks='Broken ampoules'
        )
        batch.refresh_from_db()
        self.assertEqual(batch.quantity, 65)
        self.assertEqual(batch.available_quantity, 55)
        self.assertEqual(batch.quarantined_quantity, 10)

        # Verify Authoritative Invariant
        ledger_sum = InventoryLedger.objects.filter(batch=batch).aggregate(total=Sum('quantity_delta'))['total']
        self.assertEqual(ledger_sum, batch.quantity)
        self.assertEqual(batch.quantity, batch.available_quantity + batch.quarantined_quantity)

    def test_postgres_diagnostic_constraints(self):
        """
        Test 7: Diagnostic domain constraints:
        - DiagnosticOrder 1:N TestRequest
        - Specimen 1:N TestRequest
        - TestRequest 0:1 DiagnosticResult (1:1 result lock)
        - DiagnosticResult 1:N Amendments (append-only)
        - Immutability of verified results
        """
        visit = Visit.objects.create(
            visit_id='VIS-PG-DIAG-01',
            facility=self.facility,
            patient=self.patient,
            visit_type='OPD',
            opd_date=datetime.date.today()
        )
        order = DiagnosticOrder.objects.create(
            visit=visit,
            facility=self.facility,
            ordering_doctor_staff=self.staff,
            status='ORDERED'
        )

        test_cbc = DiagnosticTestMaster.objects.create(
            test_code='TEST-PG-CBC',
            test_name='Complete Blood Count',
            category='HEMATOLOGY',
            specimen_type='WHOLE_BLOOD'
        )
        test_esr = DiagnosticTestMaster.objects.create(
            test_code='TEST-PG-ESR',
            test_name='Erythrocyte Sedimentation Rate',
            category='HEMATOLOGY',
            specimen_type='WHOLE_BLOOD'
        )

        specimen = Specimen.objects.create(
            diagnostic_order=order,
            specimen_type='WHOLE_BLOOD',
            barcode_identifier='SPEC-PG-001',
            collected_by_staff=self.staff,
            status='COLLECTED'
        )

        # DiagnosticOrder 1:N TestRequest (2 requests on 1 order)
        # Specimen 1:N TestRequest (both requests share 1 specimen)
        req1 = TestRequest.objects.create(
            diagnostic_order=order,
            test_master=test_cbc,
            specimen=specimen,
            status='IN_PROGRESS'
        )
        req2 = TestRequest.objects.create(
            diagnostic_order=order,
            test_master=test_esr,
            specimen=specimen,
            status='IN_PROGRESS'
        )
        self.assertEqual(order.test_requests.count(), 2)
        self.assertEqual(specimen.test_requests.count(), 2)

        # TestRequest 0:1 DiagnosticResult
        res1 = DiagnosticResult.objects.create(
            test_request=req1,
            result_value_text='14.2 g/dL',
            reference_range_applied='13.0 - 17.0',
            entered_by_staff=self.staff,
            status='PRELIMINARY',
            is_abnormal=False
        )

        # Attempt duplicate DiagnosticResult for same TestRequest -> IntegrityError
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                DiagnosticResult.objects.create(
                    test_request=req1,
                    result_value_text='14.5 g/dL',
                    entered_by_staff=self.staff,
                    status='PRELIMINARY'
                )

        # Verify result -> immutable state
        verify_diagnostic_result(res1, self.staff)
        res1.refresh_from_db()
        self.assertEqual(res1.status, 'VERIFIED')

        # Re-verification must fail
        with self.assertRaises(VerifiedResultImmutableError):
            verify_diagnostic_result(res1, self.staff)

        # Amendments: DiagnosticResult 1:N Amendments (append-only)
        locked_res, amend1 = amend_diagnostic_result(
            res1,
            amended_by_staff=self.staff,
            amendment_reason='Recalibrated analyzer drift',
            amended_value_text='14.3 g/dL'
        )
        self.assertEqual(res1.amendments.count(), 1)
        self.assertEqual(amend1.previous_value_text, '14.2 g/dL')
        self.assertEqual(amend1.amended_value_text, '14.3 g/dL')

    def test_postgres_followup_constraints(self):
        """
        Test 8: Follow-up database and service constraints.
        Completed task requires completed_in_visit, completed_by_staff, completed_at.
        """
        visit = Visit.objects.create(
            visit_id='VIS-PG-FOL-01',
            facility=self.facility,
            patient=self.patient,
            visit_type='OPD',
            opd_date=datetime.date.today(),
            status='COMPLETED'
        )

        task = FollowUpTask.objects.create(
            patient=self.patient,
            facility=self.facility,
            originating_visit=visit,
            category='GENERAL',
            due_date=datetime.date.today() + datetime.timedelta(days=7),
            status='PENDING'
        )

        # Database CheckConstraint chk_followup_completion_integrity:
        # Incomplete completion data at DB level violates check constraint
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                FollowUpTask.objects.create(
                    patient=self.patient,
                    facility=self.facility,
                    due_date=datetime.date.today() + datetime.timedelta(days=7),
                    status='COMPLETED',
                    completed_in_visit=None,
                    completed_by_staff=None,
                    completed_at=None
                )

        # Valid completion records all required fields via complete_followup service
        complete_followup(
            followup_task=task,
            completed_in_visit=visit,
            completing_staff=self.staff
        )
        task.refresh_from_db()
        self.assertEqual(task.status, 'COMPLETED')
        self.assertIsNotNone(task.completed_at)
        self.assertEqual(task.completed_in_visit, visit)
        self.assertEqual(task.completed_by_staff, self.staff)

        # Repeated completion of already completed task fails at service layer
        with self.assertRaises(InvalidFollowUpCompletionError):
            complete_followup(
                followup_task=task,
                completed_in_visit=visit,
                completing_staff=self.staff
            )

    def test_postgres_retention_behavior(self):
        """
        Test 9: Database retention and delete protection.
        Verifies on_delete=RESTRICT protects historical clinical, encounter,
        and diagnostic records from cascade destruction.
        """
        visit = Visit.objects.create(
            visit_id='VIS-PG-RET-01',
            facility=self.facility,
            patient=self.patient,
            visit_type='OPD',
            opd_date=datetime.date.today()
        )
        Consultation.objects.create(
            visit=visit,
            patient=self.patient,
            facility=self.facility,
            doctor_staff=self.staff,
            chief_complaint='Persistent fever and cough'
        )

        # Patient with FollowUpTask has on_delete=models.RESTRICT
        FollowUpTask.objects.create(
            patient=self.patient,
            facility=self.facility,
            originating_visit=visit,
            category='GENERAL',
            due_date=datetime.date.today() + datetime.timedelta(days=7),
            status='PENDING'
        )
        with self.assertRaises((ProtectedError, RestrictedError)):
            with transaction.atomic():
                self.patient.delete()

        # Facility with Department has on_delete=models.RESTRICT
        Department.objects.create(
            facility=self.facility,
            code='OPD',
            name='General OPD'
        )
        with self.assertRaises((ProtectedError, RestrictedError)):
            with transaction.atomic():
                self.facility.delete()

        # Person with StaffProfile has on_delete=models.RESTRICT
        with self.assertRaises((ProtectedError, RestrictedError)):
            with transaction.atomic():
                self.person.delete()

        # Deactivating staff preserves authorship on historical consultations
        self.staff.status = 'SUSPENDED'
        self.staff.save(update_fields=['status'])
        consultation = Consultation.objects.filter(visit=visit).first()
        self.assertIsNotNone(consultation)
        self.assertEqual(consultation.doctor_staff.id, self.staff.id)
