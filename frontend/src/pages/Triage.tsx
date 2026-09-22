import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import api from '../services/api';
import type { Visit } from '../types';
import { useAuth } from '../context/AuthContext';
import { hasPermission } from '../utils/permissions';
import { Stethoscope } from 'lucide-react';

export const Triage: React.FC = () => {
  const { activeFacility, user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const stateVisitId = location.state?.visitId;

  const [waitingVisits, setWaitingVisits] = useState<Visit[]>([]);
  const [selectedVisit, setSelectedVisit] = useState<Visit | null>(null);

  // Vitals form
  const [sys, setSys] = useState('142');
  const [dia, setDia] = useState('94');
  const [pulse, setPulse] = useState('82');
  const [temp, setTemp] = useState('98.6');
  const [spo2, setSpo2] = useState('98');
  const [resp] = useState('18');
  const [height, setHeight] = useState('165');
  const [weight, setWeight] = useState('68');
  const [glucose, setGlucose] = useState('175');
  const [notes, setNotes] = useState('High BP and elevated glucose detected. High risk flag auto-triggered.');
  const [saving, setSaving] = useState(false);

  const loadQueue = async () => {
    if (!activeFacility) return;
    try {
      const res = await api.get(`visits/?facility=${activeFacility.id}&queue=TRIAGE`);
      const list: Visit[] = res.data.results || res.data || [];
      setWaitingVisits(list);

      if (stateVisitId) {
        const found = list.find((v) => v.id === stateVisitId);
        if (found) setSelectedVisit(found);
        else if (list.length > 0) setSelectedVisit(list[0]);
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

  const handleSaveTriage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedVisit) return;
    setSaving(true);

    try {
      await api.post('triage/', {
        visit: selectedVisit.id,
        patient: selectedVisit.patient,
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

      alert(`Nurse triage vitals logged for ${selectedVisit.patient_details?.name}! High Risk flags evaluated.`);
      loadQueue();
      navigate('/queue');
    } finally {
      setSaving(false);
    }
  };

  // Dynamic BMI Calculation
  const heightM = (parseFloat(height) || 165) / 100;
  const weightKg = parseFloat(weight) || 68;
  const calculatedBmi = (weightKg / (heightM * heightM)).toFixed(1);

  // Dynamic Risk Flags Evaluator
  const sNum = parseInt(sys) || 120;
  const dNum = parseInt(dia) || 80;
  const tempNum = parseFloat(temp) || 98.6;
  const spo2Num = parseInt(spo2) || 98;
  const gluNum = parseInt(glucose) || 100;

  const isHighBp = sNum >= 140 || dNum >= 90;
  const isFever = tempNum >= 100.4;
  const isLowSpo2 = spo2Num < 95;
  const isHighGlucose = gluNum >= 140;
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
                  onClick={() => setSelectedVisit(v)}
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
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-emerald-600 font-mono font-bold text-amber-700"
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

              {hasPermission(user?.role, 'triage.create') ? (
                <button
                  type="submit"
                  disabled={saving}
                  className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-md transition"
                >
                  {saving ? 'Logging Vitals...' : 'Log Nurse Triage & Forward to Doctor Queue'}
                </button>
              ) : (
                <div className="p-3 bg-slate-100 text-slate-500 rounded-xl text-center text-xs font-semibold">
                  Triage vital modifications are restricted to nursing staff.
                </div>
              )}
            </form>
          ) : (
            <div className="p-12 text-center text-xs text-slate-400">
              Select a patient from the queue to start logging triage vitals.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
