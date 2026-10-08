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
from apps.surveillance.demographic_services import (
    validate_demographic_params,
    validate_severity_param,
)
from apps.surveillance.vulnerable_population_services import (
    validate_vulnerable_group_param,
)
from apps.surveillance.patient_type_services import (
    validate_patient_type_param,
)
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

    def get_demographic_filters(self, request):
        age_group = request.query_params.get('age_group')
        gender = request.query_params.get('gender')
        return validate_demographic_params(age_group=age_group, gender=gender)

    def get_severity_filter(self, request):
        severity = request.query_params.get('severity')
        return validate_severity_param(severity=severity)

    def get_vulnerable_group_filter(self, request):
        vulnerable_group = request.query_params.get('vulnerable_group')
        return validate_vulnerable_group_param(vulnerable_group=vulnerable_group)

    def get_patient_type_filter(self, request):
        patient_type = request.query_params.get('patient_type')
        return validate_patient_type_param(patient_type=patient_type)


class PublicHealthDiseaseTrendsView(BaseIntelligenceView):
    """
    1. Disease Trend Analysis Endpoint
    Computes current, previous, 7d, 30d, 90d cases, monthly counts,
    percentage change, and trend direction.
    Supports optional age_group, gender, severity, vulnerable_group, and patient_type filtering.
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

        clean_ag, clean_g, err_demo = self.get_demographic_filters(request)
        if err_demo:
            return Response({'error': err_demo}, status=status.HTTP_400_BAD_REQUEST)

        clean_sev, err_sev = self.get_severity_filter(request)
        if err_sev:
            return Response({'error': err_sev}, status=status.HTTP_400_BAD_REQUEST)

        clean_vg, err_vg = self.get_vulnerable_group_filter(request)
        if err_vg:
            return Response({'error': err_vg}, status=status.HTTP_400_BAD_REQUEST)

        clean_pt, err_pt = self.get_patient_type_filter(request)
        if err_pt:
            return Response({'error': err_pt}, status=status.HTTP_400_BAD_REQUEST)

        data = calculate_disease_trends(
            facility_ids=scope.facility_ids,
            district_id=scope.district_id,
            disease_name=disease,
            start_date=start_date,
            end_date=end_date,
            as_of_date=as_of_date,
            window_days=days,
            age_group=clean_ag,
            gender=clean_g,
            severity=clean_sev,
            vulnerable_group=clean_vg,
            patient_type=clean_pt
        )
        return Response(data)


class PublicHealthDiseaseLocalityView(BaseIntelligenceView):
    """
    2. Disease-by-Locality Aggregation Endpoint
    Computes cases by locality/ward, reporting hospitals, locality share %,
    and trend direction.
    Supports optional age_group, gender, severity, vulnerable_group, and patient_type filtering.
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

        clean_ag, clean_g, err_demo = self.get_demographic_filters(request)
        if err_demo:
            return Response({'error': err_demo}, status=status.HTTP_400_BAD_REQUEST)

        clean_sev, err_sev = self.get_severity_filter(request)
        if err_sev:
            return Response({'error': err_sev}, status=status.HTTP_400_BAD_REQUEST)

        clean_vg, err_vg = self.get_vulnerable_group_filter(request)
        if err_vg:
            return Response({'error': err_vg}, status=status.HTTP_400_BAD_REQUEST)

        clean_pt, err_pt = self.get_patient_type_filter(request)
        if err_pt:
            return Response({'error': err_pt}, status=status.HTTP_400_BAD_REQUEST)

        data = aggregate_disease_by_locality(
            facility_ids=scope.facility_ids,
            district_id=scope.district_id,
            disease_name=disease,
            start_date=start_date,
            end_date=end_date,
            as_of_date=as_of_date,
            window_days=days,
            age_group=clean_ag,
            gender=clean_g,
            severity=clean_sev,
            vulnerable_group=clean_vg,
            patient_type=clean_pt
        )
        return Response(data)


