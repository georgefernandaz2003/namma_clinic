# PHASE 26A — PHARMACY INTEGRITY & AUTHORIZATION HARDENING REPORT

## 1. Executive Summary

This report documents the verification, hardening, and safety validation of the **Pharmacy Clinical Workflow** for Namma Clinic (Phase 26A).

Phase 26A is an integrity and safety hardening phase designed to provide proof of the pharmacy clinical workflow under concurrent PostgreSQL execution, strict role-based separation of duties, inventory double-entry auditing, facility scope isolation, and error/retry resilience.

**Strict Boundary Adherence**:
- No Phase 27 work has been started.
- No Procurement UI, Goods Receipt Note (GRN) UI, or Vendor management UI was created.
- No Maternal/Child, Non-Communicable Diseases (NCD), Teleconsultation, Admin, or District operational workflows were modified.
- The system operates strictly on the local architecture: PostgreSQL 16 on port 49392, Django 4.2 / DRF on port 8000, and React 19 / Vite 8 on port 3000.

All 8 Phase 26A concurrency and integrity tests, all 52 Pharmacy Hardening tests (+23 procurement assertions), all 94 established backend regression tests, and all 154 frontend tests pass deterministically.

---

## 2. Git Baseline and Commits

- **Baseline Commit**: `d5bf52111c8290cb6f9075b6bcec5bb982ebd9ce`
- **Active Branch**: `feature/namma-clinic-demo-data-model`
- **History Preservation**: No commits were rebased, reset, squashed, or rewritten.
- **Phase 26A Commit**: Exactly one targeted commit will be created with message:
  `fix(namma-clinic): harden pharmacy workflow integrity`

---

## 3. Actual Implementation Analysis

Review of the codebase revealed several areas requiring defensive hardening to ensure separation of duties and transactional integrity:

1. **Role Guarding on Dispensation**:
   - `apps/pharmacy/api_v1.py` (`DispensationViewSet.create`): Previously relied on generic `IsAuthenticated`. Hardened to enforce `is_pharm` check via `StaffRoleAssignment`. Requests from `DOCTOR`, `NURSE`, `LAB_TECHNICIAN`, `HOSPITAL_ADMIN`, and `DISTRICT_OFFICER` are rejected with `403 Forbidden`.
   - `apps/pharmacy/views.py` (`DispenseMedicineView.post`): Added `HOSPITAL_ADMIN` to the list of prohibited non-pharmacist roles.

2. **Prescription Status & Row-Level Locking**:
   - `apps/pharmacy/services.py` (`dispense_prescription`): Added explicit row-level lock `locked_rx = Prescription.objects.select_for_update().get(pk=prescription.pk)` inside `transaction.atomic()`. Prescriptions in `DISPENSED` status are immediately rejected with `DomainValidationError`. The rejection message is composite (`Prescription #{id} has already been fully dispensed and cannot be dispensed in status 'DISPENSED'`) to maintain compatibility with all legacy assertions.

3. **Hold and Reject Reason Enforcement**:
   - `apps/pharmacy/api_v1.py` (`PrescriptionViewSet.hold` & `reject`): Hardened to require non-empty payload input. Requests with missing or whitespace-only reasons are rejected with `400 Bad Request`. Valid reasons are persisted to `verification_notes` (for hold) and `rejection_reason` (for reject).
   - `frontend/src/pages/Pharmacy.tsx`: Hardened `handleHold` to ensure `holdNotes.trim()` is non-empty before dispatching the API request.

4. **Facility Isolation & Parameter Tampering**:
   - `apps/pharmacy/api_v1.py` (`DispensationViewSet.create`): Validates that the requesting user's assigned facility matches the dispensation facility, matches the prescription facility, matches each prescription item, and matches each batch facility. Any mismatch or manipulated `facility_id` parameter returns `403 Forbidden`.

5. **Inventory Ledger Immutability**:
   - `apps/pharmacy/api_v1.py` (`InventoryLedgerViewSet`): Inherits from `ReadOnlyModelViewSet`. `PUT`, `PATCH`, and `DELETE` requests are rejected with `405 Method Not Allowed`.

---

## 4. Row-Level Locking and Concurrency Verification

PostgreSQL row-level locking was validated under multi-threaded execution using `ThreadPoolExecutor(max_workers=2)`:

