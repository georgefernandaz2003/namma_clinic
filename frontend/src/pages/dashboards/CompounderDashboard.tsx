import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import type { Patient, Visit } from '../../types';
import {
  Users, UserPlus, Search, Clock, CheckCircle2,
  AlertTriangle, RotateCcw, Building2, Ticket,
  UserCheck, ShieldAlert, ArrowRight, Ban
} from 'lucide-react';
import ErrorAlert from '../../components/common/ErrorAlert';

export const CompounderDashboard: React.FC = () => {
  const { user, activeFacility: authFacility } = useAuth();
  const activeFacility = authFacility || (user?.facility_details ? (user.facility_details as any) : (user?.assigned_facility ? { id: user.assigned_facility, facility_name: user.facility_name || 'Assigned Facility', facility_code: '' } : null));
  const navigate = useNavigate();

  // Data States
  const [patients, setPatients] = useState<Patient[]>([]);
  const [visits, setVisits] = useState<Visit[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Search State
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Register Modal State
  const [showRegisterModal, setShowRegisterModal] = useState<boolean>(false);
  const [regName, setRegName] = useState<string>('');
  const [regAge, setRegAge] = useState<string>('');
  const [regGender, setRegGender] = useState<'MALE' | 'FEMALE' | 'OTHER'>('MALE');
  const [regMobile, setRegMobile] = useState<string>('');
  const [regAddress, setRegAddress] = useState<string>('');
  const [regAbhaId, setRegAbhaId] = useState<string>('');
  const [regVulnerability, setRegVulnerability] = useState<string>('Slum Resident / Low Income Group');
  const [registering, setRegistering] = useState<boolean>(false);
  const [duplicateWarning, setDuplicateWarning] = useState<string | null>(null);

  // Token Modal State
  const [showTokenModal, setShowTokenModal] = useState<boolean>(false);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [visitType, setVisitType] = useState<string>('GENERAL_OPD');
  const [priority, setPriority] = useState<string>('NORMAL');
  const [submittingToken, setSubmittingToken] = useState<boolean>(false);

  // Void Token State
  const [voidingVisitId, setVoidingVisitId] = useState<number | null>(null);

  const loadDashboardData = useCallback(async (isManual = false) => {
    if (isManual) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const facQuery = activeFacility?.id ? `?facility=${activeFacility.id}` : '';
      const [patientsRes, visitsRes] = await Promise.all([
        api.get(`v1/patients/${facQuery}`),
        api.get(`v1/visits/${facQuery ? facQuery + '&date=today' : '?date=today'}`)
      ]);

      const pats = patientsRes.data.results || patientsRes.data || [];
      const vsts = visitsRes.data.results || visitsRes.data || [];

      setPatients(Array.isArray(pats) ? pats : []);
      setVisits(Array.isArray(vsts) ? vsts : []);
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Failed to load front-desk intake data.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [activeFacility]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  // Real-time duplicate check when entering mobile or name
  useEffect(() => {
    if (!regMobile.trim() && !regName.trim()) {
      setDuplicateWarning(null);
      return;
    }

    const trimmedMobile = regMobile.trim();
    const trimmedName = regName.trim().toLowerCase();

    const matches = patients.filter((p) => {
      const mobileMatch = trimmedMobile && p.mobile === trimmedMobile;
      const nameMatch = trimmedName && p.name.toLowerCase() === trimmedName;
      return mobileMatch || nameMatch;
    });

    if (matches.length > 0) {
      const first = matches[0];
      setDuplicateWarning(`Potential duplicate detected! Patient "${first.name}" (${first.patient_id}) already exists with mobile ${first.mobile}.`);
    } else {
      setDuplicateWarning(null);
    }
  }, [regMobile, regName, patients]);

  const handleRegisterPatient = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeFacility) {
      setError('Operational facility is required for patient intake.');
      return;
    }

    setRegistering(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const res = await api.post('v1/patients/', {
        name: regName.trim(),
        age: parseInt(regAge) || 30,
        gender: regGender,
        mobile: regMobile.trim(),
        address: regAddress.trim(),
        ABHA_ID_DEMO: regAbhaId.trim(),
        vulnerability_information: regVulnerability,
        registered_at_facility: activeFacility.id
      });

      const newPat = res.data;
      setSuccessMsg(`Patient '${newPat.name}' registered successfully! Assigned Patient ID: ${newPat.patient_id}`);
      setShowRegisterModal(false);
      setRegName('');
      setRegAge('');
      setRegMobile('');
      setRegAddress('');
      setRegAbhaId('');
      setDuplicateWarning(null);
      await loadDashboardData(true);
    } catch (err: any) {
      let msg = 'Failed to register patient.';
      if (err.response?.status === 409) {
        const dup = err.response.data?.existing_patient;
        if (dup) {
          msg = `Duplicate patient detected: "${dup.name}" (${dup.patient_id}) with mobile ${dup.mobile} is already registered at this facility.`;
          setDuplicateWarning(`Patient "${dup.name}" (${dup.patient_id}) already exists at this facility.`);
        } else {
          msg = err.response.data?.error || err.response.data?.detail || 'A patient with matching name and mobile already exists at this facility.';
          setDuplicateWarning(msg);
        }
      } else if (err.response?.data?.error) {
        msg = err.response.data.error;
      } else if (err.response?.data?.detail) {
        msg = err.response.data.detail;
      } else if (err.response?.data && typeof err.response.data === 'object') {
        msg = Object.entries(err.response.data)
          .map(([k, v]) => `${k.toUpperCase()}: ${Array.isArray(v) ? v.join(', ') : v}`)
          .join('; ');
      }
      setError(msg);
    } finally {
      setRegistering(false);
    }
  };

  const handleIssueToken = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPatient || !activeFacility) return;

    setSubmittingToken(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const res = await api.post('v1/visits/', {
        patient: selectedPatient.id,
        facility: activeFacility.id,
        visit_type: visitType,
        priority
      });

      const newVisit = res.data;
      const tokenNum = newVisit.token_number || newVisit.id;
      setSuccessMsg(`OPD Token #${tokenNum} issued for ${selectedPatient.name}! Added to live front desk queue.`);
      setShowTokenModal(false);
      setSelectedPatient(null);
      await loadDashboardData(true);
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Failed to issue OPD queue token.');
    } finally {
      setSubmittingToken(false);
    }
  };

  const handleVoidToken = async (visitId: number) => {
    if (!confirm('Are you sure you want to void this duplicate/erroneous OPD token?')) return;

    setVoidingVisitId(visitId);
    setError(null);
    setSuccessMsg(null);

    try {
      await api.delete(`v1/visits/${visitId}/`);
      setSuccessMsg(`OPD Token for visit #${visitId} voided successfully.`);
      await loadDashboardData(true);
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Failed to void OPD token.');
    } finally {
      setVoidingVisitId(null);
    }
  };

  // Filtered patients for search
  const filteredPatients = patients.filter((p) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    const nameMatch = (p.name || '').toLowerCase().includes(q);
    const idMatch = (p.patient_id || '').toLowerCase().includes(q);
    const mobMatch = (p.mobile || '').includes(q);
    const abhaMatch = (p.ABHA_ID_DEMO || '').toLowerCase().includes(q);
    return nameMatch || idMatch || mobMatch || abhaMatch;
  });

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Users className="w-6 h-6 text-emerald-600" />
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Front-Desk Patient Intake & OPD Registration
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
              Front Desk Console
            </span>
          </div>
          <p className="text-xs text-slate-500 font-medium">
            Patient demographic registration, duplicate warning check, OPD token generation, and front desk queue management
          </p>
          {activeFacility && (
            <div className="flex items-center gap-1.5 text-xs text-slate-600 font-medium pt-1">
              <Building2 className="w-3.5 h-3.5 text-slate-400" />
              <span>Assigned Facility:</span>
              <span className="font-bold text-slate-800">{activeFacility.facility_name}</span>
              <span className="text-slate-400 font-mono">[{activeFacility.facility_code}]</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowRegisterModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-xs transition cursor-pointer"
          >
            <UserPlus className="w-4 h-4" />
            <span>Register New Patient</span>
          </button>

          <button
            onClick={() => loadDashboardData(true)}
            disabled={loading || refreshing}
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-50 hover:bg-slate-100 text-slate-700 font-semibold text-xs rounded-xl border border-slate-200 transition cursor-pointer disabled:opacity-50"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
          </button>
        </div>
      </div>

      {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}
      {successMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 font-medium flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg(null)} className="text-emerald-700 font-bold hover:text-emerald-900 cursor-pointer">✕</button>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-600">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-medium">Registered Patients</div>
            <div className="text-xl font-black text-slate-900">{patients.length}</div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600">
            <Ticket className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-medium">Today's OPD Queue</div>
            <div className="text-xl font-black text-slate-900">{visits.length}</div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-purple-50 flex items-center justify-center text-purple-600">
            <UserCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-medium">Waiting for Triage</div>
            <div className="text-xl font-black text-slate-900">
              {visits.filter((v) => v.current_queue === 'TRIAGE' || v.status === 'WAITING' || v.status === 'REGISTERED').length}
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center text-amber-600">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-medium">Emergency / Priority</div>
            <div className="text-xl font-black text-slate-900">
              {visits.filter((v) => v.priority === 'EMERGENCY' || v.priority === 'HIGH').length}
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: Search & Register Left, Today's Queue Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Patient Directory Search */}
        <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-4 border-b border-slate-200 bg-slate-50/70 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Search className="w-4 h-4 text-emerald-600" />
              <h2 className="text-sm font-bold text-slate-900">
                Patient Search & Demographic Intake ({filteredPatients.length})
              </h2>
            </div>
            <div className="relative w-full sm:w-64">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search name, mobile, ABHA..."
                className="w-full pl-8 pr-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs placeholder:text-slate-400 focus:outline-none focus:border-emerald-600"
              />
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                <tr>
                  <th className="p-3">Patient ID</th>
                  <th className="p-3">Full Name</th>
                  <th className="p-3">Demographics</th>
                  <th className="p-3">Mobile</th>
                  <th className="p-3">ABHA ID</th>
                  <th className="p-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredPatients.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-6 text-center text-slate-400 italic">
                      No matching patients found. Use "Register New Patient" to create an intake record.
                    </td>
                  </tr>
                ) : (
                  filteredPatients.slice(0, 15).map((p) => (
                    <tr
                      key={p.id}
                      onClick={() => navigate(`/patients/${p.id}`)}
                      className="hover:bg-slate-50 cursor-pointer transition"
                      title="View front desk patient demographic profile"
                    >
                      <td className="p-3 font-mono font-bold text-emerald-700">{p.patient_id}</td>
                      <td className="p-3 font-bold text-slate-900">{p.name}</td>
                      <td className="p-3 text-slate-600">{p.age} yrs • {p.gender}</td>
                      <td className="p-3 font-mono text-slate-700">{p.mobile}</td>
                      <td className="p-3 font-mono text-slate-500">{p.ABHA_ID_DEMO || 'N/A'}</td>
                      <td className="p-3 text-right" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => {
                            setSelectedPatient(p);
                            setShowTokenModal(true);
                          }}
                          className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg text-[11px] inline-flex items-center gap-1 transition cursor-pointer"
                        >
                          <Ticket className="w-3 h-3" />
                          <span>Issue Token</span>
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: Today's OPD Queue */}
        <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-4 border-b border-slate-200 bg-slate-50/70 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-blue-600" />
              <h2 className="text-sm font-bold text-slate-900">
                Active OPD Front-Desk Queue ({visits.length})
              </h2>
            </div>
            <button
              onClick={() => navigate('/queue')}
              className="text-[11px] font-bold text-emerald-600 hover:text-emerald-700 flex items-center gap-1"
            >
              <span>Full Queue</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="divide-y divide-slate-100 max-h-[500px] overflow-y-auto">
            {visits.length === 0 ? (
              <div className="p-6 text-center text-slate-400 italic text-xs">
                No active OPD tokens issued today.
              </div>
            ) : (
              visits.map((v) => (
                <div key={v.id} className="p-3 hover:bg-slate-50/60 flex items-center justify-between gap-3 text-xs">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-black text-sm text-emerald-700">
                        #{v.token_number || v.id}
                      </span>
                      <span className="font-bold text-slate-900">
                        {v.patient_details?.name || `Patient #${v.patient}`}
                      </span>
                      <span className="font-mono text-[10px] text-slate-400">
                        [{v.patient_details?.uhid || v.visit_id || ''}]
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-500 flex items-center gap-2">
                      <span>Type: {v.visit_type}</span>
                      <span>•</span>
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700">
                        Queue: {v.current_queue || v.status}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {(v.status === 'REGISTERED' || v.status === 'WAITING' || v.current_queue === 'TRIAGE') && (
                      <button
                        onClick={() => handleVoidToken(v.id)}
                        disabled={voidingVisitId === v.id}
                        className="p-1 text-slate-400 hover:text-rose-600 transition cursor-pointer"
                        title="Void eligible duplicate token"
                      >
                        <Ban className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Register Modal */}
      {showRegisterModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 border border-slate-200 w-full max-w-lg space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <UserPlus className="w-4 h-4 text-emerald-600" />
                <span>Patient Front-Desk Registration</span>
              </h2>
              <button
                onClick={() => setShowRegisterModal(false)}
                className="text-slate-400 hover:text-slate-700 cursor-pointer"
              >
                ✕
              </button>
            </div>

            {duplicateWarning && (
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <div className="space-y-0.5">
                  <div className="font-bold">Duplicate Warning:</div>
                  <div>{duplicateWarning}</div>
                </div>
              </div>
            )}

            <form onSubmit={handleRegisterPatient} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-700 font-bold mb-1">Patient Full Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Ramesh Kumar"
                  value={regName}
                  onChange={(e) => setRegName(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 focus:outline-none focus:border-emerald-600 font-medium"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Age *</label>
                  <input
                    type="number"
                    required
                    min={0}
                    max={120}
                    placeholder="e.g. 35"
                    value={regAge}
                    onChange={(e) => setRegAge(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 focus:outline-none focus:border-emerald-600 font-medium"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Gender *</label>
                  <select
                    value={regGender}
                    onChange={(e: any) => setRegGender(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 focus:outline-none focus:border-emerald-600 font-medium"
                  >
                    <option value="MALE">Male</option>
                    <option value="FEMALE">Female</option>
                    <option value="OTHER">Other</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Mobile Number *</label>
                <input
                  type="tel"
                  required
                  placeholder="10-digit mobile number"
                  value={regMobile}
                  onChange={(e) => setRegMobile(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 focus:outline-none focus:border-emerald-600 font-medium font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Address / Locality</label>
                <input
                  type="text"
                  placeholder="Ward/Street/Area"
                  value={regAddress}
                  onChange={(e) => setRegAddress(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 focus:outline-none focus:border-emerald-600 font-medium"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">ABHA ID (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. 14-digit ABHA or health ID"
                  value={regAbhaId}
                  onChange={(e) => setRegAbhaId(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 focus:outline-none focus:border-emerald-600 font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Vulnerability Category</label>
                <select
                  value={regVulnerability}
                  onChange={(e) => setRegVulnerability(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 focus:outline-none focus:border-emerald-600 font-medium"
                >
                  <option value="Slum Resident / Low Income Group">Slum Resident / Low Income Group</option>
                  <option value="Daily Wage Laborer / BPL">Daily Wage Laborer / BPL</option>
                  <option value="Senior Citizen (BPL)">Senior Citizen (BPL)</option>
                  <option value="Pregnant Mother / High Risk">Pregnant Mother / High Risk</option>
                  <option value="None / General Citizen">None / General Citizen</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowRegisterModal(false)}
                  className="px-4 py-2 border border-slate-300 rounded-xl font-bold text-slate-600 hover:bg-slate-50 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={registering}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl shadow-xs cursor-pointer disabled:opacity-50"
                >
                  {registering ? 'Registering...' : 'Register Patient'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Issue Token Modal */}
      {showTokenModal && selectedPatient && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 border border-slate-200 w-full max-w-md space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Ticket className="w-4 h-4 text-emerald-600" />
                <span>Issue OPD Queue Token</span>
              </h2>
              <button
                onClick={() => {
                  setShowTokenModal(false);
                  setSelectedPatient(null);
                }}
                className="text-slate-400 hover:text-slate-700 cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="p-3 bg-slate-50 rounded-xl space-y-1 text-xs">
              <div className="font-bold text-slate-900">{selectedPatient.name}</div>
              <div className="text-slate-500 font-mono">Patient ID: {selectedPatient.patient_id}</div>
              <div className="text-slate-500">{selectedPatient.age} yrs • {selectedPatient.gender} • Mobile: {selectedPatient.mobile}</div>
            </div>

            <form onSubmit={handleIssueToken} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-700 font-bold mb-1">Visit Type *</label>
                <select
                  value={visitType}
                  onChange={(e) => setVisitType(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 focus:outline-none focus:border-emerald-600 font-medium"
                >
                  <option value="GENERAL_OPD">General OPD Consultation</option>
                  <option value="ANC_FOLLOWUP">Antenatal Care (ANC)</option>
                  <option value="NCD_SCREENING">NCD Chronic Care Screening</option>
                  <option value="IMMUNIZATION">Immunization / Child Health</option>
                  <option value="EMERGENCY">Emergency / Acute Triage</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Queue Priority</label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 focus:outline-none focus:border-emerald-600 font-medium"
                >
                  <option value="NORMAL">Normal OPD Flow</option>
                  <option value="URGENT">Urgent Care</option>
                  <option value="EMERGENCY">Emergency / Stat</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => {
                    setShowTokenModal(false);
                    setSelectedPatient(null);
                  }}
                  className="px-4 py-2 border border-slate-300 rounded-xl font-bold text-slate-600 hover:bg-slate-50 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingToken}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl shadow-xs cursor-pointer disabled:opacity-50"
                >
                  {submittingToken ? 'Issuing...' : 'Generate Token'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default CompounderDashboard;
