"""
DRF Views for Public Health Intelligence & Forecasting Module.
Provides secure, role-scoped endpoints for the 10 intelligence capabilities
and a master unified overview endpoint.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

from apps.accounts.permissions import HasPermission, get_accessible_facility_ids_for_user
from apps.surveillance.intelligence_services import (
    get_disease_trend_analysis,
    get_disease_by_locality_analysis,
    get_historical_disease_analysis,
    detect_emerging_patterns,
    get_locality_risk_analysis,
    forecast_disease_incidence,
    forecast_locality_demand,
    detect_seasonal_patterns,
    estimate_future_health_demand,
    estimate_resource_planning,
    get_public_health_intelligence_overview
)


def _resolve_scope(request):
    """
    Resolves facility_id and district_id from request user and query params.
    Enforces role scoping rules:
    - DISTRICT_OFFICER: Defaults to assigned district. Can inspect specific facility if within district.
    - HOSPITAL_ADMIN, DOCTOR, NURSE: Strictly locked to assigned facility.
    - Superusers: Free access to all facilities and districts.
    """
    user = request.user
    role = getattr(user, 'role', '')
    req_facility = request.query_params.get('facility')
    req_district = request.query_params.get('district')

    facility_id = None
    district_id = None

    if getattr(user, 'is_superuser', False):
        facility_id = int(req_facility) if req_facility and req_facility.isdigit() else None
        district_id = int(req_district) if req_district and req_district.isdigit() else None
    elif role == 'DISTRICT_OFFICER':
        district_id = user.assigned_district_id
        if req_facility and req_facility.isdigit():
            # Check if requested facility is in the district
            from apps.facilities.models import Facility
            fac = Facility.objects.filter(id=int(req_facility), district_id=district_id).first()
            if fac:
                facility_id = fac.id
    else:
        # Operational roles locked to assigned facility
        facility_id = getattr(user, 'assigned_facility_id', None)
        if user.assigned_facility and user.assigned_facility.district_id:
            district_id = user.assigned_facility.district_id

    return facility_id, district_id


class BaseIntelligenceView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasPermission]
    required_permission = 'dashboard.view'


class PublicHealthIntelligenceOverviewView(BaseIntelligenceView):
    """
    Master unified overview of all 10 Public Health Intelligence capabilities.
    """
    def get(self, request):
        fac_id, dist_id = _resolve_scope(request)
        target_date = request.query_params.get('date')

        overview = get_public_health_intelligence_overview(
            district_id=dist_id,
            facility_id=fac_id,
            as_of_date=target_date
        )
        return Response(overview)


class DiseaseTrendsView(BaseIntelligenceView):
    """1. Disease Trend Analysis"""
    def get(self, request):
        fac_id, dist_id = _resolve_scope(request)
        disease = request.query_params.get('disease')
        days = int(request.query_params.get('days', 7))
        baseline_days = int(request.query_params.get('baseline_days', 30))
        target_date = request.query_params.get('date')

        data = get_disease_trend_analysis(
            district_id=dist_id,
            facility_id=fac_id,
            disease_name=disease,
            window_days=days,
            baseline_days=baseline_days,
            as_of_date=target_date
        )
        return Response(data)


class DiseaseByLocalityView(BaseIntelligenceView):
    """2. Disease-by-Locality Analysis"""
    def get(self, request):
        fac_id, dist_id = _resolve_scope(request)
        disease = request.query_params.get('disease')
        days = int(request.query_params.get('days', 14))
        target_date = request.query_params.get('date')

        data = get_disease_by_locality_analysis(
            district_id=dist_id,
            facility_id=fac_id,
            disease_name=disease,
            window_days=days,
            as_of_date=target_date
        )
        return Response(data)


class HistoricalDiseaseView(BaseIntelligenceView):
    """3. Historical Disease Analysis"""
    def get(self, request):
        fac_id, dist_id = _resolve_scope(request)
        disease = request.query_params.get('disease')
        periods = int(request.query_params.get('periods', 6))
        period_unit = request.query_params.get('period_unit', 'week')
        target_date = request.query_params.get('date')

        data = get_historical_disease_analysis(
            disease_name=disease,
            district_id=dist_id,
            facility_id=fac_id,
            periods=periods,
            period_unit=period_unit,
            as_of_date=target_date
        )
        return Response(data)


class EmergingPatternsView(BaseIntelligenceView):
    """4. Emerging Pattern Detection"""
    def get(self, request):
        fac_id, dist_id = _resolve_scope(request)
        target_date = request.query_params.get('date')

        data = detect_emerging_patterns(
            district_id=dist_id,
            facility_id=fac_id,
            as_of_date=target_date
        )
        return Response(data)


class LocalityRiskView(BaseIntelligenceView):
    """5. Locality Risk Analysis"""
    def get(self, request):
        _, dist_id = _resolve_scope(request)
        target_date = request.query_params.get('date')

        data = get_locality_risk_analysis(
            district_id=dist_id,
            as_of_date=target_date
        )
        return Response(data)


class DiseaseForecastView(BaseIntelligenceView):
    """6. Disease Forecasting"""
    def get(self, request):
        fac_id, dist_id = _resolve_scope(request)
        disease = request.query_params.get('disease')
        forecast_days = int(request.query_params.get('forecast_days', 14))
        target_date = request.query_params.get('date')

        data = forecast_disease_incidence(
            disease_name=disease,
            facility_id=fac_id,
            district_id=dist_id,
            forecast_days=forecast_days,
            as_of_date=target_date
        )
        return Response(data)


class LocalityForecastView(BaseIntelligenceView):
    """7. Locality Demand Forecasting"""
    def get(self, request):
        _, dist_id = _resolve_scope(request)
        ward_id = request.query_params.get('ward')
        ward_id = int(ward_id) if ward_id and ward_id.isdigit() else None
        forecast_days = int(request.query_params.get('forecast_days', 14))
        target_date = request.query_params.get('date')

        data = forecast_locality_demand(
            ward_id=ward_id,
            district_id=dist_id,
            forecast_days=forecast_days,
            as_of_date=target_date
        )
        return Response(data)


class SeasonalPatternsView(BaseIntelligenceView):
    """8. Seasonal Pattern Detection"""
    def get(self, request):
        fac_id, dist_id = _resolve_scope(request)
        disease = request.query_params.get('disease')
        target_date = request.query_params.get('date')

        data = detect_seasonal_patterns(
            disease_name=disease,
            facility_id=fac_id,
            district_id=dist_id,
            as_of_date=target_date
        )
        return Response(data)


class FutureHealthDemandView(BaseIntelligenceView):
    """9. Future Health-Demand Estimation"""
    def get(self, request):
        fac_id, dist_id = _resolve_scope(request)
        forecast_days = int(request.query_params.get('forecast_days', 14))
        target_date = request.query_params.get('date')

        data = estimate_future_health_demand(
            facility_id=fac_id,
            district_id=dist_id,
            forecast_days=forecast_days,
            as_of_date=target_date
        )
        return Response(data)


class ResourcePlanningView(BaseIntelligenceView):
    """10. Resource Planning Estimates"""
    def get(self, request):
        fac_id, dist_id = _resolve_scope(request)
        forecast_days = int(request.query_params.get('forecast_days', 14))
        target_date = request.query_params.get('date')

        data = estimate_resource_planning(
            facility_id=fac_id,
            district_id=dist_id,
            forecast_days=forecast_days,
            as_of_date=target_date
        )
        return Response(data)
