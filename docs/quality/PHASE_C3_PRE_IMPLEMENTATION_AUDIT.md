# Namma Clinic — Phase C3 Pre-Implementation Audit Report

**Branch:** `feature/namma-clinic-demo-data-model`  
**Audit Date:** September 21, 2026  
**Auditor:** Senior Healthcare Application Engineer (PM + RSA Review Process)  
**Governance Gate:** Phase C3 Pre-Implementation Scope & Quality Audit  
**Baseline Commit:** `b6bfbcf3965f0a8ada5ef0959093a0ec4ebec152`  
**Current Status:** AUDIT COMPLETE — PENDING PM/RSA IMPLEMENTATION AUTHORIZATION  

---

## 1. Executive Summary

Phase C3 focuses on resolving remaining client-visible workflow disconnects, clinical input ergonomics, and live demo completeness across the Namma Clinic Digital Health & Operations Platform.

Following the successful implementation, validation, and GitHub push of Phase C1 (Security, Route Guards, CSV Export Scoping, Localhost Alignment, Idempotency) and Phase C2 (Data Integrity, Patient Scoping, Queue Synchronization, Prescription Invariance, FEFO Inventory Transaction Lineage), this pre-implementation audit systematically reassessed all remaining findings from the original 18-ticket backlog.

### Key Audit Findings:
1. **Critical Consultation Workflow Blocker (FND-16):** In `Consultation.tsx`, `refUrgency` defaults to `'HIGH' as any`. Because the backend `Referral` model choices are strictly `ROUTINE`, `URGENT`, and `EMERGENCY`, submitting a consultation with an enabled referral causes `POST /api/referrals/` to fail with HTTP 400 (`"HIGH" is not a valid choice.`), which triggers an uncaught rejection and aborts the entire consultation save with an alert ("Failed to save consultation.").
2. **Clinical Ergonomics Defect (FND-13):** `Consultation.tsx` hardcodes clinical history (`'Known history of hypertension...'`) and diagnosis (`'Type 2 Diabetes Mellitus with Essential Hypertension'`) in state initializers without setters, forcing identical diagnoses and hardcoded medicine IDs on every patient encounter during live client demos.
3. **Incomplete Continuity of Care (FND-17):** `FollowUps.tsx` is strictly read-only. While the backend `FollowUpViewSet` supports `PATCH /api/followups/{id}/`, the UI provides no button to complete a follow-up or generate a return visit token.
4. **Simulated Teleconsultation Workspace (FND-06):** `Teleconsultation.tsx` contains hardcoded static JSX for Ramesh Kumar and a dummy `alert()` on "Save Advice". It requires either realistic persistence to the existing `Teleconsultation` model or explicit product-approved demo guidance.
5. **DHO Role Access Omission:** `DISTRICT_OFFICER` has backend read access to Clinic Infrastructure (`/api/facilities-infra/*`), but `/infrastructure` is missing from `ROLE_ALLOWED_PATHS` in `permissions.ts`.
6. **Dormant Transaction Models (FND-15):** 10 models in the database currently have 0 rows. In particular, `Vendor` and `PurchaseOrder` have 0 records, causing the "Purchase Orders" tab in `Pharmacy.tsx` to render empty counters (`(0)`) and tables during procurement demonstrations.

---

## 2. Baseline Architecture & Git Verification

* **Repository:** `georgefernandaz2003/namma_clinic`
* **Current Branch:** `feature/namma-clinic-demo-data-model`
* **Local HEAD Commit:** `b6bfbcf3965f0a8ada5ef0959093a0ec4ebec152`
* **Remote HEAD Commit:** `b6bfbcf3965f0a8ada5ef0959093a0ec4ebec152` (`origin/feature/namma-clinic-demo-data-model`)
* **Tracking Status:** In exact parity with remote (`Your branch is up to date`).
* **Working Tree:** Clean (`nothing to commit, working tree clean`).

---

## 3. C1 & C2 Closed Findings Verification

Before evaluating C3, all items completed during Phases C1 and C2 were independently re-tested to verify no regressions:

