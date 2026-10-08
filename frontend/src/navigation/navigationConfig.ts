import type { Role } from '../types/auth';

export interface NavItem {
  name: string;
  path: string;
  iconName: string;
  description: string;
  requiredPermission?: string;
}

export interface NavSection {
  title: string;
  items: NavItem[];
}

export interface RoleDashboardMeta {
  role: Role;
  title: string;
  subtitle: string;
  landingRoute: string;
  iconName: string;
  scopeTypeRequired: 'DISTRICT' | 'FACILITY';
}

export const ROLE_DASHBOARD_ROUTES: Record<Role, string> = {
  DISTRICT_OFFICER: '/dashboard/district',
  HOSPITAL_ADMIN: '/dashboard/admin',
  DOCTOR: '/dashboard/doctor',
  NURSE: '/dashboard/nurse',
  FRONT_DESK_OFFICER: '/dashboard/front-desk',
  LAB_TECHNICIAN: '/dashboard/lab',
  PHARMACIST: '/dashboard/pharmacy',
  INVENTORY: '/inventory',
};

export const ROLE_DASHBOARD_METADATA: Record<Role, RoleDashboardMeta> = {
  DISTRICT_OFFICER: {
    role: 'DISTRICT_OFFICER',
    title: 'District Health Officer Oversight Console',
    subtitle: 'District-wide healthcare network administration, public health surveillance, and governance.',
    landingRoute: '/dashboard/district',
    iconName: 'Network',
    scopeTypeRequired: 'DISTRICT',
  },
  HOSPITAL_ADMIN: {
    role: 'HOSPITAL_ADMIN',
    title: 'Hospital Administrator Operations Console',
    subtitle: 'Facility governance, infrastructure maintenance, ARS committee records, and quality compliance.',
    landingRoute: '/dashboard/admin',
    iconName: 'Building2',
    scopeTypeRequired: 'FACILITY',
  },
  DOCTOR: {
    role: 'DOCTOR',
    title: 'Medical Officer Clinical Console',
    subtitle: 'Outpatient consultations, diagnostic order entry, prescriptions, and referral coordination.',
    landingRoute: '/dashboard/doctor',
    iconName: 'Stethoscope',
    scopeTypeRequired: 'FACILITY',
  },
  NURSE: {
    role: 'NURSE',
    title: 'Nursing & Triage Station Console',
    subtitle: 'Patient intake registration, vital signs assessment, follow-up tracking, and community outreach.',
    landingRoute: '/dashboard/nurse',
    iconName: 'Clock',
    scopeTypeRequired: 'FACILITY',
  },
  LAB_TECHNICIAN: {
    role: 'LAB_TECHNICIAN',
    title: 'Diagnostic Laboratory Console',
    subtitle: 'Test request accessioning, specimen processing, and laboratory result entry.',
    landingRoute: '/dashboard/lab',
    iconName: 'TestTube',
    scopeTypeRequired: 'FACILITY',
  },
  PHARMACIST: {
    role: 'PHARMACIST',
    title: 'Pharmacy Dispensing & Inventory Console',
    subtitle: 'Prescription verification, FEFO-governed drug dispensing, and inventory stock reconciliation.',
    landingRoute: '/dashboard/pharmacy',
    iconName: 'Pill',
    scopeTypeRequired: 'FACILITY',
  },
  FRONT_DESK_OFFICER: {
    role: 'FRONT_DESK_OFFICER',
    title: 'Front Desk Officer Console',
    subtitle: 'Patient registration, master patient index lookup, and OPD queue management.',
    landingRoute: '/dashboard/front-desk',
    iconName: 'Users',
    scopeTypeRequired: 'FACILITY',
  },
  INVENTORY: {
    role: 'INVENTORY',
    title: 'Inventory & Procurement Workstation',
    subtitle: 'Procurement orders, Goods Receipt Notes (GRN), batch tracking, and physical stock reconciliation.',
    landingRoute: '/inventory',
    iconName: 'Package',
    scopeTypeRequired: 'FACILITY',
  },
};

