import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  getRoleNavigation,
  formatScopeDisplay,
  type NavSection,
  type NavItem,
} from '../navigation/navigationConfig';
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
  Radio,
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
  Wrench,
  Menu,
  X,
} from 'lucide-react';

const ICON_MAP: Record<string, React.ReactNode> = {
  LayoutDashboard: <LayoutDashboard className="w-4 h-4 text-emerald-600" />,
  Network: <Network className="w-4 h-4 text-teal-600" />,
  Building2: <Building2 className="w-4 h-4 text-indigo-600" />,
  Users: <Users className="w-4 h-4 text-blue-600" />,
  Clock: <Clock className="w-4 h-4 text-emerald-600" />,
  Stethoscope: <Stethoscope className="w-4 h-4 text-emerald-600" />,
  TestTube: <TestTube className="w-4 h-4 text-purple-600" />,
  Pill: <Pill className="w-4 h-4 text-amber-600" />,
  Share2: <Share2 className="w-4 h-4 text-rose-600" />,
  CalendarCheck: <CalendarCheck className="w-4 h-4 text-teal-600" />,
  Activity: <Activity className="w-4 h-4 text-rose-500" />,
  Radio: <Radio className="w-4 h-4 text-red-600" />,
  Users2: <Users2 className="w-4 h-4 text-indigo-600" />,
  ShieldCheck: <ShieldCheck className="w-4 h-4 text-emerald-600" />,
  FileSpreadsheet: <FileSpreadsheet className="w-4 h-4 text-teal-600" />,
  CheckSquare: <CheckSquare className="w-4 h-4 text-emerald-600" />,
  Lock: <Lock className="w-4 h-4 text-slate-600" />,
  Sliders: <Sliders className="w-4 h-4 text-slate-600" />,
  Bell: <Bell className="w-4 h-4 text-yellow-600" />,
  Wrench: <Wrench className="w-4 h-4 text-amber-600" />,
  FileText: <FileText className="w-4 h-4 text-blue-600" />,
  MapPin: <MapPin className="w-4 h-4 text-emerald-600" />,
  Smile: <Smile className="w-4 h-4 text-teal-600" />,
};

