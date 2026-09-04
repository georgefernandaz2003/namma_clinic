import React, { useState, useEffect } from 'react';
import api from '../services/api';
import type { Alert } from '../types';
import { useAuth } from '../context/AuthContext';
import { Bell, CheckCircle2 } from 'lucide-react';

export const Alerts: React.FC = () => {
  const { activeFacility } = useAuth();
  const [alerts, setAlerts] = useState<Alert[]>([]);

  const loadData = async () => {
    if (!activeFacility) return;
    try {
      const res = await api.get(`alerts/?facility=${activeFacility.id}`);
      setAlerts(res.data.results || res.data || []);
    } catch (e) {
      console.error('Failed to load alerts', e);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeFacility]);

  const handleAcknowledge = async (alertId: number) => {
    try {
      await api.patch(`alerts/${alertId}/`, { status: 'ACKNOWLEDGED' });
      loadData();
    } catch (e) {
      alert('Failed to acknowledge alert.');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <Bell className="w-6 h-6 text-amber-600" />
          Automated Alert Engine & Decision Support System
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Rule-based alerts for low medicine stock, near-expiry batches, referral pendency, and disease thresholds
        </p>
      </div>

      <div className="glass-panel rounded-2xl border border-slate-200 bg-white p-5 space-y-4 shadow-xs">
        <h2 className="text-sm font-bold text-slate-900">Active System Alerts</h2>
        <div className="space-y-3">
          {alerts.map((a) => (
            <div
              key={a.id}
              className={`p-4 rounded-xl border flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 ${
                a.severity === 'CRITICAL'
                  ? 'bg-rose-50 border-rose-200 text-rose-900'
                  : a.severity === 'HIGH'
                  ? 'bg-amber-50 border-amber-200 text-amber-900'
                  : 'bg-slate-50 border-slate-200 text-slate-900'
              }`}
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    a.severity === 'CRITICAL' ? 'bg-rose-200 text-rose-900 border border-rose-300' : 'bg-amber-200 text-amber-900 border border-amber-300'
                  }`}>
                    {a.severity}
                  </span>
                  <span className="font-bold text-slate-900 text-xs">{a.title}</span>
                </div>
                <p className="text-xs text-slate-700 font-medium">{a.description}</p>
                <span className="text-[10px] text-slate-500 font-mono block">Triggered at: {a.created_at}</span>
              </div>

              {a.status === 'NEW' ? (
                <button
                  onClick={() => handleAcknowledge(a.id)}
                  className="px-3 py-1.5 bg-white hover:bg-slate-100 text-slate-800 border border-slate-300 rounded-lg text-xs font-bold shrink-0 shadow-xs"
                >
                  Acknowledge Alert
                </button>
              ) : (
                <span className="text-xs font-bold text-emerald-700 flex items-center gap-1 shrink-0">
                  <CheckCircle2 className="w-4 h-4" /> Acknowledged
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
