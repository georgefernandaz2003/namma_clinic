import React from 'react';
import type { Consultation } from '../../types';
import { FileText, ExternalLink } from 'lucide-react';

interface ConsultationHistoryCardProps {
  consultations: Consultation[];
  onSelectVisit?: (visitId: number) => void;
}

export const ConsultationHistoryCard: React.FC<ConsultationHistoryCardProps> = ({
  consultations,
  onSelectVisit
}) => {
  if (consultations.length === 0) return null;

  return (
    <section aria-labelledby="history-heading" className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
      <div className="flex items-center justify-between mb-2">
        <h2 id="history-heading" className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <FileText className="w-4 h-4 text-emerald-600" aria-hidden="true" />
          <span>Patient Longitudinal History ({consultations.length} previous records)</span>
        </h2>
        <span className="text-[11px] text-slate-400 font-medium">Click any visit to view full clinical details</span>
      </div>
      <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
        {consultations.map((c) => (
          <div
            key={c.id}
            role="button"
            tabIndex={0}
            aria-label={`View full details for Visit #${c.visit} - ${c.diagnosis_name || 'Diagnosis unrecorded'}`}
            onClick={(e) => {
              e.stopPropagation();
              onSelectVisit?.(c.visit);
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                e.stopPropagation();
                onSelectVisit?.(c.visit);
              }
            }}
            className="group p-3 bg-slate-50 hover:bg-emerald-50/60 rounded-xl border border-slate-200 hover:border-emerald-300 transition-all text-xs cursor-pointer shadow-2xs hover:shadow-xs focus:outline-none focus:ring-2 focus:ring-emerald-500/40 select-none"
          >
            <div className="flex items-center justify-between font-bold text-slate-800">
              <div className="flex items-center gap-1.5 min-w-0">
                <span className="font-mono text-emerald-800 group-hover:text-emerald-950 font-bold shrink-0">
                  Visit #{c.visit}
                </span>
                <span className="text-slate-400 font-normal shrink-0">•</span>
                <span className="text-slate-900 font-semibold truncate">
                  {c.diagnosis_name || 'Diagnosis unrecorded'}
                </span>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className="font-mono text-slate-500 font-normal">{c.created_at?.split('T')[0]}</span>
                <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-100/70 border border-emerald-200 px-1.5 py-0.5 rounded-md flex items-center gap-1 group-hover:bg-emerald-600 group-hover:text-white transition-colors">
                  <span>View Details</span>
                  <ExternalLink className="w-2.5 h-2.5" aria-hidden="true" />
                </span>
              </div>
            </div>
            <div className="text-slate-600 mt-1 line-clamp-2">
              <strong className="text-slate-700">Complaint:</strong> {c.chief_complaint}
              {c.treatment_plan && ` | Plan: ${c.treatment_plan}`}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

export default ConsultationHistoryCard;
