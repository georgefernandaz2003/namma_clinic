# PHASE 12A — API SAFETY CONTRACT & ARCHITECTURAL MANDATES

## 1. PURPOSE & ARCHITECTURAL PREMISE

This contract establishes binding rules for future REST API, ViewSet, and Serializer implementation across all Namma Clinic clinical and administrative modules.

The approved layered architecture is:

```
HTTP Request / Future ViewSet
              ↓
  Authentication & Request Actor Context
              ↓
      Domain Service Layer
              ↓
   Django ORM / Target Models
              ↓
         Database
```

**Core Principle:** Business invariants and data integrity MUST NEVER depend on DRF Serializers or HTTP ViewSets alone. All mutations of security-sensitive, clinical, accounting, or lifecycle state must be executed exclusively through the authoritative Domain Service Layer.

---

## 2. MANDATORY FLOW FOR API VIEWSETS

Every incoming mutating API call must execute the following uniform flow:

1. **Authentication:**
   Authenticate the incoming `request.user`.

2. **Durable Actor Context Extraction:**
   Resolve the user's active professional identity (`request.user.person.staff_profile`).
   - If an endpoint requires clinical or administrative authority and no active `StaffProfile` exists, the API MUST reject the request (`403 Forbidden` / `UnauthorizedDomainAction`).

3. **Domain Service Invocation:**
   Call the corresponding domain service function, passing:
   - Target entity / aggregate root
   - Validated domain parameters
   - The authenticated `actor_staff` (or `performed_by_staff`, `verified_by_staff`, `completing_staff`, `dispensing_staff`, `approver_staff`)

4. **Deterministic Exception Translation:**
   Catch explicit domain exceptions from `apps.common.exceptions` and map them to HTTP responses:
   - `UnauthorizedDomainAction` → `403 Forbidden`
   - `DomainValidationError`, `InvalidAssignmentPeriodError`, `OverlappingAssignmentError` → `400 Bad Request`
   - `InvalidStateTransition`, `VerifiedResultImmutableError`, `DiagnosticResultAlreadyExistsError` → `409 Conflict`
   - `InsufficientStockError`, `InvalidBatchOperationError`, `InvalidProcurementStateError` → `422 Unprocessable Entity`

---

## 3. STRICT PROHIBITIONS ("THE MUST NOTs")

Future API developers MUST NOT:

1. **NO Direct Model Mutations on Protected Entities:**
   - Never call `.save()`, `.update()`, or `.delete()` directly on `InventoryLedger`, `MedicineBatch` (quantities), `DiagnosticResult` (verified state), `FollowUpTask` (completion status), `StaffRoleAssignment`, or `StaffFacilityAssignment`.
   - All state transitions must occur through domain services.

2. **NO Independent Stock Accounting:**
   - Never compute stock balances or adjust `available_quantity` inside serializers, views, or endpoints.
   - `InventoryLedger` is the sole accounting source of truth. All stock deductions, receipts, recalls, damages, or quarantines must invoke `post_inventory_movement` or dedicated inventory services.

3. **NO Bypass of Service Authorization:**
   - Never pass dummy or arbitrary staff profiles to bypass domain privilege checks.
   - The service layer independently verifies actor active status and administrative scopes.

4. **NO Direct Mutation of Verified Diagnostic Results:**
   - Once a `DiagnosticResult` is in status `VERIFIED`, it cannot be altered or overwritten.
   - Corrections must go through `amend_diagnostic_result`, creating an immutable `DiagnosticResultAmendment`.

5. **NO Direct Completion of Follow-Up Tasks:**
   - Never directly mark a `FollowUpTask` as completed.
   - `complete_followup()` must be invoked, ensuring patient match, facility match, completed visit encounter, and authorized completing staff.

6. **NO Unchecked Role or Facility Manipulation:**
   - Role assignments, facility attachments, and staff transfers must strictly flow through `assign_role()`, `assign_facility()`, and `transfer_staff()`.
   - Ordinary staff cannot elevate privileges or assign administrative roles.

---

## 4. DOMAIN SERVICE BOUNDARY REFERENCE

| Target Operation | Required Domain Service | Disallowed Direct Action |
| :--- | :--- | :--- |
| **Assign Role** | `apps.accounts.services.assign_role` | `StaffRoleAssignment.objects.create(...)` |
| **Transfer Staff** | `apps.accounts.services.transfer_staff` | `facility_assignment.save()` |
| **Allocate OPD / Lab Token** | `apps.visits.services.issue_opd_token` / `issue_lab_token` | Manual sequence generation / counter update |
| **Record Diagnostic Result** | `apps.laboratory.services.record_diagnostic_result` | Raw `DiagnosticResult.objects.create(...)` |
| **Verify Lab Result** | `apps.laboratory.services.verify_diagnostic_result` | Direct status edit to `VERIFIED` |
| **Amend Verified Result** | `apps.laboratory.services.amend_diagnostic_result` | Direct update of result values |
| **Complete Follow-Up** | `apps.referrals.services.complete_followup` | Setting `followup.status = 'COMPLETED'` |
| **Referral Transition** | `apps.referrals.services.transition_referral_state` | Modifying `referral.status` without `ReferralEvent` |
| **Stock Movement / Adjustment** | `apps.pharmacy.services.post_inventory_movement` | Direct modification of `batch.quantity` |
| **Quarantine / Recall / Damage** | `apps.pharmacy.services.quarantine_stock` etc. | Manipulating batch quantity buckets directly |
| **Prescription Dispensing** | `apps.pharmacy.services.dispense_prescription` | Custom dispensing loops or item status updates |
| **PO Approval** | `apps.pharmacy.procurement_services.approve_purchase_order` | Setting `po.status = 'APPROVED'` |
| **GRN Receiving** | `apps.pharmacy.procurement_services.receive_goods_receipt` | Creating batch with manual stock addition |
| **NCD & Surveillance** | `apps.ncd.services` / `apps.surveillance.services` | Ad-hoc diagnosis shortcuts |
| **Audit Logging** | `apps.audit.services.record_audit_event` | Direct DB manipulation without audit provenance |

---

## 5. AUDIT & PROVENANCE REQUIREMENT

Every privileged API mutation must produce an audit trail containing:
- Authenticated `actor_staff`
- Role snapshot at time of execution
- Entity type and Primary Key
- Snapshot of before/after payloads for critical state transitions

Violation of this safety contract will result in rejection at code review and architectural gating.
