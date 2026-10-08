import React, { useEffect, useRef, useState } from 'react';
import { CheckCircle2, X, ExternalLink, Ticket, ArrowRight } from 'lucide-react';
import type { Patient } from '../../types';

export interface PatientRegistrationSuccessModalProps {
  isOpen: boolean;
  patient: Patient | null;
  canIssueToken?: boolean;
  onClose: () => void;
  onViewPatient?: (patient: Patient) => void;
  onConfirmIssueToken?: (patient: Patient) => Promise<any> | void;
  onNavigateQueue?: () => void;
}

export const PatientRegistrationSuccessModal: React.FC<PatientRegistrationSuccessModalProps> = ({
  isOpen,
  patient,
  canIssueToken = true,
  onClose,
  onViewPatient,
  onConfirmIssueToken,
  onNavigateQueue,
}) => {
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const [isIssuingToken, setIsIssuingToken] = useState(false);
  const [tokenError, setTokenError] = useState<string | null>(null);
  const [issuedToken, setIssuedToken] = useState<{
    tokenNumber: string | number;
    visitId?: string | number;
    queue?: string;
  } | null>(null);

  useEffect(() => {
    if (!isOpen) {
      setIssuedToken(null);
      setTokenError(null);
      setIsIssuingToken(false);
      return;
    }

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

  const handleConfirmToken = async () => {
    if (!patient || !onConfirmIssueToken || isIssuingToken) return;
    setIsIssuingToken(true);
    setTokenError(null);
    try {
      const result = await onConfirmIssueToken(patient);
      if (result) {
        const tokenNum =
          result.token_details?.token_number ||
          result.token_number ||
          result.id;
        setIssuedToken({
          tokenNumber: tokenNum,
          visitId: result.visit_id || result.id,
          queue: result.current_queue || 'TRIAGE',
        });
      }
    } catch (err: any) {
      const msg =
        err?.response?.data?.error ||
        err?.response?.data?.detail ||
        (err?.response?.data && typeof err.response.data === 'object'
          ? Object.entries(err.response.data)
              .map(([k, v]) => `${k.toUpperCase()}: ${Array.isArray(v) ? v.join(', ') : v}`)
              .join('\n')
          : null) ||
        err?.message ||
        'Failed to automatically create OPD queue token.';
      setTokenError(msg);
    } finally {
      setIsIssuingToken(false);
    }
  };

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
            disabled={isIssuingToken}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition cursor-pointer disabled:opacity-50"
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

        {/* OPD Token Issuance Confirmation Section */}
        {canIssueToken && onConfirmIssueToken && (
          <>
            {issuedToken ? (
              <div
                className="bg-emerald-50 border border-emerald-300 rounded-xl p-4 text-center space-y-1.5"
                data-testid="token-issued-success"
              >
                <div className="flex items-center justify-center gap-1.5 text-emerald-900 font-bold text-xs">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>OPD Queue Token Created Successfully!</span>
                </div>
                <div
                  className="text-2xl font-black text-emerald-700 font-mono tracking-tight"
                  data-testid="issued-token-number"
                >
                  Token #{issuedToken.tokenNumber}
                </div>
                <p className="text-[11px] text-emerald-700">
                  {patient.name} has been added to the live clinic queue.
                </p>
              </div>
            ) : (
              <div
                className="bg-emerald-50/70 border border-emerald-200/80 rounded-xl p-3.5 space-y-1.5"
                data-testid="token-confirmation-prompt"
              >
                <div className="flex items-center gap-2 text-emerald-900 font-bold text-xs">
                  <Ticket className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>Issue OPD Queue Token</span>
                </div>
                <p className="text-[11px] text-emerald-800 leading-relaxed">
                  Would you like to automatically create an OPD queue token and place <strong>{patient.name}</strong> into the live consultation queue?
                </p>
                {tokenError && (
                  <div
                    className="mt-2 p-2 bg-rose-50 border border-rose-200 rounded-lg text-[11px] text-rose-700 font-medium"
                    data-testid="token-issuance-error"
                  >
                    {tokenError}
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100 flex-wrap">
          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            disabled={isIssuingToken}
            className="px-3.5 py-2 border border-slate-300 text-slate-700 font-bold text-xs rounded-xl hover:bg-slate-100 transition cursor-pointer disabled:opacity-50"
            data-testid="close-confirmation-button"
          >
            Close
          </button>

          {onViewPatient && patient.id && !issuedToken && (
            <button
              type="button"
              onClick={() => onViewPatient(patient)}
              disabled={isIssuingToken}
              className="px-3.5 py-2 border border-slate-300 text-slate-700 font-bold text-xs rounded-xl hover:bg-slate-100 transition cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
              data-testid="view-patient-button"
            >
              <span>View Patient</span>
              <ExternalLink className="w-3.5 h-3.5" aria-hidden="true" />
            </button>
          )}

          {canIssueToken && onConfirmIssueToken && !issuedToken && (
            <button
              type="button"
              onClick={handleConfirmToken}
              disabled={isIssuingToken}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs transition cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
              data-testid="confirm-issue-token-button"
            >
              {isIssuingToken ? (
                <>
                  <span className="inline-block w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Creating OPD Token...</span>
                </>
              ) : (
                <>
                  <Ticket className="w-3.5 h-3.5" aria-hidden="true" />
                  <span>Confirm & Create OPD Token</span>
                </>
              )}
            </button>
          )}

          {issuedToken && onNavigateQueue && (
            <button
              type="button"
              onClick={onNavigateQueue}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs transition cursor-pointer flex items-center gap-1.5"
              data-testid="go-to-queue-button"
            >
              <span>View in OPD Queue</span>
              <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default PatientRegistrationSuccessModal;
