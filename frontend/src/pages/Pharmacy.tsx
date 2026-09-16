import React, { useState, useEffect } from 'react';
import api from '../services/api';
import type { Prescription, MedicineBatch } from '../types';
import { useAuth } from '../context/AuthContext';
import { Pill, PackageCheck, AlertTriangle, ArrowDown, TrendingDown, Layers, ShieldCheck } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const Pharmacy: React.FC = () => {
  const { activeFacility } = useAuth();
  const navigate = useNavigate();
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [batches, setBatches] = useState<MedicineBatch[]>([]);
  const [activeTab, setActiveTab] = useState<'PRESCRIPTIONS' | 'INVENTORY'>('PRESCRIPTIONS');

  const loadData = async () => {
    if (!activeFacility) return;
    try {
      const pRes = await api.get(`pharmacy/prescriptions/?facility=${activeFacility.id}`);
      setPrescriptions(pRes.data.results || pRes.data || []);

      const bRes = await api.get(`pharmacy/batches/?facility=${activeFacility.id}`);
      setBatches(bRes.data.results || bRes.data || []);
    } catch (e) {
      console.error('Failed to load pharmacy data', e);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeFacility]);

  const handleDispense = async (prescriptionId: number) => {
    try {
      await api.post('pharmacy/dispense/', { prescription_id: prescriptionId });
      alert('Prescription dispensed using FEFO auto-selection engine! Stock reduced in real-time.');
      loadData();
    } catch (e: any) {
      const msg = e.response?.data?.error || 'Failed to dispense prescription.';
      alert(msg);
    }
  };

  // Group batches by generic medicine name to demonstrate FEFO batch selection
  const groupedBatches = batches.reduce((acc: Record<string, MedicineBatch[]>, b) => {
    const key = b.medicine_name || 'Generic Drug';
    if (!acc[key]) acc[key] = [];
    acc[key].push(b);
    return acc;
  }, {});

  // Sort each medicine's batches by expiry date (earliest expiry first = FEFO order)
  Object.keys(groupedBatches).forEach((key) => {
    groupedBatches[key].sort((a, b) => new Date(a.expiry_date).getTime() - new Date(b.expiry_date).getTime());
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Pill className="w-6 h-6 text-amber-600" />
            FEFO Pharmacy Store & Medicine Batch Ledger
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            First-Expiry First-Out (FEFO) auto-selection dispense engine, generic stock ledgers, and low stock warnings
          </p>
        </div>

        <button
          onClick={loadData}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-bold text-xs rounded-xl shadow-xs transition"
        >
          <PackageCheck className="w-3.5 h-3.5 text-amber-600" />
          <span>Refresh Stock Ledgers</span>
        </button>
      </div>

      {/* Value Proposition Callout Banners */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        <div className="bg-gradient-to-r from-amber-900 via-yellow-900 to-slate-900 p-4 rounded-2xl text-white space-y-1 shadow-md">
          <div className="flex items-center gap-2 font-black uppercase tracking-wider text-amber-400 text-[11px]">
            <ShieldCheck className="w-4 h-4" />
            <span>Government FEFO Dispensing Mandate</span>
          </div>
          <p className="text-amber-100 font-medium leading-relaxed text-[11px]">
            &ldquo;The Government guidelines explicitly require near-expiry medicines to be dispensed first and maintain drug stock/issue/dispense/expiry records.&rdquo;
          </p>
        </div>

        <div className="bg-gradient-to-r from-emerald-900 via-teal-900 to-slate-900 p-4 rounded-2xl text-white space-y-1 shadow-md">
          <div className="flex items-center gap-2 font-black uppercase tracking-wider text-emerald-400 text-[11px]">
            <TrendingDown className="w-4 h-4" />
            <span>High Impact Business Value</span>
          </div>
          <p className="text-emerald-100 font-bold leading-relaxed text-xs">
            Less Expiry <span className="text-emerald-300">→</span> Less Wastage <span className="text-emerald-300">→</span> Better Stock Availability <span className="text-emerald-300">→</span> Optimized Procurement Planning
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-3">
        <button
          onClick={() => setActiveTab('PRESCRIPTIONS')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition ${
            activeTab === 'PRESCRIPTIONS'
              ? 'bg-amber-600 text-white shadow-xs'
              : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
          }`}
        >
          Prescription Queue & Dispense ({prescriptions.length})
        </button>
        <button
          onClick={() => setActiveTab('INVENTORY')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition ${
            activeTab === 'INVENTORY'
              ? 'bg-amber-600 text-white shadow-xs'
              : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
          }`}
        >
          FEFO Stock Batch Selection Ledger ({batches.length} Batches)
        </button>
      </div>

      {activeTab === 'PRESCRIPTIONS' ? (
        <div className="glass-panel rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                <tr>
                  <th className="p-4">Rx ID</th>
                  <th className="p-4">Patient Name</th>
                  <th className="p-4">Prescribed Medicines (EDL List)</th>
                  <th className="p-4">FEFO Auto-Selection Batch Target</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {prescriptions.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-slate-400 font-medium">
                      No pending prescriptions in pharmacy queue.
                    </td>
                  </tr>
                ) : (
                  prescriptions.map((p) => (
                    <tr key={p.id} className="hover:bg-slate-50/80 transition">
                      <td className="p-4 font-mono font-bold text-amber-700">#RX-{String(p.id).padStart(4, '0')}</td>
                      <td className="p-4 font-bold text-slate-900">{p.patient_name}</td>
                      <td className="p-4 space-y-1">
                        {p.items?.map((item, i) => (
                          <div key={i} className="text-slate-800 text-[11px]">
                            <strong>{item.medicine_name}</strong> - {item.dosage} ({item.quantity} units)
                          </div>
                        ))}
                      </td>
                      <td className="p-4">
                        <span className="px-2.5 py-1 rounded bg-amber-50 text-amber-900 border border-amber-200 font-mono text-[10px] font-bold block">
                          🎯 FEFO Target: Earliest Expiry Batch
                        </span>
                      </td>
                      <td className="p-4">
                        <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold ${
                          p.status === 'DISPENSED' ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' : 'bg-amber-100 text-amber-900 border border-amber-200'
                        }`}>
                          {p.status}
                        </span>
                      </td>
                      <td className="p-4">
                        {p.status === 'PENDING' || p.status === 'ACTIVE' ? (
                          <button
                            onClick={() => handleDispense(p.id)}
                            className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs rounded-xl shadow-xs flex items-center gap-1.5 transition"
                          >
                            <PackageCheck className="w-3.5 h-3.5" /> Auto-FEFO Dispense
                          </button>
                        ) : (
                          <button
                            onClick={() => navigate(`/patients/${p.patient}`)}
                            className="text-emerald-700 font-bold text-[11px] hover:underline"
                          >
                            Dispensed & Logged
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {/* FEFO Batch Comparison Grouping */}
          <div className="glass-panel p-4 rounded-2xl border border-slate-200 bg-white shadow-xs space-y-4">
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-2">
              <Layers className="w-4 h-4 text-amber-600" />
              FEFO Priority Batch Comparison Matrix (Earliest Expiry First)
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.keys(groupedBatches).map((medName) => {
                const medBatches = groupedBatches[medName];
                const earliestBatch = medBatches[0];

                return (
                  <div key={medName} className="p-4 rounded-xl border border-slate-200 bg-slate-50/60 space-y-3">
                    <div className="flex justify-between items-center border-b border-slate-200 pb-2">
                      <span className="font-bold text-slate-900 text-xs">{medName}</span>
                      <span className="text-[10px] font-bold text-slate-500 font-mono">
                        {medBatches.reduce((sum, b) => sum + b.quantity, 0)} Units Available
                      </span>
                    </div>

                    <div className="space-y-2">
                      {medBatches.map((b, idx) => {
                        const isEarliest = idx === 0;

                        return (
                          <div
                            key={b.id}
                            className={`p-3 rounded-lg border flex justify-between items-center transition ${
                              isEarliest
                                ? 'bg-amber-50 border-amber-400 text-slate-900 shadow-2xs'
                                : 'bg-white border-slate-200 text-slate-700'
                            }`}
                          >
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-mono font-bold text-xs">{b.batch_number}</span>
                                {isEarliest && (
                                  <span className="px-2 py-0.5 rounded text-[9px] font-black bg-amber-600 text-white uppercase tracking-wider">
                                    Batch A — FEFO Auto-Selected (Expires Sooner)
                                  </span>
                                )}
                                {!isEarliest && (
                                  <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-slate-200 text-slate-700">
                                    Batch B (Expires Later)
                                  </span>
                                )}
                              </div>
                              <span className="text-[10px] text-slate-500 block font-medium mt-0.5">
                                Supplier: {b.supplier} • Quantity: <strong className="text-slate-900">{b.quantity} units</strong>
                              </span>
                            </div>

                            <div className="text-right">
                              <span className={`font-mono text-xs font-bold ${isEarliest ? 'text-amber-800' : 'text-slate-700'}`}>
                                Exp: {b.expiry_date}
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
