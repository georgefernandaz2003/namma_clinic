"""
Pharmacy & Inventory Domain Services.
Enforces InventoryLedger as single accounting source of truth, synchronized fast-read buckets,
concurrency row-level locks, multi-batch dispensing, and auditable procurement receipts.
"""
import uuid
import datetime
from django.db import transaction
from django.utils import timezone
from apps.pharmacy.models import (
    MedicineMaster, MedicineBatch, Dispensation,
    DispensationItem, InventoryLedger, Vendor,
    PurchaseOrder, PurchaseOrderItem, PurchaseOrderApproval,
    GoodsReceiptNote, GoodsReceiptItem
)
from apps.consultations.models import Prescription, PrescriptionItem
from apps.common.exceptions import (
    UnauthorizedDomainAction,
    DomainValidationError,
    InsufficientStockError,
    InvalidBatchOperationError,
    InvalidProcurementStateError,
    InvalidStateTransition
)
from apps.audit.services import record_audit_event


def post_inventory_movement(
    batch,
    facility,
    performed_by_staff,
    transaction_type,
    quantity_delta,
    reference_entity_type=None,
    reference_entity_id=None,
    remarks="",
    bucket_deltas=None
):
    """
    Authoritative double-entry stock mutation.
    Posts immutable journal record to InventoryLedger and atomically reconciles
    MedicineBatch fast-read quantity buckets under SELECT FOR UPDATE row lock.
    """
    if not performed_by_staff or performed_by_staff.status != "ACTIVE":
        raise UnauthorizedDomainAction("Only active staff may perform inventory stock movements.")
    with transaction.atomic():
        locked_batch = MedicineBatch.objects.select_for_update().get(pk=batch.pk)
        current_balance = locked_batch.quantity
        new_balance = current_balance + quantity_delta

        if new_balance < 0:
            raise InsufficientStockError(locked_batch.id, abs(quantity_delta), current_balance)

        # Apply bucket adjustments
        if bucket_deltas:
            for bucket, delta in bucket_deltas.items():
                curr_val = getattr(locked_batch, bucket, 0)
                if curr_val + delta < 0:
                    raise InsufficientStockError(locked_batch.id, abs(delta), curr_val)
                setattr(locked_batch, bucket, curr_val + delta)
        else:
            # Default distribution: movements apply directly to available_quantity
            if locked_batch.available_quantity + quantity_delta < 0:
                raise InsufficientStockError(locked_batch.id, abs(quantity_delta), locked_batch.available_quantity)
            locked_batch.available_quantity += quantity_delta

        # Fast-read balance update
        locked_batch.quantity = new_balance
        locked_batch.status = locked_batch.derive_operational_status()
        locked_batch.save()

        # Immutable ledger record creation
        ledger_entry = InventoryLedger.objects.create(
            batch=locked_batch,
            facility=facility,
            performed_by_staff=performed_by_staff,
            transaction_type=transaction_type,
            quantity_delta=quantity_delta,
            balance_after=new_balance,
            reference_entity_type=reference_entity_type,
            reference_entity_id=reference_entity_id,
            remarks=remarks
        )

        return ledger_entry


def quarantine_stock(batch, facility, performed_by_staff, quantity, reason=""):
    """
    Moves stock from available bucket to quarantine hold (physical stock unchanged).
    """
    if quantity <= 0:
        raise DomainValidationError("Quarantine quantity must be positive.")

    with transaction.atomic():
        locked_batch = MedicineBatch.objects.select_for_update().get(pk=batch.pk)
        if locked_batch.available_quantity < quantity:
            raise InsufficientStockError(locked_batch.id, quantity, locked_batch.available_quantity)

        return post_inventory_movement(
            batch=locked_batch,
            facility=facility,
            performed_by_staff=performed_by_staff,
            transaction_type="AUDIT_CORRECTION",
            quantity_delta=0,
            remarks=f"QUARANTINE_HOLD: {reason}".strip(),
            bucket_deltas={"available_quantity": -quantity, "quarantined_quantity": quantity}
        )


def release_quarantined_stock(batch, facility, performed_by_staff, quantity, reason=""):
    """
    Releases stock from quarantine hold back to available usable stock.
    """
    if quantity <= 0:
        raise DomainValidationError("Release quantity must be positive.")

    with transaction.atomic():
        locked_batch = MedicineBatch.objects.select_for_update().get(pk=batch.pk)
        if locked_batch.quarantined_quantity < quantity:
            raise InsufficientStockError(locked_batch.id, quantity, locked_batch.quarantined_quantity)

        return post_inventory_movement(
            batch=locked_batch,
            facility=facility,
            performed_by_staff=performed_by_staff,
            transaction_type="AUDIT_CORRECTION",
            quantity_delta=0,
            remarks=f"QUARANTINE_RELEASE: {reason}".strip(),
            bucket_deltas={"quarantined_quantity": -quantity, "available_quantity": quantity}
        )


def recall_stock(batch, facility, performed_by_staff, quantity, reason=""):
    """
    Moves stock to regulatory recall hold.
    """
    if quantity <= 0:
        raise DomainValidationError("Recall quantity must be positive.")

    with transaction.atomic():
        locked_batch = MedicineBatch.objects.select_for_update().get(pk=batch.pk)
        if locked_batch.available_quantity < quantity:
            raise InsufficientStockError(locked_batch.id, quantity, locked_batch.available_quantity)

        return post_inventory_movement(
            batch=locked_batch,
            facility=facility,
            performed_by_staff=performed_by_staff,
            transaction_type="AUDIT_CORRECTION",
            quantity_delta=0,
            remarks=f"RECALL_HOLD: {reason}".strip(),
            bucket_deltas={"available_quantity": -quantity, "recalled_quantity": quantity}
        )


