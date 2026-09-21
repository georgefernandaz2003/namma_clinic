import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { isPathAllowedForRole } from '../utils/permissions';
import api from '../services/api';
import {
  LayoutDashboard,
  Network,
  Building2,
  Users,
  Clock,
  Stethoscope,
  FileText,
  TestTube,
  Pill,
  Share2,
  CalendarCheck,
  Activity,
  HeartPulse,
  Radio,
  Video,
  MapPin,
  Smile,
  Users2,
  ShieldCheck,
  FileSpreadsheet,
  Bell,
  Sliders,
  CheckSquare,
  Lock,
  LogOut,
  RotateCcw,
  Building,
  Wrench
} from 'lucide-react';

interface NavItem {
  name: string;
  path: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  { name: 'Dashboard', path: '/', icon: <LayoutDashboard className="w-5 h-5" /> },
  { name: 'Healthcare Network', path: '/network', icon: <Network className="w-5 h-5 text-teal-600" /> },
  { name: 'Facilities Master', path: '/facilities', icon: <Building2 className="w-5 h-5" /> },
  { name: 'Patients', path: '/patients', icon: <Users className="w-5 h-5" /> },
  { name: 'OPD Queue', path: '/queue', icon: <Clock className="w-5 h-5" /> },
  { name: 'Nurse Triage', path: '/triage', icon: <Stethoscope className="w-5 h-5 text-emerald-600" /> },
  { name: 'Doctor Consultation', path: '/consultation', icon: <FileText className="w-5 h-5 text-blue-600" /> },
  { name: 'Diagnostics Lab', path: '/lab', icon: <TestTube className="w-5 h-5 text-purple-600" /> },
  { name: 'Pharmacy & FEFO', path: '/pharmacy', icon: <Pill className="w-5 h-5 text-amber-600" /> },
  { name: 'Referral Network', path: '/referrals', icon: <Share2 className="w-5 h-5 text-rose-600" /> },
  { name: 'Follow-up Care', path: '/followups', icon: <CalendarCheck className="w-5 h-5" /> },
  { name: 'NCD Management', path: '/ncd', icon: <Activity className="w-5 h-5" /> },
  { name: 'Disease Surveillance', path: '/surveillance', icon: <Radio className="w-5 h-5 text-red-600" /> },
  { name: 'Teleconsultation', path: '/teleconsultation', icon: <Video className="w-5 h-5" /> },
  { name: 'Outreach & Camps', path: '/outreach', icon: <MapPin className="w-5 h-5" /> },
  { name: 'Wellness Sessions', path: '/wellness', icon: <Smile className="w-5 h-5" /> },
  { name: 'ARS Committee', path: '/ars', icon: <Users2 className="w-5 h-5" /> },
  { name: 'Quality & Waste', path: '/quality', icon: <ShieldCheck className="w-5 h-5" /> },
  { name: 'Clinic Infra & Maintenance', path: '/infrastructure', icon: <Wrench className="w-5 h-5 text-amber-600" /> },
  { name: 'Reports & CSV', path: '/reports', icon: <FileSpreadsheet className="w-5 h-5" /> },
  { name: 'Alert Engine', path: '/alerts', icon: <Bell className="w-5 h-5 text-yellow-600" /> },
  { name: 'Integrations (Mock)', path: '/integrations', icon: <Sliders className="w-5 h-5" /> },
  { name: 'Namma Compliance', path: '/compliance', icon: <CheckSquare className="w-5 h-5 text-emerald-600" /> },
  { name: 'Audit Trail', path: '/audit', icon: <Lock className="w-5 h-5" /> },
];

