import React from 'react';
import { HeartPulse, Baby } from 'lucide-react';

export const MaternalChild: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <HeartPulse className="w-6 h-6 text-rose-600" />
          Maternal, Child & Reproductive Health (RCH) Console
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Antenatal Care (ANC), High-Risk Pregnancy tracking, PNC follow-ups, and Immunization schedules
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-panel p-5 rounded-2xl border border-slate-200 bg-white space-y-3 shadow-xs">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2 pb-2 border-b border-slate-100">
            <HeartPulse className="w-4 h-4 text-rose-600" />
            Antenatal Care (ANC) & High-Risk Pregnancy Roster
          </h2>
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2 text-xs">
            <div className="flex justify-between items-center">
              <span className="font-bold text-slate-900">Anita Devi (Age 30)</span>
              <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200">High Risk ANC</span>
            </div>
            <p className="text-slate-600">ANC Registration #: ANC-2026-0042 • EDD: 2026-11-15</p>
            <p className="text-slate-800 font-medium">TT Vaccine: Done • IFA Tablets: Issued • High Risk Reason: Severe Anemia suspicion</p>
          </div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-200 bg-white space-y-3 shadow-xs">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2 pb-2 border-b border-slate-100">
            <Baby className="w-4 h-4 text-teal-600" />
            Child Health & Immunization Tracker
          </h2>
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2 text-xs">
            <div className="flex justify-between items-center">
              <span className="font-bold text-slate-900">Baby of Anita (Age 11 months)</span>
              <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">Immunization Up-to-date</span>
            </div>
            <p className="text-slate-600">Birth Weight: 3.1 kg • Growth Chart: Green Zone</p>
            <p className="text-slate-800 font-medium">Next Scheduled Vaccine: MR 1st Dose & Vitamin A</p>
          </div>
        </div>
      </div>
    </div>
  );
};
