# Namma Clinic — Phase C.1 Implementation Report
**Demo Blockers, Security Alignment & Critical Data Integrity**

**Branch:** `feature/namma-clinic-demo-data-model`  
**Baseline Commit:** `e92ed9bfd4bc881d8b896ea4943773bf7d81c041`  
**Execution Date:** September 21, 2026  
**Implementation Engineer:** Antigravity (PM + RSA Review Approved)  
**Status Gate:** PASSED (26/26 backend tests passed, frontend build clean, 6/6 demo journeys verified)

---

## 1. Executive Summary

Phase C.1 strictly targeted the approved remediation scope: critical route blockers, role-based access control (RBAC) misalignments, clinical re-save exceptions, unhandled reporting exports, and cross-encounter data corruption. Out-of-scope functional redesigns (teleconsultation, prescription statuses, lab orders, inventory ledger) were preserved without scope creep.

| Finding ID | Severity | Description | Status | Verification |
|---|---|---|---|---|
| **FND-01** | `CRITICAL` | Route guard failures (`/ars`, `/quality`, `/integrations`) | **IMPLEMENTED** | HTTP 200 on all endpoints for DHO & Admin |
| **FND-02** | `CRITICAL` | Doctor & Hospital Admin blocked from queue operations | **IMPLEMENTED** | Granular queue permissions & queue calling restrictions |
| **FND-03** | `CRITICAL` | FollowUp #9 cross-encounter foreign key contradiction | **IMPLEMENTED** | Clean validation, serializer validation, seed & DB corrected |
| **FND-04** | `CRITICAL` | Silent data fall-through in CSV Export engine | **IMPLEMENTED** | Explicit handlers for NCD & Disease Surveillance CSVs |
| **FND-05** | `HIGH` | Hardcoded localhost URL in `Reports.tsx` | **IMPLEMENTED** | Uses configured Axios client with `responseType: 'blob'` |
| **FND-07** | `HIGH` | OneToOne database crash on triage/consultation re-submission | **IMPLEMENTED** | `get → update` semantics returning HTTP 200 on re-save |

---

## 2. Baseline Status

- **Git Branch:** `feature/namma-clinic-demo-data-model`
- **Baseline Commit:** `e92ed9bfd4bc881d8b896ea4943773bf7d81c041`
- **Initial Test Suite:** 13 passed in `apps.accounts`
- **Frontend Build Baseline:** Vite v8.2.2 bundle clean
- **Safety Precaution:** Full SQLite backup taken at `backend/db.sqlite3.bak_phase_c1` before data modifications.

---

## 3. Detailed Changes by Finding

### FND-01: Route Guard Failures (`/ars`, `/quality`, `/integrations`)
- **Backend Permissions (`backend/apps/accounts/permissions.py`):**
  - Added permissions `'ars.view'`, `'quality.view'`, and `'integrations.view'` to `DISTRICT_OFFICER` and `HOSPITAL_ADMIN`.
- **Frontend Permissions (`frontend/src/utils/permissions.ts`):**
  - Added `/ars`, `/quality`, `/integrations` to `ROLE_ALLOWED_PATHS['DISTRICT_OFFICER']`.
  - Added `/ars`, `/quality`, `/integrations` to `ROLE_ALLOWED_PATHS['HOSPITAL_ADMIN']`.
  - Added `'ars.view'`, `'quality.view'`, `'integrations.view'` to `ROLE_PERMISSIONS` in TypeScript.

### FND-02: Doctor Queue 403 & Least-Privilege Granular Permissions
- **Granular Queue Permissions (`backend/apps/accounts/permissions.py`):**
  - Added `'queue.call_next'` and `'queue.transition'` to `DOCTOR`, `NURSE`, and `HOSPITAL_ADMIN`.
  - Added `'queue.create'` to `NURSE` and `HOSPITAL_ADMIN`.
  - Kept `DOCTOR` strictly prohibited from arbitrary queue creation or mutation outside the clinical consultation workflow.
  - Kept `DISTRICT_OFFICER` strictly read-only (`queue.view`).
- **Granular Action Mapping (`backend/apps/visits/views.py`):**
  - In `VisitViewSet`:
    - `call_next_patient` mapped to `'queue.call_next'`.
    - `transition_status` mapped to `'queue.transition'`.
    - `create` mapped to `'queue.create'`.
  - Enforced role isolation inside `call_next_patient`:
    - `DOCTOR` is restricted to calling from the `DOCTOR` queue (calling `TRIAGE` returns HTTP 403).
    - `NURSE` is restricted to calling from the `TRIAGE` queue.

