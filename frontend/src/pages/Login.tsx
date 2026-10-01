import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import {
  Shield,
  KeyRound,
  UserCheck,
  Eye,
  EyeOff,
  Stethoscope,
  Activity,
  FlaskConical,
  Pill,
  Package,
  Building2,
  Landmark,
  Layers,
  UserPlus,
  CheckCircle2,
} from 'lucide-react';
import ErrorAlert from '../components/common/ErrorAlert';

interface DemoUser {
  role: string;
  roleBadge: string;
  username: string;
  password: string;
  desc: string;
  category: 'operational' | 'legacy';
  icon: React.ComponentType<{ className?: string }>;
  accentColor: string;
}

const ALL_DEMO_CREDENTIALS: DemoUser[] = [
  // --- All 8 Core Operational Roles + Dual Role ---
  {
    role: 'Compounder / Intake',
    roleBadge: 'COMPOUNDER',
    username: 'e2e_compounder_user',
    password: 'Password123!',
    desc: 'Patient intake registration, demographic search & OPD token issuance',
    category: 'operational',
    icon: UserPlus,
    accentColor: 'text-sky-600 bg-sky-50 border-sky-200',
  },
  {
    role: 'Staff Nurse',
    roleBadge: 'NURSE',
    username: 'e2e_nurse_user',
    password: 'Password123!',
    desc: 'Vitals triage recording, warning flags & doctor queue handoff',
    category: 'operational',
    icon: Activity,
    accentColor: 'text-emerald-600 bg-emerald-50 border-emerald-200',
  },
  {
    role: 'Medical Officer / Doctor',
    roleBadge: 'DOCTOR',
    username: 'e2e_doctor_user',
    password: 'Password123!',
    desc: 'Clinical consults, diagnosis, e-prescriptions & diagnostic lab orders',
    category: 'operational',
    icon: Stethoscope,
    accentColor: 'text-blue-600 bg-blue-50 border-blue-200',
  },
  {
    role: 'Lab Technician',
    roleBadge: 'LAB_TECHNICIAN',
    username: 'e2e_lab_user',
    password: 'Password123!',
    desc: 'Diagnostic order accessioning, specimen intake & test results',
    category: 'operational',
    icon: FlaskConical,
    accentColor: 'text-purple-600 bg-purple-50 border-purple-200',
  },
  {
    role: 'Pharmacist',
    roleBadge: 'PHARMACIST',
    username: 'e2e_pharmacist_user',
    password: 'Password123!',
    desc: 'Prescription verification, FEFO batch selection & medication dispensing',
    category: 'operational',
    icon: Pill,
    accentColor: 'text-amber-600 bg-amber-50 border-amber-200',
  },
  {
    role: 'Inventory Officer',
    roleBadge: 'INVENTORY',
    username: 'e2e_inventory_user',
    password: 'Password123!',
    desc: 'PO procurement, GRN intake, physical stock audits & immutable ledger',
    category: 'operational',
    icon: Package,
    accentColor: 'text-teal-600 bg-teal-50 border-teal-200',
  },
  {
    role: 'Dual-Role (Inv + Pharm)',
    roleBadge: 'INVENTORY + PHARMACIST',
    username: 'e2e_dual_user',
    password: 'Password123!',
    desc: 'Combined operational rights: procurement admin + prescription dispensing',
    category: 'operational',
    icon: Layers,
    accentColor: 'text-violet-600 bg-violet-50 border-violet-200',
  },
  {
    role: 'Hospital Admin',
    roleBadge: 'HOSPITAL_ADMIN',
    username: 'e2e_admin_user',
    password: 'Password123!',
    desc: 'Facility operational settings, staff administration & audit logs',
    category: 'operational',
    icon: Building2,
    accentColor: 'text-indigo-600 bg-indigo-50 border-indigo-200',
  },
  {
    role: 'District Health Officer',
    roleBadge: 'DISTRICT_OFFICER',
    username: 'e2e_dho_user',
    password: 'Password123!',
    desc: 'District health network surveillance, compliance KPI monitoring & audits',
    category: 'operational',
    icon: Landmark,
    accentColor: 'text-rose-600 bg-rose-50 border-rose-200',
  },

  // --- Legacy Dev Fixture Accounts ---
  {
    role: 'Medical Officer (Legacy)',
    roleBadge: 'DOCTOR',
    username: 'localdoc',
    password: 'DoctorPassword123!',
    desc: 'Legacy dev fixture for clinical consultations & prescriptions',
    category: 'legacy',
    icon: Stethoscope,
    accentColor: 'text-slate-600 bg-slate-50 border-slate-200',
  },
  {
    role: 'Staff Nurse (Legacy)',
    roleBadge: 'NURSE',
    username: 'localnurse',
    password: 'NursePassword123!',
    desc: 'Legacy dev fixture for triage recording & nurse queue',
    category: 'legacy',
    icon: Activity,
    accentColor: 'text-slate-600 bg-slate-50 border-slate-200',
  },
  {
    role: 'Pharmacist (Legacy)',
    roleBadge: 'PHARMACIST',
    username: 'localpharm',
    password: 'PharmPassword123!',
    desc: 'Legacy dev fixture for prescription verification & dispensing',
    category: 'legacy',
    icon: Pill,
    accentColor: 'text-slate-600 bg-slate-50 border-slate-200',
  },
  {
    role: 'Lab Tech (Legacy)',
    roleBadge: 'LAB_TECHNICIAN',
    username: 'locallab',
    password: 'LabPassword123!',
    desc: 'Legacy dev fixture for laboratory diagnostic orders',
    category: 'legacy',
    icon: FlaskConical,
    accentColor: 'text-slate-600 bg-slate-50 border-slate-200',
  },
  {
    role: 'Hospital Admin (Legacy)',
    roleBadge: 'HOSPITAL_ADMIN',
    username: 'testadmin',
    password: 'AdminPassword123!',
    desc: 'Legacy dev fixture for hospital admin configuration',
    category: 'legacy',
    icon: Building2,
    accentColor: 'text-slate-600 bg-slate-50 border-slate-200',
  },
  {
    role: 'District Officer (Legacy)',
    roleBadge: 'DISTRICT_OFFICER',
    username: 'localdistrict',
    password: 'DistrictPassword123!',
    desc: 'Legacy dev fixture for district health officer oversight',
    category: 'legacy',
    icon: Landmark,
    accentColor: 'text-slate-600 bg-slate-50 border-slate-200',
  },
];

