# Namma Clinic — Phase C Remediation Backlog
**Branch:** `feature/namma-clinic-demo-data-model`  
**Audit Date:** September 21, 2026  
**Auditor:** Implementation Engineer (PM + RSA Review Process)  
**Status Gate:** Phase C Quality Audit  

---

## 1. Backlog Summary & Defect Metrics

| Severity | Count | Primary Impact Areas |
|---|:---:|---|
| **CRITICAL** | 4 | Role Guard Blocks, 403 Errors on Core Queues, Silent Data Corruption |
| **HIGH** | 4 | Disconnected Workflows, Hardcoded URLs, Unhandled DB Exceptions, Orphaned Master Records |
| **MEDIUM** | 6 | State Desynchronization, Incomplete Seed Ledgers, Hardcoded UI Presets, Token Collision |
| **LOW** | 3 | Read-only UI Endpoints, Enum Inconsistencies, Dormant Tables with 0 Seed Rows |
| **INFO** | 1 | Dormant Code Files in Backend Repository (`apps.maternal`, `apps.child`) |
| **TOTAL** | **18** | Complete Remediation Target |

---

## 2. Structured Remediation Backlog Tickets

### [FND-01] CRITICAL: Unreachable Routes Guard Block (`/ars`, `/quality`, `/integrations`)
- **Status:** `IMPLEMENTED` (Phase C.1)
- **Severity:** `CRITICAL`
- **Module:** Security / RBAC / Frontend Routing
- **Problem:** Routes `/ars`, `/quality`, and `/integrations` are registered in `App.tsx` and listed in `DashboardLayout.tsx`'s navigation items, but are **omitted from `ROLE_ALLOWED_PATHS` for all 6 roles** in `frontend/src/utils/permissions.ts`.
- **Evidence:** 
  - `frontend/src/utils/permissions.ts:53-72` contains zero entries for `/ars`, `/quality`, or `/integrations`.
  - Direct URL access to `http://localhost:5173/ars` renders the `ShieldAlert` HTTP 403 Forbidden Access Denied component.
- **Client Impact:** A client or presenter attempting to inspect Quality checklists, ARS committee minutes, or Integration connectors is greeted by an Access Denied error.
- **Technical Impact:** Dead code paths; navigational links in sidebar are either filtered out or lead to route guard rejections.
- **Recommended Fix:** 
  1. Authorize `/quality` and `/ars` for `DISTRICT_OFFICER` and `HOSPITAL_ADMIN` in `ROLE_ALLOWED_PATHS`.
  2. Authorize `/integrations` for `DISTRICT_OFFICER`.
- **Dependencies:** None.
- **Risk:** Low risk; isolated to client permission map.

---

### [FND-02] CRITICAL: Doctor & Hospital Admin Blocked from Queue Operations (Call-Next & Transition)
- **Status:** `IMPLEMENTED` (Phase C.1)
- **Severity:** `CRITICAL`
- **Module:** OPD Queue / RBAC / Clinical Flow
- **Problem:** `VisitViewSet` requires permission `'queue.update'` for all state transition actions (`POST /api/visits/call-next/` and `POST /api/visits/{id}/transition-status/`). In `backend/apps/accounts/permissions.py`, `'queue.update'` is granted strictly to `NURSE`. `DOCTOR` and `HOSPITAL_ADMIN` only possess `'queue.view'`.
- **Evidence:**
  - `backend/apps/accounts/permissions.py:19-25`: `DOCTOR` permissions have `'queue.view'` but lack `'queue.update'`.
  - Calling `POST /api/visits/call-next/` with a Doctor JWT produces HTTP 403: `"You do not have permission to perform this action."`
- **Client Impact:** In a live demonstration of doctor consultation, clicking "Call Next Patient" in the queue immediately aborts with a permission denied alert.
- **Technical Impact:** Breaks doctor workflow in `Queue.tsx` and `Consultation.tsx`.
- **Recommended Fix:** Add `'queue.update'` to `DOCTOR` and `HOSPITAL_ADMIN` in both `backend/apps/accounts/permissions.py` and `frontend/src/utils/permissions.ts`.
- **Dependencies:** None.
- **Risk:** Low risk; aligns permissions with intended clinical role authority.

