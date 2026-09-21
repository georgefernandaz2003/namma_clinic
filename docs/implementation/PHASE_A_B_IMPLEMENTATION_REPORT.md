# Namma Clinic — Phase A & Phase B Implementation Report

**Document Reference**: `NC-IMPL-PHASE-AB-001`  
**Execution Scope**: Phase A (RBAC / DHO Route Access) & Phase B (Data Integrity & KPI Data Lineage)  
**Target Repository**: `georgefernandaz2003/namma_clinic`  
**Development Branch**: `feature/namma-clinic-demo-data-model`  
**Status**: Completed & Verified  

---

## 1. Executive Summary

This report documents the end-to-end technical remediation of the Namma Clinic digital platform across **Phase A** (Role-Based Access Control and DHO Route Access) and **Phase B** (Data Integrity and KPI Data Lineage). 

All implementations strictly follow the non-expansion constraint:
- **No Product Scope Expansion**: Phase C (Epidemic Surveillance Module) and Phase D (Maternal & Child Module) remain deferred.
- **Maternal & Child Complete Removal**: All references, routes, navigation elements, and prototype views for Maternal & Child have been completely excised from the frontend codebase. No mock/prototype banner was created.
- **Relational Integrity**: Established relational integrity using `models.SET_NULL, null=True, blank=True` for foreign key cascades, preventing data loss on formulary modifications while ensuring non-null linkages during live operations.
- **Elimination of Mock Fallbacks**: Hardcoded dashboard fallbacks (`or 14`, `or todays_opd`) and client-side pagination slicing were eliminated and replaced with authoritative, scoped SQL aggregations.
- **Negative Security Verification**: Full suite of negative security tests proving that administrative supervisor roles (e.g., `DISTRICT_OFFICER`) are granted strictly read-only visibility and are programmatically blocked from mutating patient or clinical encounter state.

---

## 2. Problems Addressed & Technical Remediations

### 2.1 RBAC & DHO Route Access (Phase A)
* **Problem**: Users with the `DISTRICT_OFFICER` role experienced HTTP `403 Forbidden` errors when attempting to navigate to `/patients`, `/ncd`, and `/surveillance`. The backend permissions matrix omitted required read permissions (`'ncd.view'`, `'surveillance.view'`, `'triage.view'`, `'patients.view'`), while the frontend router blocked navigation in `ROLE_ALLOWED_PATHS`.
* **Remediation**:
  1. Updated `backend/apps/accounts/permissions.py` to grant `DISTRICT_OFFICER` read permissions across all monitoring domains (`patients.view`, `ncd.view`, `surveillance.view`, `triage.view`, `reports.view`, `referrals.view`).
  2. Implemented strict mutation safeguards: Updated `PatientViewSet`, `NCDRecordViewSet`, `DiseaseCaseViewSet`, `ConsultationViewSet`, `PrescriptionViewSet`, `DispenseMedicineView`, and `ReferralViewSet` to block `DISTRICT_OFFICER` from executing `POST`, `PUT`, `PATCH`, or `DELETE` requests.
  3. Added `[permissions.IsAuthenticated, HasPermission, HasFacilityScope]` to `NCDRecordViewSet` and `DiseaseCaseViewSet`.
  4. Updated `frontend/src/utils/permissions.ts` to add `'/patients'`, `'/ncd'`, and `'/surveillance'` to `ROLE_ALLOWED_PATHS['DISTRICT_OFFICER']`.

### 2.2 Complete Removal of Maternal & Child
* **Problem**: The system had an un-activated, dummy `MaternalChild.tsx` page exposed in the nurse's navigation menu and application routing, violating demo integrity.
* **Remediation**:
  1. Completely deleted `frontend/src/pages/MaternalChild.tsx`.
  2. Removed `'/maternal-child'` route from `frontend/src/App.tsx`.
  3. Removed the Maternal & Child navigation item from `frontend/src/layouts/DashboardLayout.tsx`.
  4. Removed `'/maternal-child'` from `ROLE_ALLOWED_PATHS` in `frontend/src/utils/permissions.ts`.
  5. Adhered strictly to the directive: **Did not create any prototype or "under construction" banner**.

