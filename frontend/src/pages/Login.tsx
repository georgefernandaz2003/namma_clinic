import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Shield, KeyRound, UserCheck, Eye, EyeOff } from 'lucide-react';
import ErrorAlert from '../components/common/ErrorAlert';

interface DemoUser {
  role: string;
  roleBadge: string;
  username: string;
  password: string;
  desc: string;
}

const LOCAL_DEMO_USERS: DemoUser[] = [
  {
    role: 'Medical Officer',
    roleBadge: 'DOCTOR',
    username: 'localdoc',
    password: 'DoctorPassword123!',
    desc: 'Clinical consults, triage review, OPD prescriptions',
  },
  {
    role: 'Staff Nurse',
    roleBadge: 'NURSE',
    username: 'localnurse',
    password: 'NursePassword123!',
    desc: 'Patient intake registration & vitals triage recording',
  },
  {
    role: 'Pharmacist',
    roleBadge: 'PHARMACIST',
    username: 'localpharm',
    password: 'PharmPassword123!',
    desc: 'Prescription verification & inventory dispensation',
  },
  {
    role: 'Hospital Admin',
    roleBadge: 'HOSPITAL_ADMIN',
    username: 'testadmin',
    password: 'AdminPassword123!',
    desc: 'Facility configuration, procurement approval & audit logs',
  },
  {
    role: 'Lab Technician',
    roleBadge: 'LAB_TECHNICIAN',
    username: 'locallab',
    password: 'LabPassword123!',
    desc: 'Diagnostic order processing & specimen test results',
  },
  {
    role: 'District Officer',
    roleBadge: 'DISTRICT_OFFICER',
    username: 'localdistrict',
    password: 'DistrictPassword123!',
    desc: 'District-wide healthcare network monitoring & surveillance',
  },
];

export const Login: React.FC = () => {
  const { login, error: authError, clearError } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState('localdoc');
  const [password, setPassword] = useState('DoctorPassword123!');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [localError, setLocalError] = useState('');

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

      <div className="sm:mx-auto sm:w-full sm:max-w-xl z-10">
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
          className="bg-white rounded-2xl p-6 sm:p-8 shadow-xl border border-slate-200"
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

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-sm rounded-lg shadow-md transition cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2"
            >
              {isSubmitting ? 'Authenticating...' : 'Sign In to Console'}
            </button>
          </form>

          {/* Quick Demo Credentials Matrix */}
          <div className="mt-8 pt-6 border-t border-slate-200">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-1.5">
              <UserCheck className="w-4 h-4 text-emerald-600" aria-hidden="true" />
              Quick Select Demo Credentials (6 Roles Matrix)
            </h3>
            <div
              role="group"
              aria-label="Demo Role Accounts"
              className="grid grid-cols-1 sm:grid-cols-2 gap-2"
            >
              {LOCAL_DEMO_USERS.map((u) => {
                const isSelected = username === u.username;
                return (
                  <button
                    key={u.username}
                    type="button"
                    onClick={() => handleQuickSelect(u)}
                    className={`p-2.5 rounded-lg border text-left transition flex flex-col justify-between cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 ${
                      isSelected
                        ? 'bg-emerald-50 border-emerald-500 text-emerald-900 shadow-xs'
                        : 'bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-700'
                    }`}
                    aria-pressed={isSelected}
                  >
                    <div className="flex justify-between items-center w-full">
                      <span className="text-xs font-bold text-slate-900">{u.role}</span>
                      <span className="text-[10px] font-mono font-semibold text-emerald-700 bg-emerald-100/60 px-1.5 py-0.5 rounded">
                        {u.username}
                      </span>
                    </div>
                    <span className="text-[10px] text-slate-500 truncate mt-1 block">
                      {u.desc}
                    </span>
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
