import React from 'react';
import { Activity } from 'lucide-react';

interface ConsultationFormCardProps {
  chiefComplaint: string;
  setChiefComplaint: (val: string) => void;
  clinicalHistory: string;
  setClinicalHistory: (val: string) => void;
  clinicalAssessment: string;
  setClinicalAssessment: (val: string) => void;
  diagnosisCode: string;
  setDiagnosisCode: (val: string) => void;
  diagnosisName: string;
  setDiagnosisName: (val: string) => void;
  treatmentPlan: string;
  setTreatmentPlan: (val: string) => void;
  clinicalNotes: string;
  setClinicalNotes: (val: string) => void;
}

export const ConsultationFormCard: React.FC<ConsultationFormCardProps> = ({
  chiefComplaint,
  setChiefComplaint,
  clinicalHistory,
  setClinicalHistory,
  clinicalAssessment,
  setClinicalAssessment,
  diagnosisCode,
  setDiagnosisCode,
  diagnosisName,
  setDiagnosisName,
  treatmentPlan,
  setTreatmentPlan,
  clinicalNotes,
  setClinicalNotes
}) => {
  return (
    <section aria-labelledby="exam-heading" className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-4">
      <h2 id="exam-heading" className="text-sm font-bold text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-2">
        <Activity className="w-4 h-4 text-emerald-600" aria-hidden="true" />
        <span>Medical Officer Consultation Documentation</span>
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="chief-complaint" className="block text-xs font-bold text-slate-700 mb-1">
            Chief Complaint <span className="text-rose-500">*</span>
          </label>
          <textarea
            id="chief-complaint"
            rows={2}
            value={chiefComplaint}
            onChange={(e) => setChiefComplaint(e.target.value)}
            placeholder="e.g. High fever with chills, body aches for 3 days"
            required
            className="w-full text-xs p-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:border-emerald-600"
          />
        </div>

        <div>
          <label htmlFor="clinical-history" className="block text-xs font-bold text-slate-700 mb-1">
            History of Present Illness & Comorbidities
          </label>
          <textarea
            id="clinical-history"
            rows={2}
            value={clinicalHistory}
            onChange={(e) => setClinicalHistory(e.target.value)}
            placeholder="e.g. Known hypertensive, no history of cough or rash"
            className="w-full text-xs p-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:border-emerald-600"
          />
        </div>
      </div>

      <div>
        <label htmlFor="clinical-assessment" className="block text-xs font-bold text-slate-700 mb-1">
          Clinical Assessment & Physical Examination Findings
        </label>
        <textarea
          id="clinical-assessment"
          rows={2}
          value={clinicalAssessment}
          onChange={(e) => setClinicalAssessment(e.target.value)}
          placeholder="e.g. Mild pharyngeal congestion, chest clear, no hepatosplenomegaly"
          className="w-full text-xs p-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:border-emerald-600"
        />
      </div>

      {/* Structured Diagnosis */}
      <div className="p-3 bg-emerald-50/50 border border-emerald-200 rounded-xl space-y-3">
        <span className="text-xs font-bold text-emerald-900 block">
          Authoritative Clinical Diagnosis
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label htmlFor="diagnosis-code" className="block text-[11px] font-bold text-slate-700 mb-1">
              Diagnosis Code (ICD-10) <span className="text-rose-500">*</span>
            </label>
            <input
              id="diagnosis-code"
              type="text"
              value={diagnosisCode}
              onChange={(e) => setDiagnosisCode(e.target.value)}
              placeholder="e.g. R50.9, I10, A90"
              required
              className="w-full text-xs p-2 bg-white border border-slate-300 rounded-lg font-mono focus:outline-none focus:border-emerald-600"
            />
          </div>
          <div className="sm:col-span-2">
            <label htmlFor="diagnosis-name" className="block text-[11px] font-bold text-slate-700 mb-1">
              Diagnosis Name / Condition <span className="text-rose-500">*</span>
            </label>
            <input
              id="diagnosis-name"
              type="text"
              value={diagnosisName}
              onChange={(e) => setDiagnosisName(e.target.value)}
              placeholder="e.g. Viral Pyrexia / Suspected Dengue Fever"
              required
              className="w-full text-xs p-2 bg-white border border-slate-300 rounded-lg focus:outline-none focus:border-emerald-600"
            />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="treatment-plan" className="block text-xs font-bold text-slate-700 mb-1">
            Treatment Plan & Advice
          </label>
          <textarea
            id="treatment-plan"
            rows={2}
            value={treatmentPlan}
            onChange={(e) => setTreatmentPlan(e.target.value)}
            placeholder="e.g. Adequate oral hydration, rest, warning signs explained"
            className="w-full text-xs p-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:border-emerald-600"
          />
        </div>

        <div>
          <label htmlFor="clinical-notes" className="block text-xs font-bold text-slate-700 mb-1">
            Confidential Clinical Notes
          </label>
          <textarea
            id="clinical-notes"
            rows={2}
            value={clinicalNotes}
            onChange={(e) => setClinicalNotes(e.target.value)}
            placeholder="Physician notes, differential diagnosis observations"
            className="w-full text-xs p-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:border-emerald-600"
          />
        </div>
      </div>
    </section>
  );
};

export default ConsultationFormCard;
