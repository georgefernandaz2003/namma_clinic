import React, { useState, useEffect, useMemo } from 'react';
import {
  FileSpreadsheet, Download, RefreshCw, Calendar, Building2,
  Users, Clock, Stethoscope, TestTube, Pill, Share2, Activity,
  Baby, AlertTriangle, ChevronRight, Search, Filter, ArrowUpRight,
  ArrowDownRight, CheckCircle2, XCircle, AlertCircle, ShoppingCart,
  Package, TrendingUp, BarChart3, HelpCircle
} from 'lucide-react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useConfirm } from '../context/ConfirmContext';

type PeriodType = 'day' | 'week' | 'month' | 'year';

interface ReportData {
  facility: {
    id: number | null;
    name: string;
    type: string;
    district: string | null;
  };
  period: {
    type: PeriodType;
    start_date: string;
    end_date: string;
    target_date: string;
  };
  summary_cards: {
    patients: { total_visits: number; new_patients: number; completed: number; emergency: number };
    services: { triage_waiting: number; doctor_waiting: number; lab_pending: number; pharmacy_waiting: number };
    pharmacy: { dispensed_units: number; low_stock_medicines: number; out_of_stock_medicines: number; expiring_soon_batches: number };
    procurement: { pending_po: number; received_po: number; procurement_amount: number };
    referrals: { created: number; in_transit: number; completed: number };
  };
  comparison: {
    period_label: string;
    current_range: string;
    previous_range: string;
    metrics: {
      opd_visits: { current: number; previous: number; difference: number; percent: number | null; display: string };
      new_patients: { current: number; previous: number; difference: number; percent: number | null; display: string };
      prescriptions_dispensed: { current: number; previous: number; difference: number; percent: number | null; display: string };
      lab_verified: { current: number; previous: number; difference: number; percent: number | null; display: string };
      referrals_created: { current: number; previous: number; difference: number; percent: number | null; display: string };
    };
  };
  opd_patient: {
    total_registered_patients: number;
    new_patients: number;
    returning_patients: number;
    total_opd_visits: number;
    completed_visits: number;
    cancelled_visits: number;
    emergency_visits: number;
    demographics: { male: number; female: number; other: number };
    age_groups: { '0_5': number; '6_18': number; '19_30': number; '31_45': number; '46_60': number; '60_plus': number };
    trend: Array<{ label: string; date?: string; visits: number }>;
  };
  queue_service: {
    stages: Record<string, { waiting: number; in_progress: number; completed: number }>;
    avg_triage_wait_minutes: number | null;
    avg_doctor_wait_minutes: number | null;
    avg_total_duration_minutes: number | null;
    peak_queue_period: string;
  };
  doctor_staff: {
    total_staff: number;
    active_staff: number;
    inactive_staff: number;
    roles: Record<string, { active: number; inactive: number; total: number }>;
    doctor_activity: Array<{
      doctor_id: number;
      name: string;
      username: string;
      is_active: boolean;
      patients_consulted: number;
      consultations_completed: number;
      lab_orders: number;
      prescriptions: number;
      referrals: number;
    }>;
  };
  laboratory: {
    total_orders: number;
    samples_collected: number;
    in_progress: number;
    results_pending: number;
    results_completed: number;
    verified_results: number;
    cancelled_tests: number;
    test_breakdown: Array<{
      code: string;
      name: string;
      category: string;
      unit: string;
      reference_range: string;
      total_orders: number;
      verified: number;
      pending: number;
    }>;
  };
  pharmacy: {
    prescriptions: { total_prescriptions: number; pending: number; partially_dispensed: number; dispensed: number; cancelled: number };
    dispensing: {
      total_medicines_dispensed: number;
      total_dispensing_transactions: number;
      patients_served: number;
      top_dispensed_medicines: Array<{
        medicine_id: number;
        generic_name: string;
        brand_name: string;
        unit: string;
        quantity_dispensed: number;
        prescriptions_count: number;
      }>;
    };
    inventory: {
      total_medicines_master: number;
      medicines_currently_stocked: number;
      total_available_units: number;
      low_stock_medicines: number;
      out_of_stock_medicines: number;
      expiring_soon_batches: number;
      expired_batches: number;
    };
    purchases: {
      total_purchase_orders: number;
      draft: number;
      pending_approval: number;
      approved: number;
      ordered: number;
      partially_received: number;
      received: number;
      cancelled: number;
      procurement_amount: number;
      purchase_orders_list: Array<{
        id: number;
        po_number: string;
        vendor_name: string;
        order_date: string;
        status: string;
        total_amount: number;
      }>;
    };
    vendors: { active_vendors: number; inactive_vendors: number };
    stock_movement: {
      summary: {
        opening_stock: number;
        stock_received: number;
        stock_dispensed: number;
        stock_adjusted: number;
        closing_stock: number;
      };
      items: Array<{
        medicine_id: number;
        medicine: string;
        brand_name: string;
        dosage_form: string;
        unit: string;
        opening_stock: number;
        received: number;
        dispensed: number;
        adjusted: number;
        closing_stock: number;
      }>;
    };
    expiry_monitoring: {
      categories: {
        expired: number;
        expires_within_7_days: number;
        expires_within_30_days: number;
        expires_within_60_days: number;
        expires_within_90_days: number;
      };
      batches: Array<{
        batch_id: number;
        medicine_name: string;
        brand_name: string;
        batch_number: string;
        quantity: number;
        expiry_date: string;
        days_remaining: number;
        status: string;
        category: string;
      }>;
    };
    low_stock_report: Array<{
      id: number;
      generic_name: string;
      brand_name: string;
      category: string;
      unit: string;
      current_stock: number;
      minimum_stock: number;
      reorder_level: number;
      status: 'NORMAL' | 'LOW_STOCK' | 'OUT_OF_STOCK';
    }>;
  };
  referrals: {
    total_referrals: number;
    created: number;
    accepted: number;
    rejected: number;
    in_transit: number;
    under_treatment: number;
    completed: number;
    outgoing_count: number;
    incoming_count: number;
    items: Array<{
      referral_id: string;
      patient_name: string;
      source_facility: string;
      destination_facility: string;
      urgency: string;
      status: string;
      required_service: string;
      date: string;
    }>;
  };
  follow_up: {
    total_due: number;
    completed: number;
    pending: number;
    overdue: number;
    items: Array<{
      id: number;
      patient_name: string;
      category: string;
      due_date: string;
      status: string;
      notes: string;
    }>;
  };
  ncd: {
    total_ncd_patients: number;
    new_screenings_in_period: number;
    hypertension: { screened: number; diagnosed: number };
    diabetes: { screened: number; diagnosed: number };
    risk_levels: { high: number; moderate: number; low: number };
    control_status: { controlled: number; uncontrolled: number };
  };
  maternal_child?: {
    available: boolean;
    maternal?: {
      anc_visits: number;
      total_registered_mothers: number;
      high_risk_cases: number;
      tt_vaccine_given: number;
      ifa_tablets_issued: number;
    };
    child?: {
      total_children: number;
      immunization_up_to_date: number;
      sam_mam_cases: number;
    };
  };
  alerts: {
    total_alerts: number;
    new: number;
    acknowledged: number;
    resolved: number;
    open_alerts: number;
    categories: Record<string, { total: number; new: number; resolved: number }>;
  };
}

