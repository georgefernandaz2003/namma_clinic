import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, Trash2, Award } from 'lucide-react';

export const Quality: React.FC = () => {
  const { activeFacility } = useAuth();
  const [checklists, setChecklists] = useState<any[]>([]);
  const [wasteLogs, setWasteLogs] = useState<any[]>([]);

  const loadData = async () => {
    if (!activeFacility) return;
    try {
      const cRes = await api.get(`quality/checklists/?facility=${activeFacility.id}`);
      setChecklists(cRes.data.results || cRes.data || []);

      const wRes = await api.get(`quality/waste-logs/?facility=${activeFacility.id}`);
      setWasteLogs(wRes.data.results || wRes.data || []);
    } catch (e) {
      console.error('Failed to load quality logs', e);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeFacility]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <ShieldCheck className="w-6 h-6 text-emerald-600" />
          Kayakalpa Quality Assurance & Bio-Medical Waste Log
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Infection control checklists, Kayakalpa scorecards, and CBWTF bio-medical waste segregation logs
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-panel p-5 rounded-2xl border border-slate-200 bg-white space-y-3 shadow-xs">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2 pb-2 border-b border-slate-100">
            <Award className="w-4 h-4 text-emerald-600" />
            Kayakalpa Quality & Infection Control Audit
          </h2>
          {checklists.map((c) => (
            <div key={c.id} className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2 text-xs">
              <div className="flex justify-between items-center">
                <span className="font-bold text-slate-900">Kayakalpa Cleanliness Score</span>
                <span className="text-sm font-bold text-emerald-700 font-mono">{c.cleanliness_score} %</span>
              </div>
              <p className="text-slate-600 font-medium">Infection Control: Passed • Audit Status: {c.kayakalpa_audit_status}</p>
            </div>
          ))}
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-200 bg-white space-y-3 shadow-xs">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2 pb-2 border-b border-slate-100">
            <Trash2 className="w-4 h-4 text-rose-600" />
            Bio-Medical Waste Handover Log
          </h2>
          {wasteLogs.map((w) => (
            <div key={w.id} className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2 text-xs">
              <div className="flex justify-between items-center">
                <span className="font-bold text-slate-900">Waste Handover Date: {w.date}</span>
                <span className="text-[10px] text-slate-500 font-semibold">{w.disposal_agency}</span>
              </div>
              <div className="grid grid-cols-4 gap-2 text-[10px] font-mono font-bold pt-1 text-slate-800">
                <div className="bg-amber-100 text-amber-900 p-1.5 rounded border border-amber-200">Yellow: {w.yellow_bag_kg} kg</div>
                <div className="bg-rose-100 text-rose-900 p-1.5 rounded border border-rose-200">Red: {w.red_bag_kg} kg</div>
                <div className="bg-slate-200 text-slate-900 p-1.5 rounded border border-slate-300">Sharps: {w.white_translucent_sharp_kg} kg</div>
                <div className="bg-blue-100 text-blue-900 p-1.5 rounded border border-blue-200">Blue: {w.blue_box_glass_kg} kg</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
