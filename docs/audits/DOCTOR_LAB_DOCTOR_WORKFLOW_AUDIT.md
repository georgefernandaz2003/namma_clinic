# NAMMA CLINIC — DOCTOR → LAB → DOCTOR WORKFLOW IMPLEMENTATION AUDIT

**Audit Date:** September 22, 2026  
**Audit Mode:** Read-Only Forensic Architecture & Workflow Audit  
**Baseline HEAD:** `e037d5fd93eb67d4c5f6576e85ebbb6ac976fff3`  
**Branch:** `feature/namma-clinic-demo-data-model`  
**Application Code Modified:** None (0 lines)  
**Database Modified:** None (0 changes)  

---

## 1. Executive Summary

This audit evaluates the real implementation of the clinical workflow when a patient transitions from:
$$\text{Registration} \to \text{OPD Token} \to \text{Nurse Triage} \to \text{Doctor Consultation} \to \text{Laboratory Investigation} \to \text{Patient Returns to Doctor} \to \text{Prescription / Final Discharge}$$

### Intended Core Business Workflow vs Actual Implementation:
1. **The Intended Design:**
   - One OPD Token covers the overall clinical encounter (Visit).
   - When a doctor orders laboratory investigations, a distinct **Lab Token / Order** is issued for the laboratory service queue.
   - Multiple tests (e.g. CBC, HbA1c, Lipid Profile) reside under that Lab Order.
   - The original OPD Encounter remains open (`WAITING_FOR_LAB`).
   - After the lab technician collects the specimen, enters results, and verifies them, the patient returns to the doctor (`DOCTOR_REVIEW`).
   - The doctor reviews the verified results within the same encounter, finalizes treatment/prescriptions, and completes the OPD encounter.
2. **The Actual Implementation:**
   - **No Lab Token Entity:** The system does not possess a `LabToken` model or daily laboratory sequence token. It relies on standard auto-incrementing `LabOrder.id` primary keys.
   - **Premature Encounter Termination:** When a doctor submits a consultation with lab orders, `ConsultationViewSet.create()` transitions the visit immediately to `'PHARMACY'` (if prescription items exist) or `'COMPLETED'` (if no medicines are prescribed). The OPD encounter is prematurely closed before the patient even reaches the lab bench.
   - **Linkage Gap at Runtime:** While the `LabOrder` schema has a foreign key to `Consultation`, the frontend `Consultation.tsx` omits `consultation: consultationId` when calling `POST /api/lab/orders/`. Consequently, lab orders created via the UI have `consultation_id = NULL`.
   - **Asynchronous Result Review:** There is no queue loop-back mechanism to return the patient to the doctor's active queue. The doctor reviews results out-of-band via `/lab` or the patient's longitudinal health record (`/patients/:id`).

---

## 2. Stage-by-Stage Trace (15 Workflow Stages)