export const DashboardLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, activeFacility, allFacilities, logout, setActiveFacility, refreshUserData } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [resetting, setResetting] = useState(false);

  const handleResetDemo = async () => {
    if (!window.confirm('Reset all demo data back to initial pristine state?')) return;
    setResetting(true);
    try {
      await api.post('admin/reset-demo/');
      await refreshUserData();
      alert('Demo data successfully reset!');
      navigate('/');
    } catch (e) {
      alert('Failed to reset demo data.');
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-72 bg-white border-r border-slate-200 flex flex-col z-20 shadow-sm">
        {/* Brand Header */}
        <div className="p-4 border-b border-slate-200 flex items-center gap-3 bg-emerald-50/50">
          <div className="w-10 h-10 rounded-xl bg-emerald-600 flex items-center justify-center font-bold text-white shadow-md shadow-emerald-600/30">
            NC
          </div>
          <div>
            <h1 className="font-bold text-base text-slate-900 tracking-wide leading-tight">NAMMA CLINIC</h1>
            <p className="text-xs text-emerald-700 font-bold">Digital Healthcare Network</p>
          </div>
        </div>

        {/* Facility Context Switcher / Scope Badge */}
        <div className="p-3 border-b border-slate-200 bg-slate-50">
          <label className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 flex items-center justify-between">
            <span>{user?.role === 'DISTRICT_OFFICER' ? 'District View Filter' : 'Assigned Facility Scope'}</span>
            {user?.role !== 'DISTRICT_OFFICER' && <Lock className="w-3 h-3 text-emerald-600" />}
          </label>
          
          {user?.role === 'DISTRICT_OFFICER' ? (
            <div className="flex items-center gap-2 bg-white border border-slate-300 rounded-lg p-2 shadow-xs">
              <Building className="w-4 h-4 text-emerald-600 shrink-0" />
              <select
                value={activeFacility?.id || ''}
                onChange={(e) => {
                  const found = allFacilities.find((f) => f.id === parseInt(e.target.value));
                  if (found) setActiveFacility(found);
                }}
                className="bg-transparent text-xs text-slate-800 font-semibold focus:outline-none w-full cursor-pointer"
              >
                {allFacilities.map((fac) => (
                  <option key={fac.id} value={fac.id} className="bg-white text-slate-800">
                    {fac.facility_name} ({fac.facility_type.replace('_', ' ')})
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div className="flex items-center gap-2 bg-emerald-50/80 border border-emerald-300 rounded-lg p-2 shadow-xs">
              <Building className="w-4 h-4 text-emerald-700 shrink-0" />
              <div className="truncate">
                <span className="text-xs font-extrabold text-emerald-950 block truncate">
                  {user?.facility_name || activeFacility?.facility_name || 'Assigned Hospital'}
                </span>
                <span className="text-[9px] text-emerald-700 font-bold uppercase tracking-wider block">
                  Authorized Facility Scope
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 overflow-y-auto p-3 space-y-1">
          {navItems
            .filter((item) => isPathAllowedForRole(user?.role, item.path))
            .map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-emerald-100/70 text-emerald-900 border border-emerald-300 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  {item.icon}
                  <span>{item.name}</span>
                </Link>
              );
            })}
        </nav>

        {/* User Footer with Identity & Scope */}
        <div className="p-3 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-2 overflow-hidden">
            <div className="w-8 h-8 rounded-full bg-emerald-600 border border-emerald-400 flex items-center justify-center text-xs font-black text-white shrink-0 shadow-xs">
              {user?.full_name?.charAt(0) || 'U'}
            </div>
            <div className="truncate">
              <p className="text-xs font-bold text-slate-900 truncate">{user?.full_name || 'Demo User'}</p>
              <p className="text-[10px] text-emerald-700 font-extrabold truncate">
                {user?.role_display || (user?.role ? user.role.replace(/_/g, ' ') : 'User')} • {user?.role === 'DISTRICT_OFFICER' ? 'District Scope' : (user?.facility_name || activeFacility?.facility_name || 'Facility Scope')}
              </p>
            </div>
          </div>
          <button
            onClick={logout}
            title="Logout"
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-slate-200 transition cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>

      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="h-14 bg-white border-b border-slate-200 px-6 flex items-center justify-between z-10 shadow-xs">
          {/* Demo Mode Banner & User Role Identity */}
          <div className="flex items-center gap-3">
            <span className="px-2.5 py-1 rounded-full text-[10px] font-extrabold bg-emerald-100 text-emerald-900 border border-emerald-300 uppercase tracking-widest flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              {user?.role_display || 'Namma Clinic Operational Console'}
            </span>
            <p className="text-xs text-slate-600 font-medium hidden sm:block">
              {activeFacility?.facility_name || user?.facility_name || 'BBMP District Health Network'}
            </p>
          </div>

          {/* Action & Notification Buttons */}
          <div className="flex items-center gap-3">
            <Link
              to="/alerts"
              className="relative p-2 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition"
              title="Alert Notifications"
            >
              <Bell className="w-4 h-4" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-rose-500 rounded-full animate-ping" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-rose-500 rounded-full" />
            </Link>

            <button
              onClick={handleResetDemo}
              disabled={resetting}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold border border-slate-300 transition cursor-pointer"
            >
              <RotateCcw className={`w-3.5 h-3.5 text-amber-600 ${resetting ? 'animate-spin' : ''}`} />
              <span>{resetting ? 'Resetting...' : 'Reset Demo'}</span>
            </button>
          </div>
        </header>

        {/* Page Body */}
        <main className="flex-1 overflow-y-auto p-6 bg-slate-50">{children}</main>
      </div>
    </div>
  );
};
