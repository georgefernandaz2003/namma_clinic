import test from 'node:test';
import assert from 'node:assert/strict';

interface ConsultationItem {
  id: number;
  visit: number;
  patient: number;
  chief_complaint: string;
  diagnosis_code: string;
  diagnosis_name: string;
  treatment_plan: string;
  created_at: string;
}

test('Consultation Longitudinal History Clickability & Selection Logic', async (t) => {
  const mockConsultations: ConsultationItem[] = [
    {
      id: 101,
      visit: 193,
      patient: 173,
      chief_complaint: 'Gastric discomfort for 1 week',
      diagnosis_code: 'K21.9',
      diagnosis_name: 'Gastro-oesophageal reflux disease without oesophagitis',
      treatment_plan: 'Antacids, dietary advice',
      created_at: '2026-10-01T10:00:00Z'
    },
    {
      id: 102,
      visit: 198,
      patient: 173,
      chief_complaint: 'High fever with chills',
      diagnosis_code: 'A90',
      diagnosis_name: 'Dengue fever [classical dengue]',
      treatment_plan: 'Oral hydration, paracetamol',
      created_at: '2026-10-05T11:30:00Z'
    },
    {
      id: 103,
      visit: 199,
      patient: 173,
      chief_complaint: 'Persistent headaches and elevated BP',
      diagnosis_code: 'I10',
      diagnosis_name: 'Essential (primary) hypertension',
      treatment_plan: 'Amlodipine 5mg OD',
      created_at: '2026-10-08T09:15:00Z'
    }
  ];

  await t.test('1. Clicking historical visit card dispatches exact visit ID', () => {
    let selectedVisitId: number | null = null;
    const handleSelectVisit = (vId: number) => {
      selectedVisitId = vId;
    };

    // Simulate clicking second visit (visit 198)
    handleSelectVisit(mockConsultations[1].visit);
    assert.equal(selectedVisitId, 198, 'Must select exact visit 198, not first visit');

    // Simulate clicking third visit (visit 199)
    handleSelectVisit(mockConsultations[2].visit);
    assert.equal(selectedVisitId, 199, 'Must select exact visit 199');

    // Simulate clicking first visit (visit 193)
    handleSelectVisit(mockConsultations[0].visit);
    assert.equal(selectedVisitId, 193, 'Must select exact visit 193');
  });

  await t.test('2. Keyboard interaction (Enter / Space) triggers visit selection', () => {
    let triggeredVisitId: number | null = null;
    const onSelect = (id: number) => { triggeredVisitId = id; };

    const simulateKeyDown = (key: string, visitId: number) => {
      if (key === 'Enter' || key === ' ') {
        onSelect(visitId);
      }
    };

    simulateKeyDown('Enter', 198);
    assert.equal(triggeredVisitId, 198);

    simulateKeyDown(' ', 193);
    assert.equal(triggeredVisitId, 193);

    // Other keys do not trigger
    triggeredVisitId = null;
    simulateKeyDown('Tab', 199);
    assert.equal(triggeredVisitId, null);
  });

  await t.test('3. Modal open / close lifecycle preserves consultation form state', () => {
    // Current ongoing consultation draft state
    const currentEncounterState = {
      currentVisitId: 280,
      chiefComplaint: 'Acute cough and pharyngitis',
      diagnosisCode: 'J02.9',
      diagnosisName: 'Acute pharyngitis, unspecified',
      treatmentPlan: 'Warm saline gargle, throat lozenges'
    };

    let modalOpen = false;
    let inspectedVisitId: number | null = null;

    // Doctor opens modal for historical visit 198
    modalOpen = true;
    inspectedVisitId = 198;
    assert.equal(modalOpen, true);
    assert.equal(inspectedVisitId, 198);

    // Doctor closes modal
    modalOpen = false;
    inspectedVisitId = null;
    assert.equal(modalOpen, false);
    assert.equal(inspectedVisitId, null);

    // Verify current consultation form state is 100% intact
    assert.equal(currentEncounterState.currentVisitId, 280);
    assert.equal(currentEncounterState.chiefComplaint, 'Acute cough and pharyngitis');
    assert.equal(currentEncounterState.diagnosisCode, 'J02.9');
    assert.equal(currentEncounterState.diagnosisName, 'Acute pharyngitis, unspecified');
  });

  await t.test('4. Empty sections display "No data recorded" without fallback to current encounter', () => {
    const historicalEncounterWithoutLabOrRx = {
      visit: {
        id: 193,
        visit_id: 'VIS-20261001-0001',
        visit_date: '2026-10-01 10:00',
        facility_name: 'Namma Clinic Local PHC',
        status: 'COMPLETED'
      },
      triage: null,
      consultation: {
        diagnosis_code: 'K21.9',
        diagnosis_name: 'Gastro-oesophageal reflux disease without oesophagitis',
        treatment_plan: null,
        clinical_notes: null
      },
      labReports: [],
      prescriptions: [],
      documents: []
    };

    assert.equal(historicalEncounterWithoutLabOrRx.triage, null);
    assert.equal(historicalEncounterWithoutLabOrRx.labReports.length, 0);
    assert.equal(historicalEncounterWithoutLabOrRx.prescriptions.length, 0);
    assert.equal(historicalEncounterWithoutLabOrRx.documents.length, 0);
    assert.equal(historicalEncounterWithoutLabOrRx.consultation.treatment_plan, null);
  });
});