| Stage # | Workflow Stage | Frontend Page / Component | Backend API Endpoint | Model(s) Affected | Database State & Changes | Token Involved | Queue Involved | Current Status Transition |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **OPD Token Creation** | `Queue.tsx`<br>`Patients.tsx` | `POST /api/visits/` | `visits.Token` | Row created in `visits_token` with sequential `token_number` for facility and date | **OPD Token Created** (e.g. #1) | `TRIAGE` | `Token.status = 'WAITING'` |
| **2** | **Visit Creation** | `Queue.tsx`<br>`Patients.tsx` | `POST /api/visits/` | `visits.Visit` | Row created in `visits_visit` (`visit_id = VIS-F112-YYYYMMDD-001`) | OPD Token linked via `OneToOneField` | `TRIAGE` | `Visit.status = 'WAITING_FOR_TRIAGE'`, `current_queue = 'TRIAGE'` |
| **3** | **Doctor Consultation Start** | `Consultation.tsx` | `GET /api/visits/?queue=DOCTOR`<br>`POST /api/visits/call-next/` | `visits.Visit` | `assigned_doctor = request.user`, `consultation_start_time = now` | Existing OPD Token | `DOCTOR` | `Visit.status: WAITING_FOR_DOCTOR -> IN_CONSULTATION` |
| **4** | **Doctor Selecting Lab Tests** | `Consultation.tsx` | `GET /api/lab/tests/` | None (Client state) | Test IDs stored in React state `selectedTestIds: number[]` | Existing OPD Token | `DOCTOR` | None (Form interaction in UI) |
| **5** | **Doctor Submitting Consultation** | `Consultation.tsx` | `POST /api/consultations/` | `consultations.Consultation`<br>`visits.Visit`<br>`visits.Token` | Row created in `consultations_consultation`. `Visit.current_queue` set to `'PHARMACY'` or `'COMPLETED'` | Existing OPD Token | **PHARMACY or COMPLETED (Premature!)** | `Visit.status: IN_CONSULTATION -> WAITING_FOR_PHARMACY` or `'COMPLETED'` |
| **6** | **LabOrder Creation** | `Consultation.tsx` (Lines 245–255) | `POST /api/lab/orders/` | `laboratory.LabOrder` | $N$ rows created in `laboratory_laborder` (`consultation_id = NULL`) | **None** (No token created) | `LAB` (implicit) | `LabOrder.status = 'ORDERED'` |
| **7** | **Lab Token Creation** | **NON-EXISTENT** | **NON-EXISTENT** | **None** | No table or model exists for Lab Token. `LabOrder.id` used as identifier | **NO LAB TOKEN CREATED** | N/A | N/A |
| **8** | **Lab Queue Entry** | `Laboratory.tsx` | `GET /api/lab/orders/?facility={id}` | `laboratory.LabOrder` | Fetches orders sorted by `-order_date`. `Visit.current_queue` is NOT queried | None | Lab Orders Queue | Displays status `'ORDERED'` |
| **9** | **Sample Collection** | `Laboratory.tsx` | `POST /api/lab/orders/{id}/collect-sample/` | `laboratory.LabSample`<br>`laboratory.LabOrder` | Row created in `laboratory_labsample` with unique `sample_code` (`SMP-XXXX`). `LabOrder.status = 'SAMPLE_COLLECTED'` | Accession Barcode Tag | Lab Orders Queue | `LabOrder.status: ORDERED -> SAMPLE_COLLECTED` |
| **10** | **Result Entry** | `Laboratory.tsx` | Modal form interaction | None (Client state) | Technician enters `result_value`, `units`, `flags`, `notes` | None | Lab Orders Queue | Form state preparation |
| **11** | **Result Verification** | `Laboratory.tsx` | `POST /api/lab/orders/{id}/save-result/` | `laboratory.LabResult`<br>`laboratory.LabOrder` | Row created in `laboratory_labresult`. `LabOrder.status = 'VERIFIED'`. `verified_by = user`, `verified_at = now` | None | Lab Orders Queue | `LabOrder.status: SAMPLE_COLLECTED -> VERIFIED` |
| **12** | **Returning Patient to Doctor** | **WORKFLOW GAP** | **NON-EXISTENT** | `visits.Visit` | No automated transition exists. Visit remains in `PHARMACY` or `COMPLETED`. Not visible in live Doctor queue | None | **ORPHANED / OUT-OF-BAND** | No queue transition occurs on lab completion |
| **13** | **Doctor Reviewing Results** | `Laboratory.tsx`<br>`PatientDetail.tsx` | `GET /api/lab/orders/`<br>`GET /api/patients/{id}/medical-records/` | None (Read-only query) | Read-only inspection of verified results, reference ranges, and flags | Original OPD Token (referenced in EMR) | N/A | Read-only view (no state change) |
| **14** | **Prescription Creation** | `Consultation.tsx` | `POST /api/consultations/` (nested items) | `consultations.Prescription`<br>`consultations.PrescriptionItem` | Rows created in `consultations_prescription` and `consultations_prescriptionitem` | Original OPD Token | `PHARMACY` | `Prescription.status = 'ACTIVE'`, items `'PENDING'` |
| **15** | **Final OPD Completion** | `Pharmacy.tsx` | `POST /api/pharmacy/dispense/` | `visits.Visit`<br>`visits.Token` | `Visit.status = 'COMPLETED'`, `current_queue = 'COMPLETED'`, `Token.status = 'COMPLETED'` | Original OPD Token | `COMPLETED` | `Visit.status -> COMPLETED` |

