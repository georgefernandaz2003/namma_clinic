/**
 * Type definitions for Public Health Intelligence & Forecasting Module
 * Strictly matches Step 1 and Step 2 backend API contract.
 */

export type TrendDirection =
  | 'NORMAL'
  | 'INCREASING'
  | 'DECREASING'
  | 'POSSIBLE_INCREASE'
  | 'INSUFFICIENT_DATA';

export type ForecastStatus = 'AVAILABLE' | 'INSUFFICIENT_DATA';
export type SeasonalStatus = 'DETECTED' | 'WEAK' | 'NOT_ENOUGH_DATA';

export type PatientTypeFilter = 'NEW' | 'FOLLOW_UP';

export interface IntelligenceFilterParams {
  facility?: number | string;
  district?: number | string;
  disease?: string;
  date?: string; // YYYY-MM-DD
  days?: number;
  weeks?: number;
  months?: number;
  age_group?: string;
  gender?: string;
  severity?: string;
  vulnerable_group?: string;
  patient_type?: PatientTypeFilter | string;
}

export interface SummaryKPIs {
  total_current_cases: number;
  total_previous_cases: number;
  total_7d_cases: number;
  total_30d_cases: number;
  total_90d_cases: number;
  percentage_change: number | null;
  overall_trend_direction: TrendDirection;
  diseases_monitored_count: number;
  observation_period: {
    start_date: string;
    end_date: string;
    duration_days: number;
  };
}

export interface DiseaseTrendItem {
  disease: string;
  current_cases: number;
  previous_period_cases: number;
  cases_7d: number;
  cases_30d: number;
  cases_90d: number;
  percentage_change: number | null;
  trend_direction: TrendDirection;
  explanation: string;
  monthly_history?: Array<{
    period_label: string;
    year: number;
    month: number;
    cases: number;
  }>;
}

export interface DiseaseTrendsResponse {
  summary: SummaryKPIs;
  disease_trends: DiseaseTrendItem[];
}

export interface ReportingHospital {
  hospital_id: number;
  hospital_name: string;
  hospital_code: string;
  cases_reported: number;
}

export interface LocalityAggregationItem {
  locality: {
    ward_id: number | null;
    ward_number: number | null;
    name: string;
    zone: string | null;
    population: number | null;
    slum_population: number | null;
  };
  disease: string;
  current_cases: number;
  previous_period_cases: number;
  percentage_change: number | null;
  locality_share_pct: number;
  trend_direction: TrendDirection;
  reporting_hospitals_count: number;
  reporting_hospitals: ReportingHospital[];
  explanation: string;
  observation_period: {
    start_date: string;
    end_date: string;
    duration_days: number;
  };
}

export interface DiseaseLocalityResponse {
  total_cases_in_period: number;
  localities_count: number;
  locality_aggregations: LocalityAggregationItem[];
}

export interface HistoricalSeriesPoint {
  period_label: string;
  year: number;
  month: number;
  total_cases: number;
  severity_breakdown: {
    MILD: number;
    MODERATE: number;
    SEVERE: number;
  };
}

export interface HistoricalDiseaseResponse {
  disease: string;
  months_analyzed: number;
  total_cases_in_history: number;
  monthly_average: number;
  current_month_cases: number;
  previous_month_cases: number;
  percentage_change: number | null;
  trend_direction: TrendDirection;
  explanation: string;
  historical_series: HistoricalSeriesPoint[];
}

export interface ForecastPoint {
  forecast_week_start: string;
  forecast_week_end: string;
  predicted_cases: number;
  lower_bound: number;
  upper_bound: number;
}

export interface ForecastData {
  status: ForecastStatus;
  horizon_weeks: number;
  method: string;
  historical_window_weeks?: number;
  points: ForecastPoint[];
  explanation: string;
}

export type ForecastRiskLevel = 'NORMAL' | 'ELEVATED' | 'HIGH_RISK' | 'INSUFFICIENT_DATA';
export type ForecastRiskStatus = 'AVAILABLE' | 'INSUFFICIENT_DATA';

export interface ForecastRiskPoint {
  forecast_week?: number;
  forecast_week_start: string;
  forecast_week_end: string;
  predicted_cases: number;
  historical_baseline: number;
  ratio_to_baseline: number | null;
  risk_level: 'NORMAL' | 'ELEVATED' | 'HIGH_RISK';
  explanation: string;
}

export interface ForecastRiskData {
  status: ForecastRiskStatus;
  historical_baseline: number | null;
  elevation_ratio_threshold: number;
  high_risk_ratio_threshold: number;
  risk_points: ForecastRiskPoint[];
  highest_risk_level: ForecastRiskLevel;
  risk_points_count: number;
  high_risk_points_count: number;
  elevated_points_count: number;
  normal_points_count: number;
  explanation: string;
}

export interface MonthlyPatternItem {
  month_number: number;
  month_name: string;
  total_cases: number;
  occurrences: number;
  average_cases: number;
}

export interface StrongestPeriodItem {
  period: string;
  average_cases: number;
  total_cases: number;
}

export interface SeasonalSubgroupItem {
  monthly_patterns: MonthlyPatternItem[];
  total_cases: number;
  peak_month: MonthlyPatternItem | null;
  seasonal_strength: number;
  seasonal_status: SeasonalStatus;
}

export interface SeasonalAgeGroupItem extends SeasonalSubgroupItem {
  age_group: string;
}

