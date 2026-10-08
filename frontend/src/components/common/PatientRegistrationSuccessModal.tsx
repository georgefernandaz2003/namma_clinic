import React, { useEffect, useRef } from 'react';
import { CheckCircle2, X, ExternalLink } from 'lucide-react';
import type { Patient } from '../../types';

export interface PatientRegistrationSuccessModalProps {
  isOpen: boolean;
  patient: Patient | null;
  onClose: () => void;
  onViewPatient?: (patient: Patient) => void;
}

export const PatientRegistrationSuccessModal: React.FC<PatientRegistrationSuccessModalProps> = ({
  isOpen,
  patient,
  onClose,
  onViewPatient,
}) => {
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    const timer = setTimeout(() => {
      closeButtonRef.current?.focus();
    }, 50);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      clearTimeout(timer);
    };
  }, [isOpen, onClose]);

  if (!isOpen || !patient) return null;

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="registration-success-title"
      data-testid="patient-registration-success-modal"
    >
      <div className="relative bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
        {/* Top Header & Close Icon */}
        <div className="flex items-start justify-between">
          <div className="w-8" aria-hidden="true" />
          <div className="flex flex-col items-center text-center">
            <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mb-2 shadow-xs">
              <CheckCircle2 className="w-7 h-7 text-emerald-600" aria-hidden="true" />
            </div>
            <h2
              id="registration-success-title"
              className="text-lg font-bold text-slate-900"
              data-testid="registration-success-title"
            >
              Patient Registered Successfully
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Demographic intake verified & added to master directory
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition cursor-pointer"
            aria-label="Close confirmation dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Authoritative Patient Details Card */}
        <div
          className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2.5 text-xs"
          data-testid="registration-success-patient-details"
        >
          <div className="flex items-center justify-between">
            <span className="text-slate-500 font-medium">Patient Name:</span>
            <span
              className="text-slate-900 font-bold"
              data-testid="registered-patient-name"
            >
              {patient.name}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-slate-500 font-medium">Patient ID:</span>
            <span
              className="font-mono font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-lg border border-emerald-200"
              data-testid="registered-patient-id"
            >
              {patient.patient_id || String(patient.id)}
            </span>
          </div>

          {patient.mobile && (
            <div className="flex items-center justify-between">
              <span className="text-slate-500 font-medium">Mobile Number:</span>
              <span
                className="text-slate-800 font-medium font-mono"
                data-testid="registered-patient-mobile"
              >
                {patient.mobile}
              </span>
            </div>
          )}

          {patient.facility_name && (
            <div className="flex items-center justify-between">
              <span className="text-slate-500 font-medium">Registered Facility:</span>
              <span
                className="text-slate-800 font-medium"
                data-testid="registered-patient-facility"
              >
                {patient.facility_name}
              </span>
            </div>
          )}

          <div className="flex items-center justify-between pt-1 border-t border-slate-200/70">
            <span className="text-slate-500 font-medium">Registration Status:</span>
            <span
              className="inline-flex items-center gap-1.5 font-bold text-emerald-700 bg-emerald-100/70 px-2.5 py-0.5 rounded-full text-[11px]"
              data-testid="registered-patient-status"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" aria-hidden="true" />
              Registered
            </span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-slate-100">
          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            className="px-4 py-2 border border-slate-300 text-slate-700 font-bold text-xs rounded-xl hover:bg-slate-100 transition cursor-pointer"
            data-testid="close-confirmation-button"
          >
            Close
          </button>
          {onViewPatient && patient.id && (
            <button
              type="button"
              onClick={() => onViewPatient(patient)}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs transition cursor-pointer flex items-center gap-1.5"
              data-testid="view-patient-button"
            >
              <span>View Patient</span>
              <ExternalLink className="w-3.5 h-3.5" aria-hidden="true" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default PatientRegistrationSuccessModal;
