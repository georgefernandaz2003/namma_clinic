import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import type { Patient } from '../types';
import { useAuth } from '../context/AuthContext';
import { 
  ArrowLeft, User, Phone, MapPin, Activity, Clock, 
  FileText, Pill, Share2, Stethoscope, History, Plus,
  ChevronDown, ChevronRight, Filter, RotateCcw, Calendar, UserPlus
} from 'lucide-react';

export const PatientDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { activeFacility } = useAuth();

  const [patient, setPatient] = useState<Patient | null>(null);
  const [timelineEvents, setTimelineEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Quick Issue Token Modal State
  const [showTokenModal, setShowTokenModal] = useState(false);
  const [visitType, setVisitType] = useState('GENERAL_OPD');
  const [priority, setPriority] = useState('NORMAL');
  const [chiefComplaint, setChiefComplaint] = useState('');
  const [submittingToken, setSubmittingToken] = useState(false);

  // Filter States
  const [fromDate, setFromDate] = useState<string>('');
  const [toDate, setToDate] = useState<string>('');
  const [quickFilter, setQuickFilter] = useState<'ALL' | 'TODAY' | '7DAYS' | '30DAYS' | '3MONTHS'>('ALL');
  const [eventTypeFilter, setEventTypeFilter] = useState<string>('ALL');

  // Collapsible Accordion State: { [dateGroupKey]: boolean }
  const [expandedDates, setExpandedDates] = useState<Record<string, boolean>>({});

  const loadPatientData = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const res = await api.get(`patients/${id}/timeline/`);
      setPatient(res.data.patient || null);
      setTimelineEvents(res.data.timeline || []);
    } catch (e) {
      console.error('Failed to load patient detail', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPatientData();
  }, [id]);

  // Handle Quick Date Filter Selection
  const applyQuickFilter = (type: 'ALL' | 'TODAY' | '7DAYS' | '30DAYS' | '3MONTHS') => {
    setQuickFilter(type);
    const now = new Date();
    const formatDate = (d: Date) => d.toISOString().split('T')[0];

    if (type === 'TODAY') {
      const todayStr = formatDate(now);
      setFromDate(todayStr);
      setToDate(todayStr);
    } else if (type === '7DAYS') {
      const past = new Date(now);
      past.setDate(past.getDate() - 6);
      setFromDate(formatDate(past));
      setToDate(formatDate(now));
    } else if (type === '30DAYS') {
      const past = new Date(now);
      past.setDate(past.getDate() - 29);
      setFromDate(formatDate(past));
      setToDate(formatDate(now));
    } else if (type === '3MONTHS') {
      const past = new Date(now);
      past.setMonth(past.getMonth() - 3);
      setFromDate(formatDate(past));
      setToDate(formatDate(now));
    } else {
      setFromDate('');
      setToDate('');
    }
  };

  const handleClearFilters = () => {
    setFromDate('');
    setToDate('');
    setQuickFilter('ALL');
    setEventTypeFilter('ALL');
  };

  // Helper to parse date object safely from event date string
  const parseEventDate = (dateStr: string): Date => {
    if (!dateStr) return new Date(0);
    const normalized = dateStr.replace(' ', 'T');
    const d = new Date(normalized);
    return isNaN(d.getTime()) ? new Date(dateStr) : d;
  };

  // Helper to format time into "07:03 AM" directly from event date string (avoids timezone shifts)
  const formatEventTime = (dateStr: string): string => {
    if (!dateStr || !dateStr.includes(' ')) return '';
    const parts = dateStr.split(' ');
    const timePart = parts[1]; // e.g. "07:03" or "07:03:00"
    if (!timePart) return '';

    const timeComponents = timePart.split(':');
    let hours = parseInt(timeComponents[0], 10);
    let minutes = parseInt(timeComponents[1], 10);

    if (isNaN(hours) || isNaN(minutes)) return timePart;

    const ampm = hours >= 12 ? 'PM' : 'AM';
    const hours12 = hours % 12 || 12;
    const padHours = hours12 < 10 ? `0${hours12}` : `${hours12}`;
    const padMinutes = minutes < 10 ? `0${minutes}` : `${minutes}`;

    return `${padHours}:${padMinutes} ${ampm}`;
  };

  // Dynamically Filtered & Sorted Timeline Events
  const filteredEvents = useMemo(() => {
    return timelineEvents.filter((ev) => {
      // 1. Event Type Filter
      if (eventTypeFilter !== 'ALL') {
        if (eventTypeFilter === 'VISIT' && ev.type !== 'VISIT' && ev.type !== 'TRIAGE') return false;
        if (eventTypeFilter === 'CONSULTATION' && ev.type !== 'CONSULTATION') return false;
        if (eventTypeFilter === 'PRESCRIPTION' && ev.type !== 'PRESCRIPTION') return false;
        if (eventTypeFilter === 'LAB' && ev.type !== 'LAB') return false;
        if (eventTypeFilter === 'REFERRAL' && ev.type !== 'REFERRAL') return false;
        if (eventTypeFilter === 'OTHER' && ['VISIT', 'TRIAGE', 'CONSULTATION', 'PRESCRIPTION', 'LAB', 'REFERRAL'].includes(ev.type)) return false;
      }

      // 2. Date Range Filter
      const evDate = parseEventDate(ev.date);
      if (fromDate) {
        const fDate = new Date(`${fromDate}T00:00:00`);
        if (evDate < fDate) return false;
      }
      if (toDate) {
        const tDate = new Date(`${toDate}T23:59:59.999`);
        if (evDate > tDate) return false;
      }

      return true;
    });
  }, [timelineEvents, fromDate, toDate, eventTypeFilter]);

  // Dynamic Summary Counters
  const summaryCounts = useMemo(() => {
    let visits = 0;
    let diagnoses = 0;
    let prescriptions = 0;
    let labs = 0;
    let referrals = 0;

    filteredEvents.forEach((ev) => {
      if (ev.type === 'VISIT' || ev.type === 'TRIAGE') visits++;
      if (ev.type === 'CONSULTATION') diagnoses++;
      if (ev.type === 'PRESCRIPTION') prescriptions++;
      if (ev.type === 'LAB') labs++;
      if (ev.type === 'REFERRAL') referrals++;
    });

    return { visits, diagnoses, prescriptions, labs, referrals };
  }, [filteredEvents]);

  // Group events by Calendar Date (Sorted Newest Date First, Newest Event Time First)
  const groupedEvents = useMemo(() => {
    const groups: { [dateKey: string]: { displayDate: string; rawDate: Date; dateKey: string; events: any[] } } = {};

    filteredEvents.forEach((ev) => {
      const evDate = parseEventDate(ev.date);
      const dateKey = !isNaN(evDate.getTime()) ? evDate.toISOString().split('T')[0] : (ev.date ? ev.date.split(' ')[0] : '1970-01-01');
      const displayDate = !isNaN(evDate.getTime())
        ? evDate.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
        : ev.date;

      if (!groups[dateKey]) {
        groups[dateKey] = {
          displayDate,
          rawDate: evDate,
          dateKey,
          events: []
        };
      }
      groups[dateKey].events.push(ev);
    });

    // Sort events inside each group by timestamp descending (newest event time first)
    Object.keys(groups).forEach((key) => {
      groups[key].events.sort((a, b) => parseEventDate(b.date).getTime() - parseEventDate(a.date).getTime());
    });

    // Convert to array and sort date groups descending (newest date first)
    return Object.keys(groups)
      .map((key) => groups[key])
      .sort((a, b) => b.rawDate.getTime() - a.rawDate.getTime());
  }, [filteredEvents]);

  const isGroupExpanded = (dateKey: string, index: number) => {
    if (expandedDates[dateKey] !== undefined) {
      return expandedDates[dateKey];
    }
    // Default: latest date (index 0) expanded, older dates collapsed
    return index === 0;
  };

  const toggleDateGroup = (dateKey: string, index: number) => {
    const currentState = isGroupExpanded(dateKey, index);
    setExpandedDates((prev) => ({
      ...prev,
      [dateKey]: !currentState
    }));
  };

  const handleIssueTokenSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!patient || !activeFacility) return;
    setSubmittingToken(true);
    try {
      const res = await api.post('visits/', {
        patient: patient.id,
        facility: activeFacility.id,
        visit_type: visitType,
        priority,
        chief_complaint: chiefComplaint
      });
      const newVisit = res.data;
      alert(`OPD Token #${newVisit.token_details?.token_number || newVisit.id} Issued for ${patient.name}!`);
      setShowTokenModal(false);
      navigate('/queue');
    } catch (e: any) {
      alert(e.response?.data?.error || 'Failed to issue OPD token');
    } finally {
      setSubmittingToken(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-xs text-slate-500">
        Loading comprehensive patient EMR profile...
      </div>
    );
  }

  if (!patient) {
    return (
      <div className="p-12 text-center text-xs text-slate-500 space-y-3">
        <p>Patient record not found.</p>
        <button
          onClick={() => navigate('/patients')}
          className="px-4 py-2 bg-emerald-600 text-white font-bold rounded-xl"
        >
          Back to Patients Directory
        </button>
      </div>
    );
  }

  // Extract latest vitals and active prescriptions for summary cards
  const latestTriage = timelineEvents.find((ev) => ev.type === 'TRIAGE');
  const latestConsultation = timelineEvents.find((ev) => ev.type === 'CONSULTATION');
  const activePrescription = timelineEvents.find((ev) => ev.type === 'PRESCRIPTION');

  return (
    <div className="space-y-6 pb-12">
      {/* Top Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <button
          onClick={() => navigate('/patients')}
          className="flex items-center gap-2 text-xs font-bold text-slate-600 hover:text-slate-900 transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Patients Directory</span>
        </button>

        <button
          onClick={() => setShowTokenModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-sm transition"
        >
          <Plus className="w-4 h-4" />
          <span>Issue OPD Queue Token</span>
        </button>
      </div>

      {/* Patient Identification Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-200 bg-white space-y-4 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-100 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-black text-slate-900">{patient.name}</h1>
              <span className="px-3 py-1 rounded-full text-xs font-black font-mono bg-emerald-100 text-emerald-800 border border-emerald-200">
                {patient.patient_id}
              </span>
            </div>
            <p className="text-xs text-slate-500 font-medium flex items-center gap-2">
              <span>{patient.age} years old</span>
              <span>•</span>
              <span>{patient.gender}</span>
              <span>•</span>
              <span className="font-mono text-slate-700 font-bold">{patient.mobile}</span>
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <span className="px-3 py-1 rounded-lg text-xs font-bold bg-amber-100 text-amber-900 border border-amber-200">
              Vulnerability: {patient.vulnerability_information || 'General BPL'}
            </span>
            <span className="px-3 py-1 rounded-lg text-xs font-bold bg-blue-100 text-blue-900 border border-blue-200 font-mono">
              ABHA: {patient.ABHA_ID_DEMO || 'ABHA-2026-PENDING'}
            </span>
          </div>
        </div>

        {/* Demographics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="flex items-start gap-2 text-slate-700">
            <MapPin className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold block text-slate-900">Residential Address</span>
              <span>{patient.address || 'Address not logged'}</span>
            </div>
          </div>

          <div className="flex items-start gap-2 text-slate-700">
            <User className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold block text-slate-900">Registered Facility</span>
              <span>{patient.facility_name || 'Indiranagar Namma Clinic'}</span>
            </div>
          </div>

          <div className="flex items-start gap-2 text-slate-700">
            <Phone className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold block text-slate-900">Emergency Contact</span>
              <span>{patient.emergency_contact || patient.mobile}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Clinical Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        {/* Card 1: Latest Triage Vitals */}
        <div className="glass-panel p-4 rounded-xl border border-slate-200 bg-white space-y-2">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h3 className="font-bold text-slate-900 flex items-center gap-1.5">
              <Activity className="w-4 h-4 text-rose-600" />
              Latest Triage Vitals
            </h3>
            <span className="text-[10px] text-slate-400 font-mono">{latestTriage?.date || 'Recent'}</span>
          </div>
          {latestTriage ? (
            <p className="text-slate-700 leading-relaxed text-[11px] font-medium">{latestTriage.details}</p>
          ) : (
            <p className="text-slate-400 italic">No triage vitals recorded yet.</p>
          )}
        </div>

        {/* Card 2: Diagnosis & Clinical Notes */}
        <div className="glass-panel p-4 rounded-xl border border-slate-200 bg-white space-y-2">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h3 className="font-bold text-slate-900 flex items-center gap-1.5">
              <Stethoscope className="w-4 h-4 text-indigo-600" />
              Latest Doctor Diagnosis
            </h3>
            <span className="text-[10px] text-slate-400 font-mono">{latestConsultation?.date || 'Recent'}</span>
          </div>
          {latestConsultation ? (
            <p className="text-slate-700 leading-relaxed text-[11px] font-medium">{latestConsultation.details}</p>
          ) : (
            <p className="text-slate-400 italic">No doctor consultation logged yet.</p>
          )}
        </div>

        {/* Card 3: Active Medications */}
        <div className="glass-panel p-4 rounded-xl border border-slate-200 bg-white space-y-2">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h3 className="font-bold text-slate-900 flex items-center gap-1.5">
              <Pill className="w-4 h-4 text-amber-600" />
              Active Prescriptions
            </h3>
            <span className="text-[10px] text-slate-400 font-mono">{activePrescription?.date || 'EDL'}</span>
          </div>
          {activePrescription ? (
            <p className="text-slate-700 leading-relaxed text-[11px] font-medium">{activePrescription.details}</p>
          ) : (
            <p className="text-slate-400 italic">No active prescriptions pending.</p>
          )}
        </div>
      </div>

      {/* Longitudinal EMR Timeline & Encounters Log */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-200 bg-white space-y-5 shadow-xs">
        <div className="border-b border-slate-100 pb-4 space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <History className="w-5 h-5 text-blue-600" />
              Longitudinal EMR Timeline & Encounters Log
            </h2>

            {(fromDate || toDate || eventTypeFilter !== 'ALL' || quickFilter !== 'ALL') && (
              <button
                onClick={handleClearFilters}
                className="flex items-center gap-1.5 text-xs text-rose-600 font-bold hover:text-rose-700 transition"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Clear Filters</span>
              </button>
            )}
          </div>

          {/* 1. Date & Event Filters Control Bar */}
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3 text-xs">
            {/* Custom Date Range & Event Type Inputs */}
            <div className="flex flex-wrap items-end gap-3">
              <div className="space-y-1">
                <label className="block text-[11px] font-bold text-slate-700">From Date</label>
                <input
                  type="date"
                  value={fromDate}
                  onChange={(e) => {
                    setFromDate(e.target.value);
                    setQuickFilter('ALL');
                  }}
                  className="px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-blue-600 font-medium"
                />
              </div>

              <div className="space-y-1">
                <label className="block text-[11px] font-bold text-slate-700">To Date</label>
                <input
                  type="date"
                  value={toDate}
                  onChange={(e) => {
                    setToDate(e.target.value);
                    setQuickFilter('ALL');
                  }}
                  className="px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-blue-600 font-medium"
                />
              </div>

              <div className="space-y-1">
                <label className="block text-[11px] font-bold text-slate-700">Event Type</label>
                <select
                  value={eventTypeFilter}
                  onChange={(e) => setEventTypeFilter(e.target.value)}
                  className="px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none font-medium min-w-[160px]"
                >
                  <option value="ALL">All Events</option>
                  <option value="VISIT">Clinic Visits</option>
                  <option value="TRIAGE">Nurse Triage</option>
                  <option value="CONSULTATION">Diagnoses</option>
                  <option value="PRESCRIPTION">Prescriptions</option>
                  <option value="LAB">Lab Investigations</option>
                  <option value="REFERRAL">Referrals</option>
                  <option value="OTHER">Other Events</option>
                </select>
              </div>

              <button
                onClick={() => {}}
                className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white font-bold rounded-lg flex items-center gap-1 shadow-xs"
              >
                <Filter className="w-3.5 h-3.5" />
                <span>Apply Filter</span>
              </button>
            </div>

            {/* Quick Date Range Buttons */}
            <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-slate-200">
              <span className="text-[11px] font-bold text-slate-500 mr-2 flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                Quick Range:
              </span>
              {[
                { label: 'Today', key: 'TODAY' },
                { label: 'Last 7 Days', key: '7DAYS' },
                { label: 'Last 30 Days', key: '30DAYS' },
                { label: 'Last 3 Months', key: '3MONTHS' },
                { label: 'All History', key: 'ALL' }
              ].map((btn) => (
                <button
                  key={btn.key}
                  onClick={() => applyQuickFilter(btn.key as any)}
                  className={`px-2.5 py-1 rounded-lg font-bold text-[11px] transition ${
                    quickFilter === btn.key && !fromDate && !toDate
                      ? 'bg-blue-600 text-white shadow-xs'
                      : quickFilter === btn.key
                      ? 'bg-blue-600 text-white shadow-xs'
                      : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100'
                  }`}
                >
                  {btn.label}
                </button>
              ))}
            </div>
          </div>

          {/* 2. History Summary Chips */}
          <div className="bg-blue-50/60 p-3 rounded-xl border border-blue-100 flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="font-bold text-blue-900 flex items-center gap-2">
              <span>History Summary</span>
              <span className="text-[10px] text-blue-600 font-mono font-medium">({filteredEvents.length} Records)</span>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-[11px]">
              <span className="font-semibold text-slate-800">
                <strong className="text-blue-700">{summaryCounts.visits}</strong> Clinic Visits
              </span>
              <span>•</span>
              <span className="font-semibold text-slate-800">
                <strong className="text-indigo-700">{summaryCounts.diagnoses}</strong> Diagnoses
              </span>
              <span>•</span>
              <span className="font-semibold text-slate-800">
                <strong className="text-amber-700">{summaryCounts.prescriptions}</strong> Prescriptions
              </span>
              <span>•</span>
              <span className="font-semibold text-slate-800">
                <strong className="text-teal-700">{summaryCounts.labs}</strong> Lab Results
              </span>
              <span>•</span>
              <span className="font-semibold text-slate-800">
                <strong className="text-rose-700">{summaryCounts.referrals}</strong> Referrals
              </span>
            </div>
          </div>
        </div>

        {/* 3. Grouped History Timeline List & Empty State */}
        {groupedEvents.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <p className="text-xs text-slate-500 font-medium">No medical history found for the selected date range.</p>
            <button
              onClick={handleClearFilters}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl inline-flex items-center gap-1.5 transition"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Clear Filters</span>
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            {groupedEvents.map((group, groupIdx) => {
              const expanded = isGroupExpanded(group.dateKey, groupIdx);

              return (
                <div key={group.dateKey} className="space-y-3">
                  {/* Collapsible Date Header */}
                  <div
                    onClick={() => toggleDateGroup(group.dateKey, groupIdx)}
                    className="flex items-center justify-between p-3 rounded-xl bg-slate-100 hover:bg-slate-200/80 cursor-pointer transition border border-slate-200 select-none"
                  >
                    <div className="flex items-center gap-2 font-black text-slate-900 text-xs">
                      {expanded ? (
                        <ChevronDown className="w-4 h-4 text-blue-600" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-slate-400" />
                      )}
                      <span>{group.displayDate}</span>
                    </div>

                    <span className="px-2.5 py-0.5 rounded-full bg-white text-slate-700 text-[11px] font-mono font-bold border border-slate-200">
                      {group.events.length} {group.events.length === 1 ? 'Event' : 'Events'}
                    </span>
                  </div>

                  {/* Date Group Events List */}
                  {expanded && (
                    <div className="relative pl-6 space-y-4 border-l-2 border-blue-500 ml-4 py-1 text-xs">
                      {group.events.map((ev, idx) => {
                        const timeStr = formatEventTime(ev.date) || (ev.date.includes(' ') ? ev.date.split(' ')[1] : '');

                        return (
                          <div key={idx} className="relative group">
                            <div className="absolute -left-[31px] top-1.5 p-1 bg-white border-2 border-blue-600 rounded-full text-blue-600 shadow-xs">
                              {ev.type === 'REGISTRATION' && <UserPlus className="w-3.5 h-3.5" />}
                              {ev.type === 'VISIT' && <Clock className="w-3.5 h-3.5 text-blue-600" />}
                              {ev.type === 'TRIAGE' && <Activity className="w-3.5 h-3.5 text-rose-600" />}
                              {ev.type === 'CONSULTATION' && <Stethoscope className="w-3.5 h-3.5 text-indigo-600" />}
                              {ev.type === 'PRESCRIPTION' && <Pill className="w-3.5 h-3.5 text-amber-600" />}
                              {ev.type === 'LAB' && <FileText className="w-3.5 h-3.5 text-teal-600" />}
                              {ev.type === 'REFERRAL' && <Share2 className="w-3.5 h-3.5 text-rose-600" />}
                            </div>

                            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1.5 hover:bg-white transition shadow-2xs">
                              <div className="flex justify-between items-center">
                                <div className="flex items-center gap-2">
                                  {timeStr && (
                                    <span className="font-mono text-[11px] font-bold text-blue-700 bg-blue-100/80 border border-blue-200 px-2 py-0.5 rounded-md shadow-2xs">
                                      {timeStr}
                                    </span>
                                  )}
                                  <span className="font-bold text-slate-900 text-xs">
                                    {ev.title}
                                  </span>
                                </div>
                                {!timeStr && (
                                  <span className="font-mono text-[10px] text-slate-400">{ev.date}</span>
                                )}
                              </div>
                              <p className="text-[11px] text-slate-700 leading-relaxed font-medium">{ev.details}</p>
                              <span className="text-[10px] text-slate-500 font-semibold block">{ev.facility}</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Token Modal */}
      {showTokenModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 border border-slate-200 w-full max-w-lg space-y-4 shadow-xl">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Clock className="w-5 h-5 text-emerald-600" />
                  Issue OPD Token for {patient.name}
                </h2>
                <p className="text-xs text-slate-500 font-mono mt-0.5">
                  ID: {patient.patient_id} • Mobile: {patient.mobile}
                </p>
              </div>
            </div>

            <form onSubmit={handleIssueTokenSubmit} className="space-y-4 text-xs">
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
                    <option value="MATERNAL">Maternal ANC Care</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Chief Symptoms / Complaint</label>
                <input
                  type="text"
                  placeholder="e.g. Chest pain, Fever, Routine BP check"
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
                  disabled={submittingToken}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl shadow-sm"
                >
                  {submittingToken ? 'Issuing...' : 'Issue Token & Add to Queue'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
