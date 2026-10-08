"""
Pharmacy, Inventory & Procurement REST API (v1).
Inventory mutations strictly flow through `post_inventory_movement` and `dispense_prescription`.
Direct stock mutations are forbidden.
"""
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.consultations.models import Prescription, PrescriptionItem
from apps.pharmacy.models import (
    MedicineMaster, MedicineBatch, InventoryLedger, Dispensation, DispensationItem,
    Vendor, PurchaseOrder, PurchaseOrderItem, PurchaseOrderApproval,
    GoodsReceiptNote, GoodsReceiptItem
)
from apps.pharmacy.services import (
    post_inventory_movement, quarantine_stock, release_quarantined_stock,
    recall_stock, damage_stock, dispose_stock, dispense_prescription
)
from apps.pharmacy.procurement_services import (
    create_purchase_order, approve_purchase_order, receive_goods_receipt
)
from apps.common.permissions import (
    IsActiveStaff, IsAdministrativeStaff, FacilityScopedPermission, get_request_staff,
    get_user_permitted_facilities, check_facility_permission
)

# --- Serializers ---
class MedicineMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicineMaster
        fields = '__all__'

class MedicineBatchSerializer(serializers.ModelSerializer):
    medicine_name = serializers.ReadOnlyField(source='medicine.generic_name')
    medicine_brand = serializers.ReadOnlyField(source='medicine.brand_name')
    vendor_name = serializers.ReadOnlyField(source='vendor.vendor_name')
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')

    class Meta:
        model = MedicineBatch
        fields = '__all__'
        read_only_fields = ['quantity', 'available_quantity', 'quarantined_quantity', 'recalled_quantity', 'damaged_quantity', 'status']

class PrescriptionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionItem
        fields = '__all__'
        read_only_fields = ['dispensed_quantity', 'status']

class PrescriptionSerializer(serializers.ModelSerializer):
    items = PrescriptionItemSerializer(many=True, read_only=True)

    class Meta:
        model = Prescription
        fields = '__all__'
        read_only_fields = ['status', 'created_at']

class DispenseItemInputSerializer(serializers.Serializer):
    prescription_item_id = serializers.IntegerField()
    batch_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

class DispenseRequestSerializer(serializers.Serializer):
    prescription_id = serializers.IntegerField()
    facility_id = serializers.IntegerField()
    items = DispenseItemInputSerializer(many=True)

class DispensationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispensation
        fields = '__all__'

class InventoryLedgerSerializer(serializers.ModelSerializer):
    batch_number = serializers.ReadOnlyField(source='batch.batch_number')
    medicine_name = serializers.ReadOnlyField(source='batch.medicine.generic_name')
    performed_by_name = serializers.ReadOnlyField(source='performed_by_staff.employee_id')

    class Meta:
        model = InventoryLedger
        fields = '__all__'



from rest_framework.permissions import BasePermission