export const Login: React.FC = () => {
  const { login, error: authError, clearError } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState('e2e_doctor_user');
  const [password, setPassword] = useState('Password123!');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [localError, setLocalError] = useState('');
  const [activeTab, setActiveTab] = useState<'operational' | 'legacy'>('operational');

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setLocalError('Please enter both username and password.');
      return;
    }

    setIsSubmitting(true);
    setLocalError('');
    clearError();

    try {
      await login(username, password);
      navigate('/', { replace: true });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Invalid credentials. Please verify your username and password.';
      setLocalError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickSelect = (user: DemoUser) => {
    setUsername(user.username);
    setPassword(user.password);
    setLocalError('');
    clearError();
  };

  const displayError = localError || authError;

  const displayedCredentials = activeTab === 'operational'
    ? ALL_DEMO_CREDENTIALS.filter((u) => u.category === 'operational')
    : ALL_DEMO_CREDENTIALS.filter((u) => u.category === 'legacy');

  return (
    <main className="min-h-screen bg-slate-50 flex flex-col justify-center py-10 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Decorative ambient background */}
      <div
        className="absolute top-1/4 left-1/3 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"
        aria-hidden="true"
      />
      <div
        className="absolute bottom-1/4 right-1/3 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none"
        aria-hidden="true"
      />

      <div className="sm:mx-auto sm:w-full sm:max-w-3xl z-10">
        {/* Brand Header */}
        <header className="flex justify-center items-center gap-3 mb-4">
          <div
            className="w-12 h-12 rounded-2xl bg-emerald-600 flex items-center justify-center font-black text-2xl text-white shadow-lg shadow-emerald-600/30"
            aria-hidden="true"
          >
            NC
          </div>
          <div>
            <h1 className="text-2xl font-black text-slate-900 tracking-wide">NAMMA CLINIC</h1>
            <p className="text-xs text-emerald-700 font-extrabold tracking-wider uppercase">
              Integrated Digital Healthcare Network
            </p>
          </div>
        </header>

        {/* Local Environment Notice */}
        <section
          aria-label="System Notice"
          className="bg-amber-50 border border-amber-200 rounded-xl p-3 mb-6 text-center shadow-xs"
        >
          <p className="text-xs font-bold text-amber-900">
            LOCAL LAPTOP EXECUTION • DEMO HEALTHCARE NETWORK • POSTGRESQL 16
          </p>
        </section>

        {/* Login Card */}
        <section
          aria-labelledby="login-heading"
          className="bg-white rounded-2xl p-6 sm:p-8 shadow-xl border border-slate-200 mb-6"
        >
          <h2 id="login-heading" className="text-lg font-bold text-slate-900 mb-4">
            Sign In to Clinical Console
          </h2>

          {displayError && (
            <div className="mb-4">
              <ErrorAlert
                title="Authentication Failed"
                message={displayError}
                onDismiss={() => {
                  setLocalError('');
                  clearError();
                }}
              />
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Username Input */}
              <div>
                <label htmlFor="login-username" className="block text-xs font-bold text-slate-700 mb-1">
                  Username <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <Shield
                    className="w-4 h-4 text-slate-400 absolute left-3 top-3.5 pointer-events-none"
                    aria-hidden="true"
                  />
                  <input
                    id="login-username"
                    name="username"
                    type="text"
                    autoComplete="username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    disabled={isSubmitting}
                    className="w-full pl-9 pr-4 py-2.5 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 text-sm font-medium focus:outline-none focus:border-emerald-600 focus-visible:ring-2 focus-visible:ring-emerald-500/20 disabled:bg-slate-100 disabled:cursor-not-allowed"
                    placeholder="Enter staff username"
                    required
                  />
                </div>
              </div>

              {/* Password Input */}
              <div>
                <label htmlFor="login-password" className="block text-xs font-bold text-slate-700 mb-1">
                  Password <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <KeyRound
                    className="w-4 h-4 text-slate-400 absolute left-3 top-3.5 pointer-events-none"
                    aria-hidden="true"
                  />
                  <input
                    id="login-password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={isSubmitting}
                    className="w-full pl-9 pr-10 py-2.5 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 text-sm font-medium focus:outline-none focus:border-emerald-600 focus-visible:ring-2 focus-visible:ring-emerald-500/20 disabled:bg-slate-100 disabled:cursor-not-allowed"
                    placeholder="Enter password"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((prev) => !prev)}
                    className="absolute right-3 top-3 text-slate-400 hover:text-slate-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 rounded p-0.5 cursor-pointer"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? (
                      <EyeOff className="w-4 h-4" aria-hidden="true" />
                    ) : (
                      <Eye className="w-4 h-4" aria-hidden="true" />
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-sm rounded-lg shadow-md transition cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 flex items-center justify-center gap-2"
            >
              {isSubmitting ? (
                'Authenticating...'
              ) : (
                <>
                  <UserCheck className="w-4 h-4" />
                  Sign In as {username || 'Selected User'}
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Credentials Matrix */}
          <div className="mt-8 pt-6 border-t border-slate-200">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center gap-1.5">
                <UserCheck className="w-4 h-4 text-emerald-600" aria-hidden="true" />
                Quick Select Demo Credentials
              </h3>

              {/* Category Filter Tabs */}
              <div className="inline-flex p-1 bg-slate-100 rounded-lg text-xs font-semibold">
                <button
                  type="button"
                  onClick={() => setActiveTab('operational')}
                  className={`px-3 py-1 rounded-md transition cursor-pointer ${
                    activeTab === 'operational'
                      ? 'bg-white text-emerald-800 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  All 8 Roles & Dual ({ALL_DEMO_CREDENTIALS.filter(u => u.category === 'operational').length})
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('legacy')}
                  className={`px-3 py-1 rounded-md transition cursor-pointer ${
                    activeTab === 'legacy'
                      ? 'bg-white text-emerald-800 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Legacy Dev Accounts ({ALL_DEMO_CREDENTIALS.filter(u => u.category === 'legacy').length})
                </button>
              </div>
            </div>

            <div
              role="group"
              aria-label="Demo Role Accounts"
              className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5"
            >
              {displayedCredentials.map((u) => {
                const isSelected = username === u.username;
                const IconComponent = u.icon;
                return (
                  <button
                    key={u.username}
                    type="button"
                    onClick={() => handleQuickSelect(u)}
                    className={`p-3 rounded-xl border text-left transition flex flex-col justify-between cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 relative ${
                      isSelected
                        ? 'bg-emerald-50/80 border-emerald-500 ring-2 ring-emerald-500/20 shadow-sm'
                        : 'bg-slate-50 border-slate-200 hover:bg-slate-100/80 hover:border-slate-300 text-slate-700'
                    }`}
                    aria-pressed={isSelected}
                  >
                    <div>
                      <div className="flex items-start justify-between gap-1 mb-1">
                        <div className="flex items-center gap-1.5 min-w-0">
                          <span className={`p-1 rounded-md ${u.accentColor}`}>
                            <IconComponent className="w-3.5 h-3.5" />
                          </span>
                          <span className="text-xs font-bold text-slate-900 truncate">
                            {u.role}
                          </span>
                        </div>
                        {isSelected && (
                          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                        )}
                      </div>

                      <div className="flex items-center gap-1.5 my-1.5 flex-wrap">
                        <span className="text-[10px] font-mono font-bold text-slate-800 bg-white border border-slate-200 px-1.5 py-0.5 rounded shadow-2xs">
                          {u.username}
                        </span>
                        <span className="text-[10px] font-mono text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                          {u.password}
                        </span>
                      </div>

                      <p className="text-[10px] text-slate-500 line-clamp-2 leading-relaxed">
                        {u.desc}
                      </p>
                    </div>

                    <div className="mt-2 pt-1.5 border-t border-slate-200/60 flex items-center justify-between text-[10px]">
                      <span className="font-semibold text-emerald-700">
                        {u.roleBadge}
                      </span>
                      <span className="text-slate-400 font-medium">Click to Fill</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
};

export default Login;
