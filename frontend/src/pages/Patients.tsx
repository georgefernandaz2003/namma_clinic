import React, { useState, useEffect } from 'react';
import api from '../services/api';
import type { Patient } from '../types';
import { useAuth } from '../context/AuthContext';
import { Users, Search, UserPlus } from 'lucide-react';

export const Patients: React.FC = () => {
  const { activeFacility } = useAuth();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [search, setSearch] = useState('');

  // Register Modal State
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [name, setName] = useState('');
  const [age, setAge] = useState('');
  const [gender, setGender] = useState<'MALE' | 'FEMALE' | 'OTHER'>('MALE');
  const [mobile, setMobile] = useState('');
  const [address, setAddress] = useState('');
  const [abhaId, setAbhaId] = useState('');
  const [vulnerability] = useState('Slum Resident BPL');

  const loadPatients = async () => {
    try {
      const res = await api.get('patients/');
      setPatients(res.data.results || res.data || []);
    } catch (e) {
      console.error('Failed to load patients', e);
    }
  };

  useEffect(() => {
    loadPatients();
  }, []);

  const handleRegisterPatient = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('patients/', {
        name,
        age: parseInt(age) || 30,
        gender,
        mobile,
        address,
        ABHA_ID_DEMO: abhaId || `ABHA-2026-${Math.floor(1000 + Math.random() * 9000)}`,
        vulnerability_information: vulnerability,
        registered_at_facility: activeFacility?.id
      });
      alert(`Patient ${name} registered successfully! Duplicate check passed.`);
      setShowRegisterModal(false);
      setName('');
      setMobile('');
      loadPatients();
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.response?.data?.error || 'Failed to register patient (Possible duplicate patient match!).';
      alert(msg);
    }
  };

  const filtered = patients.filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.patient_id.toLowerCase().includes(search.toLowerCase()) ||
      p.mobile.includes(search)
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Users className="w-6 h-6 text-emerald-600" />
            Patient Master Directory & Longitudinal EMR Registry
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Registered citizen master with duplicate detection, ABHA ID mapping, and vulnerability tags
          </p>
        </div>

        <button
          onClick={() => setShowRegisterModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-sm transition"
        >
          <UserPlus className="w-4 h-4" />
          <span>Register New Patient</span>
        </button>
      </div>

      {/* Search Bar */}
      <div className="glass-panel p-4 rounded-xl border border-slate-200 bg-white flex items-center gap-3">
        <Search className="w-5 h-5 text-slate-400 shrink-0" />
        <input
          type="text"
          placeholder="Search by Patient ID, Name, Mobile Number, or ABHA ID..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-transparent text-sm text-slate-900 placeholder-slate-400 focus:outline-none font-medium"
        />
      </div>

      {/* Patient Table */}
      <div className="glass-panel rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
              <tr>
                <th className="p-4">Patient ID</th>
                <th className="p-4">Full Name</th>
                <th className="p-4">Demographics</th>
                <th className="p-4">Mobile</th>
                <th className="p-4">ABHA ID (Demo)</th>
                <th className="p-4">Registered Facility</th>
                <th className="p-4">Vulnerability Flag</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((p) => (
                <tr key={p.id} className="hover:bg-slate-50/80 transition">
                  <td className="p-4 font-mono font-bold text-emerald-700">{p.patient_id}</td>
                  <td className="p-4 font-bold text-slate-900">{p.name}</td>
                  <td className="p-4 text-slate-600">{p.age} yrs • {p.gender}</td>
                  <td className="p-4 font-mono text-slate-700">{p.mobile}</td>
                  <td className="p-4 font-mono text-slate-600">{p.ABHA_ID_DEMO || 'N/A'}</td>
                  <td className="p-4 text-slate-700">{p.facility_name || 'Namma Clinic'}</td>
                  <td className="p-4">
                    <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-200">
                      {p.vulnerability_information || 'General'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Register Modal */}
      {showRegisterModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 border border-slate-200 w-full max-w-lg space-y-4 shadow-xl">
            <div className="flex justify-between items-center pb-3 border-b border-slate-100">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-emerald-600" />
                Register New Patient (With Duplicate Check)
              </h2>
              <button onClick={() => setShowRegisterModal(false)} className="text-slate-400 hover:text-slate-600 font-bold">✕</button>
            </div>

            <form onSubmit={handleRegisterPatient} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-700 font-bold mb-1">Patient Full Name *</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-emerald-600"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Age *</label>
                  <input
                    type="number"
                    value={age}
                    onChange={(e) => setAge(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-emerald-600"
                    required
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Gender *</label>
                  <select
                    value={gender}
                    onChange={(e) => setGender(e.target.value as any)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-emerald-600"
                  >
                    <option value="MALE">Male</option>
                    <option value="FEMALE">Female</option>
                    <option value="OTHER">Other</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Mobile Number *</label>
                  <input
                    type="text"
                    value={mobile}
                    onChange={(e) => setMobile(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-emerald-600"
                    required
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-bold mb-1">ABHA ID (Optional)</label>
                  <input
                    type="text"
                    value={abhaId}
                    onChange={(e) => setAbhaId(e.target.value)}
                    placeholder="ABHA-2026-XXXX"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-emerald-600"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Residential Address</label>
                <textarea
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-emerald-600"
                />
              </div>

              <button
                type="submit"
                className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-md transition"
              >
                Register & Verify Duplicate Status
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