| Finding | Description | Phase | Verification Method | Status |
|---|---|:---:|---|:---:|
| **FND-01** | Route guard blocks (`/ars`, `/quality`, `/integrations`) | C1 | Inspected `ROLE_ALLOWED_PATHS` and route guards | **VERIFIED CLOSED** |
| **FND-02** | Doctor & Admin 403 on queue operations (`call-next`, `transition`) | C1 | Executed `call-next` and `transition` with Doctor JWT | **VERIFIED CLOSED** |
| **FND-03** | FollowUp #9 cross-encounter FK mismatch (visit 35 vs 40) | C1 | Query `FollowUp(id=9).visit_id == 40 == Referral(id=16).visit_id` | **VERIFIED CLOSED** |
| **FND-04** | CSV export fall-through & DHO district scoping | C1 | Automated regression tests in `test_csv_export_scoping` | **VERIFIED CLOSED** |
| **FND-05** | Hardcoded localhost URL in `Reports.tsx` | C1 | Grepped frontend: only `api.ts` environment fallback remains | **VERIFIED CLOSED** |
| **FND-07** | OneToOne HTTP 500 crash on triage & consultation re-save | C1 | Verified `update_or_create` keyed by `visit_id` | **VERIFIED CLOSED** |
| **FND-08** | Patient #216 orphaned from district and facility | C2 | Reconciled to Facility 68 / District 11; model clean invariant active | **VERIFIED CLOSED** |
| **FND-09** | Triage bypassed for Visit #39 | C2 | Triage vitals #28 linked; transition guard blocks untriaged visits | **VERIFIED CLOSED** |
| **FND-10** | Visits #40 and #41 remaining in DOCTOR queue after completion | C2 | Auto-sync `status='COMPLETED' <-> queue='COMPLETED'` active | **VERIFIED CLOSED** |
| **FND-11** | Prescription #26 marked DISPENSED with PENDING items | C2 | Prescription items reconciled; validation invariant active | **VERIFIED CLOSED** |
| **FND-12** | Missing InventoryTransaction for Amlodipine (Visit 35 & 41) | C2 | Transactions #7, #8, #9 created; atomic FEFO deduction verified | **VERIFIED CLOSED** |

All 11 completed Phase C1 and C2 tickets remain fully intact, tested, and verified.

---

## 4. Remaining Known Findings Reassessment

### [FND-06] Teleconsultation Screen Hardcoding & Non-Persistent Advice
- **Current Status:** Still Exists.
- **Evidence:** 
  - `frontend/src/pages/Teleconsultation.tsx`: Lines 91-93 hardcode patient details (`Ramesh Kumar (52/M)`, `Chief Complaint: Severe Dizziness & Uncontrolled BP`, `Vitals: BP 148/96 mmHg`).
  - Line 102 hardcodes advice note text in `defaultValue`.
  - Line 107 executes `onClick={() => alert('Teleconsultation advice notes saved to patient visit EMR!')}` with zero backend API call.
  - `backend/apps/telemedicine/models.py` has a complete `Teleconsultation` model with 0 records.
- **Client Impact:** A government official asking how specialist tele-advice flows into the primary care record will observe an offline mock popup with no real database record.
- **Classification:** **SHOULD FIX IN C3 / NEEDS PRODUCT DECISION**
- **Recommended Action:** Connect `Teleconsultation.tsx` to `POST /api/telemedicine/` and save consultation notes into the active patient timeline, or retain as clearly badged prototype simulation.

---

### [FND-13] Hardcoded Clinical Defaults in `Consultation.tsx`
- **Current Status:** Still Exists.
- **Evidence:**
  - `frontend/src/pages/Consultation.tsx:20-24`:
    - `const [history] = useState('Known history of hypertension, poor compliance.');` (No setter declared)
    - `const [diagCode] = useState('E11.9 / I10');` (No setter declared)
    - `const [diagName, setDiagName] = useState('Type 2 Diabetes Mellitus with Essential Hypertension');`
    - `const [notes] = useState('Advised low salt diet, lifestyle modifications, and regular monitoring.');` (No setter declared)
    - `prescriptions` array hardcodes Metformin 500mg (ID 26) and Amlodipine 5mg (ID 27).
- **Client Impact:** In every patient consultation demonstrated, the patient automatically displays hypertensive/diabetic history and diagnosis, and identical prescriptions. The clinician cannot edit history or notes because no input handlers or setters exist.
- **Classification:** **MUST FIX IN C3**
- **Recommended Action:** Replace static initializers with editable input state initialized dynamically from `selectedVisit.chief_complaint` and dynamic diagnosis selection.