---

### [FND-03] CRITICAL: Cross-Encounter Foreign Key Contradiction in Seed Data
- **Status:** `IMPLEMENTED` (Phase C.1)
- **Severity:** `CRITICAL`
- **Module:** Data Integrity / Referrals / Follow-Up
- **Problem:** FollowUp #9 links to `referral_id = 16` and `visit_id = 35`. However, Referral #16 has `visit_id = 40`.
- **Evidence:**
  - DB Query on `apps.referrals.models.FollowUp`: `FollowUp(id=9, referral_id=16, visit_id=35)`.
  - DB Query on `apps.referrals.models.Referral`: `Referral(id=16, visit_id=40)`.
- **Client Impact:** When reviewing the patient's longitudinal record, FollowUp #9 displays under Visit #35, but refers to specialist advice from Visit #40, breaking clinical credibility during client scrutiny.
- **Technical Impact:** Corrupted foreign key lineage; join queries between `FollowUp` and `Referral` on `visit_id` fail or produce contradictory timelines.
- **Recommended Fix:** Update `FollowUp` #9's `visit_id` to `40` in `backend/apps/management/commands/seed_demo.py`.
- **Dependencies:** None.
- **Risk:** Low risk; pure seed data alignment.

---

### [FND-04] CRITICAL: Silent Data Fall-Through in CSV Export Engine
- **Status:** `IMPLEMENTED` (Phase C.1)
- **Severity:** `CRITICAL`
- **Module:** Public Health Reports / API
- **Problem:** In `backend/apps/reports/views.py`, `CSVExportView.get()` handles `report_type` values `'opd'`, `'pharmacy'`, and `'referrals'`. For any other report type, it falls into `else:` and exports the `Patient` master directory.
- **Evidence:**
  - `backend/apps/reports/views.py:309-322`: Requests for `type=ncd` or `type=surveillance` fall into `else:` and output Patient ID, Name, Age, Gender, Mobile, District.
  - `frontend/src/pages/Reports.tsx:7,10` offers buttons for "NCD Screening & Control Report" and "Disease Surveillance & Outbreak Report".
- **Client Impact:** Client downloads an NCD or Disease Surveillance report and receives a list of patient demographic names instead of disease cases or risk scores.
- **Technical Impact:** Silent bug; incorrect model queried without throwing an HTTP error.
- **Recommended Fix:** Implement explicit handlers in `CSVExportView` for `ncd` (exporting `NCDRecord`) and `surveillance` (exporting `DiseaseCase`).
- **Dependencies:** None.
- **Risk:** Low risk; isolated to reporting view.

---

### [FND-05] HIGH: Hardcoded Localhost API URL in `Reports.tsx`
- **Status:** `IMPLEMENTED` (Phase C.1)
- **Severity:** `HIGH`
- **Module:** Frontend / Networking / Environment Configuration
- **Problem:** `Reports.tsx` line 21 hardcodes `http://localhost:8000/api/reports/export/` using the browser `fetch()` API rather than the pre-configured Axios `api` service.
- **Evidence:**
  - `frontend/src/pages/Reports.tsx:21`: `const url = 'http://localhost:8000/api/reports/export/?type=${type}${facParam}';`
- **Client Impact:** Demonstrating the application across a local area network, Wi-Fi hotspot, staging server, or Docker container causes report exports to fail with a network connection error.
- **Technical Impact:** Bypasses Axios base URL environment variable (`VITE_API_BASE_URL`), authentication interceptor headers, and proxy configs.
- **Recommended Fix:** Refactor `handleExportCSV` in `Reports.tsx` to use `api.get('reports/export/...', { responseType: 'blob' })`.
- **Dependencies:** None.
- **Risk:** Low risk.

---

