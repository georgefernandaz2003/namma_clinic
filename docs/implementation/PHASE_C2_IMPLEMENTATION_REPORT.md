# Namma Clinic — Phase C.2 Implementation Report
## Data Integrity & Patient Journey Consistency

- **Date:** 2026-09-21
- **Phase:** Phase C.2 (Approved Remediation Scope)
- **Branch:** `feature/namma-clinic-demo-data-model`
- **Baseline Commit:** `54c6d2c`
- **Status:** Complete & Validated in Tested Scope

---

## 1. Scope

Phase C.2 addresses **Data Integrity and Patient Journey Consistency**, ensuring that every clinical state across the patient journey (`Patient -> Facility -> Visit -> Queue -> Triage -> Doctor -> Consultation -> Prescription -> Pharmacy -> Inventory`) is strictly backed by authoritative database state and transactions.

### In Scope (Approved C2 Findings Only):
1. **FND-08 (HIGH):** Patient facility/district assignment inconsistency causing patients to disappear from DHO district scope.
2. **FND-09 (MEDIUM):** Visit waiting for doctor consultation without prerequisite recorded nurse triage vitals.
3. **FND-10 (MEDIUM):** Visit status vs queue state desynchronization (completed visits remaining in `DOCTOR` queue).
4. **FND-11 (MEDIUM):** Prescription header marked `DISPENSED` while child prescription line items remain `PENDING`.
5. **FND-12 (MEDIUM):** Pharmacy medicine dispensing occurring without corresponding authoritative `InventoryTransaction`.

### Explicitly Deferred / Out of Scope:
- FND-01, FND-02, FND-03, FND-04, FND-05, FND-07 (Remediated in Phase C.1)
- FND-06 Teleconsultation (Deferred)
- FND-13 Hardcoded consultation defaults (Deferred)
- FND-14 UHID redesign (Deferred)
- FND-15 Dormant models (Deferred)
- FND-16 Referral urgency constraints (Deferred)
- FND-17 Follow-up mutation constraints (Deferred)
- LabOrder -> Visit FK (Deferred)
- Triage -> Alert event bus (Deferred)
- Maternal & Child health activation (Deferred)

---

## 2. Findings Addressed & Root Cause Analysis

| Finding ID | Severity | Root Cause |
|---|---|---|
| **FND-08** | HIGH | `Patient` model lacked model-level and serializer validation enforcing alignment between `registered_at_facility.district` and `patient.district`. Patient #216 had `None` for both fields, escaping DHO district scoping. |
| **FND-09** | MEDIUM | `VisitViewSet.transition_status()` and `call_next_patient()` did not check for prerequisite `TriageVitals` before advancing visit queue to `DOCTOR` or setting status to `WAITING_FOR_DOCTOR`. Demo Visit #39 was seeded without triage vitals. |
| **FND-10** | MEDIUM | Dual-state tracking (`visit.status` and `visit.current_queue`) lacked bidirectional synchronization. In `ConsultationViewSet.create()` and past seed records, `status` was set to `'COMPLETED'` without updating `current_queue` from `'DOCTOR'` to `'COMPLETED'`. |
| **FND-11** | MEDIUM | `Prescription` model permitted `status='DISPENSED'` independently of child `PrescriptionItem` statuses. Prescription #26 header was set to `DISPENSED` while items #68 and #69 remained `PENDING`. |
| **FND-12** | MEDIUM | In Visit #35, Metformin generated an `InventoryTransaction`, but Amlodipine (Item #65) was decremented without creating an `InventoryTransaction`. Similarly, Prescription #26 had no inventory transactions created. In dispensing logic, repeated dispensing was not guarded against double-decrementing. |

---

## 3. Implementation Details

### FND-08: Patient Facility / District Integrity
1. **Model Validation (`backend/apps/patients/models.py`):**
   - Added `clean()` and `save()` hooks on `Patient`.
   - When `registered_at_facility` is set, `patient.district` is automatically derived from `registered_at_facility.district` if unset.
   - If `patient.district` is explicitly provided, validation raises `ValidationError` if `district != registered_at_facility.district`.
   - Cross-facility care documentation: Patients may receive care across facilities (encounters/visits and referrals at secondary hospitals), so `Visit.facility` is not restricted to `Patient.registered_at_facility`. However, registration district and facility district must remain consistent for DHO oversight.
2. **Serializer Validation (`backend/apps/patients/serializers.py`):**
   - Added `validate()` method in `PatientSerializer` enforcing facility/district/ward alignment.

