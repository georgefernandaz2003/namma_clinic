import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Smile } from 'lucide-react';

export const Wellness: React.FC = () => {
  const { activeFacility } = useAuth();
  const [sessions, setSessions] = useState<any[]>([]);

  const loadData = async () => {
    if (!activeFacility) return;
    try {
      const res = await api.get(`wellness/?facility=${activeFacility.id}`);
      setSessions(res.data.results || res.data || []);
    } catch (e) {
      console.error('Failed to load wellness sessions', e);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeFacility]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <Smile className="w-6 h-6 text-emerald-600" />
          Wellness & Health Promotion Sessions (Yoga / Meditation)
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Operational Guideline requirement: 8 sessions per month, AYUSH instructor register & Rs. 250 incentive tracking
        </p>
      </div>

      <div className="glass-panel rounded-2xl border border-slate-200 bg-white p-5 space-y-4 shadow-xs">
        <h2 className="text-sm font-bold text-slate-900">Monthly Yoga & Meditation Sessions Log</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          {sessions.map((s) => (
            <div key={s.id} className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
              <div className="flex justify-between items-start">
                <span className="font-bold text-slate-900 text-sm">{s.session_type}</span>
                <span className="text-[10px] font-mono text-emerald-700 font-bold">{s.session_date}</span>
              </div>
              <p className="text-slate-700 font-medium">Instructor: <strong className="text-slate-900">{s.instructor_name}</strong></p>
              <p className="text-slate-600">Venue: {s.venue} ({s.session_time})</p>
              <div className="flex justify-between items-center pt-2 border-t border-slate-200 text-[11px]">
                <span className="text-slate-600">Attendance: <strong className="text-emerald-700 font-bold">{s.participants_count} Citizens</strong></span>
                <span className="text-amber-800 font-bold font-mono">Incentive: ₹ {s.incentive_amount_rs}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
