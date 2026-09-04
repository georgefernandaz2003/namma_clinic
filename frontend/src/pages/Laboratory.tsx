import React, { useState, useEffect } from 'react';
import api from '../services/api';
import type { LabOrder } from '../types';
import { useAuth } from '../context/AuthContext';
import { TestTube, CheckCircle2, FileCheck } from 'lucide-react';

export const Laboratory: React.FC = () => {
  const { activeFacility } = useAuth();
  const [orders, setOrders] = useState<LabOrder[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<LabOrder | null>(null);
  const [resultVal, setResultVal] = useState('8.4');
  const [interpFlag, setInterpFlag] = useState<'NORMAL' | 'HIGH' | 'LOW' | 'CRITICAL'>('HIGH');
  const [notes, setNotes] = useState('Fasting plasma glucose elevated. Recommend doctor review.');

  const loadData = async () => {
    if (!activeFacility) return;
    try {
      const res = await api.get(`lab/orders/?facility=${activeFacility.id}`);
      setOrders(res.data.results || res.data || []);
    } catch (e) {
      console.error('Failed to load lab orders', e);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeFacility]);

  const handleCollectSample = async (orderId: number) => {
    try {
      await api.post(`lab/orders/${orderId}/collect-sample/`, {
        sample_type: 'Blood / Serum',
        sample_code: `SMP-2026-${Math.floor(1000 + Math.random() * 9000)}`
      });
      alert('Sample collected and logged!');
      loadData();
    } catch (e) {
      alert('Failed to collect sample.');
    }
  };

  const handleSaveResult = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrder) return;

    try {
      await api.post(`lab/orders/${selectedOrder.id}/save-result/`, {
        result_value: resultVal,
        unit: 'mmol/L',
        reference_range: '3.9 - 6.1',
        interpretation_flag: interpFlag,
        notes
      });
      alert('Lab result verified and saved!');
      setSelectedOrder(null);
      loadData();
    } catch (e) {
      alert('Failed to save lab result.');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <TestTube className="w-6 h-6 text-purple-600" />
          Diagnostic Laboratory & Specimen Workflow
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Order queue, sample barcode logging, laboratory result entry, and technician verification
        </p>
      </div>

      <div className="glass-panel rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-xs">
        <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
          <h2 className="text-sm font-bold text-slate-900">Diagnostic Test Orders</h2>
          <button onClick={loadData} className="px-3 py-1 bg-white border border-slate-300 text-slate-700 text-xs font-bold rounded-lg hover:bg-slate-100">Refresh</button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
              <tr>
                <th className="p-4">Order ID</th>
                <th className="p-4">Patient</th>
                <th className="p-4">Test Name</th>
                <th className="p-4">Status</th>
                <th className="p-4">Result</th>
                <th className="p-4">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {orders.map((o) => (
                <tr key={o.id} className="hover:bg-slate-50/80 transition">
                  <td className="p-4 font-mono text-purple-700 font-bold">#LAB-{String(o.id).padStart(4, '0')}</td>
                  <td className="p-4">
                    <span className="font-bold text-slate-900 block">{o.patient_name}</span>
                    <span className="text-[10px] text-slate-500">{o.patient_mobile}</span>
                  </td>
                  <td className="p-4 text-slate-800 font-semibold">{o.test_name}</td>
                  <td className="p-4">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      o.status === 'VERIFIED' ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' :
                      o.status === 'SAMPLE_COLLECTED' ? 'bg-blue-100 text-blue-800 border border-blue-200' :
                      'bg-amber-100 text-amber-900 border border-amber-200'
                    }`}>
                      {o.status}
                    </span>
                  </td>
                  <td className="p-4 font-mono text-slate-800 font-semibold">
                    {o.result ? `${o.result.result_value} ${o.result.unit}` : 'Pending'}
                  </td>
                  <td className="p-4 space-x-2">
                    {o.status === 'ORDERED' && (
                      <button
                        onClick={() => handleCollectSample(o.id)}
                        className="px-2.5 py-1 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded text-[10px]"
                      >
                        Collect Sample
                      </button>
                    )}
                    {o.status === 'SAMPLE_COLLECTED' && (
                      <button
                        onClick={() => setSelectedOrder(o)}
                        className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded text-[10px]"
                      >
                        Enter Result
                      </button>
                    )}
                    {o.status === 'VERIFIED' && (
                      <span className="text-emerald-700 font-bold flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Released
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Result Modal */}
      {selectedOrder && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 border border-slate-200 w-full max-w-md space-y-4 shadow-xl text-xs">
            <div className="flex justify-between items-center pb-3 border-b border-slate-100">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <FileCheck className="w-4 h-4 text-purple-600" />
                Enter Lab Result for {selectedOrder.patient_name}
              </h2>
              <button onClick={() => setSelectedOrder(null)} className="text-slate-400 font-bold">✕</button>
            </div>

            <form onSubmit={handleSaveResult} className="space-y-3">
              <div>
                <label className="block text-slate-700 font-bold mb-1">Result Value *</label>
                <input
                  type="text"
                  value={resultVal}
                  onChange={(e) => setResultVal(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-purple-600 font-mono font-bold"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Interpretation Flag</label>
                <select
                  value={interpFlag}
                  onChange={(e) => setInterpFlag(e.target.value as any)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-purple-600"
                >
                  <option value="NORMAL">Normal</option>
                  <option value="HIGH">High</option>
                  <option value="LOW">Low</option>
                  <option value="CRITICAL">Critical</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Lab Notes</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-purple-600"
                />
              </div>

              <button
                type="submit"
                className="w-full py-2.5 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-xl shadow-md transition"
              >
                Verify & Save Result
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
