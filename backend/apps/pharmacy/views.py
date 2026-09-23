import datetime
from django.db import transaction, models
from django.utils import timezone
from rest_framework import serializers, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.pharmacy.models import (
    MedicineMaster, MedicineBatch, InventoryTransaction,
    Vendor, PurchaseOrder, PurchaseOrderItem
)
from apps.consultations.models import Prescription, PrescriptionItem
from apps.audit.models import AuditLog
from apps.alerts.models import Alert
from apps.accounts.permissions import get_accessible_facility_ids_for_user, HasPermission, HasFacilityScope
from apps.reports.services import EXPIRING_SOON_DAYS

# Serializers
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
        
        batches = obj.batches.filter(status__in=['ACTIVE', 'LOW_STOCK', 'EXPIRING_SOON'])
        if accessible_ids is not None:
            batches = batches.filter(facility_id__in=accessible_ids)
        
        facility_param = request.query_params.get('facility') if request else None
        if facility_param:
            batches = batches.filter(facility_id=facility_param)
            
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

    class Meta:
        model = MedicineBatch
        fields = '__all__'

    def get_is_expired(self, obj):
        return obj.expiry_date <= datetime.date.today()

    def get_days_to_expiry(self, obj):
        delta = obj.expiry_date - datetime.date.today()
        return delta.days


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.ReadOnlyField(source='medicine.generic_name')
    medicine_brand = serializers.ReadOnlyField(source='medicine.brand_name')
    medicine_strength = serializers.ReadOnlyField(source='medicine.strength')
    medicine_unit = serializers.ReadOnlyField(source='medicine.unit')
    remaining_quantity = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrderItem
        fields = '__all__'

    def get_remaining_quantity(self, obj):
        return max(0, obj.ordered_quantity - obj.received_quantity)


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    vendor_name = serializers.ReadOnlyField(source='vendor.vendor_name')
    vendor_code = serializers.SerializerMethodField()
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')
    created_by_name = serializers.ReadOnlyField(source='created_by.full_name')
    approved_by_name = serializers.ReadOnlyField(source='approved_by.full_name')
    rejected_by_name = serializers.ReadOnlyField(source='rejected_by.full_name')

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


# ViewSets & APIs

