# NAMMA CLINIC — DOCTOR CONSULTATION → LAB TEST FLOW AUDIT

**Audit Date:** September 22, 2026  
**Audit Scope:** Read-Only Implementation Audit of Patient Registration → OPD Token → Nurse Triage → Doctor Consultation → Lab Order → Lab Queue → Sample Collection → Result Entry → Verification → Doctor Review  
**Baseline HEAD:** `e037d5fd93eb67d4c5f6576e85ebbb6ac976fff3`  
**Branch:** `feature/namma-clinic-demo-data-model`  
**Repository State:** Unmodified · Read-Only Verification  

---

## 1. Executive Summary

This audit evaluates the complete end-to-end operational and clinical data flow from patient registration to laboratory test resulting and doctor review within the Namma Clinic repository.

### Key Audit Conclusions:
1. **Token Invariant Integrity (PASS):**
   - **One clinical Visit/Encounter generates exactly ONE OPD token.**
   - Ordering one or multiple laboratory tests **does NOT create additional OPD tokens**.
   - Lab orders maintain their own distinct operational identifiers (`id` and `LAB-{id:04d}`).
   - Schema enforcement via `OneToOneField(Visit, ...)` on `Token.visit` strictly prevents multiple tokens per visit at the database level.
2. **Laboratory Queue Separation (PASS):**
   - The laboratory does **NOT** overload or duplicate the OPD token queue.
   - The lab workstation (`frontend/src/pages/Laboratory.tsx`) queries dedicated `LabOrder` entities via `GET /api/lab/orders/?facility={id}`.
3. **Linkage Defect Identified (WARN):**
   - In `frontend/src/pages/Consultation.tsx` (lines 245–255), when diagnostic investigations are ordered, the API request `POST /api/lab/orders/` transmits `{ patient, facility, test_master }` but **omits `consultation: consultationId`** and **`doctor`**.
   - Consequently, while `LabOrder.patient` is correctly linked, `LabOrder.consultation` remains `NULL` for orders created via the doctor consultation UI. Tracing from Consultation $\to$ Lab Order via the direct foreign key fails at runtime, falling back to correlation by `patient_id`.
4. **Doctor Return Queue Status (WARN):**
   - Upon completing a consultation where lab tests are ordered, `backend/apps/consultations/views.py` sets `visit.current_queue` to `'PHARMACY'` (if prescription items exist) or `'COMPLETED'` (if no medicines are prescribed).
   - The visit is **never** transitioned to `current_queue = 'LAB'`. When the lab results are verified, there is no automated hook transitioning the patient back into the Doctor's queue (`current_queue = 'DOCTOR'`). The doctor reviews completed lab results asynchronously via the **Diagnostics Lab** console (`/lab`) or the **Patient Longitudinal Health Record** (`/patients/:id`).

---

## 2. Actual End-to-End Flow Analysis

```
[1. Patient Registration]
      │
      ▼ (POST /api/patients/ - 0 Tokens Created)
[2. OPD Check-in / Token Issuance]
      │
      ▼ (POST /api/visits/ - EXACTLY 1 Token & 1 Visit Created)
[3. Nurse Vitals Triage]
      │
      ▼ (POST /api/triage/ - 0 Tokens Created, Visit transitions to DOCTOR queue)
[4. Doctor Consultation]
      │
      ▼ (POST /api/consultations/ - 0 Tokens Created, Visit transitions to PHARMACY/COMPLETED)
[5. Lab Orders Created]
      │
      ▼ (POST /api/lab/orders/ - N Lab Orders Created, 0 Tokens Created)
[6. Lab Station Queue]
      │
      ▼ (GET /api/lab/orders/ - Separate LabOrder queue in Laboratory.tsx)
[7. Specimen Collection]
      │
      ▼ (POST /api/lab/orders/{id}/collect-sample/ - Unique Barcode Created, 0 Tokens Created)
[8. Result Entry & Verification]
      │
      ▼ (POST /api/lab/orders/{id}/save-result/ - LabResult Released, 0 Tokens Created)
[9. Doctor Result Review]
      │
      ▼ (Asynchronous review via /lab or /patients/:id - 0 Tokens Created)
```

