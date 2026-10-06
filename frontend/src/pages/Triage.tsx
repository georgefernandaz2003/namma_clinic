import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import api from '../services/api';
import type { Visit } from '../types';
import { useAuth } from '../context/AuthContext';
import { useConfirm } from '../context/ConfirmContext';
import { Stethoscope, CheckCircle2, UserCheck } from 'lucide-react';

export const Triage: React.FC = () => {
  const { activeFacility } = useAuth();
  const { confirm } = useConfirm();
  const location = useLocation();
  const navigate = useNavigate();
  const stateVisitId = location.state?.visitId;

  const [waitingVisits, setWaitingVisits] = useState<Visit[]>([]);
  const [selectedVisit, setSelectedVisit] = useState<Visit | null>(null);

  // Facility Doctors for nurse routing
  const [facilityDoctors, setFacilityDoctors] = useState<any[]>([]);
  const [selectedDoctorId, setSelectedDoctorId] = useState<number | ''>('');

  // Vitals form - standard normal baseline vitals
  const [sys, setSys] = useState('120');
  const [dia, setDia] = useState('80');
  const [pulse, setPulse] = useState('72');
  const [temp, setTemp] = useState('98.6');
  const [spo2, setSpo2] = useState('98');
  const [resp] = useState('18');
  const [height, setHeight] = useState('165');
  const [weight, setWeight] = useState('65');
  const [glucose, setGlucose] = useState('100');
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [completedInfo, setCompletedInfo] = useState<{ patientName: string; tokenNumber?: string | number; doctorName?: string } | null>(null);

  const resetVitalsForm = (visit?: Visit | null) => {
    const vTriage = (visit as any)?.triage;
    if (vTriage) {
      setSys(String(vTriage.blood_pressure_systolic ?? '120'));
      setDia(String(vTriage.blood_pressure_diastolic ?? '80'));
      setPulse(String(vTriage.pulse_bpm ?? '72'));
      setTemp(String(vTriage.temperature_f ?? '98.6'));
      setSpo2(String(vTriage.spo2_percent ?? '98'));
      setHeight(String(vTriage.height_cm ?? '165'));
      setWeight(String(vTriage.weight_kg ?? '65'));
      setGlucose(String(vTriage.blood_glucose_mgdl ?? '100'));
      setNotes(vTriage.nurse_notes || '');
    } else {
      setSys('120');
      setDia('80');
      setPulse('72');
      setTemp('98.6');
      setSpo2('98');
      setHeight('165');
      setWeight('65');
      setGlucose('100');
      setNotes('');
    }
  };

  useEffect(() => {
    if (selectedVisit) {
      resetVitalsForm(selectedVisit);
    }
  }, [selectedVisit?.id]);

  const loadQueue = async (targetId?: number | null) => {
    if (!activeFacility) return;
    try {
      const res = await api.get(`visits/?facility=${activeFacility.id}&queue=TRIAGE`);
      const list: Visit[] = res.data.results || res.data || [];
      setWaitingVisits(list);

      const effectiveTargetId = targetId !== undefined ? targetId : stateVisitId;

      if (effectiveTargetId) {
        const found = list.find((v) => v.id === effectiveTargetId);
        if (found) {
          setSelectedVisit(found);
        } else if (list.length > 0) {
          setSelectedVisit(list[0]);
        } else {
          setSelectedVisit(null);
        }
      } else if (list.length > 0) {
        setSelectedVisit(list[0]);
      } else {
        setSelectedVisit(null);
      }
    } catch (e) {
      console.error('Failed to load triage queue', e);
    }
  };

  useEffect(() => {
    loadQueue();
  }, [activeFacility]);

  useEffect(() => {
    const fetchDoctors = async () => {
      if (!activeFacility) return;
      try {
        const res = await api.get(`accounts/doctors/?facility=${activeFacility.id}`);
        const docs = res.data || [];
        setFacilityDoctors(docs);
        if (docs.length > 0) {
          if (selectedVisit?.assigned_doctor) {
            setSelectedDoctorId(selectedVisit.assigned_doctor);
          } else {
            setSelectedDoctorId(docs[0].id);
          }
        }
      } catch (e) {
        console.error('Failed to load facility doctors', e);
      }
    };
    fetchDoctors();
  }, [activeFacility, selectedVisit]);

  const handleSaveTriage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedVisit) return;

    const patientName = selectedVisit.patient_details?.name || 'Patient';
    const tokenNum = selectedVisit.token_details?.token_number || selectedVisit.token_number || selectedVisit.id;
    const chosenDoc = facilityDoctors.find((d) => d.id === selectedDoctorId);
    const chosenDocName = chosenDoc ? chosenDoc.full_name : 'General Doctor Queue';

    confirm({
      title: 'Confirm Triage Assessment & Routing',
      message: `Are you sure you want to save these vitals and route ${patientName} to ${chosenDocName}?`,
      confirmText: 'Save Vitals & Route to Doctor',
      cancelText: 'Cancel',
      variant: 'primary',
      loadingText: 'Saving Triage Assessment...',
      details: [
        { label: 'Patient Name', value: patientName },
        { label: 'Token Number', value: `#${tokenNum}` },
        { label: 'Assigned Doctor', value: chosenDocName },
        { label: 'Blood Pressure', value: `${sys}/${dia} mmHg` },
        { label: 'Pulse / SpO2', value: `${pulse} bpm • ${spo2}%` },
        { label: 'Temperature', value: `${temp} °F` },
        { label: 'Blood Glucose', value: `${glucose} mg/dL` },
        { label: 'BMI', value: `${calculatedBmi} kg/m²` },
        { label: 'Destination Queue', value: 'Doctor Consultation' }
      ],
      onConfirm: async () => {
        setSaving(true);
        try {
          await api.post('triage/', {
            visit: selectedVisit.id,
            patient: selectedVisit.patient,
            assigned_doctor: selectedDoctorId || null,
            blood_pressure_systolic: parseInt(sys) || 120,
            blood_pressure_diastolic: parseInt(dia) || 80,
            pulse_bpm: parseInt(pulse) || 72,
            temperature_f: parseFloat(temp) || 98.6,
            spo2_percent: parseInt(spo2) || 98,
            respiratory_rate: parseInt(resp) || 18,
            height_cm: parseFloat(height) || 165,
            weight_kg: parseFloat(weight) || 60,
            blood_glucose_mgdl: parseInt(glucose) || 100,
            nurse_notes: notes
          });

          // Immediately remove the completed patient from the triage screen
          setSelectedVisit(null);

          setCompletedInfo({
            patientName,
            tokenNumber: tokenNum,
            doctorName: chosenDocName
          });

          // Reset vitals form for next patient
          setSys('120');
          setDia('80');
          setPulse('72');
          setTemp('98.6');
          setSpo2('98');
          setHeight('165');
          setWeight('65');
          setGlucose('100');
          setNotes('');

          // Clear location.state so stateVisitId won't re-select the completed patient
          if (location.state?.visitId) {
            navigate(location.pathname, { replace: true, state: {} });
          }

          await loadQueue(null);
        } finally {
          setSaving(false);
        }
      }
    });
  };

  // Dynamic BMI Calculation
  const heightM = (parseFloat(height) || 165) / 100;
  const weightKg = parseFloat(weight) || 65;
  const calculatedBmi = (weightKg / (heightM * heightM)).toFixed(1);

  // Dynamic Risk Flags Evaluator
  const sNum = parseInt(sys, 10);
  const dNum = parseInt(dia, 10);
  const tempNum = parseFloat(temp);
  const spo2Num = parseInt(spo2, 10);
  const gluNum = parseInt(glucose, 10);

  const isHighBp = (!isNaN(sNum) && sNum >= 140) || (!isNaN(dNum) && dNum >= 90);
  const isFever = !isNaN(tempNum) && tempNum >= 100.4;
  const isLowSpo2 = !isNaN(spo2Num) && spo2Num > 0 && spo2Num < 95;
  const isHighGlucose = !isNaN(gluNum) && gluNum >= 160;
  const hasRiskFlags = isHighBp || isFever || isLowSpo2 || isHighGlucose;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <Stethoscope className="w-6 h-6 text-emerald-600" />
          Staff Nurse Triage Console & Vitals Assessment
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Vitals logging, automatic high-risk condition flagging (High BP, High Glucose, Low SpO2, Fever)
        </p>
      </div>

      {/* Triage Completed Banner */}
      {completedInfo && (
        <div className="bg-emerald-50 border border-emerald-300 rounded-2xl p-4 flex items-center justify-between shadow-sm animate-fadeIn">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-600 text-white flex items-center justify-center font-bold shadow-xs shrink-0">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-sm font-extrabold text-emerald-950">
                Triage is completed!
              </h3>
              <p className="text-xs text-emerald-800">
                Vitals logged for <strong>{completedInfo.patientName}</strong> (Token #{completedInfo.tokenNumber}). Patient has been moved to Doctor&apos;s Waiting Queue.
              </p>
            </div>
          </div>
          <button
            onClick={() => setCompletedInfo(null)}
            className="text-emerald-700 hover:text-emerald-900 text-xs font-bold px-3 py-1.5 rounded-lg bg-emerald-100 hover:bg-emerald-200 transition shrink-0"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Value Proposition Callout Banner */}
      <div className="bg-gradient-to-r from-emerald-900 via-teal-900 to-slate-900 p-4 rounded-2xl text-white space-y-1 shadow-md">
        <div className="flex items-center gap-2 text-xs font-black uppercase tracking-wider text-emerald-400">
          <span>🩺 Structured Pre-Consultation Triage</span>
        </div>
        <p className="text-xs text-emerald-100 font-medium leading-relaxed">
          &ldquo;The doctor doesn&apos;t start from a blank screen. The doctor receives a structured clinical picture before consultation.&rdquo;
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Waiting Queue */}
        <div className="glass-panel p-4 rounded-2xl border border-slate-200 bg-white space-y-3 shadow-xs">
          <h2 className="text-xs font-bold uppercase tracking-wider text-emerald-700 flex items-center justify-between pb-2 border-b border-slate-100">
            <span>Waiting for Triage</span>
            <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-mono">
              {waitingVisits.length}
            </span>
          </h2>

          {waitingVisits.length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-400">No patients waiting for triage.</div>
          ) : (
            <div className="space-y-2 max-h-[500px] overflow-y-auto">
              {waitingVisits.map((v) => (
                <div
                  key={v.id}
                  onClick={() => {
                    setSelectedVisit(v);
                    setCompletedInfo(null);
                  }}
                  className={`p-3 rounded-xl border transition cursor-pointer ${
                    selectedVisit?.id === v.id
                      ? 'bg-emerald-50 border-emerald-500 text-slate-900 shadow-xs'
                      : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-xs">{v.patient_details?.name}</span>
                    <span className="text-[10px] font-mono text-emerald-700 font-bold">Token #{v.token_details?.token_number || v.id}</span>
                  </div>
                  <span className="text-[10px] text-slate-500 block">{v.patient_details?.age} yrs • {v.chief_complaint}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Triage Vitals Form */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-slate-200 bg-white space-y-5 shadow-xs">
          {selectedVisit ? (
            <form onSubmit={handleSaveTriage} className="space-y-4 text-xs">
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 flex justify-between items-center">
                <div>
                  <h2 className="text-base font-bold text-slate-900">{selectedVisit.patient_details?.name}</h2>
                  <p className="text-xs text-slate-500">
                    ID: {selectedVisit.patient_details?.patient_id} • Age: {selectedVisit.patient_details?.age} yrs • Complaint: {selectedVisit.chief_complaint}
                  </p>
                </div>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                  Token #{selectedVisit.token_details?.token_number || 1}
                </span>
              </div>

              {/* Automatic Clinical Risk Flag Alert Banner */}
              {hasRiskFlags && (
                <div className="bg-rose-50 border-2 border-rose-500/80 p-3.5 rounded-xl space-y-1.5 animate-pulse">
                  <div className="flex items-center gap-2 text-xs font-black text-rose-800">
                    <span>🚨 AUTOMATIC CLINICAL RISK FLAGS DETECTED</span>
                  </div>
                  <div className="flex flex-wrap items-center gap-2 text-[11px] font-bold">
                    {isHighBp && (
                      <span className="px-2 py-0.5 rounded bg-rose-200 text-rose-900 border border-rose-300">
                        High BP: {sys}/{dia} mmHg
                      </span>
                    )}
                    {isFever && (
                      <span className="px-2 py-0.5 rounded bg-amber-200 text-amber-900 border border-amber-300">
                        High Fever: {temp}°F
                      </span>
                    )}
                    {isLowSpo2 && (
                      <span className="px-2 py-0.5 rounded bg-rose-200 text-rose-900 border border-rose-300">
                        Low SpO2: {spo2}%
                      </span>
                    )}
                    {isHighGlucose && (
                      <span className="px-2 py-0.5 rounded bg-purple-200 text-purple-900 border border-purple-300">
                        Elevated Blood Glucose: {glucose} mg/dL
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-rose-700 font-medium pt-0.5">
                    System automatically flagged high priority clinical risk. Doctor will see pre-triage alerts before consultation.
                  </p>
                </div>
              )}

              {/* Vitals Input Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div>
                  <label className="block text-slate-700 font-bold mb-1">BP Systolic (mmHg)</label>
                  <input
                    type="number"
                    value={sys}
                    onChange={(e) => setSys(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-emerald-600 font-mono font-bold"
                    required
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-bold mb-1">BP Diastolic (mmHg)</label>
                  <input
                    type="number"
                    value={dia}
                    onChange={(e) => setDia(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-emerald-600 font-mono font-bold"
                    required
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Pulse Rate (bpm)</label>
                  <input
                    type="number"
                    value={pulse}
                    onChange={(e) => setPulse(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-emerald-600 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Temperature (°F)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={temp}
                    onChange={(e) => setTemp(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-emerald-600 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-bold mb-1">SpO2 Oxygen (%)</label>
                  <input
                    type="number"
                    value={spo2}
                    onChange={(e) => setSpo2(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-emerald-600 font-mono font-bold"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Blood Glucose (mg/dL)</label>
                  <input
                    type="number"
                    value={glucose}
                    onChange={(e) => setGlucose(e.target.value)}
                    className={`w-full px-3 py-2 bg-slate-50 border rounded-lg focus:outline-none focus:border-emerald-600 font-mono font-bold ${
                      isHighGlucose ? 'border-purple-400 text-purple-700 bg-purple-50/40' : 'border-slate-300 text-slate-900'
                    }`}
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Height (cm)</label>
                  <input
                    type="number"
                    value={height}
                    onChange={(e) => setHeight(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-emerald-600 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Weight (kg)</label>
                  <input
                    type="number"
                    value={weight}
                    onChange={(e) => setWeight(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-emerald-600 font-mono"
                  />
                </div>
              </div>

              {/* Dynamic Calculated BMI Indicator */}
              <div className="p-3 bg-slate-100 rounded-xl border border-slate-200 flex items-center justify-between font-mono font-bold">
                <span className="text-slate-700 text-xs">Calculated Body Mass Index (BMI):</span>
                <span className="text-emerald-700 text-sm">{calculatedBmi} kg/m²</span>
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Nurse Triage Notes</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-emerald-600"
                />
              </div>

              {/* Doctor Assignment Selection */}
              <div className="p-4 bg-teal-50/70 rounded-xl border border-teal-200 space-y-2.5">
                <div className="flex items-center justify-between">
                  <label className="text-slate-800 font-bold flex items-center gap-1.5 text-xs">
                    <UserCheck className="w-4 h-4 text-teal-600" />
                    Assign Patient to Consulting Doctor *
                  </label>
                  <span className="text-[10px] text-teal-800 font-semibold px-2 py-0.5 bg-teal-100/70 rounded-full border border-teal-300">
                    {facilityDoctors.length} Doctor{facilityDoctors.length !== 1 ? 's' : ''} on Duty
                  </span>
                </div>

                {facilityDoctors.length === 0 ? (
                  <p className="text-xs text-slate-500 italic">No specific doctors registered. Patient will route to General OPD pool.</p>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    {facilityDoctors.map((doc, idx) => {
                      const isSelected = selectedDoctorId === doc.id;
                      return (
                        <div
                          key={doc.id}
                          onClick={() => setSelectedDoctorId(doc.id)}
                          className={`p-3 rounded-xl border cursor-pointer transition flex items-center justify-between ${
                            isSelected
                              ? 'bg-teal-600 text-white border-teal-600 shadow-sm ring-2 ring-teal-300/60'
                              : 'bg-white text-slate-800 border-slate-200 hover:border-teal-400 hover:bg-teal-50/40'
                          }`}
                        >
                          <div>
                            <span className="font-bold text-xs block leading-tight">{doc.full_name}</span>
                            <span className={`text-[10px] block mt-0.5 ${isSelected ? 'text-teal-100 font-medium' : 'text-slate-500'}`}>
                              Consulting Room #{idx + 1} • {doc.username}
                            </span>
                          </div>
                          <div className={`w-4 h-4 rounded-full border flex items-center justify-center shrink-0 ${
                            isSelected ? 'bg-white border-white text-teal-600' : 'border-slate-300 bg-white'
                          }`}>
                            {isSelected && <div className="w-2 h-2 rounded-full bg-teal-600" />}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              <button
                type="submit"
                disabled={saving}
                className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-md transition cursor-pointer"
              >
                {saving ? 'Logging Vitals & Assigning Doctor...' : 'Log Nurse Triage & Route to Selected Doctor'}
              </button>
            </form>
          ) : (
            <div className="p-16 text-center space-y-3">
              <div className="w-14 h-14 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto border border-emerald-100 shadow-2xs">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <h3 className="text-sm font-bold text-slate-800">
                {waitingVisits.length === 0
                  ? 'All Waiting Patients Triaged'
                  : 'Ready for Next Patient'}
              </h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto leading-relaxed">
                {waitingVisits.length === 0
                  ? 'There are currently no patients waiting in the triage queue. Newly registered patients will appear on the left.'
                  : 'Select a patient from the waiting queue on the left to start logging triage vitals.'}
              </p>
              {waitingVisits.length === 0 && (
                <div className="pt-2 flex items-center justify-center gap-2">
                  <button
                    type="button"
                    onClick={() => navigate('/queue')}
                    className="px-3.5 py-1.5 text-xs font-bold rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 transition cursor-pointer shadow-2xs"
                  >
                    View OPD Queue
                  </button>
                  <button
                    type="button"
                    onClick={() => navigate('/consultation')}
                    className="px-3.5 py-1.5 text-xs font-bold rounded-lg bg-teal-600 text-white hover:bg-teal-500 transition cursor-pointer shadow-2xs"
                  >
                    Go to Doctor Console
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
