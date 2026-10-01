import React, { useState, useEffect } from 'react';
import api from '../services/api';
import type { Referral } from '../types';
import { useAuth } from '../context/AuthContext';
import { Share2, CheckCircle2, Stethoscope, RefreshCw, Repeat, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const Referrals: React.FC = () => {
  const { activeFacility, user } = useAuth();
  const navigate = useNavigate();
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [selectedReferral, setSelectedReferral] = useState<Referral | null>(null);

  // Specialist Response Form
  const [findings, setFindings] = useState('Coronary artery disease ruled out; mild LV dysfunction on Echocardiogram.');
  const [treatment, setTreatment] = useState('Adjusted antihypertensive therapy: Telmisartan 40mg + Hydrochlorothiazide 12.5mg.');
  const [advice, setAdvice] = useState('Return to Namma Clinic for weekly blood pressure monitoring. Review at Hub in 1 month.');
  const [submitting, setSubmitting] = useState(false);

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
    setSubmitting(true);

    try {
      await api.post(`referrals/${selectedReferral.id}/respond/`, {
        specialist_findings: findings,
        treatment_summary: treatment,
        return_advice: advice
      });
      alert(`Specialist feedback sent back to ${selectedReferral.source_facility_name}! Closed-loop referral completed.`);
      setSelectedReferral(null);
      loadData();
    } catch (e) {
      alert('Failed to save specialist referral response.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Share2 className="w-6 h-6 text-rose-600" />
            Cross-Facility Referral & Two-Way Specialist Continuum
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Two-way referral loop: Namma Clinic → Referral → Specialist → Feedback → Namma Clinic Follow-up
          </p>
        </div>

        <button
          onClick={loadData}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-bold text-xs rounded-xl shadow-xs transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Referral Queue</span>
        </button>
      </div>

      {/* Value Proposition Callout Banner */}
      <div className="bg-gradient-to-r from-rose-900 via-pink-900 to-slate-900 p-4 rounded-2xl text-white space-y-1 shadow-md">
        <div className="flex items-center gap-2 text-xs font-black uppercase tracking-wider text-rose-400">
          <Repeat className="w-4 h-4" />
          <span>Two-Way Closed-Loop Referral Model (Continuity of Care)</span>
        </div>
        <p className="text-xs text-rose-100 font-medium leading-relaxed">
          &ldquo;The Government model is not: Namma Clinic → send patient away. It is: <strong className="text-white">Namma Clinic → Referral → Specialist → Feedback → Namma Clinic Follow-up</strong> (Continuity of Care).&rdquo;
        </p>
      </div>

      {/* 4-Step Two-Way Visual Pipeline */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-200 bg-white shadow-xs space-y-3">
        <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-2">
          <Repeat className="w-4 h-4 text-rose-600" />
          Two-Way Referral Loop Flow Architecture
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-center text-xs">
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 space-y-1">
            <span className="font-mono text-[10px] font-bold block text-rose-600 uppercase">Stage 1</span>
            <span className="font-bold block text-xs">1. Primary Assessment</span>
            <span className="text-[10px] text-slate-500 block">Namma Clinic Doctor</span>
          </div>
          <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-900 space-y-1">
            <span className="font-mono text-[10px] font-bold block text-rose-600 uppercase">Stage 2</span>
            <span className="font-bold block text-xs">2. Specialist Referral</span>
            <span className="text-[10px] text-rose-700 block">Outbound to Hub</span>
          </div>
          <div className="p-3 rounded-xl bg-purple-50 border border-purple-200 text-purple-900 space-y-1">
            <span className="font-mono text-[10px] font-bold block text-purple-600 uppercase">Stage 3</span>
            <span className="font-bold block text-xs">3. Specialist Feedback</span>
            <span className="text-[10px] text-purple-700 block">Findings & Advice</span>
          </div>
          <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 space-y-1">
            <span className="font-mono text-[10px] font-bold block text-emerald-600 uppercase">Stage 4</span>
            <span className="font-bold block text-xs">4. Closed-Loop Follow-up</span>
            <span className="text-[10px] text-emerald-700 block">Return to Namma Clinic</span>
          </div>
        </div>
      </div>

      {/* Main Referral Table */}
      <div className="glass-panel rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-xs">
        <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
          <h2 className="text-sm font-bold text-slate-900">Active Cross-Facility Referrals Ledger</h2>
          <span className="px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-rose-100 text-rose-800 border border-rose-200">
            {referrals.length} Total Referrals
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
              <tr>
                <th className="p-4">Referral ID</th>
                <th className="p-4">Patient Name</th>
                <th className="p-4">Source Clinic → Destination Hub</th>
                <th className="p-4">Urgency</th>
                <th className="p-4">Reason / Service</th>
                <th className="p-4">Status</th>
                <th className="p-4">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {referrals.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-400 font-medium">
                    No active cross-facility referrals logged for this facility.
                  </td>
                </tr>
              ) : (
                referrals.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50/80 transition">
                    <td className="p-4 font-mono font-bold text-rose-700">{r.referral_id}</td>
                    <td className="p-4">
                      <span className="font-bold text-slate-900 block">{r.patient_name}</span>
                      <span className="text-[10px] text-slate-500 font-mono">{r.patient_mobile}</span>
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
                    <td className="p-4 text-slate-700 font-medium">{r.reason}</td>
                    <td className="p-4">
                      <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold ${
                        r.status === 'COMPLETED' ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' : 'bg-slate-100 text-slate-700 border border-slate-200'
                      }`}>
                        {r.status}
                      </span>
                    </td>
                    <td className="p-4">
                      {r.destination_facility === activeFacility?.id && r.status !== 'COMPLETED' && (user?.role === 'DOCTOR' || user?.role === 'HOSPITAL_ADMIN') ? (
                        <button
                          onClick={() => setSelectedReferral(r)}
                          className="px-3 py-1 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded-lg text-[10px] flex items-center gap-1 shadow-xs transition"
                        >
                          <Stethoscope className="w-3.5 h-3.5" /> Enter Specialist Feedback
                        </button>
                      ) : r.status === 'COMPLETED' ? (
                        <button
                          onClick={() => navigate(`/patients/${r.patient}`)}
                          className="text-emerald-700 font-bold text-[11px] flex items-center gap-1 hover:underline"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" /> Closed-Loop Synced
                        </button>
                      ) : (
                        <span className="text-slate-500 text-[11px] font-semibold">
                          {r.destination_facility === activeFacility?.id ? 'Pending Specialist Review' : 'Outbound to Hub'}
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Specialist Response Modal */}
      {selectedReferral && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 border border-slate-200 w-full max-w-lg space-y-4 shadow-xl text-xs">
            <div className="flex justify-between items-center pb-3 border-b border-slate-100">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Stethoscope className="w-4 h-4 text-rose-600" />
                Hospital Specialist Feedback for {selectedReferral.patient_name}
              </h2>
              <button onClick={() => setSelectedReferral(null)} className="text-slate-400 font-bold hover:text-slate-700">✕</button>
            </div>

            <form onSubmit={handleRespondReferral} className="space-y-3">
              <div className="bg-rose-50 p-3 rounded-xl border border-rose-100 space-y-1 text-[11px]">
                <div className="flex justify-between font-bold text-rose-900">
                  <span>Referral ID: {selectedReferral.referral_id}</span>
                  <span>Urgency: {selectedReferral.urgency}</span>
                </div>
                <div className="text-rose-700 font-medium">
                  Source: {selectedReferral.source_facility_name} → Destination: {selectedReferral.destination_facility_name}
                </div>
                <div className="text-slate-700 font-semibold pt-1">
                  Reason: {selectedReferral.reason}
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Specialist Clinical Findings *</label>
                <textarea
                  value={findings}
                  onChange={(e) => setFindings(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-rose-600"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Treatment / Procedures Done *</label>
                <textarea
                  value={treatment}
                  onChange={(e) => setTreatment(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-rose-600"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Return Advice to Namma Clinic (Continuity of Care) *</label>
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
                disabled={submitting}
                className="w-full py-2.5 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded-xl shadow-md transition flex items-center justify-center gap-1.5"
              >
                <CheckCircle2 className="w-4 h-4" />
                {submitting ? 'Sending Feedback...' : 'Send Feedback & Complete Two-Way Loop'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
