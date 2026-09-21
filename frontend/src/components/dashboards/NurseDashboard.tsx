import React, { useState, useEffect } from 'react';
import { Stethoscope, Clock, ShieldAlert, Heart, Activity, Thermometer, UserPlus, Check } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../../services/api';

interface NurseDashboardProps {
  summary: any;
  date: string;
  isToday: boolean;
}

export const NurseDashboard: React.FC<NurseDashboardProps> = ({ summary, date, isToday }) => {
  const navigate = useNavigate();
  const kpis = summary?.kpis || {};
  const [triageQueue, setTriageQueue] = useState<any[]>([]);
  const [selectedVisit, setSelectedVisit] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [vitals, setVitals] = useState({
    sys: '140',
    dia: '90',
    pulse: '80',
    temp: '98.6',
    spo2: '98',
    height: '168',
    weight: '70',
    glucose: '120',
    notes: ''
  });

  const fetchTriageQueue = async () => {
    try {
      const res = await api.get(`visits/?queue=TRIAGE&date=${date}`);
      const list = res.data.results || res.data || [];
      setTriageQueue(list);
      if (list.length > 0 && !selectedVisit) {
        setSelectedVisit(list[0]);
      }
    } catch (e) {
      console.error('Failed to load triage queue', e);
    }
  };

  useEffect(() => {
    fetchTriageQueue();
  }, [date]);

  const handleSaveTriage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedVisit) return;
    if (!isToday) {
      alert('Triage vitals modifications are blocked on historical dates.');
      return;
    }
    setSaving(true);
    try {
      await api.post('triage/', {
        visit: selectedVisit.id,
        patient: selectedVisit.patient,
        blood_pressure_systolic: parseInt(vitals.sys),
        blood_pressure_diastolic: parseInt(vitals.dia),
        pulse_bpm: parseInt(vitals.pulse),
        temperature_f: parseFloat(vitals.temp),
        spo2_percent: parseInt(vitals.spo2),
        height_cm: parseFloat(vitals.height),
        weight_kg: parseFloat(vitals.weight),
        blood_glucose_mgdl: parseInt(vitals.glucose),
        nurse_notes: vitals.notes
      });
      alert('Triage vitals recorded successfully!');
      fetchTriageQueue();
      setSelectedVisit(null);
    } catch (err) {
      alert('Failed to save triage vitals.');
    } finally {
      setSaving(false);
    }
  };

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
              Patient registration, physiological vitals capture (BP, Pulse, SpO2, Temp, Glucose), NCD risk screening, and emergency queue prioritization.
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
          <p className="text-[10px] text-amber-700 font-medium mt-0.5">Vitals Pending</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-blue-200 bg-blue-50/30 shadow-xs">
          <p className="text-[11px] font-bold text-blue-800 uppercase">In Triage</p>
          <h3 className="text-xl font-black text-blue-900 mt-1">{kpis.in_triage || 0}</h3>
          <p className="text-[10px] text-blue-700 font-medium mt-0.5">Being Screened</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-purple-200 bg-purple-50/30 shadow-xs">
          <p className="text-[11px] font-bold text-purple-800 uppercase">Vitals Pending</p>
          <h3 className="text-xl font-black text-purple-900 mt-1">{kpis.vitals_pending || 0}</h3>
          <p className="text-[10px] text-purple-700 font-medium mt-0.5">Physical Check</p>
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

      {/* Main Grid: Active Triage Form & Queue Table */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Triage Entry Form */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-600" />
              Active Triage Vitals Entry
            </h2>
            {selectedVisit && (
              <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-900 font-mono font-bold text-xs">
                #{selectedVisit.token_details?.token_number || selectedVisit.id}
              </span>
            )}
          </div>

          {selectedVisit ? (
            <form onSubmit={handleSaveTriage} className="space-y-3">
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                <p className="font-bold text-slate-900">{selectedVisit.patient_details?.name || 'Patient'}</p>
                <p className="text-slate-500">{selectedVisit.patient_details?.age ? `${selectedVisit.patient_details.age} Yrs • ` : ''}{selectedVisit.patient_details?.gender || 'N/A'}{selectedVisit.chief_complaint ? ` • ${selectedVisit.chief_complaint}` : ''}</p>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <label className="block text-[10px] font-bold text-slate-600 mb-1">BP Systolic</label>
                  <input
                    type="number"
                    value={vitals.sys}
                    onChange={(e) => setVitals({ ...vitals, sys: e.target.value })}
                    className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
                    required
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-600 mb-1">BP Diastolic</label>
                  <input
                    type="number"
                    value={vitals.dia}
                    onChange={(e) => setVitals({ ...vitals, dia: e.target.value })}
                    className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
                    required
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-600 mb-1">Pulse (bpm)</label>
                  <input
                    type="number"
                    value={vitals.pulse}
                    onChange={(e) => setVitals({ ...vitals, pulse: e.target.value })}
                    className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
                    required
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-600 mb-1">SpO2 (%)</label>
                  <input
                    type="number"
                    value={vitals.spo2}
                    onChange={(e) => setVitals({ ...vitals, spo2: e.target.value })}
                    className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
                    required
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-600 mb-1">Temp (°F)</label>
                  <input
                    type="text"
                    value={vitals.temp}
                    onChange={(e) => setVitals({ ...vitals, temp: e.target.value })}
                    className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
                    required
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-600 mb-1">Glucose (mg/dL)</label>
                  <input
                    type="number"
                    value={vitals.glucose}
                    onChange={(e) => setVitals({ ...vitals, glucose: e.target.value })}
                    className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={saving || !isToday}
                className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-md transition cursor-pointer"
              >
                {saving ? 'Saving Vitals...' : 'Complete Triage & Move to Doctor Queue'}
              </button>
            </form>
          ) : (
            <div className="p-8 text-center text-xs text-slate-400 font-medium border border-dashed border-slate-200 rounded-xl">
              Select a waiting patient from the queue to record vitals.
            </div>
          )}
        </div>

        {/* Triage Queue Table */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
            <div>
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Clock className="w-4 h-4 text-emerald-600" />
                Triage Queue ({date})
              </h2>
              <p className="text-xs text-slate-500">Patients awaiting nurse physical screening</p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-100/70 border-b border-slate-200 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                  <th className="py-3 px-4">Priority</th>
                  <th className="py-3 px-4 text-center">Token</th>
                  <th className="py-3 px-4">Patient</th>
                  <th className="py-3 px-4 text-center">Age</th>
                  <th className="py-3 px-4 text-center">Arrival</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs font-medium">
                {triageQueue.length > 0 ? (
                  triageQueue.map((v: any) => (
                    <tr key={v.id} className="hover:bg-slate-50 transition">
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase bg-slate-100 text-slate-700">
                          {v.priority}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center font-mono font-bold text-emerald-700">
                        #{v.token_details?.token_number || v.id}
                      </td>
                      <td className="py-3 px-4 font-bold text-slate-900">{v.patient_details?.name || 'Patient'}</td>
                      <td className="py-3 px-4 text-center text-slate-600">{v.patient_details?.age ?? '-'}</td>
                      <td className="py-3 px-4 text-center text-slate-500">{v.waiting_time_minutes ? `${v.waiting_time_minutes}m ago` : '-'}</td>
                      <td className="py-3 px-4 text-center">
                        <span className="px-2 py-0.5 rounded-md bg-amber-50 text-amber-700 font-bold text-[10px] border border-amber-200">
                          {v.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => setSelectedVisit(v)}
                          className="px-2.5 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 font-bold text-[11px] rounded-lg transition cursor-pointer"
                        >
                          Start Triage
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-xs text-slate-400 font-medium">
                      No patients waiting for triage on selected date.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
