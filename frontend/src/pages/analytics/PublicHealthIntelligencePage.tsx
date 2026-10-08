import React, { useState, useEffect, useMemo } from 'react';
import {
  Activity,
  Shield,
  Building2,
  Users,
  AlertTriangle,
  Pill,
  TrendingUp,
  TrendingDown,
  Clock,
  Calendar,
  Layers,
  ChevronRight,
  RefreshCw,
  Info,
  CheckCircle2,
  AlertCircle,
  Truck,
  HeartPulse,
  Stethoscope,
  Microscope,
  FileText,
  UserCheck,
  Search,
  Filter,
  Eye,
  Sliders,
  BedDouble,
  Thermometer,
  Zap
} from 'lucide-react';
import api from '../../services/api';

// Navigation Section Tabs
type NavSection =
  | 'command_center'
  | 'trend_analysis'
  | 'disease_intelligence'
  | 'healthcare_operations'
  | 'pharmacy_supply'
  | 'workforce_intelligence'
  | 'predictive_intelligence'
  | 'alerts_actions';

export const PublicHealthIntelligencePage: React.FC = () => {
  // Cascading Filter States
  const [selectedDistrict, setSelectedDistrict] = useState<string>('all');
  const [selectedZone, setSelectedZone] = useState<string>('all');
  const [selectedHospital, setSelectedHospital] = useState<string>('all');
  const [selectedTimePeriod, setSelectedTimePeriod] = useState<string>('last_30_days');
  const [selectedRoleLens, setSelectedRoleLens] = useState<string>('HOSPITAL_ADMIN');

  // Navigation State
  const [activeSection, setActiveSection] = useState<NavSection>('command_center');

  // Interactive Hover & Filter States
  const [hoveredTrendIdx, setHoveredTrendIdx] = useState<number | null>(null);
  const [hoveredBarCategory, setHoveredBarCategory] = useState<string | null>(null);
  const [selectedDiseaseCategory, setSelectedDiseaseCategory] = useState<string>('ALL');
  const [selectedMedicineFilter, setSelectedMedicineFilter] = useState<string>('ALL');
  const [selectedAlertSeverity, setSelectedAlertSeverity] = useState<string>('ALL');

  // API Data & Loading States
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch Command Center Payload
  const fetchCommandCenterData = async () => {
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
      console.error('Failed to load Karnataka Command Center data:', err);
      setError('Unable to retrieve Command Center telemetry. Please verify backend service.');
    } finally {
      setLoading(false);
    }
  };

  // Re-fetch when cascading filters or role lens change
  useEffect(() => {
    fetchCommandCenterData();
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

  // Derived filter options from API response or fallbacks
  const availableDistricts = data?.filters?.available_districts || [];
  const availableZones = data?.filters?.available_zones || [];
  const availableHospitals = data?.filters?.available_hospitals || [];
  const availableTimePeriods = data?.filters?.available_time_periods || [];
  const breadcrumbs = data?.filters?.breadcrumbs || ['Central Command', 'Karnataka State'];
  const activeScope = data?.filters?.active_scope || {
    level: 'STATE',
    name: 'Karnataka State Apex Command',
    type: 'State-Wide Healthcare Ecosystem'
  };

  // Role Lens list
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
      <div className="min-h-[80vh] flex flex-col items-center justify-center p-8 space-y-4">
        <RefreshCw className="w-10 h-10 text-emerald-600 animate-spin" />
        <h2 className="text-xl font-bold text-slate-800">Initializing Karnataka Command Center...</h2>
        <p className="text-sm text-slate-500">Aggregating state-wide telemetry across 9 districts, 21 zones, and 33 hospitals...</p>
      </div>
    );
  }

  return (
    <div className="max-w-[1600px] mx-auto space-y-6 pb-20">
      {/* --------------------------------------------------------------------------- */}
      {/* 1. TOP APEX HEADER: KARNATAKA PUBLIC HEALTH COMMAND CENTER                  */}
      {/* --------------------------------------------------------------------------- */}
      <div className="bg-slate-900 text-white rounded-2xl p-6 shadow-xl border border-slate-800 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold tracking-wide uppercase bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                Apex Telemetry Active
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                DEMO / SYNTHETIC DATA
              </span>
              <span className="text-xs text-slate-400 font-mono">
                {data?.metadata?.timestamp || 'Live Stream'}
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white flex items-center gap-3">
              <Activity className="w-8 h-8 text-emerald-400" />
              KARNATAKA PUBLIC HEALTH COMMAND CENTER
            </h1>
            <p className="text-sm text-slate-300">
              State-wide healthcare intelligence, clinical workload forecasting, and predictive governance
            </p>
          </div>

          {/* Right Action Bar */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-slate-800/90 border border-slate-700 rounded-xl px-3 py-1.5">
              <Sliders className="w-4 h-4 text-emerald-400" />
              <label htmlFor="role-lens-select" className="text-xs font-semibold text-slate-300">Role Lens:</label>
              <select
                id="role-lens-select"
                aria-label="Role Lens"
                value={selectedRoleLens}
                onChange={(e) => setSelectedRoleLens(e.target.value)}
                className="bg-transparent text-xs text-emerald-300 font-bold focus:outline-none cursor-pointer"
              >
                {roleLensOptions.map((r) => (
                  <option key={r.id} value={r.id} className="bg-slate-900 text-white">
                    {r.label}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={fetchCommandCenterData}
              disabled={loading}
              className="flex items-center gap-1.5 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold transition shadow-sm"
              title="Refresh Telemetry"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Sync Telemetry
            </button>
          </div>
        </div>

        {/* --------------------------------------------------------------------------- */}
        {/* 2. CASCADING GLOBAL DROPDOWN FILTERS & BREADCRUMBS                          */}
        {/* State -> District -> Zone -> Hospital / Facility                           */}
        {/* --------------------------------------------------------------------------- */}
        <div className="pt-5 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
            {/* 1. State Filter */}
            <div className="space-y-1">
              <label htmlFor="state-filter-select" className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">State</label>
              <div className="bg-slate-800/90 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white font-semibold flex items-center justify-between">
                <span>Karnataka (KA)</span>
                <span className="text-[10px] bg-emerald-950 text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-800">Apex</span>
              </div>
            </div>

            {/* 2. District Filter */}
            <div className="space-y-1">
              <label htmlFor="district-filter-select" className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">District</label>
              <select
                id="district-filter-select"
                aria-label="District Filter"
                value={selectedDistrict}
                onChange={(e) => handleDistrictChange(e.target.value)}
                className="w-full bg-slate-800/90 border border-slate-700 hover:border-slate-600 rounded-xl px-3 py-2 text-sm text-white font-medium focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              >
                {availableDistricts.map((d: any) => (
                  <option key={d.id} value={d.id} className="bg-slate-900 text-white">
                    {d.name}
                  </option>
                ))}
              </select>
            </div>

            {/* 3. Zone Filter */}
            <div className="space-y-1">
              <label htmlFor="zone-filter-select" className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Zone / Taluk</label>
              <select
                id="zone-filter-select"
                aria-label="Zone or Taluk Filter"
                value={selectedZone}
                onChange={(e) => handleZoneChange(e.target.value)}
                disabled={selectedDistrict === 'all'}
                className="w-full bg-slate-800/90 border border-slate-700 hover:border-slate-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl px-3 py-2 text-sm text-white font-medium focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              >
                {availableZones.map((z: any) => (
                  <option key={z.id} value={z.id} className="bg-slate-900 text-white">
                    {z.name}
                  </option>
                ))}
              </select>
            </div>

            {/* 4. Hospital Filter */}
            <div className="space-y-1">
              <label htmlFor="hospital-filter-select" className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Hospital / Facility</label>
              <select
                id="hospital-filter-select"
                aria-label="Hospital or Facility Filter"
                value={selectedHospital}
                onChange={(e) => setSelectedHospital(e.target.value)}
                disabled={selectedDistrict === 'all' && selectedZone === 'all'}
                className="w-full bg-slate-800/90 border border-slate-700 hover:border-slate-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl px-3 py-2 text-sm text-white font-medium focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              >
                {availableHospitals.map((h: any) => (
                  <option key={h.id} value={h.id} className="bg-slate-900 text-white">
                    {h.name}
                  </option>
                ))}
              </select>
            </div>

            {/* 5. Time Period Filter */}
            <div className="space-y-1">
              <label htmlFor="time-period-select" className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Time Period</label>
              <select
                id="time-period-select"
                aria-label="Time Period Filter"
                value={selectedTimePeriod}
                onChange={(e) => setSelectedTimePeriod(e.target.value)}
                className="w-full bg-slate-800/90 border border-slate-700 hover:border-slate-600 rounded-xl px-3 py-2 text-sm text-white font-medium focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              >
                {availableTimePeriods.map((t: any) => (
                  <option key={t.id} value={t.id} className="bg-slate-900 text-white">
                    {t.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Breadcrumb Navigation & Active Scope Indicator */}
          <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-950/60 border border-slate-800 rounded-xl px-4 py-2.5 text-xs">
            <div className="flex flex-wrap items-center gap-1.5 text-slate-400 font-medium">
              <span className="text-slate-500 uppercase tracking-wider font-bold text-[10px]">Active Drilldown:</span>
              {breadcrumbs.map((b: string, idx: number) => (
                <React.Fragment key={idx}>
                  {idx > 0 && <ChevronRight className="w-3.5 h-3.5 text-slate-600" />}
                  <span className={idx === breadcrumbs.length - 1 ? 'text-emerald-400 font-bold' : 'text-slate-300'}>
                    {b}
                  </span>
                </React.Fragment>
              ))}
            </div>

            <div className="flex items-center gap-3">
              <span className="text-slate-400">
                Operating Scope: <strong className="text-white">{activeScope.name}</strong> ({activeScope.type})
              </span>
              <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono font-bold">
                {activeScope.facility_count || 1} Centers • {(activeScope.total_beds || 0).toLocaleString()} Beds
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* --------------------------------------------------------------------------- */}
      {/* 3. ROLE LENS EMPHASIS BANNER (SECTION 19)                                    */}
      {/* --------------------------------------------------------------------------- */}
      <div className="bg-gradient-to-r from-emerald-950/80 via-slate-900 to-slate-900 border border-emerald-800/40 rounded-xl p-3.5 flex items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold">
            <UserCheck className="w-4 h-4" />
          </div>
          <div>
            <span className="text-emerald-400 font-bold uppercase tracking-wider block text-[10px]">
              ROLE INTELLIGENCE LENS: {data?.role_lens?.role_title || 'Hospital Administrator'}
            </span>
            <p className="text-slate-300">
              {data?.role_lens?.priority_focus}
            </p>
          </div>
        </div>
        <span className="hidden sm:inline-block px-2 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[11px] whitespace-nowrap">
          Context-Aware Telemetry
        </span>
      </div>

      {/* --------------------------------------------------------------------------- */}
      {/* 4. MAIN NAVIGATION: 8 DEDICATED SECTIONS                                    */}
      {/* --------------------------------------------------------------------------- */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 pb-2">
        {[
          { id: 'command_center', label: '1. Command Center', icon: Activity },
          { id: 'trend_analysis', label: '2. Trend Analysis', icon: TrendingUp },
          { id: 'disease_intelligence', label: '3. Disease Intelligence', icon: HeartPulse },
          { id: 'healthcare_operations', label: '4. Healthcare Operations', icon: Building2 },
          { id: 'pharmacy_supply', label: '5. Pharmacy & Supply Chain', icon: Pill },
          { id: 'workforce_intelligence', label: '6. Workforce Intelligence', icon: Users },
          { id: 'predictive_intelligence', label: '7. Predictive Intelligence', icon: Zap },
          { id: 'alerts_actions', label: '8. Alerts & Actions', icon: AlertTriangle }
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeSection === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveSection(tab.id as NavSection)}
              className={`flex items-center gap-2 px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all shadow-sm ${
                isActive
                  ? 'bg-slate-900 text-white ring-2 ring-emerald-500/50'
                  : 'bg-white hover:bg-slate-100 text-slate-600 border border-slate-200'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* =========================================================================== */}
      {/* SECTION 1: COMMAND CENTER (MAIN EXECUTIVE OVERVIEW)                         */}
      {/* =========================================================================== */}
      {activeSection === 'command_center' && (
        <div className="space-y-6">
          {/* The 5 Golden Governance Questions Card */}
          <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm grid grid-cols-1 md:grid-cols-5 gap-3 text-xs divide-y md:divide-y-0 md:divide-x divide-slate-100">
            <div className="pt-2 md:pt-0 md:px-2">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">1. What is Happening?</span>
              <p className="font-semibold text-slate-800 mt-1">
                Monsoon viral surge and elevated outpatient intake (+12.1% OPD velocity).
              </p>
            </div>
            <div className="pt-2 md:pt-0 md:px-2">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">2. Where is it Happening?</span>
              <p className="font-semibold text-slate-800 mt-1">
                {activeScope.name} ({activeScope.type}).
              </p>
            </div>
            <div className="pt-2 md:pt-0 md:px-2">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">3. Situation Trajectory?</span>
              <p className="font-semibold text-amber-700 mt-1 flex items-center gap-1">
                <TrendingUp className="w-3.5 h-3.5 text-amber-600" />
                Acute demand rising; chronic NCD BP cohort stabilized at 91.5%.
              </p>
            </div>
            <div className="pt-2 md:pt-0 md:px-2">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">4. What Happens Next?</span>
              <p className="font-semibold text-slate-800 mt-1">
                Dengue caseload expected +24% next 14 days; ICU bed ceiling at 91.8%.
              </p>
            </div>
            <div className="pt-2 md:pt-0 md:px-2">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">5. Action to Take?</span>
              <p className="font-semibold text-emerald-700 mt-1">
                Auto-indent KSMSCL PO for 30,000 ORS/Paracetamol units; deploy ASHA fever squads.
              </p>
            </div>
          </div>

          {/* 6-8 Top High-Impact KPIs */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
            {data?.command_center?.kpis?.map((kpi: any) => {
              const isWarning = kpi.status === 'warning';
              const isCritical = kpi.status === 'critical';
              return (
                <div
                  key={kpi.id}
                  className={`rounded-2xl p-3.5 border transition shadow-sm ${
                    isCritical
                      ? 'bg-rose-50/70 border-rose-200'
                      : isWarning
                      ? 'bg-amber-50/70 border-amber-200'
                      : 'bg-white border-slate-200'
                  }`}
                >
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block truncate">
                    {kpi.label}
                  </span>
                  <div className="text-xl font-black text-slate-900 mt-1">{kpi.value}</div>
                  <div className="flex items-center justify-between text-[11px] mt-1.5 pt-1 border-t border-slate-100">
                    <span className="text-slate-500 truncate">{kpi.unit}</span>
                    <span
                      className={`font-bold ${
                        isCritical ? 'text-rose-600' : isWarning ? 'text-amber-600' : 'text-emerald-600'
                      }`}
                    >
                      {kpi.change}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* District / Zone Healthcare Workload Comparison Chart */}
          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
                  <Layers className="w-5 h-5 text-emerald-600" />
                  {data?.command_center?.comparison_chart?.title || 'Healthcare Workload Comparison'}
                </h3>
                <p className="text-xs text-slate-500">
                  Comparative intake, bed capacity, and emergency volume across active jurisdiction
                </p>
              </div>
              <div className="flex items-center gap-4 text-xs">
                {data?.command_center?.comparison_chart?.series?.map((s: any, idx: number) => (
                  <div key={idx} className="flex items-center gap-1.5">
                    <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: s.color }} />
                    <span className="text-slate-600 font-medium">{s.name}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* SVG Grouped Comparison Bar Chart */}
            <div className="w-full overflow-x-auto">
              <div className="min-w-[650px] h-64 relative flex items-end justify-between px-6 pt-6 pb-8 border-b border-l border-slate-200">
                {data?.command_center?.comparison_chart?.categories?.map((cat: string, cIdx: number) => {
                  const s1Val = data.command_center.comparison_chart.series[0]?.values[cIdx] || 0;
                  const s2Val = data.command_center.comparison_chart.series[1]?.values[cIdx] || 0;
                  const maxS1 = Math.max(...(data.command_center.comparison_chart.series[0]?.values || [1]), 1);
                  const maxS2 = Math.max(...(data.command_center.comparison_chart.series[1]?.values || [1]), 1);

                  const h1 = Math.max(8, (s1Val / maxS1) * 160);
                  const h2 = Math.max(8, (s2Val / maxS2) * 160);

                  const isHovered = hoveredBarCategory === cat;

                  return (
                    <div
                      key={cIdx}
                      className="flex-1 flex flex-col items-center justify-end h-full px-1.5 group cursor-pointer"
                      onMouseEnter={() => setHoveredBarCategory(cat)}
                      onMouseLeave={() => setHoveredBarCategory(null)}
                    >
                      {/* Tooltip */}
                      {isHovered && (
                        <div className="absolute top-2 left-1/2 -translate-x-1/2 bg-slate-900 text-white rounded-lg px-3 py-1.5 text-xs shadow-lg z-20 pointer-events-none">
                          <span className="font-bold block text-emerald-400">{cat}</span>
                          <span>
                            {data.command_center.comparison_chart.series[0]?.name}: {s1Val}
                          </span>
                          <span className="block">
                            {data.command_center.comparison_chart.series[1]?.name}: {s2Val}
                          </span>
                        </div>
                      )}

                      {/* Bar Pair */}
                      <div className="flex items-end gap-1.5 w-full justify-center">
                        <div
                          style={{
                            height: `${h1}px`,
                            backgroundColor: data.command_center.comparison_chart.series[0]?.color || '#3B82F6'
                          }}
                          className="w-4 sm:w-5 rounded-t transition-all group-hover:brightness-110"
                        />
                        <div
                          style={{
                            height: `${h2}px`,
                            backgroundColor: data.command_center.comparison_chart.series[1]?.color || '#10B981'
                          }}
                          className="w-4 sm:w-5 rounded-t transition-all group-hover:brightness-110"
                        />
                      </div>

                      {/* Category Label */}
                      <span className="text-[10px] font-semibold text-slate-600 mt-2 truncate max-w-[80px] text-center">
                        {cat}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Top 3 Predictions & Critical Actionable Alerts (Side by Side) */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Predictions */}
            <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
                  <Zap className="w-5 h-5 text-amber-500" />
                  Key Predictive Forecasts
                </h3>
                <span className="text-xs text-slate-500">Early Warning Signal Engine</span>
              </div>

              <div className="space-y-3">
                {data?.command_center?.top_predictions?.map((pred: any, idx: number) => (
                  <div key={idx} className="bg-slate-50 rounded-xl p-3.5 border border-slate-200 space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-900 text-sm">{pred.title}</span>
                      <span
                        className={`px-2 py-0.5 rounded font-bold uppercase text-[10px] ${
                          pred.risk === 'CRITICAL'
                            ? 'bg-rose-100 text-rose-700'
                            : 'bg-amber-100 text-amber-700'
                        }`}
                      >
                        {pred.risk} RISK
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-slate-600">
                      <div>
                        <span className="text-slate-400 block text-[10px]">CURRENT:</span>
                        <strong className="text-slate-800">{pred.current}</strong>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px]">PREDICTED NEXT:</span>
                        <strong className="text-slate-800">{pred.prediction}</strong>
                      </div>
                    </div>
                    <div className="bg-emerald-50 rounded-lg p-2 border border-emerald-200 text-emerald-800 font-medium">
                      <strong>Action:</strong> {pred.recommended_action}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Critical Actionable Alerts */}
            <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-rose-600" />
                  Immediate Action Directives
                </h3>
                <span className="text-xs text-slate-500">Live Incident Stream</span>
              </div>

              <div className="space-y-3">
                {data?.command_center?.critical_alerts?.map((alt: any) => (
                  <div
                    key={alt.id}
                    className={`rounded-xl p-3.5 border space-y-1.5 text-xs ${
                      alt.severity === 'CRITICAL'
                        ? 'bg-rose-50/80 border-rose-200'
                        : 'bg-amber-50/80 border-amber-200'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-900 text-sm">{alt.problem}</span>
                      <span
                        className={`px-2 py-0.5 rounded font-bold uppercase text-[10px] ${
                          alt.severity === 'CRITICAL' ? 'bg-rose-600 text-white' : 'bg-amber-600 text-white'
                        }`}
                      >
                        {alt.severity}
                      </span>
                    </div>
                    <div className="text-slate-600">
                      <strong>Location:</strong> {alt.location} • <strong>Impact:</strong> {alt.impact}
                    </div>
                    <div className="text-slate-800 font-semibold pt-1">
                      ➔ Directive: {alt.recommended_action}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================== */}
      {/* SECTION 2: TREND ANALYSIS (SIMPLE LINE CHARTS HISTORICAL -> FORECAST)       */}
      {/* =========================================================================== */}
      {activeSection === 'trend_analysis' && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-2">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-emerald-600" />
                  Longitudinal Healthcare Trends & Multi-Month Forecasts
                </h2>
                <p className="text-xs text-slate-500">
                  Tracking 10 months of historical baseline (Jan–Oct 2026) and 2 months of predictive forecasts (Nov–Dec 2026)
                </p>
              </div>
              <div className="flex items-center gap-3 text-xs">
                <span className="flex items-center gap-1.5">
                  <span className="w-4 h-1 bg-emerald-600 rounded" />
                  <span className="text-slate-600 font-medium">Historical Baseline</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-4 h-1 bg-amber-500 border-dashed rounded" />
                  <span className="text-slate-600 font-medium">Forecast (Projected)</span>
                </span>
              </div>
            </div>
          </div>

          {/* 7 Clean Simple Trend Cards with SVG Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {[
              {
                id: 'opd',
                title: 'Patient / Outpatient (OPD) Visits',
                series: data?.trend_analysis?.series?.opd || [],
                unit: 'Visits',
                direction: 'Increasing (+12.1%)',
                color: '#2563EB',
                action: 'Surging demand during seasonal transition; expand registration windows.'
              },
              {
                id: 'ipd',
                title: 'Inpatient (IPD) Admissions',
                series: data?.trend_analysis?.series?.ipd || [],
                unit: 'Admissions',
                direction: 'Stable (+4.2%)',
                color: '#059669',
                action: 'Steady admissions rate; regular bed turnover maintained.'
              },
              {
                id: 'emergency',
                title: 'Emergency & Trauma Presentations',
                series: data?.trend_analysis?.series?.emergency || [],
                unit: 'Cases',
                direction: 'Increasing (+18.6%)',
                color: '#DC2626',
                action: 'Acute trauma surge; alert night shift casualty surgeons.'
              },
              {
                id: 'disease',
                title: 'Vector-Borne (Dengue & Enteric) Caseload',
                series: data?.trend_analysis?.series?.disease_cases || [],
                unit: 'Active Cases',
                direction: 'Peak Vector Wave',
                color: '#D97706',
                action: 'Cases peaked at month 9; larvicidal intervention beginning to taper.'
              },
              {
                id: 'bed_occupancy',
                title: 'Bed Occupancy Percentage (%)',
                series: data?.trend_analysis?.series?.bed_occupancy || [],
                unit: '% Occupancy',
                direction: 'High Load (84.6%)',
                color: '#7C3AED',
                action: 'Approaching critical ward saturation in major district centers.'
              },
              {
                id: 'medicine',
                title: 'Medicine Consumption Velocity',
                series: data?.trend_analysis?.series?.medicine_consumption || [],
                unit: 'Units Dispensed',
                direction: 'Accelerating (+16.4%)',
                color: '#0D9488',
                action: 'Rising antibiotic and antipyretic burn; maintain 15-day safety buffer.'
              }
            ].map((trend) => {
              const months = data?.trend_analysis?.months || [];
              const splitIdx = data?.trend_analysis?.split_index || 10;
              const maxVal = Math.max(...trend.series, 1);
              const minVal = Math.min(...trend.series, 0);

              return (
                <div key={trend.id} className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-bold text-slate-800 text-sm">{trend.title}</h4>
                      <span className="text-xs font-semibold text-emerald-600">{trend.direction}</span>
                    </div>
                    <span className="text-xs text-slate-400 font-mono">
                      Current: {trend.series[splitIdx - 1]?.toLocaleString()} {trend.unit}
                    </span>
                  </div>

                  {/* Clean SVG Line Chart */}
                  <div className="w-full h-44 relative bg-slate-50/50 rounded-xl p-3 border border-slate-100 flex flex-col justify-end">
                    <svg viewBox="0 0 500 120" className="w-full h-28 overflow-visible">
                      {/* Grid lines */}
                      <line x1="0" y1="20" x2="500" y2="20" stroke="#E2E8F0" strokeDasharray="3,3" />
                      <line x1="0" y1="60" x2="500" y2="60" stroke="#E2E8F0" strokeDasharray="3,3" />
                      <line x1="0" y1="100" x2="500" y2="100" stroke="#E2E8F0" strokeDasharray="3,3" />

                      {/* Historical Solid Line (0 to splitIdx - 1) */}
                      {trend.series.slice(0, splitIdx).map((val: number, i: number, arr: number[]) => {
                        if (i === arr.length - 1) return null;
                        const x1 = (i / 11) * 480 + 10;
                        const y1 = 110 - ((val - minVal) / (maxVal - minVal || 1)) * 90;
                        const x2 = ((i + 1) / 11) * 480 + 10;
                        const y2 = 110 - ((arr[i + 1] - minVal) / (maxVal - minVal || 1)) * 90;
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

                      {/* Forecast Dashed Line (splitIdx - 1 to end) */}
                      {trend.series.slice(splitIdx - 1).map((val: number, i: number, arr: number[]) => {
                        if (i === arr.length - 1) return null;
                        const actualIdx = splitIdx - 1 + i;
                        const x1 = (actualIdx / 11) * 480 + 10;
                        const y1 = 110 - ((val - minVal) / (maxVal - minVal || 1)) * 90;
                        const x2 = ((actualIdx + 1) / 11) * 480 + 10;
                        const y2 = 110 - ((arr[i + 1] - minVal) / (maxVal - minVal || 1)) * 90;
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

                      {/* Data Dots */}
                      {trend.series.map((val: number, i: number) => {
                        const cx = (i / 11) * 480 + 10;
                        const cy = 110 - ((val - minVal) / (maxVal - minVal || 1)) * 90;
                        const isForecast = i >= splitIdx;
                        return (
                          <circle
                            key={`dot-${i}`}
                            cx={cx}
                            cy={cy}
                            r={i === splitIdx - 1 ? "4.5" : "3"}
                            fill={i === splitIdx - 1 ? "#EF4444" : isForecast ? "#F59E0B" : trend.color}
                            stroke="#FFF"
                            strokeWidth="1.5"
                          />
                        );
                      })}
                    </svg>

                    {/* Month Labels */}
                    <div className="flex justify-between text-[9px] text-slate-400 font-mono pt-2 border-t border-slate-200">
                      {months.map((m: string, idx: number) => (
                        <span key={idx} className={idx >= splitIdx ? 'text-amber-600 font-bold' : ''}>
                          {m}
                        </span>
                      ))}
                    </div>
                  </div>

                  <p className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                    <strong>Operational Directive:</strong> {trend.action}
                  </p>
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
          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <HeartPulse className="w-5 h-5 text-rose-600" />
                State-Wide Communicable & Chronic Disease Intelligence
              </h2>
              <p className="text-xs text-slate-500">
                Active surveillance, epidemiological clustering, and multi-week outbreak trajectory
              </p>
            </div>
            {/* Filter by Category */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 font-medium">Filter:</span>
              {['ALL', 'Vector-Borne', 'Airborne', 'Non-Communicable'].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedDiseaseCategory(cat)}
                  className={`px-3 py-1 rounded-lg text-xs font-bold transition ${
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

          {/* Disease Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {data?.disease_intelligence?.diseases
              ?.filter((d: any) => {
                if (selectedDiseaseCategory === 'ALL') return true;
                return d.category.toLowerCase().includes(selectedDiseaseCategory.toLowerCase());
              })
              .map((disease: any) => {
                const isHighRisk = disease.risk.includes('HIGH');
                return (
                  <div
                    key={disease.id}
                    className={`bg-white rounded-2xl p-4 border shadow-sm space-y-3 transition ${
                      isHighRisk ? 'border-rose-300 ring-1 ring-rose-200' : 'border-slate-200'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-bold text-slate-900 text-sm">{disease.name}</h4>
                        <span className="text-[10px] text-slate-500 block">{disease.category}</span>
                      </div>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          isHighRisk ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-700'
                        }`}
                      >
                        {disease.risk}
                      </span>
                    </div>

                    <div className="grid grid-cols-3 gap-2 bg-slate-50 rounded-xl p-2.5 text-center text-xs">
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

                    <div className="space-y-1 text-xs">
                      <div className="flex justify-between text-slate-600">
                        <span>7-Day Forecast:</span>
                        <strong className={disease.forecast_7d.includes('+') ? 'text-rose-600' : 'text-emerald-600'}>
                          {disease.forecast_7d}
                        </strong>
                      </div>
                      <div className="flex justify-between text-slate-600">
                        <span>14-Day Trajectory:</span>
                        <strong className="text-slate-800">{disease.forecast_14d}</strong>
                      </div>
                      <div className="text-slate-500 text-[11px] pt-1">
                        <strong>Epicenter:</strong> {disease.affected_area}
                      </div>
                    </div>

                    <div className="bg-emerald-50/80 rounded-lg p-2 text-[11px] text-emerald-900 border border-emerald-200 font-medium">
                      <strong>Directive:</strong> {disease.recommended_action}
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
          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-1">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Building2 className="w-5 h-5 text-emerald-600" />
              Healthcare Capacity & Clinical Inflow Telemetry
            </h2>
            <p className="text-xs text-slate-500">
              Inpatient bed utilization, critical care ICU surge, emergency trauma throughput, and inter-facility referrals
            </p>
          </div>

          {/* Operations Stat Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {[
              { label: 'Total Inpatient Beds', value: data?.healthcare_operations?.bed_capacity?.toLocaleString(), sub: `${data?.healthcare_operations?.occupied_beds?.toLocaleString()} Occupied`, color: 'text-slate-900' },
              { label: 'Bed Occupancy %', value: `${data?.healthcare_operations?.bed_occupancy_pct}%`, sub: 'Ward Load Factor', color: 'text-purple-600' },
              { label: 'ICU Critical Care Beds', value: `${data?.healthcare_operations?.occupied_icu}/${data?.healthcare_operations?.icu_capacity}`, sub: `${data?.healthcare_operations?.icu_occupancy_pct}% Saturation`, color: 'text-rose-600' },
              { label: 'Avg Waiting Time', value: `${data?.healthcare_operations?.avg_waiting_time_mins} mins`, sub: 'Registration to Doctor', color: 'text-amber-600' },
              { label: 'Avg Length of Stay', value: `${data?.healthcare_operations?.avg_length_of_stay_days} days`, sub: 'Inpatient Discharge Cycle', color: 'text-blue-600' },
              { label: 'Active Transfers Out', value: data?.healthcare_operations?.referrals_out?.toLocaleString(), sub: 'Tertiary Escalations', color: 'text-emerald-600' }
            ].map((stat, idx) => (
              <div key={idx} className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">{stat.label}</span>
                <div className={`text-xl font-black ${stat.color}`}>{stat.value}</div>
                <span className="text-[11px] text-slate-500 block">{stat.sub}</span>
              </div>
            ))}
          </div>

          {/* Detailed Bed & Referral Status Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-3 text-xs">
              <h4 className="font-bold text-slate-800 text-sm flex items-center gap-2">
                <BedDouble className="w-4 h-4 text-purple-600" />
                Inpatient Bed & ICU Surge Status
              </h4>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between font-semibold mb-1">
                    <span>General Ward Occupancy</span>
                    <span>{data?.healthcare_operations?.bed_occupancy_pct}%</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                    <div
                      className="bg-purple-600 h-2.5 rounded-full"
                      style={{ width: `${Math.min(100, data?.healthcare_operations?.bed_occupancy_pct || 80)}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between font-semibold mb-1">
                    <span>ICU Ventilator Bed Capacity</span>
                    <span className="text-rose-600">{data?.healthcare_operations?.icu_occupancy_pct}% Saturation</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                    <div
                      className="bg-rose-600 h-2.5 rounded-full"
                      style={{ width: `${Math.min(100, data?.healthcare_operations?.icu_occupancy_pct || 90)}%` }}
                    />
                  </div>
                </div>
              </div>
              <p className="text-slate-600 pt-2 border-t border-slate-100">
                <strong>Administrative Takeaway:</strong> When ICU occupancy crosses 90%, initiate secondary hospital transfer protocols for stabilized post-operative patients to free ventilator slots.
              </p>
            </div>

            <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-3 text-xs">
              <h4 className="font-bold text-slate-800 text-sm flex items-center gap-2">
                <Truck className="w-4 h-4 text-blue-600" />
                Inter-Facility Referral Inflow & Discharge Velocity
              </h4>
              <div className="grid grid-cols-2 gap-3 bg-slate-50 p-3 rounded-xl">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-bold block">Referrals Received</span>
                  <span className="text-base font-bold text-slate-800">
                    {data?.healthcare_operations?.referrals_in?.toLocaleString()}
                  </span>
                  <span className="text-[10px] text-slate-500 block">From PHCs & CHCs</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-bold block">30-Day Readmissions</span>
                  <span className="text-base font-bold text-emerald-700">
                    {data?.healthcare_operations?.readmissions_30d?.toLocaleString()}
                  </span>
                  <span className="text-[10px] text-emerald-600 block">Low Complication Rate (3.8%)</span>
                </div>
              </div>
              <p className="text-slate-600 pt-1">
                <strong>Care Continuity:</strong> Digital discharge summaries synchronized directly with primary clinic NCD registries for home follow-up.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================== */}
      {/* SECTION 5: PHARMACY & SUPPLY CHAIN + MEDICINE PREDICTIONS                   */}
      {/* =========================================================================== */}
      {activeSection === 'pharmacy_supply' && (
        <div className="space-y-6">
          {/* Pharmacy Summary Banner */}
          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <Pill className="w-5 h-5 text-emerald-600" />
                State-Wide Pharmaceutical Inventory & KSMSCL Procurement
              </h2>
              <p className="text-xs text-slate-500">
                FEFO compliance, multi-month burn velocity, and automated stock-out prevention triggers
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-bold">
                FEFO Expiry: 0.0% Wastage
              </span>
              <span className="px-3 py-1 rounded-lg bg-blue-50 text-blue-700 border border-blue-200 text-xs font-bold">
                Valuation: {data?.pharmacy_supply?.summary?.total_inventory_valuation_inr}
              </span>
            </div>
          </div>

          {/* Essential Generic Medicines Audit Table */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-4 bg-slate-50 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs">
              <div>
                <h3 className="font-bold text-slate-800 text-sm">Essential Generics: Burn Velocity & Reorder Runways</h3>
                <span className="text-slate-500">Historical consumption versus forecast stockout dates</span>
              </div>
              <div className="flex items-center gap-2">
                {['ALL', 'CRITICAL', 'MODERATE', 'NORMAL'].map((f) => (
                  <button
                    key={f}
                    onClick={() => setSelectedMedicineFilter(f)}
                    className={`px-3 py-1 rounded-lg text-xs font-bold transition ${
                      selectedMedicineFilter === f
                        ? 'bg-slate-900 text-white'
                        : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-100'
                    }`}
                  >
                    {f}
                  </button>
                ))}
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-100 text-slate-500 font-semibold border-b border-slate-200 uppercase text-[10px]">
                  <tr>
                    <th className="p-3">Medicine & Generic</th>
                    <th className="p-3 text-right">Current Stock</th>
                    <th className="p-3 text-right">Daily Burn</th>
                    <th className="p-3 text-center">Runway</th>
                    <th className="p-3 text-center">Predicted Stockout</th>
                    <th className="p-3 text-right">Recommended Reorder</th>
                    <th className="p-3">Procurement Directive</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data?.pharmacy_supply?.medicines
                    ?.filter((med: any) => {
                      if (selectedMedicineFilter === 'ALL') return true;
                      return med.risk === selectedMedicineFilter;
                    })
                    .map((med: any, idx: number) => {
                      const isCritical = med.risk === 'CRITICAL';
                      const isMod = med.risk === 'MODERATE';
                      return (
                        <tr key={idx} className="hover:bg-slate-50/80 transition">
                          <td className="p-3">
                            <span className="font-bold text-slate-900 block">{med.name}</span>
                            <span className="text-[10px] text-slate-500">{med.generic}</span>
                          </td>
                          <td className="p-3 text-right font-bold text-slate-900">
                            {med.current_stock.toLocaleString()}
                          </td>
                          <td className="p-3 text-right text-slate-600">
                            {med.daily_consumption.toLocaleString()} / day
                          </td>
                          <td className="p-3 text-center">
                            <span
                              className={`px-2 py-0.5 rounded font-bold uppercase text-[10px] ${
                                isCritical
                                  ? 'bg-rose-100 text-rose-700'
                                  : isMod
                                  ? 'bg-amber-100 text-amber-700'
                                  : 'bg-emerald-100 text-emerald-700'
                              }`}
                            >
                              {med.days_runway} Days
                            </span>
                          </td>
                          <td className="p-3 text-center font-medium text-slate-700">
                            {med.predicted_stockout_date}
                          </td>
                          <td className="p-3 text-right font-bold text-emerald-700">
                            +{med.recommended_reorder.toLocaleString()} Units
                          </td>
                          <td className="p-3 text-slate-600">
                            <span className="font-medium">{med.po_status}</span>
                          </td>
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
          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-1">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Users className="w-5 h-5 text-emerald-600" />
              Healthcare Workforce & Duty Roster Intelligence
            </h2>
            <p className="text-xs text-slate-500">
              Staff availability, shift-strain ratios, diagnostic turnaround workload, and clinical staffing projections
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {/* Doctors */}
            <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-900 flex items-center gap-1.5">
                  <Stethoscope className="w-4 h-4 text-blue-600" />
                  Medical Doctors
                </span>
                <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-bold text-[10px]">
                  {data?.workforce_intelligence?.doctors?.on_duty} on duty
                </span>
              </div>
              <div className="space-y-1 text-slate-600 pt-2 border-t border-slate-100">
                <div className="flex justify-between">
                  <span>Total Sanctioned:</span>
                  <strong>{data?.workforce_intelligence?.doctors?.total}</strong>
                </div>
                <div className="flex justify-between">
                  <span>Patients / Doctor:</span>
                  <strong className="text-slate-900">{data?.workforce_intelligence?.doctors?.patients_per_doctor}</strong>
                </div>
                <div className="flex justify-between">
                  <span>Workload Status:</span>
                  <strong className="text-amber-600">{data?.workforce_intelligence?.doctors?.workload_status}</strong>
                </div>
              </div>
            </div>

            {/* Staff Nurses */}
            <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-900 flex items-center gap-1.5">
                  <HeartPulse className="w-4 h-4 text-rose-600" />
                  Staff Nurses
                </span>
                <span className="px-2 py-0.5 rounded bg-rose-100 text-rose-800 font-bold text-[10px]">
                  {data?.workforce_intelligence?.nurses?.on_duty} on duty
                </span>
              </div>
              <div className="space-y-1 text-slate-600 pt-2 border-t border-slate-100">
                <div className="flex justify-between">
                  <span>Total Sanctioned:</span>
                  <strong>{data?.workforce_intelligence?.nurses?.total}</strong>
                </div>
                <div className="flex justify-between">
                  <span>Bed-to-Nurse Ratio:</span>
                  <strong className="text-slate-900">{data?.workforce_intelligence?.nurses?.patient_to_nurse_ratio}</strong>
                </div>
                <div className="flex justify-between">
                  <span>Shift Strain:</span>
                  <strong className="text-rose-600">{data?.workforce_intelligence?.nurses?.workload_status}</strong>
                </div>
              </div>
            </div>

            {/* Lab Technicians */}
            <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-900 flex items-center gap-1.5">
                  <Microscope className="w-4 h-4 text-purple-600" />
                  Lab Technicians
                </span>
                <span className="px-2 py-0.5 rounded bg-purple-100 text-purple-800 font-bold text-[10px]">
                  {data?.workforce_intelligence?.lab_technicians?.on_duty} on duty
                </span>
              </div>
              <div className="space-y-1 text-slate-600 pt-2 border-t border-slate-100">
                <div className="flex justify-between">
                  <span>Processed Today:</span>
                  <strong>{data?.workforce_intelligence?.lab_technicians?.tests_processed?.toLocaleString()}</strong>
                </div>
                <div className="flex justify-between">
                  <span>Pending Tests:</span>
                  <strong className="text-amber-600">{data?.workforce_intelligence?.lab_technicians?.pending_tests}</strong>
                </div>
                <div className="flex justify-between">
                  <span>Avg Turnaround:</span>
                  <strong>{data?.workforce_intelligence?.lab_technicians?.avg_turnaround_hrs} hrs</strong>
                </div>
              </div>
            </div>

            {/* Pharmacists */}
            <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-900 flex items-center gap-1.5">
                  <Pill className="w-4 h-4 text-emerald-600" />
                  Pharmacists
                </span>
                <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold text-[10px]">
                  {data?.workforce_intelligence?.pharmacists?.on_duty} on duty
                </span>
              </div>
              <div className="space-y-1 text-slate-600 pt-2 border-t border-slate-100">
                <div className="flex justify-between">
                  <span>Total Staff:</span>
                  <strong>{data?.workforce_intelligence?.pharmacists?.total}</strong>
                </div>
                <div className="flex justify-between">
                  <span>Processed Rxs:</span>
                  <strong>{data?.workforce_intelligence?.pharmacists?.prescriptions_processed?.toLocaleString()}</strong>
                </div>
                <div className="flex justify-between">
                  <span>Pace:</span>
                  <strong className="text-emerald-700">{data?.workforce_intelligence?.pharmacists?.workload_status}</strong>
                </div>
              </div>
            </div>

            {/* Inventory Officers */}
            <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-900 flex items-center gap-1.5">
                  <Truck className="w-4 h-4 text-amber-600" />
                  Inventory Officers
                </span>
                <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-bold text-[10px]">
                  {data?.workforce_intelligence?.inventory_officers?.on_duty} on duty
                </span>
              </div>
              <div className="space-y-1 text-slate-600 pt-2 border-t border-slate-100">
                <div className="flex justify-between">
                  <span>Active Stock Alerts:</span>
                  <strong className="text-rose-600">{data?.workforce_intelligence?.inventory_officers?.low_stock_alerts_handled}</strong>
                </div>
                <div className="flex justify-between">
                  <span>Critical Indents:</span>
                  <strong>{data?.workforce_intelligence?.inventory_officers?.critical_pos_raised}</strong>
                </div>
                <div className="flex justify-between">
                  <span>KSMSCL Follow-up:</span>
                  <strong className="text-blue-600">Active</strong>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================== */}
      {/* SECTION 7: PREDICTIVE INTELLIGENCE (COMPLETE FORECAST SUITE)                */}
      {/* =========================================================================== */}
      {activeSection === 'predictive_intelligence' && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-1">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Zap className="w-5 h-5 text-amber-500" />
              Authoritative Public Health Predictive Intelligence Suite
            </h2>
            <p className="text-xs text-slate-500">
              Epidemiological AI models, hospital queue surge predictions, and medicine stock-out projections
            </p>
          </div>

          {/* 6 Structured Prediction Cards (Current -> Trend -> Prediction -> Risk -> Action) */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {data?.predictive_intelligence?.predictions?.map((pred: any) => {
              const isCritical = pred.risk === 'CRITICAL';
              return (
                <div
                  key={pred.id}
                  className={`bg-white rounded-2xl p-5 border shadow-sm space-y-3 text-xs transition ${
                    isCritical ? 'border-rose-300 ring-1 ring-rose-200' : 'border-slate-200'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">
                        {pred.category}
                      </span>
                      <h4 className="font-bold text-slate-900 text-sm mt-0.5">{pred.title}</h4>
                    </div>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        isCritical ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'
                      }`}
                    >
                      {pred.risk} RISK
                    </span>
                  </div>

                  <div className="space-y-2 bg-slate-50 p-3 rounded-xl border border-slate-100">
                    <div>
                      <span className="text-[10px] text-slate-400 font-bold block uppercase">Current Baseline:</span>
                      <p className="font-medium text-slate-800">{pred.current}</p>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 font-bold block uppercase">Observed Trend:</span>
                      <p className="font-medium text-slate-800">{pred.trend}</p>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 font-bold block uppercase">Predictive Horizon:</span>
                      <p className="font-bold text-rose-600">{pred.prediction}</p>
                    </div>
                  </div>

                  <div className="bg-emerald-50 rounded-xl p-3 border border-emerald-200 text-emerald-900">
                    <span className="text-[10px] uppercase font-bold text-emerald-700 block">Recommended Public Health Action:</span>
                    <p className="font-semibold mt-0.5">{pred.recommended_action}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* =========================================================================== */}
      {/* SECTION 8: ALERTS & ACTIONS                                                 */}
      {/* =========================================================================== */}
      {activeSection === 'alerts_actions' && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-rose-600" />
                Actionable Public Health Directives & Operational Signals
              </h2>
              <p className="text-xs text-slate-500">
                Statutory clinical alerts categorized by urgency level with prescribed executive action
              </p>
            </div>
            {/* Severity Filter Tabs */}
            <div className="flex items-center gap-2">
              {['ALL', 'CRITICAL', 'HIGH', 'WARNING', 'NORMAL'].map((sev) => (
                <button
                  key={sev}
                  onClick={() => setSelectedAlertSeverity(sev)}
                  className={`px-3 py-1 rounded-lg text-xs font-bold transition ${
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
                const isWarn = alert.severity === 'WARNING';

                const borderCol = isCrit
                  ? 'border-rose-300 bg-rose-50/50'
                  : isHigh
                  ? 'border-amber-300 bg-amber-50/50'
                  : isWarn
                  ? 'border-yellow-300 bg-yellow-50/50'
                  : 'border-emerald-300 bg-emerald-50/50';

                const badgeCol = isCrit
                  ? 'bg-rose-600 text-white'
                  : isHigh
                  ? 'bg-amber-600 text-white'
                  : isWarn
                  ? 'bg-yellow-500 text-slate-900'
                  : 'bg-emerald-600 text-white';

                return (
                  <div key={alert.id} className={`rounded-2xl p-4 border shadow-sm space-y-2 text-xs ${borderCol}`}>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <span className={`px-2.5 py-0.5 rounded font-black text-[10px] uppercase ${badgeCol}`}>
                          {alert.severity}
                        </span>
                        <h4 className="font-bold text-slate-900 text-sm">{alert.problem}</h4>
                      </div>
                      <span className="text-slate-400 font-mono text-[11px]">{alert.location}</span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-slate-700 bg-white/70 p-3 rounded-xl border border-slate-200/50">
                      <div>
                        <span className="text-[10px] text-slate-400 font-bold block uppercase">Clinical & Operational Impact:</span>
                        <p className="font-medium text-slate-800">{alert.impact}</p>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 font-bold block uppercase">Prescribed Directive / Protocol:</span>
                        <p className="font-bold text-emerald-800">{alert.recommended_action}</p>
                      </div>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* --------------------------------------------------------------------------- */}
      {/* APEX FOOTER WITH SYNTHETIC DATA GOVERNANCE NOTICE                           */}
      {/* --------------------------------------------------------------------------- */}
      <div className="bg-slate-100 rounded-2xl p-4 border border-slate-200 text-center text-xs text-slate-500 space-y-1">
        <p className="font-semibold text-slate-700">
          Government of Karnataka • Health & Family Welfare Department • Public Health Command Center Telemetry
        </p>
        <p className="text-[11px]">
          Classification: <strong>DEMO / SYNTHETIC DATA</strong> — Built for simulated state-wide clinical decision support across all 31 administrative districts.
        </p>
      </div>
    </div>
  );
};

export default PublicHealthIntelligencePage;
