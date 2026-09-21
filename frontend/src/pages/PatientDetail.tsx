import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import type { Patient, PatientDocument } from '../types';
import { useAuth } from '../context/AuthContext';
import { 
  ArrowLeft, User, Phone, MapPin, Activity, Clock, 
  FileText, Pill, Share2, Stethoscope, History, Plus,
  ChevronDown, ChevronRight, Filter, RotateCcw, Calendar, UserPlus,
  Upload, Download, Eye, Trash2, File, FileCheck, Shield,
  CheckCircle, AlertTriangle, X, Search, Building, FolderOpen,
  FileSpreadsheet
} from 'lucide-react';

export const PatientDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user, activeFacility } = useAuth();
  const isDistrictOfficer = user?.role === 'DISTRICT_OFFICER';

  // Navigation Tab State
  const [activeTab, setActiveTab] = useState<'OVERVIEW' | 'VISITS' | 'MEDICAL_RECORDS' | 'LAB_REPORTS' | 'PRESCRIPTIONS' | 'DOCUMENTS'>('OVERVIEW');

  // Core Data States
  const [patient, setPatient] = useState<Patient | null>(null);
  const [timelineEvents, setTimelineEvents] = useState<any[]>([]);
  const [recordsData, setRecordsData] = useState<{
    visits: any[];
    medical_records: any[];
    lab_reports: any[];
    prescriptions: any[];
    documents: PatientDocument[];
  }>({
    visits: [],
    medical_records: [],
    lab_reports: [],
    prescriptions: [],
    documents: []
  });

  const [loading, setLoading] = useState(true);

  // Quick Issue Token Modal State
  const [showTokenModal, setShowTokenModal] = useState(false);
  const [visitType, setVisitType] = useState('GENERAL_OPD');
  const [priority, setPriority] = useState('NORMAL');
  const [chiefComplaint, setChiefComplaint] = useState('');
  const [submittingToken, setSubmittingToken] = useState(false);

  // Document Upload Modal State
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadType, setUploadType] = useState('MEDICAL_RECORD');
  const [uploadDescription, setUploadDescription] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Document Filter & Search State
  const [docCategoryFilter, setDocCategoryFilter] = useState<string>('ALL');
  const [docSearchQuery, setDocSearchQuery] = useState<string>('');

  // Document Preview Modal State
  const [previewDoc, setPreviewDoc] = useState<PatientDocument | null>(null);
  const [downloadingDocId, setDownloadingDocId] = useState<number | null>(null);

  // Overview EMR Filter States
  const [fromDate, setFromDate] = useState<string>('');
  const [toDate, setToDate] = useState<string>('');
  const [quickFilter, setQuickFilter] = useState<'ALL' | 'TODAY' | '7DAYS' | '30DAYS' | '3MONTHS'>('ALL');
  const [eventTypeFilter, setEventTypeFilter] = useState<string>('ALL');
  const [expandedDates, setExpandedDates] = useState<Record<string, boolean>>({});

  const fetchPatientData = async () => {
    if (!id) return;
    setLoading(true);
    try {
      // Parallel fetch of EMR Timeline and Structured Records
      const [timelineRes, recordsRes] = await Promise.all([
        api.get(`patients/${id}/timeline/`),
        api.get(`patients/${id}/records/`)
      ]);

      setPatient(timelineRes.data.patient || recordsRes.data.patient || null);
      setTimelineEvents(timelineRes.data.timeline || []);
      setRecordsData({
        visits: recordsRes.data.visits || [],
        medical_records: recordsRes.data.medical_records || [],
        lab_reports: recordsRes.data.lab_reports || [],
        prescriptions: recordsRes.data.prescriptions || [],
        documents: recordsRes.data.documents || []
      });
    } catch (e) {
      console.error('Failed to load patient records', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPatientData();
  }, [id]);

  // Handle Document Upload Submit
  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!patient || !uploadFile) {
      setUploadError('Please select a valid document file to upload.');
      return;
    }

    if (!uploadTitle.trim()) {
      setUploadError('Please provide a document title.');
      return;
    }

    // Client-side file size validation (15 MB max)
    const MAX_SIZE = 15 * 1024 * 1024;
    if (uploadFile.size > MAX_SIZE) {
      setUploadError('File size exceeds the 15 MB limit. Please select a smaller file.');
      return;
    }

    setUploading(true);
    setUploadError(null);

    try {
      const formData = new FormData();
      formData.append('title', uploadTitle.trim());
      formData.append('document_type', uploadType);
      formData.append('description', uploadDescription.trim());
      formData.append('file', uploadFile);

      await api.post(`patients/${patient.id}/documents/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      alert(`Document '${uploadTitle}' uploaded successfully!`);
      setShowUploadModal(false);
      setUploadTitle('');
      setUploadType('MEDICAL_RECORD');
      setUploadDescription('');
      setUploadFile(null);
      
      // Refresh patient data
      fetchPatientData();
    } catch (err: any) {
      console.error('Document upload error', err);
      let msg = 'Failed to upload document.';
      if (err.response?.data?.error) {
        msg = err.response.data.error;
      } else if (err.response?.data && typeof err.response.data === 'object') {
        msg = Object.entries(err.response.data)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
          .join('\n');
      }
      setUploadError(msg);
    } finally {
      setUploading(false);
    }
  };

  // Secure Document Download
  const handleDownloadDocument = async (doc: PatientDocument) => {
    if (!patient) return;
    setDownloadingDocId(doc.id);
    try {
      const res = await api.get(`patients/${patient.id}/documents/${doc.id}/download/`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', doc.file_name);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Failed to download document. You may not have required permissions.');
    } finally {
      setDownloadingDocId(null);
    }
  };

  // Delete Document
  const handleDeleteDocument = async (docId: number, docTitle: string) => {
    if (!patient) return;
    if (!window.confirm(`Are you sure you want to delete the document '${docTitle}'? This action cannot be undone.`)) return;

    try {
      await api.delete(`patients/${patient.id}/documents/${docId}/`);
      alert('Document deleted successfully.');
      fetchPatientData();
    } catch (err: any) {
      alert(err.response?.data?.error || 'Failed to delete document.');
    }
  };

  // Quick Date Filter Handler
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

  const parseEventDate = (dateStr: string): Date => {
    if (!dateStr) return new Date(0);
    const normalized = dateStr.replace(' ', 'T');
    const d = new Date(normalized);
    return isNaN(d.getTime()) ? new Date(dateStr) : d;
  };

  const formatEventTime = (dateStr: string): string => {
    if (!dateStr || !dateStr.includes(' ')) return '';
    const parts = dateStr.split(' ');
    const timePart = parts[1];
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

  // Filtered EMR Timeline
  const filteredTimelineEvents = useMemo(() => {
    return timelineEvents.filter((ev) => {
      if (eventTypeFilter !== 'ALL') {
        if (eventTypeFilter === 'VISIT' && ev.type !== 'VISIT' && ev.type !== 'TRIAGE') return false;
        if (eventTypeFilter === 'CONSULTATION' && ev.type !== 'CONSULTATION') return false;
        if (eventTypeFilter === 'PRESCRIPTION' && ev.type !== 'PRESCRIPTION') return false;
        if (eventTypeFilter === 'LAB' && ev.type !== 'LAB') return false;
        if (eventTypeFilter === 'DOCUMENT' && ev.type !== 'DOCUMENT') return false;
        if (eventTypeFilter === 'REFERRAL' && ev.type !== 'REFERRAL') return false;
        if (eventTypeFilter === 'OTHER' && ['VISIT', 'TRIAGE', 'CONSULTATION', 'PRESCRIPTION', 'LAB', 'DOCUMENT', 'REFERRAL'].includes(ev.type)) return false;
      }
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

  // Group timeline events by date
  const groupedTimelineEvents = useMemo(() => {
    const groups: { [dateKey: string]: { displayDate: string; rawDate: Date; dateKey: string; events: any[] } } = {};
    filteredTimelineEvents.forEach((ev) => {
      const evDate = parseEventDate(ev.date);
      const dateKey = !isNaN(evDate.getTime()) ? evDate.toISOString().split('T')[0] : (ev.date ? ev.date.split(' ')[0] : '1970-01-01');
      const displayDate = !isNaN(evDate.getTime())
        ? evDate.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
        : ev.date;

      if (!groups[dateKey]) {
        groups[dateKey] = { displayDate, rawDate: evDate, dateKey, events: [] };
      }
      groups[dateKey].events.push(ev);
    });

    Object.keys(groups).forEach((key) => {
      groups[key].events.sort((a, b) => parseEventDate(b.date).getTime() - parseEventDate(a.date).getTime());
    });

    return Object.keys(groups)
      .map((key) => groups[key])
      .sort((a, b) => b.rawDate.getTime() - a.rawDate.getTime());
  }, [filteredTimelineEvents]);

  // Filtered Documents
  const filteredDocuments = useMemo(() => {
    return recordsData.documents.filter((doc) => {
      // Category filter
      if (docCategoryFilter !== 'ALL' && doc.document_type !== docCategoryFilter) {
        return false;
      }
      // Search query filter
      if (docSearchQuery.trim()) {
        const q = docSearchQuery.toLowerCase().trim();
        const titleMatch = doc.title?.toLowerCase().includes(q);
        const fileNameMatch = doc.file_name?.toLowerCase().includes(q);
        const descMatch = doc.description?.toLowerCase().includes(q);
        const uploaderMatch = doc.uploaded_by_name?.toLowerCase().includes(q);
        const facilityMatch = doc.facility_name?.toLowerCase().includes(q);
        if (!titleMatch && !fileNameMatch && !descMatch && !uploaderMatch && !facilityMatch) {
          return false;
        }
      }
      return true;
    });
  }, [recordsData.documents, docCategoryFilter, docSearchQuery]);

  // Issue Token Submit
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

  const isGroupExpanded = (dateKey: string, index: number) => {
    if (expandedDates[dateKey] !== undefined) return expandedDates[dateKey];
    return index === 0;
  };

  const toggleDateGroup = (dateKey: string, index: number) => {
    const currentState = isGroupExpanded(dateKey, index);
    setExpandedDates((prev) => ({ ...prev, [dateKey]: !currentState }));
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-xs text-slate-500 font-medium space-y-2">
        <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
        <p>Loading patient medical EMR records & document vault...</p>
      </div>
    );
  }

  if (!patient) {
    return (
      <div className="p-12 text-center text-xs text-slate-500 space-y-3">
        <p>Patient record not found or access restricted.</p>
        <button
          onClick={() => navigate('/patients')}
          className="px-4 py-2 bg-emerald-600 text-white font-bold rounded-xl hover:bg-emerald-500 transition"
        >
          Back to Patients Directory
        </button>
      </div>
    );
  }

  const latestTriage = timelineEvents.find((ev) => ev.type === 'TRIAGE');
  const latestConsultation = timelineEvents.find((ev) => ev.type === 'CONSULTATION');
  const activePrescription = timelineEvents.find((ev) => ev.type === 'PRESCRIPTION');

  return (
    <div className="space-y-6 pb-12">
      {/* Top Bar Navigation & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <button
          onClick={() => navigate('/patients')}
          className="flex items-center gap-2 text-xs font-bold text-slate-600 hover:text-slate-900 transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Patients Directory</span>
        </button>

        <div className="flex flex-wrap items-center gap-2">
          {!isDistrictOfficer && (
            <button
              onClick={() => setShowUploadModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs rounded-xl shadow-xs transition"
            >
              <Upload className="w-4 h-4 text-emerald-400" />
              <span>Upload Medical Document</span>
            </button>
          )}

          <button
            onClick={() => setShowTokenModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs transition"
          >
            <Plus className="w-4 h-4" />
            <span>Issue OPD Queue Token</span>
          </button>
        </div>
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
              <span>{patient.facility_name || 'Namma Clinic'}</span>
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

      {/* 6 Tabs EMR Navigation Bar */}
      <div className="bg-slate-100 p-1.5 rounded-2xl border border-slate-200 flex flex-wrap gap-1 text-xs font-bold">
        <button
          onClick={() => setActiveTab('OVERVIEW')}
          className={`flex-1 min-w-[120px] py-2.5 px-3 rounded-xl flex items-center justify-center gap-2 transition ${
            activeTab === 'OVERVIEW'
              ? 'bg-white text-blue-700 shadow-sm border border-slate-200 font-black'
              : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
          }`}
        >
          <History className="w-4 h-4 text-blue-600" />
          <span>Overview</span>
        </button>

        <button
          onClick={() => setActiveTab('VISITS')}
          className={`flex-1 min-w-[120px] py-2.5 px-3 rounded-xl flex items-center justify-center gap-2 transition ${
            activeTab === 'VISITS'
              ? 'bg-white text-blue-700 shadow-sm border border-slate-200 font-black'
              : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
          }`}
        >
          <Clock className="w-4 h-4 text-emerald-600" />
          <span>Visits ({recordsData.visits.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('MEDICAL_RECORDS')}
          className={`flex-1 min-w-[140px] py-2.5 px-3 rounded-xl flex items-center justify-center gap-2 transition ${
            activeTab === 'MEDICAL_RECORDS'
              ? 'bg-white text-blue-700 shadow-sm border border-slate-200 font-black'
              : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
          }`}
        >
          <Stethoscope className="w-4 h-4 text-indigo-600" />
          <span>Medical Records ({recordsData.medical_records.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('LAB_REPORTS')}
          className={`flex-1 min-w-[130px] py-2.5 px-3 rounded-xl flex items-center justify-center gap-2 transition ${
            activeTab === 'LAB_REPORTS'
              ? 'bg-white text-blue-700 shadow-sm border border-slate-200 font-black'
              : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
          }`}
        >
          <Activity className="w-4 h-4 text-teal-600" />
          <span>Lab Reports ({recordsData.lab_reports.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('PRESCRIPTIONS')}
          className={`flex-1 min-w-[130px] py-2.5 px-3 rounded-xl flex items-center justify-center gap-2 transition ${
            activeTab === 'PRESCRIPTIONS'
              ? 'bg-white text-blue-700 shadow-sm border border-slate-200 font-black'
              : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
          }`}
        >
          <Pill className="w-4 h-4 text-amber-600" />
          <span>Prescriptions ({recordsData.prescriptions.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('DOCUMENTS')}
          className={`flex-1 min-w-[130px] py-2.5 px-3 rounded-xl flex items-center justify-center gap-2 transition ${
            activeTab === 'DOCUMENTS'
              ? 'bg-white text-blue-700 shadow-sm border border-slate-200 font-black'
              : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
          }`}
        >
          <FolderOpen className="w-4 h-4 text-purple-600" />
          <span>Documents ({recordsData.documents.length})</span>
        </button>
      </div>

      {/* TAB 1: OVERVIEW */}
      {activeTab === 'OVERVIEW' && (
        <div className="space-y-6">
          {/* Clinical Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
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

          {/* Longitudinal Timeline Log */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-200 bg-white space-y-5 shadow-xs">
            <div className="border-b border-slate-100 pb-4 space-y-4">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <History className="w-5 h-5 text-blue-600" />
                  Longitudinal EMR Timeline Log
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

              {/* Date & Event Filters Control Bar */}
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3 text-xs">
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
                      className="px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-slate-900 font-medium"
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
                      className="px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-slate-900 font-medium"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="block text-[11px] font-bold text-slate-700">Event Type</label>
                    <select
                      value={eventTypeFilter}
                      onChange={(e) => setEventTypeFilter(e.target.value)}
                      className="px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-slate-900 font-medium min-w-[160px]"
                    >
                      <option value="ALL">All Events</option>
                      <option value="VISIT">Clinic Visits</option>
                      <option value="TRIAGE">Nurse Triage</option>
                      <option value="CONSULTATION">Diagnoses</option>
                      <option value="PRESCRIPTION">Prescriptions</option>
                      <option value="LAB">Lab Investigations</option>
                      <option value="DOCUMENT">Uploaded Documents</option>
                      <option value="REFERRAL">Referrals</option>
                      <option value="OTHER">Other Events</option>
                    </select>
                  </div>
                </div>

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
                        quickFilter === btn.key
                          ? 'bg-blue-600 text-white shadow-xs'
                          : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100'
                      }`}
                    >
                      {btn.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {groupedTimelineEvents.length === 0 ? (
              <div className="p-12 text-center text-xs text-slate-500">
                No medical events found matching the criteria.
              </div>
            ) : (
              <div className="space-y-6">
                {groupedTimelineEvents.map((group, groupIdx) => {
                  const expanded = isGroupExpanded(group.dateKey, groupIdx);
                  return (
                    <div key={group.dateKey} className="space-y-3">
                      <div
                        onClick={() => toggleDateGroup(group.dateKey, groupIdx)}
                        className="flex items-center justify-between p-3 rounded-xl bg-slate-100 hover:bg-slate-200/80 cursor-pointer transition border border-slate-200 select-none"
                      >
                        <div className="flex items-center gap-2 font-black text-slate-900 text-xs">
                          {expanded ? <ChevronDown className="w-4 h-4 text-blue-600" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
                          <span>{group.displayDate}</span>
                        </div>
                        <span className="px-2.5 py-0.5 rounded-full bg-white text-slate-700 text-[11px] font-mono font-bold border border-slate-200">
                          {group.events.length} {group.events.length === 1 ? 'Event' : 'Events'}
                        </span>
                      </div>

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
                                  {ev.type === 'DOCUMENT' && <FolderOpen className="w-3.5 h-3.5 text-purple-600" />}
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
                                      <span className="font-bold text-slate-900 text-xs">{ev.title}</span>
                                    </div>
                                    {!timeStr && <span className="font-mono text-[10px] text-slate-400">{ev.date}</span>}
                                  </div>
                                  <p className="text-[11px] text-slate-700 leading-relaxed font-medium">{ev.details}</p>
                                  <div className="flex justify-between items-center pt-1">
                                    <span className="text-[10px] text-slate-500 font-semibold">{ev.facility}</span>
                                    {ev.document_id && (
                                      <button
                                        onClick={() => {
                                          const docObj = recordsData.documents.find(d => d.id === ev.document_id);
                                          if (docObj) handleDownloadDocument(docObj);
                                        }}
                                        className="text-[10px] font-bold text-purple-700 hover:text-purple-900 flex items-center gap-1"
                                      >
                                        <Download className="w-3 h-3" /> Download Document
                                      </button>
                                    )}
                                  </div>
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
        </div>
      )}

      {/* TAB 2: VISITS */}
      {activeTab === 'VISITS' && (
        <div className="glass-panel p-6 rounded-2xl border border-slate-200 bg-white space-y-4 shadow-xs">
          <div className="flex justify-between items-center border-b border-slate-100 pb-3">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Clock className="w-5 h-5 text-emerald-600" />
              OPD Clinic Visits History
            </h2>
            <span className="text-xs text-slate-500 font-mono font-bold">
              Total Visits: {recordsData.visits.length}
            </span>
          </div>

          {recordsData.visits.length === 0 ? (
            <div className="p-12 text-center text-xs text-slate-500">No OPD clinic visits logged for this patient.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-50 text-slate-700 border-b border-slate-200 font-bold">
                    <th className="p-3">Visit Date / Time</th>
                    <th className="p-3">Visit ID</th>
                    <th className="p-3">OPD Token #</th>
                    <th className="p-3">Healthcare Facility</th>
                    <th className="p-3">Visit Category</th>
                    <th className="p-3">Priority Tag</th>
                    <th className="p-3">Chief Symptoms</th>
                    <th className="p-3">Queue Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {recordsData.visits.map((v) => (
                    <tr key={v.id} className="hover:bg-slate-50/80 font-medium">
                      <td className="p-3 font-mono text-slate-900 font-bold">{v.visit_date}</td>
                      <td className="p-3 font-mono text-emerald-700 font-bold">{v.visit_id}</td>
                      <td className="p-3 font-mono font-black text-blue-700">
                        {v.token_number ? `#${v.token_number}` : '-'}
                      </td>
                      <td className="p-3 text-slate-900 font-semibold">{v.facility_name}</td>
                      <td className="p-3 text-slate-700">{v.visit_type?.replace('_', ' ')}</td>
                      <td className="p-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          v.priority === 'EMERGENCY' ? 'bg-rose-100 text-rose-800 border border-rose-300' :
                          v.priority === 'HIGH' ? 'bg-amber-100 text-amber-800 border border-amber-300' :
                          'bg-slate-100 text-slate-700 border border-slate-200'
                        }`}>
                          {v.priority}
                        </span>
                      </td>
                      <td className="p-3 text-slate-800">{v.chief_complaint || 'Routine OPD'}</td>
                      <td className="p-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-200">
                          {v.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: MEDICAL RECORDS (CONSULTATIONS) */}
      {activeTab === 'MEDICAL_RECORDS' && (
        <div className="glass-panel p-6 rounded-2xl border border-slate-200 bg-white space-y-4 shadow-xs">
          <div className="flex justify-between items-center border-b border-slate-100 pb-3">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Stethoscope className="w-5 h-5 text-indigo-600" />
              Doctor EMR Consultations & Clinical Diagnoses
            </h2>
            <span className="text-xs text-slate-500 font-mono font-bold">
              Total EMR Notes: {recordsData.medical_records.length}
            </span>
          </div>

          {recordsData.medical_records.length === 0 ? (
            <div className="p-12 text-center text-xs text-slate-500">No doctor consultations recorded yet.</div>
          ) : (
            <div className="space-y-4">
              {recordsData.medical_records.map((c) => (
                <div key={c.id} className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-200 pb-2 gap-2 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-blue-700 bg-blue-100 px-2.5 py-0.5 rounded-md border border-blue-200">
                        {c.created_at}
                      </span>
                      <span className="font-bold text-slate-900">{c.facility_name}</span>
                    </div>
                    <div className="text-slate-600">
                      Attending Clinician: <strong className="text-slate-900">{c.doctor_name}</strong>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="font-bold text-slate-900 block mb-1">Chief Complaint</span>
                      <p className="text-slate-700 bg-white p-2.5 rounded-lg border border-slate-200 font-medium">{c.chief_complaint}</p>
                    </div>

                    <div>
                      <span className="font-bold text-slate-900 block mb-1">Diagnosis (ICD-11 / SNOMED)</span>
                      <div className="bg-indigo-50/70 p-2.5 rounded-lg border border-indigo-200 text-indigo-950 font-bold flex items-center justify-between">
                        <span>{c.diagnosis_name}</span>
                        <span className="font-mono text-[10px] bg-indigo-200 text-indigo-900 px-2 py-0.5 rounded">{c.diagnosis_code}</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-1 text-xs">
                    <span className="font-bold text-slate-900 block">Clinical Assessment & Treatment Plan</span>
                    <p className="text-slate-700 bg-white p-3 rounded-xl border border-slate-200 leading-relaxed font-medium">
                      {c.clinical_assessment || c.treatment_plan || c.clinical_notes}
                    </p>
                  </div>

                  {c.follow_up_date && (
                    <div className="text-xs font-bold text-amber-800 bg-amber-50 p-2 rounded-lg border border-amber-200 inline-block">
                      Follow-up Advised: {c.follow_up_date}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 4: LAB REPORTS */}
      {activeTab === 'LAB_REPORTS' && (
        <div className="glass-panel p-6 rounded-2xl border border-slate-200 bg-white space-y-4 shadow-xs">
          <div className="flex justify-between items-center border-b border-slate-100 pb-3">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Activity className="w-5 h-5 text-teal-600" />
              Laboratory Tests & Diagnostic Investigation Reports
            </h2>
            <span className="text-xs text-slate-500 font-mono font-bold">
              Total Tests: {recordsData.lab_reports.length}
            </span>
          </div>

          {recordsData.lab_reports.length === 0 ? (
            <div className="p-12 text-center text-xs text-slate-500">No laboratory test orders recorded.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-50 text-slate-700 border-b border-slate-200 font-bold">
                    <th className="p-3">Order Date</th>
                    <th className="p-3">Order ID</th>
                    <th className="p-3">Test Investigation</th>
                    <th className="p-3">Facility</th>
                    <th className="p-3">Status</th>
                    <th className="p-3">Lab Result Value</th>
                    <th className="p-3">Interpretation Flag</th>
                    <th className="p-3">Verified By</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {recordsData.lab_reports.map((lo) => (
                    <tr key={lo.id} className="hover:bg-slate-50/80 font-medium">
                      <td className="p-3 font-mono text-slate-900 font-bold">{lo.order_date}</td>
                      <td className="p-3 font-mono text-teal-700 font-bold">{lo.order_id}</td>
                      <td className="p-3">
                        <span className="font-bold text-slate-900 block">{lo.test_name}</span>
                        <span className="font-mono text-[10px] text-slate-500">{lo.test_code}</span>
                      </td>
                      <td className="p-3 text-slate-800">{lo.facility_name}</td>
                      <td className="p-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          lo.status === 'VERIFIED' ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' :
                          lo.status === 'SAMPLE_COLLECTED' ? 'bg-blue-100 text-blue-800 border border-blue-200' :
                          'bg-amber-100 text-amber-800 border border-amber-200'
                        }`}>
                          {lo.status}
                        </span>
                      </td>
                      <td className="p-3 font-mono font-bold text-slate-900">
                        {lo.result_value ? `${lo.result_value} ${lo.unit || ''}` : <span className="text-slate-400 italic">Pending Result</span>}
                      </td>
                      <td className="p-3">
                        {lo.interpretation_flag ? (
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            lo.interpretation_flag === 'CRITICAL' ? 'bg-rose-600 text-white animate-pulse' :
                            lo.interpretation_flag === 'HIGH' ? 'bg-rose-100 text-rose-800 border border-rose-300' :
                            lo.interpretation_flag === 'LOW' ? 'bg-amber-100 text-amber-800 border border-amber-300' :
                            'bg-emerald-100 text-emerald-800 border border-emerald-200'
                          }`}>
                            {lo.interpretation_flag}
                          </span>
                        ) : '-'}
                      </td>
                      <td className="p-3 text-slate-600 text-[11px]">
                        {lo.verified_by ? (
                          <span>{lo.verified_by}<br/><span className="font-mono text-[10px] text-slate-400">{lo.verified_at}</span></span>
                        ) : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB 5: PRESCRIPTIONS */}
      {activeTab === 'PRESCRIPTIONS' && (
        <div className="glass-panel p-6 rounded-2xl border border-slate-200 bg-white space-y-4 shadow-xs">
          <div className="flex justify-between items-center border-b border-slate-100 pb-3">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Pill className="w-5 h-5 text-amber-600" />
              Medication Prescriptions & Essential Drug Dispensations
            </h2>
            <span className="text-xs text-slate-500 font-mono font-bold">
              Total Prescriptions: {recordsData.prescriptions.length}
            </span>
          </div>

          {recordsData.prescriptions.length === 0 ? (
            <div className="p-12 text-center text-xs text-slate-500">No prescriptions recorded.</div>
          ) : (
            <div className="space-y-4">
              {recordsData.prescriptions.map((p) => (
                <div key={p.id} className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                  <div className="flex justify-between items-center border-b border-slate-200 pb-2 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-amber-800 bg-amber-100 px-2.5 py-0.5 rounded-md border border-amber-200">
                        {p.date}
                      </span>
                      <span className="font-bold text-slate-900">{p.facility_name}</span>
                    </div>
                    <div className="text-slate-600">
                      Prescribing Doctor: <strong className="text-slate-900">{p.doctor_name}</strong>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="text-slate-500 font-bold border-b border-slate-200">
                          <th className="pb-2">Essential Medicine Name</th>
                          <th className="pb-2">Dosage Regimen</th>
                          <th className="pb-2">Frequency</th>
                          <th className="pb-2">Duration</th>
                          <th className="pb-2">Qty Prescribed</th>
                          <th className="pb-2">Pharmacy Dispense</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200">
                        {p.items?.map((item: any) => (
                          <tr key={item.id} className="font-medium">
                            <td className="py-2 font-bold text-slate-900">{item.medicine_name}</td>
                            <td className="py-2 text-slate-700">{item.dosage}</td>
                            <td className="py-2 text-slate-700">{item.frequency}</td>
                            <td className="py-2 text-slate-700">{item.duration_days} Days</td>
                            <td className="py-2 font-mono font-bold text-slate-900">{item.quantity} Units</td>
                            <td className="py-2">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                item.status === 'DISPENSED'
                                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                                  : 'bg-amber-100 text-amber-800 border border-amber-200'
                              }`}>
                                {item.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 6: DOCUMENTS (PATIENT DOCUMENT VAULT) */}
      {activeTab === 'DOCUMENTS' && (
        <div className="space-y-5">
          {/* Documents Header & Controls Bar */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-200 bg-white space-y-4 shadow-xs">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4">
              <div>
                <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <FolderOpen className="w-5 h-5 text-purple-600" />
                  Patient Medical Document Vault
                </h2>
                <p className="text-xs text-slate-500 font-medium mt-0.5">
                  Store, preview, and download external hospital discharge summaries, diagnostic lab scans, and clinical reports.
                </p>
              </div>

              {!isDistrictOfficer ? (
                <button
                  onClick={() => setShowUploadModal(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs transition shrink-0"
                >
                  <Upload className="w-4 h-4" />
                  <span>Upload Medical Document</span>
                </button>
              ) : (
                <span className="text-[11px] font-bold text-amber-800 bg-amber-50 px-3 py-1.5 rounded-xl border border-amber-200">
                  District Officer: Read-Only Vault Access
                </span>
              )}
            </div>

            {/* Filter and Search Inputs Bar */}
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
              {/* Category Filter Pills */}
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="font-bold text-slate-700 mr-1 flex items-center gap-1">
                  <Filter className="w-3.5 h-3.5 text-slate-400" />
                  Category:
                </span>
                {[
                  { label: 'All Files', key: 'ALL' },
                  { label: 'Medical Records', key: 'MEDICAL_RECORD' },
                  { label: 'Lab Reports', key: 'LAB_REPORT' },
                  { label: 'Prescriptions', key: 'PRESCRIPTION' },
                  { label: 'Discharge Summaries', key: 'DISCHARGE_SUMMARY' },
                  { label: 'Referrals', key: 'REFERRAL_DOC' },
                  { label: 'Other', key: 'OTHER' }
                ].map((cat) => (
                  <button
                    key={cat.key}
                    onClick={() => setDocCategoryFilter(cat.key)}
                    className={`px-3 py-1 rounded-lg font-bold text-[11px] transition ${
                      docCategoryFilter === cat.key
                        ? 'bg-purple-600 text-white shadow-xs'
                        : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100'
                    }`}
                  >
                    {cat.label}
                  </button>
                ))}
              </div>

              {/* Title Search Input */}
              <div className="relative min-w-[240px]">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search title, filename, staff..."
                  value={docSearchQuery}
                  onChange={(e) => setDocSearchQuery(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-xl pl-9 pr-3 py-2 text-slate-900 font-medium text-xs focus:outline-none focus:border-purple-600"
                />
              </div>
            </div>
          </div>

          {/* Documents Grid */}
          {filteredDocuments.length === 0 ? (
            <div className="glass-panel p-12 rounded-2xl border border-slate-200 bg-white text-center text-xs text-slate-500 space-y-3 shadow-xs">
              <FolderOpen className="w-10 h-10 text-slate-300 mx-auto" />
              <p className="font-medium">No medical documents found in this view.</p>
              {!isDistrictOfficer && (
                <button
                  onClick={() => setShowUploadModal(true)}
                  className="px-4 py-2 bg-emerald-600 text-white font-bold rounded-xl hover:bg-emerald-500 transition inline-flex items-center gap-1.5"
                >
                  <Upload className="w-4 h-4" />
                  <span>Upload First Document</span>
                </button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredDocuments.map((doc) => {
                const isImage = ['image/jpeg', 'image/png', 'image/jpg'].includes(doc.mime_type?.toLowerCase()) ||
                  ['.jpg', '.jpeg', '.png'].some(ext => doc.file_name?.toLowerCase().endsWith(ext));

                return (
                  <div
                    key={doc.id}
                    className="glass-panel p-5 rounded-2xl border border-slate-200 bg-white space-y-4 hover:border-purple-300 hover:shadow-md transition group flex flex-col justify-between"
                  >
                    <div className="space-y-3">
                      {/* Document Type Header Badge & Icon */}
                      <div className="flex items-center justify-between">
                        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                          doc.document_type === 'MEDICAL_RECORD' ? 'bg-blue-100 text-blue-800 border-blue-200' :
                          doc.document_type === 'LAB_REPORT' ? 'bg-teal-100 text-teal-800 border-teal-200' :
                          doc.document_type === 'PRESCRIPTION' ? 'bg-amber-100 text-amber-800 border-amber-200' :
                          doc.document_type === 'DISCHARGE_SUMMARY' ? 'bg-purple-100 text-purple-800 border-purple-200' :
                          'bg-slate-100 text-slate-800 border-slate-200'
                        }`}>
                          {doc.document_type_display || doc.document_type}
                        </span>

                        <span className="font-mono text-[10px] font-bold text-slate-500">
                          {doc.file_size_formatted || `${intKB(doc.file_size)} KB`}
                        </span>
                      </div>

                      {/* Title & Description */}
                      <div className="space-y-1">
                        <h3 className="font-bold text-slate-900 text-sm group-hover:text-purple-700 transition line-clamp-1">
                          {doc.title}
                        </h3>
                        {doc.description && (
                          <p className="text-[11px] text-slate-600 line-clamp-2 font-medium">
                            {doc.description}
                          </p>
                        )}
                      </div>

                      {/* File Metadata Info */}
                      <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-[11px] space-y-1.5 font-medium">
                        <div className="flex items-center gap-1.5 text-slate-700 truncate">
                          <File className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                          <span className="font-mono truncate">{doc.file_name}</span>
                        </div>

                        <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1 border-t border-slate-200/60">
                          <span>Uploaded: <strong className="text-slate-700">{doc.uploaded_at?.split(' ')[0]}</strong></span>
                          <span>By: <strong className="text-slate-700">{doc.uploaded_by_name || 'Staff'}</strong></span>
                        </div>
                      </div>
                    </div>

                    {/* Actions Row */}
                    <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-2 text-xs">
                      <button
                        onClick={() => setPreviewDoc(doc)}
                        className="flex-1 py-1.5 px-3 bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold rounded-lg flex items-center justify-center gap-1 transition"
                      >
                        <Eye className="w-3.5 h-3.5 text-slate-600" />
                        <span>Preview</span>
                      </button>

                      <button
                        onClick={() => handleDownloadDocument(doc)}
                        disabled={downloadingDocId === doc.id}
                        className="flex-1 py-1.5 px-3 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-lg flex items-center justify-center gap-1 transition shadow-2xs disabled:opacity-50"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>{downloadingDocId === doc.id ? 'Downloading...' : 'Download'}</span>
                      </button>

                      {!isDistrictOfficer && (
                        <button
                          onClick={() => handleDeleteDocument(doc.id, doc.title)}
                          className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
                          title="Delete Document"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* UPLOAD DOCUMENT MODAL */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 border border-slate-200 w-full max-w-lg space-y-4 shadow-xl">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Upload className="w-5 h-5 text-emerald-600" />
                Upload Patient Medical Document
              </h2>
              <button onClick={() => setShowUploadModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {uploadError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs font-semibold flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                <span>{uploadError}</span>
              </div>
            )}

            <form onSubmit={handleUploadSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-700 font-bold mb-1">Document Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Victoria Hospital Discharge Summary, Diagnostic ECG Scan"
                  value={uploadTitle}
                  onChange={(e) => setUploadTitle(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 font-medium focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Document Category *</label>
                  <select
                    value={uploadType}
                    onChange={(e) => setUploadType(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 font-medium focus:outline-none"
                  >
                    <option value="MEDICAL_RECORD">Medical Record / EMR</option>
                    <option value="LAB_REPORT">Lab Report / Scan</option>
                    <option value="PRESCRIPTION">Prescription Slip</option>
                    <option value="DISCHARGE_SUMMARY">Discharge Summary</option>
                    <option value="REFERRAL_DOC">Referral Document</option>
                    <option value="OTHER">Other Clinical File</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-700 font-bold mb-1">Target Patient</label>
                  <input
                    type="text"
                    disabled
                    value={`${patient.name} (${patient.patient_id})`}
                    className="w-full bg-slate-100 border border-slate-200 rounded-xl p-2.5 text-slate-600 font-bold"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Document File *</label>
                <input
                  type="file"
                  required
                  accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                  onChange={(e) => setUploadFile(e.target.files ? e.target.files[0] : null)}
                  className="w-full text-xs text-slate-700 bg-slate-50 border border-slate-300 rounded-xl p-2 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-bold file:bg-slate-900 file:text-white hover:file:bg-slate-800"
                />
                <span className="text-[10px] text-slate-500 mt-1 block">
                  Allowed file formats: PDF, JPG, JPEG, PNG, DOC, DOCX (Max size: 15 MB)
                </span>
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Notes / Description (Optional)</label>
                <textarea
                  rows={2}
                  placeholder="Additional context or notes regarding this document..."
                  value={uploadDescription}
                  onChange={(e) => setUploadDescription(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 font-medium focus:outline-none"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-4 py-2 border border-slate-300 text-slate-700 font-bold rounded-xl hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl shadow-sm disabled:opacity-50 flex items-center gap-1.5"
                >
                  <Upload className="w-4 h-4" />
                  <span>{uploading ? 'Uploading File...' : 'Upload Document'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* DOCUMENT PREVIEW & DETAILS MODAL */}
      {previewDoc && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 border border-slate-200 w-full max-w-2xl space-y-4 shadow-2xl">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-base font-bold text-slate-900">{previewDoc.title}</h2>
                <span className="text-xs text-purple-700 font-mono font-bold">
                  {previewDoc.document_type_display || previewDoc.document_type}
                </span>
              </div>
              <button onClick={() => setPreviewDoc(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Document Content / Image View */}
            <div className="bg-slate-900 p-4 rounded-xl text-center min-h-[220px] flex items-center justify-center overflow-hidden">
              {['image/jpeg', 'image/png', 'image/jpg'].includes(previewDoc.mime_type?.toLowerCase()) ||
              ['.jpg', '.jpeg', '.png'].some(ext => previewDoc.file_name?.toLowerCase().endsWith(ext)) ? (
                <img
                  src={previewDoc.file_url || previewDoc.file}
                  alt={previewDoc.title}
                  className="max-h-[360px] object-contain rounded-lg"
                />
              ) : (
                <div className="text-slate-300 space-y-2">
                  <FileText className="w-12 h-12 text-purple-400 mx-auto" />
                  <p className="text-xs font-bold font-mono">{previewDoc.file_name}</p>
                  <p className="text-[11px] text-slate-400">Preview not supported for document format. Please click Download.</p>
                </div>
              )}
            </div>

            {/* Document Info Metadata List */}
            <div className="grid grid-cols-2 gap-3 text-xs bg-slate-50 p-3 rounded-xl border border-slate-200">
              <div>
                <span className="text-slate-500 font-medium block">File Name</span>
                <span className="font-bold text-slate-900 font-mono truncate block">{previewDoc.file_name}</span>
              </div>
              <div>
                <span className="text-slate-500 font-medium block">File Size</span>
                <span className="font-bold text-slate-900 font-mono">{previewDoc.file_size_formatted || `${intKB(previewDoc.file_size)} KB`}</span>
              </div>
              <div>
                <span className="text-slate-500 font-medium block">Uploaded On</span>
                <span className="font-bold text-slate-900 font-mono">{previewDoc.uploaded_at}</span>
              </div>
              <div>
                <span className="text-slate-500 font-medium block">Uploaded By Staff</span>
                <span className="font-bold text-slate-900">{previewDoc.uploaded_by_name || 'Healthcare Staff'}</span>
              </div>
            </div>

            {/* Action Bar */}
            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                onClick={() => setPreviewDoc(null)}
                className="px-4 py-2 border border-slate-300 text-slate-700 font-bold rounded-xl text-xs hover:bg-slate-100"
              >
                Close
              </button>
              <button
                onClick={() => {
                  handleDownloadDocument(previewDoc);
                  setPreviewDoc(null);
                }}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-xl text-xs flex items-center gap-1.5 shadow-sm"
              >
                <Download className="w-4 h-4" />
                <span>Download Document File</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Quick Token Modal */}
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
              <button onClick={() => setShowTokenModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
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

function intKB(bytes?: number): number {
  if (!bytes) return 0;
  return Math.round(bytes / 1024);
}
