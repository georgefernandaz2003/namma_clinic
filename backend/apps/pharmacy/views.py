import datetime
from django.db import transaction, models
from django.utils import timezone
from rest_framework import serializers, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.pharmacy.models import (
    MedicineMaster, MedicineBatch, InventoryTransaction,
    Vendor, PurchaseOrder, PurchaseOrderItem,
    GoodsReceiptNote, GoodsReceiptItem, DispensationReturn,
    BatchRecall, PatientCounselling, ColdChainLog
)
from apps.facilities.models import Facility
from apps.consultations.models import Prescription, PrescriptionItem
from apps.audit.models import AuditLog
from apps.alerts.models import Alert
from apps.accounts.permissions import get_accessible_facility_ids_for_user, HasPermission, HasFacilityScope


# -------------------------------------------------------------
# Serializers
# -------------------------------------------------------------

class MedicineMasterSerializer(serializers.ModelSerializer):
    available_stock = serializers.SerializerMethodField()
    stock_status = serializers.SerializerMethodField()

    class Meta:
        model = MedicineMaster
        fields = '__all__'

    def get_available_stock(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        accessible_ids = get_accessible_facility_ids_for_user(user) if user else None

        batches = obj.batches.filter(status__in=['AVAILABLE', 'ACTIVE'])
        if accessible_ids is not None:
            batches = batches.filter(facility_id__in=accessible_ids)

        facility_param = request.query_params.get('facility') if request else None
        if facility_param:
            batches = batches.filter(facility_id=facility_param)

        total = batches.aggregate(total=models.Sum('available_quantity'))['total']
        if total is None:
            # Fallback for batches that may have quantity
            total = batches.aggregate(total=models.Sum('quantity'))['total'] or 0
        return total

    def get_stock_status(self, obj):
        stock = self.get_available_stock(obj)
        if stock == 0:
            return 'OUT_OF_STOCK'
        elif stock <= obj.minimum_stock or stock <= obj.reorder_level:
            return 'LOW_STOCK'
        return 'NORMAL'


class VendorSerializer(serializers.ModelSerializer):
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')
    po_count = serializers.SerializerMethodField()
    pending_orders = serializers.SerializerMethodField()
    completed_orders = serializers.SerializerMethodField()
    total_spend = serializers.SerializerMethodField()
    name = serializers.ReadOnlyField(source='vendor_name')
    vendor_code = serializers.SerializerMethodField()
    gstin = serializers.ReadOnlyField(source='gst_number')
    created_by_name = serializers.ReadOnlyField(source='created_by.full_name')

    class Meta:
        model = Vendor
        fields = '__all__'

    def get_po_count(self, obj):
        return obj.purchase_orders.count()

    def get_pending_orders(self, obj):
        return obj.purchase_orders.filter(status__in=['DRAFT', 'PENDING_APPROVAL', 'PENDING', 'APPROVED', 'ORDERED', 'PARTIALLY_RECEIVED']).count()

    def get_completed_orders(self, obj):
        return obj.purchase_orders.filter(status='RECEIVED').count()

    def get_total_spend(self, obj):
        total = obj.purchase_orders.filter(status__in=['APPROVED', 'ORDERED', 'PARTIALLY_RECEIVED', 'RECEIVED']).aggregate(t=models.Sum('total_amount'))['t'] or 0
        return float(total)

    def get_vendor_code(self, obj):
        return f"VEND-{obj.id:04d}"


class MedicineBatchSerializer(serializers.ModelSerializer):
    medicine_name = serializers.ReadOnlyField(source='medicine.generic_name')
    medicine_brand = serializers.ReadOnlyField(source='medicine.brand_name')
    medicine_unit = serializers.ReadOnlyField(source='medicine.unit')
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')
    vendor_name = serializers.ReadOnlyField(source='vendor.vendor_name')
    is_expired = serializers.SerializerMethodField()
    days_to_expiry = serializers.SerializerMethodField()
    total_physical_stock = serializers.ReadOnlyField()
    is_dispensable = serializers.ReadOnlyField()
    expiry_bucket = serializers.ReadOnlyField()

    class Meta:
        model = MedicineBatch
        fields = '__all__'

    def get_is_expired(self, obj):
        return obj.expiry_date <= datetime.date.today()

    def get_days_to_expiry(self, obj):
        delta = obj.expiry_date - datetime.date.today()
        return delta.days


class GoodsReceiptItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.ReadOnlyField(source='medicine.generic_name')

    class Meta:
        model = GoodsReceiptItem
        fields = '__all__'


class GoodsReceiptNoteSerializer(serializers.ModelSerializer):
    items = GoodsReceiptItemSerializer(many=True, read_only=True)
    vendor_name = serializers.ReadOnlyField(source='vendor.vendor_name')
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')
    received_by_name = serializers.ReadOnlyField(source='received_by.full_name')

    class Meta:
        model = GoodsReceiptNote
        fields = '__all__'


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.ReadOnlyField(source='medicine.generic_name')
    medicine_brand = serializers.ReadOnlyField(source='medicine.brand_name')
    medicine_strength = serializers.ReadOnlyField(source='medicine.strength')
    medicine_unit = serializers.ReadOnlyField(source='medicine.unit')
    remaining_quantity = serializers.ReadOnlyField()
    resolved_quantity = serializers.ReadOnlyField()

    class Meta:
        model = PurchaseOrderItem
        fields = '__all__'


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    goods_receipts = GoodsReceiptNoteSerializer(many=True, read_only=True)
    vendor_name = serializers.ReadOnlyField(source='vendor.vendor_name')
    vendor_code = serializers.SerializerMethodField()
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')
    created_by_name = serializers.ReadOnlyField(source='created_by.full_name')
    approved_by_name = serializers.ReadOnlyField(source='approved_by.full_name')
    rejected_by_name = serializers.ReadOnlyField(source='rejected_by.full_name')
    total_ordered_quantity = serializers.ReadOnlyField()
    total_received_quantity = serializers.ReadOnlyField()
    total_accepted_quantity = serializers.ReadOnlyField()
    total_rejected_quantity = serializers.ReadOnlyField()
    total_remaining_quantity = serializers.ReadOnlyField()

    class Meta:
        model = PurchaseOrder
        fields = '__all__'

    def get_vendor_code(self, obj):
        return f"VEND-{obj.vendor_id:04d}" if obj.vendor_id else None


class InventoryTransactionSerializer(serializers.ModelSerializer):
    medicine_name = serializers.ReadOnlyField(source='medicine.generic_name')
    batch_number = serializers.ReadOnlyField(source='batch.batch_number')
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')
    performed_by_name = serializers.ReadOnlyField(source='created_by.full_name')

    class Meta:
        model = InventoryTransaction
        fields = '__all__'


class DispensationReturnSerializer(serializers.ModelSerializer):
    medicine_name = serializers.ReadOnlyField(source='batch.medicine.generic_name')
    batch_number = serializers.ReadOnlyField(source='batch.batch_number')
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')
    returned_by_name = serializers.ReadOnlyField(source='returned_by.full_name')
    assessed_by_name = serializers.ReadOnlyField(source='assessed_by.full_name')

    class Meta:
        model = DispensationReturn
        fields = '__all__'


class BatchRecallSerializer(serializers.ModelSerializer):
    batch_number = serializers.ReadOnlyField(source='batch.batch_number')
    medicine_name = serializers.ReadOnlyField(source='batch.medicine.generic_name')
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')
    initiated_by_name = serializers.ReadOnlyField(source='initiated_by.full_name')

    class Meta:
        model = BatchRecall
        fields = '__all__'


class PatientCounsellingSerializer(serializers.ModelSerializer):
    pharmacist = serializers.PrimaryKeyRelatedField(read_only=True)
    pharmacist_name = serializers.ReadOnlyField(source='pharmacist.full_name')
    patient_name = serializers.ReadOnlyField(source='patient.name')

    class Meta:
        model = PatientCounselling
        fields = '__all__'


class ColdChainLogSerializer(serializers.ModelSerializer):
    facility = serializers.PrimaryKeyRelatedField(queryset=Facility.objects.all(), required=False)
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')
    recorded_by = serializers.PrimaryKeyRelatedField(read_only=True)
    recorded_by_name = serializers.ReadOnlyField(source='recorded_by.full_name')

    class Meta:
        model = ColdChainLog
        fields = '__all__'


# -------------------------------------------------------------
# ViewSets & APIs
# -------------------------------------------------------------

class MedicineMasterViewSet(viewsets.ModelViewSet):
    queryset = MedicineMaster.objects.all()
    serializer_class = MedicineMasterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class VendorViewSet(viewsets.ModelViewSet):
    serializer_class = VendorSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permissions = {
        'GET': 'vendor.view',
        'POST': 'vendor.create',
        'PUT': 'vendor.update',
        'PATCH': 'vendor.update',
        'DELETE': 'vendor.update'
    }

    def get_queryset(self):
        queryset = Vendor.objects.all().prefetch_related('purchase_orders')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(models.Q(facility_id__in=accessible_ids) | models.Q(facility__isnull=True))
        facility_param = self.request.query_params.get('facility')
        if facility_param:
            queryset = queryset.filter(models.Q(facility_id=facility_param) | models.Q(facility__isnull=True))

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(vendor_name__icontains=search) |
                models.Q(contact_person__icontains=search) |
                models.Q(phone__icontains=search) |
                models.Q(gst_number__icontains=search)
            )

        status_param = self.request.query_params.get('status')
        if status_param and status_param != 'ALL':
            queryset = queryset.filter(status=status_param.upper())

        return queryset

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if 'name' in data and 'vendor_name' not in data:
            data['vendor_name'] = data['name']
        if 'gstin' in data and 'gst_number' not in data:
            data['gst_number'] = data['gstin']
        if 'active' in data and 'status' not in data:
            data['status'] = 'ACTIVE' if data['active'] else 'INACTIVE'
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        user = self.request.user
        facility = user.assigned_facility if user.role != 'DISTRICT_OFFICER' else None
        vendor = serializer.save(created_by=user, facility=facility)
        AuditLog.objects.create(
            user=user,
            username_snapshot=user.username,
            action='VENDOR_CREATED',
            facility=vendor.facility,
            details=f"Created Vendor #{vendor.id}: {vendor.vendor_name}"
        )

    def perform_update(self, serializer):
        vendor = serializer.save()
        AuditLog.objects.create(
            user=self.request.user,
            username_snapshot=self.request.user.username,
            action='VENDOR_UPDATED',
            facility=vendor.facility,
            details=f"Updated Vendor #{vendor.id}: {vendor.vendor_name}"
        )

    def destroy(self, request, *args, **kwargs):
        vendor = self.get_object()
        if vendor.purchase_orders.exists() or vendor.supplied_batches.exists():
            return Response({
                'error': f"Vendor '{vendor.vendor_name}' has associated purchase orders or batch records and cannot be deleted. Please deactivate instead."
            }, status=status.HTTP_400_BAD_REQUEST)

        AuditLog.objects.create(
            user=request.user,
            username_snapshot=request.user.username,
            action='VENDOR_DELETED',
            facility=vendor.facility,
            details=f"Deleted Vendor #{vendor.id}: {vendor.vendor_name}"
        )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        vendor = self.get_object()
        vendor.status = 'INACTIVE' if vendor.status == 'ACTIVE' else 'ACTIVE'
        vendor.save()
        AuditLog.objects.create(
            user=request.user,
            username_snapshot=request.user.username,
            action='VENDOR_STATUS_CHANGED',
            facility=vendor.facility,
            details=f"Vendor #{vendor.id} {vendor.vendor_name} status changed to {vendor.status}"
        )
        return Response({
            'message': f"Vendor '{vendor.vendor_name}' is now {vendor.status}.",
            'status': vendor.status,
            'vendor': VendorSerializer(vendor).data
        })

    @action(detail=True, methods=['get'])
    def purchase_history(self, request, pk=None):
        vendor = self.get_object()
        pos = vendor.purchase_orders.all().select_related('facility', 'created_by', 'approved_by').prefetch_related('items__medicine')
        accessible_ids = get_accessible_facility_ids_for_user(request.user)
        if accessible_ids is not None:
            pos = pos.filter(facility_id__in=accessible_ids)
        serializer = PurchaseOrderSerializer(pos, many=True)
        return Response(serializer.data)


