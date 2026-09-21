import React, { useState, useEffect } from 'react';
import api from '../services/api';
import type { FollowUp } from '../types';
import { useAuth } from '../context/AuthContext';
import { CalendarCheck } from 'lucide-react';

export const FollowUps: React.FC = () => {
  const { activeFacility } = useAuth();
  const [followups, setFollowups] = useState<FollowUp[]>([]);

  const loadData = async () => {
    if (!activeFacility) return;
    try {
      const res = await api.get(`followups/?facility=${activeFacility.id}`);
      setFollowups(res.data.results || res.data || []);
    } catch (e) {
      console.error('Failed to load followups', e);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeFacility]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <CalendarCheck className="w-6 h-6 text-emerald-600" />
          Patient Follow-up & Care Continuity Tracker
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Tracking overdue, due today, and scheduled follow-up visits across NCD and Referral cases
        </p>
      </div>

      <div className="glass-panel rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-xs">
        <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
          <h2 className="text-sm font-bold text-slate-900">Scheduled Follow-ups List</h2>
          <button onClick={loadData} className="px-3 py-1 bg-white border border-slate-300 text-slate-700 text-xs font-bold rounded-lg hover:bg-slate-100">Refresh</button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
              <tr>
                <th className="p-4">Patient Name</th>
                <th className="p-4">Category</th>
                <th className="p-4">Due Date</th>
                <th className="p-4">Status</th>
                <th className="p-4">Clinical Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {followups.map((f) => (
                <tr key={f.id} className="hover:bg-slate-50/80 transition">
                  <td className="p-4 font-bold text-slate-900">{f.patient_name}</td>
                  <td className="p-4">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-800 border border-slate-200">
                      {f.category}
                    </span>
                  </td>
                  <td className="p-4 font-mono text-slate-700">{f.due_date}</td>
                  <td className="p-4">
                    <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold ${
                      f.status === 'COMPLETED' ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' : 'bg-amber-100 text-amber-900 border border-amber-200'
                    }`}>
                      {f.status}
                    </span>
                  </td>
                  <td className="p-4 text-slate-600 max-w-xs truncate">{f.notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