---

## 3. Token Generation Flow

### Implementation Location:
- **Model:** `backend/apps/visits/models.py` (Lines 99–115)
- **View:** `backend/apps/visits/views.py` (Lines 118–185, `VisitViewSet.create`)
- **Frontend Trigger:** `frontend/src/pages/Queue.tsx` (Lines 101–138, `handleIssueToken`) and `frontend/src/pages/Patients.tsx` (Token modal)

### Logic Verification:
When a patient is admitted for an outpatient encounter, `POST /api/visits/` is invoked:
```python
# backend/apps/visits/views.py (Lines 140-174)
with transaction.atomic():
    max_token = Token.objects.select_for_update().filter(
        facility_id=facility_id, date=today
    ).aggregate(models.Max('token_number'))['token_number__max'] or 0
    
    token_number = max_token + 1
    base_id = f"VIS-F{facility_id}-{today.strftime('%Y%m%d')}-{token_number:03d}"
    visit = Visit.objects.create(
        visit_id=visit_id,
        patient_id=patient_id,
        facility_id=facility_id,
        opd_date=today,
        current_queue='TRIAGE',
        status='WAITING_FOR_TRIAGE',
        ...
    )
    token = Token.objects.create(
        token_number=token_number,
        visit=visit,
        facility_id=facility_id,
        date=today,
        priority=priority,
        status='WAITING'
    )
```

