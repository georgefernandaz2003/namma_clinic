from django.db import migrations, models


def reconcile_procurement_data_forward(apps, schema_editor):
    PurchaseOrder = apps.get_model('pharmacy', 'PurchaseOrder')
    PurchaseOrderItem = apps.get_model('pharmacy', 'PurchaseOrderItem')
    GoodsReceiptItem = apps.get_model('pharmacy', 'GoodsReceiptItem')

    # 1. Controlled cleanup/correction of zero-item approved POs (no silent deletion)
    zero_item_pos = PurchaseOrder.objects.annotate(item_count=models.Count('items')).filter(item_count=0)
    for po in zero_item_pos:
        if po.status in ['APPROVED', 'ORDERED', 'PENDING_APPROVAL']:
            po.status = 'CANCELLED'
            po.notes = f"{po.notes} [Audit Correction: Zero-item PO cancelled with audit reason during procurement hardening]".strip()
            po.save()

    # 2. Reconcile total_amount on all PurchaseOrders
    for po in PurchaseOrder.objects.all():
        items = PurchaseOrderItem.objects.filter(purchase_order=po)
        if items.exists():
            tot = sum(i.ordered_quantity * i.unit_price for i in items)
            if po.total_amount != tot:
                po.total_amount = tot
                po.save()

    # 3. Reconcile accepted_quantity and rejected_quantity on PurchaseOrderItems from GoodsReceiptItems
    for item in PurchaseOrderItem.objects.all():
        grn_items = GoodsReceiptItem.objects.filter(po_item=item)
        if grn_items.exists():
            acc = sum(g.accepted_quantity for g in grn_items)
            rej = sum(g.rejected_quantity for g in grn_items)
            item.accepted_quantity = acc
            item.rejected_quantity = rej
            item.received_quantity = acc + rej
            item.save()
        else:
            if item.purchase_order.status == 'RECEIVED' and item.received_quantity > 0:
                item.accepted_quantity = item.received_quantity
                item.rejected_quantity = 0
                item.save()

    # 4. Reconcile PO status based on resolved quantities
    for po in PurchaseOrder.objects.exclude(status__in=['DRAFT', 'CANCELLED', 'PENDING_APPROVAL', 'PENDING']):
        items = PurchaseOrderItem.objects.filter(purchase_order=po)
        if items.exists():
            all_resolved = all(i.received_quantity >= i.ordered_quantity for i in items)
            any_resolved = any(i.received_quantity > 0 for i in items)
            if all_resolved and po.status != 'RECEIVED':
                po.status = 'RECEIVED'
                po.save()
            elif any_resolved and not all_resolved and po.status != 'PARTIALLY_RECEIVED':
                po.status = 'PARTIALLY_RECEIVED'
                po.save()


def reconcile_procurement_data_backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0007_purchaseorderitem_quantities'),
    ]

    operations = [
        migrations.RunPython(reconcile_procurement_data_forward, reconcile_procurement_data_backward),
    ]
