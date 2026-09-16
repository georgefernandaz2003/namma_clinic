import React, { useState, useEffect } from 'react';
import api from '../services/api';
import type { LabOrder } from '../types';
import { useAuth } from '../context/AuthContext';
import { TestTube, CheckCircle2, FileCheck, QrCode, Layers, RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const Laboratory: React.FC = () => {
  const { activeFacility } = useAuth();
  const navigate = useNavigate();
  const [orders, setOrders] = useState<LabOrder[]>([]);
  const [catalogue, setCatalogue] = useState<any[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<LabOrder | null>(null);
  const [resultVal, setResultVal] = useState('8.4');
  const [interpFlag, setInterpFlag] = useState<'NORMAL' | 'HIGH' | 'LOW' | 'CRITICAL'>('HIGH');
  const [notes, setNotes] = useState('Fasting plasma glucose elevated. Verified by Lab Tech.');

  const loadData = async () => {
    if (!activeFacility) return;
    try {
      const res = await api.get(`lab/orders/?facility=${activeFacility.id}`);
      setOrders(res.data.results || res.data || []);
    } catch (e) {
      console.error('Failed to load lab orders', e);
    }
  };

  const loadCatalogue = async () => {
    try {
      const res = await api.get('lab/tests/');
      setCatalogue(res.data.results || res.data || []);
    } catch (e) {
      console.error('Failed to load lab test catalogue', e);
    }
  };

  useEffect(() => {
    loadData();
    loadCatalogue();
  }, [activeFacility]);

  const handleCollectSample = async (orderId: number) => {
    try {
      const barcode = `SMP-2026-${Math.floor(1000 + Math.random() * 9000)}`;
      await api.post(`lab/orders/${orderId}/collect-sample/`, {
        sample_type: 'Blood / Serum',
        sample_code: barcode
      });
      alert(`Sample collected! Barcode ID generated: ${barcode}`);
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
        unit: 'mg/dL',
        reference_range: '70 - 140',
        interpretation_flag: interpFlag,
        notes
      });
      alert(`Lab result verified and pushed to patient EMR timeline for ${selectedOrder.patient_name}!`);
      setSelectedOrder(null);
      loadData();
    } catch (e) {
      alert('Failed to save lab result.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <TestTube className="w-6 h-6 text-purple-600" />
            Diagnostic Laboratory & Specimen Workflow
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Full 6-Step Specimen Pipeline: Order → Sample → Barcode → Result → Verification → Patient EMR Record
          </p>
        </div>

        <button
          onClick={() => {
            loadData();
            loadCatalogue();
          }}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-bold text-xs rounded-xl shadow-xs transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Queue & Catalogue</span>
        </button>
      </div>

      {/* Value Proposition Callout Banner */}
      <div className="bg-gradient-to-r from-purple-900 via-indigo-900 to-slate-900 p-4 rounded-2xl text-white space-y-1 shadow-md">
        <div className="flex items-center gap-2 text-xs font-black uppercase tracking-wider text-purple-400">
          <span>🧪 Approved 14 Essential Diagnostic Tests for Namma Clinics / UHWC</span>
        </div>
        <p className="text-xs text-purple-100 font-medium leading-relaxed">
          Full point-of-care and referral laboratory integration tracking specimen lifecycle end-to-end: <strong className="text-white">Order → Sample Collection → Barcode Generation → Laboratory Resulting → Technician Verification → Patient EMR Sync</strong>.
        </p>
      </div>

      {/* 6-Step Specimen Workflow Visual Pipeline */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-200 bg-white shadow-xs space-y-3">
        <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-2">
          <Layers className="w-4 h-4 text-purple-600" />
          6-Step Specimen Diagnostic Lifecycle Pipeline
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 text-center text-xs">
          <div className="p-2.5 rounded-xl bg-purple-50 border border-purple-200 text-purple-900 space-y-1">
            <span className="font-mono text-[10px] font-bold block text-purple-600 uppercase">Step 1</span>
            <span className="font-bold block text-xs">1. Doctor Order</span>
            <span className="text-[10px] text-purple-700 block">Requested in OPD</span>
          </div>
          <div className="p-2.5 rounded-xl bg-blue-50 border border-blue-200 text-blue-900 space-y-1">
            <span className="font-mono text-[10px] font-bold block text-blue-600 uppercase">Step 2</span>
            <span className="font-bold block text-xs">2. Sample Collect</span>
            <span className="text-[10px] text-blue-700 block">Blood/Urine/Sputum</span>
          </div>
          <div className="p-2.5 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-900 space-y-1">
            <span className="font-mono text-[10px] font-bold block text-indigo-600 uppercase">Step 3</span>
            <span className="font-bold block text-xs">3. Barcode Tag</span>
            <span className="text-[10px] text-indigo-700 block">SMP-2026 Code</span>
          </div>
          <div className="p-2.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 space-y-1">
            <span className="font-mono text-[10px] font-bold block text-amber-600 uppercase">Step 4</span>
            <span className="font-bold block text-xs">4. Enter Result</span>
            <span className="text-[10px] text-amber-700 block">Value & Unit</span>
          </div>
          <div className="p-2.5 rounded-xl bg-teal-50 border border-teal-200 text-teal-900 space-y-1">
            <span className="font-mono text-[10px] font-bold block text-teal-600 uppercase">Step 5</span>
            <span className="font-bold block text-xs">5. Verify</span>
            <span className="text-[10px] text-teal-700 block">Tech Sign-Off</span>
          </div>
          <div className="p-2.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 space-y-1">
            <span className="font-mono text-[10px] font-bold block text-emerald-600 uppercase">Step 6</span>
            <span className="font-bold block text-xs">6. EMR Sync</span>
            <span className="text-[10px] text-emerald-700 block">Live in Profile</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Orders Queue & Complete 14-Test Catalogue */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Lab Orders Queue Table */}
        <div className="lg:col-span-2 glass-panel rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-xs space-y-0">
          <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
            <h2 className="text-sm font-bold text-slate-900">Active Laboratory Test Orders</h2>
            <span className="px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-purple-100 text-purple-800 border border-purple-200">
              {orders.length} Active Orders
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                <tr>
                  <th className="p-3.5">Order ID</th>
                  <th className="p-3.5">Patient</th>
                  <th className="p-3.5">Test Name</th>
                  <th className="p-3.5">Barcode</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5">Result</th>
                  <th className="p-3.5">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {orders.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-slate-400 font-medium">
                      No active diagnostic test orders found for this facility.
                    </td>
                  </tr>
                ) : (
                  orders.map((o) => (
                    <tr key={o.id} className="hover:bg-slate-50/80 transition">
                      <td className="p-3.5 font-mono text-purple-700 font-bold">#LAB-{String(o.id).padStart(4, '0')}</td>
                      <td className="p-3.5">
                        <span className="font-bold text-slate-900 block">{o.patient_name}</span>
                        <span className="text-[10px] text-slate-500 font-mono">{o.patient_mobile}</span>
                      </td>
                      <td className="p-3.5 text-slate-800 font-semibold">{o.test_name}</td>
                      <td className="p-3.5">
                        {o.sample_details?.sample_code ? (
                          <span className="font-mono text-[10px] font-bold bg-slate-100 text-slate-800 px-2 py-0.5 rounded border border-slate-200 flex items-center gap-1">
                            <QrCode className="w-3 h-3 text-purple-600" />
                            {o.sample_details.sample_code}
                          </span>
                        ) : (
                          <span className="text-[10px] text-slate-400 italic">Pending</span>
                        )}
                      </td>
                      <td className="p-3.5">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          o.status === 'VERIFIED' ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' :
                          o.status === 'SAMPLE_COLLECTED' ? 'bg-blue-100 text-blue-800 border border-blue-200' :
                          'bg-amber-100 text-amber-900 border border-amber-200'
                        }`}>
                          {o.status}
                        </span>
                      </td>
                      <td className="p-3.5 font-mono text-slate-800 font-semibold">
                        {o.result ? (
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            o.result.interpretation_flag === 'HIGH' || o.result.interpretation_flag === 'CRITICAL'
                              ? 'bg-rose-100 text-rose-800 border border-rose-200'
                              : 'bg-slate-100 text-slate-800'
                          }`}>
                            {o.result.result_value} {o.result.unit}
                          </span>
                        ) : (
                          <span className="text-slate-400 text-[10px]">Pending</span>
                        )}
                      </td>
                      <td className="p-3.5 space-x-2">
                        {o.status === 'ORDERED' && (
                          <button
                            onClick={() => handleCollectSample(o.id)}
                            className="px-2.5 py-1 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded text-[10px] shadow-xs"
                          >
                            Collect Sample
                          </button>
                        )}
                        {o.status === 'SAMPLE_COLLECTED' && (
                          <button
                            onClick={() => setSelectedOrder(o)}
                            className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded text-[10px] shadow-xs"
                          >
                            Enter Result
                          </button>
                        )}
                        {o.status === 'VERIFIED' && (
                          <button
                            onClick={() => navigate(`/patients/${o.patient}`)}
                            className="text-emerald-700 font-bold text-[10px] hover:underline flex items-center gap-1"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Synced EMR
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

        {/* Complete Approved 14-Test Catalogue Panel */}
        <div className="glass-panel p-4 rounded-2xl border border-slate-200 bg-white space-y-3 shadow-xs">
          <div className="border-b border-slate-100 pb-2 flex justify-between items-center">
            <h2 className="text-xs font-bold uppercase tracking-wider text-purple-900 flex items-center gap-1.5">
              <TestTube className="w-4 h-4 text-purple-600" />
              Approved 14 Diagnostic Test Catalogue
            </h2>
            <span className="px-2 py-0.5 rounded bg-purple-100 text-purple-800 font-mono text-[10px] font-bold">
              {catalogue.length} Tests
            </span>
          </div>

          <p className="text-[11px] text-slate-500 font-medium">
            Government-approved essential point-of-care and laboratory test list for Urban Health & Wellness Clinics / Namma Clinics.
          </p>

          <div className="space-y-2 max-h-[520px] overflow-y-auto pr-1 text-xs">
            {catalogue.map((test) => (
              <div
                key={test.id}
                className="p-3 rounded-xl border border-slate-200 bg-slate-50/70 space-y-1 hover:bg-white hover:border-purple-300 transition shadow-2xs"
              >
                <div className="flex justify-between items-start">
                  <span className="font-bold text-slate-900 text-xs">{test.name}</span>
                  <span className="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded bg-purple-100 text-purple-800">
                    {test.code}
                  </span>
                </div>
                <div className="flex justify-between items-center text-[10px] text-slate-500 pt-0.5">
                  <span className="font-semibold text-slate-700">Category: {test.category}</span>
                  <span className="font-mono">Ref: {test.reference_range}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Result Verification Modal */}
      {selectedOrder && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 border border-slate-200 w-full max-w-md space-y-4 shadow-xl text-xs">
            <div className="flex justify-between items-center pb-3 border-b border-slate-100">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <FileCheck className="w-4 h-4 text-purple-600" />
                Enter & Verify Result for {selectedOrder.patient_name}
              </h2>
              <button onClick={() => setSelectedOrder(null)} className="text-slate-400 font-bold hover:text-slate-700">✕</button>
            </div>

            <form onSubmit={handleSaveResult} className="space-y-3">
              <div className="bg-purple-50 p-3 rounded-xl border border-purple-100 space-y-1 font-mono text-[11px]">
                <div className="flex justify-between">
                  <span className="text-purple-800 font-bold">Test: {selectedOrder.test_name}</span>
                  <span className="text-purple-600">ID: #LAB-{selectedOrder.id}</span>
                </div>
                <div className="text-purple-700">
                  Specimen Code: {selectedOrder.sample_details?.sample_code || 'SMP-2026-LOGGED'}
                </div>
              </div>

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
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-purple-600 font-medium"
                >
                  <option value="NORMAL">Normal / Within Reference Range</option>
                  <option value="HIGH">High / Above Reference Limit</option>
                  <option value="LOW">Low / Below Reference Limit</option>
                  <option value="CRITICAL">Critical Alert Value 🚨</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Technician Verification Notes</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-purple-600"
                />
              </div>

              <button
                type="submit"
                className="w-full py-2.5 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-xl shadow-md transition"
              >
                Verify Result & Release to Patient EMR
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