### [FND-06] HIGH: Completely Mocked / Disconnected Teleconsultation Workspace
- **Severity:** `HIGH`
- **Module:** Teleconsultation / EMR Integration
- **Problem:** `Teleconsultation.tsx` is an entirely cosmetic simulation. Patient demographic data ("Ramesh Kumar 52/M"), chief complaints, and vitals are hardcoded in the JSX. Clicking "Save Advice to Patient Record" executes `alert()` without calling any backend API.
- **Evidence:**
  - `frontend/src/pages/Teleconsultation.tsx:107`: `onClick={() => alert('Teleconsultation advice notes saved to patient visit EMR!')}`.
  - `backend/apps/telemedicine/models.py` has a `Teleconsultation` model with 0 records in SQLite.
- **Client Impact:** A government official asking to see how remote specialist advice attaches to the patient's record will discover that the button is a dummy prompt.
- **Technical Impact:** Dead backend application; UI is disconnected from the database.
- **Recommended Fix:** 
  - Option A: Connect `Teleconsultation.tsx` to `POST /api/telemedicine/` and save consultation notes into the active patient timeline.
  - Option B: Add a clear "SIMULATED TELE-MEDICINE WORKSPACE (DEMO PROTOTYPE)" header banner explaining the offline simulation state.
- **Dependencies:** Decision from PM/RSA.
- **Risk:** Medium risk.

---

### [FND-07] HIGH: OneToOne Database Crash on Triage & Consultation Re-Submission
- **Status:** `IMPLEMENTED` (Phase C.1)
- **Severity:** `HIGH`
- **Module:** Clinical Documentation / Error Handling
- **Problem:** Both `TriageVitals.visit` and `Consultation.visit` are declared with `OneToOneField(Visit)`. In `TriageVitalsViewSet.create` and `ConsultationViewSet.create`, requests invoke `serializer.save()`. If a nurse or doctor attempts to update or re-submit an existing visit record, the database raises an unhandled `UNIQUE constraint failed` crash (HTTP 500).
- **Evidence:**
  - `backend/apps/triage/views.py`: Standard `ModelViewSet` lacking `update_or_create` logic.
  - `backend/apps/consultations/views.py`: Standard `ModelViewSet` lacking `update_or_create` logic.
- **Client Impact:** If a clinician corrects an accidental typing mistake and clicks "Save" again, the application crashes with a raw server error.
- **Technical Impact:** Unhandled 500 Internal Server Error; lack of idempotency on clinical creation endpoints.
- **Recommended Fix:** In `TriageVitalsViewSet.create` and `ConsultationViewSet.create`, use `update_or_create` keyed by `visit_id`.
- **Dependencies:** None.
- **Risk:** Medium risk.

---

### [FND-08] HIGH: Patient #216 Orphaned from District & Facility Scope
- **Severity:** `HIGH`
- **Module:** Patient Master / Data Model
- **Problem:** Patient #216 (`NC-KA-2026-8717`, `Ramesh Kumar Gowda`) has `registered_at_facility = None` and `district = None` in seed data.
- **Evidence:**
  - Database row: `Patient.objects.get(id=216)` has `registered_at_facility_id is None` and `district_id is None`.
  - Visit #41 for Patient #216 is assigned to Facility 68 (`Varthur Rural Clinic`).
- **Client Impact:** When the DHO views the patient directory filtered by District 11, Patient #216 vanishes from the list, yet appears in Clinic A4's visit queue.
- **Technical Impact:** Null foreign keys defeat facility-scoping filters (`Patient.objects.filter(district_id=dho_dist_id)`).
- **Recommended Fix:** Assign `registered_at_facility = 68` and `district = 11` for Patient #216 in `seed_demo.py`.
- **Dependencies:** None.
- **Risk:** Low risk.

---

### [FND-09] MEDIUM: Triage Queue Bypassed in Seed Data (Visit #39)
- **Severity:** `MEDIUM`
- **Module:** OPD Queue / Workflow Integrity
- **Problem:** Visit #39 (`VIS-20260917-003`, Anita Devi) is seeded with `status='WAITING_FOR_DOCTOR'` and `queue='DOCTOR'`, but has no associated `TriageVitals` record.
- **Evidence:**
  - `TriageVitals.objects.filter(visit_id=39).exists() == False`.