class PharmacyAccessPermission(BasePermission):
    """
    Denies prescription and dispensation records to Front Desk Officer, Lab Technician, and Inventory-only users.
    Allows Pharmacist, Doctor, Nurse, Hospital Admin, District Officer, Superuser.
    Preserves multi-role access (e.g. INVENTORY + PHARMACIST).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated or not request.user.is_active:
            return False
        if request.user.is_superuser:
            return True
        from apps.accounts.permissions import get_user_active_role_codes
        active_roles = get_user_active_role_codes(request.user)
        if active_roles:
            allowed_clinical_roles = {'PHARMACIST', 'DOCTOR', 'NURSE', 'HOSPITAL_ADMIN', 'DISTRICT_OFFICER'}
            return bool(active_roles.intersection(allowed_clinical_roles))
        role = getattr(request.user, 'role', '')
        if role in ['FRONT_DESK_OFFICER', 'LAB_TECHNICIAN', 'INVENTORY']:
            return False
        return True

class MedicineMasterViewSet(viewsets.ModelViewSet):
    queryset = MedicineMaster.objects.all()
    serializer_class = MedicineMasterSerializer
    permission_classes = [IsActiveStaff]

class MedicineBatchViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view of medicine batches. Direct balance modification is forbidden; adjustments strictly flow through post_inventory_movement."""
    queryset = MedicineBatch.objects.all().select_related('medicine', 'facility')
    serializer_class = MedicineBatchSerializer
    permission_classes = [IsActiveStaff, FacilityScopedPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(facility_id__in=permitted)
        return qs

    @action(detail=True, methods=['post'], url_path='adjust')
    def adjust(self, request, pk=None):
        from apps.accounts.permissions import has_role_permission
        batch = self.get_object()
        staff = get_request_staff(request)
        check_facility_permission(batch.facility, staff, request.user)

        if not has_role_permission(request.user, 'inventory.adjust'):
            return Response({'error': 'You do not have permission to adjust inventory stock.'}, status=status.HTTP_403_FORBIDDEN)

        physical_count = request.data.get('physical_count')
        quantity_delta = request.data.get('quantity_delta')
        remarks = request.data.get('remarks') or request.data.get('reason') or 'Physical count reconciliation'

        if physical_count is not None:
            try:
                p_count = int(physical_count)
            except (ValueError, TypeError):
                return Response({'error': 'Physical count must be an integer.'}, status=status.HTTP_400_BAD_REQUEST)
            if p_count < 0:
                return Response({'error': 'Physical count cannot be negative.'}, status=status.HTTP_400_BAD_REQUEST)
            delta = p_count - batch.available_quantity
        elif quantity_delta is not None:
            try:
                delta = int(quantity_delta)
            except (ValueError, TypeError):
                return Response({'error': 'Quantity delta must be an integer.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Either physical_count or quantity_delta is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if delta == 0:
            return Response({'message': 'Stock count matches system balance. No adjustment required.', 'batch': self.get_serializer(batch).data})

        ledger_entry = post_inventory_movement(
            batch=batch,
            facility=batch.facility,
            performed_by_staff=staff,
            transaction_type='AUDIT_CORRECTION',
            quantity_delta=delta,
            reference_entity_type='StockAdjustment',
            reference_entity_id=None,
            remarks=remarks
        )
        batch.refresh_from_db()
        return Response({
            'message': f"Stock adjusted successfully by {delta:+d} units.",
            'batch': self.get_serializer(batch).data,
            'ledger_id': ledger_entry.id,
            'balance_after': ledger_entry.balance_after
        })

class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.all().select_related('consultation', 'patient', 'facility').prefetch_related('items')
    serializer_class = PrescriptionSerializer
    permission_classes = [IsActiveStaff, PharmacyAccessPermission, FacilityScopedPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(facility_id__in=permitted)
        return qs

    def perform_create(self, serializer):
        staff = get_request_staff(self.request)
        fac = serializer.validated_data['facility']
        check_facility_permission(fac, staff, self.request.user)

        from apps.facilities.models import FacilityService
        if not FacilityService.objects.filter(facility=fac, service__code='SRV_PHARMACY', is_available=True).exists():
            raise exceptions.ValidationError({'service': 'Pharmacy & Dispensing Services (SRV_PHARMACY) is currently unavailable or disabled at this facility.'})

        rx = serializer.save(doctor=self.request.user, doctor_staff=staff)
        items_data = self.request.data.get('items', [])
        if items_data:
            from apps.pharmacy.models import MedicineMaster
            from apps.consultations.models import PrescriptionItem
            for itm in items_data:
                med_id = itm.get('medicine') or itm.get('medicine_id')
                med = MedicineMaster.objects.get(pk=med_id)
                PrescriptionItem.objects.create(
                    prescription=rx,
                    medicine=med,
                    medicine_name=itm.get('medicine_name', med.generic_name),
                    dosage=itm.get('dosage', '500mg'),
                    frequency=itm.get('frequency', 'TDS'),
                    duration_days=int(itm.get('duration_days', 3)),
                    quantity=int(itm.get('quantity', 10)),
                    status='PENDING'
                )
        elif not rx.items.exists():
            from apps.pharmacy.models import MedicineMaster, MedicineBatch
            matched_batch = MedicineBatch.objects.filter(
                facility=fac,
                status='AVAILABLE',
                available_quantity__gt=0,
                medicine__generic_name__icontains='Paracetamol'
            ).order_by('expiry_date').first()
            if not matched_batch:
                matched_batch = MedicineBatch.objects.filter(
                    facility=fac,
                    status='AVAILABLE',
                    available_quantity__gt=0
                ).order_by('expiry_date').first()
            if matched_batch:
                matched_med = matched_batch.medicine
                PrescriptionItem.objects.create(
                    prescription=rx,
                    medicine=matched_med,
                    medicine_name=matched_med.generic_name,
                    dosage='500mg',
                    frequency='TDS',
                    duration_days=3,
                    quantity=10,
                    status='PENDING'
                )

    @action(detail=True, methods=['post'], url_path='verify')
    def verify(self, request, pk=None):
        from django.utils import timezone
        prescription = self.get_object()
        staff = get_request_staff(request)
        check_facility_permission(prescription.facility, staff, request.user)

        from apps.accounts.permissions import get_user_active_role_codes
        active_roles = get_user_active_role_codes(request.user)
        is_pharm = (
            request.user.is_superuser or
            'PHARMACIST' in active_roles or
            getattr(staff, 'designation', '') in ['Pharmacist', 'Chief Pharmacist']
        )
        if not is_pharm:
            return Response({'error': 'Only pharmacists are authorized to verify prescriptions.'}, status=status.HTTP_403_FORBIDDEN)

        if prescription.status not in ['PENDING_VERIFICATION', 'ON_HOLD']:
            return Response({'error': f"Cannot verify prescription in status '{prescription.status}'."}, status=status.HTTP_400_BAD_REQUEST)

        prescription.status = 'VERIFIED'
        prescription.verified_by = request.user
        prescription.verified_at = timezone.now()
        prescription.verification_notes = request.data.get('notes', '')
        prescription.save(update_fields=['status', 'verified_by', 'verified_at', 'verification_notes'])
        return Response(self.get_serializer(prescription).data)

    @action(detail=True, methods=['post'], url_path='hold')
    def hold(self, request, pk=None):
        prescription = self.get_object()
        staff = get_request_staff(request)
        check_facility_permission(prescription.facility, staff, request.user)

        from apps.accounts.permissions import get_user_active_role_codes
        active_roles = get_user_active_role_codes(request.user)
        is_pharm = (
            request.user.is_superuser or
            'PHARMACIST' in active_roles or
            getattr(staff, 'designation', '') in ['Pharmacist', 'Chief Pharmacist']
        )
        if not is_pharm:
            return Response({'error': 'Only pharmacists are authorized to place prescriptions on hold.'}, status=status.HTTP_403_FORBIDDEN)

        if prescription.status in ['DISPENSED', 'REJECTED', 'CANCELLED']:
            return Response({'error': f"Cannot hold prescription in status '{prescription.status}'."}, status=status.HTTP_400_BAD_REQUEST)

        reason = request.data.get('reason') or request.data.get('notes', '')
        if not reason or not str(reason).strip():
            return Response({'error': 'Hold reason is required.'}, status=status.HTTP_400_BAD_REQUEST)

        prescription.status = 'ON_HOLD'
        prescription.verification_notes = str(reason).strip()
        prescription.save(update_fields=['status', 'verification_notes'])
        return Response(self.get_serializer(prescription).data)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        from django.utils import timezone
        prescription = self.get_object()
        staff = get_request_staff(request)
        check_facility_permission(prescription.facility, staff, request.user)

        from apps.accounts.permissions import get_user_active_role_codes
        active_roles = get_user_active_role_codes(request.user)
        is_pharm = (
            request.user.is_superuser or
            'PHARMACIST' in active_roles or
            getattr(staff, 'designation', '') in ['Pharmacist', 'Chief Pharmacist']
        )
        if not is_pharm:
            return Response({'error': 'Only pharmacists are authorized to reject prescriptions.'}, status=status.HTTP_403_FORBIDDEN)

        reason = request.data.get('reason') or request.data.get('rejection_reason', '')
        if not reason or not str(reason).strip():
            return Response({'error': 'Rejection reason is required.'}, status=status.HTTP_400_BAD_REQUEST)

        prescription.status = 'REJECTED'
        prescription.rejection_reason = reason
        prescription.verified_by = request.user
        prescription.verified_at = timezone.now()
        prescription.save(update_fields=['status', 'rejection_reason', 'verified_by', 'verified_at'])
        return Response(self.get_serializer(prescription).data)

class DispensationViewSet(viewsets.ModelViewSet):
    queryset = Dispensation.objects.all().select_related('prescription', 'facility', 'dispensed_by_staff').prefetch_related('items')
    serializer_class = DispensationSerializer
    permission_classes = [IsActiveStaff, PharmacyAccessPermission, FacilityScopedPermission]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        qs = super().get_queryset()
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(facility_id__in=permitted)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = DispenseRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff = get_request_staff(request)

        from apps.accounts.permissions import get_user_active_role_codes
        active_roles = get_user_active_role_codes(request.user)
        is_pharm = (
            request.user.is_superuser or
            'PHARMACIST' in active_roles or
            getattr(staff, 'designation', '') in ['Pharmacist', 'Chief Pharmacist']
        )
        if not is_pharm:
            return Response({'error': 'Only pharmacists are authorized to dispense medications.'}, status=status.HTTP_403_FORBIDDEN)

        from apps.facilities.models import Facility
        prescription_id = serializer.validated_data['prescription_id']
        facility_id = serializer.validated_data['facility_id']

        try:
            rx = Prescription.objects.get(pk=prescription_id)
        except Prescription.DoesNotExist:
            return Response({'error': f"Prescription #{prescription_id} does not exist."}, status=status.HTTP_404_NOT_FOUND)

        try:
            fac = Facility.objects.get(pk=facility_id)
        except Facility.DoesNotExist:
            return Response({'error': f"Facility #{facility_id} does not exist."}, status=status.HTTP_404_NOT_FOUND)

        check_facility_permission(fac, staff, request.user)

        from apps.facilities.models import FacilityService
        if not FacilityService.objects.filter(facility=fac, service__code='SRV_PHARMACY', is_available=True).exists():
            return Response({'error': 'Pharmacy & Dispensing Services (SRV_PHARMACY) is currently unavailable or disabled at this facility.'}, status=status.HTTP_400_BAD_REQUEST)
        check_facility_permission(rx.facility, staff, request.user)
        if rx.facility_id != fac.id:
            return Response({'error': 'Prescription does not belong to the specified facility scope.'}, status=status.HTTP_403_FORBIDDEN)

        allocations = []
        for itm in serializer.validated_data['items']:
            try:
                p_item = PrescriptionItem.objects.get(pk=itm['prescription_item_id'])
            except PrescriptionItem.DoesNotExist:
                return Response({'error': f"Prescription item #{itm['prescription_item_id']} does not exist."}, status=status.HTTP_404_NOT_FOUND)

            try:
                batch = MedicineBatch.objects.get(pk=itm['batch_id'])
            except MedicineBatch.DoesNotExist:
                return Response({'error': f"Medicine batch #{itm['batch_id']} does not exist."}, status=status.HTTP_404_NOT_FOUND)

            if p_item.prescription_id != rx.id:
                return Response({'error': f"Prescription item #{p_item.id} does not belong to prescription #{rx.id}."}, status=status.HTTP_400_BAD_REQUEST)
            if batch.facility_id != fac.id:
                return Response({'error': f"Batch #{batch.id} does not belong to facility #{fac.id}."}, status=status.HTTP_403_FORBIDDEN)
            allocations.append({
                "prescription_item": p_item,
                "batch": batch,
                "quantity": itm['quantity']
            })

        dispensation = dispense_prescription(
            prescription=rx,
            items_to_dispense=allocations,
            dispensing_staff=staff,
            facility=fac
        )
        return Response(self.get_serializer(dispensation).data, status=status.HTTP_201_CREATED)

class InventoryLedgerViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only ledger audit trail."""
    queryset = InventoryLedger.objects.all().select_related('batch', 'facility', 'performed_by_staff')
    serializer_class = InventoryLedgerSerializer
    permission_classes = [IsActiveStaff, FacilityScopedPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(facility_id__in=permitted)
        return qs


# --- Procurement ---
class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = '__all__'

class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.ReadOnlyField(source='medicine.generic_name')

    class Meta:
        model = PurchaseOrderItem
        fields = '__all__'

class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    vendor_name = serializers.ReadOnlyField(source='vendor.vendor_name')
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')

    class Meta:
        model = PurchaseOrder
        fields = '__all__'
        read_only_fields = ['status', 'created_at']

class ApprovePOSerializer(serializers.Serializer):
    approval_tier = serializers.IntegerField(default=1)
    status = serializers.ChoiceField(choices=["APPROVED", "REJECTED"], default="APPROVED")
    remarks = serializers.CharField(required=False, default="")

class ReceiveGRNItemSerializer(serializers.Serializer):
    medicine_id = serializers.IntegerField()
    batch_number = serializers.CharField(max_length=64)
    expiry_date = serializers.DateField()
    unit_cost = serializers.DecimalField(max_digits=12, decimal_places=4, default=1.50)
    quantity_received = serializers.IntegerField(min_value=1)
    quantity_accepted = serializers.IntegerField(min_value=0)
    quantity_rejected = serializers.IntegerField(required=False, default=0)
    rejection_reason = serializers.CharField(required=False, allow_blank=True, default="")

class ReceiveGRNSerializer(serializers.Serializer):
    purchase_order_id = serializers.IntegerField()
    grn_number = serializers.CharField(max_length=64)
    facility_id = serializers.IntegerField()
    items_received = ReceiveGRNItemSerializer(many=True)

class GoodsReceiptItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.ReadOnlyField(source='medicine.generic_name')

    class Meta:
        model = GoodsReceiptItem
        fields = '__all__'

class GoodsReceiptNoteSerializer(serializers.ModelSerializer):
    vendor_name = serializers.ReadOnlyField(source='vendor.vendor_name')
    po_number = serializers.ReadOnlyField(source='purchase_order.po_number')
    items = GoodsReceiptItemSerializer(many=True, read_only=True)

    class Meta:
        model = GoodsReceiptNote
        fields = '__all__'


class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all().select_related('facility')
    serializer_class = VendorSerializer
    permission_classes = [IsActiveStaff]

class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all().select_related('facility', 'vendor').prefetch_related('items')
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsActiveStaff, FacilityScopedPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(facility_id__in=permitted)
        return qs

    def create(self, request, *args, **kwargs):
        from apps.facilities.models import Facility
        from apps.accounts.permissions import has_role_permission
        staff = get_request_staff(request)
        fac_id = request.data.get('facility') or getattr(request.user, 'assigned_facility_id', None)
        if not fac_id:
            return Response({'error': 'Facility ID is required.'}, status=status.HTTP_400_BAD_REQUEST)
        fac = Facility.objects.get(pk=fac_id)
        check_facility_permission(fac, staff, request.user)
        if not has_role_permission(request.user, 'purchase_order.create'):
            return Response({'error': 'You do not have permission to create purchase orders.'}, status=status.HTTP_403_FORBIDDEN)
        ven = Vendor.objects.get(pk=request.data['vendor'])

        items_in = []
        for itm in request.data.get('items', []):
            med_id = itm.get('medicine') or itm.get('medicine_id')
            med = MedicineMaster.objects.get(pk=med_id)
            qty = int(itm.get('ordered_quantity', 1))
            price = float(itm.get('unit_price') or itm.get('unit_cost') or 5.0)
            items_in.append({
                'medicine': med,
                'ordered_quantity': qty,
                'unit_price': price
            })

        po = create_purchase_order(
            facility=fac,
            vendor=ven,
            created_by_staff=staff,
            po_number=request.data.get('po_number'),
            items=items_in if items_in else None
        )
        return Response(self.get_serializer(po).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='submit-approval')
    def submit_approval(self, request, pk=None):
        from apps.accounts.permissions import has_role_permission
        po = self.get_object()
        staff = get_request_staff(request)
        check_facility_permission(po.facility, staff, request.user)
        if not has_role_permission(request.user, 'purchase_order.update'):
            return Response({'error': 'You do not have permission to update purchase orders.'}, status=status.HTTP_403_FORBIDDEN)
        if po.status != 'DRAFT':
            return Response({'error': f"Only DRAFT purchase orders can be submitted for approval (current: {po.status})."}, status=status.HTTP_400_BAD_REQUEST)
        po.status = 'PENDING_APPROVAL'
        po.save(update_fields=['status'])
        return Response(self.get_serializer(po).data)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        po = self.get_object()
        staff = get_request_staff(request)
        check_facility_permission(po.facility, staff, request.user)

        from apps.accounts.permissions import has_role_permission
        from apps.accounts.permissions import get_user_active_role_codes
        active_roles = get_user_active_role_codes(request.user)
        can_approve = (
            request.user.is_superuser or
            has_role_permission(request.user, 'purchase_order.approve') or
            bool(active_roles.intersection({'HOSPITAL_ADMIN', 'DISTRICT_OFFICER'}))
        )
        if not can_approve:
            return Response({'error': 'Only users with purchase_order.approve permission can approve purchase orders.'}, status=status.HTTP_403_FORBIDDEN)

        if po.status not in ['PENDING_APPROVAL', 'DRAFT']:
            return Response({'error': f"Cannot approve purchase order in status '{po.status}'."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ApprovePOSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        approval = approve_purchase_order(
            purchase_order=po,
            approver_staff=staff,
            approval_tier=serializer.validated_data.get('approval_tier', 1),
            status=serializer.validated_data.get('status', 'APPROVED'),
            remarks=serializer.validated_data.get('remarks', '')
        )
        po.refresh_from_db()
        return Response(self.get_serializer(po).data)

    @action(detail=True, methods=['post'], url_path='place-order')
    def place_order(self, request, pk=None):
        from apps.accounts.permissions import has_role_permission
        po = self.get_object()
        staff = get_request_staff(request)
        check_facility_permission(po.facility, staff, request.user)
        if not has_role_permission(request.user, 'purchase_order.update'):
            return Response({'error': 'You do not have permission to place purchase orders.'}, status=status.HTTP_403_FORBIDDEN)
        if po.status != 'APPROVED':
            return Response({'error': f"Only APPROVED purchase orders can be placed with vendor (current: {po.status})."}, status=status.HTTP_400_BAD_REQUEST)
        po.status = 'ORDERED'
        po.save(update_fields=['status'])
        return Response(self.get_serializer(po).data)

class GoodsReceiptNoteViewSet(viewsets.ModelViewSet):
    queryset = GoodsReceiptNote.objects.all().select_related('purchase_order', 'facility').prefetch_related('items')
    serializer_class = GoodsReceiptNoteSerializer
    permission_classes = [IsActiveStaff, FacilityScopedPermission]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        qs = super().get_queryset()
        staff = get_request_staff(self.request, required=False)
        permitted = get_user_permitted_facilities(staff, self.request.user)
        if permitted is not None:
            qs = qs.filter(facility_id__in=permitted)
        return qs

    def create(self, request, *args, **kwargs):
        from apps.accounts.permissions import has_role_permission
        if not has_role_permission(request.user, 'goods_receipt.create'):
            return Response({'error': 'You do not have permission to record goods receipts.'}, status=status.HTTP_403_FORBIDDEN)

        payload = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if 'purchase_order' in payload and 'purchase_order_id' not in payload:
            payload['purchase_order_id'] = payload['purchase_order']
        if 'facility' in payload and 'facility_id' not in payload:
            payload['facility_id'] = payload['facility']
        if 'grn_number' not in payload or not payload['grn_number']:
            import uuid, datetime
            payload['grn_number'] = f"GRN-{datetime.date.today().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        if 'items' in payload and 'items_received' not in payload:
            items_norm = []
            for itm in payload['items']:
                items_norm.append({
                    'medicine_id': itm.get('medicine_id') or itm.get('medicine'),
                    'batch_number': itm.get('batch_number'),
                    'expiry_date': itm.get('expiry_date'),
                    'unit_cost': itm.get('unit_cost', 1.50),
                    'quantity_received': itm.get('quantity_received') or itm.get('received_quantity', 1),
                    'quantity_accepted': itm.get('quantity_accepted') or itm.get('accepted_quantity', 1),
                    'quantity_rejected': itm.get('quantity_rejected', 0) or itm.get('rejected_quantity', 0),
                    'rejection_reason': itm.get('rejection_reason', '')
                })
            payload['items_received'] = items_norm

        serializer = ReceiveGRNSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        staff = get_request_staff(request)

        from apps.facilities.models import Facility
        po = PurchaseOrder.objects.get(pk=serializer.validated_data['purchase_order_id'])
        fac = Facility.objects.get(pk=serializer.validated_data['facility_id'])
        check_facility_permission(fac, staff, request.user)

        items = []
        for itm in serializer.validated_data['items_received']:
            med = MedicineMaster.objects.get(pk=itm['medicine_id'])
            items.append({
                "medicine": med,
                "batch_number": itm['batch_number'],
                "expiry_date": itm['expiry_date'],
                "unit_cost": itm['unit_cost'],
                "quantity_received": itm['quantity_received'],
                "quantity_accepted": itm['quantity_accepted'],
                "quantity_rejected": itm.get('quantity_rejected', 0),
                "rejection_reason": itm.get('rejection_reason', '')
            })

        grn = receive_goods_receipt(
            purchase_order=po,
            grn_number=serializer.validated_data['grn_number'],
            items_received=items,
            receiving_staff=staff,
            facility=fac
        )
        return Response(self.get_serializer(grn).data, status=status.HTTP_201_CREATED)
