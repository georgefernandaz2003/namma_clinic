import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Users2, CheckCircle2 } from 'lucide-react';

export const ARS: React.FC = () => {
  const { activeFacility } = useAuth();
  const [meetings, setMeetings] = useState<any[]>([]);

  const loadData = async () => {
    if (!activeFacility) return;
    try {
      const res = await api.get(`ars/meetings/?facility=${activeFacility.id}`);
      setMeetings(res.data.results || res.data || []);
    } catch (e) {
      console.error('Failed to load ARS meetings', e);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeFacility]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <Users2 className="w-6 h-6 text-teal-600" />
          Arogya Raksha Samiti (ARS) Committee & Untied Grants
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Monthly committee meetings chaired by Ward Councillor/Corporator, signed proceedings, and untied grant expenditure
        </p>
      </div>

      <div className="glass-panel rounded-2xl border border-slate-200 bg-white p-5 space-y-4 shadow-xs">
        <h2 className="text-sm font-bold text-slate-900">Monthly ARS Meetings & Proceedings Register</h2>
        <div className="space-y-4 text-xs">
          {meetings.map((m) => (
            <div key={m.id} className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
              <div className="flex justify-between items-start">
                <div>
                  <span className="font-bold text-slate-900 text-sm">ARS Meeting - {m.meeting_date}</span>
                  <span className="text-slate-600 block text-[11px] font-medium">Chairperson: {m.chairperson_name} ({m.attendees_count} Members Present)</span>
                </div>
                <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Signed by Chairman
                </span>
              </div>

              <div className="space-y-1 bg-white p-3 rounded-lg border border-slate-200">
                <span className="font-bold text-slate-800">Agenda & Proceedings:</span>
                <p className="text-slate-600 text-[11px] font-medium">{m.proceedings_summary}</p>
              </div>

              <div className="flex justify-between items-center text-[11px] pt-1">
                <span className="text-slate-600">Action Plan Items: <strong className="text-slate-900">{m.action_items?.length ?? 0} Tasks Assigned</strong></span>
                <span className="text-emerald-700 font-bold font-mono">Untied Grant Approved: ₹ {m.untied_funds_spent_rs}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