def damage_stock(batch, facility, performed_by_staff, quantity, reason=""):
    """
    Marks stock as damaged / condemned.
    """
    if quantity <= 0:
        raise DomainValidationError("Damage quantity must be positive.")

    with transaction.atomic():
        locked_batch = MedicineBatch.objects.select_for_update().get(pk=batch.pk)
        if locked_batch.available_quantity < quantity:
            raise InsufficientStockError(locked_batch.id, quantity, locked_batch.available_quantity)

        return post_inventory_movement(
            batch=locked_batch,
            facility=facility,
            performed_by_staff=performed_by_staff,
            transaction_type="DAMAGE_WRITEOFF",
            quantity_delta=0,
            remarks=f"DAMAGED_HOLD: {reason}".strip(),
            bucket_deltas={"available_quantity": -quantity, "damaged_quantity": quantity}
        )


def dispose_stock(batch, facility, performed_by_staff, quantity, from_bucket="damaged_quantity", reason=""):
    """
    Formally disposes / incinerates condemned stock, decrementing total physical inventory on site.
    """
    if quantity <= 0:
        raise DomainValidationError("Disposal quantity must be positive.")

    with transaction.atomic():
        locked_batch = MedicineBatch.objects.select_for_update().get(pk=batch.pk)
        curr_b = getattr(locked_batch, from_bucket, 0)
        if curr_b < quantity:
            raise InsufficientStockError(locked_batch.id, quantity, curr_b)

        return post_inventory_movement(
            batch=locked_batch,
            facility=facility,
            performed_by_staff=performed_by_staff,
            transaction_type="DAMAGE_WRITEOFF",
            quantity_delta=-quantity,
            remarks=f"FORMAL_DISPOSAL from {from_bucket}: {reason}".strip(),
            bucket_deltas={from_bucket: -quantity, "disposed_quantity": quantity}
        )


def dispense_prescription(prescription, items_to_dispense, dispensing_staff, facility):
    """
    Executes prescription medication dispensation.
    items_to_dispense: list of dicts: [{'prescription_item': item, 'batch': batch, 'quantity': qty}]
    """
    if prescription.status not in ["VERIFIED", "ACTIVE", "PARTIALLY_DISPENSED"]:
        raise DomainValidationError(
            f"Prescription #{prescription.id} is in status '{prescription.status}'. Only VERIFIED or ACTIVE prescriptions can be dispensed."
        )

    if not items_to_dispense:
        raise DomainValidationError("No items specified for dispensation.")

    today = datetime.date.today()
    disp_num = f"DISP-{today.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    with transaction.atomic():
        dispensation = Dispensation.objects.create(
            prescription=prescription,
            facility=facility,
            dispensed_by_staff=dispensing_staff,
            dispensation_number=disp_num
        )

        for allocation in items_to_dispense:
            p_item = allocation["prescription_item"]
            batch = allocation["batch"]
            qty = allocation["quantity"]

            if qty <= 0:
                continue

            # Lock prescription item
            locked_item = PrescriptionItem.objects.select_for_update().get(pk=p_item.pk)
            if locked_item.dispensed_quantity + qty > locked_item.quantity:
                raise DomainValidationError(
                    f"Requested dispense quantity ({qty}) exceeds remaining prescribed quantity ({locked_item.remaining_quantity}) for '{locked_item.medicine_name}'."
                )

            # Check batch validity
            locked_batch = MedicineBatch.objects.select_for_update().get(pk=batch.pk)
            if locked_batch.expiry_date <= today:
                raise DomainValidationError(f"Batch '{locked_batch.batch_number}' has expired on {locked_batch.expiry_date}.")

            if locked_batch.available_quantity < qty:
                raise InsufficientStockError(locked_batch.id, qty, locked_batch.available_quantity)

            # Create DispensationItem
            DispensationItem.objects.create(
                dispensation=dispensation,
                prescription_item=locked_item,
                batch=locked_batch,
                quantity_dispensed=qty
            )

            # Deduct stock via authoritative InventoryLedger
            post_inventory_movement(
                batch=locked_batch,
                facility=facility,
                performed_by_staff=dispensing_staff,
                transaction_type="DISPENSE",
                quantity_delta=-qty,
                reference_entity_type="Dispensation",
                reference_entity_id=dispensation.id,
                remarks=f"Prescription #{prescription.id} Dispensation #{dispensation.dispensation_number}",
                bucket_deltas={"available_quantity": -qty}
            )

            # Update item progression
            locked_item.dispensed_quantity += qty
            locked_item.status = "DISPENSED" if locked_item.remaining_quantity == 0 else "PARTIALLY_DISPENSED"
            locked_item.save(update_fields=["dispensed_quantity", "status"])

        # Update prescription overall state
        all_items = prescription.items.all()
        if all(it.status == "DISPENSED" for it in all_items):
            prescription.status = "DISPENSED"
        else:
            prescription.status = "PARTIALLY_DISPENSED"
        prescription.save(update_fields=["status"])

        return dispensation



# Re-export decoupled procurement domain services for backward compatibility
from apps.pharmacy.procurement_services import (
    create_purchase_order,
    approve_purchase_order,
    receive_goods_receipt
)
