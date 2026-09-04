import React, { useState, useEffect } from 'react';
import api from '../services/api';
import type { OutreachActivity } from '../types';
import { useAuth } from '../context/AuthContext';
import { MapPin } from 'lucide-react';

export const Outreach: React.FC = () => {
  const { activeFacility } = useAuth();
  const [activities, setActivities] = useState<OutreachActivity[]>([]);

  const loadData = async () => {
    if (!activeFacility) return;
    try {
      const res = await api.get(`outreach/?facility=${activeFacility.id}`);
      setActivities(res.data.results || res.data || []);
    } catch (e) {
      console.error('Failed to load outreach activities', e);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeFacility]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <MapPin className="w-6 h-6 text-teal-600" />
          Community Outreach & Slum Population Health Register
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Household surveys, vulnerable population screening camps, and ASHA field activities
        </p>
      </div>

      <div className="glass-panel rounded-2xl border border-slate-200 bg-white p-5 space-y-4 shadow-xs">
        <h2 className="text-sm font-bold text-slate-900">Outreach Activities & Health Camps Log</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          {activities.map((a) => (
            <div key={a.id} className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
              <div className="flex justify-between items-start">
                <span className="font-bold text-slate-900 text-sm">{a.activity_type}</span>
                <span className="text-[10px] font-mono text-emerald-700 font-bold">{a.activity_date}</span>
              </div>
              <p className="text-slate-600 font-medium">Conducted By: {a.conducted_by}</p>
              <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-200 text-[11px]">
                <div><span className="text-slate-500 block font-semibold">Households</span><span className="font-bold text-slate-900">{a.households_covered}</span></div>
                <div><span className="text-slate-500 block font-semibold">Screened</span><span className="font-bold text-emerald-700">{a.persons_screened}</span></div>
                <div><span className="text-slate-500 block font-semibold">Vulnerable</span><span className="font-bold text-amber-700">{a.vulnerable_identified}</span></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
