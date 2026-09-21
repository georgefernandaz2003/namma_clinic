import React from 'react';
import { FileSpreadsheet, Download } from 'lucide-react';

const reportTypes = [
  { id: 'opd', title: 'Daily OPD & Footfall Report', desc: 'Patient OPD visits, tokens, triage status & doctor consultation notes' },
  { id: 'patients', title: 'Patient Master Directory Export', desc: 'Registered patients, demographics, ward & ABHA ID status' },
  { id: 'ncd', title: 'NCD Screening & Control Report', desc: 'Hypertension & Diabetes screening, risk categories, and follow-up compliance' },
  { id: 'pharmacy', title: 'Pharmacy Inventory & Batch Expiry Ledger', desc: 'Generic medicine master, FEFO batch stock levels, low-stock & expiry alerts' },
  { id: 'referrals', title: 'Cross-Facility Referral & Continuity Report', desc: 'Source & destination facility referral tracking, urgency & hospital response' },
  { id: 'surveillance', title: 'Disease Surveillance & Outbreak Report', desc: 'Communicable disease case registers, ward distributions & threshold alerts' }
];

import { useAuth } from '../context/AuthContext';

export const Reports: React.FC = () => {
  const { activeFacility } = useAuth();

  const handleExportCSV = (type: string) => {
    const token = localStorage.getItem('access_token');
    const facParam = activeFacility?.id ? `&facility=${activeFacility.id}` : '';
    const url = `http://localhost:8000/api/reports/export/?type=${type}${facParam}`;
    
    fetch(url, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then((res) => res.blob())
      .then((blob) => {
        const a = document.createElement('a');
        a.href = window.URL.createObjectURL(blob);
        a.download = `namma_clinic_${type}_report_${new Date().toISOString().slice(0, 10)}.csv`;
        a.click();
      })
      .catch(() => alert('Failed to download CSV report.'));
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <FileSpreadsheet className="w-6 h-6 text-emerald-600" />
          Configurable Public Health Reports & Local CSV Data Exporter
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Generate and download structured CSV reports for clinic operations, pharmacy stock, referrals, and surveillance
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {reportTypes.map((r) => (
          <div key={r.id} className="glass-card p-5 rounded-2xl border border-slate-200 bg-white flex flex-col justify-between space-y-4 shadow-xs">
            <div>
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
                {r.title}
              </h3>
              <p className="text-xs text-slate-500 mt-1 font-medium">{r.desc}</p>
            </div>

            <button
              onClick={() => handleExportCSV(r.id)}
              className="w-full py-2.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 font-bold text-xs rounded-xl flex items-center justify-center gap-2 transition"
            >
              <Download className="w-4 h-4 text-emerald-700" />
              <span>Export Local CSV Data</span>
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
