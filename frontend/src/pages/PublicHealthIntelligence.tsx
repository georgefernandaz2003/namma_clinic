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
  Info,
  Bell,
  CheckCircle2,
  X,
  ExternalLink,
  ShieldCheck,
  Filter,
  RotateCcw,
  Users
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useConfirm } from '../context/ConfirmContext';
import { hasPermission } from '../utils/permissions';
import intelligenceService from '../services/intelligenceService';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';
import type {
  TrendDirection,
  DiseaseTrendsResponse,
  DiseaseLocalityResponse,
  HistoricalDiseaseResponse,
  ForecastSummaryResponse,
  SeasonalityData,
  DistrictAggregationResponse,
  IntelligenceFilterParams,
  IntelligenceAlert,
  AlertSeverity,
  AlertStatus,
  ForecastRiskData,
  ForecastRiskPoint,
  ForecastRiskLevel,
  PatientTypeFilter
} from '../types/intelligence';

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
  const defaultFilters = useMemo(() => ({
    date: todayStr,
    disease: 'All Monitored Conditions',
    facility: userAssignedFacilityId ? String(userAssignedFacilityId) : '',
    district: userAssignedDistrictId ? String(userAssignedDistrictId) : '',
    age_group: '',
    gender: '',
    severity: '',
    vulnerable_group: '',
    patient_type: '' as '' | 'NEW' | 'FOLLOW_UP',
    weeks: 4,
    months: 12,
  }), [todayStr, userAssignedFacilityId, userAssignedDistrictId]);

  const [filters, setFilters] = useState(defaultFilters);

  // Sync role-assigned facility/district if auth loaded asynchronously
  useEffect(() => {
    setFilters(prev => ({
      ...prev,
      facility: prev.facility || (userAssignedFacilityId ? String(userAssignedFacilityId) : ''),
      district: prev.district || (userAssignedDistrictId ? String(userAssignedDistrictId) : ''),
    }));
  }, [userAssignedFacilityId, userAssignedDistrictId]);

  const updateFilter = useCallback(<K extends keyof typeof defaultFilters>(
    key: K,
    val: (typeof defaultFilters)[K]
  ) => {
    setFilters(prev => ({ ...prev, [key]: val }));
  }, []);

  const handleResetFilters = useCallback(() => {
    setFilters(defaultFilters);
  }, [defaultFilters]);

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

  // Step 4: Surveillance Alerts & Signals State
  const { confirm } = useConfirm();
  const [alerts, setAlerts] = useState<IntelligenceAlert[]>([]);
  const [alertsLoading, setAlertsLoading] = useState<boolean>(false);
  const [evaluatingAlerts, setEvaluatingAlerts] = useState<boolean>(false);
  const [evaluationFeedback, setEvaluationFeedback] = useState<string | null>(null);
  const [selectedAlert, setSelectedAlert] = useState<IntelligenceAlert | null>(null);
  const [alertStatusFilter, setAlertStatusFilter] = useState<'ALL' | 'NEW' | 'ACKNOWLEDGED' | 'RESOLVED'>('ALL');

  // Request race condition prevention
  const activeRequestIdRef = useRef<number>(0);

  // Centralized Alerts Fetcher
  const loadAlerts = useCallback(async () => {
    setAlertsLoading(true);
    const effectiveFacility = (isHospitalAdmin || isDoctorOrNurse)
      ? userAssignedFacilityId || undefined
      : filters.facility ? Number(filters.facility) : undefined;

    const effectiveDistrict = isDistrictOfficer
      ? userAssignedDistrictId || undefined
      : filters.district ? Number(filters.district) : undefined;

    try {
      const res = await intelligenceService.getAlerts({
        facility: effectiveFacility,
        district: effectiveDistrict,
        date: filters.date || undefined,
      });
      setAlerts(res.results || []);
    } catch {
      // silent fallback
    } finally {
      setAlertsLoading(false);
    }
  }, [
    isHospitalAdmin,
    isDoctorOrNurse,
    isDistrictOfficer,
    userAssignedFacilityId,
    userAssignedDistrictId,
    filters.facility,
    filters.district,
    filters.date
  ]);

  // Centralized Data Fetcher
  const fetchIntelligenceData = useCallback(async () => {
    const currentReqId = ++activeRequestIdRef.current;
    setLoading(true);
    setErrorMessage(null);
    setIsUnauthorized(false);

    // Compute effective params strictly respecting role boundaries
    const effectiveFacility = (isHospitalAdmin || isDoctorOrNurse)
      ? userAssignedFacilityId || undefined
      : filters.facility ? Number(filters.facility) : undefined;

    const effectiveDistrict = isDistrictOfficer
      ? userAssignedDistrictId || undefined
      : filters.district ? Number(filters.district) : undefined;

    const effectiveDisease = filters.disease === 'All Monitored Conditions' ? undefined : filters.disease;

    const queryParams: IntelligenceFilterParams = {
      facility: effectiveFacility,
      district: effectiveDistrict,
      disease: effectiveDisease,
      date: filters.date || undefined,
      weeks: filters.weeks,
      months: filters.months,
      age_group: filters.age_group || undefined,
      gender: filters.gender || undefined,
      severity: filters.severity || undefined,
      vulnerable_group: filters.vulnerable_group || undefined,
      patient_type: filters.patient_type || undefined,
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
      const apiErr = err as { response?: { status?: number; data?: { error?: string; detail?: string } } };
      if (apiErr.response?.status === 403) {
        setIsUnauthorized(true);
        setErrorMessage(apiErr.response?.data?.error || apiErr.response?.data?.detail || 'Access denied: You do not have authorization for this facility or district scope.');
      } else if (apiErr.response?.status === 400) {
        setErrorMessage(apiErr.response?.data?.error || apiErr.response?.data?.detail || 'Invalid filter parameters submitted. Please adjust your filter selections.');
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
    filters
  ]);

  useEffect(() => {
    fetchIntelligenceData();
    loadAlerts();
  }, [fetchIntelligenceData, loadAlerts]);

  // Step 4 Handlers: Manual Evaluation, Acknowledge, Resolve
  const canEvaluateSignals = isDistrictOfficer || isHospitalAdmin || isDoctorOrNurse;

  const handleEvaluateSignals = async () => {
    if (!canEvaluateSignals) return;
    setEvaluatingAlerts(true);
    setEvaluationFeedback(null);
    try {
      const effectiveFacility = (isHospitalAdmin || isDoctorOrNurse)
        ? userAssignedFacilityId || undefined
        : filters.facility ? Number(filters.facility) : undefined;

      const effectiveDistrict = isDistrictOfficer
        ? userAssignedDistrictId || undefined
        : filters.district ? Number(filters.district) : undefined;

      const res = await intelligenceService.evaluateAlerts({
        facility: effectiveFacility,
        district: effectiveDistrict,
        date: filters.date || undefined,
      });
      setEvaluationFeedback(
        `Evaluation complete: ${res.created_count} new signal(s) created, ${res.updated_count} existing signal(s) updated.`
      );
      await loadAlerts();
    } catch (err: unknown) {
      const apiErr = err as { response?: { data?: { error?: string } } };
      setEvaluationFeedback(apiErr.response?.data?.error || 'Failed to evaluate surveillance signals.');
    } finally {
      setEvaluatingAlerts(false);
    }
  };

  const handleAcknowledgeAlert = (alertItem: IntelligenceAlert) => {
    confirm({
      title: 'Acknowledge Surveillance Signal',
      message: 'Are you sure you want to mark this surveillance alert as acknowledged? This signals that an authorized human reviewer has inspected the data.',
      confirmText: 'Acknowledge Signal',
      cancelText: 'Cancel',
      variant: 'warning',
      loadingText: 'Acknowledging Signal...',
      details: [
        { label: 'Signal Title', value: alertItem.title },
        { label: 'Severity', value: alertItem.severity },
        { label: 'Disease', value: alertItem.metadata?.disease || 'Monitored Disease' },
        { label: 'Facility', value: alertItem.facility_name || String(alertItem.facility) },
        { label: 'Observation Date', value: alertItem.metadata?.observation_date || alertItem.created_at },
      ],
      onConfirm: async () => {
        await intelligenceService.acknowledgeAlert(alertItem.id);
        await loadAlerts();
        if (selectedAlert?.id === alertItem.id) {
          setSelectedAlert(prev => prev ? { ...prev, status: 'ACKNOWLEDGED' } : null);
        }
      },
    });
  };

  const handleResolveAlert = (alertItem: IntelligenceAlert) => {
    confirm({
      title: 'Resolve Surveillance Signal',
      message: 'Are you sure you want to mark this surveillance signal as resolved? Resolution indicates review and appropriate clinical/public health actions are complete.',
      confirmText: 'Resolve Signal',
      cancelText: 'Cancel',
      variant: 'danger',
      loadingText: 'Resolving Signal...',
      details: [
        { label: 'Signal Title', value: alertItem.title },
        { label: 'Severity', value: alertItem.severity },
        { label: 'Disease', value: alertItem.metadata?.disease || 'Monitored Disease' },
        { label: 'Facility', value: alertItem.facility_name || String(alertItem.facility) },
        { label: 'Resolution Note', value: 'Surveillance signal reviewed and addressed' },
      ],
      onConfirm: async () => {
        await intelligenceService.resolveAlert(alertItem.id, 'Surveillance signal reviewed and addressed');
        await loadAlerts();
        if (selectedAlert?.id === alertItem.id) {
          setSelectedAlert(prev => prev ? { ...prev, status: 'RESOLVED' } : null);
        }
      },
    });
  };

  const filteredAlerts = useMemo(() => {
    if (alertStatusFilter === 'ALL') return alerts;
    return alerts.filter(a => a.status === alertStatusFilter);
  }, [alerts, alertStatusFilter]);

  const alertCounts = useMemo(() => {
    return {
      all: alerts.length,
      open: alerts.filter(a => a.status === 'NEW').length,
      acknowledged: alerts.filter(a => a.status === 'ACKNOWLEDGED').length,
      resolved: alerts.filter(a => a.status === 'RESOLVED').length,
    };
  }, [alerts]);

  const renderAlertSeverityBadge = (severity: AlertSeverity | string) => {
    switch (severity) {
      case 'CRITICAL':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black tracking-wide bg-rose-100 text-rose-800 border border-rose-300 flex items-center gap-1 shadow-xs">
            <AlertTriangle className="w-3 h-3 text-rose-600" /> CRITICAL
          </span>
        );
      case 'WARNING':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black tracking-wide bg-amber-100 text-amber-800 border border-amber-300 flex items-center gap-1 shadow-xs">
            <AlertTriangle className="w-3 h-3 text-amber-600" /> WARNING
          </span>
        );
      case 'INFO':
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black tracking-wide bg-blue-100 text-blue-800 border border-blue-300 flex items-center gap-1 shadow-xs">
            <Info className="w-3 h-3 text-blue-600" /> INFO
          </span>
        );
    }
  };

  const renderAlertStatusBadge = (statusVal: AlertStatus | string) => {
    switch (statusVal) {
      case 'NEW':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" /> OPEN
          </span>
        );
      case 'ACKNOWLEDGED':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-amber-100 text-amber-800 border border-amber-300 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-amber-600" /> ACKNOWLEDGED
          </span>
        );
      case 'RESOLVED':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-slate-100 text-slate-700 border border-slate-300 flex items-center gap-1">
            <ShieldCheck className="w-3 h-3 text-slate-500" /> RESOLVED
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-slate-100 text-slate-700 border border-slate-300">
            {statusVal}
          </span>
        );
    }
  };

  const getSignalTypeDisplay = (alertType: string, metaSignal?: string) => {
    const raw = metaSignal || alertType;
    if (raw === 'DISEASE_TREND' || raw === 'INTELLIGENCE_TREND' || raw === 'DISEASE_TREND_INCREASING') return 'Increasing Disease Trend';
    if (raw === 'DISEASE_TREND_POSSIBLE_INCREASE') return 'Possible Disease Trend Increase';
    if (raw === 'HIGH_LOCALITY_CONCENTRATION' || raw === 'INTELLIGENCE_LOCALITY') return 'High Locality Concentration';
    if (raw === 'FORECAST_SURVEILLANCE_SIGNAL' || raw === 'INTELLIGENCE_FORECAST') return 'Forecast Surveillance Signal';
    if (raw === 'SEASONAL_SURVEILLANCE_SIGNAL' || raw === 'INTELLIGENCE_SEASONALITY') return 'Seasonal Surveillance Signal';
    return raw;
  };

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

  // Dynamic disease options derived strictly from backend response
  const diseaseOptions = useMemo(() => {
    const list: string[] = ['All Monitored Conditions'];
    const seen = new Set<string>(['All Monitored Conditions']);

    if (trendsData?.disease_trends) {
      for (const item of trendsData.disease_trends) {
        if (item.disease && !seen.has(item.disease)) {
          seen.add(item.disease);
          list.push(item.disease);
        }
      }
    }

    // Preserve active selection if not yet in list
    if (filters.disease && !seen.has(filters.disease)) {
      list.push(filters.disease);
    }

    return list;
  }, [trendsData, filters.disease]);

  // Historical chart data mapped directly from backend historical_series
  const historicalChartData = useMemo(() => {
    if (!historicalData?.historical_series) return [];
    return historicalData.historical_series.map(pt => ({
      period_label: pt.period_label,
      total_cases: pt.total_cases,
      MILD: pt.severity_breakdown?.MILD ?? 0,
      MODERATE: pt.severity_breakdown?.MODERATE ?? 0,
      SEVERE: pt.severity_breakdown?.SEVERE ?? 0,
    }));
  }, [historicalData]);

  // Demographic filter presence check
  const hasActiveDemographicFilters = Boolean(
    filters.age_group ||
    filters.gender ||
    filters.severity ||
    filters.vulnerable_group ||
    filters.patient_type
  );

  const hasAnyCustomFilters = Boolean(
    filters.disease !== 'All Monitored Conditions' ||
    filters.facility !== (userAssignedFacilityId ? String(userAssignedFacilityId) : '') ||
    filters.date !== todayStr ||
    filters.weeks !== 4 ||
    filters.months !== 12 ||
    hasActiveDemographicFilters
  );

  // Authoritative observation population count for transparency
  const totalPopulationCases = useMemo(() => {
    if (forecastData?.observation_period?.total_cases !== undefined) {
      return forecastData.observation_period.total_cases;
    }
    if (trendsData?.summary?.total_current_cases !== undefined) {
      return trendsData.summary.total_current_cases;
    }
    if (historicalData?.total_cases_in_history !== undefined) {
      return historicalData.total_cases_in_history;
    }
    return 0;
  }, [forecastData, trendsData, historicalData]);

  // Authoritative visual risk level badge with explicit text representation
  const renderRiskLevelBadge = (level?: ForecastRiskLevel | string) => {
    switch (level) {
      case 'HIGH_RISK':
        return (
          <span
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black tracking-wide bg-rose-500/20 text-rose-300 border border-rose-400/40 shadow-xs"
            aria-label="HIGH RISK"
            title="HIGH RISK"
          >
            <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
            <span>HIGH RISK</span>
          </span>
        );
      case 'ELEVATED':
        return (
          <span
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black tracking-wide bg-amber-500/20 text-amber-300 border border-amber-400/40 shadow-xs"
            aria-label="ELEVATED"
            title="ELEVATED"
          >
            <TrendingUp className="w-3.5 h-3.5 text-amber-400" />
            <span>ELEVATED</span>
          </span>
        );
      case 'NORMAL':
        return (
          <span
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black tracking-wide bg-emerald-500/20 text-emerald-300 border border-emerald-400/40 shadow-xs"
            aria-label="NORMAL"
            title="NORMAL"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>NORMAL</span>
          </span>
        );
      case 'INSUFFICIENT_DATA':
      default:
        return (
          <span
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black tracking-wide bg-slate-500/20 text-slate-300 border border-slate-400/40 shadow-xs"
            aria-label="INSUFFICIENT DATA"
            title="INSUFFICIENT DATA"
          >
            <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
            <span>INSUFFICIENT DATA</span>
          </span>
        );
    }
  };

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
              {filters.facility && ` (${availableFacilities.find(f => f.id === Number(filters.facility))?.facility_name || `Facility #${filters.facility}`})`}
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
            As-of Date: {filters.date}
          </span>
        </div>
      </div>

      {/* FILTER BAR */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-600" />
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Surveillance Intelligence Filters
            </h2>
            <span className="text-[11px] text-slate-500 font-normal hidden sm:inline">
              (All sections strictly synchronized with AND logic)
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              id="reset-filters-btn"
              onClick={handleResetFilters}
              className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition flex items-center gap-1.5 border border-slate-200 shadow-2xs"
              aria-label="Reset Filters"
            >
              <RotateCcw className="w-3.5 h-3.5 text-slate-500" />
              <span>Reset Filters</span>
            </button>
          </div>
        </div>

        {/* Primary Scope Filters (Row 1) */}
        <div>
          <span className="text-[10px] font-black uppercase tracking-wider text-slate-400 block mb-2">
            Primary Scope & Horizon
          </span>
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
                  value={filters.date}
                  onChange={e => updateFilter('date', e.target.value)}
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
                value={filters.disease}
                onChange={e => updateFilter('disease', e.target.value)}
                className="w-full text-xs font-medium bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                {diseaseOptions.map(d => (
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
                  value={filters.facility}
                  onChange={e => updateFilter('facility', e.target.value)}
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
                value={filters.weeks}
                onChange={e => updateFilter('weeks', Number(e.target.value))}
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
                value={filters.months}
                onChange={e => updateFilter('months', Number(e.target.value))}
                className="w-full text-xs font-medium bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value={6}>Past 6 Months</option>
                <option value={12}>Past 12 Months (1 Year)</option>
                <option value={24}>Past 24 Months (2 Years)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Demographic & Clinical Cohort Filters (Row 2) */}
        <div className="pt-3 border-t border-slate-100">
          <span className="text-[10px] font-black uppercase tracking-wider text-slate-400 block mb-2">
            Demographic, Clinical & Vulnerability Cohorts
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            {/* 6. Age Group */}
            <div>
              <label htmlFor="age-group-filter-select" className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
                Age Group
              </label>
              <select
                id="age-group-filter-select"
                value={filters.age_group}
                onChange={e => updateFilter('age_group', e.target.value)}
                className="w-full text-xs font-medium bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="">All Age Groups</option>
                <option value="0-5">0-5</option>
                <option value="6-14">6-14</option>
                <option value="15-24">15-24</option>
                <option value="25-44">25-44</option>
                <option value="45-59">45-59</option>
                <option value="60+">60+</option>
              </select>
            </div>

            {/* 7. Gender */}
            <div>
              <label htmlFor="gender-filter-select" className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
                Gender
              </label>
              <select
                id="gender-filter-select"
                value={filters.gender}
                onChange={e => updateFilter('gender', e.target.value)}
                className="w-full text-xs font-medium bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="">All Genders</option>
                <option value="MALE">MALE</option>
                <option value="FEMALE">FEMALE</option>
                <option value="OTHER">OTHER</option>
              </select>
            </div>

            {/* 8. Severity */}
            <div>
              <label htmlFor="severity-filter-select" className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
                Severity
              </label>
              <select
                id="severity-filter-select"
                value={filters.severity}
                onChange={e => updateFilter('severity', e.target.value)}
                className="w-full text-xs font-medium bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="">All Severities</option>
                <option value="MILD">MILD</option>
                <option value="MODERATE">MODERATE</option>
                <option value="SEVERE">SEVERE</option>
              </select>
            </div>

            {/* 9. Vulnerable Group */}
            <div>
              <label htmlFor="vulnerable-group-filter-select" className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
                Vulnerable Group
              </label>
              <select
                id="vulnerable-group-filter-select"
                value={filters.vulnerable_group}
                onChange={e => updateFilter('vulnerable_group', e.target.value)}
                className="w-full text-xs font-medium bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="">All Vulnerable Groups</option>
                <option value="PREGNANT">PREGNANT</option>
                <option value="ELDERLY">ELDERLY</option>
                <option value="DISABILITY">DISABILITY</option>
                <option value="CHRONIC_CONDITION">CHRONIC_CONDITION</option>
                <option value="LOW_INCOME_SLUM">LOW_INCOME_SLUM</option>
                <option value="GENERAL">GENERAL</option>
              </select>
            </div>

            {/* 10. Patient Type */}
            <div>
              <label htmlFor="patient-type-filter-select" className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
                Patient Type
              </label>
              <select
                id="patient-type-filter-select"
                value={filters.patient_type}
                onChange={e => updateFilter('patient_type', e.target.value as '' | 'NEW' | 'FOLLOW_UP')}
                className="w-full text-xs font-medium bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="">All Patient Types</option>
                <option value="NEW">NEW</option>
                <option value="FOLLOW_UP">FOLLOW_UP</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Active Demographic / Population Filter Summary */}
      <div
        className="bg-indigo-50/70 border border-indigo-200/80 rounded-2xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-xs"
        data-testid="active-demographic-summary"
        aria-label="Active Demographic Cohort Summary"
      >
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="font-bold text-indigo-950 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
            <Filter className="w-3.5 h-3.5 text-indigo-600" />
            Selected population:
          </span>
          {hasActiveDemographicFilters ? (
            <div className="flex flex-wrap items-center gap-1.5" data-testid="selected-population-tags">
              {filters.age_group && (
                <span className="px-2.5 py-1 bg-white border border-indigo-200 text-indigo-900 rounded-lg font-semibold flex items-center gap-1 shadow-2xs">
                  Age: <strong className="font-black">{filters.age_group}</strong>
                  <button
                    onClick={() => updateFilter('age_group', '')}
                    className="ml-1 text-slate-400 hover:text-rose-600 focus:outline-none"
                    aria-label="Clear age group filter"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}
              {filters.gender && (
                <span className="px-2.5 py-1 bg-white border border-indigo-200 text-indigo-900 rounded-lg font-semibold flex items-center gap-1 shadow-2xs">
                  Gender: <strong className="font-black">{filters.gender === 'MALE' ? 'Male' : filters.gender === 'FEMALE' ? 'Female' : 'Other'}</strong>
                  <button
                    onClick={() => updateFilter('gender', '')}
                    className="ml-1 text-slate-400 hover:text-rose-600 focus:outline-none"
                    aria-label="Clear gender filter"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}
              {filters.severity && (
                <span className="px-2.5 py-1 bg-white border border-indigo-200 text-indigo-900 rounded-lg font-semibold flex items-center gap-1 shadow-2xs">
                  Severity: <strong className="font-black">{filters.severity === 'MILD' ? 'Mild' : filters.severity === 'MODERATE' ? 'Moderate' : 'Severe'}</strong>
                  <button
                    onClick={() => updateFilter('severity', '')}
                    className="ml-1 text-slate-400 hover:text-rose-600 focus:outline-none"
                    aria-label="Clear severity filter"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}
              {filters.vulnerable_group && (
                <span className="px-2.5 py-1 bg-white border border-indigo-200 text-indigo-900 rounded-lg font-semibold flex items-center gap-1 shadow-2xs">
                  Vulnerable Group: <strong className="font-black">{
                    filters.vulnerable_group === 'PREGNANT' ? 'Pregnant' :
                    filters.vulnerable_group === 'ELDERLY' ? 'Elderly' :
                    filters.vulnerable_group === 'DISABILITY' ? 'Disability' :
                    filters.vulnerable_group === 'CHRONIC_CONDITION' ? 'Chronic Condition' :
                    filters.vulnerable_group === 'LOW_INCOME_SLUM' ? 'Low Income / Slum' : 'General'
                  }</strong>
                  <button
                    onClick={() => updateFilter('vulnerable_group', '')}
                    className="ml-1 text-slate-400 hover:text-rose-600 focus:outline-none"
                    aria-label="Clear vulnerable group filter"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}
              {filters.patient_type && (
                <span className="px-2.5 py-1 bg-white border border-indigo-200 text-indigo-900 rounded-lg font-semibold flex items-center gap-1 shadow-2xs">
                  Patient Type: <strong className="font-black">{filters.patient_type === 'NEW' ? 'New' : 'Follow-up'}</strong>
                  <button
                    onClick={() => updateFilter('patient_type', '')}
                    className="ml-1 text-slate-400 hover:text-rose-600 focus:outline-none"
                    aria-label="Clear patient type filter"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}
            </div>
          ) : (
            <span className="text-slate-600 italic">
              All eligible population
            </span>
          )}
        </div>

        {/* Observation Population Transparency */}
        <div className="flex items-center gap-3 text-xs">
          <div className="font-semibold text-slate-700 font-mono">
            {totalPopulationCases > 0 ? (
              <span className="text-indigo-900 bg-white px-3 py-1.5 rounded-lg border border-indigo-200 shadow-2xs">
                Cases in selected population: <strong className="font-black text-indigo-950">{totalPopulationCases}</strong>
              </span>
            ) : (
              <span className="text-amber-800 bg-amber-50 px-3 py-1.5 rounded-lg border border-amber-200 font-medium">
                No cases found for the selected filters.
              </span>
            )}
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

          {/* STEP 4: SURVEILLANCE ALERTS & ACTION LAYER */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden" data-testid="surveillance-alerts-panel">
            <div className="p-5 border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-50/50">
              <div>
                <div className="flex items-center gap-2">
                  <span className="p-1.5 rounded-lg bg-amber-100 text-amber-800 border border-amber-200">
                    <Bell className="w-4 h-4 text-amber-700" />
                  </span>
                  <h3 className="text-sm font-bold text-slate-900">
                    Surveillance Alerts & Signals
                  </h3>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-indigo-100 text-indigo-800 border border-indigo-200">
                    Step 4
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Actionable, human-reviewable surveillance alerts derived strictly from authoritative database signals.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                {/* Status Filter Pills */}
                <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs">
                  <button
                    onClick={() => setAlertStatusFilter('ALL')}
                    className={`px-2.5 py-1 rounded-lg font-bold transition cursor-pointer ${
                      alertStatusFilter === 'ALL'
                        ? 'bg-white text-slate-900 shadow-xs'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    All ({alertCounts.all})
                  </button>
                  <button
                    onClick={() => setAlertStatusFilter('NEW')}
                    className={`px-2.5 py-1 rounded-lg font-bold transition cursor-pointer ${
                      alertStatusFilter === 'NEW'
                        ? 'bg-white text-emerald-800 shadow-xs'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Open ({alertCounts.open})
                  </button>
                  <button
                    onClick={() => setAlertStatusFilter('ACKNOWLEDGED')}
                    className={`px-2.5 py-1 rounded-lg font-bold transition cursor-pointer ${
                      alertStatusFilter === 'ACKNOWLEDGED'
                        ? 'bg-white text-amber-800 shadow-xs'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Ack ({alertCounts.acknowledged})
                  </button>
                  <button
                    onClick={() => setAlertStatusFilter('RESOLVED')}
                    className={`px-2.5 py-1 rounded-lg font-bold transition cursor-pointer ${
                      alertStatusFilter === 'RESOLVED'
                        ? 'bg-white text-slate-800 shadow-xs'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Resolved ({alertCounts.resolved})
                  </button>
                </div>

                {/* Evaluate Surveillance Signals Action */}
                {canEvaluateSignals && (
                  <button
                    onClick={handleEvaluateSignals}
                    disabled={evaluatingAlerts}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition cursor-pointer disabled:opacity-60 shadow-xs"
                    data-testid="evaluate-signals-btn"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${evaluatingAlerts ? 'animate-spin' : ''}`} />
                    <span>{evaluatingAlerts ? 'Evaluating Signals...' : 'Evaluate Surveillance Signals'}</span>
                  </button>
                )}
              </div>
            </div>

            {/* Evaluation Feedback Banner */}
            {evaluationFeedback && (
              <div className="px-5 py-2.5 bg-indigo-50 border-b border-indigo-100 flex items-center justify-between text-xs text-indigo-900">
                <span className="font-semibold flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                  {evaluationFeedback}
                </span>
                <button
                  onClick={() => setEvaluationFeedback(null)}
                  className="text-indigo-400 hover:text-indigo-700 cursor-pointer"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            )}

            {/* Alerts List */}
            <div className="p-5">
              {alertsLoading ? (
                <div className="py-8 text-center text-xs text-slate-500 font-medium flex items-center justify-center gap-2">
                  <Activity className="w-4 h-4 animate-spin text-indigo-600" />
                  Loading surveillance alerts...
                </div>
              ) : filteredAlerts.length === 0 ? (
                <div className="py-8 text-center text-slate-400 font-medium text-xs">
                  <ShieldCheck className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-80" />
                  No surveillance alerts matching the current filters.
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {filteredAlerts.map(alert => (
                    <div
                      key={alert.id}
                      className={`p-4 rounded-xl border transition flex flex-col justify-between gap-3 shadow-xs ${
                        alert.severity === 'CRITICAL'
                          ? 'bg-rose-50/60 border-rose-200'
                          : alert.severity === 'WARNING'
                          ? 'bg-amber-50/60 border-amber-200'
                          : 'bg-slate-50/60 border-slate-200'
                      }`}
                      data-testid={`alert-card-${alert.id}`}
                    >
                      <div className="space-y-2">
                        {/* Header Badges */}
                        <div className="flex items-center justify-between gap-2 flex-wrap">
                          <div className="flex items-center gap-1.5">
                            {renderAlertSeverityBadge(alert.severity)}
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-white text-slate-700 border border-slate-200">
                              {getSignalTypeDisplay(alert.alert_type, alert.metadata?.signal_type)}
                            </span>
                          </div>
                          {renderAlertStatusBadge(alert.status)}
                        </div>

                        {/* Title & Scope */}
                        <div>
                          <h4 className="font-bold text-slate-900 text-sm">
                            {alert.metadata?.disease || alert.title}
                          </h4>
                          <p className="text-[11px] text-slate-500 font-medium flex items-center gap-1 mt-0.5">
                            <MapPin className="w-3 h-3 text-slate-400 shrink-0" />
                            {alert.metadata?.locality ? `${alert.metadata.locality} • ` : ''}
                            {alert.facility_name || `Facility #${alert.facility}`}
                            {alert.metadata?.observation_date && (
                              <span className="ml-1 text-slate-400">• Obs: {alert.metadata.observation_date}</span>
                            )}
                          </p>
                        </div>

                        {/* Metrics Summary Strip */}
                        {alert.metadata && (
                          <div className="p-2.5 rounded-lg bg-white/80 border border-slate-200/80 text-[11px] text-slate-700 grid grid-cols-2 sm:grid-cols-3 gap-2">
                            {alert.metadata.current_cases !== undefined && (
                              <div>
                                <span className="text-[10px] text-slate-400 uppercase font-bold block">Current</span>
                                <span className="font-black text-slate-900">{alert.metadata.current_cases}</span>
                              </div>
                            )}
                            {alert.metadata.previous_cases !== undefined && (
                              <div>
                                <span className="text-[10px] text-slate-400 uppercase font-bold block">Previous</span>
                                <span className="font-bold text-slate-800">{alert.metadata.previous_cases}</span>
                              </div>
                            )}
                            {alert.metadata.percentage_change !== undefined && (
                              <div>
                                <span className="text-[10px] text-slate-400 uppercase font-bold block">Change</span>
                                <span className={`font-black ${
                                  (alert.metadata.percentage_change ?? 0) > 0 ? 'text-rose-600' : 'text-emerald-600'
                                }`}>
                                  {alert.metadata.percentage_change !== null ? `${alert.metadata.percentage_change > 0 ? '+' : ''}${alert.metadata.percentage_change}%` : 'N/A'}
                                </span>
                              </div>
                            )}
                            {alert.metadata.locality_share !== undefined && (
                              <div>
                                <span className="text-[10px] text-slate-400 uppercase font-bold block">Locality Share</span>
                                <span className="font-black text-amber-700">{alert.metadata.locality_share}%</span>
                              </div>
                            )}
                            {alert.metadata.predicted_cases !== undefined && (
                              <div>
                                <span className="text-[10px] text-slate-400 uppercase font-bold block">Predicted</span>
                                <span className="font-black text-indigo-700">{alert.metadata.predicted_cases}</span>
                              </div>
                            )}
                            {alert.metadata.historical_baseline !== undefined && (
                              <div>
                                <span className="text-[10px] text-slate-400 uppercase font-bold block">Baseline</span>
                                <span className="font-bold text-slate-800">{alert.metadata.historical_baseline}</span>
                              </div>
                            )}
                            {alert.metadata.highest_case_month && (
                              <div className="col-span-2">
                                <span className="text-[10px] text-slate-400 uppercase font-bold block">Seasonal Peak</span>
                                <span className="font-bold text-blue-700">{alert.metadata.highest_case_month}</span>
                              </div>
                            )}
                          </div>
                        )}

                        {/* Explanation */}
                        <p className="text-xs text-slate-600 leading-relaxed font-medium">
                          {alert.description}
                        </p>
                      </div>

                      {/* Card Action Buttons */}
                      <div className="pt-2 border-t border-slate-200/60 flex items-center justify-between gap-2 flex-wrap">
                        <button
                          onClick={() => setSelectedAlert(alert)}
                          className="px-2.5 py-1 text-xs font-bold text-indigo-700 hover:text-indigo-900 hover:bg-indigo-50 rounded-lg transition flex items-center gap-1 cursor-pointer"
                        >
                          <Info className="w-3.5 h-3.5" />
                          <span>View Evidence</span>
                        </button>

                        <div className="flex items-center gap-1.5">
                          {alert.status === 'NEW' && (
                            <button
                              onClick={() => handleAcknowledgeAlert(alert)}
                              className="px-2.5 py-1 bg-white hover:bg-amber-50 text-amber-900 border border-amber-300 rounded-lg text-xs font-bold transition shadow-xs cursor-pointer"
                              data-testid={`ack-btn-${alert.id}`}
                            >
                              Acknowledge
                            </button>
                          )}
                          {alert.status !== 'RESOLVED' && (
                            <button
                              onClick={() => handleResolveAlert(alert)}
                              className="px-2.5 py-1 bg-white hover:bg-slate-100 text-slate-800 border border-slate-300 rounded-lg text-xs font-bold transition shadow-xs cursor-pointer"
                              data-testid={`resolve-btn-${alert.id}`}
                            >
                              Resolve
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
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

              {/* Historical Trend Chart */}
              <div
                className="h-64 sm:h-72 w-full pt-2"
                data-testid="historical-chart-container"
                role="region"
                aria-label="Historical Disease Trend Chart"
              >
                <ResponsiveContainer width="100%" height="100%" minWidth={100} minHeight={260}>
                  <BarChart
                    data={historicalChartData}
                    margin={{ top: 10, right: 20, left: -10, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis
                      dataKey="period_label"
                      tick={{ fontSize: 11, fill: '#64748b' }}
                      axisLine={{ stroke: '#cbd5e1' }}
                      tickLine={false}
                    />
                    <YAxis
                      allowDecimals={false}
                      tick={{ fontSize: 11, fill: '#64748b' }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0f172a',
                        borderRadius: '0.75rem',
                        border: 'none',
                        color: '#f8fafc',
                        fontSize: '12px',
                        boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
                      }}
                      formatter={(value: any, name: any) => [
                        `${value} cases`,
                        name === 'MILD' ? 'Mild Severity' : name === 'MODERATE' ? 'Moderate Severity' : name === 'SEVERE' ? 'Severe Case' : name
                      ]}
                      labelStyle={{ fontWeight: 'bold', color: '#cbd5e1', marginBottom: '4px' }}
                    />
                    <Legend
                      verticalAlign="top"
                      align="right"
                      wrapperStyle={{ paddingBottom: '10px', fontSize: '11px', fontWeight: 600 }}
                    />
                    <Bar dataKey="MILD" name="MILD" stackId="severity" fill="#10b981" radius={[0, 0, 0, 0]} />
                    <Bar dataKey="MODERATE" name="MODERATE" stackId="severity" fill="#f59e0b" radius={[0, 0, 0, 0]} />
                    <Bar dataKey="SEVERE" name="SEVERE" stackId="severity" fill="#f43f5e" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
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
                  Public Health Epidemiological Forecast ({forecastData?.disease || 'Selected Condition'})
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

            {/* Selected Population Summary in Forecast Section */}
            <div className="my-4 p-3.5 bg-white/5 rounded-xl border border-white/10 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2" data-testid="forecast-selected-population">
              <div>
                <span className="font-bold text-indigo-300 uppercase tracking-wider block text-[11px]">
                  Selected Population
                </span>
                {hasActiveDemographicFilters ? (
                  <div className="flex flex-wrap items-center gap-2.5 mt-1 text-slate-200">
                    {filters.age_group && (
                      <span>Age: <strong className="text-white font-bold">{filters.age_group}</strong></span>
                    )}
                    {filters.gender && (
                      <span>Gender: <strong className="text-white font-bold">{filters.gender === 'MALE' ? 'Male' : filters.gender === 'FEMALE' ? 'Female' : 'Other'}</strong></span>
                    )}
                    {filters.severity && (
                      <span>Severity: <strong className="text-white font-bold">{filters.severity === 'MILD' ? 'Mild' : filters.severity === 'MODERATE' ? 'Moderate' : 'Severe'}</strong></span>
                    )}
                    {filters.vulnerable_group && (
                      <span>Vulnerable Group: <strong className="text-white font-bold">{
                        filters.vulnerable_group === 'PREGNANT' ? 'Pregnant' :
                        filters.vulnerable_group === 'ELDERLY' ? 'Elderly' :
                        filters.vulnerable_group === 'DISABILITY' ? 'Disability' :
                        filters.vulnerable_group === 'CHRONIC_CONDITION' ? 'Chronic Condition' :
                        filters.vulnerable_group === 'LOW_INCOME_SLUM' ? 'Low Income / Slum' : 'General'
                      }</strong></span>
                    )}
                    {filters.patient_type && (
                      <span>Patient Type: <strong className="text-white font-bold">{filters.patient_type === 'NEW' ? 'New' : 'Follow-up'}</strong></span>
                    )}
                  </div>
                ) : (
                  <span className="text-slate-300 italic block mt-1">All eligible population</span>
                )}
              </div>

              <div className="font-mono text-xs shrink-0">
                {forecastData?.observation_period && forecastData.observation_period.total_cases > 0 ? (
                  <span className="text-indigo-200 bg-white/10 px-2.5 py-1 rounded-lg border border-white/10 inline-block">
                    Cases in selected population: <strong className="text-white font-bold">{forecastData.observation_period.total_cases}</strong>
                  </span>
                ) : (
                  <span className="text-amber-300 bg-amber-500/10 px-2.5 py-1 rounded-lg border border-amber-500/20 inline-block">
                    No cases found for the selected filters.
                  </span>
                )}
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
                {forecastData.forecast_risk && (
                  <div className="mt-4 pt-3 border-t border-white/10 text-xs text-amber-300/90 font-medium" data-testid="insufficient-forecast-risk">
                    <span>{forecastData.forecast_risk.explanation || 'Insufficient historical data for reliable forecast risk classification.'}</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="mt-5 space-y-5">
                {/* Explanation Banner */}
                <div className="p-3.5 bg-indigo-950/60 rounded-xl border border-indigo-700/40 text-xs text-indigo-200 flex items-start gap-2.5">
                  <Info className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                  <span>{forecastData?.forecast.explanation}</span>
                </div>

                {/* Forecast Weekly Horizon Points */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                  {forecastData?.forecast.points.map((pt, idx) => {
                    const riskPt = forecastData?.forecast_risk?.risk_points?.find(
                      rp => rp.forecast_week_start === pt.forecast_week_start
                    ) || forecastData?.forecast_risk?.risk_points?.[idx];

                    return (
                      <div key={idx} className="bg-white/10 backdrop-blur-md p-4 rounded-xl border border-white/10 flex flex-col justify-between">
                        <div>
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
                          <div className="mt-2 pt-2 border-t border-white/10 flex justify-between items-center text-[11px] font-mono">
                            <span className="text-slate-400">Range:</span>
                            <span className="text-indigo-200 font-bold">
                              [{pt.lower_bound} — {pt.upper_bound}]
                            </span>
                          </div>
                        </div>

                        {/* Forecast Week Risk Point Badge & Ratio */}
                        {riskPt && forecastData?.forecast_risk?.status === 'AVAILABLE' && (
                          <div className="mt-3 pt-2.5 border-t border-white/10 space-y-1 text-[11px]">
                            <div className="flex justify-between items-center">
                              <span className="text-[10px] font-bold uppercase text-slate-400">Risk:</span>
                              {renderRiskLevelBadge(riskPt.risk_level)}
                            </div>
                            <div className="flex justify-between items-center font-mono text-[10px] text-slate-300">
                              <span>Ratio:</span>
                              <span className="font-bold text-white">
                                {riskPt.ratio_to_baseline !== null ? `${riskPt.ratio_to_baseline}×` : 'N/A'}
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* FORECAST RISK & THRESHOLD SURVEILLANCE INTELLIGENCE */}
                {forecastData?.forecast_risk && (
                  <div className="mt-6 pt-5 border-t border-indigo-800/60 space-y-4" data-testid="forecast-risk-section">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <ShieldAlert className="w-5 h-5 text-indigo-400" />
                        <h4 className="text-sm font-black text-white uppercase tracking-wider">
                          Forecast Risk & Surveillance Threshold Intelligence
                        </h4>
                      </div>
                      {forecastData.forecast_risk.status === 'AVAILABLE' && (
                        <div className="flex items-center gap-2 text-xs">
                          <span className="text-indigo-200 font-semibold">Highest Risk Level:</span>
                          {renderRiskLevelBadge(forecastData.forecast_risk.highest_risk_level)}
                        </div>
                      )}
                    </div>

                    {forecastData.forecast_risk.status === 'INSUFFICIENT_DATA' ? (
                      <div className="p-4 rounded-xl bg-white/5 border border-white/10 text-center" data-testid="insufficient-forecast-risk">
                        <HelpCircle className="w-7 h-7 text-amber-400 mx-auto mb-2 opacity-80" />
                        <h5 className="text-sm font-bold text-slate-100">
                          Insufficient historical data for reliable forecast risk classification.
                        </h5>
                        <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto font-medium">
                          {forecastData.forecast_risk.explanation || 'Insufficient historical data for reliable forecast risk classification.'}
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {/* Risk Overview KPI Cards */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                          {/* 1. Highest Risk Level */}
                          <div className="bg-white/10 backdrop-blur-md p-4 rounded-xl border border-white/10" data-testid="kpi-highest-risk">
                            <p className="text-[10px] font-bold text-indigo-300 uppercase tracking-wider">Highest Risk Level</p>
                            <div className="mt-2">
                              {renderRiskLevelBadge(forecastData.forecast_risk.highest_risk_level)}
                            </div>
                            <p className="text-[11px] text-slate-300 mt-2 font-medium">
                              {forecastData.forecast_risk.highest_risk_level === 'HIGH_RISK'
                                ? 'High projected surveillance risk'
                                : forecastData.forecast_risk.highest_risk_level === 'ELEVATED'
                                ? 'Elevated surveillance signal'
                                : 'Normal baseline projection'}
                            </p>
                          </div>

                          {/* 2. Historical Baseline */}
                          <div className="bg-white/10 backdrop-blur-md p-4 rounded-xl border border-white/10" data-testid="kpi-historical-baseline">
                            <p className="text-[10px] font-bold text-indigo-300 uppercase tracking-wider">Historical Baseline</p>
                            <div className="mt-2 flex items-baseline gap-1">
                              <span className="text-2xl font-black text-white">{forecastData.forecast_risk.historical_baseline ?? 0}</span>
                              <span className="text-xs text-indigo-300 font-medium">cases/wk</span>
                            </div>
                            <p className="text-[11px] text-slate-300 mt-1 font-mono">
                              Observation window weekly baseline
                            </p>
                          </div>

                          {/* 3. Elevation & High-Risk Thresholds */}
                          <div className="bg-white/10 backdrop-blur-md p-4 rounded-xl border border-white/10" data-testid="kpi-thresholds">
                            <p className="text-[10px] font-bold text-indigo-300 uppercase tracking-wider">Surveillance Thresholds</p>
                            <div className="mt-2 space-y-1 text-xs font-mono">
                              <div className="flex justify-between items-center text-amber-300">
                                <span>Elevation Threshold:</span>
                                <span className="font-bold">≥ {forecastData.forecast_risk.elevation_ratio_threshold}×</span>
                              </div>
                              <div className="flex justify-between items-center text-rose-300">
                                <span>High-Risk Threshold:</span>
                                <span className="font-bold">≥ {forecastData.forecast_risk.high_risk_ratio_threshold}×</span>
                              </div>
                            </div>
                          </div>

                          {/* 4. Projected Week Counts */}
                          <div className="bg-white/10 backdrop-blur-md p-4 rounded-xl border border-white/10" data-testid="kpi-risk-counts">
                            <p className="text-[10px] font-bold text-indigo-300 uppercase tracking-wider">Projected Week Distribution</p>
                            <div className="mt-2 grid grid-cols-3 gap-1.5 text-center font-mono">
                              <div className="p-1.5 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
                                <span className="text-[10px] text-emerald-300 block font-bold">Normal Projected Weeks</span>
                                <span className="text-sm font-black text-white">{forecastData.forecast_risk.normal_points_count}</span>
                              </div>
                              <div className="p-1.5 bg-amber-500/10 rounded-lg border border-amber-500/20">
                                <span className="text-[10px] text-amber-300 block font-bold">Elevated Projected Weeks</span>
                                <span className="text-sm font-black text-white">{forecastData.forecast_risk.elevated_points_count}</span>
                              </div>
                              <div className="p-1.5 bg-rose-500/10 rounded-lg border border-rose-500/20">
                                <span className="text-[10px] text-rose-300 block font-bold">High-Risk Projected Weeks</span>
                                <span className="text-sm font-black text-white">{forecastData.forecast_risk.high_risk_points_count}</span>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Risk Explanation */}
                        <div className="p-3.5 bg-indigo-950/70 rounded-xl border border-indigo-700/50 text-xs text-indigo-200 flex items-start gap-2.5" data-testid="risk-explanation">
                          <Info className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                          <div>
                            <span className="font-bold text-white block">Risk Explanation:</span>
                            <span>{forecastData.forecast_risk.explanation}</span>
                          </div>
                        </div>

                        {/* Weekly Forecast Risk Points Table */}
                        {forecastData.forecast_risk.risk_points && forecastData.forecast_risk.risk_points.length > 0 && (
                          <div className="space-y-2 mt-4" data-testid="forecast-risk-points-table">
                            <h5 className="text-xs font-bold text-indigo-200 uppercase tracking-wider">
                              Forecast Risk Points
                            </h5>
                            <div className="overflow-x-auto rounded-xl border border-white/10 bg-white/5">
                              <table className="w-full text-left text-xs">
                                <thead className="bg-white/10 text-indigo-200 font-bold border-b border-white/10">
                                  <tr>
                                    <th className="p-3">Forecast Week</th>
                                    <th className="p-3">Predicted Cases</th>
                                    <th className="p-3">Historical Baseline</th>
                                    <th className="p-3">Ratio to Baseline</th>
                                    <th className="p-3">Risk Level</th>
                                    <th className="p-3">Explanation</th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5 text-slate-200 font-medium">
                                  {forecastData.forecast_risk.risk_points.map((rp, idx) => (
                                    <tr key={idx} className="hover:bg-white/5 transition" data-testid={`risk-point-row-${idx}`}>
                                      <td className="p-3 font-mono font-bold text-white">
                                        Week +{rp.forecast_week ?? idx + 1}
                                      </td>
                                      <td className="p-3 font-mono font-bold text-white">
                                        {rp.predicted_cases}
                                      </td>
                                      <td className="p-3 font-mono text-slate-300">
                                        {rp.historical_baseline}
                                      </td>
                                      <td className="p-3 font-mono font-bold">
                                        {rp.ratio_to_baseline !== null ? `${rp.ratio_to_baseline}×` : 'N/A'}
                                      </td>
                                      <td className="p-3">
                                        {renderRiskLevelBadge(rp.risk_level)}
                                      </td>
                                      <td className="p-3 text-[11px] text-slate-300 max-w-sm">
                                        {rp.explanation}
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
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

      {/* ALERT DETAILS & EVIDENCE MODAL */}
      {selectedAlert && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in"
          data-testid="alert-detail-modal"
        >
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-slate-200 p-6 space-y-5">
            {/* Modal Header */}
            <div className="flex items-start justify-between gap-3 border-b border-slate-100 pb-4">
              <div>
                <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                  {renderAlertSeverityBadge(selectedAlert.severity)}
                  {renderAlertStatusBadge(selectedAlert.status)}
                  <span className="text-[11px] font-bold text-slate-500 font-mono">#{selectedAlert.id}</span>
                </div>
                <h3 className="text-lg font-black text-slate-900">{selectedAlert.title}</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Signal Type: {getSignalTypeDisplay(selectedAlert.alert_type, selectedAlert.metadata?.signal_type)}
                </p>
              </div>
              <button
                onClick={() => setSelectedAlert(null)}
                className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition cursor-pointer"
                data-testid="close-modal-btn"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Scope Information */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3.5 bg-slate-50 rounded-xl border border-slate-200 text-xs">
              <div>
                <span className="text-[10px] text-slate-400 font-bold uppercase block">Disease</span>
                <span className="font-bold text-slate-900">{selectedAlert.metadata?.disease || 'Monitored'}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 font-bold uppercase block">Facility</span>
                <span className="font-bold text-slate-900 truncate block">{selectedAlert.facility_name || `#${selectedAlert.facility}`}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 font-bold uppercase block">District</span>
                <span className="font-bold text-slate-900">{selectedAlert.district_name || selectedAlert.metadata?.district_name || 'N/A'}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 font-bold uppercase block">Observation Date</span>
                <span className="font-mono text-slate-900">{selectedAlert.metadata?.observation_date || 'N/A'}</span>
              </div>
            </div>

            {/* Diagnostic Evidence Details */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Epidemiological Evidence
              </h4>
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3 text-xs">
                <p className="text-slate-700 font-medium leading-relaxed">
                  {selectedAlert.metadata?.explanation || selectedAlert.description}
                </p>

                {/* Structured metrics breakdown */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-3 border-t border-slate-200">
                  {selectedAlert.metadata?.current_cases !== undefined && (
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase font-bold block">Current Cases</span>
                      <span className="font-black text-slate-900 text-base">{selectedAlert.metadata.current_cases}</span>
                    </div>
                  )}
                  {selectedAlert.metadata?.previous_cases !== undefined && (
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase font-bold block">Previous Cases</span>
                      <span className="font-bold text-slate-800 text-base">{selectedAlert.metadata.previous_cases}</span>
                    </div>
                  )}
                  {selectedAlert.metadata?.percentage_change !== undefined && (
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase font-bold block">Percentage Change</span>
                      <span className={`font-black text-base ${
                        (selectedAlert.metadata.percentage_change ?? 0) > 0 ? 'text-rose-600' : 'text-emerald-600'
                      }`}>
                        {selectedAlert.metadata.percentage_change !== null ? `${selectedAlert.metadata.percentage_change > 0 ? '+' : ''}${selectedAlert.metadata.percentage_change}%` : 'N/A'}
                      </span>
                    </div>
                  )}
                  {selectedAlert.metadata?.locality && (
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase font-bold block">Locality</span>
                      <span className="font-bold text-slate-900">{selectedAlert.metadata.locality}</span>
                    </div>
                  )}
                  {selectedAlert.metadata?.locality_share !== undefined && (
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase font-bold block">Locality Share</span>
                      <span className="font-black text-amber-700">{selectedAlert.metadata.locality_share}%</span>
                    </div>
                  )}
                  {selectedAlert.metadata?.predicted_cases !== undefined && (
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase font-bold block">Predicted Volume</span>
                      <span className="font-black text-indigo-700">{selectedAlert.metadata.predicted_cases}</span>
                    </div>
                  )}
                  {selectedAlert.metadata?.lower_bound !== undefined && selectedAlert.metadata?.upper_bound !== undefined && (
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase font-bold block">Forecast Bounds (90% CI)</span>
                      <span className="font-mono text-slate-800">[{selectedAlert.metadata.lower_bound} - {selectedAlert.metadata.upper_bound}]</span>
                    </div>
                  )}
                  {selectedAlert.metadata?.historical_baseline !== undefined && (
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase font-bold block">Historical Baseline</span>
                      <span className="font-bold text-slate-800">{selectedAlert.metadata.historical_baseline}</span>
                    </div>
                  )}
                  {selectedAlert.metadata?.forecast_method && (
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase font-bold block">Forecast Model</span>
                      <span className="font-mono text-slate-700">{selectedAlert.metadata.forecast_method}</span>
                    </div>
                  )}
                  {selectedAlert.metadata?.highest_case_month && (
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase font-bold block">Peak Seasonal Month</span>
                      <span className="font-bold text-blue-700">{selectedAlert.metadata.highest_case_month}</span>
                    </div>
                  )}
                  {selectedAlert.metadata?.seasonal_strength !== undefined && (
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase font-bold block">Seasonal Strength</span>
                      <span className="font-bold text-slate-900">{selectedAlert.metadata.seasonal_strength}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Lifecycle & Audit History */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Lifecycle & Review Tracking
              </h4>
              <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-2 text-slate-600">
                <div className="flex justify-between items-center">
                  <span className="font-semibold text-slate-500">Created:</span>
                  <span className="font-mono text-slate-800">{selectedAlert.created_at}</span>
                </div>
                {selectedAlert.acknowledged_at && (
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-slate-500">Acknowledged:</span>
                    <span className="font-mono text-slate-800">
                      {selectedAlert.acknowledged_at} {selectedAlert.acknowledged_by_username ? `by ${selectedAlert.acknowledged_by_username}` : ''}
                    </span>
                  </div>
                )}
                {selectedAlert.resolved_at && (
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-slate-500">Resolved:</span>
                    <span className="font-mono text-slate-800">
                      {selectedAlert.resolved_at} {selectedAlert.resolved_by_username ? `by ${selectedAlert.resolved_by_username}` : ''}
                    </span>
                  </div>
                )}
                {selectedAlert.resolution_notes && (
                  <div className="pt-2 border-t border-slate-200">
                    <span className="font-semibold text-slate-500 block mb-0.5">Resolution Notes:</span>
                    <span className="text-slate-800 font-medium">{selectedAlert.resolution_notes}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Modal Actions */}
            <div className="pt-4 border-t border-slate-100 flex items-center justify-between gap-3">
              <button
                onClick={() => setSelectedAlert(null)}
                className="px-4 py-2 rounded-xl border border-slate-300 text-slate-700 hover:bg-slate-100 text-xs font-bold transition cursor-pointer"
              >
                Close
              </button>

              <div className="flex items-center gap-2">
                {selectedAlert.status === 'NEW' && (
                  <button
                    onClick={() => handleAcknowledgeAlert(selectedAlert)}
                    className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold transition shadow-xs cursor-pointer"
                  >
                    Acknowledge Signal
                  </button>
                )}
                {selectedAlert.status !== 'RESOLVED' && (
                  <button
                    onClick={() => handleResolveAlert(selectedAlert)}
                    className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition shadow-xs cursor-pointer"
                  >
                    Resolve Signal
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PublicHealthIntelligence;
