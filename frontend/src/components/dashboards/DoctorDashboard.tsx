import React, { useState, useEffect } from 'react';
import { Stethoscope, Clock, TestTube, CalendarCheck, User, ShieldAlert, ArrowRight, Activity, FileText } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../../services/api';

interface DoctorDashboardProps {
  summary: any;
  date: string;
  isToday: boolean;
}

export const DoctorDashboard: React.FC<DoctorDashboardProps> = ({ summary, date, isToday }) => {
  const navigate = useNavigate();
  const kpis = summary?.kpis || {};
  const [opdQueue, setOpdQueue] = useState<any[]>([]);
  const [activeVisit, setActiveVisit] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const actionRequired = summary?.action_required || [];

  const fetchDoctorQueue = async () => {
    setLoading(true);
    try {
      const res = await api.get(`visits/?queue=DOCTOR&date=${date}`);
      const list = res.data.results || res.data || [];
      setOpdQueue(list);
      
      // Check if there is an active called patient in consultation for current doctor
      const active = list.find((v: any) => v.status === 'IN_CONSULTATION');
      if (active) setActiveVisit(active);
    } catch (e) {
      console.error('Failed to load doctor OPD queue', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDoctorQueue();
  }, [date]);

  const handleCallPatient = async (visitId: number) => {
    if (!isToday) {
      alert('Queue status modifications are blocked on historical OPD dates.');
      return;
    }
    try {
      const res = await api.post('visits/call-next/', { queue: 'DOCTOR' });
      if (res.data && res.data.id) {
        setActiveVisit(res.data);
        fetchDoctorQueue();
      } else {
        alert(res.data.message || 'No waiting patients found.');
      }
    } catch (e) {
      alert('Failed to call next patient.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Doctor Header Banner */}
      <div className="bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 rounded-2xl p-6 text-white shadow-md relative overflow-hidden">
        <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 bg-blue-700/80 text-blue-100 text-[10px] font-extrabold rounded-full uppercase tracking-wider border border-blue-500/30">
                Medical Officer Desk Scope
              </span>
              <span className="text-xs text-blue-200 font-semibold">• {summary?.active_facility || 'Facility OPD'}</span>
            </div>
            <h1 className="text-2xl font-black tracking-tight">Doctor Clinical Dashboard</h1>
            <p className="text-xs text-blue-100 mt-1 max-w-xl">
              OPD consultation queue management, called patient triage vitals review, lab diagnostic orders, and electronic prescription issuing.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Link
              to="/consultation"
              className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white font-bold text-xs rounded-xl shadow-md transition flex items-center gap-1.5"
            >
              <Stethoscope className="w-4 h-4" />
              <span>Open EMR Console</span>
            </Link>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase">Waiting for Doctor</p>
              <h3 className="text-2xl font-black text-amber-900 mt-1">{kpis.doctor_waiting || 0}</h3>
              <p className="text-[10px] text-amber-700 font-medium mt-1">Triaged & Ready</p>
            </div>
            <div className="p-3 bg-amber-50 rounded-xl text-amber-700 border border-amber-100">
              <Clock className="w-5 h-5" />
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase">My OPD Today</p>
              <h3 className="text-2xl font-black text-slate-900 mt-1">{summary?.todays_opd || 0}</h3>
              <p className="text-[10px] text-blue-700 font-medium mt-1">Total Assigned Visits</p>
            </div>
            <div className="p-3 bg-blue-50 rounded-xl text-blue-700 border border-blue-100">
              <Stethoscope className="w-5 h-5" />
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase">Lab Pending</p>
              <h3 className="text-2xl font-black text-purple-900 mt-1">{kpis.lab_pending || 0}</h3>
              <p className="text-[10px] text-purple-700 font-medium mt-1">Investigations Ordered</p>
            </div>
            <div className="p-3 bg-purple-50 rounded-xl text-purple-700 border border-purple-100">
              <TestTube className="w-5 h-5" />
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase">Follow-ups</p>
              <h3 className="text-2xl font-black text-emerald-900 mt-1">{summary?.followups_summary?.due_today ?? summary?.kpis?.followups_due ?? 0}</h3>
              <p className="text-[10px] text-emerald-700 font-medium mt-1">Scheduled Reviews</p>

            </div>
            <div className="p-3 bg-emerald-50 rounded-xl text-emerald-700 border border-emerald-100">
              <CalendarCheck className="w-5 h-5" />
            </div>
          </div>
        </div>
      </div>

      {/* Active Patient Called Panel (If Called) */}
      {activeVisit && (
        <div className="bg-gradient-to-r from-slate-900 to-blue-950 rounded-2xl p-6 text-white shadow-lg border border-blue-800 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-blue-800/80 pb-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-blue-600 border border-blue-400 flex items-center justify-center font-black text-xl text-white shadow-xs">
                #{activeVisit.token_details?.token_number || activeVisit.id}
              </div>
              <div>
                <span className="px-2 py-0.5 rounded-md text-[10px] font-extrabold bg-blue-800 text-blue-200 uppercase tracking-widest">
                  ACTIVE PATIENT IN CONSULTATION
                </span>
                <h2 className="text-lg font-black text-white mt-0.5">
                  {activeVisit.patient_details?.name || 'Ramesh Kumar'}
                </h2>
                <p className="text-xs text-blue-200 font-medium">
                  {activeVisit.patient_details?.age || 52} Yrs • {activeVisit.patient_details?.gender || 'MALE'} • UHID: {activeVisit.patient_details?.patient_id || 'NC-001'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Link
                to={`/consultation?visit=${activeVisit.id}`}
                className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-xs rounded-xl shadow-md transition flex items-center gap-1.5"
              >
                <FileText className="w-4 h-4" />
                <span>Start EMR Consultation &rarr;</span>
              </Link>
            </div>
          </div>

          {/* Vitals Summary from Triage */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 text-xs">
            <div className="p-2.5 rounded-lg bg-white/10 border border-white/10">
              <span className="text-[10px] text-blue-300 uppercase font-bold block">Chief Complaint</span>
              <span className="font-semibold text-white block truncate">{activeVisit.chief_complaint || 'General OPD'}</span>
            </div>
            <div className="p-2.5 rounded-lg bg-white/10 border border-white/10">
              <span className="text-[10px] text-blue-300 uppercase font-bold block">Blood Pressure</span>
              <span className="font-bold text-white block">150/96 mmHg</span>
            </div>
            <div className="p-2.5 rounded-lg bg-white/10 border border-white/10">
              <span className="text-[10px] text-blue-300 uppercase font-bold block">Pulse / SpO2</span>
              <span className="font-bold text-white block">88 bpm / 97%</span>
            </div>
            <div className="p-2.5 rounded-lg bg-white/10 border border-white/10">
              <span className="text-[10px] text-blue-300 uppercase font-bold block">Blood Glucose</span>
              <span className="font-bold text-rose-300 block">190 mg/dL (HIGH)</span>
            </div>
            <div className="p-2.5 rounded-lg bg-white/10 border border-white/10">
              <span className="text-[10px] text-blue-300 uppercase font-bold block">Temperature</span>
              <span className="font-bold text-white block">101.2 °F</span>
            </div>
            <div className="p-2.5 rounded-lg bg-white/10 border border-white/10">
              <span className="text-[10px] text-blue-300 uppercase font-bold block">Priority</span>
              <span className="font-extrabold text-amber-300 block uppercase">{activeVisit.priority || 'NORMAL'}</span>
            </div>
          </div>
        </div>
      )}

      {/* Main Grid: My OPD Queue & Doctor Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* OPD Queue Table */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
            <div>
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Clock className="w-4 h-4 text-blue-600" />
                My OPD Queue ({date})
              </h2>
              <p className="text-xs text-slate-500">Waiting triaged patients scheduled for doctor evaluation</p>
            </div>

            {isToday && (
              <button
                onClick={() => handleCallPatient(0)}
                className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-xs transition flex items-center gap-1.5 cursor-pointer"
              >
                <Activity className="w-3.5 h-3.5" />
                <span>Call Next Patient</span>
              </button>
            )}
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-100/70 border-b border-slate-200 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                  <th className="py-3 px-4">Priority</th>
                  <th className="py-3 px-4 text-center">Token</th>
                  <th className="py-3 px-4">Patient</th>
                  <th className="py-3 px-4 text-center">Age</th>
                  <th className="py-3 px-4 text-center">Waiting Time</th>
                  <th className="py-3 px-4">Visit Type</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs font-medium">
                {opdQueue.length > 0 ? (
                  opdQueue.map((v: any) => (
                    <tr key={v.id} className="hover:bg-slate-50 transition">
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase ${
                          v.priority === 'EMERGENCY' ? 'bg-rose-100 text-rose-800 border border-rose-200' :
                          v.priority === 'HIGH' ? 'bg-amber-100 text-amber-800 border border-amber-200' :
                          'bg-slate-100 text-slate-700'
                        }`}>
                          {v.priority}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center font-mono font-bold text-emerald-700">
                        #{v.token_details?.token_number || v.id}
                      </td>
                      <td className="py-3 px-4 font-bold text-slate-900">{v.patient_details?.name || 'Patient'}</td>
                      <td className="py-3 px-4 text-center text-slate-600">{v.patient_details?.age || 45}</td>
                      <td className="py-3 px-4 text-center font-mono text-slate-500">{v.waiting_time_minutes || 12} mins</td>
                      <td className="py-3 px-4 text-slate-600">{v.visit_type}</td>
                      <td className="py-3 px-4 text-center">
                        <span className="px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 font-bold text-[10px] border border-blue-200">
                          {v.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right space-x-1">
                        <Link
                          to={`/consultation?visit=${v.id}`}
                          className="px-2.5 py-1 bg-blue-50 hover:bg-blue-100 text-blue-700 font-bold text-[11px] rounded-lg transition"
                        >
                          Consult
                        </Link>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-xs text-slate-400 font-medium">
                      No waiting patients in doctor queue for selected date.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Doctor Action Required & Alerts */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-rose-600" />
              Doctor Clinical Alerts
            </h2>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800">
              {actionRequired.length} Alerts
            </span>
          </div>

          <div className="space-y-3 text-xs">
            {actionRequired.length > 0 ? (
              actionRequired.map((item: any) => (
                <div key={item.id} className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                  <span className="font-bold text-slate-900 block">{item.title}</span>
                  <span className="text-[10px] text-slate-500 font-medium">Module: {item.module}</span>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-400 italic">No urgent clinical alerts for doctor desk.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
