"""
DRF Views for Public Health Intelligence Forecasting & Seasonal Analysis - STEP 2 Module
Provides secure, role-scoped endpoints for:
1. Disease forecasting and weekly trends (/api/surveillance/intelligence/forecast/)
2. Seasonal pattern analysis (/api/surveillance/intelligence/seasonality/)
"""

import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

from apps.accounts.permissions import HasPermission
from apps.surveillance.demographic_services import validate_demographic_params
from apps.surveillance.intelligence_services import resolve_facility_scope
from apps.surveillance.intelligence_forecast_services import (
    generate_forecast_summary,
    calculate_seasonal_pattern
)


class BaseForecastView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasPermission]
    required_permission = 'dashboard.view'

    def parse_and_validate_params(self, request):
        """
        Parses and strictly validates query parameters.
        Returns (validated_dict, error_response).
        """
        fac_id = request.query_params.get('facility')
        dist_id = request.query_params.get('district')
        disease = request.query_params.get('disease')
        date_str = request.query_params.get('date')
        weeks_str = request.query_params.get('weeks')
        months_str = request.query_params.get('months')

        # Validate numeric weeks parameter if present
        horizon_weeks = 4
        if weeks_str is not None and str(weeks_str).strip() != '':
            try:
                horizon_weeks = int(weeks_str)
                if horizon_weeks <= 0 or horizon_weeks > 52:
                    return None, Response(
                        {'error': 'Invalid weeks parameter. Must be an integer between 1 and 52.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except (ValueError, TypeError):
                return None, Response(
                    {'error': 'Invalid weeks parameter. Must be a valid positive integer.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Validate numeric months parameter if present
        months_count = 12
        if months_str is not None and str(months_str).strip() != '':
            try:
                months_count = int(months_str)
                if months_count <= 0 or months_count > 60:
                    return None, Response(
                        {'error': 'Invalid months parameter. Must be an integer between 1 and 60.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except (ValueError, TypeError):
                return None, Response(
                    {'error': 'Invalid months parameter. Must be a valid positive integer.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Validate date format if present
        as_of_date = None
        if date_str is not None and str(date_str).strip() != '':
            try:
                as_of_date = datetime.datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
            except ValueError:
                return None, Response(
                    {'error': 'Invalid date parameter. Format must be YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Validate demographic parameters
        age_group = request.query_params.get('age_group')
        gender = request.query_params.get('gender')
        clean_ag, clean_g, err_demo = validate_demographic_params(age_group=age_group, gender=gender)
        if err_demo:
            return None, Response({'error': err_demo}, status=status.HTTP_400_BAD_REQUEST)

        return {
            'facility': fac_id,
            'district': dist_id,
            'disease': disease,
            'as_of_date': as_of_date,
            'horizon_weeks': horizon_weeks,
            'months_count': months_count,
            'age_group': clean_ag,
            'gender': clean_g,
        }, None


class PublicHealthForecastView(BaseForecastView):
    """
    1. Disease Forecasting Endpoint
    Returns continuous weekly time series, Step 1 trend indicator,
    and Weighted Moving Average forecast with confidence bounds.
    Supports optional age_group and gender demographic filtering.
    """
    def get(self, request):
        fac_id = request.query_params.get('facility')
        dist_id = request.query_params.get('district')

        # Strict authorization scope check
        scope = resolve_facility_scope(
            user=request.user,
            requested_facility_id=fac_id,
            requested_district_id=dist_id
        )
        if not scope.is_authorized:
            return Response({'error': scope.error}, status=status.HTTP_403_FORBIDDEN)

        params, err_resp = self.parse_and_validate_params(request)
        if err_resp:
            return err_resp

        # Historical weeks = approximately 4.3 weeks per month
        historical_weeks = max(4, int(params['months_count'] * 4.33))

        data = generate_forecast_summary(
            facility_id=params['facility'],
            district_id=params['district'],
            disease_name=params['disease'],
            as_of_date=params['as_of_date'],
            historical_weeks=historical_weeks,
            horizon_weeks=params['horizon_weeks'],
            months_count=params['months_count'],
            user=request.user,
            age_group=params['age_group'],
            gender=params['gender']
        )

        if not data.get('is_authorized', True):
            return Response({'error': data.get('error')}, status=status.HTTP_403_FORBIDDEN)

        return Response(data)


class PublicHealthSeasonalityView(BaseForecastView):
    """
    2. Seasonal Pattern Analysis Endpoint
    Returns monthly case distribution, highest/lowest case months,
    strongest historical periods, and seasonal strength index.
    Supports optional age_group and gender demographic filtering.
    """
    def get(self, request):
        fac_id = request.query_params.get('facility')
        dist_id = request.query_params.get('district')

        # Strict authorization scope check
        scope = resolve_facility_scope(
            user=request.user,
            requested_facility_id=fac_id,
            requested_district_id=dist_id
        )
        if not scope.is_authorized:
            return Response({'error': scope.error}, status=status.HTTP_403_FORBIDDEN)

        params, err_resp = self.parse_and_validate_params(request)
        if err_resp:
            return err_resp

        data = calculate_seasonal_pattern(
            facility_ids=scope.facility_ids,
            district_id=scope.district_id,
            disease_name=params['disease'],
            as_of_date=params['as_of_date'],
            months_count=params['months_count'],
            age_group=params['age_group'],
            gender=params['gender']
        )

        return Response(data)

