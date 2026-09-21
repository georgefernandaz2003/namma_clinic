import React, { useState, useEffect } from 'react';
import { Stethoscope, Clock, Users, ArrowRight, Activity } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../../services/api';

interface NurseDashboardProps {
  summary: any;
  date: string;
  isToday: boolean;
}

export const NurseDashboard: React.FC<NurseDashboardProps> = ({ summary, date }) => {
  const navigate = useNavigate();
  const kpis = summary?.kpis || {};
  const [triageQueue, setTriageQueue] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchTriageQueue = async () => {
    setLoading(true);
    try {
      const res = await api.get(`visits/?queue=TRIAGE&date=${date}`);
      const list = res.data.results || res.data || [];
      setTriageQueue(list);
    } catch (e) {
      console.error('Failed to load triage queue', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTriageQueue();
  }, [date]);

  return (
    <div className="space-y-6">
      {/* Nurse Banner */}
      <div className="bg-gradient-to-r from-emerald-900 via-teal-900 to-slate-900 rounded-2xl p-6 text-white shadow-md relative overflow-hidden">
        <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 bg-emerald-700/80 text-emerald-100 text-[10px] font-extrabold rounded-full uppercase tracking-wider border border-emerald-500/30">
                Nursing Station Scope
              </span>
              <span className="text-xs text-emerald-200 font-semibold">• {summary?.active_facility || 'Facility Clinic'}</span>
            </div>
            <h1 className="text-2xl font-black tracking-tight">Staff Nurse Triage & Vitals Desk</h1>
            <p className="text-xs text-emerald-100 mt-1 max-w-xl">
              Patient queue monitoring, comprehensive physiological vitals screening (BP, Pulse, SpO2, Temperature, Blood Glucose), and clinical triage routing.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Link
              to="/triage"
              className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-xs rounded-xl shadow-md transition flex items-center gap-1.5"
            >
              <Stethoscope className="w-4 h-4" />
              <span>Full Triage Desk</span>
            </Link>
          </div>
        </div>
      </div>

      {/* 5 KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <p className="text-[11px] font-bold text-slate-500 uppercase">Triage Waiting</p>
          <h3 className="text-xl font-black text-amber-900 mt-1">{kpis.triage_waiting || 0}</h3>
          <p className="text-[10px] text-amber-700 font-medium mt-0.5">Awaiting Screening</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-blue-200 bg-blue-50/30 shadow-xs">
          <p className="text-[11px] font-bold text-blue-800 uppercase">In Triage</p>
          <h3 className="text-xl font-black text-blue-900 mt-1">{kpis.in_triage || 0}</h3>
          <p className="text-[10px] text-blue-700 font-medium mt-0.5">Being Screened</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-purple-200 bg-purple-50/30 shadow-xs">
          <p className="text-[11px] font-bold text-purple-800 uppercase flex items-center gap-1.5">
            <Users className="w-3.5 h-3.5 text-purple-600" />
            Total Patients Today
          </p>
          <h3 className="text-xl font-black text-purple-900 mt-1">{summary?.todays_opd || 0}</h3>
          <p className="text-[10px] text-purple-700 font-medium mt-0.5">Today's OPD Count</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-emerald-200 bg-emerald-50/30 shadow-xs">
          <p className="text-[11px] font-bold text-emerald-800 uppercase">Registered Today</p>
          <h3 className="text-xl font-black text-emerald-900 mt-1">{summary?.registered_today || 0}</h3>
          <p className="text-[10px] text-emerald-700 font-medium mt-0.5">New Patient Intake</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-rose-200 bg-rose-50/30 shadow-xs">
          <p className="text-[11px] font-bold text-rose-800 uppercase">Emergency</p>
          <h3 className="text-xl font-black text-rose-900 mt-1">0</h3>
          <p className="text-[10px] text-rose-700 font-medium mt-0.5">Priority Red Flags</p>
        </div>
      </div>

      {/* Full-Width Triage Queue Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div>
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Clock className="w-4 h-4 text-emerald-600" />
              Triage Queue ({date})
            </h2>
            <p className="text-xs text-slate-500">Patients awaiting nurse physical screening and vitals documentation</p>
          </div>
          <button
            onClick={fetchTriageQueue}
            disabled={loading}
            className="px-3 py-1 bg-white border border-slate-300 text-slate-700 text-xs font-bold rounded-lg hover:bg-slate-100 transition disabled:opacity-50"
          >
            {loading ? 'Refreshing...' : 'Refresh Queue'}
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-100/70 border-b border-slate-200 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                <th className="py-3.5 px-4">Priority</th>
                <th className="py-3.5 px-4 text-center">Token</th>
                <th className="py-3.5 px-4">Patient Name</th>
                <th className="py-3.5 px-4 text-center">Age / Gender</th>
                <th className="py-3.5 px-4">Chief Complaint</th>
                <th className="py-3.5 px-4 text-center">Arrival</th>
                <th className="py-3.5 px-4 text-center">Status</th>
                <th className="py-3.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs font-medium">
              {triageQueue.length > 0 ? (
                triageQueue.map((v: any) => (
                  <tr key={v.id} className="hover:bg-slate-50 transition">
                    <td className="py-3.5 px-4">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase ${
                        v.priority === 'EMERGENCY'
                          ? 'bg-rose-100 text-rose-800'
                          : v.priority === 'URGENT'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-slate-100 text-slate-700'
                      }`}>
                        {v.priority}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-center font-mono font-bold text-emerald-700">
                      #{v.token_details?.token_number || v.token_number || v.id}
                    </td>
                    <td className="py-3.5 px-4">
                      <p className="font-bold text-slate-900">{v.patient_details?.name || v.patient_name || 'Patient'}</p>
                      <p className="text-[11px] text-slate-400">{v.patient_details?.mobile || v.patient_mobile || 'No contact'}</p>
                    </td>
                    <td className="py-3.5 px-4 text-center text-slate-600">
                      {v.patient_details?.age || 45} Y / {v.patient_details?.gender || 'M'}
                    </td>
                    <td className="py-3.5 px-4 text-slate-700 max-w-xs truncate">
                      {v.chief_complaint || 'Routine General OPD Checkup'}
                    </td>
                    <td className="py-3.5 px-4 text-center text-slate-500">
                      {v.waiting_time_minutes || 5}m ago
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <span className="px-2.5 py-0.5 rounded-md bg-amber-50 text-amber-700 font-bold text-[10px] border border-amber-200">
                        {v.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => navigate('/triage', { state: { visitId: v.id } })}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-xs transition cursor-pointer"
                      >
                        <Stethoscope className="w-3.5 h-3.5" />
                        <span>Start Triage</span>
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-xs text-slate-400 font-medium">
                    <Activity className="w-6 h-6 text-slate-300 mx-auto mb-2" />
                    No patients waiting for triage on selected date.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
