import React from 'react';
import { Users, Clock, Stethoscope, TestTube, Pill, CheckCircle2, ShieldAlert, ArrowRight, UserCheck, Package, Share2 } from 'lucide-react';
import { Link } from 'react-router-dom';

interface HospitalAdminDashboardProps {
  summary: any;
}

export const HospitalAdminDashboard: React.FC<HospitalAdminDashboardProps> = ({ summary }) => {
  const kpis = summary?.kpis || {};
  const stageFlow = summary?.opd_stage_flow || {};
  const staff = summary?.staff_status || {};
  const inventory = summary?.inventory_summary || {};
  const referrals = summary?.referrals_summary || {};
  const actionRequired = summary?.action_required || [];

  return (
    <div className="space-y-6">
      {/* Scope Header */}
      <div className="bg-gradient-to-r from-teal-800 to-emerald-900 rounded-2xl p-6 text-white shadow-md relative overflow-hidden">
        <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 bg-teal-700/80 text-teal-100 text-[10px] font-extrabold rounded-full uppercase tracking-wider border border-teal-500/30">
                Hospital Administration Scope
              </span>
              <span className="text-xs text-teal-200 font-semibold">• {summary?.active_facility || 'Assigned Facility'}</span>
            </div>
            <h1 className="text-2xl font-black tracking-tight">{summary?.active_facility || 'Facility Executive Dashboard'}</h1>
            <p className="text-xs text-teal-100 mt-1 max-w-xl">
              Facility-level operational management, stage-wise OPD queue flow, clinical staffing availability, and stock inventory monitoring.
            </p>
          </div>
        </div>
      </div>

      {/* 6 Primary KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <p className="text-[11px] font-bold text-slate-500 uppercase">Patients Today</p>
          <h3 className="text-xl font-black text-slate-900 mt-1">{summary?.todays_opd || 0}</h3>
          <p className="text-[10px] text-emerald-700 font-medium mt-0.5">Facility Footfall</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-amber-200 bg-amber-50/30 shadow-xs">
          <p className="text-[11px] font-bold text-amber-800 uppercase">OPD Waiting</p>
          <h3 className="text-xl font-black text-amber-900 mt-1">{(kpis.triage_waiting || 0) + (kpis.doctor_waiting || 0)}</h3>
          <p className="text-[10px] text-amber-700 font-medium mt-0.5">Triage & Doctor Queue</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-blue-200 bg-blue-50/30 shadow-xs">
          <p className="text-[11px] font-bold text-blue-800 uppercase">In Consultation</p>
          <h3 className="text-xl font-black text-blue-900 mt-1">{kpis.in_consultation || 0}</h3>
          <p className="text-[10px] text-blue-700 font-medium mt-0.5">Active Doctor Desk</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-purple-200 bg-purple-50/30 shadow-xs">
          <p className="text-[11px] font-bold text-purple-800 uppercase">Lab Pending</p>
          <h3 className="text-xl font-black text-purple-900 mt-1">{kpis.lab_pending || 0}</h3>
          <p className="text-[10px] text-purple-700 font-medium mt-0.5">Sample & Results</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-orange-200 bg-orange-50/30 shadow-xs">
          <p className="text-[11px] font-bold text-orange-800 uppercase">Pharmacy Queue</p>
          <h3 className="text-xl font-black text-orange-900 mt-1">{kpis.pharmacy_waiting || 0}</h3>
          <p className="text-[10px] text-orange-700 font-medium mt-0.5">FEFO Dispense Waiting</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-emerald-200 bg-emerald-50/30 shadow-xs">
          <p className="text-[11px] font-bold text-emerald-800 uppercase">Completed</p>
          <h3 className="text-xl font-black text-emerald-900 mt-1">{kpis.completed || 0}</h3>
          <p className="text-[10px] text-emerald-700 font-medium mt-0.5">Discharged Today</p>
        </div>
      </div>

      {/* OPD Flow Diagram */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Clock className="w-4 h-4 text-emerald-600" />
              OPD Patient Flow Architecture
            </h2>
            <p className="text-xs text-slate-500">Sequential stage-by-stage patient count progression for selected date</p>
          </div>
          <Link to="/queue" className="text-xs font-bold text-emerald-700 hover:text-emerald-800">
            Open OPD Queue &rarr;
          </Link>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 items-center">
          {[
            { label: 'Registration', count: stageFlow.registration || 0, icon: <Users className="w-4 h-4 text-emerald-600" /> },
            { label: 'Triage', count: stageFlow.triage || 0, icon: <Stethoscope className="w-4 h-4 text-amber-600" /> },
            { label: 'Doctor', count: stageFlow.doctor || 0, icon: <Clock className="w-4 h-4 text-blue-600" /> },
            { label: 'Lab', count: stageFlow.lab || 0, icon: <TestTube className="w-4 h-4 text-purple-600" /> },
            { label: 'Pharmacy', count: stageFlow.pharmacy || 0, icon: <Pill className="w-4 h-4 text-orange-600" /> },
            { label: 'Completed', count: stageFlow.completed || 0, icon: <CheckCircle2 className="w-4 h-4 text-emerald-600" /> }
          ].map((stg, i) => (
            <div key={i} className="flex items-center gap-2">
              <div className="flex-1 p-3 rounded-xl bg-slate-50 border border-slate-200 flex flex-col items-center text-center">
                <div className="p-1.5 rounded-lg bg-white border border-slate-200 mb-1">{stg.icon}</div>
                <span className="text-[10px] font-bold text-slate-500 uppercase">{stg.label}</span>
                <span className="text-lg font-black text-slate-900 mt-0.5">{stg.count}</span>
              </div>
              {i < 5 && <ArrowRight className="w-4 h-4 text-slate-300 hidden lg:block shrink-0" />}
            </div>
          ))}
        </div>
      </div>

      {/* Grid: Staff Status, Inventory Summary & Referrals */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Staff Status */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <UserCheck className="w-4 h-4 text-teal-600" />
              Staff Status
            </h2>
            <span className="text-xs font-bold text-slate-500">Active / Total</span>
          </div>

          <div className="space-y-3 divide-y divide-slate-100 text-xs font-medium">
            <div className="pt-2 flex justify-between items-center">
              <span className="text-slate-700 font-bold">Medical Officers / Doctors</span>
              <span className="px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-800 font-extrabold border border-emerald-200">
                {staff.doctors?.active || 0} / {staff.doctors?.total || 0} Active
              </span>
            </div>
            <div className="pt-2 flex justify-between items-center">
              <span className="text-slate-700 font-bold">Staff Nurses</span>
              <span className="px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-800 font-extrabold border border-emerald-200">
                {staff.nurses?.active || 0} / {staff.nurses?.total || 0} Active
              </span>
            </div>
            <div className="pt-2 flex justify-between items-center">
              <span className="text-slate-700 font-bold">Lab Technicians</span>
              <span className="px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-800 font-extrabold border border-emerald-200">
                {staff.lab_technicians?.active || 0} / {staff.lab_technicians?.total || 0} Active
              </span>
            </div>
            <div className="pt-2 flex justify-between items-center">
              <span className="text-slate-700 font-bold">Pharmacists</span>
              <span className="px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-800 font-extrabold border border-emerald-200">
                {staff.pharmacists?.active || 0} / {staff.pharmacists?.total || 0} Active
              </span>
            </div>
          </div>
        </div>

        {/* Inventory Summary */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Package className="w-4 h-4 text-amber-600" />
              Inventory Summary
            </h2>
            <Link to="/pharmacy" className="text-xs font-bold text-amber-700 hover:text-amber-800">
              Manage &rarr;
            </Link>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-[10px] font-bold text-slate-500 uppercase">Total Medicines</span>
              <p className="text-lg font-black text-slate-900 mt-1">{inventory.total_medicines ?? 0}</p>
            </div>
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl">
              <span className="text-[10px] font-bold text-amber-800 uppercase">Low Stock</span>
              <p className="text-lg font-black text-amber-900 mt-1">{inventory.low_stock || 0}</p>
            </div>
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl">
              <span className="text-[10px] font-bold text-rose-800 uppercase">Out of Stock</span>
              <p className="text-lg font-black text-rose-900 mt-1">{inventory.out_of_stock || 0}</p>
            </div>
            <div className="p-3 bg-orange-50 border border-orange-200 rounded-xl">
              <span className="text-[10px] font-bold text-orange-800 uppercase">Expiring Soon</span>
              <p className="text-lg font-black text-orange-900 mt-1">{inventory.expiring_soon || 0}</p>
            </div>
          </div>
        </div>

        {/* Referrals & Action Required */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Share2 className="w-4 h-4 text-rose-600" />
              Referral Status
            </h2>
            <Link to="/referrals" className="text-xs font-bold text-rose-700 hover:text-rose-800">
              Network &rarr;
            </Link>
          </div>

          <div className="grid grid-cols-3 gap-2 text-center text-xs">
            <div className="p-2.5 bg-rose-50 border border-rose-200 rounded-xl">
              <span className="text-[10px] font-bold text-rose-800 uppercase">Pending</span>
              <p className="text-base font-black text-rose-900 mt-0.5">{referrals.pending || 0}</p>
            </div>
            <div className="p-2.5 bg-blue-50 border border-blue-200 rounded-xl">
              <span className="text-[10px] font-bold text-blue-800 uppercase">Accepted</span>
              <p className="text-base font-black text-blue-900 mt-0.5">{referrals.accepted || 0}</p>
            </div>
            <div className="p-2.5 bg-emerald-50 border border-emerald-200 rounded-xl">
              <span className="text-[10px] font-bold text-emerald-800 uppercase">Completed</span>
              <p className="text-base font-black text-emerald-900 mt-0.5">{referrals.completed || 0}</p>
            </div>
          </div>

          {/* Action Required */}
          <div className="pt-2 border-t border-slate-100 space-y-2">
            <h3 className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
              Facility Action Required
            </h3>
            {actionRequired.length > 0 ? (
              actionRequired.map((item: any) => (
                <div key={item.id} className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs">
                  <p className="font-bold text-slate-900">{item.title}</p>
                </div>
              ))
            ) : (
              <p className="text-[11px] text-slate-400 italic">No facility action items pending.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
