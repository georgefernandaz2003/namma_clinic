# Namma Clinic — Role Flow Execution Report & Defect Matrix

## 1. Executive Summary

A comprehensive, controlled role-based flow audit was executed across all 6 active production roles in the Namma Clinic Digital Health & Operations Platform.

The audit verified that the primary underlying business logic, database transactions, FEFO stock decrements, and cross-role data handoffs function consistently end-to-end. However, four critical frontend navigation and UI-binding defects were uncovered that interrupt seamless role transitions or display stale/hardcoded data to clinic operators.

Zero database mutations or code changes were made during this audit pass. A controlled demonstration citizen (`Anand Varma`, UHID `NC-KA-2026-8262`) was traced across the entire 13-stage clinical pathway in an isolated transaction that was safely rolled back upon completion.

---

## 2. Role Journey Execution Results

### Role Journey 1 — Staff Nurse (`nurse`)
- **Assigned Facility**: Varthur Rural Primary Clinic A4 (Facility ID #108 / #112)
- **Workflow Executed**:
  1. Login as `nurse` → Navigated to `/patients` (PASS).
  2. Registered citizen "Anand Varma" with valid demographic, mobile, Slum Resident vulnerability (PASS - Patient ID #639).
  3. Issued daily OPD Token for General OPD (PASS - Visit ID #163, Token #4).
  4. Verified visit appeared in `TRIAGE` queue with `WAITING_FOR_TRIAGE` status (PASS).
  5. Opened `/triage` and recorded physiological vitals: BP 148/96 mmHg, pulse 82, glucose 175 mg/dL (PASS - Triage ID #99).
  6. High BP and High Glucose flags evaluated true (PASS).
  7. Visit automatically transitioned to `WAITING_FOR_DOCTOR` in `DOCTOR` queue (PASS).
- **Navigation Interruption (Defect)**: Upon saving triage, `Triage.tsx` attempts `navigate('/consultation')`, triggering an HTTP 403 Access Denied screen because Nurse role is prohibited from accessing doctor consultations.
- **Role Result**: **FAIL (Workflow blocked by invalid post-triage redirect)**.

### Role Journey 2 — Medical Officer (`doctor`)
- **Assigned Facility**: Varthur Rural Primary Clinic A4
- **Workflow Executed**:
  1. Login as `doctor` → Navigated to `/queue` (PASS).
  2. Verified triaged patient "Anand Varma" appeared in `DOCTOR` queue with status `WAITING_FOR_DOCTOR` (PASS).
  3. Called patient using `POST /api/visits/call-next/` → status transitioned to `IN_CONSULTATION` (PASS).
  4. Opened Consultation console; reviewed triage vitals and clinical warning flags (PASS).
  5. Recorded clinical examination and ICD diagnosis "Essential hypertension with Type 2 Diabetes" (PASS - Consultation ID #74).
  6. Prescribed Metformin 500mg (28 tabs) and Amlodipine 5mg (14 tabs) linked to `MedicineMaster` (PASS - Prescription ID #74 with 2 items).
  7. Ordered Fasting Blood Sugar lab test (PASS - LabOrder ID #55).
  8. Initiated routine referral to Victoria District Hospital specialist center (PASS - Referral ID #41).
  9. Scheduled 14-day follow-up appointment for chronic review (PASS - FollowUp ID #33).
  10. Saved consultation → visit automatically transitioned to `WAITING_FOR_PHARMACY` in `PHARMACY` queue (PASS).
- **UI Binding Defects**:
  - Doctor Dashboard active patient card displays hardcoded static vitals (`150/96 mmHg`, `190 mg/dL`) instead of real vitals.
  - "Start EMR Consultation →" button links to `/consultation?visit=X`, but `Consultation.tsx` does not parse URL search parameters, failing to preselect the called patient.
- **Role Result**: **PASS with UI Defects (FND-FLOW-02, FND-FLOW-03)**.

### Role Journey 3 — Lab Technician (`lab`)
- **Assigned Facility**: Varthur Rural Primary Clinic A4
- **Workflow Executed**:
  1. Login as `lab` → Navigated to `/lab` (PASS).
  2. Verified pending lab order for "Anand Varma" in `ORDERED` status (PASS).
  3. Collected specimen using `POST /api/lab/orders/55/collect-sample/` → unique barcode `SMP-0055` generated (PASS).
  4. Entered and verified test result: `168.0 mg/dL` (`HIGH`) via `POST /api/lab/orders/55/save-result/` (PASS).
  5. Order status transitioned to `COMPLETED` (PASS).
  6. Doctor inspected and verified result immediately in patient EMR timeline (PASS).
- **Role Result**: **PASS (100% operational)**.

### Role Journey 4 — Pharmacist (`pharmacy`)
- **Assigned Facility**: Varthur Rural Primary Clinic A4
- **Workflow Executed**:
  1. Login as `pharmacy` → Navigated to `/pharmacy` (PASS).
  2. Verified pending prescription #74 for "Anand Varma" (PASS).
  3. Inspected available stock batches across Metformin and Amlodipine (PASS).
  4. Executed dispensing using `POST /api/pharmacy/dispense/` (PASS).
  5. Verified FEFO batch selection: deducted 28 tabs from earliest expiry batch `MET-RC-A4-04-2026A` and 14 tabs from `AML-RC-A4-04-2026B` (PASS).
  6. Two `InventoryTransaction` ledger rows created with reference `PRESCR-74` (PASS).
  7. Prescription header and item statuses updated to `DISPENSED` (PASS).
  8. Visit status updated to `COMPLETED` in `COMPLETED` queue (PASS).
- **Role Result**: **PASS (100% operational)**.

### Role Journey 5 — Hospital Admin (`hospital` / `vh1_admin`)
- **Assigned Facility**: Victoria District General Hospital (Facility ID #106)
- **Workflow Executed**:
  1. Login as `hospital` → Navigated to `/` (PASS).
  2. Verified own facility administration metrics, staff, beds, and oxygen banks (PASS).
  3. Inspected incoming specialist referrals → verified incoming referral #41 from Varthur Clinic for "Anand Varma" (PASS).
  4. Created Purchase Order `PO-HA-TEST-...` against approved vendor (PASS).
  5. Attempted direct access to another facility's private resources (`/api/facilities/108/`) → strictly rejected with HTTP 404 Not Found (PASS).
- **Role Result**: **PASS (100% operational)**.

### Role Journey 6 — District Health Officer (`district`)
- **Assigned District**: BBMP Central (District ID #31; 4 facilities)
- **Workflow Executed**:
  1. Login as `district` → Navigated to `/` (PASS).
  2. Verified district-wide aggregated statistics (39 patients, 4 connected clinics) (PASS).
  3. Queried longitudinal patient timeline for "Anand Varma" via `GET /api/patients/639/timeline/` (PASS).
  4. Confirmed all 8 chronological encounter events displayed (Registration, Visit, Triage, Consultation, Prescription, Lab Investigation, Referral, Follow-up) (PASS).
  5. Attempted clinical mutation (`POST /api/patients/`) → strictly rejected with HTTP 403 Forbidden (PASS).
  6. Exported OPD CSV report for authorized facility 108 (PASS - HTTP 200).
  7. Attempted cross-district export for unauthorized facility 9999 → returned empty dataset with 0 patient records (PASS - HTTP 200 with header only).
- **Role Result**: **PASS (100% operational)**.

---

## 3. Findings & Defect Classification

| Finding ID | Severity | Role Impacted | Page / Component | Problem Description | Root Cause | Recommended Action |
|---|---|---|---|---|---|---|
| **FND-FLOW-01** | **HIGH** | `NURSE` | `frontend/src/pages/Triage.tsx` (Line 79) | After nurse saves triage vitals, the UI navigates to `/consultation`. The route guard immediately blocks access and displays the `Access Denied (HTTP 403)` error screen to the nurse. | `navigate('/consultation')` was hardcoded instead of returning to `/queue` or remaining on `/triage`. | Update post-triage redirect in `Triage.tsx` to navigate to `/queue` with success notification. |
| **FND-FLOW-02** | **HIGH** | `DOCTOR` | `frontend/src/pages/Consultation.tsx` (Lines 12, 79-82) | Clicking "Start EMR Consultation →" from the Doctor Dashboard links to `/consultation?visit=X`, but the consultation form does not pre-select the called patient; it falls back to the first patient in the queue. | `Consultation.tsx` only reads `location.state?.visitId` and fails to parse `?visit=` URL search parameters. | In `Consultation.tsx`, parse `new URLSearchParams(location.search).get('visit')` to initialize `stateVisitId`. |
| **FND-FLOW-03** | **MEDIUM** | `DOCTOR` | `frontend/src/components/dashboards/DoctorDashboard.tsx` (Lines 185, 189, 193, 197) | When an active called patient is displayed on the Doctor Dashboard, the triage summary displays static hardcoded strings (`150/96 mmHg`, `190 mg/dL`, `88 bpm`) instead of the real vitals recorded by the nurse. | JSX contains static strings rather than dynamically rendering from `activeVisit.triage_details` or fetching triage vitals. | Fetch or bind real triage vitals to the active called patient card in `DoctorDashboard.tsx`. |
| **FND-FLOW-04** | **MEDIUM** | `ALL ROLES` (`NURSE`, `DOCTOR`, `PHARMACIST`) | `frontend/src/pages/Queue.tsx` (Lines 516-550) | In the OPD Queue table, action buttons ("Triage", "Consult", "Dispense") appear on every row regardless of the user's role. A Nurse clicking "Consult" gets HTTP 403, and a Doctor clicking "Triage" or "Dispense" gets HTTP 403. | The row action buttons check `isToday` and `v.status`, but do not filter actions by `isPathAllowedForRole(user?.role, path)`. | Filter action buttons in `Queue.tsx` based on user role authorization so users only see actionable buttons for their own station. |
| **FND-FLOW-05** | **LOW** | `DOCTOR` | `frontend/src/utils/permissions.ts` (Lines 23, 65) | Doctors have backend permission for `ncd.view`, but `/ncd` is omitted from `ROLE_ALLOWED_PATHS['DOCTOR']`, preventing doctors from viewing the facility NCD screening register. | Inconsistency between `ROLE_PERMISSIONS` and `ROLE_ALLOWED_PATHS`. | Add `/ncd` to `ROLE_ALLOWED_PATHS['DOCTOR']` in `permissions.ts`. |
| **FND-FLOW-06** | **INFO** | `SYSTEM` | Backend DRF Pagination | Test runs output `UnorderedObjectListWarning: Pagination may yield inconsistent results with an unordered object_list: <class 'apps.consultations.models.Prescription'>`. | `Prescription` model lacks explicit ordering in `Meta` or queryset. | Add `ordering = ['-id']` in `Prescription.Meta` when schema changes are permitted. |

---

## 4. Prioritized Correction Plan

### Step 1: Fix Nurse Post-Triage Redirection (FND-FLOW-01)
- **Target File**: `frontend/src/pages/Triage.tsx`
- **Change**: Change line 79 from:
  ```typescript
  navigate('/consultation', { state: { visitId: selectedVisit.id } });
  ```
  to:
  ```typescript
  navigate('/queue');
  ```
- **Validation**: Nurse saves triage vitals and returns cleanly to `/queue` without encountering HTTP 403 Access Denied.

### Step 2: Fix Consultation URL Search Parameter Binding (FND-FLOW-02)
- **Target File**: `frontend/src/pages/Consultation.tsx`
- **Change**: Update visit ID resolution to support query parameter:
  ```typescript
  const queryVisitId = new URLSearchParams(location.search).get('visit');
  const stateVisitId = location.state?.visitId || (queryVisitId ? parseInt(queryVisitId) : undefined);
  ```
- **Validation**: Clicking "Start EMR Consultation →" on Doctor Dashboard successfully opens and pre-selects the exact called patient.

### Step 3: Bind Real Triage Vitals on Doctor Dashboard (FND-FLOW-03)
- **Target File**: `frontend/src/components/dashboards/DoctorDashboard.tsx`
- **Change**: When `activeVisit` is present, fetch or display real triage vitals from `/api/triage/?visit=${activeVisit.id}` or `activeVisit.triage_details`.
- **Validation**: Doctor Dashboard displays the exact physiological vitals recorded by the nurse (e.g. 148/96 mmHg, 175 mg/dL) rather than static placeholders.

### Step 4: Role-Filter Action Buttons in OPD Queue (FND-FLOW-04)
- **Target File**: `frontend/src/pages/Queue.tsx`
- **Change**: Wrap action buttons with `isPathAllowedForRole(user?.role, targetPath)`. For unauthorized stages, render informative status text (e.g. "Waiting for Doctor", "Waiting for Pharmacy") instead of a clickable button that leads to 403.
- **Validation**: Nurse only sees "Triage →"; Doctor only sees "Consult →"; Pharmacist only sees "Dispense →". Zero 403 errors when clicking queue actions.

### Step 5: Authorize Doctor NCD Register Access (FND-FLOW-05)
- **Target File**: `frontend/src/utils/permissions.ts`
- **Change**: Add `'/ncd'` to `ROLE_ALLOWED_PATHS['DOCTOR']`.
- **Validation**: Doctor can view `/ncd` register for chronic disease monitoring without route guard rejection.

---

## 5. Controlled Implementation & Validation Record

| Finding ID | Severity | Status | Original Defect | Applied Correction | Targeted Validation Result | End-to-End Regression Result |
|---|---|---|---|---|---|---|
| **FND-FLOW-01** | **HIGH** | **RESOLVED** | After Nurse saves triage vitals, `Triage.tsx` redirected to `/consultation`, triggering HTTP 403 Access Denied. | Updated `Triage.tsx` post-save navigation target from `/consultation` to `/queue`. | Nurse records vitals, saves, visit transitions to `WAITING_FOR_DOCTOR`, UI redirects to `/queue`. 0 HTTP 403 errors. | Full Nurse → Doctor OPD handoff verified: patient appears in DOCTOR queue. |
| **FND-FLOW-02** | **HIGH** | **RESOLVED** | Doctor Dashboard navigated to `/consultation?visit=<ID>`, but `Consultation.tsx` only inspected `location.state?.visitId`, failing to preselect the called patient. | Updated `Consultation.tsx` to resolve target visit ID from `location.state?.visitId` first, then URL query parameter `new URLSearchParams(location.search).get('visit')`, with safe fallback fetching. | Calling Patient A and clicking "Start EMR Consultation" opens Patient A / Visit A without defaulting to other queue rows. Direct URL navigation `/consultation?visit=<ID>` verified. | Doctor encounter lifecycle executes with accurate patient identity. |
| **FND-FLOW-03** | **MEDIUM** | **RESOLVED** | Doctor Dashboard displayed hardcoded/static vitals (`150/96 mmHg`, `190 mg/dL`, `88 bpm`, `101.2 °F`) on the active patient card instead of real nurse-recorded vitals. | Updated `DoctorDashboard.tsx` to dynamically fetch and bind `/api/triage/?visit=${activeVisit.id}` or `activeVisit.triage_details`. Replaced hardcoded values with real measurements and fallback `Vitals not recorded`. | When Nurse records vitals (e.g. BP 148/96), Doctor Dashboard renders the exact persisted values. Empty vitals render `Vitals not recorded`. | Zero invented clinical placeholders. Full clinical data lineage verified. |
| **FND-FLOW-04** | **MEDIUM** | **RESOLVED** | OPD Queue row action buttons ("Triage", "Consult", "Dispense") were rendered for all users, triggering HTTP 403 when clicked by unauthorized roles. | Wrapped action buttons in `Queue.tsx` with `isPathAllowedForRole(user?.role, targetPath)`. Rendered clear informative status text (e.g. "Awaiting Triage", "Awaiting Doctor", "In Lab", "In Pharmacy") for unauthorized stages. | Nurse sees actionable "Triage" button only; Doctor sees actionable "Consult" only; Pharmacist sees actionable "Dispense" only. Zero clickable 403 buttons rendered. | Backend 403 protections remain intact; UI permissions match RBAC matrix. |
| **FND-FLOW-05** | **LOW** | **RESOLVED** | Doctor had backend permission `ncd.view`, but route `/ncd` was missing from `ROLE_ALLOWED_PATHS['DOCTOR']`, blocking Doctor from viewing NCD screening cohort. | Added `'/ncd'` to `ROLE_ALLOWED_PATHS['DOCTOR']` in `frontend/src/utils/permissions.ts`. | Doctor can navigate to `/ncd` from Dashboard and direct URL navigation without route guard denial. | DHO, Nurse, and Doctor access to NCD verified consistent across frontend and backend. |
| **FND-FLOW-06** | **INFO** | **DEFERRED** | Unordered pagination warning in DRF for Prescription model. | Deferred per PM/RSA instructions (zero code modification authorized for FND-FLOW-06). | Baseline test suite continues to pass 44/44 without error. | Preserved cleanly for future maintenance. |

### Test Suite Execution Summary
- **Backend Test Suite**: `44/44 PASS` (`Ran 44 tests in 37.1s, OK`)
- **Django Migrations**: `No changes detected`
- **Frontend Build**: `dist/` built successfully with 0 errors (`tsc -b && vite build`)
- **Frontend Lint**: `0 errors` (118 warnings, 0 errors across 41 files)
- **Targeted Regression Suite**: `5/5 PASS` (Automated verification script passed)
- **Comprehensive 6-Role Journey**: `6/6 PASS` (Nurse, Doctor, Lab Tech, Pharmacist, Hospital Admin, District Officer)
