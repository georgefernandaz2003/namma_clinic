# Phase 15 — Backend QA & Reliability Hardening Report

## 1. Objective
Phase 15 is a dedicated backend quality assurance, reliability, failure-mode, and contract-hardening phase. Building on the approved Phase 14 baseline, the primary objective is to verify that the backend behaves deterministically and safely under duplicate requests, out-of-order operations, invalid states, unauthorized actions, partial transaction failures, retries, and cross-facility boundaries.

This phase is not a feature-development phase and introduces no frontend or UI components.

---

## 2. Git Baseline Verification

| Attribute | Value | Status |
| :--- | :--- | :--- |
| **Initial Baseline HEAD** | `403675c20eef2a87a17dd1d6689d044238e815e9` | Verified |
| **Active Branch** | `feature/namma-clinic-demo-data-model` | Verified |
| **Pre-Phase 15 Working Tree** | Clean prior to Phase 15 additions | Verified |

---

## 3. Final HEAD & Commit

| Attribute | Value |
| :--- | :--- |
| **Final HEAD** | `(Created upon commit)` |
| **Commit Message** | `feat(namma-clinic): harden backend reliability` |
| **Cumulative Test Suite** | **85 passed / 0 failed / 0 errors / 0 skipped** (43.133s) |

---

## 4. Repository Status
The backend architecture comprises:
- **Presentation Layer**: Versioned Django REST Framework APIs (`/api/v1/`) with custom permission classes (`IsActiveStaff`, `IsAdministrativeStaff`, `IsMedicalOfficer`, `FacilityScopedPermission`).
- **Domain Service Layer**: Transactional boundaries (`@transaction.atomic()`), lifecycle state machines, and business invariant validations.
- **Physical Data Model**: Django physical models representing the 50-table candidate schema.
- **Audit & Accounting Subsystem**: Server-derived `AuditLogEntry` generation and double-entry authoritative `InventoryLedger` recording.

---

## 5. State-Machine Hardening
Lifecycle state transitions across all critical entities were tested against illegal mutations and invalid sequences:

1. **Diagnostic Results**:
   - Re-verification of an already verified result is rejected with `HTTP 409 Conflict` (`VerifiedResultImmutableError`).
   - Duplicate result creation for the same `TestRequest` is rejected (`HTTP 400 Bad Request` or `HTTP 409 Conflict` via `DiagnosticResultAlreadyExistsError`).
2. **Prescriptions**:
   - Dispensing against an already `DISPENSED` or `CANCELLED` prescription is blocked (`HTTP 400 Bad Request`).
3. **Referrals**:
   - Progression must follow the valid state graph: `INITIATED` -> `ACKNOWLEDGED` -> `IN_TRANSIT` -> `ARRIVED` -> `COMPLETED`.
   - Illegal transitions (e.g. `INITIATED` -> `ARRIVED`, or `COMPLETED` -> `ARRIVED`) are rejected with `HTTP 409 Conflict` (`InvalidStateTransition`).
4. **Follow-Up Tasks**:
   - Repeated completion of an already `COMPLETED` task is rejected (`HTTP 409 Conflict`).
   - Completion against an in-progress or cancelled visit is rejected (`HTTP 409 Conflict`).
5. **Procurement**:
   - Receiving goods against a `DRAFT` or unapproved PO is rejected (`HTTP 409 Conflict` via `InvalidProcurementStateError`).
   - Duplicate approval of an approved PO tier is rejected (`HTTP 409 Conflict`).

---

## 6. Idempotency & Duplicate Request Resilience
High-risk endpoints subject to network retries and duplicate submissions were tested:

1. **Monotonic OPD Tokens**: Re-calling `issue-opd-token` on a visit returns the existing allocated token without creating duplicate token numbers or orphan records.
2. **Monotonic Lab Tokens**: Re-calling `issue-lab-token` for a diagnostic order returns the existing lab token number.
3. **Goods Receipt Notes (GRN)**: Submitting duplicate GRN payloads with the same `grn_number` is intercepted by the domain service and rejected with `HTTP 400 Bad Request` (`VALIDATION_ERROR`), preventing raw database `IntegrityError` crashes and double stock ingestion.
4. **Operational Alert Acknowledgment**: Multiple consecutive calls to `acknowledge` on the same alert remain safely idempotent (`is_active = False`).

---

## 7. Inventory Reliability
The inventory domain was subjected to negative testing to verify accounting invariants:

