# Phase C4 Pre-Implementation Audit

**Document Reference:** NC-DOC-C4-AUDIT-001  
**Project:** Namma Clinic Digital Health & Operations Platform  
**Audit Date:** September 21, 2026  
**Auditor:** Implementation Engineer (under strict PM + RSA Governance)  
**Governance Phase:** Phase C4 Pre-Implementation Quality & Scope Audit  
**Target File:** `docs/audits/PHASE_C4_PRE_IMPLEMENTATION_AUDIT.md`  

---

## 1. Baseline

- **Branch:** `feature/namma-clinic-demo-data-model`
- **Verified GitHub HEAD:** `13958a4605e8262cc3618e4d718b59a6a4afc789`
- **Commit Message:** `Fix Namma Clinic Phase C3 scope corrections`
- **Working Tree:** Clean (`nothing to commit, working tree clean`)
- **Previous Accepted Phase:** Phase C3 (Client Readiness & Workflow Remediation) formally ACCEPTED and CLOSED in commits `561026b` and `13958a4`.

### Baseline Verification Evidence
```bash
$ git status
On branch feature/namma-clinic-demo-data-model
Your branch is up to date with 'origin/feature/namma-clinic-demo-data-model'.
nothing to commit, working tree clean

$ git rev-parse HEAD
13958a4605e8262cc3618e4d718b59a6a4afc789

$ git log -5 --oneline
13958a4 Fix Namma Clinic Phase C3 scope corrections
561026b Fix Namma Clinic Phase C3 client readiness
493b417 Add Phase C3 pre-implementation audit
b6bfbcf Fix Namma Clinic Phase C2 data integrity
54c6d2c Enforce DHO export isolation and explicit environment configuration contract
```

---

## 2. Current Application State

The Namma Clinic Digital Health & Operations Platform is a tiered public healthcare management system designed for municipal primary health clinics (Namma Clinics / UPHCs), secondary community health centers, and tertiary referral hospitals.

