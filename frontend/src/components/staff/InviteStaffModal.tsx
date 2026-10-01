import React, { useState } from 'react';
import { X, UserPlus, AlertCircle } from 'lucide-react';
import type { Role } from '../../types/auth';
import type { InviteStaffPayload } from '../../types/staff';

interface FacilityOption {
  id: number;
  name: string;
}

interface InviteStaffModalProps {
  isOpen: boolean;
  userRole?: Role;
  userFacilityId?: number | null;
  facilities?: FacilityOption[];
  isLoading?: boolean;
  onInvite: (payload: InviteStaffPayload) => Promise<void>;
  onClose: () => void;
}

export const InviteStaffModal: React.FC<InviteStaffModalProps> = ({
  isOpen,
  userRole,
  userFacilityId,
  facilities = [],
  isLoading = false,
  onInvite,
  onClose,
}) => {
  const isDHO = userRole === 'DISTRICT_OFFICER';

  // Allowed operational roles strictly governed by backend permissions
  // Hospital Admin can only invite operational clinical roles
  // DHO can also assign Hospital Admin for a clinic
  // NEVER SYSTEM_ADMIN, SUPER_ADMIN, CLINIC_ADMIN, NURSE_COMPOUNDER
  const roleOptions: { value: Role; label: string }[] = isDHO
    ? [
        { value: 'DOCTOR', label: 'Doctor (Medical Officer)' },
        { value: 'NURSE', label: 'Nurse' },
        { value: 'COMPOUNDER', label: 'Compounder' },
        { value: 'LAB_TECHNICIAN', label: 'Lab Technician' },
        { value: 'PHARMACIST', label: 'Pharmacist' },
        { value: 'HOSPITAL_ADMIN', label: 'Hospital Admin (Clinic Admin)' },
      ]
    : [
        { value: 'DOCTOR', label: 'Doctor (Medical Officer)' },
        { value: 'NURSE', label: 'Nurse' },
        { value: 'COMPOUNDER', label: 'Compounder' },
        { value: 'LAB_TECHNICIAN', label: 'Lab Technician' },
        { value: 'PHARMACIST', label: 'Pharmacist' },
      ];

  const defaultFacilityId = userFacilityId || facilities[0]?.id || 1;

  const [formData, setFormData] = useState<{
    first_name: string;
    last_name: string;
    gender: string;
    date_of_birth: string;
    phone_number: string;
    employee_id: string;
    designation: string;
    role_code: Role;
    facility_id: number;
    medical_council_reg_number: string;
    email: string;
  }>({
    first_name: '',
    last_name: '',
    gender: 'FEMALE',
    date_of_birth: '1990-01-01',
    phone_number: '',
    employee_id: '',
    designation: 'Medical Officer',
    role_code: 'DOCTOR',
    facility_id: defaultFacilityId,
    medical_council_reg_number: '',
    email: '',
  });

  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!formData.first_name.trim()) {
      setError('First name is required.');
      return;
    }
    if (!formData.last_name.trim()) {
      setError('Last name is required.');
      return;
    }
    if (!formData.employee_id.trim()) {
      setError('Employee ID is required.');
      return;
    }
    if (!formData.role_code) {
      setError('Operational role is required.');
      return;
    }

    try {
      const targetFacilityId = isDHO ? Number(formData.facility_id) : (userFacilityId || Number(formData.facility_id));
      const payload: InviteStaffPayload = {
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
        gender: formData.gender,
        date_of_birth: formData.date_of_birth,
        phone_number: formData.phone_number.trim() || undefined,
        employee_id: formData.employee_id.trim().toUpperCase(),
        designation: formData.designation.trim() || formData.role_code,
        role_code: formData.role_code,
        facility_id: targetFacilityId,
        medical_council_reg_number: formData.medical_council_reg_number.trim() || undefined,
        email: formData.email.trim() || undefined,
      };

      await onInvite(payload);
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to send invitation. Please check details and try again.');
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="invite-staff-title"
    >
      <div className="relative bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-100 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-emerald-50 text-emerald-600 rounded-xl">
              <UserPlus className="w-5 h-5" />
            </div>
            <div>
              <h3 id="invite-staff-title" className="text-lg font-bold text-slate-900">
                Invite Healthcare Staff
              </h3>
              <p className="text-xs text-slate-500">
                Create new staff account in INVITED state. Role and facility scope are governed by backend authority.
              </p>
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
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                First Name <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                placeholder="e.g. Priya"
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                data-testid="invite-firstname-input"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Last Name <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                placeholder="e.g. Sharma"
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                data-testid="invite-lastname-input"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Employee ID <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                value={formData.employee_id}
                onChange={(e) => setFormData({ ...formData, employee_id: e.target.value.toUpperCase() })}
                placeholder="e.g. EMP-9021"
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500 focus:outline-none font-mono uppercase"
                data-testid="invite-employeeid-input"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="priya@nammaclinic.gov.in"
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                data-testid="invite-email-input"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Gender</label>
              <select
                value={formData.gender}
                onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              >
                <option value="FEMALE">Female</option>
                <option value="MALE">Male</option>
                <option value="OTHER">Other</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Date of Birth</label>
              <input
                type="date"
                required
                value={formData.date_of_birth}
                onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Phone Number</label>
              <input
                type="tel"
                value={formData.phone_number}
                onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                placeholder="9876543210"
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Initial Operational Role <span className="text-rose-500">*</span>
              </label>
              <select
                value={formData.role_code}
                onChange={(e) => setFormData({ ...formData, role_code: e.target.value as Role })}
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                data-testid="invite-role-select"
              >
                {roleOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Designation</label>
              <input
                type="text"
                value={formData.designation}
                onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
                placeholder="e.g. Senior Medical Officer"
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Facility Selection */}
          {isDHO ? (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Assigned Clinic / Facility <span className="text-rose-500">*</span>
              </label>
              <select
                value={formData.facility_id}
                onChange={(e) => setFormData({ ...formData, facility_id: Number(e.target.value) })}
                className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                data-testid="invite-facility-select"
              >
                {facilities.map((fac) => (
                  <option key={fac.id} value={fac.id}>
                    {fac.name}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Facility Assignment</label>
              <input
                type="text"
                disabled
                value="Current Authorized Facility"
                className="w-full text-sm border border-slate-200 bg-slate-50 text-slate-500 rounded-lg p-2.5 cursor-not-allowed"
              />
              <p className="text-[11px] text-slate-400 mt-1">
                As Hospital Admin, invitations are automatically bound to your facility.
              </p>
            </div>
          )}

          {/* Registration Number */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Medical Council Reg. No. (Optional)</label>
            <input
              type="text"
              value={formData.medical_council_reg_number}
              onChange={(e) => setFormData({ ...formData, medical_council_reg_number: e.target.value })}
              placeholder="e.g. KMC-102934"
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
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
              disabled={isLoading}
              className="px-4 py-2 text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-sm transition disabled:opacity-50 inline-flex items-center gap-2"
              data-testid="submit-invite-btn"
            >
              {isLoading ? 'Sending Invitation...' : 'Send Invitation'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default InviteStaffModal;