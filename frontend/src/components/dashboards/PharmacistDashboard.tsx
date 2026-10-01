import React, { useState, useEffect } from 'react';
import { Pill, Clock, ShieldAlert, CheckCircle2, Package, AlertTriangle, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import api from '../../services/api';

interface PharmacistDashboardProps {
  summary: any;
  date: string;
  isToday: boolean;
}

export const PharmacistDashboard: React.FC<PharmacistDashboardProps> = ({ summary, date, isToday }) => {
  const kpis = summary?.kpis || {};
  const inventory = summary?.inventory_summary || {};
  const [prescriptions, setPrescriptions] = useState<any[]>([]);
  const [selectedRx, setSelectedRx] = useState<any>(null);
  const [dispensing, setDispensing] = useState(false);
  const actionRequired = summary?.action_required || [];

  const fetchPrescriptions = async () => {
    try {
      const res = await api.get('prescriptions/');
      const list = res.data.results || res.data || [];
      setPrescriptions(list);
      if (list.length > 0 && !selectedRx) {
        setSelectedRx(list[0]);
      }
    } catch (e) {
      console.error('Failed to load prescriptions', e);
    }
  };

  useEffect(() => {
    fetchPrescriptions();
  }, [date]);

  const handleDispense = async (rxId: number) => {
    if (!isToday) {
      alert('Pharmacy dispensing actions are blocked on historical dates.');
      return;
    }
    setDispensing(true);
    try {
      const res = await api.post('pharmacy/dispense/', { prescription_id: rxId });
      alert(res.data.message || 'Prescription dispensed using FEFO batch rules!');
      fetchPrescriptions();
      setSelectedRx(null);
    } catch (e: any) {
      alert(e.response?.data?.error || 'Failed to dispense prescription.');
    } finally {
      setDispensing(false);
    }
  };

  const handleVerify = async (rxId: number) => {
    try {
      const res = await api.post(`prescriptions/${rxId}/verify/`, {
        notes: 'Pharmacist verification completed at dispensing counter',
      });
      alert(res.data.message || 'Prescription verified successfully.');
      fetchPrescriptions();
      if (selectedRx && selectedRx.id === rxId) {
        setSelectedRx({ ...selectedRx, status: 'VERIFIED' });
      }
    } catch (e: any) {
      alert(e.response?.data?.error || 'Failed to verify prescription.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Pharmacist Banner */}
      <div className="bg-gradient-to-r from-amber-900 via-orange-900 to-slate-900 rounded-2xl p-6 text-white shadow-md relative overflow-hidden">
        <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 bg-amber-700/80 text-amber-100 text-[10px] font-extrabold rounded-full uppercase tracking-wider border border-amber-500/30">
                Pharmacy & Drug Inventory Scope
              </span>
              <span className="text-xs text-amber-200 font-semibold">• {summary?.active_facility || 'Facility Pharmacy'}</span>
            </div>
            <h1 className="text-2xl font-black tracking-tight">Pharmacist Dispensing & Inventory Desk</h1>
            <p className="text-xs text-amber-100 mt-1 max-w-xl">
              First-Expiry First-Out (FEFO) automated drug batch selection, stock inventory monitoring, and prescription dispensing.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Link
              to="/pharmacy"
              className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs rounded-xl shadow-md transition flex items-center gap-1.5"
            >
              <Pill className="w-4 h-4" />
              <span>Full Pharmacy Module</span>
            </Link>
          </div>
        </div>
      </div>

      {/* 5 KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <p className="text-[11px] font-bold text-slate-500 uppercase">Prescriptions</p>
          <h3 className="text-xl font-black text-slate-900 mt-1">{summary?.pharmacy_summary?.total_prescriptions ?? summary?.kpis?.pharmacy_total ?? 0}</h3>
          <p className="text-[10px] text-amber-700 font-medium mt-0.5">Total EMR Orders</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-amber-200 bg-amber-50/30 shadow-xs">
          <p className="text-[11px] font-bold text-amber-800 uppercase">Waiting</p>
          <h3 className="text-xl font-black text-amber-900 mt-1">{summary?.pharmacy_summary?.pending ?? summary?.kpis?.pharmacy_waiting ?? 0}</h3>
          <p className="text-[10px] text-amber-700 font-medium mt-0.5">Dispense Queue</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-emerald-200 bg-emerald-50/30 shadow-xs">
          <p className="text-[11px] font-bold text-emerald-800 uppercase">Dispensed</p>
          <h3 className="text-xl font-black text-emerald-900 mt-1">{summary?.pharmacy_summary?.dispensed_today ?? summary?.kpis?.pharmacy_dispensed_today ?? 0}</h3>
          <p className="text-[10px] text-emerald-700 font-medium mt-0.5">Completed Today</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-rose-200 bg-rose-50/30 shadow-xs">
          <p className="text-[11px] font-bold text-rose-800 uppercase">Low Stock</p>
          <h3 className="text-xl font-black text-rose-900 mt-1">{summary?.inventory_summary?.low_stock ?? summary?.pharmacy_summary?.low_stock ?? 0}</h3>
          <p className="text-[10px] text-rose-700 font-medium mt-0.5">Below Threshold</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-orange-200 bg-orange-50/30 shadow-xs">
          <p className="text-[11px] font-bold text-orange-800 uppercase">Expiring Soon</p>
          <h3 className="text-xl font-black text-orange-900 mt-1">{summary?.inventory_summary?.expiring_soon ?? summary?.pharmacy_summary?.expiring_soon ?? 0}</h3>
          <p className="text-[10px] text-orange-700 font-medium mt-0.5">FEFO Action Required</p>
        </div>

      </div>

      {/* Main Grid: Active Prescription Panel & Pharmacy Queue */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Prescription FEFO Dispense Panel */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Pill className="w-4 h-4 text-amber-600" />
              FEFO Automated Dispensing Panel
            </h2>
            {selectedRx && (
              <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-900 font-mono font-bold text-xs">
                Rx #{selectedRx.id}
              </span>
            )}
          </div>

          {selectedRx ? (
            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                <p className="font-bold text-slate-900">{selectedRx.patient_name || 'Patient Name'}</p>
                <p className="text-slate-500">Doctor: {selectedRx.doctor_name || 'Medical Officer'} • Status: <strong className="text-amber-800">{selectedRx.status}</strong></p>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-600 uppercase mb-1">Prescribed EDL Medicines</label>
                <div className="space-y-1.5 max-h-40 overflow-y-auto p-2 bg-slate-50 border border-slate-200 rounded-lg">
                  {selectedRx.items && selectedRx.items.length > 0 ? (
                    selectedRx.items.map((it: any, idx: number) => (
                      <div key={idx} className="flex justify-between items-center text-[11px] p-1.5 bg-white rounded border border-slate-200">
                        <span className="font-bold text-slate-800">{it.medicine_name}</span>
                        <span className="font-mono text-amber-700 font-semibold">{it.dosage} ({it.quantity} units)</span>
                      </div>
                    ))
                  ) : (
                    <div className="text-slate-400 italic">Standard EDL Metformin & Amlodipine</div>
                  )}
                </div>
              </div>

              <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-950 text-[11px]">
                <strong className="block font-bold mb-0.5">FEFO Automated Engine Active</strong>
                System will automatically pick earliest expiring active batch and update inventory stock in backend.
              </div>

              {selectedRx.status === 'PENDING_VERIFICATION' ? (
                <button
                  onClick={() => handleVerify(selectedRx.id)}
                  disabled={!isToday}
                  className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-md transition cursor-pointer flex items-center justify-center gap-1.5"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" /> Verify Prescription Safety Check
                </button>
              ) : ['VERIFIED', 'ACTIVE', 'PENDING', 'PARTIALLY_DISPENSED'].includes(selectedRx.status) ? (
                <button
                  onClick={() => handleDispense(selectedRx.id)}
                  disabled={dispensing || !isToday}
                  className="w-full py-2.5 bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs rounded-xl shadow-md transition cursor-pointer"
                >
                  {dispensing ? 'Dispensing...' : 'Execute FEFO Dispense & Deduct Stock'}
                </button>
              ) : (
                <div className="p-2.5 rounded-xl bg-slate-100 text-slate-800 font-bold text-center">
                  Prescription Status: {selectedRx.status}
                </div>
              )}
            </div>
          ) : (
            <div className="p-8 text-center text-xs text-slate-400 font-medium border border-dashed border-slate-200 rounded-xl">
              Select a prescription from the queue to dispense.
            </div>
          )}
        </div>

        {/* Pharmacy Queue Table */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
            <div>
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Clock className="w-4 h-4 text-amber-600" />
                Pharmacy Queue
              </h2>
              <p className="text-xs text-slate-500">Prescriptions waiting for drug issue</p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-100/70 border-b border-slate-200 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                  <th className="py-3 px-4">Rx ID</th>
                  <th className="py-3 px-4">Patient</th>
                  <th className="py-3 px-4">Prescribed Items</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs font-medium">
                {prescriptions.length > 0 ? (
                  prescriptions.map((p: any) => (
                    <tr key={p.id} className="hover:bg-slate-50 transition">
                      <td className="py-3 px-4 font-mono font-bold text-amber-700">#{p.id}</td>
                      <td className="py-3 px-4 font-bold text-slate-900">{p.patient_name || 'Patient'}</td>
                      <td className="py-3 px-4 text-slate-600">
                        {p.items ? p.items.map((i: any) => i.medicine_name).join(', ') : 'EDL Medications'}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold border ${
                          p.status === 'DISPENSED'
                            ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                            : p.status === 'VERIFIED'
                            ? 'bg-teal-50 text-teal-800 border-teal-200'
                            : p.status === 'PARTIALLY_DISPENSED'
                            ? 'bg-blue-50 text-blue-800 border-blue-200'
                            : 'bg-amber-50 text-amber-800 border-amber-200'
                        }`}>
                          {p.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => setSelectedRx(p)}
                          className="px-2.5 py-1 bg-amber-50 hover:bg-amber-100 text-amber-800 font-bold text-[11px] rounded-lg transition cursor-pointer"
                        >
                          View Rx
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-xs text-slate-400 font-medium">
                      No prescriptions found for selected date.
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