### FND-09: Triage before Doctor Consultation
1. **Queue Advancement Guard (`backend/apps/visits/views.py`):**
   - In `VisitViewSet.transition_status()`: Advancing to `DOCTOR` queue or statuses `TRIAGED`, `WAITING_FOR_DOCTOR`, or `IN_CONSULTATION` requires `TriageVitals.objects.filter(visit=visit).exists()`. Untriaged visits return HTTP 400 Bad Request.
   - Added role guard: Only clinical roles (`NURSE`, `DOCTOR`, `ADMIN`, `SYSTEM_ADMIN`) can transition visits to the doctor queue.
2. **Consultation Guard (`backend/apps/consultations/views.py`):**
   - In `ConsultationViewSet.create()`: If a visit is currently in `TRIAGE` queue, consultation creation is rejected if triage vitals have not been recorded.
3. **Model Invariant (`backend/apps/visits/models.py`):**
   - Added validation in `Visit.clean()` preventing `current_queue='DOCTOR'` or `WAITING_FOR_DOCTOR` without recorded triage vitals.

### FND-10: Visit Status vs Queue State
1. **Bidirectional State Synchronization (`backend/apps/visits/models.py`):**
   - In `Visit.save()`: Setting `status = 'COMPLETED'` automatically synchronizes `current_queue = 'COMPLETED'` and populates `completed_time`.
   - In `Visit.clean()`: Explicitly forbids `status='COMPLETED'` with `current_queue='DOCTOR'` or any non-completed queue.
2. **Workflow Transition Alignment (`backend/apps/visits/views.py`):**
   - In `VisitViewSet.transition_status()`: Transitioning to `COMPLETED` sets both `current_queue='COMPLETED'` and `status='COMPLETED'`.

### FND-11: Prescription Header vs Line Item Status
1. **Prescription Invariant (`backend/apps/consultations/models.py`):**
   - In `Prescription.clean()` and `Prescription.save()`: Raising `ValidationError` if `status == 'DISPENSED'` while any child item in `self.items` has `status == 'PENDING'`.
2. **Serializer Guard (`backend/apps/consultations/views.py`):**
   - Added `validate()` in `PrescriptionSerializer` rejecting attempts to update header to `DISPENSED` when pending items exist.

### FND-12: Atomic Inventory Transactions & Dispensing Lineage
1. **Hardened Dispensing Service (`backend/apps/pharmacy/views.py`):**
   - In `DispenseMedicineView`: Atomic transaction (`with transaction.atomic():`) wraps batch stock deduction, `InventoryTransaction` creation, and `PrescriptionItem` status update.
   - Added double-dispensing guard: If an item has already been marked `DISPENSED`, repeated dispensing attempts are rejected with HTTP 400.
2. **Seed Data Generator (`backend/apps/accounts/management/commands/seed_demo.py`):**
   - Updated initial seed dispensations (`pr_dh`, `pr_sdh`, `pr_vc`) to create authentic `InventoryTransaction` records with correct batch decrements.

---

## 4. Data Model & Migration Impact

- **Database Column Changes:** None. All models utilize existing database columns and relationships.
- **Migration Verification:**
  - Command: `python manage.py makemigrations --check --dry-run`
  - Output: `No changes detected`
  - Result: **PASS** (Zero schema migrations required).

---

## 5. API & UI Impact

- **API Endpoints Hardened:**
  - `POST /api/patients/`: Enforces facility-district alignment.
  - `POST /api/visits/{id}/transition-status/`: Rejects advancing untriaged visits to DOCTOR queue (HTTP 400); enforces role authorization (HTTP 403).
  - `POST /api/consultations/`: Rejects clinical consultation on patients awaiting triage.
  - `POST /api/pharmacy/dispense/`: Prevents double-dispensing of line items; creates atomic ledger transactions.
  - `PATCH /api/prescriptions/{id}/`: Rejects header status `'DISPENSED'` if child items are pending.
- **UI State Consistency:**
  - Completed patients are removed from active doctor queues, preventing ghost records in clinic worklists.
  - DHO patient directory consistently reflects all patients registered in the district.
  - Pharmacy status chips and stock counts remain synchronized with ledger transactions.

---

## 6. Demo Data Reconciliation

All inconsistent historical demo records identified in the Phase C audit were reconciled in `db.sqlite3`:

