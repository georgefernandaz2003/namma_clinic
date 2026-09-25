import React, { useState, useId } from 'react';
import {
  Heart,
  Activity,
  Thermometer,
  Gauge,
  Wind,
  Scale,
  Droplet,
  AlertTriangle,
  FileText,
  ShieldAlert,
  Save,
  CheckCircle2
} from 'lucide-react';
import type { CreateTriagePayload, TriageVitals } from '../../types';
import ErrorAlert from '../common/ErrorAlert';

interface TriageVitalsFormProps {
  initialVitals?: TriageVitals | null;
  onSubmit: (payload: CreateTriagePayload) => Promise<void>;
  loading: boolean;
  nurseName?: string;
  onCancel?: () => void;
}

export const TriageVitalsForm: React.FC<TriageVitalsFormProps> = ({
  initialVitals,
  onSubmit,
  loading,
  nurseName,
  onCancel
}) => {
  const formId = useId();

  // Field states
  const [systolic, setSystolic] = useState<string>(
    initialVitals?.blood_pressure_systolic ? String(initialVitals.blood_pressure_systolic) : '120'
  );
  const [diastolic, setDiastolic] = useState<string>(
    initialVitals?.blood_pressure_diastolic ? String(initialVitals.blood_pressure_diastolic) : '80'
  );
  const [pulse, setPulse] = useState<string>(
    initialVitals?.pulse_bpm ? String(initialVitals.pulse_bpm) : '76'
  );
  const [temperature, setTemperature] = useState<string>(
    initialVitals?.temperature_f ? String(initialVitals.temperature_f) : '98.6'
  );
  const [spo2, setSpo2] = useState<string>(
    initialVitals?.spo2_percent ? String(initialVitals.spo2_percent) : '99'
  );
  const [respiratoryRate, setRespiratoryRate] = useState<string>(
    initialVitals?.respiratory_rate ? String(initialVitals.respiratory_rate) : '18'
  );
  const [height, setHeight] = useState<string>(
    initialVitals?.height_cm ? String(initialVitals.height_cm) : '165'
  );
  const [weight, setWeight] = useState<string>(
    initialVitals?.weight_kg ? String(initialVitals.weight_kg) : '65'
  );
  const [glucose, setGlucose] = useState<string>(
    initialVitals?.blood_glucose_mgdl ? String(initialVitals.blood_glucose_mgdl) : '110'
  );
  const [emergencyFlag, setEmergencyFlag] = useState<boolean>(
    initialVitals?.emergency_flag ?? false
  );
  const [pregnancyFlag, setPregnancyFlag] = useState<boolean>(
    initialVitals?.pregnancy_high_risk_flag ?? false
  );
  const [ncdFlag, setNcdFlag] = useState<boolean>(
    initialVitals?.ncd_risk_flag ?? false
  );
  const [notes, setNotes] = useState<string>(initialVitals?.nurse_notes ?? '');
  const [validationError, setValidationError] = useState<string | null>(null);

  // Dynamic calculations
  const sNum = parseInt(systolic, 10) || 0;
  const dNum = parseInt(diastolic, 10) || 0;
  const tempNum = parseFloat(temperature) || 0;
  const spo2Num = parseInt(spo2, 10) || 0;
  const gluNum = parseInt(glucose, 10) || 0;
  const hNum = parseFloat(height) || 0;
  const wNum = parseFloat(weight) || 0;

  // Real-time BMI computation
  let calculatedBmi: string | null = null;
  let bmiCategory: string = '';
  if (hNum > 0 && wNum > 0) {
    const hM = hNum / 100.0;
    const bmiVal = wNum / (hM * hM);
    calculatedBmi = bmiVal.toFixed(1);
    if (bmiVal < 18.5) bmiCategory = 'Underweight';
    else if (bmiVal < 25) bmiCategory = 'Normal';
    else if (bmiVal < 30) bmiCategory = 'Overweight';
    else bmiCategory = 'Obese';
  }

  // Real-time Clinical Warning Thresholds (mirroring backend domain rules)
  const isHighBp = sNum >= 140 || dNum >= 90;
  const isFever = tempNum >= 100.4;
  const isLowSpo2 = spo2Num > 0 && spo2Num < 95;
  const isHighGlucose = gluNum >= 160;
  const hasThresholdWarnings = isHighBp || isFever || isLowSpo2 || isHighGlucose || emergencyFlag;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    // Validation rules
    if (!systolic || sNum < 50 || sNum > 300) {
      setValidationError('Systolic BP must be a valid number between 50 and 300 mmHg.');
      return;
    }
    if (!diastolic || dNum < 30 || dNum > 200) {
      setValidationError('Diastolic BP must be a valid number between 30 and 200 mmHg.');
      return;
    }
    if (dNum >= sNum) {
      setValidationError('Diastolic BP cannot be greater than or equal to Systolic BP.');
      return;
    }
    if (!pulse || parseInt(pulse, 10) < 30 || parseInt(pulse, 10) > 250) {
      setValidationError('Pulse rate must be between 30 and 250 bpm.');
      return;
    }
    if (!temperature || tempNum < 90 || tempNum > 110) {
      setValidationError('Body temperature must be between 90.0°F and 110.0°F.');
      return;
    }
    if (!spo2 || spo2Num < 50 || spo2Num > 100) {
      setValidationError('Oxygen saturation (SpO2) must be between 50% and 100%.');
      return;
    }
    if (respiratoryRate && (parseInt(respiratoryRate, 10) < 5 || parseInt(respiratoryRate, 10) > 60)) {
      setValidationError('Respiratory rate must be between 5 and 60 breaths/min.');
      return;
    }
    if (hNum <= 0 || hNum > 260) {
      setValidationError('Height must be between 30 and 260 cm.');
      return;
    }
    if (wNum <= 0 || wNum > 350) {
      setValidationError('Weight must be between 1 and 350 kg.');
      return;
    }
    if (gluNum < 20 || gluNum > 800) {
      setValidationError('Blood glucose must be between 20 and 800 mg/dL.');
      return;
    }

    const payload: Partial<CreateTriagePayload> = {
      blood_pressure_systolic: sNum,
      blood_pressure_diastolic: dNum,
      pulse_bpm: parseInt(pulse, 10),
      temperature_f: tempNum,
      spo2_percent: spo2Num,
      respiratory_rate: parseInt(respiratoryRate, 10) || 18,
      height_cm: hNum,
      weight_kg: wNum,
      blood_glucose_mgdl: gluNum,
      pregnancy_high_risk_flag: pregnancyFlag,
      emergency_flag: emergencyFlag,
      ncd_risk_flag: ncdFlag,
      nurse_notes: notes.trim()
    };

    await onSubmit(payload as CreateTriagePayload);
  };

  return (
    <form noValidate onSubmit={handleSubmit} className="bg-white rounded-xl shadow-xs border border-slate-200 overflow-hidden mb-6">
      <div className="bg-slate-50 border-b border-slate-200 px-6 py-4 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Activity className="w-5 h-5 text-teal-600" aria-hidden="true" />
            Triage Vital Signs & Clinical Intake Assessment
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Authoritative clinical measurement. Values will be evaluated against health protocols and forwarded to the Doctor.
          </p>
        </div>

        {nurseName && (
          <span className="text-xs bg-teal-50 border border-teal-200 text-teal-800 px-3 py-1 rounded-full font-medium">
            Staff Nurse: <strong>{nurseName}</strong>
          </span>
        )}
      </div>

      <div className="p-6 space-y-6">
        {validationError && (
          <ErrorAlert title="Triage Validation Notice" message={validationError} />
        )}

        {/* Dynamic Warning Banner */}
        {hasThresholdWarnings && (
          <div className="p-4 bg-amber-50 border border-amber-300 rounded-lg">
            <div className="flex items-center gap-2 text-amber-900 font-bold text-xs uppercase tracking-wider mb-2">
              <AlertTriangle className="w-4 h-4 text-amber-600" aria-hidden="true" />
              <span>Real-Time Clinical Warning Triggers:</span>
            </div>
            <div className="flex flex-wrap gap-2 text-xs">
              {isHighBp && (
                <span className="bg-rose-100 text-rose-800 border border-rose-300 px-2.5 py-1 rounded font-bold">
                  Hypertension Warning (BP {sNum}/{dNum} ≥ 140/90)
                </span>
              )}
              {isFever && (
                <span className="bg-amber-100 text-amber-800 border border-amber-300 px-2.5 py-1 rounded font-bold">
                  Pyrexia / Fever ({tempNum}°F ≥ 100.4°F)
                </span>
              )}
              {isLowSpo2 && (
                <span className="bg-rose-100 text-rose-800 border border-rose-300 px-2.5 py-1 rounded font-bold">
                  Hypoxia Warning (SpO2 {spo2Num}% &lt; 95%)
                </span>
              )}
              {isHighGlucose && (
                <span className="bg-amber-100 text-amber-800 border border-amber-300 px-2.5 py-1 rounded font-bold">
                  Hyperglycemia ({gluNum} mg/dL ≥ 160 mg/dL)
                </span>
              )}
              {emergencyFlag && (
                <span className="bg-rose-600 text-white px-2.5 py-1 rounded font-bold">
                  EMERGENCY ENCOUNTER FLAGGED
                </span>
              )}
            </div>
          </div>
        )}

        {/* Vital Signs Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          {/* Blood Pressure Systolic */}
          <div>
            <label htmlFor={`${formId}-sys-bp`} className="block text-xs font-bold text-slate-700 mb-1 flex items-center justify-between">
              <span className="flex items-center gap-1">
                <Heart className="w-3.5 h-3.5 text-rose-500" aria-hidden="true" />
                Systolic BP (mmHg) *
              </span>
              <span className="text-[10px] text-slate-400">Target &lt; 140</span>
            </label>
            <input
              id={`${formId}-sys-bp`}
              data-testid="sys-bp"
              type="number"
              min={50}
              max={300}
              required
              value={systolic}
              onChange={(e) => setSystolic(e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg text-sm font-semibold focus:outline-hidden focus:ring-2 ${
                isHighBp ? 'border-rose-400 bg-rose-50/40 text-rose-900 focus:ring-rose-400' : 'border-slate-300 focus:ring-teal-500'
              }`}
              placeholder="120"
            />
          </div>

          {/* Blood Pressure Diastolic */}
          <div>
            <label htmlFor={`${formId}-dia-bp`} className="block text-xs font-bold text-slate-700 mb-1 flex items-center justify-between">
              <span className="flex items-center gap-1">
                <Heart className="w-3.5 h-3.5 text-rose-500" aria-hidden="true" />
                Diastolic BP (mmHg) *
              </span>
              <span className="text-[10px] text-slate-400">Target &lt; 90</span>
            </label>
            <input
              id={`${formId}-dia-bp`}
              data-testid="dia-bp"
              type="number"
              min={30}
              max={200}
              required
              value={diastolic}
              onChange={(e) => setDiastolic(e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg text-sm font-semibold focus:outline-hidden focus:ring-2 ${
                isHighBp ? 'border-rose-400 bg-rose-50/40 text-rose-900 focus:ring-rose-400' : 'border-slate-300 focus:ring-teal-500'
              }`}
              placeholder="80"
            />
          </div>

          {/* Pulse Rate */}
          <div>
            <label htmlFor={`${formId}-pulse-rate`} className="block text-xs font-bold text-slate-700 mb-1 flex items-center justify-between">
              <span className="flex items-center gap-1">
                <Activity className="w-3.5 h-3.5 text-emerald-500" aria-hidden="true" />
                Pulse Rate (bpm) *
              </span>
              <span className="text-[10px] text-slate-400">60 - 100</span>
            </label>
            <input
              id={`${formId}-pulse-rate`}
              data-testid="pulse-rate"
              type="number"
              min={30}
              max={250}
              required
              value={pulse}
              onChange={(e) => setPulse(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-semibold focus:outline-hidden focus:ring-2 focus:ring-teal-500"
              placeholder="76"
            />
          </div>

          {/* Temperature */}
          <div>
            <label htmlFor={`${formId}-temperature`} className="block text-xs font-bold text-slate-700 mb-1 flex items-center justify-between">
              <span className="flex items-center gap-1">
                <Thermometer className="w-3.5 h-3.5 text-amber-500" aria-hidden="true" />
                Temperature (°F) *
              </span>
              <span className="text-[10px] text-slate-400">Normal 98.6°F</span>
            </label>
            <input
              id={`${formId}-temperature`}
              data-testid="temperature"
              type="number"
              step="0.1"
              min={90}
              max={110}
              required
              value={temperature}
              onChange={(e) => setTemperature(e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg text-sm font-semibold focus:outline-hidden focus:ring-2 ${
                isFever ? 'border-amber-400 bg-amber-50/40 text-amber-900 focus:ring-amber-400' : 'border-slate-300 focus:ring-teal-500'
              }`}
              placeholder="98.6"
            />
          </div>

          {/* SpO2 */}
          <div>
            <label htmlFor={`${formId}-spo2-level`} className="block text-xs font-bold text-slate-700 mb-1 flex items-center justify-between">
              <span className="flex items-center gap-1">
                <Gauge className="w-3.5 h-3.5 text-sky-500" aria-hidden="true" />
                SpO2 Oxygen (%) *
              </span>
              <span className="text-[10px] text-slate-400">Normal ≥ 95%</span>
            </label>
            <input
              id={`${formId}-spo2-level`}
              data-testid="spo2-level"
              type="number"
              min={50}
              max={100}
              required
              value={spo2}
              onChange={(e) => setSpo2(e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg text-sm font-semibold focus:outline-hidden focus:ring-2 ${
                isLowSpo2 ? 'border-rose-400 bg-rose-50/40 text-rose-900 focus:ring-rose-400' : 'border-slate-300 focus:ring-teal-500'
              }`}
              placeholder="99"
            />
          </div>

          {/* Respiratory Rate */}
          <div>
            <label htmlFor={`${formId}-resp-rate`} className="block text-xs font-bold text-slate-700 mb-1 flex items-center justify-between">
              <span className="flex items-center gap-1">
                <Wind className="w-3.5 h-3.5 text-indigo-500" aria-hidden="true" />
                Resp. Rate (/min)
              </span>
              <span className="text-[10px] text-slate-400">Normal 12 - 20</span>
            </label>
            <input
              id={`${formId}-resp-rate`}
              data-testid="resp-rate"
              type="number"
              min={5}
              max={60}
              value={respiratoryRate}
              onChange={(e) => setRespiratoryRate(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-semibold focus:outline-hidden focus:ring-2 focus:ring-teal-500"
              placeholder="18"
            />
          </div>

          {/* Height (cm) */}
          <div>
            <label htmlFor={`${formId}-patient-height`} className="block text-xs font-bold text-slate-700 mb-1 flex items-center justify-between">
              <span className="flex items-center gap-1">
                <Scale className="w-3.5 h-3.5 text-slate-500" aria-hidden="true" />
                Height (cm) *
              </span>
              <span className="text-[10px] text-slate-400">30 - 250 cm</span>
            </label>
            <input
              id={`${formId}-patient-height`}
              data-testid="patient-height"
              type="number"
              step="0.5"
              min={30}
              max={250}
              required
              value={height}
              onChange={(e) => setHeight(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-semibold focus:outline-hidden focus:ring-2 focus:ring-teal-500"
              placeholder="165"
            />
          </div>

          {/* Weight (kg) */}
          <div>
            <label htmlFor={`${formId}-patient-weight`} className="block text-xs font-bold text-slate-700 mb-1 flex items-center justify-between">
              <span className="flex items-center gap-1">
                <Scale className="w-3.5 h-3.5 text-slate-500" aria-hidden="true" />
                Weight (kg) *
              </span>
              <span className="text-[10px] text-slate-400">1 - 300 kg</span>
            </label>
            <input
              id={`${formId}-patient-weight`}
              data-testid="patient-weight"
              type="number"
              step="0.5"
              min={1}
              max={300}
              required
              value={weight}
              onChange={(e) => setWeight(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-semibold focus:outline-hidden focus:ring-2 focus:ring-teal-500"
              placeholder="65"
            />
          </div>
        </div>

        {/* Secondary Row: BMI display + Random Blood Sugar + Risk Indicators */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 pt-2 border-t border-slate-100">
          {/* Dynamic BMI Indicator Card */}
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between">
            <div>
              <span className="text-xs font-bold text-slate-700 block">Computed BMI:</span>
              <span className="text-xs text-slate-500">Auto-calculated from H/W</span>
            </div>
            <div className="text-right">
              <span className="text-lg font-black text-slate-900 block">
                {calculatedBmi || '--'}
              </span>
              {bmiCategory && (
                <span className="text-[10px] font-bold text-teal-700 bg-teal-100 px-1.5 py-0.5 rounded">
                  {bmiCategory}
                </span>
              )}
            </div>
          </div>

          {/* Random Blood Glucose */}
          <div>
            <label htmlFor={`${formId}-blood-glucose`} className="block text-xs font-bold text-slate-700 mb-1 flex items-center justify-between">
              <span className="flex items-center gap-1">
                <Droplet className="w-3.5 h-3.5 text-rose-500" aria-hidden="true" />
                Random Blood Glucose (mg/dL) *
              </span>
              <span className="text-[10px] text-slate-400">&lt; 160 mg/dL</span>
            </label>
            <input
              id={`${formId}-blood-glucose`}
              data-testid="blood-glucose"
              type="number"
              min={20}
              max={800}
              required
              value={glucose}
              onChange={(e) => setGlucose(e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg text-sm font-semibold focus:outline-hidden focus:ring-2 ${
                isHighGlucose ? 'border-amber-400 bg-amber-50/40 text-amber-900 focus:ring-amber-400' : 'border-slate-300 focus:ring-teal-500'
              }`}
              placeholder="110"
            />
          </div>

          {/* Clinical Escalation Toggles */}
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex flex-col justify-center gap-2">
            <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider">
              Encounter Risk Flags:
            </span>
            <div className="flex flex-wrap items-center gap-3">
              <label className="flex items-center gap-1.5 text-xs text-slate-700 cursor-pointer">
                <input
                  id={`${formId}-emergency-flag`}
                  data-testid="emergency-flag"
                  type="checkbox"
                  checked={emergencyFlag}
                  onChange={(e) => setEmergencyFlag(e.target.checked)}
                  className="rounded text-rose-600 focus:ring-rose-500"
                />
                <span className="font-bold text-rose-700 flex items-center gap-0.5">
                  <ShieldAlert className="w-3 h-3" aria-hidden="true" />
                  Emergency
                </span>
              </label>

              <label className="flex items-center gap-1.5 text-xs text-slate-700 cursor-pointer">
                <input
                  id={`${formId}-pregnancy-flag`}
                  data-testid="pregnancy-flag"
                  type="checkbox"
                  checked={pregnancyFlag}
                  onChange={(e) => setPregnancyFlag(e.target.checked)}
                  className="rounded text-purple-600 focus:ring-purple-500"
                />
                <span>High-Risk Pregnancy</span>
              </label>

              <label className="flex items-center gap-1.5 text-xs text-slate-700 cursor-pointer">
                <input
                  id={`${formId}-ncd-flag`}
                  data-testid="ncd-flag"
                  type="checkbox"
                  checked={ncdFlag}
                  onChange={(e) => setNcdFlag(e.target.checked)}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                <span>NCD Risk</span>
              </label>
            </div>
          </div>
        </div>

        {/* Nurse Notes / Clinical Observations */}
        <div>
          <label htmlFor={`${formId}-nurse-notes`} className="block text-xs font-bold text-slate-700 mb-1 flex items-center gap-1">
            <FileText className="w-3.5 h-3.5 text-slate-500" aria-hidden="true" />
            Nurse Triage Intake Notes & Clinical Observations
          </label>
          <textarea
            id={`${formId}-nurse-notes`}
            data-testid="nurse-notes"
            rows={2}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-hidden focus:ring-2 focus:ring-teal-500"
            placeholder="e.g. Patient conscious, oriented to time and place. Reports fever for 3 days and joint discomfort. Ambulatory without support."
          />
        </div>

        {/* Action Buttons */}
        <div className="pt-4 border-t border-slate-200 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" aria-hidden="true" />
            <span>
              Saving will forward this encounter to <strong>Doctor Consultation Queue</strong>.
            </span>
          </div>

          <div className="flex items-center gap-3">
            {onCancel && (
              <button
                type="button"
                onClick={onCancel}
                disabled={loading}
                className="px-4 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors shadow-2xs"
              >
                Cancel
              </button>
            )}

            <button
              id={`${formId}-save-triage-btn`}
              data-testid="save-triage-btn"
              type="submit"
              disabled={loading}
              className="inline-flex items-center gap-2 px-5 py-2 text-xs font-bold text-white bg-teal-700 hover:bg-teal-800 disabled:bg-slate-300 rounded-lg transition-colors shadow-2xs"
            >
              <Save className="w-4 h-4" aria-hidden="true" />
              {loading ? 'Saving Triage...' : 'Save Triage & Forward to Doctor'}
            </button>
          </div>
        </div>
      </div>
    </form>
  );
};

export default TriageVitalsForm;