---

### [FND-14] Random 4-Digit Patient ID Generator & Collision Loop
- **Current Status:** Still Exists in Code, but Non-Blocking.
- **Evidence:**
  - `backend/apps/patients/views.py:80-84`:
    ```python
    while True:
        candidate_id = f"NC-KA-2026-{random.randint(1000, 9999)}"
        if not Patient.objects.filter(patient_id=candidate_id).exists():
            data['patient_id'] = candidate_id
            break
    ```
- **Client Impact:** None during current demonstrations. With ~216 seeded patients out of 9,000 possibilities, collisions are statistically negligible and resolve in <2 iterations.
- **Classification:** **DEFER**
- **Recommended Action:** Defer sequential ID generator redesign to production scaling phase.

---

### [FND-15] Dormant Transaction Models with Zero Database Records
- **Current Status:** Still Exists.
- **Evidence:** Exactly 10 models have 0 rows:
  - Framework: `admin.LogEntry`, `auth.Group`, `sessions.Session`
  - Patients: `patients.Household`, `patients.PatientDocument`
  - Pharmacy: `pharmacy.Vendor`, `pharmacy.PurchaseOrder`, `pharmacy.PurchaseOrderItem`
  - Telemedicine: `telemedicine.Teleconsultation`
  - Reporting: `reports.ReportExportLog`
- **Client Impact:** 
  - In `Pharmacy.tsx`, the "Purchase Orders" tab displays `(0)` and empty procurement tables.
  - In `PatientDetail.tsx`, the "Documents" tab displays empty states.
- **Classification:** **SHOULD FIX IN C3** (Targeted seed data for `Vendor`, `PurchaseOrder`, and `PatientDocument`).
- **Recommended Action:** Seed 2 vendors, 2 purchase orders, and 2 patient clinical documents in `seed_demo.py` so procurement and document workflows can be demonstrated live.

---

### [FND-16] Referral Urgency Enum Discrepancy ('HIGH' vs 'URGENT')
- **Current Status:** Still Exists — **CRITICAL RUNTIME ERROR**.
- **Evidence:**
  - `frontend/src/pages/Consultation.tsx:37`: `const [refUrgency, setRefUrgency] = useState<'ROUTINE' | 'URGENT' | 'EMERGENCY'>('HIGH' as any);`
  - `backend/apps/referrals/models.py:15-19`: Valid choices are `('ROUTINE', 'Routine Referral')`, `('URGENT', 'Urgent Evaluation')`, `('EMERGENCY', 'Emergency Referral')`.
  - When saving consultation with default referral, `urgency: 'HIGH'` is sent to `POST /api/referrals/`. DRF rejects with HTTP 400 (`"HIGH" is not a valid choice.`), which triggers `catch (e) { alert('Failed to save consultation.'); }`.
- **Client Impact:** Any doctor saving a consultation that includes a referral crashes with a generic failure alert unless they manually toggle the dropdown.
- **Classification:** **MUST FIX IN C3**
- **Recommended Action:** Change initial state in `Consultation.tsx:37` to `'URGENT'`.

---

### [FND-17] Read-Only Follow-Up Care Module
- **Current Status:** Still Exists.
- **Evidence:**
  - `frontend/src/pages/FollowUps.tsx`: Only contains `loadData()` and a read-only table.
  - `backend/apps/referrals/views.py`: `FollowUpViewSet` already inherits `ModelViewSet` and accepts `PATCH /api/followups/{id}/` with `{'status': 'COMPLETED'}`.
- **Client Impact:** When reviewing scheduled return visits or post-referral care, presenters cannot demonstrate closing the loop or marking a follow-up visit as completed.
- **Classification:** **SHOULD FIX IN C3**
- **Recommended Action:** Add a "Mark Completed" button in `FollowUps.tsx` calling `api.patch('followups/{id}/', { status: 'COMPLETED' })`.

---

### [Additional Technical Items Reassessment]