### FND-03: FollowUp Cross-Encounter Integrity
- **Authoritative Relationship:**
  - Clinical encounter chain: `Patient → Visit → Consultation → Referral → FollowUp`.
  - Enforced rule: A `FollowUp` must belong to the exact same `patient` and `visit` as its source `referral`.
- **Model Validation (`backend/apps/referrals/models.py`):**
  - Added `clean()` and updated `save()` on `FollowUp`:
    ```python
    if self.referral:
        if self.patient_id != self.referral.patient_id:
            raise ValidationError("FollowUp patient must match Referral patient.")
        if self.referral.visit_id and self.visit_id != self.referral.visit_id:
            raise ValidationError("FollowUp visit must match Referral visit.")
        if self.referral.source_facility_id and self.facility_id != self.referral.source_facility_id:
            raise ValidationError("FollowUp facility must match Referral source facility.")
    ```
- **API & Serializer Validation (`backend/apps/referrals/views.py`):**
  - In `FollowUpSerializer.validate()`: Enforced matching `visit`, `patient`, and `facility` against `referral`.
  - In `ReferralViewSet.respond()`: Automatically sets `visit=referral.visit` when creating follow-up on referral response.
- **Data Correction & Seed Update:**
  - Database row: Updated `FollowUp #9` from `visit_id = 35` to `visit_id = 40` (matching `Referral #16`'s `visit_id = 40`).
  - Seed file: Updated `backend/apps/accounts/management/commands/seed_demo.py` line 601 to use `visit=ref_ramesh.visit`.

### FND-04: Public Health CSV Export Fall-Through
- **Explicit Handlers (`backend/apps/reports/views.py`):**
  - Replaced fallback `else:` block with explicit handlers for each report type:
    - `type == 'ncd'`: Queries `apps.ncd.models.NCDRecord` with facility scoping; outputs Patient ID, Patient Name, Facility, Screening Date, Hypertension Diagnosed, Diabetes Diagnosed, Risk Level, Control Status, Last BP, Last Glucose, Next Followup Due.
    - `type == 'surveillance'`: Queries `apps.surveillance.models.DiseaseCase` with facility scoping; outputs Disease Name, Patient Name, Facility, Ward, Report Date, Severity, Status, Notes.
    - `type == 'patients'`: Queries `apps.patients.models.Patient` master directory.
  - Added `HasPermission` and enforced `'reports.export'` permission on `CSVExportView`.

### FND-05: Hardcoded Localhost API URL
- **Frontend API Config (`frontend/src/services/api.ts`):**
  - Dynamic `baseURL` configured using `(import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000/api/'`.
- **Frontend Reports Component (`frontend/src/pages/Reports.tsx`):**
  - Replaced browser `fetch('http://localhost:8000/api/reports/export/...')` with `api.get('reports/export/?type=...', { responseType: 'blob' })`.
  - Employs object URL blob download adhering to existing Axios interceptors and staging configurations.

### FND-07: Clinical Re-Save HTTP 500 Prevention
- **Triage Vitals (`backend/apps/triage/views.py`):**
  - Implemented `get → update` semantics in `TriageVitalsViewSet.create()`:
    - If `TriageVitals` exists for `visit_id`, update the existing record and return HTTP 200 OK.
    - If new, create record and return HTTP 201 Created.
  - Added `triage.view`, `triage.create`, and `triage.update` permissions to `DOCTOR` in both backend and frontend so doctors can inspect and re-save triage vitals.
- **Consultation (`backend/apps/consultations/views.py`):**
  - Implemented `get → update` semantics in `ConsultationViewSet.create()`:
    - If `Consultation` exists for `visit_id`, update existing record and return HTTP 200 OK.
    - If new, create record and return HTTP 201 Created.
    - Avoids unhandled `UNIQUE constraint failed: consultations_consultation.visit_id`.

---

## 4. Modified Files Summary

| File | Type | Changes Made |
|---|---|---|
| `backend/apps/accounts/permissions.py` | Python | Granular queue permissions (`queue.call_next`, `queue.transition`, `queue.create`), ARS/Quality/Integrations perms, DOCTOR triage perms |
| `backend/apps/visits/views.py` | Python | Mapped granular permissions on action decorators; enforced role queue calling isolation |
| `backend/apps/triage/views.py` | Python | `get → update` re-save semantics returning HTTP 200 on existing vitals |
| `backend/apps/consultations/views.py` | Python | `get → update` re-save semantics returning HTTP 200 on existing consultation |
| `backend/apps/referrals/models.py` | Python | `clean()` and `save()` cross-encounter validation against referral |
| `backend/apps/referrals/views.py` | Python | `FollowUpSerializer.validate()` cross-encounter integrity; `ReferralViewSet.respond()` sets `visit` |
| `backend/apps/reports/views.py` | Python | Explicit NCD and Surveillance CSV export handlers with facility scoping and permission check |
| `backend/apps/accounts/management/commands/seed_demo.py` | Python | Set `visit=ref_ramesh.visit` on FollowUp seed generation |
| `backend/apps/accounts/tests.py` | Python | Added 13 comprehensive regression test cases covering Phase C.1 |
| `frontend/src/services/api.ts` | TypeScript | Dynamic `VITE_API_BASE_URL` fallback |
| `frontend/src/utils/permissions.ts` | TypeScript | Added `/ars`, `/quality`, `/integrations` to DHO/Admin; added queue & triage perms |
| `frontend/src/pages/Reports.tsx` | TypeScript React | Replaced hardcoded `localhost:8000` with Axios `api.get` blob download |
| `docs/quality/PHASE_C_REMEDIATION_BACKLOG.md` | Markdown | Marked FND-01, FND-02, FND-03, FND-04, FND-05, FND-07 as `IMPLEMENTED` |

---

## 5. Database Migrations & Data Corrections

- **Django Migrations:** No schema altering changes were required (`python backend/manage.py makemigrations --check --dry-run` reports `No changes detected`).
- **Database Backup:** Backed up to `backend/db.sqlite3.bak_phase_c1`.
- **Database Row Corrections:**
  - `FollowUp #9`:
    - Before: `visit_id = 35`, `referral_id = 16`, `patient_id = 182`, `facility_id = 68`.
    - After: `visit_id = 40`, `referral_id = 16`, `patient_id = 182`, `facility_id = 68`.
    - Referral #16: `visit_id = 40`, `patient_id = 182`, `source_facility_id = 68`.
    - Relationship is now 100% consistent across patient, visit, and facility.

---

## 6. Verification and Test Results

### Automated Regression Test Suite
- Command: `python backend/manage.py test apps.accounts`
- Total Tests: **26 tests** (13 baseline + 13 Phase C.1 regression tests)
- Outcome: **26 passed, 0 failures, 0 errors (OK)**
- Duration: 88.0 seconds

Tests added for Phase C.1:
1. `test_fnd01_dho_and_admin_have_access_to_ars_quality_and_integrations`: Verifies DHO & Admin access to `/api/ars/meetings/`, `/api/quality/checklists/`, `/api/quality/waste-logs/`, `/api/integrations/`.
2. `test_fnd01_doctor_and_nurse_blocked_from_ars_and_integrations`: Verifies operational roles receive HTTP 403 on administrative routes.
3. `test_fnd02_doctor_can_call_next_patient_in_doctor_queue`: Verifies Doctor calling next waiting patient transitions visit to `IN_CONSULTATION`.
4. `test_fnd02_doctor_cannot_call_triage_queue`: Verifies Doctor receives HTTP 403 when attempting to call from the `TRIAGE` queue.
5. `test_fnd02_nurse_can_call_triage_queue_and_transition_status`: Verifies Nurse calling next waiting patient transitions visit to `IN_TRIAGE`.
6. `test_fnd02_nurse_cannot_call_doctor_queue`: Verifies Nurse receives HTTP 403 when attempting to call from the `DOCTOR` queue.
7. `test_fnd02_dho_cannot_call_next_or_transition`: Verifies DHO receives HTTP 403 on queue mutations.
8. `test_fnd04_ncd_export_returns_ncd_data_not_patient_master`: Verifies NCD export returns `NCDRecord` CSV with disease columns.
9. `test_fnd04_surveillance_export_returns_disease_case_data`: Verifies Surveillance export returns `DiseaseCase` CSV with outbreak columns.
10. `test_fnd04_patient_export_returns_patient_demographics`: Verifies Patient export returns `Patient` demographic CSV.
11. `test_fnd07_triage_resave_updates_existing_record_without_500`: Verifies re-saving triage returns HTTP 200 without HTTP 500.
12. `test_fnd07_consultation_resave_updates_existing_record_without_500`: Verifies re-saving consultation returns HTTP 200 without HTTP 500.
13. `test_fnd03_followup_cross_encounter_validation`: Verifies model and serializer validation rejects mismatched `patient_id` or `visit_id`.

### Frontend Build
- Command: `npm run build` in `frontend/`
- Outcome: **Vite build clean, 0 TypeScript errors**
- Bundle: `dist/index.html` (0.47 kB), `dist/assets/index-DVy0SpeJ.js` (708.51 kB).

---

## 7. Client Demo Journey Verification

All 6 required end-to-end client journeys were executed and passed with 0 errors:

1. **Doctor Queue → Call Next Patient → Consultation:**
   - Doctor authenticates and views OPD queue.
   - Executes `POST /api/visits/call-next/` with `queue='DOCTOR'`.
   - Highest priority patient atomically locked; status transitions from `WAITING_FOR_DOCTOR` to `IN_CONSULTATION`.
   - Calling `queue='TRIAGE'` blocked with HTTP 403.
   - Result: **PASS**

2. **DHO Login → ARS, Quality, Integrations:**
   - DHO accesses `/api/ars/meetings/` (HTTP 200).
   - DHO accesses `/api/ars/members/` (HTTP 200).
   - DHO accesses `/api/quality/checklists/` (HTTP 200).
   - DHO accesses `/api/quality/waste-logs/` (HTTP 200).
   - DHO accesses `/api/integrations/` (HTTP 200).
   - Result: **PASS**

3. **DHO → NCD → Export NCD:**
   - DHO requests `GET /api/reports/export/?type=ncd`.
   - Returns HTTP 200 with `Content-Type: text/csv`.
   - Headers: `Patient ID, Patient Name, Facility, Screening Date, Hypertension Diagnosed, Diabetes Diagnosed, Risk Level, Control Status, Last BP, Last Glucose, Next Followup Due`.
   - Result: **PASS**

4. **DHO → Surveillance → Export Surveillance:**
   - DHO requests `GET /api/reports/export/?type=surveillance`.
   - Returns HTTP 200 with `Content-Type: text/csv`.
   - Headers: `Disease Name, Patient Name, Facility, Ward, Report Date, Severity, Status, Notes`.
   - Result: **PASS**

5. **Doctor → Existing Patient → Existing Triage/Consultation → Save Again:**
   - Doctor re-saves existing `TriageVitals` for Visit #35 → Returns HTTP 200 (updated pulse from 84 to 76).
   - Doctor re-saves existing `Consultation` for Visit #35 → Returns HTTP 200 (updated notes).
   - Zero HTTP 500 errors; zero unhandled `IntegrityError` exceptions.
   - Result: **PASS**

6. **FollowUp → Referral → Visit → Patient Consistency Check:**
   - Checked all `FollowUp` rows against linked `Referral` records.
   - FollowUp #9: `patient=182, visit=40, facility=68`.
   - Referral #16: `patient=182, visit=40, source_facility=68`.
   - 100% encounter consistency verified.
   - Result: **PASS**

---

## 8. Remaining Phase C Remediation Backlog Findings

The following 12 findings remain for future controlled phases:

1. `FND-06` (HIGH): Teleconsultation UI disconnected / simulation banner.
2. `FND-08` (HIGH): Patient #216 null facility/district seed data.
3. `FND-09` (MEDIUM): Triage seed record desynchronization.
4. `FND-10` (MEDIUM): Queue state cleanup & orphan token synchronization.
5. `FND-11` (MEDIUM): Prescription status transitions & dispenser attribution.
6. `FND-12` (MEDIUM): Inventory transaction ledger alignment on dispensing.
7. `FND-13` (MEDIUM): Consultation default template text modernization.
8. `FND-14` (MEDIUM): UHID collision prevention.
9. `FND-15` (LOW): Dormant tables with 0 seed rows (Outreach, Wellness).
10. `FND-16` (LOW): Referral urgency enum normalization.
11. `FND-17` (LOW): Follow-up lifecycle completion flags.
12. `INFO`: Unused dead code files in `apps.maternal` and `apps.child`.

---

## 9. Known Risks & Technical Observations

1. **Vite Bundle Size Warning:** The production client bundle exceeds 500 kB (`708 kB`). Future frontend optimization should introduce code-splitting on lazy-loaded route components.
2. **Django Timezone Warning:** `Visit.visit_date` received a naive datetime in legacy seed data during initial test setup, raising a benign runtime warning.
3. **Pagination Ordering Warnings:** `ARSMeeting`, `QualityChecklist`, and `IntegrationConfiguration` querysets logged unordered object list warnings during DRF pagination; these models can add default `ordering = ['-id']` in an upcoming cleanup pass.