---

## 3. Detailed Answers to Critical Audit Questions

### A. Does the current system create a LAB token at the time the doctor orders tests?
**NO.**  
There is no `LabToken` model, database table, or token generator in the laboratory module. The system creates one or more `LabOrder` records with standard database integer primary keys (`id`).

---

### B. If not, exactly where is the current laboratory token/queue number generated?
The laboratory order identifier is simply the primary key integer `LabOrder.id`.  
In the user interface:
- In `frontend/src/pages/Laboratory.tsx` (Line 100): formatted as `#LAB-${String(order.id).padStart(4, '0')}` (e.g., `#LAB-0051`).
- In `backend/apps/patients/views.py` (Line 304): formatted as `'order_id': f"LAB-{lo.id:04d}"`.
- Specimen accession barcodes are generated as `SMP-2026-XXXX` during sample collection.  
There is **no sequential daily queue token** for the laboratory.

---

### C. Does "Complete Consultation & Issue Orders" prematurely close the OPD encounter?
**YES.**  
In `backend/apps/consultations/views.py` (Lines 158–171):
- If the doctor prescribes medication at the same time: `visit.current_queue` is transitioned to `'PHARMACY'` (`status = 'WAITING_FOR_PHARMACY'`).
- If the doctor does not prescribe medication (intending to await lab results): `visit.current_queue` is transitioned immediately to `'COMPLETED'` (`status = 'COMPLETED'`, `completed_time = now`).  
In both scenarios, the OPD encounter is removed from the consultation state before the patient even arrives at the diagnostic laboratory.

---

### D. Can the patient return to the same doctor using the same Visit and OPD Token after laboratory completion?
**NOT through the automated queue workflow; YES via direct URL or EMR lookup.**  
- **Queue Barrier:** The doctor consultation queue (`/consultation` and `/queue?queue=DOCTOR`) filters strictly for `current_queue === 'DOCTOR' && status !== 'COMPLETED'`. Because the visit was set to `PHARMACY` or `COMPLETED`, the patient disappears from the doctor's queue.
- **Idempotency Support:** If the doctor manually navigates to `/consultation?visit={id}`, the page loads the existing visit, and submitting `POST /api/consultations/` performs an idempotent **UPDATE** on the existing `Consultation` record.
- **Risk:** In real clinic operations, reception staff who do not know how to URL-route the patient frequently click `"Issue New OPD Token"`, creating an unintended duplicate Visit and second OPD token.

---

### E. Can the doctor retrieve the verified laboratory results from the same encounter?
**NO inside `Consultation.tsx`; YES on `/patients/:id` and `/lab`.**  
- Inside `Consultation.tsx`, `selectVisit()` fetches `triage/?visit={id}` and `consultations/?visit={id}`, but **does not fetch `lab/orders/`**. The consultation screen has no UI section displaying lab results.
- To inspect results, the doctor must leave the consultation screen and open `PatientDetail.tsx` (`/patients/:id`) under the "Diagnostic Investigations & Laboratory Results" tab or open `Laboratory.tsx` (`/lab`).

---

### F. Does completing the lab accidentally create another Visit or OPD token?
**NO.**  
- `POST /api/lab/orders/{id}/collect-sample/` creates only a `LabSample`.
- `POST /api/lab/orders/{id}/save-result/` creates only a `LabResult`.
Neither endpoint touches `Visit` or `Token`.

---

### G. If multiple tests are selected, how many lab tokens are created?
**0 Lab Tokens; exactly $N$ `LabOrder` records.**  
In `Consultation.tsx` (Lines 245–255), selecting $N$ tests iterates through a loop calling `POST /api/lab/orders/` $N$ times. Each test creates an independent `LabOrder` record (e.g. Test 1 = `LabOrder #51`, Test 2 = `LabOrder #52`).

---

### H. Are LabOrder records linked to the active Consultation?
**NO at runtime (Schema exists, but frontend payload omits the link).**  
- Database schema: `LabOrder.consultation` is a nullable foreign key.
- Runtime implementation: `Consultation.tsx` (Line 247) sends `{ patient, facility, test_master }` without `consultation: consultationId`.
- Database verification: All records created via the frontend UI have `consultation_id = NULL`.

