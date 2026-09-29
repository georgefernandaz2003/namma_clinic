import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  getDiagnosticOrders,
  getTestRequests,
  getSpecimens,
  getDiagnosticResults,
  getDiagnosticTestMasters,
  getVisits,
  createSpecimen,
  createDiagnosticResult,
  verifyDiagnosticResult,
  amendDiagnosticResult
} from '../api/clinical';
import { parseApiError } from '../api/client';
import type {
  DiagnosticOrder,
  TestRequest,
  Specimen,
  DiagnosticResult,
  DiagnosticTestMaster,
  Visit
} from '../types';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorAlert from '../components/common/ErrorAlert';
import EmptyState from '../components/common/EmptyState';
import {
  TestTube,
  Clock,
  RotateCcw,
  CheckCircle2,
  Syringe,
  Microscope,
  FileCheck,
  Building2,
  ShieldAlert,
  Search,
  Lock,
  Edit3,
  Calendar,
  BookOpen
} from 'lucide-react';

export const Laboratory: React.FC = () => {
  const { user, activeFacility } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  // Role permissions: Only LAB_TECHNICIAN has operational mutation authority. DOCTOR has read-only clinical review.
  const isLabTech = user?.role === 'LAB_TECHNICIAN';
  const isDoctor = user?.role === 'DOCTOR';

  // Data State
  const [orders, setOrders] = useState<DiagnosticOrder[]>([]);
  const [requests, setRequests] = useState<TestRequest[]>([]);
  const [specimens, setSpecimens] = useState<Specimen[]>([]);
  const [results, setResults] = useState<DiagnosticResult[]>([]);
  const [testMasters, setTestMasters] = useState<DiagnosticTestMaster[]>([]);
  const [visits, setVisits] = useState<Visit[]>([]);

  // Selection & UI State
  const [selectedOrderId, setSelectedOrderId] = useState<number | null>(null);
  const [filterStatus, setFilterStatus] = useState<'ALL' | 'ORDERED' | 'SAMPLE_COLLECTED' | 'RESULT_ENTERED' | 'VERIFIED'>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Form States for Specimen Collection
  const [collectingForOrder, setCollectingForOrder] = useState<boolean>(false);
  const [specimenBarcode, setSpecimenBarcode] = useState<string>('');
  const [specimenType, setSpecimenType] = useState<string>('WHOLE_BLOOD');
  const [selectedReqIdsForSpecimen, setSelectedReqIdsForSpecimen] = useState<number[]>([]);
  const [savingSpecimen, setSavingSpecimen] = useState<boolean>(false);

  // Form States for Result Entry
  const [activeResultEntryReqId, setActiveResultEntryReqId] = useState<number | null>(null);
  const [resultTextVal, setResultTextVal] = useState<string>('');
  const [resultNumericVal, setResultNumericVal] = useState<string>('');
  const [refRangeApplied, setRefRangeApplied] = useState<string>('');
  const [isAbnormal, setIsAbnormal] = useState<boolean>(false);
  const [isCriticalPanic, setIsCriticalPanic] = useState<boolean>(false);
  const [savingResult, setSavingResult] = useState<boolean>(false);

  // Verification & Amendment States
  const [verifyingResultId, setVerifyingResultId] = useState<number | null>(null);
  const [verificationNotice, setVerificationNotice] = useState<string | null>(null);

  const [activeAmendmentResultId, setActiveAmendmentResultId] = useState<number | null>(null);
  const [amendmentReason, setAmendmentReason] = useState<string>('');
  const [amendedTextVal, setAmendedTextVal] = useState<string>('');
  const [amendedNumericVal, setAmendedNumericVal] = useState<string>('');
  const [savingAmendment, setSavingAmendment] = useState<boolean>(false);

  // Load all laboratory clinical data
  const loadLabData = useCallback(async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    else setRefreshing(true);
    setError(null);

    try {
      const [ordersData, reqsData, specsData, resData, mastersData, visitsData] = await Promise.all([
        getDiagnosticOrders(),
        getTestRequests(),
        getSpecimens(),
        getDiagnosticResults(),
        getDiagnosticTestMasters(),
        getVisits()
      ]);

      setOrders(ordersData);
      setRequests(reqsData);
      setSpecimens(specsData);
      setResults(resData);
      setTestMasters(mastersData);
      setVisits(visitsData);

      // Check if order ID is specified in query parameters
      const urlOrderParam = searchParams.get('order');
      if (urlOrderParam) {
        const orderIdNum = Number(urlOrderParam);
        if (ordersData.some((o: DiagnosticOrder) => o.id === orderIdNum)) {
          setSelectedOrderId(orderIdNum);
        }
      } else if (ordersData.length > 0 && !selectedOrderId) {
        setSelectedOrderId(ordersData[0].id);
      }
    } catch (err) {
      setError(parseApiError(err));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [searchParams, selectedOrderId]);

  useEffect(() => {
    loadLabData();
  }, [loadLabData]);

  // Lookup maps
  const visitMap = new Map(visits.map((v) => [v.id, v]));
  const testMasterMap = new Map(testMasters.map((t) => [t.id, t]));
  const specimenMap = new Map(specimens.map((s) => [s.id, s]));

  const selectedOrder = orders.find((o) => o.id === selectedOrderId) || null;
  const selectedVisit = selectedOrder ? visitMap.get(selectedOrder.visit) : null;
  const selectedOrderRequests = selectedOrder
    ? requests.filter((r) => r.diagnostic_order === selectedOrder.id)
    : [];

  // Filtered orders list
  const filteredOrders = orders.filter((order) => {
    if (filterStatus !== 'ALL' && order.status !== filterStatus) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const visit = visitMap.get(order.visit);
      const patName = (visit?.patient_details?.name || '').toLowerCase();
      const uhid = (visit?.patient_details?.uhid || '').toLowerCase();
      const ordNum = order.order_number.toLowerCase();
      return patName.includes(q) || uhid.includes(q) || ordNum.includes(q);
    }
    return true;
  });

  // Handle Order Selection
  const handleSelectOrder = (orderId: number) => {
    setSelectedOrderId(orderId);
    setSearchParams({ order: String(orderId) });
    setCollectingForOrder(false);
    setActiveResultEntryReqId(null);
    setActiveAmendmentResultId(null);
    setVerificationNotice(null);
    setError(null);
    setSuccessMsg(null);
  };

  // Specimen Collection Handler
  const handleOpenSpecimenModal = () => {
    if (!selectedOrder) return;
    // Default to first pending request specimen type or test master
    const pendingReqs = selectedOrderRequests.filter((r) => !r.specimen);
    const firstTm = pendingReqs.length > 0 ? testMasterMap.get(pendingReqs[0].test_master) : null;
    const defaultType = firstTm ? firstTm.specimen_type : 'WHOLE_BLOOD';

    // Generate compliant specimen accession barcode
    const barcodeSuffix = selectedOrder ? String(selectedOrder.id).padStart(4, '0') : '0001';
    setSpecimenBarcode(`SMP-2026-${barcodeSuffix}`);
    setSpecimenType(defaultType || 'WHOLE_BLOOD');
    setSelectedReqIdsForSpecimen(pendingReqs.map((r) => r.id));
    setCollectingForOrder(true);
  };

  const handleSaveSpecimen = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrder) return;
    if (!specimenBarcode.trim()) {
      setError('Barcode identifier is required.');
      return;
    }

    setSavingSpecimen(true);
    setError(null);
    setSuccessMsg(null);

    try {
      await createSpecimen({
        diagnostic_order: selectedOrder.id,
        barcode_identifier: specimenBarcode.trim().toUpperCase(),
        specimen_type: specimenType,
        test_request_ids: selectedReqIdsForSpecimen
      });

      setSuccessMsg(`Specimen [${specimenBarcode.trim().toUpperCase()}] collected successfully! Linked to ${selectedReqIdsForSpecimen.length} test(s).`);
      setCollectingForOrder(false);
      await loadLabData(true);
    } catch (err) {
      setError(parseApiError(err));
    } finally {
      setSavingSpecimen(false);
    }
  };

  // Result Entry Handler
  const handleOpenResultEntry = (req: TestRequest) => {
    const tm = testMasterMap.get(req.test_master);
    setActiveResultEntryReqId(req.id);
    setResultTextVal('');
    setResultNumericVal('');
    setRefRangeApplied(tm?.reference_range_male || tm?.reference_range_female || '');
    setIsAbnormal(false);
    setIsCriticalPanic(false);
    setError(null);
  };

  const handleSaveResult = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeResultEntryReqId) return;

    if (!resultTextVal.trim() && resultNumericVal === '') {
      setError('Please provide at least a numeric result value or descriptive text result.');
      return;
    }

    setSavingResult(true);
    setError(null);
    setSuccessMsg(null);

    try {
      await createDiagnosticResult({
        test_request: activeResultEntryReqId,
        result_value_text: resultTextVal.trim(),
        result_value_numeric: resultNumericVal !== '' ? Number(resultNumericVal) : null,
        reference_range_applied: refRangeApplied.trim(),
        is_abnormal: isAbnormal,
        is_critical_panic: isCriticalPanic
      });

      setSuccessMsg('Diagnostic test result entered successfully! Status transitioned to ENTERED.');
      setActiveResultEntryReqId(null);
      await loadLabData(true);
    } catch (err) {
      setError(parseApiError(err));
    } finally {
      setSavingResult(false);
    }
  };

  // Verification Handler
  const handleVerifyResult = async (resultId: number) => {
    setVerifyingResultId(resultId);
    setError(null);
    setSuccessMsg(null);
    setVerificationNotice(null);

    try {
      const verified = await verifyDiagnosticResult(resultId);
      setSuccessMsg(`Result #${verified.id} successfully verified and released to EMR!`);
      await loadLabData(true);
    } catch (err) {
      const parsedErr = parseApiError(err);
      if (parsedErr.includes('403') || parsedErr.includes('permission') || parsedErr.includes('Forbidden')) {
        setVerificationNotice(
          'Authoritative Separation-of-Duties: The backend enforces that only Medical Officers (Doctors) are authorized to verify results in this clinic deployment (HTTP 403). The result remains securely in ENTERED status awaiting Doctor review.'
        );
      } else {
        setError(parsedErr);
      }
    } finally {
      setVerifyingResultId(null);
    }
  };

  // Amendment Handler
  const handleOpenAmendment = (res: DiagnosticResult) => {
    setActiveAmendmentResultId(res.id);
    setAmendmentReason('');
    setAmendedTextVal(res.result_value_text || '');
    setAmendedNumericVal(res.result_value_numeric !== null && res.result_value_numeric !== undefined ? String(res.result_value_numeric) : '');
    setError(null);
  };

  const handleSaveAmendment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeAmendmentResultId) return;

    if (!amendmentReason.trim()) {
      setError('Amendment reason is mandatory when correcting a verified result.');
      return;
    }

    setSavingAmendment(true);
    setError(null);
    setSuccessMsg(null);

    try {
      await amendDiagnosticResult(activeAmendmentResultId, {
        amendment_reason: amendmentReason.trim(),
        amended_value_text: amendedTextVal.trim(),
        amended_value_numeric: amendedNumericVal !== '' ? Number(amendedNumericVal) : null
      });

      setSuccessMsg('Result successfully amended! Historical record preserved in audit log.');
      setActiveAmendmentResultId(null);
      await loadLabData(true);
    } catch (err) {
      setError(parseApiError(err));
    } finally {
      setSavingAmendment(false);
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'STAT':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200">
            STAT
          </span>
        );
      case 'URGENT':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
            URGENT
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
            ROUTINE
          </span>
        );
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ORDERED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-100 text-purple-800">ORDERED</span>;
      case 'SAMPLE_COLLECTED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800">SAMPLE DRAWN</span>;
      case 'IN_TESTING':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-100 text-cyan-800">IN TESTING</span>;
      case 'RESULT_ENTERED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">ENTERED</span>;
      case 'VERIFIED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">VERIFIED</span>;
      case 'AMENDED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-100 text-indigo-800">AMENDED</span>;
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
            <TestTube className="w-6 h-6 text-purple-600" />
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Laboratory Clinical Workstation
            </h1>
            {isDoctor && (
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-sky-100 text-sky-800 border border-sky-200">
                Doctor Review Mode (Read-Only)
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 font-medium">
            Essential point-of-care diagnostics, specimen barcoding, result entry & verification pipeline
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

        <button
          onClick={() => loadLabData(true)}
          disabled={loading || refreshing}
          className="flex items-center gap-1.5 px-3 py-2 bg-slate-50 hover:bg-slate-100 text-slate-700 font-semibold text-xs rounded-xl border border-slate-200 transition cursor-pointer disabled:opacity-50 self-start sm:self-center"
        >
          <RotateCcw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          <span>{refreshing ? 'Refreshing...' : 'Refresh Laboratory Data'}</span>
        </button>
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

      {/* Main Grid: Orders Queue (Left) vs Workstation Detail (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Requisition Queue */}
        <div className="lg:col-span-4 bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden space-y-0">
          <div className="p-4 border-b border-slate-200 bg-slate-50/70 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Clock className="w-4 h-4 text-purple-600" />
                Laboratory Queue ({filteredOrders.length})
              </h2>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-purple-100 text-purple-800">
                {orders.length} Total
              </span>
            </div>

            {/* Search Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search patient, UHID, or order #..."
                className="w-full pl-8 pr-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs placeholder:text-slate-400 focus:outline-none focus:border-purple-600"
              />
            </div>

            {/* Filter Tabs */}
            <div className="flex flex-wrap gap-1">
              {(['ALL', 'ORDERED', 'SAMPLE_COLLECTED', 'RESULT_ENTERED', 'VERIFIED'] as const).map((status) => (
                <button
                  key={status}
                  onClick={() => setFilterStatus(status)}
                  className={`px-2 py-1 rounded text-[10px] font-bold transition cursor-pointer ${
                    filterStatus === status
                      ? 'bg-purple-600 text-white'
                      : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  {status}
                </button>
              ))}
            </div>
          </div>

          {/* Queue Items List */}
          {loading ? (
            <div className="p-8 flex justify-center">
              <LoadingSpinner size="md" label="Loading requisitions..." />
            </div>
          ) : filteredOrders.length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-400">
              No laboratory orders match your criteria.
            </div>
          ) : (
            <div className="divide-y divide-slate-100 max-h-[640px] overflow-y-auto">
              {filteredOrders.map((ord) => {
                const visit = visitMap.get(ord.visit);
                const isSelected = ord.id === selectedOrderId;
                const orderReqs = requests.filter((r) => r.diagnostic_order === ord.id);

                return (
                  <button
                    key={ord.id}
                    onClick={() => handleSelectOrder(ord.id)}
                    className={`w-full text-left p-3.5 transition flex flex-col gap-1 cursor-pointer ${
                      isSelected
                        ? 'bg-purple-50/80 border-l-4 border-purple-600'
                        : 'hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-slate-900 truncate">
                        {visit?.patient_details?.name || `Patient #${visit?.patient || ord.visit}`}
                      </span>
                      {getPriorityBadge(ord.priority)}
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-slate-500 font-mono">
                      <span className="text-purple-700 font-bold">{ord.order_number}</span>
                      <span>{ord.order_date}</span>
                    </div>

                    <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1">
                      <span>{orderReqs.length} Investigation(s)</span>
                      {getStatusBadge(ord.status)}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Workstation Console & Investigation Processing */}
        <div className="lg:col-span-8 space-y-5">
          {selectedOrder ? (
            <>
              {/* Patient & Order Header Banner */}
              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-base font-bold text-slate-900">
                        {selectedVisit?.patient_details?.name || `Patient #${selectedVisit?.patient || 'Unknown'}`}
                      </h2>
                      {getPriorityBadge(selectedOrder.priority)}
                      {getStatusBadge(selectedOrder.status)}
                    </div>
                    <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 font-mono mt-1">
                      <span>UHID: <strong>{selectedVisit?.patient_details?.uhid || 'N/A'}</strong></span>
                      <span>•</span>
                      <span>Age: {selectedVisit?.patient_details?.age || 'N/A'}</span>
                      <span>•</span>
                      <span>Gender: {selectedVisit?.patient_details?.gender || 'N/A'}</span>
                      <span>•</span>
                      <span>Visit Token: #{selectedVisit?.token_number || selectedOrder.visit}</span>
                    </div>
                  </div>

                  <div className="text-right text-xs">
                    <div className="font-mono font-bold text-purple-700">{selectedOrder.order_number}</div>
                    <div className="text-slate-400 text-[11px] flex items-center justify-end gap-1">
                      <Calendar className="w-3 h-3" />
                      {selectedOrder.order_date}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs bg-slate-50 p-3 rounded-xl border border-slate-200">
                  <div>
                    <span className="text-[11px] text-slate-500 font-semibold block">Clinical Indication:</span>
                    <span className="text-slate-800 font-medium">
                      {selectedOrder.clinical_indication || 'Routine diagnostic evaluation'}
                    </span>
                  </div>
                  <div>
                    <span className="text-[11px] text-slate-500 font-semibold block">Ordering Clinician:</span>
                    <span className="text-slate-800 font-medium">
                      Staff ID #{selectedOrder.ordering_doctor_staff || 'Medical Officer'} (Locked - separation of duties)
                    </span>
                  </div>
                </div>

                {/* Specimen Collection Action Banner */}
                {isLabTech && selectedOrderRequests.some((r) => !r.specimen) && !collectingForOrder && (
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl flex items-center justify-between">
                    <div className="flex items-center gap-2 text-xs text-blue-900 font-medium">
                      <Syringe className="w-4 h-4 text-blue-600" />
                      <span>One or more requested tests require biological specimen collection.</span>
                    </div>
                    <button
                      onClick={handleOpenSpecimenModal}
                      className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-lg shadow-xs transition cursor-pointer"
                    >
                      Collect Specimen
                    </button>
                  </div>
                )}
              </div>

              {/* Specimen Collection Form (Inline Panel) */}
              {collectingForOrder && isLabTech && (
                <div className="bg-white p-5 rounded-2xl border-2 border-blue-400 shadow-md space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                    <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                      <Syringe className="w-4 h-4 text-blue-600" />
                      Biological Specimen Collection & Barcode Accessioning
                    </h3>
                    <button
                      onClick={() => setCollectingForOrder(false)}
                      className="text-slate-400 hover:text-slate-700 text-xs font-bold cursor-pointer"
                    >
                      Cancel
                    </button>
                  </div>

                  <form onSubmit={handleSaveSpecimen} className="space-y-4 text-xs">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-[11px] font-bold text-slate-700 mb-1">
                          Barcode Identifier <span className="text-rose-500">*</span>
                        </label>
                        <input
                          type="text"
                          value={specimenBarcode}
                          onChange={(e) => setSpecimenBarcode(e.target.value)}
                          placeholder="e.g. SMP-2026-8492"
                          className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 font-mono font-bold focus:outline-none focus:border-blue-600 uppercase"
                          required
                        />
                        <span className="text-[10px] text-slate-400 mt-0.5 block">
                          Manual accession barcode entry supported per UHWC protocol.
                        </span>
                      </div>

                      <div>
                        <label className="block text-[11px] font-bold text-slate-700 mb-1">
                          Specimen Type <span className="text-rose-500">*</span>
                        </label>
                        <select
                          value={specimenType}
                          onChange={(e) => setSpecimenType(e.target.value)}
                          className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 font-bold focus:outline-none focus:border-blue-600"
                        >
                          <option value="WHOLE_BLOOD">WHOLE_BLOOD (EDTA / Heparin)</option>
                          <option value="SERUM">SERUM (Plain Clot Activator)</option>
                          <option value="PLASMA">PLASMA (Fluoride / Citrate)</option>
                          <option value="URINE">URINE (Clean Catch Sterile Container)</option>
                          <option value="SPUTUM">SPUTUM</option>
                          <option value="SWAB">SWAB (Nasopharyngeal / Throat)</option>
                        </select>
                      </div>
                    </div>

                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 mb-1.5">
                        Link to Requisitioned Test Investigations:
                      </label>
                      <div className="space-y-1.5 bg-slate-50 p-3 rounded-xl border border-slate-200">
                        {selectedOrderRequests.map((req) => {
                          const tm = testMasterMap.get(req.test_master);
                          const isChecked = selectedReqIdsForSpecimen.includes(req.id);

                          return (
                            <label key={req.id} className="flex items-center gap-2 cursor-pointer">
                              <input
                                type="checkbox"
                                checked={isChecked}
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    setSelectedReqIdsForSpecimen([...selectedReqIdsForSpecimen, req.id]);
                                  } else {
                                    setSelectedReqIdsForSpecimen(selectedReqIdsForSpecimen.filter((id) => id !== req.id));
                                  }
                                }}
                                className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4 cursor-pointer"
                              />
                              <span className="font-mono font-bold text-slate-800">
                                {tm ? tm.test_code : `TR #${req.id}`}
                              </span>
                              <span className="text-slate-600">
                                — {tm ? tm.test_name : 'Unknown Test'} ({tm?.category})
                              </span>
                            </label>
                          );
                        })}
                      </div>
                    </div>

                    <div className="flex justify-end gap-2 pt-2">
                      <button
                        type="button"
                        onClick={() => setCollectingForOrder(false)}
                        className="px-4 py-2 border border-slate-300 text-slate-700 font-bold text-xs rounded-xl hover:bg-slate-50 transition cursor-pointer"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={savingSpecimen || selectedReqIdsForSpecimen.length === 0}
                        className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl shadow-xs transition cursor-pointer disabled:opacity-50 flex items-center gap-1.5"
                      >
                        {savingSpecimen ? <LoadingSpinner size="sm" /> : <CheckCircle2 className="w-4 h-4" />}
                        <span>Confirm Specimen Collection</span>
                      </button>
                    </div>
                  </form>
                </div>
              )}

              {/* Verification Notice Callout if Doctor Authorization Check Triggered */}
              {verificationNotice && (
                <div className="p-4 bg-amber-50 border border-amber-300 rounded-2xl text-xs text-amber-900 space-y-1">
                  <div className="flex items-center gap-2 font-bold text-amber-950">
                    <ShieldAlert className="w-4 h-4 text-amber-600" />
                    Separation-of-Duties Notice
                  </div>
                  <p className="font-medium text-slate-700">{verificationNotice}</p>
                </div>
              )}

              {/* Investigation Pipeline: Individual Test Cards */}
              <div className="space-y-4">
                <div className="flex items-center justify-between text-xs font-bold text-slate-700 px-1">
                  <span className="uppercase tracking-wider flex items-center gap-1.5">
                    <Microscope className="w-4 h-4 text-purple-600" />
                    Requested Investigations & Diagnostic Results ({selectedOrderRequests.length})
                  </span>
                </div>

                {selectedOrderRequests.length === 0 ? (
                  <div className="p-8 bg-white rounded-2xl border border-slate-200 text-center text-xs text-slate-400">
                    No individual test requests found under this order.
                  </div>
                ) : (
                  selectedOrderRequests.map((req) => {
                    const tm = testMasterMap.get(req.test_master);
                    const specimen = req.specimen ? specimenMap.get(req.specimen) : null;
                    const res = results.find((r) => r.test_request === req.id) || null;

                    const isEnteringResult = activeResultEntryReqId === req.id;
                    const isAmendingResult = activeAmendmentResultId === res?.id;

                    return (
                      <div
                        key={req.id}
                        className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-4"
                      >
                        {/* Investigation Card Header */}
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-mono font-bold text-xs px-2 py-0.5 rounded bg-purple-100 text-purple-900">
                                {tm?.test_code || 'TEST'}
                              </span>
                              <h4 className="font-bold text-slate-900 text-sm">
                                {tm?.test_name || `Investigation #${req.id}`}
                              </h4>
                            </div>
                            <div className="text-[11px] text-slate-500 mt-0.5">
                              Category: <strong className="text-slate-700">{tm?.category || 'PATHOLOGY'}</strong> • Standard Unit: {tm?.default_unit || 'N/A'}
                            </div>
                          </div>

                          <div className="flex items-center gap-2 text-xs">
                            <span className="text-[11px] text-slate-500 font-semibold">Status:</span>
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-800">
                              {req.status}
                            </span>
                          </div>
                        </div>

                        {/* Specimen Association Info */}
                        <div className="text-xs bg-slate-50 p-3 rounded-xl border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <Syringe className="w-3.5 h-3.5 text-purple-600" />
                            <span className="font-semibold text-slate-700">Specimen:</span>
                            {specimen ? (
                              <span className="font-mono font-bold text-emerald-800">
                                {specimen.barcode_identifier} ({specimen.specimen_type})
                              </span>
                            ) : (
                              <span className="text-amber-700 font-semibold">
                                Pending Collection (Draw required: {tm?.specimen_type || 'BLOOD'})
                              </span>
                            )}
                          </div>
                          {specimen && (
                            <span className="text-[11px] text-slate-400 font-mono">
                              Collected: {specimen.collected_at ? new Date(specimen.collected_at).toLocaleTimeString() : 'Recorded'}
                            </span>
                          )}
                        </div>

                        {/* Existing Result View */}
                        {res && !isAmendingResult && (
                          <div className="p-4 rounded-xl border border-slate-200 bg-purple-50/20 space-y-3">
                            <div className="flex items-center justify-between border-b border-purple-100 pb-2">
                              <div className="flex items-center gap-2">
                                <FileCheck className="w-4 h-4 text-purple-700" />
                                <span className="font-bold text-slate-900 text-xs">Recorded Diagnostic Analysis</span>
                                {res.is_abnormal && (
                                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">
                                    ABNORMAL
                                  </span>
                                )}
                                {res.is_critical_panic && (
                                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-300 animate-pulse">
                                    CRITICAL PANIC
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center gap-2">
                                <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                                  res.status === 'VERIFIED'
                                    ? 'bg-emerald-100 text-emerald-900'
                                    : res.status === 'AMENDED'
                                    ? 'bg-indigo-100 text-indigo-900'
                                    : 'bg-amber-100 text-amber-900'
                                }`}>
                                  {res.status}
                                </span>
                              </div>
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                              <div>
                                <span className="text-[10px] text-slate-500 uppercase font-bold block">Result Value</span>
                                <span className="text-sm font-black text-slate-900 font-mono">
                                  {res.result_value_text || res.result_value_numeric || 'Recorded'} {tm?.default_unit}
                                </span>
                              </div>
                              <div>
                                <span className="text-[10px] text-slate-500 uppercase font-bold block">Reference Range Applied</span>
                                <span className="text-xs font-mono font-medium text-slate-700">
                                  {res.reference_range_applied || tm?.reference_range_male || 'Established Standard'}
                                </span>
                              </div>
                              <div>
                                <span className="text-[10px] text-slate-500 uppercase font-bold block">Authorship & Timestamp</span>
                                <span className="text-[11px] text-slate-600 block">
                                  Entered by Staff #{res.entered_by_staff || 'Technician'}
                                </span>
                                {res.verified_at && (
                                  <span className="text-[11px] text-emerald-700 block font-medium">
                                    Verified by Staff #{res.verified_by_staff} on {new Date(res.verified_at).toLocaleDateString()}
                                  </span>
                                )}
                              </div>
                            </div>

                            {/* Actions on Result */}
                            <div className="flex items-center justify-end gap-2 pt-2 border-t border-purple-100">
                              {/* If ENTERED: Verification Action */}
                              {res.status === 'ENTERED' && (
                                <button
                                  onClick={() => handleVerifyResult(res.id)}
                                  disabled={verifyingResultId === res.id}
                                  className="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs rounded-lg transition cursor-pointer flex items-center gap-1.5"
                                >
                                  {verifyingResultId === res.id ? (
                                    <LoadingSpinner size="sm" />
                                  ) : (
                                    <Lock className="w-3.5 h-3.5" />
                                  )}
                                  <span>Verify Result</span>
                                </button>
                              )}

                              {/* If VERIFIED or AMENDED: Amendment Action */}
                              {isLabTech && (res.status === 'VERIFIED' || res.status === 'AMENDED') && (
                                <button
                                  onClick={() => handleOpenAmendment(res)}
                                  className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-lg transition cursor-pointer flex items-center gap-1.5"
                                >
                                  <Edit3 className="w-3.5 h-3.5 text-slate-600" />
                                  <span>Amend Result</span>
                                </button>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Result Entry Form */}
                        {isEnteringResult && isLabTech && (
                          <form onSubmit={handleSaveResult} className="p-4 rounded-xl border-2 border-purple-400 bg-white space-y-3 text-xs">
                            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                              <span className="font-bold text-slate-900 text-xs flex items-center gap-1.5">
                                <TestTube className="w-4 h-4 text-purple-600" />
                                Enter Diagnostic Result for {tm?.test_name}
                              </span>
                              <button
                                type="button"
                                onClick={() => setActiveResultEntryReqId(null)}
                                className="text-slate-400 hover:text-slate-700 font-bold"
                              >
                                Cancel
                              </button>
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                              <div>
                                <label className="block text-[11px] font-bold text-slate-700 mb-1">
                                  Result Value (Numeric)
                                </label>
                                <input
                                  type="number"
                                  step="any"
                                  value={resultNumericVal}
                                  onChange={(e) => setResultNumericVal(e.target.value)}
                                  placeholder={`e.g. 12.5 ${tm?.default_unit || ''}`}
                                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 font-mono font-bold focus:outline-none focus:border-purple-600"
                                />
                              </div>

                              <div>
                                <label className="block text-[11px] font-bold text-slate-700 mb-1">
                                  Result Value (Text / Descriptive)
                                </label>
                                <input
                                  type="text"
                                  value={resultTextVal}
                                  onChange={(e) => setResultTextVal(e.target.value)}
                                  placeholder="e.g. Negative, Reactive, or Normal"
                                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-purple-600"
                                />
                              </div>
                            </div>

                            <div>
                              <label className="block text-[11px] font-bold text-slate-700 mb-1">
                                Reference Range Applied
                              </label>
                              <input
                                type="text"
                                value={refRangeApplied}
                                onChange={(e) => setRefRangeApplied(e.target.value)}
                                placeholder="Reference range from approved catalogue"
                                className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-700 font-mono text-[11px] focus:outline-none focus:border-purple-600"
                              />
                            </div>

                            <div className="flex items-center gap-4 pt-1">
                              <label className="flex items-center gap-1.5 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={isAbnormal}
                                  onChange={(e) => setIsAbnormal(e.target.checked)}
                                  className="rounded text-amber-600 focus:ring-amber-500 w-4 h-4 cursor-pointer"
                                />
                                <span className="font-bold text-amber-900">Abnormal Result Flag</span>
                              </label>

                              <label className="flex items-center gap-1.5 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={isCriticalPanic}
                                  onChange={(e) => setIsCriticalPanic(e.target.checked)}
                                  className="rounded text-rose-600 focus:ring-rose-500 w-4 h-4 cursor-pointer"
                                />
                                <span className="font-bold text-rose-900">Critical / Panic Value Alert</span>
                              </label>
                            </div>

                            <div className="flex justify-end gap-2 pt-2">
                              <button
                                type="button"
                                onClick={() => setActiveResultEntryReqId(null)}
                                className="px-3 py-1.5 border border-slate-300 text-slate-700 font-bold text-xs rounded-lg hover:bg-slate-50 cursor-pointer"
                              >
                                Cancel
                              </button>
                              <button
                                type="submit"
                                disabled={savingResult}
                                className="px-4 py-1.5 bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs rounded-lg shadow-xs transition cursor-pointer flex items-center gap-1.5"
                              >
                                {savingResult ? <LoadingSpinner size="sm" /> : <CheckCircle2 className="w-4 h-4" />}
                                <span>Save Result (Status: ENTERED)</span>
                              </button>
                            </div>
                          </form>
                        )}

                        {/* Result Amendment Form */}
                        {isAmendingResult && isLabTech && (
                          <form onSubmit={handleSaveAmendment} className="p-4 rounded-xl border-2 border-indigo-400 bg-white space-y-3 text-xs">
                            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                              <span className="font-bold text-indigo-900 text-xs flex items-center gap-1.5">
                                <Edit3 className="w-4 h-4 text-indigo-600" />
                                Amend Verified Result #{res?.id} (Append-only audit trail)
                              </span>
                              <button
                                type="button"
                                onClick={() => setActiveAmendmentResultId(null)}
                                className="text-slate-400 hover:text-slate-700 font-bold"
                              >
                                Cancel
                              </button>
                            </div>

                            <div>
                              <label className="block text-[11px] font-bold text-slate-700 mb-1">
                                Amendment Reason <span className="text-rose-500">*</span>
                              </label>
                              <input
                                type="text"
                                value={amendmentReason}
                                onChange={(e) => setAmendmentReason(e.target.value)}
                                placeholder="Mandatory reason (e.g. Dilution check, instrument re-calibration)"
                                className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-indigo-600"
                                required
                              />
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                              <div>
                                <label className="block text-[11px] font-bold text-slate-700 mb-1">
                                  Amended Numeric Value
                                </label>
                                <input
                                  type="number"
                                  step="any"
                                  value={amendedNumericVal}
                                  onChange={(e) => setAmendedNumericVal(e.target.value)}
                                  placeholder="Amended numeric value"
                                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 font-mono font-bold focus:outline-none focus:border-indigo-600"
                                />
                              </div>

                              <div>
                                <label className="block text-[11px] font-bold text-slate-700 mb-1">
                                  Amended Text Value
                                </label>
                                <input
                                  type="text"
                                  value={amendedTextVal}
                                  onChange={(e) => setAmendedTextVal(e.target.value)}
                                  placeholder="Amended descriptive text"
                                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:border-indigo-600"
                                />
                              </div>
                            </div>

                            <div className="flex justify-end gap-2 pt-2">
                              <button
                                type="button"
                                onClick={() => setActiveAmendmentResultId(null)}
                                className="px-3 py-1.5 border border-slate-300 text-slate-700 font-bold text-xs rounded-lg hover:bg-slate-50 cursor-pointer"
                              >
                                Cancel
                              </button>
                              <button
                                type="submit"
                                disabled={savingAmendment || !amendmentReason.trim()}
                                className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs rounded-lg shadow-xs transition cursor-pointer flex items-center gap-1.5"
                              >
                                {savingAmendment ? <LoadingSpinner size="sm" /> : <CheckCircle2 className="w-4 h-4" />}
                                <span>Submit Immutable Amendment</span>
                              </button>
                            </div>
                          </form>
                        )}

                        {/* No result yet banner */}
                        {!res && !isEnteringResult && (
                          <div className="flex items-center justify-between bg-slate-50 p-3 rounded-xl border border-dashed border-slate-200 text-xs">
                            <span className="text-slate-500 font-medium">
                              {specimen ? 'Specimen collected — ready for analytical result entry.' : 'Awaiting biological sample draw before testing.'}
                            </span>
                            {isLabTech && specimen && (
                              <button
                                onClick={() => handleOpenResultEntry(req)}
                                className="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs rounded-lg transition cursor-pointer flex items-center gap-1"
                              >
                                <TestTube className="w-3.5 h-3.5" />
                                <span>Enter Result</span>
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </>
          ) : (
            <div className="bg-white p-12 rounded-2xl border border-slate-200 text-center">
              <EmptyState
                title="Select a Diagnostic Requisition"
                description="Select an order from the laboratory queue on the left to view requested investigations, log specimens, and enter test results."
              />
            </div>
          )}

          {/* Approved 14 Essential Diagnostics Reference Catalogue Card */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-purple-900 flex items-center gap-1.5">
                <BookOpen className="w-4 h-4 text-purple-600" />
                Approved Essential Diagnostic Test Catalogue ({testMasters.length} tests)
              </h3>
              <span className="text-[10px] text-slate-500 font-mono">Government UHWC Standard</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 text-xs">
              {testMasters.map((tm) => (
                <div key={tm.id} className="p-2.5 rounded-xl border border-slate-200 bg-slate-50/60 space-y-1">
                  <div className="flex items-center justify-between font-mono">
                    <span className="font-bold text-purple-800 text-xs">{tm.test_code}</span>
                    <span className="text-[10px] text-slate-500 font-semibold">{tm.category}</span>
                  </div>
                  <div className="font-bold text-slate-900 text-xs truncate">{tm.test_name}</div>
                  <div className="text-[10px] text-slate-500 flex justify-between">
                    <span>Draw: {tm.specimen_type}</span>
                    <span>Ref: {tm.reference_range_male || 'Standard'}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Laboratory;
