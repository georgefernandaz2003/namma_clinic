# PHASE 12A — DOMAIN SERVICE INTEGRITY & AUTHORIZATION REVIEW

## 1. EXECUTIVE SUMMARY & GATE STATUS

- **Phase Status:** `PHASE_12A_APPROVED`
- **Authorized Git Baseline:** `7dfe9114cea2d0aba5d246ada5bea3c5a37920b4`
- **Branch:** `feature/namma-clinic-demo-data-model`
- **Review Scope:** Service Boundary Integrity, Actor Authorization Scopes, Procurement/Pharmacy Separation, Concurrency Locking, Failure Rollback Guarantees, Test Expansion, and API Safety Contract.
- **Database Schema Migrations:** Zero schema changes (`makemigrations --check`: `No changes detected`).

Phase 12A was conducted as a rigorous, code-level integrity and authorization audit of the Phase 12 domain service layer. All services were inspected against the approved database architecture. The procurement domain has been formally decoupled into `apps/pharmacy/procurement_services.py` while ensuring inventory posting remains strictly centralized under `post_inventory_movement`. Actor authorization checks have been hardened across privileged IAM, laboratory verification, follow-up completion, inventory movements, and procurement approvals. 10 mandatory failure/rollback test scenarios were authored and passed, proving comprehensive transaction safety and privilege escalation prevention.

---

## 2. GIT BASELINE VERIFICATION

The exact repository status at the beginning of Phase 12A:
- **Baseline HEAD:** `7dfe9114cea2d0aba5d246ada5bea3c5a37920b4`
- **Branch:** `feature/namma-clinic-demo-data-model`
- **Working Tree:** Clean (Phase 12 domain service commit).

---

## 3. SERVICE INVENTORY

| Domain | Service Module | Public Service Functions | Model Dependencies | Transaction Scope | Concurrency Lock | Authorization Enforcement | Audit Req. | Test Location |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **IAM** | `apps.accounts.services` | `create_staff_profile`, `update_staff_status`, `assign_role`, `end_role_assignment`, `assign_facility`, `transfer_staff` | `Person`, `StaffProfile`, `RoleMaster`, `StaffRoleAssignment`, `StaffFacilityAssignment` | `transaction.atomic` | N/A | Active actor required; Admin check for privileged roles | Yes | `apps/accounts/tests_services.py` |
| **Tokens** | `apps.visits.services` | `allocate_token`, `issue_opd_token`, `issue_lab_token` | `FacilityDailyCounter`, `Visit`, `DiagnosticOrder` | `transaction.atomic` | `select_for_update` on Counter | Implicit via Visit / Order context | Monotonic log | `apps/visits/tests_services.py` |
| **Diagnostics** | `apps.laboratory.services` | `create_diagnostic_order`, `create_test_request`, `collect_specimen`, `record_diagnostic_result`, `verify_diagnostic_result`, `amend_diagnostic_result` | `DiagnosticOrder`, `TestRequest`, `Specimen`, `DiagnosticResult`, `DiagnosticResultAmendment` | `transaction.atomic` | `select_for_update` on Result | Active clinical staff for verification/amendment | Yes | `apps/laboratory/tests_services.py` |
| **Follow-Up** | `apps.referrals.services` | `create_followup_task`, `complete_followup` | `FollowUpTask`, `Visit`, `Patient`, `Facility` | `transaction.atomic` | `select_for_update` on Task | Active staff; Completed Visit; Patient/Facility match | Yes | `apps/referrals/tests_services.py` |
| **Referrals** | `apps.referrals.services` | `create_referral_order`, `transition_referral_state` | `ReferralOrder`, `ReferralEvent` | `transaction.atomic` | N/A | Active clinical staff | Append-only event | `apps/referrals/tests_services.py` |
| **Inventory** | `apps.pharmacy.services` | `post_inventory_movement`, `quarantine_stock`, `release_quarantined_stock`, `recall_stock`, `damage_stock`, `dispose_stock` | `InventoryLedger`, `MedicineBatch` | `transaction.atomic` | `select_for_update` on Batch | Active staff; Negative balance guard | Immutable ledger | `apps/pharmacy/tests_services.py` |
| **Dispensation** | `apps.pharmacy.services` | `dispense_prescription` | `Prescription`, `PrescriptionItem`, `Dispensation`, `DispensationItem`, `MedicineBatch`, `InventoryLedger` | `transaction.atomic` | `select_for_update` on Batch & Item | Active staff; Verified Rx; Multi-batch FEFO | Ledger + Dispensation | `apps/pharmacy/tests_services.py` |
| **Procurement** | `apps.pharmacy.procurement_services` | `create_purchase_order`, `approve_purchase_order`, `receive_goods_receipt` | `PurchaseOrder`, `PurchaseOrderItem`, `PurchaseOrderApproval`, `GoodsReceiptNote`, `GoodsReceiptItem`, `MedicineBatch` | `transaction.atomic` | Delegated to `post_inventory_movement` | Active staff; Approval tier guards | Yes | `apps/pharmacy/tests_services.py` |
| **NCD** | `apps.ncd.services` | `register_ncd_condition`, `record_ncd_assessment` | `NCDCondition`, `NCDAssessment` | `transaction.atomic` | N/A | Active clinical staff | Yes | `apps/accounts/tests_phase12_services.py` |
| **Surveillance**| `apps.surveillance.services` | `report_surveillance_case`, `dispatch_public_health_notification` | `DiseaseSurveillanceCase`, `PublicHealthNotification` | `transaction.atomic` | N/A | Active staff / Surveillance officer | Yes | `apps/accounts/tests_phase12_services.py` |
| **Audit** | `apps.audit.services` | `record_audit_event` | `AuditLogEntry`, `StaffProfile`, `Facility` | Standalone | N/A | Durable actor capture | Write-only | `apps/audit/tests_services.py` |

