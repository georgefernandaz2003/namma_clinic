import React from 'react';
import type { StaffLifecycleStatus } from '../../types/staff';
import { STATUS_LABELS } from '../../types/staff';

interface StaffStatusBadgeProps {
  status: StaffLifecycleStatus | string;
  size?: 'sm' | 'md';
}

export const StaffStatusBadge: React.FC<StaffStatusBadgeProps> = ({ status, size = 'sm' }) => {
  const normStatus = (status || '').toUpperCase() as StaffLifecycleStatus;
  const label = STATUS_LABELS[normStatus] || status || 'Unknown';

  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-semibold';

  let colorClasses = 'bg-slate-100 text-slate-700 border-slate-200';

  switch (normStatus) {
    case 'ACTIVE':
      colorClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200';
      break;
    case 'INVITED':
      colorClasses = 'bg-amber-50 text-amber-700 border-amber-200';
      break;
    case 'SUSPENDED':
      colorClasses = 'bg-rose-50 text-rose-700 border-rose-200';
      break;
    case 'TRANSFER_PENDING':
      colorClasses = 'bg-blue-50 text-blue-700 border-blue-200';
      break;
    case 'DEACTIVATED':
      colorClasses = 'bg-slate-100 text-slate-500 border-slate-200 line-through';
      break;
    default:
      colorClasses = 'bg-slate-100 text-slate-700 border-slate-200';
  }

  return (
    <span
      className={`inline-flex items-center gap-1 font-medium rounded-full border ${sizeClasses} ${colorClasses}`}
      data-testid={`status-badge-${(status || '').toLowerCase()}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-70" />
      {label}
    </span>
  );
};

export default StaffStatusBadge;