| Item | Evidence | Client Impact | Classification |
|---|---|---|:---:|
| **Missing LabOrder → Visit FK** | `LabOrder` references `consultation`, `patient`, `facility`. Consultation has `OneToOneField(Visit)`. | Zero visible defect. Adding FK requires database migration. | **DEFER** |
| **Missing Triage → Alert Event Bus** | `TriageVitals` computes clinical flags inline. `Alert` model is designed for facility operational alerts. | Zero visible defect; flags display in Doctor Console. | **DEFER** |
| **DHO Access to `/infrastructure`** | Backend `facilities-infra/*` permits DHO read access, but `/infrastructure` omitted from `ROLE_ALLOWED_PATHS`. | DHO cannot review oxygen cylinders, maintenance tickets, or bed capacity. | **SHOULD FIX IN C3** |
| **Registration Vulnerability Dropdown** | `Patients.tsx` hardcodes `'Slum Resident BPL'`. | Presenters cannot select other vulnerable groups (Construction Worker, Migrant Laborer). | **SHOULD FIX IN C3** |

---

## 5. Client-Facing Screen Audit

Comprehensive review of all 25 active screens against live backend APIs and database state:

| Screen | Route | Role Authority | Data Backing | Actions Status | Verdict | Evidence / Notes |
|---|---|---|---|---|:---:|---|
| **Login** | `/login` | All Roles | `apps.accounts.models.User` | JWT Auth functional | **PASS** | Role quick-switch badges work reliably. |
| **Dashboard** | `/` | All Roles | `DashboardSummaryView` | Date navigation functional | **PASS** | Dynamic KPIs per role and facility. |
| **Healthcare Network** | `/network` | DHO | `FacilityHierarchyView` | Tree & Graph modes work | **PASS** | Renders 11 facilities and relationships. |
| **Facilities Registry** | `/facilities` | DHO, Admin | `FacilityViewSet` | Search and filter work | **PASS** | Real-time facility search functional. |
| **Patient Registration** | `/patients` | Admin, Doctor, Nurse | `PatientViewSet.create` | Modal save functional | **WARN** | Vulnerability field hardcoded to 'Slum Resident BPL'. |
| **Patient Directory** | `/patients` | DHO, Admin, Doctor, Nurse | `PatientViewSet.list` | Search, pagination, filter | **PASS** | District and facility scoping enforced. |
| **Patient Details** | `/patients/:id` | DHO, Admin, Doctor, Nurse | `PatientTimelineView`, `records` | Timeline, Records, Upload | **PASS** | 13 timeline events render cleanly for Ramesh Kumar. |
| **OPD Queue** | `/queue` | All Roles | `VisitViewSet` | Call Next, Status Transitions | **PASS** | Calling and status transitions verified in C1/C2. |
| **Nurse Triage** | `/triage` | Nurse | `TriageVitalsViewSet` | Vitals entry & calculations | **PASS** | Idempotent re-entry verified in C1. |
| **Doctor Consultation** | `/consultation` | Doctor | `ConsultationViewSet`, `PrescriptionViewSet` | Save Consultation | **FAIL** | Blocked on referral save due to `refUrgency='HIGH'`. Hardcoded notes. |
| **Prescription Modal** | `/pharmacy` | Doctor, Pharmacist | `PrescriptionViewSet` | View & Dispense | **PASS** | Linked to consultation and patient record. |
| **Pharmacy & FEFO** | `/pharmacy` | DHO, Admin, Pharmacist | `MedicineMaster`, `MedicineBatch` | FEFO Dispense, Batch Adjust | **WARN** | Purchase Orders tab shows `(0)` due to dormant table. |
| **Inventory Ledger** | `/pharmacy` | DHO, Admin, Pharmacist | `InventoryTransactionViewSet` | Filter by Batch, Type | **PASS** | All dispensed items generate audit transactions. |
| **Diagnostics Lab** | `/lab` | Doctor, Lab Tech | `LabOrderViewSet`, `LabSample`, `LabResult` | Barcode, Result Entry, Verify | **PASS** | Verification releases results cleanly. |
| **Referral Network** | `/referrals` | DHO, Admin, Doctor | `ReferralViewSet`, `ReferralResponse` | Dispatch, Complete Response | **PASS** | Cross-facility referral routing verified. |
| **Follow-up Care** | `/followups` | Admin, Doctor, Nurse | `FollowUpViewSet` | Read-only listing | **WARN** | Cannot mark follow-up completed from UI. |
| **NCD Management** | `/ncd` | DHO, Nurse | `NCDRecordViewSet` | Screening, Cohort Registry | **PASS** | Blood pressure and glucose tracking functional. |
| **Disease Surveillance** | `/surveillance` | DHO | `DiseaseCaseViewSet` | Epidemic monitoring | **PASS** | Real-time surveillance listing functional. |
| **Teleconsultation** | `/teleconsultation` | Doctor | None (Static JSX) | Simulated video & dummy alert | **WARN** | Fully mocked UI; does not persist advice. |
| **Outreach & Camps** | `/outreach` | Nurse | `OutreachActivityViewSet` | Camp scheduling | **PASS** | Ward camp schedule renders from database. |
| **Wellness Sessions** | `/wellness` | Nurse | `WellnessSessionViewSet` | Yoga / Health education | **PASS** | Session attendance records functional. |
| **ARS Committee** | `/ars` | DHO, Admin | `ARSMeetingViewSet` | Meeting proceedings register | **PASS** | Signed minutes and grant expenditure render. |
| **Quality & Waste** | `/quality` | DHO, Admin | `QualityChecklist`, `BiomedicalWasteLog` | Cleanliness & Waste handover | **PASS** | Kayakalpa audit checklists and waste logs render. |
| **Clinic Infrastructure** | `/infrastructure` | Admin, Pharmacist | `FacilityOxygenSupply`, `Consumable`, `Tickets` | Infrastructure management | **WARN** | DHO blocked by route guard despite backend access. |
| **Reports & CSV** | `/reports` | DHO, Admin | `CSVExportView` | OPD, Pharmacy, Ref, NCD, Surv | **PASS** | Strict DHO isolation confirmed by regression suite. |
| **Alert Engine** | `/alerts` | All Roles | `AlertViewSet` | Operational alerts list | **PASS** | Stock, referral, and lab alerts functional. |
| **Integrations** | `/integrations` | DHO, Admin | `IntegrationConfigurationViewSet` | Simulated Sync triggers | **PASS** | Explicitly badged as mock offline connectors. |
| **Namma Compliance** | `/compliance` | DHO | `ComplianceItemViewSet` | Statutory checklist | **PASS** | Biomedical waste, drug license status active. |
| **Audit Trail** | `/audit` | DHO | `AuditLogViewSet` | Immutable event log | **PASS** | User action audit log functional. |

