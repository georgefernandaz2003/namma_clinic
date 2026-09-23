import React, { useState, useEffect } from 'react';
import {
  Stethoscope,
  Clock,
  ShieldAlert,
  Activity,
  UserPlus,
  Check,
  CalendarCheck,
  Users,
  RefreshCw,
  CheckCircle2
} from 'lucide-react';
import { Link } from 'react-router-dom';
import api from '../../services/api';

interface NurseDashboardProps {
  summary: any;
  date: string;
  isToday: boolean;
}

export const NurseDashboard: React.FC<NurseDashboardProps> = ({ summary, date, isToday }) => {
  const [allVisits, setAllVisits] = useState<any[]>([]);
  const [triageQueue, setTriageQueue] = useState<any[]>([]);
  const [triages, setTriages] = useState<any[]>([]);
  const [followups, setFollowups] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedVisit, setSelectedVisit] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'triaged' | 'followups' | 'alerts'>('triaged');

  // Vitals form state
  const [vitals, setVitals] = useState({
    sys: '120',
    dia: '80',
    pulse: '76',
    temp: '98.6',
    spo2: '98',
    height: '165',
    weight: '65',
    glucose: '105',
    notes: ''
  });

  const loadNurseDashboardData = async () => {
    setLoading(true);
    try {
      // 1. Fetch Visits for target date
      const visitsRes = await api.get(`visits/?date=${date}`);
      const visitsList = visitsRes.data.results || visitsRes.data || [];
      setAllVisits(visitsList);

      // Filter visits waiting for triage
      const waiting = visitsList.filter((v: any) =>
        v.current_queue === 'TRIAGE' ||
        ['WAITING', 'WAITING_FOR_TRIAGE', 'IN_TRIAGE'].includes(v.status)
      );
      setTriageQueue(waiting);

      if (waiting.length > 0 && !selectedVisit) {
        setSelectedVisit(waiting[0]);
      } else if (waiting.length === 0) {
        setSelectedVisit(null);
      }

      // 2. Fetch Triage records
      const triageRes = await api.get('triage/');
      const triageList = triageRes.data.results || triageRes.data || [];
      setTriages(triageList);

      // 3. Fetch Follow-up Care patients
      const followupsRes = await api.get('followups/');
      const followupsList = followupsRes.data.results || followupsRes.data || [];
      setFollowups(followupsList);

      // 4. Fetch Clinical Alerts
      const alertsRes = await api.get('alerts/');
      const alertsList = alertsRes.data.results || alertsRes.data || [];
      setAlerts(alertsList);
    } catch (e) {
      console.error('Failed to load nurse dashboard data', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNurseDashboardData();
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
        blood_pressure_systolic: parseInt(vitals.sys) || 120,
        blood_pressure_diastolic: parseInt(vitals.dia) || 80,
        pulse_bpm: parseInt(vitals.pulse) || 72,
        temperature_f: parseFloat(vitals.temp) || 98.6,
        spo2_percent: parseInt(vitals.spo2) || 98,
        height_cm: parseFloat(vitals.height) || 165,
        weight_kg: parseFloat(vitals.weight) || 60,
        blood_glucose_mgdl: parseInt(vitals.glucose) || 100,
        nurse_notes: vitals.notes
      });
      alert(`Triage vitals recorded successfully for ${selectedVisit.patient_details?.name || 'patient'}!`);
      loadNurseDashboardData();
      setSelectedVisit(null);
    } catch {
      alert('Failed to save triage vitals.');
    } finally {
      setSaving(false);
    }
  };

  // KPI calculations from real API data
  const totalOpdToday = summary?.todays_opd ?? allVisits.length;
  const newPatientsToday = summary?.registered_today ?? 0;
  const waitingTriageCount = triageQueue.length;

  // Triages completed today
  const triagedVisitsToday = allVisits.filter((v: any) =>
    ['TRIAGED', 'WAITING_FOR_DOCTOR', 'IN_CONSULTATION', 'LAB_IN_PROGRESS', 'WAITING_FOR_PHARMACY', 'COMPLETED'].includes(v.status)
  );
  const triageCompletedToday = triagedVisitsToday.length;

  // Emergency / Red Flags count
  const emergencyVisits = allVisits.filter((v: any) => v.priority === 'EMERGENCY');
  const redFlagTriages = triages.filter((t: any) =>
    t.emergency_flag || t.high_bp_flag || t.fever_flag || t.low_spo2_flag
  );
  const emergencyCount = emergencyVisits.length + redFlagTriages.filter((t: any) => t.emergency_flag).length;

  return (
    <div className="space-y-6">
      {/* 1. Dashboard Header Banner */}
      <div className="bg-gradient-to-r from-emerald-900 via-teal-900 to-slate-900 rounded-2xl p-6 text-white shadow-md relative overflow-hidden">
        <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 bg-emerald-700/80 text-emerald-100 text-[10px] font-extrabold rounded-full uppercase tracking-wider border border-emerald-500/30">
                Nursing Station Scope
              </span>
              <span className="text-xs text-emerald-200 font-semibold">• {summary?.active_facility || 'Assigned Primary Clinic'}</span>
              <span className="text-xs text-emerald-300 font-mono">• Operational Date: {date}</span>
            </div>
            <h1 className="text-2xl font-black tracking-tight">Nursing Station Dashboard</h1>
            <p className="text-xs text-emerald-100 mt-1 max-w-xl">
              Outpatient triage queue, physiological vitals assessment, high-risk screening, and follow-up care management.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={loadNurseDashboardData}
              disabled={loading}
              className="px-3 py-2 bg-emerald-800/80 hover:bg-emerald-700 text-emerald-100 font-bold text-xs rounded-xl shadow-xs transition flex items-center gap-1.5 border border-emerald-600/40 cursor-pointer"
              title="Refresh Dashboard Data"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
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

      {/* 2. KPI Cards (5 Cards) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {/* Total OPD Patients Today */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-bold text-slate-500 uppercase">Total OPD Patients Today</p>
            <Users className="w-4 h-4 text-purple-600" />
          </div>
          <h3 className="text-2xl font-black text-slate-900 mt-1">{totalOpdToday}</h3>
          <p className="text-[10px] text-purple-700 font-medium mt-0.5">Total Clinic Visits</p>
        </div>

        {/* New Patients Today */}
        <div className="bg-white p-4 rounded-xl border border-emerald-200 bg-emerald-50/20 shadow-xs">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-bold text-emerald-800 uppercase">New Patients Today</p>
            <UserPlus className="w-4 h-4 text-emerald-600" />
          </div>
          <h3 className="text-2xl font-black text-emerald-900 mt-1">{newPatientsToday}</h3>
          <p className="text-[10px] text-emerald-700 font-medium mt-0.5">Registered Today</p>
        </div>

        {/* Waiting for Triage */}
        <div className="bg-white p-4 rounded-xl border border-amber-200 bg-amber-50/20 shadow-xs">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-bold text-amber-800 uppercase">Waiting for Triage</p>
            <Clock className="w-4 h-4 text-amber-600" />
          </div>
          <h3 className="text-2xl font-black text-amber-900 mt-1">{waitingTriageCount}</h3>
          <p className="text-[10px] text-amber-700 font-medium mt-0.5">Vitals Pending</p>
        </div>

        {/* Triage Completed Today */}
        <div className="bg-white p-4 rounded-xl border border-teal-200 bg-teal-50/20 shadow-xs">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-bold text-teal-800 uppercase">Triage Completed Today</p>
            <CheckCircle2 className="w-4 h-4 text-teal-600" />
          </div>
          <h3 className="text-2xl font-black text-teal-900 mt-1">{triageCompletedToday}</h3>
          <p className="text-[10px] text-teal-700 font-medium mt-0.5">Screened & Routed</p>
        </div>

        {/* Emergency / Red Flags */}
        <div className="bg-white p-4 rounded-xl border border-rose-200 bg-rose-50/20 shadow-xs">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-bold text-rose-800 uppercase">Emergency / Red Flags</p>
            <ShieldAlert className="w-4 h-4 text-rose-600" />
          </div>
          <h3 className="text-2xl font-black text-rose-900 mt-1">{emergencyCount}</h3>
          <p className="text-[10px] text-rose-700 font-medium mt-0.5">Priority Red Flags</p>
        </div>
      </div>

      {/* 3. Primary Operational Section: Triage Queue */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Triage Queue Table */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden flex flex-col">
          <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
            <div>
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Clock className="w-4 h-4 text-emerald-600" />
                <span>Triage Queue ({date})</span>
                <span className="ml-2 px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded-full text-[11px] font-bold">
                  {triageQueue.length} Waiting
                </span>
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Primary operational queue — patients awaiting physical examination and physiological vitals documentation
              </p>
            </div>
          </div>

          <div className="overflow-x-auto flex-1">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-100/70 border-b border-slate-200 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                  <th className="py-3 px-4">Priority</th>
                  <th className="py-3 px-4 text-center">Token</th>
                  <th className="py-3 px-4">Patient</th>
                  <th className="py-3 px-4 text-center">Age / Gender</th>
                  <th className="py-3 px-4">Chief Complaint</th>
                  <th className="py-3 px-4 text-center">Arrival</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs font-medium">
                {triageQueue.length > 0 ? (
                  triageQueue.map((v: any) => {
                    const isEmergency = v.priority === 'EMERGENCY';
                    const isHigh = v.priority === 'HIGH';
                    const isSelected = selectedVisit?.id === v.id;

                    return (
                      <tr
                        key={v.id}
                        className={`transition hover:bg-slate-50/80 ${
                          isSelected ? 'bg-emerald-50/60 border-l-4 border-l-emerald-600' : ''
                        }`}
                      >
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase border ${
                              isEmergency
                                ? 'bg-rose-100 text-rose-800 border-rose-200'
                                : isHigh
                                ? 'bg-amber-100 text-amber-800 border-amber-200'
                                : 'bg-slate-100 text-slate-700 border-slate-200'
                            }`}
                          >
                            {v.priority}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-center font-mono font-bold text-emerald-700">
                          #{v.token_details?.token_number || v.id}
                        </td>
                        <td className="py-3 px-4">
                          <p className="font-bold text-slate-900">{v.patient_details?.name || 'Patient'}</p>
                          <p className="text-[10px] text-slate-400 font-mono">{v.visit_id}</p>
                        </td>
                        <td className="py-3 px-4 text-center text-slate-600 whitespace-nowrap">
                          {v.patient_details?.age ? `${v.patient_details.age}y` : '-'} / {v.patient_details?.gender || '-'}
                        </td>
                        <td className="py-3 px-4 text-slate-700 max-w-[180px] truncate" title={v.chief_complaint}>
                          {v.chief_complaint || 'Routine Consultation'}
                        </td>
                        <td className="py-3 px-4 text-center text-slate-500 whitespace-nowrap">
                          {v.waiting_time_minutes ? `${v.waiting_time_minutes}m ago` : 'Just now'}
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span className="px-2 py-0.5 rounded-md bg-amber-50 text-amber-700 font-bold text-[10px] border border-amber-200 whitespace-nowrap">
                            {v.status?.replace(/_/g, ' ')}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => setSelectedVisit(v)}
                            className={`px-3 py-1 font-bold text-[11px] rounded-lg transition cursor-pointer ${
                              isSelected
                                ? 'bg-emerald-600 text-white'
                                : 'bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200'
                            }`}
                          >
                            {isSelected ? 'Screening' : 'Start Triage'}
                          </button>
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={8} className="py-10 text-center text-xs text-slate-400 font-medium">
                      <Check className="w-6 h-6 mx-auto mb-2 text-emerald-400 opacity-60" />
                      No patients waiting in the triage queue on selected date.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Col: Active Triage Vitals Form */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-600" />
              <span>Active Vitals Intake</span>
            </h2>
            {selectedVisit && (
              <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-900 font-mono font-bold text-xs">
                Token #{selectedVisit.token_details?.token_number || selectedVisit.id}
              </span>
            )}
          </div>

          {selectedVisit ? (
            <form onSubmit={handleSaveTriage} className="space-y-3">
              <div className="p-3 rounded-xl bg-emerald-50/50 border border-emerald-200/60 text-xs">
                <p className="font-bold text-slate-900">{selectedVisit.patient_details?.name || 'Patient'}</p>
                <p className="text-slate-600 mt-0.5">
                  {selectedVisit.patient_details?.age ? `${selectedVisit.patient_details.age}y • ` : ''}
                  {selectedVisit.patient_details?.gender || 'N/A'}
                  {selectedVisit.chief_complaint ? ` • ${selectedVisit.chief_complaint}` : ''}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <label className="block text-[10px] font-bold text-slate-600 mb-1">BP Systolic (mmHg)</label>
                  <input
                    type="number"
                    value={vitals.sys}
                    onChange={(e) => setVitals({ ...vitals, sys: e.target.value })}
                    className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg text-xs font-bold"
                    required
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-600 mb-1">BP Diastolic (mmHg)</label>
                  <input
                    type="number"
                    value={vitals.dia}
                    onChange={(e) => setVitals({ ...vitals, dia: e.target.value })}
                    className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg text-xs font-bold"
                    required
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-600 mb-1">Pulse (bpm)</label>
                  <input
                    type="number"
                    value={vitals.pulse}
                    onChange={(e) => setVitals({ ...vitals, pulse: e.target.value })}
                    className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg text-xs font-bold"
                    required
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-600 mb-1">SpO2 (%)</label>
                  <input
                    type="number"
                    value={vitals.spo2}
                    onChange={(e) => setVitals({ ...vitals, spo2: e.target.value })}
                    className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg text-xs font-bold"
                    required
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-600 mb-1">Temp (°F)</label>
                  <input
                    type="text"
                    value={vitals.temp}
                    onChange={(e) => setVitals({ ...vitals, temp: e.target.value })}
                    className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg text-xs font-bold"
                    required
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-600 mb-1">Blood Glucose (mg/dL)</label>
                  <input
                    type="number"
                    value={vitals.glucose}
                    onChange={(e) => setVitals({ ...vitals, glucose: e.target.value })}
                    className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg text-xs font-bold"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-600 mb-1">Nurse Clinical Notes</label>
                <textarea
                  value={vitals.notes}
                  onChange={(e) => setVitals({ ...vitals, notes: e.target.value })}
                  placeholder="Record patient presentation observations, visible distress, or NCD risk..."
                  className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg text-xs h-16 resize-none"
                />
              </div>

              <button
                type="submit"
                disabled={saving || !isToday}
                className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 text-white font-bold text-xs rounded-xl shadow-md transition cursor-pointer"
              >
                {saving ? 'Saving Vitals...' : 'Complete Triage & Route to Doctor Queue'}
              </button>
            </form>
          ) : (
            <div className="p-8 text-center text-xs text-slate-400 font-medium border border-dashed border-slate-200 rounded-xl space-y-2">
              <Stethoscope className="w-6 h-6 mx-auto text-slate-300" />
              <p>Select a waiting patient from the triage queue to record physiological vitals.</p>
            </div>
          )}
        </div>
      </div>

      {/* 4. Secondary Operational Sections (Recently Triaged, Follow-up Patients, Emergency Alerts) */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        {/* Navigation Tabs */}
        <div className="border-b border-slate-200 px-5 flex items-center gap-6 bg-slate-50/50">
          <button
            onClick={() => setActiveTab('triaged')}
            className={`py-3.5 text-xs font-bold flex items-center gap-2 border-b-2 transition cursor-pointer ${
              activeTab === 'triaged'
                ? 'border-emerald-600 text-emerald-800'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>Recently Triaged Patients</span>
            <span className="ml-1 px-1.5 py-0.5 rounded-full bg-slate-200 text-slate-700 text-[10px] font-bold">
              {triages.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('followups')}
            className={`py-3.5 text-xs font-bold flex items-center gap-2 border-b-2 transition cursor-pointer ${
              activeTab === 'followups'
                ? 'border-emerald-600 text-emerald-800'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <CalendarCheck className="w-4 h-4" />
            <span>Follow-up Patients</span>
            <span className="ml-1 px-1.5 py-0.5 rounded-full bg-slate-200 text-slate-700 text-[10px] font-bold">
              {followups.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('alerts')}
            className={`py-3.5 text-xs font-bold flex items-center gap-2 border-b-2 transition cursor-pointer ${
              activeTab === 'alerts'
                ? 'border-rose-600 text-rose-800'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <ShieldAlert className="w-4 h-4 text-rose-600" />
            <span>Emergency / Red Flag Alerts</span>
            <span className="ml-1 px-1.5 py-0.5 rounded-full bg-rose-100 text-rose-800 text-[10px] font-bold">
              {redFlagTriages.length + emergencyVisits.length}
            </span>
          </button>
        </div>

        {/* Tab 1: Recently Triaged Patients */}
        {activeTab === 'triaged' && (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-100/60 border-b border-slate-200 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                  <th className="py-3 px-4">Patient</th>
                  <th className="py-3 px-4 text-center">BP (mmHg)</th>
                  <th className="py-3 px-4 text-center">Pulse</th>
                  <th className="py-3 px-4 text-center">Temp</th>
                  <th className="py-3 px-4 text-center">SpO2</th>
                  <th className="py-3 px-4 text-center">Glucose</th>
                  <th className="py-3 px-4">Clinical Flags</th>
                  <th className="py-3 px-4">Nurse Observations</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {triages.length > 0 ? (
                  triages.map((t: any) => {
                    const isHighBp = t.high_bp_flag || t.blood_pressure_systolic >= 140 || t.blood_pressure_diastolic >= 90;
                    const isFever = t.fever_flag || parseFloat(t.temperature_f) >= 100.4;
                    const isHighGlucose = t.high_glucose_flag || t.blood_glucose_mgdl >= 160;

                    return (
                      <tr key={t.id} className="hover:bg-slate-50/70 transition">
                        <td className="py-3 px-4 font-bold text-slate-900">
                          {t.patient_name || 'Patient'}
                        </td>
                        <td className="py-3 px-4 text-center font-mono">
                          <span className={`px-1.5 py-0.5 rounded font-bold ${isHighBp ? 'bg-rose-100 text-rose-800' : 'text-slate-800'}`}>
                            {t.blood_pressure_systolic}/{t.blood_pressure_diastolic}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-center font-mono text-slate-700">
                          {t.pulse_bpm} bpm
                        </td>
                        <td className="py-3 px-4 text-center font-mono">
                          <span className={`${isFever ? 'text-rose-700 font-bold' : 'text-slate-700'}`}>
                            {t.temperature_f}°F
                          </span>
                        </td>
                        <td className="py-3 px-4 text-center font-mono text-slate-700">
                          {t.spo2_percent}%
                        </td>
                        <td className="py-3 px-4 text-center font-mono">
                          <span className={`${isHighGlucose ? 'text-amber-700 font-bold' : 'text-slate-700'}`}>
                            {t.blood_glucose_mgdl} mg/dL
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex flex-wrap gap-1">
                            {isHighBp && (
                              <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800">
                                High BP
                              </span>
                            )}
                            {isHighGlucose && (
                              <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">
                                High Glucose
                              </span>
                            )}
                            {isFever && (
                              <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-orange-100 text-orange-800">
                                Pyrexia
                              </span>
                            )}
                            {t.emergency_flag && (
                              <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-red-600 text-white animate-pulse">
                                RED FLAG
                              </span>
                            )}
                            {!isHighBp && !isHighGlucose && !isFever && !t.emergency_flag && (
                              <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700">
                                Normal Vitals
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4 text-slate-600 max-w-[220px] truncate" title={t.nurse_notes}>
                          {t.nurse_notes || 'Routine vitals recorded.'}
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-xs text-slate-400 font-medium">
                      No triage vitals documented yet for this facility.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Tab 2: Follow-up Patients */}
        {activeTab === 'followups' && (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-100/60 border-b border-slate-200 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                  <th className="py-3 px-4">Patient</th>
                  <th className="py-3 px-4 text-center">Category</th>
                  <th className="py-3 px-4 text-center">Due Date</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4">Follow-up Instructions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {followups.length > 0 ? (
                  followups.map((f: any) => (
                    <tr key={f.id} className="hover:bg-slate-50/70 transition">
                      <td className="py-3 px-4 font-bold text-slate-900">
                        {f.patient_name || 'Patient'}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                          {f.category}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center font-mono font-bold text-slate-800">
                        {f.due_date}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span
                          className={`px-2 py-0.5 rounded-md text-[10px] font-bold border ${
                            f.status === 'COMPLETED'
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                              : 'bg-amber-50 text-amber-700 border-amber-200'
                          }`}
                        >
                          {f.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-600 max-w-[280px] truncate" title={f.notes}>
                        {f.notes || 'Routine follow-up assessment.'}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-xs text-slate-400 font-medium">
                      No follow-up care schedules logged for this facility.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Tab 3: Emergency / Red Flag Alerts */}
        {activeTab === 'alerts' && (
          <div className="p-5 space-y-3">
            {emergencyVisits.length > 0 || redFlagTriages.length > 0 || alerts.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {emergencyVisits.map((ev: any) => (
                  <div key={ev.id} className="p-4 rounded-xl border border-rose-300 bg-rose-50/40 shadow-xs space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="px-2 py-0.5 rounded bg-rose-600 text-white font-extrabold text-[10px] uppercase">
                        CRITICAL EMERGENCY
                      </span>
                      <span className="text-[10px] font-mono font-bold text-rose-800">#{ev.token_details?.token_number || ev.id}</span>
                    </div>
                    <p className="font-bold text-slate-900 text-sm">{ev.patient_details?.name || 'Patient'}</p>
                    <p className="text-xs text-rose-900 font-medium">{ev.chief_complaint || 'Severe acute presentation'}</p>
                    <p className="text-[10px] text-slate-500">Queue: {ev.current_queue} • Status: {ev.status}</p>
                  </div>
                ))}

                {redFlagTriages.map((rt: any) => (
                  <div key={rt.id} className="p-4 rounded-xl border border-amber-300 bg-amber-50/40 shadow-xs space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="px-2 py-0.5 rounded bg-amber-600 text-white font-extrabold text-[10px] uppercase">
                        Vitals Excursion Flag
                      </span>
                      <span className="text-[10px] font-bold text-amber-800">
                        BP {rt.blood_pressure_systolic}/{rt.blood_pressure_diastolic}
                      </span>
                    </div>
                    <p className="font-bold text-slate-900 text-sm">{rt.patient_name || 'Patient'}</p>
                    <p className="text-xs text-amber-900 font-medium">{rt.nurse_notes || 'Elevated physiological markers detected.'}</p>
                    <div className="flex gap-1 flex-wrap pt-0.5">
                      {rt.high_bp_flag && <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-rose-100 text-rose-800">High BP</span>}
                      {rt.fever_flag && <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-orange-100 text-orange-800">Fever</span>}
                      {rt.high_glucose_flag && <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-100 text-amber-800">High Glucose</span>}
                    </div>
                  </div>
                ))}

                {alerts.map((al: any) => (
                  <div key={al.id} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 shadow-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="px-2 py-0.5 rounded bg-slate-200 text-slate-700 font-bold text-[10px] uppercase">
                        {al.severity || 'ALERT'}
                      </span>
                      <span className="text-[10px] text-slate-400 font-semibold">{al.status}</span>
                    </div>
                    <p className="font-bold text-slate-900 text-xs">{al.title}</p>
                    <p className="text-[11px] text-slate-600 line-clamp-2">{al.description}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-8 text-center text-xs text-slate-400 font-medium">
                <ShieldAlert className="w-6 h-6 mx-auto mb-2 text-slate-300" />
                No active emergency flags or clinical red flags detected.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
