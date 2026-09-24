import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  ROLE_DASHBOARD_METADATA,
  getRoleNavigation,
  formatScopeDisplay,
  type NavItem,
} from '../../navigation/navigationConfig';
import EmptyState from '../../components/common/EmptyState';
import {
  LayoutDashboard,
  Network,
  Building2,
  Users,
  Clock,
  Stethoscope,
  TestTube,
  Pill,
  Share2,
  CalendarCheck,
  Activity,
  Radio,
  Users2,
  ShieldCheck,
  FileSpreadsheet,
  CheckSquare,
  Lock,
  Sliders,
  Bell,
  Wrench,
  FileText,
  MapPin,
  Smile,
  Shield,
  ArrowRight,
  Building,
} from 'lucide-react';
import type { Role } from '../../types/auth';

const ICON_MAP: Record<string, React.ReactNode> = {
  LayoutDashboard: <LayoutDashboard className="w-5 h-5 text-emerald-600" />,
  Network: <Network className="w-5 h-5 text-teal-600" />,
  Building2: <Building2 className="w-5 h-5 text-indigo-600" />,
  Users: <Users className="w-5 h-5 text-blue-600" />,
  Clock: <Clock className="w-5 h-5 text-emerald-600" />,
  Stethoscope: <Stethoscope className="w-5 h-5 text-emerald-600" />,
  TestTube: <TestTube className="w-5 h-5 text-purple-600" />,
  Pill: <Pill className="w-5 h-5 text-amber-600" />,
  Share2: <Share2 className="w-5 h-5 text-rose-600" />,
  CalendarCheck: <CalendarCheck className="w-5 h-5 text-teal-600" />,
  Activity: <Activity className="w-5 h-5 text-rose-500" />,
  Radio: <Radio className="w-5 h-5 text-red-600" />,
  Users2: <Users2 className="w-5 h-5 text-indigo-600" />,
  ShieldCheck: <ShieldCheck className="w-5 h-5 text-emerald-600" />,
  FileSpreadsheet: <FileSpreadsheet className="w-5 h-5 text-teal-600" />,
  CheckSquare: <CheckSquare className="w-5 h-5 text-emerald-600" />,
  Lock: <Lock className="w-5 h-5 text-slate-600" />,
  Sliders: <Sliders className="w-5 h-5 text-slate-600" />,
  Bell: <Bell className="w-5 h-5 text-yellow-600" />,
  Wrench: <Wrench className="w-5 h-5 text-amber-600" />,
  FileText: <FileText className="w-5 h-5 text-blue-600" />,
  MapPin: <MapPin className="w-5 h-5 text-emerald-600" />,
  Smile: <Smile className="w-5 h-5 text-teal-600" />,
};

interface RoleDashboardFoundationProps {
  expectedRole: Role;
}

export const RoleDashboardFoundation: React.FC<RoleDashboardFoundationProps> = ({ expectedRole }) => {
  const { user, activeFacility } = useAuth();

  const meta = ROLE_DASHBOARD_METADATA[expectedRole];
  const navSections = getRoleNavigation(expectedRole, user?.permissions);

  const scopeInfo = formatScopeDisplay(
    user?.scope_type,
    activeFacility?.facility_name || user?.facility_name,
    activeFacility?.facility_code || user?.facility_details?.facility_code,
    user?.district_name || (user?.assigned_district ? `District #${user.assigned_district}` : null)
  );

  return (
    <div className="space-y-6">
      {/* Role Landing Header Banner */}
      <section
        aria-labelledby="dashboard-header-title"
        className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs relative overflow-hidden"
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-emerald-100 text-emerald-900 border border-emerald-300 uppercase tracking-wider">
                {user?.role_display || expectedRole}
              </span>
              <span className="text-xs text-slate-400">•</span>
              <span className="text-xs font-semibold text-slate-500">
                {scopeInfo.label}
              </span>
            </div>
            <h1 id="dashboard-header-title" className="text-xl font-bold text-slate-900 tracking-tight">
              {meta.title}
            </h1>
            <p className="text-xs text-slate-600 max-w-2xl leading-relaxed">
              {meta.subtitle}
            </p>
          </div>

          {/* Scope and User Identity Summary Box */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-right shrink-0">
            <p className="text-xs font-bold text-slate-900 flex items-center gap-1.5 justify-end">
              <Shield className="w-3.5 h-3.5 text-emerald-600" aria-hidden="true" />
              {user?.full_name || 'Healthcare Practitioner'}
            </p>
            <p className="text-[11px] font-mono text-slate-500 mt-0.5">
              Username: <span className="font-semibold text-slate-800">{user?.username}</span>
            </p>
            <p className="text-[11px] font-medium text-emerald-800 mt-1 flex items-center gap-1 justify-end">
              <Building className="w-3.5 h-3.5 text-emerald-700" aria-hidden="true" />
              <span>{scopeInfo.details}</span>
            </p>
          </div>
        </div>
      </section>

      {/* Authorized Navigation Directory */}
      <section aria-labelledby="authorized-nav-title" className="space-y-4">
        <h2 id="authorized-nav-title" className="text-xs font-bold uppercase tracking-wider text-slate-500">
          Authorized Operational Stations & Modules
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {navSections.flatMap((section) =>
            section.items
              .filter((item) => item.path !== meta.landingRoute)
              .map((item: NavItem) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className="bg-white border border-slate-200 hover:border-emerald-400 p-4 rounded-xl shadow-xs transition hover:shadow-sm flex flex-col justify-between group focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="w-9 h-9 rounded-lg bg-slate-50 group-hover:bg-emerald-50 border border-slate-200 group-hover:border-emerald-200 flex items-center justify-center transition">
                        {ICON_MAP[item.iconName] || <LayoutDashboard className="w-5 h-5 text-slate-600" />}
                      </div>
                      <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-emerald-600 group-hover:translate-x-0.5 transition-all" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-slate-900 group-hover:text-emerald-900 transition">
                        {item.name}
                      </h3>
                      <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">
                        {item.description}
                      </p>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono text-slate-400 group-hover:text-emerald-700 mt-3 block">
                    {item.path}
                  </span>
                </Link>
              ))
          )}
        </div>
      </section>

      {/* Domain Workflow & Real-Time Statistics Placeholder */}
      <section aria-labelledby="workflow-status-title" className="mt-8">
        <EmptyState
          title="Clinical & Operational Workflows Under Active Staging"
          description={`Domain encounter forms, queues, and real-time live metrics for ${meta.title} are scheduled for implementation in subsequent domain phases. Backend service layer and permission boundaries remain authoritative.`}
          className="border-slate-300 bg-white shadow-xs"
        />
      </section>
    </div>
  );
};

export default RoleDashboardFoundation;
