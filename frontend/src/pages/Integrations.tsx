import React, { useState, useEffect } from 'react';
import api from '../services/api';
import type { IntegrationConfiguration } from '../types';
import { Sliders, RefreshCw, Server, AlertCircle } from 'lucide-react';

export const Integrations: React.FC = () => {
  const [integrations, setIntegrations] = useState<IntegrationConfiguration[]>([]);
  const [syncing, setSyncing] = useState<Record<string, boolean>>({});

  const loadData = async () => {
    try {
      const res = await api.get('integrations/');
      setIntegrations(res.data.results || res.data || []);
    } catch (e) {
      console.error('Failed to load integrations', e);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSimulateSync = (sysName: string) => {
    setSyncing((prev) => ({ ...prev, [sysName]: true }));
    setTimeout(() => {
      setSyncing((prev) => ({ ...prev, [sysName]: false }));
      alert(`Simulated sync complete for ${sysName}! No external internet connection used.`);
    }, 1200);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <Sliders className="w-6 h-6 text-emerald-600" />
          Government & Ecosystem Integration Connectors (Mock Simulation)
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Simulated integration endpoints for ABDM, ABHA, HMIS, RCH, and E-Aushada (100% Offline Compatible)
        </p>
      </div>

      <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl flex items-center gap-3 text-xs shadow-xs">
        <AlertCircle className="w-5 h-5 text-amber-700 shrink-0" />
        <p className="text-amber-900 font-bold">
          "Demo integration — no external system or cloud API connected." All connectors run locally in MOCK state.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {integrations.map((item) => (
          <div key={item.id} className="glass-card p-5 rounded-2xl border border-slate-200 bg-white space-y-4 shadow-xs">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-200">
                  Status: {item.status}
                </span>
                <h3 className="font-bold text-slate-900 text-sm mt-1.5">{item.display_name}</h3>
              </div>
              <Server className="w-5 h-5 text-slate-400" />
            </div>

            <p className="text-xs text-slate-600 font-medium bg-slate-50 p-3 rounded-xl border border-slate-200">{item.notes}</p>

            <button
              onClick={() => handleSimulateSync(item.system_name)}
              disabled={syncing[item.system_name]}
              className="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-300 font-bold text-xs rounded-xl flex items-center justify-center gap-2 transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-emerald-700 ${syncing[item.system_name] ? 'animate-spin' : ''}`} />
              <span>{syncing[item.system_name] ? 'Simulating Sync...' : 'Trigger Simulated Sync'}</span>
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