---

### I. Does LabOrder retain:
- **patient:** **YES** (`patient_id` ForeignKey)
- **facility:** **YES** (`facility_id` ForeignKey)
- **visit/encounter:** **NO** (No `visit` column exists on `LabOrder`)
- **consultation:** **NO at runtime** (Schema field exists, but is `NULL` for UI-created orders)
- **lab token:** **NO** (No lab token field exists)
- **test master:** **YES** (`test_master_id` ForeignKey to `LabTestMaster`)

---

### J. What happens to the OPD queue state while the patient is waiting for laboratory results?
The OPD queue state is **completely disengaged from the laboratory process**:
- The visit is either in `current_queue = 'PHARMACY'` (waiting for drug dispensing) or `current_queue = 'COMPLETED'` (closed).
- The `LAB` queue choice (`Visit.current_queue = 'LAB'`) and status choices (`'LAB_PENDING'`, `'LAB_IN_PROGRESS'`, `'LAB_COMPLETED'`) defined in `backend/apps/visits/models.py` are **never utilized** during runtime consultation processing.

---

## 4. State Model Reconciliation Matrix

### 4.1 OPD State Model Comparison
```
Expected Architecture:
WAITING_FOR_DOCTOR ──► IN_CONSULTATION ──► WAITING_FOR_LAB ──► LAB_COMPLETED ──► DOCTOR_REVIEW ──► COMPLETED

Actual Implementation:
WAITING_FOR_DOCTOR ──► IN_CONSULTATION ──► [Branch on Prescription Items]:
                                            ├── Has Rx Items: WAITING_FOR_PHARMACY ──► (Pharmacy Dispense) ──► COMPLETED
                                            └── No Rx Items:  COMPLETED (Premature Termination!)
```

| State Name | Expected in Business Flow | Present in `Visit.STATUS_CHOICES` | Actually Used at Runtime |
| :--- | :---: | :---: | :---: |
| `WAITING_FOR_TRIAGE` | YES | YES | **YES** (On OPD check-in) |
| `IN_TRIAGE` | YES | YES | **YES** (On Nurse call-next) |
| `TRIAGED` | YES | YES | **YES** (On Nurse vitals save) |
| `WAITING_FOR_DOCTOR` | YES | YES | **YES** (After Nurse triage) |
| `IN_CONSULTATION` | YES | YES | **YES** (On Doctor call-next) |
| `WAITING_FOR_LAB` | YES | NO (`LAB_PENDING` exists) | **NO** (Bypassed) |
| `LAB_IN_PROGRESS` | YES | YES | **NO** (Bypassed) |
| `LAB_COMPLETED` | YES | YES | **NO** (Bypassed) |
| `DOCTOR_REVIEW` | YES | NO | **NO** (Does not exist) |
| `WAITING_FOR_PHARMACY`| YES | YES | **YES** (If medicines prescribed) |
| `COMPLETED` | YES | YES | **YES** (Set prematurely if no Rx) |

---

### 4.2 Laboratory State Model Comparison

| Lab State | Expected in Business Flow | Present in `LabOrder.status` | Actually Used at Runtime |
| :--- | :---: | :---: | :---: |
| `ORDERED` | YES | YES | **YES** (On Doctor consult save) |
| `QUEUED` | YES | NO (Implicit in `ORDERED`) | **YES** (Filtered as `ORDERED`) |
| `SAMPLE_COLLECTED` | YES | YES | **YES** (On `collect-sample/`) |
| `PROCESSING` | YES | NO | **NO** (Remains `SAMPLE_COLLECTED`) |
| `RESULT_ENTRY` | YES | YES | **NO** (Skipped directly to `VERIFIED`) |
| `VERIFIED` | YES | YES | **YES** (On `save-result/`) |
| `COMPLETED` | YES | NO (`VERIFIED` is terminal) | **YES** (Represented by `VERIFIED`) |

---

## 5. Token Architecture Analysis

### Architectural Rules Observed:
1. **OPD Token:**
   - Sequential integer restarting at #1 each operational date per facility.
   - Enforced by `UniqueConstraint(fields=['facility', 'date', 'token_number'])`.
   - Bound 1:1 with `Visit` via `OneToOneField`.
