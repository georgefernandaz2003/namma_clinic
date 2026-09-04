import React, { useState, useEffect } from 'react';
import api from '../services/api';
import type { Facility } from '../types';
import { Building2, Search } from 'lucide-react';

export const Facilities: React.FC = () => {
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [search, setSearch] = useState('');

  const loadData = async () => {
    try {
      const res = await api.get('facilities/');
      setFacilities(res.data.results || res.data || []);
    } catch (e) {
      console.error('Failed to load facilities', e);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const filtered = facilities.filter((f) => f.facility_name.toLowerCase().includes(search.toLowerCase()) || f.facility_code.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Building2 className="w-6 h-6 text-teal-600" />
            Healthcare Facilities Master Registry
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Database-driven registry of Main Hospitals, UPHCs, Namma Clinics, Rural Clinics & Satellites
          </p>
        </div>
      </div>

      <div className="glass-panel p-4 rounded-xl border border-slate-200 bg-white flex items-center gap-3 shadow-xs">
        <Search className="w-5 h-5 text-slate-400 shrink-0" />
        <input
          type="text"
          placeholder="Filter facilities by Code, Name, District..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-transparent text-sm text-slate-900 placeholder-slate-400 focus:outline-none font-medium"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((f) => (
          <div key={f.id} className="glass-card p-5 rounded-2xl border border-slate-200 bg-white space-y-3 shadow-xs">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-200">
                  {f.facility_type.replace('_', ' ')}
                </span>
                <h3 className="font-bold text-slate-900 text-sm mt-1.5">{f.facility_name}</h3>
                <p className="text-[11px] text-slate-500 font-semibold">{f.district_name || 'BBMP Central'}</p>
              </div>
              <span className="text-[10px] font-mono text-slate-400 font-semibold">{f.facility_code}</span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[10px] text-slate-700 bg-slate-50 p-2.5 rounded-xl border border-slate-200">
              <div>
                <span className="text-slate-500 block font-semibold">Population Served</span>
                <span className="font-bold text-emerald-700">{f.population_served.toLocaleString()}</span>
              </div>
              <div>
                <span className="text-slate-500 block font-semibold">Vulnerable Target</span>
                <span className="font-bold text-amber-700">{f.vulnerable_population.toLocaleString()}</span>
              </div>
            </div>

            <div className="text-[11px] text-slate-600 space-y-1">
              <p><strong>Opening Hours:</strong> {f.opening_time} - {f.closing_time}</p>
              <p><strong>Services:</strong> {f.services}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
