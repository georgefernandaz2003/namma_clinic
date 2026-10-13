import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { canAccessPatientDocuments } from '../../utils/permissions';
import {
  Clock, User, Activity, Stethoscope, FileText, Pill,
  Building2, FolderOpen, CheckCircle2, X, ShieldAlert,
  Eye, Download, File
} from 'lucide-react';

export interface VisitDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  visitId: number | string | null;
  patient?: any;
  initialVisitData?: any;
}

export const VisitDetailsModal: React.FC<VisitDetailsModalProps> = ({
  isOpen,
  onClose,
  visitId,
  patient,
  initialVisitData
}) => {
  const { user } = useAuth();
  const isFrontDeskOfficer = user?.role === 'FRONT_DESK_OFFICER';
  const isLabTech = user?.role === 'LAB_TECHNICIAN';
  const isPharmacist = user?.role === 'PHARMACIST';
  const canAccessDocuments = canAccessPatientDocuments(user?.role);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedVisitData, setSelectedVisitData] = useState<{
    visit: any;
    patient: any;
    triage: any | null;
    consultation: any | null;
    labReports: any[];
    prescriptions: any[];
    documents: any[];
    followUp: any | null;
  } | null>(null);

  // Document Preview Modal State
  const [previewDoc, setPreviewDoc] = useState<any | null>(null);
  const [downloadingDocId, setDownloadingDocId] = useState<number | null>(null);

  useEffect(() => {
    if (!isOpen || !visitId) {
      setSelectedVisitData(null);
      setError(null);
      return;
    }

    if (initialVisitData) {
      setSelectedVisitData(initialVisitData);
      setLoading(false);
      return;
    }

    let isMounted = true;
    const fetchVisitTransaction = async () => {
      setLoading(true);
      setError(null);

      try {
        // 1. Fetch target visit detail
        const visitRes = await api.get(`visits/${visitId}/?date=all`);
        const fullVisit = visitRes.data;
        const targetPatientId = fullVisit.patient || patient?.id;

        // 2. Fetch triage vitals (if authorized)
        let triageData: any = null;
        if (!isFrontDeskOfficer && !isLabTech && !isPharmacist) {
          try {
            const triageRes = await api.get(`triage/?visit=${visitId}`);
            if (triageRes.data) {
              const list = Array.isArray(triageRes.data)
                ? triageRes.data
                : (Array.isArray(triageRes.data.results) ? triageRes.data.results : (triageRes.data.id ? [triageRes.data] : []));
              if (list.length > 0) {
                triageData = list[0];
              }
            }
          } catch (err) {
            console.warn('Could not fetch triage vitals for visit', err);
          }
        }

        // 3. Fetch structured patient records & timeline
        let records: any = {
          medical_records: [],
          lab_reports: [],
          prescriptions: [],
          documents: []
        };
        let timeline: any[] = [];
        let resolvedPatient = patient || null;

        if (targetPatientId) {
          try {
            const [recordsRes, timelineRes] = await Promise.all([
              api.get(`patients/${targetPatientId}/records/`).catch(() => ({ data: {} })),
              api.get(`patients/${targetPatientId}/timeline/`).catch(() => ({ data: {} }))
            ]);

            if (recordsRes.data) {
              records = {
                medical_records: recordsRes.data.medical_records || [],
                lab_reports: recordsRes.data.lab_reports || [],
                prescriptions: recordsRes.data.prescriptions || [],
                documents: recordsRes.data.documents || []
              };
              if (!resolvedPatient) {
                resolvedPatient = recordsRes.data.patient;
              }
            }

            if (timelineRes.data) {
              timeline = timelineRes.data.timeline || [];
              if (!resolvedPatient) {
                resolvedPatient = timelineRes.data.patient;
              }
            }
          } catch (err) {
            console.warn('Could not fetch patient records for visit', err);
          }
        }

        // 4. Fetch direct consultation or match by exact visit ID
        let matchingConsultation: any = null;
        if (!isFrontDeskOfficer && !isLabTech && !isPharmacist && user?.role !== 'NURSE') {
          try {
            const consultRes = await api.get(`consultations/?visit=${visitId}`);
            if (consultRes.data) {
              const list = Array.isArray(consultRes.data)
                ? consultRes.data
                : (Array.isArray(consultRes.data.results) ? consultRes.data.results : (consultRes.data.id ? [consultRes.data] : []));
              if (list.length > 0) {
                const rawC = list[0];
                matchingConsultation = {
                  id: rawC.id,
                  visit_id: fullVisit.visit_id,
                  created_at: rawC.created_at,
                  facility_name: rawC.facility_name || fullVisit.facility_name,
                  doctor_name: rawC.doctor_name || 'Medical Officer',
                  chief_complaint: rawC.chief_complaint,
                  clinical_history: rawC.clinical_history,
                  clinical_assessment: rawC.clinical_assessment,
                  diagnosis_code: rawC.diagnosis_code,
                  diagnosis_name: rawC.diagnosis_name,
                  treatment_plan: rawC.treatment_plan,
                  clinical_notes: rawC.clinical_notes,
                  follow_up_date: rawC.follow_up_date,
                  prescription: rawC.prescription
                };
              }
            }
          } catch (err) {
            console.warn('Could not fetch direct consultation for visit', err);
          }
        }

        if (!matchingConsultation && records.medical_records) {
          matchingConsultation = records.medical_records.find((c: any) =>
            c.visit_id && (c.visit_id === fullVisit.visit_id || c.visit_id === String(fullVisit.id) || c.visit === fullVisit.id)
          ) || null;
        }

        // 5. Match lab reports
        let matchingLabReports: any[] = [];
        if (!isFrontDeskOfficer && !isPharmacist) {
          try {
            const labRes = await api.get(`lab/orders/?visit=${visitId}`);
            if (labRes.data) {
              const list = Array.isArray(labRes.data)
                ? labRes.data
                : (Array.isArray(labRes.data.results) ? labRes.data.results : []);
              if (list.length > 0) {
                matchingLabReports = list;
              }
            }
          } catch (err) {
            console.warn('Could not fetch direct lab orders for visit', err);
          }
        }
        if (matchingLabReports.length === 0 && records.lab_reports) {
          matchingLabReports = records.lab_reports.filter((l: any) =>
            l.visit_id && (l.visit_id === fullVisit.visit_id || l.visit_id === fullVisit.id)
          );
        }

        // 6. Match prescriptions
        let matchingPrescriptions: any[] = [];
        if (matchingConsultation?.prescription) {
          matchingPrescriptions = [matchingConsultation.prescription];
        } else if (!isFrontDeskOfficer && !isLabTech) {
          try {
            const rxRes = await api.get(`prescriptions/?visit=${visitId}`);
            if (rxRes.data) {
              const list = Array.isArray(rxRes.data)
                ? rxRes.data
                : (Array.isArray(rxRes.data.results) ? rxRes.data.results : []);
              if (list.length > 0) {
                matchingPrescriptions = list.filter((p: any) =>
                  !matchingConsultation?.id || p.consultation === matchingConsultation.id || p.consultation_id === matchingConsultation.id
                );
              }
            }
          } catch (err) {
            console.warn('Could not fetch direct prescriptions for visit', err);
          }
        }
        if (matchingPrescriptions.length === 0 && records.prescriptions) {
          matchingPrescriptions = records.prescriptions.filter((p: any) =>
            p.visit_id && (p.visit_id === fullVisit.visit_id || p.visit_id === fullVisit.id)
          );
        }

        // 7. Match documents
        const matchingDocs = (records.documents || []).filter((d: any) =>
          d.visit_id ? (d.visit_id === fullVisit.visit_id || d.visit_id === fullVisit.id) : true
        );

        // 8. Match follow-up
        const targetDate = fullVisit.visit_date ? fullVisit.visit_date.slice(0, 10) : '';
        const matchingFollowUp = timeline.find((ev: any) =>
          ev.type === 'FOLLOWUP' && (
            (targetDate && ev.date && ev.date.slice(0, 10) === targetDate) ||
            (matchingConsultation && matchingConsultation.follow_up_date)
          )
        );

        if (isMounted) {
          setSelectedVisitData({
            visit: fullVisit,
            patient: resolvedPatient || {
              name: fullVisit.patient_name || 'Patient',
              patient_id: fullVisit.patient_id || 'ID N/A'
            },
            triage: triageData,
            consultation: matchingConsultation,
            labReports: matchingLabReports,
            prescriptions: matchingPrescriptions,
            documents: matchingDocs.length > 0 ? matchingDocs : records.documents,
            followUp: matchingFollowUp || (matchingConsultation?.follow_up_date ? { due_date: matchingConsultation.follow_up_date } : null)
          });
        }
      } catch (err: any) {
        console.error('Failed to load visit details modal data', err);
        if (isMounted) {
          setError('Failed to load visit encounter details.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchVisitTransaction();
    return () => {
      isMounted = false;
    };
  }, [isOpen, visitId, patient, initialVisitData, isFrontDeskOfficer, isLabTech, isPharmacist, user?.role]);

  // Secure Document Download
  const handleDownloadDocument = async (doc: any) => {
    const targetPatientId = selectedVisitData?.patient?.id || selectedVisitData?.visit?.patient;
    if (!targetPatientId) return;

    setDownloadingDocId(doc.id);
    try {
      const res = await api.get(`patients/${targetPatientId}/documents/${doc.id}/download/`, {
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
    } catch {
      alert('Failed to download document. You may not have required permissions.');
    } finally {
      setDownloadingDocId(null);
    }
  };

  if (!isOpen) return null;

  const currentPatient = selectedVisitData?.patient || patient || {
    name: selectedVisitData?.visit?.patient_name || 'Patient',
    patient_id: selectedVisitData?.visit?.patient_id || 'ID N/A'
  };

  return (
    <>
      <div
        className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in duration-150"
        role="dialog"
        aria-modal="true"
        aria-labelledby="visit-details-modal-title"
        onClick={(e) => {
          if (e.target === e.currentTarget) onClose();
        }}
      >
        <div className="bg-white rounded-2xl border border-slate-200 max-w-4xl w-full max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
          {/* Modal Header */}
          <div className="p-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/70">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-blue-100 text-blue-700 rounded-xl">
                <Clock className="w-5 h-5" aria-hidden="true" />
              </div>
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <h2 id="visit-details-modal-title" className="text-base font-bold text-slate-900">
                    Visit Details — {selectedVisitData?.visit?.visit_id || (visitId ? `Encounter #${visitId}` : 'Loading...')}
                  </h2>
                  {selectedVisitData?.visit && (
                    <>
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold font-mono bg-blue-100 text-blue-800 border border-blue-200">
                        Token #{selectedVisitData.visit.token_details?.token_number || selectedVisitData.visit.token_number || selectedVisitData.visit.id}
                      </span>
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
                        {selectedVisitData.visit.status || 'Active'}
                      </span>
                    </>
                  )}
                </div>
                <p className="text-xs text-slate-500 font-medium mt-0.5">
                  {currentPatient.name} ({currentPatient.patient_id}) • {selectedVisitData?.visit?.facility_name || 'Namma Clinic Local PHC'} • {selectedVisitData?.visit?.visit_date || 'Date N/A'}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              aria-label="Close modal"
              className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-xl transition cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Modal Scrollable Body */}
          <div className="p-6 overflow-y-auto space-y-6 text-xs flex-1">
            {loading ? (
              <div className="py-12 text-center text-slate-500 space-y-2">
                <div className="w-7 h-7 border-3 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
                <p className="text-xs font-medium">Loading clinical transaction details...</p>
              </div>
            ) : error ? (
              <div className="p-6 text-center text-rose-600 bg-rose-50 rounded-xl border border-rose-200">
                <p className="font-bold">{error}</p>
                <p className="text-xs text-rose-500 mt-1">Please try reopening or contact your clinic administrator.</p>
              </div>
            ) : selectedVisitData ? (
              <>
                {/* 1. Patient & Visit Encounter Information */}
                <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-3 shadow-2xs">
                  <div className="flex items-center gap-2 text-slate-900 font-bold border-b border-slate-100 pb-2">
                    <User className="w-4 h-4 text-blue-600" aria-hidden="true" />
                    <span>1. Patient & Visit Encounter Information</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
                    <div>
                      <span className="text-[11px] text-slate-500 font-medium block">Patient Name / ID</span>
                      <span className="font-bold text-slate-900">{currentPatient.name} ({currentPatient.patient_id})</span>
                    </div>
                    <div>
                      <span className="text-[11px] text-slate-500 font-medium block">Visit Number</span>
                      <span className="font-bold font-mono text-emerald-700">{selectedVisitData.visit.visit_id || `#${selectedVisitData.visit.id}`}</span>
                    </div>
                    <div>
                      <span className="text-[11px] text-slate-500 font-medium block">Visit Type</span>
                      <span className="font-bold text-slate-800">{selectedVisitData.visit.visit_type?.replace(/_/g, ' ') || 'GENERAL OPD'}</span>
                    </div>
                    <div>
                      <span className="text-[11px] text-slate-500 font-medium block">Facility</span>
                      <span className="font-bold text-slate-800">{selectedVisitData.visit.facility_name || 'Namma Clinic Local PHC'}</span>
                    </div>
                    <div>
                      <span className="text-[11px] text-slate-500 font-medium block">Visit Date / Time</span>
                      <span className="font-bold font-mono text-slate-800">{selectedVisitData.visit.visit_date || selectedVisitData.visit.arrival_time || 'No data recorded'}</span>
                    </div>
                    <div>
                      <span className="text-[11px] text-slate-500 font-medium block">Visit Status</span>
                      <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-200">
                        {selectedVisitData.visit.status || 'Active'}
                      </span>
                    </div>
                    <div className="sm:col-span-2">
                      <span className="text-[11px] text-slate-500 font-medium block">Chief Complaint</span>
                      <span className="font-bold text-slate-900">{selectedVisitData.visit.chief_complaint || selectedVisitData.consultation?.chief_complaint || 'No data recorded'}</span>
                    </div>
                  </div>
                </div>

                {/* 2. OPD & Queue Management Details */}
                <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-3 shadow-2xs">
                  <div className="flex items-center gap-2 text-slate-900 font-bold border-b border-slate-100 pb-2">
                    <Clock className="w-4 h-4 text-emerald-600" aria-hidden="true" />
                    <span>2. OPD & Queue Management Details</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div>
                      <span className="text-[11px] text-slate-500 font-medium block">Token Number</span>
                      <span className="font-black text-blue-700 font-mono text-sm">
                        {selectedVisitData.visit.token_details?.token_number || selectedVisitData.visit.token_number
                          ? `#${selectedVisitData.visit.token_details?.token_number || selectedVisitData.visit.token_number}`
                          : 'No data recorded'}
                      </span>
                    </div>
                    <div>
                      <span className="text-[11px] text-slate-500 font-medium block">Queue Status</span>
                      <span className="font-bold text-slate-800">{selectedVisitData.visit.current_queue || selectedVisitData.visit.queue || 'No data recorded'}</span>
                    </div>
                    <div>
                      <span className="text-[11px] text-slate-500 font-medium block">Priority Tag</span>
                      <span className="font-bold text-slate-800">{selectedVisitData.visit.priority || 'NORMAL'}</span>
                    </div>
                  </div>
                  {/* Status History Transitions */}
                  <div className="pt-2 border-t border-slate-100 space-y-1.5">
                    <span className="text-[11px] text-slate-500 font-bold block">Encounter Status Audit Trail & Intake Notes</span>
                    {selectedVisitData.visit.status_history_list && selectedVisitData.visit.status_history_list.length > 0 ? (
                      <div className="space-y-1.5">
                        {selectedVisitData.visit.status_history_list.map((h: any, hIdx: number) => (
                          <div key={hIdx} className="p-2 bg-slate-50 rounded-lg border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-[11px]">
                            <div>
                              <span className="font-bold text-slate-900">{h.from_status || 'START'} → {h.to_status}</span>
                              {h.notes && <span className="text-slate-600 ml-2 italic font-normal">({h.notes})</span>}
                            </div>
                            <div className="text-slate-500 font-mono text-[10px]">
                              {h.performed_by_name || h.performed_by_role || 'Staff'} • {h.timestamp ? new Date(h.timestamp).toLocaleTimeString() : ''}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-slate-600">Standard OPD registration completed and queued for clinical consultation.</p>
                    )}
                  </div>
                </div>

                {/* 3. Nurse Triage Assessment & Vitals */}
                <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-3 shadow-2xs">
                  <div className="flex items-center gap-2 text-slate-900 font-bold border-b border-slate-100 pb-2">
                    <Activity className="w-4 h-4 text-rose-600" aria-hidden="true" />
                    <span>3. Nurse Triage Assessment & Vitals</span>
                  </div>
                  {(isFrontDeskOfficer || isLabTech || isPharmacist) ? (
                    <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-xl text-amber-900 text-xs flex items-center gap-2 font-medium">
                      <ShieldAlert className="w-4 h-4 text-amber-600 flex-shrink-0" aria-hidden="true" />
                      <span>Clinical triage vitals are restricted to authorized clinical staff (Doctor / Nurse).</span>
                    </div>
                  ) : selectedVisitData.triage ? (
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-200">
                          <span className="text-[10px] text-slate-500 block">Blood Pressure</span>
                          <span className="font-bold text-slate-900 font-mono">
                            {selectedVisitData.triage.blood_pressure_systolic} / {selectedVisitData.triage.blood_pressure_diastolic} mmHg
                          </span>
                        </div>
                        <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-200">
                          <span className="text-[10px] text-slate-500 block">Pulse Rate</span>
                          <span className="font-bold text-slate-900 font-mono">{selectedVisitData.triage.pulse_bpm} bpm</span>
                        </div>
                        <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-200">
                          <span className="text-[10px] text-slate-500 block">Temperature</span>
                          <span className="font-bold text-slate-900 font-mono">{selectedVisitData.triage.temperature_f}°F</span>
                        </div>
                        <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-200">
                          <span className="text-[10px] text-slate-500 block">SpO2 Saturation</span>
                          <span className="font-bold text-slate-900 font-mono">{selectedVisitData.triage.spo2_percent}%</span>
                        </div>
                        <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-200">
                          <span className="text-[10px] text-slate-500 block">Respiratory Rate</span>
                          <span className="font-bold text-slate-900 font-mono">
                            {selectedVisitData.triage.respiratory_rate ? `${selectedVisitData.triage.respiratory_rate} /min` : 'No data recorded'}
                          </span>
                        </div>
                        <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-200">
                          <span className="text-[10px] text-slate-500 block">Height / Weight / BMI</span>
                          <span className="font-bold text-slate-900 font-mono">
                            {selectedVisitData.triage.height_cm}cm / {selectedVisitData.triage.weight_kg}kg (BMI {selectedVisitData.triage.bmi})
                          </span>
                        </div>
                        <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-200">
                          <span className="text-[10px] text-slate-500 block">Blood Glucose</span>
                          <span className="font-bold text-slate-900 font-mono">
                            {selectedVisitData.triage.blood_glucose_mgdl ? `${selectedVisitData.triage.blood_glucose_mgdl} mg/dL` : 'No data recorded'}
                          </span>
                        </div>
                        <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-200">
                          <span className="text-[10px] text-slate-500 block">Acuity Tag</span>
                          <div className="flex flex-wrap gap-1 mt-0.5">
                            {selectedVisitData.triage.emergency_flag && <span className="px-1.5 py-0.5 bg-rose-100 text-rose-800 text-[10px] font-bold rounded">Emergency 🚨</span>}
                            {selectedVisitData.triage.high_bp_flag && <span className="px-1.5 py-0.5 bg-amber-100 text-amber-800 text-[10px] font-bold rounded">High BP</span>}
                            {selectedVisitData.triage.fever_flag && <span className="px-1.5 py-0.5 bg-amber-100 text-amber-800 text-[10px] font-bold rounded">Fever</span>}
                            {selectedVisitData.triage.low_spo2_flag && <span className="px-1.5 py-0.5 bg-rose-100 text-rose-800 text-[10px] font-bold rounded">Low SpO2</span>}
                            {!selectedVisitData.triage.emergency_flag && !selectedVisitData.triage.high_bp_flag && !selectedVisitData.triage.fever_flag && !selectedVisitData.triage.low_spo2_flag && (
                              <span className="text-slate-700 font-bold text-[10px]">Normal Acuity</span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div>
                        <span className="text-[11px] text-slate-500 font-bold block mb-1">Nurse Assessment Notes</span>
                        <p className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-slate-700 font-medium">
                          {selectedVisitData.triage.nurse_notes || 'No assessment notes recorded'}
                        </p>
                      </div>
                    </div>
                  ) : (
                    <p className="text-slate-400 italic">No data recorded</p>
                  )}
                </div>

                {/* 4. Doctor Consultation & Clinical Diagnosis */}
                <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-3 shadow-2xs">
                  <div className="flex items-center gap-2 text-slate-900 font-bold border-b border-slate-100 pb-2">
                    <Stethoscope className="w-4 h-4 text-indigo-600" aria-hidden="true" />
                    <span>4. Doctor Consultation & Clinical Diagnosis</span>
                  </div>
                  {(isFrontDeskOfficer || isLabTech || isPharmacist || user?.role === 'NURSE') ? (
                    <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-xl text-amber-900 text-xs flex items-center gap-2 font-medium">
                      <ShieldAlert className="w-4 h-4 text-amber-600 flex-shrink-0" aria-hidden="true" />
                      <span>Doctor clinical consultation records, diagnoses, and examination notes are restricted to authorized medical personnel.</span>
                    </div>
                  ) : selectedVisitData.consultation ? (
                    <div className="space-y-3">
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                        <div>
                          <span className="text-[11px] text-slate-500 font-medium block">Attending Doctor</span>
                          <span className="font-bold text-slate-900">{selectedVisitData.consultation.doctor_name || selectedVisitData.visit.assigned_doctor_name || 'Medical Officer'}</span>
                        </div>
                        <div>
                          <span className="text-[11px] text-slate-500 font-medium block">Consultation Status</span>
                          <span className="font-bold text-slate-800">
                            {selectedVisitData.visit.status === 'COMPLETED' ? 'Completed & Finalized' : 'Consultation In Progress'}
                          </span>
                        </div>
                        <div>
                          <span className="text-[11px] text-slate-500 font-medium block">Diagnosis (ICD Code)</span>
                          <span className="font-bold text-indigo-900 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded inline-block font-mono">
                            {selectedVisitData.consultation.diagnosis_name} [{selectedVisitData.consultation.diagnosis_code}]
                          </span>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div>
                          <span className="text-[11px] text-slate-500 font-bold block mb-1">Clinical History & Complaints</span>
                          <p className="p-2.5 bg-slate-50 rounded-xl border border-slate-200 text-slate-700 font-medium">
                            {selectedVisitData.consultation.clinical_history || selectedVisitData.consultation.chief_complaint || 'No data recorded'}
                          </p>
                        </div>
                        <div>
                          <span className="text-[11px] text-slate-500 font-bold block mb-1">Clinical Assessment & Examination</span>
                          <p className="p-2.5 bg-slate-50 rounded-xl border border-slate-200 text-slate-700 font-medium">
                            {selectedVisitData.consultation.clinical_assessment || 'No data recorded'}
                          </p>
                        </div>
                      </div>

                      <div>
                        <span className="text-[11px] text-slate-500 font-bold block mb-1">Treatment Plan & Clinical Notes</span>
                        <p className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-slate-700 font-medium leading-relaxed">
                          {selectedVisitData.consultation.treatment_plan || selectedVisitData.consultation.clinical_notes || 'No data recorded'}
                        </p>
                      </div>
                    </div>
                  ) : (
                    <p className="text-slate-400 italic">No data recorded</p>
                  )}
                </div>

                {/* 5. Diagnostic Laboratory Investigations */}
                <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-3 shadow-2xs">
                  <div className="flex items-center gap-2 text-slate-900 font-bold border-b border-slate-100 pb-2">
                    <FileText className="w-4 h-4 text-teal-600" aria-hidden="true" />
                    <span>5. Diagnostic Laboratory Investigations</span>
                  </div>
                  {(isFrontDeskOfficer || isPharmacist) ? (
                    <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-xl text-amber-900 text-xs flex items-center gap-2 font-medium">
                      <ShieldAlert className="w-4 h-4 text-amber-600 flex-shrink-0" aria-hidden="true" />
                      <span>Diagnostic laboratory investigations and specimen results are restricted to Doctor and Lab Technician roles.</span>
                    </div>
                  ) : selectedVisitData.labReports && selectedVisitData.labReports.length > 0 ? (
                    <div className="space-y-2">
                      {selectedVisitData.labReports.map((l: any, lIdx: number) => (
                        <div key={lIdx} className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                          <div className="flex justify-between items-center">
                            <span className="font-bold text-slate-900">{l.test_name} ({l.test_code})</span>
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-100 text-teal-800 border border-teal-200">
                              {l.status}
                            </span>
                          </div>
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
                            <div>
                              <span className="text-slate-500 block">Specimen</span>
                              <span className="font-bold text-slate-800">{l.sample_code ? `Specimen #${l.sample_code}` : 'Specimen collected'}</span>
                            </div>
                            <div>
                              <span className="text-slate-500 block">Result Value</span>
                              <span className="font-bold text-slate-900 font-mono">{l.result_value ? `${l.result_value} ${l.unit || ''}` : 'Pending'}</span>
                            </div>
                            <div>
                              <span className="text-slate-500 block">Interpretation</span>
                              <span className="font-bold text-slate-800">{l.interpretation_flag || 'Normal'}</span>
                            </div>
                            <div>
                              <span className="text-slate-500 block">Validation</span>
                              <span className="font-bold text-slate-800">{l.verified_by ? `Validated by ${l.verified_by}` : 'Pending validation'}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-400 italic">No data recorded</p>
                  )}
                </div>

                {/* 6. Medical Prescription */}
                <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-3 shadow-2xs">
                  <div className="flex items-center gap-2 text-slate-900 font-bold border-b border-slate-100 pb-2">
                    <Pill className="w-4 h-4 text-amber-600" aria-hidden="true" />
                    <span>6. Medical Prescription</span>
                  </div>
                  {(isFrontDeskOfficer || isLabTech) ? (
                    <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-xl text-amber-900 text-xs flex items-center gap-2 font-medium">
                      <ShieldAlert className="w-4 h-4 text-amber-600 flex-shrink-0" aria-hidden="true" />
                      <span>Prescription medication orders are restricted to Doctor, Nurse, and Pharmacist roles.</span>
                    </div>
                  ) : selectedVisitData.prescriptions && selectedVisitData.prescriptions.length > 0 ? (
                    <div className="space-y-3">
                      {selectedVisitData.prescriptions.map((rx: any, rxIdx: number) => (
                        <div key={rxIdx} className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                          <div className="flex justify-between items-center text-xs">
                            <div>
                              Prescriber: <strong className="text-slate-900">{rx.doctor_name || 'Medical Officer'}</strong>
                              <span className="text-slate-400 font-mono ml-2">({rx.date})</span>
                            </div>
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
                              {rx.status}
                            </span>
                          </div>
                          {rx.items && rx.items.length > 0 ? (
                            <div className="overflow-x-auto">
                              <table className="w-full text-left text-[11px] border-collapse bg-white rounded-lg overflow-hidden border border-slate-200">
                                <thead className="bg-slate-100/70 text-slate-700 font-bold">
                                  <tr>
                                    <th className="p-2">Medicine</th>
                                    <th className="p-2">Dose</th>
                                    <th className="p-2">Frequency</th>
                                    <th className="p-2">Duration</th>
                                    <th className="p-2">Quantity</th>
                                    <th className="p-2">Instructions</th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                  {rx.items.map((it: any, itIdx: number) => (
                                    <tr key={itIdx}>
                                      <td className="p-2 font-bold text-slate-900">{it.medicine_name}</td>
                                      <td className="p-2 font-mono text-slate-700">{it.dosage}</td>
                                      <td className="p-2 text-slate-700">{it.frequency}</td>
                                      <td className="p-2 text-slate-700">{it.duration_days} days</td>
                                      <td className="p-2 font-mono font-bold text-slate-900">{it.quantity}</td>
                                      <td className="p-2 text-slate-600">{it.dosage ? `${it.dosage}, ${it.frequency}` : 'As prescribed'}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          ) : (
                            <p className="text-slate-400 italic">No prescription items listed.</p>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-400 italic">No data recorded</p>
                  )}
                </div>

                {/* 7. Pharmacy Dispensing & Stock Verification */}
                <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-3 shadow-2xs">
                  <div className="flex items-center gap-2 text-slate-900 font-bold border-b border-slate-100 pb-2">
                    <Building2 className="w-4 h-4 text-blue-600" aria-hidden="true" />
                    <span>7. Pharmacy Dispensing & Stock Verification</span>
                  </div>
                  {(isFrontDeskOfficer || isLabTech || user?.role === 'NURSE') ? (
                    <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-xl text-amber-900 text-xs flex items-center gap-2 font-medium">
                      <ShieldAlert className="w-4 h-4 text-amber-600 flex-shrink-0" aria-hidden="true" />
                      <span>Pharmacy dispensing records are restricted to Pharmacist and Clinical Administration.</span>
                    </div>
                  ) : selectedVisitData.prescriptions && selectedVisitData.prescriptions.some((rx: any) => rx.status === 'DISPENSED' || rx.status === 'VERIFIED' || rx.items?.some((it: any) => it.status === 'DISPENSED')) ? (
                    <div className="space-y-3">
                      {selectedVisitData.prescriptions.filter((rx: any) => rx.status === 'DISPENSED' || rx.status === 'VERIFIED' || rx.items?.some((it: any) => it.status === 'DISPENSED')).map((rx: any, rxIdx: number) => (
                        <div key={rxIdx} className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
                            <div>
                              <span className="text-slate-500 block">Pharmacist</span>
                              <span className="font-bold text-slate-900">{rx.verified_by || 'Staff Pharmacist'}</span>
                            </div>
                            <div>
                              <span className="text-slate-500 block">Verification Status</span>
                              <span className="font-bold text-emerald-700">{rx.status === 'VERIFIED' || rx.status === 'DISPENSED' ? 'Verified by Pharmacist' : rx.status}</span>
                            </div>
                            <div>
                              <span className="text-slate-500 block">Dispensing Status</span>
                              <span className="font-bold text-slate-900">{rx.status === 'DISPENSED' ? 'Fully Dispensed' : 'Partially Dispensed'}</span>
                            </div>
                            <div>
                              <span className="text-slate-500 block">Dispensing Date / Time</span>
                              <span className="font-bold font-mono text-slate-800">{rx.date || 'Encounter date'}</span>
                            </div>
                          </div>
                          <div className="p-2 bg-white rounded-lg border border-slate-200 text-[11px]">
                            <span className="text-slate-500 block mb-1">FEFO Allocation & Quantity:</span>
                            <div className="flex flex-wrap gap-2">
                              {rx.items?.map((it: any, iIdx: number) => (
                                <span key={iIdx} className="px-2 py-0.5 bg-slate-100 rounded text-slate-800 font-medium">
                                  {it.medicine_name}: <strong>{it.dispensed_quantity || it.quantity} units</strong> (FEFO Allocated)
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-400 italic">No data recorded</p>
                  )}
                </div>

                {/* 8. Patient Documents & Uploads */}
                <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-3 shadow-2xs">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                    <div className="flex items-center gap-2 text-slate-900 font-bold">
                      <FolderOpen className="w-4 h-4 text-purple-600" aria-hidden="true" />
                      <span>8. Patient Documents & Uploads</span>
                    </div>
                  </div>
                  {isFrontDeskOfficer ? (
                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                      <p className="text-slate-600 text-[11px]">
                        Front Desk Officers are authorized to upload intake and identity documents. Confidential clinical document viewing is restricted.
                      </p>
                    </div>
                  ) : selectedVisitData.documents && selectedVisitData.documents.length > 0 ? (
                    <div className="space-y-2">
                      {selectedVisitData.documents.map((doc: any, dIdx: number) => (
                        <div key={dIdx} className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between gap-3 text-xs flex-wrap">
                          <div>
                            <div className="font-bold text-slate-900 flex items-center gap-2">
                              <span>{doc.title}</span>
                              <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-purple-100 text-purple-800">
                                {doc.document_type_display || doc.document_type}
                              </span>
                            </div>
                            <p className="text-[11px] text-slate-500 font-mono mt-0.5">
                              Uploaded on {doc.uploaded_at} by {doc.uploaded_by_name || 'Staff'} • {doc.file_name}
                            </p>
                          </div>
                          <div className="flex items-center gap-2">
                            {canAccessDocuments && (
                              <button
                                onClick={() => setPreviewDoc(doc)}
                                className="px-2.5 py-1 bg-white hover:bg-slate-100 text-slate-700 font-bold rounded-lg border border-slate-200 text-[11px] flex items-center gap-1 shadow-2xs cursor-pointer"
                              >
                                <Eye className="w-3 h-3 text-slate-500" />
                                <span>Preview</span>
                              </button>
                            )}
                            <button
                              onClick={() => handleDownloadDocument(doc)}
                              disabled={downloadingDocId === doc.id}
                              className="px-2.5 py-1 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-lg text-[11px] flex items-center gap-1 shadow-2xs cursor-pointer"
                            >
                              <Download className="w-3 h-3" />
                              <span>{downloadingDocId === doc.id ? 'Downloading...' : 'Download'}</span>
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-400 italic">No data recorded</p>
                  )}
                </div>

                {/* 9. Visit Completion & Follow-up Details */}
                <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-3 shadow-2xs">
                  <div className="flex items-center gap-2 text-slate-900 font-bold border-b border-slate-100 pb-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" aria-hidden="true" />
                    <span>9. Visit Completion & Follow-up Details</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div>
                      <span className="text-[11px] text-slate-500 font-medium block">Final Encounter Status</span>
                      <span className="font-bold text-slate-900">{selectedVisitData.visit.status || 'Active'}</span>
                    </div>
                    <div>
                      <span className="text-[11px] text-slate-500 font-medium block">Completion Timestamp</span>
                      <span className="font-bold font-mono text-slate-800">
                        {selectedVisitData.visit.completed_time
                          ? new Date(selectedVisitData.visit.completed_time).toLocaleString()
                          : (selectedVisitData.visit.status === 'COMPLETED' ? (selectedVisitData.visit.visit_date || 'Encounter concluded') : 'In progress')}
                      </span>
                    </div>
                    <div>
                      <span className="text-[11px] text-slate-500 font-medium block">Follow-up / Recall Schedule</span>
                      <span className="font-bold text-slate-900">
                        {selectedVisitData.followUp?.due_date || selectedVisitData.consultation?.follow_up_date
                          ? `Scheduled Date: ${selectedVisitData.followUp?.due_date || selectedVisitData.consultation?.follow_up_date}`
                          : 'No data recorded'}
                      </span>
                    </div>
                  </div>
                </div>
              </>
            ) : null}
          </div>

          {/* Modal Footer */}
          <div className="p-4 border-t border-slate-100 bg-slate-50 flex justify-end">
            <button
              onClick={onClose}
              className="px-5 py-2 bg-slate-900 hover:bg-slate-800 text-white font-bold rounded-xl text-xs shadow-sm transition cursor-pointer"
            >
              Close Visit Details
            </button>
          </div>
        </div>
      </div>

      {/* Document Preview Modal */}
      {previewDoc && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 z-60 animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden border border-slate-200">
            <div className="p-4 border-b border-slate-200 flex justify-between items-center bg-slate-50">
              <div className="flex items-center gap-2">
                <File className="w-5 h-5 text-purple-600" />
                <div>
                  <h3 className="font-bold text-slate-900 text-sm">{previewDoc.title}</h3>
                  <p className="text-[11px] text-slate-500 font-mono">{previewDoc.file_name}</p>
                </div>
              </div>
              <button
                onClick={() => setPreviewDoc(null)}
                className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 overflow-y-auto flex-1 flex items-center justify-center bg-slate-100 min-h-[300px]">
              {previewDoc.file?.toLowerCase().endsWith('.pdf') ? (
                <iframe src={previewDoc.file} title={previewDoc.title} className="w-full h-[500px] rounded-lg border border-slate-300" />
              ) : previewDoc.file?.match(/\.(jpeg|jpg|gif|png|webp)$/i) ? (
                <img src={previewDoc.file} alt={previewDoc.title} className="max-h-[500px] max-w-full rounded-lg shadow-md object-contain" />
              ) : (
                <div className="text-center p-8 bg-white rounded-xl shadow-xs border border-slate-200">
                  <File className="w-12 h-12 text-slate-400 mx-auto mb-2" />
                  <p className="font-bold text-slate-800">Preview not supported for this file format.</p>
                  <button
                    onClick={() => handleDownloadDocument(previewDoc)}
                    className="mt-4 px-4 py-2 bg-purple-600 text-white rounded-xl text-xs font-bold inline-flex items-center gap-1.5"
                  >
                    <Download className="w-4 h-4" /> Download File
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default VisitDetailsModal;
