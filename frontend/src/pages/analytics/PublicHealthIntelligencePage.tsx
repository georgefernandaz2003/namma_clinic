import React, { useState, useEffect } from 'react';
import {
  Globe,
  TrendingUp,
  Brain,
  Building2,
  Users,
  Activity,
  AlertTriangle,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Pill,
  TestTube,
  Calendar,
  Layers,
  MapPin,
  ChevronRight,
  Filter,
  BarChart3,
  Flame,
  Droplets,
  HeartPulse,
  Package,
  RefreshCw,
  ExternalLink,
  ArrowUpRight,
  ArrowDownRight,
  CheckCircle,
  HelpCircle,
  Sparkles,
  Info,
  Truck,
  Landmark
} from 'lucide-react';
import api from '../../services/api';

type TabType = 'hierarchy' | 'trends' | 'predictive';
type LevelType = 'ALL' | 'STATE' | 'DISTRICT' | 'ZONE' | 'WARD' | 'FACILITY';

export const PublicHealthIntelligencePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('hierarchy');
  const [selectedLevel, setSelectedLevel] = useState<LevelType>('ALL');
  const [selectedMedFilter, setSelectedMedFilter] = useState<string>('ALL');
  const [hoveredMonthIdx, setHoveredMonthIdx] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [multiLevelData, setMultiLevelData] = useState<any>(null);
  const [trendData, setTrendData] = useState<any>(null);
  const [predictiveData, setPredictiveData] = useState<any>(null);

  const fetchAllAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const [mlRes, trRes, prRes] = await Promise.all([
        api.get('analytics/multi-level/'),
        api.get('analytics/trends/'),
        api.get('analytics/predictive/'),
      ]);
      setMultiLevelData(mlRes.data);
      setTrendData(trRes.data);
      setPredictiveData(prRes.data);
    } catch (err: any) {
      console.error('Failed to load analytics', err);
      setError('Unable to load public health intelligence data. Ensure the backend server is active.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllAnalytics();
  }, []);

  const executiveSummary = multiLevelData?.executive_summary || {};
  const urbanRuralStory = multiLevelData?.urban_rural_story || {};
  const stateInfo = multiLevelData?.state || {};
  const districts = multiLevelData?.districts || [];
  const zones = multiLevelData?.zones || [];
  const wards = multiLevelData?.wards || [];
  const facilities = multiLevelData?.facilities || [];

  const trendStory = trendData?.trend_story || {};
  const monthlyFootfall = trendData?.monthly_footfall || [];
  const epidemicCurves = trendData?.epidemic_curve || [];
  const ncdTrajectories = trendData?.ncd_trajectories || [];

  const supplyChainSummary = predictiveData?.supply_chain_summary || {};
  const medicinesStockHistory = predictiveData?.medicines_stock_history || predictiveData?.pharmacy_stock_runway || [];
  const outbreakRisks = predictiveData?.outbreak_risk_predictions || [];
  const surgeForecast = predictiveData?.patient_surge_forecast || {};

  const filteredMedicines = selectedMedFilter === 'ALL'
    ? medicinesStockHistory
    : medicinesStockHistory.filter((m: any) =>
        selectedMedFilter === 'REORDER' ? (m.buffer_status?.includes('REORDER') || m.buffer_status?.includes('CRITICAL')) : true
      );

  return (
    <div className="space-y-6 pb-16">
      {/* 1. EXECUTIVE STORY HERO BANNER */}
      <div className="bg-gradient-to-r from-slate-950 via-teal-950 to-emerald-950 rounded-2xl p-6 text-white shadow-xl relative overflow-hidden border border-emerald-900/40">
        <div className="absolute right-0 top-0 translate-x-12 -translate-y-8 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 space-y-4">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                <span className="px-3 py-0.5 bg-emerald-500/20 text-emerald-300 text-[11px] font-black rounded-full uppercase tracking-wider border border-emerald-400/30 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping inline-block" />
                  Government of Karnataka • Health & Family Welfare
                </span>
                <span className="text-xs text-emerald-200/90 font-semibold flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  Public Health Intelligence & Predictive Governance
                </span>
              </div>
              <h1 className="text-2xl lg:text-3xl font-black tracking-tight text-white flex items-center gap-3">
                Healthcare Intelligence & Predictive Analytics
              </h1>
            </div>
            <button
              onClick={fetchAllAnalytics}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-emerald-600/30 hover:bg-emerald-600/50 border border-emerald-500/40 rounded-xl text-xs font-bold text-emerald-200 transition shadow-xs self-start lg:self-center"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Refresh Intelligence
            </button>
          </div>

          {/* Narrative Story Bar */}
          <div className="bg-slate-900/80 backdrop-blur-md rounded-xl p-4 border border-emerald-500/20 shadow-inner">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-emerald-500/20 text-emerald-300 rounded-lg mt-0.5 shrink-0">
                <Sparkles className="w-4 h-4" />
              </div>
              <div className="space-y-1.5">
                <p className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Executive Situation Report</p>
                <p className="text-sm font-extrabold text-white leading-relaxed">
                  {executiveSummary.headline || "Urban Outbreak Contained in West Zone • NCD Cohort Blood Pressure Control Reaches 91.5% • Critical KSMSCL Reorder Triggered for Metformin"}
                </p>
                <div className="flex flex-wrap gap-2 pt-1">
                  <span className="px-2.5 py-0.5 bg-emerald-950/80 border border-emerald-700/50 text-emerald-300 text-[11px] rounded-md font-semibold">
                    EPIDEMIOLOGY: Ward 68 Dengue Vector Fogging Dispatched
                  </span>
                  <span className="px-2.5 py-0.5 bg-blue-950/80 border border-blue-700/50 text-blue-300 text-[11px] rounded-md font-semibold">
                    CLINICAL OUTCOME: 91.5% Chronic BP Cohort Control
                  </span>
                  <span className="px-2.5 py-0.5 bg-amber-950/80 border border-amber-700/50 text-amber-300 text-[11px] rounded-md font-semibold">
                    SUPPLY CHAIN: KSMSCL PO-2026-10-88 Raised
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* 6 High-Impact Operational KPI Ribbons */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-1">
            <div className="bg-slate-900/60 border border-slate-700/50 rounded-xl p-3">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Registered Citizens</span>
              <span className="text-xl font-black text-white">{stateInfo.registered_citizens || 75}</span>
              <span className="text-[10px] text-emerald-400 block mt-0.5 font-medium">100% Verified Identifiers</span>
            </div>
            <div className="bg-slate-900/60 border border-slate-700/50 rounded-xl p-3">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Total Encounters</span>
              <span className="text-xl font-black text-white">{stateInfo.total_opd_encounters || 123}</span>
              <span className="text-[10px] text-blue-400 block mt-0.5 font-medium">OPD & Follow-ups</span>
            </div>
            <div className="bg-slate-900/60 border border-slate-700/50 rounded-xl p-3">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Active NCD Cohort</span>
              <span className="text-xl font-black text-white">{stateInfo.active_ncd_patients || 29}</span>
              <span className="text-[10px] text-emerald-400 block mt-0.5 font-medium">91.5% Stabilized BP/Sugar</span>
            </div>
            <div className="bg-slate-900/60 border border-slate-700/50 rounded-xl p-3">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">IDSP Surveillance</span>
              <span className="text-xl font-black text-amber-400">{stateInfo.communicable_surveillance_cases || 16}</span>
              <span className="text-[10px] text-amber-300/80 block mt-0.5 font-medium">Vector & Enteric Watch</span>
            </div>
            <div className="bg-slate-900/60 border border-slate-700/50 rounded-xl p-3">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Diagnostic Tests</span>
              <span className="text-xl font-black text-white">{stateInfo.diagnostic_tests_conducted || 75}</span>
              <span className="text-[10px] text-purple-400 block mt-0.5 font-medium">Lab Verified Reports</span>
            </div>
            <div className="bg-slate-900/60 border border-slate-700/50 rounded-xl p-3">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Pharmacy Dispensed</span>
              <span className="text-xl font-black text-emerald-400">{stateInfo.pharmacy_dispensations || 211}</span>
              <span className="text-[10px] text-emerald-300/80 block mt-0.5 font-medium">FEFO Ledger Audited</span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. PRIMARY TAB NAVIGATION */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-white p-2 rounded-2xl border border-slate-200 shadow-xs">
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            onClick={() => setActiveTab('hierarchy')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-black transition ${
              activeTab === 'hierarchy'
                ? 'bg-slate-900 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <Globe className="w-4 h-4 text-emerald-400" />
            1. Multi-Level Hierarchy & Urban vs. Rural Story
          </button>
          <button
            onClick={() => setActiveTab('trends')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-black transition ${
              activeTab === 'trends'
                ? 'bg-slate-900 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <TrendingUp className="w-4 h-4 text-blue-400" />
            2. Longitudinal Trend Analysis (Visual Charts)
          </button>
          <button
            onClick={() => setActiveTab('predictive')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-black transition ${
              activeTab === 'predictive'
                ? 'bg-slate-900 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <Brain className="w-4 h-4 text-purple-400" />
            3. Predictive Intelligence & Stock History (MoM / YoY)
          </button>
        </div>

        {activeTab === 'hierarchy' && (
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-slate-500">Filter Level:</span>
            <select
              value={selectedLevel}
              onChange={(e) => setSelectedLevel(e.target.value as LevelType)}
              className="text-xs font-bold bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="ALL">All Jurisdictions</option>
              <option value="STATE">State Level (Karnataka)</option>
              <option value="DISTRICT">District Level (Urban vs. Rural)</option>
              <option value="ZONE">Zone Level (4 Zones)</option>
              <option value="WARD">Ward Level (5 Catchment Wards)</option>
              <option value="FACILITY">Facility Level (PHC vs Rural)</option>
            </select>
          </div>
        )}
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs font-semibold flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {/* =========================================================================
          TAB 1: MULTI-LEVEL HIERARCHY & URBAN VS. RURAL STORY
          ========================================================================= */}
      {activeTab === 'hierarchy' && (
        <div className="space-y-6">
          {/* THE URBAN VS. RURAL HEALTHCARE DISPARITY STORY CARD */}
          {(selectedLevel === 'ALL' || selectedLevel === 'DISTRICT' || selectedLevel === 'FACILITY') && (
            <div className="bg-gradient-to-br from-slate-900 to-slate-950 text-white rounded-2xl p-6 border border-slate-800 shadow-lg space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
                <div>
                  <span className="px-2.5 py-0.5 bg-emerald-500/20 text-emerald-300 text-[10px] font-black rounded-full uppercase tracking-wider border border-emerald-500/30">
                    Comparative Healthcare Architecture
                  </span>
                  <h2 className="text-lg font-black text-white mt-1">
                    Urban vs. Rural Healthcare Burden Sharing & Clinical Velocity
                  </h2>
                  <p className="text-xs text-slate-400">
                    How high-density urban sentinel clinics protect tertiary hospitals, while rural outposts maintain chronic elder continuity.
                  </p>
                </div>
                <div className="text-right shrink-0">
                  <span className="text-[11px] font-bold text-slate-400 block">Total Active Catchment</span>
                  <span className="text-sm font-black text-emerald-400">227,000 Karnataka Citizens</span>
                </div>
              </div>

              {/* Side-by-side comparison */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Urban Card */}
                <div className="p-5 rounded-xl bg-slate-800/60 border border-cyan-800/40 space-y-3 relative overflow-hidden">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="px-2 py-0.5 bg-cyan-500/20 text-cyan-300 text-[10px] font-bold rounded-md uppercase">
                        {urbanRuralStory.urban?.tag || "HIGH-VELOCITY SENTINEL HUB"}
                      </span>
                      <h3 className="text-base font-black text-white mt-1">
                        {urbanRuralStory.urban?.district_name || "BBMP Central (Bengaluru Urban)"}
                      </h3>
                      <p className="text-[11px] text-cyan-200/70 font-mono">
                        {urbanRuralStory.urban?.facility_name || "Namma Clinic Local PHC [PHC-LOCAL-01]"}
                      </p>
                    </div>
                    <Building2 className="w-8 h-8 text-cyan-400/50" />
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">
                    {urbanRuralStory.urban?.story || "High population density creates acute infection waves. Absorbs 108 encounters and dispenses 196 generic medicines, offloading critical dengue and surgical cases to KC General Hospital."}
                  </p>

                  <div className="p-3 bg-cyan-950/40 rounded-lg border border-cyan-800/30 text-[11px] text-cyan-300 font-medium">
                    <strong className="text-white">Demographic Vulnerability:</strong> {urbanRuralStory.urban?.vulnerability_context || "28.4% slum catchment density with seasonal storm-water drainage vulnerability."}
                  </div>

                  <div className="grid grid-cols-4 gap-2 pt-2 border-t border-slate-700 text-center">
                    <div>
                      <span className="text-[10px] text-slate-400 block font-semibold">Patients</span>
                      <span className="text-sm font-black text-white">60</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block font-semibold">OPD Visits</span>
                      <span className="text-sm font-black text-cyan-400">108</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block font-semibold">Dispensations</span>
                      <span className="text-sm font-black text-emerald-400">196</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block font-semibold">Referrals Out</span>
                      <span className="text-sm font-black text-amber-400">8</span>
                    </div>
                  </div>
                </div>

                {/* Rural Card */}
                <div className="p-5 rounded-xl bg-slate-800/60 border border-emerald-800/40 space-y-3 relative overflow-hidden">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-300 text-[10px] font-bold rounded-md uppercase">
                        {urbanRuralStory.rural?.tag || "CHRONIC CONTINUITY & BUFFER STABILITY"}
                      </span>
                      <h3 className="text-base font-black text-white mt-1">
                        {urbanRuralStory.rural?.district_name || "Bengaluru Rural (Varthur / Hoskote)"}
                      </h3>
                      <p className="text-[11px] text-emerald-200/70 font-mono">
                        {urbanRuralStory.rural?.facility_name || "Varthur Rural Primary Clinic A4 [RC-A4-01]"}
                      </p>
                    </div>
                    <Landmark className="w-8 h-8 text-emerald-400/50" />
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">
                    {urbanRuralStory.rural?.story || "Serves dispersed agrarian elderly population focused on continuous hypertension and diabetes maintenance. Zero secondary hospital transfers needed, but requires larger buffer stock due to 11-day central warehouse transit lead times."}
                  </p>

                  <div className="p-3 bg-emerald-950/40 rounded-lg border border-emerald-800/30 text-[11px] text-emerald-300 font-medium">
                    <strong className="text-white">Demographic Vulnerability:</strong> {urbanRuralStory.rural?.vulnerability_context || "12.1% remote agrarian accessibility index with decentralized farm outreach."}
                  </div>

                  <div className="grid grid-cols-4 gap-2 pt-2 border-t border-slate-700 text-center">
                    <div>
                      <span className="text-[10px] text-slate-400 block font-semibold">Patients</span>
                      <span className="text-sm font-black text-white">15</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block font-semibold">OPD Visits</span>
                      <span className="text-sm font-black text-emerald-400">15</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block font-semibold">Dispensations</span>
                      <span className="text-sm font-black text-emerald-400">15</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block font-semibold">Referrals Out</span>
                      <span className="text-sm font-black text-slate-400">0</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Strategic Governance Takeaway */}
              <div className="p-4 bg-emerald-950/30 border border-emerald-800/40 rounded-xl flex items-start gap-3">
                <Info className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                <p className="text-xs text-emerald-200 leading-relaxed font-medium">
                  <strong>Strategic Takeaway:</strong> {urbanRuralStory.strategic_takeaway || "Urban clinics require agile daily queue triage and fast tertiary transfer channels; Rural outposts require enlarged medicine buffers to absorb central depot delivery latency."}
                </p>
              </div>
            </div>
          )}

          {/* JURISDICTION LEVEL BREAKDOWN CARDS */}
          {/* 1. STATE LEVEL */}
          {(selectedLevel === 'ALL' || selectedLevel === 'STATE') && (
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div>
                  <h3 className="text-base font-black text-slate-900 flex items-center gap-2">
                    <Globe className="w-5 h-5 text-emerald-600" />
                    Karnataka State Level Health Summary
                  </h3>
                  <p className="text-xs text-slate-500">Apex jurisdiction governing municipal primary health centers</p>
                </div>
                <span className="text-xs font-black text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200">
                  State Code: KA • Capital: Bengaluru
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <p className="text-[10px] font-bold text-slate-500 uppercase">State Population Coverage</p>
                  <p className="text-xl font-black text-slate-900 mt-1">61.1 Million</p>
                  <p className="text-[10px] text-slate-500">Across 31 Districts</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <p className="text-[10px] font-bold text-slate-500 uppercase">Registered Citizens (Demo Network)</p>
                  <p className="text-xl font-black text-emerald-700 mt-1">{stateInfo.registered_citizens || 75}</p>
                  <p className="text-[10px] text-emerald-700 font-medium">100% Identity Bound</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <p className="text-[10px] font-bold text-slate-500 uppercase">Clinical Encounters</p>
                  <p className="text-xl font-black text-blue-900 mt-1">{stateInfo.total_opd_encounters || 123}</p>
                  <p className="text-[10px] text-blue-700 font-medium">OPD & Follow-ups</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <p className="text-[10px] font-bold text-slate-500 uppercase">Active Facilities</p>
                  <p className="text-xl font-black text-purple-900 mt-1">{facilities.length || 2} Centers</p>
                  <p className="text-[10px] text-purple-700 font-medium">Urban PHC + Rural Clinic</p>
                </div>
              </div>
            </div>
          )}

          {/* 2. DISTRICT LEVEL */}
          {(selectedLevel === 'ALL' || selectedLevel === 'DISTRICT') && (
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div>
                  <h3 className="text-base font-black text-slate-900 flex items-center gap-2">
                    <Building2 className="w-5 h-5 text-indigo-600" />
                    District Level Breakdown (Urban vs. Rural)
                  </h3>
                  <p className="text-xs text-slate-500">Comparative operational and surveillance statistics between administrative districts</p>
                </div>
                <span className="text-xs font-bold text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded-lg border border-indigo-200">
                  2 Districts Under Active Coverage
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {districts.map((d: any, idx: number) => (
                  <div key={idx} className="p-5 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white hover:border-indigo-300 transition shadow-xs space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-extrabold text-sm text-slate-900">{d.name}</h4>
                          <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-slate-200 text-slate-800">
                            {d.code}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-0.5">Headquarters: {d.headquarters}</p>
                      </div>
                      <span className="text-xs font-bold text-indigo-900 bg-indigo-100 px-2.5 py-0.5 rounded-md">
                        {d.total_facilities} Facility
                      </span>
                    </div>

                    <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-200/60">
                      <div>
                        <p className="text-[10px] font-semibold text-slate-500">Patients</p>
                        <p className="text-base font-black text-slate-900">{d.total_patients}</p>
                      </div>
                      <div>
                        <p className="text-[10px] font-semibold text-slate-500">OPD Visits</p>
                        <p className="text-base font-black text-blue-900">{d.total_visits}</p>
                      </div>
                      <div>
                        <p className="text-[10px] font-semibold text-slate-500">Surveillance</p>
                        <p className="text-base font-black text-rose-900">{d.surveillance_cases} cases</p>
                      </div>
                    </div>

                    <div className="pt-2 border-t border-slate-200/60 flex items-center justify-between text-xs">
                      <span className="text-slate-500 font-medium">Prescriptions: <strong className="text-slate-800">{d.prescriptions_issued}</strong></span>
                      <span className="text-slate-500 font-medium">Dispensations: <strong className="text-emerald-700">{d.dispensations_completed}</strong></span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 3. WARD LEVEL */}
          {(selectedLevel === 'ALL' || selectedLevel === 'WARD') && (
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div>
                  <h3 className="text-base font-black text-slate-900 flex items-center gap-2">
                    <MapPin className="w-5 h-5 text-amber-600" />
                    Ward Level Public Health Distribution (5 Catchment Wards)
                  </h3>
                  <p className="text-xs text-slate-500">Local municipal ward populations, registered citizens, and disease surveillance density</p>
                </div>
                <span className="text-xs font-bold text-amber-800 bg-amber-50 px-2.5 py-1 rounded-lg border border-amber-200">
                  Catchment Ward Breakdown
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {wards.map((w: any, idx: number) => (
                  <div key={idx} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white hover:border-amber-300 transition shadow-xs space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="font-extrabold text-sm text-slate-900">{w.name}</h4>
                      <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-amber-100 text-amber-900">
                        Ward #{w.ward_number}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500">Zone: <strong className="text-slate-700">{w.zone_name}</strong></p>

                    <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-200 text-center">
                      <div>
                        <span className="text-[9px] text-slate-500 block uppercase font-bold">Population</span>
                        <span className="text-xs font-black text-slate-800">{w.population?.toLocaleString() || "N/A"}</span>
                      </div>
                      <div>
                        <span className="text-[9px] text-slate-500 block uppercase font-bold">Patients</span>
                        <span className="text-xs font-black text-emerald-700">{w.registered_citizens}</span>
                      </div>
                      <div>
                        <span className="text-[9px] text-slate-500 block uppercase font-bold">IDSP Cases</span>
                        <span className={`text-xs font-black ${w.surveillance_cases > 3 ? 'text-rose-700' : 'text-slate-700'}`}>
                          {w.surveillance_cases}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 4. FACILITY LEVEL */}
          {(selectedLevel === 'ALL' || selectedLevel === 'FACILITY') && (
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div>
                  <h3 className="text-base font-black text-slate-900 flex items-center gap-2">
                    <Activity className="w-5 h-5 text-emerald-600" />
                    Facility Level Performance & Clinical Velocity
                  </h3>
                  <p className="text-xs text-slate-500">Direct comparison between Primary Urban Clinic and Rural Outreach Center</p>
                </div>
                <span className="text-xs font-bold text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200">
                  2 Operational Primary Centers
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {facilities.map((f: any, idx: number) => (
                  <div key={idx} className="p-5 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white hover:border-emerald-300 transition shadow-xs space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-extrabold text-sm text-slate-900">{f.facility_name}</h4>
                          <span className="px-2 py-0.5 text-[10px] font-bold rounded-md bg-emerald-100 text-emerald-800">
                            {f.facility_code}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-0.5">Type: {f.facility_type} • District: {f.district_name}</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-4 gap-2 pt-2 border-t border-slate-200 text-center">
                      <div>
                        <span className="text-[10px] text-slate-500 block font-semibold">PATIENTS</span>
                        <span className="text-base font-black text-slate-900">{f.registered_citizens}</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-500 block font-semibold">OPD VISITS</span>
                        <span className="text-base font-black text-blue-900">{f.total_opd_encounters}</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-500 block font-semibold">DISPENSED</span>
                        <span className="text-base font-black text-emerald-700">{f.pharmacy_dispensations}</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-500 block font-semibold">REFERRALS</span>
                        <span className="text-base font-black text-rose-700">{f.referrals_initiated}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* =========================================================================
          TAB 2: LONGITUDINAL TREND ANALYSIS (WITH VISUAL CHARTS)
          ========================================================================= */}
      {activeTab === 'trends' && (
        <div className="space-y-6">
          {/* Executive Narrative Callout */}
          <div className="bg-gradient-to-r from-blue-950 via-slate-900 to-indigo-950 text-white rounded-2xl p-6 border border-blue-900/40 shadow-lg space-y-3">
            <div className="flex items-center gap-2 text-blue-400 font-bold text-xs uppercase tracking-wider">
              <TrendingUp className="w-4 h-4" />
              Longitudinal Clinical Trajectory Story
            </div>
            <h2 className="text-xl font-black text-white">
              {trendStory.headline || "From Crisis Intake to Clinical Control: How Continuous Generic Therapy Changed Patient Outcomes"}
            </h2>
            <p className="text-xs text-slate-300 leading-relaxed">
              {trendStory.key_achievement || "Over 90 days, mean systolic blood pressure dropped by 17.9 mmHg, driving cohort clinical control from 52.0% to 91.5%."}
            </p>
            <div className="flex flex-wrap gap-3 pt-2">
              <span className="px-3 py-1 bg-emerald-500/20 text-emerald-300 text-xs font-bold rounded-lg border border-emerald-500/30">
                14 Secondary Hospitalizations Averted
              </span>
              <span className="px-3 py-1 bg-blue-500/20 text-blue-300 text-xs font-bold rounded-lg border border-blue-500/30">
                123 Total Clinical Encounters Tracked
              </span>
            </div>
          </div>

          {/* CHART 1: MONTHLY CARE VELOCITY (GROUPED SVG BAR & LINE CHART) */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-black text-slate-900 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-blue-600" />
                  4-Month Longitudinal Utilization & Care Velocity (July – October 2026)
                </h3>
                <p className="text-xs text-slate-500">Visual comparison of monthly OPD visits, prescriptions, and diagnostic lab tests</p>
              </div>
              <div className="flex items-center gap-4 text-xs font-bold">
                <span className="flex items-center gap-1.5 text-blue-800">
                  <span className="w-3 h-3 rounded-xs bg-blue-600 inline-block" /> OPD Visits
                </span>
                <span className="flex items-center gap-1.5 text-emerald-800">
                  <span className="w-3 h-3 rounded-xs bg-emerald-500 inline-block" /> Prescriptions
                </span>
                <span className="flex items-center gap-1.5 text-purple-800">
                  <span className="w-3 h-3 rounded-full bg-purple-600 inline-block" /> Lab Tests (Line)
                </span>
              </div>
            </div>

            {/* SVG Interactive Grouped Bar Chart */}
            <div className="pt-4">
              <div className="relative h-64 w-full bg-slate-50/60 rounded-xl p-4 border border-slate-200 flex items-end justify-between gap-4">
                {/* Horizontal gridlines */}
                <div className="absolute inset-x-4 top-8 border-b border-slate-200/60 text-[10px] text-slate-400">100 units</div>
                <div className="absolute inset-x-4 top-24 border-b border-slate-200/60 text-[10px] text-slate-400">60 units</div>
                <div className="absolute inset-x-4 top-40 border-b border-slate-200/60 text-[10px] text-slate-400">20 units</div>

                {monthlyFootfall.map((m: any, idx: number) => {
                  const maxVal = 120;
                  const vHeight = Math.min(100, (m.opd_visits / maxVal) * 100);
                  const rxHeight = Math.min(100, (m.prescriptions / maxVal) * 100);
                  const labHeight = Math.min(100, (m.lab_tests / maxVal) * 100);

                  return (
                    <div
                      key={idx}
                      className="flex-1 flex flex-col items-center h-full justify-end relative group cursor-pointer"
                      onMouseEnter={() => setHoveredMonthIdx(idx)}
                      onMouseLeave={() => setHoveredMonthIdx(null)}
                    >
                      {/* Tooltip on hover */}
                      {hoveredMonthIdx === idx && (
                        <div className="absolute -top-16 z-20 bg-slate-900 text-white text-[11px] rounded-lg px-3 py-2 shadow-xl border border-slate-700 whitespace-nowrap space-y-0.5">
                          <p className="font-bold text-emerald-400">{m.month}: {m.mom_growth}</p>
                          <p className="text-slate-300">OPD: {m.opd_visits} • Rx: {m.prescriptions} • Labs: {m.lab_tests}</p>
                          <p className="text-[10px] text-slate-400">{m.narrative}</p>
                        </div>
                      )}

                      {/* Bar Group */}
                      <div className="w-full flex items-end justify-center gap-2 h-48">
                        {/* OPD Bar */}
                        <div
                          style={{ height: `${Math.max(vHeight, 8)}%` }}
                          className="w-5 bg-gradient-to-t from-blue-700 to-blue-500 rounded-t-md hover:brightness-110 transition-all shadow-xs relative"
                        >
                          <span className="absolute -top-4 inset-x-0 text-center text-[10px] font-black text-blue-900">
                            {m.opd_visits}
                          </span>
                        </div>
                        {/* Prescription Bar */}
                        <div
                          style={{ height: `${Math.max(rxHeight, 8)}%` }}
                          className="w-5 bg-gradient-to-t from-emerald-600 to-emerald-400 rounded-t-md hover:brightness-110 transition-all shadow-xs relative"
                        >
                          <span className="absolute -top-4 inset-x-0 text-center text-[10px] font-black text-emerald-800">
                            {m.prescriptions}
                          </span>
                        </div>
                        {/* Lab Test Indicator */}
                        <div
                          style={{ height: `${Math.max(labHeight, 8)}%` }}
                          className="w-3 bg-purple-400 rounded-t-xs hover:brightness-110 transition-all shadow-xs relative"
                        >
                          <div className="w-2.5 h-2.5 rounded-full bg-purple-700 absolute -top-1 -left-0.5 border border-white" />
                        </div>
                      </div>

                      {/* Month Label */}
                      <div className="mt-3 text-center">
                        <span className="text-xs font-black text-slate-800 block">{m.month}</span>
                        <span className="text-[10px] font-bold text-emerald-700 block">{m.mom_growth}</span>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Monthly Story Callout Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-4">
                {monthlyFootfall.map((m: any, idx: number) => (
                  <div key={idx} className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 text-xs space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-extrabold text-slate-900">{m.month}</span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-800">
                        {m.utilization_pct}% Capacity
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-600 leading-snug">{m.narrative}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* CHART 2: IDSP COMMUNICABLE EPIDEMIC CURVES & OUTBREAK THRESHOLD */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-black text-slate-900 flex items-center gap-2">
                  <Flame className="w-5 h-5 text-rose-600" />
                  IDSP Communicable Epidemic Curves & Threshold Monitoring
                </h3>
                <p className="text-xs text-slate-500">Statutory disease weekly surveillance curves with red outbreak alert threshold</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 bg-rose-50 border border-rose-200 text-rose-700 text-xs font-bold rounded-lg flex items-center gap-1.5">
                  <span className="w-2.5 h-0.5 bg-rose-600 inline-block border-t-2 border-dashed border-rose-600" />
                  Alert Threshold Line (4 Cases)
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {epidemicCurves.map((c: any, idx: number) => (
                <div key={idx} className="p-4 rounded-xl border border-slate-200 bg-slate-50/70 hover:bg-white hover:border-slate-300 transition shadow-xs space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-extrabold text-sm text-slate-900">{c.disease_name}</h4>
                      <span className="text-[10px] text-slate-500">{c.transmission}</span>
                    </div>
                    <span className={`text-[10px] font-black px-2 py-0.5 rounded-md ${
                      c.status === 'ALERT_CONTAINED' ? 'bg-rose-100 text-rose-800' : 'bg-emerald-100 text-emerald-800'
                    }`}>
                      {c.status}
                    </span>
                  </div>

                  {/* Visual Mini Weekly Sparkline */}
                  <div className="h-16 flex items-end gap-1.5 bg-white p-2 rounded-lg border border-slate-200/80 relative">
                    {/* Dotted threshold line */}
                    <div className="absolute inset-x-2 top-4 border-b border-dashed border-rose-400" />
                    {c.weekly_data.map((w: any, wIdx: number) => {
                      const h = Math.min(100, (w.cases / 4) * 100);
                      const isOver = w.cases >= 3;
                      return (
                        <div key={wIdx} className="flex-1 flex flex-col items-center h-full justify-end group relative">
                          <div
                            style={{ height: `${Math.max(h, 10)}%` }}
                            className={`w-full rounded-t-xs transition-all ${
                              isOver ? 'bg-rose-500' : 'bg-slate-400 group-hover:bg-blue-500'
                            }`}
                          />
                          <span className="text-[8px] text-slate-400 mt-1">{w.week.split(' ')[1]}</span>
                        </div>
                      );
                    })}
                  </div>

                  <p className="text-[11px] text-slate-600 leading-snug">
                    {c.story}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* CHART 3: NCD CLINICAL OUTCOME TRAJECTORY (BP & DIABETES CONTROL) */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-black text-slate-900 flex items-center gap-2">
                  <HeartPulse className="w-5 h-5 text-emerald-600" />
                  NCD Longitudinal Clinical Trajectory (Chronic Disease Control)
                </h3>
                <p className="text-xs text-slate-500">Quarterly blood pressure and glycemic stabilization under continuous generic medicine</p>
              </div>
              <span className="text-xs font-black text-emerald-800 bg-emerald-50 px-3 py-1 rounded-lg border border-emerald-200">
                Current Control Rate: 91.5%
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {ncdTrajectories.map((n: any, idx: number) => (
                <div key={idx} className="p-4 rounded-xl border border-slate-200 bg-slate-50 hover:bg-white hover:border-emerald-300 transition shadow-xs space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-black text-sm text-slate-900">{n.month}</span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                      {n.stage}
                    </span>
                  </div>

                  <div className="space-y-2 pt-1 border-t border-slate-200">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500 font-semibold">Mean Blood Pressure:</span>
                      <strong className={`font-black ${n.avg_systolic_bp > 140 ? 'text-rose-700' : 'text-emerald-700'}`}>
                        {n.avg_systolic_bp} / {n.avg_diastolic_bp} mmHg
                      </strong>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500 font-semibold">Fasting Blood Sugar:</span>
                      <strong className={`font-black ${n.avg_fasting_sugar > 140 ? 'text-amber-700' : 'text-emerald-700'}`}>
                        {n.avg_fasting_sugar} mg/dL
                      </strong>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500 font-semibold">Cohort Control %:</span>
                      <strong className="text-emerald-700 font-black">{n.control_rate_pct}%</strong>
                    </div>

                    {/* Visual Progress Meter */}
                    <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden mt-1">
                      <div
                        style={{ width: `${n.control_rate_pct}%` }}
                        className="bg-gradient-to-r from-emerald-500 to-teal-600 h-full rounded-full transition-all duration-500"
                      />
                    </div>
                  </div>

                  <p className="text-[11px] text-slate-600 leading-snug pt-1">
                    {n.narrative}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 3: PREDICTIVE INTELLIGENCE & STOCK HISTORY (MoM / YoY STOCKS)
          ========================================================================= */}
      {activeTab === 'predictive' && (
        <div className="space-y-6">
          {/* Pharmacy Supply Chain Headline Summary */}
          <div className="bg-gradient-to-r from-slate-900 via-teal-950 to-slate-950 text-white rounded-2xl p-6 border border-teal-900/40 shadow-lg space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div>
                <span className="px-2.5 py-0.5 bg-teal-500/20 text-teal-300 text-[10px] font-black rounded-full uppercase tracking-wider border border-teal-500/30">
                  KSMSCL State Procurement & Inventory Governance
                </span>
                <h2 className="text-lg font-black text-white mt-1">
                  Pharmacy Stock Movement, Historical Comparison & Automated Runway Forecast
                </h2>
                <p className="text-xs text-slate-400">
                  Tracks current shelf stocks, previous month (MoM), baseline, and year-ago (YoY) levels with automated reorder triggers.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-3 py-1 bg-emerald-500/20 text-emerald-300 text-xs font-bold rounded-lg border border-emerald-500/30">
                  FEFO Expiry: 0.0% Wastage
                </span>
              </div>
            </div>

            {/* 4 Summary Inventory Stat Badges */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
                <span className="text-[10px] text-slate-400 block font-bold uppercase">Total Inventory Valuation</span>
                <span className="text-lg font-black text-white">₹{supplyChainSummary.total_inventory_valuation_inr?.toLocaleString() || "2,84,500"}</span>
                <span className="text-[10px] text-emerald-400 block font-medium">Generic Price Schedule</span>
              </div>
              <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
                <span className="text-[10px] text-slate-400 block font-bold uppercase">Active Shelf Stock</span>
                <span className="text-lg font-black text-teal-400">{supplyChainSummary.total_shelf_stock_units?.toLocaleString() || "9,420"} Units</span>
                <span className="text-[10px] text-teal-300/80 block font-medium">Batch Verified</span>
              </div>
              <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
                <span className="text-[10px] text-slate-400 block font-bold uppercase">Monthly Inflow (Oct)</span>
                <span className="text-lg font-black text-blue-400">+{supplyChainSummary.monthly_inflow_units || 800} Units</span>
                <span className="text-[10px] text-blue-300/80 block font-medium">KSMSCL GRN Delivery</span>
              </div>
              <div className="bg-slate-800/60 p-3 rounded-xl border border-slate-700/60">
                <span className="text-[10px] text-slate-400 block font-bold uppercase">Monthly Dispensed (Oct)</span>
                <span className="text-lg font-black text-emerald-400">-{supplyChainSummary.monthly_outflow_units || 1970} Units</span>
                <span className="text-[10px] text-emerald-300/80 block font-medium">Patient Consumption</span>
              </div>
            </div>
          </div>

          {/* COMPREHENSIVE PHARMACY STOCK AUDIT TABLE (MONTHLY & YEARLY WISE) */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-black text-slate-900 flex items-center gap-2">
                  <Package className="w-5 h-5 text-teal-600" />
                  Essential Generic Medicines: Monthly, YoY & Reorder Runway Audit
                </h3>
                <p className="text-xs text-slate-500">Historical stock progression, monthly burn velocity, and automated KSMSCL procurement triggers</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setSelectedMedFilter('ALL')}
                  className={`px-3 py-1 text-xs font-bold rounded-lg border transition ${
                    selectedMedFilter === 'ALL'
                      ? 'bg-slate-900 text-white border-slate-900'
                      : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  All Generics ({medicinesStockHistory.length})
                </button>
                <button
                  onClick={() => setSelectedMedFilter('REORDER')}
                  className={`px-3 py-1 text-xs font-bold rounded-lg border transition ${
                    selectedMedFilter === 'REORDER'
                      ? 'bg-amber-600 text-white border-amber-600'
                      : 'bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100'
                  }`}
                >
                  Reorder Required
                </button>
              </div>
            </div>

            {/* Comprehensive Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500 bg-slate-50/80 uppercase text-[10px] font-bold">
                    <th className="py-3 px-3">Medicine & Generic Formulation</th>
                    <th className="py-3 px-2 text-right">Current Stock (Oct 2026)</th>
                    <th className="py-3 px-2 text-right">Last Month (Sep 2026)</th>
                    <th className="py-3 px-2 text-right">Baseline (Jul 2026)</th>
                    <th className="py-3 px-2 text-right">Last Year (Oct 2025)</th>
                    <th className="py-3 px-2 text-right">Oct Inflow / Outflow</th>
                    <th className="py-3 px-2 text-right">Daily Burn</th>
                    <th className="py-3 px-3 text-center">Runway Days</th>
                    <th className="py-3 px-3">Procurement Action & Story</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredMedicines.map((m: any, idx: number) => {
                    const isReorder = m.buffer_status?.includes('REORDER') || m.buffer_status?.includes('CRITICAL');
                    return (
                      <tr key={idx} className="hover:bg-slate-50/60 transition">
                        <td className="py-3.5 px-3">
                          <p className="font-extrabold text-slate-900 text-xs">{m.medicine_name}</p>
                          <span className="text-[10px] text-slate-500 block">{m.category} • {m.medicine_code}</span>
                        </td>
                        <td className="py-3.5 px-2 text-right">
                          <span className="font-black text-slate-900 text-sm">{m.current_stock_oct?.toLocaleString() || m.current_usable_stock?.toLocaleString()}</span>
                          <span className={`block text-[10px] font-bold ${
                            m.mom_stock_delta_pct > 0 ? 'text-emerald-600' : 'text-amber-600'
                          }`}>
                            {m.mom_stock_delta_pct > 0 ? `+${m.mom_stock_delta_pct}%` : `${m.mom_stock_delta_pct || 0}%`} MoM
                          </span>
                        </td>
                        <td className="py-3.5 px-2 text-right font-semibold text-slate-700">
                          {m.last_month_stock_sep?.toLocaleString() || "-"}
                        </td>
                        <td className="py-3.5 px-2 text-right font-semibold text-slate-500">
                          {m.baseline_stock_jul?.toLocaleString() || "-"}
                        </td>
                        <td className="py-3.5 px-2 text-right font-semibold text-slate-500">
                          {m.same_period_last_year?.toLocaleString() || "-"}
                        </td>
                        <td className="py-3.5 px-2 text-right">
                          <span className="text-[11px] font-bold text-blue-700">+{m.monthly_receipts_oct || 0} In</span>
                          <span className="text-[11px] font-bold text-rose-700 block">-{m.monthly_dispensed_oct || 0} Out</span>
                        </td>
                        <td className="py-3.5 px-2 text-right font-black text-slate-800">
                          {m.daily_burn_rate} /day
                        </td>
                        <td className="py-3.5 px-3 text-center">
                          <div className="inline-block">
                            <span className={`px-2.5 py-0.5 rounded-full text-xs font-black block ${
                              isReorder ? 'bg-amber-100 text-amber-900 border border-amber-300' : 'bg-emerald-100 text-emerald-900 border border-emerald-300'
                            }`}>
                              {m.predicted_runway_days} Days
                            </span>
                            <span className="text-[9px] text-slate-400 mt-0.5 block">Reorder at 15d</span>
                          </div>
                        </td>
                        <td className="py-3.5 px-3 max-w-xs">
                          <p className="text-[11px] text-slate-700 leading-snug">
                            {m.procurement_story || `Stock runway is ${m.predicted_runway_days} days under current consumption velocity.`}
                          </p>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* WARD-LEVEL OUTBREAK RISK PREDICTOR & QUEUE SURGE */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Outbreak Risk AI Index */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div>
                  <h3 className="text-base font-black text-slate-900 flex items-center gap-2">
                    <Flame className="w-5 h-5 text-rose-600" />
                    Ward Outbreak Risk Scoring (Epidemiological AI Index)
                  </h3>
                  <p className="text-xs text-slate-500">Calculated from fever clustering, slum vector density, and municipal drainage status</p>
                </div>
                <span className="text-xs font-bold text-rose-700 bg-rose-50 px-2.5 py-1 rounded-lg border border-rose-200">
                  5 Catchment Wards
                </span>
              </div>

              <div className="space-y-3">
                {outbreakRisks.map((w: any, idx: number) => {
                  const isHigh = w.risk_level === 'HIGH';
                  const isMod = w.risk_level === 'MODERATE';
                  return (
                    <div key={idx} className={`p-3.5 rounded-xl border transition space-y-2 ${
                      isHigh ? 'bg-rose-50/70 border-rose-200' : isMod ? 'bg-amber-50/50 border-amber-200' : 'bg-slate-50 border-slate-200'
                    }`}>
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="font-extrabold text-sm text-slate-900">{w.ward_name}</span>
                          <span className="text-xs text-slate-500 ml-1.5">(Ward #{w.ward_number} • {w.zone_name})</span>
                        </div>
                        <span className={`text-[10px] font-black px-2 py-0.5 rounded-md ${
                          isHigh ? 'bg-rose-600 text-white' : isMod ? 'bg-amber-500 text-white' : 'bg-emerald-600 text-white'
                        }`}>
                          {w.risk_level} ({w.risk_score_pct}%)
                        </span>
                      </div>

                      <p className="text-xs text-slate-700">
                        <strong>Top Threat:</strong> {w.primary_threat} ({w.reported_cases} active cases)
                      </p>

                      <p className="text-[11px] text-slate-600 bg-white/80 p-2 rounded-md border border-slate-200/60 leading-snug">
                        <strong>Action Protocol:</strong> {w.recommended_action}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Tomorrow's Queue Rush & Crowding Predictor */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div>
                  <h3 className="text-base font-black text-slate-900 flex items-center gap-2">
                    <Clock className="w-5 h-5 text-indigo-600" />
                    Tomorrow's Patient Surge & Waiting Hall Load Forecast
                  </h3>
                  <p className="text-xs text-slate-500">Predictive timeline of peak arrival windows and staffing requirements</p>
                </div>
                <span className="text-xs font-bold text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded-lg border border-indigo-200">
                  {surgeForecast.forecast_period || "Tomorrow Clinic"}
                </span>
              </div>

              {/* Peak Window Timeline Cards */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-4 bg-amber-50/80 rounded-xl border border-amber-200 space-y-1">
                  <span className="text-[10px] font-black text-amber-800 uppercase tracking-wider block">Peak Morning Rush</span>
                  <span className="text-sm font-black text-slate-900 block">{surgeForecast.morning_surge_window || "09:30 AM - 11:30 AM"}</span>
                  <p className="text-xs text-amber-900 font-bold mt-1">Expected: {surgeForecast.morning_expected_patients || 32} Patients</p>
                  <p className="text-[10px] text-slate-600">Peak triage vitals & token intake</p>
                </div>
                <div className="p-4 bg-blue-50/80 rounded-xl border border-blue-200 space-y-1">
                  <span className="text-[10px] font-black text-blue-800 uppercase tracking-wider block">Evening Clinic Rush</span>
                  <span className="text-sm font-black text-slate-900 block">{surgeForecast.evening_surge_window || "04:30 PM - 06:00 PM"}</span>
                  <p className="text-xs text-blue-900 font-bold mt-1">Expected: {surgeForecast.evening_expected_patients || 20} Patients</p>
                  <p className="text-[10px] text-slate-600">Working population NCD pickups</p>
                </div>
              </div>

              {/* Recommended Staffing */}
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                <span className="text-xs font-extrabold text-slate-900 block">Recommended Clinical Duty Roster:</span>
                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="p-2 bg-white rounded-lg border border-slate-200 font-bold text-slate-800">
                    2 Medical Officers
                  </div>
                  <div className="p-2 bg-white rounded-lg border border-slate-200 font-bold text-slate-800">
                    2 Triage Nurses
                  </div>
                  <div className="p-2 bg-white rounded-lg border border-slate-200 font-bold text-slate-800">
                    1 Pharmacist
                  </div>
                </div>
                <p className="text-[11px] text-slate-600 pt-1 leading-snug">
                  <strong>Prescriptive Strategy:</strong> {surgeForecast.queue_strategy_story || "Deploy Nurse Triage fast-track lane at 09:30 AM for routine NCD refill pickups to cap doctor consult wait times under 15 minutes."}
                </p>
              </div>

              {/* Expected Total & Avg Wait */}
              <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200 flex items-center justify-between text-xs font-bold text-emerald-900">
                <span>Predicted Total Footfall: ~{surgeForecast.predicted_total_footfall || 52} Patients</span>
                <span>Forecasted Wait Time: ~{surgeForecast.estimated_avg_wait_mins || 14} Mins</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PublicHealthIntelligencePage;
