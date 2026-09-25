import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
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
import { Stethoscope, ArrowLeft, CheckCircle2, ChevronRight, Users } from 'lucide-react';

export const Triage: React.FC = () => {
  const { user, activeFacility } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  // Role security check
  const isNurse = user?.role === 'NURSE';

  // Core encounter state
  const visitIdParam = searchParams.get('visit');
  const [activeVisit, setActiveVisit] = useState<Visit | null>(null);
  const [patient, setPatient] = useState<Patient | null>(null);
  const [existingTriage, setExistingTriage] = useState<TriageVitals | null>(null);
  const [triageQueue, setTriageQueue] = useState<Visit[]>([]);

  // Page lifecycle
  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState<boolean>(false);

  // Load all visits for the nurse queue dropdown/roster
  const loadTriageQueue = useCallback(async () => {
    try {
      const visits = await getVisits();
      setTriageQueue(visits);
      return visits;
    } catch (err) {
      console.error('Failed to load queue in Triage:', err);
      return [];
    }
  }, []);

  // Load specific encounter
  const loadEncounter = useCallback(async (vId: number) => {
    setLoading(true);
    setError(null);
    setSuccessMessage(null);
    setIsEditing(false);

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

  // Initialize
  useEffect(() => {
    let isMounted = true;

    const init = async () => {
      setLoading(true);
      const queue = await loadTriageQueue();

      if (!isMounted) return;

      if (visitIdParam) {
        const parsed = parseInt(visitIdParam, 10);
        if (!isNaN(parsed)) {
          await loadEncounter(parsed);
          return;
        }
      }

      // Default to first pending visit in queue, or first visit
      const pending = queue.find(
        (v) => v.current_queue === 'TRIAGE' || ['WAITING_FOR_TRIAGE', 'REGISTERED', 'IN_TRIAGE'].includes(v.status)
      );

      if (pending) {
        setSearchParams({ visit: String(pending.id) }, { replace: true });
        await loadEncounter(pending.id);
      } else if (queue.length > 0) {
        setSearchParams({ visit: String(queue[0].id) }, { replace: true });
        await loadEncounter(queue[0].id);
      } else {
        setLoading(false);
      }
    };

    init();

    return () => {
      isMounted = false;
    };
  }, [visitIdParam, loadTriageQueue, loadEncounter, setSearchParams]);

  // Handle Encounter Change via Selector
  const handleSelectVisit = (vId: number) => {
    setSearchParams({ visit: String(vId) });
  };

  // Submit Triage
  const handleSaveTriage = async (payload: CreateTriagePayload) => {
    if (!activeVisit || !patient) return;
    setSubmitting(true);
    setError(null);
    setSuccessMessage(null);

    try {
      let savedTriage: TriageVitals;

      if (existingTriage && isEditing) {
        savedTriage = await updateTriageVitals(existingTriage.id, payload);
      } else {
        savedTriage = await createTriageVitals({
          ...payload,
          visit: activeVisit.id,
          patient: patient.id
        });
      }

      // Transition visit lifecycle: Forward to Doctor Consultation Queue
      const updatedVisit = await updateVisit(activeVisit.id, {
        status: 'TRIAGED',
        current_queue: 'DOCTOR'
      });

      setActiveVisit(updatedVisit);
      setExistingTriage(savedTriage);
      setIsEditing(false);

      const patientName =
        patient.name ||
        `${patient.first_name || ''} ${patient.last_name || ''}`.trim() ||
        `Patient #${patient.id}`;

      setSuccessMessage(
        `Triage vitals recorded successfully for ${patientName}. Encounter #${activeVisit.token_number ?? activeVisit.id} has been forwarded to Doctor Consultation Queue.`
      );

      // Refresh queue in background
      loadTriageQueue();
    } catch (err) {
      setError(parseApiError(err));
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

        {/* Encounter Selector Dropdown */}
        {triageQueue.length > 0 && (
          <div className="flex items-center gap-2 bg-white px-3 py-2 rounded-lg border border-slate-200 shadow-2xs">
            <Users className="w-4 h-4 text-slate-400" aria-hidden="true" />
            <label htmlFor="triage-encounter-select" className="text-xs font-bold text-slate-700 whitespace-nowrap">
              Active Encounter:
            </label>
            <select
              id="triage-encounter-select"
              value={activeVisit?.id || ''}
              onChange={(e) => handleSelectVisit(Number(e.target.value))}
              className="text-xs font-semibold text-slate-800 bg-transparent border-0 focus:ring-0 cursor-pointer"
            >
              {triageQueue.map((v) => (
                <option key={v.id} value={v.id}>
                  Token #{v.token_number ?? v.id} - Patient #{v.patient} ({v.status})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Global Error Notice */}
      {error && (
        <ErrorAlert
          title="Clinical Triage Error"
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
                The encounter is now marked <strong>Ready for Doctor</strong> and visible in the Medical Officer queue.
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
            />
          ) : (
            <TriageVitalsForm
              initialVitals={existingTriage}
              onSubmit={handleSaveTriage}
              loading={submitting}
              nurseName={user?.username}
              onCancel={existingTriage ? () => setIsEditing(false) : undefined}
            />
          )}
        </>
      )}
    </div>
  );
};

export default Triage;
