import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  getDiagnosticOrders,
  getTestRequests,
  getSpecimens,
  getDiagnosticResults,
  getDiagnosticTestMasters,
  getVisits
} from '../../api/clinical';
import { parseApiError } from '../../api/client';
import type {
  DiagnosticOrder,
  TestRequest,
  Specimen,
  DiagnosticResult,
  DiagnosticTestMaster,
  Visit
} from '../../types';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import EmptyState from '../../components/common/EmptyState';
import {
  TestTube,
  Clock,
  RotateCcw,
  ArrowRight,
  Building2,
  AlertTriangle,
  FileCheck,
  CheckCircle2,
  Syringe,
  Microscope,
  BookOpen
} from 'lucide-react';

export const LabDashboard: React.FC = () => {
  const { user, activeFacility } = useAuth();
  const navigate = useNavigate();

  const [orders, setOrders] = useState<DiagnosticOrder[]>([]);
  const [requests, setRequests] = useState<TestRequest[]>([]);
  const [specimens, setSpecimens] = useState<Specimen[]>([]);
  const [results, setResults] = useState<DiagnosticResult[]>([]);
  const [testMasters, setTestMasters] = useState<DiagnosticTestMaster[]>([]);
  const [visits, setVisits] = useState<Visit[]>([]);

  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Filter Tab: 'ALL' | 'AWAITING_SPECIMEN' | 'IN_TESTING' | 'AWAITING_VERIFY' | 'VERIFIED'
  const [filterTab, setFilterTab] = useState<'ALL' | 'AWAITING_SPECIMEN' | 'IN_TESTING' | 'AWAITING_VERIFY' | 'VERIFIED'>('ALL');

  const loadDashboardData = useCallback(async (isSilent = false) => {
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
    } catch (err) {
      setError(parseApiError(err));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  // Authoritative Derived Metric Counters
  const pendingOrdersCount = orders.filter((o) => o.status === 'ORDERED').length;

  const specimensToCollectCount = requests.filter(
    (r) => !r.specimen && r.status !== 'CANCELLED' && r.status !== 'COMPLETED'
  ).length;

  const inTestingCount = requests.filter(
    (r) => (r.specimen || r.status === 'IN_TESTING') && !results.some((res) => res.test_request === r.id)
  ).length;

  const awaitingVerificationCount = results.filter((res) => res.status === 'ENTERED').length;

  const verifiedCount = results.filter((res) => res.status === 'VERIFIED' || res.status === 'AMENDED').length;

  const statOrUrgentCount = orders.filter(
    (o) => (o.priority === 'STAT' || o.priority === 'URGENT') && o.status !== 'VERIFIED' && o.status !== 'CANCELLED'
  ).length;

  // Helper lookups
  const visitMap = new Map(visits.map((v) => [v.id, v]));
  const testMasterMap = new Map(testMasters.map((t) => [t.id, t]));

  // Filtering orders
  const filteredOrders = orders.filter((order) => {
    const orderReqs = requests.filter((r) => r.diagnostic_order === order.id);
    const orderResults = results.filter((res) => orderReqs.some((r) => r.id === res.test_request));

    if (filterTab === 'AWAITING_SPECIMEN') {
      return orderReqs.some((r) => !r.specimen && r.status !== 'COMPLETED' && r.status !== 'CANCELLED');
    }
    if (filterTab === 'IN_TESTING') {
      return orderReqs.some((r) => r.specimen && !results.some((res) => res.test_request === r.id));
    }
    if (filterTab === 'AWAITING_VERIFY') {
      return orderResults.some((res) => res.status === 'ENTERED');
    }
    if (filterTab === 'VERIFIED') {
      return orderResults.some((res) => res.status === 'VERIFIED' || res.status === 'AMENDED');
    }
    return true;
  });

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'STAT':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200 animate-pulse">
            STAT / Emergency
          </span>
        );
      case 'URGENT':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
            Urgent
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
            Routine
          </span>
        );
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ORDERED':
        return (
          <span className="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-purple-50 text-purple-700 border border-purple-200">
            Ordered
          </span>
        );
      case 'SAMPLE_COLLECTED':
        return (
          <span className="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            Sample Collected
          </span>
        );
      case 'IN_TESTING':
        return (
          <span className="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-cyan-50 text-cyan-700 border border-cyan-200">
            In Testing
          </span>
        );
      case 'RESULT_ENTERED':
        return (
          <span className="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            Result Entered
          </span>
        );
      case 'VERIFIED':
        return (
          <span className="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            Verified
          </span>
        );
      case 'AMENDED':
        return (
          <span className="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
            Amended
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
            <TestTube className="w-6 h-6 text-purple-600" />
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Laboratory Technician Dashboard
            </h1>
          </div>
          <p className="text-xs text-slate-500 font-medium">
            Diagnostic requisitions, biological specimen collection, result entry & verification queue
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
            onClick={() => navigate('/lab')}
            className="flex items-center gap-1.5 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs rounded-xl shadow-xs transition cursor-pointer"
          >
            <span>Open Lab Workstation</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

      {/* Authoritative Metric KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-white p-4 rounded-xl border border-purple-200 bg-purple-50/20 shadow-xs">
          <div className="flex items-center justify-between text-purple-700 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">Requisitions</span>
            <Clock className="w-4 h-4" />
          </div>
          <div className="text-2xl font-black text-purple-950 font-mono">{pendingOrdersCount}</div>
          <div className="text-[10px] text-purple-700 font-medium mt-0.5">Ordered requisitions</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-blue-200 bg-blue-50/20 shadow-xs">
          <div className="flex items-center justify-between text-blue-700 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">Specimens Due</span>
            <Syringe className="w-4 h-4" />
          </div>
          <div className="text-2xl font-black text-blue-950 font-mono">{specimensToCollectCount}</div>
          <div className="text-[10px] text-blue-700 font-medium mt-0.5">Awaiting collection</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-cyan-200 bg-cyan-50/20 shadow-xs">
          <div className="flex items-center justify-between text-cyan-700 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">In Testing</span>
            <Microscope className="w-4 h-4" />
          </div>
          <div className="text-2xl font-black text-cyan-950 font-mono">{inTestingCount}</div>
          <div className="text-[10px] text-cyan-700 font-medium mt-0.5">Processing in lab</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-amber-200 bg-amber-50/20 shadow-xs">
          <div className="flex items-center justify-between text-amber-700 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">Awaiting Verify</span>
            <FileCheck className="w-4 h-4" />
          </div>
          <div className="text-2xl font-black text-amber-950 font-mono">{awaitingVerificationCount}</div>
          <div className="text-[10px] text-amber-700 font-medium mt-0.5">Entered results</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-emerald-200 bg-emerald-50/20 shadow-xs">
          <div className="flex items-center justify-between text-emerald-700 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">Completed</span>
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <div className="text-2xl font-black text-emerald-950 font-mono">{verifiedCount}</div>
          <div className="text-[10px] text-emerald-700 font-medium mt-0.5">Verified & released</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-rose-200 bg-rose-50/20 shadow-xs">
          <div className="flex items-center justify-between text-rose-700 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider">STAT / Urgent</span>
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div className="text-2xl font-black text-rose-950 font-mono">{statOrUrgentCount}</div>
          <div className="text-[10px] text-rose-700 font-medium mt-0.5">High priority orders</div>
        </div>
      </div>

      {/* Main Diagnostic Queue Console */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        {/* Tab Navigation */}
        <div className="p-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50/60">
          <div className="flex items-center gap-1 overflow-x-auto pb-1 sm:pb-0">
            <button
              onClick={() => setFilterTab('ALL')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition whitespace-nowrap cursor-pointer ${
                filterTab === 'ALL'
                  ? 'bg-purple-600 text-white shadow-xs'
                  : 'text-slate-600 hover:bg-slate-200/60'
              }`}
            >
              All Requisitions ({orders.length})
            </button>
            <button
              onClick={() => setFilterTab('AWAITING_SPECIMEN')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition whitespace-nowrap cursor-pointer ${
                filterTab === 'AWAITING_SPECIMEN'
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'text-slate-600 hover:bg-slate-200/60'
              }`}
            >
              Awaiting Specimen ({orders.filter((o) => requests.filter((r) => r.diagnostic_order === o.id).some((r) => !r.specimen && r.status !== 'COMPLETED')).length})
            </button>
            <button
              onClick={() => setFilterTab('IN_TESTING')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition whitespace-nowrap cursor-pointer ${
                filterTab === 'IN_TESTING'
                  ? 'bg-cyan-600 text-white shadow-xs'
                  : 'text-slate-600 hover:bg-slate-200/60'
              }`}
            >
              Processing ({orders.filter((o) => requests.filter((r) => r.diagnostic_order === o.id).some((r) => r.specimen && !results.some((res) => res.test_request === r.id))).length})
            </button>
            <button
              onClick={() => setFilterTab('AWAITING_VERIFY')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition whitespace-nowrap cursor-pointer ${
                filterTab === 'AWAITING_VERIFY'
                  ? 'bg-amber-600 text-white shadow-xs'
                  : 'text-slate-600 hover:bg-slate-200/60'
              }`}
            >
              Awaiting Verify ({orders.filter((o) => results.filter((res) => requests.filter((r) => r.diagnostic_order === o.id).some((r) => r.id === res.test_request)).some((res) => res.status === 'ENTERED')).length})
            </button>
            <button
              onClick={() => setFilterTab('VERIFIED')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition whitespace-nowrap cursor-pointer ${
                filterTab === 'VERIFIED'
                  ? 'bg-emerald-600 text-white shadow-xs'
                  : 'text-slate-600 hover:bg-slate-200/60'
              }`}
            >
              Verified / Completed ({orders.filter((o) => results.filter((res) => requests.filter((r) => r.diagnostic_order === o.id).some((r) => r.id === res.test_request)).some((res) => res.status === 'VERIFIED' || res.status === 'AMENDED')).length})
            </button>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
            <BookOpen className="w-3.5 h-3.5 text-purple-600" />
            <span>Catalogue: {testMasters.length} tests active</span>
          </div>
        </div>

        {/* Table Content */}
        {loading ? (
          <div className="p-12 flex justify-center">
            <LoadingSpinner size="lg" label="Loading facility diagnostic orders & laboratory queue..." />
          </div>
        ) : filteredOrders.length === 0 ? (
          <div className="p-8">
            <EmptyState
              title="No Diagnostic Orders in this Queue"
              description="There are currently no laboratory diagnostic requisitions matching this category for the facility."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-100/70 border-b border-slate-200 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                  <th className="py-3 px-4">Order Number</th>
                  <th className="py-3 px-4">Patient / Visit</th>
                  <th className="py-3 px-4">Priority</th>
                  <th className="py-3 px-4">Requested Tests</th>
                  <th className="py-3 px-4">Specimen Status</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {filteredOrders.map((order) => {
                  const visit = visitMap.get(order.visit);
                  const orderReqs = requests.filter((r) => r.diagnostic_order === order.id);
                  const hasSpecimen = orderReqs.some((r) => Boolean(r.specimen));

                  return (
                    <tr key={order.id} className="hover:bg-slate-50/80 transition">
                      <td className="py-3 px-4 font-mono font-bold text-purple-700 whitespace-nowrap">
                        {order.order_number}
                        <div className="text-[10px] text-slate-400 font-normal font-sans">
                          {order.order_date}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-bold text-slate-900">
                          {visit?.patient_details?.name || `Patient #${visit?.patient || 'Unknown'}`}
                        </div>
                        <div className="text-[10px] text-slate-500 font-mono">
                          UHID: {visit?.patient_details?.uhid || 'N/A'} • Token #{visit?.token_number || order.visit}
                        </div>
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">{getPriorityBadge(order.priority)}</td>
                      <td className="py-3 px-4">
                        {orderReqs.length > 0 ? (
                          <div className="flex flex-wrap gap-1 max-w-xs">
                            {orderReqs.map((req) => {
                              const tm = testMasterMap.get(req.test_master);
                              return (
                                <span
                                  key={req.id}
                                  className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-purple-50 text-purple-800 border border-purple-200"
                                >
                                  {tm ? tm.test_code : `TR #${req.id}`}
                                </span>
                              );
                            })}
                          </div>
                        ) : (
                          <span className="text-slate-400 italic text-[11px]">No test requisitions</span>
                        )}
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        {hasSpecimen ? (
                          <span className="inline-flex items-center gap-1 text-[11px] text-emerald-700 font-bold">
                            <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Collected
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[11px] text-amber-700 font-semibold">
                            <Syringe className="w-3 h-3 text-amber-500" /> Due for Draw
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-center whitespace-nowrap">
                        {getStatusBadge(order.status)}
                      </td>
                      <td className="py-3 px-4 text-right whitespace-nowrap">
                        <button
                          onClick={() => navigate(`/lab?order=${order.id}`)}
                          className="px-3 py-1.5 bg-purple-50 hover:bg-purple-100 text-purple-700 font-bold text-xs rounded-lg transition cursor-pointer inline-flex items-center gap-1"
                        >
                          <span>Process</span>
                          <ArrowRight className="w-3 h-3" />
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

export default LabDashboard;
