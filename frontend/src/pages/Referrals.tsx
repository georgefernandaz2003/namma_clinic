import React, { useState, useEffect } from 'react';
import api from '../services/api';
import type { Referral } from '../types';
import { useAuth } from '../context/AuthContext';
import { Share2, CheckCircle2, Stethoscope } from 'lucide-react';

export const Referrals: React.FC = () => {
  const { activeFacility } = useAuth();
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [selectedReferral, setSelectedReferral] = useState<Referral | null>(null);

  // Response form
  const [findings, setFindings] = useState('Coronary artery disease ruled out; mild LV dysfunction.');
  const [treatment, setTreatment] = useState('Initiated Telmisartan 40mg + Hydrochlorothiazide 12.5mg.');
  const [advice, setAdvice] = useState('Return to Namma Clinic for weekly BP monitoring. Review in 1 month.');

  const loadData = async () => {
    if (!activeFacility) return;
    try {
      const res = await api.get(`referrals/?facility=${activeFacility.id}`);
      setReferrals(res.data.results || res.data || []);
    } catch (e) {
      console.error('Failed to load referrals', e);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeFacility]);

  const handleRespondReferral = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedReferral) return;

    try {
      await api.post(`referrals/${selectedReferral.id}/respond/`, {
        specialist_findings: findings,
        treatment_summary: treatment,
        return_advice: advice
      });
      alert('Specialist response recorded and sent back to origin clinic!');
      setSelectedReferral(null);
      loadData();
    } catch (e) {
      alert('Failed to save specialist referral response.');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <Share2 className="w-6 h-6 text-rose-600" />
          Cross-Facility Referral & Specialist Continuum
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Tracking patient referrals between Namma Clinics, UPHCs, and Main Hospital Specialist Hubs
        </p>
      </div>

      <div className="glass-panel rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-xs">
        <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
          <h2 className="text-sm font-bold text-slate-900">Active Referral Queue</h2>
          <button onClick={loadData} className="px-3 py-1 bg-white border border-slate-300 text-slate-700 text-xs font-bold rounded-lg hover:bg-slate-100">Refresh</button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
              <tr>
                <th className="p-4">Referral ID</th>
                <th className="p-4">Patient</th>
                <th className="p-4">Source → Destination</th>
                <th className="p-4">Urgency</th>
                <th className="p-4">Reason / Service</th>
                <th className="p-4">Status</th>
                <th className="p-4">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {referrals.map((r) => (
                <tr key={r.id} className="hover:bg-slate-50/80 transition">
                  <td className="p-4 font-mono font-bold text-rose-700">{r.referral_id}</td>
                  <td className="p-4">
                    <span className="font-bold text-slate-900 block">{r.patient_name}</span>
                    <span className="text-[10px] text-slate-500">{r.patient_mobile}</span>
                  </td>
                  <td className="p-4 text-slate-800">
                    <span className="font-semibold">{r.source_facility_name}</span>
                    <span className="text-rose-600 font-bold mx-1">→</span>
                    <span className="font-semibold">{r.destination_facility_name}</span>
                  </td>
                  <td className="p-4">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      r.urgency === 'EMERGENCY' ? 'bg-rose-100 text-rose-800 border border-rose-200' :
                      r.urgency === 'URGENT' ? 'bg-amber-100 text-amber-900 border border-amber-200' :
                      'bg-emerald-100 text-emerald-800 border border-emerald-200'
                    }`}>
                      {r.urgency}
                    </span>
                  </td>
                  <td className="p-4 text-slate-700">{r.reason}</td>
                  <td className="p-4">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
                      {r.status}
                    </span>
                  </td>
                  <td className="p-4">
                    {r.destination_facility === activeFacility?.id && r.status !== 'COMPLETED' ? (
                      <button
                        onClick={() => setSelectedReferral(r)}
                        className="px-2.5 py-1 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded text-[10px] flex items-center gap-1 shadow-xs"
                      >
                        <Stethoscope className="w-3 h-3" /> Specialist Response
                      </button>
                    ) : r.status === 'COMPLETED' ? (
                      <span className="text-emerald-700 font-bold text-[11px] flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Closed
                      </span>
                    ) : (
                      <span className="text-slate-400 text-[11px]">Outbound</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Specialist Response Modal */}
      {selectedReferral && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 border border-slate-200 w-full max-w-lg space-y-4 shadow-xl text-xs">
            <div className="flex justify-between items-center pb-3 border-b border-slate-100">
              <h2 className="text-sm font-bold text-slate-900">
                Hospital Specialist Response for {selectedReferral.patient_name}
              </h2>
              <button onClick={() => setSelectedReferral(null)} className="text-slate-400 font-bold">✕</button>
            </div>

            <form onSubmit={handleRespondReferral} className="space-y-3">
              <div>
                <label className="block text-slate-700 font-bold mb-1">Specialist Findings *</label>
                <textarea
                  value={findings}
                  onChange={(e) => setFindings(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-rose-600"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Treatment Rendered at Hospital Hub *</label>
                <textarea
                  value={treatment}
                  onChange={(e) => setTreatment(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-rose-600"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Return Advice for Namma Clinic MO *</label>
                <textarea
                  value={advice}
                  onChange={(e) => setAdvice(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-rose-600"
                  required
                />
              </div>

              <button
                type="submit"
                className="w-full py-2.5 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded-xl shadow-md transition"
              >
                Send Specialist Feedback & Complete Referral
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