### 2.3 PrescriptionItem $\rightarrow$ MedicineMaster Relational Linkage (Phase B)
* **Problem**: `PrescriptionItem` stored drug names as free-text `medicine_name` strings without a foreign key to `MedicineMaster`. Consequently:
  - Prescriptions were unlinked from formulary masters.
  - Dispensation relied on string matching, creating high vulnerability to spelling differences.
  - Inventory could not track which doctor prescriptions consumed which batch.
* **Remediation**:
  1. Modified `backend/apps/consultations/models.py` to add:
     ```python
     medicine = models.ForeignKey(
         'pharmacy.MedicineMaster',
         on_delete=models.SET_NULL,
         null=True,
         blank=True,
         related_name='prescription_items'
     )
     ```
  2. Generated and applied schema migration `0002_prescriptionitem_medicine.py`.
  3. Executed data migration `0003_populate_prescriptionitem_medicine.py` which mapped all existing `PrescriptionItem` records in `backend/db.sqlite3` to their respective `MedicineMaster` rows.
  4. Updated `ConsultationViewSet.create` and `PrescriptionItemSerializer` in `backend/apps/consultations/views.py` to accept `medicine_id`, resolve `MedicineMaster`, and set both `medicine` and `medicine_name`.
  5. Updated `DispenseMedicineView` in `backend/apps/pharmacy/views.py` to allocate FEFO inventory batches using `p_item.medicine` directly.
  6. Updated `frontend/src/pages/Consultation.tsx` to load formulary medicines from `/api/pharmacy/medicines/` and submit `medicine_id`.

### 2.4 Referral $\rightarrow$ Encounter Linkage (Phase B)
* **Problem**: The `Referral` model existed in isolation from the clinical encounter (`Visit` and `Consultation`), making it impossible to audit which consultation generated an outbound transfer.
* **Remediation**:
  1. Modified `backend/apps/referrals/models.py` to add:
     ```python
     visit = models.ForeignKey('visits.Visit', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
     consultation = models.ForeignKey('consultations.Consultation', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
     ```
  2. Generated and applied schema migration `0002_referral_consultation_referral_visit.py`.
  3. Executed data migration `0003_populate_referral_encounter.py` linking legacy referral record #16 to Visit #40 and Consultation #25.
  4. Updated `ReferralViewSet.create` in `backend/apps/referrals/views.py` to accept `visit_id` and `consultation_id`.
  5. Updated `frontend/src/pages/Consultation.tsx` to include `visit_id` and `consultation_id` when raising cross-facility referrals.

### 2.5 KPI Fallback Elimination & Lineage Correction (Phase B)
* **Problem 1 (`or 14`)**: In `backend/apps/reports/views.py`, the `total_medicines` KPI contained a hardcoded fallback:
  ```python
  # OLD BUG:
  total_medicines = MedicineBatch.objects.filter(...).values('medicine').distinct().count() or 14
  ```
  If a facility had 0 active batches, it erroneously reported 14.
  * **Fix**: Removed `or 14`. Now returns exact count (0 if empty).
* **Problem 2 (`or todays_opd`)**: In `backend/apps/reports/views.py`, `registered_today` fell back to `todays_opd`:
  ```python
  # OLD BUG:
  registered_today = Patient.objects.filter(registered_at_facility=fac, registration_date=today).count() or todays_opd
  ```
  This conflated check-in footfall with new citizen registration.
  * **Fix**: Removed `or todays_opd`. Now returns the exact count of new registrations for the day.
* **Problem 3 (Doctor Dashboard Follow-Up Mislabeling)**:
  `DoctorDashboard.tsx` displayed `summary.referrals_summary.completed` in the metric card titled "Follow-ups", showing completed outbound hospital transfers instead of scheduled patient review dates.
  * **Fix**: Replaced with `summary?.followups_summary?.due_today ?? summary?.kpis?.followups_due ?? 0`, backed directly by `referrals_followup`.
