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
  updateVisit
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
import { Stethoscope, ArrowLeft, CheckCircle2, Save } from 'lucide-react';

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

  const [chiefComplaint, setChiefComplaint] = useState<string>('');
  const [clinicalHistory, setClinicalHistory] = useState<string>('');
  const [clinicalAssessment, setClinicalAssessment] = useState<string>('');
  const [diagnosisCode, setDiagnosisCode] = useState<string>('');
  const [diagnosisName, setDiagnosisName] = useState<string>('');
  const [treatmentPlan, setTreatmentPlan] = useState<string>('');
  const [clinicalNotes, setClinicalNotes] = useState<string>('');

  const [orderDiagnostics, setOrderDiagnostics] = useState<boolean>(false);
  const [selectedTestMasterId, setSelectedTestMasterId] = useState<number | ''>('');
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
          const firstEligible = data.find((v) => v.status !== 'COMPLETED') || data[0];
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

      const patientData = await getPatient(visitData.patient);
      setPatient(patientData);

      const triageData = await getTriageVitals(vId);
      setTriage(triageData);

      const [consults, diagOrders, diagRes, rxList] = await Promise.all([
        getConsultations({ patient: visitData.patient }),
        getDiagnosticOrders({ visit: vId }),
        getDiagnosticResults(),
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

    setSubmitting(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const facilityId = visit.facility;
      const consultation = await createConsultation({
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
      });

      let diagOrderCreated = false;
      if (orderDiagnostics && selectedTestMasterId) {
        const order = await createDiagnosticOrder({
          visit: visit.id,
          facility: facilityId,
          priority: diagPriority,
          clinical_indication: diagIndication.trim() || `Assessment for ${diagnosisName.trim()}`,
          order_date: new Date().toISOString().split('T')[0]
        });

        await createTestRequest({
          diagnostic_order: order.id,
          test_master: Number(selectedTestMasterId)
        });
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

      let nextStatus = 'COMPLETED';
      let nextQueue = 'COMPLETED';
      if (diagOrderCreated) {
        nextStatus = 'WAITING_FOR_LAB';
        nextQueue = 'LAB';
      } else if (rxCreated) {
        nextStatus = 'WAITING_FOR_PHARMACY';
        nextQueue = 'PHARMACY';
      }

      await updateVisit(visit.id, {
        status: nextStatus,
        current_queue: nextQueue,
        chief_complaint: chiefComplaint.trim()
      });

      setSuccessMessage(
        `Consultation recorded successfully for ${patient.name} (Visit #${visit.visit_id}). Workflow advanced to ${nextStatus}.`
      );

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
            diagPriority={diagPriority}
            setDiagPriority={setDiagPriority}
            diagIndication={diagIndication}
            setDiagIndication={setDiagIndication}
            testMasters={testMasters}
            existingResults={existingResults}
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
            <div className="text-xs text-slate-600">
              Preserving Medical Officer clinical authorship. Prescribing Doctor: <strong>{user?.username}</strong>.
            </div>

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => navigate('/dashboard/doctor')}
                className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition cursor-pointer"
              >
                Cancel / Return to Queue
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="inline-flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs rounded-xl shadow-md transition disabled:opacity-50 cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
              >
                {submitting ? (
                  <LoadingSpinner size="sm" label="Saving..." />
                ) : (
                  <>
                    <Save className="w-4 h-4" aria-hidden="true" />
                    <span>Save & Complete Consultation</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </form>
      )}
    </div>
  );
};

export default Consultation;