class PublicHealthHistoricalDiseaseView(BaseIntelligenceView):
    """
    3. Historical Disease Aggregation Endpoint
    Multi-month sequential series with severity breakdowns.
    Supports optional age_group, gender, severity, vulnerable_group, and patient_type filtering.
    """
    def get(self, request):
        fac_id = request.query_params.get('facility')
        dist_id = request.query_params.get('district')
        disease = request.query_params.get('disease')
        as_of_date = request.query_params.get('date')

        scope = resolve_facility_scope(
            user=request.user,
            requested_facility_id=fac_id,
            requested_district_id=dist_id
        )
        if not scope.is_authorized:
            return Response({'error': scope.error}, status=status.HTTP_403_FORBIDDEN)

        months_param = request.query_params.get('months')
        months = 6
        if months_param is not None and str(months_param).strip() != '':
            try:
                months = int(months_param)
                if months <= 0 or months > 60:
                    return Response({'error': 'Invalid months parameter. Must be an integer between 1 and 60.'}, status=status.HTTP_400_BAD_REQUEST)
            except (ValueError, TypeError):
                return Response({'error': 'Invalid months parameter. Must be a valid positive integer.'}, status=status.HTTP_400_BAD_REQUEST)

        clean_ag, clean_g, err_demo = self.get_demographic_filters(request)
        if err_demo:
            return Response({'error': err_demo}, status=status.HTTP_400_BAD_REQUEST)

        clean_sev, err_sev = self.get_severity_filter(request)
        if err_sev:
            return Response({'error': err_sev}, status=status.HTTP_400_BAD_REQUEST)

        clean_vg, err_vg = self.get_vulnerable_group_filter(request)
        if err_vg:
            return Response({'error': err_vg}, status=status.HTTP_400_BAD_REQUEST)

        clean_pt, err_pt = self.get_patient_type_filter(request)
        if err_pt:
            return Response({'error': err_pt}, status=status.HTTP_400_BAD_REQUEST)

        data = aggregate_historical_disease(
            facility_ids=scope.facility_ids,
            district_id=scope.district_id,
            disease_name=disease,
            months=months,
            as_of_date=as_of_date,
            age_group=clean_ag,
            gender=clean_g,
            severity=clean_sev,
            vulnerable_group=clean_vg,
            patient_type=clean_pt
        )
        return Response(data)


class PublicHealthHospitalAggregationView(BaseIntelligenceView):
    """
    4. Hospital-Level Aggregation Endpoint
    Strictly locked to assigned hospital for Hospital Admin / Doctor.
    Supports optional age_group, gender, severity, vulnerable_group, and patient_type filtering.
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

        clean_ag, clean_g, err_demo = self.get_demographic_filters(request)
        if err_demo:
            return Response({'error': err_demo}, status=status.HTTP_400_BAD_REQUEST)

        clean_sev, err_sev = self.get_severity_filter(request)
        if err_sev:
            return Response({'error': err_sev}, status=status.HTTP_400_BAD_REQUEST)

        clean_vg, err_vg = self.get_vulnerable_group_filter(request)
        if err_vg:
            return Response({'error': err_vg}, status=status.HTTP_400_BAD_REQUEST)

        clean_pt, err_pt = self.get_patient_type_filter(request)
        if err_pt:
            return Response({'error': err_pt}, status=status.HTTP_400_BAD_REQUEST)

        data = aggregate_hospital_level(
            facility_id=scope.facility_ids[0],
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            as_of_date=as_of_date,
            age_group=clean_ag,
            gender=clean_g,
            severity=clean_sev,
            vulnerable_group=clean_vg,
            patient_type=clean_pt
        )
        if 'error' in data:
            return Response(data, status=status.HTTP_403_FORBIDDEN)
        return Response(data)


class PublicHealthDistrictAggregationView(BaseIntelligenceView):
    """
    5. District-Level Aggregation Endpoint
    Scoped to assigned district with strict cross-district isolation.
    Supports optional age_group, gender, severity, vulnerable_group, and patient_type filtering.
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

        clean_ag, clean_g, err_demo = self.get_demographic_filters(request)
        if err_demo:
            return Response({'error': err_demo}, status=status.HTTP_400_BAD_REQUEST)

        clean_sev, err_sev = self.get_severity_filter(request)
        if err_sev:
            return Response({'error': err_sev}, status=status.HTTP_400_BAD_REQUEST)

        clean_vg, err_vg = self.get_vulnerable_group_filter(request)
        if err_vg:
            return Response({'error': err_vg}, status=status.HTTP_400_BAD_REQUEST)

        clean_pt, err_pt = self.get_patient_type_filter(request)
        if err_pt:
            return Response({'error': err_pt}, status=status.HTTP_400_BAD_REQUEST)

        data = aggregate_district_level(
            district_id=scope.district_id,
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            as_of_date=as_of_date,
            age_group=clean_ag,
            gender=clean_g,
            severity=clean_sev,
            vulnerable_group=clean_vg,
            patient_type=clean_pt
        )
        if 'error' in data:
            return Response(data, status=status.HTTP_403_FORBIDDEN)
        return Response(data)