---

## 6. Core Patient Journey Audit

The end-to-end patient journey was re-validated across all 10 clinical milestones:

```
[1. Registration] ──> [2. Token Generation] ──> [3. OPD Queue] ──> [4. Nurse Triage]
                                                                          │
                                                                          ▼
[8. Inventory FEFO] <── [7. Pharmacy Dispense] <── [6. Prescription] <── [5. Doctor Consultation]
                                                                          │
                                                                   ┌──────┴──────┐
                                                                   ▼             ▼
                                                            [Lab Orders]  [Referral & Follow-up]
```

### Milestone Re-Validation Status:
1. **Registration:** Generates valid UHID `NC-KA-2026-XXXX`. Enforces facility and district scoping. (*Ergonomics Note: Vulnerability dropdown lacks choices*).
2. **Token Generation:** Generates atomic daily sequence token (`Token #1`, `Token #2`) scoped to facility and date.
3. **OPD Queue:** Doctor and Nurse can transition patients across stages. Verified that doctor cannot call triage queue, and nurse cannot call doctor queue.
4. **Nurse Triage:** Computes BMI, pulse, blood pressure, blood glucose, temperature. Idempotent re-entry saves cleanly.
5. **Doctor Consultation:** **BLOCKED ON REFERRALS** when `refUrgency='HIGH'`. Works if referral is disabled or manually changed to `'ROUTINE'`. Consultation text fields default to static hypertension notes.
6. **Diagnostics Lab:** Doctor orders lab tests; Lab technician collects samples with barcodes, enters results, and verifies. Clean end-to-end integration.
7. **Prescription:** OneToOne linkage with consultation. Status invariance strictly enforced (`DISPENSED` prescriptions cannot hold `PENDING` items).
8. **FEFO Pharmacy Dispense:** Atomically allocates medicine from nearest expiry batch and logs `InventoryTransaction` with exact reference ID.
9. **Referral Routing:** Correctly links source clinic, destination hospital hub, and patient.
10. **Continuity Follow-Up:** Correctly scheduled from referral response or consultation. (*Workflow Gap: UI cannot mark follow-up completed*).

