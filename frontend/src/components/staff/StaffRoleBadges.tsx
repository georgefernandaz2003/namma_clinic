import React from 'react';
import type { StaffRoleItem } from '../../types/staff';
import type { Role } from '../../types/auth';
import { ROLE_LABELS } from '../../types/auth';

interface StaffRoleBadgesProps {
  roles?: StaffRoleItem[] | string[];
  maxDisplay?: number;
}

export const StaffRoleBadges: React.FC<StaffRoleBadgesProps> = ({ roles = [], maxDisplay = 3 }) => {
  if (!roles || roles.length === 0) {
    return <span className="text-xs text-slate-400 italic">No roles assigned</span>;
  }

  // Normalize role items whether they are strings or StaffRoleItem objects
  const roleList: { role: string; roleName: string; isActive: boolean }[] = roles.map((r) => {
    if (typeof r === 'string') {
      return { role: r, roleName: r, isActive: true };
    }
    return {
      role: r.role_code,
      roleName: r.role_name || r.role_code,
      isActive: r.is_active !== false && !r.effective_to,
    };
  });

  const displayRoles = roleList.slice(0, maxDisplay);
  const remaining = roleList.length - maxDisplay;

  const getRoleBadgeColor = (roleStr: string) => {
    switch (roleStr) {
      case 'DOCTOR':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'NURSE':
        return 'bg-teal-50 text-teal-700 border-teal-200';
      case 'FRONT_DESK_OFFICER':
      case 'COMPOUNDER':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'LAB_TECHNICIAN':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'PHARMACIST':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'HOSPITAL_ADMIN':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      case 'DISTRICT_OFFICER':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-1.5" data-testid="staff-role-badges">
      {displayRoles.map((item, idx) => {
        const label = ROLE_LABELS[item.role as Role] || item.roleName || item.role;
        const colorClasses = getRoleBadgeColor(item.role);
        return (
          <span
            key={`${item.role}-${idx}`}
            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${colorClasses} ${
              !item.isActive ? 'opacity-50 line-through' : ''
            }`}
            data-testid={`role-badge-${item.role.toLowerCase()}`}
          >
            {label}
          </span>
        );
      })}
      {remaining > 0 && (
        <span className="text-xs text-slate-500 font-medium">+{remaining} more</span>
      )}
    </div>
  );
};

export default StaffRoleBadges;