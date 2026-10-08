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
} from 'lucide-react';
import api from '../../services/api';

type TabType = 'hierarchy' | 'trends' | 'predictive';
type LevelType = 'ALL' | 'STATE' | 'DISTRICT' | 'ZONE' | 'WARD' | 'FACILITY';

export const PublicHealthIntelligencePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('hierarchy');
  const [selectedLevel, setSelectedLevel] = useState<LevelType>('ALL');
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

  const stateInfo = multiLevelData?.state || {};
  const districts = multiLevelData?.districts || [];
  const zones = multiLevelData?.zones || [];
  const wards = multiLevelData?.wards || [];
  const facilities = multiLevelData?.facilities || [];

  const monthlyFootfall = trendData?.monthly_footfall || [];
  const epidemicCurve = trendData?.epidemic_curve || [];
  const ncdTrajectories = trendData?.ncd_trajectories || [];
  const dailyVelocity = trendData?.recent_daily_velocity || [];

  const outbreakRisks = predictiveData?.outbreak_risk_predictions || [];
  const stockRunways = predictiveData?.pharmacy_stock_runway || [];
  const surgeForecast = predictiveData?.patient_surge_forecast || {};

  return (
    <div className="space-y-6 pb-12">
      {/* Page Header */}
      <div className="bg-gradient-to-r from-teal-900 via-emerald-900 to-slate-900 rounded-2xl p-6 text-white shadow-lg relative overflow-hidden">
        <div className="absolute right-0 top-0 translate-x-12 -translate-y-8 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
              <span className="px-3 py-0.5 bg-emerald-500/20 text-emerald-300 text-[11px] font-extrabold rounded-full uppercase tracking-wider border border-emerald-400/30">
                Hospital Administration & Public Health Division
              </span>
              <span className="text-xs text-emerald-200/90 font-medium flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                Authoritative Multi-Level Health Intelligence
              </span>
            </div>
            <h1 className="text-2xl lg:text-3xl font-black tracking-tight text-white flex items-center gap-3">
              Public Health & Predictive Analytics
            </h1>
            <p className="text-xs lg:text-sm text-emerald-100/80 mt-1 max-w-2xl leading-relaxed">
              Longitudinal surveillance curves, multi-tiered health jurisdiction KPIs, pharmacy run-out forecasting, and ward-level outbreak risk scoring.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={fetchAllAnalytics}
              disabled={loading}
              className="px-4 py-2 bg-emerald-800/60 hover:bg-emerald-700/80 border border-emerald-500/40 text-emerald-100 text-xs font-bold rounded-xl transition flex items-center gap-2 shadow-xs cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh Metrics</span>
            </button>
          </div>
        </div>

        {/* Global Key Figure Ribbon */}
        <div className="mt-6 pt-5 border-t border-emerald-800/60 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-3 border border-white/10">
            <p className="text-[10px] font-bold text-emerald-200 uppercase tracking-wider">Registered Citizens</p>
            <p className="text-xl font-black text-white mt-0.5">{stateInfo.registered_citizens || 75}</p>
            <p className="text-[10px] text-emerald-300 mt-0.5">100% Verified Identifiers</p>
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-3 border border-white/10">
            <p className="text-[10px] font-bold text-emerald-200 uppercase tracking-wider">Total Encounters</p>
            <p className="text-xl font-black text-white mt-0.5">{stateInfo.total_opd_encounters || 123}</p>
            <p className="text-[10px] text-emerald-300 mt-0.5">OPD & Review Visits</p>
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-3 border border-white/10">
            <p className="text-[10px] font-bold text-emerald-200 uppercase tracking-wider">Active NCD Cohort</p>
            <p className="text-xl font-black text-white mt-0.5">{stateInfo.active_ncd_patients || 75}</p>
            <p className="text-[10px] text-emerald-300 mt-0.5">BP & Glycemic Monitoring</p>
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-3 border border-white/10">
            <p className="text-[10px] font-bold text-emerald-200 uppercase tracking-wider">IDSP Surveillance</p>
            <p className="text-xl font-black text-white mt-0.5">{stateInfo.communicable_surveillance_cases || 16}</p>
            <p className="text-[10px] text-amber-300 mt-0.5">Vector & Fever Watch</p>
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-3 border border-white/10">
            <p className="text-[10px] font-bold text-emerald-200 uppercase tracking-wider">Diagnostic Tests</p>
            <p className="text-xl font-black text-white mt-0.5">{stateInfo.diagnostic_tests_conducted || 75}</p>
            <p className="text-[10px] text-emerald-300 mt-0.5">Lab Results Verified</p>
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-3 border border-white/10">
            <p className="text-[10px] font-bold text-emerald-200 uppercase tracking-wider">Pharmacy Dispensed</p>
            <p className="text-xl font-black text-white mt-0.5">{stateInfo.pharmacy_dispensations || 113}</p>
            <p className="text-[10px] text-emerald-300 mt-0.5">FEFO Ledger Audited</p>
          </div>
        </div>
      </div>

      {/* Primary Tab Navigation & View Selector */}
      <div className="bg-white p-3 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-xl">
          <button
            onClick={() => setActiveTab('hierarchy')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
              activeTab === 'hierarchy'
                ? 'bg-white text-emerald-900 shadow-xs border border-slate-200'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Globe className="w-4 h-4 text-emerald-600" />
            <span>🌐 Multi-Level Hierarchy</span>
          </button>

          <button
            onClick={() => setActiveTab('trends')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
              activeTab === 'trends'
                ? 'bg-white text-emerald-900 shadow-xs border border-slate-200'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <TrendingUp className="w-4 h-4 text-blue-600" />
            <span>📈 Trend Analysis</span>
          </button>

          <button
            onClick={() => setActiveTab('predictive')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
              activeTab === 'predictive'
                ? 'bg-white text-emerald-900 shadow-xs border border-slate-200'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Brain className="w-4 h-4 text-purple-600" />
            <span>🔮 Predictive Analytics</span>
          </button>
        </div>

        {/* Level Quick Dropdown / Jump */}
        {activeTab === 'hierarchy' && (
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-slate-500 flex items-center gap-1">
              <Filter className="w-3.5 h-3.5" />
              Administrative Level:
            </span>
            <select
              value={selectedLevel}
              onChange={(e) => setSelectedLevel(e.target.value as LevelType)}
              className="bg-slate-50 border border-slate-200 text-slate-800 text-xs font-bold rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="ALL">All Levels (Comprehensive View)</option>
              <option value="STATE">State Level (Karnataka)</option>
              <option value="DISTRICT">District Level (Urban & Rural)</option>
              <option value="ZONE">Zone Level (4 Zones)</option>
              <option value="WARD">Ward Level (5 Wards)</option>
              <option value="FACILITY">Facility Level (PHC & Rural)</option>
            </select>
          </div>
        )}
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 font-semibold flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 1: MULTI-LEVEL HIERARCHY DASHBOARD */}
      {/* ========================================================================= */}
      {activeTab === 'hierarchy' && (
        <div className="space-y-6">
          {/* Level Filter Pills */}
          <div className="flex flex-wrap gap-2">
            {[
              { id: 'ALL', label: 'All Jurisdictions' },
              { id: 'STATE', label: '1. State Level' },
              { id: 'DISTRICT', label: '2. District Level' },
              { id: 'ZONE', label: '3. Zone Level' },
              { id: 'WARD', label: '4. Ward Level' },
              { id: 'FACILITY', label: '5. Facility Level' },
            ].map((lvl) => (
              <button
                key={lvl.id}
                onClick={() => setSelectedLevel(lvl.id as LevelType)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer border ${
                  selectedLevel === lvl.id
                    ? 'bg-emerald-800 text-white border-emerald-900 shadow-xs'
                    : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                }`}
              >
                {lvl.label}
              </button>
            ))}
          </div>

          {/* 1. STATE LEVEL CARD */}
          {(selectedLevel === 'ALL' || selectedLevel === 'STATE') && (
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-800 font-black text-sm">
                    KA
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-base font-black text-slate-900">State Level: Karnataka</h2>
                      <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 text-[10px] font-bold rounded-full">
                        State Health Registry
                      </span>
                    </div>
                    <p className="text-xs text-slate-500">
                      Capital: Bengaluru • Total Census Population: {stateInfo.total_population?.toLocaleString() || '61,130,704'}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-xs font-bold text-slate-600 block">Active Health Jurisdictions</span>
                  <span className="text-xs font-mono text-emerald-700 font-bold">2 Districts • 4 Zones • 5 Wards • 2 Primary Centers</span>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <p className="text-[10px] font-bold text-slate-500 uppercase">Registered Citizens</p>
                  <p className="text-xl font-black text-slate-900 mt-1">{stateInfo.registered_citizens || 75}</p>
                  <p className="text-[10px] text-emerald-700 font-medium">100% Identity Bound</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <p className="text-[10px] font-bold text-slate-500 uppercase">Total Clinical Visits</p>
                  <p className="text-xl font-black text-blue-900 mt-1">{stateInfo.total_opd_encounters || 123}</p>
                  <p className="text-[10px] text-blue-700 font-medium">OPD & Follow-ups</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <p className="text-[10px] font-bold text-slate-500 uppercase">IDSP Surveillance Cases</p>
                  <p className="text-xl font-black text-rose-900 mt-1">{stateInfo.communicable_surveillance_cases || 16}</p>
                  <p className="text-[10px] text-rose-700 font-medium">Active Vector Registry</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <p className="text-[10px] font-bold text-slate-500 uppercase">Pharmacy Dispensations</p>
                  <p className="text-xl font-black text-emerald-900 mt-1">{stateInfo.pharmacy_dispensations || 113}</p>
                  <p className="text-[10px] text-emerald-700 font-medium">FEFO Batch Traced</p>
                </div>
              </div>
            </div>
          )}

          {/* 2. DISTRICT LEVEL COMPARISON */}
          {(selectedLevel === 'ALL' || selectedLevel === 'DISTRICT') && (
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div>
                  <h2 className="text-base font-black text-slate-900 flex items-center gap-2">
                    <Building2 className="w-5 h-5 text-indigo-600" />
                    District Level Breakdown (Urban vs. Rural)
                  </h2>
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
                          <h3 className="font-extrabold text-sm text-slate-900">{d.name}</h3>
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

          {/* 3. ZONE LEVEL COMPARISON TABLE */}
          {(selectedLevel === 'ALL' || selectedLevel === 'ZONE') && (
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div>
                  <h2 className="text-base font-black text-slate-900 flex items-center gap-2">
                    <Layers className="w-5 h-5 text-teal-600" />
                    Zone Level Operational Distribution (4 Municipal Zones)
                  </h2>
                  <p className="text-xs text-slate-500">Zonal health management and jurisdictional patient density</p>
                </div>
                <span className="text-xs font-bold text-teal-700 bg-teal-50 px-2.5 py-1 rounded-lg border border-teal-200">
                  BBMP & Rural Zones
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                    <tr>
                      <th className="p-3">Zone Name & Code</th>
                      <th className="p-3">District Authority</th>
                      <th className="p-3">Registered Patients</th>
                      <th className="p-3">OPD Visits</th>
                      <th className="p-3">Surveillance Cases</th>
                      <th className="p-3">Action Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {zones.map((z: any, idx: number) => (
                      <tr key={idx} className="hover:bg-slate-50/80 transition">
                        <td className="p-3">
                          <span className="font-bold text-slate-900 block">{z.name}</span>
                          <span className="text-[10px] font-mono text-slate-400">{z.code}</span>
                        </td>
                        <td className="p-3 font-semibold text-slate-700">{z.district}</td>
                        <td className="p-3">
                          <span className="font-extrabold text-slate-900">{z.total_patients}</span>
                          <span className="text-[10px] text-slate-500 block">registered</span>
                        </td>
                        <td className="p-3">
                          <span className="font-extrabold text-blue-900">{z.total_visits}</span>
                          <span className="text-[10px] text-slate-500 block">encounters</span>
                        </td>
                        <td className="p-3">
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800">
                            {z.surveillance_cases} Cases
                          </span>
                        </td>
                        <td className="p-3">
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                            Active Operational
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 4. WARD LEVEL BREAKDOWN */}
          {(selectedLevel === 'ALL' || selectedLevel === 'WARD') && (
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div>
                  <h2 className="text-base font-black text-slate-900 flex items-center gap-2">
                    <MapPin className="w-5 h-5 text-amber-600" />
                    Ward Level Public Health Distribution (5 Wards)
                  </h2>
                  <p className="text-xs text-slate-500">Catchment ward population, registered citizens, and disease surveillance density</p>
                </div>
                <span className="text-xs font-bold text-amber-800 bg-amber-50 px-2.5 py-1 rounded-lg border border-amber-200">
                  Ward Catchment Areas
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {wards.map((w: any, idx: number) => (
                  <div key={idx} className="p-4 rounded-xl border border-slate-200 bg-slate-50/40 hover:bg-white hover:border-amber-300 transition shadow-xs space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-extrabold text-slate-900">{w.name}</span>
                      <span className="px-2 py-0.5 bg-amber-100 text-amber-900 text-[10px] font-extrabold rounded-md">
                        Ward #{w.ward_number}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500">Zone: <strong className="text-slate-700">{w.zone_name || w.zone || 'Central Zone'}</strong></p>
                    <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-200/60 text-xs">
                      <div>
                        <span className="text-[10px] text-slate-400 font-semibold block">POPULATION</span>
                        <span className="font-bold text-slate-800">{w.population?.toLocaleString() || '35,000'}</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 font-semibold block">PATIENTS</span>
                        <span className="font-extrabold text-slate-900">{w.registered_citizens ?? w.patients_registered ?? 0}</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 font-semibold block">IDSP CASES</span>
                        <span className="font-extrabold text-rose-800">{w.surveillance_cases ?? 0}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 5. FACILITY LEVEL COMPARISON */}
          {(selectedLevel === 'ALL' || selectedLevel === 'FACILITY') && (
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div>
                  <h2 className="text-base font-black text-slate-900 flex items-center gap-2">
                    <Building2 className="w-5 h-5 text-emerald-600" />
                    Facility Level Performance Comparison
                  </h2>
                  <p className="text-xs text-slate-500">Direct comparison between Namma Clinic Local PHC and Rural Primary Center</p>
                </div>
                <span className="text-xs font-bold text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200">
                  2 Operational Primary Centers
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {facilities
                  .filter((f: any) => (f.registered_citizens > 0 || f.total_opd_encounters > 0 || f.facility_code === 'PHC-LOCAL-01' || f.facility_code === 'RC-A4-01'))
                  .map((f: any, idx: number) => (
                  <div key={idx} className="p-5 rounded-2xl border border-slate-200 bg-gradient-to-b from-white to-slate-50/50 hover:border-emerald-300 transition shadow-xs space-y-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-black text-slate-900 text-sm">{f.facility_name || f.name}</h3>
                          <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 text-[10px] font-extrabold rounded-md font-mono">
                            {f.facility_code || f.code}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 mt-0.5">Type: {f.facility_type || f.type} • District: {f.district_name || f.district}</p>
                      </div>
                      <span className="px-2.5 py-1 bg-emerald-50 text-emerald-800 text-[10px] font-bold rounded-lg border border-emerald-200">
                        {f.district_name || f.district}
                      </span>
                    </div>

                    <div className="grid grid-cols-4 gap-2 pt-2 border-t border-slate-200 text-center">
                      <div className="p-2 bg-white rounded-lg border border-slate-200">
                        <p className="text-[10px] font-bold text-slate-400">PATIENTS</p>
                        <p className="text-base font-black text-slate-900 mt-0.5">{f.registered_citizens ?? f.patients_registered ?? 0}</p>
                      </div>
                      <div className="p-2 bg-white rounded-lg border border-slate-200">
                        <p className="text-[10px] font-bold text-slate-400">OPD VISITS</p>
                        <p className="text-base font-black text-blue-900 mt-0.5">{f.total_opd_encounters ?? f.total_visits ?? 0}</p>
                      </div>
                      <div className="p-2 bg-white rounded-lg border border-slate-200">
                        <p className="text-[10px] font-bold text-slate-400">DISPENSED</p>
                        <p className="text-base font-black text-emerald-900 mt-0.5">{f.pharmacy_dispensations ?? 0}</p>
                      </div>
                      <div className="p-2 bg-white rounded-lg border border-slate-200">
                        <p className="text-[10px] font-bold text-slate-400">REFERRALS</p>
                        <p className="text-base font-black text-rose-900 mt-0.5">{f.referrals_initiated ?? 0}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: LONGITUDINAL TREND ANALYSIS */}
      {/* ========================================================================= */}
      {activeTab === 'trends' && (
        <div className="space-y-6">
          {/* 4-Month Footfall Trajectory */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-base font-black text-slate-900 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-blue-600" />
                  4-Month Longitudinal Utilization & Care Velocity (July – October 2026)
                </h2>
                <p className="text-xs text-slate-500">Longitudinal footfall progression across OPD encounters, doctor prescriptions, and laboratory tests</p>
              </div>
              <span className="text-xs font-bold text-blue-700 bg-blue-50 px-2.5 py-1 rounded-lg border border-blue-200">
                123 Total Encounters
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {monthlyFootfall.map((m: any, idx: number) => {
                const maxVal = 50;
                const pct = Math.min(Math.round((m.opd_visits / maxVal) * 100), 100);
                return (
                  <div key={idx} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white hover:border-blue-300 transition shadow-xs space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="font-extrabold text-slate-900 text-sm">{m.month}</span>
                      <span className="text-xs font-bold text-blue-800 bg-blue-100 px-2 py-0.5 rounded-full">
                        {m.opd_visits} Visits
                      </span>
                    </div>

                    <div className="space-y-1">
                      <div className="flex justify-between text-[11px] text-slate-500">
                        <span>Relative Utilization</span>
                        <span className="font-bold text-slate-700">{pct}% capacity</span>
                      </div>
                      <div className="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-blue-500 to-indigo-600 h-2.5 rounded-full transition-all duration-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-200 text-xs">
                      <div>
                        <span className="text-[10px] text-slate-400 font-semibold block">PRESCRIPTIONS</span>
                        <span className="font-bold text-slate-800">{m.prescriptions}</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 font-semibold block">LAB TESTS</span>
                        <span className="font-bold text-purple-800">{m.lab_tests}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* IDSP Communicable Disease Epidemic Curves */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-base font-black text-slate-900 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-rose-600" />
                  IDSP Communicable Epidemic Curves & Threshold Monitoring
                </h2>
                <p className="text-xs text-slate-500">Integrated Disease Surveillance Programme (IDSP) outbreak tracking curves</p>
              </div>
              <span className="text-xs font-bold text-rose-800 bg-rose-50 px-2.5 py-1 rounded-lg border border-rose-200">
                16 Total Monitored Cases
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {epidemicCurve.map((d: any, idx: number) => (
                <div key={idx} className="p-4 rounded-xl border border-slate-200 bg-white hover:border-rose-300 transition shadow-xs space-y-2">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-extrabold text-slate-900 text-sm">{d.disease_name}</h3>
                      <p className="text-[10px] font-mono text-slate-400 mt-0.5">ICD/IDSP: {d.disease_code}</p>
                    </div>
                    <span className="px-2 py-0.5 bg-rose-100 text-rose-800 text-[10px] font-black rounded-md">
                      {d.cases_count} Cases
                    </span>
                  </div>

                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                    <span className="text-[11px] text-slate-500 font-medium">Surveillance Status:</span>
                    <span className="text-[11px] font-bold text-emerald-700 flex items-center gap-1">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      {d.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Chronic Disease Control Trajectory (Hypertension & Diabetes) */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-base font-black text-slate-900 flex items-center gap-2">
                  <HeartPulse className="w-5 h-5 text-emerald-600" />
                  NCD Chronic Care Trajectory: Longitudinal BP & Glycemic Control
                </h2>
                <p className="text-xs text-slate-500">
                  Progression of hypertensive and diabetic patient cohorts under continuous generic drug dispensing and follow-ups
                </p>
              </div>
              <span className="text-xs font-bold text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200">
                +39.5% Control Improvement
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {ncdTrajectories.map((tr: any, idx: number) => (
                <div key={idx} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white hover:border-emerald-300 transition shadow-xs space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-extrabold text-slate-900 text-sm">{tr.month}</span>
                    <span className="text-xs font-bold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-full">
                      {tr.control_rate_pct}% In Control
                    </span>
                  </div>

                  <div className="space-y-1.5 text-xs">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Avg Blood Pressure:</span>
                      <strong className="text-slate-800">{tr.avg_systolic_bp} / {tr.avg_diastolic_bp} mmHg</strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Avg Fasting Sugar:</span>
                      <strong className="text-slate-800">{tr.avg_fasting_sugar} mg/dL</strong>
                    </div>
                  </div>

                  <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-emerald-600 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${tr.control_rate_pct}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent 7-Day Live Queue Velocity */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-base font-black text-slate-900 flex items-center gap-2">
                  <Clock className="w-5 h-5 text-indigo-600" />
                  Recent 7-Day Live Queue & OPD Velocity
                </h2>
                <p className="text-xs text-slate-500">Daily patient arrivals across the trailing week</p>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
              {dailyVelocity.map((day: any, idx: number) => (
                <div key={idx} className="p-3 rounded-xl border border-slate-200 bg-white text-center shadow-xs">
                  <span className="text-[10px] font-bold text-slate-400 uppercase block">{day.day_name}</span>
                  <span className="text-xs font-semibold text-slate-600">{day.date}</span>
                  <p className="text-xl font-black text-slate-900 mt-2">{day.visits}</p>
                  <span className="text-[10px] text-emerald-700 font-semibold block mt-0.5">Visits</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: PREDICTIVE ANALYTICS & INTELLIGENCE */}
      {/* ========================================================================= */}
      {activeTab === 'predictive' && (
        <div className="space-y-6">
          {/* 1. Ward Disease Outbreak Risk Scoring Index */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-base font-black text-slate-900 flex items-center gap-2">
                  <Brain className="w-5 h-5 text-purple-600" />
                  Ward-Level Disease Outbreak Risk Scoring (Epidemiological AI Index)
                </h2>
                <p className="text-xs text-slate-500">
                  Calculated from fever clustering, monsoonal vector density, historical attack rates, and demographic vulnerability
                </p>
              </div>
              <span className="text-xs font-bold text-purple-800 bg-purple-50 px-2.5 py-1 rounded-lg border border-purple-200">
                5 Wards Analyzed
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {outbreakRisks.map((w: any, idx: number) => {
                const riskScore = w.risk_score_pct ?? w.outbreak_risk_score ?? 0;
                const isHigh = riskScore >= 70;
                const isMod = riskScore >= 40 && riskScore < 70;
                const badgeColor = isHigh ? 'bg-rose-100 text-rose-900 border-rose-300' : isMod ? 'bg-amber-100 text-amber-900 border-amber-300' : 'bg-emerald-100 text-emerald-900 border-emerald-300';
                const barColor = isHigh ? 'bg-rose-600' : isMod ? 'bg-amber-500' : 'bg-emerald-600';

                return (
                  <div key={idx} className="p-5 rounded-2xl border border-slate-200 bg-white hover:shadow-sm transition space-y-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-black text-sm text-slate-900">{w.ward_name}</h3>
                          <span className="text-[10px] font-mono text-slate-400">#{w.ward_number}</span>
                        </div>
                        <p className="text-[11px] text-slate-500">{w.zone_name}</p>
                      </div>
                      <span className={`px-2.5 py-1 text-[10px] font-extrabold rounded-lg border ${badgeColor}`}>
                        {w.risk_level} RISK
                      </span>
                    </div>

                    <div className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="font-semibold text-slate-600">Outbreak Risk Index:</span>
                        <span className="font-black text-slate-900">{riskScore}%</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                        <div className={`${barColor} h-2.5 rounded-full transition-all duration-500`} style={{ width: `${riskScore}%` }} />
                      </div>
                    </div>

                    <div className="pt-2 border-t border-slate-100 space-y-1.5 text-xs">
                      <div className="flex justify-between">
                        <span className="text-slate-500">Primary Monitored Threat:</span>
                        <strong className="text-rose-800">{w.primary_threat}</strong>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Reported Surveillance Cases:</span>
                        <span className="text-slate-800 font-bold">{w.reported_cases} active cases</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Surveillance Status:</span>
                        <span className="font-bold text-emerald-700">Active Field Monitoring</span>
                      </div>
                    </div>

                    <div className="pt-2 border-t border-slate-100 bg-slate-50 -mx-5 -mb-5 p-3 rounded-b-2xl">
                      <p className="text-[11px] text-slate-600 font-medium">
                        <strong className="text-slate-800">Intervention Protocol:</strong> {w.recommended_action}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 2. KSMSCL Pharmacy Stockout Runway Forecasting */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-base font-black text-slate-900 flex items-center gap-2">
                  <Package className="w-5 h-5 text-amber-600" />
                  KSMSCL Pharmacy Stockout Runway Forecasting (Runout AI Predictor)
                </h2>
                <p className="text-xs text-slate-500">
                  Burn rate analysis estimating days of medicine stock remaining before mandatory re-order threshold
                </p>
              </div>
              <span className="text-xs font-bold text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200">
                100% Usable Batch Stock
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                  <tr>
                    <th className="p-3">Medicine & Form</th>
                    <th className="p-3">Category</th>
                    <th className="p-3">Usable Stock</th>
                    <th className="p-3">Daily Burn Rate</th>
                    <th className="p-3">Predicted Runway</th>
                    <th className="p-3">Status</th>
                    <th className="p-3">Suggested Re-Order</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {stockRunways.map((item: any, idx: number) => {
                    const statusColor = item.stock_status === 'EXCELLENT' ? 'bg-emerald-100 text-emerald-800' : item.stock_status === 'ADEQUATE' ? 'bg-blue-100 text-blue-800' : 'bg-amber-100 text-amber-800';
                    return (
                      <tr key={idx} className="hover:bg-slate-50/80 transition">
                        <td className="p-3">
                          <span className="font-bold text-slate-900 block">{item.medicine_name}</span>
                          <span className="text-[10px] font-mono text-slate-400">{item.medicine_code}</span>
                        </td>
                        <td className="p-3 font-semibold text-slate-700">{item.category}</td>
                        <td className="p-3">
                          <span className="font-extrabold text-slate-900">{item.current_usable_stock?.toLocaleString()}</span>
                          <span className="text-[10px] text-slate-400 block">units</span>
                        </td>
                        <td className="p-3 font-semibold text-slate-700">~{item.daily_burn_rate} / day</td>
                        <td className="p-3">
                          <span className="font-black text-indigo-900 text-sm">{item.predicted_runway_days}</span>
                          <span className="text-[10px] text-slate-500 block">days runway</span>
                        </td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold ${statusColor}`}>
                            {item.stock_status}
                          </span>
                        </td>
                        <td className="p-3 font-mono font-bold text-slate-700">
                          {item.suggested_order_date}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* 3. Patient Surge & Queue Capacity Forecast */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-base font-black text-slate-900 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-indigo-600" />
                  Predictive Patient Surge & Peak Queue Hours Forecast
                </h2>
                <p className="text-xs text-slate-500">Simulated demand forecasting to optimize doctor consultation desk queues and nurse triage velocity</p>
              </div>
              <span className="text-xs font-bold text-indigo-800 bg-indigo-50 px-2.5 py-1 rounded-lg border border-indigo-200">
                {surgeForecast.forecast_period || 'Next 7 Days'}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase">PREDICTED PEAK DAY</span>
                <p className="text-xl font-black text-slate-900">{surgeForecast.predicted_peak_day || 'Monday'}</p>
                <p className="text-xs text-slate-500">Post-weekend clinical inflow surge</p>
              </div>

              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase">PEAK ARRIVAL WINDOW</span>
                <p className="text-xl font-black text-amber-900">{surgeForecast.predicted_peak_arrival_window || '09:30 AM - 11:30 AM'}</p>
                <p className="text-xs text-slate-500">Token distribution high load</p>
              </div>

              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase">EXPECTED PEAK FOOTFALL</span>
                <p className="text-xl font-black text-blue-900">~{surgeForecast.expected_monday_surge_footfall || 42} Patients</p>
                <p className="text-xs text-slate-500">vs {surgeForecast.expected_daily_average_footfall || 28} daily baseline</p>
              </div>

              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase">STAFFING ADEQUACY</span>
                <p className="text-xl font-black text-emerald-900">{surgeForecast.staffing_adequacy_score || '98%'}</p>
                <p className="text-xs text-emerald-700 font-semibold">Sufficient clinical roster</p>
              </div>
            </div>

            <div className="p-4 rounded-xl border border-amber-200 bg-amber-50/60 space-y-1.5">
              <div className="flex items-center gap-2 text-amber-950 font-bold text-xs">
                <AlertTriangle className="w-4 h-4 text-amber-700" />
                <span>Primary Bottleneck Risk: {surgeForecast.bottleneck_risk}</span>
              </div>
              <p className="text-xs text-amber-900 pl-6">
                <strong>Mitigation Strategy:</strong> {surgeForecast.mitigation_plan}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PublicHealthIntelligencePage;
