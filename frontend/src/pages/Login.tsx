import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Shield, KeyRound, UserCheck } from 'lucide-react';

const demoUsers = [
  { role: 'Super Admin', username: 'admin', password: 'admin123', desc: 'System Configuration & Network Admin' },
  { role: 'District Officer', username: 'district', password: 'district123', desc: 'District Health Office Dashboard' },
  { role: 'Hospital Admin', username: 'hospital', password: 'hospital123', desc: 'Main Hospital Specialist Hub' },
  { role: 'Doctor (Medical Officer)', username: 'doctor', password: 'doctor123', desc: 'Rural Clinic A4 OPD Queue & EMR' },
  { role: 'Staff Nurse', username: 'nurse', password: 'nurse123', desc: 'Registration & Triage Vitals' },
  { role: 'Lab Technician', username: 'lab', password: 'lab123', desc: 'Diagnostic Orders & Result Entry' },
  { role: 'Pharmacist', username: 'pharmacy', password: 'pharmacy123', desc: 'FEFO Dispensing & Stock Inventory' },
  { role: 'Public Health Officer', username: 'officer', password: 'officer123', desc: 'Surveillance & Disease Anomalies' }
];

export const Login: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('doctor');
  const [password, setPassword] = useState('doctor123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await login(username, password);
      navigate('/');
    } catch (err) {
      setError('Invalid username or password.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickSelect = (u: string, p: string) => {
    setUsername(u);
    setPassword(p);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 px-6 lg:px-8 relative overflow-hidden">
      {/* Background accents */}
      <div className="absolute top-1/4 left-1/3 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/3 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-xl z-10">
        <div className="flex justify-center items-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-2xl bg-emerald-600 flex items-center justify-center font-bold text-2xl text-white shadow-lg shadow-emerald-600/30">
            NC
          </div>
          <div>
            <h2 className="text-2xl font-black text-slate-900 tracking-wide">NAMMA CLINIC</h2>
            <p className="text-xs text-emerald-700 font-extrabold tracking-wider uppercase">Integrated Digital Healthcare Network</p>
          </div>
        </div>

        <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 mb-6 text-center shadow-xs">
          <p className="text-xs font-bold text-amber-900">
            DEMO SYSTEM ONLY • FICTIONAL DATA • LOCAL EXECUTION
          </p>
        </div>

        <div className="bg-white rounded-2xl p-8 shadow-xl border border-slate-200">
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Username</label>
              <div className="relative">
                <Shield className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full pl-9 pr-4 py-2.5 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 text-sm focus:outline-none focus:border-emerald-600 font-medium"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Password</label>
              <div className="relative">
                <KeyRound className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-9 pr-4 py-2.5 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 text-sm focus:outline-none focus:border-emerald-600 font-medium"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-sm rounded-lg shadow-md transition"
            >
              {loading ? 'Authenticating...' : 'Sign In to Demo Console'}
            </button>
          </form>

          {/* Quick Demo Credentials Matrix */}
          <div className="mt-8 pt-6 border-t border-slate-200">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-1.5">
              <UserCheck className="w-4 h-4 text-emerald-600" />
              Quick Select Demo Credentials
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {demoUsers.map((u) => (
                <button
                  key={u.username}
                  type="button"
                  onClick={() => handleQuickSelect(u.username, u.password)}
                  className={`p-2.5 rounded-lg border text-left transition flex flex-col justify-between ${
                    username === u.username
                      ? 'bg-emerald-50 border-emerald-500 text-emerald-900'
                      : 'bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-700'
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold">{u.role}</span>
                    <span className="text-[10px] font-mono font-semibold text-emerald-700">{u.username}</span>
                  </div>
                  <span className="text-[10px] text-slate-500 truncate">{u.desc}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
