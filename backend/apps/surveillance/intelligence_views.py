"""
DRF Views for Public Health Intelligence Module - STEP 1 Foundation
Provides secure, role-scoped endpoints for:
1. Disease trend analysis
2. Disease-by-locality aggregation
3. Historical disease aggregation
4. Hospital-level aggregation
5. District-level aggregation
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

from apps.accounts.permissions import HasPermission
from apps.surveillance.intelligence_services import (
    calculate_disease_trends,
    aggregate_disease_by_locality,
    aggregate_historical_disease,
    aggregate_hospital_level,
    aggregate_district_level,
    get_public_health_intelligence_summary,
    get_demographic_intelligence,
    resolve_facility_scope
)


class BaseIntelligenceView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasPermission]
    required_permission = 'dashboard.view'


class PublicHealthDiseaseTrendsView(BaseIntelligenceView):
    """
    1. Disease Trend Analysis Endpoint
    Computes current, previous, 7d, 30d, 90d cases, monthly counts,
    percentage change, and trend direction.
    """
    def get(self, request):
        fac_id = request.query_params.get('facility')
        dist_id = request.query_params.get('district')
        disease = request.query_params.get('disease')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        as_of_date = request.query_params.get('date')
        days = int(request.query_params.get('days', 7))

        scope = resolve_facility_scope(
            user=request.user,
            requested_facility_id=fac_id,
            requested_district_id=dist_id
        )
        if not scope.is_authorized:
            return Response({'error': scope.error}, status=status.HTTP_403_FORBIDDEN)

        data = calculate_disease_trends(
            facility_ids=scope.facility_ids,
            district_id=scope.district_id,
            disease_name=disease,
            start_date=start_date,
            end_date=end_date,
            as_of_date=as_of_date,
            window_days=days
        )
        return Response(data)


class PublicHealthDiseaseLocalityView(BaseIntelligenceView):
    """
    2. Disease-by-Locality Aggregation Endpoint
    Computes cases by locality/ward, reporting hospitals, locality share %,
    and trend direction.
    """
    def get(self, request):
        fac_id = request.query_params.get('facility')
        dist_id = request.query_params.get('district')
        disease = request.query_params.get('disease')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        as_of_date = request.query_params.get('date')
        days = int(request.query_params.get('days', 14))

        scope = resolve_facility_scope(
            user=request.user,
            requested_facility_id=fac_id,
            requested_district_id=dist_id
        )
        if not scope.is_authorized:
            return Response({'error': scope.error}, status=status.HTTP_403_FORBIDDEN)

        data = aggregate_disease_by_locality(
            facility_ids=scope.facility_ids,
            district_id=scope.district_id,
            disease_name=disease,
            start_date=start_date,
            end_date=end_date,
            as_of_date=as_of_date,
            window_days=days
        )
        return Response(data)


class PublicHealthHistoricalDiseaseView(BaseIntelligenceView):
    """
    3. Historical Disease Aggregation Endpoint
    Multi-month sequential series with severity breakdowns.
    """
    def get(self, request):
        fac_id = request.query_params.get('facility')
        dist_id = request.query_params.get('district')
        disease = request.query_params.get('disease')
        months = int(request.query_params.get('months', 6))
        as_of_date = request.query_params.get('date')

        scope = resolve_facility_scope(
            user=request.user,
            requested_facility_id=fac_id,
            requested_district_id=dist_id
        )
        if not scope.is_authorized:
            return Response({'error': scope.error}, status=status.HTTP_403_FORBIDDEN)

        data = aggregate_historical_disease(
            facility_ids=scope.facility_ids,
            district_id=scope.district_id,
            disease_name=disease,
            months=months,
            as_of_date=as_of_date
        )
        return Response(data)


class PublicHealthHospitalAggregationView(BaseIntelligenceView):
    """
    4. Hospital-Level Aggregation Endpoint
    Strictly locked to assigned hospital for Hospital Admin / Doctor.
    """
    def get(self, request):
        fac_id = request.query_params.get('facility')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        as_of_date = request.query_params.get('date')

        # Determine target hospital ID
        target_fac_id = fac_id if (fac_id is not None and str(fac_id).strip() != '') else getattr(request.user, 'assigned_facility_id', None)
        if not target_fac_id:
            return Response({'error': 'Hospital identifier required.'}, status=status.HTTP_400_BAD_REQUEST)

        scope = resolve_facility_scope(user=request.user, requested_facility_id=target_fac_id)
        if not scope.is_authorized:
            return Response({'error': scope.error}, status=status.HTTP_403_FORBIDDEN)

        data = aggregate_hospital_level(
            facility_id=scope.facility_ids[0],
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            as_of_date=as_of_date
        )
        if 'error' in data:
            return Response(data, status=status.HTTP_403_FORBIDDEN)
        return Response(data)


class PublicHealthDistrictAggregationView(BaseIntelligenceView):
    """
    5. District-Level Aggregation Endpoint
    Scoped to assigned district with strict cross-district isolation.
    """
    def get(self, request):
        dist_id = request.query_params.get('district')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        as_of_date = request.query_params.get('date')

        target_dist_id = dist_id if (dist_id is not None and str(dist_id).strip() != '') else getattr(request.user, 'assigned_district_id', None)
        if not target_dist_id:
            return Response({'error': 'District identifier required.'}, status=status.HTTP_400_BAD_REQUEST)

        scope = resolve_facility_scope(user=request.user, requested_district_id=target_dist_id)
        if not scope.is_authorized:
            return Response({'error': scope.error}, status=status.HTTP_403_FORBIDDEN)

        data = aggregate_district_level(
            district_id=scope.district_id,
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            as_of_date=as_of_date
        )
        if 'error' in data:
            return Response(data, status=status.HTTP_403_FORBIDDEN)
        return Response(data)


class PublicHealthIntelligenceSummaryView(BaseIntelligenceView):
    """
    Unified Public Health Intelligence Summary Endpoint (Step 1 Foundation)
    """
    def get(self, request):
        fac_id = request.query_params.get('facility')
        dist_id = request.query_params.get('district')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        as_of_date = request.query_params.get('date')

        scope = resolve_facility_scope(
            user=request.user,
            requested_facility_id=fac_id,
            requested_district_id=dist_id
        )
        if not scope.is_authorized:
            return Response({'error': scope.error}, status=status.HTTP_403_FORBIDDEN)

        data = get_public_health_intelligence_summary(
            facility_id=scope.facility_ids[0] if (fac_id and len(scope.facility_ids) == 1) else None,
            district_id=scope.district_id,
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            as_of_date=as_of_date
        )
        if 'error' in data:
            return Response(data, status=status.HTTP_403_FORBIDDEN)
        return Response(data)


class PublicHealthDemographicsView(BaseIntelligenceView):
    """
    Authoritative Demographic Breakdown Endpoint for Public Health Intelligence.
    Returns age, age group, and gender distributions from real database records.
    """
    def get(self, request):
        fac_id = request.query_params.get('facility')
        dist_id = request.query_params.get('district')
        disease = request.query_params.get('disease')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        as_of_date = request.query_params.get('date')

        scope = resolve_facility_scope(
            user=request.user,
            requested_facility_id=fac_id,
            requested_district_id=dist_id
        )
        if not scope.is_authorized:
            return Response({'error': scope.error}, status=status.HTTP_403_FORBIDDEN)

        data = get_demographic_intelligence(
            facility_ids=scope.facility_ids,
            district_id=scope.district_id,
            disease_name=disease,
            start_date=start_date,
            end_date=end_date,
            as_of_date=as_of_date
        )
        return Response(data)