export const DashboardLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, activeFacility, allFacilities, logout, setActiveFacility, refreshUserData } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [resetting, setResetting] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  const handleResetDemo = async () => {
    if (!window.confirm('Reset all demo data back to initial pristine state?')) return;
    setResetting(true);
    try {
      await api.post('admin/reset-demo/');
      await refreshUserData();
      alert('Demo data successfully reset!');
      navigate('/dashboard');
    } catch (e) {
      alert('Failed to reset demo data.');
    } finally {
      setResetting(false);
    }
  };

  const navSections = getRoleNavigation(user?.role, user?.permissions);

  const scopeInfo = formatScopeDisplay(
    user?.scope_type,
    activeFacility?.facility_name || user?.facility_name,
    activeFacility?.facility_code || user?.facility_details?.facility_code,
    user?.district_name || (user?.assigned_district ? `District #${user.assigned_district}` : null)
  );

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 overflow-hidden">
      {/* Accessibility Skip Link */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:px-4 focus:py-2 focus:bg-emerald-600 focus:text-white focus:rounded-lg focus:shadow-lg focus:font-bold focus:text-xs"
      >
        Skip to main content
      </a>

      {/* Mobile Backdrop Overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 bg-slate-950/40 z-30 md:hidden backdrop-blur-xs transition-opacity"
          onClick={() => setMobileMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Navigation */}
      <aside
        aria-label="Primary Navigation"
        className={`fixed md:static inset-y-0 left-0 z-40 w-72 bg-white border-r border-slate-200 flex flex-col shadow-sm transition-transform duration-200 ease-in-out ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        {/* Brand Header */}
        <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-emerald-50/50">
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-xl bg-emerald-600 flex items-center justify-center font-black text-white shadow-md shadow-emerald-600/30 select-none"
              aria-hidden="true"
            >
              NC
            </div>
            <div>
              <span className="font-bold text-base text-slate-900 tracking-wide leading-tight block">
                NAMMA CLINIC
              </span>
              <p className="text-xs text-emerald-700 font-bold">Digital Healthcare Network</p>
            </div>
          </div>

          {/* Mobile close button */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(false)}
            className="md:hidden p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg cursor-pointer"
            aria-label="Close menu"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Facility Context Switcher / Scope Badge */}
        <div className="p-3 border-b border-slate-200 bg-slate-50">
          <label className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 flex items-center justify-between">
            <span>{scopeInfo.label}</span>
            {!scopeInfo.isDistrict && <Lock className="w-3 h-3 text-emerald-600" aria-hidden="true" />}
          </label>

          {scopeInfo.isDistrict ? (
            <div className="flex items-center gap-2 bg-white border border-slate-300 rounded-lg p-2 shadow-xs">
              <Building className="w-4 h-4 text-emerald-600 shrink-0" aria-hidden="true" />
              <select
                aria-label="Select facility filter"
                value={activeFacility?.id || ''}
                onChange={(e) => {
                  const found = allFacilities.find((f) => f.id === parseInt(e.target.value, 10));
                  if (found) setActiveFacility(found);
                }}
                className="bg-transparent text-xs text-slate-800 font-semibold focus:outline-none w-full cursor-pointer"
              >
                {allFacilities.map((fac) => (
                  <option key={fac.id} value={fac.id} className="bg-white text-slate-800">
                    {fac.facility_name} ({fac.facility_type.replace(/_/g, ' ')})
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div className="flex items-center gap-2 bg-emerald-50/80 border border-emerald-300 rounded-lg p-2 shadow-xs">
              <Building className="w-4 h-4 text-emerald-700 shrink-0" aria-hidden="true" />
              <div className="truncate">
                <span className="text-xs font-extrabold text-emerald-950 block truncate">
                  {scopeInfo.details}
                </span>
                <span className="text-[9px] text-emerald-700 font-bold uppercase tracking-wider block">
                  Authorized Scope
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 overflow-y-auto p-3 space-y-3" aria-label="Sidebar Sections">
          {navSections.map((section: NavSection, sIdx: number) => {
            if (section.items.length === 0) return null;

            return (
              <div key={section.title || sIdx} className="space-y-1">
                {section.title && (
                  <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400 px-3 pt-2 pb-1 select-none">
                    {section.title}
                  </div>
                )}
                {section.items.map((item: NavItem) => {
                  const isActive = location.pathname === item.path;
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-semibold transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 ${
                        isActive
                          ? 'bg-emerald-100/80 text-emerald-900 border border-emerald-300 shadow-xs font-bold'
                          : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                      }`}
                      aria-current={isActive ? 'page' : undefined}
                    >
                      {ICON_MAP[item.iconName] || <LayoutDashboard className="w-4 h-4 text-slate-500" />}
                      <span>{item.name}</span>
                    </Link>
                  );
                })}
              </div>
            );
          })}
        </nav>

        {/* User Footer with Identity & Scope */}
        <div className="p-3 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-2 overflow-hidden">
            <div
              className="w-8 h-8 rounded-full bg-emerald-600 border border-emerald-400 flex items-center justify-center text-xs font-black text-white shrink-0 shadow-xs select-none"
              aria-hidden="true"
            >
              {user?.full_name?.charAt(0) || user?.username?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <div className="truncate">
              <p className="text-xs font-bold text-slate-900 truncate">
                {user?.full_name || user?.username || 'Demo User'}
              </p>
              <p className="text-[10px] text-emerald-700 font-extrabold truncate">
                {user?.role_display || user?.role || 'Staff'} • {scopeInfo.isDistrict ? 'District Scope' : 'Facility Scope'}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            title="Sign out of console"
            aria-label="Sign out of console"
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-slate-200 transition cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-rose-500"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </aside>

      {/* Main Layout Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="h-14 bg-white border-b border-slate-200 px-4 sm:px-6 flex items-center justify-between z-10 shadow-xs">
          <div className="flex items-center gap-3">
            {/* Mobile menu hamburger toggle */}
            <button
              type="button"
              onClick={() => setMobileMenuOpen(true)}
              className="md:hidden p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 cursor-pointer"
              aria-label="Open navigation menu"
            >
              <Menu className="w-5 h-5" />
            </button>

            {/* Role Identity Badge */}
            <span className="px-2.5 py-1 rounded-full text-[10px] font-extrabold bg-emerald-100 text-emerald-900 border border-emerald-300 uppercase tracking-widest flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" aria-hidden="true" />
              {user?.role_display || user?.role || 'Clinical Console'}
            </span>
            <p className="text-xs text-slate-600 font-medium hidden sm:block truncate max-w-xs md:max-w-md">
              {scopeInfo.details}
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3">
            <Link
              to="/alerts"
              className="relative p-2 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
              title="Alert Notifications"
              aria-label="View Alerts"
            >
              <Bell className="w-4 h-4" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-rose-500 rounded-full animate-ping" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-rose-500 rounded-full" />
            </Link>

            <button
              type="button"
              onClick={handleResetDemo}
              disabled={resetting}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold border border-slate-300 transition cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
              aria-label="Reset demo dataset"
            >
              <RotateCcw className={`w-3.5 h-3.5 text-amber-600 ${resetting ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">{resetting ? 'Resetting...' : 'Reset Demo'}</span>
            </button>

            <button
              type="button"
              onClick={handleLogout}
              className="hidden sm:flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold text-slate-600 hover:text-rose-600 hover:bg-rose-50 border border-slate-200 transition cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-rose-500"
              aria-label="Sign out"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign Out</span>
            </button>
          </div>
        </header>

        {/* Page Body */}
        <main id="main-content" className="flex-1 overflow-y-auto p-4 sm:p-6 bg-slate-50">
          {children}
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
