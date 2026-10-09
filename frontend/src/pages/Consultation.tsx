import React, { useState, useEffect, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  getVisits,
  getVisit,
  getPatient,
  getTriageVitals,
  getConsultations,
  createConsultation,
  getDiagnosticTestMasters,
  createDiagnosticOrder,
  createTestRequest,
  getDiagnosticOrders,
  getDiagnosticResults,
  getMedicines,
  createPrescription,
  getPrescriptions,
  getFacilities,
  createReferralOrder,
  createFollowUpTask,
  updateVisit,
  updateConsultation
} from '../api/clinical';
import type {
  Visit,
  Patient,
  TriageVitals,
  Consultation as ConsultationType,
  DiagnosticTestMaster,
  DiagnosticOrder,
  DiagnosticResult,
  MedicineMaster,
  Prescription,
  Facility
} from '../types';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorAlert from '../components/common/ErrorAlert';
import EmptyState from '../components/common/EmptyState';
import ConsultationBanner from '../components/clinical/ConsultationBanner';
import TriageReviewCard from '../components/clinical/TriageReviewCard';
import ConsultationHistoryCard from '../components/clinical/ConsultationHistoryCard';
import ConsultationFormCard from '../components/clinical/ConsultationFormCard';
import DiagnosticOrderCard from '../components/clinical/DiagnosticOrderCard';
import PrescriptionCard, { type RxItemInput } from '../components/clinical/PrescriptionCard';
import ReferralFollowUpCard from '../components/clinical/ReferralFollowUpCard';
import { Stethoscope, ArrowLeft, ArrowRight, CheckCircle2, Save, Clock, AlertCircle } from 'lucide-react';

