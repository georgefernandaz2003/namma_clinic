import type { Role } from '../types';

export const ROLE_PERMISSIONS: Record<Role, Set<string>> = {
  DISTRICT_OFFICER: new Set([
    'district.view', 'hospital.view', 'clinic.view', 'reports.view', 'reports.export',
    'audit_logs.view', 'dashboard.view', 'medicine_master.view'
  ]),
  HOSPITAL_ADMIN: new Set([
    'hospital.view', 'clinic.view', 'staff.view', 'staff.create', 'staff.update',
    'patients.view', 'patients.create', 'appointments.view', 'appointments.create', 'appointments.update',
    'inventory.view', 'inventory.create', 'inventory.update', 'reports.view', 'reports.export',
    'system_config.view', 'system_config.update', 'dashboard.view', 'demo.reset',
    'medicine_master.view', 'medicine_master.create', 'medicine_master.update', 'medicine_master.delete'
  ]),
  DOCTOR: new Set([
    'patients.view', 'appointments.view', 'consultation.view', 'consultation.create', 'consultation.update',
    'diagnosis.view', 'diagnosis.create', 'diagnosis.update', 'prescription.view', 'prescription.create', 'prescription.update',
    'lab_orders.view', 'lab_orders.create', 'lab_results.view', 'referrals.view', 'referrals.create',
    'clinic.view', 'queue.view', 'dashboard.view', 'medicine_master.view'
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
    'reports.view', 'reports.export', 'clinic.view', 'dashboard.view',
    'medicine_master.view'
  ])
};

export const HUMAN_ROLE_LABELS: Record<Role, string> = {
  DISTRICT_OFFICER: 'District Officer',
  HOSPITAL_ADMIN: 'Hospital Admin',
  DOCTOR: 'Doctor',
  NURSE: 'Nurse',
  LAB_TECHNICIAN: 'Lab Technician',
  PHARMACIST: 'Pharmacist'
};

export const getHumanRoleLabel = (role: Role | string | undefined): string => {
  if (!role) return 'Healthcare User';
  if (role in HUMAN_ROLE_LABELS) {
    return HUMAN_ROLE_LABELS[role as Role];
  }
  return role.replace(/_/g, ' ');
};

export const ROLE_ALLOWED_PATHS: Record<Role, string[]> = {
  DISTRICT_OFFICER: [
    '/', '/network', '/facilities', '/queue', '/referrals', '/pharmacy', '/reports', '/alerts', '/compliance', '/audit'
  ],
  HOSPITAL_ADMIN: [
    '/', '/patients', '/queue', '/facilities', '/pharmacy', '/referrals', '/followups', '/infrastructure', '/reports', '/alerts'
  ],
  DOCTOR: [
    '/', '/patients', '/queue', '/consultation', '/referrals', '/followups', '/teleconsultation', '/alerts'
  ],
  NURSE: [
    '/', '/patients', '/triage', '/queue', '/followups', '/ncd', '/maternal-child', '/outreach', '/wellness', '/alerts'
  ],
  LAB_TECHNICIAN: [
    '/', '/lab', '/alerts'
  ],
  PHARMACIST: [
    '/', '/pharmacy', '/infrastructure', '/alerts'
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
