import React, { useState, useEffect } from 'react';
import api from '../services/api';
import type { Patient } from '../types';
import { useAuth } from '../context/AuthContext';
import { Users, Search, UserPlus, Clock, History, X, Activity, FileText, Pill, Share2, Stethoscope } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const Patients: React.FC = () => {
  const { activeFacility } = useAuth();
  const navigate = useNavigate();
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
  const [vulnerability, setVulnerability] = useState('Slum Resident / Low Income Group');
  const [customVulnerability, setCustomVulnerability] = useState('');
  const [registerForOpd, setRegisterForOpd] = useState(true);

  // Token Modal State
  const [showTokenModal, setShowTokenModal] = useState(false);
  const [targetPatient, setTargetPatient] = useState<Patient | null>(null);
  const [visitType, setVisitType] = useState('GENERAL_OPD');
  const [priority, setPriority] = useState('NORMAL');
  const [chiefComplaint, setChiefComplaint] = useState('');
  const [submittingToken, setSubmittingToken] = useState(false);

  // Timeline / History Modal State
  const [showTimelineModal, setShowTimelineModal] = useState(false);
  const [timelinePatient, setTimelinePatient] = useState<Patient | null>(null);
  const [timelineEvents, setTimelineEvents] = useState<any[]>([]);
  const [loadingTimeline, setLoadingTimeline] = useState(false);

  const loadPatients = async () => {
    try {
      const facQuery = activeFacility?.id ? `?facility=${activeFacility.id}` : '';
      const res = await api.get(`patients/${facQuery}`);
      setPatients(res.data.results || res.data || []);
    } catch (e) {
      console.error('Failed to load patients', e);
    }
  };

  useEffect(() => {
    loadPatients();
  }, [activeFacility]);

  const handleRegisterPatient = async (e: React.FormEvent) => {
    e.preventDefault();
    const finalVulnerability = vulnerability === 'OTHER'
      ? (customVulnerability.trim() || 'General / Non-Vulnerable')
      : vulnerability;

    try {
      const res = await api.post('patients/', {
        name,
        age: parseInt(age) || 30,
        gender,
        mobile,
        address,
        ABHA_ID_DEMO: abhaId || `ABHA-2026-${Math.floor(1000 + Math.random() * 9000)}`,
        vulnerability_information: finalVulnerability,
        registered_at_facility: activeFacility?.id
      });
      const newPat = res.data;

      if (registerForOpd && activeFacility) {
        try {
          const vRes = await api.post('visits/', {
            patient: newPat.id,
            facility: activeFacility.id,
            visit_type: 'GENERAL_OPD',
            priority: 'NORMAL',
            chief_complaint: 'Routine General OPD Checkup'
          });
          const vData = vRes.data;
          alert(`Patient '${newPat.name}' registered & OPD Token #${vData.token_details?.token_number || vData.id} issued successfully!`);
        } catch (vErr: any) {
          alert(`Patient '${newPat.name}' registered, but failed to issue OPD token: ${vErr.response?.data?.error || 'Error'}`);
        }
      } else {
        alert(`Patient '${newPat.name}' registered successfully!\nAssigned Patient ID: ${newPat.patient_id}`);
      }

      setShowRegisterModal(false);
      setName('');
      setAge('');
      setMobile('');
      setAddress('');
      setAbhaId('');
      setVulnerability('Slum Resident / Low Income Group');
      setCustomVulnerability('');
      loadPatients();
    } catch (e: any) {
      let msg = 'Failed to register patient.';
      if (e.response?.data?.error) {
        msg = e.response.data.error;
      } else if (e.response?.data?.detail) {
        msg = e.response.data.detail;
      } else if (e.response?.data && typeof e.response.data === 'object') {
        msg = Object.entries(e.response.data)
          .map(([k, v]) => `${k.toUpperCase()}: ${Array.isArray(v) ? v.join(', ') : v}`)
          .join('\n');
      }
      alert(msg);
    }
  };

  const handleIssueTokenSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetPatient || !activeFacility) return;
    setSubmittingToken(true);
    try {
      const res = await api.post('visits/', {
        patient: targetPatient.id,
        facility: activeFacility.id,
        visit_type: visitType,
        priority,
        chief_complaint: chiefComplaint
      });
      const newVisit = res.data;
      alert(`OPD Token #${newVisit.token_details?.token_number || newVisit.id} Issued for ${targetPatient.name}!`);
      setShowTokenModal(false);
      setChiefComplaint('');
      navigate('/queue');
    } catch (e: any) {
      alert(e.response?.data?.error || 'Failed to issue OPD token');
    } finally {
      setSubmittingToken(false);
    }
  };

  const openTimelineModal = async (p: Patient) => {
    setTimelinePatient(p);
    setShowTimelineModal(true);
    setLoadingTimeline(true);
    try {
      const res = await api.get(`patients/${p.id}/timeline/`);
      setTimelineEvents(res.data.timeline || []);
    } catch (e) {
      console.error('Failed to load patient timeline', e);
      setTimelineEvents([]);
    } finally {
      setLoadingTimeline(false);
    }
  };

  const filtered = patients.filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.patient_id.toLowerCase().includes(search.toLowerCase()) ||
      p.mobile.includes(search) ||
      (p.ABHA_ID_DEMO && p.ABHA_ID_DEMO.toLowerCase().includes(search.toLowerCase())) ||
      (p.vulnerability_information && p.vulnerability_information.toLowerCase().includes(search.toLowerCase()))
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
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((p) => (
                <tr
                  key={p.id}
                  onClick={() => navigate(`/patients/${p.id}`)}
                  className="hover:bg-blue-50/60 cursor-pointer transition group"
                  title="Click to view full patient EMR profile & history"
                >
                  <td className="p-4 font-mono font-bold text-emerald-700">{p.patient_id}</td>
                  <td className="p-4 font-bold text-slate-900 group-hover:text-blue-600 transition flex items-center gap-1.5">
                    <span>{p.name}</span>
                  </td>
                  <td className="p-4 text-slate-600">{p.age} yrs • {p.gender}</td>
                  <td className="p-4 font-mono text-slate-700">{p.mobile}</td>
                  <td className="p-4 font-mono text-slate-600">{p.ABHA_ID_DEMO || 'N/A'}</td>
                  <td className="p-4 text-slate-700">{p.facility_name || 'Namma Clinic'}</td>
                  <td className="p-4">
                    <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-200">
                      {p.vulnerability_information || 'General'}
                    </span>
                  </td>
                  <td className="p-4 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setTargetPatient(p);
                        setShowTokenModal(true);
                      }}
                      className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg text-xs inline-flex items-center gap-1 shadow-xs transition"
                    >
                      <Clock className="w-3.5 h-3.5" />
                      <span>Issue Token</span>
                    </button>
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
            <h2 className="text-base font-bold text-slate-900">Register New Patient</h2>

            <form onSubmit={handleRegisterPatient} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-700 font-bold mb-1">Patient Full Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Rajesh Gowda"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 focus:outline-none font-medium"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Age *</label>
                  <input
                    type="number"
                    required
                    placeholder="e.g. 35"
                    value={age}
                    onChange={(e) => setAge(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 focus:outline-none font-medium"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Gender *</label>
                  <select
                    value={gender}
                    onChange={(e: any) => setGender(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 focus:outline-none font-medium"
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
                    required
                    placeholder="10-digit mobile"
                    value={mobile}
                    onChange={(e) => setMobile(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 focus:outline-none font-medium"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-bold mb-1">ABHA ID (Optional)</label>
                  <input
                    type="text"
                    placeholder="ABHA-2026-XXXX"
                    value={abhaId}
                    onChange={(e) => setAbhaId(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 focus:outline-none font-medium"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Residential Address</label>
                <textarea
                  rows={2}
                  placeholder="Street / Slum Ward / Village address"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 focus:outline-none font-medium"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Vulnerability Flag *</label>
                <select
                  value={vulnerability}
                  onChange={(e) => setVulnerability(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 focus:outline-none font-medium"
                >
                  <option value="Slum Resident / Low Income Group">Slum Resident / Low Income Group</option>
                  <option value="Slum Household BPL">Slum Household BPL</option>
                  <option value="Urban Slum Resident BPL">Urban Slum Resident BPL</option>
                  <option value="Diabetic Elderly">Diabetic Elderly</option>
                  <option value="Senior Citizen / Diabetic">Senior Citizen / Diabetic</option>
                  <option value="Senior Citizen / Cardiac History">Senior Citizen / Cardiac History</option>
                  <option value="High Risk Pregnancy ANC">High Risk Pregnancy ANC</option>
                  <option value="Maternal ANC / Rural BPL">Maternal ANC / Rural BPL</option>
                  <option value="Hypertension / General BPL">Hypertension / General BPL</option>
                  <option value="Acute Febrile Illness / Slum BPL">Acute Febrile Illness / Slum BPL</option>
                  <option value="Migrant / Daily Wage Worker">Migrant / Daily Wage Worker</option>
                  <option value="Person with Disability (PwD)">Person with Disability (PwD)</option>
                  <option value="General / Non-Vulnerable">General / Non-Vulnerable</option>
                  <option value="OTHER">Other (Custom Vulnerability Flag)...</option>
                </select>
                {vulnerability === 'OTHER' && (
                  <input
                    type="text"
                    placeholder="Enter custom vulnerability flag..."
                    value={customVulnerability}
                    onChange={(e) => setCustomVulnerability(e.target.value)}
                    required
                    className="mt-2 w-full bg-white border border-amber-300 rounded-xl p-2.5 text-slate-900 focus:outline-none font-medium text-xs shadow-xs"
                  />
                )}
              </div>

              <label className="flex items-center gap-2 p-2.5 bg-emerald-50 rounded-xl border border-emerald-200 cursor-pointer">
                <input
                  type="checkbox"
                  checked={registerForOpd}
                  onChange={(e) => setRegisterForOpd(e.target.checked)}
                  className="w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500"
                />
                <span className="text-xs font-bold text-emerald-900">
                  Also register for Today's OPD (Issue Token & add to Queue)
                </span>
              </label>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowRegisterModal(false)}
                  className="px-4 py-2 border border-slate-300 text-slate-700 font-bold rounded-xl hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl shadow-sm"
                >
                  Register & Verify Duplicate Status
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Issue Token Modal */}
      {showTokenModal && targetPatient && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 border border-slate-200 w-full max-w-lg space-y-4 shadow-xl">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Clock className="w-5 h-5 text-emerald-600" />
                  Issue OPD Token for {targetPatient.name}
                </h2>
                <p className="text-xs text-slate-500 font-mono mt-0.5">
                  ID: {targetPatient.patient_id} • Mobile: {targetPatient.mobile}
                </p>
              </div>
              <button
                onClick={() => setShowTokenModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleIssueTokenSubmit} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Visit Type</label>
                  <select
                    value={visitType}
                    onChange={(e) => setVisitType(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 font-medium focus:outline-none"
                  >
                    <option value="GENERAL_OPD">General OPD</option>
                    <option value="NCD_SCREENING">NCD Screening</option>
                    <option value="MATERNAL_ANC">Maternal ANC</option>
                    <option value="CHILD_IMMUNIZATION">Child Immunization</option>
                    <option value="TELECONSULTATION">Teleconsultation</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-700 font-bold mb-1">Priority Tag</label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 font-medium focus:outline-none"
                  >
                    <option value="NORMAL">Normal / Routine</option>
                    <option value="HIGH">High Priority</option>
                    <option value="EMERGENCY">Emergency 🚨</option>
                    <option value="MATERNAL">Maternal ANC Care</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Chief Symptoms / Complaint</label>
                <input
                  type="text"
                  placeholder="e.g. Chest pain, Fever, Routine BP check"
                  value={chiefComplaint}
                  onChange={(e) => setChiefComplaint(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 font-medium focus:outline-none"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowTokenModal(false)}
                  className="px-4 py-2 border border-slate-300 text-slate-700 font-bold rounded-xl hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingToken}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl shadow-sm"
                >
                  {submittingToken ? 'Issuing...' : 'Issue Token & Add to Queue'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Longitudinal EMR Timeline Modal */}
      {showTimelineModal && timelinePatient && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 border border-slate-200 w-full max-w-2xl space-y-4 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <History className="w-5 h-5 text-blue-600" />
                  Longitudinal EMR Timeline & History
                </h2>
                <div className="text-xs text-slate-600 mt-1 space-x-2">
                  <span className="font-bold text-slate-900">{timelinePatient.name}</span>
                  <span>•</span>
                  <span className="font-mono text-emerald-700 font-bold">{timelinePatient.patient_id}</span>
                  <span>•</span>
                  <span>{timelinePatient.age} yrs, {timelinePatient.gender}</span>
                  <span>•</span>
                  <span className="font-mono">{timelinePatient.mobile}</span>
                </div>
                <div className="flex gap-2 mt-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-200">
                    Vulnerability Tag: {timelinePatient.vulnerability_information || 'General'}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-900 border border-blue-200 font-mono">
                    ABHA: {timelinePatient.ABHA_ID_DEMO || 'N/A'}
                  </span>
                </div>
              </div>
              <button
                onClick={() => setShowTimelineModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {loadingTimeline ? (
              <div className="p-8 text-center text-xs text-slate-400">Loading patient timeline history...</div>
            ) : timelineEvents.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400">No previous visit records found for this patient.</div>
            ) : (
              <div className="relative pl-6 space-y-4 border-l-2 border-slate-200 ml-2 py-2 text-xs">
                {timelineEvents.map((ev, idx) => (
                  <div key={idx} className="relative group">
                    <div className="absolute -left-[31px] top-1 p-1 bg-white border-2 border-blue-600 rounded-full text-blue-600 shadow-xs">
                      {ev.type === 'REGISTRATION' && <UserPlus className="w-3.5 h-3.5" />}
                      {ev.type === 'VISIT' && <Clock className="w-3.5 h-3.5" />}
                      {ev.type === 'TRIAGE' && <Activity className="w-3.5 h-3.5 text-rose-600" />}
                      {ev.type === 'CONSULTATION' && <Stethoscope className="w-3.5 h-3.5 text-indigo-600" />}
                      {ev.type === 'PRESCRIPTION' && <Pill className="w-3.5 h-3.5 text-amber-600" />}
                      {ev.type === 'LAB' && <FileText className="w-3.5 h-3.5 text-teal-600" />}
                      {ev.type === 'REFERRAL' && <Share2 className="w-3.5 h-3.5 text-rose-600" />}
                    </div>

                    <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-1 hover:bg-white transition">
                      <div className="flex justify-between items-center">
                        <span className="font-bold text-slate-900 text-xs">{ev.title}</span>
                        <span className="font-mono text-[10px] text-slate-500">{ev.date}</span>
                      </div>
                      <p className="text-[11px] text-slate-700 leading-relaxed">{ev.details}</p>
                      <span className="text-[10px] text-slate-400 font-semibold block">{ev.facility}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
