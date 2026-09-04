import React, { useState, useEffect } from 'react';
import api from '../services/api';
import type { DiseaseCase } from '../types';
import { useAuth } from '../context/AuthContext';
import { Radio, AlertTriangle } from 'lucide-react';

export const Surveillance: React.FC = () => {
  const { activeFacility } = useAuth();
  const [cases, setCases] = useState<DiseaseCase[]>([]);

  const loadData = async () => {
    if (!activeFacility) return;
    try {
      const res = await api.get(`surveillance/?facility=${activeFacility.id}`);
      setCases(res.data.results || res.data || []);
    } catch (e) {
      console.error('Failed to load surveillance data', e);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeFacility]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <Radio className="w-6 h-6 text-red-600" />
          Public Health Communicable Disease Surveillance
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Real-time tracking of Pyrexia, Dengue, Gastroenteritis, and Ward-level epidemic threshold alerts
        </p>
      </div>

      <div className="bg-rose-50 border border-rose-200 p-4 rounded-xl flex items-center gap-3 shadow-xs">
        <AlertTriangle className="w-6 h-6 text-rose-600 shrink-0" />
        <div className="text-xs">
          <span className="font-bold text-rose-900 block">PUBLIC HEALTH DEMO ALERT TRIGGERED</span>
          <span className="text-rose-800 font-medium">
            Fever cases in Varthur Ward exceeded weekly threshold (15 cases reported). Inspection team dispatched.
          </span>
        </div>
      </div>

      <div className="glass-panel rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-xs">
        <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
          <h2 className="text-sm font-bold text-slate-900">Reported Disease Surveillance Cases</h2>
          <button onClick={loadData} className="px-3 py-1 bg-white border border-slate-300 text-slate-700 text-xs font-bold rounded-lg hover:bg-slate-100">Refresh</button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
              <tr>
                <th className="p-4">Disease Name</th>
                <th className="p-4">Patient Name</th>
                <th className="p-4">Ward / Area</th>
                <th className="p-4">Report Date</th>
                <th className="p-4">Severity</th>
                <th className="p-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {cases.map((c) => (
                <tr key={c.id} className="hover:bg-slate-50/80 transition">
                  <td className="p-4 font-bold text-rose-700">{c.disease_name}</td>
                  <td className="p-4 text-slate-900 font-bold">{c.patient_name}</td>
                  <td className="p-4 text-slate-700">{c.ward_name || 'Varthur Ward'}</td>
                  <td className="p-4 font-mono text-slate-600">{c.report_date}</td>
                  <td className="p-4">
                    <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-200">
                      {c.severity}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                      {c.status}
                    </span>
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