export const ROLE_NAVIGATION_CONFIG: Record<Role, NavSection[]> = {
  DISTRICT_OFFICER: [
    {
      title: 'DISTRICT OVERSIGHT',
      items: [
        { name: 'District Dashboard', path: '/dashboard/district', iconName: 'LayoutDashboard', description: 'Network KPIs, facilities status, and district overview' },
        { name: 'Healthcare Network', path: '/network', iconName: 'Network', description: 'Interactive network graph of regional hospital connectivity' },
        { name: 'Staff Directory', path: '/admin/staff', iconName: 'Users', description: 'District staff identity, postings, and lifecycle administration' },
        { name: 'Facilities Master', path: '/facilities', iconName: 'Building2', description: 'Registry of district hospitals, clinics, and UPHCs' },
        { name: 'Patients Registry', path: '/patients', iconName: 'Users', description: 'Master patient index across district facilities' },
        { name: 'OPD Queue Overview', path: '/queue', iconName: 'Clock', description: 'Cross-facility outpatient queue status' },
        { name: 'Pharmacy Network', path: '/pharmacy', iconName: 'Pill', description: 'District pharmaceutical stock levels and ledger' },
        { name: 'Referral Network', path: '/referrals', iconName: 'Share2', description: 'Inter-facility tertiary care transfer tracking' },
      ],
    },
    {
      title: 'PUBLIC HEALTH & SURVEILLANCE',
      items: [
        { name: 'NCD Management', path: '/ncd', iconName: 'Activity', description: 'Non-communicable disease chronic care monitoring' },
        { name: 'Disease Surveillance', path: '/surveillance', iconName: 'Radio', description: 'Outbreak signals and infectious disease tracking' },
      ],
    },
    {
      title: 'GOVERNANCE & AUDIT',
      items: [
        { name: 'ARS Committee', path: '/ars', iconName: 'Users2', description: 'Arogya Raksha Samiti governance records' },
        { name: 'Quality & Waste', path: '/quality', iconName: 'ShieldCheck', description: 'Biomedical waste and clinical quality logs' },
        { name: 'Infrastructure Maintenance', path: '/infrastructure', iconName: 'Wrench', description: 'Equipment tickets and clinic maintenance' },
        { name: 'Reports & Export', path: '/reports', iconName: 'FileSpreadsheet', description: 'Operational report generation and data export' },
        { name: 'Compliance Review', path: '/compliance', iconName: 'CheckSquare', description: 'Health standards and statutory compliance audit' },
        { name: 'System Audit Trail', path: '/audit', iconName: 'Lock', description: 'Immutable security and clinical access logs' },
      ],
    },
    {
      title: 'SYSTEM',
      items: [
        { name: 'System Integrations', path: '/integrations', iconName: 'Sliders', description: 'External health exchange interfaces' },
        { name: 'Alert Engine', path: '/alerts', iconName: 'Bell', description: 'Automated clinical and inventory notifications' },
      ],
    },
  ],

  HOSPITAL_ADMIN: [
    {
      title: 'FACILITY OPERATIONS',
      items: [
        { name: 'Admin Dashboard', path: '/dashboard/admin', iconName: 'LayoutDashboard', description: 'Facility operations overview and management' },
        { name: 'Facility Profile', path: '/facilities', iconName: 'Building2', description: 'Facility configuration and departmental registry' },
        { name: 'Staff Directory', path: '/admin/staff', iconName: 'Users', description: 'Facility staff roster, invitations, and role assignments' },
        { name: 'Patients Registry', path: '/patients', iconName: 'Users', description: 'Facility patient master and demographic records' },
        { name: 'OPD Queue Status', path: '/queue', iconName: 'Clock', description: 'Daily outpatient appointment and token flow' },
        { name: 'Pharmacy & Stock', path: '/pharmacy', iconName: 'Pill', description: 'Dispensing records and medicine inventory batches' },
        { name: 'Inventory & Procurement', path: '/inventory', iconName: 'Package', description: 'Procurement orders, goods receipt, and stock ledger' },
        { name: 'Follow-up Tracking', path: '/followups', iconName: 'CalendarCheck', description: 'Post-consultation follow-up scheduling' },
        { name: 'NCD Management', path: '/ncd', iconName: 'Activity', description: 'Non-communicable disease chronic care monitoring' },
        { name: 'Infra & Maintenance', path: '/infrastructure', iconName: 'Wrench', description: 'Facility maintenance tickets and consumable stock' },
      ],
    },
    {
      title: 'GOVERNANCE & QUALITY',
      items: [
        { name: 'ARS Committee', path: '/ars', iconName: 'Users2', description: 'Facility ARS meetings, budget, and resolutions' },
        { name: 'Quality & Biomedical Waste', path: '/quality', iconName: 'ShieldCheck', description: 'Infection control and waste disposal logs' },
        { name: 'Reports & Audits', path: '/reports', iconName: 'FileSpreadsheet', description: 'Operational metrics and CSV data downloads' },
      ],
    },
    {
      title: 'SYSTEM',
      items: [
        { name: 'System Integrations', path: '/integrations', iconName: 'Sliders', description: 'Facility external interface connectors' },
        { name: 'Alert Engine', path: '/alerts', iconName: 'Bell', description: 'Operations and facility supply alerts' },
      ],
    },
  ],

  DOCTOR: [
    {
      title: 'CLINICAL CARE',
      items: [
        { name: 'Doctor Dashboard', path: '/dashboard/doctor', iconName: 'LayoutDashboard', description: 'Active clinical caseload and daily outpatient roster' },
        { name: 'Patients', path: '/patients', iconName: 'Users', description: 'Patient records, consultation history, and vitals' },
        { name: 'Consultation Queue', path: '/queue', iconName: 'Clock', description: 'Triaged patients awaiting clinical examination' },
        { name: 'Doctor Consultation', path: '/consultation', iconName: 'FileText', description: 'Active clinical encounter examination and diagnosis' },
        { name: 'Diagnostic Orders', path: '/lab', iconName: 'TestTube', description: 'Laboratory test requests and verified lab results' },
        { name: 'Referral Network', path: '/referrals', iconName: 'Share2', description: 'Specialist and emergency hospital referral orders' },
        { name: 'Follow-up Care', path: '/followups', iconName: 'CalendarCheck', description: 'Scheduled patient review and follow-up care' },
        { name: 'NCD Longitudinal Care', path: '/ncd', iconName: 'Activity', description: 'Chronic disease tracking and treatment adherence' },
      ],
    },
    {
      title: 'SYSTEM',
      items: [
        { name: 'Clinical Alerts', path: '/alerts', iconName: 'Bell', description: 'Critical vitals and abnormal lab result notifications' },
      ],
    },
  ],

  NURSE: [
    {
      title: 'PRIMARY CARE & TRIAGE',
      items: [
        { name: 'Nurse Dashboard', path: '/dashboard/nurse', iconName: 'LayoutDashboard', description: 'Triage intake summary and daily clinic flow' },
        { name: 'Patient Intake', path: '/patients', iconName: 'Users', description: 'New patient registration and demographic intake' },
        { name: 'Triage Queue', path: '/queue', iconName: 'Clock', description: 'Registered patients awaiting vitals measurement' },
        { name: 'Nurse Vitals Triage', path: '/triage', iconName: 'Stethoscope', description: 'BP, pulse, SpO2, and temperature vitals entry' },
        { name: 'Follow-up Tracking', path: '/followups', iconName: 'CalendarCheck', description: 'Community patient follow-up contact list' },
        { name: 'NCD Screening', path: '/ncd', iconName: 'Activity', description: 'Hypertension and diabetes community screening' },
      ],
    },
    {
      title: 'COMMUNITY HEALTH',
      items: [
        { name: 'Outreach & Camps', path: '/outreach', iconName: 'MapPin', description: 'Community health camp and household visits' },
        { name: 'Wellness Sessions', path: '/wellness', iconName: 'Smile', description: 'Preventive health education and wellness workshops' },
      ],
    },
    {
      title: 'SYSTEM',
      items: [
        { name: 'Operational Alerts', path: '/alerts', iconName: 'Bell', description: 'Patient queue and triage escalation alerts' },
      ],
    },
  ],

  LAB_TECHNICIAN: [
    {
      title: 'DIAGNOSTIC LABORATORY',
      items: [
        { name: 'Laboratory Dashboard', path: '/dashboard/lab', iconName: 'LayoutDashboard', description: 'Pending specimens and daily test accessioning' },
        { name: 'Lab Specimen Queue', path: '/queue', iconName: 'Clock', description: 'Patients with outstanding diagnostic test orders' },
        { name: 'Laboratory Workstation', path: '/lab', iconName: 'TestTube', description: 'Specimen collection, analysis, and result entry' },
      ],
    },
    {
      title: 'SYSTEM',
      items: [
        { name: 'Critical Alerts', path: '/alerts', iconName: 'Bell', description: 'Stat laboratory orders and critical result alerts' },
      ],
    },
  ],

  PHARMACIST: [
    {
      title: 'PHARMACY & DRUG LEDGER',
      items: [
        { name: 'Pharmacy Dashboard', path: '/dashboard/pharmacy', iconName: 'LayoutDashboard', description: 'Prescription dispensing queue and stock summary' },
        { name: 'Dispensing Queue', path: '/queue', iconName: 'Clock', description: 'Verified doctor prescriptions awaiting drug dispensing' },
        { name: 'FEFO Drug Dispensation', path: '/pharmacy', iconName: 'Pill', description: 'Batch-tracked medicine issue with FEFO allocation' },
      ],
    },
    {
      title: 'SYSTEM',
      items: [
        { name: 'Stock Alerts', path: '/alerts', iconName: 'Bell', description: 'Near-expiry batches and minimum stock warning alerts' },
      ],
    },
  ],
  FRONT_DESK_OFFICER: [
    {
      title: 'PATIENT INTAKE & REGISTRATION',
      items: [
        { name: 'Front Desk Console', path: '/dashboard/front-desk', iconName: 'LayoutDashboard', description: 'Front desk intake, registration, duplicate warning, and tokens' },
        { name: 'Patient Directory', path: '/patients', iconName: 'Users', description: 'Patient demographic records and registration list' },
        { name: 'OPD Queue', path: '/queue', iconName: 'Clock', description: 'Outpatient flow and token management' },
      ],
    },
    {
      title: 'SYSTEM',
      items: [
        { name: 'Operational Alerts', path: '/alerts', iconName: 'Bell', description: 'Patient queue and intake alerts' },
      ],
    },
  ],

  INVENTORY: [
    {
      title: 'INVENTORY & PROCUREMENT',
      items: [
        { name: 'Inventory Console', path: '/inventory', iconName: 'Package', description: 'Stock levels, batch expiry, and movement ledger' },
      ],
    },
    {
      title: 'SYSTEM',
      items: [
        { name: 'Stock Alerts', path: '/alerts', iconName: 'Bell', description: 'Near-expiry batches and minimum stock warning alerts' },
      ],
    },
  ],
};

