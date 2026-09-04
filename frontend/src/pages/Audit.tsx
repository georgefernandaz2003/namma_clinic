import React, { useState, useEffect } from 'react';
import api from '../services/api';
import type { AuditLog } from '../types';
import { Lock } from 'lucide-react';

export const Audit: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);

  const loadData = async () => {
    try {
      const res = await api.get('audit/');
      setLogs(res.data.results || res.data || []);
    } catch (e) {
      console.error('Failed to load audit logs', e);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <Lock className="w-6 h-6 text-emerald-600" />
          Security Audit Log & System Activity Trail
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Immutable audit record of user logins, patient access, clinical consultations, prescriptions, and inventory edits
        </p>
      </div>

      <div className="glass-panel rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-xs">
        <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
          <h2 className="text-sm font-bold text-slate-900">System Audit Log History</h2>
          <button onClick={loadData} className="px-3 py-1 bg-white border border-slate-300 text-slate-700 text-xs font-bold rounded-lg hover:bg-slate-100">Refresh</button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
              <tr>
                <th className="p-4">Timestamp</th>
                <th className="p-4">User</th>
                <th className="p-4">Action Event</th>
                <th className="p-4">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50/80 transition">
                  <td className="p-4 text-slate-500">{log.timestamp}</td>
                  <td className="p-4 text-emerald-800 font-bold">{log.username_snapshot}</td>
                  <td className="p-4 text-slate-900 font-bold">{log.action}</td>
                  <td className="p-4 text-slate-700 font-medium">{log.details}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