* **Problem 4 (Pharmacist & Lab Dashboard Pagination Slicing)**:
  `PharmacistDashboard.tsx` and `LabTechnicianDashboard.tsx` computed summary counts by running `.filter(...)` on the first page of results (limited to 50 rows).
  * **Fix**: Added authoritative summary endpoints in `reports/views.py`:
    - `summary.pharmacy_summary`: `{ total_prescriptions, pending_prescriptions, dispensed_today }`
    - `summary.lab_summary`: `{ total_orders, pending_orders, completed_today }`
    - `summary.followups_summary`: `{ total_followups, due_today, overdue }`
    Updated frontend dashboards to bind directly to these backend counts.

---

## 3. Client Challenge Audit Matrix

The following matrix documents every critical observation, audit challenge, and architectural inquiry regarding the platform's reliability and compliance:

| Ref | Audit Challenge / Question | Risk / Impact Prior to Remediation | Remediation Implemented | Verification & Evidence |
| :--- | :--- | :--- | :--- | :--- |
| **CCA-01** | **Why do District Health Officers receive 403 Forbidden errors when accessing the Patient Directory or NCD registries?** | Operational paralysis for municipal health supervisors unable to review population health status or monitor chronic disease cohorts. | Added missing permissions to `ROLE_PERMISSIONS['DISTRICT_OFFICER']` and permitted routes in `ROLE_ALLOWED_PATHS`. Preserved read-only scope. | Automated test `test_dho_can_view_patients_read_only` passes with HTTP 200 OK. Frontend navigation loads successfully. |
| **CCA-02** | **Can District Officers or administrative auditors accidentally alter clinical notes, dispense drugs, or create patients?** | Integrity violation of medical encounters and chain of custody; administrative roles contaminating clinical datasets. | Enforced strict mutation blocking in DRF viewsets (`create`, `update`, `partial_update`, `destroy`) rejecting `DISTRICT_OFFICER` with HTTP 403 Forbidden. | 6 automated negative tests (`test_dho_cannot_create_*`) confirm HTTP 403 Forbidden on all state mutations. |
| **CCA-03** | **Why did the pharmacy inventory report always display 14 active medicines even when a clinic stockroom was completely empty?** | Regulatory misreporting; false impression of essential drug availability risking stockouts going undetected by procurement officers. | Removed the `or 14` hardcoded Python fallback in `DashboardSummaryView`. Count is derived purely from `MedicineBatch` filtered by unexpired, non-zero stock. | Automated test `test_reports_no_hardcoded_fallbacks` proves count drops to exact integer (0 when unstocked). |
| **CCA-04** | **Why did daily patient registration counts duplicate Outpatient Department (OPD) queue footfall?** | Misleading population demographic statistics; returning patients counted as newly registered citizens. | Removed `or todays_opd` fallback. `registered_today` now strictly counts `Patient` records with `registration_date == today`. | Automated test confirms `registered_today == 0` when existing patients check in without new citizens registering. |
| **CCA-05** | **How does the system guarantee that dispensing drugs depletes the correct batch if drug names are entered with slight typographic differences?** | Free-text string matching between `PrescriptionItem.medicine_name` and `MedicineMaster.brand_name` caused inventory allocation failures or wrong drug deductions. | Added foreign key `PrescriptionItem.medicine` $\rightarrow$ `MedicineMaster`. Dispensing logic now queries batches matching `batch.medicine == p_item.medicine`. | Migration `0002_prescriptionitem_medicine` + `0003_populate_prescriptionitem_medicine`. Model test `test_prescription_item_medicine_foreign_key_relationship` passes. |
| **CCA-06** | **What prevents historic prescription and encounter records from being corrupted or deleted if a formulary item is discontinued?** | Cascading `CASCADE` deletes would purge patient prescription history upon drug master retirement. | Implemented `on_delete=models.SET_NULL, null=True, blank=True` on `PrescriptionItem.medicine` while preserving immutable `medicine_name` snapshot. | Schema migration `0002_prescriptionitem_medicine` specifies `SET_NULL`. Preserves historical clinical audit trail. |
| **CCA-07** | **Why were completed patient hospital referrals being displayed to Medical Officers as "Follow-ups Due"?** | Clinical confusion: Doctors could not distinguish between outbound referrals transferred to tertiary hospitals and routine chronic disease follow-up appointments. | Rewired `DoctorDashboard.tsx` "Follow-ups" metric card to `summary.followups_summary.due_today` which aggregates `referrals_followup`. | Verified in `DoctorDashboard.tsx` and tested via `test_dashboard_authoritative_summaries`. |
| **CCA-08** | **If an OPD clinic logs hundreds of prescriptions or lab orders, why did the pharmacy and lab metric cards cap at 50?** | Dashboard metric cards calculated `.filter()` counts client-side on paginated API payloads (capped at `page_size = 50`). | Implemented server-side authoritative counts in `summary.pharmacy_summary` and `summary.lab_summary`. Dashboards consume full database aggregates. | Verified in `PharmacistDashboard.tsx` and `LabTechnicianDashboard.tsx`. Zero dependency on paginated table limits. |
| **CCA-09** | **Can cross-facility referrals be traced back to the specific consultation and clinical notes that recommended the transfer?** | Disconnected referrals lacked clinical context, requiring clinicians to manually search through past visit notes. | Added `visit` and `consultation` foreign keys (`on_delete=models.SET_NULL`) to `Referral` model. Updated referral creation flow to link both. | Schema migration `0002` + Data migration `0003`. Verified via `test_referral_encounter_linkage`. |
| **CCA-10** | **Why was an un-activated Maternal & Child navigation link visible in the clinic interface?** | Prototype illusion; misled users into expecting functional antenatal/pediatric workflows. | Completely deleted `MaternalChild.tsx`, routes, and navigation items without adding placeholder banners, respecting scope boundaries. | Zero dead links in frontend build; `npm run build` succeeds cleanly. |