---

## 4. PROCUREMENT vs PHARMACY BOUNDARY AUDIT

### 4.1 Finding & Assessment
- **Status:** `CORRECTED`
- In Phase 12, procurement services (`approve_purchase_order`, `receive_goods_receipt`) were defined inside `apps/pharmacy/services.py`.
- While the Django application layout groups procurement models under the `pharmacy` app label (preserving the approved Phase 11 database schema), procurement decisions and inventory accounting represent distinct business domains.

### 4.2 Architectural Resolution
1. Extracted dedicated procurement workflows into:
   [`apps/pharmacy/procurement_services.py`](file:///d:/project/namma_clinic/backend/apps/pharmacy/procurement_services.py)
   Containing:
   - `create_purchase_order`
   - `approve_purchase_order`
   - `receive_goods_receipt`
2. **Critical Rule Enforced:**
   - Procurement owns purchase order agreements, approvals, and goods receipt inspections.
   - When goods are accepted in `receive_goods_receipt`, stock creation and balance increments are strictly delegated to `post_inventory_movement` from `apps.pharmacy.services`.
   - Procurement does NOT maintain an independent stock accounting mechanism.
3. In `apps/pharmacy/services.py`, the procurement functions are cleanly re-exported to maintain backwards compatibility with existing consumers.

---

## 5. ACTOR & AUTHORIZATION AUDIT

### 5.1 Verification Flow
The conceptual flow was verified and enforced across all privileged domain services:
```
requesting_actor (StaffProfile)
         ↓
  authorization validation (status == ACTIVE, role/scope check)
         ↓
  business validation (invariants, date bounds, balance checks)
         ↓
  database transaction (`transaction.atomic`)
         ↓
  row-level locking (`select_for_update`)
         ↓
  state mutation
         ↓
  audit event creation (`record_audit_event`)
```

### 5.2 Specific Hardening Applied
1. **IAM Privilege Escalation Prevention:**
   - In `assign_role`: Verified that if a caller attempts to assign privileged roles (`ADMIN`, `SYSTEM_ADMIN`, `HOSPITAL_ADMIN`), the `actor_staff` MUST hold administrative credentials. Non-admin callers (such as Nurses or ordinary Medical Officers) attempting to assign admin roles are rejected with `UnauthorizedDomainAction`.
   - In `assign_facility` and `transfer_staff`: Inactive or suspended actors are rejected with `UnauthorizedDomainAction`.
2. **Diagnostic Result Verification:**
   - In `verify_diagnostic_result`: `verified_by_staff` is validated. Inactive staff (`status != 'ACTIVE'`) are rejected with `UnauthorizedDomainAction`.
   - In `amend_diagnostic_result`: Inactive amending staff are rejected with `UnauthorizedDomainAction`.
3. **Follow-Up Completion:**
   - In `complete_followup`: `completing_staff` is validated. Inactive staff are rejected with `UnauthorizedDomainAction`.
   - Encounter status is validated: Attempts to complete a follow-up using a non-completed visit (e.g. `IN_CONSULTATION`) are rejected with `InvalidFollowUpCompletionError`.
4. **Inventory & Dispensation:**
   - In `post_inventory_movement`: `performed_by_staff` must be active (`status == 'ACTIVE'`). Inactive staff are rejected with `UnauthorizedDomainAction`.
   - In `dispense_prescription`: `dispensing_staff` must be active (`status == 'ACTIVE'`). Inactive staff are rejected with `UnauthorizedDomainAction`.
5. **Procurement Approvals & GRN:**
   - In `approve_purchase_order`: `approver_staff` must be active (`status == 'ACTIVE'`).
   - In `receive_goods_receipt`: `receiving_staff` must be active (`status == 'ACTIVE'`).

---

## 6. INVENTORY ACCOUNTING AUDIT

### 6.1 Findings
- **Status:** `VERIFIED`
- **Accounting Source:** `InventoryLedger` is the sole source of truth. Every mutation creates an immutable journal row with `quantity_delta` and `balance_after`.
- **Fast-Read Synchronization:** `MedicineBatch` fast-read fields (`quantity`, `available_quantity`, `quarantined_quantity`, `recalled_quantity`, `damaged_quantity`) are updated atomically inside the same transaction.
- **Row Locking:** All movements execute under `MedicineBatch.objects.select_for_update().get(pk=batch.pk)`.
- **Negative Balance Prevention:**
  - `if new_balance < 0: raise InsufficientStockError(...)`
  - `if curr_val + delta < 0: raise InsufficientStockError(...)`
- **Rollback Guarantee:** If an operation attempts to exceed available stock or encounters an exception, `transaction.atomic()` discards all database modifications. Neither ledger records nor batch balance modifications persist. Tested in `test_insufficient_inventory_rollback`.

---

## 7. DISPENSATION AUDIT

### 7.1 Findings
- **Status:** `VERIFIED`
- **Prescription Linkage:** Verified prescriptions (`status == 'VERIFIED'`) are required.
- **Multi-Batch & Partial Dispensing:** Supported. Each batch allocation is locked with `select_for_update()` and deducted via `post_inventory_movement`.
- **Rollback Guarantee:** Dispensing multi-item prescriptions is wrapped in a single `transaction.atomic()`. If item 2 fails (e.g. insufficient batch stock), item 1's deduction, `Dispensation`, `DispensationItem`, and `InventoryLedger` entries are completely rolled back. Tested in `test_dispensing_multi_item_insufficient_stock_rollback`.

---

## 8. DIAGNOSTIC SERVICE AUDIT

### 8.1 Findings
- **Status:** `VERIFIED`
- **Durable Staff Authorship:** `entered_by_staff`, `verified_by_staff`, and `amended_by_staff` are preserved.
- **1:1 Result Uniqueness:** Attempting to record a second result for a `TestRequest` raises `DiagnosticResultAlreadyExistsError`.
- **Verified Immutability:** Once verified, re-verifying raises `VerifiedResultImmutableError`. Values can only be corrected through `amend_diagnostic_result`, creating an immutable `DiagnosticResultAmendment`.

---

## 9. FOLLOW-UP & REFERRAL AUDIT

### 9.1 Findings
- **Status:** `VERIFIED`
- **Follow-Up Invariants:**
  1. Task must be in `PENDING` status.
  2. Visit must be in `COMPLETED` status.
  3. Patient IDs must match.
  4. Facility IDs must match.
  5. Completing staff must be active.
- **Referral Invariants:**
  1. Valid state machine progression.
  2. Append-only `ReferralEvent` generation on every transition.

---

## 10. TEST ORGANIZATION & EXPANSION

### 10.1 Test Architecture
Tests were modularized into domain test files close to their respective domain services:
- `apps/common/tests_base.py` (`DomainServiceBaseTestCase`: standard geography, facilities, active/suspended staff, roles, patients, visits)
- `apps/accounts/tests_services.py` (7 tests: staff profiles, valid assignments, non-admin privilege rejection, inactive actor rejection, invalid period, overlap, transfer)
- `apps/visits/tests_services.py` (1 test: token allocation, counter isolation)
- `apps/laboratory/tests_services.py` (4 tests: multi-requests, shared specimen, result uniqueness, verified immutability, inactive verification rejection, amendment)
- `apps/referrals/tests_services.py` (5 tests: referral state machine, follow-up valid completion, inactive completing staff rejection, non-completed visit rejection, mismatch rejection)
- `apps/pharmacy/tests_services.py` (4 tests: unauthorized inventory mutation, insufficient stock rollback, multi-item dispensing rollback, GRN failure rollback)
- `apps/audit/tests_services.py` (1 test: audit event recording, actor preservation, payload before/after)
- `apps/accounts/tests_phase12_services.py` (15 integration tests across all workflows)

### 10.2 Mandatory Failure & Rollback Test Scenarios
All 10 required failure/rollback scenarios were explicitly implemented and passed:
1. `test_unauthorized_role_assignment_non_admin` [PASS]
2. `test_unauthorized_facility_assignment_inactive_actor` [PASS]
3. `test_unauthorized_diagnostic_verification_inactive_actor` [PASS]
4. `test_unauthorized_followup_completion_inactive_staff` & `test_followup_completion_non_completed_visit_rejected` [PASS]
5. `test_unauthorized_inventory_mutation` [PASS]
6. `test_insufficient_inventory_rollback` [PASS]
7. `test_grn_failure_rollback` [PASS]
8. `test_dispensing_multi_item_insufficient_stock_rollback` [PASS]
9. `test_diagnostic_result_uniqueness_and_verification` (re-verification immutability) [PASS]
10. `test_audit_event_recording_and_actor_preservation` [PASS]

### 10.3 Test Execution Results
- **Domain Service Tests (22 tests):** `OK` (0 errors, 0 failures in 0.205s)
- **Phase 12 Integration Tests (15 tests):** `OK` (0 errors, 0 failures in 0.166s)
- **Phase 11 Model Regression Tests (17 tests):** `OK` (0 errors, 0 failures in 0.102s)
- **Total Passing Service & Model Tests:** 54 tests.

---

## 11. CLASSIFICATION OF FINDINGS

| Item | Classification | Status & Resolution |
| :--- | :--- | :--- |
| **Procurement Service Separation** | `CORRECTED` | Extracted into `apps/pharmacy/procurement_services.py`; inventory mutations delegated to `post_inventory_movement`. |
| **IAM Privilege Escalation** | `CORRECTED` | Non-admin callers prevented from assigning administrative roles; inactive callers rejected. |
| **Diagnostic Verification Authorization** | `CORRECTED` | Inactive staff prevented from verifying or amending results. |
| **Follow-Up Encounter Validation** | `CORRECTED` | Enforced completed visit requirement and active staff validation in `complete_followup`. |
| **Inventory Mutator Authorization** | `CORRECTED` | Inactive staff rejected in `post_inventory_movement` and `dispense_prescription`. |
| **Dispensing Multi-Item Rollback** | `VERIFIED` | Atomic transaction rollback verified when subsequent items fail. |
| **Inventory Negative Balance Prevention** | `VERIFIED` | Verified under row lock (`select_for_update`). |
| **GRN Rollback on Failure** | `VERIFIED` | Verified zero ghost batches or ledger entries on GRN rejection. |
| **Service Test Placement** | `CORRECTED` | Tests distributed into domain service test files backed by `DomainServiceBaseTestCase`. |
| **API Safety Contract** | `VERIFIED` | Documented in `docs/PHASE_12A_API_SAFETY_CONTRACT.md`. |
| **PostgreSQL Exclusion Constraints** | `DEFERRED` | Btree-gist exclusion constraints deferred to production PostgreSQL target deployment. |
| **SQLite Row Lock Simulation** | `KNOWN LIMITATION`| SQLite serializes file writes; actual multi-process row locking activates in production PostgreSQL. |

---

## 12. CONCLUSION & GATE APPROVAL

All domain service boundaries, actor authorization checks, inventory ledger invariants, and transactional rollback guarantees have been rigorously hardened, tested, and documented.

**GATE STATUS: PHASE_12A_APPROVED**
