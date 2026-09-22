import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import api from '../services/api';
import type { Visit, TriageVitals } from '../types';
import { useAuth } from '../context/AuthContext';
import { FileText, Pill, Share2, Plus, Trash2, TestTube, CheckCircle2, Clock } from 'lucide-react';

export const Consultation: React.FC = () => {
  const { activeFacility, allFacilities } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const queryVisitParam = new URLSearchParams(location.search).get('visit');
  const targetVisitId = location.state?.visitId || (queryVisitParam ? parseInt(queryVisitParam) : undefined);

  const [triagedVisits, setTriagedVisits] = useState<Visit[]>([]);
  const [selectedVisit, setSelectedVisit] = useState<Visit | null>(null);
  const [vitals, setVitals] = useState<TriageVitals | null>(null);

  // Form states
  const [chiefComplaint, setChiefComplaint] = useState('');
  const [history, setHistory] = useState('');
  const [assessment, setAssessment] = useState('');
  const [diagCode, setDiagCode] = useState('');
  const [diagName, setDiagName] = useState('');
  const [notes, setNotes] = useState('');

  // Prescription items (empty initially, doctor adds as needed)
  const [prescriptions, setPrescriptions] = useState<Array<{ medicine_id?: number | null; medicine_name: string; dosage: string; quantity: number }>>([]);
  const [availableMedicines, setAvailableMedicines] = useState<any[]>([]);

  // Referral creation state
  const [createReferral, setCreateReferral] = useState(false);
  const [destFacilityId, setDestFacilityId] = useState<number | ''>('');
  const [refReason, setRefReason] = useState('');
  const [refUrgency, setRefUrgency] = useState<'ROUTINE' | 'URGENT' | 'EMERGENCY'>('URGENT');

  // Diagnostic Tests (14 Essential Tests) State
  const [availableTests, setAvailableTests] = useState<any[]>([]);
  const [selectedTestIds, setSelectedTestIds] = useState<number[]>([]);

  // Laboratory Orders & Verified Results for current encounter
  const [visitLabOrders, setVisitLabOrders] = useState<any[]>([]);

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
    const fetchMedicines = async () => {
      try {
        const res = await api.get('pharmacy/medicines/');
        const meds = res.data.results || res.data || [];
        setAvailableMedicines(meds);
      } catch (e) {
        console.error('Failed to load medicines formulary', e);
      }
    };
    fetchLabTests();
    fetchMedicines();
  }, []);


  const loadQueue = async () => {
    if (!activeFacility) return;
    try {
      const res = await api.get(`visits/?facility=${activeFacility.id}&queue=DOCTOR`);
      const rawList: Visit[] = res.data.results || res.data || [];
      const activeDoctorList = rawList.filter((v) => v.current_queue === 'DOCTOR' && v.status !== 'COMPLETED');
      setTriagedVisits(activeDoctorList);

      if (targetVisitId) {
        let found = activeDoctorList.find((v) => v.id === targetVisitId);
        if (!found) {
          try {
            const singleRes = await api.get(`visits/${targetVisitId}/`);
            if (singleRes.data && singleRes.data.id) {
              found = singleRes.data;
              setTriagedVisits((prev) => [found!, ...prev.filter((x) => x.id !== found!.id)]);
            }
          } catch (err) {
            console.error('Failed to fetch specific visit for consultation', err);
          }
        }
        if (found) selectVisit(found);
        else if (activeDoctorList.length > 0) selectVisit(activeDoctorList[0]);
        else {
          setSelectedVisit(null);
          setVitals(null);
        }
      } else if (activeDoctorList.length > 0) {
        selectVisit(activeDoctorList[0]);
      } else {
        setSelectedVisit(null);
        setVitals(null);
      }
    } catch (e) {
      console.error('Failed to load doctor queue', e);
    }
  };


  const selectVisit = async (v: Visit) => {
    setSelectedVisit(v);
    setChiefComplaint(v.chief_complaint || '');
    setHistory('');
    setAssessment('');
    setDiagCode('');
    setDiagName('');
    setNotes('');
    setPrescriptions([]);
    setRefReason(v.chief_complaint ? `Specialist evaluation for ${v.chief_complaint}` : 'Specialist evaluation');
    setRefUrgency('URGENT');

    try {
      const trRes = await api.get(`triage/?visit=${v.id}`);
      const trList = trRes.data.results || trRes.data || [];
      if (trList.length > 0) {
        setVitals(trList[0]);
      } else {
        setVitals(null);
      }
    } catch (e) {
      setVitals(null);
    }

    try {
      const conRes = await api.get(`consultations/?visit=${v.id}`);
      const conList = conRes.data.results || conRes.data || [];
      if (conList.length > 0) {
        const con = conList[0];
        if (con.clinical_history) setHistory(con.clinical_history);
        if (con.clinical_assessment) setAssessment(con.clinical_assessment);
        if (con.diagnosis_code) setDiagCode(con.diagnosis_code);
        if (con.diagnosis_name) setDiagName(con.diagnosis_name);
        if (con.clinical_notes) setNotes(con.clinical_notes);
        if (con.treatment_plan && !notes) setNotes(con.treatment_plan);
        if (con.prescription?.items && con.prescription.items.length > 0) {
          setPrescriptions(con.prescription.items.map((it: any) => ({
            medicine_id: it.medicine,
            medicine_name: it.medicine_name,
            dosage: it.dosage,
            quantity: it.quantity
          })));
        }
      }
    } catch (e) {
      // ignore
    }

    try {
      const labRes = await api.get(`lab/orders/?visit=${v.id}`);
      const labList = labRes.data.results || labRes.data || [];
      setVisitLabOrders(labList);
      if (labList.length > 0) {
        // Preselect ordered tests in UI if already ordered
        setSelectedTestIds(labList.map((o: any) => o.test_master));
      } else {
        setSelectedTestIds([]);
      }
    } catch (e) {
      setVisitLabOrders([]);
      setSelectedTestIds([]);
    }
  };

  useEffect(() => {
    loadQueue();
  }, [activeFacility]);

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
  const referralDestinations = (networkFacilities.length > 0 ? networkFacilities : allFacilities).filter(
    (f) => f.id !== activeFacility?.id
  );

  useEffect(() => {
    if (referralDestinations.length > 0 && !destFacilityId) {
      setDestFacilityId(referralDestinations[0].id);
    }
  }, [referralDestinations]);

  const handleAddMed = () => {
    const firstMed = availableMedicines.length > 0 ? availableMedicines[0] : null;
    setPrescriptions([
      ...prescriptions,
      {
        medicine_id: firstMed?.id || null,
        medicine_name: firstMed ? `${firstMed.generic_name} ${firstMed.strength}` : 'Paracetamol 650 mg Tablet',
        dosage: '1-0-1 After Food',
        quantity: 10
      }
    ]);
  };

  const handleRemoveMed = (idx: number) => {
    setPrescriptions(prescriptions.filter((_, i) => i !== idx));
  };

  const toggleTestSelection = (testId: number) => {
    setSelectedTestIds((prev) =>
      prev.includes(testId) ? prev.filter((id) => id !== testId) : [...prev, testId]
    );
  };

  const handleSaveConsultation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedVisit || !activeFacility) return;
    setSaving(true);

    try {
      const isReviewFlow = selectedVisit.status === 'DOCTOR_REVIEW';
      const willOrderTests = selectedTestIds.length > 0 && !isReviewFlow;

      // 1. Save Consultation, Prescriptions & Diagnostic Lab Orders (Authoritative endpoint)
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
        has_lab_orders: willOrderTests,
        lab_test_ids: willOrderTests ? selectedTestIds : []
      });

      const consultationId = consultRes.data?.id;
      const createdLabTokenCode = consultRes.data?.lab_token_code || '';

      // 2. Save Referral if checked with authoritative Visit and Consultation links
      if (createReferral && destFacilityId) {
        await api.post('referrals/', {
          patient: selectedVisit.patient,
          visit: selectedVisit.id,
          consultation: consultationId,
          source_facility: activeFacility.id,
          destination_facility: destFacilityId,
          reason: refReason,
          clinical_summary: vitals?.blood_pressure_systolic ? `${diagName} - BP ${vitals.blood_pressure_systolic}/${vitals.blood_pressure_diastolic} mmHg` : diagName,
          required_service: 'Specialist Consultation',
          urgency: refUrgency
        });
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

      if (willOrderTests) {
        alert(`Laboratory Investigations Ordered!\n\nLAB Token: ${createdLabTokenCode || 'Generated'}\nEncounter Status: WAITING FOR LAB RESULTS\n\nPatient is routed to the diagnostic laboratory queue.`);
      } else {
        alert(`Consultation & Prescriptions finalized for ${selectedVisit.patient_details?.name || 'patient'}!`);
      }

      loadQueue();
      navigate('/queue');
    } catch (e) {
      alert('Failed to save consultation.');
    } finally {
      setSaving(false);
    }
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
          <h2 className="text-xs font-bold uppercase tracking-wider text-teal-700 flex items-center justify-between pb-2 border-b border-slate-100">
            <span>Patients Ready for Doctor</span>
            <span className="px-2 py-0.5 rounded bg-teal-100 text-teal-800 font-mono">
              {triagedVisits.length}
            </span>
          </h2>

          {triagedVisits.length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-400">No patients waiting in doctor queue.</div>
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
                  <span className="text-[10px] text-slate-500 block">{v.patient_details?.age} yrs • {v.chief_complaint}</span>
                  {(v.status === 'DOCTOR_REVIEW' || v.status === 'LAB_COMPLETED') && (
                    <span className="mt-1 inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold bg-purple-100 text-purple-800 border border-purple-200">
                      🔬 Lab Results Verified
                    </span>
                  )}
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
              </div>

              {/* Laboratory Investigation & Verified Results Section */}
              {visitLabOrders.length > 0 && (
                <div className="space-y-3">
                  {/* Status Banner */}
                  {(() => {
                    const isAllVerified = visitLabOrders.every((o: any) => o.status === 'VERIFIED');
                    const labTokenCode = visitLabOrders.find((o: any) => o.lab_token_code)?.lab_token_code || 'LAB-Active';
                    return (
                      <div className={`p-4 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                        isAllVerified ? 'bg-emerald-50 border-emerald-300 text-emerald-950 shadow-xs' : 'bg-amber-50 border-amber-300 text-amber-950 shadow-xs'
                      }`}>
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <TestTube className={`w-4 h-4 ${isAllVerified ? 'text-emerald-700' : 'text-amber-700'}`} />
                            <span className="font-bold text-xs uppercase tracking-wider">Laboratory Investigation</span>
                            <span className="px-2 py-0.5 rounded font-mono font-bold bg-white text-slate-900 border text-[11px] shadow-2xs">
                              LAB Token: {labTokenCode}
                            </span>
                          </div>
                          <p className="text-xs font-semibold">
                            {isAllVerified ? (
                              <span className="text-emerald-800">Status: VERIFIED — All ordered laboratory investigations completed and released.</span>
                            ) : (
                              <span className="text-amber-800">Status: WAITING FOR LAB RESULTS — Specimen processing in laboratory queue.</span>
                            )}
                          </p>
                        </div>
                        <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold self-start sm:self-auto uppercase tracking-wider border ${
                          isAllVerified ? 'bg-emerald-100 text-emerald-900 border-emerald-300' : 'bg-amber-100 text-amber-900 border-amber-300'
                        }`}>
                          {isAllVerified ? 'RESULTS VERIFIED' : 'WAITING FOR LAB'}
                        </span>
                      </div>
                    );
                  })()}

                  {/* Laboratory Results Table */}
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                    <div className="flex justify-between items-center">
                      <h3 className="font-bold text-slate-900 flex items-center gap-1.5 text-xs">
                        <TestTube className="w-4 h-4 text-purple-600" />
                        Active Encounter Laboratory Results
                      </h3>
                      <span className="text-[10px] font-semibold text-slate-500">
                        {visitLabOrders.filter((o: any) => o.status === 'VERIFIED').length} of {visitLabOrders.length} verified
                      </span>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs bg-white rounded-lg border border-slate-200 overflow-hidden shadow-2xs">
                        <thead className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200">
                          <tr>
                            <th className="p-2.5">Test Name</th>
                            <th className="p-2.5">Result</th>
                            <th className="p-2.5">Unit</th>
                            <th className="p-2.5">Reference Range</th>
                            <th className="p-2.5">Flag</th>
                            <th className="p-2.5">Verification Status</th>
                            <th className="p-2.5">Result Timestamp</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 text-[11px]">
                          {visitLabOrders.map((ord: any) => {
                            const res = ord.result;
                            const isVerified = ord.status === 'VERIFIED' && res;
                            return (
                              <tr key={ord.id} className="hover:bg-slate-50">
                                <td className="p-2.5 font-bold text-slate-900">{ord.test_name}</td>
                                <td className="p-2.5 font-mono font-bold text-slate-800">
                                  {isVerified ? res.result_value : <span className="text-slate-400 italic">Processing in Lab</span>}
                                </td>
                                <td className="p-2.5 text-slate-600 font-mono">{isVerified ? (res.unit || '—') : '—'}</td>
                                <td className="p-2.5 text-slate-600 font-mono">{isVerified ? (res.reference_range || '—') : '—'}</td>
                                <td className="p-2.5">
                                  {isVerified ? (
                                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                      res.interpretation_flag === 'CRITICAL' ? 'bg-rose-100 text-rose-800 border border-rose-300' :
                                      res.interpretation_flag === 'HIGH' ? 'bg-amber-100 text-amber-800 border border-amber-300' :
                                      res.interpretation_flag === 'LOW' ? 'bg-blue-100 text-blue-800 border border-blue-300' :
                                      'bg-emerald-100 text-emerald-800 border border-emerald-300'
                                    }`}>
                                      {res.interpretation_flag}
                                    </span>
                                  ) : (
                                    <span className="text-slate-400 italic">—</span>
                                  )}
                                </td>
                                <td className="p-2.5">
                                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                    isVerified ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' : 'bg-amber-100 text-amber-800 border border-amber-200'
                                  }`}>
                                    {ord.status.replace(/_/g, ' ')}
                                  </span>
                                </td>
                                <td className="p-2.5 font-mono text-slate-500">
                                  {isVerified && res.verified_at ? new Date(res.verified_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : '—'}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* Chief Complaint, Diagnosis, History, Assessment, and Notes */}
              <div className="space-y-3">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-700 font-bold mb-1">Chief Complaint *</label>
                    <input
                      type="text"
                      placeholder="e.g. Fever, cough, general malaise"
                      value={chiefComplaint}
                      onChange={(e) => setChiefComplaint(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-blue-600"
                      required
                    />
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <label className="block text-slate-700 font-bold mb-1">ICD-10 Code</label>
                      <input
                        type="text"
                        placeholder="e.g. J06.9"
                        value={diagCode}
                        onChange={(e) => setDiagCode(e.target.value)}
                        className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-blue-600 font-mono text-xs"
                      />
                    </div>
                    <div className="col-span-2">
                      <label className="block text-slate-700 font-bold mb-1">Diagnosis Name *</label>
                      <input
                        type="text"
                        placeholder="e.g. Acute Upper Respiratory Infection"
                        value={diagName}
                        onChange={(e) => setDiagName(e.target.value)}
                        className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-blue-600"
                        required
                      />
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-700 font-bold mb-1">Patient Clinical / Medical History</label>
                    <textarea
                      value={history}
                      onChange={(e) => setHistory(e.target.value)}
                      rows={2}
                      placeholder="Past illnesses, known allergies, chronic conditions..."
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-blue-600 text-xs"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-700 font-bold mb-1">Clinical Assessment & Examination</label>
                    <textarea
                      value={assessment}
                      onChange={(e) => setAssessment(e.target.value)}
                      rows={2}
                      placeholder="Clinical findings, systemic examination..."
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-blue-600 text-xs"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-slate-700 font-bold mb-1">Treatment Plan & Clinical Advice</label>
                  <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    rows={2}
                    placeholder="Diet, lifestyle advice, precautions, follow-up directions..."
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-blue-600 text-xs"
                  />
                </div>
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
                      {availableMedicines.length > 0 ? (
                        <select
                          value={p.medicine_id || ''}
                          onChange={(e) => {
                            const medId = parseInt(e.target.value) || null;
                            const found = availableMedicines.find((m) => m.id === medId);
                            const updated = [...prescriptions];
                            updated[idx].medicine_id = medId;
                            updated[idx].medicine_name = found ? `${found.generic_name} ${found.strength}` : p.medicine_name;
                            setPrescriptions(updated);
                          }}
                          className="flex-1 px-2 py-1 bg-slate-50 border border-slate-300 rounded text-slate-900 text-xs font-semibold"
                        >
                          <option value="">Select Medicine from Formulary...</option>
                          {availableMedicines.map((m) => (
                            <option key={m.id} value={m.id}>
                              {m.generic_name} ({m.brand_name || 'Generic'}) - {m.strength}
                            </option>
                          ))}
                        </select>
                      ) : (
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
                      )}
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
                        htmlFor={`test-check-${t.id}`}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            toggleTestSelection(t.id);
                          }
                        }}
                        className={`p-2 rounded-lg border flex items-center justify-between cursor-pointer transition select-none ${
                          isSelected
                            ? 'bg-teal-50 border-teal-500 text-teal-900 font-bold'
                            : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-100'
                        }`}
                      >
                        <span className="cursor-pointer">{t.name}</span>
                        <input
                          id={`test-check-${t.id}`}
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleTestSelection(t.id)}
                          className="w-3.5 h-3.5 text-teal-600 rounded border-slate-300 focus:ring-teal-500 cursor-pointer"
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
                        className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-900"
                      >
                        {referralDestinations.map((f) => (
                          <option key={f.id} value={f.id}>
                            {f.facility_name} ({f.facility_type.replace('_', ' ')})
                          </option>
                        ))}
                      </select>
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
                className={`w-full py-3 text-white font-bold text-xs rounded-xl shadow-md transition ${
                  selectedTestIds.length > 0 && selectedVisit.status !== 'DOCTOR_REVIEW'
                    ? 'bg-gradient-to-r from-teal-600 to-purple-600 hover:from-teal-500 hover:to-purple-500'
                    : selectedVisit.status === 'DOCTOR_REVIEW'
                    ? 'bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500'
                    : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500'
                }`}
              >
                {saving
                  ? 'Processing...'
                  : selectedTestIds.length > 0 && selectedVisit.status !== 'DOCTOR_REVIEW'
                  ? 'Order Lab Tests & Route to Laboratory Queue (Lab Token)'
                  : selectedVisit.status === 'DOCTOR_REVIEW'
                  ? 'Complete Doctor Review & Finalize Encounter'
                  : 'Complete Consultation & Finalize'}
              </button>
            </form>
          ) : (
            <div className="p-12 text-center text-xs text-slate-400">
              Select a triaged patient from the queue to start doctor consultation.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