class PublicHealthIntelligenceSummaryView(BaseIntelligenceView):
    """
    Unified Public Health Intelligence Summary Endpoint (Step 1 Foundation)
    Supports optional age_group, gender, severity, vulnerable_group, and patient_type filtering.
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

        clean_ag, clean_g, err_demo = self.get_demographic_filters(request)
        if err_demo:
            return Response({'error': err_demo}, status=status.HTTP_400_BAD_REQUEST)

        clean_sev, err_sev = self.get_severity_filter(request)
        if err_sev:
            return Response({'error': err_sev}, status=status.HTTP_400_BAD_REQUEST)

        clean_vg, err_vg = self.get_vulnerable_group_filter(request)
        if err_vg:
            return Response({'error': err_vg}, status=status.HTTP_400_BAD_REQUEST)

        clean_pt, err_pt = self.get_patient_type_filter(request)
        if err_pt:
            return Response({'error': err_pt}, status=status.HTTP_400_BAD_REQUEST)

        data = get_public_health_intelligence_summary(
            facility_id=scope.facility_ids[0] if (fac_id and len(scope.facility_ids) == 1) else None,
            district_id=scope.district_id,
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            as_of_date=as_of_date,
            age_group=clean_ag,
            gender=clean_g,
            severity=clean_sev,
            vulnerable_group=clean_vg,
            patient_type=clean_pt
        )
        if 'error' in data:
            return Response(data, status=status.HTTP_403_FORBIDDEN)
        return Response(data)


class PublicHealthDemographicsView(BaseIntelligenceView):
    """
    Authoritative Demographic Breakdown Endpoint for Public Health Intelligence.
    Returns age, age group, and gender distributions from real database records.
    Supports optional age_group, gender, severity, vulnerable_group, and patient_type filtering.
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

        clean_ag, clean_g, err_demo = self.get_demographic_filters(request)
        if err_demo:
            return Response({'error': err_demo}, status=status.HTTP_400_BAD_REQUEST)

        clean_sev, err_sev = self.get_severity_filter(request)
        if err_sev:
            return Response({'error': err_sev}, status=status.HTTP_400_BAD_REQUEST)

        clean_vg, err_vg = self.get_vulnerable_group_filter(request)
        if err_vg:
            return Response({'error': err_vg}, status=status.HTTP_400_BAD_REQUEST)

        clean_pt, err_pt = self.get_patient_type_filter(request)
        if err_pt:
            return Response({'error': err_pt}, status=status.HTTP_400_BAD_REQUEST)

        data = get_demographic_intelligence(
            facility_ids=scope.facility_ids,
            district_id=scope.district_id,
            disease_name=disease,
            start_date=start_date,
            end_date=end_date,
            as_of_date=as_of_date,
            age_group=clean_ag,
            gender=clean_g,
            severity=clean_sev,
            vulnerable_group=clean_vg,
            patient_type=clean_pt
        )
        return Response(data)

