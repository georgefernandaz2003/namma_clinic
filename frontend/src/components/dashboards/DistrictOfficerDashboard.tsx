import React from 'react';
import { Building2, Users, Activity, Share2, ShieldAlert, ArrowUpRight } from 'lucide-react';
import { Link } from 'react-router-dom';

interface DistrictOfficerDashboardProps {
  summary: any;
}

export const DistrictOfficerDashboard: React.FC<DistrictOfficerDashboardProps> = ({ summary }) => {
  const facilityOverview = summary?.facility_overview || [];
  const actionRequired = summary?.action_required || [];

  return (
    <div className="space-y-6">
      {/* Scope Banner */}
      <div className="bg-gradient-to-r from-emerald-800 to-teal-900 rounded-2xl p-6 text-white shadow-md relative overflow-hidden">
        <div className="absolute right-0 top-0 translate-x-4 -translate-y-4 w-64 h-64 bg-white/5 rounded-full blur-2xl pointer-events-none" />
        <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 bg-emerald-700/80 text-emerald-100 text-[10px] font-extrabold rounded-full uppercase tracking-wider border border-emerald-500/30">
                District Health Office Scope
              </span>
              <span className="text-xs text-emerald-200 font-semibold">• Full District Monitoring Access</span>
            </div>
            <h1 className="text-2xl font-black tracking-tight">District Executive Overview</h1>
            <p className="text-xs text-emerald-100 mt-1 max-w-xl">
              Monitoring operational health, patient inflow, cross-facility referrals, and facility statuses across all direct healthcare facilities in Central District.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              to="/reports"
              className="px-4 py-2 bg-white text-emerald-950 font-bold text-xs rounded-xl shadow-md hover:bg-emerald-50 transition flex items-center gap-1.5"
            >
              <span>View District Reports</span>
              <ArrowUpRight className="w-4 h-4 text-emerald-700" />
            </Link>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Patients</p>
              <h3 className="text-2xl font-black text-slate-900 mt-1">{summary?.total_patients?.toLocaleString() || 0}</h3>
              <p className="text-[10px] text-emerald-700 font-semibold mt-1">District Registered Citizens</p>
            </div>
            <div className="p-3 bg-emerald-50 rounded-xl text-emerald-700 border border-emerald-100">
              <Users className="w-5 h-5" />
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">OPD Patients Today</p>
              <h3 className="text-2xl font-black text-slate-900 mt-1">{summary?.todays_opd?.toLocaleString() || 0}</h3>
              <p className="text-[10px] text-blue-700 font-semibold mt-1">Date OPD Footfall</p>
            </div>
            <div className="p-3 bg-blue-50 rounded-xl text-blue-700 border border-blue-100">
              <Activity className="w-5 h-5" />
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Pending Referrals</p>
              <h3 className="text-2xl font-black text-rose-900 mt-1">{summary?.referrals_summary?.pending || 0}</h3>
              <p className="text-[10px] text-rose-700 font-semibold mt-1">Cross-Facility Transfer</p>
            </div>
            <div className="p-3 bg-rose-50 rounded-xl text-rose-700 border border-rose-100">
              <Share2 className="w-5 h-5" />
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Facilities</p>
              <h3 className="text-2xl font-black text-slate-900 mt-1">{summary?.total_facilities ?? 0}</h3>
              <p className="text-[10px] text-teal-700 font-semibold mt-1">Active Healthcare Nodes</p>
            </div>
            <div className="p-3 bg-teal-50 rounded-xl text-teal-700 border border-teal-100">
              <Building2 className="w-5 h-5" />
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: Facility Operation Overview & Action Required */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Facility Operation Overview Table */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
            <div>
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Building2 className="w-4 h-4 text-emerald-600" />
                Facility Operation Overview
              </h2>
              <p className="text-xs text-slate-500">Live operational status across district hospitals & village clinics</p>
            </div>
            <Link to="/facilities" className="text-xs font-bold text-emerald-700 hover:text-emerald-800">
              View All Master Facilities &rarr;
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-100/70 border-b border-slate-200 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                  <th className="py-3 px-4">Facility</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4 text-center">Patients</th>
                  <th className="py-3 px-4 text-center">Waiting Queue</th>
                  <th className="py-3 px-4 text-center">Active Referrals</th>
                  <th className="py-3 px-4 text-right">Operational Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs font-medium">
                {facilityOverview.map((fac: any) => {
                  let badgeClass = 'bg-emerald-50 text-emerald-800 border-emerald-200';
                  if (fac.status === 'Attention Required') badgeClass = 'bg-rose-50 text-rose-800 border-rose-200';
                  else if (fac.status === 'Busy') badgeClass = 'bg-amber-50 text-amber-800 border-amber-200';

                  return (
                    <tr key={fac.id} className="hover:bg-slate-50 transition">
                      <td className="py-3.5 px-4 font-bold text-slate-900">{fac.name}</td>
                      <td className="py-3.5 px-4 text-slate-600 text-[11px]">{fac.type}</td>
                      <td className="py-3.5 px-4 text-center font-semibold text-slate-800">{fac.patients}</td>
                      <td className="py-3.5 px-4 text-center">
                        <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 font-bold">
                          {fac.waiting}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-center font-semibold text-rose-700">{fac.referrals}</td>
                      <td className="py-3.5 px-4 text-right">
                        <span className={`px-2.5 py-1 rounded-full text-[10px] font-extrabold border ${badgeClass}`}>
                          {fac.status}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* District Action Required & Alerts */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-rose-600" />
              Action Required
            </h2>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800">
              {actionRequired.length} Items
            </span>
          </div>

          <p className="text-xs text-slate-500">
            High-priority operational alerts and pending tasks requiring district supervisory attention:
          </p>

          <div className="space-y-3">
            {actionRequired.length > 0 ? (
              actionRequired.map((item: any) => (
                <div key={item.id} className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900">{item.title}</span>
                    <span className={`text-[9px] font-extrabold px-2 py-0.5 rounded-full uppercase ${
                      item.severity === 'HIGH' ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'
                    }`}>
                      {item.severity}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 font-medium">Module: {item.module}</p>
                </div>
              ))
            ) : (
              <div className="p-4 text-center text-xs text-slate-400 font-medium border border-dashed border-slate-200 rounded-xl">
                No active critical alerts for the selected parameters.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
