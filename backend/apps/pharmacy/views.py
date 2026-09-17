from rest_framework import serializers, viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.pharmacy.models import MedicineMaster, MedicineBatch, InventoryTransaction
from apps.consultations.models import Prescription, PrescriptionItem
import datetime

class MedicineMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicineMaster
        fields = '__all__'

class MedicineBatchSerializer(serializers.ModelSerializer):
    medicine_name = serializers.ReadOnlyField(source='medicine.generic_name')
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')

    class Meta:
        model = MedicineBatch
        fields = '__all__'

class InventoryTransactionSerializer(serializers.ModelSerializer):
    medicine_name = serializers.ReadOnlyField(source='medicine.generic_name')
    batch_number = serializers.ReadOnlyField(source='batch.batch_number')

    class Meta:
        model = InventoryTransaction
        fields = '__all__'

class MedicineMasterViewSet(viewsets.ModelViewSet):
    queryset = MedicineMaster.objects.all()
    serializer_class = MedicineMasterSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

from apps.accounts.permissions import get_accessible_facility_ids_for_user, HasPermission, HasFacilityScope

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
    filterset_fields = ['facility', 'status', 'medicine']

    def get_queryset(self):
        queryset = MedicineBatch.objects.all().select_related('medicine', 'facility')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        return queryset

class DispenseMedicineView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permission = 'pharmacy.dispense'


    def post(self, request):
        prescription_id = request.data.get('prescription_id')
        items_to_dispense = request.data.get('items', []) # [{'item_id': 1, 'batch_id': 2, 'qty': 14}]

        if not prescription_id:
            return Response({'error': 'Prescription ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            prescription = Prescription.objects.get(pk=prescription_id)
        except Prescription.DoesNotExist:
            return Response({'error': 'Prescription not found'}, status=status.HTTP_404_NOT_FOUND)

        dispensed_summary = []
        for item in items_to_dispense:
            item_id = item.get('item_id')
            batch_id = item.get('batch_id')
            qty = item.get('qty', 14)

            p_item = PrescriptionItem.objects.filter(pk=item_id, prescription=prescription).first()
            if not p_item:
                continue

            # FEFO Batch selection: if batch_id not provided, pick earliest expiry active batch
            if batch_id:
                batch = MedicineBatch.objects.filter(pk=batch_id, facility=prescription.facility).first()
            else:
                batch = MedicineBatch.objects.filter(
                    facility=prescription.facility,
                    quantity__gte=qty,
                    expiry_date__gt=datetime.date.today(),
                    status='ACTIVE'
                ).order_by('expiry_date').first()

            if batch:
                batch.quantity -= qty
                if batch.quantity <= 50:
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
                    created_by=request.user
                )

                p_item.status = 'DISPENSED'
                p_item.save()
                dispensed_summary.append({
                    'item': p_item.medicine_name,
                    'batch': batch.batch_number,
                    'qty': qty,
                    'remaining_stock': batch.quantity
                })

        prescription.status = 'DISPENSED'
        prescription.save()

        return Response({
            'message': 'Medicines successfully dispensed using FEFO rule!',
            'dispensed_items': dispensed_summary
        })