- **Authoritative Ledger Invariant**: The sum of `quantity_delta` across all `InventoryLedger` entries for a batch strictly equals `MedicineBatch.quantity`.
- **Negative Stock Prevention**: Attempting to dispense more units than `available_quantity` is rejected with `HTTP 409 Conflict` (`InsufficientStockError`), leaving physical stock and ledger records completely unchanged.
- **Quarantine Hold Protection**: Quarantining stock moves units from `available_quantity` to `quarantined_quantity`. Attempting to dispense units locked in quarantine fails. Releasing quarantine restores available stock.
- **Multi-Batch Dispensation Atomicity**: In a multi-batch dispensation where one batch has sufficient stock but another batch has insufficient stock, the entire transaction rolls back atomically. Zero ledger rows are inserted, and no partial stock is deducted.

---

## 8. Transaction Failure & Rollback
Controlled failure scenarios were verified using injected runtime exceptions:

- **Mid-Transaction Dispensation Failure**: An injected database error during dispensation item creation triggers a complete atomic rollback. `MedicineBatch.available_quantity` remains untouched, zero `InventoryLedger` movements are recorded, and zero phantom `AuditLogEntry` rows are written.
- **Mid-Transaction GRN Failure**: An error during batch receipt rolls back both the `GoodsReceiptNote` and the associated inventory movements.
- **Zero Phantom Audit Guarantee**: Calls to `record_audit_event` reside within the transactional atomic block; when the transaction aborts, the audit entry is rolled back along with the business mutation.

---

## 9. Authorization Negative Testing
The authorization boundary was tested against an exhaustive role-privilege matrix:

| Persona | Unauthorized Actions Tested | Expected Result | Actual Result |
| :--- | :--- | :--- | :--- |
| **Unauthenticated** | Accessing protected clinical/operational endpoints | HTTP 401 Unauthorized | HTTP 401 Unauthorized |
| **DOCTOR** | Approving purchase orders; dispensing medications | HTTP 403 Forbidden | HTTP 403 Forbidden |
| **NURSE** | Conducting medical consultations; verifying lab results; approving POs | HTTP 403 Forbidden | HTTP 403 Forbidden |
| **LAB_TECHNICIAN** | Conducting medical consultations; verifying lab results; approving POs | HTTP 403 Forbidden | HTTP 403 Forbidden |
| **PHARMACIST** | Conducting medical consultations; verifying lab results; prescribing medications | HTTP 403 Forbidden | HTTP 403 Forbidden |
| **HOSPITAL_ADMIN** | Conducting medical consultations; prescribing medications | HTTP 403 Forbidden | HTTP 403 Forbidden |

---

## 10. Staff Lifecycle, Transfers & Historical Integrity
1. **Inactive / Suspended Staff**:
   - Updating a staff member's status to `SUSPENDED` immediately revokes mutation access across the REST API (`HTTP 403 Forbidden`).
2. **Staff Transfers**:
   - Transferring staff from Clinic A to Clinic B closes the Clinic A primary assignment and updates both `StaffFacilityAssignment` and `User.assigned_facility`.
   - The transferred staff member immediately loses mutation access to Clinic A (`HTTP 403 Forbidden`) and gains authorized access to Clinic B (`HTTP 201 Created`).
3. **Effective Date Scoping**:
   - Future assignments (`effective_from > today`) do not grant premature facility access (`HTTP 403 Forbidden`).
   - Expired assignments (`effective_to < today`) do not grant facility access.
4. **Historical Authorship Integrity**:
   - Suspending or transferring a staff member preserves historical clinical authorship. Past consultations, prescriptions, and verified diagnostic results maintain the original author's foreign key intact without data destruction.

---

## 11. Cross-Facility Multi-Tenancy Boundaries
- **Operational Data Isolation**: Facility A staff cannot read, mutate, or acknowledge Facility B visits, consultations, prescriptions, inventory batches, or operational alerts (`HTTP 403 Forbidden` / `HTTP 404 Not Found`).
- **Continuity of Care**:
  - Default patient listing (`GET /api/v1/patients/`) returns strictly facility-scoped patients.
  - Explicit demographic search (`GET /api/v1/patients/?search=<mobile or id>`) permits statewide patient lookup across facilities to support referrals and transferred clinical care.

---

## 12. API Error Contracts
The API error handling envelope was verified across all failure categories:

| Status Code | Error Code | Scenario | Structure Verified |
| :--- | :--- | :--- | :--- |
| **401 Unauthorized** | N/A | Missing / expired JWT authentication | DRF standard 401 envelope |
| **403 Forbidden** | `UNAUTHORIZED_DOMAIN_ACTION` | Unauthorized role or facility scope violation | `{"error": "...", "code": "UNAUTHORIZED_DOMAIN_ACTION", "details": {}}` |
| **400 Bad Request** | `VALIDATION_ERROR` | Schema validation error, malformed input, duplicate GRN | `{"error": "...", "code": "VALIDATION_ERROR", "details": {}}` |
| **409 Conflict** | `CONFLICT` / `INSUFFICIENT_STOCK` / `INVALID_STATE_TRANSITION` | Illegal state machine transition, stock shortfall, verified result lock | `{"error": "...", "code": "<SPECIFIC_CODE>", "details": {}}` |

---

## 13. Serializer Mass-Assignment Defense
Protected server-derived fields were tested against client payload tampering:

- **Clinical Authorship**: Client-supplied `doctor_staff` in consultation payloads and `referring_doctor` in referral payloads are ignored; the server binds authorship strictly from authenticated actor context.
- **Physical Inventory**: Client attempts to update `available_quantity`, `quantity`, or `status` via `PATCH /api/v1/pharmacy/batches/{id}/` are blocked (`read_only_fields` enforcement).

---

## 14. Audit Reliability
- Server-side derivation of actor credentials (`actor_staff`, `actor_role_snapshot`, `facility`) prevents client payload forgery.
- Audits are recorded atomically with business transactions: if a mutation rolls back, no audit row is persisted.

---

## 15. Database Constraint Testing
- **Unique Constraints**: Daily OPD token uniqueness, laboratory token uniqueness, diagnostic result OneToOne binding, and GRN number uniqueness.
- **Check Constraints**: Non-negative inventory balance checks and physiological vitals range constraints.

---

## 16. SQLite vs. PostgreSQL Boundary

| Operational Requirement | SQLite-Proven Behavior | PostgreSQL-Required Staging Validation |
| :--- | :--- | :--- |
| **Monotonic Token Allocation** | Validated sequentially within test transactions | Multi-process concurrent worker thread isolation using PostgreSQL row-level locks |
| **Inventory `select_for_update()`** | Validated in single-thread serialized execution | Multi-cashier concurrent dispensation row locking under high write contention |
| **GRN Inventory Posting** | Atomicity and rollback validated under injected failure | Concurrent multi-GRN receipt against shared batch pools |
| **Foreign Key `RESTRICT` Constraints** | Enforced by SQLite runtime (`PRAGMA foreign_keys = ON`) | Production PostgreSQL constraint enforcement under foreign-table cascades |

---

## 17. Performance Sanity Findings
- **N+1 Query Resolution**: During performance query-count auditing of `VisitViewSet`, an N+1 query loop was identified where serializing `token_number` caused a separate `SELECT` query per visit row. Resolved by adding `token` to `select_related('patient', 'facility', 'token')`, reducing query counts from 9 queries to 4 queries on list endpoints.
- **Pagination & Bounds**: Verified that patient, visit, and consultation list endpoints paginate by default and avoid unbounded querysets.

---

## 18. Security Regression
All Phase 13A security safeguards remain 100% intact:
- Facility scoping active across all ViewSets.
- Direct stock mutation endpoints remain blocked.
- Diagnostic result immutability is maintained.
- Consultation creation is now strictly gated to medical doctors.

---

## 19. Defects Discovered During Phase 15

| Defect ID | Severity | Component | Finding |
| :--- | :--- | :--- | :--- |
| **DEF-15-01** | High | `apps.consultations.api_v1` | `ConsultationViewSet.perform_create` lacked role-level validation, allowing non-doctors (pharmacists, nurses) to record clinical consultations. |
| **DEF-15-02** | High | `apps.laboratory.api_v1` | `DiagnosticResultViewSet.verify` lacked role permission gating, allowing nurses and lab technicians to verify diagnostic results. |
| **DEF-15-03** | Medium | `apps.pharmacy.procurement_services` | Duplicate `grn_number` submissions caused unhandled raw database `IntegrityError` instead of domain-level validation. |
| **DEF-15-04** | Medium | `apps.visits.api_v1` | `VisitViewSet.queryset` omitted `token` from `select_related`, triggering N+1 queries when serializing visit lists. |
| **DEF-15-05** | Medium | `apps.common.permissions` | `get_user_permitted_facilities` did not filter on `effective_from` and `effective_to` dates, potentially granting premature or expired facility access. |
| **DEF-15-06** | Low | `apps.accounts.services` | `transfer_staff` updated `StaffFacilityAssignment` but omitted syncing `User.assigned_facility`. |

---