- **Client Impact:** Doctor inspecting this patient sees blank vitals. Client asks: "Can a patient skip triage without nurse vitals?"
- **Technical Impact:** Breaks clinical workflow validation; queue state allowed to advance without prerequisite milestone.
- **Recommended Fix:** Generate a valid `TriageVitals` record for Visit #39 in `seed_demo.py`.
- **Dependencies:** None.
- **Risk:** Low risk.

---

### [FND-10] MEDIUM: Queue State Desynchronization After Visit Completion (Visits #40 & #41)
- **Severity:** `MEDIUM`
- **Module:** OPD Queue / Status Consistency
- **Problem:** Visits #40 and #41 have `status = 'COMPLETED'`, but their `current_queue` remains `'DOCTOR'`.
- **Evidence:**
  - `Visit.objects.filter(id__in=[40, 41]).values('status', 'current_queue')` returns `[{'status': 'COMPLETED', 'current_queue': 'DOCTOR'}, ...]`.
- **Client Impact:** Completed patients may erroneously remain in active doctor queue lists if the query filters only by `current_queue='DOCTOR'`.
- **Technical Impact:** Inconsistent dual-state tracking (`status` vs `current_queue`).
- **Recommended Fix:** Set `current_queue = 'COMPLETED'` when `status` becomes `'COMPLETED'`.
- **Dependencies:** None.
- **Risk:** Low risk.

---

### [FND-11] MEDIUM: Prescription Marked 'DISPENSED' with Items Remaining 'PENDING'
- **Severity:** `MEDIUM`
- **Module:** Pharmacy Dispensing / Consistency
- **Problem:** In Visit #41, `Prescription #26.status = 'DISPENSED'`, but both child items (`PrescriptionItem #68, #69`) have `status = 'PENDING'`.
- **Evidence:**
  - `Prescription.objects.get(id=26).status == 'DISPENSED'`
  - `PrescriptionItem.objects.filter(prescription_id=26).values_list('status', flat=True) == ['PENDING', 'PENDING']`
- **Client Impact:** Client examining prescription line items sees items marked pending despite the prescription being marked fulfilled.
- **Technical Impact:** Inconsistency between header status and line item status.
- **Recommended Fix:** In `DispenseMedicineView` and seed script, update `PrescriptionItem.status = 'DISPENSED'` when dispensing is completed.
- **Dependencies:** None.
- **Risk:** Low risk.

---

### [FND-12] MEDIUM: Missing Inventory Transaction for Amlodipine Dispensing
- **Severity:** `MEDIUM`
- **Module:** Pharmacy / Stock Ledger
- **Problem:** In Visit #35, Metformin generated `InventoryTransaction #6`, but Amlodipine (Item #65, 14 units) has no `InventoryTransaction` record.
- **Evidence:**
  - `InventoryTransaction.objects.filter(medicine__generic_name__icontains='Amlodipine').count() == 0`.
- **Client Impact:** Stock audit report cannot explain why Amlodipine batch quantity decreased.
- **Technical Impact:** Broken transaction lineage for FEFO audit.
- **Recommended Fix:** Add matching `InventoryTransaction` for Amlodipine in `seed_demo.py`.
- **Dependencies:** None.
- **Risk:** Low risk.

---

### [FND-13] MEDIUM: Hardcoded Clinical Defaults in `Consultation.tsx`
- **Severity:** `MEDIUM`
- **Module:** Doctor Consultation UI
- **Problem:** `Consultation.tsx` initializes form state with hardcoded text ("Known history of hypertension, poor compliance", "Type 2 Diabetes Mellitus with Essential Hypertension").
- **Evidence:**
  - `frontend/src/pages/Consultation.tsx:20-24`: `useState('Known history of hypertension...')` and `useState('Type 2 Diabetes Mellitus...')`.
- **Client Impact:** Every patient examined during a demo defaults to identical diabetic/hypertensive history and clinical assessment notes.
- **Technical Impact:** Obscures dynamic patient clinical individuality.
- **Recommended Fix:** Dynamically populate consultation fields from `selectedVisit.chief_complaint` and dynamic diagnosis masters.
- **Dependencies:** None.
- **Risk:** Low risk.

---

