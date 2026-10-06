import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import {
  Activity,
  Calendar,
  Building2,
  MapPin,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  HelpCircle,
  RefreshCw,
  Search,
  ShieldAlert,
  BarChart3,
  Layers,
  Sparkles,
  ArrowRight,
  Info
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { hasPermission } from '../utils/permissions';
import intelligenceService from '../services/intelligenceService';
import type {
  TrendDirection,
  DiseaseTrendsResponse,
  DiseaseLocalityResponse,
  HistoricalDiseaseResponse,
  ForecastSummaryResponse,
  SeasonalityData,
  DistrictAggregationResponse,
  IntelligenceFilterParams
} from '../types/intelligence';

// Common Monitored Disease Options in Primary Health System
const COMMON_DISEASES = [
  'All Monitored Conditions',
  'Dengue Fever',
  'Acute Pyrexia / Suspected Viral Fever',
  'Acute Gastroenteritis',
  'Malaria',
  'Typhoid',
  'Chikungunya',
  'Respiratory Infection (ARI)'
];

export const PublicHealthIntelligence: React.FC = () => {
  const { user, allFacilities } = useAuth();

  // Role detection
  const isDistrictOfficer = user?.role === 'DISTRICT_OFFICER';
  const isHospitalAdmin = user?.role === 'HOSPITAL_ADMIN';
  const isDoctorOrNurse = user?.role === 'DOCTOR' || user?.role === 'NURSE';

  // Verify dashboard.view permission
  const canViewDashboard = Boolean(
    (user?.permissions && user.permissions.includes('dashboard.view')) ||
    hasPermission(user?.role, 'dashboard.view')
  );

  // Authoritative scope determination
  const userAssignedDistrictId = user?.assigned_district || null;
  const userAssignedFacilityId = user?.assigned_facility || null;

  // Facilities accessible to current user for the selector
  const availableFacilities = useMemo(() => {
    if (isDistrictOfficer && userAssignedDistrictId) {
      return allFacilities.filter(f => f.district === userAssignedDistrictId);
    }
    if (isHospitalAdmin || isDoctorOrNurse) {
      if (userAssignedFacilityId) {
        return allFacilities.filter(f => f.id === userAssignedFacilityId);
      }
    }
    return allFacilities;
  }, [allFacilities, isDistrictOfficer, isHospitalAdmin, isDoctorOrNurse, userAssignedDistrictId, userAssignedFacilityId]);

  // Filters State
  const todayStr = useMemo(() => new Date().toISOString().split('T')[0], []);
  const [selectedDate, setSelectedDate] = useState<string>(todayStr);
  const [selectedDisease, setSelectedDisease] = useState<string>('All Monitored Conditions');
  const [selectedFacilityId, setSelectedFacilityId] = useState<string>(
    userAssignedFacilityId ? String(userAssignedFacilityId) : ''
  );
  const [selectedDistrictId] = useState<string>(
    userAssignedDistrictId ? String(userAssignedDistrictId) : ''
  );
  const [forecastHorizonWeeks, setForecastHorizonWeeks] = useState<number>(4);
  const [historicalMonthsCount, setHistoricalMonthsCount] = useState<number>(12);

  // Search filter within locality/disease tables
  const [localitySearch, setLocalitySearch] = useState<string>('');
  const [diseaseSearch, setDiseaseSearch] = useState<string>('');

  // Data States
  const [trendsData, setTrendsData] = useState<DiseaseTrendsResponse | null>(null);
  const [localityData, setLocalityData] = useState<DiseaseLocalityResponse | null>(null);
  const [historicalData, setHistoricalData] = useState<HistoricalDiseaseResponse | null>(null);
  const [forecastData, setForecastData] = useState<ForecastSummaryResponse | null>(null);
  const [seasonalityData, setSeasonalityData] = useState<SeasonalityData | null>(null);
  const [districtAggData, setDistrictAggData] = useState<DistrictAggregationResponse | null>(null);

  // Loading, Error, and Unauthorized states
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isUnauthorized, setIsUnauthorized] = useState<boolean>(false);

  // Request race condition prevention
  const activeRequestIdRef = useRef<number>(0);

  // Centralized Data Fetcher
  const fetchIntelligenceData = useCallback(async () => {
    const currentReqId = ++activeRequestIdRef.current;
    setLoading(true);
    setErrorMessage(null);
    setIsUnauthorized(false);

    // Compute effective params strictly respecting role boundaries
    const effectiveFacility = (isHospitalAdmin || isDoctorOrNurse)
      ? userAssignedFacilityId || undefined
      : selectedFacilityId ? Number(selectedFacilityId) : undefined;

    const effectiveDistrict = isDistrictOfficer
      ? userAssignedDistrictId || undefined
      : selectedDistrictId ? Number(selectedDistrictId) : undefined;

    const effectiveDisease = selectedDisease === 'All Monitored Conditions' ? undefined : selectedDisease;

    const queryParams: IntelligenceFilterParams = {
      facility: effectiveFacility,
      district: effectiveDistrict,
      disease: effectiveDisease,
      date: selectedDate || undefined,
      weeks: forecastHorizonWeeks,
      months: historicalMonthsCount
    };

    try {
      // Parallel fetch across endpoints
      const trendsPromise = intelligenceService.getDiseaseTrends(queryParams);
      const localityPromise = intelligenceService.getDiseaseLocality(queryParams);
      const historicalPromise = intelligenceService.getHistoricalDisease(queryParams);
      const forecastPromise = intelligenceService.getForecast(queryParams);
      const seasonalityPromise = intelligenceService.getSeasonality(queryParams);

      // District comparison only when district officer
      const districtPromise = (isDistrictOfficer && userAssignedDistrictId)
        ? intelligenceService.getDistrictAggregation(userAssignedDistrictId, queryParams)
        : Promise.resolve(null);

      const [trends, locality, historical, forecast, seasonality, districtAgg] = await Promise.all([
        trendsPromise,
        localityPromise,
        historicalPromise,
        forecastPromise,
        seasonalityPromise,
        districtPromise
      ]);

      // Guard against stale response
      if (currentReqId !== activeRequestIdRef.current) return;

      setTrendsData(trends);
      setLocalityData(locality);
      setHistoricalData(historical);
      setForecastData(forecast);
      setSeasonalityData(seasonality);
      setDistrictAggData(districtAgg);
    } catch (err: unknown) {
      if (currentReqId !== activeRequestIdRef.current) return;
      const apiErr = err as { response?: { status?: number; data?: { error?: string } } };
      if (apiErr.response?.status === 403) {
        setIsUnauthorized(true);
        setErrorMessage(apiErr.response?.data?.error || 'Access denied: You do not have authorization for this facility or district scope.');
      } else {
        setErrorMessage('Failed to load public health intelligence data. Please verify your connection or retry.');
      }
    } finally {
      if (currentReqId === activeRequestIdRef.current) {
        setLoading(false);
      }
    }
  }, [
    isHospitalAdmin,
    isDoctorOrNurse,
    isDistrictOfficer,
    userAssignedFacilityId,
    userAssignedDistrictId,
    selectedFacilityId,
    selectedDistrictId,
    selectedDisease,
    selectedDate,
    forecastHorizonWeeks,
    historicalMonthsCount
  ]);

  useEffect(() => {
    fetchIntelligenceData();
  }, [fetchIntelligenceData]);

  // Helpers for Trend Badges
  const renderTrendBadge = (direction: TrendDirection | string | undefined) => {
    switch (direction) {
      case 'INCREASING':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-rose-100 text-rose-800 border border-rose-300">
            <TrendingUp className="w-3 h-3 text-rose-700" />
            INCREASING
          </span>
        );
      case 'DECREASING':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-emerald-100 text-emerald-800 border border-emerald-300">
            <TrendingDown className="w-3 h-3 text-emerald-700" />
            DECREASING
          </span>
        );
      case 'POSSIBLE_INCREASE':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-amber-100 text-amber-900 border border-amber-300">
            <TrendingUp className="w-3 h-3 text-amber-700" />
            POSSIBLE INCREASE
          </span>
        );
      case 'NORMAL':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-blue-100 text-blue-800 border border-blue-300">
            <Minus className="w-3 h-3 text-blue-700" />
            NORMAL
          </span>
        );
      case 'INSUFFICIENT_DATA':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-slate-100 text-slate-700 border border-slate-300">
            <HelpCircle className="w-3 h-3 text-slate-500" />
            INSUFFICIENT DATA
          </span>
        );
    }
  };

  const renderPercentageBadge = (pct: number | null | undefined) => {
    if (pct === null || pct === undefined) {
      return <span className="text-slate-400 font-mono text-xs">Baseline 0</span>;
    }
    const isPositive = pct > 0;
    const isZero = pct === 0;
    return (
      <span
        className={`font-mono font-bold text-xs ${
          isZero ? 'text-slate-600' : isPositive ? 'text-rose-600' : 'text-emerald-600'
        }`}
      >
        {isPositive ? `+${pct}%` : `${pct}%`}
      </span>
    );
  };

  // Filtered lists for table search
  const filteredDiseaseTrends = useMemo(() => {
    const list = trendsData?.disease_trends || [];
    if (!diseaseSearch.trim()) return list;
    return list.filter(d => d.disease.toLowerCase().includes(diseaseSearch.toLowerCase()));
  }, [trendsData, diseaseSearch]);

  const filteredLocalities = useMemo(() => {
    const list = localityData?.locality_aggregations || [];
    if (!localitySearch.trim()) return list;
    return list.filter(l => l.locality.name.toLowerCase().includes(localitySearch.toLowerCase()));
  }, [localityData, localitySearch]);

  // Unauthorized page guard
  if (!canViewDashboard) {
    return (
      <div className="bg-rose-50 border border-rose-200 rounded-2xl p-8 max-w-xl mx-auto my-12 text-center shadow-lg">
        <div className="w-14 h-14 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mx-auto mb-4 border border-rose-300">
          <ShieldAlert className="w-7 h-7 text-rose-600" />
        </div>
        <h2 className="text-xl font-black text-rose-950 mb-2">Access Denied (HTTP 403)</h2>
        <p className="text-sm font-semibold text-rose-700">
          You do not possess the required dashboard view permission to access Public Health Intelligence.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Scope Banner & Header */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 rounded-2xl p-6 text-white shadow-md relative overflow-hidden border border-slate-800">
        <div className="absolute right-0 top-0 translate-x-6 -translate-y-6 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 bg-indigo-500/20 text-indigo-300 text-[10px] font-extrabold rounded-full uppercase tracking-wider border border-indigo-500/30">
                Epidemiological Intelligence & Surveillance
              </span>
              <span className="text-xs text-slate-400 font-semibold">• Step 1 & Step 2 Verified Backend</span>
            </div>
            <h1 className="text-2xl font-black tracking-tight flex items-center gap-2.5">
              <Activity className="w-6 h-6 text-indigo-400" />
              Public Health Intelligence & Forecasting
            </h1>
            <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
              Real historical DiseaseCase data aggregation, locality tracking, Weighted Moving Average forecasting signals, and seasonal pattern analysis.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={fetchIntelligenceData}
              disabled={loading}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-xl shadow-md transition flex items-center gap-2 disabled:opacity-50"
              aria-label="Refresh public health intelligence data"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>{loading ? 'Refreshing...' : 'Refresh Data'}</span>
            </button>
          </div>
        </div>

        {/* Current Active Scope Pill */}
        <div className="mt-4 pt-4 border-t border-slate-800/80 flex flex-wrap items-center gap-3 text-xs text-slate-300 font-mono">
          <span className="text-slate-400 font-bold uppercase tracking-wider text-[10px]">Active Scope:</span>
          {isDistrictOfficer && (
            <span className="px-2.5 py-1 bg-emerald-950/80 text-emerald-300 rounded-lg border border-emerald-800/50 flex items-center gap-1.5 font-bold">
              <Building2 className="w-3.5 h-3.5 text-emerald-400" />
              District Officer: {user?.district_name || `District ID #${userAssignedDistrictId}`}
              {selectedFacilityId && ` (${availableFacilities.find(f => f.id === Number(selectedFacilityId))?.facility_name || `Facility #${selectedFacilityId}`})`}
            </span>
          )}
          {(isHospitalAdmin || isDoctorOrNurse) && (
            <span className="px-2.5 py-1 bg-blue-950/80 text-blue-300 rounded-lg border border-blue-800/50 flex items-center gap-1.5 font-bold">
              <Building2 className="w-3.5 h-3.5 text-blue-400" />
              Assigned Facility: {user?.facility_name || `Hospital #${userAssignedFacilityId}`}
            </span>
          )}
          <span className="px-2.5 py-1 bg-slate-800/80 text-slate-300 rounded-lg border border-slate-700/50 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-indigo-400" />
            As-of Date: {selectedDate}
          </span>
        </div>
      </div>

      {/* FILTER BAR */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
        <div className="flex items-center gap-2 mb-3 pb-3 border-b border-slate-100">
          <Layers className="w-4 h-4 text-indigo-600" />
          <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Surveillance Intelligence Filters
          </h2>
          <span className="text-[11px] text-slate-500 font-normal">
            (All sections strictly synchronized to selected parameters)
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* 1. As-of Date Selector */}
          <div>
            <label htmlFor="as-of-date-input" className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
              As-of Date
            </label>
            <div className="relative">
              <input
                id="as-of-date-input"
                type="date"
                value={selectedDate}
                onChange={e => setSelectedDate(e.target.value)}
                className="w-full text-xs font-medium bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
          </div>

          {/* 2. Disease Selector */}
          <div>
            <label htmlFor="disease-filter-select" className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
              Disease Condition
            </label>
            <select
              id="disease-filter-select"
              value={selectedDisease}
              onChange={e => setSelectedDisease(e.target.value)}
              className="w-full text-xs font-medium bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              {COMMON_DISEASES.map(d => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          {/* 3. Facility Scope (Role-Aware) */}
          <div>
            <label htmlFor="facility-scope-select" className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
              Facility Scope
            </label>
            {isDistrictOfficer ? (
              <select
                id="facility-scope-select"
                value={selectedFacilityId}
                onChange={e => setSelectedFacilityId(e.target.value)}
                className="w-full text-xs font-medium bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="">All District Facilities (Aggregated)</option>
                {availableFacilities.map(f => (
                  <option key={f.id} value={f.id}>
                    {f.facility_name} ({f.facility_code})
                  </option>
                ))}
              </select>
            ) : (
              <div
                id="facility-scope-select"
                className="w-full text-xs font-semibold bg-slate-100 border border-slate-200 rounded-xl px-3 py-2 text-slate-700 truncate cursor-not-allowed"
                title="Hospital Admin scope is strictly locked to your assigned hospital"
              >
                {user?.facility_name || `Hospital #${userAssignedFacilityId}`}
              </div>
            )}
          </div>

          {/* 4. Forecast Horizon */}
          <div>
            <label htmlFor="forecast-horizon-select" className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
              Forecast Horizon
            </label>
            <select
              id="forecast-horizon-select"
              value={forecastHorizonWeeks}
              onChange={e => setForecastHorizonWeeks(Number(e.target.value))}
              className="w-full text-xs font-medium bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value={2}>Next 2 Weeks</option>
              <option value={4}>Next 4 Weeks (Standard)</option>
              <option value={8}>Next 8 Weeks</option>
              <option value={12}>Next 12 Weeks (Quarterly)</option>
            </select>
          </div>

          {/* 5. Historical Period */}
          <div>
            <label htmlFor="historical-period-select" className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
              Historical Window
            </label>
            <select
              id="historical-period-select"
              value={historicalMonthsCount}
              onChange={e => setHistoricalMonthsCount(Number(e.target.value))}
              className="w-full text-xs font-medium bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value={6}>Past 6 Months</option>
              <option value={12}>Past 12 Months (1 Year)</option>
              <option value={24}>Past 24 Months (2 Years)</option>
            </select>
          </div>
        </div>
      </div>

      {/* ERROR / UNAUTHORIZED ALERT */}
      {isUnauthorized && (
        <div className="bg-rose-50 border border-rose-300 rounded-2xl p-5 text-rose-900 flex items-start gap-3 shadow-xs">
          <ShieldAlert className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div className="text-xs">
            <h4 className="font-bold text-rose-950 text-sm">Cross-Scope Authorization Rejected (HTTP 403)</h4>
            <p className="mt-1 font-medium">{errorMessage}</p>
            <p className="mt-1 text-slate-600">The backend strictly enforces tenant isolation and prevented data exposure.</p>
          </div>
        </div>
      )}

      {errorMessage && !isUnauthorized && (
        <div className="bg-amber-50 border border-amber-300 rounded-2xl p-4 text-amber-900 flex items-start gap-3 text-xs shadow-xs">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold block">Failed to complete intelligence calculation</span>
            <span className="font-medium text-amber-800">{errorMessage}</span>
          </div>
        </div>
      )}

      {/* LOADING STATE */}
      {loading && (
        <div className="p-12 text-center bg-white rounded-2xl border border-slate-200 shadow-xs">
          <div className="inline-block p-4 bg-indigo-50 rounded-full text-indigo-600 mb-3 animate-pulse">
            <Activity className="w-8 h-8 animate-spin" />
          </div>
          <h3 className="text-sm font-bold text-slate-900">Loading public health intelligence...</h3>
          <p className="text-xs text-slate-500 mt-1">Aggregating historical records, computing trends, and building statistical forecast models</p>
        </div>
      )}

      {!loading && !isUnauthorized && (
        <>
          {/* 5. EXECUTIVE KPI SECTION */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Total Current Cases */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Current Period Cases</p>
                  <h3 className="text-2xl font-black text-slate-900 mt-1">
                    {trendsData?.summary.total_current_cases?.toLocaleString() ?? 0}
                  </h3>
                  <div className="flex items-center gap-1.5 mt-2 text-xs">
                    <span className="text-slate-500 text-[11px]">vs Previous:</span>
                    <span className="font-bold text-slate-700">{trendsData?.summary.total_previous_cases ?? 0}</span>
                    <span className="text-slate-300">•</span>
                    {renderPercentageBadge(trendsData?.summary.percentage_change)}
                  </div>
                </div>
                <div className="p-3 bg-indigo-50 rounded-xl text-indigo-600 border border-indigo-100">
                  <Activity className="w-5 h-5" />
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                <span className="text-[11px] font-semibold text-slate-500">Overall Trend Signal:</span>
                {renderTrendBadge(trendsData?.summary.overall_trend_direction)}
              </div>
            </div>

            {/* 7-Day Velocity */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">7-Day Case Velocity</p>
                  <h3 className="text-2xl font-black text-blue-900 mt-1">
                    {trendsData?.summary.total_7d_cases?.toLocaleString() ?? 0}
                  </h3>
                  <p className="text-[11px] text-blue-700 font-semibold mt-1">Trailing 7 days activity</p>
                </div>
                <div className="p-3 bg-blue-50 rounded-xl text-blue-600 border border-blue-100">
                  <Calendar className="w-5 h-5" />
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-slate-100 text-[11px] text-slate-500 font-medium">
                Recent acute patient presentation rate
              </div>
            </div>

            {/* 30-Day & 90-Day Accumulation */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">30-Day Cumulative</p>
                  <h3 className="text-2xl font-black text-slate-900 mt-1">
                    {trendsData?.summary.total_30d_cases?.toLocaleString() ?? 0}
                  </h3>
                  <div className="flex items-center gap-1.5 mt-1 text-xs">
                    <span className="text-[11px] text-slate-500 font-semibold">90-Day:</span>
                    <span className="font-bold text-slate-700">{trendsData?.summary.total_90d_cases?.toLocaleString() ?? 0}</span>
                  </div>
                </div>
                <div className="p-3 bg-purple-50 rounded-xl text-purple-600 border border-purple-100">
                  <BarChart3 className="w-5 h-5" />
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-slate-100 text-[11px] text-slate-500 font-medium">
                Medium and long-term transmission baseline
              </div>
            </div>

            {/* Monitored Diseases Scope */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Monitored Diseases</p>
                  <h3 className="text-2xl font-black text-teal-900 mt-1">
                    {trendsData?.summary.diseases_monitored_count ?? 0}
                  </h3>
                  <p className="text-[11px] text-teal-700 font-semibold mt-1">Active surveillance targets</p>
                </div>
                <div className="p-3 bg-teal-50 rounded-xl text-teal-600 border border-teal-100">
                  <Building2 className="w-5 h-5" />
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-slate-100 text-[11px] text-slate-500 font-medium truncate">
                Observation window: {trendsData?.summary.observation_period?.duration_days ?? 7} days
              </div>
            </div>
          </div>

          {/* 6. DISEASE TREND TABLE SECTION */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="p-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50/50">
              <div>
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-indigo-600" />
                  Disease Trend Analysis (Authoritative Step 1 Breakdown)
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Real disease totals, percentage change, and trend directions derived strictly from backend calculations.
                </p>
              </div>

              <div className="relative w-full sm:w-64">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Filter diseases..."
                  value={diseaseSearch}
                  onChange={e => setDiseaseSearch(e.target.value)}
                  className="w-full text-xs pl-8 pr-3 py-1.5 bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                  <tr>
                    <th className="p-4">Disease Condition</th>
                    <th className="p-4 text-center">Current</th>
                    <th className="p-4 text-center">Previous</th>
                    <th className="p-4 text-center">Change %</th>
                    <th className="p-4 text-center">Trend Signal</th>
                    <th className="p-4 text-center">7-Day</th>
                    <th className="p-4 text-center">30-Day</th>
                    <th className="p-4 text-center">90-Day</th>
                    <th className="p-4">Explanation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredDiseaseTrends.length === 0 ? (
                    <tr>
                      <td colSpan={9} className="p-8 text-center text-slate-400 font-medium">
                        No disease cases recorded for the selected scope and date.
                      </td>
                    </tr>
                  ) : (
                    filteredDiseaseTrends.map((item, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/80 transition">
                        <td className="p-4 font-bold text-slate-900 flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-indigo-500" />
                          {item.disease}
                        </td>
                        <td className="p-4 text-center font-bold text-slate-900 text-sm">
                          {item.current_cases}
                        </td>
                        <td className="p-4 text-center text-slate-600">
                          {item.previous_period_cases}
                        </td>
                        <td className="p-4 text-center">
                          {renderPercentageBadge(item.percentage_change)}
                        </td>
                        <td className="p-4 text-center">
                          {renderTrendBadge(item.trend_direction)}
                        </td>
                        <td className="p-4 text-center font-mono text-slate-700">
                          {item.cases_7d}
                        </td>
                        <td className="p-4 text-center font-mono text-slate-700">
                          {item.cases_30d}
                        </td>
                        <td className="p-4 text-center font-mono text-slate-700">
                          {item.cases_90d}
                        </td>
                        <td className="p-4 text-slate-600 text-[11px] max-w-xs">
                          {item.explanation}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* 7. DISEASE BY LOCALITY & WARD ANALYSIS */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="p-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50/50">
              <div>
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-rose-600" />
                  Disease Concentration by Locality & Ward
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Cases distributed across urban wards, slum pockets, and reporting hospitals.
                </p>
              </div>

              <div className="relative w-full sm:w-64">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Filter localities..."
                  value={localitySearch}
                  onChange={e => setLocalitySearch(e.target.value)}
                  className="w-full text-xs pl-8 pr-3 py-1.5 bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                  <tr>
                    <th className="p-4">Locality / Ward</th>
                    <th className="p-4 text-center">Current Cases</th>
                    <th className="p-4 text-center">Previous</th>
                    <th className="p-4 text-center">Change %</th>
                    <th className="p-4">Locality Share</th>
                    <th className="p-4 text-center">Trend Signal</th>
                    <th className="p-4">Reporting Hospitals</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredLocalities.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="p-8 text-center text-slate-400 font-medium">
                        No locality case concentrations observed in this window.
                      </td>
                    </tr>
                  ) : (
                    filteredLocalities.map((loc, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/80 transition">
                        <td className="p-4">
                          <div className="font-bold text-slate-900 flex items-center gap-2">
                            {loc.locality.ward_id === null ? (
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300">
                                Unknown Locality
                              </span>
                            ) : (
                              <span>{loc.locality.name}</span>
                            )}
                          </div>
                          {loc.locality.zone && (
                            <span className="text-[10px] text-slate-500 block mt-0.5">
                              Zone: {loc.locality.zone} {loc.locality.ward_number ? `• Ward #${loc.locality.ward_number}` : ''}
                            </span>
                          )}
                        </td>
                        <td className="p-4 text-center font-bold text-slate-900 text-sm">
                          {loc.current_cases}
                        </td>
                        <td className="p-4 text-center text-slate-600">
                          {loc.previous_period_cases}
                        </td>
                        <td className="p-4 text-center">
                          {renderPercentageBadge(loc.percentage_change)}
                        </td>
                        <td className="p-4 min-w-[140px]">
                          <div className="flex items-center justify-between text-[11px] font-bold text-slate-700 mb-1">
                            <span>{loc.locality_share_pct}%</span>
                          </div>
                          <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                            <div
                              className="bg-indigo-600 h-1.5 rounded-full"
                              style={{ width: `${Math.min(100, loc.locality_share_pct)}%` }}
                            />
                          </div>
                        </td>
                        <td className="p-4 text-center">
                          {renderTrendBadge(loc.trend_direction)}
                        </td>
                        <td className="p-4">
                          <div className="flex flex-wrap gap-1">
                            {loc.reporting_hospitals.map((h, hIdx) => (
                              <span
                                key={hIdx}
                                className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-[10px] font-medium border border-slate-200"
                                title={`Reported ${h.cases_reported} cases`}
                              >
                                {h.hospital_name} ({h.cases_reported})
                              </span>
                            ))}
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* 8. HISTORICAL DISEASE ANALYSIS */}
          {historicalData && (
            <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-blue-600" />
                    Historical Disease Trajectory ({historicalData.disease})
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Multi-month chronological series ({historicalData.months_analyzed} months) with severity distributions.
                  </p>
                </div>
                <div className="flex items-center gap-3 text-xs font-semibold text-slate-600">
                  <span>Current Month: <strong className="text-slate-900">{historicalData.current_month_cases}</strong></span>
                  <span>•</span>
                  <span>Prior Month: <strong className="text-slate-900">{historicalData.previous_month_cases}</strong></span>
                  <span>•</span>
                  {renderPercentageBadge(historicalData.percentage_change)}
                </div>
              </div>

              {/* Monthly Severity Breakdown Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                {historicalData.historical_series.map((item, idx) => (
                  <div key={idx} className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 flex flex-col justify-between">
                    <div>
                      <p className="text-[11px] font-bold text-slate-600 uppercase font-mono">{item.period_label}</p>
                      <h4 className="text-xl font-black text-slate-900 mt-1">{item.total_cases}</h4>
                    </div>
                    <div className="mt-3 pt-2 border-t border-slate-200/80 space-y-1 text-[10px]">
                      <div className="flex justify-between text-emerald-700 font-semibold">
                        <span>Mild:</span>
                        <span>{item.severity_breakdown.MILD}</span>
                      </div>
                      <div className="flex justify-between text-amber-700 font-semibold">
                        <span>Moderate:</span>
                        <span>{item.severity_breakdown.MODERATE}</span>
                      </div>
                      <div className="flex justify-between text-rose-700 font-semibold">
                        <span>Severe:</span>
                        <span>{item.severity_breakdown.SEVERE}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 9. FORECAST SECTION (Surveillance Signal) */}
          <div className="bg-gradient-to-br from-indigo-900 via-slate-900 to-indigo-950 rounded-2xl p-6 text-white shadow-md border border-indigo-800/50">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-indigo-800/60">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="px-2 py-0.5 rounded text-[10px] font-extrabold bg-indigo-500/20 text-indigo-300 border border-indigo-400/30 uppercase tracking-wider">
                    Forecast / Surveillance Signal
                  </span>
                  <span className="text-xs text-indigo-300 font-semibold">• Statistical Projection</span>
                </div>
                <h3 className="text-lg font-black tracking-tight flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-indigo-400" />
                  Primary Health Epidemiological Forecast ({forecastData?.disease || 'Selected Condition'})
                </h3>
                <p className="text-xs text-slate-300 mt-1 max-w-xl">
                  Baseline statistical projection for health resource planning and surveillance monitoring. Not a confirmed outbreak prediction.
                </p>
              </div>

              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-300">Method:</span>
                <span className="px-2.5 py-1 bg-white/10 rounded-lg text-indigo-200 font-mono font-bold text-[11px] border border-white/10">
                  {forecastData?.forecast.method || 'WEIGHTED_MOVING_AVERAGE'}
                </span>
              </div>
            </div>

            {/* Forecast Body */}
            {forecastData?.forecast.status === 'INSUFFICIENT_DATA' ? (
              <div className="my-6 p-6 rounded-xl bg-white/5 border border-white/10 text-center">
                <HelpCircle className="w-8 h-8 text-amber-400 mx-auto mb-2 opacity-80" />
                <h4 className="text-sm font-bold text-slate-100">
                  Insufficient historical surveillance data for a reliable forecast.
                </h4>
                <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto font-medium">
                  {forecastData.forecast.explanation || 'A minimum observation baseline of at least 3 cases is required to construct a valid statistical forecast model.'}
                </p>
              </div>
            ) : (
              <div className="mt-5 space-y-4">
                {/* Explanation Banner */}
                <div className="p-3.5 bg-indigo-950/60 rounded-xl border border-indigo-700/40 text-xs text-indigo-200 flex items-start gap-2.5">
                  <Info className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                  <span>{forecastData?.forecast.explanation}</span>
                </div>

                {/* Forecast Weekly Horizon Points */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                  {forecastData?.forecast.points.map((pt, idx) => (
                    <div key={idx} className="bg-white/10 backdrop-blur-md p-4 rounded-xl border border-white/10">
                      <div className="flex justify-between items-center text-[10px] font-bold text-indigo-300 uppercase font-mono">
                        <span>Week +{idx + 1}</span>
                        <span>{pt.forecast_week_start}</span>
                      </div>
                      <div className="mt-2">
                        <span className="text-[10px] text-slate-400 block font-semibold">Predicted Volume</span>
                        <div className="text-2xl font-black text-white mt-0.5">
                          {pt.predicted_cases}
                          <span className="text-xs text-indigo-300 font-normal ml-1">cases</span>
                        </div>
                      </div>
                      <div className="mt-3 pt-2 border-t border-white/10 flex justify-between items-center text-[11px] font-mono">
                        <span className="text-slate-400">Range:</span>
                        <span className="text-indigo-200 font-bold">
                          [{pt.lower_bound} — {pt.upper_bound}]
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* 10. SEASONAL PATTERN SECTION */}
          {seasonalityData && (
            <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-emerald-600" />
                    Seasonal Pattern Analysis ({seasonalityData.disease})
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Calendar-month historical case distributions and seasonal clustering signals.
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-500">Pattern Status:</span>
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[11px] font-extrabold border ${
                      seasonalityData.seasonal_status === 'DETECTED'
                        ? 'bg-amber-100 text-amber-900 border-amber-300'
                        : seasonalityData.seasonal_status === 'WEAK'
                        ? 'bg-blue-100 text-blue-900 border-blue-300'
                        : 'bg-slate-100 text-slate-700 border-slate-300'
                    }`}
                  >
                    {seasonalityData.seasonal_status}
                  </span>
                </div>
              </div>

              {seasonalityData.seasonal_status === 'NOT_ENOUGH_DATA' ? (
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-600 text-center">
                  <p className="font-semibold text-slate-800">{seasonalityData.explanation}</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Summary Metric Cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                      <p className="text-[10px] font-bold text-slate-500 uppercase">Seasonal Strength Index</p>
                      <h4 className="text-xl font-black text-slate-900 mt-1">{seasonalityData.seasonal_strength}</h4>
                      <p className="text-[10px] text-slate-400 mt-0.5">Normalized variation metric [0.0 - 1.0]</p>
                    </div>

                    <div className="bg-rose-50/60 p-3.5 rounded-xl border border-rose-200">
                      <p className="text-[10px] font-bold text-rose-700 uppercase">Highest Case Month</p>
                      <h4 className="text-xl font-black text-rose-950 mt-1">
                        {seasonalityData.highest_case_month?.month_name || 'N/A'}
                      </h4>
                      <p className="text-[10px] text-rose-700 mt-0.5 font-semibold">
                        Averaging {seasonalityData.highest_case_month?.average_cases ?? 0} cases / month
                      </p>
                    </div>

                    <div className="bg-emerald-50/60 p-3.5 rounded-xl border border-emerald-200">
                      <p className="text-[10px] font-bold text-emerald-700 uppercase">Lowest Case Month</p>
                      <h4 className="text-xl font-black text-emerald-950 mt-1">
                        {seasonalityData.lowest_case_month?.month_name || 'N/A'}
                      </h4>
                      <p className="text-[10px] text-emerald-700 mt-0.5 font-semibold">
                        Averaging {seasonalityData.lowest_case_month?.average_cases ?? 0} cases / month
                      </p>
                    </div>
                  </div>

                  {/* Monthly Pattern Bar Cards */}
                  <div>
                    <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                      Calendar Month Historical Distribution
                    </h4>
                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
                      {seasonalityData.monthly_patterns.map((m, idx) => (
                        <div key={idx} className="p-2.5 bg-slate-50 rounded-lg border border-slate-200 text-center">
                          <p className="text-[11px] font-bold text-slate-700">{m.month_name}</p>
                          <p className="text-base font-black text-slate-900 mt-0.5">{m.average_cases}</p>
                          <p className="text-[10px] text-slate-500 font-mono mt-0.5">
                            Total: {m.total_cases} ({m.occurrences}x)
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 11. HOSPITAL COMPARISON SECTION (District Officer Scope Only) */}
          {isDistrictOfficer && districtAggData && (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
              <div className="p-5 border-b border-slate-100 bg-slate-50/50">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-emerald-600" />
                  District Hospital Case Comparison ({districtAggData.district.name})
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Comparative disease reporting volume across all authorized facilities within {districtAggData.district.name}.
                </p>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                    <tr>
                      <th className="p-4">Hospital Name</th>
                      <th className="p-4">Facility Code</th>
                      <th className="p-4">Facility Type</th>
                      <th className="p-4 text-right">Cases Reported</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {districtAggData.hospital_comparison.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="p-6 text-center text-slate-400 font-medium">
                          No hospital records found in this district.
                        </td>
                      </tr>
                    ) : (
                      districtAggData.hospital_comparison.map((hosp, idx) => (
                        <tr key={idx} className="hover:bg-slate-50/80 transition">
                          <td className="p-4 font-bold text-slate-900 flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
                            {hosp.hospital_name}
                          </td>
                          <td className="p-4 font-mono text-slate-600">{hosp.hospital_code}</td>
                          <td className="p-4 text-slate-700">{hosp.facility_type}</td>
                          <td className="p-4 text-right font-black text-slate-900 text-sm">
                            {hosp.cases_reported}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default PublicHealthIntelligence;
