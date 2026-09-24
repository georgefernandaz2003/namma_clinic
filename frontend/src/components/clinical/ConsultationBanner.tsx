import React from 'react';
import type { Patient, Visit } from '../../types';
import { User } from 'lucide-react';

interface ConsultationBannerProps {
  patient: Patient;
  visit: Visit;
}

export const ConsultationBanner: React.FC<ConsultationBannerProps> = ({ patient, visit }) => {
  return (
    <section aria-labelledby="patient-banner-heading" className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs">
      <h2 id="patient-banner-heading" className="sr-only">Patient Information</h2>
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center justify-center shrink-0">
            <User className="w-6 h-6" aria-hidden="true" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-slate-900">{patient.name}</h2>
              <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
                {patient.gender} • {patient.age} yrs
              </span>
              <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-100 text-emerald-800">
                Token #{visit.token_number || visit.id}
              </span>
            </div>
            <div className="text-xs text-slate-500 mt-1 flex flex-wrap items-center gap-x-4 gap-y-1">
              <span>Patient ID: <strong className="font-mono text-slate-700">{patient.patient_id}</strong></span>
              <span>Visit ID: <strong className="font-mono text-slate-700">{visit.visit_id}</strong></span>
              <span>Mobile: <strong>{patient.mobile || 'N/A'}</strong></span>
              <span>Priority: <strong>{visit.priority || 'NORMAL'}</strong></span>
            </div>
          </div>
        </div>

        <div className="text-right text-xs text-slate-500 self-end md:self-center">
          <div>Encounter Status: <strong className="text-slate-800">{visit.status}</strong></div>
          <div>Queue: <strong className="font-mono text-slate-800">{visit.current_queue}</strong></div>
        </div>
      </div>
    </section>
  );
};

export default ConsultationBanner;
