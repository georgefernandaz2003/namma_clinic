import React, { useState, useEffect } from 'react';
import {
  Activity,
  Building2,
  Users,
  AlertTriangle,
  Pill,
  TrendingUp,
  RefreshCw,
  ChevronRight,
  UserCheck,
  Sliders,
  BedDouble,
  HeartPulse,
  Stethoscope,
  Microscope,
  Truck,
  CheckCircle2,
  Calendar,
  Layers,
  ArrowUpRight,
  AlertCircle
} from 'lucide-react';
import api from '../../services/api';

// Navigation Section Tabs
type NavSection =
  | 'overview'
  | 'trend_analysis'
  | 'disease_intelligence'
  | 'healthcare_operations'
  | 'pharmacy_supply'
  | 'workforce_intelligence'
  | 'predictions_trends'
  | 'alerts_recommendations';

export const PublicHealthIntelligencePage: React.FC = () => {
  // Cascading Filter States
  const [selectedDistrict, setSelectedDistrict] = useState<string>('all');
  const [selectedZone, setSelectedZone] = useState<string>('all');
  const [selectedHospital, setSelectedHospital] = useState<string>('all');
  const [selectedTimePeriod, setSelectedTimePeriod] = useState<string>('last_30_days');
  const [selectedRoleLens, setSelectedRoleLens] = useState<string>('HOSPITAL_ADMIN');

  // Navigation State
  const [activeSection, setActiveSection] = useState<NavSection>('overview');

  // District Comparison Metric Toggle
  const [comparisonMetricIdx, setComparisonMetricIdx] = useState<number>(0);
  const [hoveredBarCategory, setHoveredBarCategory] = useState<string | null>(null);

  // Sub-filter States
  const [selectedDiseaseCategory, setSelectedDiseaseCategory] = useState<string>('ALL');
  const [selectedMedicineFilter, setSelectedMedicineFilter] = useState<string>('ALL');
  const [selectedAlertSeverity, setSelectedAlertSeverity] = useState<string>('ALL');

  // API Data & Loading States
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch Healthcare Intelligence Payload
  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        district: selectedDistrict,
        zone: selectedZone,
        hospital: selectedHospital,
        time_period: selectedTimePeriod,
        role: selectedRoleLens
      });
      const res = await api.get(`analytics/command-center/?${params.toString()}`);
      setData(res.data);
    } catch (err: any) {
      console.error('Failed to load healthcare telemetry:', err);
      setError('Unable to load healthcare data. Please verify network connection.');
    } finally {
      setLoading(false);
    }
  };

  // Re-fetch when cascading filters or role lens change
  useEffect(() => {
    fetchDashboardData();
  }, [selectedDistrict, selectedZone, selectedHospital, selectedTimePeriod, selectedRoleLens]);

  // Handle District Change (Reset Zone and Hospital)
  const handleDistrictChange = (distId: string) => {
    setSelectedDistrict(distId);
    setSelectedZone('all');
    setSelectedHospital('all');
  };

  // Handle Zone Change (Reset Hospital)
  const handleZoneChange = (zoneId: string) => {
    setSelectedZone(zoneId);
    setSelectedHospital('all');
  };

  // Derived filter options from API response
  const availableDistricts = data?.filters?.available_districts || [];
  const availableZones = data?.filters?.available_zones || [];
  const availableHospitals = data?.filters?.available_hospitals || [];
  const availableTimePeriods = data?.filters?.available_time_periods || [];
  const breadcrumbs = data?.filters?.breadcrumbs || ['Karnataka'];
  const activeScope = data?.filters?.active_scope || {
    level: 'STATE',
    name: 'Karnataka State Overview',
    type: 'State-Wide Healthcare Overview'
  };

  const roleLensOptions = [
    { id: 'HOSPITAL_ADMIN', label: 'Hospital Administrator' },
    { id: 'DISTRICT_OFFICER', label: 'District Health Officer' },
    { id: 'DOCTOR', label: 'Medical Officer / Doctor' },
    { id: 'NURSE', label: 'Staff Nurse' },
    { id: 'LAB_TECHNICIAN', label: 'Lab Technician' },
    { id: 'PHARMACIST', label: 'Pharmacist' },
    { id: 'INVENTORY_OFFICER', label: 'Inventory Officer' }
  ];

  if (loading && !data) {
    return (
      <div className="min-h-[75vh] flex flex-col items-center justify-center p-8 space-y-3">
        <RefreshCw className="w-8 h-8 text-emerald-600 animate-spin" />
        <h2 className="text-base font-semibold text-slate-700">Loading Healthcare Dashboard...</h2>
        <p className="text-xs text-slate-400">Fetching statewide metrics and clinical telemetry...</p>
      </div>
    );
  }

  return (
    <div className="max-w-[1560px] mx-auto space-y-6 pb-20 font-sans text-slate-900">
      {/* --------------------------------------------------------------------------- */}
      {/* 1. TOP HEADER & CASCADING FILTERS (CLEAN HEALTHCARE STYLE)                  */}
      {/* --------------------------------------------------------------------------- */}
      <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-5 space-y-4">
        {/* Title & Top Metadata Row */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-100 pb-4">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">
                Healthcare Dashboard
              </h1>
              <span className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-slate-100 text-slate-600 border border-slate-200">
                DEMO / SYNTHETIC DATA
              </span>
            </div>
            <p className="text-xs text-slate-500 font-medium">
              Karnataka • State-wide Health Overview
            </p>
          </div>

          {/* Right Action Controls: Role Selector & Sync */}
          <div className="flex items-center gap-2.5">
            <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs">
              <Sliders className="w-3.5 h-3.5 text-slate-500" />
              <label htmlFor="role-lens-select" className="text-slate-500 font-medium">Role:</label>
              <select
                id="role-lens-select"
                aria-label="Select Clinical Role Lens"
                value={selectedRoleLens}
                onChange={(e) => setSelectedRoleLens(e.target.value)}
                className="bg-transparent text-slate-800 font-semibold focus:outline-none cursor-pointer"
              >
                {roleLensOptions.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.label}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={fetchDashboardData}
              disabled={loading}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>

        {/* Cascading Filter Controls: State -> District -> Zone -> Hospital -> Time Period */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3 pt-1">
          {/* 1. State Filter */}
          <div className="space-y-1">
            <label htmlFor="state-filter-select" className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide block">
              State
            </label>
            <div className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-semibold text-slate-700 flex items-center justify-between">
              <span>Karnataka</span>
              <span className="text-[10px] text-slate-400 font-normal">State-wide</span>
            </div>
          </div>

          {/* 2. District Filter */}
          <div className="space-y-1">
            <label htmlFor="district-filter-select" className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide block">
              District
            </label>
            <select
              id="district-filter-select"
              aria-label="District Filter"
              value={selectedDistrict}
              onChange={(e) => handleDistrictChange(e.target.value)}
              className="w-full bg-white border border-slate-200 hover:border-slate-300 rounded-lg px-3 py-2 text-xs font-medium text-slate-800 focus:ring-1 focus:ring-emerald-500 focus:outline-none"
            >
              {availableDistricts.map((d: any) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>

          {/* 3. Zone Filter */}
          <div className="space-y-1">
            <label htmlFor="zone-filter-select" className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide block">
              Zone / Taluk
            </label>
            <select
              id="zone-filter-select"
              aria-label="Zone or Taluk Filter"
              value={selectedZone}
              onChange={(e) => handleZoneChange(e.target.value)}
              disabled={selectedDistrict === 'all'}
              className="w-full bg-white border border-slate-200 hover:border-slate-300 disabled:bg-slate-50 disabled:text-slate-400 rounded-lg px-3 py-2 text-xs font-medium text-slate-800 focus:ring-1 focus:ring-emerald-500 focus:outline-none"
            >
              {availableZones.map((z: any) => (
                <option key={z.id} value={z.id}>
                  {z.name}
                </option>
              ))}
            </select>
          </div>

          {/* 4. Hospital Filter */}
          <div className="space-y-1">
            <label htmlFor="hospital-filter-select" className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide block">
              Hospital / Facility
            </label>
            <select
              id="hospital-filter-select"
              aria-label="Hospital or Facility Filter"
              value={selectedHospital}
              onChange={(e) => setSelectedHospital(e.target.value)}
              disabled={selectedDistrict === 'all' && selectedZone === 'all'}
              className="w-full bg-white border border-slate-200 hover:border-slate-300 disabled:bg-slate-50 disabled:text-slate-400 rounded-lg px-3 py-2 text-xs font-medium text-slate-800 focus:ring-1 focus:ring-emerald-500 focus:outline-none"
            >
              {availableHospitals.map((h: any) => (
                <option key={h.id} value={h.id}>
                  {h.name}
                </option>
              ))}
            </select>
          </div>

          {/* 5. Time Period Filter */}
          <div className="space-y-1">
            <label htmlFor="time-period-select" className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide block">
              Time Period
            </label>
            <select
              id="time-period-select"
              aria-label="Time Period Filter"
              value={selectedTimePeriod}
              onChange={(e) => setSelectedTimePeriod(e.target.value)}
              className="w-full bg-white border border-slate-200 hover:border-slate-300 rounded-lg px-3 py-2 text-xs font-medium text-slate-800 focus:ring-1 focus:ring-emerald-500 focus:outline-none"
            >
              {availableTimePeriods.map((t: any) => (
                <option key={t.id} value={t.id}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Clean Breadcrumbs & Active Scope Status */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-100 text-xs">
          <div className="flex flex-wrap items-center gap-1.5 text-slate-500">
            <span className="font-semibold text-slate-400">Location:</span>
            {breadcrumbs.map((b: string, idx: number) => (
              <React.Fragment key={idx}>
                {idx > 0 && <ChevronRight className="w-3.5 h-3.5 text-slate-300" />}
                <span className={idx === breadcrumbs.length - 1 ? 'text-slate-900 font-semibold' : 'text-slate-600'}>
                  {b}
                </span>
              </React.Fragment>
            ))}
          </div>

          <div className="text-slate-500">
            Scope: <strong className="text-slate-800">{activeScope.name}</strong> •{' '}
            <span className="text-slate-600 font-medium">{activeScope.facility_count || 1} Facilities</span> •{' '}
            <span className="text-slate-600 font-medium">{(activeScope.total_beds || 0).toLocaleString()} Beds</span>
          </div>
        </div>
      </div>

      {/* --------------------------------------------------------------------------- */}
      {/* 2. MAIN NAVIGATION TABS (CLEAN TABS)                                        */}
      {/* --------------------------------------------------------------------------- */}
      <div className="flex flex-wrap items-center gap-1.5 border-b border-slate-200 pb-2">
        {[
          { id: 'overview', label: 'Overview' },
          { id: 'trend_analysis', label: 'Trend Analysis' },
          { id: 'disease_intelligence', label: 'Disease Intelligence' },
          { id: 'healthcare_operations', label: 'Healthcare Operations' },
          { id: 'pharmacy_supply', label: 'Pharmacy & Supply Chain' },
          { id: 'workforce_intelligence', label: 'Workforce Intelligence' },
          { id: 'predictions_trends', label: 'Predictions & Trends' },
          { id: 'alerts_recommendations', label: 'Alerts & Recommendations' }
        ].map((tab) => {
          const isActive = activeSection === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveSection(tab.id as NavSection)}
              className={`px-3.5 py-2 rounded-lg text-xs font-semibold transition ${
                isActive
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'bg-white hover:bg-slate-50 text-slate-600 border border-slate-200'
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* =========================================================================== */}
      {/* SECTION 1: OVERVIEW (CLEAN HEALTHCARE SUMMARY)                              */}
      {/* =========================================================================== */}
      {activeSection === 'overview' && (
        <div className="space-y-6">
          {/* Health Overview (Section 6 of requirements: 4 simple concise insights) */}
          <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-4">
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2.5">
              Health Overview
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs divide-y sm:divide-y-0 sm:divide-x divide-slate-100">
              <div className="pt-2 sm:pt-0 sm:px-2 space-y-0.5">
                <span className="text-[10px] uppercase font-bold text-slate-400 block">WHAT'S CHANGING</span>
                <p className="font-semibold text-slate-800">
                  {data?.command_center?.health_overview?.whats_changing || 'Outpatient visits increased 12%.'}
                </p>
              </div>

              <div className="pt-2 sm:pt-0 sm:px-2 space-y-0.5">
                <span className="text-[10px] uppercase font-bold text-slate-400 block">WHERE</span>
                <p className="font-semibold text-slate-800">
                  {data?.command_center?.health_overview?.where || `Highest demand: ${activeScope.name}.`}
                </p>
              </div>

              <div className="pt-2 sm:pt-0 sm:px-2 space-y-0.5">
                <span className="text-[10px] uppercase font-bold text-slate-400 block">FORECAST</span>
                <p className="font-semibold text-amber-700">
                  {data?.command_center?.health_overview?.forecast || 'Dengue cases expected to increase 24%.'}
                </p>
              </div>

              <div className="pt-2 sm:pt-0 sm:px-2 space-y-0.5">
                <span className="text-[10px] uppercase font-bold text-slate-400 block">ACTION</span>
                <p className="font-semibold text-emerald-700">
                  {data?.command_center?.health_overview?.action || 'Increase surveillance in affected zones.'}
                </p>
              </div>
            </div>
          </div>

          {/* Key KPI Cards (Section 7: 6–8 simple, number-prominent cards in 4x2 grid) */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {data?.command_center?.kpis?.map((kpi: any) => {
              const isCrit = kpi.status === 'critical';
              const isWarn = kpi.status === 'warning';
              return (
                <div
                  key={kpi.id}
                  className={`bg-white rounded-xl p-4 border shadow-sm flex flex-col justify-between space-y-2 ${
                    isCrit ? 'border-rose-200' : isWarn ? 'border-amber-200' : 'border-slate-200'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
                      {kpi.label}
                    </span>
                    <span
                      className={`text-[11px] font-bold px-1.5 py-0.5 rounded ${
                        isCrit ? 'bg-rose-100 text-rose-700' : isWarn ? 'bg-amber-100 text-amber-700' : 'bg-emerald-50 text-emerald-700'
                      }`}
                    >
                      {kpi.change}
                    </span>
                  </div>
                  <div className="text-3xl font-black text-slate-900 tracking-tight">
                    {kpi.value}
                  </div>
                  <div className="text-xs text-slate-500 pt-1 border-t border-slate-100">
                    {kpi.unit}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Trend Charts (Section 8: Prioritize OPD, Disease, Bed Occupancy, Medicine Consumption, Hospital Demand) */}
          <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-5 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  Trend Charts
                </h3>
                <p className="text-xs text-slate-500">
                  Key historical trends, current volumes, and forecast trajectory
                </p>
              </div>
              <div className="flex items-center gap-4 text-xs font-medium text-slate-600">
                <span className="flex items-center gap-1.5">
                  <span className="w-3.5 h-1 bg-blue-600 rounded" />
                  <span>Historical</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-rose-500 ring-2 ring-rose-200" />
                  <span>Current</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3.5 h-1 bg-amber-500 border-dashed rounded" />
                  <span>Forecast</span>
                </span>
              </div>
            </div>

            {/* 5 Prioritized Line Charts */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[
                {
                  id: 'opd',
                  title: '1. OPD Trend',
                  series: data?.trend_analysis?.series?.opd || [],
                  unit: 'Visits',
                  status: '+12% Surge',
                  color: '#2563EB'
                },
                {
                  id: 'disease',
                  title: '2. Disease Trend (Dengue Cases)',
                  series: data?.trend_analysis?.series?.disease_cases || [],
                  unit: 'Cases',
                  status: 'Forecast +24%',
                  color: '#D97706'
                },
                {
                  id: 'bed_occupancy',
                  title: '3. Bed Occupancy Trend',
                  series: data?.trend_analysis?.series?.bed_occupancy || [],
                  unit: '%',
                  status: 'Current 84.6%',
                  color: '#7C3AED'
                },
                {
                  id: 'medicine',
                  title: '4. Medicine Consumption Trend',
                  series: data?.trend_analysis?.series?.medicine_consumption || [],
                  unit: 'Units',
                  status: 'Increasing burn rate',
                  color: '#059669'
                },
                {
                  id: 'hospital_demand',
                  title: '5. Hospital Demand Trend',
                  series: data?.trend_analysis?.series?.hospital_crowd_index || [],
                  unit: 'Visits / Center',
                  status: 'Forecast +21%',
                  color: '#0284C7'
                }
              ].map((trend) => {
                const splitIdx = data?.trend_analysis?.split_index || 10;
                const maxVal = Math.max(...trend.series, 1);
                const minVal = Math.min(...trend.series, 0);

                return (
                  <div key={trend.id} className="bg-slate-50/70 rounded-xl border border-slate-200/80 p-3.5 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-900 text-xs">{trend.title}</span>
                      <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded">
                        {trend.status}
                      </span>
                    </div>
                    <div className="text-xs text-slate-500 font-medium">
                      Current: <strong className="text-slate-800">{trend.series[splitIdx - 1]?.toLocaleString()} {trend.unit}</strong>
                    </div>

                    {/* Clean SVG Line */}
                    <div className="w-full h-28 bg-white rounded-lg p-2 border border-slate-100 flex flex-col justify-end">
                      <svg viewBox="0 0 500 110" className="w-full h-20 overflow-visible">
                        <line x1="0" y1="20" x2="500" y2="20" stroke="#F1F5F9" strokeDasharray="3,3" />
                        <line x1="0" y1="60" x2="500" y2="60" stroke="#F1F5F9" strokeDasharray="3,3" />
                        <line x1="0" y1="100" x2="500" y2="100" stroke="#F1F5F9" strokeDasharray="3,3" />

                        {/* Historical solid line */}
                        {trend.series.slice(0, splitIdx).map((val: number, i: number, arr: number[]) => {
                          if (i === arr.length - 1) return null;
                          const x1 = (i / 11) * 480 + 10;
                          const y1 = 100 - ((val - minVal) / (maxVal - minVal || 1)) * 80;
                          const x2 = ((i + 1) / 11) * 480 + 10;
                          const y2 = 100 - ((arr[i + 1] - minVal) / (maxVal - minVal || 1)) * 80;
                          return (
                            <line
                              key={`hist-${i}`}
                              x1={x1}
                              y1={y1}
                              x2={x2}
                              y2={y2}
                              stroke={trend.color}
                              strokeWidth="2.5"
                              strokeLinecap="round"
                            />
                          );
                        })}

                        {/* Current Data Point */}
                        {trend.series[splitIdx - 1] !== undefined && (() => {
                          const cx = ((splitIdx - 1) / 11) * 480 + 10;
                          const cy = 100 - ((trend.series[splitIdx - 1] - minVal) / (maxVal - minVal || 1)) * 80;
                          return (
                            <circle
                              cx={cx}
                              cy={cy}
                              r="4"
                              fill="#EF4444"
                              stroke="#FFFFFF"
                              strokeWidth="1.5"
                            />
                          );
                        })()}

                        {/* Forecast dashed line */}
                        {trend.series.slice(splitIdx - 1).map((val: number, i: number, arr: number[]) => {
                          if (i === arr.length - 1) return null;
                          const idx1 = splitIdx - 1 + i;
                          const idx2 = splitIdx - 1 + i + 1;
                          const x1 = (idx1 / 11) * 480 + 10;
                          const y1 = 100 - ((val - minVal) / (maxVal - minVal || 1)) * 80;
                          const x2 = (idx2 / 11) * 480 + 10;
                          const y2 = 100 - ((arr[i + 1] - minVal) / (maxVal - minVal || 1)) * 80;
                          return (
                            <line
                              key={`fc-${i}`}
                              x1={x1}
                              y1={y1}
                              x2={x2}
                              y2={y2}
                              stroke="#F59E0B"
                              strokeWidth="2"
                              strokeDasharray="4,4"
                              strokeLinecap="round"
                            />
                          );
                        })}
                      </svg>

                      {/* X-Axis Month labels */}
                      <div className="flex justify-between text-[9px] text-slate-400 font-medium px-1 mt-1">
                        <span>Jan</span>
                        <span>May</span>
                        <span>Sep</span>
                        <span className="font-bold text-slate-700">Oct (Current)</span>
                        <span className="font-bold text-amber-600">Nov (F)</span>
                        <span className="font-bold text-amber-600">Dec (F)</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* District Healthcare Overview (Section 9: Clean Bar Chart with metric toggle) */}
          <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-5 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  {data?.command_center?.comparison_chart?.title || 'District Healthcare Overview'}
                </h3>
                <p className="text-xs text-slate-500">
                  Compare healthcare volume across administrative locations
                </p>
              </div>

              {/* Metric Selector Toggle (Section 9 requirement) */}
              <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-lg text-xs font-semibold">
                {data?.command_center?.comparison_chart?.series?.map((s: any, idx: number) => (
                  <button
                    key={idx}
                    onClick={() => setComparisonMetricIdx(idx)}
                    className={`px-3 py-1 rounded-md transition ${
                      comparisonMetricIdx === idx
                        ? 'bg-white text-slate-900 shadow-xs'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    {s.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Clean Responsive SVG Bar Chart */}
            <div className="w-full overflow-x-auto">
              <div className="min-w-[620px] h-56 relative flex items-end justify-between px-4 pt-4 pb-6 border-b border-slate-200">
                {data?.command_center?.comparison_chart?.categories?.map((cat: string, cIdx: number) => {
                  const activeSeries = data.command_center.comparison_chart.series[comparisonMetricIdx] || { values: [], color: '#3B82F6', name: 'Value' };
                  const val = activeSeries.values[cIdx] || 0;
                  const maxVal = Math.max(...activeSeries.values, 1);
                  const h = Math.max(10, (val / maxVal) * 140);
                  const isHovered = hoveredBarCategory === cat;

                  return (
                    <div
                      key={cIdx}
                      className="flex-1 flex flex-col items-center justify-end h-full px-2 group cursor-pointer"
                      onMouseEnter={() => setHoveredBarCategory(cat)}
                      onMouseLeave={() => setHoveredBarCategory(null)}
                    >
                      {/* Tooltip */}
                      {isHovered && (
                        <div className="absolute top-1 bg-slate-900 text-white rounded-md px-2.5 py-1 text-xs shadow-md z-10 pointer-events-none">
                          <span className="font-semibold block">{cat}</span>
                          <span>{activeSeries.name}: {val.toLocaleString()}</span>
                        </div>
                      )}

                      {/* Bar */}
                      <div
                        style={{ height: `${h}px`, backgroundColor: activeSeries.color }}
                        className="w-6 sm:w-8 rounded-t transition-all group-hover:opacity-90"
                      />

                      {/* Category Label */}
                      <span className="text-[10px] font-medium text-slate-600 mt-2 truncate max-w-[80px] text-center">
                        {cat}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Predictions & Trends (Section 4: Compact Cards, No Paragraphs, 1-line recommendations) */}
          <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Predictions & Trends</h3>
                <p className="text-xs text-slate-500">Short-term healthcare projections & actionable recommendations</p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {data?.command_center?.top_predictions?.slice(0, 4).map((pred: any) => {
                const isCrit = pred.risk === 'CRITICAL';
                return (
                  <div
                    key={pred.id}
                    className="bg-slate-50/80 rounded-xl p-4 border border-slate-200/90 space-y-3 text-xs flex flex-col justify-between"
                  >
                    <div className="flex items-start justify-between">
                      <h4 className="font-bold text-slate-900 text-sm">{pred.title}</h4>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                          isCrit ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'
                        }`}
                      >
                        {pred.risk}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs py-1">
                      <div>
                        <span className="text-slate-400 block text-[10px] uppercase font-bold">Current</span>
                        <strong className="text-slate-900 text-base font-black">{pred.current}</strong>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px] uppercase font-bold">Forecast</span>
                        <strong className="text-slate-900 text-base font-black">{pred.forecast}</strong>
                      </div>
                    </div>

                    <div className="pt-2 border-t border-slate-200/70 text-slate-600 text-xs">
                      <span className="font-bold text-slate-800">Recommendation:</span>{' '}
                      {pred.recommendation}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Alerts & Recommendations (Section 5: Compact rows, readable, no military jargon) */}
          <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Alerts & Recommendations</h3>
                <p className="text-xs text-slate-500">Active operational and clinical advisories</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {data?.command_center?.critical_alerts?.map((alt: any) => {
                const isCrit = alt.severity === 'CRITICAL';
                const isHigh = alt.severity === 'HIGH';
                return (
                  <div
                    key={alt.id}
                    className="bg-slate-50/80 rounded-xl p-3.5 border border-slate-200/90 space-y-1.5 text-xs flex flex-col justify-between"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-sm">{isCrit ? '🔴' : isHigh ? '🟠' : '🟡'}</span>
                      <strong className="text-slate-900 text-xs">
                        {alt.title} — {alt.severity === 'CRITICAL' ? 'Critical' : alt.severity === 'HIGH' ? 'High' : 'Warning'}
                      </strong>
                    </div>
                    <p className="text-slate-700 text-xs pl-6">
                      <span className="font-semibold">{alt.status}</span> {alt.explanation}
                    </p>
                    <p className="text-slate-800 text-xs pl-6 pt-1 border-t border-slate-200/60">
                      <strong>Recommendation:</strong> {alt.recommendation}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================== */}
      {/* SECTION 2: TREND ANALYSIS (SIMPLE, READABLE LINE CHARTS)                    */}
      {/* =========================================================================== */}
      {activeSection === 'trend_analysis' && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-bold text-slate-900">
                Healthcare Trend Analysis
              </h2>
              <p className="text-xs text-slate-500">
                Tracking historical monthly trends and short-term forecast
              </p>
            </div>
            <div className="flex items-center gap-4 text-xs font-medium text-slate-600">
              <span className="flex items-center gap-1.5">
                <span className="w-3.5 h-1 bg-emerald-600 rounded" />
                <span>Historical</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3.5 h-1 bg-amber-500 border-dashed rounded" />
                <span>Forecast</span>
              </span>
            </div>
          </div>

          {/* Simple Line Charts Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {[
              {
                id: 'opd',
                title: 'Outpatient (OPD) Visits',
                series: data?.trend_analysis?.series?.opd || [],
                unit: 'Visits',
                status: 'Increasing (+12%)',
                color: '#2563EB'
              },
              {
                id: 'disease',
                title: 'Disease Trend (Dengue Cases)',
                series: data?.trend_analysis?.series?.disease_cases || [],
                unit: 'Cases',
                status: 'Forecast +24%',
                color: '#D97706'
              },
              {
                id: 'bed_occupancy',
                title: 'Bed Occupancy (%)',
                series: data?.trend_analysis?.series?.bed_occupancy || [],
                unit: '%',
                status: 'High (84.6%)',
                color: '#7C3AED'
              },
              {
                id: 'medicine',
                title: 'Medicine Consumption Trend',
                series: data?.trend_analysis?.series?.medicine_consumption || [],
                unit: 'Units',
                status: 'Increasing burn rate',
                color: '#059669'
              },
              {
                id: 'emergency',
                title: 'Emergency Case Trend',
                series: data?.trend_analysis?.series?.emergency || [],
                unit: 'Cases',
                status: 'Acute demand surge',
                color: '#DC2626'
              },
              {
                id: 'hospital_demand',
                title: 'Hospital Demand Trend',
                series: data?.trend_analysis?.series?.hospital_crowd_index || [],
                unit: 'Daily visits',
                status: 'Forecast +21%',
                color: '#0284C7'
              }
            ].map((trend) => {
              const months = data?.trend_analysis?.months || [];
              const splitIdx = data?.trend_analysis?.split_index || 10;
              const maxVal = Math.max(...trend.series, 1);
              const minVal = Math.min(...trend.series, 0);

              return (
                <div key={trend.id} className="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-bold text-slate-900 text-sm">{trend.title}</h4>
                      <span className="text-xs font-semibold text-emerald-700">{trend.status}</span>
                    </div>
                    <span className="text-xs text-slate-500 font-medium">
                      Current: {trend.series[splitIdx - 1]?.toLocaleString()} {trend.unit}
                    </span>
                  </div>

                  {/* Clean SVG Line */}
                  <div className="w-full h-40 bg-slate-50/70 rounded-xl p-3 border border-slate-100 flex flex-col justify-end">
                    <svg viewBox="0 0 500 110" className="w-full h-24 overflow-visible">
                      <line x1="0" y1="20" x2="500" y2="20" stroke="#E2E8F0" strokeDasharray="3,3" />
                      <line x1="0" y1="60" x2="500" y2="60" stroke="#E2E8F0" strokeDasharray="3,3" />
                      <line x1="0" y1="100" x2="500" y2="100" stroke="#E2E8F0" strokeDasharray="3,3" />

                      {/* Historical solid */}
                      {trend.series.slice(0, splitIdx).map((val: number, i: number, arr: number[]) => {
                        if (i === arr.length - 1) return null;
                        const x1 = (i / 11) * 480 + 10;
                        const y1 = 100 - ((val - minVal) / (maxVal - minVal || 1)) * 80;
                        const x2 = ((i + 1) / 11) * 480 + 10;
                        const y2 = 100 - ((arr[i + 1] - minVal) / (maxVal - minVal || 1)) * 80;
                        return (
                          <line
                            key={`hist-${i}`}
                            x1={x1}
                            y1={y1}
                            x2={x2}
                            y2={y2}
                            stroke={trend.color}
                            strokeWidth="2.5"
                          />
                        );
                      })}

                      {/* Forecast dashed */}
                      {trend.series.slice(splitIdx - 1).map((val: number, i: number, arr: number[]) => {
                        if (i === arr.length - 1) return null;
                        const actualIdx = splitIdx - 1 + i;
                        const x1 = (actualIdx / 11) * 480 + 10;
                        const y1 = 100 - ((val - minVal) / (maxVal - minVal || 1)) * 80;
                        const x2 = ((actualIdx + 1) / 11) * 480 + 10;
                        const y2 = 100 - ((arr[i + 1] - minVal) / (maxVal - minVal || 1)) * 80;
                        return (
                          <line
                            key={`fc-${i}`}
                            x1={x1}
                            y1={y1}
                            x2={x2}
                            y2={y2}
                            stroke="#F59E0B"
                            strokeWidth="2.5"
                            strokeDasharray="4,4"
                          />
                        );
                      })}

                      {/* Dots */}
                      {trend.series.map((val: number, i: number) => {
                        const cx = (i / 11) * 480 + 10;
                        const cy = 100 - ((val - minVal) / (maxVal - minVal || 1)) * 80;
                        const isForecast = i >= splitIdx;
                        return (
                          <circle
                            key={`dot-${i}`}
                            cx={cx}
                            cy={cy}
                            r={i === splitIdx - 1 ? '4' : '2.5'}
                            fill={i === splitIdx - 1 ? '#EF4444' : isForecast ? '#F59E0B' : trend.color}
                            stroke="#FFF"
                            strokeWidth="1.5"
                          />
                        );
                      })}
                    </svg>

                    <div className="flex justify-between text-[9px] text-slate-400 pt-2 border-t border-slate-200">
                      {months.map((m: string, idx: number) => (
                        <span key={idx} className={idx >= splitIdx ? 'text-amber-600 font-semibold' : ''}>
                          {m}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* =========================================================================== */}
      {/* SECTION 3: DISEASE INTELLIGENCE                                            */}
      {/* =========================================================================== */}
      {activeSection === 'disease_intelligence' && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-bold text-slate-900">
                Disease Intelligence & Surveillance
              </h2>
              <p className="text-xs text-slate-500">
                Track disease trends, active cases, and short-term projections
              </p>
            </div>
            <div className="flex items-center gap-1.5">
              {['ALL', 'Vector-Borne', 'Airborne', 'Non-Communicable'].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedDiseaseCategory(cat)}
                  className={`px-3 py-1 rounded-md text-xs font-semibold transition ${
                    selectedDiseaseCategory === cat
                      ? 'bg-slate-900 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {data?.disease_intelligence?.diseases
              ?.filter((d: any) => {
                if (selectedDiseaseCategory === 'ALL') return true;
                return d.category.toLowerCase().includes(selectedDiseaseCategory.toLowerCase());
              })
              .map((disease: any) => {
                const isHigh = disease.risk.includes('HIGH');
                return (
                  <div
                    key={disease.id}
                    className="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-4 space-y-3 text-xs"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-bold text-slate-900 text-sm">{disease.name}</h4>
                        <span className="text-[11px] text-slate-500">{disease.category}</span>
                      </div>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          isHigh ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-700'
                        }`}
                      >
                        {disease.risk}
                      </span>
                    </div>

                    <div className="grid grid-cols-3 gap-2 bg-slate-50 rounded-xl p-2.5 text-center">
                      <div>
                        <span className="text-[10px] text-slate-400 block uppercase">Current</span>
                        <strong className="text-slate-800 font-bold">{disease.current_cases.toLocaleString()}</strong>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 block uppercase">Active</span>
                        <strong className="text-amber-600 font-bold">{disease.active_cases.toLocaleString()}</strong>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 block uppercase">Recovered</span>
                        <strong className="text-emerald-600 font-bold">{disease.recovered.toLocaleString()}</strong>
                      </div>
                    </div>

                    <div className="space-y-1 text-[11px] text-slate-600">
                      <div className="flex justify-between">
                        <span>7-Day Forecast:</span>
                        <strong className={disease.forecast_7d.includes('+') ? 'text-rose-600' : 'text-emerald-600'}>
                          {disease.forecast_7d}
                        </strong>
                      </div>
                      <div>
                        <strong>Area:</strong> {disease.affected_area}
                      </div>
                    </div>

                    <div className="bg-slate-50 rounded-lg p-2 text-[11px] text-slate-700 font-medium">
                      <strong>Recommendation:</strong> {disease.recommended_action}
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* =========================================================================== */}
      {/* SECTION 4: HEALTHCARE OPERATIONS                                           */}
      {/* =========================================================================== */}
      {activeSection === 'healthcare_operations' && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-5">
            <h2 className="text-base font-bold text-slate-900">
              Healthcare Operations Overview
            </h2>
            <p className="text-xs text-slate-500">
              Bed capacity, emergency intake, average waiting times, and referrals
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {[
              { label: 'Total Inpatient Beds', value: data?.healthcare_operations?.bed_capacity?.toLocaleString(), sub: `${data?.healthcare_operations?.occupied_beds?.toLocaleString()} Occupied` },
              { label: 'Bed Occupancy', value: `${data?.healthcare_operations?.bed_occupancy_pct}%`, sub: 'Ward Utilization' },
              { label: 'ICU Beds', value: `${data?.healthcare_operations?.occupied_icu}/${data?.healthcare_operations?.icu_capacity}`, sub: `${data?.healthcare_operations?.icu_occupancy_pct}% Saturation` },
              { label: 'Avg Waiting Time', value: `${data?.healthcare_operations?.avg_waiting_time_mins} mins`, sub: 'Token to Doctor' },
              { label: 'Avg Length of Stay', value: `${data?.healthcare_operations?.avg_length_of_stay_days} days`, sub: 'Inpatient Stay' },
              { label: 'Transfers Out', value: data?.healthcare_operations?.referrals_out?.toLocaleString(), sub: 'Secondary Referrals' }
            ].map((stat, idx) => (
              <div key={idx} className="bg-white rounded-xl p-3.5 border border-slate-200/90 shadow-sm space-y-1">
                <span className="text-[11px] font-semibold text-slate-400 block">{stat.label}</span>
                <div className="text-xl font-black text-slate-900">{stat.value}</div>
                <span className="text-[11px] text-slate-500 block">{stat.sub}</span>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-5 space-y-3 text-xs">
              <h4 className="font-bold text-slate-800 text-sm">Bed Occupancy Status</h4>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between font-semibold mb-1">
                    <span>General Ward Occupancy</span>
                    <span>{data?.healthcare_operations?.bed_occupancy_pct}%</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-emerald-600 h-2 rounded-full"
                      style={{ width: `${Math.min(100, data?.healthcare_operations?.bed_occupancy_pct || 80)}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between font-semibold mb-1">
                    <span>ICU Bed Saturation</span>
                    <span className="text-rose-600">{data?.healthcare_operations?.icu_occupancy_pct}%</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-rose-600 h-2 rounded-full"
                      style={{ width: `${Math.min(100, data?.healthcare_operations?.icu_occupancy_pct || 90)}%` }}
                    />
                  </div>
                </div>
              </div>
              <p className="text-slate-500 pt-2 text-[11px]">
                Recommendation: Review step-down transfers when ICU occupancy exceeds 90%.
              </p>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-5 space-y-3 text-xs">
              <h4 className="font-bold text-slate-800 text-sm">Referral & Admission Flow</h4>
              <div className="grid grid-cols-2 gap-3 bg-slate-50 p-3 rounded-xl">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-semibold block">Referrals Received</span>
                  <span className="text-base font-bold text-slate-800">
                    {data?.healthcare_operations?.referrals_in?.toLocaleString()}
                  </span>
                  <span className="text-[10px] text-slate-500 block">From Primary Centers</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-semibold block">30-Day Readmissions</span>
                  <span className="text-base font-bold text-slate-800">
                    {data?.healthcare_operations?.readmissions_30d?.toLocaleString()}
                  </span>
                  <span className="text-[10px] text-slate-500 block">Stable Discharge Rate</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================== */}
      {/* SECTION 5: PHARMACY & SUPPLY CHAIN                                         */}
      {/* =========================================================================== */}
      {activeSection === 'pharmacy_supply' && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-5 flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-bold text-slate-900">
                Pharmacy & Medicine Stock
              </h2>
              <p className="text-xs text-slate-500">
                Stock levels, burn rate, and projected stockout dates
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-1 rounded bg-slate-100 text-slate-700 text-xs font-semibold">
                FEFO Expiry: 0.0%
              </span>
              <span className="px-2.5 py-1 rounded bg-slate-100 text-slate-700 text-xs font-semibold">
                Total Valuation: {data?.pharmacy_supply?.summary?.total_inventory_valuation_inr}
              </span>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden">
            <div className="p-4 bg-slate-50 border-b border-slate-200/80 flex items-center justify-between text-xs">
              <span className="font-bold text-slate-800">Essential Medicines Status</span>
              <div className="flex items-center gap-1.5">
                {['ALL', 'CRITICAL', 'MODERATE', 'NORMAL'].map((f) => (
                  <button
                    key={f}
                    onClick={() => setSelectedMedicineFilter(f)}
                    className={`px-2.5 py-1 rounded text-xs font-semibold transition ${
                      selectedMedicineFilter === f
                        ? 'bg-slate-900 text-white'
                        : 'bg-white text-slate-600 border border-slate-200'
                    }`}
                  >
                    {f}
                  </button>
                ))}
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-100/70 text-slate-500 font-semibold border-b border-slate-200 uppercase text-[10px]">
                  <tr>
                    <th className="p-3">Medicine</th>
                    <th className="p-3 text-right">Current Stock</th>
                    <th className="p-3 text-right">Daily Burn</th>
                    <th className="p-3 text-center">Runway</th>
                    <th className="p-3 text-center">Predicted Stockout</th>
                    <th className="p-3 text-right">Recommended Reorder</th>
                    <th className="p-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data?.pharmacy_supply?.medicines
                    ?.filter((med: any) => {
                      if (selectedMedicineFilter === 'ALL') return true;
                      return med.risk === selectedMedicineFilter;
                    })
                    .map((med: any, idx: number) => {
                      const isCrit = med.risk === 'CRITICAL';
                      const isMod = med.risk === 'MODERATE';
                      return (
                        <tr key={idx} className="hover:bg-slate-50/70 transition">
                          <td className="p-3">
                            <span className="font-bold text-slate-900 block">{med.name}</span>
                            <span className="text-[10px] text-slate-400">{med.generic}</span>
                          </td>
                          <td className="p-3 text-right font-bold text-slate-900">
                            {med.current_stock.toLocaleString()}
                          </td>
                          <td className="p-3 text-right text-slate-600">
                            {med.daily_consumption.toLocaleString()} / day
                          </td>
                          <td className="p-3 text-center">
                            <span
                              className={`px-2 py-0.5 rounded font-bold text-[10px] ${
                                isCrit ? 'bg-rose-100 text-rose-700' : isMod ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'
                              }`}
                            >
                              {med.days_runway} Days
                            </span>
                          </td>
                          <td className="p-3 text-center text-slate-600">{med.predicted_stockout_date}</td>
                          <td className="p-3 text-right font-semibold text-slate-800">
                            +{med.recommended_reorder.toLocaleString()}
                          </td>
                          <td className="p-3 text-slate-600 text-[11px]">{med.po_status}</td>
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================== */}
      {/* SECTION 6: WORKFORCE INTELLIGENCE                                          */}
      {/* =========================================================================== */}
      {activeSection === 'workforce_intelligence' && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-5">
            <h2 className="text-base font-bold text-slate-900">
              Workforce Intelligence
            </h2>
            <p className="text-xs text-slate-500">
              Staff availability, shift allocations, and diagnostic workloads
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 text-xs">
            {/* Doctors */}
            <div className="bg-white rounded-xl p-4 border border-slate-200/90 shadow-sm space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-900 flex items-center gap-1.5">
                  <Stethoscope className="w-4 h-4 text-slate-600" />
                  Doctors
                </span>
                <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 font-semibold text-[10px]">
                  {data?.workforce_intelligence?.doctors?.on_duty} on duty
                </span>
              </div>
              <div className="space-y-1 text-slate-600 pt-1.5 border-t border-slate-100">
                <div className="flex justify-between">
                  <span>Total Sanctioned:</span>
                  <strong>{data?.workforce_intelligence?.doctors?.total}</strong>
                </div>
                <div className="flex justify-between">
                  <span>Patients / Doctor:</span>
                  <strong>{data?.workforce_intelligence?.doctors?.patients_per_doctor}</strong>
                </div>
              </div>
            </div>

            {/* Nurses */}
            <div className="bg-white rounded-xl p-4 border border-slate-200/90 shadow-sm space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-900 flex items-center gap-1.5">
                  <HeartPulse className="w-4 h-4 text-slate-600" />
                  Nurses
                </span>
                <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 font-semibold text-[10px]">
                  {data?.workforce_intelligence?.nurses?.on_duty} on duty
                </span>
              </div>
              <div className="space-y-1 text-slate-600 pt-1.5 border-t border-slate-100">
                <div className="flex justify-between">
                  <span>Total Sanctioned:</span>
                  <strong>{data?.workforce_intelligence?.nurses?.total}</strong>
                </div>
                <div className="flex justify-between">
                  <span>Bed Ratio:</span>
                  <strong>{data?.workforce_intelligence?.nurses?.patient_to_nurse_ratio}</strong>
                </div>
              </div>
            </div>

            {/* Lab Technicians */}
            <div className="bg-white rounded-xl p-4 border border-slate-200/90 shadow-sm space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-900 flex items-center gap-1.5">
                  <Microscope className="w-4 h-4 text-slate-600" />
                  Lab Technicians
                </span>
                <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 font-semibold text-[10px]">
                  {data?.workforce_intelligence?.lab_technicians?.on_duty} on duty
                </span>
              </div>
              <div className="space-y-1 text-slate-600 pt-1.5 border-t border-slate-100">
                <div className="flex justify-between">
                  <span>Processed Today:</span>
                  <strong>{data?.workforce_intelligence?.lab_technicians?.tests_processed?.toLocaleString()}</strong>
                </div>
                <div className="flex justify-between">
                  <span>Avg Turnaround:</span>
                  <strong>{data?.workforce_intelligence?.lab_technicians?.avg_turnaround_hrs} hrs</strong>
                </div>
              </div>
            </div>

            {/* Pharmacists */}
            <div className="bg-white rounded-xl p-4 border border-slate-200/90 shadow-sm space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-900 flex items-center gap-1.5">
                  <Pill className="w-4 h-4 text-slate-600" />
                  Pharmacists
                </span>
                <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 font-semibold text-[10px]">
                  {data?.workforce_intelligence?.pharmacists?.on_duty} on duty
                </span>
              </div>
              <div className="space-y-1 text-slate-600 pt-1.5 border-t border-slate-100">
                <div className="flex justify-between">
                  <span>Total Staff:</span>
                  <strong>{data?.workforce_intelligence?.pharmacists?.total}</strong>
                </div>
                <div className="flex justify-between">
                  <span>Processed Rxs:</span>
                  <strong>{data?.workforce_intelligence?.pharmacists?.prescriptions_processed?.toLocaleString()}</strong>
                </div>
              </div>
            </div>

            {/* Inventory Officers */}
            <div className="bg-white rounded-xl p-4 border border-slate-200/90 shadow-sm space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-900 flex items-center gap-1.5">
                  <Truck className="w-4 h-4 text-slate-600" />
                  Inventory Officers
                </span>
                <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 font-semibold text-[10px]">
                  {data?.workforce_intelligence?.inventory_officers?.on_duty} on duty
                </span>
              </div>
              <div className="space-y-1 text-slate-600 pt-1.5 border-t border-slate-100">
                <div className="flex justify-between">
                  <span>Stock Alerts:</span>
                  <strong>{data?.workforce_intelligence?.inventory_officers?.low_stock_alerts_handled}</strong>
                </div>
                <div className="flex justify-between">
                  <span>Critical Indents:</span>
                  <strong>{data?.workforce_intelligence?.inventory_officers?.critical_pos_raised}</strong>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================== */}
      {/* SECTION 7: PREDICTIONS & TRENDS                                            */}
      {/* =========================================================================== */}
      {activeSection === 'predictions_trends' && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-5">
            <h2 className="text-base font-bold text-slate-900">
              Predictions & Trends
            </h2>
            <p className="text-xs text-slate-500">
              Short-term clinical demand and resource forecasting
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {data?.predictive_intelligence?.predictions?.map((pred: any) => {
              const isCrit = pred.risk === 'CRITICAL';
              return (
                <div
                  key={pred.id}
                  className="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-5 space-y-3 text-xs"
                >
                  <div className="flex items-start justify-between">
                    <h4 className="font-bold text-slate-900 text-sm">{pred.title}</h4>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        isCrit ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'
                      }`}
                    >
                      {pred.risk}
                    </span>
                  </div>

                  <div className="space-y-2 bg-slate-50 p-3 rounded-xl border border-slate-100">
                    <div>
                      <span className="text-[10px] text-slate-400 font-semibold block uppercase">Current</span>
                      <p className="font-bold text-slate-900 text-sm">{pred.current}</p>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 font-semibold block uppercase">Forecast</span>
                      <p className="font-bold text-slate-900 text-sm">{pred.forecast}</p>
                    </div>
                  </div>

                  <div className="text-slate-700 pt-1">
                    <strong className="text-slate-900">Recommendation:</strong> {pred.recommendation}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* =========================================================================== */}
      {/* SECTION 8: ALERTS & RECOMMENDATIONS                                        */}
      {/* =========================================================================== */}
      {activeSection === 'alerts_recommendations' && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-bold text-slate-900">
                Alerts & Recommendations
              </h2>
              <p className="text-xs text-slate-500">
                Active clinical notices and suggested actions
              </p>
            </div>
            <div className="flex items-center gap-1.5">
              {['ALL', 'CRITICAL', 'HIGH', 'WARNING'].map((sev) => (
                <button
                  key={sev}
                  onClick={() => setSelectedAlertSeverity(sev)}
                  className={`px-3 py-1 rounded-md text-xs font-semibold transition ${
                    selectedAlertSeverity === sev
                      ? 'bg-slate-900 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {sev}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            {data?.alerts_actions
              ?.filter((a: any) => {
                if (selectedAlertSeverity === 'ALL') return true;
                return a.severity === selectedAlertSeverity;
              })
              .map((alert: any) => {
                const isCrit = alert.severity === 'CRITICAL';
                const isHigh = alert.severity === 'HIGH';
                return (
                  <div
                    key={alert.id}
                    className="bg-white rounded-xl p-4 border border-slate-200/90 shadow-sm space-y-1.5 text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <span>{isCrit ? '🔴' : isHigh ? '🟠' : '🟡'}</span>
                      <h4 className="font-bold text-slate-900 text-sm">
                        {alert.title} — {alert.severity === 'CRITICAL' ? 'Critical' : alert.severity === 'HIGH' ? 'High' : 'Warning'}
                      </h4>
                    </div>

                    <p className="text-slate-600 pl-6">
                      {alert.status} {alert.explanation}
                    </p>

                    <p className="text-slate-800 font-medium pl-6 pt-0.5">
                      <strong>Recommendation:</strong> {alert.recommendation}
                    </p>
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* --------------------------------------------------------------------------- */}
      {/* FOOTER NOTICE                                                               */}
      {/* --------------------------------------------------------------------------- */}
      <div className="text-center text-xs text-slate-400 py-4 space-y-0.5">
        <p className="font-medium text-slate-500">
          Government of Karnataka • Health & Family Welfare Department
        </p>
        <p className="text-[11px]">
          Demo / Synthetic Data — For healthcare intelligence and simulation across Karnataka districts.
        </p>
      </div>
    </div>
  );
};

export default PublicHealthIntelligencePage;
