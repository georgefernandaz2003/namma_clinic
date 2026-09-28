import React, { useState, useEffect, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import api from '../services/api';
import type { Visit, TriageVitals, LabOrder } from '../types';
import { useAuth } from '../context/AuthContext';
import { useConfirm } from '../context/ConfirmContext';
import {
  FileText, Pill, Share2, Plus, Trash2, TestTube,
  Clock, CheckCircle2, AlertTriangle, AlertCircle, RefreshCw,
  ChevronDown, ChevronUp, FlaskConical
} from 'lucide-react';
import { ICD10Select } from '../components/ui/ICD10Select';

export const Consultation: React.FC = () => {
  const { activeFacility, allFacilities, user } = useAuth();
  const { confirm } = useConfirm();
  const location = useLocation();
  const navigate = useNavigate();
  const queryParams = new URLSearchParams(location.search);
  const targetVisitId = location.state?.visitId || (queryParams.get('visit') ? parseInt(queryParams.get('visit')!) : null);

  const [triagedVisits, setTriagedVisits] = useState<Visit[]>([]);
  const [selectedVisit, setSelectedVisit] = useState<Visit | null>(null);
  const [vitals, setVitals] = useState<TriageVitals | null>(null);
  const [labOrders, setLabOrders] = useState<LabOrder[]>([]);
  const [loadingLab, setLoadingLab] = useState(false);
  const [patientLabHistory, setPatientLabHistory] = useState<LabOrder[]>([]);
  const [showPreviousLabHistory, setShowPreviousLabHistory] = useState(false);

  // Form states
  const [chiefComplaint, setChiefComplaint] = useState('');
  const [history] = useState('Known history of hypertension, poor compliance.');
  const [assessment, setAssessment] = useState('High BP 148/96 mmHg with elevated blood glucose.');
  const [diagCode, setDiagCode] = useState('E11.9 / I10');
  const [diagName, setDiagName] = useState('Type 2 Diabetes Mellitus with Essential Hypertension');
  const [notes] = useState('Advised low salt diet, lifestyle modifications, and regular monitoring.');

  // Prescription items
  const [prescriptions, setPrescriptions] = useState<Array<{ medicine_name: string; dosage: string; quantity: number }>>([
    { medicine_name: 'Metformin HCl 500 mg Tablet', dosage: '1-0-1 After Food', quantity: 28 },
    { medicine_name: 'Amlodipine Besylate 5 mg Tablet', dosage: '1-0-0 Morning', quantity: 14 }
  ]);

  // Referral creation state
  const [createReferral, setCreateReferral] = useState(true);
  const [destFacilityId, setDestFacilityId] = useState<number | ''>('');
  const [refReason, setRefReason] = useState('Specialist evaluation for uncontrolled hypertension');
  const [refUrgency, setRefUrgency] = useState<'ROUTINE' | 'URGENT' | 'EMERGENCY'>('HIGH' as any);

  // Diagnostic Tests (14 Essential Tests) State
  const [availableTests, setAvailableTests] = useState<any[]>([]);
  const [selectedTestIds, setSelectedTestIds] = useState<number[]>([]);

  // Follow-up State
  const [followUpDate, setFollowUpDate] = useState<string>('');
  const [followUpCategory, setFollowUpCategory] = useState<string>('ROUTINE_MONITORING');
  const [followUpNotes, setFollowUpNotes] = useState<string>('Review BP & blood sugar in 14 days');

  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const fetchLabTests = async () => {
      try {
        const res = await api.get('lab/tests/');
        const tests = res.data.results || res.data || [];
        setAvailableTests(tests);
      } catch (e) {
        console.error('Failed to load lab test master', e);
      }
    };
    fetchLabTests();
  }, []);

  const loadQueue = async () => {
    if (!activeFacility) return;
    try {
      const res = await api.get(`visits/?facility=${activeFacility.id}&queue=DOCTOR`);
      const rawList: Visit[] = res.data.results || res.data || [];
      const activeDoctorList = rawList.filter((v) => v.current_queue === 'DOCTOR' && v.status !== 'COMPLETED');

      // Strictly isolate to the logged-in doctor's assigned patients only
      const myVisits = activeDoctorList.filter(
        (v) =>
          v.assigned_doctor === user?.id ||
          (v.assigned_doctor_name && user?.full_name && v.assigned_doctor_name.toLowerCase().includes(user.full_name.toLowerCase()))
      );
      setTriagedVisits(myVisits);

      if (targetVisitId) {
        const found = myVisits.find((v) => v.id === targetVisitId);
        if (found) {
          selectVisit(found);
        } else if (myVisits.length > 0) {
          selectVisit(myVisits[0]);
        } else {
          setSelectedVisit(null);
          setVitals(null);
          setLabOrders([]);
          setPatientLabHistory([]);
        }
      } else if (myVisits.length > 0) {
        selectVisit(myVisits[0]);
      } else {
        setSelectedVisit(null);
        setVitals(null);
        setLabOrders([]);
        setPatientLabHistory([]);
      }
    } catch (e) {
      console.error('Failed to load doctor queue', e);
    }
  };

  const selectVisit = async (v: Visit) => {
    setSelectedVisit(v);
    setSelectedTestIds([]);
    setChiefComplaint(v.chief_complaint || 'Dizziness and fatigue');
    try {
      const trRes = await api.get(`triage/?visit=${v.id}`);
      const trList = trRes.data.results || trRes.data || [];
      if (trList.length > 0) setVitals(trList[0]);
      else setVitals(null);
    } catch (e) {
      setVitals(null);
    }

    try {
      setLoadingLab(true);
      const labRes = await api.get(`lab/orders/?visit=${v.id}`);
      const labList: LabOrder[] = labRes.data.results || labRes.data || [];
      setLabOrders(labList);

      const patId = v.patient || v.patient_details?.id;
      if (patId) {
        const histRes = await api.get(`lab/orders/?patient=${patId}`);
        const histList: LabOrder[] = histRes.data.results || histRes.data || [];
        setPatientLabHistory(histList);
      } else {
        setPatientLabHistory([]);
      }
    } catch (e) {
      console.error('Failed to load lab orders for consultation', e);
      setLabOrders([]);
      setPatientLabHistory([]);
    } finally {
      setLoadingLab(false);
    }

    try {
      const cRes = await api.get(`consultations/?visit=${v.id}`);
      const cList = cRes.data.results || cRes.data || [];
      if (cList.length > 0) {
        const c = cList[0];
        if (c.diagnosis_code) setDiagCode(c.diagnosis_code);
        if (c.diagnosis_name) setDiagName(c.diagnosis_name);
        if (c.clinical_assessment) setAssessment(c.clinical_assessment);
        if (c.chief_complaint) setChiefComplaint(c.chief_complaint);
      }
    } catch (e) {
      // ignore
    }
  };

  useEffect(() => {
    loadQueue();
  }, [activeFacility, targetVisitId]);

  const [networkFacilities, setNetworkFacilities] = useState<any[]>([]);

  useEffect(() => {
    const fetchNetworkFacilities = async () => {
      try {
        const res = await api.get('facilities/?all=true');
        const facs = res.data.results || res.data || [];
        setNetworkFacilities(facs);
      } catch (e) {
        console.error('Failed to load network facilities', e);
      }
    };
    fetchNetworkFacilities();
  }, []);

  // Filter local referral destination options
  const referralDestinations = useMemo(() => {
    const list = networkFacilities.length > 0 ? networkFacilities : allFacilities;
    return list.filter((f) => f.id !== activeFacility?.id);
  }, [networkFacilities, allFacilities, activeFacility]);

  useEffect(() => {
    if (referralDestinations.length > 0) {
      const exists = referralDestinations.some((f) => f.id === destFacilityId);
      if (!exists || !destFacilityId) {
        setDestFacilityId(referralDestinations[0].id);
      }
    }
  }, [referralDestinations, destFacilityId]);

  const handleAddMed = () => {
    setPrescriptions([...prescriptions, { medicine_name: 'Paracetamol 650 mg Tablet', dosage: '1-0-1', quantity: 10 }]);
  };

  const handleRemoveMed = (idx: number) => {
    setPrescriptions(prescriptions.filter((_, i) => i !== idx));
  };

  const toggleTestSelection = (testId: number) => {
    if (selectedTestIds.includes(testId)) {
      setSelectedTestIds(selectedTestIds.filter((id) => id !== testId));
    } else {
      setSelectedTestIds([...selectedTestIds, testId]);
    }
  };

  const handleSaveConsultation = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedVisit || !activeFacility) return;

    const patientName = selectedVisit.patient_details?.name || 'Patient';
    const tokenNum = selectedVisit.token_details?.token_number || selectedVisit.id;

    confirm({
      title: 'Confirm Consultation Completion',
      message: `Are you sure you want to complete this clinical consultation and save records for ${patientName}?`,
      confirmText: 'Complete Consultation & Issue Orders',
      cancelText: 'Cancel',
      variant: 'success',
      loadingText: 'Finalizing Consultation...',
      details: [
        { label: 'Patient Name', value: patientName },
        { label: 'Token / Visit', value: `Token #${tokenNum}` },
        { label: 'Attending Doctor', value: user?.full_name ? `Dr. ${user.full_name}` : (user?.username || 'Medical Officer') },
        { label: 'Diagnosis', value: diagName },
        { label: 'Prescriptions', value: `${prescriptions.length} Medicines Prescribed` },
        { label: 'Laboratory Orders', value: selectedTestIds.length > 0 ? `${selectedTestIds.length} Tests Ordered` : 'None' },
        { label: 'Referral', value: createReferral && destFacilityId ? 'Yes (Specialist Referral)' : 'No' },
        { label: 'Follow-up Date', value: followUpDate || 'None Scheduled' }
      ],
      onConfirm: async () => {
        setSaving(true);
        try {
          // 1. Save Consultation & Prescription & Lab Test Requisitions
          const consultRes = await api.post('consultations/', {
            visit: selectedVisit.id,
            patient: selectedVisit.patient,
            facility: activeFacility.id,
            chief_complaint: chiefComplaint,
            clinical_history: history,
            clinical_assessment: assessment,
            diagnosis_code: diagCode,
            diagnosis_name: diagName,
            clinical_notes: notes,
            prescription_items: prescriptions,
            lab_test_ids: selectedTestIds
          });

          // 2. Save Referral if checked
          if (createReferral && destFacilityId) {
            await api.post('referrals/', {
              patient: selectedVisit.patient,
              source_facility: activeFacility.id,
              destination_facility: destFacilityId,
              reason: refReason,
              clinical_summary: `${diagName} - BP ${vitals?.blood_pressure_systolic || 140}/${vitals?.blood_pressure_diastolic || 90} mmHg`,
              required_service: 'Specialist Consultation',
              urgency: refUrgency
            });
          }

          // 3. Save Diagnostic Lab Orders (idempotent fallback)
          for (const testId of selectedTestIds) {
            try {
              await api.post('lab/orders/', {
                visit: selectedVisit.id,
                consultation: consultRes.data?.id,
                patient: selectedVisit.patient,
                facility: activeFacility.id,
                test_master: testId
              });
            } catch (err) {
              console.error('Failed to order lab test', err);
            }
          }

          // 4. Save Scheduled Follow-up
          if (followUpDate) {
            try {
              await api.post('followups/', {
                patient: selectedVisit.patient,
                facility: activeFacility.id,
                due_date: followUpDate,
                category: followUpCategory,
                notes: followUpNotes
              });
            } catch (err) {
              console.error('Failed to schedule follow-up', err);
            }
          }

          setSelectedTestIds([]);
          await loadQueue();
          navigate('/queue');
        } finally {
          setSaving(false);
        }
      }
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <FileText className="w-6 h-6 text-blue-600" />
          Doctor Console & EMR-Lite Workflow
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Primary care EMR documentation, diagnosis, prescriptions, and cross-facility referral creation
        </p>
      </div>

      {/* EMR-Lite Value Proposition Banner */}
      <div className="bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 p-4 rounded-2xl text-white space-y-1 shadow-md">
        <div className="flex items-center gap-2 text-xs font-black uppercase tracking-wider text-blue-400">
          <span>📋 Streamlined Primary Care EMR-Lite</span>
        </div>
        <p className="text-xs text-blue-100 font-medium leading-relaxed">
          &ldquo;We are designing this EMR-lite for a busy primary-care doctor, not a heavy hospital ERP.&rdquo;
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Doctor Queue */}
        <div className="glass-panel p-4 rounded-2xl border border-slate-200 bg-white space-y-3 shadow-xs">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <h2 className="text-xs font-bold uppercase tracking-wider text-teal-700 flex items-center gap-1.5">
              <span>My Assigned Queue</span>
              <span className="bg-teal-100 text-teal-800 px-1.5 py-0.5 rounded-full font-mono text-[10px]">
                {triagedVisits.length}
              </span>
            </h2>
            <span className="text-[10px] font-bold text-teal-800 bg-teal-50 px-2 py-0.5 rounded-full border border-teal-200">
              Dr. {user?.full_name || user?.username}
            </span>
          </div>

          {triagedVisits.length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-400">
              No waiting patients currently assigned to Dr. {user?.full_name || user?.username}.
            </div>
          ) : (
            <div className="space-y-2 max-h-[500px] overflow-y-auto">
              {triagedVisits.map((v) => (
                <div
                  key={v.id}
                  onClick={() => selectVisit(v)}
                  className={`p-3 rounded-xl border transition cursor-pointer ${
                    selectedVisit?.id === v.id
                      ? 'bg-blue-50 border-blue-500 text-slate-900 shadow-xs'
                      : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-xs">{v.patient_details?.name}</span>
                    <span className="text-[10px] font-mono text-teal-700 font-bold">Token #{v.token_details?.token_number || v.id}</span>
                  </div>
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-[10px] text-slate-500 truncate max-w-[140px]">{v.patient_details?.age} yrs • {v.chief_complaint}</span>
                    {v.status === 'LAB_COMPLETED' ? (
                      <span className="text-[9px] font-extrabold px-1.5 py-0.5 rounded bg-purple-100 text-purple-800 border border-purple-200">
                        Lab Ready
                      </span>
                    ) : null}
                  </div>
                  <div className="mt-1.5 pt-1 border-t border-slate-100 flex items-center justify-between">
                    <span className="text-[9px] font-semibold text-teal-800 bg-teal-50 px-1.5 py-0.5 rounded border border-teal-200/60 truncate max-w-[200px]">
                      🩺 Assigned to Dr. {user?.full_name || user?.username}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* EMR Console & Form */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-slate-200 bg-white space-y-5 shadow-xs">
          {selectedVisit ? (
            <form onSubmit={handleSaveConsultation} className="space-y-5 text-xs">
              {/* Patient, Vitals & History Summary */}
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
                <div className="flex justify-between items-start">
                  <div>
                    <h2 className="text-base font-bold text-slate-900">{selectedVisit.patient_details?.name}</h2>
                    <p className="text-xs text-slate-500">
                      ID: {selectedVisit.patient_details?.patient_id} • Age: {selectedVisit.patient_details?.age} • Gender: {selectedVisit.patient_details?.gender}
                    </p>
                    <div className="mt-1.5 flex items-center gap-2">
                      <span className="text-[10px] font-bold text-teal-800 bg-teal-50 px-2 py-0.5 rounded border border-teal-200 flex items-center gap-1">
                        🩺 Attending Physician: Dr. {user?.full_name || user?.username}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => navigate(`/patients/${selectedVisit.patient_details?.id || selectedVisit.patient}`)}
                      className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-white text-blue-700 border border-blue-200 hover:bg-blue-50 transition flex items-center gap-1 shadow-2xs"
                    >
                      <FileText className="w-3.5 h-3.5" /> View EMR Timeline History
                    </button>
                    <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-200">
                      Token #{selectedVisit.token_details?.token_number || 1}
                    </span>
                  </div>
                </div>

                {vitals && (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-200 text-[11px]">
                    <div className="bg-white p-2 rounded border border-slate-200">
                      <span className="text-[10px] text-slate-500 block font-semibold">BP Vitals</span>
                      <span className={`font-bold font-mono ${vitals.high_bp_flag ? 'text-rose-600' : 'text-slate-800'}`}>
                        {vitals.blood_pressure_systolic}/{vitals.blood_pressure_diastolic} mmHg
                      </span>
                    </div>
                    <div className="bg-white p-2 rounded border border-slate-200">
                      <span className="text-[10px] text-slate-500 block font-semibold">Pulse / Temp</span>
                      <span className="font-bold font-mono text-slate-800">{vitals.pulse_bpm} bpm • {vitals.temperature_f}°F</span>
                    </div>
                    <div className="bg-white p-2 rounded border border-slate-200">
                      <span className="text-[10px] text-slate-500 block font-semibold">Blood Glucose</span>
                      <span className={`font-bold font-mono ${vitals.high_glucose_flag ? 'text-amber-600' : 'text-slate-800'}`}>
                        {vitals.blood_glucose_mgdl} mg/dL
                      </span>
                    </div>
                    <div className="bg-white p-2 rounded border border-slate-200">
                      <span className="text-[10px] text-slate-500 block font-semibold">BMI</span>
                      <span className="font-bold font-mono text-slate-800">{vitals.bmi}</span>
                    </div>
                  </div>
                )}

                {/* Laboratory Diagnostic Results */}
                <div className="pt-3 border-t border-slate-200 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                      <FlaskConical className="w-4 h-4 text-purple-600" />
                      <span>Lab Diagnostic Results</span>
                      {labOrders.length > 0 && (
                        <span className="px-1.5 py-0.5 text-[10px] rounded-full bg-purple-100 text-purple-800 font-mono font-bold">
                          {labOrders.length} test{labOrders.length > 1 ? 's' : ''}
                        </span>
                      )}
                    </div>
                    {patientLabHistory.length > labOrders.length && (
                      <button
                        type="button"
                        onClick={() => setShowPreviousLabHistory(!showPreviousLabHistory)}
                        className="text-[10px] font-bold text-purple-700 hover:text-purple-900 flex items-center gap-1 hover:underline cursor-pointer"
                      >
                        {showPreviousLabHistory ? (
                          <>Hide Past Lab Records ({patientLabHistory.length}) <ChevronUp className="w-3 h-3" /></>
                        ) : (
                          <>Show All Patient Lab Records ({patientLabHistory.length}) <ChevronDown className="w-3 h-3" /></>
                        )}
                      </button>
                    )}
                  </div>

                  {loadingLab ? (
                    <div className="p-3 bg-white rounded-lg border border-slate-200 text-center text-slate-400 text-xs flex items-center justify-center gap-2">
                      <RefreshCw className="w-3.5 h-3.5 animate-spin text-purple-600" />
                      <span>Loading laboratory investigations...</span>
                    </div>
                  ) : (labOrders.length === 0 && !showPreviousLabHistory) ? (
                    <div className="p-3 bg-white/70 rounded-lg border border-slate-200 text-slate-500 text-[11px] flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <TestTube className="w-4 h-4 text-slate-400" />
                        <span>No lab tests ordered for this current visit yet.</span>
                      </div>
                      <span className="text-[10px] text-slate-400">Order from EDL Diagnostic Tests below</span>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                      {(showPreviousLabHistory ? patientLabHistory : labOrders).map((order) => {
                        const hasResult = Boolean(order.result && order.result.result_value);
                        const flag = order.result?.interpretation_flag;
                        const isCritical = flag === 'CRITICAL';
                        const isAbnormal = flag && ['HIGH', 'LOW', 'CRITICAL'].includes(flag);

                        return (
                          <div
                            key={order.id}
                            className={`p-2.5 rounded-lg border transition text-[11px] flex flex-col justify-between ${
                              isCritical
                                ? 'bg-rose-50/90 border-rose-300 ring-1 ring-rose-200'
                                : isAbnormal
                                ? 'bg-amber-50/80 border-amber-300 ring-1 ring-amber-200'
                                : order.status === 'VERIFIED'
                                ? 'bg-emerald-50/60 border-emerald-300'
                                : 'bg-white border-slate-200'
                            }`}
                          >
                            <div className="flex items-start justify-between gap-1.5 pb-1 border-b border-slate-100">
                              <div>
                                <span className="font-bold text-slate-900 block leading-snug">
                                  {order.test_name || `Test #${order.test_master}`}
                                </span>
                                {order.test_code && (
                                  <span className="text-[9px] font-mono text-slate-400 block">
                                    {order.test_code}
                                  </span>
                                )}
                              </div>
                              <span
                                className={`text-[9px] font-black uppercase px-1.5 py-0.5 rounded tracking-wide shrink-0 font-mono ${
                                  order.status === 'VERIFIED'
                                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                                    : order.status === 'SAMPLE_COLLECTED'
                                    ? 'bg-purple-100 text-purple-800 border border-purple-200'
                                    : 'bg-slate-100 text-slate-700 border border-slate-200'
                                }`}
                              >
                                {order.status === 'VERIFIED' ? 'Verified' : order.status.replace('_', ' ')}
                              </span>
                            </div>

                            {hasResult ? (
                              <div className="pt-1.5 space-y-1">
                                <div className="flex items-baseline justify-between">
                                  <div className="flex items-baseline gap-1">
                                    <span className="text-[10px] text-slate-500 font-medium">Result:</span>
                                    <span
                                      className={`text-base font-extrabold font-mono ${
                                        isCritical
                                          ? 'text-rose-700'
                                          : isAbnormal
                                          ? 'text-amber-700'
                                          : 'text-emerald-700'
                                      }`}
                                    >
                                      {order.result?.result_value}
                                    </span>
                                    <span className="text-[10px] text-slate-600 font-medium">
                                      {order.result?.unit}
                                    </span>
                                  </div>

                                  {flag && (
                                    <span
                                      className={`text-[9px] font-extrabold px-1.5 py-0.5 rounded uppercase font-mono ${
                                        isCritical
                                          ? 'bg-rose-200 text-rose-900 animate-pulse'
                                          : isAbnormal
                                          ? 'bg-amber-200 text-amber-900'
                                          : 'bg-emerald-100 text-emerald-800'
                                      }`}
                                    >
                                      {flag}
                                    </span>
                                  )}
                                </div>

                                {order.result?.reference_range && (
                                  <div className="text-[10px] text-slate-500 font-mono">
                                    <span className="font-semibold text-slate-600">Ref:</span> {order.result.reference_range}
                                  </div>
                                )}

                                {order.result?.notes && (
                                  <div className="text-[10px] text-slate-600 italic bg-white/60 p-1 rounded border border-slate-200/50">
                                    &ldquo;{order.result.notes}&rdquo;
                                  </div>
                                )}
                              </div>
                            ) : (
                              <div className="pt-2 flex items-center gap-1.5 text-[10px] text-slate-500">
                                <Clock className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                                <span>
                                  {order.status === 'SAMPLE_COLLECTED'
                                    ? 'Sample collected in lab. Analysis pending.'
                                    : 'Lab order created. Specimen collection pending.'}
                                </span>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>

              {/* Chief Complaint & Assessment */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Chief Complaint *</label>
                  <input
                    type="text"
                    value={chiefComplaint}
                    onChange={(e) => setChiefComplaint(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-blue-600"
                    required
                  />
                </div>
                <ICD10Select
                  value={diagName}
                  code={diagCode}
                  onChange={(newCode, newName) => {
                    setDiagCode(newCode);
                    setDiagName(newName);
                  }}
                  required
                />
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Clinical Assessment & Examination</label>
                <textarea
                  value={assessment}
                  onChange={(e) => setAssessment(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-blue-600"
                />
              </div>

              {/* Prescription Section */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                <div className="flex justify-between items-center">
                  <h3 className="font-bold text-slate-900 flex items-center gap-1.5 text-xs">
                    <Pill className="w-4 h-4 text-amber-600" />
                    Prescribe Medication (EDL List - FEFO Dispensing Ready)
                  </h3>
                  <button
                    type="button"
                    onClick={handleAddMed}
                    className="flex items-center gap-1 px-2.5 py-1 bg-white border border-slate-300 hover:bg-slate-100 text-amber-800 rounded-lg text-[11px] font-bold"
                  >
                    <Plus className="w-3.5 h-3.5" /> Add Medicine
                  </button>
                </div>

                <div className="space-y-2">
                  {prescriptions.map((p, idx) => (
                    <div key={idx} className="flex items-center gap-2 bg-white p-2 rounded-lg border border-slate-200">
                      <input
                        type="text"
                        value={p.medicine_name}
                        onChange={(e) => {
                          const updated = [...prescriptions];
                          updated[idx].medicine_name = e.target.value;
                          setPrescriptions(updated);
                        }}
                        className="flex-1 px-2 py-1 bg-slate-50 border border-slate-300 rounded text-slate-900 text-xs font-semibold"
                      />
                      <input
                        type="text"
                        value={p.dosage}
                        onChange={(e) => {
                          const updated = [...prescriptions];
                          updated[idx].dosage = e.target.value;
                          setPrescriptions(updated);
                        }}
                        className="w-32 px-2 py-1 bg-slate-50 border border-slate-300 rounded text-slate-900 text-xs"
                      />
                      <input
                        type="number"
                        value={p.quantity}
                        onChange={(e) => {
                          const updated = [...prescriptions];
                          updated[idx].quantity = parseInt(e.target.value) || 0;
                          setPrescriptions(updated);
                        }}
                        className="w-16 px-2 py-1 bg-slate-50 border border-slate-300 rounded text-slate-900 text-xs font-mono font-bold"
                      />
                      <button
                        type="button"
                        onClick={() => handleRemoveMed(idx)}
                        className="p-1 text-slate-400 hover:text-rose-600"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Order Diagnostic Investigations (14 Essential Tests) */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                <h3 className="font-bold text-slate-900 flex items-center gap-1.5 text-xs">
                  <FileText className="w-4 h-4 text-teal-600" />
                  Order 14 Essential Diagnostic Tests (Point-of-Care & Hub Lab)
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] max-h-48 overflow-y-auto pr-1">
                  {availableTests.map((t) => {
                    const isSelected = selectedTestIds.includes(t.id);
                    return (
                      <label
                        key={t.id}
                        onClick={() => toggleTestSelection(t.id)}
                        className={`p-2 rounded-lg border flex items-center justify-between cursor-pointer transition select-none ${
                          isSelected
                            ? 'bg-teal-50 border-teal-500 text-teal-900 font-bold'
                            : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-100'
                        }`}
                      >
                        <span>{t.name}</span>
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => {}}
                          className="w-3.5 h-3.5 text-teal-600 rounded border-slate-300"
                        />
                      </label>
                    );
                  })}
                </div>
              </div>

              {/* Cross-Facility Referral Creation */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="refCheck"
                    checked={createReferral}
                    onChange={(e) => setCreateReferral(e.target.checked)}
                    className="w-4 h-4 text-emerald-600 rounded bg-white border-slate-300"
                  />
                  <label htmlFor="refCheck" className="font-bold text-slate-900 flex items-center gap-1.5 cursor-pointer">
                    <Share2 className="w-4 h-4 text-rose-600" />
                    Raise Cross-Facility Referral to Secondary/Specialist Hospital Hub
                  </label>
                </div>

                {createReferral && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                    <div>
                      <label className="block text-slate-700 font-bold mb-1">Select Destination Facility *</label>
                      <select
                        value={destFacilityId}
                        onChange={(e) => setDestFacilityId(parseInt(e.target.value))}
                        className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-900 font-medium focus:outline-none focus:border-blue-600"
                        required={createReferral}
                      >
                        {referralDestinations.length === 0 ? (
                          <option value="" disabled>Loading available referral facilities...</option>
                        ) : (
                          referralDestinations.map((f) => (
                            <option key={f.id} value={f.id}>
                              {f.facility_name} ({f.facility_type ? f.facility_type.replace('_', ' ') : 'Hospital'})
                            </option>
                          ))
                        )}
                      </select>
                      {destFacilityId ? (
                        <p className="text-[11px] text-slate-500 mt-1">
                          Connected referral hub for secondary/tertiary specialist review.
                        </p>
                      ) : null}
                    </div>

                    <div>
                      <label className="block text-slate-700 font-bold mb-1">Urgency Priority</label>
                      <select
                        value={refUrgency}
                        onChange={(e) => setRefUrgency(e.target.value as any)}
                        className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-900"
                      >
                        <option value="ROUTINE">Routine Referral</option>
                        <option value="URGENT">Urgent Evaluation</option>
                        <option value="EMERGENCY">Emergency Referral</option>
                      </select>
                    </div>

                    <div className="sm:col-span-2">
                      <label className="block text-slate-700 font-bold mb-1">Referral Reason</label>
                      <input
                        type="text"
                        value={refReason}
                        onChange={(e) => setRefReason(e.target.value)}
                        className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-900"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Schedule Follow-up Visit */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                <h3 className="font-bold text-slate-900 flex items-center gap-1.5 text-xs">
                  <FileText className="w-4 h-4 text-purple-600" />
                  Schedule Follow-Up Visit
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div>
                    <label className="block text-slate-700 font-bold mb-1">Follow-Up Date</label>
                    <input
                      type="date"
                      value={followUpDate}
                      onChange={(e) => setFollowUpDate(e.target.value)}
                      className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-900"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-700 font-bold mb-1">Follow-Up Notes</label>
                    <input
                      type="text"
                      value={followUpNotes}
                      onChange={(e) => setFollowUpNotes(e.target.value)}
                      className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-900"
                    />
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={saving}
                className="w-full py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-xs rounded-xl shadow-md transition"
              >
                {saving ? 'Saving Consultation...' : 'Complete Consultation & Issue Orders'}
              </button>
            </form>
          ) : (
            <div className="p-12 text-center text-xs text-slate-400 space-y-3">
              <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto border border-blue-200">
                <FileText className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-bold text-slate-800">
                {triagedVisits.length === 0
                  ? `No Patients Waiting for Dr. ${user?.full_name || user?.username}`
                  : 'Select a Patient to Consult'}
              </h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                {triagedVisits.length === 0
                  ? 'Patients triaged and assigned to your clinical consultation desk by the triage nurse will appear in your queue.'
                  : 'Select an assigned patient from your queue on the left to begin consultation.'}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
