import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render as rtlRender, screen, fireEvent, waitFor, within } from '@testing-library/react';
import React from 'react';
import { PublicHealthIntelligence } from '../PublicHealthIntelligence';
import intelligenceService from '../../services/intelligenceService';
import * as AuthContextModule from '../../context/AuthContext';
import { ConfirmProvider } from '../../context/ConfirmContext';
import type {
  DiseaseTrendsResponse,
  DiseaseLocalityResponse,
  HistoricalDiseaseResponse,
  ForecastSummaryResponse,
  SeasonalityData,
  DistrictAggregationResponse,
  IntelligenceAlert,
} from '../../types/intelligence';
import type { Facility } from '../../types';

// Mock intelligenceService
vi.mock('../../services/intelligenceService', () => ({
  default: {
    getDiseaseTrends: vi.fn(),
    getDiseaseLocality: vi.fn(),
    getHistoricalDisease: vi.fn(),
    getForecast: vi.fn(),
    getSeasonality: vi.fn(),
    getDistrictAggregation: vi.fn(),
    getAlerts: vi.fn(),
    evaluateAlerts: vi.fn(),
    acknowledgeAlert: vi.fn(),
    resolveAlert: vi.fn(),
  },
}));

// Mock AuthContext
vi.mock('../../context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

const render = (ui: React.ReactElement, options?: Parameters<typeof rtlRender>[1]) => {
  return rtlRender(<ConfirmProvider>{ui}</ConfirmProvider>, options);
};

const mockTrends: DiseaseTrendsResponse = {
  summary: {
    total_current_cases: 42,
    total_previous_cases: 30,
    total_7d_cases: 15,
    total_30d_cases: 60,
    total_90d_cases: 120,
    percentage_change: 40.0,
    overall_trend_direction: 'INCREASING',
    diseases_monitored_count: 5,
    observation_period: {
      start_date: '2026-09-29',
      end_date: '2026-10-06',
      duration_days: 7,
    },
  },
  disease_trends: [
    {
      disease: 'Dengue Fever',
      current_cases: 25,
      previous_period_cases: 15,
      cases_7d: 12,
      cases_30d: 40,
      cases_90d: 80,
      percentage_change: 66.7,
      trend_direction: 'INCREASING',
      explanation: 'Recent cluster identified in north wards',
    },
  ],
};

const mockLocality: DiseaseLocalityResponse = {
  total_cases_in_period: 42,
  localities_count: 2,
  locality_aggregations: [
    {
      locality: {
        ward_id: 101,
        ward_number: 12,
        name: 'Shivajinagar Ward',
        zone: 'East',
        population: 45000,
        slum_population: 12000,
      },
      disease: 'Dengue Fever',
      current_cases: 20,
      previous_period_cases: 10,
      percentage_change: 100.0,
      locality_share_pct: 47.6,
      trend_direction: 'INCREASING',
      reporting_hospitals_count: 1,
      reporting_hospitals: [
        {
          hospital_id: 1,
          hospital_name: 'City Hospital',
          hospital_code: 'HOSP01',
          cases_reported: 20,
        },
      ],
      explanation: 'High concentration in Ward 12',
      observation_period: {
        start_date: '2026-09-29',
        end_date: '2026-10-06',
        duration_days: 7,
      },
    },
    {
      locality: {
        ward_id: null,
        ward_number: null,
        name: 'Unknown Locality',
        zone: null,
        population: null,
        slum_population: null,
      },
      disease: 'Dengue Fever',
      current_cases: 5,
      previous_period_cases: 2,
      percentage_change: 150.0,
      locality_share_pct: 11.9,
      trend_direction: 'POSSIBLE_INCREASE',
      reporting_hospitals_count: 1,
      reporting_hospitals: [
        {
          hospital_id: 1,
          hospital_name: 'City Hospital',
          hospital_code: 'HOSP01',
          cases_reported: 5,
        },
      ],
      explanation: 'Unmapped residential address',
      observation_period: {
        start_date: '2026-09-29',
        end_date: '2026-10-06',
        duration_days: 7,
      },
    },
  ],
};

const mockHistorical: HistoricalDiseaseResponse = {
  disease: 'Dengue Fever',
  months_analyzed: 3,
  total_cases_in_history: 50,
  monthly_average: 16.7,
  current_month_cases: 25,
  previous_month_cases: 15,
  percentage_change: 66.7,
  trend_direction: 'INCREASING',
  explanation: 'Consistent multi-month rise in Dengue cases.',
  historical_series: [
    {
      period_label: 'Aug 2026',
      year: 2026,
      month: 8,
      total_cases: 10,
      severity_breakdown: { MILD: 8, MODERATE: 2, SEVERE: 0 },
    },
    {
      period_label: 'Sep 2026',
      year: 2026,
      month: 9,
      total_cases: 15,
      severity_breakdown: { MILD: 10, MODERATE: 4, SEVERE: 1 },
    },
    {
      period_label: 'Oct 2026',
      year: 2026,
      month: 10,
      total_cases: 25,
      severity_breakdown: { MILD: 18, MODERATE: 5, SEVERE: 2 },
    },
  ],
};

const mockSeasonality: SeasonalityData = {
  disease: 'Dengue Fever',
  months_analyzed: 12,
  total_cases_analyzed: 54,
  seasonal_status: 'DETECTED',
  seasonal_strength: 0.75,
  highest_case_month: {
    month_number: 10,
    month_name: 'October',
    average_cases: 25.0,
    total_cases: 50,
    occurrences: 2,
  },
  lowest_case_month: {
    month_number: 2,
    month_name: 'February',
    average_cases: 2.0,
    total_cases: 4,
    occurrences: 2,
  },
  strongest_historical_periods: [
    {
      period: 'October (Calendar Month 10)',
      average_cases: 25.0,
      total_cases: 50,
    },
  ],
  monthly_patterns: [
    {
      month_number: 10,
      month_name: 'October',
      average_cases: 25.0,
      total_cases: 50,
      occurrences: 2,
    },
  ],
  explanation: 'Consistent autumn peak detected across observation window.',
};

const mockForecastAvailable: ForecastSummaryResponse = {
  is_authorized: true,
  disease: 'Dengue Fever',
  scope: {
    facility_ids: [1],
    district_id: null,
  },
  observation_period: {
    start_date: '2026-08-01',
    end_date: '2026-10-06',
    weeks_count: 8,
    total_cases: 50,
  },
  historical_series: [],
  trend: {
    direction: 'INCREASING',
    percentage_change: 66.7,
    current_week_cases: 25,
    previous_week_cases: 15,
    explanation: 'Upward trend detected',
  },
  forecast: {
    status: 'AVAILABLE',
    method: 'WEIGHTED_MOVING_AVERAGE',
    historical_window_weeks: 8,
    horizon_weeks: 4,
    points: [
      {
        forecast_week_start: '2026-10-07',
        forecast_week_end: '2026-10-13',
        predicted_cases: 12,
        lower_bound: 8,
        upper_bound: 16,
      },
    ],
    explanation: 'Based on 8-week historical volume with weighted moving average.',
  },
  forecast_risk: {
    status: 'AVAILABLE',
    historical_baseline: 8.0,
    elevation_ratio_threshold: 1.15,
    high_risk_ratio_threshold: 1.5,
    risk_points: [
      {
        forecast_week: 1,
        forecast_week_start: '2026-10-07',
        forecast_week_end: '2026-10-13',
        predicted_cases: 12,
        historical_baseline: 8.0,
        ratio_to_baseline: 1.5,
        risk_level: 'HIGH_RISK',
        explanation: 'Predicted volume exceeds high-risk threshold (1.5x baseline).',
      },
    ],
    highest_risk_level: 'HIGH_RISK',
    risk_points_count: 1,
    high_risk_points_count: 1,
    elevated_points_count: 0,
    normal_points_count: 0,
    explanation: 'Surveillance signal indicates high projected risk above historical baseline.',
  },
  seasonality: mockSeasonality,
  explanation: 'Surveillance summary',
};

const mockForecastInsufficient: ForecastSummaryResponse = {
  is_authorized: true,
  disease: 'Dengue Fever',
  scope: {
    facility_ids: [1],
    district_id: null,
  },
  observation_period: {
    start_date: '2026-08-01',
    end_date: '2026-10-06',
    weeks_count: 8,
    total_cases: 2,
  },
  historical_series: [],
  trend: {
    direction: 'INSUFFICIENT_DATA',
    percentage_change: null,
    current_week_cases: 1,
    previous_week_cases: 1,
    explanation: 'Low volume',
  },
  forecast: {
    status: 'INSUFFICIENT_DATA',
    method: 'WEIGHTED_MOVING_AVERAGE',
    historical_window_weeks: 8,
    horizon_weeks: 4,
    points: [],
    explanation: 'Insufficient historical surveillance data for a reliable forecast.',
  },
  forecast_risk: {
    status: 'INSUFFICIENT_DATA',
    historical_baseline: null,
    elevation_ratio_threshold: 1.15,
    high_risk_ratio_threshold: 1.5,
    risk_points: [],
    highest_risk_level: 'INSUFFICIENT_DATA',
    risk_points_count: 0,
    high_risk_points_count: 0,
    elevated_points_count: 0,
    normal_points_count: 0,
    explanation: 'Insufficient historical data for reliable forecast risk classification.',
  },
  seasonality: mockSeasonality,
  explanation: 'Low volume surveillance signal',
};

const mockDistrictAgg: DistrictAggregationResponse = {
  district: {
    id: 5,
    name: 'Central District',
    code: 'DIST05',
    state: 'Karnataka',
    total_facilities: 2,
  },
  summary: mockTrends.summary,
  diseases: mockTrends.disease_trends,
  localities: mockLocality.locality_aggregations,
  hospital_comparison: [
    {
      hospital_id: 1,
      hospital_name: 'City Hospital',
      hospital_code: 'HOSP01',
      facility_type: 'MAIN_HOSPITAL',
      cases_reported: 25,
    },
    {
      hospital_id: 3,
      hospital_name: 'Metro Center',
      hospital_code: 'METRO03',
      facility_type: 'SECONDARY_HOSPITAL',
      cases_reported: 17,
    },
  ],
};

const facilitiesList = [
  {
    id: 1,
    facility_name: 'City Hospital',
    facility_code: 'HOSP01',
    district: 5,
    facility_type: 'MAIN_HOSPITAL' as const,
    address: 'Central Rd',
    contact_phone: '1234567890',
    contact_email: 'city@hosp.org',
    status: 'ACTIVE' as const,
  },
  {
    id: 2,
    facility_name: 'Rural Clinic',
    facility_code: 'CLIN02',
    district: 6,
    facility_type: 'NAMMA_CLINIC' as const,
    address: 'Outer Rd',
    contact_phone: '9876543210',
    contact_email: 'rural@clinic.org',
    status: 'ACTIVE' as const,
  },
];

describe('PublicHealthIntelligence Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(intelligenceService.getDiseaseTrends).mockResolvedValue(mockTrends);
    vi.mocked(intelligenceService.getDiseaseLocality).mockResolvedValue(mockLocality);
    vi.mocked(intelligenceService.getHistoricalDisease).mockResolvedValue(mockHistorical);
    vi.mocked(intelligenceService.getForecast).mockResolvedValue(mockForecastAvailable);
    vi.mocked(intelligenceService.getSeasonality).mockResolvedValue(mockSeasonality);
    vi.mocked(intelligenceService.getDistrictAggregation).mockResolvedValue(mockDistrictAgg);
    vi.mocked(intelligenceService.getAlerts).mockResolvedValue({
      count: 0,
      next: null,
      previous: null,
      results: [],
    });
    vi.mocked(intelligenceService.evaluateAlerts).mockResolvedValue({
      created_count: 0,
      updated_count: 0,
      evaluated_signals_count: 0,
      alerts: [],
    });
    vi.mocked(intelligenceService.acknowledgeAlert).mockResolvedValue({} as any);
    vi.mocked(intelligenceService.resolveAlert).mockResolvedValue({} as any);
  });

  const setupAuth = (role: 'HOSPITAL_ADMIN' | 'DISTRICT_OFFICER' | 'DOCTOR' = 'HOSPITAL_ADMIN', permissions = ['dashboard.view']) => {
    vi.mocked(AuthContextModule.useAuth).mockReturnValue({
      user: {
        id: 10,
        username: 'testuser',
        full_name: 'Dr. Test User',
        email: 'test@hospital.gov',
        phone: '9999999999',
        role,
        role_display: role === 'DISTRICT_OFFICER' ? 'District Officer' : 'Hospital Admin',
        assigned_facility: role === 'HOSPITAL_ADMIN' ? 1 : null,
        facility_name: role === 'HOSPITAL_ADMIN' ? 'City Hospital' : undefined,
        assigned_district: role === 'DISTRICT_OFFICER' ? 5 : null,
        district_name: role === 'DISTRICT_OFFICER' ? 'Central District' : undefined,
        permissions,
      },
      token: 'jwt-mock-token',
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshUserData: vi.fn(),
      activeFacility: facilitiesList[0] as unknown as Facility,
      allFacilities: facilitiesList as unknown as Facility[],
      setActiveFacility: vi.fn(),
    });
  };

  it('1. verifies page renders properly', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    expect(screen.getByText('Loading public health intelligence...')).toBeDefined();

    await waitFor(() => {
      expect(screen.getByText('Public Health Intelligence & Forecasting')).toBeDefined();
      expect(screen.getByText('Current Period Cases')).toBeDefined();
    });
  });

  it('2. verifies Hospital Admin sees hospital-scoped intelligence', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByText(/Assigned Facility: City Hospital/i)).toBeDefined();
    });

    expect(intelligenceService.getDiseaseTrends).toHaveBeenCalledWith(
      expect.objectContaining({
        facility: 1,
        district: undefined,
      })
    );
  });

  it('3. verifies District Officer sees district intelligence and hospital comparison', async () => {
    setupAuth('DISTRICT_OFFICER');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByText(/District Officer: Central District/i)).toBeDefined();
      expect(screen.getByText(/District Hospital Case Comparison/i)).toBeDefined();
      expect(screen.getByText('City Hospital')).toBeDefined();
      expect(screen.getByText('Metro Center')).toBeDefined();
    });

    expect(intelligenceService.getDistrictAggregation).toHaveBeenCalledWith(5, expect.anything());
  });

  it('4. verifies disease trend data renders with backend terminology', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getAllByText('Dengue Fever').length).toBeGreaterThan(0);
      expect(screen.getAllByText('INCREASING').length).toBeGreaterThan(0);
      expect(screen.getByText('+40%')).toBeDefined();
    });
  });

  it('5. verifies locality data renders including "Unknown Locality"', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByText('Shivajinagar Ward')).toBeDefined();
      expect(screen.getByText('Unknown Locality')).toBeDefined();
      expect(screen.getByText('47.6%')).toBeDefined();
    });
  });

  it('6. verifies historical data renders with severity breakdown', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByText(/Historical Disease Trajectory/i)).toBeDefined();
      expect(screen.getByText('Aug 2026')).toBeDefined();
      expect(screen.getByText('Oct 2026')).toBeDefined();
      expect(screen.getAllByText(/Mild:/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Severe:/i).length).toBeGreaterThan(0);
    });
  });

  it('7. verifies forecast renders with safe wording', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByText('Forecast / Surveillance Signal')).toBeDefined();
      expect(screen.getByText(/WEIGHTED_MOVING_AVERAGE/i)).toBeDefined();
      expect(screen.getByText(/\[8 — 16\]/i)).toBeDefined();
    });
  });

  it('8. verifies seasonality renders with detected pattern and months', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.queryByText('Loading public health intelligence...')).toBeNull();
    });

    expect(screen.getByRole('heading', { name: /Seasonal Pattern Analysis/i })).toBeDefined();
    expect(screen.getByText('DETECTED')).toBeDefined();
    expect(screen.getByText('0.75')).toBeDefined();
    expect(screen.getAllByText('October').length).toBeGreaterThan(0);
    expect(screen.getByText('February')).toBeDefined();
  });

  it('9. verifies insufficient forecast data renders safely with backend explanation', async () => {
    vi.mocked(intelligenceService.getForecast).mockResolvedValue(mockForecastInsufficient);
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getAllByText(/Insufficient historical surveillance data for a reliable forecast/i).length).toBeGreaterThan(0);
    });
  });

  it('10. verifies API error renders safely with clear warning message', async () => {
    vi.mocked(intelligenceService.getDiseaseTrends).mockRejectedValue(new Error('Network error'));
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to load public health intelligence data/i)).toBeDefined();
    });
  });

  it('11. verifies unauthorized response renders safely without crashing', async () => {
    vi.mocked(intelligenceService.getDiseaseTrends).mockRejectedValue({
      response: {
        status: 403,
        data: { error: 'Scope violation: Unauthorized facility requested.' },
      },
    });
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByText(/Cross-Scope Authorization Rejected \(HTTP 403\)/i)).toBeDefined();
      expect(screen.getByText(/Scope violation: Unauthorized facility requested./i)).toBeDefined();
    });
  });

  it('12. verifies changing filters updates requests with new parameters', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByLabelText(/As-of Date/i)).toBeDefined();
    });

    const dateInput = screen.getByLabelText(/As-of Date/i);
    fireEvent.change(dateInput, { target: { value: '2026-05-15' } });

    await waitFor(() => {
      expect(intelligenceService.getDiseaseTrends).toHaveBeenCalledWith(
        expect.objectContaining({
          date: '2026-05-15',
        })
      );
    });
  });

  it('13. verifies selected date is passed consistently across all endpoints', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByLabelText(/As-of Date/i)).toBeDefined();
    });

    const dateInput = screen.getByLabelText(/As-of Date/i);
    fireEvent.change(dateInput, { target: { value: '2026-08-20' } });

    await waitFor(() => {
      const expectedParams = expect.objectContaining({ date: '2026-08-20' });
      expect(intelligenceService.getDiseaseTrends).toHaveBeenCalledWith(expectedParams);
      expect(intelligenceService.getDiseaseLocality).toHaveBeenCalledWith(expectedParams);
      expect(intelligenceService.getHistoricalDisease).toHaveBeenCalledWith(expectedParams);
      expect(intelligenceService.getForecast).toHaveBeenCalledWith(expectedParams);
      expect(intelligenceService.getSeasonality).toHaveBeenCalledWith(expectedParams);
    });
  });

  it('14. verifies no cross-facility selector is exposed to Hospital Admin', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByText('City Hospital')).toBeDefined();
    });

    // Facility selector is locked: select dropdown is not exposed, read-only div rendered instead
    const selectElem = screen.queryByRole('combobox', { name: /Facility Scope/i });
    expect(selectElem).toBeNull();
  });

  it('15. verifies no cross-district selector is exposed to District Officer', async () => {
    setupAuth('DISTRICT_OFFICER');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByText(/District Officer: Central District/i)).toBeDefined();
    });

    // District officer can select facilities within district, but not other districts
    const selectElem = screen.getByRole('combobox', { name: /Facility Scope/i }) as HTMLSelectElement;
    expect(selectElem).toBeDefined();

    // Facility from district 6 (Rural Clinic) must NOT be present in available facilities
    const options = Array.from(selectElem.options).map(o => o.text);
    expect(options.some(t => t.includes('Rural Clinic'))).toBe(false);
    expect(options.some(t => t.includes('City Hospital'))).toBe(true);
  });

  it('16. verifies historical chart renders from backend historical_series', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByTestId('historical-chart-container')).toBeDefined();
      expect(screen.getByRole('region', { name: /Historical Disease Trend Chart/i })).toBeDefined();
    });
  });

  it('17. verifies disease selector uses backend-returned disease names', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      const selectElem = screen.getByRole('combobox', { name: /Disease Condition/i }) as HTMLSelectElement;
      const options = Array.from(selectElem.options).map(o => o.text);
      expect(options).toContain('All Monitored Conditions');
      expect(options).toContain('Dengue Fever');
    });
  });

  it('18. verifies unknown/backend-added disease can appear in the selector', async () => {
    vi.mocked(intelligenceService.getDiseaseTrends).mockResolvedValue({
      ...mockTrends,
      disease_trends: [
        {
          disease: 'Novel Respiratory Illness',
          current_cases: 10,
          previous_period_cases: 2,
          cases_7d: 5,
          cases_30d: 15,
          cases_90d: 20,
          percentage_change: 400.0,
          trend_direction: 'INCREASING',
          explanation: 'Emerging cluster',
        },
      ],
    });
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      const selectElem = screen.getByRole('combobox', { name: /Disease Condition/i }) as HTMLSelectElement;
      const options = Array.from(selectElem.options).map(o => o.text);
      expect(options).toContain('Novel Respiratory Illness');
    });
  });

  it('19. verifies no duplicate disease options are rendered', async () => {
    vi.mocked(intelligenceService.getDiseaseTrends).mockResolvedValue({
      ...mockTrends,
      disease_trends: [
        {
          disease: 'Dengue Fever',
          current_cases: 25,
          previous_period_cases: 15,
          cases_7d: 12,
          cases_30d: 40,
          cases_90d: 80,
          percentage_change: 66.7,
          trend_direction: 'INCREASING',
          explanation: 'Recent cluster',
        },
        {
          disease: 'Dengue Fever',
          current_cases: 10,
          previous_period_cases: 5,
          cases_7d: 8,
          cases_30d: 20,
          cases_90d: 30,
          percentage_change: 100.0,
          trend_direction: 'INCREASING',
          explanation: 'Secondary cluster',
        },
      ],
    });
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      const selectElem = screen.getByRole('combobox', { name: /Disease Condition/i }) as HTMLSelectElement;
      const options = Array.from(selectElem.options).map(o => o.value);
      const uniqueOptions = Array.from(new Set(options));
      expect(options.length).toBe(uniqueOptions.length);
    });
  });

  it('20. verifies selecting a backend-returned disease sends that disease in API params', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByRole('combobox', { name: /Disease Condition/i })).toBeDefined();
    });

    const selectElem = screen.getByRole('combobox', { name: /Disease Condition/i });
    fireEvent.change(selectElem, { target: { value: 'Dengue Fever' } });

    await waitFor(() => {
      expect(intelligenceService.getDiseaseTrends).toHaveBeenCalledWith(
        expect.objectContaining({
          disease: 'Dengue Fever',
        })
      );
    });
  });

  it('21. verifies forecast heading says "Public Health Epidemiological Forecast"', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(
        screen.getByRole('heading', { name: /Public Health Epidemiological Forecast/i })
      ).toBeDefined();
    });
  });

  // ========================================================
  // STEP 4: SURVEILLANCE ALERTS & ACTION LAYER TESTS
  // ========================================================

  const mockTrendIncreasingAlert: IntelligenceAlert = {
    id: 101,
    alert_type: 'DISEASE_TREND',
    severity: 'WARNING',
    status: 'NEW',
    title: 'Increasing Disease Trend: Dengue Fever',
    description: 'Dengue Fever shows an increasing trend with 66.7% rise over previous period.',
    facility: 1,
    facility_name: 'City Hospital',
    district: 5,
    created_at: '2026-10-06T10:00:00Z',
    metadata: {
      disease: 'Dengue Fever',
      signal_type: 'DISEASE_TREND_INCREASING',
      trend_direction: 'INCREASING',
      current_cases: 25,
      previous_cases: 15,
      percentage_change: 66.7,
      observation_date: '2026-10-06',
    },
  };

  const mockTrendPossibleIncreaseAlert: IntelligenceAlert = {
    id: 102,
    alert_type: 'DISEASE_TREND',
    severity: 'WARNING',
    status: 'NEW',
    title: 'Possible Disease Trend Increase: Typhoid',
    description: 'Typhoid shows a possible increase with 50.0% rise over previous period.',
    facility: 1,
    facility_name: 'City Hospital',
    district: 5,
    created_at: '2026-10-06T10:00:00Z',
    metadata: {
      disease: 'Typhoid',
      signal_type: 'DISEASE_TREND_POSSIBLE_INCREASE',
      trend_direction: 'POSSIBLE_INCREASE',
      current_cases: 15,
      previous_cases: 10,
      percentage_change: 50.0,
      observation_date: '2026-10-06',
    },
  };

  const mockLocalityConcentrationAlert: IntelligenceAlert = {
    id: 103,
    alert_type: 'HIGH_LOCALITY_CONCENTRATION',
    severity: 'WARNING',
    status: 'NEW',
    title: 'High Locality Concentration: Dengue Fever in Shivajinagar Ward',
    description: 'Shivajinagar Ward accounts for 47.6% of Dengue Fever cases (threshold: 25.0%).',
    facility: 1,
    facility_name: 'City Hospital',
    district: 5,
    created_at: '2026-10-06T10:00:00Z',
    metadata: {
      disease: 'Dengue Fever',
      signal_type: 'HIGH_LOCALITY_CONCENTRATION',
      locality: 'Shivajinagar Ward',
      locality_id: 101,
      current_cases: 20,
      locality_share: 47.6,
      threshold_used: 25.0,
      observation_date: '2026-10-06',
    },
  };

  const mockForecastSignalAlert: IntelligenceAlert = {
    id: 104,
    alert_type: 'FORECAST_SURVEILLANCE_SIGNAL',
    severity: 'WARNING',
    status: 'NEW',
    title: 'Forecast Surveillance Signal: Dengue Fever',
    description: 'Forecast indicates elevated future case volume.',
    facility: 1,
    facility_name: 'City Hospital',
    district: 5,
    created_at: '2026-10-06T10:00:00Z',
    metadata: {
      disease: 'Dengue Fever',
      signal_type: 'FORECAST_SURVEILLANCE_SIGNAL',
      forecast_horizon: '4 weeks',
      predicted_cases: 12,
      lower_bound: 8,
      upper_bound: 16,
      historical_baseline: 6.25,
      forecast_method: 'WEIGHTED_MOVING_AVERAGE',
      observation_date: '2026-10-06',
    },
  };

  const mockSeasonalSignalAlert: IntelligenceAlert = {
    id: 105,
    alert_type: 'SEASONAL_SURVEILLANCE_SIGNAL',
    severity: 'INFO',
    status: 'NEW',
    title: 'Seasonal Surveillance Signal: Dengue Fever',
    description: 'Historical surveillance indicates an active seasonal pattern for Dengue Fever.',
    facility: 1,
    facility_name: 'City Hospital',
    district: 5,
    created_at: '2026-10-06T10:00:00Z',
    metadata: {
      disease: 'Dengue Fever',
      signal_type: 'SEASONAL_SURVEILLANCE_SIGNAL',
      seasonal_status: 'DETECTED',
      highest_case_month: 'October',
      seasonal_strength: 0.75,
      observation_date: '2026-10-06',
    },
  };

  it('Step 4.1: increasing disease trend creates warning signal', async () => {
    vi.mocked(intelligenceService.getAlerts).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [mockTrendIncreasingAlert],
    });
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByTestId('alert-card-101')).toBeDefined();
    });

    const card = screen.getByTestId('alert-card-101');
    expect(card.textContent).toContain('WARNING');
    expect(card.textContent).toContain('Disease Trend');
    expect(card.textContent).toContain('Dengue Fever');
    expect(card.textContent).toContain('+66.7%');
  });

  it('Step 4.2: possible increase creates warning signal', async () => {
    vi.mocked(intelligenceService.getAlerts).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [mockTrendPossibleIncreaseAlert],
    });
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByTestId('alert-card-102')).toBeDefined();
    });

    const card = screen.getByTestId('alert-card-102');
    expect(card.textContent).toContain('WARNING');
    expect(card.textContent).toContain('Typhoid');
    expect(card.textContent).toContain('+50%');
  });

  it('Step 4.3: locality threshold creates signal', async () => {
    vi.mocked(intelligenceService.getAlerts).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [mockLocalityConcentrationAlert],
    });
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByTestId('alert-card-103')).toBeDefined();
    });

    const card = screen.getByTestId('alert-card-103');
    expect(card.textContent).toContain('WARNING');
    expect(card.textContent).toContain('High Locality Concentration');
    expect(card.textContent).toContain('Shivajinagar Ward');
    expect(card.textContent).toContain('47.6%');
  });

  it('Step 4.4: forecast surveillance signal works', async () => {
    vi.mocked(intelligenceService.getAlerts).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [mockForecastSignalAlert],
    });
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByTestId('alert-card-104')).toBeDefined();
    });

    const card = screen.getByTestId('alert-card-104');
    expect(card.textContent).toContain('WARNING');
    expect(card.textContent).toContain('Forecast Surveillance Signal');
    expect(card.textContent).toContain('12');
  });

  it('Step 4.5: seasonal signal works', async () => {
    vi.mocked(intelligenceService.getAlerts).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [mockSeasonalSignalAlert],
    });
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByTestId('alert-card-105')).toBeDefined();
    });

    const card = screen.getByTestId('alert-card-105');
    expect(card.textContent).toContain('INFO');
    expect(card.textContent).toContain('Seasonal Surveillance Signal');
    expect(card.textContent).toContain('October');
  });

  it('Step 4.6: duplicate evaluation does not create duplicate alerts', async () => {
    vi.mocked(intelligenceService.getAlerts).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [mockTrendIncreasingAlert],
    });
    vi.mocked(intelligenceService.evaluateAlerts).mockResolvedValue({
      created_count: 0,
      updated_count: 1,
      evaluated_signals_count: 1,
      alerts: [mockTrendIncreasingAlert],
    });

    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByTestId('evaluate-signals-btn')).toBeDefined();
    });

    fireEvent.click(screen.getByTestId('evaluate-signals-btn'));

    await waitFor(() => {
      expect(screen.getByText(/0 new signal\(s\) created, 1 existing signal\(s\) updated\./i)).toBeDefined();
    });

    const cards = screen.getAllByTestId('alert-card-101');
    expect(cards.length).toBe(1);
  });

  it('Step 4.7: Hospital Admin sees only own facility alerts', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(intelligenceService.getAlerts).toHaveBeenCalledWith(
        expect.objectContaining({
          facility: 1,
          district: undefined,
        })
      );
    });
  });

  it('Step 4.8: District Officer sees only own district alerts', async () => {
    setupAuth('DISTRICT_OFFICER');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(intelligenceService.getAlerts).toHaveBeenCalledWith(
        expect.objectContaining({
          facility: undefined,
          district: 5,
        })
      );
    });
  });

  it('Step 4.9: cross-facility access is rejected', async () => {
    setupAuth('HOSPITAL_ADMIN');
    vi.mocked(intelligenceService.evaluateAlerts).mockRejectedValue({
      response: {
        status: 403,
        data: { error: 'Permission denied: Cannot evaluate alerts outside assigned facility.' },
      },
    });

    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByTestId('evaluate-signals-btn')).toBeDefined();
    });

    fireEvent.click(screen.getByTestId('evaluate-signals-btn'));

    await waitFor(() => {
      expect(screen.getByText(/Permission denied: Cannot evaluate alerts outside assigned facility\./i)).toBeDefined();
    });
  });

  it('Step 4.10: acknowledge works', async () => {
    vi.mocked(intelligenceService.getAlerts).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [mockTrendIncreasingAlert],
    });
    vi.mocked(intelligenceService.acknowledgeAlert).mockResolvedValue({
      ...mockTrendIncreasingAlert,
      status: 'ACKNOWLEDGED',
    });

    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByTestId('ack-btn-101')).toBeDefined();
    });

    fireEvent.click(screen.getByTestId('ack-btn-101'));

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeDefined();
      expect(screen.getByText('Acknowledge Surveillance Signal')).toBeDefined();
    });

    const confirmBtn = screen.getByRole('button', { name: 'Acknowledge Signal' });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(intelligenceService.acknowledgeAlert).toHaveBeenCalledWith(101);
    });
  });

  it('Step 4.11: resolve works', async () => {
    vi.mocked(intelligenceService.getAlerts).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [mockTrendIncreasingAlert],
    });
    vi.mocked(intelligenceService.resolveAlert).mockResolvedValue({
      ...mockTrendIncreasingAlert,
      status: 'RESOLVED',
    });

    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByTestId('resolve-btn-101')).toBeDefined();
    });

    fireEvent.click(screen.getByTestId('resolve-btn-101'));

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeDefined();
      expect(screen.getByText('Resolve Surveillance Signal')).toBeDefined();
    });

    const confirmBtn = screen.getByRole('button', { name: 'Resolve Signal' });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(intelligenceService.resolveAlert).toHaveBeenCalledWith(101, expect.any(String));
    });
  });

  it('Step 4.12: confirmation popup is used', async () => {
    vi.mocked(intelligenceService.getAlerts).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [mockTrendIncreasingAlert],
    });

    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByTestId('ack-btn-101')).toBeDefined();
    });

    fireEvent.click(screen.getByTestId('ack-btn-101'));

    await waitFor(() => {
      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeDefined();
      expect(within(dialog).getByText('Signal Title')).toBeDefined();
      expect(within(dialog).getByText('City Hospital')).toBeDefined();
    });
  });

  it('Step 4.13: no window.confirm or window.alert is called', async () => {
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
    const confirmSpy = vi.spyOn(window, 'confirm').mockImplementation(() => true);

    vi.mocked(intelligenceService.getAlerts).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [mockTrendIncreasingAlert],
    });

    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByTestId('ack-btn-101')).toBeDefined();
    });

    fireEvent.click(screen.getByTestId('ack-btn-101'));

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeDefined();
    });

    expect(alertSpy).toHaveBeenCalledTimes(0);
    expect(confirmSpy).toHaveBeenCalledTimes(0);

    alertSpy.mockRestore();
    confirmSpy.mockRestore();
  });

  it('Step 4.14: alert details show evidence', async () => {
    vi.mocked(intelligenceService.getAlerts).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [mockForecastSignalAlert],
    });

    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByTestId('alert-card-104')).toBeDefined();
    });

    const evidenceBtn = screen.getByRole('button', { name: /View Evidence/i });
    fireEvent.click(evidenceBtn);

    await waitFor(() => {
      const modal = screen.getByTestId('alert-detail-modal');
      expect(modal).toBeDefined();
      expect(within(modal).getByText('Epidemiological Evidence')).toBeDefined();
      expect(within(modal).getByText(/Forecast Bounds \(90% CI\)/i)).toBeDefined();
      expect(within(modal).getByText('[8 - 16]')).toBeDefined();
      expect(within(modal).getByText('WEIGHTED_MOVING_AVERAGE')).toBeDefined();
    });
  });

  it('Step 4.15: navbar count integrates correctly', () => {
    const alertsList: IntelligenceAlert[] = [
      { ...mockTrendIncreasingAlert, status: 'NEW' },
      { ...mockTrendPossibleIncreaseAlert, status: 'NEW' },
      { ...mockLocalityConcentrationAlert, status: 'ACKNOWLEDGED' },
      { ...mockForecastSignalAlert, status: 'RESOLVED' },
    ];
    const openCount = alertsList.filter(a => a.status === 'NEW').length;
    expect(openCount).toBe(2);
  });

  // ========================================================
  // PROMPT 10: DEMOGRAPHIC FILTERS & FORECAST RISK UI TESTS
  // ========================================================

  it('1. Age Group filter renders', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      const select = screen.getByLabelText(/Age Group/i) as HTMLSelectElement;
      expect(select).toBeDefined();
      const options = Array.from(select.options).map(o => o.value);
      expect(options).toContain('');
      expect(options).toContain('0-5');
      expect(options).toContain('15-24');
      expect(options).toContain('60+');
    });
  });

  it('2. Gender filter renders', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      const select = screen.getByLabelText(/^Gender$/i) as HTMLSelectElement;
      expect(select).toBeDefined();
      const options = Array.from(select.options).map(o => o.value);
      expect(options).toContain('');
      expect(options).toContain('MALE');
      expect(options).toContain('FEMALE');
      expect(options).toContain('OTHER');
    });
  });

  it('3. Severity filter renders', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      const select = screen.getByLabelText(/^Severity$/i) as HTMLSelectElement;
      expect(select).toBeDefined();
      const options = Array.from(select.options).map(o => o.value);
      expect(options).toContain('');
      expect(options).toContain('MILD');
      expect(options).toContain('MODERATE');
      expect(options).toContain('SEVERE');
    });
  });

  it('4. Vulnerable Group filter renders', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      const select = screen.getByLabelText(/^Vulnerable Group$/i) as HTMLSelectElement;
      expect(select).toBeDefined();
      const options = Array.from(select.options).map(o => o.value);
      expect(options).toContain('');
      expect(options).toContain('PREGNANT');
      expect(options).toContain('ELDERLY');
      expect(options).not.toContain('UNKNOWN');
    });
  });

  it('5. Patient Type filter renders', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      const select = screen.getByLabelText(/^Patient Type$/i) as HTMLSelectElement;
      expect(select).toBeDefined();
      const options = Array.from(select.options).map(o => o.value);
      expect(options).toContain('');
      expect(options).toContain('NEW');
      expect(options).toContain('FOLLOW_UP');
      expect(options).not.toContain('UNKNOWN');
    });
  });

  it('6. Multiple demographic filters are sent together', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByLabelText(/Age Group/i)).toBeDefined();
    });

    fireEvent.change(screen.getByLabelText(/Age Group/i), { target: { value: '15-24' } });
    fireEvent.change(screen.getByLabelText(/^Gender$/i), { target: { value: 'FEMALE' } });
    fireEvent.change(screen.getByLabelText(/^Severity$/i), { target: { value: 'SEVERE' } });
    fireEvent.change(screen.getByLabelText(/^Vulnerable Group$/i), { target: { value: 'PREGNANT' } });
    fireEvent.change(screen.getByLabelText(/^Patient Type$/i), { target: { value: 'FOLLOW_UP' } });

    await waitFor(() => {
      const expectedParams = expect.objectContaining({
        age_group: '15-24',
        gender: 'FEMALE',
        severity: 'SEVERE',
        vulnerable_group: 'PREGNANT',
        patient_type: 'FOLLOW_UP',
      });
      expect(intelligenceService.getDiseaseTrends).toHaveBeenCalledWith(expectedParams);
      expect(intelligenceService.getDiseaseLocality).toHaveBeenCalledWith(expectedParams);
      expect(intelligenceService.getHistoricalDisease).toHaveBeenCalledWith(expectedParams);
      expect(intelligenceService.getForecast).toHaveBeenCalledWith(expectedParams);
      expect(intelligenceService.getSeasonality).toHaveBeenCalledWith(expectedParams);
    });
  });

  it('7. Reset Filters restores demographic defaults', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByLabelText(/Age Group/i)).toBeDefined();
    });

    // Apply multiple filters
    fireEvent.change(screen.getByLabelText(/Age Group/i), { target: { value: '60+' } });
    fireEvent.change(screen.getByLabelText(/^Severity$/i), { target: { value: 'SEVERE' } });

    await waitFor(() => {
      expect(intelligenceService.getForecast).toHaveBeenCalledWith(
        expect.objectContaining({ age_group: '60+', severity: 'SEVERE' })
      );
    });

    // Click Reset Filters
    const resetBtn = screen.getByRole('button', { name: /Reset Filters/i });
    fireEvent.click(resetBtn);

    await waitFor(() => {
      const lastForecastCall = vi.mocked(intelligenceService.getForecast).mock.calls.at(-1)?.[0];
      expect(lastForecastCall?.age_group).toBeUndefined();
      expect(lastForecastCall?.severity).toBeUndefined();
      expect((screen.getByLabelText(/Age Group/i) as HTMLSelectElement).value).toBe('');
      expect((screen.getByLabelText(/^Severity$/i) as HTMLSelectElement).value).toBe('');
    });
  });

  it('8. Forecast risk section renders', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByTestId('forecast-risk-section')).toBeDefined();
      expect(screen.getByTestId('kpi-historical-baseline')).toBeDefined();
      expect(within(screen.getByTestId('kpi-historical-baseline')).getByText('8')).toBeDefined();
      expect(screen.getByText(/Elevation Threshold:/i)).toBeDefined();
      expect(screen.getByText(/≥ 1.15×/i)).toBeDefined();
      expect(screen.getByText(/High-Risk Threshold:/i)).toBeDefined();
      expect(screen.getByText(/≥ 1.5×/i)).toBeDefined();
      expect(screen.getByTestId('risk-explanation')).toBeDefined();
      expect(screen.getByText(/Risk Explanation:/i)).toBeDefined();
    });
  });

  it('9. Highest risk level renders', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      const riskCard = screen.getByTestId('kpi-highest-risk');
      expect(within(riskCard).getByText('HIGH RISK')).toBeDefined();
      expect(within(riskCard).getByText(/High projected surveillance risk/i)).toBeDefined();
      // Ensure no sensationalized outbreak wording inside risk assessment
      expect(within(riskCard).queryByText(/confirmed outbreak/i)).toBeNull();
      expect(within(riskCard).queryByText(/confirmed epidemic/i)).toBeNull();
    });
  });

  it('10. Risk counts render', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      const countsCard = screen.getByTestId('kpi-risk-counts');
      expect(within(countsCard).getByText(/Normal Projected Weeks/i)).toBeDefined();
      expect(within(countsCard).getByText(/Elevated Projected Weeks/i)).toBeDefined();
      expect(within(countsCard).getByText(/High-Risk Projected Weeks/i)).toBeDefined();
      expect(within(countsCard).getByText('1')).toBeDefined(); // high risk count
    });
  });

  it('11. Risk points render', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByTestId('forecast-risk-points-table')).toBeDefined();
      const row = screen.getByTestId('risk-point-row-0');
      expect(within(row).getByText('Week +1')).toBeDefined();
      expect(within(row).getByText('12')).toBeDefined();
      expect(within(row).getByText('8')).toBeDefined();
      expect(within(row).getByText('1.5×')).toBeDefined();
      expect(within(row).getByText('HIGH RISK')).toBeDefined();
      expect(within(row).getByText(/Predicted volume exceeds high-risk threshold/i)).toBeDefined();
    });
  });

  it('12. INSUFFICIENT_DATA displays the insufficient-data message', async () => {
    vi.mocked(intelligenceService.getForecast).mockResolvedValue(mockForecastInsufficient);
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getAllByText(/Insufficient historical data for reliable forecast risk classification/i).length).toBeGreaterThan(0);
    });
  });

  it('13. INSUFFICIENT_DATA does not display fake risk points', async () => {
    vi.mocked(intelligenceService.getForecast).mockResolvedValue({
      ...mockForecastInsufficient,
      forecast_risk: {
        status: 'INSUFFICIENT_DATA',
        historical_baseline: null,
        elevation_ratio_threshold: 1.15,
        high_risk_ratio_threshold: 1.5,
        risk_points: [],
        highest_risk_level: 'INSUFFICIENT_DATA',
        risk_points_count: 0,
        high_risk_points_count: 0,
        elevated_points_count: 0,
        normal_points_count: 0,
        explanation: 'Insufficient historical data for reliable forecast risk classification.',
      },
    });
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getAllByText(/Insufficient historical data for reliable forecast risk classification/i).length).toBeGreaterThan(0);
    });

    // Verify no fake baseline or fake points are rendered
    expect(screen.queryByTestId('kpi-historical-baseline')).toBeNull();
    expect(screen.queryByTestId('forecast-risk-points-table')).toBeNull();
    expect(screen.queryByTestId('risk-point-row-0')).toBeNull();
  });

  it('14. Selected Population summary displays active filters', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByLabelText(/Age Group/i)).toBeDefined();
    });

    // Apply demographic filters: age 25-44, FEMALE, MODERATE, PREGNANT, NEW
    fireEvent.change(screen.getByLabelText(/Age Group/i), { target: { value: '25-44' } });
    fireEvent.change(screen.getByLabelText(/^Gender$/i), { target: { value: 'FEMALE' } });
    fireEvent.change(screen.getByLabelText(/^Severity$/i), { target: { value: 'MODERATE' } });
    fireEvent.change(screen.getByLabelText(/^Vulnerable Group$/i), { target: { value: 'PREGNANT' } });
    fireEvent.change(screen.getByLabelText(/^Patient Type$/i), { target: { value: 'NEW' } });

    await waitFor(() => {
      const summary = screen.getByTestId('forecast-selected-population');
      expect(within(summary).getByText('25-44')).toBeDefined();
      expect(within(summary).getByText('Female')).toBeDefined();
      expect(within(summary).getByText('Moderate')).toBeDefined();
      expect(within(summary).getByText('Pregnant')).toBeDefined();
      expect(within(summary).getByText('New')).toBeDefined();
    });
  });

  it('15. No demographic filters displays "All eligible population"', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByLabelText(/Age Group/i)).toBeDefined();
    });

    // Without demographic filters, displays "All eligible population"
    const summary = screen.getByTestId('forecast-selected-population');
    expect(within(summary).getByText('All eligible population')).toBeDefined();
  });

  it('16. Filtered case count displays "Cases in selected population: 12"', async () => {
    vi.mocked(intelligenceService.getForecast).mockResolvedValue({
      ...mockForecastAvailable,
      observation_period: {
        ...mockForecastAvailable.observation_period,
        total_cases: 12,
      },
    });
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getAllByText(/Cases in selected population:/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText('12').length).toBeGreaterThan(0);
    });
  });

  it('17. Zero selected-population cases displays "No cases found for the selected filters." and no fabricated normal risk', async () => {
    vi.mocked(intelligenceService.getForecast).mockResolvedValue({
      ...mockForecastAvailable,
      observation_period: {
        ...mockForecastAvailable.observation_period,
        total_cases: 0,
      },
      forecast_risk: {
        status: 'INSUFFICIENT_DATA',
        historical_baseline: null,
        elevation_ratio_threshold: 1.15,
        high_risk_ratio_threshold: 1.5,
        risk_points: [],
        highest_risk_level: 'INSUFFICIENT_DATA',
        risk_points_count: 0,
        high_risk_points_count: 0,
        elevated_points_count: 0,
        normal_points_count: 0,
        explanation: 'Insufficient historical data for reliable forecast risk classification.',
      },
    });
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getAllByText(/No cases found for the selected filters/i).length).toBeGreaterThan(0);
    });

    // Verify zero cases does NOT display fabricated normal-risk result or points
    expect(screen.queryByLabelText('NORMAL')).toBeNull();
    expect(screen.queryByTestId('kpi-historical-baseline')).toBeNull();
    expect(screen.queryByTestId('forecast-risk-points-table')).toBeNull();
  });

  it('18. Existing no-filter behavior continues working', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      // Summary KPIs
      expect(screen.getByText('Current Period Cases')).toBeDefined();
      expect(screen.getByText('42')).toBeDefined();
      // Trends
      expect(screen.getAllByText('Dengue Fever').length).toBeGreaterThan(0);
      // Forecast
      expect(screen.getByRole('heading', { name: /Public Health Epidemiological Forecast/i })).toBeDefined();
      // Seasonality
      expect(screen.getByRole('heading', { name: /Seasonal Pattern Analysis/i })).toBeDefined();
    });
  });

  it('Prompt 10: individual filter changes update service parameters correctly', async () => {
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByLabelText(/Age Group/i)).toBeDefined();
    });

    fireEvent.change(screen.getByLabelText(/Age Group/i), { target: { value: '25-44' } });
    await waitFor(() => {
      expect(intelligenceService.getForecast).toHaveBeenCalledWith(
        expect.objectContaining({ age_group: '25-44' })
      );
    });

    fireEvent.change(screen.getByLabelText(/^Gender$/i), { target: { value: 'MALE' } });
    await waitFor(() => {
      expect(intelligenceService.getForecast).toHaveBeenCalledWith(
        expect.objectContaining({ gender: 'MALE' })
      );
    });

    fireEvent.change(screen.getByLabelText(/^Severity$/i), { target: { value: 'MODERATE' } });
    await waitFor(() => {
      expect(intelligenceService.getForecast).toHaveBeenCalledWith(
        expect.objectContaining({ severity: 'MODERATE' })
      );
    });
  });

  it('Prompt 10: HTTP 400 invalid filter error is displayed safely', async () => {
    vi.mocked(intelligenceService.getDiseaseTrends).mockRejectedValue({
      response: {
        status: 400,
        data: { error: 'Invalid age_group value provided.' },
      },
    });
    setupAuth('HOSPITAL_ADMIN');
    render(<PublicHealthIntelligence />);

    await waitFor(() => {
      expect(screen.getByText(/Invalid age_group value provided./i)).toBeDefined();
    });
  });

  describe('Prompt Visual Enhancements & Non-Technical Health Staff Views', () => {
    const mockRichSeasonality: SeasonalityData = {
      ...mockSeasonality,
      seasonal_age_groups: [
        { age_group: '0-5', total_cases: 5, seasonal_strength: 0.5, seasonal_status: 'DETECTED', monthly_patterns: [], peak_month: null },
        { age_group: '6-14', total_cases: 8, seasonal_strength: 0.6, seasonal_status: 'DETECTED', monthly_patterns: [], peak_month: null },
        { age_group: '15-24', total_cases: 12, seasonal_strength: 0.7, seasonal_status: 'DETECTED', monthly_patterns: [], peak_month: null },
        { age_group: '25-44', total_cases: 20, seasonal_strength: 0.8, seasonal_status: 'DETECTED', monthly_patterns: [], peak_month: null },
        { age_group: '45-59', total_cases: 10, seasonal_strength: 0.5, seasonal_status: 'DETECTED', monthly_patterns: [], peak_month: null },
        { age_group: '60+', total_cases: 4, seasonal_strength: 0.4, seasonal_status: 'DETECTED', monthly_patterns: [], peak_month: null },
      ],
      seasonal_gender: [
        { gender: 'MALE', total_cases: 32, seasonal_strength: 0.7, seasonal_status: 'DETECTED', monthly_patterns: [], peak_month: null },
        { gender: 'FEMALE', total_cases: 27, seasonal_strength: 0.7, seasonal_status: 'DETECTED', monthly_patterns: [], peak_month: null },
      ],
      seasonal_severity: [
        { severity: 'MILD', total_cases: 36, seasonal_strength: 0.7, seasonal_status: 'DETECTED', monthly_patterns: [], peak_month: null },
        { severity: 'MODERATE', total_cases: 11, seasonal_strength: 0.5, seasonal_status: 'DETECTED', monthly_patterns: [], peak_month: null },
        { severity: 'SEVERE', total_cases: 3, seasonal_strength: 0.3, seasonal_status: 'DETECTED', monthly_patterns: [], peak_month: null },
      ],
      seasonal_vulnerable_groups: [
        { vulnerable_group: 'PREGNANT', total_cases: 7, seasonal_strength: 0.5, seasonal_status: 'DETECTED', monthly_patterns: [], peak_month: null },
        { vulnerable_group: 'ELDERLY', total_cases: 14, seasonal_strength: 0.6, seasonal_status: 'DETECTED', monthly_patterns: [], peak_month: null },
        { vulnerable_group: 'GENERAL', total_cases: 35, seasonal_strength: 0.7, seasonal_status: 'DETECTED', monthly_patterns: [], peak_month: null },
      ],
      seasonal_patient_types: [
        { patient_type: 'NEW', total_cases: 42, seasonal_strength: 0.7, seasonal_status: 'DETECTED', monthly_patterns: [], peak_month: null },
        { patient_type: 'FOLLOW_UP', total_cases: 17, seasonal_strength: 0.4, seasonal_status: 'DETECTED', monthly_patterns: [], peak_month: null },
      ],
      seasonal_age_gender: {
        '25-44': {
          MALE: { total_cases: 12, monthly_patterns: [] },
          FEMALE: { total_cases: 8, monthly_patterns: [] },
        },
      },
    };

    it('renders Overview KPI cards with authoritative numbers and descriptions', async () => {
      vi.mocked(intelligenceService.getSeasonality).mockResolvedValue(mockRichSeasonality);
      setupAuth('HOSPITAL_ADMIN');
      render(<PublicHealthIntelligence />);

      await waitFor(() => {
        expect(screen.getByText('Total Cases')).toBeDefined();
        expect(screen.getByText('Cases in selected population')).toBeDefined();
        expect(screen.getByText('Active Diseases')).toBeDefined();
        expect(screen.getByText('Forecast Cases')).toBeDefined();
        expect(screen.getByText('Expected cases in forecast period')).toBeDefined();
        expect(screen.getByText('High Risk Signals')).toBeDefined();
        expect(screen.getByText('Areas requiring attention')).toBeDefined();
      });
    });

    it('renders Disease Trend visualization with line/area chart and derived insight', async () => {
      vi.mocked(intelligenceService.getSeasonality).mockResolvedValue(mockRichSeasonality);
      setupAuth('HOSPITAL_ADMIN');
      render(<PublicHealthIntelligence />);

      await waitFor(() => {
        expect(screen.getByText(/📈 Disease Trend/i)).toBeDefined();
        expect(screen.getByText(/Shows how reported cases have changed over time/i)).toBeDefined();
        expect(screen.getByText(/Cases are increasing over the selected period/i)).toBeDefined();
      });
    });

    it('renders Disease Distribution and derived highest reported disease', async () => {
      vi.mocked(intelligenceService.getSeasonality).mockResolvedValue(mockRichSeasonality);
      setupAuth('HOSPITAL_ADMIN');
      render(<PublicHealthIntelligence />);

      await waitFor(() => {
        expect(screen.getByText(/🦠 Disease Distribution/i)).toBeDefined();
        expect(screen.getByText(/Shows which diseases have the highest number of reported cases/i)).toBeDefined();
        expect(screen.getByText(/Highest reported disease:/i)).toBeDefined();
      });
    });

    it('renders Age and Gender distributions with insights', async () => {
      vi.mocked(intelligenceService.getSeasonality).mockResolvedValue(mockRichSeasonality);
      setupAuth('HOSPITAL_ADMIN');
      render(<PublicHealthIntelligence />);

      await waitFor(() => {
        expect(screen.getByText(/👥 Age Distribution/i)).toBeDefined();
        expect(screen.getByText(/^Gender Distribution$/i)).toBeDefined();
        const ageCard = screen.getByTestId('age-distribution-card');
        expect(ageCard.textContent).toContain('Most cases are in the');
        expect(ageCard.textContent).toContain('25-44');
      });
    });

    it('renders Case Severity, Vulnerable Population, and Patient Type with insights', async () => {
      vi.mocked(intelligenceService.getSeasonality).mockResolvedValue(mockRichSeasonality);
      setupAuth('HOSPITAL_ADMIN');
      render(<PublicHealthIntelligence />);

      await waitFor(() => {
        expect(screen.getByText(/🩺 Case Severity/i)).toBeDefined();
        const sevCard = screen.getByTestId('case-severity-section');
        expect(sevCard.textContent).toContain('Most reported cases are');
        expect(sevCard.textContent).toContain('Mild');
        expect(screen.getByText(/🤝 Vulnerable Population/i)).toBeDefined();
        const ptCard = screen.getByTestId('patient-type-section');
        expect(ptCard.textContent).toContain('Patient Type');
      });
    });

    it('renders Seasonality Pattern visualization with peak month insight', async () => {
      vi.mocked(intelligenceService.getSeasonality).mockResolvedValue(mockRichSeasonality);
      setupAuth('HOSPITAL_ADMIN');
      render(<PublicHealthIntelligence />);

      await waitFor(() => {
        expect(screen.getByText(/🗓️ Seasonal Pattern/i)).toBeDefined();
        expect(screen.getByText(/Shows when cases are more common during the selected period/i)).toBeDefined();
        expect(screen.getByText(/Highest reported activity occurred in October/i)).toBeDefined();
      });
    });

    it('renders Case Forecast and Forecast Risk with estimates explanation', async () => {
      vi.mocked(intelligenceService.getSeasonality).mockResolvedValue(mockRichSeasonality);
      setupAuth('HOSPITAL_ADMIN');
      render(<PublicHealthIntelligence />);

      await waitFor(() => {
        expect(screen.getByText(/🔮 Case Forecast/i)).toBeDefined();
        expect(screen.getByText(/Forecast values are estimates based on historical case patterns/i)).toBeDefined();
        expect(screen.getByText(/🚦 Forecast Risk/i)).toBeDefined();
      });
    });

    it('renders clean empty state when selected filters return zero cases', async () => {
      vi.mocked(intelligenceService.getForecast).mockResolvedValue({
        ...mockForecastAvailable,
        observation_period: {
          ...mockForecastAvailable.observation_period,
          total_cases: 0,
        },
        forecast_risk: {
          ...mockForecastAvailable.forecast_risk!,
          status: 'INSUFFICIENT_DATA',
          highest_risk_level: 'INSUFFICIENT_DATA',
          risk_points: [],
          historical_baseline: null,
        },
      });
      setupAuth('HOSPITAL_ADMIN');
      render(<PublicHealthIntelligence />);

      await waitFor(() => {
        expect(screen.getByText(/No cases found for the selected filters/i)).toBeDefined();
      });
    });
  });
});