### Scenario 1: Same Batch, Insufficient Stock
- **Initial State**: Batch stock = 5 units.
- **Concurrent Actions**: Thread 1 requests 4 units; Thread 2 requests 3 units (total 7 units requested).
- **Observed Behavior**: PostgreSQL serializes the batch row lock (`select_for_update()`). The first thread successfully deducts stock (stock becomes 1 or 2). The second thread reads the updated balance, detects available < requested, and raises `InsufficientStockError`.
- **Integrity Result**: Stock is never negative. Exactly one transaction succeeds and exactly one `InventoryLedger` entry is created.

### Scenario 2: Same Prescription, Single Winner
- **Initial State**: Prescription status = `VERIFIED`.
- **Concurrent Actions**: Thread 1 and Thread 2 both submit dispensation requests for the same prescription.
- **Observed Behavior**: The row lock on `Prescription` forces sequential processing. Thread 1 dispenses the items, updates prescription status to `DISPENSED`, and commits. Thread 2 acquires the lock, observes status `DISPENSED`, and raises `DomainValidationError`.
- **Integrity Result**: Exactly one `Dispensation` record is created. Duplicate dispensations for the same prescription are physically impossible.

---

## 5. Duplicate, Double Submit, and Retry Verification

Four real-world duplicate submission scenarios were tested and verified:

| Scenario | Trigger / Condition | Backend Behavior | Final Database State | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Case A: Rapid Double-Submit** | Rapid consecutive clicks on Dispense button | First request processes; second hits `locked_rx.status == 'DISPENSED'` and returns 400 | Exactly 1 dispensation, stock deducted once, 1 ledger record | **VERIFIED** |
| **Case B: Network Retry** | Client resends request after network timeout | Request rejected with 400 ("cannot be dispensed in status 'DISPENSED'") | Stock unchanged, no duplicate ledger | **VERIFIED** |
| **Case C: Stale UI Cache** | UI displays cached `VERIFIED` state while prescription was already dispensed | Server verifies current DB status under row lock, rejects with 400 | Preserved authoritative DB state | **VERIFIED** |
| **Case D: Terminal Status Dispense** | Direct API call attempting to dispense completed prescription | Immediate 400 rejection | Zero mutations | **VERIFIED** |

---

## 6. Separation of Duties and 6-Role Authorization Matrix

The six core healthcare roles were evaluated against the pharmacy API endpoints:

| Role | Prescription Verify | Prescription Hold | Prescription Reject | Dispensation Create | Inventory Ledger Read |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **PHARMACIST** | **200 OK** | **200 OK** | **200 OK** | **201 Created** | **200 OK** |
| **DOCTOR** | **403 Forbidden** | **403 Forbidden** | **403 Forbidden** | **403 Forbidden** | 200 OK (Read-Only) |
| **NURSE** | **403 Forbidden** | **403 Forbidden** | **403 Forbidden** | **403 Forbidden** | **403 Forbidden** |
| **LAB_TECHNICIAN** | **403 Forbidden** | **403 Forbidden** | **403 Forbidden** | **403 Forbidden** | **403 Forbidden** |
| **HOSPITAL_ADMIN** | **403 Forbidden** | **403 Forbidden** | **403 Forbidden** | **403 Forbidden** | 200 OK (Read-Only) |
| **DISTRICT_OFFICER** | **403 Forbidden** | **403 Forbidden** | **403 Forbidden** | **403 Forbidden** | 200 OK (Read-Only) |

**Key Clinical Invariant**: The prescribing clinician (Doctor) cannot verify or dispense medication. Verification and dispensation are strictly restricted to the `PHARMACIST` role.

---

## 7. Hold and Reject Reason Enforcement

Both `hold` and `reject` operations enforce mandatory clinical justifications:
- **Empty Reason Rejection**: Sending `{"reason": ""}` or `{"notes": "   "}` returns `400 Bad Request` with an explicit error message.
- **Valid Reason Persistence**: Providing a non-empty string successfully transitions the prescription status to `ON_HOLD` or `REJECTED` and persists the note in the database audit fields.
- **Frontend Prevention**: The UI disables the submit button and prevents dispatch when reason fields are empty.

---

## 8. FEFO Semantics: Qualification vs Enforcement

An architectural audit of First-Expiry-First-Out (FEFO) logic confirms **Option B**:
- **Backend Batch Qualification**: The backend enforces eligibility rules. A batch is eligible if and only if:
  1. It belongs to the same facility as the prescription.
  2. It has status `AVAILABLE`.
  3. It is not expired (`expiry_date > today`).
  4. It has available stock $\ge$ requested quantity.
  5. It is not under quarantine or recall.
