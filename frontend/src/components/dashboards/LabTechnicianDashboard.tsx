import React, { useState, useEffect } from 'react';
import { TestTube, Clock, ShieldAlert, CheckCircle2, FileText, AlertCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import api from '../../services/api';

interface LabTechnicianDashboardProps {
  summary: any;
  date: string;
  isToday: boolean;
}

export const LabTechnicianDashboard: React.FC<LabTechnicianDashboardProps> = ({ summary, date, isToday }) => {
  const kpis = summary?.kpis || {};
  const [labOrders, setLabOrders] = useState<any[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<any>(null);
  const [resultVal, setResultVal] = useState('8.4');
  const [resultFlag, setResultFlag] = useState('HIGH');
  const [saving, setSaving] = useState(false);

  const fetchLabOrders = async () => {
    try {
      const facParam = summary?.active_facility_id ? `facility=${summary.active_facility_id}&` : '';
      const dateParam = date ? `date=${date}` : '';
      const res = await api.get(`lab/orders/?${facParam}${dateParam}`);
      const list = res.data.results || res.data || [];
      setLabOrders(list);
      if (list.length > 0 && !selectedOrder) {
        setSelectedOrder(list[0]);
      }
    } catch (e) {
      console.error('Failed to load lab orders', e);
    }
  };

  useEffect(() => {
    fetchLabOrders();
  }, [date, summary?.active_facility_id]);

  const handleSaveResult = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrder) return;
    if (!isToday) {
      alert('Lab result verification is blocked on historical dates.');
      return;
    }
    setSaving(true);
    try {
      await api.post(`lab/orders/${selectedOrder.id}/save-result/`, {
        result_value: resultVal,
        interpretation_flag: resultFlag,
        notes: 'Result verified by lab technician.'
      });
      alert('Lab result verified and released to EMR successfully!');
      fetchLabOrders();
      setSelectedOrder(null);
    } catch (e) {
      alert('Failed to save lab result.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Lab Tech Banner */}
      <div className="bg-gradient-to-r from-purple-900 via-indigo-900 to-slate-900 rounded-2xl p-6 text-white shadow-md relative overflow-hidden">
        <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 bg-purple-700/80 text-purple-100 text-[10px] font-extrabold rounded-full uppercase tracking-wider border border-purple-500/30">
                Diagnostic Laboratory Scope
              </span>
              <span className="text-xs text-purple-200 font-semibold">• {summary?.active_facility || 'Diagnostic Center'}</span>
            </div>
            <h1 className="text-2xl font-black tracking-tight">Diagnostic Lab Technician Console</h1>
            <p className="text-xs text-purple-100 mt-1 max-w-xl">
              Specimen collection logging, 14 mandatory diagnostic test processing (HbA1c, FBG, Dengue, Hb, Lipid), and verified result entry.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Link
              to="/lab"
              className="px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white font-bold text-xs rounded-xl shadow-md transition flex items-center gap-1.5"
            >
              <TestTube className="w-4 h-4" />
              <span>Full Diagnostic Lab</span>
            </Link>
          </div>
        </div>
      </div>

      {/* 5 KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <p className="text-[11px] font-bold text-slate-500 uppercase">New Orders</p>
          <h3 className="text-xl font-black text-slate-900 mt-1">{kpis.lab_pending || 0}</h3>
          <p className="text-[10px] text-purple-700 font-medium mt-0.5">Doctor Diagnostic Requisitions</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-purple-200 bg-purple-50/30 shadow-xs">
          <p className="text-[11px] font-bold text-purple-800 uppercase">Sample Pending</p>
          <h3 className="text-xl font-black text-purple-900 mt-1">{labOrders.filter(o => o.status === 'ORDERED').length}</h3>
          <p className="text-[10px] text-purple-700 font-medium mt-0.5">Blood / Urine Draw</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-blue-200 bg-blue-50/30 shadow-xs">
          <p className="text-[11px] font-bold text-blue-800 uppercase">Processing</p>
          <h3 className="text-xl font-black text-blue-900 mt-1">{labOrders.filter(o => o.status === 'SAMPLE_COLLECTED').length}</h3>
          <p className="text-[10px] text-blue-700 font-medium mt-0.5">Rapid Strip / Analyzer</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-amber-200 bg-amber-50/30 shadow-xs">
          <p className="text-[11px] font-bold text-amber-800 uppercase">Results Pending</p>
          <h3 className="text-xl font-black text-amber-900 mt-1">{labOrders.filter(o => o.status === 'SAMPLE_COLLECTED').length}</h3>
          <p className="text-[10px] text-amber-700 font-medium mt-0.5">Awaiting Verification</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-emerald-200 bg-emerald-50/30 shadow-xs">
          <p className="text-[11px] font-bold text-emerald-800 uppercase">Completed</p>
          <h3 className="text-xl font-black text-emerald-900 mt-1">{labOrders.filter(o => o.status === 'VERIFIED').length}</h3>
          <p className="text-[10px] text-emerald-700 font-medium mt-0.5">Released to EMR</p>
        </div>
      </div>

      {/* Main Grid: Result Verification Form & Lab Queue Table */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Lab Result Verification Panel */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <TestTube className="w-4 h-4 text-purple-600" />
              Enter & Verify Test Result
            </h2>
            {selectedOrder && (
              <span className="px-2 py-0.5 rounded bg-purple-100 text-purple-900 font-mono font-bold text-xs">
                #{selectedOrder.id}
              </span>
            )}
          </div>

          {selectedOrder ? (
            <form onSubmit={handleSaveResult} className="space-y-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                <p className="font-bold text-slate-900">{selectedOrder.patient_name || 'Patient'}</p>
                <p className="text-purple-700 font-semibold">{selectedOrder.test_name || 'HbA1c Glycated Hemoglobin'}</p>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-600 mb-1">Result Value</label>
                <input
                  type="text"
                  value={resultVal}
                  onChange={(e) => setResultVal(e.target.value)}
                  className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg text-xs font-bold"
                  placeholder="e.g. 8.4 %"
                  required
                />
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-600 mb-1">Interpretation Flag</label>
                <select
                  value={resultFlag}
                  onChange={(e) => setResultFlag(e.target.value)}
                  className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg text-xs font-bold cursor-pointer"
                >
                  <option value="NORMAL">NORMAL</option>
                  <option value="HIGH">HIGH</option>
                  <option value="LOW">LOW</option>
                  <option value="CRITICAL">CRITICAL</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={saving || !isToday}
                className="w-full py-2.5 bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs rounded-xl shadow-md transition cursor-pointer"
              >
                {saving ? 'Verifying...' : 'Verify & Release Result to EMR'}
              </button>
            </form>
          ) : (
            <div className="p-8 text-center text-xs text-slate-400 font-medium border border-dashed border-slate-200 rounded-xl">
              Select a pending lab order from the queue to verify results.
            </div>
          )}
        </div>

        {/* Lab Queue Table */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
            <div>
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Clock className="w-4 h-4 text-purple-600" />
                Lab Diagnostic Queue
              </h2>
              <p className="text-xs text-slate-500">Diagnostic requisitions for authorized facility</p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-100/70 border-b border-slate-200 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                  <th className="py-3 px-4">Order ID</th>
                  <th className="py-3 px-4 text-center">Token</th>
                  <th className="py-3 px-4">Patient</th>
                  <th className="py-3 px-4">Test Requested</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs font-medium">
                {labOrders.length > 0 ? (
                  labOrders.map((o: any) => (
                    <tr key={o.id} className="hover:bg-slate-50 transition">
                      <td className="py-3 px-4 font-mono font-bold text-purple-700">#{o.id}</td>
                      <td className="py-3 px-4 text-center font-mono font-bold text-emerald-700">
                        {o.token_number ? `Token #${o.token_number}` : '—'}
                      </td>
                      <td className="py-3 px-4 font-bold text-slate-900">{o.patient_name || 'Patient'}</td>
                      <td className="py-3 px-4 text-slate-700">{o.test_name}</td>
                      <td className="py-3 px-4 text-center">
                        <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold border ${
                          o.status === 'VERIFIED' ? 'bg-emerald-50 text-emerald-800 border-emerald-200' : 'bg-purple-50 text-purple-800 border-purple-200'
                        }`}>
                          {o.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => setSelectedOrder(o)}
                          className="px-2.5 py-1 bg-purple-50 hover:bg-purple-100 text-purple-700 font-bold text-[11px] rounded-lg transition cursor-pointer"
                        >
                          Select Order
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-xs text-slate-400 font-medium">
                      No active lab orders found for selected date.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
