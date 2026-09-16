import { Role } from '../types';

export const ROLE_PERMISSIONS: Record<Role, Set<string>> = {
  DISTRICT_OFFICER: new Set([
    'district.view', 'hospital.view', 'clinic.view', 'reports.view', 'reports.export',
    'audit_logs.view', 'dashboard.view'
  ]),
  HOSPITAL_ADMIN: new Set([
    'hospital.view', 'clinic.view', 'staff.view', 'staff.create', 'staff.update',
    'patients.view', 'patients.create', 'appointments.view', 'appointments.create', 'appointments.update',
    'inventory.view', 'inventory.create', 'inventory.update', 'reports.view', 'reports.export',
    'system_config.view', 'system_config.update', 'dashboard.view'
  ]),
  DOCTOR: new Set([
    'patients.view', 'appointments.view', 'consultation.view', 'consultation.create', 'consultation.update',
    'diagnosis.view', 'diagnosis.create', 'diagnosis.update', 'prescription.view', 'prescription.create', 'prescription.update',
    'lab_orders.view', 'lab_orders.create', 'lab_results.view', 'referrals.view', 'referrals.create',
    'clinic.view', 'queue.view', 'dashboard.view'
  ]),
  NURSE: new Set([
    'patients.view', 'patients.create', 'patients.update', 'appointments.view', 'appointments.create',
    'vitals.view', 'vitals.create', 'triage.view', 'triage.create', 'queue.view', 'queue.update',
    'clinic.view', 'dashboard.view'
  ]),
  LAB_TECHNICIAN: new Set([
    'patients.view', 'lab_orders.view', 'lab_results.view', 'lab_results.create', 'lab_results.update',
    'clinic.view', 'dashboard.view'
  ]),
  PHARMACIST: new Set([
    'prescription.view', 'pharmacy.view', 'pharmacy.dispense', 'inventory.view', 'inventory.create', 'inventory.update',
    'clinic.view', 'dashboard.view'
  ])
};

export const ROLE_ALLOWED_PATHS: Record<Role, string[]> = {
  DISTRICT_OFFICER: [
    '/', '/network', '/facilities', '/reports', '/alerts', '/compliance', '/audit'
  ],
  HOSPITAL_ADMIN: [
    '/', '/network', '/facilities', '/patients', '/queue', '/pharmacy', '/referrals', '/followups', '/infrastructure', '/reports'
  ],
  DOCTOR: [
    '/', '/queue', '/patients', '/consultation', '/lab', '/referrals', '/followups', '/teleconsultation'
  ],
  NURSE: [
    '/', '/patients', '/queue', '/triage', '/followups', '/ncd', '/maternal-child', '/outreach', '/wellness'
  ],
  LAB_TECHNICIAN: [
    '/', '/lab'
  ],
  PHARMACIST: [
    '/', '/pharmacy', '/infrastructure'
  ]
};

export const hasPermission = (role: Role | undefined, permission: string): boolean => {
  if (!role) return false;
  return ROLE_PERMISSIONS[role]?.has(permission) ?? false;
};

export const isPathAllowedForRole = (role: Role | undefined, path: string): boolean => {
  if (!role) return false;
  
  // Base dashboard '/' is accessible to all logged in roles
  if (path === '/' || path === '') return true;
  
  const allowed = ROLE_ALLOWED_PATHS[role];
  if (!allowed) return false;
  
  return allowed.some(allowedPath => {
    if (allowedPath === '/') return path === '/';
    return path.startsWith(allowedPath);
  });
};