- **Pharmacist Clinical Discretion**: Any eligible batch may be dispensed. The backend does not reject a dispensation simply because another batch with an earlier expiry date exists. This allows pharmacists to exercise professional judgment (e.g. selecting an open blister pack or matching an exact pill count).
- **Frontend Clinical Decision Support**: The frontend displays batches sorted by `expiry_date ASC` and automatically tags the earliest eligible batch with `[FEFO RECOMMENDED]`.

---

## 9. Inventory Ledger Immutability & Double-Entry Verification

1. **Double-Entry Balance Verification**:
   - Every dispensation creates an `InventoryLedger` entry.
   - For every entry: `balance_after == balance_before + quantity_delta`.
   - Dispensation entries record negative `quantity_delta` (e.g. `-6`) and point to the `Dispensation` record as `reference_entity_id`.
2. **API Immutability**:
   - `InventoryLedgerViewSet` provides read-only access.
   - `PUT`, `PATCH`, and `DELETE` requests to `/api/v1/pharmacy/inventory-ledger/{id}/` return `405 Method Not Allowed`.
3. **Database Constraints**:
   - PostgreSQL schema enforces `balance_after >= 0` via table CHECK constraint.
   - *Limitation Note*: Database triggers preventing raw SQL `UPDATE` are not present; immutability is guaranteed at the application and API service layer.

---

## 10. Facility Scope Isolation & Parameter Tampering Protection

Multi-facility safety was verified across Facilities A and B:
1. **Cross-Facility Reads**: Facility A staff cannot read prescriptions or batches belonging to Facility B (returns 404 Not Found or empty results).
2. **Cross-Facility Dispensation Block**: Attempting to dispense a Facility B prescription from Facility A returns `403 Forbidden`.
3. **Parameter Tampering Block**: If a client tampers with the request payload by passing `facility_id: <Facility B>` while authenticated as Facility A staff, the backend detects the mismatch and returns `403 Forbidden`.
4. **Batch Facility Cross-Contamination**: Supplying a batch ID belonging to Facility B for a Facility A prescription returns `403 Forbidden`.

---

## 11. Counselling and Patient Safety Tracking

- **Explicit Recording**: The `counseling_provided` boolean flag is captured on every dispensation and stored on the `Dispensation` model.
- **Patient Counselling Model**: The `PatientCounselling` entity tracks specific counselling topics (dosage, frequency, precautions, food interactions, adverse reactions, storage conditions) and requires explicit clinician confirmation rather than defaulting to completed.

---

## 12. Batch Bucket Architecture & Safety States

Inventory stock is tracked across four mutually exclusive quantity buckets:
$$\text{quantity} = \text{available\_quantity} + \text{quarantined\_quantity} + \text{recalled\_quantity} + \text{damaged\_quantity}$$

- **Safety Blocks**:
  - Expired batches (`expiry_date <= today`) are blocked with `400 Bad Request`.
  - Quarantined batches (`status == 'QUARANTINED'` or `available_quantity == 0`) are blocked with `409 Conflict`.
  - Recalled batches (`status == 'RECALLED'`) are blocked with `409 Conflict`.
- **Legacy Normalization**: Historical batches with status `'ACTIVE'` are normalized to `'AVAILABLE'` during read operations.

---

## 13. Patient Return Safety & Governance

- Medication returned by patients is recorded in `DispensationReturn`.
- Returned items are placed in quarantine pending assessment; they do not automatically enter available inventory.
- Cumulative returned quantities cannot exceed the original dispensed quantity.

---

## 14. Cold Chain Excursion Detection & Governance

- `ColdChainLog` records temperature readings for cold-storage medications.
- Excursions outside the configured range trigger operational alerts.
- Unconfigured temperature ranges are not assumed to be normal.

---

## 15. High-Alert Medicine Governance

- High-alert and LASA (Look-Alike Sound-Alike) medicine flags are preserved in `MedicineMaster`.
- High-alert medicines require heightened visual attention in the UI and explicit verification during the clinical workflow.

---

## 16. Frontend Verification & Test Results

- **Oxlint**: Ran `npx oxlint src` in `frontend/`:
  - **0 errors** across 74 files with 116 rules.