---

## 4. Automated Test Suite & Negative Security Testing

An automated test suite was constructed in `backend/apps/accounts/tests.py` containing 12 unit, regression, and negative security tests.

### 4.1 Test Cases Executed

```python
apps.accounts.tests.PhaseABSecurityAndDataIntegrityTests
  ├── test_dho_can_view_patients_read_only                      [PASS] - 200 OK on GET /api/patients/
  ├── test_dho_cannot_create_patient                            [PASS] - 403 FORBIDDEN on POST /api/patients/ (Negative)
  ├── test_dho_cannot_create_consultation                       [PASS] - 403 FORBIDDEN on POST /api/consultations/ (Negative)
  ├── test_dho_cannot_create_referral                           [PASS] - 403 FORBIDDEN on POST /api/referrals/ (Negative)
  ├── test_dho_cannot_dispense_medicine                         [PASS] - 403 FORBIDDEN on POST /api/pharmacy/dispense/ (Negative)
  ├── test_dho_cannot_create_ncd_record                         [PASS] - 403 FORBIDDEN on POST /api/ncd/ (Negative)
  ├── test_dho_cannot_create_disease_case                       [PASS] - 403 FORBIDDEN on POST /api/surveillance/cases/ (Negative)
  ├── test_unauthenticated_requests_blocked                     [PASS] - 401 UNAUTHORIZED on unauthenticated GET (Negative)
  ├── test_prescription_item_medicine_foreign_key_relationship  [PASS] - DB FK linkage to MedicineMaster with SET_NULL
  ├── test_referral_encounter_linkage                           [PASS] - DB FK linkage to Visit & Consultation with SET_NULL
  ├── test_reports_no_hardcoded_fallbacks                       [PASS] - 0 medicines returned when inventory empty (No 'or 14')
  └── test_dashboard_authoritative_summaries                    [PASS] - Correct structure & exact counts in pharmacy & followups
```

