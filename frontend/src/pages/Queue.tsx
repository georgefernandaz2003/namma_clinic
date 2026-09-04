import React, { useState, useEffect } from 'react';
import api from '../services/api';
import type { Visit } from '../types';
import { useAuth } from '../context/AuthContext';
import { Clock, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const Queue: React.FC = () => {
  const { activeFacility } = useAuth();
  const navigate = useNavigate();
  const [visits, setVisits] = useState<Visit[]>([]);

  const loadQueue = async () => {
    if (!activeFacility) return;
    try {
      const res = await api.get(`visits/?facility=${activeFacility.id}`);
      setVisits(res.data.results || res.data || []);
    } catch (e) {
      console.error('Failed to load queue', e);
    }
  };

  useEffect(() => {
    loadQueue();
  }, [activeFacility]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <Clock className="w-6 h-6 text-teal-600" />
          OPD Token Priority Queue Console
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Real-time patient flow status from Registration → Triage → Doctor → Pharmacy
        </p>
      </div>

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
    </div>
  );
};