class MedicineBatchViewSet(viewsets.ModelViewSet):
    serializer_class = MedicineBatchSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permissions = {
        'GET': 'inventory.view',
        'POST': 'inventory.create',
        'PUT': 'inventory.update',
        'PATCH': 'inventory.update',
        'DELETE': 'inventory.update'
    }

    def get_queryset(self):
        queryset = MedicineBatch.objects.all().select_related('medicine', 'facility', 'vendor')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        facility_param = self.request.query_params.get('facility')
        if facility_param:
            queryset = queryset.filter(facility_id=facility_param)

        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        medicine_param = self.request.query_params.get('medicine')
        if medicine_param:
            queryset = queryset.filter(medicine_id=medicine_param)

        return queryset

    @action(detail=True, methods=['post'])
    def quarantine(self, request, pk=None):
        """Move quantity from available_quantity to quarantined_quantity (Partial or Full)."""
        if request.user.role not in ['PHARMACIST', 'HOSPITAL_ADMIN']:
            return Response({'error': 'Unauthorized to quarantine stock.'}, status=status.HTTP_403_FORBIDDEN)

        with transaction.atomic():
            batch = MedicineBatch.objects.select_for_update().get(pk=pk)
            qty = int(request.data.get('quantity') or request.data.get('quarantine_quantity') or batch.available_quantity)

            if qty <= 0:
                return Response({'error': 'Quarantine quantity must be greater than zero.'}, status=status.HTTP_400_BAD_REQUEST)
            if qty > batch.available_quantity:
                return Response({'error': f"Cannot quarantine {qty} units. Only {batch.available_quantity} units available."}, status=status.HTTP_400_BAD_REQUEST)

            src_before = batch.available_quantity
            dest_before = batch.quarantined_quantity

            batch.available_quantity -= qty
            batch.quarantined_quantity += qty
            batch.save()

            InventoryTransaction.objects.create(
                facility=batch.facility,
                medicine=batch.medicine,
                batch=batch,
                transaction_type='QUARANTINE_HOLD',
                quantity=qty,
                source_bucket='available_quantity',
                source_before_qty=src_before,
                source_after_qty=batch.available_quantity,
                destination_bucket='quarantined_quantity',
                destination_before_qty=dest_before,
                destination_after_qty=batch.quarantined_quantity,
                reference_id=f"QUAR-{batch.id}-{timezone.now().strftime('%Y%m%d%H%M')}",
                created_by=request.user,
                notes=request.data.get('reason', 'Quality hold / quarantine')
            )

            AuditLog.objects.create(
                user=request.user,
                username_snapshot=request.user.username,
                action='BATCH_QUARANTINED',
                facility=batch.facility,
                details=f"Quarantined {qty} units of Batch {batch.batch_number} ({batch.medicine.generic_name})."
            )

        return Response(MedicineBatchSerializer(batch).data)

    @action(detail=True, methods=['post'])
    def release(self, request, pk=None):
        """Release stock from quarantined or recalled bucket back to available_quantity."""
        if request.user.role not in ['PHARMACIST', 'HOSPITAL_ADMIN']:
            return Response({'error': 'Unauthorized to release held stock.'}, status=status.HTTP_403_FORBIDDEN)

        from_bucket = request.data.get('from_bucket', 'quarantined_quantity')

        with transaction.atomic():
            batch = MedicineBatch.objects.select_for_update().get(pk=pk)
            current_held = batch.quarantined_quantity if from_bucket == 'quarantined_quantity' else batch.recalled_quantity
            qty = int(request.data.get('quantity') or current_held)

            if qty <= 0:
                return Response({'error': 'Release quantity must be greater than zero.'}, status=status.HTTP_400_BAD_REQUEST)
            if qty > current_held:
                return Response({'error': f"Cannot release {qty} units. Only {current_held} units held in {from_bucket}."}, status=status.HTTP_400_BAD_REQUEST)

            src_before = current_held
            dest_before = batch.available_quantity

            if from_bucket == 'quarantined_quantity':
                batch.quarantined_quantity -= qty
                tx_type = 'QUARANTINE_RELEASE'
            else:
                batch.recalled_quantity -= qty
                tx_type = 'RECALL_RELEASE'

            batch.available_quantity += qty
            batch.save()

            InventoryTransaction.objects.create(
                facility=batch.facility,
                medicine=batch.medicine,
                batch=batch,
                transaction_type=tx_type,
                quantity=qty,
                source_bucket=from_bucket,
                source_before_qty=src_before,
                source_after_qty=src_before - qty,
                destination_bucket='available_quantity',
                destination_before_qty=dest_before,
                destination_after_qty=batch.available_quantity,
                reference_id=f"REL-{batch.id}-{timezone.now().strftime('%Y%m%d%H%M')}",
                created_by=request.user,
                notes=request.data.get('reason', 'Quality cleared / release to usable stock')
            )

            AuditLog.objects.create(
                user=request.user,
                username_snapshot=request.user.username,
                action='BATCH_RELEASED',
                facility=batch.facility,
                details=f"Released {qty} units of Batch {batch.batch_number} from {from_bucket} to available stock."
            )

        return Response(MedicineBatchSerializer(batch).data)

    @action(detail=True, methods=['post'])
    def dispose(self, request, pk=None):
        """Condemn and destroy stock from quarantined, damaged, or expired stock."""
        if request.user.role not in ['PHARMACIST', 'HOSPITAL_ADMIN']:
            return Response({'error': 'Unauthorized to dispose stock.'}, status=status.HTTP_403_FORBIDDEN)

        from_bucket = request.data.get('from_bucket', 'quarantined_quantity')

        with transaction.atomic():
            batch = MedicineBatch.objects.select_for_update().get(pk=pk)
            if from_bucket == 'quarantined_quantity':
                current_bucket_qty = batch.quarantined_quantity
            elif from_bucket == 'damaged_quantity':
                current_bucket_qty = batch.damaged_quantity
            elif from_bucket == 'available_quantity':
                current_bucket_qty = batch.available_quantity
            else:
                return Response({'error': f"Invalid source bucket '{from_bucket}' for disposal."}, status=status.HTTP_400_BAD_REQUEST)

            qty = int(request.data.get('quantity') or current_bucket_qty)

            if qty <= 0:
                return Response({'error': 'Disposal quantity must be greater than zero.'}, status=status.HTTP_400_BAD_REQUEST)
            if qty > current_bucket_qty:
                return Response({'error': f"Cannot dispose {qty} units. Only {current_bucket_qty} units in {from_bucket}."}, status=status.HTTP_400_BAD_REQUEST)

            src_before = current_bucket_qty
            dest_before = batch.disposed_quantity

            if from_bucket == 'quarantined_quantity':
                batch.quarantined_quantity -= qty
            elif from_bucket == 'damaged_quantity':
                batch.damaged_quantity -= qty
            elif from_bucket == 'available_quantity':
                batch.available_quantity -= qty

            batch.disposed_quantity += qty
            batch.status = 'DISPOSED' if batch.total_physical_stock == 0 else batch.derive_operational_status()
            batch.save()

            InventoryTransaction.objects.create(
                facility=batch.facility,
                medicine=batch.medicine,
                batch=batch,
                transaction_type='DISPOSAL_DESTROYED',
                quantity=qty,
                source_bucket=from_bucket,
                source_before_qty=src_before,
                source_after_qty=src_before - qty,
                destination_bucket='disposed_quantity',
                destination_before_qty=dest_before,
                destination_after_qty=batch.disposed_quantity,
                reference_id=f"DISP-{batch.id}-{timezone.now().strftime('%Y%m%d%H%M')}",
                created_by=request.user,
                notes=request.data.get('reason', 'Authorized disposal / incineration')
            )

            AuditLog.objects.create(
                user=request.user,
                username_snapshot=request.user.username,
                action='BATCH_DISPOSED',
                facility=batch.facility,
                details=f"Disposed {qty} units from {from_bucket} for Batch {batch.batch_number}."
            )

        return Response(MedicineBatchSerializer(batch).data)


