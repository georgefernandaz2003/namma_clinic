"""
Procurement Domain Services.
Decoupled procurement workflows for Purchase Orders, Multi-Tier Approvals, and Goods Receipt Notes (GRN).
Maintains clear separation:
- Procurement owns purchase agreements, approvals, vendor fulfillment, and receiving inspection.
- Inventory accounting is delegated authoritatively to `post_inventory_movement`.
"""
import uuid
import datetime
from django.db import transaction
from apps.pharmacy.models import (
    PurchaseOrder, PurchaseOrderItem, PurchaseOrderApproval,
    GoodsReceiptNote, GoodsReceiptItem, MedicineBatch, MedicineMaster
)
from apps.common.exceptions import (
    DomainValidationError,
    UnauthorizedDomainAction,
    InvalidProcurementStateError
)
from apps.audit.services import record_audit_event


def create_purchase_order(
    facility,
    vendor,
    created_by_staff=None,
    po_number=None,
    items=None
):
    """
    Creates a new PurchaseOrder in DRAFT status with optional initial line items.
    PO creation does NOT alter inventory stock.
    """
    if created_by_staff and created_by_staff.status != "ACTIVE":
        raise UnauthorizedDomainAction("Inactive staff cannot create purchase orders.")

    today = datetime.date.today()
    num = po_number or f"PO-{today.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    with transaction.atomic():
        po = PurchaseOrder.objects.create(
            facility=facility,
            vendor=vendor,
            po_number=num,
            order_date=today,
            status="DRAFT"
        )

        if items:
            for itm in items:
                PurchaseOrderItem.objects.create(
                    purchase_order=po,
                    medicine=itm["medicine"],
                    ordered_quantity=itm["ordered_quantity"],
                    unit_price=itm["unit_price"],
                    total_price=itm["unit_price"] * itm["ordered_quantity"]
                )

        record_audit_event(
            actor_staff=created_by_staff,
            actor_role_snapshot=created_by_staff.designation if created_by_staff else "SYSTEM",
            facility=facility,
            action_type="CREATE",
            table_name="purchase_orders",
            record_id=po.id,
            payload_after={"po_number": po.po_number, "status": po.status}
        )
        return po


def approve_purchase_order(
    purchase_order,
    approver_staff,
    approval_tier=1,
    status="APPROVED",
    remarks=""
):
    """
    Records an auditable procurement approval.
    PO creation and approval alone DO NOT mutate inventory balance.
    """
    if not approver_staff or approver_staff.status != "ACTIVE":
        raise UnauthorizedDomainAction("Only active staff may approve purchase orders.")

    if PurchaseOrderApproval.objects.filter(purchase_order=purchase_order, approval_tier=approval_tier).exists():
        raise InvalidProcurementStateError(
            purchase_order.id,
            f"Approval Tier {approval_tier} has already been recorded for PO #{purchase_order.po_number}."
        )

    with transaction.atomic():
        approval = PurchaseOrderApproval.objects.create(
            purchase_order=purchase_order,
            approver_staff=approver_staff,
            approval_tier=approval_tier,
            status=status,
            remarks=remarks
        )

        if status == "APPROVED":
            purchase_order.status = "APPROVED"
            purchase_order.save(update_fields=["status"])

        record_audit_event(
            actor_staff=approver_staff,
            actor_role_snapshot=approver_staff.designation,
            facility=purchase_order.facility,
            action_type="UPDATE",
            table_name="purchase_orders",
            record_id=purchase_order.id,
            payload_after={"status": purchase_order.status, "approval_tier": approval_tier}
        )
        return approval


def receive_goods_receipt(
    purchase_order,
    grn_number,
    items_received,
    receiving_staff,
    facility
):
    """
    Processes Goods Receipt Note (GRN) for a Purchase Order.
    Atomically creates batches and delegates stock posting to `post_inventory_movement`.
    """
    from apps.pharmacy.services import post_inventory_movement

    if not receiving_staff or receiving_staff.status != "ACTIVE":
        raise UnauthorizedDomainAction("Only active staff may receive goods receipts.")

    if purchase_order.status not in ["APPROVED", "ORDERED", "PARTIALLY_RECEIVED"]:
        raise InvalidProcurementStateError(
            purchase_order.id,
            f"Cannot receive goods for PO #{purchase_order.po_number} in status '{purchase_order.status}'."
        )

    if not items_received:
        raise DomainValidationError("Cannot process a GRN with empty received items.")

    with transaction.atomic():
        grn = GoodsReceiptNote.objects.create(
            purchase_order=purchase_order,
            vendor=purchase_order.vendor,
            grn_number=grn_number,
            facility=facility,
            received_date=datetime.date.today(),
            received_by=None
        )

        for entry in items_received:
            med = entry["medicine"]
            bn = entry["batch_number"]
            exp = entry["expiry_date"]
            cost = entry.get("unit_cost", 1.50)
            qty_rec = entry["quantity_received"]
            qty_acc = entry["quantity_accepted"]
            qty_rej = entry.get("quantity_rejected", 0)

            if exp <= datetime.date.today():
                raise DomainValidationError(f"Cannot accept expired batch '{bn}' with expiry date {exp}.")

            po_item = entry.get("po_item")
            if not po_item:
                po_item = PurchaseOrderItem.objects.filter(purchase_order=purchase_order, medicine=med).first()
                if not po_item:
                    po_item = PurchaseOrderItem.objects.create(
                        purchase_order=purchase_order,
                        medicine=med,
                        ordered_quantity=entry.get("ordered_quantity", qty_rec),
                        unit_price=cost,
                        total_price=cost * qty_rec
                    )

            GoodsReceiptItem.objects.create(
                grn=grn,
                po_item=po_item,
                medicine=med,
                batch_number=bn,
                expiry_date=exp,
                unit_cost=cost,
                ordered_quantity=entry.get("ordered_quantity", qty_rec),
                received_quantity=qty_rec,
                accepted_quantity=qty_acc,
                rejected_quantity=qty_rej,
                rejection_reason=entry.get("rejection_reason", ""),
            )

            if qty_acc > 0:
                batch, _ = MedicineBatch.objects.get_or_create(
                    facility=facility,
                    medicine=med,
                    batch_number=bn,
                    defaults={
                        "expiry_date": exp,
                        "unit_cost": cost,
                        "vendor": purchase_order.vendor,
                        "quantity": 0,
                        "available_quantity": 0
                    }
                )

                post_inventory_movement(
                    batch=batch,
                    facility=facility,
                    performed_by_staff=receiving_staff,
                    transaction_type="PURCHASE_RECEIPT",
                    quantity_delta=qty_acc,
                    reference_entity_type="GoodsReceiptNote",
                    reference_entity_id=grn.id,
                    remarks=f"GRN #{grn.grn_number} from PO #{purchase_order.po_number}",
                    bucket_deltas={"available_quantity": qty_acc}
                )

        purchase_order.status = "PARTIALLY_RECEIVED"
        purchase_order.save(update_fields=["status"])

        record_audit_event(
            actor_staff=receiving_staff,
            actor_role_snapshot=receiving_staff.designation,
            facility=facility,
            action_type="CREATE",
            table_name="goods_receipt_notes",
            record_id=grn.id,
            payload_after={"grn_number": grn.grn_number, "po_number": purchase_order.po_number}
        )
        return grn
