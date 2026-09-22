from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.facilities.models import (
    Facility, FacilityRelationship, FacilityOxygenSupply,
    FacilityConsumableInventory, FacilityMaintenanceTicket,
    FacilityBedCapacity, FacilityBedAllocation
)
from apps.facilities.serializers import (
    FacilitySerializer, FacilityRelationshipSerializer,
    FacilityOxygenSupplySerializer, FacilityConsumableInventorySerializer,
    FacilityMaintenanceTicketSerializer, FacilityBedCapacitySerializer,
    FacilityBedAllocationSerializer
)
from apps.geography.models import District
from apps.accounts.permissions import get_accessible_facility_ids_for_user, HasPermission, HasFacilityScope

class FacilityViewSet(viewsets.ModelViewSet):
    serializer_class = FacilitySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['district', 'facility_type', 'urban_rural', 'status']
    search_fields = ['facility_name', 'facility_code', 'city_or_ulb']

    def get_queryset(self):
        queryset = Facility.objects.all().select_related('district', 'zone', 'ward', 'parent_facility')
        if self.request.query_params.get('all') == 'true':
            return queryset
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(id__in=accessible_ids)
        return queryset

class FacilityRelationshipViewSet(viewsets.ModelViewSet):
    serializer_class = FacilityRelationshipSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = FacilityRelationship.objects.all().select_related('source_facility', 'destination_facility')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(source_facility_id__in=accessible_ids) | queryset.filter(destination_facility_id__in=accessible_ids)
        return queryset

class FacilityHierarchyView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        accessible_ids = get_accessible_facility_ids_for_user(request.user)
        districts = District.objects.all().prefetch_related('facilities')
        tree = []
        for dist in districts:
            hospitals = Facility.objects.filter(district=dist, parent_facility=None)
            if accessible_ids is not None:
                hospitals = hospitals.filter(id__in=accessible_ids)
            dist_data = {
                'id': f"dist-{dist.id}",
                'name': dist.name,
                'type': 'DISTRICT',
                'children': []
            }

            def build_node(facility):
                if accessible_ids is not None and facility.id not in accessible_ids:
                    return None
                children = Facility.objects.filter(parent_facility=facility)
                child_nodes = [build_node(child) for child in children]
                child_nodes = [c for c in child_nodes if c is not None]
                return {
                    'id': facility.id,
                    'facility_code': facility.facility_code,
                    'name': facility.facility_name,
                    'type': facility.facility_type,
                    'population_served': facility.population_served,
                    'services': facility.services,
                    'children': child_nodes
                }

            for hosp in hospitals:
                node = build_node(hosp)
                if node:
                    dist_data['children'].append(node)
            
            # Also check if user has access to child facilities in this district even if main hospital is not accessible
            if not dist_data['children'] and accessible_ids is not None:
                child_facilities = Facility.objects.filter(district=dist, id__in=accessible_ids)
                for fac in child_facilities:
                    dist_data['children'].append({
                        'id': fac.id,
                        'facility_code': fac.facility_code,
                        'name': fac.facility_name,
                        'type': fac.facility_type,
                        'population_served': fac.population_served,
                        'services': fac.services,
                        'children': []
                    })

            if dist_data['children']:
                tree.append(dist_data)
        return Response({'hierarchy': tree})

class NetworkGraphView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        accessible_ids = get_accessible_facility_ids_for_user(request.user)
        facilities = Facility.objects.all()
        relationships = FacilityRelationship.objects.filter(active=True)

        if accessible_ids is not None:
            facilities = facilities.filter(id__in=accessible_ids)
            relationships = relationships.filter(source_facility_id__in=accessible_ids) | relationships.filter(destination_facility_id__in=accessible_ids)

        nodes = []
        for f in facilities:
            nodes.append({
                'id': str(f.id),
                'code': f.facility_code,
                'name': f.facility_name,
                'type': f.facility_type,
                'district': f.district.name if f.district else '',
                'lat': float(f.latitude),
                'lng': float(f.longitude),
                'emergency': f.emergency_available
            })

        links = []
        for r in relationships:
            links.append({
                'id': str(r.id),
                'source': str(r.source_facility_id),
                'target': str(r.destination_facility_id),
                'type': r.relationship_type,
                'priority': r.priority,
                'distance_km': float(r.distance_km)
            })

        return Response({'nodes': nodes, 'links': links})


class FacilityOxygenSupplyViewSet(viewsets.ModelViewSet):
    serializer_class = FacilityOxygenSupplySerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permissions = {
        'GET': 'hospital.view',
        'POST': 'system_config.update',
        'PUT': 'system_config.update',
        'PATCH': 'system_config.update',
        'DELETE': 'system_config.update'
    }
    filterset_fields = ['facility', 'status', 'oxygen_source']

    def get_queryset(self):
        queryset = FacilityOxygenSupply.objects.all().select_related('facility')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        return queryset


class FacilityConsumableInventoryViewSet(viewsets.ModelViewSet):
    serializer_class = FacilityConsumableInventorySerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permissions = {
        'GET': 'hospital.view',
        'POST': 'system_config.update',
        'PUT': 'system_config.update',
        'PATCH': 'system_config.update',
        'DELETE': 'system_config.update'
    }
    filterset_fields = ['facility', 'category', 'reorder_status']

    def get_queryset(self):
        queryset = FacilityConsumableInventory.objects.all().select_related('facility')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        return queryset


class FacilityMaintenanceTicketViewSet(viewsets.ModelViewSet):
    serializer_class = FacilityMaintenanceTicketSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permissions = {
        'GET': 'hospital.view',
        'POST': 'system_config.update',
        'PUT': 'system_config.update',
        'PATCH': 'system_config.update',
        'DELETE': 'system_config.update'
    }
    filterset_fields = ['facility', 'category', 'priority', 'status']

    def get_queryset(self):
        queryset = FacilityMaintenanceTicket.objects.all().select_related('facility')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        return queryset


class FacilityBedCapacityViewSet(viewsets.ModelViewSet):
    serializer_class = FacilityBedCapacitySerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permissions = {
        'GET': 'hospital.view',
        'POST': 'system_config.update',
        'PUT': 'system_config.update',
        'PATCH': 'system_config.update',
        'DELETE': 'system_config.update'
    }
    filterset_fields = ['facility', 'bed_category']

    def get_queryset(self):
        queryset = FacilityBedCapacity.objects.all().select_related('facility')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        return queryset


class FacilityBedAllocationViewSet(viewsets.ModelViewSet):
    serializer_class = FacilityBedAllocationSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission, HasFacilityScope]
    required_permissions = {
        'GET': 'hospital.view',
        'POST': 'system_config.update',
        'PUT': 'system_config.update',
        'PATCH': 'system_config.update',
        'DELETE': 'system_config.update'
    }
    filterset_fields = ['facility', 'bed_category', 'status']

    def get_queryset(self):
        queryset = FacilityBedAllocation.objects.all().select_related('facility', 'patient')
        accessible_ids = get_accessible_facility_ids_for_user(self.request.user)
        if accessible_ids is not None:
            queryset = queryset.filter(facility_id__in=accessible_ids)
        return queryset