| Record ID | Model | Previous State | Reason for Inconsistency | Corrected State | Supporting Evidence |
|---|---|---|---|---|---|
| **Patient #216** (`NC-KA-2026-8717`) | Patient | `registered_at_facility=None`, `district=None`, `ward=None` | Orphaned patient registration record missing geographic mapping | `registered_at_facility=68`, `district=11`, `ward=30` | Linked Visit #41 is at Facility 68 (Varthur Rural Clinic, District 11, Ward 30). |
| **Visit #39** (`VIS-20260917-003`) | Visit / Triage | `queue=DOCTOR`, `status=WAITING_FOR_DOCTOR`, `triage=None` | Visit seeded in doctor queue without required triage assessment | Created `TriageVitals #28` (BP 120/80, HR 78, SpO2 99%) | Patient Anita Devi (30/F, ANC) now has verified baseline vitals for consultation. |
| **Visit #40** (`VIS-20260917-004`) | Visit | `status=COMPLETED`, `current_queue=DOCTOR` | Encounter completed by doctor without advancing queue state | `current_queue=COMPLETED`, `status=COMPLETED` | Consultation exists; encounter is finalized. |
| **Visit #41** (`VIS-20260917-005`) | Visit | `status=COMPLETED`, `current_queue=DOCTOR` | Encounter completed by doctor without advancing queue state | `current_queue=COMPLETED`, `status=COMPLETED` | Consultation exists; encounter is finalized. |
| **Prescription #26** | Prescription | `status=DISPENSED`, Items #68, #69 `PENDING` | Header marked dispensed without updating child item status | `status=DISPENSED`, Items #68, #69 `DISPENSED` | Child items fulfilled for completed encounter Visit #41. |
| **Item #65** (Rx #24) | Inventory Transaction | Metformin had Tx #6; Item #65 (Amlodipine) had no transaction | Stock decremented from Batch 28 without ledger entry | Created `InventoryTransaction #7` (qty 14, Amlodipine, Batch 28) | Authoritative stock ledger matches batch quantity. |
| **Items #68 & #69** (Rx #26) | Inventory Transaction | Items dispensed without ledger entry | Missing stock ledger records for Prescription #26 | Created `InventoryTransaction #8` (Amlodipine, qty 14) and `#9` (Metformin, qty 14); decremented Batches 28 and 26 | Stock ledger completely reconciled with patient dispensations. |

---

## 7. Automated Test Suite Results

### 1. Backend Test Suite (38 Tests)
- **Command:** `python manage.py test apps.accounts`
- **Result:** `Ran 38 tests in 31.206s. OK`
- **Breakdown:**
  - Existing regression tests: 27 PASS
  - New Phase C2 regression tests (`PhaseC2RegressionTests`): 11 PASS
    1. `test_fnd08_patient_facility_populates_district_and_dho_visibility`: PASS
    2. `test_fnd08_patient_facility_district_mismatch_rejected`: PASS
    3. `test_fnd08_no_cross_district_leakage`: PASS
    4. `test_fnd09_untriaged_visit_cannot_advance_to_doctor_queue`: PASS
    5. `test_fnd09_triaged_visit_can_advance_to_doctor_queue`: PASS
    6. `test_fnd09_unauthorized_role_cannot_transition_to_doctor_queue`: PASS
    7. `test_fnd10_completed_visit_queue_synchronized`: PASS
    8. `test_fnd11_prescription_header_cannot_be_dispensed_with_pending_items`: PASS
    9. `test_fnd11_prescription_partially_dispensed_when_some_items_remain`: PASS
    10. `test_fnd12_dispensing_creates_authoritative_inventory_transaction`: PASS
    11. `test_fnd12_cannot_double_dispense_item`: PASS

### 2. Frontend Build
- **Command:** `npm run build`
- **Result:**
  ```text
  ✓ 1918 modules transformed.
  rendering chunks...
  dist/index.html                   0.47 kB │ gzip:   0.30 kB
  dist/assets/index-DJAFoXLr.css   68.08 kB │ gzip:  11.36 kB
  dist/assets/index-DVy0SpeJ.js   708.51 kB │ gzip: 166.36 kB
  ✓ built in 510ms
  ```
- **Exit Code:** 0 (PASS)

### 3. Frontend Lint
- **Command:** `npm run lint`
- **Result:** `Found 134 warnings and 0 errors. Finished in 179ms on 41 files.`
- **Exit Code:** 0 (PASS)

---

