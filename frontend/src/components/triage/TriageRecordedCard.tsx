import React from 'react';
import {
  Heart,
  Activity,
  Thermometer,
  Gauge,
  Wind,
  Scale,
  Droplet,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Clock,
  UserCheck,
  Edit3
} from 'lucide-react';
import type { TriageVitals } from '../../types';

interface TriageRecordedCardProps {
  triage: TriageVitals;
  onEditTriage?: () => void;
  onBackToQueue: () => void;
}

export const TriageRecordedCard: React.FC<TriageRecordedCardProps> = ({
  triage,
  onEditTriage,
  onBackToQueue
}) => {
  const hasWarningFlags =
    triage.high_bp_flag ||
    triage.high_glucose_flag ||
    triage.fever_flag ||
    triage.low_spo2_flag ||
    triage.emergency_flag ||
    triage.pregnancy_high_risk_flag ||
    triage.ncd_risk_flag;

  return (
    <div data-testid="triage-recorded-card" className="bg-white rounded-xl shadow-xs border border-slate-200 overflow-hidden mb-6">
      <div className="bg-emerald-50 border-b border-emerald-200 px-6 py-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-emerald-900 font-bold">
          <CheckCircle2 className="w-5 h-5 text-emerald-600" aria-hidden="true" />
          <span>Triage Vitals Recorded — Encounter Forwarded to Doctor</span>
        </div>
        <div className="flex items-center gap-2">
          {onEditTriage && (
            <button
              type="button"
              onClick={onEditTriage}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-emerald-700 bg-white border border-emerald-300 rounded-lg hover:bg-emerald-100/50 transition-colors shadow-2xs"
            >
              <Edit3 className="w-3.5 h-3.5" aria-hidden="true" />
              Update / Correct Vitals
            </button>
          )}
          <button
            type="button"
            onClick={onBackToQueue}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-teal-700 hover:bg-teal-800 rounded-lg transition-colors shadow-2xs"
          >
            Return to Nurse Queue
          </button>
        </div>
      </div>

      <div className="p-6">
        {hasWarningFlags && (
          <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex items-center gap-2 text-amber-900 font-bold text-sm mb-2">
              <AlertTriangle className="w-4 h-4 text-amber-600" aria-hidden="true" />
              <span>Automated Clinical Warning Indicators:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {triage.high_bp_flag && (
                <span className="bg-rose-100 text-rose-800 border border-rose-300 px-2.5 py-1 rounded text-xs font-bold">
                  Hypertension Warning (BP ≥ 140/90)
                </span>
              )}
              {triage.fever_flag && (
                <span className="bg-amber-100 text-amber-800 border border-amber-300 px-2.5 py-1 rounded text-xs font-bold">
                  Pyrexia / Fever (Temp ≥ 100.4°F)
                </span>
              )}
              {triage.low_spo2_flag && (
                <span className="bg-rose-100 text-rose-800 border border-rose-300 px-2.5 py-1 rounded text-xs font-bold">
                  Hypoxia Warning (SpO2 &lt; 95%)
                </span>
              )}
              {triage.high_glucose_flag && (
                <span className="bg-amber-100 text-amber-800 border border-amber-300 px-2.5 py-1 rounded text-xs font-bold">
                  Hyperglycemia (Glucose ≥ 160 mg/dL)
                </span>
              )}
              {triage.emergency_flag && (
                <span className="bg-rose-600 text-white px-2.5 py-1 rounded text-xs font-bold">
                  EMERGENCY ENCOUNTER
                </span>
              )}
              {triage.pregnancy_high_risk_flag && (
                <span className="bg-purple-100 text-purple-800 border border-purple-300 px-2.5 py-1 rounded text-xs font-bold">
                  High Risk Pregnancy
                </span>
              )}
              {triage.ncd_risk_flag && (
                <span className="bg-blue-100 text-blue-800 border border-blue-300 px-2.5 py-1 rounded text-xs font-bold">
                  NCD Longitudinal Risk
                </span>
              )}
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-3 mb-6">
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-center">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1 flex items-center justify-center gap-1">
              <Heart className="w-3.5 h-3.5 text-rose-500" aria-hidden="true" />
              BP (Sys/Dia)
            </span>
            <span
              className={`text-base font-black ${
                triage.high_bp_flag ? 'text-rose-600' : 'text-slate-900'
              }`}
            >
              {triage.blood_pressure_systolic}/{triage.blood_pressure_diastolic}
            </span>
            <span className="text-[10px] text-slate-400 block">mmHg</span>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-center">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1 flex items-center justify-center gap-1">
              <Activity className="w-3.5 h-3.5 text-emerald-500" aria-hidden="true" />
              Pulse Rate
            </span>
            <span className="text-base font-black text-slate-900">{triage.pulse_bpm}</span>
            <span className="text-[10px] text-slate-400 block">bpm</span>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-center">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1 flex items-center justify-center gap-1">
              <Thermometer className="w-3.5 h-3.5 text-amber-500" aria-hidden="true" />
              Temperature
            </span>
            <span
              className={`text-base font-black ${
                triage.fever_flag ? 'text-amber-600' : 'text-slate-900'
              }`}
            >
              {triage.temperature_f}°F
            </span>
            <span className="text-[10px] text-slate-400 block">oral</span>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-center">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1 flex items-center justify-center gap-1">
              <Gauge className="w-3.5 h-3.5 text-sky-500" aria-hidden="true" />
              SpO2
            </span>
            <span
              className={`text-base font-black ${
                triage.low_spo2_flag ? 'text-rose-600' : 'text-slate-900'
              }`}
            >
              {triage.spo2_percent}%
            </span>
            <span className="text-[10px] text-slate-400 block">room air</span>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-center">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1 flex items-center justify-center gap-1">
              <Wind className="w-3.5 h-3.5 text-indigo-500" aria-hidden="true" />
              Resp. Rate
            </span>
            <span className="text-base font-black text-slate-900">{triage.respiratory_rate}</span>
            <span className="text-[10px] text-slate-400 block">/min</span>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-center">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1 flex items-center justify-center gap-1">
              <Scale className="w-3.5 h-3.5 text-slate-600" aria-hidden="true" />
              Height / Weight
            </span>
            <span className="text-xs font-bold text-slate-900">
              {triage.weight_kg}kg / {triage.height_cm}cm
            </span>
            <span className="text-[10px] text-slate-500 block font-semibold">BMI: {triage.bmi}</span>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-center">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1 flex items-center justify-center gap-1">
              <Droplet className="w-3.5 h-3.5 text-rose-500" aria-hidden="true" />
              Blood Sugar
            </span>
            <span
              className={`text-base font-black ${
                triage.high_glucose_flag ? 'text-amber-600' : 'text-slate-900'
              }`}
            >
              {triage.blood_glucose_mgdl}
            </span>
            <span className="text-[10px] text-slate-400 block">mg/dL</span>
          </div>
        </div>

        {triage.nurse_notes && (
          <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 mb-6">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              <FileText className="w-3.5 h-3.5 text-slate-500" aria-hidden="true" />
              Nurse Triage Notes:
            </div>
            <p className="text-sm text-slate-800 whitespace-pre-wrap">{triage.nurse_notes}</p>
          </div>
        )}

        <div className="pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-4 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <UserCheck className="w-4 h-4 text-teal-600" aria-hidden="true" />
            <span>
              Clinical Authorship: Staff Nurse (ID #{triage.nurse ?? 'Authoritative Staff'})
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-slate-400" aria-hidden="true" />
            <span>Recorded at: {new Date(triage.created_at).toLocaleString()}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TriageRecordedCard;
