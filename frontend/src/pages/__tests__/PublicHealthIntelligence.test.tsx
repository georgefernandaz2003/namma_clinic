import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { PublicHealthIntelligence } from '../PublicHealthIntelligence';
import intelligenceService from '../../services/intelligenceService';
import * as AuthContextModule from '../../context/AuthContext';
import type {
  DiseaseTrendsResponse,
  DiseaseLocalityResponse,
  HistoricalDiseaseResponse,
  ForecastSummaryResponse,
  SeasonalityData,
  DistrictAggregationResponse,
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
  },
}));

// Mock AuthContext
vi.mock('../../context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

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
});
