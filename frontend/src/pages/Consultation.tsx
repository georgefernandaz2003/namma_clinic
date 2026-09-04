import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import api from '../services/api';
import type { Visit, TriageVitals } from '../types';
import { useAuth } from '../context/AuthContext';
import { FileText, Pill, Share2, Plus, Trash2 } from 'lucide-react';

export const Consultation: React.FC = () => {
  const { activeFacility, allFacilities } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const stateVisitId = location.state?.visitId;

  const [triagedVisits, setTriagedVisits] = useState<Visit[]>([]);
  const [selectedVisit, setSelectedVisit] = useState<Visit | null>(null);
  const [vitals, setVitals] = useState<TriageVitals | null>(null);

  // Form states
  const [chiefComplaint, setChiefComplaint] = useState('');
  const [history] = useState('Known history of hypertension, poor compliance.');
  const [assessment, setAssessment] = useState('High BP 148/96 mmHg with elevated blood glucose.');
  const [diagCode] = useState('E11.9 / I10');
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

  const [saving, setSaving] = useState(false);

  const loadQueue = async () => {
    if (!activeFacility) return;
    try {
      const res = await api.get(`visits/?facility=${activeFacility.id}&status=TRIAGED`);
      const list: Visit[] = res.data.results || res.data || [];
      setTriagedVisits(list);

      if (stateVisitId) {
        const found = list.find((v) => v.id === stateVisitId);
        if (found) selectVisit(found);
      } else if (list.length > 0) {
        selectVisit(list[0]);
      }
    } catch (e) {
      console.error('Failed to load doctor queue', e);
    }
  };

  const selectVisit = async (v: Visit) => {
    setSelectedVisit(v);
    setChiefComplaint(v.chief_complaint || 'Dizziness and fatigue');
    try {
      const trRes = await api.get(`triage/?visit=${v.id}`);
      const trList = trRes.data.results || trRes.data || [];
      if (trList.length > 0) setVitals(trList[0]);
      else setVitals(null);
    } catch (e) {
      setVitals(null);
    }
  };

  useEffect(() => {
    loadQueue();
  }, [activeFacility]);

  // Filter local referral destination options
  const referralDestinations = allFacilities.filter(
    (f) => f.id !== activeFacility?.id && ['MAIN_HOSPITAL', 'REFERRAL_HOSPITAL', 'SECONDARY_HOSPITAL', 'DIAGNOSTIC_CENTER'].includes(f.facility_type)
  );

  useEffect(() => {
    if (referralDestinations.length > 0 && !destFacilityId) {
      setDestFacilityId(referralDestinations[0].id);
    }
  }, [referralDestinations]);

  const handleAddMed = () => {
    setPrescriptions([...prescriptions, { medicine_name: 'Paracetamol 650 mg Tablet', dosage: '1-0-1', quantity: 10 }]);
  };

  const handleRemoveMed = (idx: number) => {
    setPrescriptions(prescriptions.filter((_, i) => i !== idx));
  };

  const handleSaveConsultation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedVisit || !activeFacility) return;
    setSaving(true);

    try {
      // 1. Save Consultation & Prescription
      await api.post('consultations/', {
        visit: selectedVisit.id,
        patient: selectedVisit.patient,
        facility: activeFacility.id,
        chief_complaint: chiefComplaint,
        clinical_history: history,
        clinical_assessment: assessment,
        diagnosis_code: diagCode,
        diagnosis_name: diagName,
        clinical_notes: notes,
        prescription_items: prescriptions
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

      alert(`Consultation & EMR entry completed for ${selectedVisit.patient_details?.name}!`);
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
                </div>
              ))}
            </div>
          )}
        </div>

        {/* EMR Console & Form */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-slate-200 bg-white space-y-5 shadow-xs">
          {selectedVisit ? (
            <form onSubmit={handleSaveConsultation} className="space-y-5 text-xs">
              {/* Patient & Vitals Summary */}
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                <div className="flex justify-between items-start">
                  <div>
                    <h2 className="text-base font-bold text-slate-900">{selectedVisit.patient_details?.name}</h2>
                    <p className="text-xs text-slate-500">
                      ID: {selectedVisit.patient_details?.patient_id} • Age: {selectedVisit.patient_details?.age} • Gender: {selectedVisit.patient_details?.gender}
                    </p>
                  </div>
                  <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-200">
                    Token #{selectedVisit.token_details?.token_number || 1}
                  </span>
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
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Diagnosis Code & Name *</label>
                  <input
                    type="text"
                    value={diagName}
                    onChange={(e) => setDiagName(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-blue-600"
                    required
                  />
                </div>
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
                    Prescribe Medication (FEFO Dispensing Ready)
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

              <button
                type="submit"
                disabled={saving}
                className="w-full py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-xs rounded-xl shadow-md transition"
              >
                {saving ? 'Saving Consultation...' : 'Complete Consultation & Issue Orders'}
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