---

## 7. Role / RBAC Audit

All 6 active roles were audited for navigation visibility, route permissions, and API data scoping:

| Role | Username | Assigned Scope | Allowed Routes | API Mutation Authority | District Isolation |
|---|---|---|:---:|---|:---:|
| **DISTRICT_OFFICER** | `district` | District 11 (BBMP Central) | 16 routes | Read-Only across all clinical/operational endpoints | **STRICT PASS** (Scoping active across all models) |
| **HOSPITAL_ADMIN** | `hospital` | Facility 66 (CV Raman Hospital) | 13 routes | Administrative management & queue transitions | **PASS** |
| **DOCTOR** | `doctor` | Facility 68 (Varthur Rural Clinic) | 9 routes | Clinical consultations, prescriptions, lab orders, referrals | **PASS** |
| **NURSE** | `nurse` | Facility 68 (Varthur Rural Clinic) | 9 routes | Patient registration, vitals triage, outreach, wellness | **PASS** |
| **LAB_TECHNICIAN** | `lab` | Facility 68 (Varthur Rural Clinic) | 4 routes | Sample collection, result entry, verification | **PASS** |
| **PHARMACIST** | `pharmacy` | Facility 68 (Varthur Rural Clinic) | 5 routes | FEFO dispensing, stock adjustments, purchase orders | **PASS** |

*Note on DHO Authority:* The District Officer has strict read-only access. Mutation endpoints (`POST /api/visits/call-next/`, `POST /api/consultations/`, etc.) reject DHO requests with HTTP 403 Forbidden. Scoping helpers correctly restrict all DHO queries to facilities within District 11.

---

## 8. Dashboard & KPI Data Lineage Audit

Every visible KPI card across the main executive dashboards was traced from UI to API to database query:

| Dashboard KPI | Display Component | Backend API Endpoint | Database Source Query | Verdict |
|---|---|---|---|:---:|
| **Today's OPD Count** | All Dashboards | `/api/dashboard/summary/?date=...` | `Visit.objects.filter(facility_id__in=..., opd_date=...).count()` | **AUTHORITATIVE** |
| **Queue Stage Breakdown** | Doctor, Nurse, Queue | `/api/dashboard/summary/?date=...` | `Visit.objects.filter(current_queue=..., status=...).count()` | **AUTHORITATIVE** |
| **Active Stock Items** | Pharmacist, Admin | `/api/dashboard/summary/?date=...` | `MedicineBatch.objects.filter(quantity__gt=0).values('medicine').distinct().count()` | **AUTHORITATIVE** |
| **Near Expiry / Expired** | Pharmacist, DHO | `/api/dashboard/summary/?date=...` | `MedicineBatch.objects.filter(expiry_date__lte=today+60d).count()` | **AUTHORITATIVE** |
| **NCD Screening Total** | DHO, Nurse | `/api/dashboard/summary/?date=...` | `NCDRecord.objects.filter(facility_id__in=...).count()` | **AUTHORITATIVE** |
| **Active Epidemic Alerts** | DHO, Surveillance | `/api/dashboard/summary/?date=...` | `DiseaseCase.objects.filter(report_date__gte=today-7d).count()` | **AUTHORITATIVE** |
| **Untied Funds Spent** | ARS | `/api/ars/meetings/?facility=...` | `ARSMeeting.objects.aggregate(Sum('untied_funds_spent_rs'))` | **AUTHORITATIVE** |
| **Kayakalpa Score** | Quality | `/api/quality/checklists/?facility=...` | `QualityChecklist.cleanliness_score` | **AUTHORITATIVE** |

Zero hardcoded numbers or paginated totals exist in executive dashboards. All values represent direct database aggregations scoped to authorized facilities.

---

## 9. API / HTTP Error Audit

