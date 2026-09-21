import React, { useState, useEffect } from 'react';
import api from '../services/api';
import type { Visit, Patient } from '../types';
import { useAuth } from '../context/AuthContext';
import {
  Clock, ArrowRight, Plus, X, ChevronLeft, ChevronRight,
  ShieldAlert, CheckCircle, Lock, History, Eye, Play
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const Queue: React.FC = () => {
  const { activeFacility, user } = useAuth();
  const navigate = useNavigate();

  // Helper for YYYY-MM-DD
  const getTodayStr = () => new Date().toISOString().split('T')[0];

  // State
  const [selectedDate, setSelectedDate] = useState<string>(getTodayStr());
  const [activeTab, setActiveTab] = useState<string>('ALL');
  const [allVisits, setAllVisits] = useState<Visit[]>([]);
  const [visits, setVisits] = useState<Visit[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [historySummary, setHistorySummary] = useState<any[]>([]);
  const [showTokenModal, setShowTokenModal] = useState(false);
  const [showHistorySection, setShowHistorySection] = useState(false);
  const [selectedVisitHistory, setSelectedVisitHistory] = useState<Visit | null>(null);

  // Form State
  const [selectedPatientId, setSelectedPatientId] = useState<number | string>('');
  const [visitType, setVisitType] = useState('GENERAL_OPD');
  const [priority, setPriority] = useState('NORMAL');
  const [chiefComplaint, setChiefComplaint] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [callingNext, setCallingNext] = useState(false);

  const isToday = selectedDate === getTodayStr();
  const isPast = selectedDate < getTodayStr();

  const loadQueue = async () => {
    if (!activeFacility) return;
    try {
      // Always fetch all visits for the selected date to maintain accurate top KPI counters
      const allRes = await api.get(`visits/?facility=${activeFacility.id}&date=${selectedDate}`);
      const fullList: Visit[] = allRes.data.results || allRes.data || [];
      setAllVisits(fullList);

      // Populate table with filtered list
      if (activeTab === 'ALL') {
        setVisits(fullList);
      } else {
        const queueRes = await api.get(`visits/?facility=${activeFacility.id}&date=${selectedDate}&queue=${activeTab}`);
        setVisits(queueRes.data.results || queueRes.data || []);
      }
    } catch (e) {
      console.error('Failed to load date-based OPD queue', e);
    }
  };

  const loadPatients = async () => {
    try {
      const facQuery = activeFacility?.id ? `?facility=${activeFacility.id}` : '';
      const res = await api.get(`patients/${facQuery}`);
      const patList = res.data.results || res.data || [];
      setPatients(patList);
      if (patList.length > 0) {
        setSelectedPatientId(patList[0].id);
      }
    } catch (e) {
      console.error('Failed to load registered patients', e);
    }
  };

  const loadHistorySummary = async () => {
    if (!activeFacility) return;
    try {
      const res = await api.get(`visits/history-summary/?facility=${activeFacility.id}`);
      setHistorySummary(res.data || []);
    } catch (e) {
      console.error('Failed to load OPD history summary', e);
    }
  };

  useEffect(() => {
    loadQueue();
    loadPatients();
    loadHistorySummary();
  }, [activeFacility, activeFacility?.id, selectedDate, activeTab]);

  // Date Navigation Handlers
  const handlePrevDay = () => {
    const d = new Date(selectedDate);
    d.setDate(d.getDate() - 1);
    setSelectedDate(d.toISOString().split('T')[0]);
  };

  const handleNextDay = () => {
    const d = new Date(selectedDate);
    d.setDate(d.getDate() + 1);
    setSelectedDate(d.toISOString().split('T')[0]);
  };

  const handleSetToday = () => {
    setSelectedDate(getTodayStr());
  };

  // Issue Token Handler
  const handleIssueToken = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isToday) {
      alert('OPD tokens can only be issued for the current operational day (Today).');
      return;
    }
    if (!selectedPatientId || !activeFacility) {
      alert('Please select a patient and facility');
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post('visits/', {
        patient: selectedPatientId,
        facility: activeFacility.id,
        visit_type: visitType,
        priority,
        chief_complaint: chiefComplaint
      });
      const newVisit = res.data;
      const tokNum = newVisit.token_details?.token_number || newVisit.id;
      alert(`OPD Token #${tokNum} Issued Successfully!\nUnique Scope: ${activeFacility.facility_name} • Date: ${selectedDate} • Token #${tokNum}`);
      setShowTokenModal(false);
      setChiefComplaint('');
      loadQueue();
      loadHistorySummary();
    } catch (e: any) {
      let msg = 'Failed to issue OPD Token.';
      if (e.response?.data?.error) {
        msg = e.response.data.error;
      } else if (e.response?.data?.detail) {
        msg = e.response.data.detail;
      }
      alert(msg);
    } finally {
      setSubmitting(false);
    }
  };

  // Call Next Patient Handler
  const handleCallNext = async () => {
    if (!isToday) {
      alert('Calling next patient is disabled on historical or future dates.');
      return;
    }
    if (!activeFacility) return;
    setCallingNext(true);
    try {
      const targetQueue = activeTab !== 'ALL' ? activeTab : (user?.role === 'NURSE' ? 'TRIAGE' : 'DOCTOR');
      const res = await api.post('visits/call-next/', {
        facility: activeFacility.id,
        queue: targetQueue
      });
      
      if (res.data.message) {
        alert(res.data.message);
      } else {
        const called = res.data;
        const tokNum = called.token_details?.token_number || called.id;
        alert(`Patient Called Successfully!\nToken #${tokNum} (${called.patient_details?.name}) assigned to ${called.assigned_doctor_name || 'Workstation'}.`);
        loadQueue();
      }
    } catch (e: any) {
      alert(e.response?.data?.error || 'Failed to call next patient.');
    } finally {
      setCallingNext(false);
    }
  };

  // Dynamic KPI Calculations based on allVisits for selectedDate
  const totalOpdCount = allVisits.length;
  const waitingTriageCount = allVisits.filter(v => v.status === 'WAITING_FOR_TRIAGE' || (v.current_queue === 'TRIAGE' && v.status !== 'COMPLETED')).length;
  const waitingDoctorCount = allVisits.filter(v => v.status === 'WAITING_FOR_DOCTOR' || v.status === 'TRIAGED' || v.status === 'LAB_COMPLETED').length;
  const inConsultationCount = allVisits.filter(v => v.status === 'IN_CONSULTATION').length;
  const labPendingCount = allVisits.filter(v => v.current_queue === 'LAB' || v.status === 'LAB_PENDING' || v.status === 'LAB_IN_PROGRESS').length;
  const waitingPharmacyCount = allVisits.filter(v => v.current_queue === 'PHARMACY' || v.status.includes('PHARMACY')).length;
  const completedCount = allVisits.filter(v => v.status === 'COMPLETED').length;

  // Format Date for Header
  const formattedDate = new Date(selectedDate + 'T00:00:00').toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  });

  return (
    <div className="space-y-6">
      {/* Top Banner & Date Selector */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <Clock className="w-6 h-6 text-teal-600" />
            <h1 className="text-xl font-black text-slate-900">
              OPD Queue — <span className="text-emerald-700">{formattedDate}</span>
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Date-Based Facility Queue Scope: <span className="font-bold text-slate-800">{activeFacility?.facility_name || 'Select Facility'}</span>
          </p>
        </div>

        {/* Date Selector Navigation Controls */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-300">
            <button
              onClick={handlePrevDay}
              title="Previous Day"
              className="p-1.5 rounded-lg text-slate-600 hover:bg-white hover:text-slate-900 transition"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="bg-transparent text-xs font-bold text-slate-900 px-2 focus:outline-none cursor-pointer"
            />
            <button
              onClick={handleNextDay}
              title="Next Day"
              className="p-1.5 rounded-lg text-slate-600 hover:bg-white hover:text-slate-900 transition"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={handleSetToday}
            className={`px-3 py-2 rounded-xl text-xs font-bold border transition ${
              isToday
                ? 'bg-emerald-600 text-white border-emerald-600 shadow-sm'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-300'
            }`}
          >
            Today
          </button>

          {/* Issue Token Button (Enabled ONLY on Today) */}
          <button
            onClick={() => {
              if (!isToday) {
                alert('OPD tokens can only be issued for the current operational day (Today).');
                return;
              }
              loadPatients();
              setShowTokenModal(true);
            }}
            disabled={!isToday}
            className={`flex items-center gap-2 px-4 py-2 font-bold text-xs rounded-xl shadow-sm transition ${
              isToday
                ? 'bg-emerald-600 hover:bg-emerald-500 text-white'
                : 'bg-slate-200 text-slate-400 cursor-not-allowed border border-slate-300'
            }`}
          >
            <Plus className="w-4 h-4" />
            <span>Issue New OPD Token</span>
          </button>
        </div>
      </div>

      {/* Date Mode Status Banner */}
      <div className={`p-4 rounded-2xl border text-xs flex items-center justify-between shadow-xs ${
        isToday
          ? 'bg-emerald-50 border-emerald-300 text-emerald-950'
          : isPast
          ? 'bg-amber-50 border-amber-300 text-amber-950'
          : 'bg-rose-50 border-rose-300 text-rose-950'
      }`}>
        <div className="flex items-center gap-3">
          {isToday ? (
            <div className="w-8 h-8 rounded-xl bg-emerald-600 text-white flex items-center justify-center font-black shrink-0">
              🟢
            </div>
          ) : isPast ? (
            <div className="w-8 h-8 rounded-xl bg-amber-600 text-white flex items-center justify-center font-black shrink-0">
              <Lock className="w-4 h-4" />
            </div>
          ) : (
            <div className="w-8 h-8 rounded-xl bg-rose-600 text-white flex items-center justify-center font-black shrink-0">
              <ShieldAlert className="w-4 h-4" />
            </div>
          )}
          <div>
            <h2 className="font-bold text-sm">
              {isToday
                ? 'Operational OPD Queue (Live Actions Active)'
                : isPast
                ? `Historical OPD Queue Record (${formattedDate})`
                : 'Future Date OPD Queue (Token Creation Blocked)'}
            </h2>
            <p className="text-[11px] opacity-90 mt-0.5">
              {isToday
                ? 'Token numbers are unique per facility and date (restarting at #1 every morning). Clinical workflow transitions and triage routing are enabled.'
                : isPast
                ? 'Historical queue entries are stored for audit and reporting. Clinical transitions and token generation are read-only for past dates.'
                : 'Future OPD tokens cannot be created in advance. Normal OPD queues operate strictly on the current day.'}
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowHistorySection(!showHistorySection)}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-300 text-slate-800 font-bold text-xs rounded-xl hover:bg-slate-100 shrink-0"
        >
          <History className="w-3.5 h-3.5 text-teal-600" />
          <span>{showHistorySection ? 'Hide History Summary' : 'OPD History Summary'}</span>
        </button>
      </div>

      {/* Dynamic Date KPI Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
        <div className="bg-white p-3.5 rounded-2xl border border-slate-200 shadow-xs">
          <p className="text-[10px] font-bold uppercase text-slate-500 tracking-wider">Total OPD</p>
          <p className="text-xl font-black text-slate-900 mt-1">{totalOpdCount}</p>
        </div>
        <div className="bg-white p-3.5 rounded-2xl border border-emerald-200 shadow-xs">
          <p className="text-[10px] font-bold uppercase text-emerald-700 tracking-wider">Wait Triage</p>
          <p className="text-xl font-black text-emerald-800 mt-1">{waitingTriageCount}</p>
        </div>
        <div className="bg-white p-3.5 rounded-2xl border border-blue-200 shadow-xs">
          <p className="text-[10px] font-bold uppercase text-blue-700 tracking-wider">Wait Doctor</p>
          <p className="text-xl font-black text-blue-800 mt-1">{waitingDoctorCount}</p>
        </div>
        <div className="bg-white p-3.5 rounded-2xl border border-indigo-200 shadow-xs">
          <p className="text-[10px] font-bold uppercase text-indigo-700 tracking-wider">In Consult</p>
          <p className="text-xl font-black text-indigo-800 mt-1">{inConsultationCount}</p>
        </div>
        <div className="bg-white p-3.5 rounded-2xl border border-purple-200 shadow-xs">
          <p className="text-[10px] font-bold uppercase text-purple-700 tracking-wider">Lab Pending</p>
          <p className="text-xl font-black text-purple-800 mt-1">{labPendingCount}</p>
        </div>
        <div className="bg-white p-3.5 rounded-2xl border border-amber-200 shadow-xs">
          <p className="text-[10px] font-bold uppercase text-amber-700 tracking-wider">Wait Pharmacy</p>
          <p className="text-xl font-black text-amber-800 mt-1">{waitingPharmacyCount}</p>
        </div>
        <div className="bg-white p-3.5 rounded-2xl border border-teal-200 shadow-xs">
          <p className="text-[10px] font-bold uppercase text-teal-700 tracking-wider">Completed</p>
          <p className="text-xl font-black text-teal-800 mt-1">{completedCount}</p>
        </div>
      </div>

      {/* OPD History Summary Drawer */}
      {showHistorySection && (
        <div className="bg-white p-5 rounded-2xl border border-slate-200 space-y-3 shadow-md">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <History className="w-4 h-4 text-emerald-600" />
            OPD Queue History Log (Last 30 Days)
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                <tr>
                  <th className="p-3">OPD Date</th>
                  <th className="p-3">Total Registered Patients</th>
                  <th className="p-3">Completed Visits</th>
                  <th className="p-3">Cancelled / No-Show</th>
                  <th className="p-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {historySummary.map((item) => (
                  <tr key={item.opd_date} className={`hover:bg-slate-50 transition ${selectedDate === item.opd_date ? 'bg-emerald-50/60 font-bold' : ''}`}>
                    <td className="p-3 font-mono font-bold text-slate-900">{item.opd_date}</td>
                    <td className="p-3 font-bold text-slate-800">{item.total_patients} Patients</td>
                    <td className="p-3 text-emerald-700 font-bold">{item.completed_patients} Completed</td>
                    <td className="p-3 text-rose-600 font-bold">{item.cancelled_patients} Cancelled</td>
                    <td className="p-3">
                      <button
                        onClick={() => setSelectedDate(item.opd_date)}
                        className="px-3 py-1 bg-slate-100 hover:bg-emerald-100 text-emerald-800 font-bold text-xs rounded-lg border border-slate-300 transition"
                      >
                        Inspect Queue
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Queue Filter Tabs & Action Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 shadow-xs">
        {/* Role-Based Queue Filter Tabs */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs font-bold">
          {[
            { id: 'ALL', label: 'All Queue', count: allVisits.length },
            { id: 'TRIAGE', label: 'Nurse Triage', count: waitingTriageCount },
            { id: 'DOCTOR', label: 'Doctor Consult', count: waitingDoctorCount + inConsultationCount },
            { id: 'LAB', label: 'Laboratory', count: labPendingCount },
            { id: 'PHARMACY', label: 'Pharmacy', count: waitingPharmacyCount },
            { id: 'COMPLETED', label: 'Completed', count: completedCount }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3 py-2 rounded-xl transition flex items-center gap-1.5 ${
                activeTab === tab.id
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-600'
              }`}
            >
              <span>{tab.label}</span>
              <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono font-bold ${
                activeTab === tab.id ? 'bg-slate-700 text-white' : 'bg-slate-200 text-slate-700'
              }`}>
                {tab.count}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Enhanced Date-Based Queue Table */}
      <div className="glass-panel rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-xs">
        <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
          <h2 className="text-sm font-bold text-slate-900">
            {formattedDate} — {activeTab} OPD Queue List ({visits.length} Records)
          </h2>
          <button onClick={loadQueue} className="px-3 py-1 bg-white border border-slate-300 text-slate-700 text-xs font-bold rounded-lg hover:bg-slate-100">
            Refresh List
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
              <tr>
                <th className="p-3.5">Priority</th>
                <th className="p-3.5">Token #</th>
                <th className="p-3.5">Patient Details</th>
                <th className="p-3.5">Visit Type</th>
                <th className="p-3.5">Arrival</th>
                <th className="p-3.5">Waiting Time</th>
                <th className="p-3.5">Queue</th>
                <th className="p-3.5">Workflow Status</th>
                <th className="p-3.5">Assigned Clinician</th>
                <th className="p-3.5">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {visits.length === 0 ? (
                <tr>
                  <td colSpan={10} className="p-8 text-center text-slate-400 font-medium">
                    No OPD tokens found for {formattedDate} under the selected filter.
                  </td>
                </tr>
              ) : (
                visits.map((v) => {
                  const tokNum = v.token_details?.token_number || v.id;
                  const prio = v.priority || v.token_details?.priority || 'NORMAL';
                  const arrivalFormatted = v.arrival_time ? new Date(v.arrival_time).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : '—';
                  const waitingMins = v.waiting_time_minutes ?? 0;

                  return (
                    <tr key={v.id} className="hover:bg-slate-50/80 transition">
                      <td className="p-3.5">
                        <span className={`px-2 py-1 rounded-md text-[10px] font-black border ${
                          prio === 'EMERGENCY' ? 'bg-rose-100 text-rose-900 border-rose-300' :
                          prio === 'HIGH' ? 'bg-amber-100 text-amber-900 border-amber-300' :
                          'bg-emerald-100 text-emerald-900 border-emerald-300'
                        }`}>
                          {prio === 'EMERGENCY' ? '🚨 EMERGENCY' : prio === 'HIGH' ? '⚡ HIGH' : '🟢 NORMAL'}
                        </span>
                      </td>

                      <td className="p-3.5 font-mono font-black text-base text-emerald-700">
                        #{tokNum}
                      </td>

                      <td className="p-3.5">
                        <span className="font-bold text-slate-900 block">{v.patient_details?.name}</span>
                        <span className="text-[10px] text-slate-500 font-medium">
                          {v.patient_details?.age} yrs • {v.patient_details?.gender} • UHID: {v.patient_details?.patient_id}
                        </span>
                      </td>

                      <td className="p-3.5 text-slate-700 font-semibold">{v.visit_type}</td>

                      <td className="p-3.5 font-mono text-slate-700 font-medium">{arrivalFormatted}</td>

                      <td className="p-3.5 font-mono font-bold text-amber-700">
                        {v.status === 'COMPLETED' ? '—' : `${waitingMins} min`}
                      </td>

                      <td className="p-3.5">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                          v.current_queue === 'LAB' ? 'bg-purple-100 text-purple-800 border-purple-300' :
                          v.current_queue === 'PHARMACY' ? 'bg-amber-100 text-amber-800 border-amber-300' :
                          v.current_queue === 'DOCTOR' ? 'bg-blue-100 text-blue-800 border-blue-300' :
                          v.current_queue === 'TRIAGE' ? 'bg-emerald-100 text-emerald-800 border-emerald-300' :
                          'bg-slate-100 text-slate-800 border-slate-300'
                        }`}>
                          {v.current_queue || 'TRIAGE'}
                        </span>
                      </td>

                      <td className="p-3.5">
                        <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold border ${
                          v.status === 'COMPLETED' ? 'bg-teal-100 text-teal-800 border-teal-300' :
                          v.status.includes('LAB') ? 'bg-purple-100 text-purple-800 border-purple-300' :
                          v.status.includes('PHARMACY') ? 'bg-amber-100 text-amber-800 border-amber-300' :
                          v.status.includes('IN_') ? 'bg-indigo-100 text-indigo-800 border-indigo-300' :
                          v.status.includes('WAITING') ? 'bg-amber-50 text-amber-800 border-amber-300' :
                          'bg-slate-100 text-slate-700 border-slate-300'
                        }`}>
                          {v.status.replace(/_/g, ' ')}
                        </span>
                      </td>

                      <td className="p-3.5 text-slate-800 font-semibold">
                        {v.assigned_doctor_name || '—'}
                      </td>

                      <td className="p-3.5">
                        {isToday ? (
                          <div className="flex items-center gap-1.5">
                            {(v.status === 'WAITING_FOR_TRIAGE' || v.status === 'WAITING') && (
                              <button
                                onClick={() => navigate('/triage', { state: { visitId: v.id } })}
                                className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg text-xs flex items-center gap-1 shadow-xs"
                              >
                                <span>Triage</span> <ArrowRight className="w-3 h-3" />
                              </button>
                            )}

                            {(v.status === 'WAITING_FOR_DOCTOR' || v.status === 'TRIAGED' || v.status === 'IN_CONSULTATION' || v.status === 'LAB_COMPLETED') && (
                              <button
                                onClick={() => navigate('/consultation', { state: { visitId: v.id } })}
                                className={`px-3 py-1 font-bold rounded-lg text-xs flex items-center gap-1 shadow-xs text-white ${
                                  v.status === 'LAB_COMPLETED' ? 'bg-purple-600 hover:bg-purple-500' : 'bg-blue-600 hover:bg-blue-500'
                                }`}
                              >
                                <span>{v.status === 'LAB_COMPLETED' ? 'Re-Consult' : 'Consult'}</span> <ArrowRight className="w-3 h-3" />
                              </button>
                            )}

                            {(v.current_queue === 'LAB' || v.status === 'LAB_PENDING' || v.status === 'LAB_IN_PROGRESS') && (
                              <button
                                onClick={() => navigate('/lab', { state: { selectedDate } })}
                                className="px-3 py-1 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-lg text-xs flex items-center gap-1 shadow-xs"
                              >
                                <span>Lab Order</span> <ArrowRight className="w-3 h-3" />
                              </button>
                            )}

                            {(v.status.includes('PHARMACY') || v.current_queue === 'PHARMACY') && (
                              <button
                                onClick={() => navigate('/pharmacy', { state: { visitId: v.id, patientId: v.patient, activeTab: 'PRESCRIPTIONS' } })}
                                className="px-3 py-1 bg-amber-600 hover:bg-amber-500 text-white font-bold rounded-lg text-xs flex items-center gap-1 shadow-xs"
                              >
                                <span>Dispense</span> <ArrowRight className="w-3 h-3" />
                              </button>
                            )}

                            {v.status === 'COMPLETED' && (
                              <span className="text-teal-700 font-bold flex items-center gap-1">
                                <CheckCircle className="w-3.5 h-3.5 text-teal-600" /> Done
                              </span>
                            )}
                          </div>
                        ) : (
                          <button
                            onClick={() => setSelectedVisitHistory(v)}
                            className="px-2.5 py-1 bg-slate-100 text-slate-700 hover:bg-slate-200 font-bold text-[11px] rounded-lg border border-slate-300 flex items-center gap-1"
                          >
                            <Eye className="w-3 h-3 text-slate-500" /> Read-Only
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Historical Audit Detail Modal */}
      {selectedVisitHistory && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 border border-slate-200 w-full max-w-lg space-y-4 shadow-xl">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <History className="w-5 h-5 text-teal-600" />
                Historical OPD Visit Audit Log
              </h2>
              <button
                onClick={() => setSelectedVisitHistory(null)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
                <p><span className="font-bold text-slate-900">Patient:</span> {selectedVisitHistory.patient_details?.name} (UHID: {selectedVisitHistory.patient_details?.patient_id})</p>
                <p><span className="font-bold text-slate-900">OPD Date:</span> {selectedVisitHistory.opd_date}</p>
                <p><span className="font-bold text-slate-900">Token Number:</span> #{selectedVisitHistory.token_details?.token_number || selectedVisitHistory.id}</p>
                <p><span className="font-bold text-slate-900">Final Status:</span> {selectedVisitHistory.status}</p>
              </div>

              <h3 className="font-bold text-slate-900">Workflow Transition History:</h3>
              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                {selectedVisitHistory.status_history_list && selectedVisitHistory.status_history_list.length > 0 ? (
                  selectedVisitHistory.status_history_list.map((h: any) => (
                    <div key={h.id} className="p-2.5 bg-white border border-slate-200 rounded-xl space-y-1">
                      <div className="flex justify-between text-[11px] font-bold">
                        <span className="text-emerald-700">{h.from_status} → {h.to_status}</span>
                        <span className="text-slate-400">{new Date(h.timestamp).toLocaleTimeString()}</span>
                      </div>
                      <p className="text-[10px] text-slate-600">By: {h.performed_by_name || 'System'} ({h.performed_by_role})</p>
                      {h.notes && <p className="text-[10px] text-slate-500 italic">&ldquo;{h.notes}&rdquo;</p>}
                    </div>
                  ))
                ) : (
                  <p className="text-slate-500 italic">No transition history records logged for this visit.</p>
                )}
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedVisitHistory(null)}
                className="px-4 py-2 bg-slate-900 text-white font-bold rounded-xl text-xs"
              >
                Close Audit View
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Issue Token Modal (Today Only) */}
      {showTokenModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 border border-slate-200 w-full max-w-lg space-y-4 shadow-xl">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Clock className="w-5 h-5 text-emerald-600" />
                Issue Today OPD Queue Token ({formattedDate})
              </h2>
              <button
                onClick={() => setShowTokenModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleIssueToken} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-700 font-bold mb-1">Select Registered Patient *</label>
                <select
                  value={selectedPatientId}
                  onChange={(e) => setSelectedPatientId(e.target.value)}
                  required
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 font-medium focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                >
                  <option value="">-- Choose Patient --</option>
                  {patients.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.patient_id}) - {p.mobile}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Visit Type</label>
                  <select
                    value={visitType}
                    onChange={(e) => setVisitType(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 font-medium focus:outline-none"
                  >
                    <option value="GENERAL_OPD">General OPD</option>
                    <option value="NCD_SCREENING">NCD Screening</option>
                    <option value="MATERNAL_ANC">Maternal ANC</option>
                    <option value="CHILD_IMMUNIZATION">Child Immunization</option>
                    <option value="TELECONSULTATION">Teleconsultation</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-700 font-bold mb-1">Priority Tag</label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 font-medium focus:outline-none"
                  >
                    <option value="NORMAL">Normal / Routine</option>
                    <option value="HIGH">High Priority</option>
                    <option value="EMERGENCY">Emergency 🚨</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Chief Symptoms / Complaint</label>
                <input
                  type="text"
                  placeholder="e.g. Fever, Headache, High Blood Pressure check"
                  value={chiefComplaint}
                  onChange={(e) => setChiefComplaint(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 font-medium focus:outline-none"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowTokenModal(false)}
                  className="px-4 py-2 border border-slate-300 text-slate-700 font-bold rounded-xl hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl shadow-sm"
                >
                  {submitting ? 'Issuing...' : 'Issue Token & Add to Queue'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