class MedicineMasterViewSet(viewsets.ModelViewSet):
    queryset = MedicineMaster.objects.all().order_by('id')
    serializer_class = MedicineMasterSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission]
    required_permissions = {
        'GET': 'medicine_master.view',
        'POST': 'medicine_master.create',
        'PUT': 'medicine_master.update',
        'PATCH': 'medicine_master.update',
        'DELETE': 'medicine_master.delete',
        'list': 'medicine_master.view',
        'retrieve': 'medicine_master.view',
        'create': 'medicine_master.create',
        'update': 'medicine_master.update',
        'partial_update': 'medicine_master.update',
        'destroy': 'medicine_master.delete',
    }

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
        queryset = PurchaseOrder.objects.all().select_related('vendor', 'facility', 'created_by', 'approved_by', 'rejected_by').prefetch_related('items__medicine')
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
        # District Officer & Clinical roles cannot create purchase orders
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

        # Generate unique sequential PO number
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
                    return Response({'error': f"Item quantity must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)
                if price < 0:
                    return Response({'error': f"Unit price cannot be negative."}, status=status.HTTP_400_BAD_REQUEST)

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
        """Submit a DRAFT purchase order for administrative approval."""
        po = self.get_object()
        if po.status != 'DRAFT':
            return Response({'error': f"Only DRAFT purchase orders can be submitted for approval (current status: '{po.status}')."}, status=status.HTTP_400_BAD_REQUEST)

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
        return Response({'message': f"Purchase Order #{po.po_number} submitted for approval!", 'po': PurchaseOrderSerializer(po).data})

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Hospital Admin approves a purchase order."""
        if request.user.role not in ['HOSPITAL_ADMIN']:
            return Response({'error': "Separation of duties: Only a Hospital Admin can approve purchase orders."}, status=status.HTTP_403_FORBIDDEN)

        po = self.get_object()
        if po.status not in ['PENDING_APPROVAL', 'PENDING']:
            return Response({'error': f"Purchase Order cannot be approved from status '{po.status}'."}, status=status.HTTP_400_BAD_REQUEST)

        po.status = 'APPROVED'
        po.approved_by = request.user
        po.approved_at = timezone.now()
        po.save()

        Alert.objects.create(
            facility=po.facility,
            alert_type='LOW_STOCK',
            severity='MEDIUM',
            title=f"PO {po.po_number} Approved",
            description=f"Purchase Order #{po.po_number} for {po.vendor.vendor_name} has been approved by {request.user.full_name} and is ready to be placed."
        )

        AuditLog.objects.create(
            user=request.user,
            username_snapshot=request.user.username,
            action='PURCHASE_ORDER_APPROVED',
            facility=po.facility,
            details=f"Approved PO #{po.po_number} for Vendor {po.vendor.vendor_name} (Total: Rs. {po.total_amount:.2f})"
        )
        return Response({'message': f"Purchase Order #{po.po_number} approved successfully!", 'po': PurchaseOrderSerializer(po).data})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Hospital Admin rejects a purchase order with reason."""
        if request.user.role not in ['HOSPITAL_ADMIN']:
            return Response({'error': "Only a Hospital Admin can reject purchase orders."}, status=status.HTTP_403_FORBIDDEN)

        po = self.get_object()
        if po.status not in ['PENDING_APPROVAL', 'PENDING']:
            return Response({'error': f"Purchase Order cannot be rejected from status '{po.status}'."}, status=status.HTTP_400_BAD_REQUEST)

        reason = request.data.get('reason') or request.data.get('rejection_reason', 'Order rejected by administration.')
        po.status = 'DRAFT'
        po.rejected_by = request.user
        po.rejected_at = timezone.now()
        po.rejection_reason = reason
        po.save()

        Alert.objects.create(
            facility=po.facility,
            alert_type='LOW_STOCK',
            severity='HIGH',
            title=f"PO {po.po_number} Returned for Revisions",
            description=f"PO #{po.po_number} was rejected by Admin. Reason: {reason}"
        )

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
        """Transition APPROVED purchase order to ORDERED."""
        po = self.get_object()
        if po.status not in ['APPROVED', 'DRAFT']:
            return Response({'error': f"Cannot place order for PO in status '{po.status}'."}, status=status.HTTP_400_BAD_REQUEST)

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
    def cancel(self, request, pk=None):
        """Cancel purchase order."""
        po = self.get_object()
        if po.status in ['RECEIVED']:
            return Response({'error': "Cannot cancel a fully received purchase order."}, status=status.HTTP_400_BAD_REQUEST)

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

    @action(detail=True, methods=['post'], url_path='receive_items')
    def receive_items(self, request, pk=None):
        return self._execute_goods_receiving(request)

    @action(detail=True, methods=['post'], url_path='receive')
    def receive(self, request, pk=None):
        return self._execute_goods_receiving(request)

    def _execute_goods_receiving(self, request):
        """Atomic stock receiving engine with strict validation."""
        if request.user.role in ['DISTRICT_OFFICER', 'DOCTOR', 'NURSE', 'LAB_TECHNICIAN']:
            return Response({'error': f"Role '{request.user.role}' is not authorized to receive goods."}, status=status.HTTP_403_FORBIDDEN)

        po = self.get_object()
        if po.status in ['CANCELLED', 'RECEIVED']:
            return Response({'error': f"Cannot receive items for Purchase Order in status '{po.status}'."}, status=status.HTTP_400_BAD_REQUEST)

        received_items = request.data.get('received_items') or request.data.get('items') or []
        if not received_items:
            return Response({'error': 'No received items provided in receipt payload.'}, status=status.HTTP_400_BAD_REQUEST)

        today = datetime.date.today()

        with transaction.atomic():
            received_summary = []
            for item in received_items:
                item_id = item.get('item_id') or item.get('po_item_id')
                batch_number = str(item.get('batch_number', '')).strip()
                expiry_date = item.get('expiry_date')
                mfg_date = item.get('mfg_date') or None
                received_qty = int(item.get('received_qty') if item.get('received_qty') is not None else item.get('received_quantity', 0))
                unit_cost = float(item.get('unit_cost') or 0.0)

                if received_qty <= 0:
                    continue

                po_item = PurchaseOrderItem.objects.filter(pk=item_id, purchase_order=po).first()
                if not po_item:
                    return Response({'error': f"PO Item ID {item_id} does not belong to this Purchase Order."}, status=status.HTTP_400_BAD_REQUEST)

                # Over-receiving guard
                remaining_qty = po_item.ordered_quantity - po_item.received_quantity
                if received_qty > remaining_qty:
                    return Response({
                        'error': f"Cannot receive {received_qty} units for '{po_item.medicine.generic_name}'. Remaining ordered quantity is {remaining_qty}."
                    }, status=status.HTTP_400_BAD_REQUEST)

                if not batch_number:
                    return Response({'error': f"Batch Number is required for '{po_item.medicine.generic_name}'."}, status=status.HTTP_400_BAD_REQUEST)
                if not expiry_date:
                    return Response({'error': f"Expiry Date is required for '{po_item.medicine.generic_name}'."}, status=status.HTTP_400_BAD_REQUEST)

                # Date parsing & validations
                exp_d = datetime.datetime.strptime(str(expiry_date)[:10], '%Y-%m-%d').date() if isinstance(expiry_date, str) else expiry_date
                if exp_d <= today:
                    return Response({
                        'error': f"Cannot receive an already expired batch. Batch '{batch_number}' expiry ({exp_d}) is before current date."
                    }, status=status.HTTP_400_BAD_REQUEST)

                mfg_d = None
                if mfg_date:
                    mfg_d = datetime.datetime.strptime(str(mfg_date)[:10], '%Y-%m-%d').date() if isinstance(mfg_date, str) else mfg_date
                    if mfg_d > today:
                        return Response({'error': f"Manufacturing date ({mfg_d}) cannot be in the future."}, status=status.HTTP_400_BAD_REQUEST)
                    if mfg_d >= exp_d:
                        return Response({'error': f"Manufacturing date ({mfg_d}) must be before expiry date ({exp_d})."}, status=status.HTTP_400_BAD_REQUEST)

                # Create or Update MedicineBatch in FEFO order
                batch, created = MedicineBatch.objects.get_or_create(
                    facility=po.facility,
                    medicine=po_item.medicine,
                    batch_number=batch_number,
                    defaults={
                        'vendor': po.vendor,
                        'supplier': po.vendor.vendor_name,
                        'mfg_date': mfg_d,
                        'expiry_date': exp_d,
                        'quantity': received_qty,
                        'unit_cost': unit_cost if unit_cost > 0 else po_item.unit_price,
                        'status': 'ACTIVE'
                    }
                )

                if not created:
                    batch.quantity += received_qty
                    if batch.status in ['EXHAUSTED', 'LOW_STOCK']:
                        batch.status = 'ACTIVE'
                    batch.save()

                # Update PO item received quantity
                po_item.received_quantity += received_qty
                po_item.save()

                # Create immutable inventory transaction
                InventoryTransaction.objects.create(
                    facility=po.facility,
                    medicine=po_item.medicine,
                    batch=batch,
                    transaction_type='PURCHASE_RECEIVED',
                    quantity=received_qty,
                    reference_id=f"PO-{po.po_number}",
                    created_by=request.user,
                    notes=f"Stock received for PO #{po.po_number} from Vendor {po.vendor.vendor_name}"
                )

                received_summary.append({
                    'medicine': po_item.medicine.generic_name,
                    'batch_number': batch.batch_number,
                    'received_qty': received_qty
                })

            # Check if all items in PO are fully received
            fresh_items = list(PurchaseOrderItem.objects.filter(purchase_order=po))
            all_received = all(i.received_quantity >= i.ordered_quantity for i in fresh_items) if fresh_items else False
            any_received = any(i.received_quantity > 0 for i in fresh_items) if fresh_items else False

            if all_received:
                po.status = 'RECEIVED'
            elif any_received:
                po.status = 'PARTIALLY_RECEIVED'
            po.save()

            # Create notification
            notif_text = f"PO #{po.po_number} has been fully received into stock." if all_received else f"PO #{po.po_number} has been partially received."
            Alert.objects.create(
                facility=po.facility,
                alert_type='LOW_STOCK',
                severity='LOW',
                title=f"Goods Received: PO #{po.po_number}",
                description=notif_text
            )

            AuditLog.objects.create(
                user=request.user,
                username_snapshot=request.user.username,
                action='GOODS_RECEIVED',
                facility=po.facility,
                details=f"Received goods for PO #{po.po_number}. Summary: {received_summary}"
            )

        return Response({
            'message': f"Goods successfully received for PO #{po.po_number}!",
            'po_status': po.status,
            'summary': received_summary,
            'po': PurchaseOrderSerializer(po).data
        })

    @action(detail=False, methods=['get'])
    def procurement_summary(self, request):
        """Comprehensive procurement KPI summary for dashboard and reporting."""
        qs = self.get_queryset()
        counts = {
            'draft': qs.filter(status='DRAFT').count(),
            'pending_approval': qs.filter(status__in=['PENDING_APPROVAL', 'PENDING']).count(),
            'approved': qs.filter(status='APPROVED').count(),
            'ordered': qs.filter(status='ORDERED').count(),
            'partially_received': qs.filter(status='PARTIALLY_RECEIVED').count(),
            'received': qs.filter(status='RECEIVED').count(),
            'cancelled': qs.filter(status='CANCELLED').count(),
            'total_orders': qs.count(),
            'total_spend': float(qs.filter(status__in=['APPROVED', 'ORDERED', 'PARTIALLY_RECEIVED', 'RECEIVED']).aggregate(t=models.Sum('total_amount'))['t'] or 0.0)
        }
        return Response(counts)


class InventoryTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = InventoryTransactionSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permissions = {
        'GET': 'inventory.view',
        'POST': 'inventory.create',
        'PUT': 'inventory.update',
        'PATCH': 'inventory.update',
        'DELETE': 'inventory.update'
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
        items_to_dispense = request.data.get('items', []) # [{'item_id': 1, 'batch_id': 2, 'qty': 14}]

        if not prescription_id:
            return Response({'error': 'Prescription ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            prescription = Prescription.objects.get(pk=prescription_id)
        except Prescription.DoesNotExist:
            return Response({'error': 'Prescription not found'}, status=status.HTTP_404_NOT_FOUND)

        # Facility Scope Check
        accessible_ids = get_accessible_facility_ids_for_user(request.user)
        if accessible_ids is not None and prescription.facility_id not in accessible_ids:
            return Response({'error': 'You do not have permission to dispense prescriptions for another facility scope.'}, status=status.HTTP_403_FORBIDDEN)

        if not items_to_dispense:
            items_to_dispense = [
                {'item_id': pi.id, 'qty': pi.quantity, 'batch_id': None}
                for pi in prescription.items.filter(status='PENDING')
            ]

        today = datetime.date.today()
        dispensed_summary = []

        with transaction.atomic():
            for item in items_to_dispense:
                item_id = item.get('item_id')
                batch_id = item.get('batch_id')
                qty = int(item.get('qty') or item.get('qty_to_dispense') or item.get('quantity') or 0)

                if qty <= 0:
                    continue

                if item_id:
                    p_item = PrescriptionItem.objects.filter(pk=item_id, prescription=prescription).first()
                else:
                    med_name_key = item.get('medicine_name', '').split()[0] if item.get('medicine_name') else ''
                    p_item = PrescriptionItem.objects.filter(prescription=prescription, medicine_name__icontains=med_name_key, status='PENDING').first()

                if not p_item:
                    continue

                # FEFO Batch selection: if batch_id provided, select it; else pick earliest expiry active batch
                if batch_id and int(batch_id) > 0:
                    batch = MedicineBatch.objects.select_for_update().filter(pk=int(batch_id), facility=prescription.facility).first()
                else:
                    med_keyword = p_item.medicine_name.split()[0].lower()
                    batch = MedicineBatch.objects.select_for_update().filter(
                        facility=prescription.facility,
                        medicine__generic_name__icontains=med_keyword,
                        quantity__gt=0,
                        expiry_date__gt=today,
                        status__in=['ACTIVE', 'LOW_STOCK', 'EXPIRING_SOON']
                    ).order_by('expiry_date').first()

                if not batch:
                    return Response({'error': f"No active stock batch available for '{p_item.medicine_name}' in facility scope."}, status=status.HTTP_400_BAD_REQUEST)

                # Batch Expiry Validation Guard
                if batch.expiry_date <= today:
                    return Response({'error': f"Batch '{batch.batch_number}' for '{p_item.medicine_name}' HAS EXPIRED on {batch.expiry_date}. Expired stock cannot be dispensed."}, status=status.HTTP_400_BAD_REQUEST)

                # Batch Stock Quantity Validation Guard
                if qty > batch.quantity:
                    return Response({'error': f"Insufficient stock in batch '{batch.batch_number}'. Requested: {qty}, Available: {batch.quantity}."}, status=status.HTTP_400_BAD_REQUEST)

                # Atomically deduct stock
                batch.quantity -= qty
                if batch.quantity <= 0:
                    batch.status = 'EXHAUSTED'
                elif batch.quantity <= batch.medicine.minimum_stock:
                    batch.status = 'LOW_STOCK'
                batch.save()

                # Record transaction log
                InventoryTransaction.objects.create(
                    facility=prescription.facility,
                    medicine=batch.medicine,
                    batch=batch,
                    transaction_type='DISPENSED',
                    quantity=qty,
                    reference_id=f"PRESCR-{prescription.id}",
                    created_by=request.user,
                    notes=f"Dispensed {qty} units for Patient {prescription.patient.name} (Batch: {batch.batch_number})"
                )

                if qty >= p_item.quantity:
                    p_item.status = 'DISPENSED'
                else:
                    p_item.status = 'PARTIALLY_DISPENSED'
                p_item.save()

                dispensed_summary.append({
                    'item': p_item.medicine_name,
                    'batch': batch.batch_number,
                    'qty': qty,
                    'remaining_stock': batch.quantity
                })

            # Check if all prescription items are dispensed
            fresh_items = list(PrescriptionItem.objects.filter(prescription=prescription))
            all_dispensed = all(i.status == 'DISPENSED' for i in fresh_items) if fresh_items else True
            any_dispensed = any(i.status in ['DISPENSED', 'PARTIALLY_DISPENSED'] for i in fresh_items) if fresh_items else False

            prescription.status = 'DISPENSED' if all_dispensed else ('PARTIALLY_DISPENSED' if any_dispensed else 'PENDING')
            prescription.save()

            # Update OPD Visit status to COMPLETED if all dispensed
            target_v = None
            if hasattr(prescription, 'consultation') and prescription.consultation and prescription.consultation.visit:
                target_v = prescription.consultation.visit
            elif prescription.patient and prescription.facility:
                from apps.visits.models import Visit
                target_v = Visit.objects.filter(
                    patient=prescription.patient,
                    facility=prescription.facility,
                    opd_date=prescription.date if hasattr(prescription, 'date') and prescription.date else today
                ).exclude(status='COMPLETED').first()

            if target_v:
                if all_dispensed:
                    target_v.current_queue = 'COMPLETED'
                    target_v.status = 'COMPLETED'
                    target_v.completed_time = timezone.now()
                    target_v.save()
                    if hasattr(target_v, 'token') and target_v.token:
                        target_v.token.status = 'COMPLETED'
                        target_v.token.save()
                elif any_dispensed:
                    target_v.current_queue = 'PHARMACY'
                    target_v.status = 'IN_PHARMACY'
                    target_v.save()

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


class PharmacyDashboardSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permission = 'pharmacy.view'

    def get(self, request):
        user = request.user
        accessible_ids = get_accessible_facility_ids_for_user(user)
        facility_param = request.query_params.get('facility')

        # Prescriptions Query
        rx_qs = Prescription.objects.all()
        if accessible_ids is not None:
            rx_qs = rx_qs.filter(facility_id__in=accessible_ids)
        if facility_param:
            rx_qs = rx_qs.filter(facility_id=facility_param)

        pending_prescriptions_count = rx_qs.filter(status__in=['ACTIVE', 'PENDING', 'PARTIALLY_DISPENSED']).count()
        dispensed_today_count = rx_qs.filter(status='DISPENSED', date=datetime.date.today()).count()

        # Batches Query
        batch_qs = MedicineBatch.objects.all()
        if accessible_ids is not None:
            batch_qs = batch_qs.filter(facility_id__in=accessible_ids)
        if facility_param:
            batch_qs = batch_qs.filter(facility_id=facility_param)

        total_available_stock = batch_qs.aggregate(t=models.Sum('quantity'))['t'] or 0

        today = datetime.date.today()
        expiring_threshold = today + datetime.timedelta(days=60)
        expiring_soon_count = batch_qs.filter(quantity__gt=0, expiry_date__gt=today, expiry_date__lte=expiring_threshold).count()
        expired_count = batch_qs.filter(models.Q(expiry_date__lte=today) | models.Q(status='EXPIRED')).count()

        # Low Stock & Out of Stock counts
        meds = MedicineMaster.objects.all()
        total_medicines = meds.count()
        low_stock_count = 0
        out_of_stock_count = 0
        for m in meds:
            mb_qs = batch_qs.filter(medicine=m)
            tot_qty = mb_qs.aggregate(t=models.Sum('quantity'))['t'] or 0
            if tot_qty == 0:
                out_of_stock_count += 1
            elif tot_qty <= m.minimum_stock or tot_qty <= m.reorder_level:
                low_stock_count += 1

        # Purchase Orders Query
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
            'pending_prescriptions_count': pending_prescriptions_count,
            'dispensed_today_count': dispensed_today_count,
            'pending_purchase_orders_count': pending_purchase_orders_count,
            'total_vendors_count': total_vendors_count,

            # Backwards compatibility keys
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
        expiring_threshold = today + datetime.timedelta(days=EXPIRING_SOON_DAYS)

        # 1. Low stock & Out of stock alerts
        meds = MedicineMaster.objects.all()
        for m in meds:
            mb_qs = batch_qs.filter(medicine=m)
            tot_qty = mb_qs.aggregate(t=models.Sum('quantity'))['t'] or 0
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

        # 2. Expiring & Expired Batches Alerts
        for b in batch_qs:
            if b.quantity > 0:
                if b.expiry_date <= today:
                    alerts.append({
                        'id': f"EXP-{b.id}",
                        'alert_type': 'EXPIRED',
                        'severity': 'CRITICAL',
                        'title': f"EXPIRED BATCH: {b.medicine.generic_name} ({b.batch_number})",
                        'description': f"Batch expired on {b.expiry_date} with {b.quantity} {b.medicine.unit} remaining.",
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

        # 3. Pending Purchase Orders Alerts
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

        # 1. Daily Dispensing Ledger
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

        today = datetime.date.today()
        dispensed_today_qty = tx_qs.filter(transaction_type='DISPENSED', created_at__date=today).aggregate(t=models.Sum('quantity'))['t'] or 0
        dispensed_today_rx = tx_qs.filter(transaction_type='DISPENSED', created_at__date=today).values('reference_id').distinct().count()

        # 2. Stock Valuation
        active_batches = batch_qs.filter(quantity__gt=0)
        tot_batches_count = active_batches.count()
        tot_qty_in_stock = active_batches.aggregate(q=models.Sum('quantity'))['q'] or 0
        tot_val = sum(float(b.quantity) * float(b.unit_cost or 0.0) for b in active_batches)

        # 3. Medicine Consumption Summary
        consumption_summary = []
        raw_consumption = tx_qs.filter(transaction_type='DISPENSED').values('medicine__generic_name', 'medicine__brand_name').annotate(
            total_consumed=models.Sum('quantity')
        ).order_by('-total_consumed')[:15]
        for item in raw_consumption:
            consumption_summary.append({
                'batch__medicine__generic_name': item['medicine__generic_name'],
                'batch__medicine__brand_name': item.get('medicine__brand_name') or '',
                'medicine__generic_name': item['medicine__generic_name'],
                'total_consumed': item['total_consumed'],
                'total_dispensed': item['total_consumed']
            })

        # 4. Stock Status Summary
        stock_summary = []
        for m in MedicineMaster.objects.all():
            m_batches = batch_qs.filter(medicine=m)
            tot_qty = m_batches.aggregate(t=models.Sum('quantity'))['t'] or 0
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
            'dispensing_summary': {
                'dispensed_today': dispensed_today_qty,
                'prescriptions_count': dispensed_today_rx
            },
            'stock_valuation': {
                'total_batches': tot_batches_count,
                'total_quantity': tot_qty_in_stock,
                'total_value': round(tot_val, 2)
            },
            'daily_dispensing': dispensing_data,
            'consumption_summary': consumption_summary,
            'stock_summary': stock_summary,
            'total_batches': batch_qs.count(),
            'total_purchase_orders': po_qs.count()
        })
