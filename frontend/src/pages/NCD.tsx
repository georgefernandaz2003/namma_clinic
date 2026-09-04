import React, { useState, useEffect } from 'react';
import api from '../services/api';
import type { NCDRecord } from '../types';
import { useAuth } from '../context/AuthContext';
import { Activity } from 'lucide-react';

export const NCD: React.FC = () => {
  const { activeFacility } = useAuth();
  const [records, setRecords] = useState<NCDRecord[]>([]);

  const loadData = async () => {
    if (!activeFacility) return;
    try {
      const res = await api.get(`ncd/?facility=${activeFacility.id}`);
      setRecords(res.data.results || res.data || []);
    } catch (e) {
      console.error('Failed to load NCD records', e);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeFacility]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <Activity className="w-6 h-6 text-emerald-600" />
          Non-Communicable Disease (NCD) Registry & Cohort Control
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Hypertension & Diabetes screening, risk stratification, and longitudinal control monitoring
        </p>
      </div>

      <div className="glass-panel rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-xs">
        <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
          <h2 className="text-sm font-bold text-slate-900">Registered NCD Cohort Patients</h2>
          <button onClick={loadData} className="px-3 py-1 bg-white border border-slate-300 text-slate-700 text-xs font-bold rounded-lg hover:bg-slate-100">Refresh</button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
              <tr>
                <th className="p-4">Patient Name</th>
                <th className="p-4">Diagnoses</th>
                <th className="p-4">Last BP Vitals</th>
                <th className="p-4">Last Glucose</th>
                <th className="p-4">Risk Level</th>
                <th className="p-4">Control Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {records.map((r) => (
                <tr key={r.id} className="hover:bg-slate-50/80 transition">
                  <td className="p-4">
                    <span className="font-bold text-slate-900 block">{r.patient_name}</span>
                    <span className="text-[10px] text-slate-500 font-mono">{r.patient_mobile}</span>
                  </td>
                  <td className="p-4 text-slate-800">
                    {r.hypertension_diagnosed && <span className="px-2 py-0.5 rounded bg-rose-100 text-rose-800 border border-rose-200 text-[10px] font-bold mr-1">Hypertension</span>}
                    {r.diabetes_diagnosed && <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-900 border border-amber-200 text-[10px] font-bold">Diabetes</span>}
                  </td>
                  <td className="p-4 font-mono font-bold text-slate-800">{r.last_bp} mmHg</td>
                  <td className="p-4 font-mono font-bold text-slate-800">{r.last_glucose} mg/dL</td>
                  <td className="p-4">
                    <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold ${
                      r.risk_level === 'HIGH' ? 'bg-rose-100 text-rose-800 border border-rose-200' : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                    }`}>
                      {r.risk_level}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold ${
                      r.control_status === 'CONTROLLED' ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' : 'bg-rose-100 text-rose-800 border border-rose-200'
                    }`}>
                      {r.control_status}
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