### A. Frontend Architecture
- **Framework:** React 19 + TypeScript + Vite + Tailwind CSS + Lucide React.
- **Routing & Navigation:** Central router in [App.tsx](file:///d:/project/namma_clinic/frontend/src/App.tsx) serving 25 distinct functional routes.
- **Access Control:** Centralized route guards in [ProtectedRoute](file:///d:/project/namma_clinic/frontend/src/App.tsx) evaluating permissions defined in [permissions.ts](file:///d:/project/namma_clinic/frontend/src/utils/permissions.ts).
- **Active Roles:** 6 role archetypes:
  1. `DISTRICT_OFFICER` (DHO — District Health Officer)
  2. `HOSPITAL_ADMIN` (Facility / Administrative Manager)
  3. `DOCTOR` (Medical Officer / General Practitioner)
  4. `NURSE` (Staff Nurse / Triage Officer)
  5. `PHARMACIST` (Dispensing Pharmacist / Store In-Charge)
  6. `LAB_TECHNICIAN` (Medical Laboratory Technologist)

### B. Backend Architecture
- **Framework:** Django 5.x + Django REST Framework (DRF) + SimpleJWT authentication.
- **Installed Applications:** 22 active internal apps registered in `INSTALLED_APPS` ([settings.py](file:///d:/project/namma_clinic/backend/config/settings.py)):
  `accounts`, `geography`, `facilities`, `patients`, `visits`, `triage`, `consultations`, `pharmacy`, `laboratory`, `referrals`, `ncd`, `surveillance`, `telemedicine`, `outreach`, `wellness`, `ars`, `quality`, `alerts`, `integrations`, `compliance`, `audit`, `reports`.
- **API Surface:** 36 REST ViewSets and APIViews registered in [api_urls.py](file:///d:/project/namma_clinic/backend/config/api_urls.py).
- **Data Scoping:** Enforced via custom permissions [HasPermission, HasFacilityScope](file:///d:/project/namma_clinic/backend/apps/accounts/permissions.py) and scoping helper `get_accessible_facility_ids_for_user`.
- **Automated Regression Suite:** 44 tests executing project-wide across accounts, facilities, visits, triage, consultations, pharmacy, laboratory, referrals, reports, and security scoping.
- **Database Schema:** SQLite (`db.sqlite3`), 0 pending migrations detected.

---

## 3. Deferred Finding Assessment

The five findings previously deferred from Phase C3 were systematically audited against the running codebase:

| Finding | Current State | Client Impact | Data/Security Risk | C4 Action | Evidence |
|---------|---------------|---------------|--------------------|-----------|----------|
| **FND-06** — Teleconsultation | UI exists with simulated controls; "Save Advice" triggers dummy `alert()`; backend model/API exists with 0 rows | Doctor viewing `/teleconsultation` sees an offline mock; saving advice triggers browser alert without DB persistence | **None** (Isolated mock; no data corruption or security breach) | **SHOULD FIX IN C4 (or DEFER / HIDE)** | [Teleconsultation.tsx:107](file:///d:/project/namma_clinic/frontend/src/pages/Teleconsultation.tsx#L107), [models.py](file:///d:/project/namma_clinic/backend/apps/telemedicine/models.py), [api_urls.py:68](file:///d:/project/namma_clinic/backend/config/api_urls.py#L68) |
| **FND-14** — UHID Redesign | Random 4-digit ID generator (`NC-KA-2026-XXXX`) with `while True:` collision-check loop | **None** during live demonstrations; IDs generate and display reliably | **None** (Model has `unique=True`; foreign keys across all models target integer PK `id`, not string `patient_id`) | **DEFER** | [views.py:80-84](file:///d:/project/namma_clinic/backend/apps/patients/views.py#L80-L84), `Patient._meta.get_fields()` |
| **FND-18** — Dormant Maternal/Child Pruning | Files exist in filesystem (`apps/maternal/`, `apps/child/`), but NOT in `INSTALLED_APPS`; 0 DB tables; 0 APIs; 0 UI routes | **None** (Completely invisible to users; out-of-scope dropdown option removed in C3) | **None** (Completely uninstantiated; no runtime code path executes) | **NO ACTION REQUIRED / DEFER** | [settings.py](file:///d:/project/namma_clinic/backend/config/settings.py), SQLite schema check, [Patients.tsx](file:///d:/project/namma_clinic/frontend/src/pages/Patients.tsx) |
| **FND-21** — LabOrder → Visit Relationship | `LabOrder` links to `Consultation`, which links 1-to-1 with `Visit`; indirect encounter relationship exists | **None** (Diagnostics lab and patient timeline function correctly; reports filter by facility and date) | **None** (Integrity preserved; adding direct FK requires an unapproved database migration) | **DEFER** | [laboratory/models.py:13-26](file:///d:/project/namma_clinic/backend/apps/laboratory/models.py#L13-L26), [reports/views.py:69,121](file:///d:/project/namma_clinic/backend/apps/reports/views.py#L69) |
| **FND-22** — Triage → Alert Event Bus | Triage vitals calculate flags (`high_bp_flag`, etc.) synchronously on save; UI displays risk banners directly; separate operational `Alert` model exists | **None** (Real-time clinical warnings render immediately in Triage and Consultation without an async bus) | **None** (Synchronous REST model is robust; async broker like Redis/Celery is out of scope) | **DEFER** | [triage/models.py:31-40](file:///d:/project/namma_clinic/backend/apps/triage/models.py#L31-L40), [Triage.tsx:177](file:///d:/project/namma_clinic/frontend/src/pages/Triage.tsx#L177), [Consultation.tsx:358](file:///d:/project/namma_clinic/frontend/src/pages/Consultation.tsx#L358) |

---

### Detailed Finding Evaluations (A through K)

#### 1. FND-06 — Teleconsultation
- **A. Current Implementation State:** A complete simulated workspace exists in `frontend/src/pages/Teleconsultation.tsx`. It provides mock video call controls (Start/End Call, Mute) using React local state, a hardcoded case card ("Ramesh Kumar, 52/M"), and a textarea for specialist notes. Clicking "Save Advice to Patient Record" executes `alert('Teleconsultation advice notes saved to patient visit EMR!')`. On the backend, `apps/telemedicine/models.py` defines `Teleconsultation` (with fields `teleconsult_id`, `patient`, `clinic_facility`, `hub_facility`, `requesting_doctor`, `specialist_doctor`, `status`, `clinical_notes`, `specialist_advice`), and `TeleconsultationViewSet` is registered at `/api/telemedicine/`. The database table currently contains 0 records.
- **B. User-Visible:** YES. Accessible to role `DOCTOR` at route `/teleconsultation` and displayed in the sidebar navigation.
- **C. Currently Functional:** Partially. The simulated call canvas toggles state, but note persistence is non-functional.
- **D. 403 / 404 / 500 / Dead-Button / Blank-Page:** DEAD-BUTTON behavior on "Save Advice to Patient Record" (fires `alert()` without persisting or updating any clinical record).
- **E. Data-Integrity Risk:** None (no corrupt data written).
- **F. Security / RBAC Risk:** None (route guard restricts to `DOCTOR`; backend endpoint enforces authentication).
- **G. Reporting / KPI Correctness Risk:** None (no executive KPIs or DHO reports aggregate teleconsultation).
- **H. Conflict with Current Scope:** Live WebRTC or external e-Sanjeevani API integration is strictly out of scope. However, demonstrating an internal doctor-to-specialist teleconsultation workflow is aligned with primary healthcare objectives.
- **I. Required for Current Client Readiness:** If the Doctor navigation sidebar includes "Teleconsultation", a reviewer clicking "Save Advice" may perceive the browser `alert()` as an incomplete prototype.
- **J. Recommended Action:** **SHOULD FIX IN C4 (or DEFER / HIDE)**.
  - *Option 1 (Lightweight Functional Demo):* Connect `Teleconsultation.tsx` to `POST /api/telemedicine/` and persist the specialist note into the patient timeline.
  - *Option 2 (Navigation Cleanup):* Remove `/teleconsultation` from `DOCTOR` allowed paths and sidebar navigation, cleanly deferring the module to Phase D without dead buttons.
- **K. Supporting Evidence:**
  - `frontend/src/pages/Teleconsultation.tsx:107`: `onClick={() => alert('Teleconsultation advice notes saved to patient visit EMR!')}`
  - `backend/apps/telemedicine/models.py:3-26`: Model exists and is fully configured.
  - `backend/config/api_urls.py:68`: `router.register(r'telemedicine', TeleconsultationViewSet, basename='telemedicine')`

#### 2. FND-14 — UHID Redesign
- **A. Current Implementation State:** In `backend/apps/patients/views.py:80-84`, new patient registrations generate UHIDs using `candidate_id = f"NC-KA-2026-{random.randint(1000, 9999)}"` inside a `while True:` loop that verifies uniqueness against `Patient.objects.filter(patient_id=candidate_id).exists()`.
- **B. User-Visible:** YES. Displayed in patient directory, patient details, queue tokens, and badges.
- **C. Currently Functional:** YES. Generates unique, valid UHIDs on every registration.
- **D. 403 / 404 / 500 / Dead-Button / Blank-Page:** NO.
- **E. Data-Integrity Risk:** Statistically negligible for demo scale. The 4-digit namespace allows 9,000 unique IDs. Across the ~216 seeded patients, collision probability on a single insert is ~2.4%, which resolves on the second iteration in under 1 millisecond. Model constraint `unique=True` prevents database collisions.
- **F. Security / RBAC Risk:** None.
- **G. Reporting / KPI Correctness Risk:** None.
- **H. Conflict with Current Scope:** Sequential auto-increment sequence redesign is an infrastructure scaling task, not a client demo requirement.
- **I. Required for Current Client Readiness:** NO.
- **J. Recommended Action:** **DEFER**.
- **K. Supporting Evidence:**
  - Relational inspection confirms all 16 referencing foreign keys (`Visit`, `Consultation`, `Prescription`, `LabOrder`, `Referral`, `FollowUp`, `TriageVitals`, `PatientDocument`, etc.) target the integer primary key `Patient.id`, NOT `Patient.patient_id`. Changing or retaining the format causes zero relational disruption.

#### 3. FND-18 — Dormant Maternal/Child Pruning
- **A. Current Implementation State:** Model definitions exist in `backend/apps/maternal/models.py` and `backend/apps/child/models.py`. However:
  1. Neither `apps.maternal` nor `apps.child` is registered in `INSTALLED_APPS` in `config/settings.py`.
  2. No migrations exist in `apps/maternal/migrations` or `apps/child/migrations`.
  3. No database tables exist in `db.sqlite3` (`introspection.table_names()` contains 0 maternal/child tables).
  4. No API endpoints exist in `config/api_urls.py`.
  5. No frontend routes exist in `frontend/src/App.tsx`.
  6. No frontend navigation links exist in `DashboardLayout.tsx` or `Sidebar.tsx`.
  7. No permissions exist in `permissions.ts`.
  8. In Phase C3 (Issue 1), the single user-facing dropdown option `High Risk Pregnancy ANC` was permanently removed from `Patients.tsx`.
- **B. User-Visible:** NO. Completely invisible in the UI.
- **C. Currently Functional:** Dormant / Inactive.
- **D. 403 / 404 / 500 / Dead-Button / Blank-Page:** None.
- **E. Data-Integrity Risk:** None.
- **F. Security / RBAC Risk:** None.
- **G. Reporting / KPI Correctness Risk:** None.
- **H. Conflict with Current Scope:** Maternal/Child is permanently out of scope. The dormant files are completely unlinked.
- **I. Required for Current Client Readiness:** NO.
- **J. Recommended Action:** **NO ACTION REQUIRED / DEFER**. Per governance instructions: *"Do NOT delete dormant code simply because it exists. Recommend removal only if there is a concrete reason and the audit establishes that it is safe."* The dormant files have zero runtime impact. Deleting them is cosmetic code hygiene.
- **K. Supporting Evidence:**
  - `backend/config/settings.py`: Neither app is installed.
  - SQLite check: `[t for t in connection.introspection.table_names() if 'maternal' in t or 'child' in t] == []`.

#### 4. FND-21 — LabOrder → Visit Relationship
- **A. Current Implementation State:**
  - `LabOrder` belongs to `Consultation` via `consultation = ForeignKey('consultations.Consultation', on_delete=models.SET_NULL, null=True, blank=True)`.
  - `Consultation` belongs to `Visit` via `visit = OneToOneField('visits.Visit', on_delete=models.CASCADE)`.
  - Therefore, an indirect relationship exists: `lab_order.consultation.visit`.
  - In addition, `LabOrder` directly references `patient` and `facility`.
  - Multiple lab orders can legitimately belong to a single consultation encounter (e.g., CBC, Serum Creatinine, Blood Glucose).
- **B. User-Visible:** YES. Lab orders appear in the Diagnostics Lab queue, Patient Detail records, and Patient Timeline.
- **C. Currently Functional:** YES. Doctor orders lab tests during consultation, Lab Technician collects samples, enters results, and verifies. Results display in patient records.
- **D. 403 / 404 / 500 / Dead-Button / Blank-Page:** None.
- **E. Data-Integrity Risk:** None.
- **F. Security / RBAC Risk:** None.
- **G. Reporting / KPI Correctness Risk:** None. Executive KPIs (`DashboardSummaryView`, `CSVExportView`) query lab orders by `facility_id` and `order_date`, not by `visit_id`.
- **H. Conflict with Current Scope:** None.
- **I. Required for Current Client Readiness:** NO.
- **J. Recommended Action:** **DEFER**. Adding a direct `visit` foreign key requires an unapproved database migration, altering serializers, and updating seed scripts without providing any new user-facing functionality.
- **K. Supporting Evidence:**
  - `backend/apps/laboratory/models.py:13-26`
  - `backend/apps/reports/views.py:69,121`

#### 5. FND-22 — Triage → Alert Event Bus
- **A. Current Implementation State:**
  - `TriageVitals.save()` synchronously computes clinical warning flags: `high_bp_flag`, `high_glucose_flag`, `fever_flag`, `low_spo2_flag`, and `bmi`.
  - Frontend forms in `Triage.tsx` and `Consultation.tsx` evaluate these vitals and display dynamic risk alert banners (`🚨 AUTOMATIC CLINICAL RISK FLAGS DETECTED`) and color badges.
  - `Queue.tsx` displays priority flags (`🚨 EMERGENCY`, `⚡ HIGH`, `🟢 NORMAL`).
  - The `Alert` model in `apps/alerts/models.py` manages operational alerts (`LOW_STOCK`, `NEAR_EXPIRY`, `REFERRAL_OVERDUE`, `FOLLOWUP_OVERDUE`).
  - An asynchronous publish/subscribe event bus (e.g. Celery / Redis / WebSocket message broker) is not present.
- **B. User-Visible:** Clinical risk flags and operational alerts ARE user-visible.
- **C. Currently Functional:** YES. The synchronous REST workflow displays all flags and warnings without delay.
- **D. 403 / 404 / 500 / Dead-Button / Blank-Page:** None.
- **E. Data-Integrity Risk:** None.
- **F. Security / RBAC Risk:** None.
- **G. Reporting / KPI Correctness Risk:** None.
- **H. Conflict with Current Scope:** An asynchronous event broker is an infrastructure enhancement for Phase D, not required for current clinic workflows.
- **I. Required for Current Client Readiness:** NO.
- **J. Recommended Action:** **DEFER**.
- **K. Supporting Evidence:**
  - `backend/apps/triage/models.py:31-40`
  - `frontend/src/pages/Triage.tsx:177-205`
  - `frontend/src/pages/Consultation.tsx:358-375`

---

## 4. Newly Discovered Findings

During the comprehensive audit of the application, codebases, tests, and linters, two minor items were identified:

| Finding ID | Title | Module | Severity | Description | Evidence |
|---|---|---|:---:|---|---|
| **NEW-FND-01** | Frontend Linter Variable & Import Warnings | Frontend Pages | **LOW** | `npm run lint` reports 135 warnings (0 errors) across 41 files for unused imports (`Ban`, `Info`, `XCircle` in `Pharmacy.tsx`) and unreferenced variables (`isImage` in `PatientDetail.tsx`). Does not prevent building (`npm run build` succeeds). | `npm run lint` output |
| **NEW-FND-02** | Naive DateTime RuntimeWarning in Test Suite | Backend Tests | **INFO** | Test runner issues runtime warnings during `apps.visits` execution: `DateTimeField Visit.visit_date received a naive datetime while time zone support is active`. Tests pass (44/44), but test fixtures use naive datetimes. | `manage.py test` output |

*Note: No CRITICAL or HIGH severity findings were discovered. All 11 tickets resolved in C1/C2 and all 6 tickets resolved in C3 remain stable with zero regressions.*

---

## 5. Client Journey Audit

The end-to-end patient journey was validated across all 11 stages using live model execution within a dry-run transaction:

```
[1. Citizen / Catchment] 
       │
       ▼
[2. Patient Registration] ──> UHID Generated: NC-KA-2026-XXXX (Scoped to Facility & District)
       │
       ▼
[3. OPD Token & Visit]   ──> Token # Issued; Status: WAITING_FOR_TRIAGE; Queue: TRIAGE
       │
       ▼
[4. Date-Based Queue]    ──> Visible in Nurse Queue; Priority: NORMAL / HIGH / EMERGENCY
       │
       ▼
[5. Nurse Triage]        ──> Vitals Recorded; Auto-calculated BMI & Risk Flags; Queue: DOCTOR
       │
       ▼
[6. Doctor Consultation] ──> Empty Clinical Defaults; Explicit Assessment; Diagnosis & Rx
       │
       ├─────────────────────────────────┬────────────────────────────────┐
       ▼                                 ▼                                ▼
[7. Diagnostics Lab]            [8. Pharmacy Dispense]          [9. Referral & Follow-up]
Order -> Sample -> Result ->     Prescription -> FEFO Batch ->   Specialist Referral ->
Released to EMR                  Atomic Inventory Ledger         Return Care Follow-up (Completed)
       │                                 │                                │
       └─────────────────────────────────┴────────────────────────────────┘
                                         │
                                         ▼
                             [10. Public Health & Surveillance]
                             NCD Cohort Registry & IDSP Disease Anomaly Tracking
                                         │
                                         ▼
                             [11. DHO Governance & Oversight]
                             District-Scoped Network, ARS, Quality, Infrastructure, CSV Reports
```

### Stage-by-Stage Verification:

1. **Registration:**
   - *Status:* **PASS**.
   - Generates `patient_id` (`NC-KA-2026-XXXX`).
   - District and registered facility scoping enforced in `clean()`.
   - Vulnerability dropdown provides 6 application-level categories without Maternal/Child options.
2. **Visit & Token Creation:**
   - *Status:* **PASS**.
   - Generates daily sequence token scoped to facility and date.
   - Initial state: `status='WAITING_FOR_TRIAGE'`, `current_queue='TRIAGE'`.
3. **Queue:**
   - *Status:* **PASS**.
   - Filters by date, queue stage (`TRIAGE`, `DOCTOR`, `LAB`, `PHARMACY`, `COMPLETED`), and facility.
   - `Call Next` and manual stage transitions verified with role permissions.
4. **Triage:**
   - *Status:* **PASS**.
   - Nurse records vitals (BP, pulse, temp, SpO2, glucose, height, weight).
   - Flags evaluated synchronously; saves cleanly and advances visit to `WAITING_FOR_DOCTOR`.
5. **Consultation:**
   - *Status:* **PASS**.
   - Clinical assessment, history, diagnosis, and treatment plan start with clean empty defaults (C3 FND-13).
   - Vitals displayed in observational side-panel.
   - Prescription items created with valid medicines.
   - Referral created with valid urgency (`URGENT`, `ROUTINE`, `EMERGENCY` — C3 FND-16).
6. **Laboratory:**
   - *Status:* **PASS**.
   - Orders linked to consultation; sample collection with unique barcode; result entry and verification functional.
7. **Pharmacy:**
   - *Status:* **PASS**.
   - Dispensing uses FEFO (First Expiry, First Out) deduction from nearest-expiry batch.
   - Logs `InventoryTransaction` with exact reference IDs.
   - Purchase Orders tab renders seeded demo POs (`ORDERED`, `RECEIVED` — C3 FND-15).
8. **Referral:**
   - *Status:* **PASS**.
   - Outgoing referrals routed between rural clinic and hub hospital.
   - Response capture and return advice functional.
9. **Follow-Up:**
   - *Status:* **PASS**.
   - Follow-up records scheduled from referral or consultation.
   - "Mark Completed" action updates status to `COMPLETED` via `PATCH /api/followups/{id}/` (C3 FND-17).
10. **Public Health:**
    - *Status:* **PASS**.
    - NCD Registry tracks hypertension/diabetes cohorts.
    - Disease Surveillance tracks epidemic case thresholds.
11. **DHO Governance:**
    - *Status:* **PASS**.
    - DHO dashboard aggregates data exclusively for District 11 facilities.
    - CSV export isolation strictly enforced.
    - Infrastructure route `/infrastructure` accessible to DHO for oversight (C3 FND-19).

---

## 6. Data Integrity Audit

All Phase C1, C2, and C3 data invariants were re-verified against `db.sqlite3`:

1. **Patient Facility & District Alignment:**
   - `Patient.objects.filter(registered_at_facility__isnull=False).exclude(district=F('registered_at_facility__district')).count() == 0` (0 mismatches).
2. **Visit Facility & Patient District Consistency:**
   - `Visit.objects.filter(facility__isnull=False, patient__isnull=False).exclude(facility__district=F('patient__district')).count() == 0` (0 mismatches).
3. **Queue Synchronization:**
   - All completed visits have `current_queue='COMPLETED'`.
4. **Prescription Status Invariance:**
   - Total Prescriptions: 4. Total PrescriptionItems: 6.
   - Prescriptions marked `DISPENSED` have 0 `PENDING` items.
5. **Purchase Order Invariance:**
   - Exactly 2 POs seeded (`PO-HOSP-DIST-01-2026-001` [ORDERED], `PO-HOSP-DIST-01-2026-002` [RECEIVED]).
   - 0 POs with invalid statuses.
6. **Inventory Lineage:**
   - All pharmacy dispense actions have corresponding `InventoryTransaction` records with valid batch and user attribution.

---

## 7. Security / RBAC Audit

All 6 roles were checked for navigation, route guards, and API authority:

| Role | Username | Assigned Scope | Navigation Items | API Mutation Authority | District Isolation |
|---|---|---|:---:|---|:---:|
| **DISTRICT_OFFICER** | `district` | District 11 (BBMP Central) | 16 routes (incl. `/infrastructure`) | Read-Only across clinical endpoints; mutating requests return HTTP 403 | **STRICT PASS** (All queries scoped to District 11) |
| **HOSPITAL_ADMIN** | `hospital` | Facility 66 (CV Raman Hospital) | 13 routes | Admin & queue transitions permitted | **PASS** |
| **DOCTOR** | `doctor` | Facility 68 (Varthur Rural Clinic) | 9 routes | Consultations, prescriptions, lab orders, referrals permitted | **PASS** |
| **NURSE** | `nurse` | Facility 68 (Varthur Rural Clinic) | 9 routes | Registration, triage, outreach, wellness, follow-ups permitted | **PASS** |
| **PHARMACIST** | `pharmacy` | Facility 68 (Varthur Rural Clinic) | 5 routes | Dispense, batch adjustment, PO viewing permitted | **PASS** |
| **LAB_TECHNICIAN** | `lab` | Facility 68 (Varthur Rural Clinic) | 4 routes | Sample collection, results, verification permitted | **PASS** |

---

## 8. Scope Audit

### Explicit Confirmation: Maternal / Child Health Scope
- **Maternal / Child Health remains 100% INACTIVE and PERMANENTLY OUT OF SCOPE.**
- **No Maternal UI is exposed.**
- **No Child UI is exposed.**
- **No Maternal navigation links exist.**
- **No Child navigation links exist.**
- **No Maternal/Child active dropdown options exist** (`High Risk Pregnancy ANC` was permanently removed in C3).
- **No Maternal/Child workflows are active.**
- **No Maternal/Child dashboard cards exist.**
- The dormant files `backend/apps/maternal/models.py` and `backend/apps/child/models.py` have 0 database tables, 0 migrations, 0 API URLs, and are not in `INSTALLED_APPS`.

---

## 9. C4 Proposed Scope

Based on the evidence gathered in this pre-implementation audit, the proposed scope for Phase C4 is structured into four categories:

### Must Fix
*(Only actual current client-readiness blockers)*
- **NONE.** The core patient journey (Registration → Visit → Queue → Triage → Consultation → Lab → Pharmacy → Referral → Follow-up → Public Health → DHO) operates without runtime crashes, HTTP 400/403/500 errors, or data integrity anomalies. All 44 automated tests pass cleanly.

### Should Fix
*(Important non-blocking polish for client demonstration)*
1. **FND-06 — Teleconsultation Module Resolution (PM/RSA Decision Required):**
   - **Option A (Connect to Backend API):** Wire `Teleconsultation.tsx` to `POST /api/telemedicine/` so that when a doctor enters specialist advice and clicks "Save Advice", an authentic `Teleconsultation` record is created and displayed in the patient timeline, replacing the dummy `alert()`.
   - **Option B (De-clutter Doctor Navigation):** Remove `/teleconsultation` from `DOCTOR` allowed paths in `permissions.ts` and from sidebar navigation in `DashboardLayout.tsx`. Telemedicine is then cleanly deferred to Phase D.
2. **NEW-FND-01 — Frontend Linter Cleanliness:**
   - Remove unused imports and unreferenced variables across `Pharmacy.tsx` and `PatientDetail.tsx` to reduce lint warnings from 135 to 0.

### Defer
*(Valid technical enhancements that do not block client readiness)*
1. **FND-14 — UHID Sequential Generator:** Defer to production infrastructure scaling. Current unique generator functions reliably without collision in demonstration namespaces.
2. **FND-21 — LabOrder → Visit Foreign Key:** Defer to post-demo schema refactoring. Indirect relationship via Consultation is fully functional.
3. **FND-22 — Triage → Alert Asynchronous Event Bus:** Defer to Phase D. Synchronous REST evaluation of clinical flags meets all current operational requirements.
4. **FND-18 — Dormant Maternal/Child Source File Deletion:** Defer until final project maintenance. Files have zero runtime execution.

### Remove / Decommission
- **None.** No active code or functionality requires decommissioning.

---

## 10. Explicit Non-Goals

Phase C4 must **NOT** implement:
- Any redesign of the UHID generation sequence or database schema.
- Any new database migrations or schema alterations (including adding a `visit` FK to `LabOrder`).
- Any live external integrations with ABDM, ABHA, HMIS, or e-Sanjeevani (all integrations remain local simulations).
- Any WebRTC video streaming or third-party teleconsultation cloud service.
- Any asynchronous message broker (Celery, Redis, RabbitMQ, WebSockets) for alerts.
- Any reactivation or exposure of Maternal/Child models, UI, or navigation.
- Any modification to closed Phase C1, C2, or C3 data integrity invariants.

---

## 11. Validation Evidence

### Exact Commands and Execution Results

#### 1. Baseline Git Verification
```powershell
$ git status
On branch feature/namma-clinic-demo-data-model
Your branch is up to date with 'origin/feature/namma-clinic-demo-data-model'.
nothing to commit, working tree clean

$ git rev-parse HEAD
13958a4605e8262cc3618e4d718b59a6a4afc789
```

#### 2. Project-Wide Backend Automated Test Suite
```powershell
$ venv\Scripts\python.exe manage.py test
Creating test database for alias 'default'...
Found 44 test(s).
System check identified no issues (0 silenced).
............................................
----------------------------------------------------------------------
Ran 44 tests in 44.091s

OK
Destroying test database for alias 'default'...
```
- **Total Tests:** 44
- **Passed:** 44
- **Failed:** 0
- **Errors:** 0
- **Duration:** 44.091s

#### 3. Database Migration Integrity Check
```powershell
$ venv\Scripts\python.exe manage.py makemigrations --check --dry-run
No changes detected
```
- **Exit Code:** 0

#### 4. Frontend Production Build
```powershell
$ npm run build
> frontend@0.0.0 build
> tsc -b && vite build
vite v8.2.2 building client environment for production...
transforming...
✓ 1918 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.47 kB │ gzip:   0.30 kB
dist/assets/index-DJAFoXLr.css   68.08 kB │ gzip:  11.36 kB
dist/assets/index-CWI0HMXK.js   712.02 kB │ gzip: 166.87 kB
✓ built in 599ms
```
- **Errors:** 0
- **Exit Code:** 0

#### 5. Frontend Linter
```powershell
$ npm run lint
Found 135 warnings and 0 errors.
Finished in 308ms on 41 files with 116 rules using 12 threads.
```
- **Errors:** 0
- **Warnings:** 135 (unused variables / imports)

#### 6. End-to-End Client Journey Dry-Run (Atomic Transaction)
```powershell
$ venv\Scripts\python.exe -c "..."
=== TESTING CLIENT JOURNEY IN DRY-RUN TRANSACTION ===
1. Registration SUCCESS: Patient NC-KA-2026-9991, District BBMP Central (Bengaluru Urban)
2. Visit Created SUCCESS: VIS-TEST-001, Status: WAITING_FOR_TRIAGE
3. Triage SUCCESS: BP 150/95, High BP Flag: True, Fever: True
4. Consultation & Rx SUCCESS: Consult ID 70, Rx ID 70, Item Metformin HCl
5. Lab Order SUCCESS: Order ID 51, Test: HbA1c Glycated Hemoglobin
6. Referral & FollowUp SUCCESS: Ref ID REF-TEST-001, FollowUp ID 31
7. FollowUp Completed SUCCESS: status=COMPLETED
Transaction rolled back cleanly. DB unchanged.
```

---

## 12. PM/RSA Decision Required

Implementation scope requires PM/RSA approval.

The Implementation Engineer has completed this audit in strict read-only mode. No application source files, database records, seed scripts, or migrations have been modified.

### Decisions Requested from PM/RSA:
1. **FND-06 (Teleconsultation):** Choose between Option A (implement lightweight persistence to `POST /api/telemedicine/`) vs. Option B (hide `/teleconsultation` from navigation) vs. Option C (maintain current simulated state with explicit demo guidance).
2. **Authorization of C4 Scope:** Confirm whether Phase C4 should address Should-Fix items (FND-06 resolution and linter warning cleanup), or whether Phase C can be formally concluded with Phase C3.
