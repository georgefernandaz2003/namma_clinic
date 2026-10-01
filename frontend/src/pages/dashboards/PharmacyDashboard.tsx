import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Pill,
  Clock,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  ArrowRight,
  Building2,
  PackageCheck,
  PauseCircle,
  Boxes,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import {
  getPrescriptions,
  getMedicineBatches,
  getVisits,
  getMedicines
} from '../../api/clinical';
import { parseApiError } from '../../api/client';
import type { Prescription, MedicineBatch, Visit, MedicineMaster } from '../../types';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';

export const PharmacyDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { activeFacility } = useAuth();

  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Authoritative data state
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [batches, setBatches] = useState<MedicineBatch[]>([]);
  const [visits, setVisits] = useState<Visit[]>([]);
  const [medicines, setMedicines] = useState<MedicineMaster[]>([]);

  // Tab filter state
  type FilterTab = 'ALL' | 'PENDING_VERIFICATION' | 'READY_TO_DISPENSE' | 'COMPLETED' | 'ON_HOLD';
  const [filterTab, setFilterTab] = useState<FilterTab>('ALL');

  const loadDashboardData = useCallback(async (isManualRefresh = false) => {
    if (isManualRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);

    try {
      const [rxData, batchData, visitData, medData] = await Promise.all([
        getPrescriptions(activeFacility?.id ? { facility: activeFacility.id } : undefined),
        getMedicineBatches(activeFacility?.id ? { facility: activeFacility.id } : undefined),
        getVisits(activeFacility?.id ? { facility: activeFacility.id } : undefined),
        getMedicines()
      ]);

      setPrescriptions(rxData);
      setBatches(batchData);
      setVisits(visitData);
      setMedicines(medData);
    } catch (err) {
      setError(parseApiError(err));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [activeFacility]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  // Authoritative Derived Metric Counters
  const pendingVerificationCount = prescriptions.filter(
    (p) => p.status === 'PENDING_VERIFICATION'
  ).length;

  const readyToDispenseCount = prescriptions.filter(
    (p) => p.status === 'VERIFIED' || p.status === 'PARTIALLY_DISPENSED'
  ).length;

  const completedCount = prescriptions.filter(
    (p) => p.status === 'DISPENSED'
  ).length;

  const onHoldCount = prescriptions.filter(
    (p) => p.status === 'ON_HOLD'
  ).length;

  const activeBatchesCount = batches.filter(
    (b) => b.status === 'AVAILABLE' && (b.available_quantity ?? 0) > 0
  ).length;

  const stockCriticalCount = batches.filter(
    (b) => (b.available_quantity ?? 0) === 0 || b.status === 'LOW_STOCK' || b.status === 'EXPIRED'
  ).length;

  // Lookups
  const visitMap = new Map(visits.map((v) => [v.id, v]));
  const medMap = new Map(medicines.map((m) => [m.id, m]));

  // Filtering prescriptions
  const filteredPrescriptions = prescriptions.filter((rx) => {
    if (filterTab === 'PENDING_VERIFICATION') return rx.status === 'PENDING_VERIFICATION';
    if (filterTab === 'READY_TO_DISPENSE') return rx.status === 'VERIFIED' || rx.status === 'PARTIALLY_DISPENSED';
    if (filterTab === 'COMPLETED') return rx.status === 'DISPENSED';
    if (filterTab === 'ON_HOLD') return rx.status === 'ON_HOLD';
    return true;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PENDING_VERIFICATION':
        return (
          <span className="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            Awaiting Verification
          </span>
        );
      case 'VERIFIED':
        return (
          <span className="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            Verified (Ready)
          </span>
        );
      case 'PARTIALLY_DISPENSED':
        return (
          <span className="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-cyan-50 text-cyan-700 border border-cyan-200">
            Partially Dispensed
          </span>
        );
      case 'DISPENSED':
        return (
          <span className="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            Fully Dispensed
          </span>
        );
      case 'ON_HOLD':
        return (
          <span className="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-orange-50 text-orange-700 border border-orange-200">
            On Hold
          </span>
        );
      case 'REJECTED':
        return (
          <span className="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            Rejected
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-slate-50 text-slate-700 border border-slate-200">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Workspace Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Pill className="w-6 h-6 text-teal-600" />
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Pharmacist Operations Dashboard
            </h1>
          </div>
          <p className="text-xs text-slate-500 font-medium">
            Doctor prescription verification, FEFO-governed stock allocation & authoritative dispensation ledger
          </p>
          {activeFacility && (
            <div className="flex items-center gap-1.5 text-xs text-slate-600 font-medium pt-1">
              <Building2 className="w-3.5 h-3.5 text-slate-400" />
              <span>Assigned Facility:</span>
              <span className="font-bold text-slate-800">{activeFacility.facility_name}</span>
              <span className="text-slate-400 font-mono">[{activeFacility.facility_code}]</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => loadDashboardData(true)}
            disabled={loading || refreshing}
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-50 hover:bg-slate-100 text-slate-700 font-semibold text-xs rounded-xl border border-slate-200 transition cursor-pointer disabled:opacity-50"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            <span>{refreshing ? 'Refreshing...' : 'Refresh Queue'}</span>
          </button>
          <button
            onClick={() => navigate('/pharmacy')}
            className="flex items-center gap-1.5 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs rounded-xl shadow-xs transition cursor-pointer"
          >
            <span>Open Pharmacy Workstation</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

      {/* Authoritative Metric KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-white p-4 rounded-xl border border-amber-200 bg-amber-50/20 shadow-xs">
          <div className="flex items-center justify-between text-amber-700 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">Verification Due</span>
            <Clock className="w-4 h-4" />
          </div>
          <div className="text-2xl font-black text-amber-950 font-mono">{pendingVerificationCount}</div>
          <div className="text-[10px] text-amber-700 font-medium mt-0.5">Pending pharmacist check</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-emerald-200 bg-emerald-50/20 shadow-xs">
          <div className="flex items-center justify-between text-emerald-700 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">Ready to Dispense</span>
            <PackageCheck className="w-4 h-4" />
          </div>
          <div className="text-2xl font-black text-emerald-950 font-mono">{readyToDispenseCount}</div>
          <div className="text-[10px] text-emerald-700 font-medium mt-0.5">Verified prescriptions</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-blue-200 bg-blue-50/20 shadow-xs">
          <div className="flex items-center justify-between text-blue-700 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">Dispensed</span>
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <div className="text-2xl font-black text-blue-950 font-mono">{completedCount}</div>
          <div className="text-[10px] text-blue-700 font-medium mt-0.5">Completed issues</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-orange-200 bg-orange-50/20 shadow-xs">
          <div className="flex items-center justify-between text-orange-700 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">On Hold</span>
            <PauseCircle className="w-4 h-4" />
          </div>
          <div className="text-2xl font-black text-orange-950 font-mono">{onHoldCount}</div>
          <div className="text-[10px] text-orange-700 font-medium mt-0.5">Clinical queries / holds</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-teal-200 bg-teal-50/20 shadow-xs">
          <div className="flex items-center justify-between text-teal-700 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">Active Batches</span>
            <Boxes className="w-4 h-4" />
          </div>
          <div className="text-2xl font-black text-teal-950 font-mono">{activeBatchesCount}</div>
          <div className="text-[10px] text-teal-700 font-medium mt-0.5">Available in facility</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-rose-200 bg-rose-50/20 shadow-xs">
          <div className="flex items-center justify-between text-rose-700 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">Stock Alerts</span>
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div className="text-2xl font-black text-rose-950 font-mono">{stockCriticalCount}</div>
          <div className="text-[10px] text-rose-700 font-medium mt-0.5">Zero or critical stock</div>
        </div>
      </div>

      {/* Main Prescription Queue Console */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        {/* Tab Navigation */}
        <div className="p-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50/60">
          <div className="flex items-center gap-1 overflow-x-auto pb-1 sm:pb-0">
            <button
              onClick={() => setFilterTab('ALL')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition whitespace-nowrap cursor-pointer ${
                filterTab === 'ALL'
                  ? 'bg-teal-600 text-white shadow-xs'
                  : 'text-slate-600 hover:bg-slate-200/60'
              }`}
            >
              All Prescriptions ({prescriptions.length})
            </button>
            <button
              onClick={() => setFilterTab('PENDING_VERIFICATION')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition whitespace-nowrap cursor-pointer ${
                filterTab === 'PENDING_VERIFICATION'
                  ? 'bg-amber-600 text-white shadow-xs'
                  : 'text-slate-600 hover:bg-slate-200/60'
              }`}
            >
              Awaiting Verification ({pendingVerificationCount})
            </button>
            <button
              onClick={() => setFilterTab('READY_TO_DISPENSE')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition whitespace-nowrap cursor-pointer ${
                filterTab === 'READY_TO_DISPENSE'
                  ? 'bg-emerald-600 text-white shadow-xs'
                  : 'text-slate-600 hover:bg-slate-200/60'
              }`}
            >
              Ready to Dispense ({readyToDispenseCount})
            </button>
            <button
              onClick={() => setFilterTab('COMPLETED')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition whitespace-nowrap cursor-pointer ${
                filterTab === 'COMPLETED'
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'text-slate-600 hover:bg-slate-200/60'
              }`}
            >
              Completed / Dispensed ({completedCount})
            </button>
            <button
              onClick={() => setFilterTab('ON_HOLD')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition whitespace-nowrap cursor-pointer ${
                filterTab === 'ON_HOLD'
                  ? 'bg-orange-600 text-white shadow-xs'
                  : 'text-slate-600 hover:bg-slate-200/60'
              }`}
            >
              On Hold ({onHoldCount})
            </button>
          </div>

          <div className="text-xs text-slate-500 font-mono shrink-0">
            <span>Inventory Source: </span>
            <strong className="text-slate-700">InventoryLedger</strong>
          </div>
        </div>

        {/* Prescription Queue List / Table */}
        {loading ? (
          <div className="p-12 flex justify-center">
            <LoadingSpinner size="lg" label="Loading pharmacy queue & inventory ledger..." />
          </div>
        ) : filteredPrescriptions.length === 0 ? (
          <div className="p-12 text-center text-slate-400 space-y-2">
            <Pill className="w-8 h-8 text-slate-300 mx-auto" />
            <p className="text-sm font-semibold">No prescriptions found for this queue criteria.</p>
            <p className="text-xs text-slate-400">Prescriptions ordered by Medical Officers will appear here automatically.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/80 text-slate-500 font-bold border-b border-slate-200 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="py-3 px-4">Rx Number / Date</th>
                  <th className="py-3 px-4">Patient / Encounter</th>
                  <th className="py-3 px-4">Prescribing Clinician</th>
                  <th className="py-3 px-4">Prescribed Medicines</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredPrescriptions.map((rx) => {
                  const visit = visitMap.get(rx.consultation);

                  return (
                    <tr key={rx.id} className="hover:bg-slate-50/60 transition">
                      <td className="py-3.5 px-4">
                        <div className="font-mono font-bold text-teal-800">
                          RX-{String(rx.id).padStart(5, '0')}
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono mt-0.5">{rx.date}</div>
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="font-bold text-slate-900">
                          {rx.patient_name || visit?.patient_details?.name || `Patient #${rx.patient}`}
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                          UHID: {visit?.patient_details?.uhid || 'N/A'} • Token #{visit?.token_number || rx.consultation}
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="font-medium text-slate-800">
                          {rx.doctor_name || (rx.doctor_staff ? `Staff #${rx.doctor_staff}` : rx.doctor ? `Doctor #${rx.doctor}` : 'Medical Officer')}
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                          Locked - Doctor Role
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="space-y-1">
                          {rx.items.map((it, idx) => {
                            const med = it.medicine ? medMap.get(it.medicine) : null;
                            const medLabel = it.medicine_name || med?.generic_name || `Medicine #${it.medicine}`;
                            return (
                              <div key={it.id || idx} className="flex items-center gap-1.5 text-[11px]">
                                <span className="font-semibold text-slate-800">{medLabel}</span>
                                <span className="text-slate-400 font-mono">({it.dosage} {it.frequency} × {it.duration_days}d)</span>
                                <span className="font-mono font-bold text-teal-700 bg-teal-50 px-1.5 py-0.2 rounded border border-teal-200">
                                  Qty: {it.quantity}
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        {getStatusBadge(rx.status)}
                      </td>

                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={() => navigate(`/pharmacy?rx=${rx.id}`)}
                          className="px-3 py-1.5 bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs rounded-lg transition shadow-xs cursor-pointer"
                        >
                          Review & Dispense
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default PharmacyDashboard;
