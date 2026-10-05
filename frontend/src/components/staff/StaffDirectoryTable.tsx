import React from 'react';
import { Search, Eye, UserCheck } from 'lucide-react';
import type { StaffProfile } from '../../types/staff';
import { StaffStatusBadge } from './StaffStatusBadge';
import { StaffRoleBadges } from './StaffRoleBadges';
import { EmptyState } from '../common/EmptyState';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface FacilityOption {
  id: number;
  name: string;
}

interface StaffDirectoryTableProps {
  staffList: StaffProfile[];
  isLoading: boolean;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  roleFilter: string;
  onRoleFilterChange: (role: string) => void;
  statusFilter: string;
  onStatusFilterChange: (status: string) => void;
  facilityFilter?: string;
  onFacilityFilterChange?: (facilityId: string) => void;
  facilities?: FacilityOption[];
  isDHO?: boolean;
  onSelectStaff: (staff: StaffProfile) => void;
  onOpenInvite: () => void;
  onOpenCreateFacility?: () => void;
}

export const StaffDirectoryTable: React.FC<StaffDirectoryTableProps> = ({
  staffList,
  isLoading,
  searchQuery,
  onSearchChange,
  roleFilter,
  onRoleFilterChange,
  statusFilter,
  onStatusFilterChange,
  facilityFilter = '',
  onFacilityFilterChange,
  facilities = [],
  isDHO = false,
  onSelectStaff,
  onOpenInvite,
  onOpenCreateFacility,
}) => {
  return (
    <div className="space-y-4">
      {/* Top Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Search Input */}
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search staff by name, employee ID..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-emerald-500 focus:outline-none transition"
            data-testid="staff-search-input"
          />
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-2.5 w-full md:w-auto">
          {/* Role Filter */}
          <select
            value={roleFilter}
            onChange={(e) => onRoleFilterChange(e.target.value)}
            className="px-3 py-2 text-xs font-medium bg-slate-50 border border-slate-200 rounded-xl text-slate-700 focus:bg-white focus:ring-2 focus:ring-emerald-500 focus:outline-none transition cursor-pointer"
            data-testid="staff-role-filter"
          >
            <option value="">All Operational Roles</option>
            <option value="DOCTOR">Doctor</option>
            <option value="NURSE">Nurse</option>
            <option value="FRONT_DESK_OFFICER">Front Desk Officer</option>
            <option value="LAB_TECHNICIAN">Lab Technician</option>
            <option value="PHARMACIST">Pharmacist</option>
            <option value="HOSPITAL_ADMIN">Hospital Admin</option>
            {isDHO && <option value="DISTRICT_OFFICER">District Officer</option>}
          </select>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => onStatusFilterChange(e.target.value)}
            className="px-3 py-2 text-xs font-medium bg-slate-50 border border-slate-200 rounded-xl text-slate-700 focus:bg-white focus:ring-2 focus:ring-emerald-500 focus:outline-none transition cursor-pointer"
            data-testid="staff-status-filter"
          >
            <option value="">All Lifecycle Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="INVITED">Invited</option>
            <option value="SUSPENDED">Suspended</option>
            <option value="TRANSFER_PENDING">Transfer Pending</option>
            <option value="DEACTIVATED">Deactivated</option>
          </select>

          {/* Facility Filter (for DHO oversight) */}
          {isDHO && onFacilityFilterChange && (
            <select
              value={facilityFilter}
              onChange={(e) => onFacilityFilterChange(e.target.value)}
              className="px-3 py-2 text-xs font-medium bg-slate-50 border border-slate-200 rounded-xl text-slate-700 focus:bg-white focus:ring-2 focus:ring-emerald-500 focus:outline-none transition cursor-pointer max-w-[200px] truncate"
              data-testid="staff-facility-filter"
            >
              <option value="">All District Facilities</option>
              {facilities.map((fac) => (
                <option key={fac.id} value={String(fac.id)}>
                  {fac.name}
                </option>
              ))}
            </select>
          )}

          {/* Action Buttons */}
          {isDHO && onOpenCreateFacility && (
            <button
              type="button"
              onClick={onOpenCreateFacility}
              className="px-3 py-2 text-xs font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 rounded-xl border border-indigo-200 transition cursor-pointer"
              data-testid="open-create-facility-btn"
            >
              + New Clinic Facility
            </button>
          )}

          <button
            type="button"
            onClick={onOpenInvite}
            className="px-3.5 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-sm transition inline-flex items-center gap-1.5 cursor-pointer"
            data-testid="open-invite-staff-btn"
          >
            <UserCheck className="w-4 h-4" />
            Invite Staff
          </button>
        </div>
      </div>

      {/* Main Table / State */}
      {isLoading ? (
        <div className="bg-white rounded-2xl border border-slate-200/80 p-12 text-center shadow-sm">
          <LoadingSpinner size="lg" label="Loading authoritative staff directory from backend..." />
        </div>
      ) : staffList.length === 0 ? (
        <EmptyState
          title="No Staff Records Found"
          description="No staff profiles match the selected filter criteria, or no staff accounts have been provisioned in your authorized scope."
          actionText="Invite New Staff"
          onAction={onOpenInvite}
        />
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse" data-testid="staff-directory-table">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50/75 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Staff Member</th>
                  <th className="py-3 px-4">Operational Roles</th>
                  <th className="py-3 px-4">Lifecycle Status</th>
                  <th className="py-3 px-4">Assigned Facility</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {staffList.map((staff) => {
                  const staffDisplayName = `${staff.person_details?.first_name || ''} ${staff.person_details?.last_name || ''}`.trim() || staff.employee_id;
                  return (
                    <tr
                      key={staff.id}
                      className="hover:bg-slate-50/70 transition cursor-pointer"
                      onClick={() => onSelectStaff(staff)}
                      data-testid={`staff-row-${staff.employee_id.toLowerCase()}`}
                    >
                      {/* Name & Employee ID */}
                      <td className="py-3.5 px-4">
                        <div>
                          <div className="font-bold text-slate-900">
                            {staffDisplayName}
                          </div>
                          <div className="text-[11px] text-slate-400 font-mono">
                            {staff.employee_id} • {staff.designation}
                          </div>
                        </div>
                      </td>

                      {/* Roles Badges */}
                      <td className="py-3.5 px-4">
                        <StaffRoleBadges roles={staff.roles} />
                      </td>

                      {/* Status Badge */}
                      <td className="py-3.5 px-4">
                        <StaffStatusBadge status={staff.status} />
                      </td>

                      {/* Facility */}
                      <td className="py-3.5 px-4">
                        <div className="text-slate-700 font-medium">
                          {staff.facility_assignment?.facility_name || (
                            <span className="text-slate-400 italic">Unassigned</span>
                          )}
                        </div>
                        {staff.district_context?.district_name && (
                          <div className="text-[10px] text-slate-400">
                            {staff.district_context.district_name}
                          </div>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="py-3.5 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                        <button
                          type="button"
                          onClick={() => onSelectStaff(staff)}
                          className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
                          data-testid={`view-staff-btn-${staff.employee_id.toLowerCase()}`}
                        >
                          <Eye className="w-3.5 h-3.5 text-slate-500" />
                          Manage
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="py-3 px-4 bg-slate-50/50 border-t border-slate-100 text-[11px] text-slate-500 flex items-center justify-between">
            <span>Showing {staffList.length} staff records</span>
            <span className="italic">Data source: Authoritative PostgreSQL backend</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default StaffDirectoryTable;