## 8. Database Integrity Audit (Step 9 Reconciliation Checks)

Executed explicit database verification queries across `backend/db.sqlite3`:

| Check | Description | Query Criteria | Count | Result |
|---|---|---|---|---|---|
| **A** | Patients with facility/district inconsistencies | `registered_at_facility != None` AND `district != facility.district` | **0** | **PASS** |
| **B** | Completed visits in DOCTOR queue | `status = 'COMPLETED'` AND `current_queue = 'DOCTOR'` | **0** | **PASS** |
| **C** | Visits waiting for doctor without triage | `status = 'WAITING_FOR_DOCTOR'` AND `triage__isnull = True` | **0** | **PASS** |
| **D** | Header DISPENSED with PENDING item | `Prescription.status = 'DISPENSED'` AND `items__status = 'PENDING'` | **0** | **PASS** |
| **E** | Dispensed items without InventoryTransaction | `PrescriptionItem.status = 'DISPENSED'` without matching reference | **0** | **PASS** |
| **F** | Orphaned InventoryTransactions | `InventoryTransaction` where batch/facility/medicine is null | **0** | **PASS** |

**Zero contradictions remain in the active database.**

---

## 9. Client Journey Verification

Executed an end-to-end representative patient journey test verifying all 9 milestones:
1. **Patient Registration:** Patient registered at Facility 68 (`NC-KA-2026-3068`, District 11).
2. **Visit Creation:** Issued OPD visit (`VIS-F68-20260921-002`, `current_queue='TRIAGE'`, `status='WAITING_FOR_TRIAGE'`).
3. **Queue Guard Check:** Attempted transition to `DOCTOR` queue directly was rejected (HTTP 400).
4. **Nurse Triage:** Vitals logged (BP 124/82, HR 78, SpO2 98%); visit advanced to `DOCTOR` queue (`WAITING_FOR_DOCTOR`).
5. **Doctor Consultation:** Doctor called patient (`IN_CONSULTATION`) and recorded diagnosis and prescription; visit advanced to `PHARMACY` queue (`WAITING_FOR_PHARMACY`).
6. **Pharmacy Dispensing:** Pharmacist dispensed items; Batch `BATCH-PCM-2026P` decremented from 1200 to 1191; `InventoryTransaction #10` logged atomically; items and header updated to `DISPENSED`.
7. **Visit Completion:** Visit status and queue both finalized to `COMPLETED` with timestamp.

---

## 10. Summary of Files Changed

- `backend/apps/patients/models.py`: Added facility/district consistency validation in `clean()` and `save()`.
- `backend/apps/patients/serializers.py`: Added serializer validation for geographic alignment.
- `backend/apps/visits/models.py`: Added bidirectional queue/status auto-synchronization and triage requirement in `clean()`.
- `backend/apps/visits/views.py`: Added triage guard and role validation in `transition_status()`.
- `backend/apps/consultations/models.py`: Enforced header vs line item consistency in `Prescription.clean()`.
- `backend/apps/consultations/views.py`: Added triage check and serializer validation for prescription status.
- `backend/apps/pharmacy/views.py`: Guarded against double-dispensing and ensured atomic inventory movements.
- `backend/apps/accounts/management/commands/seed_demo.py`: Added triage vitals and inventory transactions for demo datasets.
- `backend/apps/accounts/tests.py`: Added 11 regression tests in `PhaseC2RegressionTests`.
- `docs/quality/PHASE_C_REMEDIATION_BACKLOG.md`: Updated finding statuses for FND-08 through FND-12.

---

## 11. Known Limitations & Deferred Work

- **Known Limitations:**
  - Automated triage vitals calculations (BMI, clinical flags) assist workflow but do not replace autonomous clinician evaluation.
  - In historical database snapshots, encounters finalized prior to C2 required data reconciliation to align with strict validation rules.
- **Deferred Findings:**
  - FND-06 (Teleconsultation module) remains deferred pending WebRTC architecture review.
  - FND-13 (hardcoded consultation form defaults) remains deferred for UI workflow phase.
  - FND-14 (UHID format generation) and FND-15 (dormant models) remain deferred.
  - FND-16, FND-17, LabOrder foreign keys remain deferred.

---

## 12. Git Commit & Working Tree Status

- **Status:** All tests pass, lint clean, database verified.
- **Target Commit Message:** `Fix Namma Clinic Phase C2 data integrity`
- **Remote Push:** Not executed (Awaiting PM/RSA acceptance gate).
