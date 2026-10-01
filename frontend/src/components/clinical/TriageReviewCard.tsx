import React from 'react';
import type { TriageVitals } from '../../types';
import { Heart, AlertTriangle } from 'lucide-react';

interface TriageReviewCardProps {
  triage: TriageVitals | null;
}

export const TriageReviewCard: React.FC<TriageReviewCardProps> = ({ triage }) => {
  return (
    <section aria-labelledby="triage-review-heading" className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
      <div className="flex items-center justify-between mb-3 border-b border-slate-100 pb-2">
        <h2 id="triage-review-heading" className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <Heart className="w-4 h-4 text-rose-500" aria-hidden="true" />
          <span>Pre-Consultation Nursing Triage Vitals</span>
        </h2>
        <span className="text-[11px] text-slate-500 italic">
          Read-only clinical observation (Authored by Staff Nurse)
        </span>
      </div>

      {triage ? (
        <div className="space-y-3">
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2.5">
            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-center">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">BP (Sys/Dia)</span>
              <span className={`text-sm font-bold ${triage.high_bp_flag ? 'text-rose-600 font-extrabold' : 'text-slate-900'}`}>
                {triage.blood_pressure_systolic}/{triage.blood_pressure_diastolic}
              </span>
              <span className="text-[10px] text-slate-400 block">mmHg</span>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-center">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">Pulse</span>
              <span className="text-sm font-bold text-slate-900">{triage.pulse_bpm}</span>
              <span className="text-[10px] text-slate-400 block">bpm</span>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-center">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">Temperature</span>
              <span className={`text-sm font-bold ${triage.fever_flag ? 'text-amber-600 font-extrabold' : 'text-slate-900'}`}>
                {triage.temperature_f}°F
              </span>
              <span className="text-[10px] text-slate-400 block">oral</span>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-center">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">SpO2</span>
              <span className={`text-sm font-bold ${triage.low_spo2_flag ? 'text-rose-600 font-extrabold' : 'text-slate-900'}`}>
                {triage.spo2_percent}%
              </span>
              <span className="text-[10px] text-slate-400 block">room air</span>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-center">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">Resp. Rate</span>
              <span className="text-sm font-bold text-slate-900">{triage.respiratory_rate}</span>
              <span className="text-[10px] text-slate-400 block">/min</span>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-center">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">Weight / Height</span>
              <span className="text-xs font-bold text-slate-900">{triage.weight_kg}kg / {triage.height_cm}cm</span>
              <span className="text-[10px] text-slate-400 block">BMI: {triage.bmi}</span>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-center">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">Blood Sugar</span>
              <span className={`text-sm font-bold ${triage.high_glucose_flag ? 'text-amber-600 font-extrabold' : 'text-slate-900'}`}>
                {triage.blood_glucose_mgdl}
              </span>
              <span className="text-[10px] text-slate-400 block">mg/dL</span>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-center">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">Triage Status</span>
              <span className="text-xs font-bold text-emerald-700">Recorded</span>
              <span className="text-[10px] text-slate-400 block">by Nurse</span>
            </div>
          </div>

          {(triage.high_bp_flag || triage.high_glucose_flag || triage.fever_flag || triage.low_spo2_flag || triage.emergency_flag) && (
            <div className="flex flex-wrap items-center gap-2 p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-900 font-medium">
              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" aria-hidden="true" />
              <span>Active Clinical Warning Flags:</span>
              {triage.high_bp_flag && <span className="bg-rose-100 text-rose-800 px-2 py-0.5 rounded text-[10px] font-bold">Hypertension Warning (BP ≥ 140/90)</span>}
              {triage.fever_flag && <span className="bg-amber-100 text-amber-800 px-2 py-0.5 rounded text-[10px] font-bold">Pyrexia (Temp ≥ 100.4°F)</span>}
              {triage.low_spo2_flag && <span className="bg-rose-100 text-rose-800 px-2 py-0.5 rounded text-[10px] font-bold">Hypoxia (SpO2 &lt; 95%)</span>}
              {triage.high_glucose_flag && <span className="bg-amber-100 text-amber-800 px-2 py-0.5 rounded text-[10px] font-bold">Hyperglycemia (Glucose ≥ 160)</span>}
              {triage.emergency_flag && <span className="bg-rose-600 text-white px-2 py-0.5 rounded text-[10px] font-bold">EMERGENCY ENCOUNTER</span>}
            </div>
          )}

          {triage.nurse_notes && (
            <div className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
              <strong className="text-slate-800">Nurse Triage Notes:</strong> {triage.nurse_notes}
            </div>
          )}
        </div>
      ) : (
        <div className="p-4 bg-slate-50 rounded-lg text-center text-xs text-slate-500">
          Triage vitals have not been recorded for this encounter yet. Doctor may proceed directly with clinical examination.
        </div>
      )}
    </section>
  );
};

export default TriageReviewCard;