### [FND-14] MEDIUM: Random 4-Digit Patient ID Generator Collision Risk
- **Severity:** `MEDIUM`
- **Module:** Patient Registration / ID Generation
- **Problem:** `PatientViewSet.create` generates candidate IDs using `f"NC-KA-2026-{random.randint(1000, 9999)}"`.
- **Evidence:**
  - `backend/apps/patients/views.py:81`: While loop tests uniqueness against 9,000 random integers.
- **Client Impact:** Potential registration hang or failure when namespace saturates.
- **Technical Impact:** Non-deterministic scalability bottleneck.
- **Recommended Fix:** Replace with an atomic sequential auto-incrementing ID or zero-padded 6-digit sequence.
- **Dependencies:** None.
- **Risk:** Low risk.

---

### [FND-15] LOW: Dormant Transaction Tables with 0 Database Rows
- **Severity:** `LOW`
- **Module:** Multi-Module / Demo Data Completeness
- **Problem:** 7 database tables currently have exactly 0 rows: `Household`, `PatientDocument`, `Vendor`, `PurchaseOrder`, `PurchaseOrderItem`, `Teleconsultation`, and `ReportExportLog`.
- **Evidence:**
  - Database row count analysis shows 0 rows across these 7 models.
- **Client Impact:** Clicking into "Vendors" or "Patient Documents" renders empty states with no demonstration data.
- **Technical Impact:** Unexercised code branches in integration views.
- **Recommended Fix:** Provide minimal realistic seed data (1-2 records each) in `seed_demo.py`.
- **Dependencies:** None.
- **Risk:** Low risk.

---

### [FND-16] LOW: Referral Urgency Enum Discrepancy ('HIGH' vs 'URGENT')
- **Severity:** `LOW`
- **Module:** Referrals
- **Problem:** In `Consultation.tsx`, `refUrgency` state is typed and defaulted to `'HIGH' as any`, whereas `Referral.urgency` choices in Django are `ROUTINE`, `URGENT`, and `EMERGENCY`.
- **Evidence:**
  - `frontend/src/pages/Consultation.tsx:37`: `useState<'ROUTINE' | 'URGENT' | 'EMERGENCY'>('HIGH' as any)`.
  - `backend/apps/referrals/models.py:15-19`: `choices=[('ROUTINE', 'Routine Referral'), ('URGENT', 'Urgent Evaluation'), ('EMERGENCY', 'Emergency Referral')]`.
- **Client Impact:** Creating a referral with `'HIGH'` could trigger a serializer validation error.
- **Technical Impact:** Enum mismatch between TypeScript and Django.
- **Recommended Fix:** Standardize default urgency to `'URGENT'` in `Consultation.tsx`.
- **Dependencies:** None.
- **Risk:** Low risk.

---

### [FND-17] LOW: Read-Only Follow-Up Care Module
- **Severity:** `LOW`
- **Module:** Follow-up Care
- **Problem:** `FollowUps.tsx` only renders a read-only list. It provides no button to complete a follow-up or generate an OPD token for a returning patient.
- **Evidence:**
  - `frontend/src/pages/FollowUps.tsx`: Contains only `loadData()` and rendering table; zero mutating actions.
- **Client Impact:** Client asks how returning patients are processed, but presenter has no action button to demonstrate workflow closure.
- **Technical Impact:** Incomplete state transition lifecycle in UI.
- **Recommended Fix:** Add "Mark Completed" and "Register Return Visit" action buttons.
- **Dependencies:** None.
- **Risk:** Low risk.

---

### [FND-18] INFO: Dormant Files in Backend Filesystem (`apps.maternal`, `apps.child`)
- **Severity:** `INFO`
- **Module:** Code Hygiene
- **Problem:** `backend/apps/maternal/models.py` and `backend/apps/child/models.py` exist in filesystem, though completely uninstalled and unused.
- **Evidence:**
  - `backend/apps/maternal/models.py` and `backend/apps/child/models.py` are present, but apps are omitted from `INSTALLED_APPS` and have no database tables.
- **Client Impact:** None (Zero visible footprint in UI or API).
- **Technical Impact:** Minor filesystem clutter.
- **Recommended Fix:** Retain as documented dead code until final repository pruning.
- **Dependencies:** None.
- **Risk:** Zero risk.