export const Consultation: React.FC = () => {
  const { user, activeFacility } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const queryVisitId = new URLSearchParams(location.search).get('visit');
  const initialVisitId = queryVisitId ? parseInt(queryVisitId, 10) : location.state?.visitId;

  const [availableVisits, setAvailableVisits] = useState<Visit[]>([]);
  const [selectedVisitId, setSelectedVisitId] = useState<number | null>(initialVisitId || null);
  const [visit, setVisit] = useState<Visit | null>(null);
  const [patient, setPatient] = useState<Patient | null>(null);
  const [triage, setTriage] = useState<TriageVitals | null>(null);
  const [previousConsultations, setPreviousConsultations] = useState<ConsultationType[]>([]);
  const [existingOrders, setExistingOrders] = useState<DiagnosticOrder[]>([]);
  const [existingResults, setExistingResults] = useState<DiagnosticResult[]>([]);
  const [existingPrescriptions, setExistingPrescriptions] = useState<Prescription[]>([]);

  const [testMasters, setTestMasters] = useState<DiagnosticTestMaster[]>([]);
  const [medicines, setMedicines] = useState<MedicineMaster[]>([]);
  const [facilities, setFacilities] = useState<Facility[]>([]);

  const [loadingContext, setLoadingContext] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isEncounterCompleted, setIsEncounterCompleted] = useState<boolean>(false);

  const [chiefComplaint, setChiefComplaint] = useState<string>('');
  const [clinicalHistory, setClinicalHistory] = useState<string>('');
  const [clinicalAssessment, setClinicalAssessment] = useState<string>('');
  const [diagnosisCode, setDiagnosisCode] = useState<string>('');
  const [diagnosisName, setDiagnosisName] = useState<string>('');
  const [treatmentPlan, setTreatmentPlan] = useState<string>('');
  const [clinicalNotes, setClinicalNotes] = useState<string>('');

  const [orderDiagnostics, setOrderDiagnostics] = useState<boolean>(false);
  const [selectedTestMasterId, setSelectedTestMasterId] = useState<number | ''>('');
  const [selectedTestMasterIds, setSelectedTestMasterIds] = useState<number[]>([]);
  const [diagPriority, setDiagPriority] = useState<'ROUTINE' | 'URGENT' | 'STAT'>('ROUTINE');
  const [diagIndication, setDiagIndication] = useState<string>('');

  const [orderPrescription, setOrderPrescription] = useState<boolean>(false);
  const [prescriptionNotes, setPrescriptionNotes] = useState<string>('');
  const [selectedMedicineId, setSelectedMedicineId] = useState<number | ''>('');
  const [dosageInstructions, setDosageInstructions] = useState<string>('1-0-1 After Food for 5 days');
  const [prescriptionItems, setPrescriptionItems] = useState<RxItemInput[]>([]);

  const [orderReferral, setOrderReferral] = useState<boolean>(false);
  const [destFacilityId, setDestFacilityId] = useState<number | ''>('');
  const [referralUrgency, setReferralUrgency] = useState<'ROUTINE' | 'URGENT' | 'EMERGENCY'>('ROUTINE');
  const [referralReason, setReferralReason] = useState<string>('');

  const [scheduleFollowUp, setScheduleFollowUp] = useState<boolean>(false);
  const [followUpDate, setFollowUpDate] = useState<string>('');
  const [followUpCategory, setFollowUpCategory] = useState<'GENERAL' | 'NCD_ROUTINE' | 'POST_REFERRAL' | 'LAB_REVIEW'>('GENERAL');
  const [followUpInstructions, setFollowUpInstructions] = useState<string>('');

  useEffect(() => {
    const loadMasters = async () => {
      try {
        const [tests, meds, facs] = await Promise.all([
          getDiagnosticTestMasters(),
          getMedicines(),
          getFacilities()
        ]);
        setTestMasters(tests);
        setMedicines(meds);
        setFacilities(facs);
      } catch (err: unknown) {
        console.error('Failed to load clinical masters:', err);
      }
    };
    loadMasters();
  }, []);

  useEffect(() => {
    const loadQueue = async () => {
      try {
        const params: Record<string, string | number> = {};
        if (activeFacility?.id) {
          params.facility = activeFacility.id;
        }
        const data = await getVisits(params);
        setAvailableVisits(data);
        if (!selectedVisitId && data.length > 0) {
          const firstEligible =
            data.find((v) => v.status === 'DOCTOR_REVIEW' && (v.current_queue === 'DOCTOR' || !v.current_queue)) ||
            data.find((v) => ['TRIAGED', 'WAITING_FOR_DOCTOR'].includes(v.status) && (v.current_queue === 'DOCTOR' || !v.current_queue)) ||
            data.find((v) => v.status !== 'COMPLETED' && (v.current_queue === 'DOCTOR' || !v.current_queue)) ||
            data[0];
          setSelectedVisitId(firstEligible.id);
        }
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Failed to load encounter queue.';
        setError(msg);
      }
    };
    loadQueue();
  }, [activeFacility?.id, selectedVisitId]);

  const loadClinicalContext = useCallback(async (vId: number) => {
    setLoadingContext(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const visitData = await getVisit(vId);
      setVisit(visitData);
      setChiefComplaint(visitData.chief_complaint || '');
      setIsEncounterCompleted(visitData.status === 'COMPLETED' || visitData.status === 'WAITING_FOR_PHARMACY');

      const patientData = await getPatient(visitData.patient);
      setPatient(patientData);

      const triageData = await getTriageVitals(vId);
      setTriage(triageData);

      const [consults, diagOrders, diagRes, rxList] = await Promise.all([
        getConsultations({ patient: visitData.patient }),
        getDiagnosticOrders({ visit: vId }),
        getDiagnosticResults({ visit: vId }),
        getPrescriptions({ patient: visitData.patient })
      ]);

      setPreviousConsultations(consults);
      setExistingOrders(diagOrders);
      setExistingResults(diagRes);
      setExistingPrescriptions(rxList);

      const thisVisitConsult = consults.find((c) => c.visit === vId);
      if (thisVisitConsult) {
        setChiefComplaint(thisVisitConsult.chief_complaint);
        setClinicalHistory(thisVisitConsult.clinical_history || '');
        setClinicalAssessment(thisVisitConsult.clinical_assessment || '');
        setDiagnosisCode(thisVisitConsult.diagnosis_code || '');
        setDiagnosisName(thisVisitConsult.diagnosis_name || '');
        setTreatmentPlan(thisVisitConsult.treatment_plan || '');
        setClinicalNotes(thisVisitConsult.clinical_notes || '');
      } else {
        setClinicalHistory('');
        setClinicalAssessment('');
        setDiagnosisCode('');
        setDiagnosisName('');
        setTreatmentPlan('');
        setClinicalNotes('');
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to retrieve patient clinical context.';
      setError(msg);
    } finally {
      setLoadingContext(false);
    }
  }, []);

  useEffect(() => {
    if (selectedVisitId) {
      loadClinicalContext(selectedVisitId);
    } else {
      setLoadingContext(false);
    }
  }, [selectedVisitId, loadClinicalContext]);

  // Status and workflow calculations
  const hasExistingOrders = existingOrders.length > 0;

  // Check if ALL existing diagnostic orders and test requests are completed and verified
  const allLabOrdersCompleted =
    hasExistingOrders &&
    existingOrders.every((order) => {
      if (order.status === 'VERIFIED' || order.status === 'AMENDED') return true;
      if (order.test_requests && order.test_requests.length > 0) {
        return order.test_requests.every(
          (tr) =>
            tr.status === 'COMPLETED' &&
            (tr.diagnostic_result?.status === 'VERIFIED' || tr.diagnostic_result?.status === 'AMENDED')
        );
      }
      return false;
    });

  // Visit has active lab orders that are still pending
  const hasPendingLabOrders = hasExistingOrders && !allLabOrdersCompleted;

  // Has doctor selected any tests to order in the form right now?
  const testsToOrder = Array.from(
    new Set([
      ...selectedTestMasterIds,
      ...(selectedTestMasterId ? [Number(selectedTestMasterId)] : [])
    ])
  );
  const isOrderingNewLab = orderDiagnostics && testsToOrder.length > 0;

  let primaryButtonLabel = 'Save & Complete Consultation';
  let PrimaryButtonIcon = Save;
  let isPrimaryDisabled = submitting;
  let primaryButtonClass =
    'bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white';

  if (isOrderingNewLab) {
    primaryButtonLabel = 'Save & Send to Laboratory';
    primaryButtonClass =
      'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white';
  } else if (hasPendingLabOrders) {
    primaryButtonLabel = 'Awaiting Laboratory Results';
    isPrimaryDisabled = true;
    primaryButtonClass = 'bg-slate-300 text-slate-500 cursor-not-allowed';
  } else if (allLabOrdersCompleted) {
    primaryButtonLabel = 'Complete Consultation';
    PrimaryButtonIcon = CheckCircle2;
    primaryButtonClass =
      'bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white';
  }

  const handleSaveDraft = async () => {
    if (!visit || !patient) return;
    if (!chiefComplaint.trim()) {
      setError('Chief Complaint is required for clinical encounter documentation.');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const facilityId = visit.facility;
      const thisVisitConsult = previousConsultations.find((c) => c.visit === visit.id);
      const consultPayload = {
        visit: visit.id,
        patient: patient.id,
        facility: facilityId,
        chief_complaint: chiefComplaint.trim(),
        clinical_history: clinicalHistory.trim(),
        clinical_assessment: clinicalAssessment.trim(),
        diagnosis_code: diagnosisCode.trim() || 'E11',
        diagnosis_name: diagnosisName.trim() || 'Under Evaluation',
        treatment_plan: treatmentPlan.trim(),
        clinical_notes: clinicalNotes.trim(),
        follow_up_date: scheduleFollowUp && followUpDate ? followUpDate : null
      };

      if (thisVisitConsult) {
        await updateConsultation(thisVisitConsult.id, consultPayload);
      } else {
        await createConsultation(consultPayload);
      }
      setSuccessMessage('Draft clinical notes saved successfully.');
      await loadClinicalContext(visit.id);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to save draft notes.';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleNextPatient = async () => {
    try {
      const params: Record<string, string | number> = {};
      if (activeFacility?.id) {
        params.facility = activeFacility.id;
      }
      const data = await getVisits(params);
      setAvailableVisits(data);

      const nextVisit =
        data.find((v) => v.id !== visit?.id && v.status === 'DOCTOR_REVIEW' && (v.current_queue === 'DOCTOR' || !v.current_queue)) ||
        data.find((v) => v.id !== visit?.id && ['TRIAGED', 'WAITING_FOR_DOCTOR'].includes(v.status) && (v.current_queue === 'DOCTOR' || !v.current_queue)) ||
        data.find((v) => v.id !== visit?.id && v.status !== 'COMPLETED' && (v.current_queue === 'DOCTOR' || !v.current_queue));

      if (nextVisit) {
        setIsEncounterCompleted(false);
        setSelectedVisitId(nextVisit.id);
        navigate(`/consultation?visit=${nextVisit.id}`);
      } else {
        navigate('/dashboard/doctor');
      }
    } catch {
      navigate('/dashboard/doctor');
    }
  };

  const handleSaveConsultation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!visit || !patient) return;

    if (!chiefComplaint.trim()) {
      setError('Chief Complaint is required for clinical encounter documentation.');
      return;
    }
    if (!diagnosisCode.trim() || !diagnosisName.trim()) {
      setError('Diagnosis Code and Diagnosis Name are mandatory clinical records.');
      return;
    }

    if (hasPendingLabOrders && !isOrderingNewLab) {
      setError('Cannot complete consultation while required laboratory investigations are awaiting results.');
      return;
    }

    setSubmitting(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const facilityId = visit.facility;
      const thisVisitConsult = previousConsultations.find((c) => c.visit === visit.id);

      const consultPayload = {
        visit: visit.id,
        patient: patient.id,
        facility: facilityId,
        chief_complaint: chiefComplaint.trim(),
        clinical_history: clinicalHistory.trim(),
        clinical_assessment: clinicalAssessment.trim(),
        diagnosis_code: diagnosisCode.trim(),
        diagnosis_name: diagnosisName.trim(),
        treatment_plan: treatmentPlan.trim(),
        clinical_notes: clinicalNotes.trim(),
        follow_up_date: scheduleFollowUp && followUpDate ? followUpDate : null
      };

      const consultation = thisVisitConsult
        ? await updateConsultation(thisVisitConsult.id, consultPayload)
        : await createConsultation(consultPayload);

      let diagOrderCreated = false;
      if (isOrderingNewLab) {
        const order = await createDiagnosticOrder({
          visit: visit.id,
          facility: facilityId,
          priority: diagPriority,
          clinical_indication: diagIndication.trim() || `Assessment for ${diagnosisName.trim()}`,
          order_date: new Date().toISOString().split('T')[0]
        });

        for (const testId of testsToOrder) {
          await createTestRequest({
            diagnostic_order: order.id,
            test_master: testId
          });
        }
        diagOrderCreated = true;
      }

      let rxCreated = false;
      if (orderPrescription && (prescriptionNotes.trim() || prescriptionItems.length > 0)) {
        await createPrescription({
          consultation: consultation.id,
          patient: patient.id,
          facility: facilityId,
          notes: prescriptionNotes.trim() || 'Prescribed medications.',
          items: prescriptionItems.map((it) => ({
            medicine_id: it.medicine_id,
            medicine_name: it.medicine_name,
            dosage: it.dosage,
            frequency: it.frequency,
            duration_days: it.duration_days,
            quantity: it.quantity
          }))
        });
        rxCreated = true;
      }

      if (orderReferral && destFacilityId) {
        await createReferralOrder({
          patient: patient.id,
          visit: visit.id,
          source_facility: facilityId,
          destination_facility: Number(destFacilityId),
          urgency: referralUrgency,
          reason: referralReason.trim() || `Specialist care for ${diagnosisName.trim()}`,
          clinical_summary: treatmentPlan.trim() || chiefComplaint.trim()
        });
      }

      if (scheduleFollowUp && followUpDate) {
        await createFollowUpTask({
          patient: patient.id,
          facility: facilityId,
          due_date: followUpDate,
          category: followUpCategory,
          originating_visit: visit.id,
          clinical_instructions: followUpInstructions.trim() || `Follow-up evaluation for ${diagnosisName.trim()}`
        });
      }

      if (diagOrderCreated) {
        // CASE 2: Lab ordered -> Send to Laboratory. DO NOT mark completed.
        await updateVisit(visit.id, {
          status: 'WAITING_FOR_LAB',
          current_queue: 'LAB',
          chief_complaint: chiefComplaint.trim()
        });

        setSuccessMessage(
          `Diagnostic order issued for ${patient.name}. Patient sent to Laboratory Queue (Awaiting Results).`
        );
        setOrderDiagnostics(false);
        setSelectedTestMasterId('');
        setSelectedTestMasterIds([]);
      } else {
        // CASE 1 or CASE 4: Finalizing consultation
        let nextStatus = 'COMPLETED';
        let nextQueue = 'COMPLETED';
        if (rxCreated) {
          nextStatus = 'WAITING_FOR_PHARMACY';
          nextQueue = 'PHARMACY';
        }

        await updateVisit(visit.id, {
          status: nextStatus,
          current_queue: nextQueue,
          chief_complaint: chiefComplaint.trim()
        });

        setIsEncounterCompleted(true);
        setSuccessMessage(
          `Consultation completed successfully for ${patient.name} (Visit #${visit.visit_id}). Workflow advanced to ${nextStatus}.`
        );
      }

      await loadClinicalContext(visit.id);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to save clinical consultation record.';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => navigate('/dashboard/doctor')}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-bold rounded-lg shadow-2xs transition cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" aria-hidden="true" />
            <span>Doctor Dashboard</span>
          </button>
          <span className="text-slate-400">/</span>
          <h1 className="text-base font-bold text-slate-900 flex items-center gap-1.5">
            <Stethoscope className="w-4 h-4 text-emerald-600" aria-hidden="true" />
            Clinical Encounter & Consultation
          </h1>
        </div>

        <div className="flex items-center gap-2">
          <label htmlFor="visit-selector" className="text-xs font-bold text-slate-700 whitespace-nowrap">
            Active Encounter:
          </label>
          <select
            id="visit-selector"
            value={selectedVisitId || ''}
            onChange={(e) => setSelectedVisitId(Number(e.target.value))}
            className="text-xs font-medium bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-slate-900 focus:outline-none focus:border-emerald-600"
          >
            {availableVisits.map((v) => (
              <option key={v.id} value={v.id}>
                Token #{v.token_number || v.id} - {v.patient_details?.name || `Patient #${v.patient}`} ({v.status})
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}
      {successMessage && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs font-medium flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" aria-hidden="true" />
          <span>{successMessage}</span>
        </div>
      )}

      {loadingContext ? (
        <div className="p-16 flex justify-center bg-white rounded-2xl border border-slate-200">
          <LoadingSpinner size="lg" label="Loading patient clinical context & triage data..." />
        </div>
      ) : !visit || !patient ? (
        <EmptyState
          title="No Patient Encounter Selected"
          description="Select an outpatient visit from the queue to start recording the clinical examination."
          actionText="Go to Doctor Queue"
          onAction={() => navigate('/dashboard/doctor')}
        />
      ) : (
        <form onSubmit={handleSaveConsultation} className="space-y-6">
          <ConsultationBanner patient={patient} visit={visit} />
          <TriageReviewCard triage={triage} />
          <ConsultationHistoryCard consultations={previousConsultations} />
          <ConsultationFormCard
            chiefComplaint={chiefComplaint}
            setChiefComplaint={setChiefComplaint}
            clinicalHistory={clinicalHistory}
            setClinicalHistory={setClinicalHistory}
            clinicalAssessment={clinicalAssessment}
            setClinicalAssessment={setClinicalAssessment}
            diagnosisCode={diagnosisCode}
            setDiagnosisCode={setDiagnosisCode}
            diagnosisName={diagnosisName}
            setDiagnosisName={setDiagnosisName}
            treatmentPlan={treatmentPlan}
            setTreatmentPlan={setTreatmentPlan}
            clinicalNotes={clinicalNotes}
            setClinicalNotes={setClinicalNotes}
          />
          <DiagnosticOrderCard
            orderDiagnostics={orderDiagnostics}
            setOrderDiagnostics={setOrderDiagnostics}
            selectedTestMasterId={selectedTestMasterId}
            setSelectedTestMasterId={setSelectedTestMasterId}
            selectedTestMasterIds={selectedTestMasterIds}
            setSelectedTestMasterIds={setSelectedTestMasterIds}
            diagPriority={diagPriority}
            setDiagPriority={setDiagPriority}
            diagIndication={diagIndication}
            setDiagIndication={setDiagIndication}
            testMasters={testMasters}
            existingOrders={existingOrders}
            existingResults={existingResults}
            hasPendingLabOrders={hasPendingLabOrders}
            allLabOrdersCompleted={allLabOrdersCompleted}
          />
          <PrescriptionCard
            orderPrescription={orderPrescription}
            setOrderPrescription={setOrderPrescription}
            prescriptionNotes={prescriptionNotes}
            setPrescriptionNotes={setPrescriptionNotes}
            selectedMedicineId={selectedMedicineId}
            setSelectedMedicineId={setSelectedMedicineId}
            dosageInstructions={dosageInstructions}
            setDosageInstructions={setDosageInstructions}
            medicines={medicines}
            prescriptionItems={prescriptionItems}
            setPrescriptionItems={setPrescriptionItems}
          />
          <ReferralFollowUpCard
            visit={visit}
            facilities={facilities}
            orderReferral={orderReferral}
            setOrderReferral={setOrderReferral}
            destFacilityId={destFacilityId}
            setDestFacilityId={setDestFacilityId}
            referralUrgency={referralUrgency}
            setReferralUrgency={setReferralUrgency}
            referralReason={referralReason}
            setReferralReason={setReferralReason}
            scheduleFollowUp={scheduleFollowUp}
            setScheduleFollowUp={setScheduleFollowUp}
            followUpDate={followUpDate}
            setFollowUpDate={setFollowUpDate}
            followUpCategory={followUpCategory}
            setFollowUpCategory={setFollowUpCategory}
            followUpInstructions={followUpInstructions}
            setFollowUpInstructions={setFollowUpInstructions}
          />

          {/* Form Actions & Save */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 bg-white border border-slate-200 rounded-2xl shadow-xs">
            <div className="text-xs text-slate-600 space-y-1">
              <div>
                Preserving Medical Officer clinical authorship. Prescribing Doctor: <strong>{user?.username}</strong>.
              </div>
              {hasPendingLabOrders && !isOrderingNewLab && (
                <div className="text-amber-700 font-bold flex items-center gap-1.5 text-[11px]">
                  <Clock className="w-3.5 h-3.5" />
                  <span>Lab orders pending — Consultation completion locked until all results are verified.</span>
                </div>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={() => navigate('/dashboard/doctor')}
                className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition cursor-pointer"
              >
                Cancel / Return to Queue
              </button>

              {hasPendingLabOrders && !isOrderingNewLab && (
                <button
                  type="button"
                  id="save-draft-button"
                  onClick={handleSaveDraft}
                  disabled={submitting}
                  className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-xs rounded-xl border border-slate-300 transition cursor-pointer"
                >
                  Save Draft Notes
                </button>
              )}

              <button
                type="submit"
                id="consultation-primary-button"
                disabled={isPrimaryDisabled}
                className={`inline-flex items-center gap-2 px-6 py-2.5 font-bold text-xs rounded-xl shadow-md transition disabled:opacity-60 cursor-pointer focus:outline-none focus-visible:ring-2 ${primaryButtonClass}`}
              >
                {submitting ? (
                  <LoadingSpinner size="sm" label="Saving..." />
                ) : (
                  <>
                    <PrimaryButtonIcon className="w-4 h-4" aria-hidden="true" />
                    <span>{primaryButtonLabel}</span>
                  </>
                )}
              </button>

              {(isEncounterCompleted || visit.status === 'COMPLETED' || visit.status === 'WAITING_FOR_PHARMACY') && (
                <button
                  type="button"
                  id="next-patient-button"
                  onClick={handleNextPatient}
                  className="inline-flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-xs rounded-xl shadow-md transition cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
                >
                  <span>Next Patient</span>
                  <ArrowRight className="w-4 h-4" aria-hidden="true" />
                </button>
              )}
            </div>
          </div>
        </form>
      )}
    </div>
  );
};

export default Consultation;