2. **Missing Lab Token Architecture:**
   - In a multi-station healthcare facility, patients moving to the lab bench require a laboratory sequence number (e.g. `L-012`) to be called by the technician.
   - Currently, the technician only sees the order list sorted by timestamp, and references the order by its permanent primary key `id` (`#LAB-0051`) or the specimen barcode (`SMP-XXXX`).
   - Adding a true `LabToken` model or sequential daily lab number would fulfill the two-token architecture without impacting the single OPD encounter invariant.

---

## 6. Comprehensive Findings (PASS / WARN / FAIL / UNKNOWN)

| Finding ID | Classification | Component | Code Location | Finding Summary |
| :--- | :---: | :--- | :--- | :--- |
| **FND-W01** | **PASS** | `backend/apps/visits/models.py` | Line 101 | **Single OPD Token Invariant:** Exactly one token exists per visit encounter. |
| **FND-W02** | **PASS** | `backend/apps/laboratory/views.py` | Lines 45–70 | **Zero Token Inflation in Lab:** Lab order creation does not create duplicate OPD tokens or duplicate visits. |
| **FND-W03** | **PASS** | `backend/apps/laboratory/views.py` | Lines 71–145 | **Sample & Result Isolation:** Specimen collection and result verification do not alter visit tokens. |
| **FND-W04** | **PASS** | `frontend/src/pages/Laboratory.tsx` | Lines 90–105 | **Specimen Accession Barcode:** Unique `SMP-XXXX` barcode generated per specimen. |
| **FND-W05** | **PASS** | `backend/apps/consultations/views.py` | Lines 84–97 | **Idempotent Consultation:** Updating an encounter does not duplicate consultations or visits. |
| **FND-W06** | **FAIL** | `backend/apps/consultations/views.py` | Lines 158–171 | **Premature OPD Completion:** Submitting a consultation with lab orders immediately marks the visit `COMPLETED` (if no Rx) or `PHARMACY`. It does not keep the visit open for lab results. |
| **FND-W07** | **FAIL** | `frontend/src/pages/Consultation.tsx` | Lines 245–255 | **Broken Consultation $\to$ LabOrder Linkage:** `POST /api/lab/orders/` omits `consultation` parameter. Runtime records have `consultation_id = NULL`. |
| **FND-W08** | **WARN** | `frontend/src/pages/Consultation.tsx`<br>`backend/apps/visits/views.py` | Lines 75–85<br>Lines 200–250 | **Missing Return-to-Doctor Queue Loop:** When lab results are verified, the visit is not transitioned back to `DOCTOR` queue. Patient is absent from active doctor consultation queue. |
| **FND-W09** | **WARN** | `backend/apps/laboratory/models.py` | Whole file | **Missing Dedicated Lab Token Entity:** No daily sequential token exists for the laboratory station; relies entirely on table primary key `id`. |
| **FND-W10** | **WARN** | `frontend/src/pages/Consultation.tsx` | Lines 111–150 | **No Lab Results Display in Consultation Screen:** Doctor cannot view lab results within `Consultation.tsx`; must navigate to `/patients/:id` or `/lab`. |

---

## 7. Explicit Final Deliverable Answers

```text
OPD TOKEN COUNT:
1 (Exactly One per clinical encounter)

LAB TOKEN COUNT:
0 (No Lab Token model currently implemented; uses LabOrder.id)

LAB TEST COUNT:
N (Arbitrary number of LabOrder records created per order selection)

Does Lab Token create a new Visit?
NO

Does Lab Token create a new OPD Token?
NO

Can patient return to same Doctor using same OPD Token?
NO (Not via normal automated queue; only via manual direct URL / EMR lookup)

Can Doctor review verified lab results in same encounter?
NO (Not within Consultation.tsx; only via separate /patients/:id or /lab screens)

Does current implementation prematurely complete the OPD encounter?
YES (Sets visit to COMPLETED if no Rx, or sends directly to PHARMACY)

Does LabOrder link to Consultation?
NO (Foreign key is NULL at runtime because Consultation.tsx omits the parameter)
```

---

**Audit Status:** Completed. Unmodified codebase. STOPPED.
