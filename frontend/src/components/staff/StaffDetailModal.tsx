import React, { useState } from 'react';
import {
  X,
  User,
  Building,
  Calendar,
  CheckCircle,
  PauseCircle,
  Ban,
  ArrowRightLeft,
  PlusCircle,
  Clock,
  Trash2,
} from 'lucide-react';
import type { StaffProfile, StaffRoleItem } from '../../types/staff';
import type { Role } from '../../types/auth';
import { StaffStatusBadge } from './StaffStatusBadge';
import { ROLE_LABELS } from '../../types/auth';
import { ConfirmActionModal } from './ConfirmActionModal';

interface StaffDetailModalProps {
  isOpen: boolean;
  staff: StaffProfile | null;
  userRole?: Role;
  isLoading?: boolean;
  onActivate: (id: number) => Promise<void>;
  onSuspend: (id: number, reason?: string) => Promise<void>;
  onDeactivate: (id: number, reason?: string) => Promise<void>;
  onEndRole: (assignmentId: number) => Promise<void>;
  onOpenAssignRole: (staff: StaffProfile) => void;
  onOpenTransfer: (staff: StaffProfile) => void;
  onClose: () => void;
}

export const StaffDetailModal: React.FC<StaffDetailModalProps> = ({
  isOpen,
  staff,
  userRole,
  isLoading = false,
  onActivate,
  onSuspend,
  onDeactivate,
  onEndRole,
  onOpenAssignRole,
  onOpenTransfer,
  onClose,
}) => {
  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    confirmLabel: string;
    variant: 'danger' | 'warning' | 'primary';
    requireReason: boolean;
    action: (reason?: string) => Promise<void>;
  }>({
    isOpen: false,
    title: '',
    message: '',
    confirmLabel: '',
    variant: 'danger',
    requireReason: false,
    action: async () => {},
  });

  if (!isOpen || !staff) return null;

  const status = staff.status || 'ACTIVE';
  const isDeactivated = status === 'DEACTIVATED';
  const isSuspended = status === 'SUSPENDED';
  const isInvited = status === 'INVITED';
  const isTransferPending = status === 'TRANSFER_PENDING';
  const isActive = status === 'ACTIVE';

  const staffDisplayName = `${staff.person_details?.first_name || ''} ${staff.person_details?.last_name || ''}`.trim() || staff.employee_id;
  const activeRoles: StaffRoleItem[] = staff.roles || [];

  const handleActivateClick = () => {
    setConfirmModal({
      isOpen: true,
      title: 'Activate Staff Member',
      message: `Are you sure you want to activate ${staffDisplayName}? This will transition their lifecycle from INVITED to ACTIVE.`,
      confirmLabel: 'Activate Staff',
      variant: 'primary',
      requireReason: false,
      action: async () => {
        await onActivate(staff.id);
        setConfirmModal((prev) => ({ ...prev, isOpen: false }));
      },
    });
  };

  const handleSuspendClick = () => {
    setConfirmModal({
      isOpen: true,
      title: 'Suspend Staff Account',
      message: `Suspending ${staffDisplayName} will temporarily revoke facility access and system authentication.`,
      confirmLabel: 'Suspend Account',
      variant: 'warning',
      requireReason: true,
      action: async (reason) => {
        await onSuspend(staff.id, reason);
        setConfirmModal((prev) => ({ ...prev, isOpen: false }));
      },
    });
  };

  const handleDeactivateClick = () => {
    setConfirmModal({
      isOpen: true,
      title: 'Deactivate Staff Account',
      message: `Deactivating ${staffDisplayName} will permanently transition this staff member to a read-only historical state.`,
      confirmLabel: 'Deactivate Staff',
      variant: 'danger',
      requireReason: true,
      action: async (reason) => {
        await onDeactivate(staff.id, reason);
        setConfirmModal((prev) => ({ ...prev, isOpen: false }));
      },
    });
  };

  const handleEndRoleClick = (roleItem: StaffRoleItem) => {
    if (!roleItem.id) return;
    const roleName = ROLE_LABELS[roleItem.role_code as Role] || roleItem.role_name || roleItem.role_code;
    setConfirmModal({
      isOpen: true,
      title: `End ${roleName} Assignment`,
      message: `Are you sure you want to end the ${roleName} role for ${staffDisplayName}? Other assigned operational roles will remain intact.`,
      confirmLabel: 'End Assignment',
      variant: 'danger',
      requireReason: false,
      action: async () => {
        await onEndRole(roleItem.id);
        setConfirmModal((prev) => ({ ...prev, isOpen: false }));
      },
    });
  };

  return (
    <>
      <div
        className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="staff-detail-title"
      >
        <div className="relative bg-white rounded-2xl max-w-2xl w-full p-6 shadow-xl border border-slate-100 max-h-[92vh] overflow-y-auto">
          {/* Header */}
          <div className="flex items-start justify-between pb-4 border-b border-slate-100">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-slate-100 text-slate-600 flex items-center justify-center font-bold text-lg">
                <User className="w-6 h-6" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 id="staff-detail-title" className="text-xl font-bold text-slate-900">
                    {staffDisplayName}
                  </h2>
                  <StaffStatusBadge status={status} size="md" />
                </div>
                <p className="text-xs text-slate-500 font-mono">
                  Employee ID: {staff.employee_id} • Designation: {staff.designation}
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

          {/* Transfer Pending Notice */}
          {isTransferPending && (
            <div className="my-4 p-3 bg-blue-50 border border-blue-200 rounded-xl text-xs text-blue-900 flex items-start gap-2.5">
              <Clock className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">Transfer Pending:</span> Staff has an approved future facility transfer. Current facility operational access remains active until the effective transfer date. Dual facility access is strictly disallowed.
              </div>
            </div>
          )}

          {/* Deactivated Notice */}
          {isDeactivated && (
            <div className="my-4 p-3 bg-slate-100 border border-slate-200 rounded-xl text-xs text-slate-600 flex items-start gap-2.5">
              <Ban className="w-4 h-4 text-slate-500 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">Historical Record:</span> This staff account has been permanently deactivated. No active clinical access or further role assignments are permitted.
              </div>
            </div>
          )}

          <div className="py-4 space-y-6">
            {/* Identity & Account Grid */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Identity Details</h4>
                <div className="space-y-1.5 text-xs">
                  <div>
                    <span className="text-slate-500">Gender:</span>{' '}
                    <span className="font-semibold text-slate-800">{staff.person_details?.gender || '—'}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Date of Birth:</span>{' '}
                    <span className="font-semibold text-slate-800">{staff.person_details?.date_of_birth || '—'}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Phone:</span>{' '}
                    <span className="font-semibold text-slate-800">{staff.person_details?.phone_number || '—'}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Registration No.:</span>{' '}
                    <span className="font-semibold text-slate-800 font-mono">
                      {staff.medical_council_reg_number || '—'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Facility Context</h4>
                <div className="space-y-1.5 text-xs">
                  <div>
                    <span className="text-slate-500">Facility:</span>{' '}
                    <span className="font-semibold text-slate-800">
                      {staff.facility_assignment?.facility_name || 'Unassigned'}
                    </span>
                  </div>
                  {staff.district_context && (
                    <div>
                      <span className="text-slate-500">District:</span>{' '}
                      <span className="font-semibold text-slate-800">{staff.district_context.district_name}</span>
                    </div>
                  )}
                  <div>
                    <span className="text-slate-500">Primary Assignment:</span>{' '}
                    <span className="font-semibold text-slate-800">
                      {staff.facility_assignment?.is_primary ? 'Yes' : 'No'}
                    </span>
                  </div>
                  {staff.facility_assignment?.effective_from && (
                    <div>
                      <span className="text-slate-500">Effective From:</span>{' '}
                      <span className="font-semibold text-slate-800">{staff.facility_assignment.effective_from}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Active Roles & Role Ending */}
            <div className="pt-4 border-t border-slate-100">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Role Assignments ({activeRoles.length})
                  </h4>
                  <p className="text-[11px] text-slate-500">
                    Active operational roles held by this staff member. Each role is governed separately.
                  </p>
                </div>
                {!isDeactivated && (
                  <button
                    type="button"
                    onClick={() => onOpenAssignRole(staff)}
                    disabled={isLoading}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 hover:text-indigo-700 bg-indigo-50 hover:bg-indigo-100 px-2.5 py-1.5 rounded-lg transition"
                    data-testid="assign-new-role-btn"
                  >
                    <PlusCircle className="w-3.5 h-3.5" />
                    Assign Role
                  </button>
                )}
              </div>

              {activeRoles.length === 0 ? (
                <div className="text-xs text-slate-400 italic p-3 bg-slate-50 rounded-lg border border-slate-100">
                  No active roles assigned. Click "Assign Role" to allocate an operational responsibility.
                </div>
              ) : (
                <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden">
                  {activeRoles.map((assignment, idx) => {
                    const roleLabel = ROLE_LABELS[assignment.role_code as Role] || assignment.role_name || assignment.role_code;
                    return (
                      <div
                        key={assignment.id || `${assignment.role_code}-${idx}`}
                        className="p-3 bg-white flex items-center justify-between hover:bg-slate-50/50 transition"
                        data-testid={`role-assignment-row-${assignment.role_code.toLowerCase()}`}
                      >
                        <div className="space-y-0.5">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-sm text-slate-800">{roleLabel}</span>
                            <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                              Active
                            </span>
                          </div>
                          <div className="flex items-center gap-3 text-xs text-slate-500">
                            {assignment.facility_name && (
                              <span className="inline-flex items-center gap-1">
                                <Building className="w-3 h-3" />
                                {assignment.facility_name}
                              </span>
                            )}
                            {assignment.effective_from && (
                              <span className="inline-flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                From: {assignment.effective_from}
                              </span>
                            )}
                            {assignment.effective_to && (
                              <span>To: {assignment.effective_to}</span>
                            )}
                          </div>
                        </div>

                        {!isDeactivated && assignment.id && (
                          <button
                            type="button"
                            onClick={() => handleEndRoleClick(assignment)}
                            disabled={isLoading}
                            className="inline-flex items-center gap-1 text-xs font-semibold text-rose-600 hover:text-rose-700 hover:bg-rose-50 px-2 py-1 rounded transition"
                            title={`End ${roleLabel} assignment`}
                            data-testid={`end-role-btn-${assignment.role_code.toLowerCase()}`}
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                            End Role
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Lifecycle Actions */}
            {!isDeactivated && (
              <div className="pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Lifecycle Actions
                </span>

                <div className="flex flex-wrap items-center gap-2">
                  {isInvited && (
                    <button
                      type="button"
                      onClick={handleActivateClick}
                      disabled={isLoading}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg shadow-sm transition"
                      data-testid="activate-staff-btn"
                    >
                      <CheckCircle className="w-3.5 h-3.5" />
                      Activate Staff
                    </button>
                  )}

                  {(isActive || isTransferPending) && (
                    <>
                      <button
                        type="button"
                        onClick={() => onOpenTransfer(staff)}
                        disabled={isLoading}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-semibold rounded-lg transition"
                        data-testid="transfer-staff-btn"
                      >
                        <ArrowRightLeft className="w-3.5 h-3.5" />
                        Transfer Facility
                      </button>

                      <button
                        type="button"
                        onClick={handleSuspendClick}
                        disabled={isLoading}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-50 hover:bg-amber-100 text-amber-700 text-xs font-semibold rounded-lg transition"
                        data-testid="suspend-staff-btn"
                      >
                        <PauseCircle className="w-3.5 h-3.5" />
                        Suspend
                      </button>
                    </>
                  )}

                  {!isDeactivated && (
                    <button
                      type="button"
                      onClick={handleDeactivateClick}
                      disabled={isLoading}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-semibold rounded-lg transition"
                      data-testid="deactivate-staff-btn"
                    >
                      <Ban className="w-3.5 h-3.5" />
                      Deactivate
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center justify-end pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
            >
              Close
            </button>
          </div>
        </div>
      </div>

      <ConfirmActionModal
        isOpen={confirmModal.isOpen}
        title={confirmModal.title}
        message={confirmModal.message}
        confirmLabel={confirmModal.confirmLabel}
        confirmVariant={confirmModal.variant}
        requireReason={confirmModal.requireReason}
        isLoading={isLoading}
        onConfirm={confirmModal.action}
        onCancel={() => setConfirmModal((prev) => ({ ...prev, isOpen: false }))}
      />
    </>
  );
};

export default StaffDetailModal;