/**
 * Returns the authoritative role landing route.
 */
export const getRoleLandingRoute = (role?: Role | null): string => {
  if (!role) return '/login';
  return ROLE_DASHBOARD_ROUTES[role] || '/login';
};

/**
 * Returns role navigation sections, optionally filtered by backend permissions.
 */
export const getRoleNavigation = (role?: Role | null, permissions?: string[]): NavSection[] => {
  if (!role || !(role in ROLE_NAVIGATION_CONFIG)) return [];

  const rawSections = ROLE_NAVIGATION_CONFIG[role];
  if (!permissions || permissions.length === 0) {
    return rawSections;
  }

  const permSet = new Set(permissions);
  return rawSections
    .map((section) => ({
      ...section,
      items: section.items.filter((item) => {
        if (!item.requiredPermission) return true;
        return permSet.has(item.requiredPermission);
      }),
    }))
    .filter((section) => section.items.length > 0);
};

/**
 * Returns all valid routes accessible by a role.
 */
export const getRoleAllowedRoutes = (role?: Role | null): string[] => {
  if (!role || !(role in ROLE_NAVIGATION_CONFIG)) return [];

  const sections = ROLE_NAVIGATION_CONFIG[role];
  const navPaths = sections.flatMap((sec) => sec.items.map((i) => i.path));

  // Common foundational routes accessible by all authenticated roles
  const baseRoutes = ['/', '/dashboard', ROLE_DASHBOARD_ROUTES[role]];

  return Array.from(new Set([...baseRoutes, ...navPaths]));
};

