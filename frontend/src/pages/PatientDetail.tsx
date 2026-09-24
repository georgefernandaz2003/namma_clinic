import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import type { Patient, PatientDocument } from '../types';
import { useAuth } from '../context/AuthContext';
import { useConfirm } from '../context/ConfirmContext';
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
  const { confirm } = useConfirm();
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
  const [expandedTimelineItems, setExpandedTimelineItems] = useState<Record<string, boolean>>({});

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

    confirm({
      title: 'Confirm Document Upload',
      message: `Are you sure you want to upload this document to ${patient.name}'s medical record?`,
      confirmText: 'Upload Document',
      cancelText: 'Cancel',
      variant: 'primary',
      loadingText: 'Uploading Document...',
      details: [
        { label: 'Patient Name', value: patient.name },
        { label: 'Document Title', value: uploadTitle.trim() },
        { label: 'Category', value: uploadType },
        { label: 'File Name', value: uploadFile.name },
        { label: 'File Size', value: `${(uploadFile.size / 1024).toFixed(1)} KB` },
      ],
      onConfirm: async () => {
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

          setShowUploadModal(false);
          setUploadTitle('');
          setUploadType('MEDICAL_RECORD');
          setUploadDescription('');
          setUploadFile(null);
          
          await fetchPatientData();
        } catch (err: any) {
          console.error('Document upload error', err);
          const msg = err.response?.data?.error || err.message || 'Failed to upload document.';
          setUploadError(msg);
          throw err;
        } finally {
          setUploading(false);
        }
      }
    });
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
  const handleDeleteDocument = (docId: number, docTitle: string) => {
    if (!patient) return;

    confirm({
      title: 'Confirm Document Deletion',
      message: `Are you sure you want to permanently delete the document '${docTitle}'?`,
      warning: 'Warning: This action is permanent and cannot be undone. The document file will be deleted from storage.',
      confirmText: 'Delete Document',
      cancelText: 'Cancel',
      variant: 'danger',
      loadingText: 'Deleting Document...',
      details: [
        { label: 'Patient Name', value: patient.name },
        { label: 'Document Title', value: docTitle },
        { label: 'Patient UHID', value: patient.patient_id }
      ],
      onConfirm: async () => {
        await api.delete(`patients/${patient.id}/documents/${docId}/`);
        await fetchPatientData();
      }
    });
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

  const parseEventDate = (ev: any): number => {
    const ts = ev?.timestamp || ev?.date;
    if (!ts) return 0;
    const normalized = ts.includes(' ') ? ts.replace(' ', 'T') : ts;
    const d = new Date(normalized);
    return isNaN(d.getTime()) ? 0 : d.getTime();
  };

  const getEventDateKey = (ev: any): string => {
    if (ev.date && !ev.date.includes(' ') && !ev.date.includes('T')) {
      return ev.date;
    }
    if (ev.timestamp) {
      return ev.timestamp.split('T')[0];
    }
    return ev.date ? (ev.date.includes(' ') ? ev.date.split(' ')[0] : ev.date.split('T')[0]) : '1970-01-01';
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

  const getEventTimeDisplay = (ev: any): string => {
    if (ev.has_time === false) {
      return ev.time_display || 'Registration time not recorded';
    }
    if (ev.time_display && ev.time_display !== 'Registration time not recorded') {
      return ev.time_display;
    }
    if (ev.timestamp) {
      const d = new Date(ev.timestamp);
      if (!isNaN(d.getTime())) {
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
      }
    }
    return formatEventTime(ev.date) || (ev.date && ev.date.includes(' ') ? ev.date.split(' ')[1] : '');
  };

  const isItemExpanded = (itemKey: string) => {
    return !!expandedTimelineItems[itemKey];
  };

  const toggleTimelineItem = (itemKey: string) => {
    setExpandedTimelineItems((prev) => ({
      ...prev,
      [itemKey]: !prev[itemKey]
    }));
  };

  // Filtered EMR Timeline
  const filteredTimelineEvents = useMemo(() => {
    return timelineEvents.filter((ev) => {
      if (eventTypeFilter !== 'ALL') {
        if (eventTypeFilter === 'VISIT' && !['VISIT', 'VISIT_COMPLETED'].includes(ev.type)) return false;
        if (eventTypeFilter === 'TRIAGE' && ev.type !== 'TRIAGE') return false;
        if (eventTypeFilter === 'CONSULTATION' && !['CONSULTATION', 'RE_CONSULTATION'].includes(ev.type)) return false;
        if (eventTypeFilter === 'PRESCRIPTION' && !['PRESCRIPTION', 'DISPENSING'].includes(ev.type)) return false;
        if (eventTypeFilter === 'LAB' && !['LAB', 'LAB_ORDER', 'SAMPLE_COLLECTION', 'LAB_RESULT'].includes(ev.type)) return false;
        if (eventTypeFilter === 'DOCUMENT' && ev.type !== 'DOCUMENT') return false;
        if (eventTypeFilter === 'REFERRAL' && !['REFERRAL', 'REFERRAL_RESPONSE'].includes(ev.type)) return false;
        if (eventTypeFilter === 'FOLLOWUP' && ev.type !== 'FOLLOWUP') return false;
        if (eventTypeFilter === 'OTHER' && [
          'REGISTRATION', 'VISIT', 'VISIT_COMPLETED', 'TRIAGE',
          'CONSULTATION', 'RE_CONSULTATION', 'PRESCRIPTION',
          'DISPENSING', 'LAB', 'LAB_ORDER', 'SAMPLE_COLLECTION',
          'LAB_RESULT', 'DOCUMENT', 'REFERRAL',
          'REFERRAL_RESPONSE', 'FOLLOWUP'
        ].includes(ev.type)) return false;
      }
      const evDateOnly = getEventDateKey(ev);
      if (fromDate) {
        if (evDateOnly < fromDate) return false;
      }
      if (toDate) {
        if (evDateOnly > toDate) return false;
      }
      return true;
    });
  }, [timelineEvents, fromDate, toDate, eventTypeFilter]);

  // Group timeline events by date
  const groupedTimelineEvents = useMemo(() => {
    const groups: { [dateKey: string]: { displayDate: string; dateKey: string; events: any[] } } = {};
    filteredTimelineEvents.forEach((ev) => {
      const dateKey = getEventDateKey(ev);
      let displayDate = dateKey;
      const parts = dateKey.split('-');
      if (parts.length === 3) {
        const d = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
        if (!isNaN(d.getTime())) {
          displayDate = d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
        }
      }

      if (!groups[dateKey]) {
        groups[dateKey] = { displayDate, dateKey, events: [] };
      }
      groups[dateKey].events.push(ev);
    });

    // Sort newest event first within each date
    Object.keys(groups).forEach((key) => {
      groups[key].events.sort((a, b) => parseEventDate(b) - parseEventDate(a));
    });

    // Sort dates in reverse chronological order (newest date first)
    return Object.keys(groups)
      .sort()
      .reverse()
      .map((key) => groups[key]);
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

  const renderExpandedEventDetails = (ev: any) => {
    const sd = ev.structured_data || {};

    switch (ev.type) {
      case 'REGISTRATION':
        return (
          <div className="mt-3 pt-3 border-t border-slate-200 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 text-xs bg-white p-3.5 rounded-xl border border-slate-200/80">
            <div><span className="text-slate-500 font-bold block">Patient UHID</span><span className="font-mono font-black text-emerald-800">{sd.patient_id}</span></div>
            <div><span className="text-slate-500 font-bold block">Full Name</span><span className="font-bold text-slate-900">{sd.name}</span></div>
            <div><span className="text-slate-500 font-bold block">Age & Gender</span><span className="font-semibold text-slate-800">{sd.age} yrs / {sd.gender}</span></div>
            <div><span className="text-slate-500 font-bold block">Mobile Contact</span><span className="font-mono font-bold text-slate-800">{sd.mobile}</span></div>
            <div><span className="text-slate-500 font-bold block">Residential Address</span><span className="text-slate-800">{sd.address}</span></div>
            <div><span className="text-slate-500 font-bold block">ABHA Health ID</span><span className="font-mono text-slate-800">{sd.abha_id}</span></div>
            <div><span className="text-slate-500 font-bold block">Vulnerability Category</span><span className="text-slate-800">{sd.vulnerability}</span></div>
            <div><span className="text-slate-500 font-bold block">Emergency Contact</span><span className="text-slate-800">{sd.emergency_contact}</span></div>
            <div><span className="text-slate-500 font-bold block">Registered Facility</span><span className="font-semibold text-slate-800">{sd.registered_facility}</span></div>
            <div><span className="text-slate-500 font-bold block">Registration Date</span><span className="font-mono font-bold text-slate-800">{sd.registration_date}</span></div>
            <div className="md:col-span-2"><span className="text-slate-500 font-bold block">Registration Time</span><span className="text-slate-500 italic">Registration time not recorded</span></div>
          </div>
        );

      case 'VISIT':
        return (
          <div className="mt-3 pt-3 border-t border-slate-200 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 text-xs bg-white p-3.5 rounded-xl border border-slate-200/80">
            <div><span className="text-slate-500 font-bold block">Visit ID</span><span className="font-mono font-bold text-emerald-800">{sd.visit_id}</span></div>
            <div><span className="text-slate-500 font-bold block">OPD Token #</span><span className="font-mono font-black text-blue-700">#{sd.token_number}</span></div>
            <div><span className="text-slate-500 font-bold block">Healthcare Facility</span><span className="font-semibold text-slate-800">{sd.facility}</span></div>
            <div><span className="text-slate-500 font-bold block">Visit Category</span><span className="text-slate-800">{sd.visit_type}</span></div>
            <div><span className="text-slate-500 font-bold block">Queue Priority</span><span className="font-bold text-slate-800">{sd.priority}</span></div>
            <div><span className="text-slate-500 font-bold block">Queue & Status</span><span className="text-slate-800">{sd.status} ({sd.current_queue})</span></div>
            <div><span className="text-slate-500 font-bold block">Assigned Doctor</span><span className="font-bold text-slate-800">{sd.assigned_doctor}</span></div>
            <div><span className="text-slate-500 font-bold block">Arrival Timestamp</span><span className="font-mono text-slate-800">{sd.arrival_time}</span></div>
            <div className="md:col-span-3"><span className="text-slate-500 font-bold block">Chief Complaint</span><span className="text-slate-900 font-medium">{sd.chief_complaint}</span></div>
          </div>
        );

      case 'VISIT_COMPLETED':
        return (
          <div className="mt-3 pt-3 border-t border-slate-200 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 text-xs bg-white p-3.5 rounded-xl border border-slate-200/80">
            <div><span className="text-slate-500 font-bold block">Visit ID</span><span className="font-mono font-bold text-emerald-800">{sd.visit_id}</span></div>
            <div><span className="text-slate-500 font-bold block">Token #</span><span className="font-mono font-bold text-blue-700">#{sd.token_number}</span></div>
            <div><span className="text-slate-500 font-bold block">Facility</span><span className="font-semibold text-slate-800">{sd.facility}</span></div>
            <div><span className="text-slate-500 font-bold block">Arrival Time</span><span className="font-mono text-slate-800">{sd.arrival_time}</span></div>
            <div><span className="text-slate-500 font-bold block">Completed Time</span><span className="font-mono font-bold text-emerald-700">{sd.completed_time}</span></div>
            <div><span className="text-slate-500 font-bold block">Total Duration</span><span className="font-bold text-slate-900">{sd.duration_minutes !== null ? `${sd.duration_minutes} minutes` : 'Completed'}</span></div>
          </div>
        );

      case 'TRIAGE':
        return (
          <div className="mt-3 pt-3 border-t border-slate-200 space-y-3 bg-white p-3.5 rounded-xl border border-slate-200/80 text-xs">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
              <div className="bg-slate-50 p-2 rounded-lg border border-slate-200">
                <span className="text-[10px] text-slate-500 font-bold block">Blood Pressure</span>
                <span className="font-mono font-bold text-slate-900 text-sm">{sd.blood_pressure}</span>
              </div>
              <div className="bg-slate-50 p-2 rounded-lg border border-slate-200">
                <span className="text-[10px] text-slate-500 font-bold block">Pulse Rate</span>
                <span className="font-mono font-bold text-slate-900 text-sm">{sd.pulse_bpm} bpm</span>
              </div>
              <div className="bg-slate-50 p-2 rounded-lg border border-slate-200">
                <span className="text-[10px] text-slate-500 font-bold block">Body Temperature</span>
                <span className="font-mono font-bold text-slate-900 text-sm">{sd.temperature_f} °F</span>
              </div>
              <div className="bg-slate-50 p-2 rounded-lg border border-slate-200">
                <span className="text-[10px] text-slate-500 font-bold block">Oxygen (SpO2)</span>
                <span className="font-mono font-bold text-slate-900 text-sm">{sd.spo2_percent}%</span>
              </div>
              <div className="bg-slate-50 p-2 rounded-lg border border-slate-200">
                <span className="text-[10px] text-slate-500 font-bold block">Blood Glucose</span>
                <span className="font-mono font-bold text-slate-900 text-sm">{sd.blood_glucose_mgdl} mg/dL</span>
              </div>
              <div className="bg-slate-50 p-2 rounded-lg border border-slate-200">
                <span className="text-[10px] text-slate-500 font-bold block">BMI</span>
                <span className="font-mono font-bold text-slate-900 text-sm">{sd.bmi}</span>
              </div>
              <div className="bg-slate-50 p-2 rounded-lg border border-slate-200">
                <span className="text-[10px] text-slate-500 font-bold block">Height & Weight</span>
                <span className="font-mono font-bold text-slate-900 text-sm">{sd.height_cm} cm / {sd.weight_kg} kg</span>
              </div>
              <div className="bg-slate-50 p-2 rounded-lg border border-slate-200">
                <span className="text-[10px] text-slate-500 font-bold block">Respiratory Rate</span>
                <span className="font-mono font-bold text-slate-900 text-sm">{sd.respiratory_rate} /min</span>
              </div>
            </div>
            {sd.active_flags && sd.active_flags.length > 0 && (
              <div className="flex flex-wrap items-center gap-1.5 pt-1">
                <span className="text-[11px] font-bold text-rose-700">Triage Alerts:</span>
                {sd.active_flags.map((f: string, i: number) => (
                  <span key={i} className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200">
                    {f}
                  </span>
                ))}
              </div>
            )}
            <div className="flex justify-between items-center pt-1 border-t border-slate-100 text-slate-600 text-[11px]">
              <span>Nurse: <strong className="text-slate-900">{sd.nurse}</strong> | Visit: <strong className="text-slate-900">{sd.visit_id}</strong></span>
              <span>Remarks: <strong className="text-slate-800">{sd.nurse_notes}</strong></span>
            </div>
          </div>
        );

      case 'CONSULTATION':
        return (
          <div className="mt-3 pt-3 border-t border-slate-200 space-y-3 bg-white p-3.5 rounded-xl border border-slate-200/80 text-xs">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <span className="text-slate-500 font-bold block mb-1">Chief Complaint</span>
                <p className="p-2.5 bg-slate-50 rounded-lg border border-slate-200 text-slate-800 font-medium">{sd.chief_complaint}</p>
              </div>
              <div>
                <span className="text-slate-500 font-bold block mb-1">Clinical Diagnosis</span>
                <div className="p-2.5 bg-indigo-50/70 rounded-lg border border-indigo-200 text-indigo-950 font-bold flex justify-between items-center">
                  <span>{sd.diagnosis_name}</span>
                  <span className="font-mono text-[10px] bg-indigo-200 text-indigo-900 px-2 py-0.5 rounded">{sd.diagnosis_code}</span>
                </div>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <span className="text-slate-500 font-bold block mb-1">Clinical History</span>
                <p className="p-2.5 bg-slate-50 rounded-lg border border-slate-200 text-slate-800 font-medium">{sd.clinical_history}</p>
              </div>
              <div>
                <span className="text-slate-500 font-bold block mb-1">Clinical Assessment</span>
                <p className="p-2.5 bg-slate-50 rounded-lg border border-slate-200 text-slate-800 font-medium">{sd.clinical_assessment}</p>
              </div>
            </div>
            <div>
              <span className="text-slate-500 font-bold block mb-1">Treatment Plan & Clinical Notes</span>
              <p className="p-2.5 bg-slate-50 rounded-lg border border-slate-200 text-slate-800 font-medium leading-relaxed">
                {sd.treatment_plan || sd.clinical_notes}
              </p>
            </div>
            <div className="flex flex-wrap justify-between items-center pt-1 border-t border-slate-100 text-slate-600 text-[11px] gap-2">
              <span>Attending Doctor: <strong className="text-slate-900">{sd.doctor}</strong> ({sd.facility})</span>
              {sd.follow_up_date && sd.follow_up_date !== 'None scheduled' && (
                <span className="px-2.5 py-0.5 rounded-lg bg-amber-50 text-amber-800 border border-amber-200 font-bold">
                  Follow-up Advised: {sd.follow_up_date}
                </span>
              )}
            </div>
          </div>
        );

      case 'RE_CONSULTATION':
        return (
          <div className="mt-3 pt-3 border-t border-slate-200 space-y-2 bg-white p-3.5 rounded-xl border border-slate-200/80 text-xs">
            <div className="p-2.5 bg-purple-50 rounded-lg border border-purple-200 text-purple-900 font-bold flex justify-between items-center">
              <span>Confirmed Diagnosis: {sd.diagnosis}</span>
              <span className="font-mono text-[10px] bg-purple-200 text-purple-900 px-2 py-0.5 rounded">Post-Lab Verified</span>
            </div>
            <div>
              <span className="text-slate-500 font-bold block mb-1">Post-Lab Clinical Review Notes</span>
              <p className="p-2.5 bg-slate-50 rounded-lg border border-slate-200 text-slate-800 font-medium">{sd.clinical_notes}</p>
            </div>
            <div>
              <span className="text-slate-500 font-bold block mb-1">Finalized Therapeutic Regime</span>
              <p className="p-2.5 bg-slate-50 rounded-lg border border-slate-200 text-slate-800 font-medium">{sd.treatment_plan}</p>
            </div>
            <div className="text-[11px] text-slate-600 pt-1 border-t border-slate-100">
              Attending Clinician: <strong className="text-slate-900">{sd.doctor}</strong> | Facility: <strong className="text-slate-900">{sd.facility}</strong>
            </div>
          </div>
        );

      case 'LAB_ORDER':
        return (
          <div className="mt-3 pt-3 border-t border-slate-200 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 text-xs bg-white p-3.5 rounded-xl border border-slate-200/80">
            <div><span className="text-slate-500 font-bold block">Order ID</span><span className="font-mono font-bold text-teal-700">{sd.order_id}</span></div>
            <div><span className="text-slate-500 font-bold block">Test Name & Code</span><span className="font-bold text-slate-900">{sd.test_name} ({sd.test_code})</span></div>
            <div><span className="text-slate-500 font-bold block">Lab Category</span><span className="text-slate-800">{sd.category}</span></div>
            <div><span className="text-slate-500 font-bold block">Ordering Doctor</span><span className="font-semibold text-slate-800">{sd.ordering_doctor}</span></div>
            <div><span className="text-slate-500 font-bold block">Healthcare Facility</span><span className="text-slate-800">{sd.facility}</span></div>
            <div><span className="text-slate-500 font-bold block">Order Status</span><span className="font-bold text-slate-800">{sd.status}</span></div>
            <div className="md:col-span-2"><span className="text-slate-500 font-bold block">Order Timestamp</span><span className="font-mono text-slate-800">{sd.order_time}</span></div>
          </div>
        );

      case 'SAMPLE_COLLECTION':
        return (
          <div className="mt-3 pt-3 border-t border-slate-200 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 text-xs bg-white p-3.5 rounded-xl border border-slate-200/80">
            <div><span className="text-slate-500 font-bold block">Lab Order Ref</span><span className="font-mono font-bold text-teal-700">{sd.order_id}</span></div>
            <div><span className="text-slate-500 font-bold block">Specimen Type</span><span className="font-bold text-slate-900">{sd.sample_type}</span></div>
            <div><span className="text-slate-500 font-bold block">Sample Barcode</span><span className="font-mono font-bold text-cyan-800">{sd.sample_code}</span></div>
            <div><span className="text-slate-500 font-bold block">Collected By</span><span className="font-semibold text-slate-800">{sd.collected_by}</span></div>
            <div><span className="text-slate-500 font-bold block">Facility</span><span className="text-slate-800">{sd.facility}</span></div>
            <div><span className="text-slate-500 font-bold block">Collection Time</span><span className="font-mono text-slate-800">{sd.collection_time}</span></div>
          </div>
        );

      case 'LAB_RESULT':
        return (
          <div className="mt-3 pt-3 border-t border-slate-200 space-y-3 bg-white p-3.5 rounded-xl border border-slate-200/80 text-xs">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                <span className="text-[10px] text-slate-500 font-bold block">Diagnostic Investigation</span>
                <span className="font-bold text-slate-900">{sd.test_name}</span>
                <span className="font-mono text-[10px] text-slate-400 block">{sd.test_code}</span>
              </div>
              <div className="bg-emerald-50/60 p-2.5 rounded-lg border border-emerald-200">
                <span className="text-[10px] text-emerald-800 font-bold block">Lab Result Value</span>
                <span className="font-mono font-black text-emerald-950 text-base">{sd.result_value} {sd.unit}</span>
                <span className="text-[10px] text-slate-500 block">Ref: {sd.reference_range}</span>
              </div>
              <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                <span className="text-[10px] text-slate-500 font-bold block">Clinical Flag</span>
                <span className={`inline-block px-2.5 py-0.5 rounded text-[11px] font-black mt-1 ${
                  sd.interpretation_flag === 'CRITICAL' ? 'bg-rose-600 text-white' :
                  sd.interpretation_flag === 'HIGH' ? 'bg-rose-100 text-rose-800 border border-rose-300' :
                  sd.interpretation_flag === 'LOW' ? 'bg-amber-100 text-amber-800 border border-amber-300' :
                  'bg-emerald-100 text-emerald-800 border border-emerald-200'
                }`}>{sd.interpretation_flag}</span>
              </div>
            </div>
            <div className="flex flex-wrap justify-between items-center pt-1 border-t border-slate-100 text-slate-600 text-[11px] gap-2">
              <span>Verified by: <strong className="text-slate-900">{sd.verified_by}</strong> ({sd.verification_time})</span>
              {sd.notes && <span>Notes: <strong className="text-slate-800">{sd.notes}</strong></span>}
            </div>
          </div>
        );

      case 'PRESCRIPTION':
        return (
          <div className="mt-3 pt-3 border-t border-slate-200 space-y-3 bg-white p-3.5 rounded-xl border border-slate-200/80 text-xs">
            <div className="flex justify-between items-center text-slate-600 text-[11px] border-b border-slate-100 pb-2">
              <span>Prescription ID: <strong className="font-mono text-slate-900">#{sd.prescription_id}</strong> | Status: <strong className="text-slate-900">{sd.status}</strong></span>
              <span>Doctor: <strong className="text-slate-900">{sd.doctor}</strong> ({sd.facility})</span>
            </div>
            {sd.items && sd.items.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="text-slate-500 font-bold border-b border-slate-200">
                      <th className="pb-1.5">Medicine</th>
                      <th className="pb-1.5">Dosage</th>
                      <th className="pb-1.5">Frequency</th>
                      <th className="pb-1.5">Duration</th>
                      <th className="pb-1.5">Quantity</th>
                      <th className="pb-1.5">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {sd.items.map((it: any, idx: number) => (
                      <tr key={idx}>
                        <td className="py-1.5 font-bold text-slate-900">{it.medicine_name}</td>
                        <td className="py-1.5 text-slate-700">{it.dosage}</td>
                        <td className="py-1.5 text-slate-700">{it.frequency}</td>
                        <td className="py-1.5 text-slate-700">{it.duration_days} Days</td>
                        <td className="py-1.5 font-mono font-bold text-slate-900">{it.quantity}</td>
                        <td className="py-1.5"><span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">{it.status}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {sd.notes && sd.notes !== 'None' && (
              <div className="text-[11px] text-slate-600 pt-1">
                Instructions: <span className="font-medium text-slate-800">{sd.notes}</span>
              </div>
            )}
          </div>
        );

      case 'DISPENSING':
        return (
          <div className="mt-3 pt-3 border-t border-slate-200 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 text-xs bg-white p-3.5 rounded-xl border border-slate-200/80">
            <div><span className="text-slate-500 font-bold block">Medicine (Generic)</span><span className="font-bold text-slate-900">{sd.medicine_name}</span></div>
            <div><span className="text-slate-500 font-bold block">Batch Number</span><span className="font-mono font-bold text-slate-800">{sd.batch_number}</span></div>
            <div><span className="text-slate-500 font-bold block">Expiry Date</span><span className="font-mono text-slate-800">{sd.expiry_date}</span></div>
            <div><span className="text-slate-500 font-bold block">Quantity Dispensed</span><span className="font-mono font-black text-emerald-700">{sd.quantity_dispensed} Units</span></div>
            <div><span className="text-slate-500 font-bold block">Dispensed By</span><span className="font-semibold text-slate-800">{sd.dispensed_by}</span></div>
            <div><span className="text-slate-500 font-bold block">Healthcare Facility</span><span className="text-slate-800">{sd.facility}</span></div>
            <div><span className="text-slate-500 font-bold block">Prescription Ref</span><span className="font-mono text-slate-800">{sd.reference_id}</span></div>
            <div><span className="text-slate-500 font-bold block">Stock Allocation</span><span className="text-slate-600">{sd.notes}</span></div>
          </div>
        );

      case 'REFERRAL':
        return (
          <div className="mt-3 pt-3 border-t border-slate-200 space-y-3 bg-white p-3.5 rounded-xl border border-slate-200/80 text-xs">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div><span className="text-slate-500 font-bold block">Referral ID</span><span className="font-mono font-bold text-orange-800">{sd.referral_id}</span></div>
              <div><span className="text-slate-500 font-bold block">Destination Facility</span><span className="font-bold text-slate-900">{sd.destination_facility}</span></div>
              <div><span className="text-slate-500 font-bold block">Urgency & Service</span><span className="font-bold text-slate-800">{sd.urgency} ({sd.required_service})</span></div>
            </div>
            <div><span className="text-slate-500 font-bold block mb-1">Reason for Referral</span><p className="p-2 bg-slate-50 rounded-lg border border-slate-200 text-slate-800 font-medium">{sd.reason}</p></div>
            <div><span className="text-slate-500 font-bold block mb-1">Clinical Case Summary</span><p className="p-2 bg-slate-50 rounded-lg border border-slate-200 text-slate-800 font-medium">{sd.clinical_summary}</p></div>
            <div className="flex justify-between items-center pt-1 border-t border-slate-100 text-slate-600 text-[11px]">
              <span>Referring Doctor: <strong className="text-slate-900">{sd.referring_doctor}</strong> ({sd.source_facility})</span>
              <span>Status: <strong className="text-slate-900">{sd.status}</strong></span>
            </div>
          </div>
        );

      case 'REFERRAL_RESPONSE':
        return (
          <div className="mt-3 pt-3 border-t border-slate-200 space-y-3 bg-white p-3.5 rounded-xl border border-slate-200/80 text-xs">
            <div className="flex justify-between items-center text-slate-600 text-[11px] border-b border-slate-100 pb-2">
              <span>Hospital: <strong className="text-slate-900">{sd.hospital}</strong> | Specialist: <strong className="text-slate-900">Dr. {sd.specialist_doctor}</strong></span>
              <span>Responded: <strong className="font-mono text-slate-800">{sd.responded_at}</strong></span>
            </div>
            <div><span className="text-slate-500 font-bold block mb-1">Specialist Clinical Findings</span><p className="p-2 bg-slate-50 rounded-lg border border-slate-200 text-slate-800 font-medium">{sd.findings}</p></div>
            <div><span className="text-slate-500 font-bold block mb-1">Hospital Treatment Administered</span><p className="p-2 bg-slate-50 rounded-lg border border-slate-200 text-slate-800 font-medium">{sd.treatment_summary}</p></div>
            <div><span className="text-slate-500 font-bold block mb-1">Return Care & Follow-up Advice</span><p className="p-2 bg-purple-50 rounded-lg border border-purple-200 text-purple-900 font-bold">{sd.return_advice}</p></div>
          </div>
        );

      case 'FOLLOWUP':
        return (
          <div className="mt-3 pt-3 border-t border-slate-200 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 text-xs bg-white p-3.5 rounded-xl border border-slate-200/80">
            <div><span className="text-slate-500 font-bold block">Follow-up Category</span><span className="font-bold text-slate-900">{sd.category}</span></div>
            <div><span className="text-slate-500 font-bold block">Due Date</span><span className="font-mono font-bold text-blue-700">{sd.due_date}</span></div>
            <div><span className="text-slate-500 font-bold block">Status</span><span className="font-bold text-slate-800">{sd.status}</span></div>
            <div><span className="text-slate-500 font-bold block">Facility</span><span className="text-slate-800">{sd.facility}</span></div>
            <div className="md:col-span-4"><span className="text-slate-500 font-bold block">Instructions & Notes</span><span className="text-slate-800 font-medium">{sd.notes}</span></div>
          </div>
        );

      case 'DOCUMENT':
        return (
          <div className="mt-3 pt-3 border-t border-slate-200 space-y-2 bg-white p-3.5 rounded-xl border border-slate-200/80 text-xs">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-slate-700">
              <div><span className="text-slate-500 font-bold block">Document Type</span><span className="font-semibold text-slate-900">{sd.document_type}</span></div>
              <div><span className="text-slate-500 font-bold block">File Name</span><span className="font-mono text-slate-800 truncate block">{sd.file_name}</span></div>
              <div><span className="text-slate-500 font-bold block">File Size</span><span className="font-mono text-slate-800">{sd.file_size_kb} KB</span></div>
              <div><span className="text-slate-500 font-bold block">Uploaded By</span><span className="text-slate-800">{sd.uploaded_by}</span></div>
            </div>
            {sd.description && sd.description !== 'No description' && (
              <div><span className="text-slate-500 font-bold block">Notes</span><p className="text-slate-700 font-medium">{sd.description}</p></div>
            )}
            {ev.document_id && (
              <div className="pt-2 flex justify-end">
                <button
                  onClick={() => {
                    const docObj = recordsData.documents.find(d => d.id === ev.document_id);
                    if (docObj) handleDownloadDocument(docObj);
                  }}
                  className="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-lg flex items-center gap-1.5 transition text-xs shadow-2xs"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download Document</span>
                </button>
              </div>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  // Issue Token Submit
  const handleIssueTokenSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!patient || !activeFacility) return;

    confirm({
      title: 'Confirm OPD Visit Token Issuance',
      message: `Are you sure you want to generate an OPD check-in token for ${patient.name}?`,
      confirmText: 'Issue Visit Token',
      cancelText: 'Cancel',
      variant: 'primary',
      loadingText: 'Issuing Token...',
      details: [
        { label: 'Patient Name', value: patient.name },
        { label: 'Patient UHID', value: patient.patient_id },
        { label: 'Facility', value: activeFacility.facility_name },
        { label: 'Visit Type', value: visitType },
        { label: 'Priority', value: priority },
        { label: 'Chief Complaint', value: chiefComplaint || 'Routine OPD' }
      ],
      onConfirm: async () => {
        setSubmittingToken(true);
        try {
          await api.post('visits/', {
            patient: patient.id,
            facility: activeFacility.id,
            visit_type: visitType,
            priority,
            chief_complaint: chiefComplaint
          });
          setShowTokenModal(false);
          navigate('/queue');
        } finally {
          setSubmittingToken(false);
        }
      }
    });
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
              Vulnerability: {patient.vulnerability_information || 'General'}
            </span>
            <span className="px-3 py-1 rounded-lg text-xs font-bold bg-blue-100 text-blue-900 border border-blue-200 font-mono">
              ABHA: {patient.ABHA_ID_DEMO || 'Not Assigned'}
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
                <span className="text-[10px] text-slate-400 font-mono">{latestTriage?.date || '-'}</span>
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
                <span className="text-[10px] text-slate-400 font-mono">{latestConsultation?.date || '-'}</span>
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
                <span className="text-[10px] text-slate-400 font-mono">{activePrescription?.date || '-'}</span>
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
                      <option value="VISIT">Clinic Visits & Completion</option>
                      <option value="TRIAGE">Nurse Triage Vitals</option>
                      <option value="CONSULTATION">Doctor Consultations</option>
                      <option value="PRESCRIPTION">Prescriptions & Pharmacy</option>
                      <option value="LAB">Lab Orders & Results</option>
                      <option value="DOCUMENT">Uploaded Documents</option>
                      <option value="REFERRAL">Referrals & Responses</option>
                      <option value="FOLLOWUP">Clinical Follow-ups</option>
                      <option value="OTHER">Other Clinical Events</option>
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
                            const timeStr = getEventTimeDisplay(ev);
                            const itemKey = ev.id || `${group.dateKey}_${idx}`;
                            const isExpanded = isItemExpanded(itemKey);

                            return (
                              <div key={idx} className="relative group">
                                <div className="absolute -left-[31px] top-1.5 p-1 bg-white border-2 border-blue-600 rounded-full text-blue-600 shadow-xs">
                                  {ev.type === 'REGISTRATION' && <UserPlus className="w-3.5 h-3.5 text-blue-600" />}
                                  {ev.type === 'VISIT' && <Clock className="w-3.5 h-3.5 text-emerald-600" />}
                                  {ev.type === 'VISIT_COMPLETED' && <CheckCircle className="w-3.5 h-3.5 text-slate-600" />}
                                  {ev.type === 'TRIAGE' && <Activity className="w-3.5 h-3.5 text-rose-600" />}
                                  {ev.type === 'CONSULTATION' && <Stethoscope className="w-3.5 h-3.5 text-indigo-600" />}
                                  {ev.type === 'RE_CONSULTATION' && <Stethoscope className="w-3.5 h-3.5 text-purple-700" />}
                                  {ev.type === 'PRESCRIPTION' && <Pill className="w-3.5 h-3.5 text-amber-600" />}
                                  {ev.type === 'DISPENSING' && <CheckCircle className="w-3.5 h-3.5 text-green-600" />}
                                  {(ev.type === 'LAB' || ev.type === 'LAB_ORDER') && <FileText className="w-3.5 h-3.5 text-teal-600" />}
                                  {ev.type === 'SAMPLE_COLLECTION' && <FileSpreadsheet className="w-3.5 h-3.5 text-cyan-600" />}
                                  {ev.type === 'LAB_RESULT' && <FileCheck className="w-3.5 h-3.5 text-emerald-600" />}
                                  {ev.type === 'DOCUMENT' && <FolderOpen className="w-3.5 h-3.5 text-purple-600" />}
                                  {ev.type === 'REFERRAL' && <Share2 className="w-3.5 h-3.5 text-orange-600" />}
                                  {ev.type === 'REFERRAL_RESPONSE' && <Share2 className="w-3.5 h-3.5 text-purple-600" />}
                                  {ev.type === 'FOLLOWUP' && <Calendar className="w-3.5 h-3.5 text-blue-600" />}
                                </div>

                                <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2 hover:bg-white transition shadow-2xs">
                                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                                    <div className="flex items-center gap-2 flex-wrap">
                                      {ev.has_time === false ? (
                                        <span className="font-mono text-[10px] font-bold text-slate-600 bg-slate-200/80 border border-slate-300 px-2 py-0.5 rounded-md">
                                          {ev.time_display || 'Registration time not recorded'}
                                        </span>
                                      ) : (
                                        <span className="font-mono text-[11px] font-bold text-blue-700 bg-blue-100/80 border border-blue-200 px-2 py-0.5 rounded-md shadow-2xs">
                                          {timeStr}
                                        </span>
                                      )}
                                      <span className="font-bold text-slate-900 text-xs">{ev.title}</span>
                                    </div>

                                    <button
                                      type="button"
                                      onClick={() => toggleTimelineItem(itemKey)}
                                      className="self-end sm:self-center flex items-center gap-1 text-[11px] font-bold text-blue-600 hover:text-blue-800 transition py-0.5 px-2 rounded-md hover:bg-blue-50 cursor-pointer"
                                    >
                                      {isExpanded ? (
                                        <>
                                          <span>Collapse Details</span>
                                          <ChevronDown className="w-3.5 h-3.5" />
                                        </>
                                      ) : (
                                        <>
                                          <span>View Structured EMR</span>
                                          <ChevronRight className="w-3.5 h-3.5" />
                                        </>
                                      )}
                                    </button>
                                  </div>

                                  <p className="text-[11px] text-slate-700 leading-relaxed font-medium">{ev.details}</p>

                                  <div className="flex justify-between items-center text-[10px] text-slate-500 font-semibold pt-1 border-t border-slate-200/60">
                                    <span>Facility: <strong className="text-slate-700">{ev.facility}</strong></span>
                                    {ev.doctor_or_staff && (
                                      <span>Clinician / Staff: <strong className="text-slate-700">{ev.doctor_or_staff}</strong></span>
                                    )}
                                  </div>

                                  {isExpanded && renderExpandedEventDetails(ev)}
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
                    <th className="p-3">Attending Doctor</th>
                    <th className="p-3">Queue Status</th>
                    <th className="p-3">Completed Time</th>
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
                      <td className="p-3 text-slate-800 font-semibold">{v.assigned_doctor_name || 'Unassigned'}</td>
                      <td className="p-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-200">
                          {v.status}
                        </span>
                      </td>
                      <td className="p-3 font-mono text-slate-600 text-[11px]">{v.completed_time || '-'}</td>
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
                    <th className="p-3">Specimen Sample</th>
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
                      <td className="p-3 text-[11px]">
                        {lo.sample_code ? (
                          <div>
                            <strong className="font-mono text-cyan-800">{lo.sample_code}</strong> ({lo.sample_type})
                            {lo.sample_collected_at && (
                              <span className="block font-mono text-[10px] text-slate-400">
                                {lo.sample_collected_at} {lo.sample_collected_by ? `• ${lo.sample_collected_by}` : ''}
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-slate-400 italic">Not collected</span>
                        )}
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
                      <td className="p-3">
                        {lo.result_value ? (
                          <div>
                            <span className="font-mono font-bold text-slate-900">{lo.result_value} {lo.unit || ''}</span>
                            {lo.reference_range && (
                              <span className="block text-[10px] text-slate-500 font-mono">Ref: {lo.reference_range}</span>
                            )}
                          </div>
                        ) : (
                          <span className="text-slate-400 italic">Pending Result</span>
                        )}
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

                  {p.dispensed_transactions && p.dispensed_transactions.length > 0 && (
                    <div className="pt-2 border-t border-slate-200">
                      <span className="text-[11px] font-bold text-slate-800 block mb-1.5 flex items-center gap-1.5">
                        <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                        Pharmacy Dispensing Audit Records ({p.dispensed_transactions.length})
                      </span>
                      <div className="overflow-x-auto bg-white rounded-lg border border-slate-200 p-2">
                        <table className="w-full text-left text-[11px]">
                          <thead>
                            <tr className="text-slate-500 font-bold border-b border-slate-100">
                              <th className="pb-1">Medicine</th>
                              <th className="pb-1">Batch #</th>
                              <th className="pb-1">Qty Dispensed</th>
                              <th className="pb-1">Dispensed At</th>
                              <th className="pb-1">Pharmacist</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100 font-medium">
                            {p.dispensed_transactions.map((tx: any) => (
                              <tr key={tx.id}>
                                <td className="py-1 font-bold text-slate-900">{tx.medicine_name}</td>
                                <td className="py-1 font-mono text-slate-700">{tx.batch_number}</td>
                                <td className="py-1 font-mono font-bold text-emerald-700">{tx.quantity} Units</td>
                                <td className="py-1 font-mono text-slate-600">{tx.dispensed_at}</td>
                                <td className="py-1 text-slate-700">{tx.dispensed_by}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
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