def execute_goods_receipt(request, po, as_grn_direct=False):
    """
    Authoritative Goods Receipt Note (GRN) execution engine:
    - Atomically processes physical intake against Purchase Order
    - Multi-batch per line item support
    - Strict over-receipt guard
    - Real resolution tracking (accepted + rejected)
    - Stock increases ONLY for accepted quantities
    - Generates immutable InventoryTransaction with dual-bucket proof
    - Concurrency protection via row-level locking
    """
    from decimal import Decimal
    if request.user.role in ['DISTRICT_OFFICER', 'DOCTOR', 'NURSE', 'LAB_TECHNICIAN']:
        return Response({'error': f"Role '{request.user.role}' is not authorized to intake goods."}, status=status.HTTP_403_FORBIDDEN)

    accessible_ids = get_accessible_facility_ids_for_user(request.user)
    if accessible_ids is not None and po.facility_id not in accessible_ids:
        return Response({'error': 'Cross-facility Goods Receipt blocked.'}, status=status.HTTP_403_FORBIDDEN)

    if po.status in ['DRAFT', 'PENDING_APPROVAL', 'PENDING']:
        return Response({'error': f"Cannot receive goods for PO in status '{po.status}'. PO must be placed/ordered first."}, status=status.HTTP_400_BAD_REQUEST)
    if po.status == 'CANCELLED':
        return Response({'error': "Cannot receive goods for a CANCELLED purchase order."}, status=status.HTTP_400_BAD_REQUEST)
    if po.status == 'RECEIVED':
        return Response({'error': "Purchase Order is already fully received."}, status=status.HTTP_400_BAD_REQUEST)

    data = request.data
    items_data = data.get('items') or data.get('received_items') or []
    if not items_data:
        return Response({'error': 'At least one item must be received.'}, status=status.HTTP_400_BAD_REQUEST)

    invoice_number = data.get('invoice_number', '').strip()
    invoice_date = data.get('invoice_date') or None
    received_date = data.get('received_date') or datetime.date.today()
    notes = data.get('notes', '')

    with transaction.atomic():
        po = PurchaseOrder.objects.select_for_update().get(pk=po.pk)
        po_item_map = {item.id: item for item in po.items.select_for_update().all()}
        incoming_by_po_item = {}

        validated_lines = []
        for line in items_data:
            po_item_id = line.get('po_item') or line.get('po_item_id') or line.get('item_id')
            if not po_item_id or po_item_id not in po_item_map:
                return Response({'error': f"Invalid or missing PO Item ID '{po_item_id}' for this Purchase Order."}, status=status.HTTP_400_BAD_REQUEST)

            po_item = po_item_map[po_item_id]

            # Quantities resolution
            if 'accepted_quantity' in line:
                accepted_qty = int(line.get('accepted_quantity') or 0)
                rejected_qty = int(line.get('rejected_quantity') or 0)
            elif 'received_quantity' in line or 'received_qty' in line:
                tot_rec = int(line.get('received_quantity') or line.get('received_qty') or 0)
                rej = int(line.get('rejected_quantity') or 0)
                accepted_qty = max(0, tot_rec - rej)
                rejected_qty = rej
            else:
                return Response({'error': f"Quantity information missing for item {po_item.medicine.generic_name}."}, status=status.HTTP_400_BAD_REQUEST)

            if accepted_qty < 0 or rejected_qty < 0:
                return Response({'error': "Accepted and rejected quantities cannot be negative."}, status=status.HTTP_400_BAD_REQUEST)

            received_qty = int(line.get('received_quantity') or (accepted_qty + rejected_qty))
            if accepted_qty + rejected_qty > received_qty:
                return Response({'error': f"Accepted ({accepted_qty}) + Rejected ({rejected_qty}) cannot exceed Received quantity ({received_qty})."}, status=status.HTTP_400_BAD_REQUEST)

            resolved_qty = accepted_qty + rejected_qty
            if resolved_qty <= 0:
                continue

            if rejected_qty > 0 and not str(line.get('rejection_reason', '')).strip():
                return Response({'error': f"Rejection reason is required for rejected quantity on item {po_item.medicine.generic_name}."}, status=status.HTTP_400_BAD_REQUEST)

            batch_number = str(line.get('batch_number', '')).strip()
            if accepted_qty > 0 and not batch_number:
                return Response({'error': f"Batch number is required for accepted quantity on item {po_item.medicine.generic_name}."}, status=status.HTTP_400_BAD_REQUEST)

            expiry_date_str = line.get('expiry_date')
            if accepted_qty > 0:
                if not expiry_date_str:
                    return Response({'error': f"Expiry date is required for accepted quantity on item {po_item.medicine.generic_name}."}, status=status.HTTP_400_BAD_REQUEST)
                try:
                    exp_date = datetime.date.fromisoformat(str(expiry_date_str))
                except ValueError:
                    return Response({'error': f"Invalid expiry date format for item {po_item.medicine.generic_name}."}, status=status.HTTP_400_BAD_REQUEST)
                if exp_date <= datetime.date.today():
                    return Response({'error': f"Expiry date must be in the future for accepted batch {batch_number} ({po_item.medicine.generic_name})."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                exp_date = datetime.date.today() + datetime.timedelta(days=365)

            mfg_date_str = line.get('mfg_date') or None
            mfg_date = None
            if mfg_date_str:
                try:
                    mfg_date = datetime.date.fromisoformat(str(mfg_date_str))
                    if mfg_date > datetime.date.today():
                        return Response({'error': f"Manufacturing date cannot be in the future for {po_item.medicine.generic_name}."}, status=status.HTTP_400_BAD_REQUEST)
                except ValueError:
                    mfg_date = None

            unit_cost = Decimal(str(line.get('unit_cost') or po_item.unit_price or 0.00))

            incoming_by_po_item[po_item_id] = incoming_by_po_item.get(po_item_id, 0) + resolved_qty
            validated_lines.append({
                'po_item': po_item,
                'accepted_qty': accepted_qty,
                'rejected_qty': rejected_qty,
                'received_qty': received_qty,
                'resolved_qty': resolved_qty,
                'batch_number': batch_number,
                'expiry_date': exp_date,
                'mfg_date': mfg_date,
                'unit_cost': unit_cost,
                'rejection_reason': str(line.get('rejection_reason', '')).strip()
            })

        if not validated_lines:
            return Response({'error': 'At least one item with quantity > 0 must be received.'}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Cumulative over-receipt guard
        for po_item_id, incoming_resolved in incoming_by_po_item.items():
            po_item = po_item_map[po_item_id]
            remaining = po_item.remaining_quantity
            if incoming_resolved > remaining:
                return Response({
                    'error': f"Resolved quantity ({incoming_resolved}) exceeds remaining ordered quantity ({remaining}) for {po_item.medicine.generic_name}."
                }, status=status.HTTP_400_BAD_REQUEST)

        # 3. Create GoodsReceiptNote
        today_str = datetime.date.today().strftime('%Y%m%d')
        facility_code = po.facility.facility_code if po.facility else 'FAC'
        grn_count = GoodsReceiptNote.objects.filter(facility=po.facility, created_at__date=datetime.date.today()).count() + 1
        grn_number = f"GRN-{facility_code}-{today_str}-{grn_count:03d}"

        grn = GoodsReceiptNote.objects.create(
            grn_number=grn_number,
            purchase_order=po,
            vendor=po.vendor,
            facility=po.facility,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            received_date=received_date,
            received_by=request.user,
            notes=notes
        )

        total_grn_accepted = 0
        total_grn_rejected = 0

        # 4. Ingest lines
        for vline in validated_lines:
            po_item = vline['po_item']
            acc = vline['accepted_qty']
            rej = vline['rejected_qty']
            total_grn_accepted += acc
            total_grn_rejected += rej

            GoodsReceiptItem.objects.create(
                grn=grn,
                po_item=po_item,
                medicine=po_item.medicine,
                batch_number=vline['batch_number'] or f"REJ-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                mfg_date=vline['mfg_date'],
                expiry_date=vline['expiry_date'],
                ordered_quantity=po_item.ordered_quantity,
                received_quantity=vline['received_qty'],
                rejected_quantity=rej,
                rejection_reason=vline['rejection_reason'],
                accepted_quantity=acc,
                unit_cost=vline['unit_cost']
            )

            # Usable stock entering inventory
            if acc > 0:
                batch, _ = MedicineBatch.objects.select_for_update().get_or_create(
                    facility=po.facility,
                    medicine=po_item.medicine,
                    batch_number=vline['batch_number'],
                    defaults={
                        'vendor': po.vendor,
                        'supplier': po.vendor.vendor_name,
                        'expiry_date': vline['expiry_date'],
                        'mfg_date': vline['mfg_date'],
                        'unit_cost': vline['unit_cost'],
                        'available_quantity': 0,
                        'status': 'AVAILABLE'
                    }
                )
                dest_before = batch.available_quantity
                batch.available_quantity += acc
                batch.save()

                InventoryTransaction.objects.create(
                    facility=po.facility,
                    medicine=po_item.medicine,
                    batch=batch,
                    transaction_type='PURCHASE_RECEIVED',
                    quantity=acc,
                    source_bucket='external_vendor',
                    source_before_qty=0,
                    source_after_qty=0,
                    destination_bucket='available_quantity',
                    destination_before_qty=dest_before,
                    destination_after_qty=batch.available_quantity,
                    reference_id=f"GRN-{grn.grn_number}",
                    created_by=request.user,
                    notes=f"Accepted stock via GRN #{grn.grn_number} for PO #{po.po_number} (Item: {po_item.medicine.generic_name})"
                )

            # Update PO item
            po_item.accepted_quantity += acc
            po_item.rejected_quantity += rej
            po_item.received_quantity += (acc + rej)
            po_item.save()

        # 5. Evaluate GRN status
        if total_grn_rejected == 0:
            grn.status = 'ACCEPTED'
        elif total_grn_accepted > 0 and total_grn_rejected > 0:
            grn.status = 'PARTIAL_ACCEPTANCE'
        else:
            grn.status = 'REJECTED'
        grn.save()

        # 6. Evaluate PO status
        all_resolved = all(i.received_quantity >= i.ordered_quantity for i in po.items.all())
        any_resolved = any(i.received_quantity > 0 for i in po.items.all())
        if all_resolved:
            po.status = 'RECEIVED'
        elif any_resolved:
            po.status = 'PARTIALLY_RECEIVED'
        po.save()

        AuditLog.objects.create(
            user=request.user,
            username_snapshot=request.user.username,
            action='GRN_PROCESSED',
            facility=po.facility,
            details=f"Processed GRN #{grn.grn_number} ({grn.status}) for PO #{po.po_number}. Accepted: {total_grn_accepted}, Rejected: {total_grn_rejected}. PO Status: {po.status}."
        )

        if as_grn_direct:
            return Response(GoodsReceiptNoteSerializer(grn).data, status=status.HTTP_201_CREATED)

        return Response({
            'message': f"Goods Receipt Note #{grn.grn_number} processed successfully! PO status is now {po.status}.",
            'grn': GoodsReceiptNoteSerializer(grn).data,
            'po': PurchaseOrderSerializer(po).data
        }, status=status.HTTP_201_CREATED)


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseOrderSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permissions = {
        'GET': 'po.view',
        'POST': 'po.create',
        'PUT': 'po.update',
        'PATCH': 'po.update',
        'DELETE': 'po.update'
    }

    def get_queryset(self):
        queryset = PurchaseOrder.objects.all().select_related('vendor', 'facility', 'created_by', 'approved_by', 'rejected_by').prefetch_related('items__medicine', 'goods_receipts__items')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        facility_param = self.request.query_params.get('facility')
        if facility_param:
            queryset = queryset.filter(facility_id=facility_param)

        status_param = self.request.query_params.get('status')
        if status_param and status_param != 'ALL':
            queryset = queryset.filter(status=status_param.upper())

        vendor_param = self.request.query_params.get('vendor')
        if vendor_param:
            queryset = queryset.filter(vendor_id=vendor_param)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(po_number__icontains=search) |
                models.Q(vendor__vendor_name__icontains=search) |
                models.Q(notes__icontains=search)
            )

        return queryset

    def create(self, request, *args, **kwargs):
        if request.user.role in ['DISTRICT_OFFICER', 'DOCTOR', 'NURSE', 'LAB_TECHNICIAN']:
            return Response({'error': f"Role '{request.user.role}' is not authorized to create purchase orders."}, status=status.HTTP_403_FORBIDDEN)

        items_data = request.data.get('items', [])
        vendor_id = request.data.get('vendor')
        facility_id = request.user.assigned_facility_id
        if not facility_id:
            return Response({'error': 'User does not have an assigned facility.'}, status=status.HTTP_400_BAD_REQUEST)

        if not vendor_id:
            return Response({'error': 'Vendor is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if not items_data or len(items_data) == 0:
            return Response({'error': 'At least one medicine item is required in the Purchase Order.'}, status=status.HTTP_400_BAD_REQUEST)

        today_str = datetime.date.today().strftime('%Y%m%d')
        facility_code = request.user.assigned_facility.facility_code if request.user.assigned_facility else 'FAC'
        po_count_today = PurchaseOrder.objects.filter(facility_id=facility_id, created_at__date=datetime.date.today()).count() + 1
        po_number = f"PO-{facility_code}-{today_str}-{po_count_today:03d}"

        req_status = request.data.get('status', 'DRAFT')
        if req_status not in ['DRAFT', 'PENDING_APPROVAL', 'PENDING']:
            req_status = 'DRAFT'
        initial_status = 'PENDING_APPROVAL' if req_status in ['PENDING_APPROVAL', 'PENDING'] else 'DRAFT'

        with transaction.atomic():
            po = PurchaseOrder.objects.create(
                po_number=po_number,
                vendor_id=vendor_id,
                facility_id=facility_id,
                order_date=request.data.get('order_date') or datetime.date.today(),
                expected_delivery_date=request.data.get('expected_delivery_date') or None,
                status=initial_status,
                created_by=request.user,
                notes=request.data.get('notes', '')
            )

            total_po_amount = 0
            for item in items_data:
                med_id = item.get('medicine') or item.get('medicine_id')
                qty = int(item.get('ordered_quantity') or item.get('requested_quantity') or 0)
                price = float(item.get('unit_price') or item.get('unit_cost') or 0.0)

                if qty <= 0:
                    return Response({'error': "Item quantity must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)
                if price < 0:
                    return Response({'error': "Unit price cannot be negative."}, status=status.HTTP_400_BAD_REQUEST)

                item_obj = PurchaseOrderItem.objects.create(
                    purchase_order=po,
                    medicine_id=med_id,
                    ordered_quantity=qty,
                    unit_price=price,
                    total_price=qty * price
                )
                total_po_amount += item_obj.total_price

            po.total_amount = total_po_amount
            po.save()

            if initial_status == 'PENDING_APPROVAL':
                Alert.objects.create(
                    facility=po.facility,
                    alert_type='LOW_STOCK',
                    severity='HIGH',
                    title=f"PO {po.po_number} Awaiting Approval",
                    description=f"Purchase Order {po.po_number} for {po.vendor.vendor_name} ({len(items_data)} items, Rs. {total_po_amount:.2f}) requires review & approval."
                )

            AuditLog.objects.create(
                user=request.user,
                username_snapshot=request.user.username,
                action='PURCHASE_ORDER_CREATED',
                facility=po.facility,
                details=f"Created PO #{po.po_number} ({initial_status}) for Vendor {po.vendor.vendor_name}. Items: {len(items_data)}, Total Amount: Rs. {total_po_amount:.2f}"
            )

        return Response(PurchaseOrderSerializer(po).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def submit_approval(self, request, pk=None):
        po = self.get_object()
        if po.status != 'DRAFT':
            return Response({'error': f"Only DRAFT purchase orders can be submitted for approval (current status: '{po.status}')."}, status=status.HTTP_400_BAD_REQUEST)

        if not po.items.exists():
            return Response({'error': "Cannot submit a Purchase Order without items."}, status=status.HTTP_400_BAD_REQUEST)
        for item in po.items.all():
            if item.ordered_quantity <= 0:
                return Response({'error': f"Item {item.medicine.generic_name} must have ordered quantity > 0."}, status=status.HTTP_400_BAD_REQUEST)

        po.recalculate_total()
        po.status = 'PENDING_APPROVAL'
        po.save()

        Alert.objects.create(
            facility=po.facility,
            alert_type='LOW_STOCK',
            severity='HIGH',
            title=f"PO {po.po_number} Awaiting Approval",
            description=f"Purchase Order {po.po_number} submitted by {request.user.full_name or request.user.username} for Rs. {po.total_amount:.2f} is awaiting Hospital Admin approval."
        )

        AuditLog.objects.create(
            user=request.user,
            username_snapshot=request.user.username,
            action='PURCHASE_ORDER_SUBMITTED',
            facility=po.facility,
            details=f"Submitted PO #{po.po_number} for administrative approval."
        )
        return Response({'message': f"Purchase Order #{po.po_number} submitted for approval.", 'po': PurchaseOrderSerializer(po).data})

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        if request.user.role not in ['HOSPITAL_ADMIN']:
            return Response({'error': f"Role '{request.user.role}' is not authorized to approve purchase orders. Approval requires Hospital Admin."}, status=status.HTTP_403_FORBIDDEN)

        po = self.get_object()
        if po.status not in ['PENDING_APPROVAL', 'PENDING', 'DRAFT']:
            return Response({'error': f"Only DRAFT or PENDING_APPROVAL purchase orders can be approved (current status: '{po.status}')."}, status=status.HTTP_400_BAD_REQUEST)

        if not po.items.exists():
            return Response({'error': "Cannot approve a Purchase Order without items."}, status=status.HTTP_400_BAD_REQUEST)
        for item in po.items.all():
            if item.ordered_quantity <= 0:
                return Response({'error': f"Item {item.medicine.generic_name} must have ordered quantity > 0."}, status=status.HTTP_400_BAD_REQUEST)

        po.recalculate_total()
        po.status = 'APPROVED'
        po.approved_by = request.user
        po.approved_at = timezone.now()
        po.save()

        AuditLog.objects.create(
            user=request.user,
            username_snapshot=request.user.username,
            action='PURCHASE_ORDER_APPROVED',
            facility=po.facility,
            details=f"Approved PO #{po.po_number} for Vendor {po.vendor.vendor_name}. Amount: Rs. {po.total_amount:.2f}"
        )
        return Response({'message': f"Purchase Order #{po.po_number} approved successfully.", 'po': PurchaseOrderSerializer(po).data})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        if request.user.role not in ['HOSPITAL_ADMIN']:
            return Response({'error': f"Role '{request.user.role}' is not authorized to reject purchase orders."}, status=status.HTTP_403_FORBIDDEN)

        po = self.get_object()
        if po.status not in ['PENDING_APPROVAL', 'PENDING']:
            return Response({'error': f"Only PENDING_APPROVAL purchase orders can be rejected (current status: '{po.status}')."}, status=status.HTTP_400_BAD_REQUEST)

        reason = request.data.get('reason', 'Rejected by administrator')
        po.status = 'DRAFT'
        po.rejected_by = request.user
        po.rejected_at = timezone.now()
        po.rejection_reason = reason
        po.save()

        AuditLog.objects.create(
            user=request.user,
            username_snapshot=request.user.username,
            action='PURCHASE_ORDER_REJECTED',
            facility=po.facility,
            details=f"Rejected PO #{po.po_number}. Reason: {reason}"
        )
        return Response({'message': f"Purchase Order #{po.po_number} returned to Draft.", 'po': PurchaseOrderSerializer(po).data})

    @action(detail=True, methods=['post'])
    def place_order(self, request, pk=None):
        po = self.get_object()
        if po.status != 'APPROVED':
            return Response({'error': f"Cannot place order for PO in status '{po.status}'. PO must be APPROVED first."}, status=status.HTTP_400_BAD_REQUEST)

        if not po.items.exists():
            return Response({'error': "Cannot place order for a Purchase Order without items."}, status=status.HTTP_400_BAD_REQUEST)

        po.status = 'ORDERED'
        po.save()

        AuditLog.objects.create(
            user=request.user,
            username_snapshot=request.user.username,
            action='PURCHASE_ORDER_ORDERED',
            facility=po.facility,
            details=f"Placed PO #{po.po_number} with Vendor {po.vendor.vendor_name}."
        )
        return Response({'message': f"Purchase Order #{po.po_number} marked as ORDERED with supplier!", 'po': PurchaseOrderSerializer(po).data})

    @action(detail=True, methods=['post'])
    def receive_items(self, request, pk=None):
        po = self.get_object()
        return execute_goods_receipt(request, po=po, as_grn_direct=False)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        po = self.get_object()
        if po.status == 'RECEIVED':
            return Response({'error': "Cannot cancel a fully received purchase order."}, status=status.HTTP_400_BAD_REQUEST)
        if po.status == 'PARTIALLY_RECEIVED':
            return Response({'error': "Cannot cancel a partially received purchase order with accepted stock. Use return/quarantine workflows."}, status=status.HTTP_400_BAD_REQUEST)

        po.status = 'CANCELLED'
        po.notes = f"{po.notes} [Cancelled by {request.user.username} on {datetime.date.today()}]".strip()
        po.save()

        AuditLog.objects.create(
            user=request.user,
            username_snapshot=request.user.username,
            action='PURCHASE_ORDER_CANCELLED',
            facility=po.facility,
            details=f"Cancelled PO #{po.po_number}."
        )
        return Response({'message': f"Purchase Order #{po.po_number} has been cancelled.", 'po': PurchaseOrderSerializer(po).data})

    @action(detail=False, methods=['get'])
    def procurement_summary(self, request):
        qs = self.get_queryset()
        active_pos = qs.filter(status__in=['APPROVED', 'ORDERED', 'PARTIALLY_RECEIVED', 'RECEIVED'])
        committed_val = float(active_pos.aggregate(t=models.Sum('total_amount'))['t'] or 0.0)

        grn_items = GoodsReceiptItem.objects.filter(grn__purchase_order__in=qs)
        received_val = float(grn_items.aggregate(
            t=models.Sum(models.F('accepted_quantity') * models.F('unit_cost'))
        )['t'] or 0.0)

        counts = {
            'draft': qs.filter(status='DRAFT').count(),
            'pending_approval': qs.filter(status__in=['PENDING_APPROVAL', 'PENDING']).count(),
            'approved': qs.filter(status='APPROVED').count(),
            'ordered': qs.filter(status='ORDERED').count(),
            'in_transit': qs.filter(status='ORDERED').count(),
            'partially_received': qs.filter(status='PARTIALLY_RECEIVED').count(),
            'received': qs.filter(status='RECEIVED').count(),
            'cancelled': qs.filter(status='CANCELLED').count(),
            'total_orders': qs.count(),
            'committed_value': committed_val,
            'received_value': received_val,
            'paid_value': 0.00,
            # Backwards compatibility key
            'total_spend': committed_val
        }
        return Response(counts)


class InventoryTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InventoryTransactionSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permissions = {
        'GET': 'inventory.view',
    }

    def get_queryset(self):
        queryset = InventoryTransaction.objects.all().select_related('medicine', 'batch', 'facility', 'created_by').order_by('-created_at')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        facility_param = self.request.query_params.get('facility')
        if facility_param:
            queryset = queryset.filter(facility_id=facility_param)
        return queryset


class DispenseMedicineView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permission = 'pharmacy.dispense'

    def post(self, request):
        if request.user.role in ['DISTRICT_OFFICER', 'DOCTOR', 'NURSE', 'LAB_TECHNICIAN']:
            return Response({'error': f"Role '{request.user.role}' is not authorized to dispense medicines."}, status=status.HTTP_403_FORBIDDEN)

        prescription_id = request.data.get('prescription_id')
        items_to_dispense = request.data.get('items', [])

        if not prescription_id:
            return Response({'error': 'Prescription ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            prescription = Prescription.objects.get(pk=prescription_id)
        except Prescription.DoesNotExist:
            return Response({'error': 'Prescription not found'}, status=status.HTTP_404_NOT_FOUND)

        accessible_ids = get_accessible_facility_ids_for_user(request.user)
        if accessible_ids is not None and prescription.facility_id not in accessible_ids:
            return Response({'error': 'You do not have permission to dispense prescriptions for another facility scope.'}, status=status.HTTP_403_FORBIDDEN)

        # Prescription verification guard: blocked states
        if prescription.status not in ['VERIFIED', 'ACTIVE', 'PARTIALLY_DISPENSED']:
            return Response({
                'error': f"Prescription cannot be dispensed in status '{prescription.status}'. Only VERIFIED or ACTIVE prescriptions can be dispensed."
            }, status=status.HTTP_400_BAD_REQUEST)

        if not items_to_dispense:
            items_to_dispense = [
                {'item_id': pi.id, 'qty': pi.remaining_quantity, 'batch_id': None}
                for pi in prescription.items.exclude(status__in=['DISPENSED', 'CANCELLED'])
            ]

        today = datetime.date.today()
        dispensed_summary = []

        with transaction.atomic():
            for item in items_to_dispense:
                if isinstance(item, str):
                    import json
                    try:
                        item = json.loads(item)
                    except Exception:
                        continue
                if not isinstance(item, dict):
                    continue
                item_id = item.get('item_id')
                batch_id = item.get('batch_id')
                qty = int(item.get('qty') or item.get('qty_to_dispense') or item.get('quantity') or 0)

                if qty <= 0:
                    continue

                if item_id:
                    p_item = PrescriptionItem.objects.select_for_update().filter(pk=item_id, prescription=prescription).first()
                else:
                    med_name_key = item.get('medicine_name', '').split()[0] if item.get('medicine_name') else ''
                    p_item = PrescriptionItem.objects.select_for_update().filter(prescription=prescription, medicine_name__icontains=med_name_key).exclude(status='DISPENSED').first()

                if not p_item:
                    continue

                if p_item.status == 'DISPENSED':
                    return Response({'error': f"Prescription item '{p_item.medicine_name}' has already been fully dispensed."}, status=status.HTTP_400_BAD_REQUEST)

                # Over-dispensing protection
                if p_item.dispensed_quantity + qty > p_item.quantity:
                    return Response({
                        'error': f"Dispense quantity {qty} exceeds remaining prescribed quantity ({p_item.remaining_quantity}) for '{p_item.medicine_name}'."
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Batch selection: specific batch_id vs FEFO automated selection
                if batch_id and int(batch_id) > 0:
                    batch = MedicineBatch.objects.select_for_update().filter(pk=int(batch_id), facility=prescription.facility).first()
                    if not batch:
                        return Response({'error': f"Batch ID {batch_id} not found in facility scope."}, status=status.HTTP_400_BAD_REQUEST)

                    if batch.expiry_date <= today:
                        return Response({'error': f"Batch '{batch.batch_number}' for '{p_item.medicine_name}' HAS EXPIRED on {batch.expiry_date}. Expired stock cannot be dispensed."}, status=status.HTTP_400_BAD_REQUEST)

                    if batch.status in ['QUARANTINED', 'RECALLED', 'DAMAGED', 'DISPOSED', 'EXHAUSTED'] or batch.available_quantity <= 0:
                        return Response({'error': f"Batch '{batch.batch_number}' cannot be dispensed (status: {batch.status}, available: {batch.available_quantity})."}, status=status.HTTP_400_BAD_REQUEST)

                    if qty > batch.available_quantity:
                        return Response({'error': f"Insufficient available stock in batch '{batch.batch_number}'. Requested: {qty}, Available: {batch.available_quantity}."}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # Authoritative FEFO query predicate:
                    # facility match, medicine match, available_quantity > 0, expiry_date > today, status in ['AVAILABLE', 'ACTIVE']
                    med_query = models.Q(medicine=p_item.medicine) if p_item.medicine else models.Q(medicine__generic_name__icontains=p_item.medicine_name.split()[0].lower())
                    batch = MedicineBatch.objects.select_for_update().filter(
                        med_query,
                        facility=prescription.facility,
                        available_quantity__gt=0,
                        expiry_date__gt=today,
                        status__in=['AVAILABLE', 'ACTIVE']
                    ).order_by('expiry_date').first()

                    if not batch:
                        return Response({'error': f"No valid unexpired available stock batch found for '{p_item.medicine_name}' in facility scope."}, status=status.HTTP_400_BAD_REQUEST)

                    if qty > batch.available_quantity:
                        return Response({'error': f"Insufficient available stock in FEFO batch '{batch.batch_number}'. Requested: {qty}, Available: {batch.available_quantity}."}, status=status.HTTP_400_BAD_REQUEST)

                # Atomically deduct stock from available_quantity bucket
                src_before = batch.available_quantity
                batch.available_quantity -= qty
                batch.save()

                # Update prescription item cumulative dispensed quantity
                p_item.dispensed_quantity += qty
                if p_item.dispensed_quantity >= p_item.quantity:
                    p_item.status = 'DISPENSED'
                else:
                    p_item.status = 'PARTIALLY_DISPENSED'
                p_item.save()

                # Record immutable InventoryTransaction with dual-bucket proof
                InventoryTransaction.objects.create(
                    facility=prescription.facility,
                    medicine=batch.medicine,
                    batch=batch,
                    transaction_type='DISPENSED',
                    quantity=qty,
                    source_bucket='available_quantity',
                    source_before_qty=src_before,
                    source_after_qty=batch.available_quantity,
                    destination_bucket='patient_dispensed',
                    destination_before_qty=0,
                    destination_after_qty=qty,
                    patient=prescription.patient,
                    visit=getattr(prescription.consultation, 'visit', None),
                    prescription=prescription,
                    prescription_item=p_item,
                    reference_id=f"PRESCR-{prescription.id}",
                    created_by=request.user,
                    notes=f"Dispensed {qty} units for Patient {prescription.patient.name} (Batch: {batch.batch_number})"
                )

                dispensed_summary.append({
                    'item': p_item.medicine_name,
                    'batch': batch.batch_number,
                    'qty': qty,
                    'remaining_prescribed': p_item.remaining_quantity,
                    'remaining_batch_available': batch.available_quantity
                })

            fresh_items = list(PrescriptionItem.objects.filter(prescription=prescription))
            all_dispensed = all(i.status == 'DISPENSED' for i in fresh_items) if fresh_items else True
            any_dispensed = any(i.status in ['DISPENSED', 'PARTIALLY_DISPENSED'] for i in fresh_items) if fresh_items else False

            prescription.status = 'DISPENSED' if all_dispensed else ('PARTIALLY_DISPENSED' if any_dispensed else prescription.status)
            prescription.save()

            if hasattr(prescription, 'consultation') and prescription.consultation and prescription.consultation.visit:
                v = prescription.consultation.visit
                if all_dispensed:
                    v.current_queue = 'COMPLETED'
                    v.status = 'COMPLETED'
                    v.completed_time = timezone.now()
                    v.save()
                    if hasattr(v, 'token') and v.token:
                        v.token.status = 'COMPLETED'
                        v.token.save()

            AuditLog.objects.create(
                user=request.user,
                username_snapshot=request.user.username,
                action='MEDICINE_DISPENSED',
                facility=prescription.facility,
                details=f"Dispensed Prescription #{prescription.id} for Patient {prescription.patient.name}. Items: {dispensed_summary}"
            )

        return Response({
            'message': 'Medicines successfully dispensed using FEFO rule!',
            'prescription_status': prescription.status,
            'dispensed_items': dispensed_summary
        })


class GoodsReceiptNoteViewSet(viewsets.ModelViewSet):
    serializer_class = GoodsReceiptNoteSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permissions = {
        'GET': 'inventory.view',
        'POST': 'inventory.create',
        'PUT': 'inventory.update',
        'PATCH': 'inventory.update',
        'DELETE': 'inventory.update'
    }

    def get_queryset(self):
        queryset = GoodsReceiptNote.objects.all().select_related('purchase_order', 'vendor', 'facility', 'received_by').prefetch_related('items__medicine')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        facility_param = self.request.query_params.get('facility')
        if facility_param:
            queryset = queryset.filter(facility_id=facility_param)
        return queryset

    def create(self, request, *args, **kwargs):
        po_id = request.data.get('purchase_order') or request.data.get('purchase_order_id')
        if not po_id:
            return Response({'error': 'Purchase Order ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            po = PurchaseOrder.objects.get(pk=po_id)
        except PurchaseOrder.DoesNotExist:
            return Response({'error': 'Purchase Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        return execute_goods_receipt(request, po=po, as_grn_direct=True)


class DispensationReturnViewSet(viewsets.ModelViewSet):
    serializer_class = DispensationReturnSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permissions = {
        'GET': 'inventory.view',
        'POST': 'inventory.create',
        'PUT': 'inventory.update',
        'PATCH': 'inventory.update',
        'DELETE': 'inventory.update'
    }

    def get_queryset(self):
        queryset = DispensationReturn.objects.all().select_related('prescription', 'prescription_item', 'batch', 'facility', 'returned_by', 'assessed_by')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        facility_param = self.request.query_params.get('facility')
        if facility_param:
            queryset = queryset.filter(facility_id=facility_param)
        return queryset

    def create(self, request, *args, **kwargs):
        """Phase 1: Log patient return as PENDING_ASSESSMENT (Usable stock delta is zero)."""
        data = request.data
        p_item_id = data.get('prescription_item') or data.get('prescription_item_id')
        try:
            qty = int(data.get('returned_quantity', 0))
        except (ValueError, TypeError):
            return Response({'error': 'Returned quantity must be a valid integer.'}, status=status.HTTP_400_BAD_REQUEST)

        if not p_item_id or qty <= 0:
            return Response({'error': 'Valid prescription item and returned quantity > 0 are required.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            try:
                p_item = PrescriptionItem.objects.select_for_update().get(pk=p_item_id)
            except PrescriptionItem.DoesNotExist:
                return Response({'error': 'Prescription Item not found.'}, status=status.HTTP_404_NOT_FOUND)

            # Cumulative return cap check: include all non-rejected quantities that reserve/consume the dispensed quantity:
            # PENDING, APPROVED_FOR_STOCK, QUARANTINE, DISPOSAL
            existing_reserved = DispensationReturn.objects.filter(
                prescription_item=p_item,
                disposition__in=['PENDING', 'APPROVED_FOR_STOCK', 'QUARANTINE', 'DISPOSAL']
            ).exclude(
                assessment_status__in=['REJECTED', 'CANCELLED']
            ).exclude(
                disposition__in=['REJECTED', 'CANCELLED']
            ).aggregate(
                t=models.Sum('returned_quantity')
            )['t'] or 0

            if existing_reserved + qty > p_item.dispensed_quantity:
                return Response({
                    'error': f"Cumulative returned quantity ({existing_reserved + qty}) cannot exceed dispensed quantity ({p_item.dispensed_quantity})."
                }, status=status.HTTP_400_BAD_REQUEST)

            batch_id = data.get('batch') or data.get('batch_id')
            batch = MedicineBatch.objects.filter(pk=batch_id).first() if batch_id else None
            if not batch and p_item.medicine:
                batch = p_item.medicine.batches.filter(facility=p_item.prescription.facility).first()

            if not batch:
                return Response({'error': 'Valid medicine batch is required for return.'}, status=status.HTTP_400_BAD_REQUEST)

            import uuid
            ret_number = f"RET-{p_item.prescription.facility.facility_code if p_item.prescription.facility else 'FAC'}-{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

            ret = DispensationReturn.objects.create(
                return_number=ret_number,
                prescription=p_item.prescription,
                prescription_item=p_item,
                batch=batch,
                facility=p_item.prescription.facility,
                returned_quantity=qty,
                return_reason=data.get('return_reason', 'Patient return'),
                returned_by=request.user,
                assessment_status='PENDING_ASSESSMENT',
                disposition='PENDING'
            )

            AuditLog.objects.create(
                user=request.user,
                username_snapshot=request.user.username,
                action='RETURN_LOGGED',
                facility=ret.facility,
                details=f"Logged Return #{ret.return_number} for {qty} units. Pending pharmacist assessment."
            )

            return Response(DispensationReturnSerializer(ret).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def assess(self, request, pk=None):
        """Phase 2: Pharmacist Clinical Assessment and Inventory Disposition."""
        if request.user.role != 'PHARMACIST':
            return Response({'error': 'Only pharmacists are authorized to assess returned medication.'}, status=status.HTTP_403_FORBIDDEN)

        disposition = request.data.get('disposition') or request.data.get('status')
        if disposition not in ['APPROVED_FOR_STOCK', 'QUARANTINE', 'DISPOSAL', 'REJECTED']:
            return Response({'error': f"Invalid disposition '{disposition}'."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            try:
                ret = DispensationReturn.objects.select_for_update().get(pk=pk)
            except DispensationReturn.DoesNotExist:
                return Response({'error': 'Return record not found.'}, status=status.HTTP_404_NOT_FOUND)

            if ret.assessment_status in ['ASSESSED', 'REJECTED']:
                return Response({'error': 'Return has already been assessed.'}, status=status.HTTP_400_BAD_REQUEST)

            p_item = PrescriptionItem.objects.select_for_update().get(pk=ret.prescription_item_id)
            batch = MedicineBatch.objects.select_for_update().get(pk=ret.batch_id)

            if disposition == 'REJECTED':
                ret.assessment_status = 'REJECTED'
                ret.disposition = 'REJECTED'
                ret.condition_intact = request.data.get('condition_intact')
                ret.packaging_sealed = request.data.get('packaging_sealed')
                ret.storage_valid = request.data.get('storage_valid')
                ret.assessed_by = request.user
                ret.assessed_at = timezone.now()
                ret.assessment_notes = request.data.get('assessment_notes', '')
                ret.save()

                AuditLog.objects.create(
                    user=request.user,
                    username_snapshot=request.user.username,
                    action='RETURN_ASSESSED',
                    facility=ret.facility,
                    details=f"Assessed Return #{ret.return_number}. Disposition: REJECTED."
                )
                return Response(DispensationReturnSerializer(ret).data)

            # For APPROVED_FOR_STOCK, QUARANTINE, DISPOSAL:
            # Enforce cumulative cap holding lock, excluding ret.pk so as not to double count
            existing_reserved = DispensationReturn.objects.filter(
                prescription_item=p_item,
                disposition__in=['PENDING', 'APPROVED_FOR_STOCK', 'QUARANTINE', 'DISPOSAL']
            ).exclude(
                assessment_status__in=['REJECTED', 'CANCELLED']
            ).exclude(
                disposition__in=['REJECTED', 'CANCELLED']
            ).exclude(
                pk=ret.pk
            ).aggregate(
                t=models.Sum('returned_quantity')
            )['t'] or 0

            if existing_reserved + ret.returned_quantity > p_item.dispensed_quantity:
                return Response({
                    'error': f"Assessing return would exceed cumulative dispensed quantity ({p_item.dispensed_quantity})."
                }, status=status.HTTP_400_BAD_REQUEST)

            if disposition == 'APPROVED_FOR_STOCK':
                dest_before = batch.available_quantity
                batch.available_quantity += ret.returned_quantity
                batch.save()

                InventoryTransaction.objects.create(
                    facility=ret.facility,
                    medicine=batch.medicine,
                    batch=batch,
                    transaction_type='RETURN_APPROVED',
                    quantity=ret.returned_quantity,
                    source_bucket='patient_return',
                    source_before_qty=0,
                    source_after_qty=0,
                    destination_bucket='available_quantity',
                    destination_before_qty=dest_before,
                    destination_after_qty=batch.available_quantity,
                    patient=ret.prescription.patient,
                    prescription=ret.prescription,
                    prescription_item=p_item,
                    reference_id=f"RET-{ret.return_number}",
                    created_by=request.user,
                    notes="Approved patient return restored to usable available stock"
                )

            elif disposition == 'QUARANTINE':
                dest_before = batch.quarantined_quantity
                batch.quarantined_quantity += ret.returned_quantity
                batch.save()

                InventoryTransaction.objects.create(
                    facility=ret.facility,
                    medicine=batch.medicine,
                    batch=batch,
                    transaction_type='RETURN_QUARANTINED',
                    quantity=ret.returned_quantity,
                    source_bucket='patient_return',
                    source_before_qty=0,
                    source_after_qty=0,
                    destination_bucket='quarantined_quantity',
                    destination_before_qty=dest_before,
                    destination_after_qty=batch.quarantined_quantity,
                    patient=ret.prescription.patient,
                    prescription=ret.prescription,
                    prescription_item=p_item,
                    reference_id=f"RET-{ret.return_number}",
                    created_by=request.user,
                    notes="Returned medication quarantined for quality investigation"
                )

            elif disposition == 'DISPOSAL':
                dest_before = batch.disposed_quantity
                batch.disposed_quantity += ret.returned_quantity
                batch.save()

                InventoryTransaction.objects.create(
                    facility=ret.facility,
                    medicine=batch.medicine,
                    batch=batch,
                    transaction_type='RETURN_DISPOSED',
                    quantity=ret.returned_quantity,
                    source_bucket='patient_return',
                    source_before_qty=0,
                    source_after_qty=0,
                    destination_bucket='disposed_quantity',
                    destination_before_qty=dest_before,
                    destination_after_qty=batch.disposed_quantity,
                    patient=ret.prescription.patient,
                    prescription=ret.prescription,
                    prescription_item=p_item,
                    reference_id=f"RET-{ret.return_number}",
                    created_by=request.user,
                    notes="Returned medication condemned for disposal"
                )

            ret.assessment_status = 'ASSESSED'
            ret.condition_intact = request.data.get('condition_intact')
            ret.packaging_sealed = request.data.get('packaging_sealed')
            ret.storage_valid = request.data.get('storage_valid')
            ret.assessed_by = request.user
            ret.assessed_at = timezone.now()
            ret.disposition = disposition
            ret.assessment_notes = request.data.get('assessment_notes', '')
            ret.save()

            AuditLog.objects.create(
                user=request.user,
                username_snapshot=request.user.username,
                action='RETURN_ASSESSED',
                facility=ret.facility,
                details=f"Assessed Return #{ret.return_number}. Disposition: {disposition}."
            )

        return Response(DispensationReturnSerializer(ret).data)


class BatchRecallViewSet(viewsets.ModelViewSet):
    serializer_class = BatchRecallSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permissions = {
        'GET': 'inventory.view',
        'POST': 'inventory.create',
        'PUT': 'inventory.update',
        'PATCH': 'inventory.update',
        'DELETE': 'inventory.update'
    }

    def get_queryset(self):
        queryset = BatchRecall.objects.all().select_related('batch__medicine', 'facility', 'initiated_by')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        facility_param = self.request.query_params.get('facility')
        if facility_param:
            queryset = queryset.filter(facility_id=facility_param)
        return queryset

    def create(self, request, *args, **kwargs):
        """Quantity-scoped regulatory batch recall."""
        if request.user.role not in ['PHARMACIST', 'HOSPITAL_ADMIN']:
            return Response({'error': f"Role '{request.user.role}' is not authorized to declare a batch recall."}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        batch_id = data.get('batch') or data.get('batch_id')
        if not batch_id:
            return Response({'error': 'Batch ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            batch = MedicineBatch.objects.select_for_update().get(pk=batch_id)
            accessible_ids = get_accessible_facility_ids_for_user(request.user)
            if accessible_ids is not None and batch.facility_id not in accessible_ids:
                return Response({'error': 'Cross-facility recall blocked.'}, status=status.HTTP_403_FORBIDDEN)

            recalled_qty = int(data.get('recalled_quantity') or batch.available_quantity)
            if recalled_qty <= 0:
                return Response({'error': 'Recalled quantity must be greater than zero.'}, status=status.HTTP_400_BAD_REQUEST)
            if recalled_qty > batch.available_quantity:
                return Response({'error': f"Cannot recall {recalled_qty} units. Only {batch.available_quantity} available."}, status=status.HTTP_400_BAD_REQUEST)

            src_before = batch.available_quantity
            dest_before = batch.recalled_quantity

            batch.available_quantity -= recalled_qty
            batch.recalled_quantity += recalled_qty
            batch.save()

            import uuid
            recall_num = f"RCL-{batch.facility.facility_code if batch.facility else 'FAC'}-{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

            recall = BatchRecall.objects.create(
                recall_number=recall_num,
                batch=batch,
                facility=batch.facility,
                recall_reference=data.get('recall_reference', f"GOV-NOTIF-{batch.batch_number}"),
                reason=data.get('reason', 'Regulatory authority recall order'),
                recalled_quantity=recalled_qty,
                initiated_by=request.user,
                status='INITIATED'
            )

            InventoryTransaction.objects.create(
                facility=batch.facility,
                medicine=batch.medicine,
                batch=batch,
                transaction_type='RECALL_HOLD',
                quantity=recalled_qty,
                source_bucket='available_quantity',
                source_before_qty=src_before,
                source_after_qty=batch.available_quantity,
                destination_bucket='recalled_quantity',
                destination_before_qty=dest_before,
                destination_after_qty=batch.recalled_quantity,
                reference_id=f"RCL-{recall.recall_number}",
                created_by=request.user,
                notes=f"Regulatory Recall: {recall.reason}"
            )

            AuditLog.objects.create(
                user=request.user,
                username_snapshot=request.user.username,
                action='RECALL_INITIATED',
                facility=batch.facility,
                details=f"Initiated recall #{recall.recall_number} for {recalled_qty} units of Batch {batch.batch_number}."
            )

        return Response(BatchRecallSerializer(recall).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def impact_report(self, request, pk=None):
        """Scoped recall impact report listing potentially affected patients."""
        recall = self.get_object()
        accessible_ids = get_accessible_facility_ids_for_user(request.user)
        if accessible_ids is not None and recall.facility_id not in accessible_ids:
            return Response({'error': 'Cross-facility recall report blocked.'}, status=status.HTTP_403_FORBIDDEN)

        # Dispensations from this batch
        tx_qs = InventoryTransaction.objects.filter(
            batch=recall.batch, transaction_type='DISPENSED'
        ).select_related('patient', 'prescription', 'prescription_item').order_by('-created_at')

        patients_impacted = []
        seen_patients = set()
        for tx in tx_qs:
            if tx.patient and tx.patient.id not in seen_patients:
                seen_patients.add(tx.patient.id)
                patients_impacted.append({
                    'patient_id': tx.patient.id,
                    'patient_name': tx.patient.name,
                    'patient_phone': getattr(tx.patient, 'phone_number', getattr(tx.patient, 'phone', 'N/A')),
                    'dispensed_at': tx.created_at.strftime('%Y-%m-%d %H:%M'),
                    'quantity_dispensed': tx.quantity,
                    'prescription_id': tx.prescription_id
                })

        return Response({
            'recall_number': recall.recall_number,
            'batch_number': recall.batch.batch_number,
            'medicine_name': recall.batch.medicine.generic_name,
            'facility_name': recall.facility.facility_name,
            'recalled_quantity': recall.recalled_quantity,
            'remaining_in_facility': recall.batch.recalled_quantity,
            'affected_patients_count': len(patients_impacted),
            'affected_patients': patients_impacted
        })


class PatientCounsellingViewSet(viewsets.ModelViewSet):
    serializer_class = PatientCounsellingSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permissions = {
        'GET': 'prescription.view',
        'POST': 'pharmacy.dispense',
        'PUT': 'pharmacy.dispense',
        'PATCH': 'pharmacy.dispense',
        'DELETE': 'pharmacy.dispense'
    }

    def get_queryset(self):
        queryset = PatientCounselling.objects.all().select_related('prescription', 'patient', 'pharmacist')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(prescription__facility_id__in=accessible_ids)
        return queryset

    def perform_create(self, serializer):
        serializer.save(pharmacist=self.request.user)


class ColdChainLogViewSet(viewsets.ModelViewSet):
    serializer_class = ColdChainLogSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permissions = {
        'GET': 'inventory.view',
        'POST': 'inventory.create',
        'PUT': 'inventory.update',
        'PATCH': 'inventory.update',
        'DELETE': 'inventory.update'
    }

    def get_queryset(self):
        queryset = ColdChainLog.objects.all().select_related('facility', 'recorded_by')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        facility_param = self.request.query_params.get('facility')
        if facility_param:
            queryset = queryset.filter(facility_id=facility_param)
        return queryset

    def perform_create(self, serializer):
        facility = serializer.validated_data.get('facility') or self.request.user.assigned_facility or Facility.objects.first()
        serializer.save(recorded_by=self.request.user, facility=facility)


class PharmacyDashboardSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permission = 'pharmacy.view'

    def get(self, request):
        user = request.user
        accessible_ids = get_accessible_facility_ids_for_user(user)
        facility_param = request.query_params.get('facility')

        rx_qs = Prescription.objects.all()
        if accessible_ids is not None:
            rx_qs = rx_qs.filter(facility_id__in=accessible_ids)
        if facility_param:
            rx_qs = rx_qs.filter(facility_id=facility_param)

        total_prescriptions_count = rx_qs.count()
        pending_prescriptions_count = rx_qs.filter(status__in=['ACTIVE', 'PENDING_VERIFICATION', 'VERIFIED', 'PARTIALLY_DISPENSED']).count()
        dispensed_today_count = rx_qs.filter(status='DISPENSED', date=datetime.date.today()).count()

        batch_qs = MedicineBatch.objects.all()
        if accessible_ids is not None:
            batch_qs = batch_qs.filter(facility_id__in=accessible_ids)
        if facility_param:
            batch_qs = batch_qs.filter(facility_id=facility_param)

        total_available_stock = batch_qs.aggregate(t=models.Sum('available_quantity'))['t'] or 0

        today = datetime.date.today()
        expiring_threshold = today + datetime.timedelta(days=60)
        expiring_soon_count = batch_qs.filter(available_quantity__gt=0, expiry_date__gt=today, expiry_date__lte=expiring_threshold).count()
        expired_count = batch_qs.filter(expiry_date__lte=today).count()

        meds = MedicineMaster.objects.all()
        total_medicines = meds.count()
        low_stock_count = 0
        out_of_stock_count = 0
        for m in meds:
            mb_qs = batch_qs.filter(medicine=m)
            tot_qty = mb_qs.aggregate(t=models.Sum('available_quantity'))['t'] or 0
            if tot_qty == 0:
                out_of_stock_count += 1
            elif tot_qty <= m.minimum_stock or tot_qty <= m.reorder_level:
                low_stock_count += 1

        po_qs = PurchaseOrder.objects.all()
        if accessible_ids is not None:
            po_qs = po_qs.filter(facility_id__in=accessible_ids)
        if facility_param:
            po_qs = po_qs.filter(facility_id=facility_param)

        pending_purchase_orders_count = po_qs.filter(status__in=['DRAFT', 'PENDING', 'APPROVED', 'ORDERED', 'PARTIALLY_RECEIVED']).count()
        total_vendors_count = Vendor.objects.filter(status='ACTIVE').count()

        return Response({
            'total_medicines': total_medicines,
            'total_available_stock': total_available_stock,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'expiring_soon_count': expiring_soon_count,
            'expired_count': expired_count,
            'total_prescriptions_count': total_prescriptions_count,
            'pending_prescriptions_count': pending_prescriptions_count,
            'dispensed_today_count': dispensed_today_count,
            'pending_purchase_orders_count': pending_purchase_orders_count,
            'total_vendors_count': total_vendors_count,

            # Backwards compatibility keys
            'total_prescriptions': total_prescriptions_count,
            'prescriptions_waiting': pending_prescriptions_count,
            'dispensed_today': dispensed_today_count,
            'current_stock_items': total_medicines - out_of_stock_count,
            'low_stock': low_stock_count,
            'out_of_stock': out_of_stock_count,
            'expiring_soon': expiring_soon_count,
            'pending_purchase_orders': pending_purchase_orders_count
        })


class PharmacyAlertsView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permission = 'pharmacy.view'

    def get(self, request):
        user = request.user
        accessible_ids = get_accessible_facility_ids_for_user(user)
        facility_param = request.query_params.get('facility')

        batch_qs = MedicineBatch.objects.all().select_related('medicine', 'facility')
        if accessible_ids is not None:
            batch_qs = batch_qs.filter(facility_id__in=accessible_ids)
        if facility_param:
            batch_qs = batch_qs.filter(facility_id=facility_param)

        alerts = []
        today = datetime.date.today()
        expiring_threshold = today + datetime.timedelta(days=30)

        meds = MedicineMaster.objects.all()
        for m in meds:
            mb_qs = batch_qs.filter(medicine=m)
            tot_qty = mb_qs.aggregate(t=models.Sum('available_quantity'))['t'] or 0
            fac_name = mb_qs.first().facility.facility_name if mb_qs.exists() else 'Namma Clinic'

            if tot_qty == 0:
                alerts.append({
                    'id': f"OUT-{m.id}",
                    'alert_type': 'OUT_OF_STOCK',
                    'severity': 'CRITICAL',
                    'title': f"OUT OF STOCK: {m.generic_name} {m.strength}",
                    'description': f"Current stock is 0 {m.unit}. Immediate procurement required.",
                    'facility_name': fac_name,
                    'created_at': today.strftime('%Y-%m-%d')
                })
            elif tot_qty <= m.minimum_stock or tot_qty <= m.reorder_level:
                alerts.append({
                    'id': f"LOW-{m.id}",
                    'alert_type': 'LOW_STOCK',
                    'severity': 'HIGH',
                    'title': f"LOW STOCK: {m.generic_name} {m.strength}",
                    'description': f"Current stock is {tot_qty} {m.unit} (Minimum threshold: {m.minimum_stock}).",
                    'facility_name': fac_name,
                    'created_at': today.strftime('%Y-%m-%d')
                })

        for b in batch_qs:
            if b.total_physical_stock > 0:
                if b.expiry_date <= today:
                    alerts.append({
                        'id': f"EXP-{b.id}",
                        'alert_type': 'EXPIRED',
                        'severity': 'CRITICAL',
                        'title': f"EXPIRED BATCH: {b.medicine.generic_name} ({b.batch_number})",
                        'description': f"Batch expired on {b.expiry_date} with {b.total_physical_stock} {b.medicine.unit} remaining.",
                        'facility_name': b.facility.facility_name,
                        'created_at': today.strftime('%Y-%m-%d')
                    })
                elif b.expiry_date <= expiring_threshold:
                    alerts.append({
                        'id': f"EXPS-{b.id}",
                        'alert_type': 'EXPIRING_SOON',
                        'severity': 'MEDIUM',
                        'title': f"EXPIRING SOON: {b.medicine.generic_name} ({b.batch_number})",
                        'description': f"Batch expires on {b.expiry_date} ({ (b.expiry_date - today).days } days remaining).",
                        'facility_name': b.facility.facility_name,
                        'created_at': today.strftime('%Y-%m-%d')
                    })

        po_qs = PurchaseOrder.objects.all().select_related('vendor', 'facility')
        if accessible_ids is not None:
            po_qs = po_qs.filter(facility_id__in=accessible_ids)
        if facility_param:
            po_qs = po_qs.filter(facility_id=facility_param)

        for po in po_qs.filter(status__in=['PENDING', 'ORDERED']):
            alerts.append({
                'id': f"PO-{po.id}",
                'alert_type': 'PENDING_PURCHASE_ORDER',
                'severity': 'MEDIUM',
                'title': f"PENDING PO #{po.po_number}",
                'description': f"PO for Vendor {po.vendor.vendor_name} is currently in status '{po.status}'.",
                'facility_name': po.facility.facility_name,
                'created_at': po.order_date.strftime('%Y-%m-%d')
            })

        return Response(alerts)


class PharmacyReportsView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permission = 'reports.view'

    def get(self, request):
        user = request.user
        accessible_ids = get_accessible_facility_ids_for_user(user)
        facility_param = request.query_params.get('facility')

        batch_qs = MedicineBatch.objects.all().select_related('medicine', 'facility', 'vendor')
        tx_qs = InventoryTransaction.objects.all().select_related('medicine', 'batch', 'facility', 'created_by')
        po_qs = PurchaseOrder.objects.all().select_related('vendor', 'facility', 'created_by')

        if accessible_ids is not None:
            batch_qs = batch_qs.filter(facility_id__in=accessible_ids)
            tx_qs = tx_qs.filter(facility_id__in=accessible_ids)
            po_qs = po_qs.filter(facility_id__in=accessible_ids)

        if facility_param:
            batch_qs = batch_qs.filter(facility_id=facility_param)
            tx_qs = tx_qs.filter(facility_id=facility_param)
            po_qs = po_qs.filter(facility_id=facility_param)

        dispensing_logs = tx_qs.filter(transaction_type='DISPENSED')[:50]
        dispensing_data = [{
            'date': tx.created_at.strftime('%Y-%m-%d %H:%M'),
            'medicine': tx.medicine.generic_name,
            'batch_number': tx.batch.batch_number if tx.batch else 'N/A',
            'quantity': tx.quantity,
            'facility': tx.facility.facility_name,
            'dispensed_by': tx.created_by.full_name if tx.created_by else 'Pharmacist',
            'reference': tx.reference_id
        } for tx in dispensing_logs]

        consumption = tx_qs.filter(transaction_type='DISPENSED').values('medicine__generic_name', 'medicine__category').annotate(
            total_dispensed=models.Sum('quantity')
        ).order_by('-total_dispensed')[:15]

        stock_summary = []
        for m in MedicineMaster.objects.all():
            m_batches = batch_qs.filter(medicine=m)
            tot_qty = m_batches.aggregate(t=models.Sum('available_quantity'))['t'] or 0
            stock_summary.append({
                'medicine_id': m.id,
                'generic_name': m.generic_name,
                'category': m.category,
                'unit': m.unit,
                'available_stock': tot_qty,
                'minimum_stock': m.minimum_stock,
                'reorder_level': m.reorder_level,
                'status': 'OUT_OF_STOCK' if tot_qty == 0 else ('LOW_STOCK' if tot_qty <= m.minimum_stock else 'NORMAL')
            })

        return Response({
            'daily_dispensing': dispensing_data,
            'consumption_summary': list(consumption),
            'stock_summary': stock_summary,
            'total_batches': batch_qs.count(),
            'total_purchase_orders': po_qs.count()
        })
