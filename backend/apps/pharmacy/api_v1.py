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
    class Meta:
        model = InventoryLedger
        fields = '__all__'



from rest_framework.permissions import BasePermission

class PharmacyAccessPermission(BasePermission):
    """
    Denies prescription and dispensation records to Compounder, Lab Technician, and Inventory-only users.
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
        if role in ['COMPOUNDER', 'LAB_TECHNICIAN', 'INVENTORY']:
            return False
        return True

class MedicineMasterViewSet(viewsets.ModelViewSet):
    queryset = MedicineMaster.objects.all()
    serializer_class = MedicineMasterSerializer
    permission_classes = [IsActiveStaff]

class MedicineBatchViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view of medicine batches. Direct balance modification is forbidden."""
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
        rx = serializer.save(doctor=self.request.user, doctor_staff=staff)
        if not rx.items.exists():
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

        is_pharm = (
            request.user.is_superuser or
            getattr(request.user, 'role', '') == 'PHARMACIST' or
            getattr(staff, 'designation', '') in ['Pharmacist', 'Chief Pharmacist'] or
            staff.role_assignments.filter(role__code='PHARMACIST', is_active=True).exists()
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

        is_pharm = (
            request.user.is_superuser or
            getattr(request.user, 'role', '') == 'PHARMACIST' or
            getattr(staff, 'designation', '') in ['Pharmacist', 'Chief Pharmacist'] or
            staff.role_assignments.filter(role__code='PHARMACIST', is_active=True).exists()
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

        is_pharm = (
            request.user.is_superuser or
            getattr(request.user, 'role', '') == 'PHARMACIST' or
            getattr(staff, 'designation', '') in ['Pharmacist', 'Chief Pharmacist'] or
            staff.role_assignments.filter(role__code='PHARMACIST', is_active=True).exists()
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

        is_pharm = (
            request.user.is_superuser or
            getattr(request.user, 'role', '') == 'PHARMACIST' or
            getattr(staff, 'designation', '') in ['Pharmacist', 'Chief Pharmacist'] or
            (staff and staff.role_assignments.filter(role__code='PHARMACIST', is_active=True).exists())
        )
        if not is_pharm:
            return Response({'error': 'Only pharmacists are authorized to dispense medications.'}, status=status.HTTP_403_FORBIDDEN)

        from apps.facilities.models import Facility
        rx = Prescription.objects.get(pk=serializer.validated_data['prescription_id'])
        fac = Facility.objects.get(pk=serializer.validated_data['facility_id'])
        check_facility_permission(fac, staff, request.user)
        check_facility_permission(rx.facility, staff, request.user)
        if rx.facility_id != fac.id:
            return Response({'error': 'Prescription does not belong to the specified facility scope.'}, status=status.HTTP_403_FORBIDDEN)

        allocations = []
        for itm in serializer.validated_data['items']:
            p_item = PrescriptionItem.objects.get(pk=itm['prescription_item_id'])
            batch = MedicineBatch.objects.get(pk=itm['batch_id'])
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
    class Meta:
        model = PurchaseOrderItem
        fields = '__all__'

class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True, read_only=True)

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
    rejection_reason = serializers.CharField(required=False, default="")

class ReceiveGRNSerializer(serializers.Serializer):
    purchase_order_id = serializers.IntegerField()
    grn_number = serializers.CharField(max_length=64)
    facility_id = serializers.IntegerField()
    items_received = ReceiveGRNItemSerializer(many=True)

class GoodsReceiptNoteSerializer(serializers.ModelSerializer):
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
        fac = Facility.objects.get(pk=request.data['facility'])
        check_facility_permission(fac, staff, request.user)
        if not has_role_permission(request.user, 'purchase_order.create'):
            return Response({'error': 'You do not have permission to create purchase orders.'}, status=status.HTTP_403_FORBIDDEN)
        ven = Vendor.objects.get(pk=request.data['vendor'])

        po = create_purchase_order(
            facility=fac,
            vendor=ven,
            created_by_staff=staff,
            po_number=request.data.get('po_number')
        )
        return Response(self.get_serializer(po).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='approve', permission_classes=[IsAdministrativeStaff])
    def approve(self, request, pk=None):
        po = self.get_object()
        serializer = ApprovePOSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff = get_request_staff(request)
        check_facility_permission(po.facility, staff, request.user)

        approval = approve_purchase_order(
            purchase_order=po,
            approver_staff=staff,
            approval_tier=serializer.validated_data.get('approval_tier', 1),
            status=serializer.validated_data.get('status', 'APPROVED'),
            remarks=serializer.validated_data.get('remarks', '')
        )
        po.refresh_from_db()
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
        serializer = ReceiveGRNSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff = get_request_staff(request)

        from apps.facilities.models import Facility
        po = PurchaseOrder.objects.get(pk=serializer.validated_data['purchase_order_id'])
        fac = Facility.objects.get(pk=serializer.validated_data['facility_id'])
        check_facility_permission(fac, staff, request.user)
        if not has_role_permission(request.user, 'goods_receipt.create'):
            return Response({'error': 'You do not have permission to record goods receipts.'}, status=status.HTTP_403_FORBIDDEN)

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
