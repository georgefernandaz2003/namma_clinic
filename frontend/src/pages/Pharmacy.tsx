import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Pill,
  Clock,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Building2,
  ShieldCheck,
  Search,
  Calendar,
  FileSpreadsheet,
  Boxes,
  PackageCheck,
  PauseCircle,
  XCircle,
  Sparkles,
  Info,
  Check
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import {
  getPrescriptions,
  verifyPrescription,
  holdPrescription,
  rejectPrescription,
  getMedicineBatches,
  createDispensation,
  getInventoryLedger,
  getMedicines,
  getVisits
} from '../api/clinical';
import { parseApiError } from '../api/client';
import type {
  Prescription,
  MedicineBatch,
  MedicineMaster,
  InventoryLedger,
  Visit
} from '../types';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorAlert from '../components/common/ErrorAlert';

export const Pharmacy: React.FC = () => {
  const { activeFacility, user } = useAuth();
  const isPharmacist = user?.role === 'PHARMACIST' || (user?.roles && user.roles.includes('PHARMACIST')) || Boolean(user?.is_superuser);
  const [searchParams, setSearchParams] = useSearchParams();

  // Active View Tab: Dispensing Console vs Inventory Ledger Audit
  type ConsoleTab = 'DISPENSING' | 'LEDGER_AUDIT';
  const [consoleTab, setConsoleTab] = useState<ConsoleTab>(isPharmacist ? 'DISPENSING' : 'LEDGER_AUDIT');

  // Data State
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [batches, setBatches] = useState<MedicineBatch[]>([]);
  const [medicines, setMedicines] = useState<MedicineMaster[]>([]);
  const [ledgerEntries, setLedgerEntries] = useState<InventoryLedger[]>([]);
  const [visits, setVisits] = useState<Visit[]>([]);

  // Selection & Queue State
  const [selectedRxId, setSelectedRxId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  type StatusFilter = 'ALL' | 'PENDING_VERIFICATION' | 'VERIFIED' | 'ON_HOLD' | 'DISPENSED' | 'REJECTED';
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('ALL');

  // UI State
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Verification / Hold / Reject Modal State
  const [verifying, setVerifying] = useState<boolean>(false);
  const [verificationNotes, setVerificationNotes] = useState<string>('');
  const [holding, setHolding] = useState<boolean>(false);
  const [holdNotes, setHoldNotes] = useState<string>('');
  const [rejecting, setRejecting] = useState<boolean>(false);
  const [rejectionReason, setRejectionReason] = useState<string>('');
  const [actionInProgress, setActionInProgress] = useState<boolean>(false);

  // Dispensing Form State: Map of prescription_item_id -> { batch_id, quantity }
  interface ItemAllocation {
    batch_id: number;
    quantity: number;
  }
  const [allocations, setAllocations] = useState<Record<number, ItemAllocation>>({});
  const [dispensing, setDispensing] = useState<boolean>(false);

  const loadPharmacyData = useCallback(async (isManualRefresh = false) => {
    if (isManualRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);

    try {
      const promises: [Promise<Prescription[]>, Promise<MedicineBatch[]>, Promise<MedicineMaster[]>, Promise<InventoryLedger[]>, Promise<Visit[]>] = [
        isPharmacist ? getPrescriptions(activeFacility?.id ? { facility: activeFacility.id } : undefined) : Promise.resolve([]),
        getMedicineBatches(activeFacility?.id ? { facility: activeFacility.id } : undefined),
        getMedicines(),
        getInventoryLedger(activeFacility?.id ? { facility: activeFacility.id } : undefined),
        getVisits(activeFacility?.id ? { facility: activeFacility.id } : undefined)
      ];

      const [rxData, batchData, medData, ledgerData, visitData] = await Promise.all(promises);
      setPrescriptions(rxData);
      setBatches(batchData);
      setMedicines(medData);
      setLedgerEntries(ledgerData);
      setVisits(visitData);

      // Auto-select from URL param or default to first prescription
      const queryRxId = searchParams.get('rx');
      if (queryRxId && rxData.some((r) => r.id === Number(queryRxId))) {
        setSelectedRxId(Number(queryRxId));
      } else if (rxData.length > 0) {
        setSelectedRxId((prev) => (prev && rxData.some((r) => r.id === prev) ? prev : rxData[0].id));
      }
    } catch (err) {
      setError(parseApiError(err));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [activeFacility, searchParams]);

  useEffect(() => {
    loadPharmacyData();
  }, [loadPharmacyData]);

  // Handle URL sync
  const handleSelectPrescription = (id: number) => {
    setSelectedRxId(id);
    setSearchParams({ rx: String(id) });
    setSuccessMsg(null);
    setError(null);
    setAllocations({});
  };

  // Lookups
  const visitMap = new Map(visits.map((v) => [v.id, v]));
  const medMap = new Map(medicines.map((m) => [m.id, m]));
  const batchMap = new Map(batches.map((b) => [b.id, b]));

  const selectedRx = prescriptions.find((r) => r.id === selectedRxId);
  const selectedVisit = selectedRx ? visitMap.get(selectedRx.consultation) : undefined;

  // Filtered Queue
  const filteredPrescriptions = prescriptions.filter((rx) => {
    const matchesStatus = statusFilter === 'ALL' || rx.status === statusFilter;
    if (!matchesStatus) return false;

    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    const rxIdStr = `rx-${rx.id}`.toLowerCase();
    const patName = (rx.patient_name || visitMap.get(rx.consultation)?.patient_details?.name || '').toLowerCase();
    const uhid = (visitMap.get(rx.consultation)?.patient_details?.uhid || '').toLowerCase();

    return rxIdStr.includes(q) || patName.includes(q) || uhid.includes(q);
  });

  // Calculate today for expiry comparison
  const todayStr = new Date().toISOString().split('T')[0];

  // Helper to find valid dispensable batches for a medicine sorted by FEFO (expiry_date ASC)
  const getFefoBatchesForMedicine = useCallback((medicineId?: number) => {
    if (!medicineId) return [];
    return batches
      .filter((b) => {
        const isMed = b.medicine === medicineId;
        const isFac = !activeFacility?.id || b.facility === activeFacility.id;
        const hasStock = (b.available_quantity ?? 0) > 0;
        const isAvailStatus = b.status === 'AVAILABLE' || b.status === 'ACTIVE';
        const notExpired = b.expiry_date > todayStr;
        return isMed && isFac && hasStock && isAvailStatus && notExpired;
      })
      .sort((a, b) => a.expiry_date.localeCompare(b.expiry_date));
  }, [batches, activeFacility, todayStr]);

  // Pre-populate FEFO allocations when a verified prescription is selected
  useEffect(() => {
    if (!selectedRx || (selectedRx.status !== 'VERIFIED' && selectedRx.status !== 'PARTIALLY_DISPENSED')) {
      return;
    }

    const initialAlloc: Record<number, ItemAllocation> = {};
    for (const it of selectedRx.items) {
      if (!it.id) continue;
      const remaining = it.quantity - (it.dispensed_quantity ?? 0);
      if (remaining <= 0) continue;

      const fefoBatches = getFefoBatchesForMedicine(it.medicine);
      if (fefoBatches.length > 0) {
        const bestBatch = fefoBatches[0];
        initialAlloc[it.id] = {
          batch_id: bestBatch.id,
          quantity: Math.min(remaining, bestBatch.available_quantity ?? remaining)
        };
      }
    }
    setAllocations(initialAlloc);
  }, [selectedRx, getFefoBatchesForMedicine]);

  // Verification Actions
  const handleVerify = async () => {
    if (!selectedRx) return;
    setActionInProgress(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const updated = await verifyPrescription(selectedRx.id, verificationNotes);
      setSuccessMsg(`Prescription #RX-${String(updated.id).padStart(5, '0')} verified successfully! Ready for dispensing.`);
      setVerifying(false);
      setVerificationNotes('');
      await loadPharmacyData(true);
    } catch (err) {
      setError(parseApiError(err));
    } finally {
      setActionInProgress(false);
    }
  };

  const handleHold = async () => {
    if (!selectedRx) return;
    if (!holdNotes.trim()) {
      setError('Clinical hold reason / query notes are required.');
      return;
    }
    setActionInProgress(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const updated = await holdPrescription(selectedRx.id, holdNotes);
      setSuccessMsg(`Prescription #RX-${String(updated.id).padStart(5, '0')} placed ON HOLD for clarification.`);
      setHolding(false);
      setHoldNotes('');
      await loadPharmacyData(true);
    } catch (err) {
      setError(parseApiError(err));
    } finally {
      setActionInProgress(false);
    }
  };

  const handleReject = async () => {
    if (!selectedRx) return;
    if (!rejectionReason.trim()) {
      setError('Clinical rejection reason is required.');
      return;
    }

    setActionInProgress(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const updated = await rejectPrescription(selectedRx.id, rejectionReason.trim());
      setSuccessMsg(`Prescription #RX-${String(updated.id).padStart(5, '0')} rejected.`);
      setRejecting(false);
      setRejectionReason('');
      await loadPharmacyData(true);
    } catch (err) {
      setError(parseApiError(err));
    } finally {
      setActionInProgress(false);
    }
  };

  // Dispensation Execution
  const handleExecuteDispensation = async () => {
    if (!selectedRx || !activeFacility) return;
    setError(null);
    setSuccessMsg(null);

    const itemsToDispense = Object.entries(allocations)
      .filter(([, alloc]) => alloc.quantity > 0 && alloc.batch_id)
      .map(([itemIdStr, alloc]) => ({
        prescription_item_id: Number(itemIdStr),
        batch_id: alloc.batch_id,
        quantity: alloc.quantity
      }));

    if (itemsToDispense.length === 0) {
      setError('Please select at least one valid batch and quantity to dispense.');
      return;
    }

    setDispensing(true);

    try {
      const disp = await createDispensation({
        prescription_id: selectedRx.id,
        facility_id: activeFacility.id,
        items: itemsToDispense
      });

      setSuccessMsg(`Dispensation #${disp.dispensation_number} recorded successfully! InventoryLedger updated atomically.`);
      setAllocations({});
      await loadPharmacyData(true);
    } catch (err) {
      setError(parseApiError(err));
    } finally {
      setDispensing(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PENDING_VERIFICATION':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">AWAITING VERIFY</span>;
      case 'VERIFIED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">VERIFIED</span>;
      case 'PARTIALLY_DISPENSED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-100 text-cyan-800">PARTIAL DISPENSED</span>;
      case 'DISPENSED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800">DISPENSED</span>;
      case 'ON_HOLD':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-orange-100 text-orange-800">ON HOLD</span>;
      case 'REJECTED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800">REJECTED</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700">{status}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Pill className="w-6 h-6 text-teal-600" />
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Pharmacy Clinical Workstation
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-teal-50 text-teal-700 border border-teal-200">
              FEFO Dispensing & Ledger
            </span>
          </div>
          <p className="text-xs text-slate-500 font-medium">
            Doctor prescription verification, First-Expiry-First-Out stock allocation & immutable inventory ledger
          </p>
          {activeFacility && (
            <div className="flex items-center gap-1.5 text-xs text-slate-600 font-medium pt-1">
              <Building2 className="w-3.5 h-3.5 text-slate-400" />
              <span>Operational Facility Scope:</span>
              <span className="font-bold text-slate-800">{activeFacility.facility_name}</span>
              <span className="text-slate-400 font-mono">[{activeFacility.facility_code}]</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* View Tab Switcher */}
          <div className="flex p-1 bg-slate-100 rounded-xl border border-slate-200 text-xs font-bold">
            {isPharmacist && (
              <button
                onClick={() => setConsoleTab('DISPENSING')}
                className={`px-3 py-1.5 rounded-lg transition cursor-pointer ${
                  consoleTab === 'DISPENSING'
                    ? 'bg-white text-teal-800 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Prescription Dispensing
              </button>
            )}
            <button
              onClick={() => setConsoleTab('LEDGER_AUDIT')}
              className={`px-3 py-1.5 rounded-lg transition cursor-pointer flex items-center gap-1.5 ${
                consoleTab === 'LEDGER_AUDIT'
                  ? 'bg-white text-teal-800 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-teal-600" />
              <span>Inventory Ledger Audit</span>
            </button>
          </div>

          <button
            onClick={() => loadPharmacyData(true)}
            disabled={loading || refreshing}
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-50 hover:bg-slate-100 text-slate-700 font-semibold text-xs rounded-xl border border-slate-200 transition cursor-pointer disabled:opacity-50"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            <span>{refreshing ? 'Refreshing...' : 'Refresh Pharmacy'}</span>
          </button>
        </div>
      </div>

      {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}
      {successMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 font-medium flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg(null)} className="text-emerald-700 font-bold hover:text-emerald-900 cursor-pointer">✕</button>
        </div>
      )}

      {isPharmacist && consoleTab === 'DISPENSING' ? (
        /* Main Grid: Prescriptions Queue (Left) vs Prescription Dispense Console (Right) */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Requisition Queue */}
          <div className="lg:col-span-4 bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden space-y-0">
            <div className="p-4 border-b border-slate-200 bg-slate-50/70 space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Clock className="w-4 h-4 text-teal-600" />
                  Pharmacy Queue ({filteredPrescriptions.length})
                </h2>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-teal-100 text-teal-800">
                  {prescriptions.length} Total
                </span>
              </div>

              {/* Live Search */}
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search patient, UHID, or Rx ID..."
                  className="w-full pl-8 pr-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs placeholder:text-slate-400 focus:outline-none focus:border-teal-600"
                />
              </div>

              {/* Status Filter Tabs */}
              <div className="flex flex-wrap gap-1">
                {(['ALL', 'PENDING_VERIFICATION', 'VERIFIED', 'ON_HOLD', 'DISPENSED', 'REJECTED'] as const).map((st) => (
                  <button
                    key={st}
                    onClick={() => setStatusFilter(st)}
                    className={`px-2 py-1 rounded text-[10px] font-bold transition cursor-pointer ${
                      statusFilter === st
                        ? 'bg-teal-600 text-white'
                        : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-100'
                    }`}
                  >
                    {st === 'PENDING_VERIFICATION' ? 'VERIFY' : st === 'DISPENSED' ? 'DISPENSED' : st}
                  </button>
                ))}
              </div>
            </div>

            {/* Queue Items List */}
            {loading ? (
              <div className="p-8 flex justify-center">
                <LoadingSpinner size="md" label="Loading prescriptions..." />
              </div>
            ) : filteredPrescriptions.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-400">
                No prescriptions match your criteria.
              </div>
            ) : (
              <div className="divide-y divide-slate-100 max-h-[640px] overflow-y-auto">
                {filteredPrescriptions.map((rx) => {
                  const visit = visitMap.get(rx.consultation);
                  const isSelected = rx.id === selectedRxId;

                  return (
                    <button
                      key={rx.id}
                      onClick={() => handleSelectPrescription(rx.id)}
                      className={`w-full text-left p-3.5 transition flex flex-col gap-1 cursor-pointer ${
                        isSelected
                          ? 'bg-teal-50/80 border-l-4 border-teal-600'
                          : 'hover:bg-slate-50'
                      }`}
                    >
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-bold text-slate-900 truncate">
                          {rx.patient_name || visit?.patient_details?.name || `Patient #${rx.patient}`}
                        </span>
                        {getStatusBadge(rx.status)}
                      </div>

                      <div className="flex items-center justify-between text-[11px] text-slate-500 font-mono">
                        <span className="text-teal-700 font-bold">RX-{String(rx.id).padStart(5, '0')}</span>
                        <span>{rx.date}</span>
                      </div>

                      <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1">
                        <span>{rx.items.length} Medicine(s)</span>
                        <span className="font-mono">Token #{visit?.token_number || rx.consultation}</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Right Column: Workstation Console & Prescription Dispensing */}
          <div className="lg:col-span-8 space-y-5">
            {selectedRx ? (
              <>
                {/* Patient & Prescription Demographic Banner */}
                <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h2 className="text-base font-bold text-slate-900">
                          {selectedRx.patient_name || selectedVisit?.patient_details?.name || `Patient #${selectedRx.patient}`}
                        </h2>
                        {getStatusBadge(selectedRx.status)}
                      </div>
                      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 font-mono mt-1">
                        <span>UHID: <strong>{selectedVisit?.patient_details?.uhid || 'N/A'}</strong></span>
                        <span>•</span>
                        <span>Age: {selectedVisit?.patient_details?.age || 'N/A'}</span>
                        <span>•</span>
                        <span>Gender: {selectedVisit?.patient_details?.gender || 'N/A'}</span>
                        <span>•</span>
                        <span>Visit Token: #{selectedVisit?.token_number || selectedRx.consultation}</span>
                      </div>
                    </div>

                    <div className="text-right text-xs">
                      <div className="font-mono font-bold text-teal-700">RX-{String(selectedRx.id).padStart(5, '0')}</div>
                      <div className="text-slate-400 text-[11px] flex items-center justify-end gap-1">
                        <Calendar className="w-3 h-3" />
                        {selectedRx.date}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs bg-slate-50 p-3 rounded-xl border border-slate-200">
                    <div>
                      <span className="text-[11px] text-slate-500 font-semibold block">Prescribing Clinician:</span>
                      <span className="text-slate-800 font-medium">
                        {selectedRx.doctor_name || (selectedRx.doctor_staff ? `Staff #${selectedRx.doctor_staff}` : selectedRx.doctor ? `Doctor #${selectedRx.doctor}` : 'Medical Officer')} (Locked - Doctor Role)
                      </span>
                    </div>
                    <div>
                      <span className="text-[11px] text-slate-500 font-semibold block">Doctor Clinical Notes:</span>
                      <span className="text-slate-800 font-medium">
                        {selectedRx.notes || 'Standard prescription directions.'}
                      </span>
                    </div>
                  </div>

                  {/* Verification & Lifecycle Status Bar */}
                  {selectedRx.status === 'PENDING_VERIFICATION' && (
                    <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl space-y-3">
                      <div className="flex items-center gap-2 text-xs font-bold text-amber-900">
                        <Clock className="w-4 h-4 text-amber-600 shrink-0" />
                        <span>Prescription Awaiting Pharmacist Clinical Verification</span>
                      </div>
                      <p className="text-[11px] text-amber-800">
                        Separation of Duties: Before any medication may be dispensed, the authenticated Pharmacist must verify prescription suitability, dosage intervals, and contraindications.
                      </p>
                      <div className="flex flex-wrap items-center gap-2 pt-1">
                        <button
                          onClick={() => { setVerifying(true); setHolding(false); setRejecting(false); }}
                          className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-lg transition shadow-xs cursor-pointer flex items-center gap-1.5"
                        >
                          <ShieldCheck className="w-3.5 h-3.5" />
                          <span>Verify Prescription</span>
                        </button>
                        <button
                          onClick={() => { setHolding(true); setVerifying(false); setRejecting(false); }}
                          className="px-3.5 py-1.5 bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs rounded-lg transition shadow-xs cursor-pointer flex items-center gap-1.5"
                        >
                          <PauseCircle className="w-3.5 h-3.5" />
                          <span>Put On Hold</span>
                        </button>
                        <button
                          onClick={() => { setRejecting(true); setVerifying(false); setHolding(false); }}
                          className="px-3.5 py-1.5 bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs rounded-lg transition shadow-xs cursor-pointer flex items-center gap-1.5"
                        >
                          <XCircle className="w-3.5 h-3.5" />
                          <span>Reject Prescription</span>
                        </button>
                      </div>
                    </div>
                  )}

                  {selectedRx.status === 'ON_HOLD' && (
                    <div className="p-4 bg-orange-50 border border-orange-200 rounded-xl space-y-2">
                      <div className="flex items-center gap-2 text-xs font-bold text-orange-900">
                        <PauseCircle className="w-4 h-4 text-orange-600 shrink-0" />
                        <span>Prescription is ON HOLD</span>
                      </div>
                      <p className="text-xs text-orange-800">
                        Notes: {selectedRx.verification_notes || 'Awaiting physician clarification.'}
                      </p>
                      <div className="flex gap-2 pt-1">
                        <button
                          onClick={() => { setVerifying(true); setRejecting(false); }}
                          className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-lg transition shadow-xs cursor-pointer flex items-center gap-1"
                        >
                          <ShieldCheck className="w-3.5 h-3.5" />
                          <span>Release & Verify</span>
                        </button>
                        <button
                          onClick={() => { setRejecting(true); setVerifying(false); }}
                          className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs rounded-lg transition shadow-xs cursor-pointer flex items-center gap-1"
                        >
                          <XCircle className="w-3.5 h-3.5" />
                          <span>Reject</span>
                        </button>
                      </div>
                    </div>
                  )}

                  {selectedRx.status === 'REJECTED' && (
                    <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl space-y-1 text-xs text-rose-900">
                      <div className="flex items-center gap-2 font-bold">
                        <XCircle className="w-4 h-4 text-rose-600 shrink-0" />
                        <span>Prescription Rejected by Pharmacist</span>
                      </div>
                      <p className="text-[11px] text-rose-800">
                        Mandatory Reason: <strong>{selectedRx.rejection_reason || 'Clinical contradiction'}</strong>
                      </p>
                      <div className="text-[10px] text-slate-500 font-mono">
                        Verified by Staff #{selectedRx.verified_by || 'Pharmacist'} on {selectedRx.verified_at || 'Recorded'}
                      </div>
                    </div>
                  )}

                  {(selectedRx.status === 'VERIFIED' || selectedRx.status === 'PARTIALLY_DISPENSED') && (
                    <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between text-xs text-emerald-900">
                      <div className="flex items-center gap-2 font-medium">
                        <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                        <span>Prescription Verified & Approved for FEFO Dispensing</span>
                      </div>
                      <div className="text-[11px] text-emerald-700 font-mono">
                        Verified by Staff #{selectedRx.verified_by || 'Pharmacist'}
                      </div>
                    </div>
                  )}

                  {selectedRx.status === 'DISPENSED' && (
                    <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl flex items-center justify-between text-xs text-blue-900">
                      <div className="flex items-center gap-2 font-medium">
                        <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0" />
                        <span>All prescribed medications fully dispensed & ledgered.</span>
                      </div>
                      <span className="font-bold text-blue-800 text-[11px]">Completed</span>
                    </div>
                  )}

                  {/* Verification Modal / Inline Form */}
                  {verifying && (
                    <div className="p-4 bg-slate-50 border border-emerald-300 rounded-xl space-y-3">
                      <div className="flex items-center justify-between text-xs font-bold text-slate-900">
                        <span className="flex items-center gap-1.5 text-emerald-800">
                          <ShieldCheck className="w-4 h-4 text-emerald-600" />
                          Confirm Pharmacist Clinical Verification
                        </span>
                        <button onClick={() => setVerifying(false)} className="text-slate-400 hover:text-slate-600 cursor-pointer">✕</button>
                      </div>
                      <div>
                        <label className="text-[11px] font-semibold text-slate-600 block mb-1">
                          Clinical Verification Notes (Optional):
                        </label>
                        <input
                          type="text"
                          value={verificationNotes}
                          onChange={(e) => setVerificationNotes(e.target.value)}
                          placeholder="e.g. Dose and frequency verified against clinical indication..."
                          className="w-full px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs"
                        />
                      </div>
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => setVerifying(false)}
                          className="px-3 py-1.5 border border-slate-300 text-slate-700 font-bold text-xs rounded-lg hover:bg-slate-100 cursor-pointer"
                        >
                          Cancel
                        </button>
                        <button
                          type="button"
                          disabled={actionInProgress}
                          onClick={handleVerify}
                          className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-lg transition cursor-pointer"
                        >
                          {actionInProgress ? 'Verifying...' : 'Approve & Verify (Status: VERIFIED)'}
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Hold Modal / Inline Form */}
                  {holding && (
                    <div className="p-4 bg-slate-50 border border-amber-300 rounded-xl space-y-3">
                      <div className="flex items-center justify-between text-xs font-bold text-slate-900">
                        <span className="flex items-center gap-1.5 text-amber-800">
                          <PauseCircle className="w-4 h-4 text-amber-600" />
                          Put Prescription On Hold
                        </span>
                        <button onClick={() => setHolding(false)} className="text-slate-400 hover:text-slate-600 cursor-pointer">✕</button>
                      </div>
                      <div>
                        <label className="text-[11px] font-semibold text-slate-600 block mb-1">
                          Reason for Hold (Clarification with Doctor):
                        </label>
                        <input
                          type="text"
                          value={holdNotes}
                          onChange={(e) => setHoldNotes(e.target.value)}
                          placeholder="e.g. Clarifying allergy contraindication with ordering physician..."
                          className="w-full px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs"
                        />
                      </div>
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => setHolding(false)}
                          className="px-3 py-1.5 border border-slate-300 text-slate-700 font-bold text-xs rounded-lg hover:bg-slate-100 cursor-pointer"
                        >
                          Cancel
                        </button>
                        <button
                          type="button"
                          disabled={actionInProgress}
                          onClick={handleHold}
                          className="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs rounded-lg transition cursor-pointer"
                        >
                          {actionInProgress ? 'Updating...' : 'Put On Hold'}
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Reject Modal / Inline Form */}
                  {rejecting && (
                    <div className="p-4 bg-slate-50 border border-rose-300 rounded-xl space-y-3">
                      <div className="flex items-center justify-between text-xs font-bold text-slate-900">
                        <span className="flex items-center gap-1.5 text-rose-800">
                          <XCircle className="w-4 h-4 text-rose-600" />
                          Reject Prescription
                        </span>
                        <button onClick={() => setRejecting(false)} className="text-slate-400 hover:text-slate-600 cursor-pointer">✕</button>
                      </div>
                      <div>
                        <label className="text-[11px] font-semibold text-slate-600 block mb-1">
                          Mandatory Rejection Reason: <span className="text-rose-600">*</span>
                        </label>
                        <input
                          type="text"
                          value={rejectionReason}
                          onChange={(e) => setRejectionReason(e.target.value)}
                          placeholder="e.g. Prescribed dosage exceeds maximum safe physiological limits..."
                          className="w-full px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs"
                        />
                      </div>
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => setRejecting(false)}
                          className="px-3 py-1.5 border border-slate-300 text-slate-700 font-bold text-xs rounded-lg hover:bg-slate-100 cursor-pointer"
                        >
                          Cancel
                        </button>
                        <button
                          type="button"
                          disabled={actionInProgress || !rejectionReason.trim()}
                          onClick={handleReject}
                          className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs rounded-lg transition cursor-pointer disabled:opacity-50"
                        >
                          {actionInProgress ? 'Rejecting...' : 'Confirm Rejection (Status: REJECTED)'}
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Prescribed Items & FEFO Dispensing Console */}
                <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                    <div className="flex items-center gap-2">
                      <Boxes className="w-5 h-5 text-teal-600" />
                      <h3 className="text-sm font-bold text-slate-900">
                        Prescribed Medications & FEFO Stock Allocation ({selectedRx.items.length})
                      </h3>
                    </div>
                    <div className="text-[11px] text-slate-500 font-mono flex items-center gap-1">
                      <Sparkles className="w-3.5 h-3.5 text-purple-600" />
                      <span>FEFO: First Expired, First Out</span>
                    </div>
                  </div>

                  {/* Items List */}
                  <div className="space-y-4">
                    {selectedRx.items.map((it) => {
                      const med = it.medicine ? medMap.get(it.medicine) : null;
                      const remaining = it.quantity - (it.dispensed_quantity ?? 0);
                      const isComplete = remaining <= 0 || it.status === 'DISPENSED';
                      const fefoBatches = getFefoBatchesForMedicine(it.medicine);
                      const currentAlloc = it.id ? allocations[it.id] : undefined;

                      return (
                        <div
                          key={it.id || it.medicine_name}
                          className={`p-4 rounded-xl border transition ${
                            isComplete
                              ? 'bg-slate-50/50 border-slate-200 opacity-80'
                              : 'bg-white border-teal-200 shadow-xs'
                          }`}
                        >
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-2.5">
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-bold text-sm text-slate-900">
                                  {it.medicine_name || med?.generic_name || `Medicine #${it.medicine}`}
                                </span>
                                {med?.brand_name && (
                                  <span className="text-xs text-slate-500 font-medium">({med.brand_name})</span>
                                )}
                                {med?.regulatory_schedule && (
                                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                                    {med.regulatory_schedule}
                                  </span>
                                )}
                              </div>
                              <div className="text-xs text-slate-500 mt-0.5">
                                Dosage: <strong>{it.dosage}</strong> • Frequency: <strong>{it.frequency}</strong> • Duration: <strong>{it.duration_days} days</strong>
                              </div>
                            </div>

                            <div className="flex items-center gap-3 text-xs">
                              <div className="text-right">
                                <div className="text-[10px] text-slate-400 uppercase font-semibold">Prescribed / Dispensed</div>
                                <div className="font-mono font-bold text-slate-800">
                                  {it.quantity} units / <span className="text-teal-700">{it.dispensed_quantity ?? 0}</span>
                                </div>
                              </div>
                              {isComplete ? (
                                <span className="px-2.5 py-1 rounded-md text-[11px] font-bold bg-blue-100 text-blue-800 flex items-center gap-1">
                                  <Check className="w-3.5 h-3.5" />
                                  Dispensed
                                </span>
                              ) : (
                                <span className="px-2.5 py-1 rounded-md text-[11px] font-bold bg-amber-100 text-amber-800">
                                  {remaining} Remaining
                                </span>
                              )}
                            </div>
                          </div>

                          {/* Allocation Controls if remaining > 0 */}
                          {!isComplete && (
                            <div className="pt-3 space-y-2">
                              {selectedRx.status !== 'VERIFIED' && selectedRx.status !== 'PARTIALLY_DISPENSED' ? (
                                <div className="text-xs text-amber-800 bg-amber-50 p-2.5 rounded-lg border border-amber-200 flex items-center gap-2">
                                  <Info className="w-4 h-4 text-amber-600 shrink-0" />
                                  <span>Prescription verification required before batch allocation and dispensing.</span>
                                </div>
                              ) : fefoBatches.length === 0 ? (
                                <div className="text-xs text-rose-800 bg-rose-50 p-2.5 rounded-lg border border-rose-200 flex items-center gap-2">
                                  <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                                  <span>No valid, active stock batches available in this facility for this medicine!</span>
                                </div>
                              ) : (
                                <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-end">
                                  <div className="sm:col-span-8 space-y-1">
                                    <label className="text-[11px] font-bold text-slate-700 uppercase flex items-center gap-1.5">
                                      <span>Select Batch (FEFO Sorted):</span>
                                      <span className="text-[10px] text-purple-700 font-semibold bg-purple-50 px-1.5 py-0.2 rounded border border-purple-200">
                                        FEFO Prioritized
                                      </span>
                                    </label>
                                    <select
                                      value={currentAlloc?.batch_id || ''}
                                      onChange={(e) => {
                                        const bId = Number(e.target.value);
                                        const bObj = batchMap.get(bId);
                                        if (it.id) {
                                          setAllocations((prev) => ({
                                            ...prev,
                                            [it.id!]: {
                                              batch_id: bId,
                                              quantity: Math.min(remaining, bObj?.available_quantity ?? remaining)
                                            }
                                          }));
                                        }
                                      }}
                                      className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-xs font-mono text-slate-800 focus:outline-none focus:border-teal-600"
                                    >
                                      {fefoBatches.map((b, idx) => (
                                        <option key={b.id} value={b.id}>
                                          {idx === 0 ? '★ [FEFO RECOMMENDED] ' : ''}
                                          Batch #{b.batch_number} • Exp: {b.expiry_date} • Avail: {b.available_quantity} units
                                        </option>
                                      ))}
                                    </select>
                                  </div>

                                  <div className="sm:col-span-4 space-y-1">
                                    <label className="text-[11px] font-bold text-slate-700 uppercase">
                                      Dispense Qty:
                                    </label>
                                    <input
                                      type="number"
                                      min={1}
                                      max={remaining}
                                      value={currentAlloc?.quantity || ''}
                                      onChange={(e) => {
                                        const qty = Math.max(1, Number(e.target.value));
                                        if (it.id) {
                                          setAllocations((prev) => ({
                                            ...prev,
                                            [it.id!]: {
                                              batch_id: prev[it.id!]?.batch_id || fefoBatches[0].id,
                                              quantity: qty
                                            }
                                          }));
                                        }
                                      }}
                                      className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-xs font-mono font-bold text-teal-800 focus:outline-none focus:border-teal-600"
                                    />
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {/* Execute Dispensation Action Button */}
                  {(selectedRx.status === 'VERIFIED' || selectedRx.status === 'PARTIALLY_DISPENSED') && (
                    <div className="pt-4 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div className="text-xs text-slate-500 font-medium">
                        Stock deduction will be posted atomically to <strong className="text-slate-700">InventoryLedger</strong>.
                      </div>
                      <button
                        type="button"
                        disabled={dispensing || Object.keys(allocations).length === 0}
                        onClick={handleExecuteDispensation}
                        className="px-5 py-2.5 bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs rounded-xl shadow-xs transition cursor-pointer disabled:opacity-50 flex items-center justify-center gap-2"
                      >
                        <PackageCheck className="w-4 h-4" />
                        <span>{dispensing ? 'Recording Dispensation...' : 'Confirm & Execute Dispensation'}</span>
                      </button>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="p-16 bg-white rounded-2xl border border-slate-200 shadow-xs text-center space-y-3">
                <Pill className="w-12 h-12 text-slate-300 mx-auto" />
                <h3 className="text-sm font-bold text-slate-800">No Prescription Selected</h3>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">
                  Select a doctor prescription from the queue on the left to verify clinical directions and allocate stock.
                </p>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Authoritative Inventory Ledger Audit Console */
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden space-y-0">
          <div className="p-5 border-b border-slate-200 bg-slate-50/70 space-y-1">
            <div className="flex items-center gap-2">
              <FileSpreadsheet className="w-5 h-5 text-teal-600" />
              <h2 className="text-sm font-bold text-slate-900">
                Authoritative Inventory Ledger (Single Source of Truth)
              </h2>
            </div>
            <p className="text-xs text-slate-500">
              Complete, immutable double-entry ledger for all pharmaceutical movements. React UI displays live ledger data; stock balances are never manipulated locally.
            </p>
          </div>

          {loading ? (
            <div className="p-12 flex justify-center">
              <LoadingSpinner size="lg" label="Loading inventory ledger movements..." />
            </div>
          ) : ledgerEntries.length === 0 ? (
            <div className="p-12 text-center text-xs text-slate-400">
              No inventory movements recorded in this facility.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50/80 text-slate-500 font-bold border-b border-slate-200 uppercase text-[10px] tracking-wider">
                  <tr>
                    <th className="py-3 px-4">Transaction ID / Time</th>
                    <th className="py-3 px-4">Type</th>
                    <th className="py-3 px-4">Medicine / Batch</th>
                    <th className="py-3 px-4 text-right">Delta</th>
                    <th className="py-3 px-4 text-right">Balance After</th>
                    <th className="py-3 px-4">Reference Entity</th>
                    <th className="py-3 px-4">Staff ID</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono">
                  {ledgerEntries.map((l) => {
                    const batch = batchMap.get(l.batch);
                    const med = batch?.medicine ? medMap.get(batch.medicine) : null;

                    return (
                      <tr key={l.id} className="hover:bg-slate-50/60 transition">
                        <td className="py-3.5 px-4">
                          <div className="font-bold text-slate-900">#LEDGER-{String(l.id).padStart(5, '0')}</div>
                          <div className="text-[10px] text-slate-400">{l.transaction_timestamp.replace('T', ' ').slice(0, 19)}</div>
                        </td>

                        <td className="py-3.5 px-4 font-sans">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            l.transaction_type === 'DISPENSE'
                              ? 'bg-blue-50 text-blue-700 border border-blue-200'
                              : l.transaction_type === 'PURCHASE_RECEIPT'
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : 'bg-slate-50 text-slate-700 border border-slate-200'
                          }`}>
                            {l.transaction_type}
                          </span>
                        </td>

                        <td className="py-3.5 px-4 font-sans">
                          <div className="font-semibold text-slate-800">
                            {med?.generic_name || `Medicine #${batch?.medicine || 'Unknown'}`}
                          </div>
                          <div className="text-[10px] text-slate-400 font-mono">
                            Batch: {batch?.batch_number || `#${l.batch}`}
                          </div>
                        </td>

                        <td className={`py-3.5 px-4 text-right font-bold ${
                          l.quantity_delta < 0 ? 'text-rose-600' : 'text-emerald-600'
                        }`}>
                          {l.quantity_delta > 0 ? `+${l.quantity_delta}` : l.quantity_delta}
                        </td>

                        <td className="py-3.5 px-4 text-right font-bold text-slate-900">
                          {l.balance_after}
                        </td>

                        <td className="py-3.5 px-4 font-sans text-[11px] text-slate-600">
                          <div>{l.reference_entity_type} #{l.reference_entity_id}</div>
                          {l.remarks && <div className="text-[10px] text-slate-400 truncate max-w-xs">{l.remarks}</div>}
                        </td>

                        <td className="py-3.5 px-4 text-slate-600 text-xs">
                          Staff #{l.performed_by_staff}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Approved Essential Medicine Formulary Reference Drawer */}
      <div className="bg-slate-50 p-5 rounded-2xl border border-slate-200 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Boxes className="w-4 h-4 text-teal-600" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-teal-900">
              Government UHWC Essential Drug Formulary ({medicines.length} Medicines)
            </h3>
          </div>
          <span className="text-[11px] text-slate-500 font-mono">National List of Essential Medicines (NLEM)</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          {medicines.map((m) => (
            <div key={m.id} className="bg-white p-3 rounded-xl border border-slate-200 text-xs space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-900">{m.generic_name}</span>
                <span className="text-[10px] font-mono px-1 rounded bg-slate-100 text-slate-600">
                  {m.regulatory_schedule || 'OTC'}
                </span>
              </div>
              <div className="text-[11px] text-slate-500">
                Brand: {m.brand_name || 'Generic'} • {m.strength} {m.dosage_form}
              </div>
              <div className="text-[10px] text-slate-400 font-mono pt-0.5">
                Category: {m.category || 'Essential'}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Pharmacy;
