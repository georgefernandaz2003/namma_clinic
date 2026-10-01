import React from 'react';
import type { Consultation } from '../../types';
import { FileText } from 'lucide-react';

interface ConsultationHistoryCardProps {
  consultations: Consultation[];
}

export const ConsultationHistoryCard: React.FC<ConsultationHistoryCardProps> = ({ consultations }) => {
  if (consultations.length === 0) return null;

  return (
    <section aria-labelledby="history-heading" className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
      <h2 id="history-heading" className="text-sm font-bold text-slate-900 mb-2 flex items-center gap-2">
        <FileText className="w-4 h-4 text-emerald-600" aria-hidden="true" />
        <span>Patient Longitudinal History ({consultations.length} previous records)</span>
      </h2>
      <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
        {consultations.map((c) => (
          <div key={c.id} className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs">
            <div className="flex items-center justify-between font-bold text-slate-800">
              <span>Visit #{c.visit} • {c.diagnosis_name || 'Diagnosis unrecorded'}</span>
              <span className="font-mono text-slate-500 font-normal">{c.created_at?.split('T')[0]}</span>
            </div>
            <div className="text-slate-600 mt-1">
              <strong>Complaint:</strong> {c.chief_complaint}
              {c.treatment_plan && ` | Plan: ${c.treatment_plan}`}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

export default ConsultationHistoryCard;
