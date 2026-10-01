import React, { useState } from 'react';
import { X, ArrowRightLeft, AlertCircle, Info } from 'lucide-react';
import type { TransferStaffPayload, StaffProfile } from '../../types/staff';

interface FacilityOption {
  id: number;
  name: string;
}

interface TransferStaffModalProps {
  isOpen: boolean;
  staff: StaffProfile;
  facilities?: FacilityOption[];
  isLoading?: boolean;
  onTransfer: (payload: TransferStaffPayload) => Promise<void>;
  onClose: () => void;
}

export const TransferStaffModal: React.FC<TransferStaffModalProps> = ({
  isOpen,
  staff,
  facilities = [],
  isLoading = false,
  onTransfer,
  onClose,
}) => {
  const currentFacilityName = staff.facility_assignment?.facility_name || 'Unassigned';
  const currentFacilityId = staff.facility_assignment?.facility_id;

  // Filter out the current facility so administrator cannot select the same facility
  const eligibleFacilities = facilities.filter((f) => f.id !== currentFacilityId);

  const todayStr = new Date().toISOString().split('T')[0];

  const [newFacilityId, setNewFacilityId] = useState<number>(eligibleFacilities[0]?.id || 1);
  const [effectiveDate, setEffectiveDate] = useState<string>(todayStr);
  const [reason, setReason] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const isFutureDate = effectiveDate > todayStr;
  const staffDisplayName = `${staff.person_details?.first_name || ''} ${staff.person_details?.last_name || ''}`.trim() || staff.employee_id;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!newFacilityId) {
      setError('Please select a destination facility.');
      return;
    }
    if (!effectiveDate) {
      setError('Please select an effective transfer date.');
      return;
    }

    try {
      const payload: TransferStaffPayload = {
        new_facility_id: Number(newFacilityId),
        effective_date: effectiveDate,
        reason: reason.trim() || undefined,
      };

      await onTransfer(payload);
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Transfer request failed. Please check parameters and try again.');
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="transfer-modal-title"
    >
      <div className="relative bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-100">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-blue-50 text-blue-600 rounded-xl">
              <ArrowRightLeft className="w-5 h-5" />
            </div>
            <div>
              <h3 id="transfer-modal-title" className="text-base font-bold text-slate-900">
                Transfer Staff Facility
              </h3>
              <p className="text-xs text-slate-500 font-medium">{staffDisplayName}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-lg transition"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded-xl flex items-start gap-2 text-xs text-rose-700 font-medium">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
              Current Facility
            </label>
            <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm font-semibold text-slate-800">
              {currentFacilityName}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              New Destination Facility <span className="text-rose-500">*</span>
            </label>
            {eligibleFacilities.length > 0 ? (
              <select
                value={newFacilityId}
                onChange={(e) => setNewFacilityId(Number(e.target.value))}
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                data-testid="transfer-destination-select"
              >
                {eligibleFacilities.map((fac) => (
                  <option key={fac.id} value={fac.id}>
                    {fac.name}
                  </option>
                ))}
              </select>
            ) : (
              <p className="text-xs text-amber-600 bg-amber-50 p-2.5 rounded-lg border border-amber-200">
                No alternative facilities available in scope for transfer.
              </p>
            )}
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Effective Transfer Date <span className="text-rose-500">*</span>
            </label>
            <input
              type="date"
              required
              value={effectiveDate}
              onChange={(e) => setEffectiveDate(e.target.value)}
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 focus:outline-none"
              data-testid="transfer-effective-date"
            />
          </div>

          {/* Transfer notice regarding single facility access */}
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl flex items-start gap-2.5">
            <Info className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-blue-900 leading-relaxed">
              {isFutureDate ? (
                <span>
                  <strong>Future Transfer:</strong> Staff will enter <code>TRANSFER_PENDING</code> state. Current facility access remains active until the effective date. Dual simultaneous facility access is never granted.
                </span>
              ) : (
                <span>
                  <strong>Immediate Transfer:</strong> Facility posting will immediately shift to the destination clinic upon confirmation.
                </span>
              )}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Reason for Transfer (Optional)</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. Administrative deployment / Staff request"
              rows={2}
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 text-sm font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || eligibleFacilities.length === 0}
              className="px-4 py-2 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition disabled:opacity-50 inline-flex items-center gap-2"
              data-testid="submit-transfer-btn"
            >
              {isLoading ? 'Executing Transfer...' : 'Confirm Transfer'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default TransferStaffModal;