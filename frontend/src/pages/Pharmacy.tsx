import React, { useState, useEffect } from 'react';
import api from '../services/api';
import type { Prescription, MedicineBatch } from '../types';
import { useAuth } from '../context/AuthContext';
import { Pill, PackageCheck } from 'lucide-react';

export const Pharmacy: React.FC = () => {
  const { activeFacility } = useAuth();
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
      alert('Prescription dispensed using FEFO auto-selection engine!');
      loadData();
    } catch (e: any) {
      const msg = e.response?.data?.error || 'Failed to dispense prescription.';
      alert(msg);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <Pill className="w-6 h-6 text-amber-600" />
          FEFO Pharmacy Store & Medicine Batch Ledger
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          First-Expiry First-Out (FEFO) auto-selection dispense engine, generic stock ledgers, and low stock warnings
        </p>
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
          FEFO Stock Batch Ledger ({batches.length})
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
                  <th className="p-4">Prescribed Medicines</th>
                  <th className="p-4">Date</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {prescriptions.map((p) => (
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
                    <td className="p-4 font-mono text-slate-600">{p.date}</td>
                    <td className="p-4">
                      <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold ${
                        p.status === 'DISPENSED' ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' : 'bg-amber-100 text-amber-900 border border-amber-200'
                      }`}>
                        {p.status}
                      </span>
                    </td>
                    <td className="p-4">
                      {p.status === 'PENDING' ? (
                        <button
                          onClick={() => handleDispense(p.id)}
                          className="px-3 py-1 bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs rounded-lg shadow-xs flex items-center gap-1.5"
                        >
                          <PackageCheck className="w-3.5 h-3.5" /> FEFO Dispense
                        </button>
                      ) : (
                        <span className="text-emerald-700 font-bold text-[11px]">Dispensed</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="glass-panel rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                <tr>
                  <th className="p-4">Batch Number</th>
                  <th className="p-4">Medicine Name</th>
                  <th className="p-4">Quantity Available</th>
                  <th className="p-4">Expiry Date</th>
                  <th className="p-4">Supplier</th>
                  <th className="p-4">Batch Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {batches.map((b) => (
                  <tr key={b.id} className="hover:bg-slate-50/80 transition">
                    <td className="p-4 font-mono font-bold text-amber-700">{b.batch_number}</td>
                    <td className="p-4 font-bold text-slate-900">{b.medicine_name}</td>
                    <td className="p-4 font-mono text-slate-900 font-bold">{b.quantity} units</td>
                    <td className="p-4 font-mono text-slate-700">{b.expiry_date}</td>
                    <td className="p-4 text-slate-600">{b.supplier}</td>
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        b.status === 'ACTIVE' ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' : 'bg-rose-100 text-rose-800 border border-rose-200'
                      }`}>
                        {b.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
