import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ForbiddenCard } from '../components/common/ForbiddenCard';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { StaffDirectoryTable } from '../components/staff/StaffDirectoryTable';
import { StaffDetailModal } from '../components/staff/StaffDetailModal';
import { InviteStaffModal } from '../components/staff/InviteStaffModal';
import { AssignRoleModal } from '../components/staff/AssignRoleModal';
import { TransferStaffModal } from '../components/staff/TransferStaffModal';
import { CreateFacilityModal } from '../components/staff/CreateFacilityModal';
import {
  fetchStaffProfiles,
  fetchStaffProfileDetail,
  inviteStaff,
  activateStaff,
  suspendStaff,
  deactivateStaff,
  assignStaffRole,
  endStaffRole,
  transferStaff,
  createClinicFacility,
} from '../api/staff';
import apiClient from '../api/client';
import type {
  StaffProfile,
  InviteStaffPayload,
  AssignRolePayload,
  TransferStaffPayload,
  CreateFacilityPayload,
} from '../types/staff';
import type { Role } from '../types/auth';
import { Users, Shield, Building2 } from 'lucide-react';

export const StaffAdministration: React.FC = () => {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const facilityParam = searchParams.get('facilityId');
  const appointAdminParam = searchParams.get('appointAdmin') === 'true';
  const currentRole = user?.role as Role | undefined;

  // Authorization check: Only DISTRICT_OFFICER and HOSPITAL_ADMIN may access this console
  const isAuthorized = currentRole === 'DISTRICT_OFFICER' || currentRole === 'HOSPITAL_ADMIN';
  const isDHO = currentRole === 'DISTRICT_OFFICER';

  // Data states
  const [staffList, setStaffList] = useState<StaffProfile[]>([]);
  const [facilities, setFacilities] = useState<{ id: number; name: string }[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [facilityFilter, setFacilityFilter] = useState<string>('');

  // Modals
  const [selectedStaff, setSelectedStaff] = useState<StaffProfile | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState<boolean>(false);
  const [isInviteOpen, setIsInviteOpen] = useState<boolean>(false);
  const [assignRoleTarget, setAssignRoleTarget] = useState<StaffProfile | null>(null);
  const [transferTarget, setTransferTarget] = useState<StaffProfile | null>(null);
  const [isCreateFacilityOpen, setIsCreateFacilityOpen] = useState<boolean>(false);

  // Extract friendly error message
  const parseApiError = (err: any): string => {
    if (err?.status === 403 || err?.response?.status === 403) {
      return 'You are not authorized to perform this action.';
    }
    if (err?.status === 409 || err?.response?.status === 409) {
      const data = err?.data || err?.response?.data;
      if (typeof data === 'string') return data;
      if (data?.detail) return data.detail;
      if (data?.error) return data.error;
      return 'Conflict: Operation violates current business or role assignment rules.';
    }
    const data = err?.data || err?.response?.data;
    if (data?.detail) return data.detail;
    if (data?.error) return data.error;
    if (typeof data === 'object') {
      const firstKey = Object.keys(data)[0];
      if (firstKey) {
        const val = data[firstKey];
        return `${firstKey}: ${Array.isArray(val) ? val.join(', ') : val}`;
      }
    }
    return err?.message || 'An unexpected error occurred while communicating with the server.';
  };

  // Load facilities for facility dropdown / transfer / creation
  const loadFacilities = useCallback(async () => {
    try {
      const resp = await apiClient.get<any>('v1/organization/facilities/');
      const results = resp.data?.results || resp.data || [];
      const list = results.map((f: any) => ({
        id: Number(f.id),
        name: f.facility_name || f.name || f.facility_code || 'Facility',
      }));
      setFacilities(list);
    } catch {
      // Non-fatal if facilities list fails; facility assignments will rely on backend defaults
    }
  }, []);

  // Fetch staff list from backend (authoritative)
  const loadStaffList = useCallback(async () => {
    if (!isAuthorized) return;
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const profiles = await fetchStaffProfiles({
        search: searchQuery || undefined,
        role: roleFilter || undefined,
        status: statusFilter || undefined,
        facility: facilityFilter || undefined,
      });
      setStaffList(profiles);
    } catch (err: any) {
      setErrorMessage(parseApiError(err));
    } finally {
      setIsLoading(false);
    }
  }, [isAuthorized, searchQuery, roleFilter, statusFilter, facilityFilter]);

  // Initial load & search param context handling
  useEffect(() => {
    if (facilityParam) {
      setFacilityFilter(facilityParam);
    }
    if (appointAdminParam) {
      setIsInviteOpen(true);
    }
  }, [facilityParam, appointAdminParam]);

  useEffect(() => {
    if (isAuthorized) {
      loadFacilities();
      loadStaffList();
    }
  }, [isAuthorized, loadFacilities, loadStaffList]);

  // Refresh single staff detail
  const refreshSelectedStaff = async (id: number) => {
    try {
      const refreshed = await fetchStaffProfileDetail(id);
      setSelectedStaff(refreshed);
      // Also update in list
      setStaffList((prev) => prev.map((s) => (s.id === id ? refreshed : s)));
    } catch (err: any) {
      setErrorMessage(parseApiError(err));
    }
  };

  // Handlers
  const handleInvite = async (payload: InviteStaffPayload) => {
    setActionLoading(true);
    setErrorMessage(null);
    try {
      await inviteStaff(payload);
      setSuccessMessage(`Invitation successfully sent for ${payload.first_name} ${payload.last_name} (${payload.employee_id}). Staff account created in INVITED status.`);
      await loadStaffList();
    } catch (err: any) {
      throw new Error(parseApiError(err));
    } finally {
      setActionLoading(false);
    }
  };

  const handleActivate = async (id: number) => {
    setActionLoading(true);
    setErrorMessage(null);
    try {
      await activateStaff(id);
      setSuccessMessage('Staff account successfully activated.');
      await refreshSelectedStaff(id);
      await loadStaffList();
    } catch (err: any) {
      throw new Error(parseApiError(err));
    } finally {
      setActionLoading(false);
    }
  };

  const handleSuspend = async (id: number, reason?: string) => {
    setActionLoading(true);
    setErrorMessage(null);
    try {
      await suspendStaff(id, reason);
      setSuccessMessage('Staff account suspended.');
      await refreshSelectedStaff(id);
      await loadStaffList();
    } catch (err: any) {
      throw new Error(parseApiError(err));
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeactivate = async (id: number, reason?: string) => {
    setActionLoading(true);
    setErrorMessage(null);
    try {
      await deactivateStaff(id, reason);
      setSuccessMessage('Staff account deactivated and moved to historical status.');
      await refreshSelectedStaff(id);
      await loadStaffList();
    } catch (err: any) {
      throw new Error(parseApiError(err));
    } finally {
      setActionLoading(false);
    }
  };

  const handleAssignRole = async (payload: AssignRolePayload) => {
    if (!assignRoleTarget) return;
    setActionLoading(true);
    setErrorMessage(null);
    try {
      await assignStaffRole(assignRoleTarget.id, payload);
      setSuccessMessage(`Operational role ${payload.role_code} successfully assigned.`);
      await refreshSelectedStaff(assignRoleTarget.id);
      await loadStaffList();
      setAssignRoleTarget(null);
    } catch (err: any) {
      throw new Error(parseApiError(err));
    } finally {
      setActionLoading(false);
    }
  };

  const handleEndRole = async (assignmentId: number) => {
    setActionLoading(true);
    setErrorMessage(null);
    try {
      await endStaffRole(assignmentId);
      setSuccessMessage('Role assignment ended.');
      if (selectedStaff) {
        await refreshSelectedStaff(selectedStaff.id);
      }
      await loadStaffList();
    } catch (err: any) {
      throw new Error(parseApiError(err));
    } finally {
      setActionLoading(false);
    }
  };

  const handleTransfer = async (payload: TransferStaffPayload) => {
    if (!transferTarget) return;
    setActionLoading(true);
    setErrorMessage(null);
    try {
      const result = await transferStaff(transferTarget.id, payload);
      setSuccessMessage(
        `Staff facility transfer recorded. Effective date: ${payload.effective_date || 'immediate'}.`
      );
      await refreshSelectedStaff(transferTarget.id);
      await loadStaffList();
      setTransferTarget(null);
    } catch (err: any) {
      throw new Error(parseApiError(err));
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateFacility = async (payload: CreateFacilityPayload) => {
    setActionLoading(true);
    setErrorMessage(null);
    try {
      const newFacility = await createClinicFacility(payload);
      setSuccessMessage(`Clinic Facility "${newFacility.facility_name}" registered successfully.`);
      await loadFacilities();
      setIsCreateFacilityOpen(false);
    } catch (err: any) {
      throw new Error(parseApiError(err));
    } finally {
      setActionLoading(false);
    }
  };

  // If role is operational (e.g. DOCTOR, NURSE, FRONT_DESK_OFFICER, LAB_TECHNICIAN, PHARMACIST)
  if (!isAuthorized) {
    return (
      <div className="p-6">
        <ForbiddenCard
          role={currentRole}
          roleDisplay={currentRole}
          requestedPath="/admin/staff"
        />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-200/80">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900">Staff & Clinic Administration</h1>
            <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
              {isDHO ? 'District Oversight' : 'Facility Administration'}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Authoritative directory, lifecycle management, role assignments, and facility postings.
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs text-slate-600 bg-white px-3 py-2 rounded-xl border border-slate-200/80 shadow-xs">
          {isDHO ? (
            <div className="flex items-center gap-1.5 font-medium">
              <Shield className="w-4 h-4 text-emerald-600" />
              <span>District Health Office Scope</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 font-medium">
              <Building2 className="w-4 h-4 text-indigo-600" />
              <span>Facility Operational Scope</span>
            </div>
          )}
        </div>
      </div>

      {/* Notifications */}
      {errorMessage && (
        <ErrorAlert
          message={errorMessage}
          onDismiss={() => setErrorMessage(null)}
        />
      )}

      {successMessage && (
        <div
          role="alert"
          className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 font-medium flex items-center justify-between shadow-xs"
        >
          <span>{successMessage}</span>
          <button
            type="button"
            onClick={() => setSuccessMessage(null)}
            className="text-emerald-600 hover:text-emerald-900 font-bold ml-4"
          >
            ✕
          </button>
        </div>
      )}

      {/* Staff Directory Table with Filtering & Actions */}
      <StaffDirectoryTable
        staffList={staffList}
        isLoading={isLoading}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        roleFilter={roleFilter}
        onRoleFilterChange={setRoleFilter}
        statusFilter={statusFilter}
        onStatusFilterChange={setStatusFilter}
        facilityFilter={facilityFilter}
        onFacilityFilterChange={setFacilityFilter}
        facilities={facilities}
        isDHO={isDHO}
        onSelectStaff={(staff) => {
          setSelectedStaff(staff);
          setIsDetailOpen(true);
        }}
        onOpenInvite={() => setIsInviteOpen(true)}
        onOpenCreateFacility={isDHO ? () => setIsCreateFacilityOpen(true) : undefined}
      />

      {/* Staff Detail Modal */}
      {isDetailOpen && selectedStaff && (
        <StaffDetailModal
          isOpen={isDetailOpen}
          staff={selectedStaff}
          userRole={currentRole}
          isLoading={actionLoading}
          onActivate={handleActivate}
          onSuspend={handleSuspend}
          onDeactivate={handleDeactivate}
          onEndRole={handleEndRole}
          onOpenAssignRole={(s) => setAssignRoleTarget(s)}
          onOpenTransfer={(s) => setTransferTarget(s)}
          onClose={() => {
            setIsDetailOpen(false);
            setSelectedStaff(null);
          }}
        />
      )}

      {/* Invite Staff Modal */}
      <InviteStaffModal
        isOpen={isInviteOpen}
        userRole={currentRole}
        userFacilityId={user?.assigned_facility}
        initialFacilityId={facilityParam ? Number(facilityParam) : null}
        initialRoleCode={appointAdminParam ? 'HOSPITAL_ADMIN' : null}
        facilities={facilities}
        isLoading={actionLoading}
        onInvite={handleInvite}
        onClose={() => {
          setIsInviteOpen(false);
          if (appointAdminParam) {
            setSearchParams({});
          }
        }}
      />

      {/* Assign Role Modal */}
      {assignRoleTarget && (
        <AssignRoleModal
          isOpen={Boolean(assignRoleTarget)}
          staffName={
            `${assignRoleTarget.person_details?.first_name || ''} ${assignRoleTarget.person_details?.last_name || ''}`.trim() ||
            assignRoleTarget.employee_id
          }
          userRole={currentRole}
          userFacilityId={user?.assigned_facility}
          facilities={facilities}
          isLoading={actionLoading}
          onAssign={handleAssignRole}
          onClose={() => setAssignRoleTarget(null)}
        />
      )}

      {/* Transfer Staff Modal */}
      {transferTarget && (
        <TransferStaffModal
          isOpen={Boolean(transferTarget)}
          staff={transferTarget}
          facilities={facilities}
          isLoading={actionLoading}
          onTransfer={handleTransfer}
          onClose={() => setTransferTarget(null)}
        />
      )}

      {/* Create Facility Modal (DHO only) */}
      {isDHO && (
        <CreateFacilityModal
          isOpen={isCreateFacilityOpen}
          districtId={user?.assigned_district}
          isLoading={actionLoading}
          onCreate={handleCreateFacility}
          onClose={() => setIsCreateFacilityOpen(false)}
        />
      )}
    </div>
  );
};

export default StaffAdministration;