### 4.2 Test Suite Execution Output

```bash
Found 12 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
............
----------------------------------------------------------------------
Ran 12 tests in 15.011s

OK
Destroying test database for alias 'default'...
```

---

## 5. Database vs API KPI Lineage Validation

To verify analytical consistency across the persistent database (`backend/db.sqlite3`), the following audit compares direct SQL counts against the API endpoint (`/api/dashboard/summary/`) under both Facility (Facility #1: Urban Primary Health Centre, Ward 12) and District scope (District #1: Central District):

| KPI Identifier | Formal SQL Definition | Raw DB Count | API Value | Discrepancy |
| :--- | :--- | :---: | :---: | :---: |
| **Total Registered Patients (District)** | `COUNT(p.id) WHERE p.facility_id IN (1, 2)` | **34** | **34** | **0.00%** |
| **OPD Footfall (Facility 1, Today)** | `COUNT(DISTINCT v.patient_id) WHERE v.facility_id=1` | **2** | **2** | **0.00%** |
| **Waiting for Doctor (Facility 1)** | `COUNT(v.id) WHERE status='WAITING_FOR_DOCTOR'` | **2** | **2** | **0.00%** |
| **Triaged Queue (Facility 1)** | `COUNT(v.id) WHERE status='TRIAGED'` | **0** | **0** | **0.00%** |
| **Total Consultations Today (Facility 1)** | `COUNT(c.id) WHERE v.opd_date=today` | **0** | **0** | **0.00%** |
| **Pending Diagnostic Lab Orders (Facility 1)**| `COUNT(lo.id) WHERE status IN ('ORDERED', 'SAMPLE_COLLECTED')` | **0** | **0** | **0.00%** |
| **Pharmacy Dispensations Today (Facility 1)** | `COUNT(p.id) WHERE status='DISPENSED' AND date=today` | **0** | **0** | **0.00%** |
| **Total Active Medicines in Stock (Facility 1)**| `COUNT(DISTINCT mb.medicine_id) WHERE qty > 0 AND unexpired` | **4** | **4** | **0.00%** |
| **Low Stock Alert Items (Facility 1)** | `COUNT(DISTINCT m.id) WHERE sum(qty) <= m.reorder_level` | **2** | **2** | **0.00%** |
| **Pending Referrals (Facility 1)** | `COUNT(r.id) WHERE status IN ('CREATED', 'ACCEPTED', ...)` | **0** | **0** | **0.00%** |
| **Follow-ups Due Today (Facility 1)** | `COUNT(fu.id) WHERE due_date=today AND status='PENDING'` | **0** | **0** | **0.00%** |
| **Active NCD Cohort (Facility 1)** | `COUNT(DISTINCT n.patient_id) WHERE treatment_status='UNDER_TREATMENT'`| **0** | **0** | **0.00%** |

*Result*: **100% Data Lineage Alignment across all 12 KPIs. Discrepancy Rate = 0.00%.**

---

## 6. Current-Application Cleanup Summary

The following cleanup actions were completed:
1. **Removed Prototype Files**: Deleted `frontend/src/pages/MaternalChild.tsx`.
2. **Removed Dead Code & Scaffolding**: Eliminated unused imports in modified frontend components (`Consultation.tsx`, `DoctorDashboard.tsx`, `PharmacistDashboard.tsx`, `LabTechnicianDashboard.tsx`).
3. **TypeScript Compilation Check**: Ran `npm run build` (`tsc -b && vite build`) — verified 0 compilation errors and clean production bundle generation.
4. **Scratch File Cleanup**: Removed temporary verification scripts (`scripts/check_db.py`, `scripts/inspect_data.py`, `scripts/validate_kpis.py`) and temporary backup databases.

---

## 7. Conclusion & Scope Compliance

Phase A and Phase B implementations have restored end-to-end role security, database referential integrity, and analytical fidelity to the Namma Clinic platform. The platform is ready for demonstration without mock fallback anomalies or permission failures.