### Constraints:
1. `Token.visit` is a `OneToOneField(Visit, on_delete=models.CASCADE, related_name='token')`.
2. `UniqueConstraint(fields=['facility', 'date', 'token_number'], name='unique_facility_opd_date_token')`.
3. Token numbers are sequential per facility per operational date (restarting at #1 every morning).
4. Token issuance is restricted strictly to the current day (`today`).

---

## 4. Visit/Encounter Flow

### Lifecycle States:
- Initial State: `current_queue = 'TRIAGE'`, `status = 'WAITING_FOR_TRIAGE'`
- Post-Triage State: `current_queue = 'DOCTOR'`, `status = 'WAITING_FOR_DOCTOR'`
- In-Consultation State: `current_queue = 'DOCTOR'`, `status = 'IN_CONSULTATION'`
- Post-Consultation State:
  - If prescription items prescribed: `current_queue = 'PHARMACY'`, `status = 'WAITING_FOR_PHARMACY'`
  - If no prescription items: `current_queue = 'COMPLETED'`, `status = 'COMPLETED'`

### Integrity Controls (`clean()` method in `backend/apps/visits/models.py`):
- Line 64–71: Completed visits must have `current_queue = 'COMPLETED'`.
- Line 74–80 (FND-09): Advancing a visit to `DOCTOR` queue or `WAITING_FOR_DOCTOR` without recorded triage vitals raises a validation error.

---

## 5. Doctor Consultation Flow

### Implementation Location:
- **Model:** `backend/apps/consultations/models.py` (Lines 3–23)
- **View:** `backend/apps/consultations/views.py` (Lines 46–174, `ConsultationViewSet.create`)
- **Frontend Page:** `frontend/src/pages/Consultation.tsx` (Lines 206–280, `handleSaveConsultation`)

### Execution Details:
1. The doctor selects an active visit from `triagedVisits` (`visits/?facility={id}&queue=DOCTOR`).
2. The doctor reviews complaints and vital signs fetched via `GET /api/triage/?visit={id}`.
3. The doctor enters chief complaint, clinical assessment, ICD diagnosis code/name, notes, prescriptions, and selects diagnostic investigations.
4. On save, `POST /api/consultations/` is executed with:
   ```json
   {
     "visit": 14,
     "patient": 639,
     "facility": 112,
     "chief_complaint": "Persistent fever and headache",
     "clinical_assessment": "Suspected viral infection",
     "diagnosis_code": "A90",
     "diagnosis_name": "Dengue Fever / Pyrexia of Unknown Origin",
     "prescription_items": [...]
   }
   ```
5. `ConsultationViewSet` detects if a consultation for `visit_id` already exists:
   - If existing: Performs an idempotent **UPDATE** on the same record.
   - If new: Creates one `Consultation` record bound to `visit_id`.
   - **No new Visit or Token is created.**

---

## 6. Lab Order Flow

### Implementation Location:
- **Model:** `backend/apps/laboratory/models.py` (Lines 13–29)
- **View:** `backend/apps/laboratory/views.py` (Lines 45–70, `LabOrderViewSet`)
- **Frontend Trigger:** `frontend/src/pages/Consultation.tsx` (Lines 245–255)

### Execution Trace:
For each test ID selected in `selectedTestIds`, `Consultation.tsx` loops and executes:
```typescript
// frontend/src/pages/Consultation.tsx (Lines 245-255)
for (const testId of selectedTestIds) {
  try {
    await api.post('lab/orders/', {
      patient: selectedVisit.patient,
      facility: activeFacility.id,
      test_master: testId
    });
  } catch (err) {
    console.error('Failed to order lab test', err);
  }
}
```

### Observed Behavior:
- **Token Count:** **0 tokens created.**
- **Visit Count:** **0 visits created.**
- **Lab Order Count:** Exactly $N$ `LabOrder` records created for $N$ selected tests.
- **Linkage Finding (WARN):** `consultation` parameter is omitted from the request body. `LabOrder.consultation` remains `NULL` in the database.

---

## 7. Lab Queue Flow

### Analysis:
1. Is the lab queue an OPD token queue?
   - **NO.** The lab queue is an independent operational queue backed by the `LabOrder` model.
2. How does the Lab Technician view the queue?
   - In `frontend/src/pages/Laboratory.tsx` (Line 25):
     `GET /api/lab/orders/?facility={activeFacility.id}`
   - The response lists all lab orders sorted by `-order_date`.
   - Filter tabs exist for `ALL`, `ORDERED`, `SAMPLE_COLLECTED`, `VERIFIED`.
3. What is `Visit.current_queue = 'LAB'`?
   - In `backend/apps/visits/models.py`, `QUEUE_CHOICES` defines `('LAB', 'Laboratory Queue')`.
   - In `frontend/src/pages/Queue.tsx`, a `LAB` tab filters `visits/?queue=LAB`.
   - **Runtime Audit:** A database inspection (`Visit.objects.filter(current_queue='LAB')`) found **0 visits in this queue**. `ConsultationViewSet` transitions visits directly to `'PHARMACY'` or `'COMPLETED'`. The lab does not consume the OPD visit queue.

---

## 8. Sample Flow

### Implementation Location:
- **Model:** `backend/apps/laboratory/models.py` (Lines 30–39, `LabSample`)
- **View Action:** `backend/apps/laboratory/views.py` (Lines 71–105, `collect_sample`)
- **Frontend Action:** `frontend/src/pages/Laboratory.tsx` (Lines 79–109, `handleCollectSample`)

### Execution Details:
1. In `Laboratory.tsx`, the Lab Technician clicks `Collect Sample`.
2. Calls `POST /api/lab/orders/{id}/collect-sample/` with `{ "sample_type": "Blood / Serum", "sample_code": "SMP-2026-XXXX" }`.
3. Backend creates a `LabSample` instance with:
   - Unique specimen barcode (`sample_code`)
   - Auto timestamp (`collected_at`)
   - Technician reference (`collected_by = request.user`)
4. Updates `LabOrder.status = 'SAMPLE_COLLECTED'`.
5. Logs immutable audit event `LAB_SAMPLE_COLLECTED`.
6. **Token Count:** **0 tokens created.**

---

## 9. Result & Verification Flow

### Implementation Location:
- **Model:** `backend/apps/laboratory/models.py` (Lines 40–57, `LabResult`)
- **View Action:** `backend/apps/laboratory/views.py` (Lines 106–145, `save_result`)
- **Frontend Action:** `frontend/src/pages/Laboratory.tsx` (Lines 111–134, `handleSaveResult`)

### Execution Details:
1. In `Laboratory.tsx`, the Lab Technician clicks `Enter Result`.
2. Modal displays the test name, reference range, and unit pre-populated from `LabTestMaster`.
3. Technician enters `result_value`, selects `interpretation_flag` (`NORMAL`, `HIGH`, `LOW`, `CRITICAL`), and enters notes.
4. Submits `POST /api/lab/orders/{id}/save-result/`.
5. Backend creates `LabResult` linked to `LabOrder` via `OneToOneField`.
6. Updates `LabOrder.status = 'VERIFIED'`.
7. Sets `verified_by = request.user` and `verified_at = timezone.now()`.
8. Logs immutable audit event `LAB_RESULT_VERIFIED`.
9. **Token Count:** **0 tokens created.**

---

## 10. Doctor Result Review Flow

### How the Doctor Reviews Lab Results:
1. **Primary Route: Diagnostics Laboratory Console (`/lab`):**
   - Doctor sidebar includes item #5: `Diagnostics Lab` (`/lab`).
   - Doctor views the laboratory order list, specimen collection status, and released results.
   - Mutation buttons (`Collect Sample`, `Enter Result`) are disabled with read-only informative chips for doctors.
2. **Secondary Route: Patient Longitudinal Health Record (`/patients/:id`):**
   - Doctor opens patient profile.
   - Dedicated tab: `Diagnostic Investigations & Laboratory Results` (`PatientDetail.tsx` lines 930–985).
   - Fetches `GET /api/patients/{id}/medical-records/`.
   - Displays all historical and current lab results with order date, investigation name, test code, result value, units, high/low flags, and verifying technician name.
3. **Queue Behavior on Doctor Return:**
   - Because the Visit was marked `PHARMACY` or `COMPLETED` when the consultation was submitted, the patient does **not** automatically reappear in the Doctor's live active queue (`visits/?queue=DOCTOR`).
   - If the patient consults the doctor on the same day to discuss results, the doctor inspects the results directly via `/patients/:id` or `/lab` under the **same existing Visit/Token**.
   - No new OPD token is required or generated for reviewing results.

---

## 11. Critical Business Question — Token Count Analysis

| Event / Scenario | Tokens Generated | Database Mechanism | Status |
| :--- | :---: | :--- | :--- |
| **1. Patient Registration** | **0** | `PatientViewSet.create()` creates `Patient` record only. | **PASS** |
| **2. One Clinical Visit / Check-in** | **1** | `VisitViewSet.create()` atomically creates 1 `Visit` and 1 `Token`. | **PASS** |
| **3. Doctor Consultation** | **0** | `ConsultationViewSet.create()` updates existing Visit encounter. | **PASS** |
| **4. Ordering 1 Lab Test** | **0** | `LabOrderViewSet.create()` creates 1 `LabOrder`. | **PASS** |
| **5. Ordering Multiple Lab Tests (e.g. 5 tests)** | **0** | Creates 5 `LabOrder` records. 0 tokens. | **PASS** |
| **6. Patient Returning to Doctor for Results** | **0** | Doctor reviews in `/patients/:id` or `/lab` under existing visit. | **PASS** |

### Summary Verification:
- **OPD Tokens for Entire Journey:** **EXACTLY ONE (1).**
- **Lab Tests Created per Token:** **Arbitrary ($N \ge 0$).**
- **Token Duplication Risk:** **ZERO.**

---

## 12. Database Relationship Trace

```
[Patient] (id: 602)
   │
   ├── (1 : N) ── [Visit] (id: 14, visit_id: "VIS-F112-20260921-001")
   │                 │
   │                 ├── (1 : 1) ── [Token] (token_number: 1, date: 2026-09-21)
   │                 │
   │                 ├── (1 : 1) ── [TriageVitals] (BP: 120/80, SpO2: 98%)
   │                 │
   │                 └── (1 : 1) ── [Consultation] (id: 70, diagnosis: "Type 2 Diabetes")
   │                                   │
   │                                   ├── (1 : 1) ── [Prescription] (status: "ACTIVE")
   │                                   │                 └── (1 : N) ── [PrescriptionItem]
   │                                   │
   │                                   └── (1 : N) ── [LabOrder] (id: 51, status: "VERIFIED")
   │                                                     │   *(Note: Linkage is NULL in UI orders)*
   │                                                     ├── (1 : 1) ── [LabSample] (sample_code: "SMP-0051")
   │                                                     ├── (1 : 1) ── [LabResult] (value: "168 mg/dL", flag: "HIGH")
   │                                                     └── (N : 1) ── [LabTestMaster] (code: "LIPID-01")
```

---

## 13. API Endpoint Trace

| Step | Operation | Method | API Endpoint | Payload Parameters | Response Status |
| :---: | :--- | :---: | :--- | :--- | :---: |
| 1 | Patient Registration | `POST` | `/api/patients/` | `{ name, mobile, gender, dob, facility }` | `201 Created` |
| 2 | Issue OPD Token | `POST` | `/api/visits/` | `{ patient, facility, visit_type, priority, chief_complaint }` | `201 Created` |
| 3 | Fetch Queue (Triage) | `GET` | `/api/visits/?facility={id}&queue=TRIAGE` | Query params: `facility`, `date`, `queue` | `200 OK` |
| 4 | Call Patient to Triage | `POST` | `/api/visits/call-next/` | `{ facility, queue: 'TRIAGE' }` | `200 OK` |
| 5 | Submit Vitals Triage | `POST` | `/api/triage/` | `{ visit, patient, systolic, diastolic, pulse, spo2 }` | `201 Created` |
| 6 | Fetch Queue (Doctor) | `GET` | `/api/visits/?facility={id}&queue=DOCTOR` | Query params: `facility`, `date`, `queue` | `200 OK` |
| 7 | Call Patient to Consult | `POST` | `/api/visits/call-next/` | `{ facility, queue: 'DOCTOR' }` | `200 OK` |
| 8 | Submit Consultation | `POST` | `/api/consultations/` | `{ visit, patient, facility, diagnosis_name, prescription_items }` | `201 Created` |
| 9 | Order Diagnostic Test | `POST` | `/api/lab/orders/` | `{ patient, facility, test_master }` | `201 Created` |
| 10 | Fetch Lab Orders Queue | `GET` | `/api/lab/orders/?facility={id}` | Query params: `facility`, `status` | `200 OK` |
| 11 | Collect Specimen | `POST` | `/api/lab/orders/{id}/collect-sample/` | `{ sample_type, sample_code }` | `200 OK` |
| 12 | Save & Verify Result | `POST` | `/api/lab/orders/{id}/save-result/` | `{ result_value, unit, reference_range, interpretation_flag }` | `200 OK` |
| 13 | Review Patient Records | `GET` | `/api/patients/{id}/medical-records/` | URL path: `{id}` | `200 OK` |

---

## 14. Frontend Route & Page Trace

| Station / Workflow | Primary User Role | Route Path | React Component | Key Actions Rendered |
| :--- | :--- | :--- | :--- | :--- |
| **Patient Registration** | `NURSE`, `HOSPITAL_ADMIN` | `/patients` | `Patients.tsx` | `+ Register New Patient`, `Issue Token` |
| **OPD Queue & Check-in** | `NURSE`, `HOSPITAL_ADMIN` | `/queue` | `Queue.tsx` | `Issue New OPD Token`, `Call Next Patient`, Queue tabs |
| **Vital Signs Triage** | `NURSE` | `/triage` | `Triage.tsx` | Record BP, Pulse, SpO2, Temp; `Save & Send to Doctor Queue` |
| **Doctor Consultation** | `DOCTOR` | `/consultation` | `Consultation.tsx` | Diagnosis entry, Rx prescribing, Checkbox test ordering, Referrals |
| **Diagnostics Lab** | `LAB_TECHNICIAN`, `DOCTOR` | `/lab` | `Laboratory.tsx` | `Collect Sample` (Tech only), `Enter Result` (Tech only), Status badges |
| **Longitudinal Records** | `DOCTOR`, `NURSE`, `ADMIN` | `/patients/:id` | `PatientDetail.tsx` | View Visits, Consultations, Prescriptions, Lab Reports |

---

## 15. Role & Permission Governance Analysis

| Role | Consultation | Order Lab Tests | Collect Samples | Enter & Verify Results | Issue OPD Token | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`DOCTOR`** | **ALLOWED** | **ALLOWED** | **DENIED** (UI Gated) | **DENIED** (UI Gated) | **DENIED** (UI Gated) | **PASS** |
| **`LAB_TECHNICIAN`** | **DENIED** (403) | **DENIED** (403) | **ALLOWED** | **ALLOWED** | **DENIED** (403) | **PASS** |
| **`NURSE`** | **DENIED** (403) | **DENIED** (403) | **DENIED** (UI Gated) | **DENIED** (UI Gated) | **ALLOWED** | **PASS** |
| **`HOSPITAL_ADMIN`** | **DENIED** (403) | **DENIED** (403) | **DENIED** (UI Gated) | **DENIED** (UI Gated) | **ALLOWED** | **PASS** |

---

## 16. Duplicate Token Risk Analysis

| Scenario Tested / Inspected | Code Mechanism Evaluated | Duplicate Token Created? | Risk Level |
| :--- | :--- | :---: | :---: |
| **Doctor orders 1 lab test** | `POST /api/lab/orders/` creates `LabOrder` only. | **NO** | **NONE** |
| **Doctor orders multiple tests** | Repeated `POST /api/lab/orders/` creates `LabOrder` records. | **NO** | **NONE** |
| **Multiple samples collected** | `LabSample` uses `OneToOneField(LabOrder)` with uniqueness check. | **NO** | **NONE** |
| **Result verified and released** | `LabResult` uses `OneToOneField(LabOrder)`. | **NO** | **NONE** |
| **Doctor reviews results** | `GET` requests on `/lab` and `/patients/:id`. | **NO** | **NONE** |
| **Consultation re-submitted** | `ConsultationViewSet.create()` updates existing consultation. | **NO** | **NONE** |
| **Database Constraint Guard** | `Token.visit` is a unique `OneToOneField`. | **ENFORCED** | **NONE** |

---

## 17. Classified Findings (PASS / WARN / FAIL / UNKNOWN)

### [PASS-01] Single Token Invariant per Visit Encounter
- **Category:** Core Business Rule
- **Classification:** **PASS**
- **Evidence:** `backend/apps/visits/models.py` (Line 101: `visit = models.OneToOneField(Visit, ...)`).
- **Finding:** A clinical visit has at most one token. No code path creates multiple tokens for a single visit.

### [PASS-02] Lab Tests Do Not Generate OPD Tokens
- **Category:** Business Logic
- **Classification:** **PASS**
- **Evidence:** `backend/apps/laboratory/views.py` (Lines 45–70).
- **Finding:** Lab orders are independent records. Calling `POST /api/lab/orders/` does not invoke `Token.objects.create()`.

### [PASS-03] Separate Operational Lab Queue
- **Category:** Workflow Architecture
- **Classification:** **PASS**
- **Evidence:** `frontend/src/pages/Laboratory.tsx` (Line 25) and `backend/apps/laboratory/views.py` (Line 61).
- **Finding:** The lab operates on its own dedicated `LabOrder` queue, not by injecting artificial visits into the OPD queue.

### [PASS-04] Distinct Test Identifiers
- **Category:** Data Model
- **Classification:** **PASS**
- **Evidence:** `backend/apps/laboratory/models.py` (Lines 13–57).
- **Finding:** Each test ordered has an independent primary key (`id`), a specimen barcode (`SMP-XXXX`), and a unique `LabResult`.

### [PASS-05] Role-Based Action Gating on Lab Actions
- **Category:** RBAC & Safety
- **Classification:** **PASS**
- **Evidence:** `frontend/src/pages/Laboratory.tsx` (Lines 310–335).
- **Finding:** Non-lab roles (Doctor, Admin) cannot trigger `Collect Sample` or `Enter Result` buttons.

---

### [WARN-01] Missing Consultation Link in Frontend Lab Order Payload
- **Category:** Entity Linkage
- **Classification:** **WARN**
- **File:** `frontend/src/pages/Consultation.tsx` (Lines 245–255)
- **Relevant Code:**
  ```typescript
  // Line 247-251
  await api.post('lab/orders/', {
    patient: selectedVisit.patient,
    facility: activeFacility.id,
    test_master: testId
    // consultation and doctor are omitted!
  });
  ```
- **Finding:** The backend `LabOrder` model contains `consultation = models.ForeignKey(Consultation, null=True, blank=True)`. However, `Consultation.tsx` does not include `consultation: consultationId` or `doctor: user.id` in the POST payload. As confirmed by database inspection (`LabOrder #55` and `#56`), runtime lab orders created via the UI have `consultation_id = NULL`.
- **Impact:** Tracing from `Consultation` $\to$ `LabOrder` via foreign key fails for UI-created orders. Tracing currently relies on `LabOrder.patient_id == Patient.id`.

### [WARN-02] Visit Queue Does Not Transition to LAB or Return to DOCTOR
- **Category:** Workflow Automation
- **Classification:** **WARN**
- **File:** `backend/apps/consultations/views.py` (Lines 158–171) and `backend/apps/laboratory/views.py` (Lines 106–145)
- **Finding:**
  1. When a doctor orders lab tests in `Consultation.tsx`, `ConsultationViewSet.create()` transitions the visit directly to `'PHARMACY'` (if medicines prescribed) or `'COMPLETED'` (if no medicines prescribed). It does not set `visit.current_queue = 'LAB'`.
  2. When the lab technician verifies results in `save_result()`, the visit status is not updated to indicate lab completion, nor is the patient returned to the doctor's active consultation queue.
- **Impact:** Doctors review lab results asynchronously via `/patients/:id` or `/lab` rather than through an automated queue loop-back.

---

## 18. Recommended Corrections (For Identified Warnings Only)

*Note: In accordance with audit instructions, no code has been modified. The following are recommended for subsequent implementation:*

1. **Fix Consultation Linkage in `Consultation.tsx`:**
   In `frontend/src/pages/Consultation.tsx` (Line 248), update the payload to include `consultation` and `doctor`:
   ```typescript
   await api.post('lab/orders/', {
     patient: selectedVisit.patient,
     facility: activeFacility.id,
     test_master: testId,
     consultation: consultationId,
     doctor: user?.id
   });
   ```
2. **Auto-Populate Doctor in `LabOrderViewSet`:**
   In `backend/apps/laboratory/views.py`, add `perform_create(self, serializer)`:
   ```python
   def perform_create(self, serializer):
       serializer.save(doctor=self.request.user)
   ```
3. **Optional Intermediate Lab Queue Transition:**
   If business requirements mandate that patients physically wait in clinic for lab results before seeing the doctor again, `ConsultationViewSet` should set `visit.current_queue = 'LAB'` when tests are ordered without immediate completion, and `save_result()` should transition the visit back to `current_queue = 'DOCTOR'`, `status = 'LAB_COMPLETED'`.

---

## 19. Final Audit Verdict

- **Read-Only Audit Concluded:** YES
- **Application Code Modified:** NO (0 lines modified)
- **Database Schema / Data Modified:** NO (0 changes)
- **Overall Evaluation:** **PASS with 2 Workflow Warnings (WARN-01, WARN-02)**
