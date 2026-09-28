import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { getVisits } from '../../api/clinical';
import { parseApiError } from '../../api/client';
import type { Visit } from '../../types';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import EmptyState from '../../components/common/EmptyState';
import {
  Stethoscope,
  Users,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Clock,
  ArrowRight,
  Building2,
  ShieldAlert
} from 'lucide-react';

export const NurseDashboard: React.FC = () => {
  const { user, activeFacility } = useAuth();
  const navigate = useNavigate();

  const [visits, setVisits] = useState<Visit[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Tab filter: 'PENDING' | 'TRIAGED' | 'ALL'
  const [filterTab, setFilterTab] = useState<'PENDING' | 'TRIAGED' | 'ALL'>('PENDING');

  const loadNurseQueue = useCallback(async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    else setRefreshing(true);
    setError(null);

    try {
      // Backend automatically applies facility isolation based on authenticated nurse profile
      const data = await getVisits();
      setVisits(data);
    } catch (err) {
      setError(parseApiError(err));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadNurseQueue();
  }, [loadNurseQueue]);

  // Authoritative queue categorizations
  const pendingVisits = visits.filter(
    (v) =>
      v.current_queue === 'TRIAGE' ||
      ['WAITING_FOR_TRIAGE', 'REGISTERED', 'IN_TRIAGE'].includes(v.status)
  );

  const triagedVisits = visits.filter(
    (v) =>
      v.current_queue !== 'TRIAGE' &&
      !['WAITING_FOR_TRIAGE', 'REGISTERED', 'IN_TRIAGE'].includes(v.status)
  );

  const emergencyOrHighVisits = visits.filter(
    (v) => v.priority === 'EMERGENCY' || v.priority === 'HIGH'
  );

  const filteredVisits = visits.filter((v) => {
    if (filterTab === 'PENDING') {
      return (
        v.current_queue === 'TRIAGE' ||
        ['WAITING_FOR_TRIAGE', 'REGISTERED', 'IN_TRIAGE'].includes(v.status)
      );
    }
    if (filterTab === 'TRIAGED') {
      return (
        v.current_queue !== 'TRIAGE' &&
        !['WAITING_FOR_TRIAGE', 'REGISTERED', 'IN_TRIAGE'].includes(v.status)
      );
    }
    return true;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'WAITING_FOR_TRIAGE':
      case 'REGISTERED':
        return (
          <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800">
            Awaiting Vitals
          </span>
        );
      case 'IN_TRIAGE':
        return (
          <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-blue-100 text-blue-800">
            In Assessment
          </span>
        );
      case 'TRIAGED':
      case 'WAITING_FOR_DOCTOR':
        return (
          <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800">
            Forwarded to Doctor
          </span>
        );
      case 'IN_CONSULTATION':
        return (
          <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-indigo-100 text-indigo-800">
            With Doctor
          </span>
        );
      case 'COMPLETED':
        return (
          <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-slate-100 text-slate-700">
            Encounter Finished
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-700">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Workspace Header Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-teal-800 mb-1">
            <span className="inline-flex items-center gap-1 bg-teal-100/80 text-teal-800 px-2.5 py-0.5 rounded-full">
              <Stethoscope className="w-3.5 h-3.5" aria-hidden="true" />
              Nurse (Staff Nurse)
            </span>
            <span className="text-slate-400">•</span>
            <span className="text-slate-600">Session: <strong>{user?.username}</strong></span>
          </div>

          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Nursing & Triage Station Console
          </h1>

          <div className="flex items-center gap-1.5 text-xs text-slate-500 mt-1">
            <Building2 className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
            <span>
              Facility Scope: <strong>{activeFacility?.facility_name || user?.facility_details?.facility_name || 'Assigned Facility'}</strong>
              {activeFacility?.facility_code && ` (${activeFacility.facility_code})`}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => loadNurseQueue(true)}
            disabled={refreshing}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors shadow-2xs"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} aria-hidden="true" />
            Refresh Queue
          </button>

          <button
            type="button"
            onClick={() => navigate('/triage')}
            className="inline-flex items-center gap-2 px-4 py-2 text-xs font-bold text-white bg-teal-700 hover:bg-teal-800 rounded-lg transition-colors shadow-2xs"
          >
            <Stethoscope className="w-4 h-4" aria-hidden="true" />
            Open Triage Station
          </button>
        </div>
      </div>

      {error && (
        <ErrorAlert
          title="Nurse Roster Sync Error"
          message={error}
          onDismiss={() => setError(null)}
        />
      )}

      {/* Authoritative Metric Counters */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Triage Queue Overview
          </h2>
          <span className="text-[11px] text-slate-400">
            Authoritative source: DRF /api/v1/visits/
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between text-slate-500 text-xs font-medium mb-1">
              <span>Pending Triage</span>
              <Clock className="w-4 h-4 text-amber-500" aria-hidden="true" />
            </div>
            <div className="text-2xl font-bold text-slate-900">{pendingVisits.length}</div>
            <span className="text-[11px] text-amber-700 font-semibold">Awaiting nurse vitals</span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between text-slate-500 text-xs font-medium mb-1">
              <span>Triaged Today</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-600" aria-hidden="true" />
            </div>
            <div className="text-2xl font-bold text-slate-900">{triagedVisits.length}</div>
            <span className="text-[11px] text-slate-500">Forwarded to Doctor</span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between text-slate-500 text-xs font-medium mb-1">
              <span>High Priority / Emergency</span>
              <ShieldAlert className="w-4 h-4 text-rose-500" aria-hidden="true" />
            </div>
            <div className="text-2xl font-bold text-rose-700">{emergencyOrHighVisits.length}</div>
            <span className="text-[11px] text-slate-500">Immediate intake needed</span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between text-slate-500 text-xs font-medium mb-1">
              <span>Total Encounters</span>
              <Users className="w-4 h-4 text-teal-600" aria-hidden="true" />
            </div>
            <div className="text-2xl font-bold text-slate-900">{visits.length}</div>
            <span className="text-[11px] text-slate-500">All registered today</span>
          </div>
        </div>
      </div>

      {/* Queue Filter Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
        <button
          type="button"
          onClick={() => setFilterTab('PENDING')}
          className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${
            filterTab === 'PENDING'
              ? 'bg-teal-700 text-white'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          Pending Triage ({pendingVisits.length})
        </button>

        <button
          type="button"
          onClick={() => setFilterTab('TRIAGED')}
          className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${
            filterTab === 'TRIAGED'
              ? 'bg-teal-700 text-white'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          Triaged / Sent to Doctor ({triagedVisits.length})
        </button>

        <button
          type="button"
          onClick={() => setFilterTab('ALL')}
          className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${
            filterTab === 'ALL'
              ? 'bg-teal-700 text-white'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          All Encounters ({visits.length})
        </button>
      </div>

      {/* Roster Container */}
      <div className="bg-white rounded-xl shadow-xs border border-slate-200 overflow-hidden">
        <div className="p-4 bg-slate-50 border-b border-slate-200 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900">
              {filterTab === 'PENDING'
                ? `Patients Awaiting Vitals Measurement (${filteredVisits.length})`
                : filterTab === 'TRIAGED'
                ? `Completed Triage Encounters (${filteredVisits.length})`
                : `All Outpatient Encounters (${filteredVisits.length})`}
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Encounter records synced from authoritative backend facility scope.
            </p>
          </div>
        </div>

        {loading ? (
          <div className="p-12 flex justify-center">
            <LoadingSpinner size="md" label="Loading nurse triage roster..." />
          </div>
        ) : filteredVisits.length === 0 ? (
          <div className="p-8">
            <EmptyState
              title="No patient encounters in this queue"
              description="There are currently no patient visits matching the selected filter for this facility scope."
              actionText="Refresh Queue"
              onAction={() => loadNurseQueue()}
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/75 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  <th className="py-3 px-4">Token / Priority</th>
                  <th className="py-3 px-4">Visit ID</th>
                  <th className="py-3 px-4">Patient</th>
                  <th className="py-3 px-4">Queue Status</th>
                  <th className="py-3 px-4">Encounter Status</th>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4 text-right">Clinical Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {filteredVisits.map((v) => {
                  const isEmerg = v.priority === 'EMERGENCY';
                  const isHigh = v.priority === 'HIGH';
                  const isPending =
                    v.current_queue === 'TRIAGE' ||
                    ['WAITING_FOR_TRIAGE', 'REGISTERED', 'IN_TRIAGE'].includes(v.status);

                  return (
                    <tr key={v.id} className="hover:bg-teal-50/30 transition-colors">
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-sm font-black text-slate-900">
                            #{v.token_number ?? v.id}
                          </span>
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              isEmerg
                                ? 'bg-rose-500 text-white animate-pulse'
                                : isHigh
                                ? 'bg-amber-100 text-amber-900 border border-amber-300'
                                : 'bg-slate-100 text-slate-700'
                            }`}
                          >
                            {v.priority || 'NORMAL'}
                          </span>
                        </div>
                      </td>

                      <td className="py-3 px-4 font-mono text-slate-600">
                        {v.visit_id || `VIS-${v.id}`}
                      </td>

                      <td className="py-3 px-4">
                        <div className="font-bold text-slate-900">
                          Patient #{v.patient}
                        </div>
                        <span className="text-[11px] text-slate-400">ID: ID #{v.patient}</span>
                      </td>

                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-slate-100 text-slate-700">
                          {v.current_queue || 'TRIAGE'}
                        </span>
                      </td>

                      <td className="py-3 px-4">
                        {getStatusBadge(v.status)}
                      </td>

                      <td className="py-3 px-4 text-slate-500">
                        {v.opd_date || v.visit_date}
                      </td>

                      <td className="py-3 px-4 text-right">
                        <button
                          type="button"
                          onClick={() => navigate(`/triage?visit=${v.id}`)}
                          className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold transition-colors shadow-2xs ${
                            isPending
                              ? 'bg-teal-700 hover:bg-teal-800 text-white'
                              : 'bg-slate-100 hover:bg-slate-200 text-slate-800'
                          }`}
                        >
                          <Stethoscope className="w-3.5 h-3.5" aria-hidden="true" />
                          {isPending ? 'Record Vitals' : 'View Vitals'}
                          <ArrowRight className="w-3 h-3 ml-0.5" aria-hidden="true" />
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

export default NurseDashboard;
