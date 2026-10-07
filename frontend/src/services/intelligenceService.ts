import api from './api';
import type {
  IntelligenceFilterParams,
  DiseaseTrendsResponse,
  DiseaseLocalityResponse,
  HistoricalDiseaseResponse,
  ForecastSummaryResponse,
  SeasonalityData,
  DistrictAggregationResponse,
} from '../types/intelligence';

/**
 * Public Health Intelligence & Forecasting API Service
 * Centralizes all communication with Step 1 and Step 2 backend endpoints.
 */

const cleanParams = (params?: IntelligenceFilterParams): Record<string, string | number> => {
  const result: Record<string, string | number> = {};
  if (!params) return result;

  if (params.facility !== undefined && params.facility !== '' && params.facility !== null) {
    result.facility = params.facility;
  }
  if (params.district !== undefined && params.district !== '' && params.district !== null) {
    result.district = params.district;
  }
  if (params.disease && params.disease.trim() !== '') {
    result.disease = params.disease.trim();
  }
  if (params.date && params.date.trim() !== '') {
    result.date = params.date.trim();
  }
  if (params.days !== undefined) {
    result.days = params.days;
  }
  if (params.weeks !== undefined) {
    result.weeks = params.weeks;
  }
  if (params.months !== undefined) {
    result.months = params.months;
  }

  return result;
};

export const intelligenceService = {
  /**
   * 1. Public Health Intelligence Overview / Summary (Step 1)
   */
  async getSummary(params?: IntelligenceFilterParams) {
    const res = await api.get('surveillance/intelligence/summary/', {
      params: cleanParams(params),
    });
    return res.data;
  },

  /**
   * 2. Disease Trends Analysis (Step 1)
   */
  async getDiseaseTrends(params?: IntelligenceFilterParams): Promise<DiseaseTrendsResponse> {
    const res = await api.get<DiseaseTrendsResponse>('surveillance/intelligence/disease-trends/', {
      params: cleanParams(params),
    });
    return res.data;
  },

  /**
   * 3. Disease-by-Locality Aggregation (Step 1)
   */
  async getDiseaseLocality(params?: IntelligenceFilterParams): Promise<DiseaseLocalityResponse> {
    const res = await api.get<DiseaseLocalityResponse>('surveillance/intelligence/disease-by-locality/', {
      params: cleanParams(params),
    });
    return res.data;
  },

  /**
   * 4. Historical Disease Aggregation (Step 1)
   */
  async getHistoricalDisease(params?: IntelligenceFilterParams): Promise<HistoricalDiseaseResponse> {
    const res = await api.get<HistoricalDiseaseResponse>('surveillance/intelligence/historical-disease/', {
      params: cleanParams(params),
    });
    return res.data;
  },

  /**
   * 5. District-Level Aggregation & Hospital Comparison (Step 1)
   */
  async getDistrictAggregation(districtId: number, params?: IntelligenceFilterParams): Promise<DistrictAggregationResponse> {
    const cleaned = cleanParams(params);
    cleaned.district = districtId;
    const res = await api.get<DistrictAggregationResponse>('surveillance/intelligence/district-aggregation/', {
      params: cleaned,
    });
    return res.data;
  },

  /**
   * 6. Disease Forecasting & Weekly Trend Signals (Step 2)
   */
  async getForecast(params?: IntelligenceFilterParams): Promise<ForecastSummaryResponse> {
    const res = await api.get<ForecastSummaryResponse>('surveillance/intelligence/forecast/', {
      params: cleanParams(params),
    });
    return res.data;
  },

  /**
   * 7. Seasonal Pattern Analysis (Step 2)
   */
  async getSeasonality(params?: IntelligenceFilterParams): Promise<SeasonalityData> {
    const res = await api.get<SeasonalityData>('surveillance/intelligence/seasonality/', {
      params: cleanParams(params),
    });
    return res.data;
  },

  /**
   * 8. Public Health Intelligence Alerts (Step 4)
   */
  async getAlerts(params?: IntelligenceFilterParams & { status?: string; severity?: string }) {
    const res = await api.get('surveillance/intelligence/alerts/', {
      params: {
        ...cleanParams(params),
        ...(params?.status ? { status: params.status } : {}),
        ...(params?.severity ? { severity: params.severity } : {}),
      },
    });
    return res.data;
  },

  /**
   * 9. Evaluate Surveillance Signals (Step 4)
   */
  async evaluateAlerts(payload: { facility?: number | string; district?: number | string; date?: string }) {
    const res = await api.post('surveillance/intelligence/alerts/evaluate/', payload);
    return res.data;
  },

  /**
   * 10. Acknowledge Alert (Step 4)
   */
  async acknowledgeAlert(alertId: number) {
    const res = await api.post(`surveillance/intelligence/alerts/${alertId}/acknowledge/`);
    return res.data;
  },

  /**
   * 11. Resolve Alert (Step 4)
   */
  async resolveAlert(alertId: number, notes?: string) {
    const res = await api.post(`surveillance/intelligence/alerts/${alertId}/resolve/`, {
      resolution_notes: notes || '',
    });
    return res.data;
  },
};

export default intelligenceService;