export const Reports: React.FC = () => {
  const { user, activeFacility, allFacilities, setActiveFacility } = useAuth();
  const { confirm } = useConfirm();

  // Period state
  const [period, setPeriod] = useState<PeriodType>('day');
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().slice(0, 10));
  const [activeTab, setActiveTab] = useState<string>('opd');
  const [pharmacySubTab, setPharmacySubTab] = useState<string>('movement');

  // Loading & Data State
  const [data, setData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Table Filters & Pagination
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const pageSize = 10;

  // Reset pagination when tab or filters change
  useEffect(() => {
    setCurrentPage(1);
    setSearchTerm('');
    setStatusFilter('ALL');
  }, [activeTab, pharmacySubTab]);

  const fetchReportData = async () => {
    setLoading(true);
    setError(null);
    try {
      const facParam = activeFacility?.id ? `&facility=${activeFacility.id}` : '';
      const url = `reports/hospital/?period=${period}&date=${selectedDate}${facParam}`;
      const res = await api.get(url);
      setData(res.data);
    } catch (err: any) {
      console.error('Failed to load report data:', err);
      setError(err?.response?.data?.detail || 'Failed to load report data. Please retry.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReportData();
  }, [period, selectedDate, activeFacility?.id]);

  // Quick period presets
  const handleQuickPreset = (preset: 'TODAY' | 'THIS_WEEK' | 'THIS_MONTH' | 'THIS_YEAR') => {
    const today = new Date().toISOString().slice(0, 10);
    setSelectedDate(today);
    if (preset === 'TODAY') setPeriod('day');
    else if (preset === 'THIS_WEEK') setPeriod('week');
    else if (preset === 'THIS_MONTH') setPeriod('month');
    else if (preset === 'THIS_YEAR') setPeriod('year');
  };

  // CSV Export with confirmation modal
  const handleExportCSV = (reportType: string, customLabel?: string) => {
    const label = customLabel || reportType.toUpperCase().replace('_', ' ');
    const facName = data?.facility?.name || activeFacility?.facility_name || 'Assigned Facility';

    confirm({
      title: 'Confirm Report Export',
      message: `Generate and download authoritative CSV data for "${label}" scoped to ${facName}?`,
      confirmText: 'Export CSV',
      cancelText: 'Cancel',
      variant: 'primary',
      loadingText: 'Generating dataset...',
      details: [
        { label: 'Report Category', value: label },
        { label: 'Facility Scope', value: facName },
        { label: 'Reporting Period', value: `${period.toUpperCase()} (${data?.period?.start_date} to ${data?.period?.end_date})` },
        { label: 'Data Source', value: 'Live Authoritative Database' }
      ],
      onConfirm: async () => {
        const token = localStorage.getItem('access_token');
        const facParam = activeFacility?.id ? `&facility=${activeFacility.id}` : '';
        const exportUrl = `http://localhost:8000/api/reports/export/?type=${reportType}&period=${period}&date=${selectedDate}${facParam}`;

        const res = await fetch(exportUrl, {
          headers: { Authorization: `Bearer ${token}` }
        });

        if (!res.ok) {
          throw new Error(`Export failed with HTTP ${res.status}`);
        }

        const blob = await res.blob();
        const a = document.createElement('a');
        a.href = window.URL.createObjectURL(blob);
        a.download = `namma_clinic_${reportType}_${period}_${selectedDate}.csv`;
        a.click();
      }
    });
  };

  const isDistrictOfficer = user?.role === 'DISTRICT_OFFICER';

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Banner & Scope Header */}
      <div className="bg-gradient-to-r from-teal-900 via-teal-800 to-emerald-900 rounded-3xl p-6 sm:p-8 text-white shadow-xl relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 w-1/3 opacity-10 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-white via-transparent to-transparent pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-3 py-1 bg-teal-700/80 text-teal-100 text-xs font-black rounded-full uppercase tracking-wider border border-teal-500/40">
                Hospital Reports Executive
              </span>
              <span className="text-xs text-teal-200 font-bold flex items-center gap-1.5">
                <Building2 className="w-3.5 h-3.5 text-teal-300" />
                {data?.facility?.name || activeFacility?.facility_name || 'Assigned Hospital'}
              </span>
              {data?.facility?.district && (
                <span className="text-xs text-teal-300/80 font-medium">
                  • {data.facility.district} District
                </span>
              )}
            </div>

            <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white">
              {data?.facility?.name || activeFacility?.facility_name || 'Hospital Operational Reports'}
            </h1>
            <p className="text-xs sm:text-sm text-teal-100/90 max-w-2xl">
              Authoritative period-scoped operational intelligence, patient footfalls, clinical queues, FEFO pharmacy consumption, and diagnostic testing.
            </p>
          </div>

          {/* Period Selector Controls */}
          <div className="bg-white/10 backdrop-blur-md p-3.5 rounded-2xl border border-white/20 flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            {/* Day / Week / Month / Year Pills */}
            <div className="inline-flex bg-teal-950/60 p-1 rounded-xl border border-teal-700/50">
              {(['day', 'week', 'month', 'year'] as PeriodType[]).map((p) => (
                <button
                  key={p}
                  onClick={() => setPeriod(p)}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-black uppercase transition tracking-wider ${
                    period === p
                      ? 'bg-emerald-500 text-white shadow-md'
                      : 'text-teal-200 hover:text-white hover:bg-teal-800/40'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>

            {/* Custom Date Input */}
            <div className="flex items-center gap-2 bg-teal-950/60 px-3 py-1.5 rounded-xl border border-teal-700/50">
              <Calendar className="w-4 h-4 text-emerald-400 shrink-0" />
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="bg-transparent text-white text-xs font-bold focus:outline-none cursor-pointer"
              />
            </div>

            {/* Refresh Button */}
            <button
              onClick={fetchReportData}
              disabled={loading}
              title="Refresh Report Data"
              className="p-2 bg-teal-700/60 hover:bg-teal-700 text-teal-100 rounded-xl transition flex items-center justify-center border border-teal-500/30"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Quick Range Indicators & Presets */}
        <div className="mt-6 pt-4 border-t border-teal-700/50 flex flex-wrap items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-teal-300 font-bold uppercase text-[11px] tracking-wider">Active Period:</span>
            <span className="font-extrabold text-white bg-teal-800/80 px-2.5 py-0.5 rounded-md border border-teal-600/40">
              {data?.period?.start_date === data?.period?.end_date
                ? data?.period?.start_date
                : `${data?.period?.start_date} → ${data?.period?.end_date}`}
            </span>
          </div>

          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-teal-300 text-[11px] font-semibold mr-1">Quick Switch:</span>
            <button
              onClick={() => handleQuickPreset('TODAY')}
              className="px-2.5 py-1 bg-teal-800/50 hover:bg-teal-700/80 text-teal-100 font-bold rounded-lg transition border border-teal-600/30"
            >
              Today
            </button>
            <button
              onClick={() => handleQuickPreset('THIS_WEEK')}
              className="px-2.5 py-1 bg-teal-800/50 hover:bg-teal-700/80 text-teal-100 font-bold rounded-lg transition border border-teal-600/30"
            >
              This Week
            </button>
            <button
              onClick={() => handleQuickPreset('THIS_MONTH')}
              className="px-2.5 py-1 bg-teal-800/50 hover:bg-teal-700/80 text-teal-100 font-bold rounded-lg transition border border-teal-600/30"
            >
              This Month
            </button>
            <button
              onClick={() => handleQuickPreset('THIS_YEAR')}
              className="px-2.5 py-1 bg-teal-800/50 hover:bg-teal-700/80 text-teal-100 font-bold rounded-lg transition border border-teal-600/30"
            >
              This Year
            </button>
          </div>
        </div>
      </div>

      {/* District Officer Facility Selector (if applicable) */}
      {isDistrictOfficer && allFacilities.length > 0 && (
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Building2 className="w-5 h-5 text-emerald-600" />
            <div>
              <p className="text-xs font-bold text-slate-800">District Officer Facility Filter</p>
              <p className="text-[11px] text-slate-500">Filter report metrics by individual clinic or network wide</p>
            </div>
          </div>
          <select
            value={activeFacility?.id || ''}
            onChange={(e) => {
              const facId = e.target.value ? parseInt(e.target.value) : null;
              const found = allFacilities.find((f) => f.id === facId) || null;
              setActiveFacility(found);
            }}
            className="px-3 py-1.5 border border-slate-300 rounded-xl text-xs font-bold text-slate-800 focus:outline-emerald-600"
          >
            <option value="">All Facilities (District Network)</option>
            {allFacilities.map((f) => (
              <option key={f.id} value={f.id}>
                {f.facility_name} ({f.facility_type})
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Section 20: Period-Over-Period Comparison Banner */}
      {data?.comparison && (
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-100 gap-2">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-emerald-600" />
              <h2 className="text-xs font-extrabold text-slate-900 uppercase tracking-wider">
                Period Comparison: {data.comparison.period_label} ({data.comparison.current_range}) vs Previous ({data.comparison.previous_range})
              </h2>
            </div>
            <span className="text-[11px] text-slate-500 font-medium">Real-time baseline comparison</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 pt-3">
            {[
              { label: 'OPD Visits', metric: data.comparison.metrics.opd_visits },
              { label: 'New Patients', metric: data.comparison.metrics.new_patients },
              { label: 'Prescriptions Dispensed', metric: data.comparison.metrics.prescriptions_dispensed },
              { label: 'Lab Tests Verified', metric: data.comparison.metrics.lab_verified },
              { label: 'Referrals Created', metric: data.comparison.metrics.referrals_created },
            ].map((item, idx) => {
              const isPositive = (item.metric?.difference || 0) > 0;
              const isZero = (item.metric?.difference || 0) === 0;
              return (
                <div key={idx} className="bg-slate-50 p-3 rounded-xl border border-slate-200">
                  <p className="text-[11px] font-bold text-slate-500 uppercase">{item.label}</p>
                  <div className="flex items-baseline justify-between mt-1">
                    <span className="text-lg font-black text-slate-900">{item.metric?.current || 0}</span>
                    <span
                      className={`text-xs font-black flex items-center ${
                        isZero
                          ? 'text-slate-500'
                          : isPositive
                          ? 'text-emerald-700 bg-emerald-100/70 px-1.5 py-0.5 rounded'
                          : 'text-rose-700 bg-rose-100/70 px-1.5 py-0.5 rounded'
                      }`}
                    >
                      {!isZero && (isPositive ? <ArrowUpRight className="w-3 h-3 mr-0.5" /> : <ArrowDownRight className="w-3 h-3 mr-0.5" />)}
                      {item.metric?.display || '0'}
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-0.5">Previous: {item.metric?.previous || 0}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Section 23: Grouped Executive Summary Cards */}
      {data?.summary_cards && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Card 1: Patients */}
          <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <span className="text-[11px] font-black text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5 text-teal-600" />
                Patients
              </span>
              <span className="text-xs font-black text-teal-800">{data.summary_cards.patients.total_visits} Total</span>
            </div>
            <div className="grid grid-cols-2 gap-2 pt-2.5 text-xs">
              <div>
                <p className="text-[10px] text-slate-500 font-bold uppercase">New Patients</p>
                <p className="text-sm font-black text-slate-900">{data.summary_cards.patients.new_patients}</p>
              </div>
              <div>
                <p className="text-[10px] text-slate-500 font-bold uppercase">Completed</p>
                <p className="text-sm font-black text-emerald-700">{data.summary_cards.patients.completed}</p>
              </div>
              <div className="col-span-2">
                <p className="text-[10px] text-rose-700 font-bold uppercase">Emergency Priority</p>
                <p className="text-sm font-black text-rose-800">{data.summary_cards.patients.emergency}</p>
              </div>
            </div>
          </div>

          {/* Card 2: Services & Queue */}
          <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <span className="text-[11px] font-black text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-blue-600" />
                Services Queue
              </span>
              <span className="text-xs font-black text-blue-800">
                {data.summary_cards.services.triage_waiting + data.summary_cards.services.doctor_waiting} Waiting
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 pt-2.5 text-xs">
              <div>
                <p className="text-[10px] text-slate-500 font-bold uppercase">Triage</p>
                <p className="text-sm font-black text-slate-900">{data.summary_cards.services.triage_waiting}</p>
              </div>
              <div>
                <p className="text-[10px] text-slate-500 font-bold uppercase">Doctor Desk</p>
                <p className="text-sm font-black text-slate-900">{data.summary_cards.services.doctor_waiting}</p>
              </div>
              <div>
                <p className="text-[10px] text-slate-500 font-bold uppercase">Lab Orders</p>
                <p className="text-sm font-black text-purple-700">{data.summary_cards.services.lab_pending}</p>
              </div>
              <div>
                <p className="text-[10px] text-slate-500 font-bold uppercase">Pharmacy</p>
                <p className="text-sm font-black text-orange-700">{data.summary_cards.services.pharmacy_waiting}</p>
              </div>
            </div>
          </div>

          {/* Card 3: Pharmacy */}
          <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <span className="text-[11px] font-black text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <Pill className="w-3.5 h-3.5 text-emerald-600" />
                Pharmacy Stock
              </span>
              <span className="text-xs font-black text-emerald-800">{data.summary_cards.pharmacy.dispensed_units} Dispensed</span>
            </div>
            <div className="grid grid-cols-2 gap-2 pt-2.5 text-xs">
              <div>
                <p className="text-[10px] text-amber-700 font-bold uppercase">Low Stock</p>
                <p className="text-sm font-black text-amber-800">{data.summary_cards.pharmacy.low_stock_medicines}</p>
              </div>
              <div>
                <p className="text-[10px] text-rose-700 font-bold uppercase">Out of Stock</p>
                <p className="text-sm font-black text-rose-800">{data.summary_cards.pharmacy.out_of_stock_medicines}</p>
              </div>
              <div className="col-span-2">
                <p className="text-[10px] text-orange-700 font-bold uppercase">Expiring (60 Days)</p>
                <p className="text-sm font-black text-orange-800">{data.summary_cards.pharmacy.expiring_soon_batches} Batches</p>
              </div>
            </div>
          </div>

          {/* Card 4: Procurement */}
          <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <span className="text-[11px] font-black text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <ShoppingCart className="w-3.5 h-3.5 text-indigo-600" />
                Procurement
              </span>
              <span className="text-xs font-black text-indigo-800">
                ₹{Number(data.summary_cards.procurement.procurement_amount).toLocaleString('en-IN')}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 pt-2.5 text-xs">
              <div>
                <p className="text-[10px] text-slate-500 font-bold uppercase">Pending POs</p>
                <p className="text-sm font-black text-amber-700">{data.summary_cards.procurement.pending_po}</p>
              </div>
              <div>
                <p className="text-[10px] text-slate-500 font-bold uppercase">Received POs</p>
                <p className="text-sm font-black text-emerald-700">{data.summary_cards.procurement.received_po}</p>
              </div>
              <div className="col-span-2">
                <p className="text-[10px] text-slate-400 font-bold uppercase">Vendors In Network</p>
                <p className="text-sm font-black text-slate-800">{data.pharmacy.vendors.active_vendors} Active</p>
              </div>
            </div>
          </div>

          {/* Card 5: Referrals */}
          <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <span className="text-[11px] font-black text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <Share2 className="w-3.5 h-3.5 text-purple-600" />
                Referrals
              </span>
              <span className="text-xs font-black text-purple-800">{data.summary_cards.referrals.created} Created</span>
            </div>
            <div className="grid grid-cols-2 gap-2 pt-2.5 text-xs">
              <div>
                <p className="text-[10px] text-slate-500 font-bold uppercase">In Transit</p>
                <p className="text-sm font-black text-amber-700">{data.summary_cards.referrals.in_transit}</p>
              </div>
              <div>
                <p className="text-[10px] text-slate-500 font-bold uppercase">Completed</p>
                <p className="text-sm font-black text-emerald-700">{data.summary_cards.referrals.completed}</p>
              </div>
              <div className="col-span-2">
                <p className="text-[10px] text-slate-400 font-bold uppercase">Facility Scope</p>
                <p className="text-[11px] font-bold text-slate-700 truncate">
                  {data.referrals.outgoing_count} Out / {data.referrals.incoming_count} In
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Primary Category Navigation Bar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-2 shadow-xs flex items-center gap-1.5 overflow-x-auto">
        {[
          { id: 'opd', label: 'OPD & Demographics', icon: Users },
          { id: 'queues', label: 'Queue & Services', icon: Clock },
          { id: 'staff', label: 'Doctor & Staff', icon: Stethoscope },
          { id: 'lab', label: 'Laboratory', icon: TestTube },
          { id: 'pharmacy', label: 'Pharmacy Intelligence', icon: Pill },
          { id: 'referrals', label: 'Referrals & Follow-ups', icon: Share2 },
          { id: 'ncd', label: 'NCD Care', icon: Activity },
          ...(data?.maternal_child?.available ? [{ id: 'maternal', label: 'Maternal & Child', icon: Baby }] : []),
          { id: 'alerts', label: 'Operational Alerts', icon: AlertTriangle },
          { id: 'exports', label: 'Quick CSV Exports', icon: FileSpreadsheet },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3.5 py-2.5 rounded-xl text-xs font-black flex items-center gap-2 whitespace-nowrap transition ${
                isActive
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Main Tab Content */}
      {loading ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center shadow-xs">
          <RefreshCw className="w-8 h-8 text-emerald-600 animate-spin mx-auto mb-3" />
          <p className="text-sm font-bold text-slate-800">Calculating authoritative hospital report metrics...</p>
          <p className="text-xs text-slate-400 mt-1">Reconciling live database transactions and scope boundaries</p>
        </div>
      ) : error ? (
        <div className="bg-rose-50 border border-rose-200 p-6 rounded-2xl text-center">
          <AlertCircle className="w-8 h-8 text-rose-600 mx-auto mb-2" />
          <p className="text-sm font-bold text-rose-900">{error}</p>
          <button
            onClick={fetchReportData}
            className="mt-3 px-4 py-2 bg-rose-600 text-white rounded-xl text-xs font-bold hover:bg-rose-700 transition"
          >
            Retry Report Request
          </button>
        </div>
      ) : data ? (
        <div>
          {/* TAB 1: OPD & PATIENTS */}
          {activeTab === 'opd' && (
            <div className="space-y-6">
              {/* Trend Chart & Breakdown */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-4">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                    <div>
                      <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                        <BarChart3 className="w-4 h-4 text-emerald-600" />
                        OPD Footfall Distribution ({period.toUpperCase()})
                      </h3>
                      <p className="text-xs text-slate-500">
                        {period === 'day' ? 'Hourly patient arrivals throughout the clinic shift' : 'Sequential period arrivals'}
                      </p>
                    </div>
                    <button
                      onClick={() => handleExportCSV('opd', 'OPD Visit Ledger')}
                      className="px-3 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 font-bold text-xs rounded-xl flex items-center gap-1.5 transition"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Export CSV</span>
                    </button>
                  </div>

                  {/* Trend visualization */}
                  {data.opd_patient.trend.length === 0 ? (
                    <div className="py-12 text-center text-xs text-slate-400">No OPD visits logged in this period.</div>
                  ) : (
                    <div className="pt-2">
                      <div className="flex items-end gap-2 h-44 border-b border-slate-200 pb-2">
                        {data.opd_patient.trend.map((pt, idx) => {
                          const maxVisits = Math.max(...data.opd_patient.trend.map((t) => t.visits), 1);
                          const barHeight = Math.round((pt.visits / maxVisits) * 100);
                          return (
                            <div key={idx} className="flex-1 flex flex-col items-center gap-1 group relative">
                              {/* Tooltip */}
                              <div className="opacity-0 group-hover:opacity-100 transition absolute -top-8 bg-slate-900 text-white text-[10px] font-bold px-2 py-0.5 rounded shadow pointer-events-none whitespace-nowrap z-20">
                                {pt.label}: {pt.visits} Visits
                              </div>
                              <div className="w-full bg-slate-100 rounded-t h-full flex items-end">
                                <div
                                  style={{ height: `${barHeight}%` }}
                                  className={`w-full rounded-t transition-all ${
                                    pt.visits > 0 ? 'bg-emerald-500 hover:bg-emerald-600' : 'bg-transparent'
                                  }`}
                                />
                              </div>
                              <span className="text-[10px] font-bold text-slate-500 truncate w-full text-center">
                                {pt.label}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>

                {/* Demographics & Age Groups */}
                <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-5">
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 pb-3 border-b border-slate-100">
                      <Users className="w-4 h-4 text-emerald-600" />
                      Patient Demographics
                    </h3>
                    <div className="grid grid-cols-3 gap-2 pt-3 text-center">
                      <div className="bg-blue-50 p-2.5 rounded-xl border border-blue-200">
                        <p className="text-[10px] font-bold text-blue-700 uppercase">Male</p>
                        <p className="text-base font-black text-blue-900">{data.opd_patient.demographics.male}</p>
                      </div>
                      <div className="bg-rose-50 p-2.5 rounded-xl border border-rose-200">
                        <p className="text-[10px] font-bold text-rose-700 uppercase">Female</p>
                        <p className="text-base font-black text-rose-900">{data.opd_patient.demographics.female}</p>
                      </div>
                      <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200">
                        <p className="text-[10px] font-bold text-slate-600 uppercase">Other</p>
                        <p className="text-base font-black text-slate-900">{data.opd_patient.demographics.other}</p>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Age Group Breakdown</h4>
                    <div className="space-y-2 text-xs">
                      {[
                        { label: '0–5 Years (Infant / Child)', count: data.opd_patient.age_groups['0_5'], color: 'bg-emerald-500' },
                        { label: '6–18 Years (Adolescent)', count: data.opd_patient.age_groups['6_18'], color: 'bg-teal-500' },
                        { label: '19–30 Years (Young Adult)', count: data.opd_patient.age_groups['19_30'], color: 'bg-blue-500' },
                        { label: '31–45 Years (Adult)', count: data.opd_patient.age_groups['31_45'], color: 'bg-indigo-500' },
                        { label: '46–60 Years (Middle Age)', count: data.opd_patient.age_groups['46_60'], color: 'bg-amber-500' },
                        { label: '60+ Years (Senior Citizen)', count: data.opd_patient.age_groups['60_plus'], color: 'bg-purple-500' },
                      ].map((ag, idx) => {
                        const totalPts = Math.max(data.opd_patient.total_registered_patients, 1);
                        const pct = Math.round((ag.count / totalPts) * 100);
                        return (
                          <div key={idx} className="space-y-1">
                            <div className="flex justify-between text-[11px] font-semibold">
                              <span className="text-slate-700">{ag.label}</span>
                              <span className="font-bold text-slate-900">{ag.count} ({pct}%)</span>
                            </div>
                            <div className="w-full bg-slate-100 rounded-full h-1.5">
                              <div className={`${ag.color} h-1.5 rounded-full`} style={{ width: `${pct}%` }} />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: QUEUE & SERVICE REPORT */}
          {activeTab === 'queues' && (
            <div className="space-y-6">
              {/* Turnaround Time Metrics */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
                  <p className="text-[10px] font-bold text-slate-500 uppercase">Average Triage Wait</p>
                  <h4 className="text-xl font-black text-slate-900 mt-1">
                    {data.queue_service.avg_triage_wait_minutes !== null ? `${data.queue_service.avg_triage_wait_minutes} mins` : 'N/A'}
                  </h4>
                  <p className="text-[10px] text-slate-400 mt-0.5">Registration to vitals recording</p>
                </div>
                <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
                  <p className="text-[10px] font-bold text-slate-500 uppercase">Average Doctor Wait</p>
                  <h4 className="text-xl font-black text-slate-900 mt-1">
                    {data.queue_service.avg_doctor_wait_minutes !== null ? `${data.queue_service.avg_doctor_wait_minutes} mins` : 'N/A'}
                  </h4>
                  <p className="text-[10px] text-slate-400 mt-0.5">Triage completion to consultation</p>
                </div>
                <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
                  <p className="text-[10px] font-bold text-slate-500 uppercase">Average Total Turnaround</p>
                  <h4 className="text-xl font-black text-slate-900 mt-1">
                    {data.queue_service.avg_total_duration_minutes !== null ? `${data.queue_service.avg_total_duration_minutes} mins` : 'N/A'}
                  </h4>
                  <p className="text-[10px] text-slate-400 mt-0.5">Arrival to final clinic discharge</p>
                </div>
                <div className="bg-white p-4 rounded-2xl border border-amber-200 bg-amber-50/20 shadow-xs">
                  <p className="text-[10px] font-bold text-amber-800 uppercase">Peak Queue Period</p>
                  <h4 className="text-xl font-black text-amber-900 mt-1">
                    {data.queue_service.peak_queue_period}
                  </h4>
                  <p className="text-[10px] text-amber-700 mt-0.5">Maximum simultaneous arrivals</p>
                </div>
              </div>

              {/* Stages Progression Cards */}
              <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 pb-3 border-b border-slate-100">
                  <Clock className="w-4 h-4 text-emerald-600" />
                  Service Desk Throughput Stages
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
                  {Object.entries(data.queue_service.stages).map(([stageName, counts]) => (
                    <div key={stageName} className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 flex flex-col justify-between">
                      <p className="text-xs font-black text-slate-900 uppercase tracking-wider">{stageName}</p>
                      <div className="space-y-1.5 mt-3 text-xs">
                        <div className="flex justify-between text-slate-600">
                          <span>Waiting:</span>
                          <span className="font-bold text-amber-800">{counts.waiting}</span>
                        </div>
                        <div className="flex justify-between text-slate-600">
                          <span>In Progress:</span>
                          <span className="font-bold text-blue-800">{counts.in_progress}</span>
                        </div>
                        <div className="flex justify-between text-slate-600 border-t border-slate-200 pt-1">
                          <span>Completed:</span>
                          <span className="font-bold text-emerald-800">{counts.completed}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: DOCTORS & STAFF */}
          {activeTab === 'staff' && (
            <div className="space-y-6">
              {/* Staff Roles Status */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                {[
                  { role: 'Doctors', stat: data.doctor_staff.roles.doctors },
                  { role: 'Nurses', stat: data.doctor_staff.roles.nurses },
                  { role: 'Lab Technicians', stat: data.doctor_staff.roles.lab_technicians },
                  { role: 'Pharmacists', stat: data.doctor_staff.roles.pharmacists },
                  { role: 'Hospital Admins', stat: data.doctor_staff.roles.admins },
                ].map((item, idx) => (
                  <div key={idx} className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                    <p className="text-[10px] font-bold text-slate-500 uppercase">{item.role}</p>
                    <h4 className="text-lg font-black text-slate-900 mt-1">{item.stat?.total || 0} Total</h4>
                    <div className="flex items-center gap-2 mt-1 text-xs">
                      <span className="text-emerald-700 font-bold">{item.stat?.active || 0} Active</span>
                      <span className="text-slate-400">•</span>
                      <span className="text-slate-500 font-medium">{item.stat?.inactive || 0} Inactive</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Doctor Activity Table */}
              <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                      <Stethoscope className="w-4 h-4 text-emerald-600" />
                      Doctor Clinical Activity Ledger ({period.toUpperCase()})
                    </h3>
                    <p className="text-xs text-slate-500">
                      Actual consultations completed, prescriptions written, lab investigations ordered, and referrals created.
                    </p>
                  </div>
                  <button
                    onClick={() => handleExportCSV('doctor_activity', 'Doctor Clinical Activity')}
                    className="px-3 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 font-bold text-xs rounded-xl flex items-center gap-1.5 transition self-start sm:self-auto"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Export CSV</span>
                  </button>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase text-[10px]">
                        <th className="py-2.5 px-3">Doctor</th>
                        <th className="py-2.5 px-3">Status</th>
                        <th className="py-2.5 px-3 text-right">Patients Consulted</th>
                        <th className="py-2.5 px-3 text-right">Consultations Completed</th>
                        <th className="py-2.5 px-3 text-right">Lab Orders</th>
                        <th className="py-2.5 px-3 text-right">Prescriptions</th>
                        <th className="py-2.5 px-3 text-right">Referrals</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {data.doctor_staff.doctor_activity.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="py-8 text-center text-slate-400">
                            No doctors assigned to this facility.
                          </td>
                        </tr>
                      ) : (
                        data.doctor_staff.doctor_activity.map((doc) => (
                          <tr key={doc.doctor_id} className="hover:bg-slate-50/80 transition">
                            <td className="py-2.5 px-3 font-bold text-slate-900">
                              {doc.name}
                              <span className="block text-[10px] text-slate-400 font-normal">@{doc.username}</span>
                            </td>
                            <td className="py-2.5 px-3">
                              <span
                                className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase ${
                                  doc.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'
                                }`}
                              >
                                {doc.is_active ? 'Active' : 'Inactive'}
                              </span>
                            </td>
                            <td className="py-2.5 px-3 text-right font-semibold text-slate-800">{doc.patients_consulted}</td>
                            <td className="py-2.5 px-3 text-right font-black text-emerald-800">{doc.consultations_completed}</td>
                            <td className="py-2.5 px-3 text-right font-semibold text-purple-800">{doc.lab_orders}</td>
                            <td className="py-2.5 px-3 text-right font-semibold text-orange-800">{doc.prescriptions}</td>
                            <td className="py-2.5 px-3 text-right font-semibold text-blue-800">{doc.referrals}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: LABORATORY */}
          {activeTab === 'lab' && (
            <div className="space-y-6">
              {/* Lab KPI Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                  <p className="text-[10px] font-bold text-slate-500 uppercase">Total Orders</p>
                  <h4 className="text-xl font-black text-slate-900 mt-1">{data.laboratory.total_orders}</h4>
                </div>
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                  <p className="text-[10px] font-bold text-slate-500 uppercase">Samples Collected</p>
                  <h4 className="text-xl font-black text-slate-900 mt-1">{data.laboratory.samples_collected}</h4>
                </div>
                <div className="bg-white p-4 rounded-xl border border-purple-200 bg-purple-50/20 shadow-xs">
                  <p className="text-[10px] font-bold text-purple-800 uppercase">In Progress</p>
                  <h4 className="text-xl font-black text-purple-900 mt-1">{data.laboratory.in_progress}</h4>
                </div>
                <div className="bg-white p-4 rounded-xl border border-amber-200 bg-amber-50/20 shadow-xs">
                  <p className="text-[10px] font-bold text-amber-800 uppercase">Pending</p>
                  <h4 className="text-xl font-black text-amber-900 mt-1">{data.laboratory.results_pending}</h4>
                </div>
                <div className="bg-white p-4 rounded-xl border border-emerald-200 bg-emerald-50/20 shadow-xs">
                  <p className="text-[10px] font-bold text-emerald-800 uppercase">Verified</p>
                  <h4 className="text-xl font-black text-emerald-900 mt-1">{data.laboratory.verified_results}</h4>
                </div>
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                  <p className="text-[10px] font-bold text-slate-500 uppercase">Cancelled</p>
                  <h4 className="text-xl font-black text-slate-900 mt-1">{data.laboratory.cancelled_tests}</h4>
                </div>
              </div>

              {/* Lab Test Master Breakdown Table */}
              <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                      <TestTube className="w-4 h-4 text-emerald-600" />
                      Laboratory Test Diagnostics Breakdown
                    </h3>
                    <p className="text-xs text-slate-500">Breakdown across all test investigations performed at facility</p>
                  </div>
                  <button
                    onClick={() => handleExportCSV('laboratory', 'Laboratory Diagnostics Ledger')}
                    className="px-3 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 font-bold text-xs rounded-xl flex items-center gap-1.5 transition self-start sm:self-auto"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Export CSV</span>
                  </button>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase text-[10px]">
                        <th className="py-2.5 px-3">Test Code</th>
                        <th className="py-2.5 px-3">Test Name</th>
                        <th className="py-2.5 px-3">Category</th>
                        <th className="py-2.5 px-3">Reference Range</th>
                        <th className="py-2.5 px-3 text-right">Orders In Period</th>
                        <th className="py-2.5 px-3 text-right">Verified</th>
                        <th className="py-2.5 px-3 text-right">Pending</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {data.laboratory.test_breakdown.map((test) => (
                        <tr key={test.code} className="hover:bg-slate-50/80 transition">
                          <td className="py-2.5 px-3 font-mono font-bold text-slate-800">{test.code}</td>
                          <td className="py-2.5 px-3 font-bold text-slate-900">{test.name}</td>
                          <td className="py-2.5 px-3 text-slate-600">{test.category}</td>
                          <td className="py-2.5 px-3 text-slate-500 font-mono text-[11px]">{test.reference_range} {test.unit}</td>
                          <td className="py-2.5 px-3 text-right font-black text-slate-900">{test.total_orders}</td>
                          <td className="py-2.5 px-3 text-right font-black text-emerald-700">{test.verified}</td>
                          <td className="py-2.5 px-3 text-right font-black text-amber-700">{test.pending}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: PHARMACY INTELLIGENCE (Comprehensive hub) */}
          {activeTab === 'pharmacy' && (
            <div className="space-y-6">
              {/* Pharmacy Sub-tab Selector */}
              <div className="inline-flex bg-slate-100 p-1 rounded-xl border border-slate-200 flex-wrap gap-1">
                {[
                  { id: 'movement', label: 'Stock Consumption & Reconciliation' },
                  { id: 'top_meds', label: 'Top Dispensed Medicines' },
                  { id: 'expiry', label: 'Expiry Monitoring Ledger' },
                  { id: 'low_stock', label: 'Low Stock & Reorder Alerts' },
                  { id: 'procurement', label: 'Purchases & Procurement' },
                ].map((st) => (
                  <button
                    key={st.id}
                    onClick={() => setPharmacySubTab(st.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                      pharmacySubTab === st.id
                        ? 'bg-white text-emerald-900 shadow-xs border border-slate-200'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    {st.label}
                  </button>
                ))}
              </div>

              {/* Sub-view: Reconciled Stock Movement & Consumption */}
              {pharmacySubTab === 'movement' && (
                <div className="space-y-4">
                  {/* Reconciliation Banner */}
                  <div className="bg-emerald-950 text-white p-4 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm border border-emerald-800">
                    <div>
                      <p className="text-xs font-extrabold uppercase tracking-wider text-emerald-400">
                        Authoritative Inventory Reconciliation Formula
                      </p>
                      <p className="text-xs text-emerald-200 mt-0.5">
                        Opening Stock + Stock Received - Stock Dispensed +/- Audit Adjustments = Closing Stock
                      </p>
                    </div>

                    <div className="flex items-center gap-3 text-xs bg-emerald-900/80 px-4 py-2 rounded-xl border border-emerald-700/60 font-mono">
                      <span>Open: <b>{data.pharmacy.stock_movement.summary.opening_stock}</b></span>
                      <span>+</span>
                      <span>Rec: <b>{data.pharmacy.stock_movement.summary.stock_received}</b></span>
                      <span>-</span>
                      <span>Disp: <b>{data.pharmacy.stock_movement.summary.stock_dispensed}</b></span>
                      <span>=</span>
                      <span className="text-emerald-300 font-black">Close: {data.pharmacy.stock_movement.summary.closing_stock}</span>
                    </div>
                  </div>

                  {/* Stock Movement Table */}
                  <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                      <div>
                        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                          <Package className="w-4 h-4 text-emerald-600" />
                          Stock Consumption & Movement Ledger ({period.toUpperCase()})
                        </h3>
                        <p className="text-xs text-slate-500">
                          Reconciled balance for every medicine actively stocked or transacted during selected period
                        </p>
                      </div>
                      <button
                        onClick={() => handleExportCSV('stock_consumption', 'Stock Consumption Ledger')}
                        className="px-3 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 font-bold text-xs rounded-xl flex items-center gap-1.5 transition self-start sm:self-auto"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Export CSV</span>
                      </button>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead>
                          <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase text-[10px]">
                            <th className="py-2.5 px-3">Medicine</th>
                            <th className="py-2.5 px-3">Dosage / Unit</th>
                            <th className="py-2.5 px-3 text-right">Opening</th>
                            <th className="py-2.5 px-3 text-right text-emerald-800">Received (+)</th>
                            <th className="py-2.5 px-3 text-right text-rose-800">Dispensed (-)</th>
                            <th className="py-2.5 px-3 text-right text-blue-800">Adjusted (+/-)</th>
                            <th className="py-2.5 px-3 text-right font-black text-slate-900">Closing Stock</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {data.pharmacy.stock_movement.items.length === 0 ? (
                            <tr>
                              <td colSpan={7} className="py-8 text-center text-slate-400">
                                No stock transactions recorded in this period.
                              </td>
                            </tr>
                          ) : (
                            data.pharmacy.stock_movement.items.map((item) => (
                              <tr key={item.medicine_id} className="hover:bg-slate-50/80 transition">
                                <td className="py-2.5 px-3 font-bold text-slate-900">
                                  {item.medicine}
                                  {item.brand_name && (
                                    <span className="block text-[10px] text-slate-400 font-normal">{item.brand_name}</span>
                                  )}
                                </td>
                                <td className="py-2.5 px-3 text-slate-600">
                                  {item.dosage_form} ({item.unit})
                                </td>
                                <td className="py-2.5 px-3 text-right font-mono font-medium text-slate-700">{item.opening_stock}</td>
                                <td className="py-2.5 px-3 text-right font-mono font-bold text-emerald-700">+{item.received}</td>
                                <td className="py-2.5 px-3 text-right font-mono font-bold text-rose-700">-{item.dispensed}</td>
                                <td className="py-2.5 px-3 text-right font-mono font-medium text-blue-700">
                                  {item.adjusted >= 0 ? `+${item.adjusted}` : item.adjusted}
                                </td>
                                <td className="py-2.5 px-3 text-right font-mono font-black text-slate-900">{item.closing_stock}</td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* Sub-view: Top Dispensed Medicines */}
              {pharmacySubTab === 'top_meds' && (
                <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                    <div>
                      <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                        <TrendingUp className="w-4 h-4 text-emerald-600" />
                        Top Dispensed Medicines ({period.toUpperCase()})
                      </h3>
                      <p className="text-xs text-slate-500">Sorted by authoritative quantity dispensed to patients</p>
                    </div>
                    <button
                      onClick={() => handleExportCSV('stock_consumption', 'Top Dispensed Medicines')}
                      className="px-3 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 font-bold text-xs rounded-xl flex items-center gap-1.5 transition self-start sm:self-auto"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Export CSV</span>
                    </button>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase text-[10px]">
                          <th className="py-2.5 px-3">Rank</th>
                          <th className="py-2.5 px-3">Medicine</th>
                          <th className="py-2.5 px-3 text-right">Quantity Dispensed</th>
                          <th className="py-2.5 px-3 text-right">Prescriptions Count</th>
                          <th className="py-2.5 px-3">Volume Distribution</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {data.pharmacy.dispensing.top_dispensed_medicines.length === 0 ? (
                          <tr>
                            <td colSpan={5} className="py-8 text-center text-slate-400">
                              No medicines dispensed in this reporting period.
                            </td>
                          </tr>
                        ) : (
                          data.pharmacy.dispensing.top_dispensed_medicines.map((m, idx) => {
                            const maxQty = Math.max(
                              ...data.pharmacy.dispensing.top_dispensed_medicines.map((item) => item.quantity_dispensed),
                              1
                            );
                            const barPct = Math.round((m.quantity_dispensed / maxQty) * 100);
                            return (
                              <tr key={m.medicine_id} className="hover:bg-slate-50/80 transition">
                                <td className="py-2.5 px-3 font-mono font-bold text-slate-500">#{idx + 1}</td>
                                <td className="py-2.5 px-3 font-bold text-slate-900">
                                  {m.generic_name}
                                  {m.brand_name && (
                                    <span className="block text-[10px] text-slate-400 font-normal">{m.brand_name}</span>
                                  )}
                                </td>
                                <td className="py-2.5 px-3 text-right font-black text-emerald-800">
                                  {m.quantity_dispensed} {m.unit}
                                </td>
                                <td className="py-2.5 px-3 text-right font-semibold text-slate-700">{m.prescriptions_count} Rx</td>
                                <td className="py-2.5 px-3 w-1/4">
                                  <div className="w-full bg-slate-100 rounded-full h-2">
                                    <div className="bg-emerald-600 h-2 rounded-full" style={{ width: `${barPct}%` }} />
                                  </div>
                                </td>
                              </tr>
                            );
                          })
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Sub-view: Expiry Monitoring */}
              {pharmacySubTab === 'expiry' && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                    <div className="bg-rose-50 border border-rose-200 p-3.5 rounded-xl text-center">
                      <p className="text-[10px] font-bold text-rose-800 uppercase">Expired</p>
                      <p className="text-xl font-black text-rose-900 mt-0.5">
                        {data.pharmacy.expiry_monitoring.categories.expired}
                      </p>
                    </div>
                    <div className="bg-amber-50 border border-amber-200 p-3.5 rounded-xl text-center">
                      <p className="text-[10px] font-bold text-amber-800 uppercase">&le; 7 Days</p>
                      <p className="text-xl font-black text-amber-900 mt-0.5">
                        {data.pharmacy.expiry_monitoring.categories.expires_within_7_days}
                      </p>
                    </div>
                    <div className="bg-orange-50 border border-orange-200 p-3.5 rounded-xl text-center">
                      <p className="text-[10px] font-bold text-orange-800 uppercase">&le; 30 Days</p>
                      <p className="text-xl font-black text-orange-900 mt-0.5">
                        {data.pharmacy.expiry_monitoring.categories.expires_within_30_days}
                      </p>
                    </div>
                    <div className="bg-yellow-50 border border-yellow-200 p-3.5 rounded-xl text-center">
                      <p className="text-[10px] font-bold text-yellow-800 uppercase">&le; 60 Days</p>
                      <p className="text-xl font-black text-yellow-900 mt-0.5">
                        {data.pharmacy.expiry_monitoring.categories.expires_within_60_days}
                      </p>
                    </div>
                    <div className="bg-slate-50 border border-slate-200 p-3.5 rounded-xl text-center col-span-2 sm:col-span-1">
                      <p className="text-[10px] font-bold text-slate-600 uppercase">&le; 90 Days</p>
                      <p className="text-xl font-black text-slate-900 mt-0.5">
                        {data.pharmacy.expiry_monitoring.categories.expires_within_90_days}
                      </p>
                    </div>
                  </div>

                  <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                      <div>
                        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                          <AlertTriangle className="w-4 h-4 text-rose-600" />
                          Batch Expiry Surveillance Ledger
                        </h3>
                        <p className="text-xs text-slate-500">
                          Batches with actual expiry dates within next 90 days. Expired batches cannot be dispensed.
                        </p>
                      </div>
                      <button
                        onClick={() => handleExportCSV('expiry', 'Batch Expiry Ledger')}
                        className="px-3 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 font-bold text-xs rounded-xl flex items-center gap-1.5 transition self-start sm:self-auto"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Export CSV</span>
                      </button>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead>
                          <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase text-[10px]">
                            <th className="py-2.5 px-3">Medicine</th>
                            <th className="py-2.5 px-3 font-mono">Batch Number</th>
                            <th className="py-2.5 px-3 text-right">Quantity</th>
                            <th className="py-2.5 px-3">Expiry Date</th>
                            <th className="py-2.5 px-3 text-right">Days Remaining</th>
                            <th className="py-2.5 px-3">Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {data.pharmacy.expiry_monitoring.batches.length === 0 ? (
                            <tr>
                              <td colSpan={6} className="py-8 text-center text-slate-400">
                                No expiring or expired batches found within 90 days.
                              </td>
                            </tr>
                          ) : (
                            data.pharmacy.expiry_monitoring.batches.map((b) => (
                              <tr key={b.batch_id} className="hover:bg-slate-50/80 transition">
                                <td className="py-2.5 px-3 font-bold text-slate-900">{b.medicine_name}</td>
                                <td className="py-2.5 px-3 font-mono text-slate-700">{b.batch_number}</td>
                                <td className="py-2.5 px-3 text-right font-black text-slate-900">{b.quantity}</td>
                                <td className="py-2.5 px-3 font-medium text-slate-700">{b.expiry_date}</td>
                                <td className="py-2.5 px-3 text-right font-black">
                                  {b.days_remaining <= 0 ? (
                                    <span className="text-rose-700">Expired</span>
                                  ) : (
                                    <span className={b.days_remaining <= 30 ? 'text-amber-700' : 'text-slate-800'}>
                                      {b.days_remaining} days
                                    </span>
                                  )}
                                </td>
                                <td className="py-2.5 px-3">
                                  <span
                                    className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase ${
                                      b.category === 'EXPIRED'
                                        ? 'bg-rose-100 text-rose-800'
                                        : b.category === 'EXPIRES_7_DAYS'
                                        ? 'bg-amber-100 text-amber-800'
                                        : 'bg-yellow-100 text-yellow-800'
                                    }`}
                                  >
                                    {b.category.replace('_', ' ')}
                                  </span>
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* Sub-view: Low Stock Report */}
              {pharmacySubTab === 'low_stock' && (
                <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                    <div>
                      <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 text-amber-600" />
                        Low Stock & Out of Stock Master Audit
                      </h3>
                      <p className="text-xs text-slate-500">
                        Uses identical business rule threshold (Quantity &le; Minimum Stock) as Pharmacy Dashboard
                      </p>
                    </div>
                    <button
                      onClick={() => handleExportCSV('low_stock', 'Low Stock Audit')}
                      className="px-3 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 font-bold text-xs rounded-xl flex items-center gap-1.5 transition self-start sm:self-auto"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Export CSV</span>
                    </button>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase text-[10px]">
                          <th className="py-2.5 px-3">Medicine</th>
                          <th className="py-2.5 px-3">Category</th>
                          <th className="py-2.5 px-3 text-right">Current Available Stock</th>
                          <th className="py-2.5 px-3 text-right">Min Stock Threshold</th>
                          <th className="py-2.5 px-3 text-right">Reorder Level</th>
                          <th className="py-2.5 px-3">Stock Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {data.pharmacy.low_stock_report.map((med) => (
                          <tr key={med.id} className="hover:bg-slate-50/80 transition">
                            <td className="py-2.5 px-3 font-bold text-slate-900">
                              {med.generic_name}
                              {med.brand_name && (
                                <span className="block text-[10px] text-slate-400 font-normal">{med.brand_name}</span>
                              )}
                            </td>
                            <td className="py-2.5 px-3 text-slate-600">{med.category}</td>
                            <td className="py-2.5 px-3 text-right font-black text-slate-900">
                              {med.current_stock} {med.unit}
                            </td>
                            <td className="py-2.5 px-3 text-right font-mono text-slate-500">{med.minimum_stock}</td>
                            <td className="py-2.5 px-3 text-right font-mono text-slate-500">{med.reorder_level}</td>
                            <td className="py-2.5 px-3">
                              <span
                                className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase ${
                                  med.status === 'OUT_OF_STOCK'
                                    ? 'bg-rose-100 text-rose-800'
                                    : med.status === 'LOW_STOCK'
                                    ? 'bg-amber-100 text-amber-800'
                                    : 'bg-emerald-100 text-emerald-800'
                                }`}
                              >
                                {med.status.replace('_', ' ')}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Sub-view: Purchases & Procurement */}
              {pharmacySubTab === 'procurement' && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                      <p className="text-[10px] font-bold text-slate-500 uppercase">Total POs in Period</p>
                      <h4 className="text-xl font-black text-slate-900 mt-1">
                        {data.pharmacy.purchases.total_purchase_orders}
                      </h4>
                    </div>
                    <div className="bg-white p-4 rounded-xl border border-amber-200 bg-amber-50/20 shadow-xs">
                      <p className="text-[10px] font-bold text-amber-800 uppercase">Pending Approval</p>
                      <h4 className="text-xl font-black text-amber-900 mt-1">
                        {data.pharmacy.purchases.pending_approval}
                      </h4>
                    </div>
                    <div className="bg-white p-4 rounded-xl border border-emerald-200 bg-emerald-50/20 shadow-xs">
                      <p className="text-[10px] font-bold text-emerald-800 uppercase">Received Stock</p>
                      <h4 className="text-xl font-black text-emerald-900 mt-1">
                        {data.pharmacy.purchases.received}
                      </h4>
                    </div>
                    <div className="bg-white p-4 rounded-xl border border-indigo-200 bg-indigo-50/20 shadow-xs">
                      <p className="text-[10px] font-bold text-indigo-800 uppercase">Total Spend</p>
                      <h4 className="text-xl font-black text-indigo-900 mt-1">
                        ₹{Number(data.pharmacy.purchases.procurement_amount).toLocaleString('en-IN')}
                      </h4>
                    </div>
                  </div>

                  <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                      <div>
                        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                          <ShoppingCart className="w-4 h-4 text-emerald-600" />
                          Purchase Orders & Procurement Ledger
                        </h3>
                        <p className="text-xs text-slate-500">Approved, ordered, and received purchase orders</p>
                      </div>
                      <button
                        onClick={() => handleExportCSV('procurement', 'Purchase Orders Ledger')}
                        className="px-3 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 font-bold text-xs rounded-xl flex items-center gap-1.5 transition self-start sm:self-auto"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Export CSV</span>
                      </button>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead>
                          <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase text-[10px]">
                            <th className="py-2.5 px-3">PO Number</th>
                            <th className="py-2.5 px-3">Vendor</th>
                            <th className="py-2.5 px-3">Order Date</th>
                            <th className="py-2.5 px-3">Status</th>
                            <th className="py-2.5 px-3 text-right">Total Amount</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {data.pharmacy.purchases.purchase_orders_list.length === 0 ? (
                            <tr>
                              <td colSpan={5} className="py-8 text-center text-slate-400">
                                No purchase orders raised during this reporting period.
                              </td>
                            </tr>
                          ) : (
                            data.pharmacy.purchases.purchase_orders_list.map((po) => (
                              <tr key={po.id} className="hover:bg-slate-50/80 transition">
                                <td className="py-2.5 px-3 font-mono font-bold text-slate-900">{po.po_number}</td>
                                <td className="py-2.5 px-3 font-medium text-slate-800">{po.vendor_name}</td>
                                <td className="py-2.5 px-3 text-slate-600">{po.order_date}</td>
                                <td className="py-2.5 px-3">
                                  <span
                                    className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase ${
                                      po.status === 'RECEIVED'
                                        ? 'bg-emerald-100 text-emerald-800'
                                        : po.status === 'CANCELLED'
                                        ? 'bg-rose-100 text-rose-800'
                                        : 'bg-amber-100 text-amber-800'
                                    }`}
                                  >
                                    {po.status.replace('_', ' ')}
                                  </span>
                                </td>
                                <td className="py-2.5 px-3 text-right font-black text-slate-900">
                                  ₹{Number(po.total_amount).toLocaleString('en-IN')}
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 6: REFERRALS & FOLLOW-UPS */}
          {activeTab === 'referrals' && (
            <div className="space-y-6">
              {/* Referral Status Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                  <p className="text-[10px] font-bold text-slate-500 uppercase">Total Referrals</p>
                  <h4 className="text-xl font-black text-slate-900 mt-1">{data.referrals.total_referrals}</h4>
                </div>
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                  <p className="text-[10px] font-bold text-slate-500 uppercase">Created</p>
                  <h4 className="text-xl font-black text-slate-900 mt-1">{data.referrals.created}</h4>
                </div>
                <div className="bg-white p-4 rounded-xl border border-blue-200 bg-blue-50/20 shadow-xs">
                  <p className="text-[10px] font-bold text-blue-800 uppercase">Accepted</p>
                  <h4 className="text-xl font-black text-blue-900 mt-1">{data.referrals.accepted}</h4>
                </div>
                <div className="bg-white p-4 rounded-xl border border-amber-200 bg-amber-50/20 shadow-xs">
                  <p className="text-[10px] font-bold text-amber-800 uppercase">In Transit</p>
                  <h4 className="text-xl font-black text-amber-900 mt-1">{data.referrals.in_transit}</h4>
                </div>
                <div className="bg-white p-4 rounded-xl border border-purple-200 bg-purple-50/20 shadow-xs">
                  <p className="text-[10px] font-bold text-purple-800 uppercase">Under Treatment</p>
                  <h4 className="text-xl font-black text-purple-900 mt-1">{data.referrals.under_treatment}</h4>
                </div>
                <div className="bg-white p-4 rounded-xl border border-emerald-200 bg-emerald-50/20 shadow-xs">
                  <p className="text-[10px] font-bold text-emerald-800 uppercase">Completed</p>
                  <h4 className="text-xl font-black text-emerald-900 mt-1">{data.referrals.completed}</h4>
                </div>
              </div>

              {/* Referrals Table */}
              <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                      <Share2 className="w-4 h-4 text-emerald-600" />
                      Cross-Facility Referral Ledger
                    </h3>
                    <p className="text-xs text-slate-500">
                      Authoritative tracking of outgoing transfers and incoming specialist cases
                    </p>
                  </div>
                  <button
                    onClick={() => handleExportCSV('referrals', 'Referral Continuity Ledger')}
                    className="px-3 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 font-bold text-xs rounded-xl flex items-center gap-1.5 transition self-start sm:self-auto"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Export CSV</span>
                  </button>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase text-[10px]">
                        <th className="py-2.5 px-3">Referral ID</th>
                        <th className="py-2.5 px-3">Patient</th>
                        <th className="py-2.5 px-3">Source Facility</th>
                        <th className="py-2.5 px-3">Destination Facility</th>
                        <th className="py-2.5 px-3">Urgency</th>
                        <th className="py-2.5 px-3">Status</th>
                        <th className="py-2.5 px-3">Date</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {data.referrals.items.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="py-8 text-center text-slate-400">
                            No referrals logged in this reporting period.
                          </td>
                        </tr>
                      ) : (
                        data.referrals.items.map((ref) => (
                          <tr key={ref.referral_id} className="hover:bg-slate-50/80 transition">
                            <td className="py-2.5 px-3 font-mono font-bold text-slate-900">{ref.referral_id}</td>
                            <td className="py-2.5 px-3 font-semibold text-slate-900">{ref.patient_name}</td>
                            <td className="py-2.5 px-3 text-slate-600">{ref.source_facility}</td>
                            <td className="py-2.5 px-3 text-slate-600">{ref.destination_facility}</td>
                            <td className="py-2.5 px-3">
                              <span
                                className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase ${
                                  ref.urgency === 'EMERGENCY'
                                    ? 'bg-rose-100 text-rose-800'
                                    : ref.urgency === 'URGENT'
                                    ? 'bg-amber-100 text-amber-800'
                                    : 'bg-slate-100 text-slate-700'
                                }`}
                              >
                                {ref.urgency}
                              </span>
                            </td>
                            <td className="py-2.5 px-3">
                              <span
                                className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase ${
                                  ref.status === 'COMPLETED'
                                    ? 'bg-emerald-100 text-emerald-800'
                                    : ref.status === 'REJECTED'
                                    ? 'bg-rose-100 text-rose-800'
                                    : 'bg-blue-100 text-blue-800'
                                }`}
                              >
                                {ref.status.replace('_', ' ')}
                              </span>
                            </td>
                            <td className="py-2.5 px-3 text-slate-500 font-mono text-[11px]">{ref.date}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 7: NCD & CHRONIC CARE */}
          {activeTab === 'ncd' && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                  <p className="text-[10px] font-bold text-slate-500 uppercase">Total NCD Patients</p>
                  <h4 className="text-xl font-black text-slate-900 mt-1">{data.ncd.total_ncd_patients}</h4>
                </div>
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                  <p className="text-[10px] font-bold text-slate-500 uppercase">Screened In Period</p>
                  <h4 className="text-xl font-black text-slate-900 mt-1">{data.ncd.new_screenings_in_period}</h4>
                </div>
                <div className="bg-white p-4 rounded-xl border border-rose-200 bg-rose-50/20 shadow-xs">
                  <p className="text-[10px] font-bold text-rose-800 uppercase">High Risk Cases</p>
                  <h4 className="text-xl font-black text-rose-900 mt-1">{data.ncd.risk_levels.high}</h4>
                </div>
                <div className="bg-white p-4 rounded-xl border border-emerald-200 bg-emerald-50/20 shadow-xs">
                  <p className="text-[10px] font-bold text-emerald-800 uppercase">Controlled Status</p>
                  <h4 className="text-xl font-black text-emerald-900 mt-1">{data.ncd.control_status.controlled}</h4>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-3">
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 pb-2 border-b border-slate-100">
                    <Activity className="w-4 h-4 text-emerald-600" />
                    Hypertension Screening
                  </h3>
                  <div className="flex justify-between items-center py-2 text-xs border-b border-slate-100">
                    <span className="text-slate-600">Total Screened</span>
                    <span className="font-bold text-slate-900">{data.ncd.hypertension.screened}</span>
                  </div>
                  <div className="flex justify-between items-center py-2 text-xs">
                    <span className="text-slate-600">Confirmed Diagnosed</span>
                    <span className="font-bold text-rose-800">{data.ncd.hypertension.diagnosed}</span>
                  </div>
                </div>

                <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-3">
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 pb-2 border-b border-slate-100">
                    <Activity className="w-4 h-4 text-teal-600" />
                    Diabetes Mellitus Screening
                  </h3>
                  <div className="flex justify-between items-center py-2 text-xs border-b border-slate-100">
                    <span className="text-slate-600">Total Screened</span>
                    <span className="font-bold text-slate-900">{data.ncd.diabetes.screened}</span>
                  </div>
                  <div className="flex justify-between items-center py-2 text-xs">
                    <span className="text-slate-600">Confirmed Diagnosed</span>
                    <span className="font-bold text-teal-800">{data.ncd.diabetes.diagnosed}</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 8: MATERNAL & CHILD */}
          {activeTab === 'maternal' && data.maternal_child?.available && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-3">
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 pb-2 border-b border-slate-100">
                    <Baby className="w-4 h-4 text-rose-600" />
                    Maternal Health (ANC Care)
                  </h3>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between py-1.5 border-b border-slate-100">
                      <span className="text-slate-600">ANC Visits In Period</span>
                      <span className="font-bold text-slate-900">{data.maternal_child.maternal?.anc_visits || 0}</span>
                    </div>
                    <div className="flex justify-between py-1.5 border-b border-slate-100">
                      <span className="text-slate-600">Registered Mothers</span>
                      <span className="font-bold text-slate-900">{data.maternal_child.maternal?.total_registered_mothers || 0}</span>
                    </div>
                    <div className="flex justify-between py-1.5 border-b border-slate-100">
                      <span className="text-rose-700 font-medium">High Risk Cases Flagged</span>
                      <span className="font-bold text-rose-800">{data.maternal_child.maternal?.high_risk_cases || 0}</span>
                    </div>
                    <div className="flex justify-between py-1.5">
                      <span className="text-slate-600">IFA Tablets Issued</span>
                      <span className="font-bold text-emerald-700">{data.maternal_child.maternal?.ifa_tablets_issued || 0}</span>
                    </div>
                  </div>
                </div>

                <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-3">
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 pb-2 border-b border-slate-100">
                    <Baby className="w-4 h-4 text-blue-600" />
                    Child Health & Immunization
                  </h3>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between py-1.5 border-b border-slate-100">
                      <span className="text-slate-600">Total Children Enrolled</span>
                      <span className="font-bold text-slate-900">{data.maternal_child.child?.total_children || 0}</span>
                    </div>
                    <div className="flex justify-between py-1.5 border-b border-slate-100">
                      <span className="text-slate-600">Immunization Up-to-Date</span>
                      <span className="font-bold text-emerald-800">{data.maternal_child.child?.immunization_up_to_date || 0}</span>
                    </div>
                    <div className="flex justify-between py-1.5">
                      <span className="text-amber-700 font-medium">SAM / MAM Malnutrition Cases</span>
                      <span className="font-bold text-amber-800">{data.maternal_child.child?.sam_mam_cases || 0}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 9: ALERTS & OPERATIONAL */}
          {activeTab === 'alerts' && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                  <p className="text-[10px] font-bold text-slate-500 uppercase">Total Alerts</p>
                  <h4 className="text-xl font-black text-slate-900 mt-1">{data.alerts.total_alerts}</h4>
                </div>
                <div className="bg-white p-4 rounded-xl border border-rose-200 bg-rose-50/20 shadow-xs">
                  <p className="text-[10px] font-bold text-rose-800 uppercase">New Alerts</p>
                  <h4 className="text-xl font-black text-rose-900 mt-1">{data.alerts.new}</h4>
                </div>
                <div className="bg-white p-4 rounded-xl border border-amber-200 bg-amber-50/20 shadow-xs">
                  <p className="text-[10px] font-bold text-amber-800 uppercase">Acknowledged</p>
                  <h4 className="text-xl font-black text-amber-900 mt-1">{data.alerts.acknowledged}</h4>
                </div>
                <div className="bg-white p-4 rounded-xl border border-emerald-200 bg-emerald-50/20 shadow-xs">
                  <p className="text-[10px] font-bold text-emerald-800 uppercase">Resolved</p>
                  <h4 className="text-xl font-black text-emerald-900 mt-1">{data.alerts.resolved}</h4>
                </div>
              </div>

              <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 pb-3 border-b border-slate-100">
                  <AlertTriangle className="w-4 h-4 text-emerald-600" />
                  Alerts By Operational Category
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
                  {Object.entries(data.alerts.categories).map(([cat, stats]) => (
                    <div key={cat} className="p-3.5 rounded-xl border border-slate-200 bg-slate-50">
                      <p className="text-xs font-black text-slate-900 uppercase tracking-wider">{cat}</p>
                      <div className="mt-2 space-y-1 text-xs">
                        <div className="flex justify-between text-slate-600">
                          <span>Total:</span>
                          <span className="font-bold text-slate-900">{stats.total}</span>
                        </div>
                        <div className="flex justify-between text-rose-700">
                          <span>New:</span>
                          <span className="font-bold">{stats.new}</span>
                        </div>
                        <div className="flex justify-between text-emerald-700">
                          <span>Resolved:</span>
                          <span className="font-bold">{stats.resolved}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 10: QUICK CSV EXPORTS */}
          {activeTab === 'exports' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-base font-bold text-slate-900">Authoritative CSV Dataset Exports</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Download structured comma-separated files respecting assigned facility scope and active period ({period.toUpperCase()}).
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[
                  { id: 'opd', title: 'OPD Footfall & Visit Ledger', desc: 'Visit IDs, patient demographics, arrival timestamps, triage stage, and clinical priority' },
                  { id: 'stock_consumption', title: 'Pharmacy Stock Consumption & Movement', desc: 'Reconciled opening stock, purchase receipts, FEFO dispensed units, audit adjustments, and closing stock' },
                  { id: 'expiry', title: 'Batch Expiry Surveillance Ledger', desc: 'Active batches expiring within 90 days, days remaining, and expired stock flags' },
                  { id: 'low_stock', title: 'Low Stock & Out of Stock Audit', desc: 'Medicine master threshold audit matching Pharmacy Dashboard low-stock rules' },
                  { id: 'procurement', title: 'Purchase Orders & Spend Ledger', desc: 'Purchase orders, vendor information, approval statuses, and procurement amounts' },
                  { id: 'doctor_activity', title: 'Doctor Clinical Activity Report', desc: 'Doctor consultations completed, patient counts, lab orders, prescriptions, and referrals' },
                  { id: 'laboratory', title: 'Laboratory Diagnostics Register', desc: 'Lab orders, test master codes, sample collection status, and verified release timestamps' },
                  { id: 'referrals', title: 'Cross-Facility Referral Continuity Ledger', desc: 'Source and destination facilities, clinical urgency, response findings, and completion status' },
                  { id: 'ncd', title: 'NCD Screening & Control Register', desc: 'Hypertension and diabetes screening outcomes, BP/glucose records, and risk categorization' },
                  { id: 'patients', title: 'Patient Master Directory Export', desc: 'Registered patients, ABHA ID status, contact mobile, and registration facility' },
                ].map((r) => (
                  <div
                    key={r.id}
                    className="p-5 rounded-2xl border border-slate-200 bg-white flex flex-col justify-between space-y-4 shadow-xs hover:border-emerald-300 transition"
                  >
                    <div>
                      <h4 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                        <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
                        {r.title}
                      </h4>
                      <p className="text-xs text-slate-500 mt-1">{r.desc}</p>
                    </div>

                    <button
                      onClick={() => handleExportCSV(r.id, r.title)}
                      className="w-full py-2.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 font-bold text-xs rounded-xl flex items-center justify-center gap-2 transition"
                    >
                      <Download className="w-4 h-4 text-emerald-700" />
                      <span>Export CSV ({period.toUpperCase()})</span>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
};