1. **HTTP 400 Bad Request in `Consultation.tsx` (FND-16):** Triggered when creating a referral with default urgency `'HIGH'`. Discovered during audit.
2. **HTTP 403 Forbidden on `/infrastructure` for DHO:** Triggered when District Officer navigates to `/infrastructure`.
3. **No HTTP 500 Errors Detected:** Both triage and consultation re-save crashes were resolved by `update_or_create` in Phase C1.
4. **No Unexpected HTTP 404 Errors:** All active router endpoints in `config/api_urls.py` resolve correctly when authenticated with assigned roles.

---

## 10. C3 Finding Classification

| Finding ID | Title | Module | Severity | Classification | Rationale |
|---|---|---|:---:|:---:|---|
| **FND-16** | Referral Urgency Mismatch (`HIGH` vs `URGENT`) | Consultation / Referrals | **HIGH** | **A. MUST FIX IN C3** | Directly aborts consultation save with HTTP 400 in core patient journey. |
| **FND-13** | Hardcoded Clinical Defaults in Consultation Form | Doctor Console | **MEDIUM** | **A. MUST FIX IN C3** | Clinicians cannot edit history/notes; all demo patients receive identical diabetic diagnosis. |
| **FND-17** | Read-Only Follow-Up Care Module | Referrals / Follow-up | **MEDIUM** | **B. SHOULD FIX IN C3** | Presenter cannot demonstrate closing the loop on returning patients; backend API already exists. |
| **FND-15** | Dormant Seed Data (`Vendor`, `PO`, `Documents`) | Pharmacy / Patients | **LOW** | **B. SHOULD FIX IN C3** | Purchase Orders tab shows empty `(0)` counters during live pharmacy demonstrations. |
| **FND-19** | DHO Access to `/infrastructure` Route | RBAC / Facilities Infra | **LOW** | **B. SHOULD FIX IN C3** | Backend supports DHO read access to infra, but frontend route guard omits path. |
| **FND-20** | Patient Registration Vulnerability Dropdown | Patient Registration | **LOW** | **B. SHOULD FIX IN C3** | Allows selecting standard vulnerable categories beyond hardcoded 'Slum Resident BPL'. |
| **FND-06** | Simulated Teleconsultation Workspace | Telemedicine | **MEDIUM** | **E. NEEDS DECISION** | Fully mocked UI. Either persist to existing model or provide product demo banner. |
| **FND-14** | Random 4-Digit Patient ID Generator | Patient Registration | **LOW** | **C. DEFER** | Zero failure risk during demo; sequential ID redesign is a technical scalability item. |
| **FND-21** | Missing Direct `LabOrder` → `Visit` FK | Laboratory | **LOW** | **C. DEFER** | Order already links to consultation; adding FK requires schema migration. |
| **FND-22** | Missing Triage → Alert Event Bus | Triage / Alerts | **LOW** | **C. DEFER** | Architectural enhancement; vitals flags display directly in consultation UI. |
| **FND-18** | Dormant Files (`apps.maternal`, `apps.child`) | Code Hygiene | **INFO** | **C. DEFER** | Zero runtime footprint; retain until final repository cleanup. |

---

## 11. Proposed C3 Implementation Scope

To maintain strict adherence to PM/RSA guidelines (minimal code footprint, no speculative redesign, no migrations, no new modules), the proposed C3 scope comprises:

1. **Fix Referral Urgency Crash (FND-16):**
   - In `frontend/src/pages/Consultation.tsx:37`, set initial state to `'URGENT'`.
2. **Make Consultation Form Dynamic (FND-13):**
   - Provide state setters and initialize consultation form dynamically from `selectedVisit.chief_complaint` and dynamic diagnosis masters.
3. **Add "Mark Completed" Action to Follow-Ups (FND-17):**
   - In `frontend/src/pages/FollowUps.tsx`, add an action button calling `api.patch('followups/{id}/', { status: 'COMPLETED' })`.
4. **Authorize DHO for `/infrastructure` (FND-19):**
   - In `frontend/src/utils/permissions.ts`, add `'/infrastructure'` to `DISTRICT_OFFICER`'s allowed paths.
5. **Add Vulnerability Categories in Patient Registration (FND-20):**
   - In `frontend/src/pages/Patients.tsx`, convert the hardcoded text into a dropdown with government-standard vulnerability options (Slum Resident BPL, Construction Worker, Street Vendor, Migrant Laborer, Destitute/Elderly).
