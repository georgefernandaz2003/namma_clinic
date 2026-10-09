"""
Pharmacy & Inventory & Procurement Domain Service Tests (apps/pharmacy/tests_services.py).
Tests authoritative InventoryLedger mutations, fast-read bucket synchronization,
unauthorized inventory mutation, insufficient stock rollback, dispensing rollback,
procurement PO approval, and GRN failure rollback.
"""
import datetime
from decimal import Decimal
from apps.common.tests_base import DomainServiceBaseTestCase
from apps.consultations.models import Prescription, PrescriptionItem
from apps.pharmacy.models import (
    MedicineMaster, MedicineBatch, InventoryLedger, Dispensation, DispensationItem,
    Vendor, PurchaseOrder, PurchaseOrderItem, GoodsReceiptNote, GoodsReceiptItem
)
from apps.pharmacy.services import (
    post_inventory_movement, quarantine_stock, release_quarantined_stock,
    recall_stock, damage_stock, dispose_stock, dispense_prescription
)
from apps.pharmacy.procurement_services import (
    approve_purchase_order, receive_goods_receipt
)
from apps.common.exceptions import (
    UnauthorizedDomainAction, InsufficientStockError, DomainValidationError
)

class PharmacyInventoryProcurementDomainTests(DomainServiceBaseTestCase):
    def setUp(self):
        super().setUp()
        self.med_paracetamol = MedicineMaster.objects.create(generic_name="Paracetamol", strength="500 mg", dosage_form="Tablet")
        self.batch_para = MedicineBatch.objects.create(
            facility=self.clinic_a, medicine=self.med_paracetamol, batch_number="PARA-B1",
            expiry_date=datetime.date.today() + datetime.timedelta(days=180),
            quantity=100, available_quantity=100, quarantined_quantity=0, recalled_quantity=0, damaged_quantity=0
        )

        self.med_amox = MedicineMaster.objects.create(generic_name="Amoxicillin", strength="250 mg", dosage_form="Capsule")
        self.batch_amox = MedicineBatch.objects.create(
            facility=self.clinic_a, medicine=self.med_amox, batch_number="AMOX-B1",
            expiry_date=datetime.date.today() + datetime.timedelta(days=90),
            quantity=10, available_quantity=10, quarantined_quantity=0, recalled_quantity=0, damaged_quantity=0
        )

    def test_unauthorized_inventory_mutation(self):
        """Failure 5: Inactive staff cannot mutate inventory."""
        with self.assertRaises(UnauthorizedDomainAction):
            post_inventory_movement(
                batch=self.batch_para, facility=self.clinic_a, performed_by_staff=self.suspended_staff,
                transaction_type="AUDIT_CORRECTION", quantity_delta=10
            )

    def test_insufficient_inventory_rollback(self):
        """Failure 6 & Rollback: Attempting to deduct more stock than available rolls back completely."""
        initial_balance = self.batch_para.quantity
        initial_ledger_count = InventoryLedger.objects.filter(batch=self.batch_para).count()

        with self.assertRaises(InsufficientStockError):
            post_inventory_movement(
                batch=self.batch_para, facility=self.clinic_a, performed_by_staff=self.doc_staff,
                transaction_type="DISPENSE", quantity_delta=-200
            )

        self.batch_para.refresh_from_db()
        self.assertEqual(self.batch_para.quantity, initial_balance)
        self.assertEqual(InventoryLedger.objects.filter(batch=self.batch_para).count(), initial_ledger_count)

    def test_dispensing_multi_item_insufficient_stock_rollback(self):
        """Failure 8 & Rollback: Multi-item dispensing failure on item 2 rolls back item 1 deductions atomically."""
        rx = Prescription.objects.create(
            consultation=self.consultation, patient=self.patient, facility=self.clinic_a, status="VERIFIED"
        )
        item1 = PrescriptionItem.objects.create(prescription=rx, medicine=self.med_paracetamol, medicine_name="Paracetamol 500mg", quantity=20, dispensed_quantity=0, status="PENDING")
        item2 = PrescriptionItem.objects.create(prescription=rx, medicine=self.med_amox, medicine_name="Amoxicillin 250mg", quantity=50, dispensed_quantity=0, status="PENDING")

        initial_para_avail = self.batch_para.available_quantity
        initial_amox_avail = self.batch_amox.available_quantity
        initial_disp_count = Dispensation.objects.count()

        items_to_dispense = [
            {"prescription_item": item1, "batch": self.batch_para, "quantity": 20},
            {"prescription_item": item2, "batch": self.batch_amox, "quantity": 50}  # Available is only 10 -> will fail!
        ]

        with self.assertRaises(InsufficientStockError):
            dispense_prescription(prescription=rx, items_to_dispense=items_to_dispense, dispensing_staff=self.doc_staff, facility=self.clinic_a)

        # Verify atomic rollback: item1 was NOT deducted, no Dispensation created
        self.batch_para.refresh_from_db()
        self.batch_amox.refresh_from_db()
        self.assertEqual(self.batch_para.available_quantity, initial_para_avail)
        self.assertEqual(self.batch_amox.available_quantity, initial_amox_avail)
        self.assertEqual(Dispensation.objects.count(), initial_disp_count)
        item1.refresh_from_db()
        self.assertEqual(item1.dispensed_quantity, 0)
        self.assertEqual(item1.status, "PENDING")

    def test_grn_failure_rollback(self):
        """Failure 7 & Rollback: GRN with invalid/expired batch aborts and creates no records."""
        vendor = Vendor.objects.create(vendor_name="Karnataka Pharma", facility=self.clinic_a)
        po = PurchaseOrder.objects.create(po_number="PO-TEST-ROLLBACK", vendor=vendor, facility=self.clinic_a, status="APPROVED")
        PurchaseOrderItem.objects.create(purchase_order=po, medicine=self.med_paracetamol, ordered_quantity=500, unit_price=1.0, total_price=500.0)

        initial_grn_count = GoodsReceiptNote.objects.count()
        initial_ledger_count = InventoryLedger.objects.count()

        items_rec = [{
            "medicine": self.med_paracetamol, "batch_number": "EXPIRED-B",
            "expiry_date": datetime.date.today() - datetime.timedelta(days=1),  # Expired -> will raise!
            "unit_cost": 1.0, "quantity_received": 100, "quantity_accepted": 100
        }]

        with self.assertRaises(DomainValidationError):
            receive_goods_receipt(po, "GRN-EXPIRED-FAIL", items_rec, self.doc_staff, self.clinic_a)

        self.assertEqual(GoodsReceiptNote.objects.count(), initial_grn_count)
        self.assertEqual(InventoryLedger.objects.count(), initial_ledger_count)
        po.refresh_from_db()
        self.assertEqual(po.status, "APPROVED")

    def test_partial_dispensing_workflow_and_ledger_accuracy(self):
        """
        Verify partial dispensing workflow:
        1. Prescription with 2 items (10 PCM, 10 AMOX) in PENDING_VERIFICATION can be directly dispensed.
        2. Partial dispense of 10 PCM and 4 AMOX transitions Rx to PARTIALLY_DISPENSED.
        3. Ledger decrements exactly 10 and 4.
        4. Dispensing while ON_HOLD is blocked.
        5. Dispensing remaining 6 AMOX completes prescription to DISPENSED.
        """
        rx = Prescription.objects.create(
            consultation=self.consultation, patient=self.patient, facility=self.clinic_a, status="PENDING_VERIFICATION"
        )
        item1 = PrescriptionItem.objects.create(
            prescription=rx, medicine=self.med_paracetamol, medicine_name="Paracetamol 500mg",
            quantity=10, dispensed_quantity=0, status="PENDING"
        )
        item2 = PrescriptionItem.objects.create(
            prescription=rx, medicine=self.med_amox, medicine_name="Amoxicillin 250mg",
            quantity=10, dispensed_quantity=0, status="PENDING"
        )

        initial_para_avail = self.batch_para.available_quantity
        initial_amox_avail = self.batch_amox.available_quantity

        # 1. Partial dispense: 10 PCM and 4 AMOX
        disp1 = dispense_prescription(
            prescription=rx,
            items_to_dispense=[
                {"prescription_item": item1, "batch": self.batch_para, "quantity": 10},
                {"prescription_item": item2, "batch": self.batch_amox, "quantity": 4},
            ],
            dispensing_staff=self.doc_staff,
            facility=self.clinic_a
        )

        rx.refresh_from_db()
        item1.refresh_from_db()
        item2.refresh_from_db()
        self.batch_para.refresh_from_db()
        self.batch_amox.refresh_from_db()

        self.assertEqual(rx.status, "PARTIALLY_DISPENSED")
        self.assertEqual(item1.dispensed_quantity, 10)
        self.assertEqual(item1.status, "DISPENSED")
        self.assertEqual(item2.dispensed_quantity, 4)
        self.assertEqual(item2.status, "PARTIALLY_DISPENSED")

        # Ledger accuracy
        self.assertEqual(self.batch_para.available_quantity, initial_para_avail - 10)
        self.assertEqual(self.batch_amox.available_quantity, initial_amox_avail - 4)

        ledger_pcm = InventoryLedger.objects.filter(batch=self.batch_para, reference_entity_id=disp1.id).first()
        ledger_amx = InventoryLedger.objects.filter(batch=self.batch_amox, reference_entity_id=disp1.id).first()
        self.assertIsNotNone(ledger_pcm)
        self.assertIsNotNone(ledger_amx)
        self.assertEqual(ledger_pcm.quantity_delta, -10)
        self.assertEqual(ledger_amx.quantity_delta, -4)

        # 2. Block dispense when ON_HOLD
        rx.status = "ON_HOLD"
        rx.save(update_fields=["status"])
        with self.assertRaises(DomainValidationError):
            dispense_prescription(
                prescription=rx,
                items_to_dispense=[{"prescription_item": item2, "batch": self.batch_amox, "quantity": 6}],
                dispensing_staff=self.doc_staff,
                facility=self.clinic_a
            )

        # Release hold
        rx.status = "PARTIALLY_DISPENSED"
        rx.save(update_fields=["status"])

        # 3. Subsequent dispense of remaining 6 AMOX completes the prescription
        disp2 = dispense_prescription(
            prescription=rx,
            items_to_dispense=[{"prescription_item": item2, "batch": self.batch_amox, "quantity": 6}],
            dispensing_staff=self.doc_staff,
            facility=self.clinic_a
        )

        rx.refresh_from_db()
        item2.refresh_from_db()
        self.batch_amox.refresh_from_db()

        self.assertEqual(rx.status, "DISPENSED")
        self.assertEqual(item2.dispensed_quantity, 10)
        self.assertEqual(item2.status, "DISPENSED")
        self.assertEqual(self.batch_amox.available_quantity, initial_amox_avail - 10)