- **Production Build**: Ran `npm run build` (`tsc -b && vite build`):
  - Completed cleanly in 634ms with 0 compilation errors.
- **Automated Frontend Test Suite**: Ran `npm test`:
  - **154 passed, 0 failed** across all test suites.

---

## 17. Backend Test Suite Results

- **Phase 26A Integrity Test Suite** (`apps.pharmacy.tests_phase26a_integrity`):
  - **8 passed, 0 failed** in 21.8s on PostgreSQL.
- **Pharmacy Hardening Verification Suite** (`apps.pharmacy.tests`):
  - **52 passed, 0 failed** across all 10 clinical hardening sections.
  - **23 passed, 0 failed** across all procurement and GRN assertions.
- **Established Regression Suite** (`tests_phase11` through `tests_phase20_contract`):
  - **94 passed, 0 failed** in 64.3s.

---

## 18. Live PostgreSQL Verification Findings

A standalone verification script (`scratch/live_validation_phase26a.py`) was executed against the live PostgreSQL 16 database and running DRF application:
1. `DOCTOR`, `NURSE`, `LAB_TECHNICIAN`, `HOSPITAL_ADMIN`, and `DISTRICT_OFFICER` were verified to receive `403 Forbidden` on dispensation creation.
2. `DOCTOR` received `403 Forbidden` on prescription verification.
3. Empty hold and reject reasons were verified to receive `400 Bad Request`.
4. Valid hold and reject reasons transitioned prescription status to `ON_HOLD` and `REJECTED` (200 OK).
5. Facility parameter tampering was rejected with `403 Forbidden`.
6. Pharmacist dispensation succeeded (201 Created), reducing available stock by exactly the dispensed quantity and generating an authoritative `InventoryLedger` record.
7. Immediate retry of the same dispensation payload was rejected with `400 Bad Request`, and stock remained unchanged.

---

## 19. Honest Limitation Register & Classification Table

| Feature / Mechanism | Classification | Clinical & Technical Rationale |
| :--- | :--- | :--- |
| **PostgreSQL Concurrency Row-Locking** | **VERIFIED** | `select_for_update()` serializes batch and prescription mutations; eliminates race conditions. |
| **Separation of Duties (6 Roles)** | **VERIFIED** | Only `PHARMACIST` can verify, hold, reject, and dispense; other 5 roles receive 403. |
| **Double-Submit / Retry Protection** | **VERIFIED** | Prescriptions in `DISPENSED` status cannot be dispensed again; stock and ledger are protected. |
| **Hold / Reject Mandatory Justification** | **VERIFIED** | Non-empty reasons strictly required by both API and frontend UI. |
| **Facility Scope Isolation** | **VERIFIED** | Cross-facility reads return 404; mutations and parameter tampering return 403. |
| **FEFO Qualified Selection** | **VERIFIED** | Backend qualifies eligible batches; frontend recommends earliest expiry; pharmacist retains override. |
| **Double-Entry Ledger Audit Trail** | **VERIFIED** | `balance_after == balance_before + quantity_delta` verified on all stock mutations. |
| **Read-Only Ledger API** | **VERIFIED** | `ReadOnlyModelViewSet` returns 405 on PUT/PATCH/DELETE. |
| **Database-Trigger Immutability** | **BACKEND LIMITATION** | Immutability is enforced at the Django service layer and API layer, not via PostgreSQL SQL triggers. |
| **Partial Dispensation Completion** | **VERIFIED** | Multi-step partial dispensations update `dispensed_quantity` until prescribed amount is met. |
| **Patient Return Usable Stock Exclusion** | **VERIFIED** | Returned medicines enter quarantine bucket and require quality disposition before reuse. |
| **Procurement UI / GRN UI** | **NOT IMPLEMENTED** | Intentionally out of scope for Phase 26A; no procurement or vendor UI screens exist. |
| **NCD & Maternal/Child Modules** | **NOT IMPLEMENTED** | Deferred to designated future phases. |
| **Teleconsultation Modules** | **NOT IMPLEMENTED** | Deferred to designated future phases. |

---

## 20. Conclusion

Phase 26A Pharmacy Integrity & Authorization Hardening is **COMPLETE** and verified on real PostgreSQL. All integrity invariants, concurrency safeguards, role constraints, and audit trails have been proven.

Work terminates at this milestone in accordance with the mandatory stop instruction. Phase 27 has not been started.