/**
 * Validates whether a specific path is permitted for the given role.
 */
export const isRouteAllowedForRole = (role: Role | null | undefined, path: string): boolean => {
  if (!role) return false;
  if (path === '/' || path === '/dashboard') return true;

  // Role dashboard isolation: a role can only access their own dashboard route
  if (path.startsWith('/dashboard/')) {
    return path === ROLE_DASHBOARD_ROUTES[role];
  }

  const allowedRoutes = getRoleAllowedRoutes(role);
  return allowedRoutes.some((allowed) => {
    if (allowed === path) return true;
    if (allowed !== '/' && allowed !== '/dashboard' && path.startsWith(`${allowed}/`)) {
      return true;
    }
    return false;
  });
};

/**
 * Returns human-readable facility/scope description.
 */
export const formatScopeDisplay = (
  scopeType: 'DISTRICT' | 'FACILITY' | 'GLOBAL' | undefined,
  facilityName?: string | null,
  facilityCode?: string | null,
  districtName?: string | null
): { label: string; details: string; isDistrict: boolean } => {
  if (scopeType === 'DISTRICT' || (!facilityName && districtName)) {
    return {
      label: 'District Oversight Scope',
      details: districtName ? `${districtName} Health Administration` : 'District Health Administration',
      isDistrict: true,
    };
  }

  if (facilityName) {
    const codeSuffix = facilityCode ? ` [${facilityCode}]` : '';
    return {
      label: 'Facility Operational Scope',
      details: `${facilityName}${codeSuffix}`,
      isDistrict: false,
    };
  }

  return {
    label: 'Unassigned Scope',
    details: 'No facility or district assigned',
    isDistrict: false,
  };
};
