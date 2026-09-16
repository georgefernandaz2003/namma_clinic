import React, { useState, useEffect } from 'react';
import api from '../services/api';
import type { Visit, Patient } from '../types';
import { useAuth } from '../context/AuthContext';
import { Clock, ArrowRight, Plus, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const Queue: React.FC = () => {
  const { activeFacility } = useAuth();
  const navigate = useNavigate();
  const [visits, setVisits] = useState<Visit[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [showTokenModal, setShowTokenModal] = useState(false);

  // Form State
  const [selectedPatientId, setSelectedPatientId] = useState<number | string>('');
  const [visitType, setVisitType] = useState('GENERAL_OPD');
  const [priority, setPriority] = useState('NORMAL');
  const [chiefComplaint, setChiefComplaint] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadQueue = async () => {
    if (!activeFacility) return;
    try {
      const res = await api.get(`visits/?facility=${activeFacility.id}`);
      setVisits(res.data.results || res.data || []);
    } catch (e) {
      console.error('Failed to load queue', e);
    }
  };

  const loadPatients = async () => {
    try {
      const res = await api.get('patients/');
      const patList = res.data.results || res.data || [];
      setPatients(patList);
      if (patList.length > 0 && !selectedPatientId) {
        setSelectedPatientId(patList[0].id);
      }
    } catch (e) {
      console.error('Failed to load patients', e);
    }
  };

  useEffect(() => {
    loadQueue();
    loadPatients();
  }, [activeFacility]);

  const handleIssueToken = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPatientId || !activeFacility) {
      alert('Please select a patient and facility');
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post('visits/', {
        patient: selectedPatientId,
        facility: activeFacility.id,
        visit_type: visitType,
        priority,
        chief_complaint: chiefComplaint
      });
      const newVisit = res.data;
      alert(`OPD Token #${newVisit.token_details?.token_number || newVisit.id} Issued Successfully!\nAdded to OPD Queue.`);
      setShowTokenModal(false);
      setChiefComplaint('');
      loadQueue();
    } catch (e: any) {
      let msg = 'Failed to issue OPD Token.';
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
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Clock className="w-6 h-6 text-teal-600" />
            OPD Token Priority Queue Console
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time patient flow status from Registration → Triage → Doctor → Pharmacy
          </p>
        </div>

        <button
          onClick={() => {
            loadPatients();
            setShowTokenModal(true);
          }}
          className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-sm transition"
        >
          <Plus className="w-4 h-4" />
          <span>Issue New OPD Token</span>
        </button>
      </div>

      {/* Value Proposition Callout Banner */}
      <div className="bg-gradient-to-r from-teal-900 via-emerald-900 to-slate-900 p-4 rounded-2xl text-white space-y-1 shadow-md">
        <div className="flex items-center gap-2 text-xs font-black uppercase tracking-wider text-emerald-400">
          <span>⚡ Smart Patient Flow Control</span>
        </div>
        <p className="text-xs text-emerald-100 font-medium leading-relaxed">
          &ldquo;The system isn&apos;t just registering the citizen. It controls the patient flow through the clinic from registration → triage → doctor → pharmacy with automatic priority triage for emergency, elderly, and maternal patients.&rdquo;
        </p>
      </div>

      {/* Queue Table Panel */}
      <div className="glass-panel rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-xs">
        <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
          <h2 className="text-sm font-bold text-slate-900">Today Patient Tokens</h2>
          <button onClick={loadQueue} className="px-3 py-1 bg-white border border-slate-300 text-slate-700 text-xs font-bold rounded-lg hover:bg-slate-100">Refresh Queue</button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
              <tr>
                <th className="p-4">Token #</th>
                <th className="p-4">Patient Name</th>
                <th className="p-4">Visit Type</th>
                <th className="p-4">Priority Tag</th>
                <th className="p-4">Workflow Status</th>
                <th className="p-4">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {visits.map((v) => (
                <tr key={v.id} className="hover:bg-slate-50/80 transition">
                  <td className="p-4 font-mono font-black text-base text-emerald-700">
                    #{v.token_details?.token_number || v.id}
                  </td>
                  <td className="p-4">
                    <span className="font-bold text-slate-900 block">{v.patient_details?.name}</span>
                    <span className="text-[10px] text-slate-500">{v.patient_details?.age} yrs • {v.patient_details?.mobile}</span>
                  </td>
                  <td className="p-4 text-slate-700 font-semibold">{v.visit_type}</td>
                  <td className="p-4">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      v.token_details?.priority === 'EMERGENCY' ? 'bg-rose-100 text-rose-800 border border-rose-200' :
                      v.token_details?.priority === 'HIGH' ? 'bg-amber-100 text-amber-800 border border-amber-200' :
                      v.token_details?.priority === 'MATERNAL' ? 'bg-purple-100 text-purple-800 border border-purple-200' :
                      'bg-emerald-100 text-emerald-800 border border-emerald-200'
                    }`}>
                      {v.token_details?.priority || 'NORMAL'}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
                      {v.status}
                    </span>
                  </td>
                  <td className="p-4">
                    {v.status === 'WAITING' ? (
                      <button
                        onClick={() => navigate('/triage', { state: { visitId: v.id } })}
                        className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded text-xs flex items-center gap-1 shadow-xs"
                      >
                        <span>Triage</span> <ArrowRight className="w-3 h-3" />
                      </button>
                    ) : v.status === 'TRIAGED' ? (
                      <button
                        onClick={() => navigate('/consultation', { state: { visitId: v.id } })}
                        className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded text-xs flex items-center gap-1 shadow-xs"
                      >
                        <span>Consult</span> <ArrowRight className="w-3 h-3" />
                      </button>
                    ) : (
                      <span className="text-slate-400 font-semibold">Done</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Issue Token Modal */}
      {showTokenModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 border border-slate-200 w-full max-w-lg space-y-4 shadow-xl">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Clock className="w-5 h-5 text-emerald-600" />
                Issue OPD Queue Token
              </h2>
              <button
                onClick={() => setShowTokenModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleIssueToken} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-700 font-bold mb-1">Select Registered Patient *</label>
                <select
                  value={selectedPatientId}
                  onChange={(e) => setSelectedPatientId(e.target.value)}
                  required
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-slate-900 font-medium focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                >
                  <option value="">-- Choose Patient --</option>
                  {patients.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.patient_id}) - {p.mobile}
                    </option>
                  ))}
                </select>
              </div>

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
                  placeholder="e.g. Fever, Headache, High Blood Pressure check"
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
                  disabled={submitting}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl shadow-sm"
                >
                  {submitting ? 'Issuing...' : 'Issue Token & Add to Queue'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
