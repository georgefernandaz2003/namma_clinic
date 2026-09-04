import React, { useState, useEffect } from 'react';
import api from '../services/api';
import type { ComplianceItem } from '../types';
import { CheckSquare } from 'lucide-react';

export const Compliance: React.FC = () => {
  const [complianceList, setComplianceList] = useState<ComplianceItem[]>([]);
  const [filterSource, setFilterSource] = useState<string>('ALL');

  const loadData = async () => {
    try {
      const res = await api.get('compliance/');
      setComplianceList(res.data.results || res.data || []);
    } catch (e) {
      console.error('Failed to load compliance data', e);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const filtered = complianceList.filter((item) => {
    if (filterSource === 'ALL') return true;
    return item.source_document === filterSource;
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <CheckSquare className="w-6 h-6 text-emerald-600" />
          Namma Clinic Operational Guidelines & Proposal Compliance Matrix
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Source document requirement mapping (ULB ROK Booklet & K Mati Project Proposal)
        </p>
      </div>

      <div className="flex items-center justify-between gap-4 bg-white p-3 rounded-xl border border-slate-200 text-xs shadow-xs">
        <span className="font-bold text-slate-800">Filter by Source Document:</span>
        <select
          value={filterSource}
          onChange={(e) => setFilterSource(e.target.value)}
          className="bg-slate-50 border border-slate-300 text-slate-900 px-3 py-1.5 rounded-lg focus:outline-none font-medium"
        >
          <option value="ALL">All Source Documents</option>
          <option value="ULB ROK Booklet">ULB ROK Booklet (Official Guideline)</option>
          <option value="K Mati Proposal">K Mati Proposal</option>
        </select>
      </div>

      <div className="glass-panel rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
              <tr>
                <th className="p-4">Req ID</th>
                <th className="p-4">Requirement Text</th>
                <th className="p-4">Source Document</th>
                <th className="p-4">Classification</th>
                <th className="p-4">Module</th>
                <th className="p-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((item) => (
                <tr key={item.id} className="hover:bg-slate-50/80 transition">
                  <td className="p-4 font-mono font-bold text-emerald-700">{item.requirement_id}</td>
                  <td className="p-4 text-slate-900 font-semibold max-w-sm">{item.requirement_text}</td>
                  <td className="p-4 text-slate-600">{item.source_document}</td>
                  <td className="p-4">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-800 border border-slate-200">
                      {item.classification}
                    </span>
                  </td>
                  <td className="p-4 text-slate-700 font-medium">{item.application_module}</td>
                  <td className="p-4">
                    <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                      {item.status}
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
