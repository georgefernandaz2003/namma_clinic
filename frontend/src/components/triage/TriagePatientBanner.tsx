import React from 'react';
import { User, Phone, MapPin, Hash, AlertTriangle, ShieldCheck, Clock } from 'lucide-react';
import type { Patient, Visit } from '../../types';

interface TriagePatientBannerProps {
  patient: Patient;
  visit: Visit;
}

export const TriagePatientBanner: React.FC<TriagePatientBannerProps> = ({ patient, visit }) => {
  const isEmergency = visit.priority === 'EMERGENCY';
  const isHighPriority = visit.priority === 'HIGH';

  const displayName =
    patient.name ||
    `${patient.first_name || ''} ${patient.last_name || ''}`.trim() ||
    `Patient #${patient.id}`;

  const displayId = patient.uhid || patient.patient_id || `PAT-${patient.id}`;
  const displayPhone = patient.mobile || patient.contact_number;
  const displayAbha = patient.abha_address || patient.ABHA_ID_DEMO;
  const initial = displayName ? displayName[0].toUpperCase() : 'P';

  return (
    <div data-testid="patient-banner" className="bg-white rounded-xl shadow-xs border border-slate-200 overflow-hidden mb-6">
      <div className="bg-gradient-to-r from-teal-700 via-teal-800 to-emerald-900 px-6 py-4 text-white">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-full bg-teal-600/60 border border-teal-400/40 flex items-center justify-center font-bold text-lg text-white">
              {initial}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight text-white">
                  {displayName}
                </h1>
                <span className="text-xs bg-teal-600/80 text-teal-100 px-2 py-0.5 rounded font-mono">
                  {patient.gender} • {patient.age} yrs
                </span>
                {patient.blood_group && (
                  <span className="text-xs bg-rose-900/60 text-rose-200 border border-rose-500/30 px-2 py-0.5 rounded font-bold">
                    {patient.blood_group}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-3 text-xs text-teal-200 mt-1">
                <span className="flex items-center gap-1 font-mono">
                  <Hash className="w-3.5 h-3.5" aria-hidden="true" />
                  ID: {displayId}
                </span>
                {displayAbha && (
                  <span className="flex items-center gap-1 bg-teal-900/60 text-teal-100 px-1.5 py-0.5 rounded text-[11px]">
                    <ShieldCheck className="w-3 h-3 text-emerald-400" aria-hidden="true" />
                    ABHA: {displayAbha}
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right">
              <span className="text-[11px] text-teal-200 block uppercase tracking-wider font-semibold">
                Daily Token
              </span>
              <span className="text-2xl font-black text-amber-300 font-mono">
                #{visit.token_number ?? visit.id}
              </span>
            </div>
            <div className="h-8 w-px bg-teal-600/60" />
            <div className="text-right">
              <span className="text-[11px] text-teal-200 block uppercase tracking-wider font-semibold">
                Priority
              </span>
              <span
                className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold ${
                  isEmergency
                    ? 'bg-rose-500 text-white animate-pulse'
                    : isHighPriority
                    ? 'bg-amber-400 text-amber-950'
                    : 'bg-teal-600/80 text-teal-100'
                }`}
              >
                {isEmergency && <AlertTriangle className="w-3 h-3" aria-hidden="true" />}
                {visit.priority || 'NORMAL'}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="px-6 py-3 bg-slate-50 border-t border-slate-100 flex flex-wrap items-center justify-between gap-4 text-xs text-slate-600">
        <div className="flex flex-wrap items-center gap-5">
          <span className="flex items-center gap-1">
            <User className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
            <strong className="text-slate-700">Visit ID:</strong> {visit.visit_id || `VIS-${visit.id}`}
          </span>
          {displayPhone && (
            <span className="flex items-center gap-1">
              <Phone className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
              <strong className="text-slate-700">Phone:</strong> {displayPhone}
            </span>
          )}
          {patient.address && (
            <span className="flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
              <strong className="text-slate-700">Address:</strong> {patient.address}
            </span>
          )}
        </div>

        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1 text-slate-500">
            <Clock className="w-3.5 h-3.5" aria-hidden="true" />
            Encounter Date: <strong className="text-slate-700">{visit.opd_date || visit.visit_date}</strong>
          </span>
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-200 text-slate-700">
            Status: {visit.status}
          </span>
        </div>
      </div>
    </div>
  );
};

export default TriagePatientBanner;
