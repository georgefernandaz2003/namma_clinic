import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useSearchParams, useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  getVisits,
  getVisit,
  getPatient,
  getTriageVitals,
  createTriageVitals,
  updateTriageVitals,
  updateVisit
} from '../api/clinical';
import { parseApiError } from '../api/client';
import type { Visit, Patient, TriageVitals, CreateTriagePayload } from '../types';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorAlert from '../components/common/ErrorAlert';
import EmptyState from '../components/common/EmptyState';
import ForbiddenCard from '../components/common/ForbiddenCard';
import TriagePatientBanner from '../components/triage/TriagePatientBanner';
import TriageRecordedCard from '../components/triage/TriageRecordedCard';
import TriageVitalsForm from '../components/triage/TriageVitalsForm';
import { Stethoscope, ArrowLeft, CheckCircle2, ChevronRight, Users, Filter } from 'lucide-react';

export const Triage: React.FC = () => {
  const { user, activeFacility } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();

  // Role security check
  const isNurse = user?.role === 'NURSE';

  // Core encounter state: support both query parameter and navigation state
  const stateVisitId = (location.state as any)?.visitId;
  const visitIdParam = searchParams.get('visit') || (stateVisitId ? String(stateVisitId) : null);
  const [activeVisit, setActiveVisit] = useState<Visit | null>(null);
  const [patient, setPatient] = useState<Patient | null>(null);
  const [existingTriage, setExistingTriage] = useState<TriageVitals | null>(null);
  const [triageQueue, setTriageQueue] = useState<Visit[]>([]);

  // Queue filter state: 'PENDING' | 'ALL' | 'TRIAGED'
  const filterParam = searchParams.get('filter');
  const [queueFilter, setQueueFilter] = useState<'PENDING' | 'ALL' | 'TRIAGED'>(() => {
    if (filterParam === 'ALL' || filterParam === 'TRIAGED' || filterParam === 'PENDING') return filterParam;
    return 'PENDING';
  });

  // Track if current vitals form has unsaved edits
  const [formIsDirty, setFormIsDirty] = useState<boolean>(false);
  const [lastKnownIndex, setLastKnownIndex] = useState<number>(0);

  // Page lifecycle
  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [handoffFailed, setHandoffFailed] = useState<boolean>(false);

  // Load all visits for the nurse queue dropdown/roster with facility scoping
  const loadTriageQueue = useCallback(async () => {
    try {
      const params: Record<string, string | number> = {};
      if (activeFacility?.id) {
        params.facility = activeFacility.id;
      }
      const visits = await getVisits(params);
      setTriageQueue(visits);
      return visits;
    } catch (err) {
      console.error('Failed to load queue in Triage:', err);
      return [];
    }
  }, [activeFacility?.id]);

  // Load specific encounter
  const loadEncounter = useCallback(async (vId: number) => {
    setLoading(true);
    setError(null);
    setSuccessMessage(null);
    setIsEditing(false);
    setHandoffFailed(false);
    setFormIsDirty(false);

    try {
      const v = await getVisit(vId);
      setActiveVisit(v);

      // Fetch patient demographics
      const ptId = typeof v.patient === 'object' ? (v.patient as any).id : v.patient;
      const pt = await getPatient(ptId);
      setPatient(pt);

      // Fetch existing triage if any
      const tr = await getTriageVitals(v.id);
      setExistingTriage(tr);
    } catch (err) {
      setError(parseApiError(err));
    } finally {
      setLoading(false);
    }
  }, []);

  // Authoritative facility isolation
  const facilityScopedVisits = useMemo(() => {
    return triageQueue.filter((v) => {
      if (activeFacility?.id && v.facility && v.facility !== activeFacility.id) {
        return false;
      }
      return true;
    });
  }, [triageQueue, activeFacility?.id]);

  // Categorizations for nurse queue navigation
  const pendingVisits = useMemo(
    () =>
      facilityScopedVisits.filter(
        (v) =>
          v.current_queue === 'TRIAGE' ||
          ['WAITING_FOR_TRIAGE', 'REGISTERED', 'IN_TRIAGE', 'WAITING'].includes(v.status)
      ),
    [facilityScopedVisits]
  );

  const triagedVisits = useMemo(
    () =>
      facilityScopedVisits.filter(
        (v) =>
          v.current_queue !== 'TRIAGE' &&
          !['WAITING_FOR_TRIAGE', 'REGISTERED', 'IN_TRIAGE', 'WAITING'].includes(v.status)
      ),
    [facilityScopedVisits]
  );

  // Active filtered queue for navigation
  const filteredQueue = useMemo(() => {
    if (queueFilter === 'PENDING') return pendingVisits;
    if (queueFilter === 'TRIAGED') return triagedVisits;
    return facilityScopedVisits;
  }, [queueFilter, pendingVisits, triagedVisits, facilityScopedVisits]);

  // Options for active encounter selector (ensuring activeVisit is visible even if just completed)
  const selectQueueOptions = useMemo(() => {
    if (activeVisit && !filteredQueue.some((v) => v.id === activeVisit.id)) {
      return [activeVisit, ...filteredQueue];
    }
    return filteredQueue;
  }, [activeVisit, filteredQueue]);

  // Queue navigation index resolution
  const currentIndex = activeVisit
    ? filteredQueue.findIndex((v) => v.id === activeVisit.id)
    : -1;

  useEffect(() => {
    if (currentIndex !== -1) {
      setLastKnownIndex(currentIndex);
    }
  }, [currentIndex]);

  const effectiveIndex = currentIndex !== -1 ? currentIndex : lastKnownIndex;

  const hasPrevious = currentIndex !== -1 ? currentIndex > 0 : effectiveIndex > 0;
  const hasNext =
    currentIndex !== -1
      ? currentIndex < filteredQueue.length - 1
      : effectiveIndex < filteredQueue.length;

  const navigateToVisit = useCallback(
    (vId: number) => {
      setFormIsDirty(false);
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          next.set('visit', String(vId));
          if (queueFilter !== 'PENDING') {
            next.set('filter', queueFilter);
          } else {
            next.delete('filter');
          }
          return next;
        },
        { replace: false }
      );
    },
    [setSearchParams, queueFilter]
  );

  const handlePreviousPatient = () => {
    if (!hasPrevious) return;
    const target =
      currentIndex !== -1
        ? filteredQueue[currentIndex - 1]
        : filteredQueue[Math.max(0, effectiveIndex - 1)];
    if (target) {
      navigateToVisit(target.id);
    }
  };

  const handleNextPatient = () => {
    if (!hasNext) return;
    const target =
      currentIndex !== -1
        ? filteredQueue[currentIndex + 1]
        : filteredQueue[Math.min(filteredQueue.length - 1, effectiveIndex)];
    if (target) {
      navigateToVisit(target.id);
    }
  };

  // Handle Encounter Change via Selector with unsaved changes guard
  const handleSelectVisit = (vId: number) => {
    if (vId === activeVisit?.id) return;
    if (formIsDirty) {
      const proceed = window.confirm(
        'You have unsaved triage vitals and clinical notes for this patient. Are you sure you want to discard your changes and navigate away?'
      );
      if (!proceed) return;
    }
    navigateToVisit(vId);
  };

  // Handle Queue Filter Change with unsaved changes guard
  const handleFilterChange = (newFilter: 'PENDING' | 'ALL' | 'TRIAGED') => {
    if (newFilter === queueFilter) return;
    if (formIsDirty) {
      const proceed = window.confirm(
        'You have unsaved triage vitals and clinical notes for this patient. Are you sure you want to discard your changes and change the queue filter?'
      );
      if (!proceed) return;
    }
    setFormIsDirty(false);
    setQueueFilter(newFilter);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (newFilter !== 'PENDING') {
        next.set('filter', newFilter);
      } else {
        next.delete('filter');
      }
      return next;
    });
  };

  // Initialize Queue & Encounter on mount or facility change
  useEffect(() => {
    let isMounted = true;

    const init = async () => {
      setLoading(true);
      const queue = await loadTriageQueue();

      if (!isMounted) return;

      const facilityVisits = queue.filter((v) => {
        if (activeFacility?.id && v.facility && v.facility !== activeFacility.id) {
          return false;
        }
        return true;
      });

      if (visitIdParam) {
        const parsed = parseInt(visitIdParam, 10);
        if (!isNaN(parsed)) {
          if (!searchParams.get('visit')) {
            setSearchParams((prev) => {
              const next = new URLSearchParams(prev);
              next.set('visit', String(parsed));
              return next;
            }, { replace: true });
          }
          await loadEncounter(parsed);
          return;
        }
      }

      // Default to first pending visit in queue, or first visit
      const pending = facilityVisits.find(
        (v) => v.current_queue === 'TRIAGE' || ['WAITING_FOR_TRIAGE', 'REGISTERED', 'IN_TRIAGE', 'WAITING'].includes(v.status)
      );

      if (pending) {
        setSearchParams({ visit: String(pending.id) }, { replace: true });
        await loadEncounter(pending.id);
      } else if (facilityVisits.length > 0) {
        setSearchParams({ visit: String(facilityVisits[0].id) }, { replace: true });
        await loadEncounter(facilityVisits[0].id);
      } else {
        setLoading(false);
      }
    };

    init();

    return () => {
      isMounted = false;
    };
  }, [activeFacility?.id, loadTriageQueue, loadEncounter, setSearchParams]);

  // Load encounter when visitIdParam changes
  const isInitialMount = useRef(true);
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }
    if (!visitIdParam) return;
    const parsed = parseInt(visitIdParam, 10);
    if (!isNaN(parsed) && parsed !== activeVisit?.id) {
      loadEncounter(parsed);
    }
  }, [visitIdParam, activeVisit?.id, loadEncounter]);

  // Submit Triage
  const handleSaveTriage = async (payload: CreateTriagePayload) => {
    if (!activeVisit || !patient) return;
    setSubmitting(true);
    setError(null);
    setSuccessMessage(null);
    setHandoffFailed(false);

    let savedTriage: TriageVitals;

    // Step 1: Save triage vitals (authoritative clinical record)
    try {
      if (existingTriage && isEditing) {
        savedTriage = await updateTriageVitals(existingTriage.id, payload);
      } else {
        savedTriage = await createTriageVitals({
          ...payload,
          visit: activeVisit.id,
          patient: patient.id
        });
      }
      setExistingTriage(savedTriage);
    } catch (err) {
      setError(parseApiError(err));
      setSubmitting(false);
      return;
    }

    // Step 2: Transition visit queue state (separate HTTP operation — non-atomic)
    try {
      const updatedVisit = await updateVisit(activeVisit.id, {
        status: 'TRIAGED',
        current_queue: 'DOCTOR'
      });

      setActiveVisit(updatedVisit);
      setIsEditing(false);
      setHandoffFailed(false);

      const patientName =
        patient.name ||
        `${patient.first_name || ''} ${patient.last_name || ''}`.trim() ||
        `Patient #${patient.id}`;

      setSuccessMessage(
        `Triage vitals recorded successfully for ${patientName}. Encounter #${activeVisit.token_number ?? activeVisit.id} forwarded to Doctor Consultation Queue.`
      );

      loadTriageQueue();
    } catch (visitErr) {
      // Partial Failure handling: Vitals are persisted, but queue forward failed
      setIsEditing(false);
      setHandoffFailed(true);
      setError(
        `Triage vitals saved, but forwarding to Doctor queue failed: ${parseApiError(visitErr)}. The encounter remains in the nurse queue. Click 'Retry Doctor Handoff' to complete queue transition.`
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleRetryHandoff = async () => {
    if (!activeVisit) return;
    setSubmitting(true);
    setError(null);

    try {
      const updatedVisit = await updateVisit(activeVisit.id, {
        status: 'TRIAGED',
        current_queue: 'DOCTOR'
      });

      setActiveVisit(updatedVisit);
      setHandoffFailed(false);
      setSuccessMessage(
        `Encounter #${activeVisit.token_number ?? activeVisit.id} successfully forwarded to Doctor Consultation Queue.`
      );
      loadTriageQueue();
    } catch (err) {
      setError(`Retry failed: ${parseApiError(err)}`);
    } finally {
      setSubmitting(false);
    }
  };

  // If user is not Nurse, render ForbiddenCard
  if (!isNurse) {
    return (
      <ForbiddenCard
        role={user?.role}
        roleDisplay={user?.role_display}
        requestedPath="/triage"
      />
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Header / Breadcrumb navigation */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 mb-1">
            <Link to="/dashboard/nurse" className="hover:text-teal-700 transition-colors flex items-center gap-1">
              <ArrowLeft className="w-3.5 h-3.5" aria-hidden="true" />
              Nurse Station Console
            </Link>
            <ChevronRight className="w-3 h-3 text-slate-400" aria-hidden="true" />
            <span className="text-teal-800 font-bold">Vitals & Clinical Triage</span>
          </div>

          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2.5">
            <Stethoscope className="w-6 h-6 text-teal-600" aria-hidden="true" />
            Nursing Triage & Vitals Assessment
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Facility Scope: <strong>{activeFacility?.facility_name || user?.facility_details?.facility_name || 'Assigned Facility'}</strong>
            {activeFacility?.facility_code && ` (${activeFacility.facility_code})`}
          </p>
        </div>

        {/* Encounter Selector Dropdown & Filter */}
        {facilityScopedVisits.length > 0 && (
          <div className="flex flex-wrap items-center gap-3">
            {/* Queue Filter */}
            <div className="flex items-center gap-2 bg-white px-3 py-2 rounded-lg border border-slate-200 shadow-2xs">
              <Filter className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
              <label htmlFor="triage-queue-filter" className="text-xs font-bold text-slate-700 whitespace-nowrap">
                Queue Filter:
              </label>
              <select
                id="triage-queue-filter"
                data-testid="triage-queue-filter"
                value={queueFilter}
                onChange={(e) => handleFilterChange(e.target.value as 'PENDING' | 'ALL' | 'TRIAGED')}
                className="text-xs font-semibold text-slate-800 bg-transparent border-0 focus:ring-0 cursor-pointer"
              >
                <option value="PENDING">Pending Triage ({pendingVisits.length})</option>
                <option value="ALL">All Visits ({facilityScopedVisits.length})</option>
                <option value="TRIAGED">Triaged ({triagedVisits.length})</option>
              </select>
            </div>

            {/* Active Encounter Selector */}
            {selectQueueOptions.length > 0 && (
              <div className="flex items-center gap-2 bg-white px-3 py-2 rounded-lg border border-slate-200 shadow-2xs">
                <Users className="w-4 h-4 text-slate-400" aria-hidden="true" />
                <label htmlFor="triage-encounter-select" className="text-xs font-bold text-slate-700 whitespace-nowrap">
                  Active Encounter:
                </label>
                <select
                  id="triage-encounter-select"
                  data-testid="triage-encounter-select"
                  value={activeVisit?.id || ''}
                  onChange={(e) => handleSelectVisit(Number(e.target.value))}
                  className="text-xs font-semibold text-slate-800 bg-transparent border-0 focus:ring-0 cursor-pointer"
                >
                  {selectQueueOptions.map((v, idx) => (
                    <option key={v.id} value={v.id}>
                      #{idx + 1}: Token #{v.token_number ?? v.id} - Patient #{v.patient} ({v.status})
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Global Error Notice */}
      {error && (
        <ErrorAlert
          title="Clinical Triage Notice"
          message={error}
          onDismiss={() => setError(null)}
        />
      )}

      {/* Success Notification Banner */}
      {successMessage && (
        <div className="p-4 bg-emerald-50 border border-emerald-300 rounded-xl shadow-xs flex flex-wrap items-center justify-between gap-4 animate-in fade-in">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600">
              <CheckCircle2 className="w-5 h-5" aria-hidden="true" />
            </div>
            <div>
              <p className="text-sm font-bold text-emerald-900">{successMessage}</p>
              <p className="text-xs text-emerald-700 mt-0.5">
                The encounter is marked <strong>Ready for Doctor</strong> and visible in the Medical Officer queue.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => navigate('/dashboard/nurse')}
              className="px-3 py-1.5 text-xs font-bold text-emerald-800 bg-emerald-100 hover:bg-emerald-200 rounded-lg transition-colors"
            >
              Return to Nurse Queue
            </button>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading ? (
        <div className="py-20 flex justify-center bg-white rounded-xl border border-slate-200">
          <LoadingSpinner size="lg" label="Loading patient clinical intake..." />
        </div>
      ) : !activeVisit || !patient ? (
        <EmptyState
          title="No Patient Encounter Selected"
          description="Select an active patient encounter from the queue to record vitals and triage assessment."
          actionText="View Nurse Queue"
          onAction={() => navigate('/dashboard/nurse')}
        />
      ) : (
        <>
          {/* Patient Demographics & Encounter Metadata Banner */}
          <TriagePatientBanner patient={patient} visit={activeVisit} />

          {/* Conditional Rendering: Already Recorded vs Form Entry */}
          {existingTriage && !isEditing ? (
            <TriageRecordedCard
              triage={existingTriage}
              onEditTriage={() => setIsEditing(true)}
              onBackToQueue={() => navigate('/dashboard/nurse')}
              isForwardedToDoctor={!handoffFailed && (activeVisit?.status === 'TRIAGED' || activeVisit?.current_queue === 'DOCTOR')}
              onRetryHandoff={handoffFailed ? handleRetryHandoff : undefined}
              hasPrevious={hasPrevious}
              hasNext={hasNext}
              onPreviousPatient={handlePreviousPatient}
              onNextPatient={handleNextPatient}
            />
          ) : (
            <TriageVitalsForm
              key={activeVisit.id}
              initialVitals={existingTriage}
              onSubmit={handleSaveTriage}
              loading={submitting}
              nurseName={user?.username}
              onCancel={existingTriage ? () => setIsEditing(false) : undefined}
              hasPrevious={hasPrevious}
              hasNext={hasNext}
              onPreviousPatient={handlePreviousPatient}
              onNextPatient={handleNextPatient}
              onDirtyChange={setFormIsDirty}
            />
          )}
        </>
      )}
    </div>
  );
};

export default Triage;