export interface SeasonalGenderItem extends SeasonalSubgroupItem {
  gender: string;
}

export interface SeasonalSeverityItem extends SeasonalSubgroupItem {
  severity: string;
}

export interface SeasonalVulnerableGroupItem extends SeasonalSubgroupItem {
  vulnerable_group: string;
}

export interface SeasonalPatientTypeItem extends SeasonalSubgroupItem {
  patient_type: string;
}

export interface SeasonalMatrixCell {
  monthly_patterns: MonthlyPatternItem[];
  total_cases: number;
}

export interface SeasonalityData {
  disease: string;
  seasonal_status: SeasonalStatus;
  seasonal_strength: number;
  total_cases_analyzed: number;
  months_analyzed: number;
  highest_case_month: MonthlyPatternItem | null;
  lowest_case_month: MonthlyPatternItem | null;
  strongest_historical_periods: StrongestPeriodItem[];
  monthly_patterns: MonthlyPatternItem[];
  explanation: string;
  seasonal_age_groups?: SeasonalAgeGroupItem[];
  seasonal_gender?: SeasonalGenderItem[];
  seasonal_severity?: SeasonalSeverityItem[];
  seasonal_vulnerable_groups?: SeasonalVulnerableGroupItem[];
  seasonal_patient_types?: SeasonalPatientTypeItem[];
  seasonal_age_gender?: Record<string, Record<string, SeasonalMatrixCell>>;
  seasonal_age_gender_severity?: Record<string, Record<string, Record<string, SeasonalMatrixCell>>>;
  seasonal_age_gender_vulnerability?: Record<string, Record<string, Record<string, SeasonalMatrixCell>>>;
  seasonal_age_gender_patient_type?: Record<string, Record<string, Record<string, SeasonalMatrixCell>>>;
}

export interface WeeklyTimeSeriesPoint {
  week_number: number;
  week_start: string;
  week_end: string;
  cases: number;
}

export interface ForecastSummaryResponse {
  is_authorized: boolean;
  disease: string;
  scope: {
    facility_ids: number[];
    district_id: number | null;
  };
  observation_period: {
    start_date: string | null;
    end_date: string | null;
    weeks_count: number;
    total_cases: number;
  };
  historical_series: WeeklyTimeSeriesPoint[];
  trend: {
    direction: TrendDirection;
    percentage_change: number | null;
    current_week_cases: number;
    previous_week_cases: number;
    explanation: string;
  };
  forecast: ForecastData;
  forecast_risk?: ForecastRiskData;
  seasonality: SeasonalityData;
  explanation: string;
}

export interface HospitalComparisonItem {
  hospital_id: number;
  hospital_name: string;
  hospital_code: string;
  facility_type: string;
  cases_reported: number;
}

export interface DistrictAggregationResponse {
  district: {
    id: number;
    name: string;
    code: string;
    state: string | null;
    total_facilities: number;
  };
  summary: SummaryKPIs;
  diseases: DiseaseTrendItem[];
  localities: LocalityAggregationItem[];
  hospital_comparison: HospitalComparisonItem[];
}

// ---------------------------------------------------------------------------
// Step 4: Public Health Intelligence Alerts & Action Layer
// ---------------------------------------------------------------------------
export type IntelligenceAlertType =
  | 'INTELLIGENCE_TREND'
  | 'INTELLIGENCE_LOCALITY'
  | 'INTELLIGENCE_FORECAST'
  | 'INTELLIGENCE_SEASONALITY';

export type AlertSeverity = 'INFO' | 'LOW' | 'MEDIUM' | 'WARNING' | 'HIGH' | 'CRITICAL';
export type AlertStatus = 'NEW' | 'ACKNOWLEDGED' | 'RESOLVED';

export interface IntelligenceAlertEvidence {
  [key: string]: any;
  signal_type?: string;
  disease?: string;
  facility_id?: number;
  facility_name?: string;
  district_id?: number | null;
  district_name?: string | null;
  locality?: string;
  locality_id?: number | null;
  observation_date?: string;
  current_cases?: number;
  previous_cases?: number;
  percentage_change?: number | null;
  trend_direction?: string;
  locality_share?: number;
  threshold_used?: number;
  reporting_hospitals?: string[];
  observation_period?: Record<string, any>;
  forecast_horizon?: string;
  predicted_cases?: number;
  lower_bound?: number;
  upper_bound?: number;
  historical_baseline?: number;
  forecast_method?: string;
  seasonal_status?: string;
  seasonal_strength?: number;
  highest_case_month?: string;
  current_month?: number;
  explanation?: string;
}

export interface IntelligenceAlert {
  id: number;
  alert_type: IntelligenceAlertType | string;
  severity: AlertSeverity;
  facility: number;
  facility_name?: string;
  district?: number | null;
  district_name?: string;
  title: string;
  description: string;
  status: AlertStatus;
  fingerprint?: string;
  metadata?: IntelligenceAlertEvidence;
  created_at: string;
  acknowledged_at?: string | null;
  acknowledged_by?: number | null;
  acknowledged_by_username?: string;
  resolved_at?: string | null;
  resolved_by?: number | null;
  resolved_by_username?: string;
  resolution_notes?: string;
}

export interface EvaluateAlertsResponse {
  status: string;
  as_of_date: string;
  facilities_evaluated: number;
  total_alerts: number;
  created_count: number;
  updated_count: number;
  alerts: IntelligenceAlert[];
}
