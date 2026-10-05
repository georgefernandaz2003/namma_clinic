import React, { useState } from 'react';
import { X, ShieldCheck, AlertCircle } from 'lucide-react';
import type { Role } from '../../types/auth';
import type { AssignRolePayload } from '../../types/staff';

interface FacilityOption {
  id: number;
  name: string;
}

interface AssignRoleModalProps {
  isOpen: boolean;
  staffName: string;
  userRole?: Role;
  userFacilityId?: number | null;
  facilities?: FacilityOption[];
  isLoading?: boolean;
  onAssign: (payload: AssignRolePayload) => Promise<void>;
  onClose: () => void;
}

export const AssignRoleModal: React.FC<AssignRoleModalProps> = ({
  isOpen,
  staffName,
  userRole,
  userFacilityId,
  facilities = [],
  isLoading = false,
  onAssign,
  onClose,
}) => {
  const isDHO = userRole === 'DISTRICT_OFFICER';

  // Allowed operational roles strictly governed by backend authority:
  // Hospital Admin can assign: DOCTOR, NURSE, COMPOUNDER, LAB_TECHNICIAN, PHARMACIST
  // DHO can also assign HOSPITAL_ADMIN
  // NEVER DISTRICT_OFFICER (to Clinic Admin), NEVER SYSTEM_ADMIN, NEVER NURSE_COMPOUNDER
  const roleOptions: { value: Role; label: string }[] = isDHO
    ? [
        { value: 'DOCTOR', label: 'Doctor (Medical Officer)' },
        { value: 'NURSE', label: 'Nurse' },
        { value: 'FRONT_DESK_OFFICER', label: 'Front Desk Officer' },
        { value: 'LAB_TECHNICIAN', label: 'Lab Technician' },
        { value: 'PHARMACIST', label: 'Pharmacist' },
        { value: 'INVENTORY', label: 'Inventory Manager' },
        { value: 'HOSPITAL_ADMIN', label: 'Hospital Admin (Clinic Admin)' },
      ]
    : [
        { value: 'DOCTOR', label: 'Doctor (Medical Officer)' },
        { value: 'NURSE', label: 'Nurse' },
        { value: 'FRONT_DESK_OFFICER', label: 'Front Desk Officer' },
        { value: 'LAB_TECHNICIAN', label: 'Lab Technician' },
        { value: 'PHARMACIST', label: 'Pharmacist' },
        { value: 'INVENTORY', label: 'Inventory Manager' },
      ];

  const todayStr = new Date().toISOString().split('T')[0];

  const [roleCode, setRoleCode] = useState<Role>('NURSE');
  const [facilityId, setFacilityId] = useState<number>(userFacilityId || facilities[0]?.id || 1);
  const [effectiveFrom, setEffectiveFrom] = useState<string>(todayStr);
  const [effectiveTo, setEffectiveTo] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!roleCode) {
      setError('Please select an operational role.');
      return;
    }

    try {
      const payload: AssignRolePayload = {
        role_code: roleCode,
        facility_id: isDHO ? Number(facilityId) : (userFacilityId || Number(facilityId)),
        effective_from: effectiveFrom,
        effective_to: effectiveTo ? effectiveTo : undefined,
      };

      await onAssign(payload);
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to assign role. The backend rejected this assignment.');
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="assign-role-title"
    >
      <div className="relative bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-100">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-indigo-50 text-indigo-600 rounded-xl">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 id="assign-role-title" className="text-base font-bold text-slate-900">
                Assign Operational Role
              </h3>
              <p className="text-xs text-slate-500 font-medium">Assign role to {staffName}</p>
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
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Select Role <span className="text-rose-500">*</span>
            </label>
            <select
              value={roleCode}
              onChange={(e) => setRoleCode(e.target.value as Role)}
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              data-testid="assign-role-select"
            >
              {roleOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <p className="text-[11px] text-slate-400 mt-1">
              For dual clinical workers (e.g. Nurse + Compounder), assign each role separately to create distinct role records.
            </p>
          </div>

          {isDHO && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Facility <span className="text-rose-500">*</span>
              </label>
              <select
                value={facilityId}
                onChange={(e) => setFacilityId(Number(e.target.value))}
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                data-testid="assign-facility-select"
              >
                {facilities.map((fac) => (
                  <option key={fac.id} value={fac.id}>
                    {fac.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Effective From <span className="text-rose-500">*</span>
              </label>
              <input
                type="date"
                required
                value={effectiveFrom}
                onChange={(e) => setEffectiveFrom(e.target.value)}
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Effective To</label>
              <input
                type="date"
                value={effectiveTo}
                min={effectiveFrom}
                onChange={(e) => setEffectiveTo(e.target.value)}
                placeholder="Optional"
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              />
            </div>
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
              disabled={isLoading}
              className="px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition disabled:opacity-50 inline-flex items-center gap-2"
              data-testid="submit-assign-role-btn"
            >
              {isLoading ? 'Assigning...' : 'Assign Role'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AssignRoleModal;