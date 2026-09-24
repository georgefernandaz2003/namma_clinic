import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { getVisits } from '../../api/clinical';
import type { Visit } from '../../types';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import EmptyState from '../../components/common/EmptyState';
import {
  Stethoscope,
  Users,
  Clock,
  CheckCircle2,
  AlertCircle,
  FileText,
  TestTube,
  RefreshCw,
  Building2,
  Calendar,
  Activity,
  ArrowRight
} from 'lucide-react';

export const DoctorDashboard: React.FC = () => {
  const { user, activeFacility } = useAuth();
  const navigate = useNavigate();

  const [visits, setVisits] = useState<Visit[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [filterTab, setFilterTab] = useState<'ALL' | 'READY' | 'IN_CONSULTATION' | 'LAB_REVIEW' | 'COMPLETED'>('ALL');

  const loadDoctorQueue = useCallback(async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    else setRefreshing(true);
    setError(null);

    try {
      // Backend automatically applies facility isolation based on authenticated doctor profile
      const params: Record<string, string | number> = {};
      if (activeFacility?.id) {
        params.facility = activeFacility.id;
      }
      const data = await getVisits(params);
      setVisits(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unable to fetch clinical encounter queue from backend.';
      setError(msg);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [activeFacility?.id]);

  useEffect(() => {
    loadDoctorQueue();
  }, [loadDoctorQueue]);

  // Authoritative metrics calculated strictly from backend response data (zero fake KPIs)
  const readyVisits = visits.filter(
    (v) => v.current_queue === 'DOCTOR' || ['TRIAGED', 'WAITING_FOR_DOCTOR', 'REGISTERED', 'WAITING_FOR_TRIAGE'].includes(v.status)
  );
  const inConsultationVisits = visits.filter((v) => v.status === 'IN_CONSULTATION');
  const labReviewVisits = visits.filter((v) => ['DOCTOR_REVIEW', 'LAB_COMPLETED', 'WAITING_FOR_LAB'].includes(v.status));
  const completedVisits = visits.filter((v) => v.status === 'COMPLETED');

  const filteredVisits = visits.filter((v) => {
    if (filterTab === 'READY') {
      return v.current_queue === 'DOCTOR' || ['TRIAGED', 'WAITING_FOR_DOCTOR', 'REGISTERED', 'WAITING_FOR_TRIAGE'].includes(v.status);
    }
    if (filterTab === 'IN_CONSULTATION') return v.status === 'IN_CONSULTATION';
    if (filterTab === 'LAB_REVIEW') return ['DOCTOR_REVIEW', 'LAB_COMPLETED', 'WAITING_FOR_LAB'].includes(v.status);
    if (filterTab === 'COMPLETED') return v.status === 'COMPLETED';
    return true;
  });

  const getPriorityBadge = (priority?: string) => {
    switch (priority) {
      case 'EMERGENCY':
        return <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-100 text-rose-800 border border-rose-200">EMERGENCY</span>;
      case 'HIGH':
        return <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 text-amber-800 border border-amber-200">HIGH</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200">NORMAL</span>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'TRIAGED':
      case 'WAITING_FOR_DOCTOR':
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800">Ready for Consultation</span>;
      case 'IN_CONSULTATION':
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-sky-100 text-sky-800">In Consultation</span>;
      case 'WAITING_FOR_LAB':
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-purple-100 text-purple-800">Awaiting Lab Results</span>;
      case 'DOCTOR_REVIEW':
      case 'LAB_COMPLETED':
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-indigo-100 text-indigo-800">Lab Ready for Review</span>;
      case 'WAITING_FOR_PHARMACY':
      case 'IN_PHARMACY':
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800">Sent to Pharmacy</span>;
      case 'COMPLETED':
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-slate-100 text-slate-700">Encounter Completed</span>;
      default:
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-slate-100 text-slate-600">{status}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Header Banner */}
      <header className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
              <Stethoscope className="w-3.5 h-3.5" aria-hidden="true" />
              Doctor (Medical Officer)
            </span>
            <span className="text-xs text-slate-500 font-mono">
              Session: {user?.username}
            </span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Medical Officer Clinical Console
          </h1>
          <p className="text-xs text-slate-600 mt-1 flex items-center gap-2">
            <Building2 className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
            <span>
              Facility Scope: <strong>{activeFacility?.facility_name || user?.facility_details?.facility_name || 'Assigned Facility'}</strong>
              {activeFacility?.facility_code && ` (${activeFacility.facility_code})`}
            </span>
          </p>
        </div>

        <div className="flex items-center gap-2 self-start md:self-auto">
          <button
            type="button"
            onClick={() => loadDoctorQueue(true)}
            disabled={refreshing}
            className="inline-flex items-center gap-1.5 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium text-xs rounded-lg transition disabled:opacity-50 cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
            aria-label="Refresh Queue"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} aria-hidden="true" />
            <span>Refresh Queue</span>
          </button>
          <button
            type="button"
            onClick={() => navigate('/consultation')}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-lg shadow-sm transition cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
          >
            <FileText className="w-4 h-4" aria-hidden="true" />
            <span>New Consultation</span>
          </button>
        </div>
      </header>

      {/* 2. Error Display */}
      {error && (
        <ErrorAlert
          message={error}
          onDismiss={() => setError(null)}
        />
      )}

      {/* 3. Authoritative Queue Metrics Bar (Zero Fake Data) */}
      <section aria-labelledby="queue-summary-heading" className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <h2 id="queue-summary-heading" className="sr-only">Clinical Queue Summary</h2>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium mb-1">
            <span>Ready for Doctor</span>
            <Users className="w-4 h-4 text-emerald-600" aria-hidden="true" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{readyVisits.length}</div>
          <span className="text-[11px] text-slate-500">Triaged / waiting OPD</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium mb-1">
            <span>In Consultation</span>
            <Activity className="w-4 h-4 text-sky-600" aria-hidden="true" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{inConsultationVisits.length}</div>
          <span className="text-[11px] text-slate-500">Currently examining</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium mb-1">
            <span>Lab Review</span>
            <TestTube className="w-4 h-4 text-purple-600" aria-hidden="true" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{labReviewVisits.length}</div>
          <span className="text-[11px] text-slate-500">Diagnostics in progress/done</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium mb-1">
            <span>Completed Today</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" aria-hidden="true" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{completedVisits.length}</div>
          <span className="text-[11px] text-slate-500">Finished encounters</span>
        </div>
      </section>

      {/* 4. Queue Filter Tabs */}
      <div className="flex items-center gap-1 border-b border-slate-200 pb-2 overflow-x-auto" role="tablist" aria-label="Queue Filter Tabs">
        <button
          type="button"
          role="tab"
          aria-selected={filterTab === 'ALL'}
          onClick={() => setFilterTab('ALL')}
          className={`px-3 py-1.5 rounded-lg text-xs font-bold transition whitespace-nowrap cursor-pointer ${
            filterTab === 'ALL'
              ? 'bg-slate-900 text-white'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          All Encounters ({visits.length})
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={filterTab === 'READY'}
          onClick={() => setFilterTab('READY')}
          className={`px-3 py-1.5 rounded-lg text-xs font-bold transition whitespace-nowrap cursor-pointer ${
            filterTab === 'READY'
              ? 'bg-emerald-600 text-white'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          Ready for Doctor ({readyVisits.length})
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={filterTab === 'IN_CONSULTATION'}
          onClick={() => setFilterTab('IN_CONSULTATION')}
          className={`px-3 py-1.5 rounded-lg text-xs font-bold transition whitespace-nowrap cursor-pointer ${
            filterTab === 'IN_CONSULTATION'
              ? 'bg-sky-600 text-white'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          In Consultation ({inConsultationVisits.length})
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={filterTab === 'LAB_REVIEW'}
          onClick={() => setFilterTab('LAB_REVIEW')}
          className={`px-3 py-1.5 rounded-lg text-xs font-bold transition whitespace-nowrap cursor-pointer ${
            filterTab === 'LAB_REVIEW'
              ? 'bg-purple-600 text-white'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          Lab Review ({labReviewVisits.length})
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={filterTab === 'COMPLETED'}
          onClick={() => setFilterTab('COMPLETED')}
          className={`px-3 py-1.5 rounded-lg text-xs font-bold transition whitespace-nowrap cursor-pointer ${
            filterTab === 'COMPLETED'
              ? 'bg-slate-700 text-white'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          Completed ({completedVisits.length})
        </button>
      </div>

      {/* 5. Patient Visits List / Table */}
      <section aria-labelledby="queue-table-heading" className="bg-white border border-slate-200 rounded-2xl shadow-xs overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          <h2 id="queue-table-heading" className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Clock className="w-4 h-4 text-emerald-600" aria-hidden="true" />
            Today's Outpatient Encounters ({filteredVisits.length})
          </h2>
          <span className="text-xs text-slate-500">
            Source: Authoritative DRF <code className="font-mono bg-slate-100 px-1 py-0.5 rounded">/api/v1/visits/</code>
          </span>
        </div>

        {loading ? (
          <div className="p-12 flex justify-center">
            <LoadingSpinner size="md" label="Loading clinical queue from backend..." />
          </div>
        ) : filteredVisits.length === 0 ? (
          <div className="p-8">
            <EmptyState
              title="No patient encounters in this queue"
              description="There are currently no patient visits matching the selected filter for this facility scope."
              actionText="Refresh Roster"
              onAction={() => loadDoctorQueue()}
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-700 font-bold border-b border-slate-200 uppercase tracking-wider text-[11px]">
                <tr>
                  <th scope="col" className="px-4 py-3">Token / Priority</th>
                  <th scope="col" className="px-4 py-3">Visit ID</th>
                  <th scope="col" className="px-4 py-3">Patient</th>
                  <th scope="col" className="px-4 py-3">Queue Status</th>
                  <th scope="col" className="px-4 py-3">Encounter Status</th>
                  <th scope="col" className="px-4 py-3">Date</th>
                  <th scope="col" className="px-4 py-3 text-right">Clinical Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredVisits.map((v) => (
                  <tr key={v.id} className="hover:bg-slate-50/80 transition">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-slate-900 bg-slate-100 px-2 py-1 rounded border border-slate-200">
                          #{v.token_number || v.id}
                        </span>
                        {getPriorityBadge(v.priority)}
                      </div>
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-600">
                      {v.visit_id}
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-bold text-slate-900">
                        {v.patient_details?.name || `Patient #${v.patient}`}
                      </div>
                      <div className="text-[11px] text-slate-500">
                        ID: {v.patient_details?.patient_id || `ID #${v.patient}`}
                        {v.patient_details?.gender && ` • ${v.patient_details.gender}`}
                        {v.patient_details?.age && ` • ${v.patient_details.age}y`}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="font-medium text-slate-700 font-mono text-[11px]">
                        {v.current_queue || 'TRIAGE'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {getStatusBadge(v.status)}
                    </td>
                    <td className="px-4 py-3 text-slate-500 font-mono text-[11px]">
                      {v.opd_date || v.visit_date?.split('T')[0] || 'Today'}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        onClick={() => navigate(`/consultation?visit=${v.id}`)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-lg shadow-2xs transition cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
                      >
                        <span>{v.status === 'COMPLETED' ? 'View Encounter' : 'Consult Patient'}</span>
                        <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
};

export default DoctorDashboard;