## 20. Defects Fixed
All six defects were corrected:
1. `backend/apps/consultations/api_v1.py`: Added explicit Doctor role verification in `perform_create` (raises `UnauthorizedDomainAction` -> 403 Forbidden).
2. `backend/apps/laboratory/api_v1.py`: Decorated `verify` action with `permission_classes=[IsMedicalOfficer]`.
3. `backend/apps/common/permissions.py`: Created `IsMedicalOfficer` permission class; hardened `get_user_permitted_facilities` with `effective_from__lte=today` and `(effective_to__isnull=True | effective_to__gte=today)`.
4. `backend/apps/pharmacy/procurement_services.py`: Added duplicate `grn_number` existence check in `receive_goods_receipt` (raises `DomainValidationError` -> 400 Bad Request).
5. `backend/apps/visits/api_v1.py`: Added `token` to `select_related('patient', 'facility', 'token')`.
6. `backend/apps/accounts/services.py`: Updated `transfer_staff` to sync `User.assigned_facility` with `new_facility`.

---

## 21. Test Matrix

| Test Name | Domain Focus | Scenario Tested | Outcome | Status |
| :--- | :--- | :--- | :--- | :--- |
| `test_01_state_machine_and_lifecycle_hardened_boundaries` | Lifecycle State Machines | Re-verification, duplicate results, closed Rx, referral transitions, follow-up, PO | All illegal transitions rejected (400/409) | **PASS** |
| `test_02_idempotency_and_duplicate_request_resilience` | Idempotency | Duplicate OPD token, Lab token, GRN, Alert acknowledgment | Safe idempotency; duplicate GRN rejected | **PASS** |
| `test_03_inventory_reliability_and_negative_stock_prevention` | Inventory Accounting | Over-dispensation, zero stock, quarantine hold/release, ledger summation | Negative stock prevented; ledger sum verified | **PASS** |
| `test_04_transaction_failure_and_rollback_zero_phantom_audit` | Transaction Rollback | Injected runtime failure in dispensation and follow-up | Zero partial mutation; zero phantom audit rows | **PASS** |
| `test_05_comprehensive_role_authorization_matrix` | Authorization | Role matrix across Doctor, Nurse, Lab Tech, Pharmacist, Admin | Unauthorized roles blocked (403); unauth (401) | **PASS** |
| `test_06_staff_lifecycle_effective_dates_and_historical_integrity` | Staff Lifecycle | Suspended staff, facility transfer, future assignments, authorship preservation | Status gated; transfer scoped; history intact | **PASS** |
| `test_07_cross_facility_boundary_and_continuity_of_care` | Multi-Tenancy | Facility A vs B isolation; continuity-of-care demographic search | Cross-facility blocked; demographic search works | **PASS** |
| `test_08_serializer_mass_assignment_defense` | Mass Assignment | Client-supplied doctor_staff, referring_doctor, batch quantities | Client forgery ignored; quantities read-only | **PASS** |
| `test_09_api_error_contract_determinism` | API Contracts | Deterministic error codes: 401, 403, 400, 409 envelopes | Consistent error structures returned | **PASS** |
| `test_10_performance_sanity_query_bounds` | Query Efficiency | Bounded query counts on patient, visit, and consultation lists | Bounded query execution; N+1 eliminated | **PASS** |

---

## 22. Complete Regression Results

### 22.1 System Check
```
python manage.py check
System check identified no issues (0 silenced).
```

### 22.2 Migration Check
```
python manage.py makemigrations --check
No changes detected
```

### 22.3 Full Repository Test Suite
Command:
```bash
python manage.py test apps.accounts.tests_phase11 apps.accounts.tests_phase12_services apps.accounts.tests_services apps.visits.tests_services apps.laboratory.tests_services apps.pharmacy.tests_services apps.referrals.tests_services apps.audit.tests_services apps.accounts.tests_phase13_api apps.accounts.tests_phase14_integration apps.accounts.tests_phase15_reliability
```

**Results:**
- **Total Tests:** 85
- **Passed:** 85
- **Failed:** 0
- **Errors:** 0
- **Skipped:** 0
- **Duration:** 43.133s
- **Status:** **OK (100% Pass Rate)**

---

## 23. Remaining Limitations
1. **Multi-Process Concurrency on SQLite**: Local SQLite tests run serialized transactions. Production PostgreSQL deployment requires load-testing concurrent `select_for_update()` row locks for token allocation and multi-cashier inventory dispensing.
2. **Third-Party Telephony / IDSP Integration**: Public health surveillance notifications and external communication gateways remain mocked at the database dispatch boundary.

---

## 24. Final Recommendation
Phase 15 backend QA, failure-mode testing, and contract hardening are complete. All identified failure modes and authorization gaps have been resolved, and 85 cumulative tests pass.

**RECOMMENDATION: APPROVE PHASE 15.**