6. **Seed Realistic Demonstration Records for Dormant Tables (FND-15):**
   - In `backend/apps/management/commands/seed_demo.py`, seed 2 vendors, 2 purchase orders, and 2 patient clinical documents so that Pharmacy Procurement and Patient Documents tabs show live demonstration data.

---

## 12. Explicitly Deferred Items

The following items are explicitly **DEFERRED** beyond Phase C3:

1. **FND-14 (UHID Sequential Auto-Increment):** The current random ID generator functions without collisions in demo namespaces. Defer until production scaling.
2. **FND-21 (Direct LabOrder → Visit FK):** LabOrder is already associated with the patient and consultation. Adding a direct FK requires a database migration, which is out of scope for C3.
3. **FND-22 (Triage-to-Alert Event Bus):** Triage flags are already visible in clinical workflows. Event-driven alerts require architectural changes not needed for demo readiness.
4. **FND-18 (Dormant maternal/child code pruning):** Completely isolated files with zero runtime execution. Retain as documented dead code until final repository cleanup.

---

## 13. Items No Longer Defects

1. **FND-08 (Patient 216 Orphaned):** Fully resolved in Phase C2; patient is correctly assigned to Facility 68 / District 11.
2. **FND-09 (Triage Bypassed for Visit 39):** Fully resolved in Phase C2; authentic triage vitals linked and queue advance guard active.
3. **FND-10 (Queue State Desynchronization):** Fully resolved in Phase C2; visits #40 and #41 synchronized to `current_queue='COMPLETED'`.
4. **FND-11 (Prescription Status Invariance):** Fully resolved in Phase C2; prescription items aligned to `DISPENSED`.
5. **FND-12 (Missing Inventory Transactions):** Fully resolved in Phase C2; FEFO transactions logged for all dispensed items.

---

## 14. Items Requiring Product Decision

### FND-06: Teleconsultation Scope Decision
- **Option 1 (Functional MVP):** Connect `Teleconsultation.tsx` to `POST /api/telemedicine/`, save specialist advice into the active patient consultation timeline, and display completed teleconsultations in `PatientDetail.tsx`.
- **Option 2 (Simulated Prototype Banner):** Keep the current local simulation UI, but enhance the header banner to clearly indicate: *"Simulated Telemedicine Workspace — Doctor-to-Specialist virtual consultation demonstration mode"*, ensuring presenters set accurate client expectations.

---

## 15. Regression Test Results

Executed prior to audit report generation on clean baseline `b6bfbcf`:

* **Complete Backend Test Suite:**
  - **Command:** `venv\Scripts\python.exe manage.py test`
  - **Total Tests:** `38`
  - **Passed:** `38`
  - **Failed:** `0`
  - **Errors:** `0`
  - **Duration:** `68.511s`
* **Migrations Check:**
  - **Command:** `venv\Scripts\python.exe manage.py makemigrations --check --dry-run`
  - **Result:** `No changes detected` (Exit code `0`)
* **Frontend Build:**
  - **Command:** `npm run build`
  - **Result:** Succeeded in `723ms` (Exit code `0`)
* **Frontend Lint:**
  - **Command:** `npm run lint`
  - **Result:** `0 errors, 134 warnings` (Exit code `0`)

---

## 16. Git Integrity Verification

* **Command:** `git status --short`
* **Untracked / Modified Files:** Only `docs/quality/PHASE_C3_PRE_IMPLEMENTATION_AUDIT.md` (the audit report artifact).
* **Application Source Code Modified:** **NONE** (0 lines of code modified).
* **Database / Migrations Modified:** **NONE**.
* **Commits Created:** **NONE**.
* **Remote Push Performed:** **NONE**.

---

## 17. Final PM / RSA Recommendation

1. **Approve Proposed C3 Scope:** Authorize implementation of tickets FND-16, FND-13, FND-17, FND-19, FND-20, and targeted seed data for FND-15.
2. **Clarify Teleconsultation Scope (FND-06):** Select Option 1 (Functional MVP with `POST /api/telemedicine/`) or Option 2 (Enhanced Demo Prototype Banner).
3. **Execute Under Governed Phase C3:** Once authorized, perform implementation, execute regression tests, and present C3 implementation report before any GitHub commit or push.
